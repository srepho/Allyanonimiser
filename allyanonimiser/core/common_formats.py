"""Fast regex recognizers for well-known data formats.

These are cheap, high-precision patterns that run alongside Presidio/spaCy
detection. Kept here rather than in ``patterns/`` because the scores and
capture-group handling are specific to how :class:`EnhancedAnalyzer`
consumes them.
"""

import re

from .recognizer_result import RecognizerResult

_EMAIL_PATTERNS: dict[str, str] = {
    "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
}

_PHONE_PATTERNS: dict[str, list[str]] = {
    "AU_PHONE": [
        r"\b(?:\+61|0)4\d{2}[\s-]?\d{3}[\s-]?\d{3}\b",  # Mobile
        r"\b(?:\+61|0)[2378][\s-]?\d{4}[\s-]?\d{4}\b",  # Landline
        r"\(\d{2}\)\s*\d{4}[\s-]?\d{4}\b",              # (02) 1234 5678
        r"\b13\d{2}\s*\d{2}\b",                          # 13xx xx
        r"\b1300\s+\d{3}\s+\d{3}\b",                     # 1300 xxx xxx
        r"\b1800\s*\d{3}\s*\d{3}\b",                     # 1800 xxx xxx
    ],
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
    "AU_TFN": [
        r"(?:TFN|Tax\s+File\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b",
    ],
    "AU_MEDICARE": [
        r"(?:Medicare|Medicare\s+Number)[:\s]*([2-6]\d{3}\s*\d{5}\s*\d{1})\b",
    ],
    "AU_ABN": [
        r"(?:ABN|Australian\s+Business\s+Number)[:\s]*(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})\b",
    ],
    "AU_ACN": [
        r"(?:ACN|Australian\s+Company\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b",
    ],
    "AU_DRIVERS_LICENSE": [
        r"(?:Driver\'?s?\s+License|Licence|DL)[:\s#]*([A-Z0-9]{6,10})\b",
        r"(?:NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\s+License[:\s]*(\d{6,10})\b",
    ],
    "AU_PASSPORT": [
        r"(?:Passport|Passport\s+Number)[:\s]*([A-Z][0-9]{7})\b",
    ],
    "AU_CENTRELINK_CRN": [
        r"(?:CRN|Centrelink\s+Reference\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3}[A-Z]?)\b",
    ],
}


def _emit(entity_type: str, pattern: str, text: str, score: float,
          flags: int = 0) -> list[RecognizerResult]:
    """Run ``pattern`` against ``text`` and emit one result per match.

    If the pattern defines a capturing group, the result spans the group
    rather than the full match.
    """
    out: list[RecognizerResult] = []
    for match in re.finditer(pattern, text, flags):
        if match.lastindex and match.lastindex > 0:
            start, end = match.start(1), match.end(1)
            matched = match.group(1)
        else:
            start, end = match.start(), match.end()
            matched = match.group()
        out.append(RecognizerResult(
            entity_type=entity_type, start=start, end=end,
            score=score, text=matched,
        ))
    return out


def analyze_common_formats(text: str) -> list[RecognizerResult]:
    """Run high-precision regex recognizers for common PII formats."""
    results: list[RecognizerResult] = []

    for entity_type, pattern in _EMAIL_PATTERNS.items():
        results.extend(_emit(entity_type, pattern, text, score=0.95))

    for entity_type, patterns_list in _PHONE_PATTERNS.items():
        for pattern in patterns_list:
            results.extend(_emit(entity_type, pattern, text, score=0.92))

    for entity_type, patterns_list in _ID_PATTERNS.items():
        for pattern in patterns_list:
            results.extend(_emit(entity_type, pattern, text, score=0.9,
                                 flags=re.IGNORECASE))

    for entity_type, patterns_list in _AU_PATTERNS.items():
        for pattern in patterns_list:
            results.extend(_emit(entity_type, pattern, text, score=0.93,
                                 flags=re.IGNORECASE))

    return results
