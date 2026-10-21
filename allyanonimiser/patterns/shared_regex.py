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
    r"(?:\+61\s?|\b0)4\d{2}[\s-]?\d{3}[\s-]?\d{3}\b",  # Mobile with flexible spacing
    r"(?:\+61\s?|\b0)[2378][\s-]?\d{4}[\s-]?\d{4}\b",  # Landline with flexible spacing
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
# Form-style label: "Worker TFN for PAYG withholding: 413 166 953". The trigger
# and the value share a line, and the value follows the first colon after the
# trigger, so "TFN: none. ABN: ..." cannot carry the TFN label to the ABN.
LABEL_FORM_GAP = r"[^\n:]{0,40}:[ \t]*"
_LEAD = rf"(?:{LABEL_FORM_GAP}|{_FILLER})"
# Digit-group separator: spaces (including non-breaking) or a single hyphen.
_SEP = r"(?:\s*|-)"

AU_TFN_LABELLED = rf"\b(?i:TFN|Tax\s+File\s+Number){_LEAD}(\d{{3}}{_SEP}\d{{3}}{_SEP}\d{{3}})\b"
AU_MEDICARE_LABELLED = rf"\b(?i:Medicare){_LEAD}([2-6]\d{{3}}{_SEP}\d{{5}}{_SEP}\d)\b"
AU_ABN_LABELLED = (
    rf"\b(?i:ABN|Australian\s+Business\s+Number){_LEAD}(\d{{2}}{_SEP}\d{{3}}{_SEP}\d{{3}}{_SEP}\d{{3}})\b"
)
AU_ACN_LABELLED = (
    rf"\b(?i:ACN|Australian\s+Company\s+Number){_LEAD}(\d{{3}}{_SEP}\d{{3}}{_SEP}\d{{3}})\b"
)
# Licence values must contain a digit, so "Licence class C" does not match.
AU_DRIVERS_LICENSE_LABELLED = (
    r"\b(?i:(?:driver'?s\s+)?licen[cs]e|DL)(?:\s+(?i:no\.?|number|is|#))*[\s:#]*"
    r"((?=[A-Z]{0,2}\d)[A-Z]{0,2}\d{5,10})\b"
)
AU_PASSPORT_LABELLED = rf"\b(?i:passport){_LEAD}([A-Z]{{1,2}}[0-9]{{7}})\b"
AU_CENTRELINK_CRN_LABELLED = (
    rf"\b(?i:CRN|Centrelink\s+Reference\s+Number){_LEAD}(\d{{3}}\s*\d{{3}}\s*\d{{3}}[A-Z]?)\b"
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


# Insurer reference numbers vary by company ("MOT-2021-554210", "HOM410293857",
# "PL/23/118204", "C2024/118233"), so after an explicit policy or claim label
# any reference-shaped token with at least five digits is accepted.
def _ref_value(min_digits: int) -> str:
    return (rf"((?=(?:[A-Za-z/-]*\d){{{min_digits}}})"
            r"[A-Za-z]{0,4}[-/]?\d[A-Za-z0-9]*(?:[-/][A-Za-z0-9]+){0,3})\b")


# Explicit lead ("Claim Number: ABC123", "pol no: ...", "policy ref X"):
# three digits suffice. Bare lead ("re claim WC-44-781203"): five digits, so
# "the policy 2024 renewal" is not a policy number.
_REF_EXPLICIT = r"(?:(?:\s+(?i:no\.?|number|#|ref(?:erence)?|id))+[ \t]*[:#.]?|[ \t]*[:#])[ \t]*"
_REF_BARE = r"[ \t]+"
POLICY_NUMBER_LABELLED = [
    rf"\b(?i:policy|pol)\b{_REF_EXPLICIT}{_ref_value(3)}",
    rf"\b(?i:policy|pol)\b{_REF_BARE}{_ref_value(5)}",
]
CLAIM_NUMBER_LABELLED = [
    rf"\b(?i:claim|clm)\b{_REF_EXPLICIT}{_ref_value(3)}",
    rf"\b(?i:claim|clm)\b{_REF_BARE}{_ref_value(5)}",
]
