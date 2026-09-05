"""Real CSV regressions for bounded streaming and replacement parity."""
import pandas as pd
import pytest

from allyanonimiser import create_allyanonimiser
from allyanonimiser.io.stream_processor import StreamProcessor

pl = pytest.importorskip("polars")


@pytest.fixture
def processor():
    return StreamProcessor(create_allyanonimiser(spacy_model=None), chunk_size=5)


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "input.csv"
    pl.DataFrame({"id": [f"{i:04}" for i in range(23)],
                  "note": [f'Email person{i}@example.com, "hello"\nnext line' for i in range(23)],
                  "other": [None] * 23}).write_csv(path)
    return path


@pytest.mark.parametrize("save_entities", [True, False])
@pytest.mark.parametrize("options", [None, {"infer_schema_length": 0}])
def test_real_file(processor, source, tmp_path, save_entities, options):
    output = tmp_path / "output.csv"
    result = processor.process_large_file(source, ["note", "other"], output,
                                         save_entities=save_entities, csv_options=options,
                                         active_entity_types=["EMAIL_ADDRESS"], progress_bar=False)
    assert result["total_rows_processed"] == 23
    assert result["total_entities_detected"] == 23
    df = pl.read_csv(output, infer_schema_length=0)
    assert df["id"].to_list() == [f"{i:04}" for i in range(23)]
    assert df["note_anonymized"].to_list() == ['Email <EMAIL_ADDRESS>, "hello"\nnext line'] * 23
    assert df["other_anonymized"].null_count() == 23
    if save_entities:
        entities = pd.read_csv(result["entities_file"])
        assert entities.row_index.tolist() == list(range(23))


def test_chunk_sizes(processor, source):
    chunks = list(processor.stream_from_file(source, "note", progress_bar=False))
    assert [c["row_count"] for c in chunks] == [5, 5, 5, 5, 3]
    assert sum(len(c["dataframe"]) for c in chunks) == 23


@pytest.mark.parametrize("rows", [[], ["hello", "world"]])
def test_no_entities_and_relative_output(processor, tmp_path, monkeypatch, rows):
    monkeypatch.chdir(tmp_path)
    pl.DataFrame({"note": rows}, schema={"note": pl.String}).write_csv("input.csv")
    result = processor.process_large_file("input.csv", "note", "out.csv", progress_bar=False)
    assert result["total_rows_processed"] == len(rows)
    assert result["total_entities_detected"] == 0
    assert pl.read_csv("out.csv").columns == ["note", "note_anonymized"]
    assert pd.read_csv(result["entities_file"]).empty


@pytest.mark.parametrize("size", [0, -1, True, 1.5])
def test_invalid_chunk_size(processor, source, size):
    with pytest.raises(ValueError, match="positive integer"):
        list(processor.stream_from_file(source, "note", chunk_size=size))


def test_path_collisions(processor, source, tmp_path):
    before = source.read_bytes()
    with pytest.raises(ValueError, match="distinct"):
        processor.process_large_file(source, "note", source, progress_bar=False)
    with pytest.raises(ValueError, match="distinct"):
        processor.process_large_file(source, "note", tmp_path / "out.csv",
                                     entities_output_path=source, progress_bar=False)
    assert source.read_bytes() == before


def test_missing_column(processor, source):
    with pytest.raises(ValueError, match="not found in CSV file"):
        list(processor.stream_from_file(source, "absent", progress_bar=False))


@pytest.mark.parametrize("threshold", [0.0, 1.0])
def test_threshold_parity(processor, threshold):
    text = "Email jane@example.com"
    expected = processor.ally.analyze(text, min_score_threshold=threshold)
    result = processor._process_chunk(pl.DataFrame({"note": [text]}), ["note"],
                                      min_score_threshold=threshold)
    replacement = processor.ally.anonymize(text, analysis_results=expected)["text"]
    assert result["dataframe"]["note_anonymized"][0] == replacement
    assert len(result["entities"]) == len(expected)


def test_separator_and_row_limit(processor, tmp_path):
    path = tmp_path / "semi.csv"
    path.write_text('id;note\n001;"a@example.com\nhello"\n002;ok\n003;skip\n')
    chunks = list(processor.stream_from_file(path, "note", progress_bar=False,
                                            csv_options={"separator": ";", "n_rows": 2}))
    assert sum(c["row_count"] for c in chunks) == 2
    assert chunks[0]["dataframe"]["id"].to_list() == ["001", "002"]


def test_malformed_csv(processor, tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("note,id\nhello,1,extra\n")
    with pytest.raises(pl.exceptions.ComputeError):
        list(processor.stream_from_file(path, "note", progress_bar=False))


def test_early_close_releases_output(processor, source, tmp_path, monkeypatch):
    import builtins

    opened = []
    real_open = builtins.open

    def track_open(*args, **kwargs):
        handle = real_open(*args, **kwargs)
        opened.append(handle)
        return handle

    monkeypatch.setitem(StreamProcessor.stream_from_file.__globals__, "open", track_open)
    stream = processor.stream_from_file(source, "note", output_path=tmp_path / "out.csv",
                                        progress_bar=False)
    assert next(stream)["row_count"] == 5
    stream.close()
    assert opened and all(handle.closed for handle in opened)


def test_missing_polars(processor, monkeypatch):
    monkeypatch.setitem(StreamProcessor._check_polars_available.__globals__, "POLARS_AVAILABLE", False)
    with pytest.raises(ImportError, match="Polars is required"):
        list(processor.stream_from_file("unused.csv", "note"))


def test_stream_does_not_grow_report(processor, source):
    from allyanonimiser.allyanonimiser import report_manager

    report = report_manager.get_current_report()
    before = repr(report.__dict__) if report else None
    list(processor.stream_from_file(source, "note", progress_bar=False))
    after = report_manager.get_current_report()
    assert (repr(after.__dict__) if after else None) == before
