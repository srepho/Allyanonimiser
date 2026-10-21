"""Regressions for gaps found on the AU challenge corpus (dev split).

Inputs are written fresh here, with identifiers that are checksum-valid but not
taken from the corpus, so the fixes are checked on unseen wording and values.
"""
import pytest

from allyanonimiser import create_allyanonimiser
from allyanonimiser.core.validators import EntityValidator


@pytest.fixture(scope="module")
def ally():
    return create_allyanonimiser(spacy_model=None)


def types_covering(ally, text, value):
    """Entity types of results that cover all of *value* (first occurrence)."""
    start = text.index(value)
    end = start + len(value)
    return {r.entity_type for r in ally.analyze(text) if r.start <= start and r.end >= end}


def masked(ally, text):
    return ally.anonymize(text, keep_postcode=False)["text"]


def assert_masked_as(ally, text, value, entity_type):
    out = masked(ally, text)
    assert value not in out, out
    assert entity_type in types_covering(ally, text, value), (text, ally.analyze(text))


# --- Batch 1: identifiers ------------------------------------------------------

@pytest.mark.parametrize("validator,value", [
    (EntityValidator.validate_tfn, "851-819-093"),
    (EntityValidator.validate_abn, "32-159-010-928"),
    (EntityValidator.validate_medicare_number, "3288-20018-2"),
])
def test_validators_accept_hyphen_separators(validator, value):
    assert validator(value)[0]


@pytest.mark.parametrize("text,value,entity_type", [
    ("Tax file number: 851-819-093 on record.", "851-819-093", "AU_TFN"),
    ("Supplier ABN 32-159-010-928 noted.", "32-159-010-928", "AU_ABN"),
    ("Registered company (ACN 187-500-474).", "187-500-474", "AU_ACN"),
    ("Medicare card 5848-37261-6 sighted.", "5848-37261-6", "AU_MEDICARE"),
])
def test_hyphenated_identifiers(ally, text, value, entity_type):
    assert_masked_as(ally, text, value, entity_type)


@pytest.mark.parametrize("text,value,entity_type", [
    ("Spouse TFN for tax offset: 684 268 465", "684 268 465", "AU_TFN"),
    ("Employee TFN (PAYG): 851819093", "851819093", "AU_TFN"),
    ("Partner Medicare details: 3288 20018 2", "3288 20018 2", "AU_MEDICARE"),
])
def test_form_style_labels_set_the_type(ally, text, value, entity_type):
    assert_masked_as(ally, text, value, entity_type)


def test_form_label_does_not_reach_past_its_own_colon(ally):
    """'TFN: none' must not make the ABN after it a TFN."""
    text = "TFN: none. ABN: 32 159 010 928"
    assert "AU_TFN" not in types_covering(ally, text, "32 159 010 928")


@pytest.mark.parametrize("text,value", [
    ("Licence number: 40917255", "40917255"),
    ("Driver's licence no. 2210934", "2210934"),
    ("DL# 618203947 checked", "618203947"),
    ("Other driver (licence S71203) admitted fault", "S71203"),
])
def test_labelled_licences(ally, text, value):
    assert_masked_as(ally, text, value, "AU_DRIVERS_LICENSE")


@pytest.mark.parametrize("text,value", [
    ("Passport is PC4418207 per the caller", "PC4418207"),
    ("passport number N3381045", "N3381045"),
])
def test_labelled_passports(ally, text, value):
    assert_masked_as(ally, text, value, "AU_PASSPORT")


@pytest.mark.parametrize("text,value", [
    ("pol no: HOM410293857", "HOM410293857"),
    ("Policy no: MOT-2021-554210 renewed", "MOT-2021-554210"),
    ("under policy number PL/23/118204", "PL/23/118204"),
    ("policy ref nr58810342", "nr58810342"),
])
def test_labelled_policy_numbers(ally, text, value):
    assert_masked_as(ally, text, value, "INSURANCE_POLICY_NUMBER")


@pytest.mark.parametrize("text,value", [
    ("Claim reference: C2024/118233", "C2024/118233"),
    ("re claim WC-44-781203 lodged", "WC-44-781203"),
    ("clm no: clm-5512870", "clm-5512870"),
])
def test_labelled_claim_numbers(ally, text, value):
    assert_masked_as(ally, text, value, "INSURANCE_CLAIM_NUMBER")


@pytest.mark.parametrize("text", [
    "Policy no: TBA until underwriting completes.",
    "The policy 2024 renewal letter was sent.",
    "Claim reference: see attached",
    "Licence class C, no restrictions.",
])
def test_labels_without_identifier_values_detect_nothing(ally, text):
    found = {r.entity_type for r in ally.analyze(text)}
    assert not found & {"INSURANCE_POLICY_NUMBER", "INSURANCE_CLAIM_NUMBER", "AU_DRIVERS_LICENSE"}, found


@pytest.mark.parametrize("value", ["+61 412 555 019", "+61 2 9012 3344", "+61 8 6123 4455"])
def test_plus61_numbers_are_au_phones(ally, value):
    assert_masked_as(ally, f"Call me on {value} after 5pm.", value, "AU_PHONE")


def test_other_country_codes_stay_international(ally):
    text = "Overseas contact +44 7911 123456 only."
    assert "PHONE_INTL" in types_covering(ally, text, "+44 7911 123456")


@pytest.mark.parametrize("text,value", [
    ("Pay to account 5521 0934 by Friday", "5521 0934"),
    ("Acct no. 778120345 (savings)", "778120345"),
])
def test_account_numbers_fully_masked(ally, text, value):
    assert_masked_as(ally, text, value, "AU_ACCOUNT_NUMBER")


@pytest.mark.parametrize("text,value,entity_type", [
    ("lodged under clm-5520918 today", "clm-5520918", "INSURANCE_CLAIM_NUMBER"),
    ("renewal of pol-77120934 sent", "pol-77120934", "INSURANCE_POLICY_NUMBER"),
])
def test_lowercase_prefixed_references(ally, text, value, entity_type):
    assert_masked_as(ally, text, value, entity_type)
