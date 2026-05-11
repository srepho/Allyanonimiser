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

from .recognizer_result import RecognizerResult
from .validators import EntityValidator

# spaCy NER occasionally mislabels date strings as ORGANIZATION. We drop
# those candidates before priority resolution so the legitimate
# DATE / DATE_OF_BIRTH / INCIDENT_DATE detection wins.
_DATE_SHAPE = re.compile(r"^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}$")

# Known false-positive span-text patterns. If the span text ends in one of
# these, all results for the span are discarded (the span is a label, not PII).
_LABEL_SUFFIXES = ("number", "ref", "#", "id", "identifier")

# Street/place suffixes that cause spaCy to misfire on PERSON.
_STREET_SUFFIXES = (
    " st", " street", " rd", " road", " ave", " avenue",
    " dr", " drive", " ln", " lane", " pl", " place",
    " ct", " court", " cr", " crescent", " mall",
)

# AU capitals + major cities that spaCy frequently mislabels as PERSON when
# they appear alone (no surrounding sentence context to reveal "place").
_AU_CITIES = frozenset({
    "sydney", "melbourne", "brisbane", "perth", "adelaide",
    "hobart", "canberra", "darwin", "newcastle", "wollongong",
    "geelong", "cairns", "townsville",
})

# Acronyms / labels that spaCy sometimes tags as PERSON.
_PERSON_ACRONYMS = frozenset({
    "vin", "abn", "acn", "tfn", "plc", "llc", "gst", "bsb",
    "crn", "dob", "doi", "ref", "pol", "id",
})

# Common label / non-name words that spaCy occasionally tags as PERSON
# alone or as the leading token of a multi-word span.
_PERSON_LABEL_WORDS = frozenset({
    "email", "phone", "mobile", "address", "subject", "tel", "fax",
    "claim", "claims", "policy", "vehicle", "residential", "patient",
    "customer", "insured", "director", "policyholder", "contact",
    "ref", "reference", "number", "date", "time", "dob", "doi",
    "medicare", "matter", "issue", "category", "type", "status",
})

# A span containing an AU state abbreviation followed by a 3-4 digit
# postcode is an address line, never a person.
_STATE_POSTCODE_RE = re.compile(
    r"\b(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s+\d{3,4}\b"
)

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


def _is_false_positive_person(text: str) -> bool:
    """Detect span text that spaCy is likely to have miscategorised as PERSON."""
    lower = text.lower().strip()
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
        or lower in {"medicare"}
        # AU capital alone is almost always a place, not a person.
        or lower in _AU_CITIES
        # Three-letter acronyms / labels frequently misfired as PERSON.
        or lower in _PERSON_ACRONYMS
        # Date-shaped spans labelled PERSON (e.g. spaCy occasionally tags
        # "04/07/1999" as PERSON when a name precedes it).
        or _DATE_SHAPE.match(lower) is not None
        # State+postcode line absorbed into a PERSON span: "Darwin NT 6000",
        # "Sydney NSW 2000". Always an address fragment.
        or _STATE_POSTCODE_RE.search(text) is not None
        # Street numbers absorbed: "460 Rundle Mall", "123 Queen St". The
        # _STREET_SUFFIXES branch catches the common ones; this catches
        # spans that BEGIN with a digit (street number).
        or (text and text[0].isdigit() and " " in text)
        # First (or only) token is a label word ("Email", "vehicle AU-4321",
        # "Residential ..."). Real names don't start with these.
        or (bool(lower.split()) and lower.split()[0] in _PERSON_LABEL_WORDS)
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

    if _DATE_SHAPE.match(text):
        results = [r for r in results if r.entity_type not in ("ORGANIZATION", "LOCATION")]
        if not results:
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

    # Validate-then-pick: walk candidates from highest priority down and
    # return the first one that passes per-type validation. Without this,
    # a permissive pattern (e.g. CREDIT_CARD matching a 13-digit phone
    # number) wins by priority, fails its checksum, and then the WHOLE
    # span is dropped — silently losing a valid runner-up like PHONE_INTL.
    for candidate in sorted(results, key=priority, reverse=True):
        if _is_valid_single(candidate):
            return candidate
    return None


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
            winner = span_results[0]
            # Single-candidate PERSON spans skip resolve_entity_conflicts, so
            # apply the FP check here too. Without this, spaCy NER PERSON
            # mislabels (cities, address fragments, label words) slip through
            # whenever they don't co-occur with another competing entity.
            if winner.entity_type == "PERSON" and _is_false_positive_person(span_text):
                continue
        else:
            winner = resolve_entity_conflicts(span_results, span_text, patterns)
        # Validate the winner regardless of how it was chosen.
        # Without this, an invalid TFN/ABN can slip through whenever the
        # same span is also matched by a competing entity type, because
        # resolve_entity_conflicts picks by priority without revalidating.
        if winner is not None and _is_valid_single(winner):
            out.append(winner)
    return out
