"""Replacement uses detections from the same prepared text and threshold."""
from unittest.mock import patch

import pandas as pd
import pytest

from allyanonimiser import create_allyanonimiser
from allyanonimiser.io.dataframe_processor import DataFrameProcessor


@pytest.mark.parametrize("threshold", [0.0, 1.0])
@pytest.mark.parametrize("expand", [False, True])
def test_dataframe_threshold_and_preprocessing(threshold, expand):
    ally = create_allyanonimiser(spacy_model=None)
    ally.set_acronyms({"CONTACT": "Email"})
    text = "CONTACT jane@example.com"
    prepared, _ = ally._preprocess(text, expand)
    expected = ally.analyze(prepared, min_score_threshold=threshold)
    replacement = ally.anonymize(prepared, analysis_results=expected, report=False)["text"]
    with patch.object(ally.analyzer, "analyze", wraps=ally.analyzer.analyze) as analyze:
        result = DataFrameProcessor(ally).process_dataframe(
            pd.DataFrame({"note": [text, None, text]}), "note",
            min_score_threshold=threshold, expand_acronyms=expand, progress_bar=False,
        )
        assert analyze.call_count == 2
    assert result["dataframe"]["note_anonymized"].iloc[[0, 2]].tolist() == [replacement] * 2
    assert len(result["entities"]) == 2 * len(expected)
    for entity in result["entities"].to_dict("records"):
        assert prepared[entity["start"]:entity["end"]] == entity["text"]
