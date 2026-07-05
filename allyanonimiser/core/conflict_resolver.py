"""Resolve overlapping/duplicate entity detections into a single result per span.

The analyzer combines results from three sources (Presidio patterns, spaCy NER,
and the common-format recognizers). When two sources cover the same span they
need to be deduplicated; when they disagree on the entity type, priority-based
resolution picks a winner.

Priority rules live in :data:`allyanonimiser.core.anonymizer.DEFAULT_ENTITY_PRIORITY`.
Custom (user-added) patterns receive a small registration-order bonus so that
later-registered entries can override built-in defaults.
"""


import re

from .false_positives import (
    DATE_SHAPE_RE,
    LABEL_SUFFIXES,
    is_false_positive_person,
)
from .recognizer_result import RecognizerResult
from .validators import EntityValidator

# Explicit-label context: if the text immediately before a span names an
# identifier type ("TFN is ...", "Medicare number: ..."), that label is
# stronger evidence than any bare-shape competitor — including one with a
# higher numeric priority. Checked against the ~48 chars preceding the span.
_LABEL_BEFORE: dict[str, re.Pattern] = {
    "AU_TFN": re.compile(
        r"(?:\btfn|\btax\s+file\s+number)(?:\s+(?:is|was|number|no\.?)){0,2}\s*[:#]?\s*$",
        re.IGNORECASE),
    "AU_CENTRELINK_CRN": re.compile(
        r"(?:\bcrn|\bcentrelink(?:\s+reference)?(?:\s+number)?)(?:\s+(?:is|was)){0,1}\s*[:#]?\s*$",
        re.IGNORECASE),
    "AU_ABN": re.compile(
        r"(?:\babn|\baustralian\s+business\s+number)(?:\s+(?:is|was|number|no\.?)){0,2}\s*[:#]?\s*$",
        re.IGNORECASE),
    "AU_ACN": re.compile(
        r"(?:\bacn|\baustralian\s+company\s+number)(?:\s+(?:is|was|number|no\.?)){0,2}\s*[:#]?\s*$",
        re.IGNORECASE),
    "AU_MEDICARE": re.compile(
        r"\bmedicare(?:\s+(?:card|number|no\.?|is|was)){0,2}\s*[:#]?\s*$",
        re.IGNORECASE),
    "US_SSN": re.compile(
        r"(?:\bssn|\bsocial\s+security(?:\s+number)?)(?:\s+(?:is|was)){0,1}\s*[:#]?\s*$",
        re.IGNORECASE),
}

_LABEL_WINDOW = 48


def _has_explicit_label(entity_type: str, full_text: str | None, span_start: int | None) -> bool:
    """True if *full_text* immediately before *span_start* names *entity_type*."""
    if full_text is None or span_start is None:
        return False
    pattern = _LABEL_BEFORE.get(entity_type)
    if pattern is None:
        return False
    prefix = full_text[max(0, span_start - _LABEL_WINDOW):span_start]
    return pattern.search(prefix) is not None

# When a DATE result fails validation, drop it only if the validator flagged
# it as one of these specific false-positive shapes. Other validation failures
# are allowed through (the span still reads like a date).
_DATE_REJECT_REASONS = frozenset({
    "state_postcode", "phone_prefix", "phone_suffix", "phone_fragment",
    "medicare_number", "service_number",
    # spaCy NER frequently mislabels bare numbers (phone fragments, postcodes,
    # generic integers) and random short strings as DATE. If the validator
    # cannot recognise the span as a real date, drop it rather than trust NER.
    "number", "postcode", "duration", "unknown",
})


