"""Regressions for defects reproduced in the October 2026 design review.

Each test states the invariant it protects. All run pattern-only so they are
independent of which spaCy model is installed.
"""
import pandas as pd
import pytest

from allyanonimiser import EnhancedAnalyzer, create_allyanonimiser
from allyanonimiser.core.pattern_manager import CustomPatternDefinition
from allyanonimiser.reporting import ReportingManager

TEXT = "Send to jane.citizen@example.com today."


@pytest.fixture
def ally():
    return create_allyanonimiser(spacy_model=None)


# --- Cached results are isolated from callers and from per-call options ---

def test_caller_mutation_does_not_change_cached_results(ally):
    """Invariant: editing a returned result never changes a later call's output."""
    first = ally.analyze(TEXT)
    assert first
    expected = [(r.entity_type, r.start, r.end, r.score) for r in first]
    for r in first:
        r.score = 0.01
        r.entity_type = "TAMPERED"
    again = ally.analyze(TEXT)
    assert [(r.entity_type, r.start, r.end, r.score) for r in again] == expected


def test_score_adjustment_does_not_leak_into_later_calls(ally):
    """Invariant: a negative adjustment on one call leaves default calls unchanged."""
    baseline = [(r.entity_type, r.score) for r in ally.analyze(TEXT)]
    adjusted = ally.analyze(TEXT, score_adjustment={"EMAIL_ADDRESS": -0.5},
                            min_score_threshold=0.0)
    assert any(r.score < 0.7 for r in adjusted if r.entity_type == "EMAIL_ADDRESS")
    assert [(r.entity_type, r.score) for r in ally.analyze(TEXT)] == baseline


def test_repeated_calls_do_not_accumulate_context_boosts():
    """Invariant: the Nth call returns the same scores as the first."""
    analyzer = EnhancedAnalyzer(spacy_model=None)
    ally = create_allyanonimiser(spacy_model=None)
    analyzer.patterns = ally.analyzer.patterns
    text = "TFN: 123 456 782"
    first = [(r.entity_type, r.score) for r in analyzer.analyze(text, min_score_threshold=0.0)]
    for threshold in (0.0, 0.1, 0.2, 0.3):  # distinct keys force pattern-cache reuse
        analyzer.analyze(text, min_score_threshold=threshold)
    assert [(r.entity_type, r.score) for r in analyzer.analyze(text, min_score_threshold=0.0)] == first


# --- Cache size limits are enforced at every insertion ---

@pytest.mark.parametrize("limit", [1, 2, 3, 10])
def test_cache_never_exceeds_limit(limit):
    """Invariant: no cache holds more than max_cache_size entries."""
    analyzer = EnhancedAnalyzer(spacy_model=None, max_cache_size=limit)
    for i in range(limit * 3 + 1):
        analyzer.analyze(f"Contact user{i}@example.com")
        assert len(analyzer._result_cache) <= limit
        assert len(analyzer._pattern_result_cache) <= limit
        assert len(analyzer._spacy_result_cache) <= limit


def test_cache_limit_keeps_most_recent_entry():
    analyzer = EnhancedAnalyzer(spacy_model=None, max_cache_size=1)
    analyzer.analyze("first@example.com")
    analyzer.analyze("second@example.com")
    assert list(analyzer._pattern_result_cache) == ["second@example.com"]


@pytest.mark.parametrize("bad", [0, -1, 1.5, "10", True])
def test_invalid_cache_size_rejected(bad):
    with pytest.raises(ValueError, match="max_cache_size"):
        EnhancedAnalyzer(spacy_model=None, max_cache_size=bad)


# --- Configured pattern scores are honoured ---

