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

# Letter classes covering Latin-1, Latin Extended-A and Vietnamese, so names
# such as Ekström, Thành or Nguyễn are letters rather than word breaks.
_UP = "A-Z\u00c0-\u00d6\u00d8-\u00de\u0100-\u017e\u1ea0-\u1ef8"
_LO = "a-z\u00df-\u00f6\u00f8-\u00ff\u0100-\u017f\u1ea0-\u1ef9"
# One name token: Lewis, O'Keefe, O’Connell, McDonald, Nguyen-Tran, Te.
_NAME_TOKEN = rf"[{_UP}](?:[{_LO}]+|['\u2019][{_UP}][{_LO}]+)(?:[{_UP}][{_LO}]+)?(?:-[{_UP}][{_LO}]+)?"
_PARTICLE = r"(?:van|von|der|den|de|da|di|del|la|le|bin|binti)"
# Names stay on one line ([ \t], not \s) so they never run onto the next
# line's label ("Ryan Rush\nPolicy: ...").
_FULL = (rf"{_NAME_TOKEN}(?:[ \t]+[{_UP}]\.)?"
         rf"(?:[ \t]+(?:{_PARTICLE}[ \t]+)*{_NAME_TOKEN}){{1,3}}")          # Anne-Marie T. Dubois
_INITIAL = rf"[{_UP}]\.(?:[ \t]*[{_UP}]\.)?[ \t]+{_NAME_TOKEN}(?:[ \t]+{_NAME_TOKEN})?"  # N. Adeyemi
_CAPS_WORD = rf"[{_UP}][{_UP}'\u2019\-]+"
_SURNAME_FIRST = rf"{_CAPS_WORD}(?:[ \t]+{_CAPS_WORD})?,[ \t]+{_NAME_TOKEN}(?:[ \t]+{_NAME_TOKEN})?"  # ADEYEMI, Ngozi
# All-caps words that are not names (company suffixes, placeholders).
_CAPS_STOP = r"(?:PTY|LTD|LIMITED|INC|CORP|CO|GROUP|TRUST|BANK|TO|BE|TBC|TBA|NOT|SEE|UNKNOWN|NONE|NIL|CONFIRMED)"
_UPPER = rf"(?!{_CAPS_STOP}\b){_CAPS_WORD}(?:[ \t]+(?!{_CAPS_STOP}\b){_CAPS_WORD}){{1,3}}\b"   # NGOZI ADEYEMI
_NAME = rf"(?:{_SURNAME_FIRST}|{_INITIAL}|{_FULL}|{_UPPER})"
_PERSON_ROLE_LABELS = (
    r"policy\s*holder|(?:named\s+)?insured(?:\s+person)?|claimant|customer|client|patient"
    r"|(?:third\s+party\s+)?driver|third\s+party|witness|beneficiary|applicant|member"
    r"|worker|employee|payee|travell?er|injured\s+person|caller"
    r"|next\s+of\s+kin|(?:full\s+|contact\s+)?name"
)
# "Policyholder: Ryan Rush", "Caller name: ...", "Claimant: ADEYEMI, Ngozi".
LABELLED_PERSON_PATTERN = rf"\b(?i:{_PERSON_ROLE_LABELS})(?i:\s+name)?[ \t]*:[ \t]*({_NAME})"
# "Mrs Adeyemi", "Dr Björn Ekström", "Mr J. Smith". The title is not captured.
TITLED_PERSON_PATTERN = (
    rf"\b(?:Mr|Mrs|Ms|Miss|Mx|Dr|Prof)\.?[ \t]+"
    rf"((?:[{_UP}]\.[ \t]+)?{_NAME_TOKEN}(?:[ \t]+(?:{_PARTICLE}[ \t]+)*{_NAME_TOKEN}){{0,2}})"
)
_GREETING_STOP = (r"(?:All|Team|Sir|Madam|Everyone|There|Again|Both|Guys|Folks|Customer|Valued"
                  r"|Mr|Mrs|Ms|Miss|Dr|Prof|Mx|Hi|Hello|Dear|Thanks)")
# Words that start sentences or headings, never surnames after an initial.
_INITIAL_STOP = (r"(?:The|This|That|These|Those|Then|There|It|In|On|At|We|I|He|She|They|You|Our"
                 r"|Your|Please|Note|See|If|As|An|And|But|Or|For|To|Of|By|With|From|Re|Subject"
                 r"|Policy|Claim|Total|Section|Plan|Part|Item|Step|Medicare)")
# "K. Oyelaran", "J.R. Whitcombe" in running text.
INITIAL_PERSON_PATTERN = (
    rf"(?<![A-Za-z.])([{_UP}]\.(?:[ \t]?[{_UP}]\.)?[ \t]+(?!{_INITIAL_STOP}\b){_NAME_TOKEN})"
)
# Self-introductions in call notes: "you're speaking with Tamsin",
# "my name is Ruairi Gallagher".
INTRODUCED_PERSON_PATTERN = (
    rf"\b(?i:speaking\s+(?:with|to)|my\s+name\s+is|(?:his|her|their)\s+name\s+is)[ \t]+"
    rf"(?!{_INITIAL_STOP}\b)({_NAME_TOKEN}(?:[ \t]+{_NAME_TOKEN})?)"
)
# "Hi Ngozi,", "Thanks Lisa." — a first name directly after a greeting.
GREETING_PERSON_PATTERN = (
    rf"\b(?:Hi|Hello|Dear|Thanks|Thank\s+you)[ \t]+(?!{_GREETING_STOP}\b)"
    rf"({_NAME_TOKEN}(?:[ \t]+{_NAME_TOKEN})?)(?=[ \t]*[,.!\n])"
)


def get_general_pattern_definitions():
    """Return patterns for common PII detection."""
    return [
        {
            "entity_type": "PERSON",
            # Excludes greetings and salutations ("Dear Sir").
            # One line only: "Khoury\nInspection" is not a name. Excludes
            # greetings and salutations ("Dear Sir").
            "patterns": [rf"\b(?!(?:Dear|Hi|Hello|Thanks)\b){_NAME_TOKEN}[ \t]+(?!{_GREETING_STOP}\b){_NAME_TOKEN}\b"],
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
            "entity_type": "PERSON",
            "patterns": [TITLED_PERSON_PATTERN, GREETING_PERSON_PATTERN,
                         INITIAL_PERSON_PATTERN, INTRODUCED_PERSON_PATTERN],
            "context": ["mr", "mrs", "ms", "dr", "dear", "hi"],
            "name": "Titled or Greeted Person Name",
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
