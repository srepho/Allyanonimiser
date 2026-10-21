"""Stateless detection primitives shared by the v3 analyzer and the v4 engine.

These functions hold no caches or configuration of their own: the caller
passes the patterns, text and spaCy ``Doc``. Moving them out of
:class:`~allyanonimiser.core.analyzer.EnhancedAnalyzer` lets the v4 engine
reuse the same tested detection without inheriting the analyzer's state.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from ..patterns.general_patterns import BROAD_PERSON_PATTERN_NAME
from .false_positives import (
    LOCATION_FP_WORDS,
    NON_LOCATION_PREFIXES,
    ORG_ABBREVIATIONS,
    PERSON_FP_WORDS,
    PERSON_TRAILING_STOP_WORDS,
    STREET_SUFFIXES,
)
from .recognizer_result import RecognizerResult

logger = logging.getLogger(__name__)

_LABEL_TEXTS = frozenset({"ref number", "reference number", "policy number", "claim number"})


def match_patterns(patterns: list[Any], text: str, *, skip_broad_person: bool) -> list[RecognizerResult]:
    """Run registered regex pattern definitions over *text*.

    Args:
        patterns: Pattern definitions (``CustomPatternDefinition`` or objects
            with ``entity_type``, ``patterns`` and optionally ``score``,
            ``name`` and ``compiled_patterns``).
        text: Text to search.
        skip_broad_person: Skip the broad two-word PERSON pattern; set when a
            NER model supplies names.

    Returns:
        One result per match, spanning the first capture group if present.
    """
    results: list[RecognizerResult] = []
    for pattern in patterns:
        if not getattr(pattern, "patterns", None):
            continue
        entity_type = pattern.entity_type
        score = getattr(pattern, "score", None)
        if score is None:
            score = 0.85
        if (skip_broad_person and entity_type == "PERSON"
                and getattr(pattern, "name", None) == BROAD_PERSON_PATTERN_NAME):
            continue

        regexes = getattr(pattern, "compiled_patterns", None)
        if regexes is None:
            regexes = [p for p in pattern.patterns if isinstance(p, str)]

        for regex in regexes:
            try:
                matches = regex.finditer(text) if isinstance(regex, re.Pattern) else re.finditer(regex, text)
                for match in matches:
                    if match.lastindex and match.lastindex > 0:
                        start, end, matched = match.start(1), match.end(1), match.group(1)
                    else:
                        start, end, matched = match.start(), match.end(), match.group()
                    lower = matched.lower()
                    if lower in _LABEL_TEXTS:
                        continue
                    if entity_type == "PERSON" and (
                        "number" in lower or lower.startswith(("ref", "policy", "claim"))
                    ):
                        continue
                    results.append(RecognizerResult(
                        entity_type=entity_type, start=start, end=end, score=score, text=matched,
                    ))
            except re.error:
                continue
            except Exception as e:  # pragma: no cover - defensive, foreign pattern objects
                logger.debug("Error processing pattern %s: %s", regex, e)
                continue
    return results


SPACY_ENTITY_MAP: dict[str, str] = {
    "PERSON": "PERSON",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "DATE": "DATE",
    "TIME": "TIME",
    "MONEY": "MONEY",
    "CARDINAL": "NUMBER",
    "ORDINAL": "NUMBER",
    "QUANTITY": "NUMBER",
    "PERCENT": "PERCENT",
    "PRODUCT": "PRODUCT",
    "EVENT": "EVENT",
    "WORK_OF_ART": "WORK_OF_ART",
    "LAW": "LAW",
    "LANGUAGE": "LANGUAGE",
    "FAC": "FACILITY",
}


def map_spacy_entity_type(label: str) -> str | None:
    """Map a spaCy entity label to an Allyanonimiser entity type."""
    return SPACY_ENTITY_MAP.get(label)


def spacy_doc_to_results(doc: Any) -> list[RecognizerResult]:
    """Convert a spaCy ``Doc`` to results, applying false-positive filters."""
    results: list[RecognizerResult] = []
    for ent in doc.ents:
        entity_type = map_spacy_entity_type(ent.label_)
        if not entity_type:
            continue
        lower = ent.text.lower()

        if entity_type == "PERSON":
            if lower.startswith(("policy", "ref", "claim")) or "number" in lower:
                continue
            if any(lower.endswith(suffix) for suffix in STREET_SUFFIXES):
                continue
            if lower in PERSON_FP_WORDS or any(word in PERSON_FP_WORDS for word in lower.split()):
                continue
            # Pop trailing label words ("Ryan Rush Policy"). split() treats a
            # newline as a separator, so newline-absorbed labels are handled too.
            parts = ent.text.split()
            trimmed = False
            while len(parts) > 1 and parts[-1].lower() in PERSON_TRAILING_STOP_WORDS:
                parts.pop()
                trimmed = True
            if trimmed:
                new_end = ent.start_char + ent.text.find(parts[-1]) + len(parts[-1])
                results.append(RecognizerResult(
                    entity_type=entity_type, start=ent.start_char, end=new_end, score=0.9,
                    text=ent.text[:new_end - ent.start_char],
                ))
                continue

        if entity_type == "ORGANIZATION" and lower in ORG_ABBREVIATIONS:
            continue

        if entity_type == "LOCATION":
            if lower in LOCATION_FP_WORDS:
                continue
            if len(lower.split()) == 1 and any(lower.startswith(p) for p in NON_LOCATION_PREFIXES):
                continue
            if lower.endswith("s") and lower[:-1] in LOCATION_FP_WORDS:
                continue

        results.append(RecognizerResult(
            entity_type=entity_type, start=ent.start_char, end=ent.end_char, score=0.9, text=ent.text,
        ))
    return results