@pytest.mark.parametrize("score", [0.2, 0.5, 0.95])
def test_custom_pattern_score_is_reported(ally, score):
    ally.add_pattern(CustomPatternDefinition(
        entity_type="WIDGET_ID", patterns=[r"XQ#\d{8}\b"], name="widget", score=score,
    ))
    results = [r for r in ally.analyze("Ref XQ#77889911 here", min_score_threshold=0.0)
               if r.entity_type == "WIDGET_ID"]
    assert [r.score for r in results] == [score]


def test_low_score_pattern_filtered_by_default_threshold(ally):
    """A 0.2 pattern sits below the 0.7 default and must not be masked."""
    ally.add_pattern(CustomPatternDefinition(
        entity_type="WIDGET_ID", patterns=[r"XQ#\d{8}\b"], name="widget", score=0.2,
    ))
    assert "XQ#77889911" in ally.anonymize("Ref XQ#77889911 here")["text"]


def test_pattern_without_score_defaults_to_085(ally):
    pattern = CustomPatternDefinition(entity_type="WIDGET_ID", patterns=[r"XQ#\d{8}\b"])
    pattern.score = None
    ally.add_pattern(pattern)
    results = [r for r in ally.analyze("Ref XQ#77889911") if r.entity_type == "WIDGET_ID"]
    assert [r.score for r in results] == [0.85]


# --- DataFrame rows are addressed by position, not index label ---

@pytest.mark.parametrize("index", [[0, 0], ["a", "a"], [5, 3]])
def test_duplicate_or_unordered_index_keeps_row_outputs(ally, index):
    """Invariant: each row's anonymized output derives from that row's input."""
    df = pd.DataFrame({"t": ["Call alice@x.com now", "No PII here"]}, index=index)
    out = ally.process_dataframe(df, text_columns=["t"], progress_bar=False)["dataframe"]
    assert list(out.index) == index
    assert out["t_anonymized"].tolist() == ["Call <EMAIL_ADDRESS> now", "No PII here"]
    assert out["t"].tolist() == df["t"].tolist()


def test_duplicate_index_with_nulls(ally):
    df = pd.DataFrame({"t": [None, "Call bob@y.com", None]}, index=[1, 1, 1])
    out = ally.process_dataframe(df, text_columns=["t"], progress_bar=False)
    values = out["dataframe"]["t_anonymized"].tolist()
    assert pd.isna(values[0]) and pd.isna(values[2])
    assert values[1] == "Call <EMAIL_ADDRESS>"
    assert out["entities"]["row_index"].tolist() == [1]


def test_entirely_null_column_still_gets_output_column(ally):
    df = pd.DataFrame({"t": [None, None]})
    out = ally.process_dataframe(df, text_columns=["t"], progress_bar=False)["dataframe"]
    assert "t_anonymized" in out.columns


def test_anonymize_column_duplicate_index(ally):
    df = pd.DataFrame({"t": ["Call alice@x.com", "plain"]}, index=[0, 0])
    out = ally._make_df_processor().anonymize_column(df, "t")
    assert out["t_anonymized"].tolist() == ["Call <EMAIL_ADDRESS>", "plain"]


# --- Reports belong to their instance ---

def test_instances_do_not_share_reports():
    first = create_allyanonimiser(spacy_model=None)
    second = create_allyanonimiser(spacy_model=None)
    first.start_new_report("only-first")
    first.anonymize(TEXT, report=True)
    assert second.get_report() is None
    assert second.get_report("only-first") is None
    assert first.get_report() is not first.report_manager.get_report("missing")


def test_reports_can_be_shared_explicitly():
    shared = ReportingManager()
    first = create_allyanonimiser(spacy_model=None, report_manager=shared)
    second = create_allyanonimiser(spacy_model=None, report_manager=shared)
    first.start_new_report("joint")
    assert second.get_report() is first.get_report()


def test_default_anonymize_report_does_not_touch_module_singleton():
    from allyanonimiser.reporting import report_manager as global_manager
    before = global_manager.get_current_report()
    create_allyanonimiser(spacy_model=None).anonymize(TEXT, report=True)
    assert global_manager.get_current_report() is before
