"""
Tests for PyArrow integration in the DataFrame processor.

The v3 processor no longer exposes ``_to_arrow_table`` / ``_get_column_from_arrow``.
Instead, ``use_pyarrow=True`` causes object-dtype string columns to be converted
to ``string[pyarrow]`` via ``_use_arrow_strings`` before processing. These tests
exercise that current behavior.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, strategies as st
import hypothesis.extra.pandas as hpd

from allyanonimiser import create_allyanonimiser
from allyanonimiser.io.dataframe_processor import (
    PYARROW_AVAILABLE,
    DataFrameProcessor,
    _use_arrow_strings,
)

pytestmark = pytest.mark.skipif(not PYARROW_AVAILABLE, reason="PyArrow not available")


@pytest.fixture
def large_sample_df():
    rows = [
        {"id": i, "text": f"Sample text {i} with PII: john.doe{i}@example.com"}
        for i in range(10)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def allyanonimiser():
    ally = create_allyanonimiser()
    ally.use_pyarrow = True
    return ally


@pytest.fixture
def dataframe_processor(allyanonimiser):
    return DataFrameProcessor(allyanonimiser, use_pyarrow=True)


def test_use_arrow_strings_converts_object_columns():
    """String object columns should become string[pyarrow]."""
    df = pd.DataFrame({"text": ["a", "b", "c"]}, dtype="object")
    assert df["text"].dtype == "object"
    converted = _use_arrow_strings(df)
    assert str(converted["text"].dtype) == "string"


def test_process_with_pyarrow(dataframe_processor, large_sample_df):
    result = dataframe_processor.process_dataframe(
        large_sample_df,
        text_columns="text",
        use_pyarrow=True,
        min_score_threshold=0.7,
        batch_size=2,
    )

    assert "dataframe" in result
    assert "entities" in result
    assert not result["entities"].empty
    assert "text" in result["entities"]["column"].unique()

    entity_types = set(result["entities"]["entity_type"].unique())
    assert entity_types & {"EMAIL_ADDRESS", "PERSON", "DATE"}


def test_toggle_pyarrow(dataframe_processor, large_sample_df):
    with_arrow = dataframe_processor.process_dataframe(
        large_sample_df, text_columns="text", use_pyarrow=True
    )
    without_arrow = dataframe_processor.process_dataframe(
        large_sample_df, text_columns="text", use_pyarrow=False
    )

    assert "dataframe" in with_arrow
    assert "dataframe" in without_arrow
    # Instance flag should not have been mutated by the per-call overrides
    assert dataframe_processor.use_pyarrow is True


def test_mixed_type_column_falls_back_gracefully(dataframe_processor):
    """Non-convertible columns should not break processing."""
    df = pd.DataFrame(
        {
            "id": range(5),
            "complex": [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}, {"e": 5}],
            "text": ["Sample text"] * 5,
        }
    )

    result = dataframe_processor.process_dataframe(
        df, text_columns="text", use_pyarrow=True
    )
    assert "dataframe" in result


def test_nan_handling(dataframe_processor):
    df = pd.DataFrame(
        {"id": range(5), "text": ["Text 1", np.nan, "Text 3", "", None]}
    )

    result = dataframe_processor.process_dataframe(
        df, text_columns="text", use_pyarrow=True
    )

    assert "dataframe" in result
    assert len(result["dataframe"]) == 5


def test_missing_column_raises(dataframe_processor, large_sample_df):
    """Regression: missing columns must raise, not silently skip."""
    with pytest.raises(ValueError, match="not found"):
        dataframe_processor.process_dataframe(
            large_sample_df, text_columns="does_not_exist"
        )


def test_integration_with_allyanonimiser(allyanonimiser, large_sample_df):
    allyanonimiser.use_pyarrow = True
    result = allyanonimiser.process_dataframe(
        large_sample_df, text_columns="text"
    )
    assert "dataframe" in result
    assert "entities" in result


dataframes = hpd.data_frames(
    columns=[
        hpd.column("id", elements=st.integers(min_value=1, max_value=1000)),
        hpd.column("text", elements=st.text(min_size=1, max_size=100)),
    ],
    index=st.just(pd.RangeIndex(0, 10)),
)


@given(df=dataframes)
def test_property_based(df):
    if df.empty:
        return

    df["text"] = df["text"].fillna("").astype(str)

    ally = create_allyanonimiser()
    processor = DataFrameProcessor(ally, use_pyarrow=True)
    result = processor.process_dataframe(
        df,
        text_columns="text",
        use_pyarrow=True,
        anonymize=False,
        min_score_threshold=0.9,
    )
    assert isinstance(result, dict)
    assert "dataframe" in result
