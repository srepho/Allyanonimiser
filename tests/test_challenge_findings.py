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


# --- Batch 2: dates ---------------------------------------------------------------

@pytest.mark.parametrize("text,value", [
    ("Born 3 March 1971 in Perth.", "3 March 1971"),
    ("Seen on the 22nd of July 2025 by the GP.", "22nd of July 2025"),
    ("Incident 5-Feb-2024 reported late.", "5-Feb-2024"),
    ("Effective 2024-11-30 until renewal.", "2024-11-30"),
    ("Payment made March 3, 2024 by EFT.", "March 3, 2024"),
    ("Hearing set for October 12th 2025.", "October 12th 2025"),
    ("Letter dated 12 Sept 2023 attached.", "12 Sept 2023"),
    ("insd rang 4 june 2025 re excess", "4 june 2025"),
    ("Discharged 01-JAN-26 per notes.", "01-JAN-26"),
])
def test_written_and_iso_dates(ally, text, value):
    out = masked(ally, text)
    assert value not in out, out


@pytest.mark.parametrize("text", [
    "May I call you back tomorrow?",
    "In March the policy renews automatically.",
    "Build version 2024-11 deployed.",
    "Invalid value 2024-13-45 rejected.",
    "We meet on 3 June at the office.",
])
def test_month_words_without_full_dates_are_not_dates(ally, text):
    found = [r for r in ally.analyze(text) if r.entity_type in {"DATE", "DATE_OF_BIRTH", "INCIDENT_DATE"}]
    assert not found, [(text[r.start:r.end], r.entity_type) for r in found]


@pytest.mark.parametrize("text,value", [
    ("Incident 14/02/2025 at the depot.", "14/02/2025"),
    ("Payment 03/06/2024 received.", "03/06/2024"),
    ("Patient 22/11/1980 admitted.", "22/11/1980"),
    ("Visa 09/09/2026 expiry noted.", "09/09/2026"),
    ("Paragraph 12/03/2024 refers.", "12/03/2024"),
])
def test_dates_after_words_ending_in_state_codes_are_kept(ally, text, value):
    """'Incident' ends in 'nt' and 'Visa' in 'sa': neither is a state code."""
    assert value not in masked(ally, text)


def test_state_postcode_still_not_a_date(ally):
    text = "Sydney NSW 2000"
    assert not [r for r in ally.analyze(text) if r.entity_type == "DATE"]


# --- Batch 3: names -------------------------------------------------------------

def person_masked(ally, text, name):
    out = masked(ally, text)
    return all(part not in out for part in name.replace(",", " ").split() if len(part) > 2), out


@pytest.mark.parametrize("text,name", [
    ("Claimant: ADEYEMI, Ngozi\nDOB unknown", "ADEYEMI, Ngozi"),
    ("Payee: NGOZI ADEYEMI\nAmount below", "NGOZI ADEYEMI"),
    ("Insured: N. Adeyemi\nPolicy pending", "N. Adeyemi"),
    ("Policyholder: Anne-Marie T. Dubois\n", "Anne-Marie T. Dubois"),
    ("Worker: Björn Ekström\nEmployer: Acme", "Björn Ekström"),
    ("Traveller: Lê Văn Thành\n", "Lê Văn Thành"),
    ("Injured person: Ahmad Al-Rashid, aged 40", "Ahmad Al-Rashid"),
    ("Caller name: Saoirse O’Connell\n", "Saoirse O’Connell"),
])
def test_role_labelled_name_forms(ally, text, name):
    ok, out = person_masked(ally, text, name)
    assert ok, out


@pytest.mark.parametrize("text,name", [
    ("Spoke to Mrs Adeyemi about the excess.", "Adeyemi"),
    ("Report reviewed by Dr Björn Ekström today.", "Björn Ekström"),
    ("Hi Ngozi, thanks for the photos.", "Ngozi"),
    ("Dear Mr Dubois, we refer to your claim.", "Dubois"),
])
def test_titles_and_greetings(ally, text, name):
    ok, out = person_masked(ally, text, name)
    assert ok, out


@pytest.mark.parametrize("text", [
    "Hi team, the report is attached.",
    "Dear Sir, please find enclosed.",
    "Thanks again, see you Monday.",
    "Payee: ACME PTY LTD\n",
    "Insured: TO BE CONFIRMED\n",
])
def test_greetings_and_labels_without_people(ally, text):
    found = [text[r.start:r.end] for r in ally.analyze(text) if r.entity_type == "PERSON"]
    assert not found, found


@pytest.fixture(scope="module")
def nlp_ally():
    import spacy.util
    if not spacy.util.is_package("en_core_web_sm"):
        pytest.skip("en_core_web_sm not installed")
    return create_allyanonimiser(spacy_model="en_core_web_sm")


@pytest.mark.parametrize("text,name", [
    ("Claimant: ADEYEMI, Ngozi\nDOB unknown", "ADEYEMI, Ngozi"),
    ("Policyholder: Anne-Marie T. Dubois\n", "Anne-Marie T. Dubois"),
    ("Spoke to Mrs Adeyemi about the excess.", "Adeyemi"),
])
def test_name_forms_with_spacy(nlp_ally, text, name):
    ok, out = person_masked(nlp_ally, text, name)
    assert ok, out


@pytest.mark.parametrize("text,name", [
    ("Claimant: Lachlan Reid\nPolicy pending", "Lachlan Reid"),
    ("Insured: Morag Kincaid\n", "Morag Kincaid"),
    ("Witness: Ahmad Al-Rashid\n", "Ahmad Al-Rashid"),
])
def test_names_ending_in_label_suffix_letters_are_kept(ally, text, name):
    """'Reid' ends in 'id' but is not the label word 'ID'."""
    ok, out = person_masked(ally, text, name)
    assert ok, out


@pytest.mark.parametrize("text", ["Policy ref", "Customer ID", "Claim #"])
def test_label_words_alone_are_not_entities(ally, text):
    assert not [r for r in ally.analyze(f"{text}: see above") if r.entity_type == "PERSON"]


def test_doubled_greeting_captures_only_the_name(ally):
    text = "Dear Hi Jenny,\nThanks for the call."
    spans = [text[r.start:r.end] for r in ally.analyze(text) if r.entity_type == "PERSON"]
    assert "Jenny" in " ".join(spans)
    assert not any(s.startswith(("Hi", "Dear")) for s in spans), spans
