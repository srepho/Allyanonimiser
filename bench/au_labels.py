"""Label mappings for the synthetic AU insurance corpus.

Shared by ``eval_ally.py`` (offline, Ally-only) and ``run_au_insurance_eval.py``
(head-to-head comparison) so the two runners cannot drift apart.
"""

# Gold corpus label -> coarse scoring category.
GOLD_TO_CAT = {
    "PERSON": "PERSON",
    "AU_ADDRESS": "ADDRESS",
    "EMAIL_ADDRESS": "EMAIL",
    "AU_PHONE": "PHONE",
    "PHONE_INTL": "PHONE",
    "DATE": "DATE",
    "ISO_DATETIME": "DATE",
    "TIME": "DATE",
    "AU_TFN": "ACCOUNT_LIKE",
    "AU_MEDICARE": "ACCOUNT_LIKE",
    "AU_ABN": "ACCOUNT_LIKE",
    "AU_ACN": "ACCOUNT_LIKE",
    "POLICY_NUMBER": "ACCOUNT_LIKE",
    "INSURANCE_CLAIM_NUMBER": "ACCOUNT_LIKE",
    "VEHICLE_REGISTRATION": "ACCOUNT_LIKE",
    "VIN": "ACCOUNT_LIKE",
    "US_SSN": "ACCOUNT_LIKE",
    "CREDIT_CARD_NUMBER": "ACCOUNT_LIKE",
    # Added for the challenge corpus (make_au_challenge.py).
    "AU_DRIVERS_LICENSE": "ACCOUNT_LIKE",
    "AU_PASSPORT": "ACCOUNT_LIKE",
    "AU_BSB": "ACCOUNT_LIKE",
    "AU_ACCOUNT_NUMBER": "ACCOUNT_LIKE",
    "AU_CENTRELINK_CRN": "ACCOUNT_LIKE",
}

# Allyanonimiser entity type -> coarse scoring category.
ALLY_TO_CAT = {
    "PERSON": "PERSON",
    "AU_ADDRESS": "ADDRESS",
    "LOCATION": "ADDRESS",
    "EMAIL_ADDRESS": "EMAIL",
    "AU_PHONE": "PHONE",
    "PHONE_INTL": "PHONE", "PHONE_NUMBER": "PHONE",
    "DATE": "DATE", "DATE_OF_BIRTH": "DATE", "INCIDENT_DATE": "DATE",
    "ISO_DATETIME": "DATE", "TIME": "DATE",
    "AU_TFN": "ACCOUNT_LIKE",
    "AU_MEDICARE": "ACCOUNT_LIKE",
    "AU_ABN": "ACCOUNT_LIKE",
    "AU_ACN": "ACCOUNT_LIKE",
    "AU_CENTRELINK_CRN": "ACCOUNT_LIKE",
    "INSURANCE_POLICY_NUMBER": "ACCOUNT_LIKE",
    "INSURANCE_CLAIM_NUMBER": "ACCOUNT_LIKE",
    "VEHICLE_REGISTRATION": "ACCOUNT_LIKE",
    "VEHICLE_VIN": "ACCOUNT_LIKE",
    "AU_POSTCODE": "ADDRESS",
    "US_SSN": "ACCOUNT_LIKE",
    "CREDIT_CARD": "ACCOUNT_LIKE",
    "CREDIT_CARD_NUMBER": "ACCOUNT_LIKE",
    "AU_DRIVERS_LICENSE": "ACCOUNT_LIKE",
    "AU_PASSPORT": "ACCOUNT_LIKE",
    "AU_BSB": "ACCOUNT_LIKE",
    "AU_ACCOUNT_NUMBER": "ACCOUNT_LIKE",
    "NAME_CONSULTANT": "PERSON",
}

# Gold label -> Allyanonimiser types that count as the *correct* type.
# Stricter than the category maps: a TFN masked as AU_CENTRELINK_CRN is
# removed (and in-category) but mistyped.
GOLD_TO_ALLY_TYPES = {
    "PERSON": {"PERSON", "NAME_CONSULTANT"},
    "AU_ADDRESS": {"AU_ADDRESS"},
    "EMAIL_ADDRESS": {"EMAIL_ADDRESS"},
    "AU_PHONE": {"AU_PHONE"},
    "PHONE_INTL": {"PHONE_INTL", "PHONE_NUMBER"},
    "DATE": {"DATE", "DATE_OF_BIRTH", "INCIDENT_DATE"},
    "ISO_DATETIME": {"ISO_DATETIME"},
    "TIME": {"TIME"},
    "AU_TFN": {"AU_TFN"},
    "AU_MEDICARE": {"AU_MEDICARE"},
    "AU_ABN": {"AU_ABN"},
    "AU_ACN": {"AU_ACN"},
    "POLICY_NUMBER": {"INSURANCE_POLICY_NUMBER"},
    "INSURANCE_CLAIM_NUMBER": {"INSURANCE_CLAIM_NUMBER"},
    "VEHICLE_REGISTRATION": {"VEHICLE_REGISTRATION"},
    "VIN": {"VEHICLE_VIN"},
    "US_SSN": {"US_SSN"},
    "CREDIT_CARD_NUMBER": {"CREDIT_CARD", "CREDIT_CARD_NUMBER"},
    "AU_DRIVERS_LICENSE": {"AU_DRIVERS_LICENSE"},
    "AU_PASSPORT": {"AU_PASSPORT"},
    "AU_BSB": {"AU_BSB"},
    "AU_ACCOUNT_NUMBER": {"AU_ACCOUNT_NUMBER"},
    "AU_CENTRELINK_CRN": {"AU_CENTRELINK_CRN"},
}

CATEGORIES = ["PERSON", "ADDRESS", "EMAIL", "PHONE", "DATE", "ACCOUNT_LIKE"]

# Template families in generation order; row i was produced by FAMILIES[i % 8]
# (see GENERATORS in make_au_insurance_eval.py).
FAMILIES = [
    "claim_note", "email", "underwriting", "medical_report", "claim_short",
    "expat_claim", "payment_record", "business_travel_claim",
]

# Held-out families. Every gold label in the test families also appears in
# the dev families, so tuning on dev can be checked on unseen templates.
TEST_FAMILIES = {"expat_claim", "payment_record"}
