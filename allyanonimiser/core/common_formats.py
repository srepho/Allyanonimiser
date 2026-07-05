"""Fast regex recognizers for well-known data formats.

These are cheap, high-precision patterns that run alongside Presidio/spaCy
detection. Kept here rather than in ``patterns/`` because the scores and
capture-group handling are specific to how :class:`EnhancedAnalyzer`
consumes them.
"""

import re

from ..patterns.shared_regex import (
    AU_ABN_LABELLED,
    AU_ACN_LABELLED,
    AU_CENTRELINK_CRN_LABELLED,
    AU_MEDICARE_LABELLED,
    AU_PASSPORT_LABELLED,
    AU_PHONE_PATTERNS,
    AU_TFN_LABELLED,
    EMAIL_ADDRESS_PATTERN,
)
from .recognizer_result import RecognizerResult

_EMAIL_PATTERNS: dict[str, str] = {
    "EMAIL_ADDRESS": EMAIL_ADDRESS_PATTERN,
}

_PHONE_PATTERNS: dict[str, list[str]] = {
    "AU_PHONE": AU_PHONE_PATTERNS,
}

# Identifier captures require at least one digit so the pattern can't grab a
# stray word after the trigger (e.g. "Claim Note" → "Note", "Policy Number" →
# "Number"). Real claim/policy/rego IDs always contain digits.
_ID_PATTERNS: dict[str, list[str]] = {
    "INSURANCE_CLAIM_NUMBER": [
        r"(?:Claim|CL|CLM)[#:\-\s]+([A-Z0-9-]*\d[A-Z0-9-]*)",
        r"(?:Claim\s+(?:Number|Reference|ID|#))[#:\-\s]+([A-Z0-9-]*\d[A-Z0-9-]*)",
    ],
    "INSURANCE_POLICY_NUMBER": [
        r"(?:Policy|POL)[#:\-\s]+([A-Z0-9-]*\d[A-Z0-9-]*)",
        r"(?:Policy\s+(?:Number|ID|#))[#:\-\s]+([A-Z0-9-]*\d[A-Z0-9-]*)",
    ],
    "VEHICLE_REGISTRATION": [
        r"(?:Registration|Rego|REG)[#:\-\s]+([A-Z0-9-]*\d[A-Z0-9-]*)",
        r"(?:Vehicle\s+(?:Registration|Rego|REG))[#:\-\s]+([A-Z0-9-]*\d[A-Z0-9-]*)",
    ],
    "VEHICLE_VIN": [
        r"(?:VIN|Vehicle\s+Identification\s+Number)[#:\-\s]+([A-Z0-9]{17})",
    ],
}

_AU_PATTERNS: dict[str, list[str]] = {
    "AU_TFN": [AU_TFN_LABELLED],
    "AU_MEDICARE": [AU_MEDICARE_LABELLED],
    "AU_ABN": [AU_ABN_LABELLED],
    "AU_ACN": [AU_ACN_LABELLED],
    # Drivers-license forms are NOT shared with patterns/au_patterns.py: the
    # labelled forms here are deliberately stricter than the standalone forms
    # loaded as analyzer patterns.
    "AU_DRIVERS_LICENSE": [
        r"(?:Driver\'?s?\s+License|Licence|DL)[:\s#]*([A-Z0-9]{6,10})\b",
        r"(?:NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\s+License[:\s]*(\d{6,10})\b",
    ],
    "AU_PASSPORT": [AU_PASSPORT_LABELLED],
    "AU_CENTRELINK_CRN": [AU_CENTRELINK_CRN_LABELLED],
}


# All recognizers compiled once at import: (entity_type, compiled, score).
_COMPILED_RECOGNIZERS: list[tuple[str, re.Pattern, float]] = [
    *((etype, re.compile(pat), 0.95)
      for etype, pat in _EMAIL_PATTERNS.items()),
    *((etype, re.compile(pat), 0.92)
      for etype, pats in _PHONE_PATTERNS.items() for pat in pats),
    *((etype, re.compile(pat, re.IGNORECASE), 0.9)
      for etype, pats in _ID_PATTERNS.items() for pat in pats),
    *((etype, re.compile(pat, re.IGNORECASE), 0.93)
      for etype, pats in _AU_PATTERNS.items() for pat in pats),
]


def analyze_common_formats(text: str) -> list[RecognizerResult]:
    """Run high-precision regex recognizers for common PII formats.

    If a pattern defines a capturing group, the result spans the group
    rather than the full match.
    """
    results: list[RecognizerResult] = []
    for entity_type, compiled, score in _COMPILED_RECOGNIZERS:
        for match in compiled.finditer(text):
            if match.lastindex and match.lastindex > 0:
                start, end = match.start(1), match.end(1)
                matched = match.group(1)
            else:
                start, end = match.start(), match.end()
                matched = match.group()
            results.append(RecognizerResult(
                entity_type=entity_type, start=start, end=end,
                score=score, text=matched,
            ))
    return results
