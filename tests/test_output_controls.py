"""Operational controls must cover real outputs, retained caches, and model failure."""
import json
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from allyanonimiser import Allyanonimiser, EnhancedAnalyzer, create_allyanonimiser
from allyanonimiser.core import analyzer as analyzer_module
from allyanonimiser.reporting import report_manager

SENTINEL = "sentinel.private@example.com"
TEXT = f"Contact {SENTINEL} for assistance."


@pytest.fixture
def minimal():
    return create_allyanonimiser(spacy_model=None, minimal_output=True)


def assert_clean(value):
    assert SENTINEL not in str(value)


def test_text_outputs_and_caches(minimal):
    previous = report_manager.start_new_report()
    before = repr(previous.__dict__)
    result = minimal.anonymize(TEXT, report=True)
    assert "original_text" not in result
    assert result["items"]
    assert all("original" not in item for item in result["items"])
    assert_clean(result)
    result = minimal.process(TEXT)
    assert result["statistics"]["entity_count"] > 0
    assert "segments" not in result and "structured_data" not in result
    assert_clean(result)
    assert_clean(minimal.batch_process([TEXT, TEXT]))
    assert all(e.text is None for e in minimal.analyze(TEXT))
    assert not minimal.analyzer.enable_caching
    assert not minimal.analyzer._result_cache
    assert not minimal.analyzer._pattern_result_cache
    assert not minimal.analyzer._spacy_result_cache
    assert repr(previous.__dict__) == before
    assert minimal.get_report() is None
    assert minimal.start_new_report() is None
    assert minimal.finalize_report() == {"error": "No active report"}


def test_existing_analyzer_cache_cleared():
    analyzer = EnhancedAnalyzer(spacy_model=None)
    analyzer.analyze(TEXT)
    assert analyzer._result_cache
    ally = Allyanonimiser(analyzer=analyzer, minimal_output=True)
    assert not ally.analyzer._result_cache
    assert not ally.analyzer.enable_caching


def test_dataframe_outputs(minimal):
    df = pd.DataFrame({"notes": [TEXT, None], "id": [1, 2]})
    result = minimal.process_dataframe(df, text_columns=["notes"], progress_bar=False)
    assert "notes" not in result["dataframe"]
    assert "text" not in result["entities"]
    assert_clean(result)
    assert_clean(minimal.detect_pii_in_dataframe(df, "notes"))
    assert_clean(minimal.anonymize_dataframe(df, "notes"))
    assert_clean(minimal.anonymize_dataframe(df, "notes", output_column="notes"))
    assert df.loc[0, "notes"] == TEXT


@pytest.mark.parametrize("empty", [False, True])
def test_stream_files(minimal, tmp_path, empty):
    pytest.importorskip("polars")
    from allyanonimiser import StreamProcessor
    source = tmp_path / "source.csv"
    output = tmp_path / "output.csv"
    entities = tmp_path / "entities.csv"
    pd.DataFrame({"notes": [] if empty else [TEXT, TEXT], "id": [] if empty else [1, 2]}).to_csv(source, index=False)
    processor = StreamProcessor(minimal, chunk_size=1)
    result = processor.process_large_file(str(source), ["notes"], str(output), entities_output_path=str(entities), progress_bar=False)
    assert result["total_rows_processed"] == (0 if empty else 2)
    assert_clean(output.read_text())
    assert_clean(entities.read_text())
    assert "notes" not in pd.read_csv(output).columns
    assert "text" not in pd.read_csv(entities).columns
    for chunk in processor.stream_from_file(str(source), ["notes"], progress_bar=False):
        assert_clean(chunk)


def test_csv_and_text_file_helpers(minimal, tmp_path):
    source = tmp_path / "source.csv"
    pd.DataFrame({"notes": [TEXT]}).to_csv(source, index=False)
    assert_clean(minimal.preview_csv_changes(str(source), columns=["notes"]))
    for method in ("process_csv_file", "stream_process_csv"):
        out = tmp_path / f"{method}.csv"
        if method == "process_csv_file":
            minimal.process_csv_file(str(source), str(out), columns_to_anonymize=["notes"])
        else:
            minimal.stream_process_csv(str(source), str(out), columns=["notes"], chunk_size=1)
        assert_clean(out.read_text())
    text = tmp_path / "input.txt"
    text.write_text(TEXT)
    result = minimal.process_files([str(text)], output_dir=str(tmp_path / "results"), save_results=True)
    assert_clean(result)
    assert "report" not in result
    for path in (tmp_path / "results").iterdir():
        assert_clean(path.read_text())


@pytest.mark.parametrize("extension", ["json", "yaml"])
def test_controls_roundtrip_and_overrides(minimal, tmp_path, extension):
    if extension == "yaml":
        pytest.importorskip("yaml")
    path = tmp_path / f"config.{extension}"
    assert minimal.export_config(str(path))
    restored = create_allyanonimiser(settings_path=str(path), enable_caching=True)
    assert restored.minimal_output and not restored.analyzer.enable_caching
    assert_clean(restored.process(TEXT))
    normal = create_allyanonimiser(settings_path=str(path), minimal_output=False, enable_caching=True)
    assert not normal.minimal_output and normal.analyzer.enable_caching
    assert normal.anonymize(TEXT, report=False)["original_text"] == TEXT


def fake_model(ner=True):
    return SimpleNamespace(pipe_names=["ner"] if ner else [])


