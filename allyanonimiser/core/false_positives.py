"""Shared false-positive knowledge for spaCy NER suppression.

Both the analyzer (:meth:`EnhancedAnalyzer._doc_to_results`, which filters
entities as they come out of spaCy) and the conflict resolver
(:mod:`allyanonimiser.core.conflict_resolver`, which re-checks winners during
span deduplication) suppress the same classes of NER mistakes. The word
lists and span-shape checks they rely on live here so a precision fix lands
in every path at once instead of drifting between two copies.
"""

import re

# spaCy NER occasionally mislabels date strings as PERSON/ORGANIZATION.
DATE_SHAPE_RE = re.compile(r"^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}$")

# A span containing an AU state abbreviation followed by a 3-4 digit
# postcode is an address line, never a person.
STATE_POSTCODE_RE = re.compile(r"\b(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s+\d{3,4}\b")

# Known false-positive span-text patterns. If the span text ends in one of
# these, the span is a label, not PII.
LABEL_SUFFIXES = ("number", "ref", "#", "id", "identifier")

# Street/place suffixes that cause spaCy to misfire on PERSON.
STREET_SUFFIXES = (
    " st", " street", " rd", " road", " ave", " avenue",
    " dr", " drive", " ln", " lane", " pl", " place",
    " ct", " court", " cr", " crescent", " mall",
)

# AU capitals + major cities that spaCy frequently mislabels as PERSON when
# they appear alone (no surrounding sentence context to reveal "place").
AU_CITIES = frozenset({
    "sydney", "melbourne", "brisbane", "perth", "adelaide",
    "hobart", "canberra", "darwin", "newcastle", "wollongong",
    "geelong", "cairns", "townsville",
})

# Acronyms / labels that spaCy sometimes tags as PERSON.
PERSON_ACRONYMS = frozenset({
    "vin", "abn", "acn", "tfn", "plc", "llc", "gst", "bsb",
    "crn", "dob", "doi", "ref", "pol", "id",
})

# Common label / non-name words that spaCy occasionally tags as PERSON
# alone or as the leading token of a multi-word span.
PERSON_LABEL_WORDS = frozenset({
    "email", "phone", "mobile", "address", "subject", "tel", "fax",
    "claim", "claims", "policy", "vehicle", "residential", "patient",
    "customer", "insured", "director", "policyholder", "contact",
    "ref", "reference", "number", "date", "time", "dob", "doi",
    "medicare", "matter", "issue", "category", "type", "status",
})

# Insurance-domain vocabulary that spaCy misfires on as PERSON: status and
# action words, business terms, and other non-name tokens seen in claim notes.
PERSON_FP_WORDS = frozenset({
    # Status and state words
    "balance", "outstanding", "await", "awaiting", "pending", "completed",
    "processed", "received", "submitted", "approved", "declined", "rejected",
    "cancelled", "closed", "open", "active", "inactive", "suspended",
    "terminated", "expired", "current", "previous", "ongoing", "finished",
    # Action words often misdetected
    "review", "update", "check", "verify", "confirm", "validate", "process",
    "submit", "approve", "decline", "reject", "cancel", "close", "complete",
    "advised", "notify", "inform", "contact", "follow", "proceed", "continue",
    # Business/Insurance specific terms
    "excess", "premium", "deductible", "coverage", "liability", "claim",
    "policy", "payment", "invoice", "receipt", "refund", "credit", "debit",
    "assessment", "evaluation", "inspection", "investigation", "settlement",
    # Service/Repair terms
    "repairer", "repairs", "service", "maintenance", "workshop", "garage",
    "parts", "replacement", "installation", "removal", "diagnostic", "estimate",
    # Communication status
    "unreachable", "unavailable", "contactable", "available", "busy", "engaged",
    # Common single words that aren't names
    "drop", "pickup", "delivery", "collection", "dispatch", "arrival",
    "departure", "transfer", "forward", "return", "exchange", "replace",
    # Document/Form related
    "form", "document", "report", "statement", "declaration", "certificate",
    "authorization", "approval", "confirmation", "acknowledgment", "notice",
    # Time-related terms
    "today", "tomorrow", "yesterday", "daily", "weekly", "monthly", "yearly",
    "immediate", "urgent", "routine", "scheduled", "overdue",
    # Quality/Condition terms
    "new", "used", "damaged", "repaired", "replaced", "original", "genuine",
    "aftermarket", "compatible", "suitable", "adequate", "insufficient",
})

