"""
General patterns for detecting common PII.

CREDIT_CARD is intentionally absent: the Luhn-validated 13-19-digit pattern
in :mod:`allyanonimiser.patterns.general_intl_patterns` is a strict superset
of the old 4x4-groups form that used to live here.
"""

from .shared_regex import EMAIL_ADDRESS_PATTERN, WRITTEN_DATE_PATTERNS

# Name of the broad two-capitalised-words PERSON pattern. It over-matches
# ("Rundle Mall", "Travel Claim"), so the analyzer skips it when spaCy NER is
# available. Every other PERSON pattern, including user-added ones, still runs.
BROAD_PERSON_PATTERN_NAME = "Person Name"

# One name token: Lewis, O'Keefe, McDonald, Nguyen-Tran, Te.
_NAME_TOKEN = r"[A-Z](?:[a-z]+|'[A-Z][a-z]+)(?:[A-Z][a-z]+)?(?:-[A-Z][a-z]+)?"
# Two to four tokens on one line: [ \t] rather than \s, so a name never runs
# onto the next line's label ("Ryan Rush\nPolicy: ...").
_NAME = rf"{_NAME_TOKEN}(?:[ \t]+{_NAME_TOKEN}){{1,3}}"
_PERSON_ROLE_LABELS = (
    r"policy\s*holder|(?:named\s+)?insured(?:\s+person)?|claimant|customer|client|patient"
    r"|(?:third\s+party\s+)?driver|third\s+party|witness|beneficiary|applicant|member"
    r"|next\s+of\s+kin|(?:full\s+|contact\s+)?name"
)
# "Policyholder: Ryan Rush" -> captures just the name.
LABELLED_PERSON_PATTERN = rf"\b(?i:{_PERSON_ROLE_LABELS})[ \t]*:[ \t]*({_NAME})"


def get_general_pattern_definitions():
    """Return patterns for common PII detection."""
    return [
        {
            "entity_type": "PERSON",
            "patterns": [r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b"],
            "context": ["name", "person", "customer", "insured", "patient"],
            "name": BROAD_PERSON_PATTERN_NAME,
        },
        {
            "entity_type": "PERSON",
            "patterns": [LABELLED_PERSON_PATTERN],
            "context": ["name", "insured", "policyholder", "claimant", "patient"],
            "name": "Labelled Person Name",
        },
        {
            "entity_type": "EMAIL_ADDRESS",
            "patterns": [EMAIL_ADDRESS_PATTERN],
            "context": ["email", "contact", "mail", "@"],
            "name": "Email Address"
        },
        {
            "entity_type": "DATE_OF_BIRTH",
            "patterns": [
                r"\bDOB:\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b",
                r"\bDate of Birth:\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b",
                r"\bBirth Date:\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b"
            ],
            "context": ["dob", "birth", "date", "born"],
            "name": "Date of Birth"
        },
        {
            "entity_type": "LOCATION",
            "patterns": [
                r"\b(?:Sydney|Melbourne|Brisbane|Perth|Adelaide|Hobart|Canberra|Darwin)(?:,\s*(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT))?\b",
                r"\b(?:New South Wales|Victoria|Queensland|Western Australia|South Australia|Tasmania|Northern Territory|Australian Capital Territory)\b"
            ],
            "context": ["location", "city", "state", "place", "at"],
            "name": "Location"
        },
        {
            "entity_type": "DATE",
            "patterns": [r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b", *WRITTEN_DATE_PATTERNS],
            "context": ["date", "on", "when", "time", "day"],
            "name": "Date"
        },
        {
            "entity_type": "MONEY_AMOUNT",
            "patterns": [r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b"],
            "context": ["amount", "payment", "cost", "price", "value"],
            "name": "Money Amount"
        },
        {
            "entity_type": "ORGANIZATION",
            "patterns": [
                r"\b(?:Insurance|Insurances|Bank|Financial|Services|Motors|Mechanics)\b",
                r"\b[A-Z][a-z]+\s+(?:Insurance|Bank|Financial|Services|Motors|Mechanics)\b",
                r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\s+(?:Pty|Proprietary)\s+Ltd\b",
                r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\s+Limited\b",
                r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*\s+(?:Inc|LLC|LLP|Corp|Corporation)\b",
                r"Payee\s*(?:Name)?\s*:\s*([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*(?:\s+(?:Pty\s+Ltd|Limited|Inc|LLC))?)\b",
                r"(?:Company|Business|Firm)\s*(?:Name)?\s*:\s*([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*)\b"
            ],
            "context": ["company", "organization", "business", "firm", "payee", "vendor", "supplier"],
            "name": "Organization"
        }
    ]