@pytest.mark.parametrize("available", ["requested", "fallback", "neither", "no_ner"])
def test_strict_model_requires_requested_ner(available):
    def loader(name):
        if available == "requested" and name == "requested_model":
            return fake_model()
        if available == "no_ner" and name == "requested_model":
            return fake_model(False)
        if available == "fallback" and name == "en_core_web_lg":
            return fake_model()
        raise OSError("missing")
    with patch.object(analyzer_module.spacy, "load", side_effect=loader) as load:
        if available == "requested":
            ally = create_allyanonimiser(spacy_model="requested_model", require_spacy_model=True)
            assert ally.check_spacy_status()["has_ner"]
        else:
            with pytest.raises(RuntimeError, match="Required spaCy NER model"):
                create_allyanonimiser(spacy_model="requested_model", require_spacy_model=True)
        assert load.call_count == 1


def test_pattern_only_and_strict_config(tmp_path):
    with patch.object(analyzer_module.spacy, "load") as load:
        assert not create_allyanonimiser(spacy_model=None).analyzer.use_spacy
        with pytest.raises(ValueError, match="named spaCy model"):
            create_allyanonimiser(spacy_model=None, require_spacy_model=True)
        load.assert_not_called()
    path = tmp_path / "strict.json"
    with patch.object(analyzer_module.spacy, "load", return_value=fake_model()):
        ally = create_allyanonimiser(spacy_model="requested_model", require_spacy_model=True)
        assert ally.export_config(str(path))
    assert json.loads(path.read_text())["analyzer"]["require_spacy_model"]
    with patch.object(analyzer_module.spacy, "load", side_effect=OSError("missing")):
        with pytest.raises(RuntimeError, match="Required spaCy"):
            create_allyanonimiser(settings_path=str(path))


def test_default_output_unchanged():
    ally = create_allyanonimiser(spacy_model=None)
    result = ally.anonymize(TEXT, report=False)
    assert result["original_text"] == TEXT
    assert any(item["original"] == SENTINEL for item in result["items"])
    assert SENTINEL in str(ally.process(TEXT, report=False))


def test_reload_clears_existing_caches(minimal, tmp_path):
    path = tmp_path / "minimal.json"
    assert minimal.export_config(str(path))
    ally = create_allyanonimiser(spacy_model=None)
    ally.analyze(TEXT)
    assert ally.analyzer._result_cache
    assert ally.load_settings(str(path))
    assert ally.minimal_output and not ally.analyzer.enable_caching
    assert not ally.analyzer._result_cache
    assert_clean(ally.anonymize(TEXT))


def test_minimal_empty_and_detection_only_dataframes(minimal):
    for values in ([], [None], [TEXT]):
        result = minimal.process_dataframe(pd.DataFrame({"notes": values}), text_columns="notes", anonymize=False, progress_bar=False)
        assert len(result["dataframe"]) == len(values)
        assert "notes" not in result["dataframe"].columns
        assert "text" not in result["entities"].columns
        assert_clean(result)


def test_minimal_stream_rejects_detection_only_before_writing(minimal, tmp_path):
    pytest.importorskip("polars")
    from allyanonimiser import StreamProcessor
    source, output = tmp_path / "source.csv", tmp_path / "output.csv"
    pd.DataFrame({"notes": [TEXT]}).to_csv(source, index=False)
    output.write_text("existing output")
    with pytest.raises(ValueError, match="requires anonymize=True"):
        list(StreamProcessor(minimal).stream_from_file(str(source), ["notes"], anonymize=False, output_path=str(output)))
    assert output.read_text() == "existing output"


def test_strict_ignores_cached_fallback():
    fallback = fake_model()
    fallback._allyanonimiser_loaded_as = "en_core_web_lg"
    with patch.dict(analyzer_module._spacy_model_cache, {("requested_model", "en_core_web_lg"): fallback}):
        with patch.object(analyzer_module.spacy, "load", side_effect=OSError("missing")):
            with pytest.raises(RuntimeError, match="Required spaCy"):
                EnhancedAnalyzer(spacy_model="requested_model", require_spacy_model=True)


@pytest.mark.parametrize("available", ["requested", "fallback", "neither"])
def test_permissive_loading_still_falls_back(available):
    def loader(name):
        if available == "requested" or (available == "fallback" and name == "en_core_web_lg"):
            return fake_model()
        raise OSError("missing")
    with patch.dict(analyzer_module._spacy_model_cache, {}, clear=True):
        with patch.object(analyzer_module.spacy, "load", side_effect=loader):
            with patch.object(analyzer_module.spacy, "blank", return_value=fake_model(False)):
                analyzer = EnhancedAnalyzer(spacy_model="requested_model")
    assert analyzer.use_spacy == (available != "neither")
    assert analyzer.spacy_model_loaded == {"requested": "requested_model", "fallback": "en_core_web_lg", "neither": "blank_en"}[available]


@pytest.mark.parametrize("values", [[], [None]])
def test_minimal_dataframe_keeps_empty_output_schema(minimal, values):
    result = minimal.process_dataframe(pd.DataFrame({"notes": values}), text_columns="notes", progress_bar=False)
    assert list(result["dataframe"].columns) == ["notes_anonymized"]
    assert len(result["dataframe"]) == len(values)
    assert result["dataframe"]["notes_anonymized"].isna().all()


def test_strict_settings_reload_preserves_requested_model(tmp_path):
    path = tmp_path / "strict.json"
    path.write_text(json.dumps({"analyzer": {"require_spacy_model": True}}))
    with patch.object(analyzer_module.spacy, "load", return_value=fake_model()) as load:
        ally = create_allyanonimiser(spacy_model="custom_model")
        assert ally.load_settings(str(path))
        assert ally.analyzer.require_spacy_model
        assert ally.analyzer.spacy_model_requested == "custom_model"
        assert load.call_args.args == ("custom_model",)
