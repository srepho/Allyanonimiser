"""From candidates to entities, and from entities to non-overlapping segments.

Two stages, kept separate on purpose:

* :func:`resolve` classifies. It validates candidates, settles competing
  types on the same span, drops context false positives and applies context
  boosts. It reuses the v3 rules unchanged.
* :func:`segment` decides what to mask. Every character of every accepted
  entity is assigned to exactly one entity, highest rank first. Overlaps can
  change an entity's *type* in the output, but never shrink what is masked.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from ..core.anonymizer import DEFAULT_ENTITY_PRIORITY
from ..core.conflict_resolver import _has_explicit_label, deduplicate_and_resolve_conflicts
from ..core.context_analyzer import ContextAnalyzer
from ..core.recognizer_result import RecognizerResult
from .policy import Policy
from .types import Entity

_CONTEXT = ContextAnalyzer()


def resolve(
    text: str,
    candidates: Iterable[tuple[str, RecognizerResult]],
    patterns: Sequence,
    entity_types: frozenset[str] | None = None,
) -> tuple[Entity, ...]:
    """Validate and classify candidates into entities.

    Args:
        text: The original text.
        candidates: ``(detector_name, candidate)`` pairs.
        patterns: Registered pattern definitions (used for priority order).
        entity_types: If given, only these types compete. Filtering before
            resolution matters: a span that DATE wins over PERSON must still
            be found when only PERSON is requested.

    Returns:
        Entities sorted by start, then end.
    """
    sources: dict[tuple[int, int, str], str] = {}
    pool: list[RecognizerResult] = []
    for detector, cand in candidates:
        if cand.end <= cand.start or (entity_types is not None and cand.entity_type not in entity_types):
            continue
        if cand.text is None:
            cand = RecognizerResult(cand.entity_type, cand.start, cand.end, cand.score, text[cand.start:cand.end])
        sources.setdefault((cand.start, cand.end, cand.entity_type), detector)
        pool.append(cand)

    entities: list[Entity] = []
    for r in deduplicate_and_resolve_conflicts(pool, list(patterns), full_text=text):
        if _CONTEXT.is_likely_false_positive(text, r.entity_type, r.start, r.end):
            continue
        boost = _CONTEXT.analyze_context(text, r.entity_type, r.start, r.end)["confidence_boost"]
        score = min(1.0, r.score + boost) if boost > 0 else r.score
        # NER spans can carry edge whitespace ("...SA 5045\n"), which turns a
        # contained span into a partial overlap. Trim it.
        start, end = r.start, r.end
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start == end:
            continue
        entities.append(Entity(
            entity_type=r.entity_type, start=start, end=end, score=round(score, 6),
            detector=sources.get((r.start, r.end, r.entity_type), "unknown"),
            labelled=_has_explicit_label(r.entity_type, text, r.start),
        ))
    entities.sort(key=lambda e: (e.start, e.end, e.entity_type))
    return tuple(entities)


def _rank(entity: Entity, policy: Policy) -> tuple:
    return (
        entity.entity_type in policy.retain,          # deliberate retention wins
        entity.labelled,                              # explicit label beats shape
        # Unlisted types (spaCy ORGANIZATION, PRODUCT, ...) rank lowest, as in
        # the v3 anonymizer, so noisy NER spans never take characters from a
        # pattern match they partly overlap.
        DEFAULT_ENTITY_PRIORITY.get(entity.entity_type, 0),
        entity.detector == "rules",                   # pattern boundaries over NER on ties
        entity.score,
        entity.end - entity.start,                    # wider span on ties
        -entity.start,
    )


def segment(text: str, entities: Sequence[Entity], policy: Policy) -> list[tuple[int, int, Entity]]:
    """Assign each masked character to one entity; return contiguous segments.

    Invariants (property-tested):

    * Segments are sorted and never overlap.
    * Every alphanumeric character inside an accepted, non-retained entity
      lies inside exactly one segment.
    * An entity strictly contained in a wider accepted entity is absorbed by
      it, unless retained or labelled.
    * Segments are trimmed of edge whitespace and contain at least one
      alphanumeric character, so no segment hides only punctuation.
    * Neighbouring segments of one type separated only by spaces or light
      punctuation on one line are joined.

    Returns:
        ``(start, end, entity)`` triples. Retained and ``keep`` entities
        produce no segments but still claim their characters.
    """
    accepted = [e for e in entities if policy.applies_to(e.entity_type, e.score)]
    if not accepted:
        return []
    # An entity strictly inside a wider one gives way to it ("St Georges"
    # inside an address), unless it is retained or explicitly labelled. This
    # only changes the output type: the container covers the same characters.
    accepted = [
        a for a in accepted
        if a.entity_type in policy.retain or a.labelled or not any(
            b is not a and b.start <= a.start and a.end <= b.end and (b.end - b.start) > (a.end - a.start)
            and b.entity_type not in policy.retain
            for b in accepted
        )
    ]
    ranked = sorted(accepted, key=lambda e: _rank(e, policy), reverse=True)
    owner: list[int] = [-1] * len(text)
    for idx, ent in enumerate(ranked):
        for pos in range(ent.start, min(ent.end, len(text))):
            if owner[pos] == -1:
                owner[pos] = idx

    segments: list[tuple[int, int, Entity]] = []
    pos = 0
    n = len(text)
    while pos < n:
        idx = owner[pos]
        if idx == -1:
            pos += 1
            continue
        end = pos
        while end < n and owner[end] == idx:
            end += 1
        ent = ranked[idx]
        s, e = pos, end
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        if (s < e and any(c.isalnum() for c in text[s:e])
                and policy.operator_for(ent.entity_type) != "keep"):
            segments.append((s, e, ent))
        pos = end
    return _merge_same_type(text, segments)


_JOINABLE_GAP = re.compile(r"[ \t,.'\u2019-]*")


def _merge_same_type(text: str, segments: list[tuple[int, int, Entity]]) -> list[tuple[int, int, Entity]]:
    """Join neighbouring segments of one type separated only by spaces or
    light punctuation on the same line ("Georgios" + "F. Rossi")."""
    merged: list[tuple[int, int, Entity]] = []
    for seg in segments:
        if merged:
            ps, pe, pent = merged[-1]
            if pent.entity_type == seg[2].entity_type and _JOINABLE_GAP.fullmatch(text[pe:seg[0]]):
                merged[-1] = (ps, seg[1], pent)
                continue
        merged.append(seg)
    return merged
