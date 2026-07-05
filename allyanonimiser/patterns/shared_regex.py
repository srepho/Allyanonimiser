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
#
# _FILLER allows up to two connective tokens between the trigger and the
# value ("TFN is 123 456 789", "ABN number: 51 824 753 556"). Without it,
# only "TFN: <digits>" / "TFN <digits>" matched, and prose forms fell through
# to bare-shape patterns — which is how a labelled TFN used to come back as
# AU_CENTRELINK_CRN (the bare 9-digit CRN pattern won the span).
_FILLER = r"(?:\s+(?:is|was|number|no\.?)){0,2}[\s:#]*"

AU_TFN_LABELLED = rf"(?:TFN|Tax\s+File\s+Number){_FILLER}(\d{{3}}\s*\d{{3}}\s*\d{{3}})\b"
AU_MEDICARE_LABELLED = (
    r"Medicare(?:\s+(?:card|number|no\.?|is|was)){0,2}[\s:#]*([2-6]\d{3}\s*\d{5}\s*\d{1})\b"
)
AU_ABN_LABELLED = (
    rf"(?:ABN|Australian\s+Business\s+Number){_FILLER}(\d{{2}}\s*\d{{3}}\s*\d{{3}}\s*\d{{3}})\b"
)
AU_ACN_LABELLED = (
    rf"(?:ACN|Australian\s+Company\s+Number){_FILLER}(\d{{3}}\s*\d{{3}}\s*\d{{3}})\b"
)
AU_PASSPORT_LABELLED = rf"(?:Passport|Passport\s+Number){_FILLER}([A-Z][0-9]{{7}})\b"
AU_CENTRELINK_CRN_LABELLED = (
    rf"(?:CRN|Centrelink\s+Reference\s+Number){_FILLER}(\d{{3}}\s*\d{{3}}\s*\d{{3}}[A-Z]?)\b"
)
