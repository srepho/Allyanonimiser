"""Configuration persistence must preserve behavior, not just field names."""
import json

import pytest

from allyanonimiser import create_allyanonimiser
from allyanonimiser.utils.settings_manager import SettingsManager


@pytest.mark.parametrize("suffix", ["json", "yaml"])
@pytest.mark.parametrize("metadata", [True, False])
def test_live_snapshot_roundtrip(tmp_path, suffix, metadata):
    if suffix == "yaml":
        pytest.importorskip("yaml")
    ally = create_allyanonimiser(spacy_model=None, enable_caching=False, max_cache_size=37)
    ally.add_pattern({"entity_type": "CUSTOM_CODE", "patterns": [r"ZZ-[A-Z]{4}"], "score": 0.6})
    ally.analyzer.set_active_entity_types(["CUSTOM_CODE", "EMAIL_ADDRESS"])
    ally.analyzer.set_min_score_threshold(0.5)
    ally.set_acronyms({"CONTACT": "Email"})
    ally.batch_size = 23
    path = tmp_path / f"config.{suffix}"
    assert ally.export_config(str(path), include_metadata=metadata)
    restored = create_allyanonimiser(settings_path=str(path))
    assert restored.analyzer.use_spacy is False
    assert restored.analyzer.enable_caching is False
    assert restored.analyzer.max_cache_size == 37
    assert restored.batch_size == 23
    assert len(restored.analyzer.patterns) == len(ally.analyzer.patterns)
    for text in ["CONTACT person@example.com ZZ-ABCD", "ZZ-EFGH", "ordinary words"]:
        expected = ally.analyze(text, expand_acronyms=True)
        actual = restored.analyze(text, expand_acronyms=True)
        assert [r.__dict__ for r in actual] == [r.__dict__ for r in expected]
        assert restored.anonymize(text, expand_acronyms=True, report=False)["text"] == ally.anonymize(
            text, expand_acronyms=True, report=False)["text"]


def test_manager_preserves_patterns_and_adjustments(tmp_path):
    settings = {"patterns": [{"entity_type": "CUSTOM", "patterns": ["ZZZZ"]}],
                "entity_types": {"active": [], "score_adjustment": {"CUSTOM": 0.1}}}
    manager = SettingsManager(settings=settings)
    path = tmp_path / "config.json"
    assert manager.export_config(str(path), include_metadata=False)
    exported = json.loads(path.read_text())
    assert exported["patterns"] == settings["patterns"]
    assert exported["entity_types"] == settings["entity_types"]
    assert "metadata" not in exported


def test_legacy_patterns_load(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"patterns": [{"entity_type": "CUSTOM", "patterns": ["ZZZZ"]}]}))
    ally = create_allyanonimiser(settings_path=str(path), spacy_model=None)
    assert "CUSTOM" in [r.entity_type for r in ally.analyze("ZZZZ")]


@pytest.mark.parametrize("bad", [
    {"schema_version": 99},
    {"schema_version": 1, "patterns": [{"entity_type": "CUSTOM", "patterns": ["["]}]},
    {"schema_version": 1, "analyzer": {"min_score_threshold": 1.5}},
    {"schema_version": 1, "processing": {"batch_size": 0}},
    {"schema_version": 1, "anonymization": {"operators": {"PERSON": "typo"}}},
])
def test_invalid_load_is_atomic(tmp_path, bad, caplog):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(bad))
    manager = SettingsManager(settings={"processing": {"batch_size": 123}})
    assert manager.load_settings(str(path)) is False
    assert manager.settings == {"processing": {"batch_size": 123}}
    assert "Error loading settings" in caplog.text
    with pytest.raises(ValueError, match="settings"):
        create_allyanonimiser(settings_path=str(path), spacy_model=None)


def test_nonserializable_export_does_not_truncate(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("keep me")
    manager = SettingsManager(settings={"custom_callback": lambda x: x})
    assert manager.export_config(str(path)) is False
    assert path.read_text() == "keep me"


def test_reload_replaces_patterns_and_clears_cache(tmp_path):
    source = create_allyanonimiser(spacy_model=None)
    source.analyzer.patterns = []
    source.add_pattern({"entity_type": "CUSTOM", "patterns": ["ZZZZ"]})
    source.anonymizer.entity_priority["CUSTOM"] = 200
    path = tmp_path / "snapshot.json"
    assert source.export_config(str(path))
    target = create_allyanonimiser()
    target.analyze("ZZZZ")
    for _ in range(2):
        assert target.load_settings(str(path))
        assert target.analyzer.use_spacy is False
        assert len(target.analyzer.patterns) == 1
        assert target.anonymizer.analyzer is target.analyzer
        assert target.anonymizer.entity_priority["CUSTOM"] == 200
        assert [r.entity_type for r in target.analyze("ZZZZ")] == ["CUSTOM"]


def test_explicit_factory_options_override_snapshot(tmp_path):
    source = create_allyanonimiser(spacy_model=None, enable_caching=False)
    path = tmp_path / "snapshot.json"
    assert source.export_config(str(path))
    target = create_allyanonimiser(settings_path=str(path), spacy_model="en_core_web_sm",
                                  enable_caching=True, max_cache_size=99)
    assert target.analyzer.spacy_model_requested == "en_core_web_sm"
    assert target.analyzer.enable_caching is True
    assert target.analyzer.max_cache_size == 99


def test_saved_per_call_options_roundtrip(tmp_path):
    source = create_allyanonimiser(spacy_model=None)
    source.settings_manager.set_value("entity_types.score_adjustment", {"EMAIL_ADDRESS": -0.2})
    source.settings_manager.set_anonymization_operators({"EMAIL_ADDRESS": "mask"})
    path = tmp_path / "snapshot.json"
    assert source.export_config(str(path))
    restored = create_allyanonimiser(settings_path=str(path))
    results = []
    for ally in (source, restored):
        text = "Email jane@example.com"
        entities = ally.analyze(text, score_adjustment=ally.settings_manager.get_value(
            "entity_types.score_adjustment"))
        results.append(ally.anonymize(text, analysis_results=entities, report=False,
                                     operators=ally.settings_manager.get_anonymization_operators())["text"])
    assert results[0] == results[1]
    assert "jane@example.com" not in results[0]
