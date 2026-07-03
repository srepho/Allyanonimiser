"""Single source of truth for regexes shared across detection sources.

These regex literals are used both by the pattern definitions in this
package (loaded into the analyzer as ``CustomPatternDefinition`` dicts) and
by the fast common-format recognizers in
:mod:`allyanonimiser.core.common_formats`. They previously existed as two
hand-maintained copies that had already begun to drift (the 1300-number
pattern differed by ``\\s+`` vs ``\\s*``); any change to an identifier's
shape must now be made exactly once, here.
"""

EMAIL_ADDRESS_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

AU_PHONE_PATTERNS: list[str] = [
    r"\b(?:\+61|0)4\d{2}[\s-]?\d{3}[\s-]?\d{3}\b",  # Mobile with flexible spacing
    r"\b(?:\+61|0)[2378][\s-]?\d{4}[\s-]?\d{4}\b",  # Landline with flexible spacing
    r"\(\d{2}\)\s*\d{4}[\s-]?\d{4}\b",              # (02) 1234 5678 format
    r"\b13\d{2}\s*\d{2}\b",                          # 13xx xx format
    r"\b1300\s*\d{3}\s*\d{3}\b",                     # 1300 xxx xxx
    r"\b1800\s*\d{3}\s*\d{3}\b",                     # 1800 xxx xxx
]

# Label-anchored ("labelled") forms: the identifier must follow its trigger
# word, and the capture group spans just the identifier so the trigger prefix
# doesn't bloat the matched span.
AU_TFN_LABELLED = r"(?:TFN|Tax\s+File\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b"
AU_MEDICARE_LABELLED = r"(?:Medicare|Medicare\s+Number)[:\s]*([2-6]\d{3}\s*\d{5}\s*\d{1})\b"
AU_ABN_LABELLED = r"(?:ABN|Australian\s+Business\s+Number)[:\s]*(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})\b"
AU_ACN_LABELLED = r"(?:ACN|Australian\s+Company\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b"
AU_PASSPORT_LABELLED = r"(?:Passport|Passport\s+Number)[:\s]*([A-Z][0-9]{7})\b"
AU_CENTRELINK_CRN_LABELLED = (
    r"(?:CRN|Centrelink\s+Reference\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3}[A-Z]?)\b"
)