def _is_valid_single(result: RecognizerResult) -> bool:
    """Return False if ``result`` fails validation for its entity type.

    Entity types without a registered validator are trusted as-is.
    """
    text = result.text
    match result.entity_type:
        case "DATE":
            is_valid, reason = EntityValidator.validate_date(text)
            return is_valid or reason not in _DATE_REJECT_REASONS
        case "NUMBER":
            return EntityValidator.validate_number(text)[0]
        case "AU_PHONE":
            return EntityValidator.validate_phone_number(text)[0]
        case "AU_MEDICARE":
            return EntityValidator.validate_medicare_number(text.replace(" ", ""))[0]
        case "AU_TFN":
            return EntityValidator.validate_tfn(text.replace(" ", ""))[0]
        case "AU_ABN":
            return EntityValidator.validate_abn(text.replace(" ", ""))[0]
        case "CREDIT_CARD":
            return EntityValidator.validate_credit_card(text)[0]
        case _:
            return True


def resolve_entity_conflicts(
    results: list[RecognizerResult],
    text: str,
    patterns: list,
    full_text: str | None = None,
    span_start: int | None = None,
) -> RecognizerResult | None:
    """Pick the best result when multiple entity types match the same span.

    Args:
        results: Competing results, all covering the same ``(start, end)`` span.
        text: The span text itself, used for false-positive heuristics.
        patterns: All patterns registered on the analyzer, in registration
            order; used to give later-registered (user-added) patterns a
            small priority bonus.
        full_text: The complete document text, used for label-context
            disambiguation. Optional for backwards compatibility.
        span_start: Start offset of the span within ``full_text``.

    Returns:
        The winning result, or ``None`` if the span should be dropped.
    """
    if any(text.lower().endswith(sfx) for sfx in LABEL_SUFFIXES):
        return None

    if DATE_SHAPE_RE.match(text):
        results = [r for r in results if r.entity_type not in ("ORGANIZATION", "LOCATION")]
        if not results:
            return None

    if any(r.entity_type == "PERSON" for r in results) and is_false_positive_person(text):
        filtered = [r for r in results if r.entity_type != "PERSON"]
        return filtered[0] if filtered else None

    # Priority-based resolution with a bonus for later-registered patterns.
    from .anonymizer import DEFAULT_ENTITY_PRIORITY

    pattern_order = {
        p.entity_type: i
        for i, p in enumerate(patterns)
        if hasattr(p, "entity_type")
    }
    num_patterns = max(len(patterns), 1)

    def priority(r: RecognizerResult) -> float:
        base = DEFAULT_ENTITY_PRIORITY.get(r.entity_type, 75)
        order = pattern_order.get(r.entity_type, -1)
        bonus = (order / num_patterns) * 10 if order >= 0 else 0
        return base + bonus + r.score

    # Explicit label immediately before the span trumps shape-based priority
    # AND per-type validation: "TFN is 123 456 789" names the identifier even
    # when the value fails its checksum (mistyped PII still needs masking
    # under the right type, not as whatever bare-shape pattern also fired).
    labelled = [r for r in results if _has_explicit_label(r.entity_type, full_text, span_start)]
    if labelled:
        return max(labelled, key=priority)

    # Validate-then-pick: walk candidates from highest priority down and
    # return the first one that passes per-type validation. Without this,
    # a permissive pattern (e.g. CREDIT_CARD matching a 13-digit phone
    # number) wins by priority, fails its checksum, and then the WHOLE
    # span is dropped — silently losing a valid runner-up like PHONE_INTL.
    for candidate in sorted(results, key=priority, reverse=True):
        if _is_valid_single(candidate):
            return candidate
    return None


# Entity types that must survive even when fully contained in a wider span.
# AU_POSTCODE inside an AU_ADDRESS is consumed by the anonymizer's
# keep_postcode feature — absorbing it would silently disable postcode
# preservation.
_NEVER_ABSORBED = frozenset({"AU_POSTCODE"})

