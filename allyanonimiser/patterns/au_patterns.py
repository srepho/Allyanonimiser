"""
Australian patterns for detecting Australian-specific PII.

Regexes shared with the fast common-format recognizers
(:mod:`allyanonimiser.core.common_formats`) live in
:mod:`allyanonimiser.patterns.shared_regex`.
"""

from .shared_regex import (
    AU_ABN_LABELLED,
    AU_ACN_LABELLED,
    AU_ADDRESS_PREFIX,
    AU_CENTRELINK_CRN_LABELLED,
    AU_DRIVERS_LICENSE_LABELLED,
    AU_MEDICARE_LABELLED,
    AU_PASSPORT_LABELLED,
    AU_PHONE_PATTERNS,
    AU_POSTAL_BOX_PATTERN,
    AU_SPOKEN_MOBILE_PATTERN,
    AU_STREET_TYPES,
    AU_TFN_LABELLED,
)


def get_au_pattern_definitions():
    """Return patterns for Australian-specific PII."""
    return [
        {
            "entity_type": "AU_TFN",
            "patterns": [AU_TFN_LABELLED],
            "context": ["tax", "file", "number", "TFN"],
            "name": "Australian Tax File Number"
        },
        {
            "entity_type": "AU_PHONE",
            "patterns": [*AU_PHONE_PATTERNS, AU_SPOKEN_MOBILE_PATTERN],
            "context": ["phone", "mobile", "call", "contact", "telephone", "ph", "tel"],
            "name": "Australian Phone Number"
        },
        {
            "entity_type": "AU_MEDICARE",
            "patterns": [
                r"\b[2-6]\d{3}(?:\s*|-)\d{5}(?:\s*|-)\d\b",  # More specific first digit
                AU_MEDICARE_LABELLED,
            ],
            "context": ["medicare", "health", "card", "insurance"],
            "name": "Australian Medicare Number"
        },
        {
            "entity_type": "AU_DRIVERS_LICENSE",
            "patterns": [
                r"\b[A-Z]{2,3}\d{5,8}\b",
                AU_DRIVERS_LICENSE_LABELLED
            ],
            "context": ["license", "licence", "driver", "driving"],
            "name": "Australian Driver's License"
        },
        {
            "entity_type": "AU_ADDRESS",
            "patterns": [
                # Title-case form: anchored by state, postcode optional. Title
                # case on street/suburb tokens keeps narrative prose like
                # "2007 the Court decided to notify the Government" from matching.
                rf"\b{AU_ADDRESS_PREFIX}\d{{1,5}}[A-Za-z]?(?:[-/]\d{{1,4}})?\s+(?:[A-Z][A-Za-z]*\s+){{1,4}}(?:{AU_STREET_TYPES})\.?,?\s+(?:[A-Z][A-Za-z]*\s*){{1,3}},?\s*(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)(?:\s+\d{{4}})?\b",
                # Case-tolerant form: accepts lowercase/mixed suburb and street
                # names ("sydney NSW 2000", "42 queen st melbourne vic 3000")
                # but REQUIRES a full postcode after the state, which is a
                # strong enough anchor to prevent prose false positives even
                # without capitalization.
                rf"(?i)\b{AU_ADDRESS_PREFIX}\d{{1,5}}[A-Za-z]?(?:[-/]\d{{1,4}})?\s+(?:[A-Za-z]+\s+){{1,4}}(?:{AU_STREET_TYPES})\.?,?\s+(?:[A-Za-z]+\s*){{1,3}},?\s*(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s+\d{{4}}\b",
                AU_POSTAL_BOX_PATTERN,
            ],
            "context": ["address", "street", "road", "suburb", "live", "residence"],
            "name": "Australian Address"
        },
        {
            "entity_type": "AU_POSTCODE",
            "patterns": [
                # Require AU context: postcode must be preceded by a state
                # abbreviation or an explicit postcode label. Bare 4-digit
                # matching produced too many false positives on years (e.g.
                # "15/03/2023") and amounts (e.g. "8500 dollars").
                # Split per-state-length because Python's re requires fixed-
                # width lookbehind.
                r"(?i)(?<=(?:NSW|VIC|QLD|TAS|ACT)\s)(?:0[289]\d{2}|[1-9]\d{3})\b",
                r"(?i)(?<=(?:WA|SA|NT)\s)(?:0[289]\d{2}|[1-9]\d{3})\b",
                # Label forms. Lookbehinds must be fixed width, so each spacing
                # / punctuation variant needs its own pattern.
                r"(?i)(?<=postcode\s)(?:0[289]\d{2}|[1-9]\d{3})\b",
                r"(?i)(?<=post\scode\s)(?:0[289]\d{2}|[1-9]\d{3})\b",
                r"(?i)(?<=postal\scode\s)(?:0[289]\d{2}|[1-9]\d{3})\b",
            ],
            "context": ["postcode", "postal", "code", "zip", "post code"],
            "name": "Australian Postcode"
        },
        {
            "entity_type": "AU_BSB",
            "patterns": [
                r"\b\d{3}-\d{3}\b",
                r"BSB\s*:\s*(\d{3}-\d{3})\b",
                r"BSB\s*(?:Number|#)?\s*:\s*(\d{3}-\d{3})\b",
                r"(?:Bank\s+State\s+Branch|BSB)\s*(?:Code|Number)?[:\s]*(\d{3}-\d{3})\b"
            ],
            "context": ["bsb", "bank", "branch", "payment", "transfer"],
            "name": "Australian BSB"
        },
        {
            "entity_type": "AU_ACCOUNT_NUMBER",
            "patterns": [
                # The split "1234 5678" form is tried first so it is not cut
                # short at four digits.
                r"\b(?i:(?:bank\s+)?account|acct)(?:\s*(?i:number|no\.?|#))*[\s:#.]*(\d{4}[ \t\u00a0]\d{4}|\d{4,10})\b"
            ],
            "context": ["account", "bank", "payment", "deposit", "transfer"],
            "name": "Australian Bank Account Number"
        },
        {
            "entity_type": "AU_ABN",
            "patterns": [AU_ABN_LABELLED],
            "context": ["abn", "australian business number", "business", "company"],
            "name": "Australian Business Number"
        },
        {
            "entity_type": "AU_ACN",
            "patterns": [AU_ACN_LABELLED],
            "context": ["acn", "australian company number", "company"],
            "name": "Australian Company Number"
        },
        {
            "entity_type": "AU_PASSPORT",
            "patterns": [
                r"\b[A-Z][0-9]{7}\b",  # Current format
                r"\b[A-Z]{2}[0-9]{6}\b",  # Older format
                AU_PASSPORT_LABELLED,
            ],
            "context": ["passport", "travel", "document"],
            "name": "Australian Passport Number"
        },
        {
            "entity_type": "AU_CENTRELINK_CRN",
            "patterns": [
                r"\b\d{3}\s*\d{3}\s*\d{3}[A-Z]?\b",  # 9 digits with optional letter
                AU_CENTRELINK_CRN_LABELLED,
            ],
            "context": ["centrelink", "crn", "reference", "welfare"],
            "name": "Centrelink Customer Reference Number"
        },
        {
            "entity_type": "VEHICLE_REGISTRATION",
            "patterns": [
                # The broad standalone form must contain a digit. Pure-letter
                # tokens like "ABCDEF" are too ambiguous and commonly occur as
                # non-plate IDs after labels such as "Claim Number".
                # Plus a guard against SSN-shape spans ("SSN 999-04-7100"):
                # if the upcoming text looks like a US SSN segment we abort.
                r"\b(?!AU-\d+\b)(?!NSW|VIC|QLD|WA|SA|TAS|NT|ACT\b)(?!(?:DOB|PLC|LLC|ABN|ACN|TFN|VIN|REF|POL|CRN|BSB|GST|SSN|TIN|NIN)(?:\b|\d))(?![A-Z]{1,3}\s+\d{3}-\d{2}-\d{4}\b)(?=[A-Z0-9-\s]*\d\b)[A-Z]{1,3}[-\s]?[A-Z0-9]{2,3}[-\s]?[A-Z0-9]{1,3}\b",  # Must have digits, exclude states & label tokens & SSN shape
                r"\b(?:Registration|Rego)(?:\.|\:|\s)+\s*([A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3})\b",  # Match after the word Registration/Rego with capturing group
                r"\brego\s+([A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3})\b",   # Match after lowercase "rego" with capturing group
                # Introduced by a vehicle word ("vehicle AU-4321", "Number plate: 1ABC234").
                # The value must mix letters and digits, so "Vehicle 4" and prose
                # after "car" do not match; label tokens (DOB30) are refused as in the
                # bare form. Bare "AU-<digits>" stays excluded above
                # because it is commonly a policy number.
                r"\b(?i:vehicle|car|plate|number\s+plate|licen[cs]e\s+plate)(?:\s+(?i:registration|rego|plate|number|no\.?|is|was)){0,2}[\s:#(]*(?!(?:DOB|PLC|LLC|ABN|ACN|TFN|VIN|REF|POL|CRN|BSB|GST|SSN|TIN|NIN)(?:\b|\d))(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])([A-Z0-9]{1,3}(?:-?[A-Z0-9]{1,4}){1,2})\b",
                r"\b(?!(?:DOB|PLC|LLC|ABN|ACN|TFN|VIN|REF|POL|CRN|BSB|GST)\d)[A-Z]{2,3}\d{2,3}[A-Z]?\b",  # Common format like ABC123 or AB123C
                r"\b\d{1,3}[A-Z]{2,3}\b"  # Common format like 123ABC
            ],
            "context": ["registration", "rego", "vehicle", "car", "plate", "number plate"],
            "name": "Vehicle Registration"
        }
    ]
