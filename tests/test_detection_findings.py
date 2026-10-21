"""Regressions for detection gaps found by the offline evaluator (bench/eval_ally.py).

Inputs are written fresh here rather than copied from the synthetic corpus, so
the fixes are checked on phrasings the corpus does not contain.
"""
import pytest

from allyanonimiser import create_allyanonimiser


@pytest.fixture(scope="module")
def ally():
    return create_allyanonimiser(spacy_model=None)


def types_at(ally, text, value):
    """Entity types covering the first occurrence of *value* in *text*."""
    start = text.index(value)
    end = start + len(value)
    return {r.entity_type for r in ally.analyze(text) if r.start <= start and r.end >= end}


def masked(ally, text, **kwargs):
    return ally.anonymize(text, keep_postcode=False, **kwargs)["text"]


# --- 1. Labelled TFNs with record-keeping filler words ----------------------

@pytest.mark.parametrize("text", [
    "TFN on file: 123 456 782.",
    "Customer TFN on record 123 456 782",
    "TFN provided: 123 456 782",
    "Tax file number as supplied: 123 456 782",
    "TFN recorded as 123 456 782.",
])
def test_labelled_tfn_with_filler_is_typed_tfn(ally, text):
    assert types_at(ally, text, "123 456 782") == {"AU_TFN"}


@pytest.mark.parametrize("text", [
    "CRN on file: 123 456 782",
    "Centrelink reference number on record: 123 456 782",
])
def test_labelled_crn_with_filler_stays_crn(ally, text):
    assert types_at(ally, text, "123 456 782") == {"AU_CENTRELINK_CRN"}


def test_unrelated_word_between_label_and_number_does_not_force_tfn(ally):
    """'not' is not filler: the TFN label must not reach a number it does not name."""
    text = "TFN not provided; reference 123 456 782"
    assert "AU_TFN" not in types_at(ally, text, "123 456 782")


# --- 2. Street types beyond the original sixteen ---------------------------

@pytest.mark.parametrize("address", [
    "88 Rundle Mall, Adelaide SA 5000",
    "14 Banksia Grove, Ringwood VIC 3134",
    "7 Hilltop Circuit, Belconnen ACT 2617",
    "201 Marine Esplanade, Cairns QLD 4870",
    "3 Federation Square, Melbourne VIC 3000",
    "5 Circular Quay, Sydney NSW 2000",
    "9 Ocean View Rise, Torquay VIC 3228",
    "12 Jacaranda Cct, Kellyville NSW 2155",
])
def test_full_address_masked_for_more_street_types(ally, address):
    text = f"The insured lives at {address} with family."
    out = masked(ally, text)
    street = address.split(",")[0].split(" ", 1)[1]
    assert street not in out, out
    assert "AU_ADDRESS" in types_at(ally, text, address)


def test_street_type_word_in_prose_is_not_an_address(ally):
    text = "We met 3 people at the Square and walked to Sydney today."
    assert "AU_ADDRESS" not in {r.entity_type for r in ally.analyze(text)}


# --- 3. Registrations introduced by vehicle words --------------------------

@pytest.mark.parametrize("text,value", [
    ("Customer called about vehicle AU-4321 today.", "AU-4321"),
    ("Number plate: 1ABC234 was photographed.", "1ABC234"),
    ("Damage to the car (plate XQ-77-ZT) noted.", "XQ-77-ZT"),
    ("Vehicle rego is BTR-555.", "BTR-555"),
])
def test_vehicle_labelled_registration_detected(ally, text, value):
    assert "VEHICLE_REGISTRATION" in types_at(ally, text, value)
    assert value not in masked(ally, text)


@pytest.mark.parametrize("text", [
    "The vehicle was damaged in the storm.",
    "Vehicle 4 in the convoy stopped.",
    "The car plate fell off at 3pm.",
])
def test_vehicle_words_without_plate_value_detect_nothing(ally, text):
    assert "VEHICLE_REGISTRATION" not in {r.entity_type for r in ally.analyze(text)}


def test_bare_au_prefixed_policy_number_unchanged(ally):
    text = "Please reference your policy AU-12345678 for claims."
    assert "VEHICLE_REGISTRATION" not in types_at(ally, text, "AU-12345678")


# --- 4. Labelled names must survive when spaCy NER is loaded ----------------

def _spacy_ally():
    import spacy.util
    if not spacy.util.is_package("en_core_web_sm"):
        pytest.skip("en_core_web_sm not installed")
    return create_allyanonimiser(spacy_model="en_core_web_sm")


@pytest.fixture(scope="module")
def nlp_ally():
    return _spacy_ally()


LABELLED_NAMES = [
    ("Payment Record\n\nPolicyholder: Ryan Rush\nPolicy: P1863121", "Ryan Rush"),
    ("Travel Claim\n\nInsured: Todd Lewis\nPolicy: P9907391", "Todd Lewis"),
    ("Claimant: Mereana Te Whatu\nIncident: hail", "Mereana Te Whatu"),
    ("Patient: Siobhan O'Keefe\nWard: 4B", "Siobhan O'Keefe"),
    ("Third party driver: Anh Nguyen-Tran\nVehicle damaged", "Anh Nguyen-Tran"),
    ("Name: Dylan Ross", "Dylan Ross"),
]


@pytest.mark.parametrize("text,name", LABELLED_NAMES)
def test_labelled_name_masked_with_spacy(nlp_ally, text, name):
    out = nlp_ally.anonymize(text)["text"]
    for part in name.replace("-", " ").replace("'", " ").split():
        if len(part) > 2:
            assert part not in out, out


@pytest.mark.parametrize("text,name", LABELLED_NAMES)
def test_labelled_name_masked_pattern_only(ally, text, name):
    out = masked(ally, text)
    assert name not in out, out


def test_labelled_name_stops_at_line_end(ally):
    """The name must not run onto the next line's label ("Ryan Rush\\nPolicy")."""
    text = "Policyholder: Ryan Rush\nPolicy: P1863121"
    spans = [text[r.start:r.end] for r in ally.analyze(text) if r.entity_type == "PERSON"]
    assert "Ryan Rush" in spans
    assert not any("Policy" in s for s in spans)


def test_label_without_name_detects_nothing(nlp_ally):
    text = "Insured: unknown at time of call\nPatient: TBC"
    assert not [r for r in nlp_ally.analyze(text) if r.entity_type == "PERSON"]


def test_custom_person_pattern_runs_with_spacy(nlp_ally):
    """A PERSON pattern the user adds is not silently ignored when NER is on."""
    from allyanonimiser.core.pattern_manager import CustomPatternDefinition
    ally = _spacy_ally()
    ally.add_pattern(CustomPatternDefinition(
        entity_type="PERSON", patterns=[r"\bAKA\s+([A-Z][a-z]+)\b"], name="alias",
    ))
    text = "Known AKA Zorblax to staff."
    assert "PERSON" in types_at(ally, text, "Zorblax")
