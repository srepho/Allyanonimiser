"""Engine contracts: immutability, determinism, offsets, policies, bundles."""
import dataclasses

import pytest

from allyanonimiser.core.pattern_manager import CustomPatternDefinition
from allyanonimiser.v4 import BUNDLES, Engine, Policy
from allyanonimiser.v4.detectors import default_patterns

TFN = "851 819 093"
TEXT = f"Insured: Ngozi Adeyemi, TFN {TFN}, email ngozi.a@example.com, lives at 27 Banksia Grove, Ringwood VIC 3134."


@pytest.fixture(scope="module")
def engine():
    return Engine.from_bundle("au-rules-v1")


def test_results_are_immutable_and_hold_no_source_values(engine):
    det = engine.detect(TEXT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        det.entities[0].score = 0.0
    result = engine.transform(TEXT)
    for record in (*det.entities, *result.entities, *result.replacements):
        assert TFN not in repr(record) and "Adeyemi" not in repr(record)
    assert TFN not in result.text and "Adeyemi" not in result.text


def test_no_state_carries_between_calls(engine):
    first = engine.detect(TEXT)
    engine.detect("Medicare 3288 20018 2 and DOB 3 March 1971")
    engine.transform("Something else entirely", Policy(min_score=0.0))
    assert engine.detect(TEXT) == first


@pytest.mark.parametrize("batch_size", [1, 2, 64])
def test_transform_many_matches_transform(engine, batch_size):
    texts = [TEXT, "", "No PII here.", "Call 0412 345 678", TEXT]
    policy = Policy.redact()
    batched = list(engine.transform_many(texts, policy, batch_size=batch_size))
    assert batched == [engine.transform(t, policy) for t in texts]


def test_offsets_are_code_points_into_the_original(engine):
    text = f"Zoë 😀 Müller — TFN {TFN} noted"
    result = engine.transform(text)
    tfn = [r for r in result.replacements if r.entity_type == "AU_TFN"]
    assert tfn and text[tfn[0].start:tfn[0].end] == TFN
    assert result.text[tfn[0].output_start:tfn[0].output_end] == "<AU_TFN>"


def test_detection_reuse_and_mismatch(engine):
    det = engine.detect(TEXT)
    assert engine.transform(TEXT, detection=det) == engine.transform(TEXT)
    with pytest.raises(ValueError, match="does not belong"):
        engine.transform(TEXT + " extra", detection=det)


def test_entity_type_filter(engine):
    result = engine.transform(TEXT, Policy.redact({"AU_TFN"}))
    assert TFN not in result.text
    assert "ngozi.a@example.com" in result.text
    assert {r.entity_type for r in result.replacements} == {"AU_TFN"}


def test_postcode_retention_is_explicit(engine):
    assert "3134" not in engine.transform(TEXT).text
    kept = engine.transform(TEXT, Policy(retain={"AU_POSTCODE"})).text
    assert "3134" in kept and "Banksia" not in kept


def test_keyed_hash_is_stable_across_formats_and_keys_differ(engine):
    policy = Policy(default_operator="hash", hash_key=b"k" * 32)
    a = engine.transform(f"TFN {TFN}", policy).text
    b = engine.transform("TFN 851-819-093", policy).text
    assert a == b and TFN not in a
    other = engine.transform(f"TFN {TFN}", Policy(default_operator="hash", hash_key=b"z" * 32)).text
    assert other != a


def test_mask_operator_preserves_length(engine):
    result = engine.transform(f"TFN {TFN}", Policy.mask(mask_char="#"))
    assert result.text == "TFN " + "#" * len(TFN)


def test_custom_pattern_scores_are_honoured():
    custom = CustomPatternDefinition(entity_type="WIDGET_ID", patterns=[r"XQ#\d{8}\b"], name="w", score=0.2)
    engine = Engine.from_bundle(patterns=(*default_patterns(), custom))
    assert "XQ#77889911" in engine.transform("Ref XQ#77889911").text
    assert "XQ#77889911" not in engine.transform("Ref XQ#77889911", Policy(min_score=0.1)).text


def test_bad_inputs_and_bundles(engine, monkeypatch):
    with pytest.raises(TypeError):
        engine.detect(None)
    with pytest.raises(ValueError, match="Unknown bundle"):
        Engine.from_bundle("nope")
    with pytest.raises(ValueError, match="batch_size"):
        list(engine.transform_many(["x"], batch_size=0))
    monkeypatch.setitem(BUNDLES, "missing-model", "xx_model_not_installed")
    with pytest.raises(RuntimeError, match="not installed"):
        Engine.from_bundle("missing-model")


def test_empty_text(engine):
    result = engine.transform("")
    assert result.text == "" and result.replacements == ()


def test_bundle_and_policy_recorded(engine):
    result = engine.transform(TEXT)
    assert result.bundle.startswith("au-rules-v1@")
    assert result.policy == Policy().digest()


@pytest.fixture(scope="module")
def nlp_engine():
    import spacy.util
    if not spacy.util.is_package("en_core_web_sm"):
        pytest.skip("en_core_web_sm not installed")
    return Engine.from_bundle("au-spacy-sm-v1")


def test_spacy_bundle_batching_is_deterministic(nlp_engine):
    texts = [TEXT, "Spoke with Jennifer Walsh in Parramatta about the claim.", TEXT]
    one = [nlp_engine.transform(t) for t in texts]
    assert list(nlp_engine.transform_many(texts, batch_size=2)) == one
    assert "en_core_web_sm" in one[0].bundle