# Types allowed to absorb contained spans: high-precision, pattern-derived
# entities whose boundaries we trust. spaCy NER types (PERSON, ORGANIZATION,
# LOCATION, FACILITY, PRODUCT, DATE-from-NER) are deliberately excluded —
# NER junk spans like ORGANIZATION('DOB 30/06/1944') would otherwise eat the
# real DATE inside them.
_ABSORBING_CONTAINERS = frozenset({
    "DATE_OF_BIRTH", "INCIDENT_DATE", "ISO_DATETIME",
    "AU_TFN", "AU_ABN", "AU_ACN", "AU_MEDICARE", "AU_CENTRELINK_CRN",
    "AU_PHONE", "PHONE_INTL", "US_SSN", "CREDIT_CARD", "EMAIL_ADDRESS",
    "AU_ADDRESS", "ADDRESS", "AU_PASSPORT", "AU_DRIVERS_LICENSE",
    "AU_BSB", "AU_ACCOUNT_NUMBER",
    "INSURANCE_POLICY_NUMBER", "INSURANCE_CLAIM_NUMBER",
    "VEHICLE_VIN", "VEHICLE_REGISTRATION",
})


def _absorb_contained(winners: list[RecognizerResult]) -> list[RecognizerResult]:
    """Drop winners whose span is fully contained in a wider winner's span.

    Fragment-prone sources produce sub-spans of wider, more specific
    entities: the spaCy lg model splits the date in "DOB: 15/03/1980" into
    two DATE entities, a bare NUMBER pattern matches the first triplet of a
    TFN, and the bare 9-digit CRN pattern matches the tail of an 11-digit
    ABN. A contained span is absorbed only when its container is a trusted
    pattern-derived type (:data:`_ABSORBING_CONTAINERS`) and its own type
    priority does not exceed the container's — so a PERSON inside an
    ADDRESS-shaped span still survives.
    """
    from .anonymizer import DEFAULT_ENTITY_PRIORITY

    def _prio(r: RecognizerResult) -> int:
        return DEFAULT_ENTITY_PRIORITY.get(r.entity_type, 75)

    out: list[RecognizerResult] = []
    for w in winners:
        if w.entity_type in _NEVER_ABSORBED:
            out.append(w)
            continue
        absorbed = any(
            o is not w
            and o.entity_type in _ABSORBING_CONTAINERS
            and o.start <= w.start
            and w.end <= o.end
            and (o.end - o.start) > (w.end - w.start)
            and _prio(w) <= _prio(o)
            for o in winners
        )
        if not absorbed:
            out.append(w)
    return out


def deduplicate_and_resolve_conflicts(
    results: list[RecognizerResult],
    patterns: list,
    full_text: str | None = None,
) -> list[RecognizerResult]:
    """Collapse duplicate spans and resolve competing entity types.

    Args:
        results: Raw combined results from patterns + spaCy + format recognizers.
        patterns: Analyzer-registered patterns (passed to
            :func:`resolve_entity_conflicts` for priority calculations).
        full_text: The complete document text; enables label-context
            disambiguation. Optional for backwards compatibility.

    Returns:
        Deduplicated results with validation applied.
    """
    spans: dict[tuple[int, int, str], list[RecognizerResult]] = {}
    for result in results:
        key = (result.start, result.end, result.text)
        spans.setdefault(key, []).append(result)

    out: list[RecognizerResult] = []
    for (_start, _end, span_text), span_results in spans.items():
        if len(span_results) == 1:
            winner = span_results[0]
            # Single-candidate PERSON spans skip resolve_entity_conflicts, so
            # apply the FP check here too. Without this, spaCy NER PERSON
            # mislabels (cities, address fragments, label words) slip through
            # whenever they don't co-occur with another competing entity.
            if winner.entity_type == "PERSON" and is_false_positive_person(span_text):
                continue
        else:
            winner = resolve_entity_conflicts(
                span_results, span_text, patterns, full_text, _start
            )
        # Validate the winner regardless of how it was chosen — except when
        # an explicit label immediately precedes the span (a labelled but
        # checksum-invalid TFN is still a TFN and still needs masking).
        # Without validation here, an invalid TFN/ABN can slip through
        # whenever the same span is also matched by a competing entity type,
        # because resolve_entity_conflicts picks by priority without
        # revalidating.
        if winner is not None and (
            _is_valid_single(winner)
            or _has_explicit_label(winner.entity_type, full_text, _start)
        ):
            out.append(winner)
    return _absorb_contained(out)
