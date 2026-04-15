"""Resolve overlapping/duplicate entity detections into a single result per span.

The analyzer combines results from three sources (Presidio patterns, spaCy NER,
and the common-format recognizers). When two sources cover the same span they
need to be deduplicated; when they disagree on the entity type, priority-based
resolution picks a winner.

Priority rules live in :data:`allyanonimiser.core.anonymizer.DEFAULT_ENTITY_PRIORITY`.
Custom (user-added) patterns receive a small registration-order bonus so that
later-registered entries can override built-in defaults.
"""


from .recognizer_result import RecognizerResult
from .validators import EntityValidator

# Known false-positive span-text patterns. If the span text ends in one of
# these, all results for the span are discarded (the span is a label, not PII).
_LABEL_SUFFIXES = ("number", "ref", "#", "id", "identifier")

# Street/place suffixes that cause spaCy to misfire on PERSON.
_STREET_SUFFIXES = (
    " st", " street", " rd", " road", " ave", " avenue",
    " dr", " drive", " ln", " lane", " pl", " place",
    " ct", " court", " cr", " crescent",
)

# When a DATE result fails validation, drop it only if the validator flagged
# it as one of these specific false-positive shapes. Other validation failures
# are allowed through (the span still reads like a date).
_DATE_REJECT_REASONS = frozenset({
    "state_postcode", "phone_prefix", "phone_suffix",
    "medicare_number", "service_number",
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
        case _:
            return True


def _is_false_positive_person(text: str) -> bool:
    """Detect span text that spaCy is likely to have miscategorised as PERSON."""
    lower = text.lower()
    upper = text.upper()
    return (
        lower.startswith("policy")
        or lower.startswith("ref")
        or lower.startswith("claim")
        or upper.startswith("POL-")
        or upper.startswith("CL-")
        or upper.startswith("CLM-")
        or "number" in lower
        or any(lower.endswith(sfx) for sfx in _STREET_SUFFIXES)
        or lower in {"medicare", "dob", "doi"}
    )


def resolve_entity_conflicts(
    results: list[RecognizerResult],
    text: str,
    patterns: list,
) -> RecognizerResult | None:
    """Pick the best result when multiple entity types match the same span.

    Args:
        results: Competing results, all covering the same ``(start, end)`` span.
        text: The span text itself, used for false-positive heuristics.
        patterns: All patterns registered on the analyzer, in registration
            order; used to give later-registered (user-added) patterns a
            small priority bonus.

    Returns:
        The winning result, or ``None`` if the span should be dropped.
    """
    if any(text.lower().endswith(sfx) for sfx in _LABEL_SUFFIXES):
        return None

    if any(r.entity_type == "PERSON" for r in results) and _is_false_positive_person(text):
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

    return max(results, key=priority)


def deduplicate_and_resolve_conflicts(
    results: list[RecognizerResult],
    patterns: list,
) -> list[RecognizerResult]:
    """Collapse duplicate spans and resolve competing entity types.

    Args:
        results: Raw combined results from patterns + spaCy + format recognizers.
        patterns: Analyzer-registered patterns (passed to
            :func:`resolve_entity_conflicts` for priority calculations).

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
            sole = span_results[0]
            if _is_valid_single(sole):
                out.append(sole)
        else:
            winner = resolve_entity_conflicts(span_results, span_text, patterns)
            if winner is not None:
                out.append(winner)
    return out