# Label tokens that spaCy NER absorbs into the end of a PERSON span
# (e.g. "Joe Smith\nDOB", "Kristin Rodriguez\nClaims") because the newline
# doesn't reset entity tagging. Trimmed off iteratively.
PERSON_TRAILING_STOP_WORDS = frozenset({
    "subject", "matter", "issue", "claim", "claims", "policy",
    "number", "date", "time", "amount", "status", "type",
    "category", "dob", "doi", "phone", "mobile", "email",
    "address", "tel", "fax", "ref", "reference",
})

# Abbreviations that spaCy sometimes tags as ORGANIZATION.
ORG_ABBREVIATIONS = frozenset({
    "dob", "doi", "medicare", "abn", "tfn", "acn",
    "ssn", "tin", "nin", "vin", "crn", "bsb", "gst",
    "pol", "ref", "id",
})

# Common words that spaCy misfires on as LOCATION.
LOCATION_FP_WORDS = frozenset({
    # Action words
    "await", "awaiting", "awaits", "awaited",
    "repair", "repairs", "repairing", "repaired",
    "service", "services", "servicing", "serviced",
    "process", "processing", "processed",
    "update", "updates", "updating", "updated",
    "review", "reviews", "reviewing", "reviewed",
    "submit", "submits", "submitting", "submitted",
    "pending", "complete", "completed", "completing",
    # Status words
    "open", "closed", "active", "inactive",
    "approved", "declined", "rejected", "cancelled",
    "available", "unavailable", "occupied", "vacant",
    # Business/Insurance terms
    "claim", "claims", "policy", "policies",
    "coverage", "liability", "excess", "premium",
    "payment", "balance", "outstanding", "overdue",
    # Department/Service terms
    "workshop", "workshops", "garage", "garages",
    "parts", "spares", "supplies", "inventory",
    "storage", "warehouse", "facility", "facilities",
    # Common misdetections
    "drop", "drops", "pickup", "delivery",
    "arrival", "departure", "transit", "shipping",
})

# Single words starting with these prefixes are usually not locations.
NON_LOCATION_PREFIXES = (
    "await", "repair", "serv", "proc", "updat", "review",
    "submit", "pend", "complet", "approv", "declin", "reject",
)


def is_false_positive_person(text: str) -> bool:
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
        or any(lower.endswith(sfx) for sfx in STREET_SUFFIXES)
        or lower in {"medicare"}
        # AU capital alone is almost always a place, not a person.
        or lower in AU_CITIES
        # Three-letter acronyms / labels frequently misfired as PERSON.
        or lower in PERSON_ACRONYMS
        # Date-shaped spans labelled PERSON (e.g. spaCy occasionally tags
        # "04/07/1999" as PERSON when a name precedes it).
        or DATE_SHAPE_RE.match(lower) is not None
        # State+postcode line absorbed into a PERSON span: "Darwin NT 6000",
        # "Sydney NSW 2000". Always an address fragment.
        or STATE_POSTCODE_RE.search(text) is not None
        # Street numbers absorbed: "460 Rundle Mall", "123 Queen St". The
        # STREET_SUFFIXES branch catches the common ones; this catches
        # spans that BEGIN with a digit (street number).
        or (text and text[0].isdigit() and " " in text)
        # First (or only) token is a label word ("Email", "vehicle AU-4321",
        # "Residential ..."). Real names don't start with these.
        or (bool(lower.split()) and lower.split()[0] in PERSON_LABEL_WORDS)
    )
