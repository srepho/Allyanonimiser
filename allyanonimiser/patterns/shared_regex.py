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
# LABEL_FILLER_WORDS are connective tokens allowed between a trigger word and
# its value: "TFN is 123 456 789", "ABN number: 51 824 753 556", "TFN on
# file: ...", "Medicare card number as supplied: ...". Without them, prose
# forms fell through to bare-shape patterns, which is how a labelled TFN came
# back as AU_CENTRELINK_CRN (the bare 9-digit CRN pattern won the span).
# core.conflict_resolver uses the same vocabulary for its label-context check,
# so the two cannot drift. Words that change meaning ("not", "missing") are
# deliberately absent.
LABEL_FILLER_WORDS = (
    r"is|was|number|no\.?|card|on|file|record|provided|supplied|recorded|listed|given|quoted|as"
)
LABEL_FILLER_MAX = 3
_FILLER = rf"(?:\s+(?i:{LABEL_FILLER_WORDS})){{0,{LABEL_FILLER_MAX}}}[\s:#]*"

AU_TFN_LABELLED = rf"\b(?i:TFN|Tax\s+File\s+Number){_FILLER}(\d{{3}}\s*\d{{3}}\s*\d{{3}})\b"
AU_MEDICARE_LABELLED = rf"\b(?i:Medicare){_FILLER}([2-6]\d{{3}}\s*\d{{5}}\s*\d{{1}})\b"
AU_ABN_LABELLED = (
    rf"\b(?i:ABN|Australian\s+Business\s+Number){_FILLER}(\d{{2}}\s*\d{{3}}\s*\d{{3}}\s*\d{{3}})\b"
)
AU_ACN_LABELLED = (
    rf"\b(?i:ACN|Australian\s+Company\s+Number){_FILLER}(\d{{3}}\s*\d{{3}}\s*\d{{3}})\b"
)
AU_PASSPORT_LABELLED = rf"(?:Passport|Passport\s+Number){_FILLER}([A-Z][0-9]{{7}})\b"
AU_CENTRELINK_CRN_LABELLED = (
    rf"\b(?i:CRN|Centrelink\s+Reference\s+Number){_FILLER}(\d{{3}}\s*\d{{3}}\s*\d{{3}}[A-Z]?)\b"
)


# Australian street types (full word and common abbreviation), used by the
# AU_ADDRESS patterns. Based on the common Australia Post street-type list;
# the original sixteen missed everyday forms such as Mall, Grove, Circuit and
# Esplanade, leaving the street part of those addresses exposed.
AU_STREET_TYPES = (
    r"Street|St\.?|Road|Rd\.?|Avenue|Ave\.?|Drive|Dr\.?|Lane|Ln\.?|Place|Pl\.?"
    r"|Court|Ct\.?|Crescent|Cres\.?|Cr\.?|Boulevard|Boulevarde|Blvd\.?|Parade|Pde\.?"
    r"|Highway|Hwy\.?|Close|Cl\.?|Terrace|Tce\.?|Way|Mall|Grove|Gr\.?|Gve\.?"
    r"|Circuit|Cct\.?|Esplanade|Esp\.?|Square|Sq\.?|Quay|Qy\.?|Rise|Row|Mews|Walk"
    r"|Promenade|Prom\.?|Arcade|Arc\.?|Alley|Circle|Loop|Track|Trail|Gardens|Gdns\.?"
    r"|Glen|Vista|View|Outlook|Ridge|Heights|Hts\.?|Green|Grn\.?|Strand|Freeway|Fwy\.?"
)
