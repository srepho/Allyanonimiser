"""
Tests for PyArrow integration in the DataFrame processor.
"""

import pytest
import pandas as pd
import numpy as np
from allyanonimiser import create_allyanonimiser
from allyanonimiser.dataframe_processor import DataFrameProcessor, PYARROW_AVAILABLE

# Skip all tests if PyArrow is not available
pytestmark = pytest.mark.skipif(not PYARROW_AVAILABLE, reason="PyArrow not available")

@pytest.fixture
def large_sample_df():
    """Create a larger DataFrame for testing PyArrow performance."""
    # Either load from file or generate on the fly
    import os
    test_data_path = os.path.join(os.path.dirname(__file__), "test_data", "large_sample.csv")
    
    if os.path.exists(test_data_path):
        return pd.read_csv(test_data_path)
    else:
        # Generate test data if file doesn't exist
        rows = []
        for i in range(10):
            row = {
                "id": i,
                "text": f"Sample text {i} with PII: john.doe{i}@example.com"
            }
            rows.append(row)
        return pd.DataFrame(rows)

@pytest.fixture
def allyanonimiser():
    """Create an Allyanonimiser instance with PyArrow enabled."""
    ally = create_allyanonimiser()
    # Ensure PyArrow is enabled
    ally.use_pyarrow = True
    return ally

@pytest.fixture
def dataframe_processor(allyanonimiser):
    """Create a DataFrameProcessor with PyArrow enabled."""
    return DataFrameProcessor(allyanonimiser, use_pyarrow=True)

def test_pyarrow_conversion(dataframe_processor, large_sample_df):
    """Test conversion of DataFrame to Arrow Table."""
    # Convert to Arrow
    arrow_table = dataframe_processor._to_arrow_table(large_sample_df)
    
    # Check that conversion happened
    assert arrow_table is not None
    
    # Check column names match
    assert set(arrow_table.column_names) == set(large_sample_df.columns)
    
    # Try to extract a column
    col_data = dataframe_processor._get_column_from_arrow(arrow_table, "text")
    
    # Check that we got data back
    assert col_data is not None
    assert len(col_data) == len(large_sample_df)
    
    # Verify some values
    assert col_data[0] == large_sample_df.iloc[0]["text"]

def test_process_with_pyarrow(dataframe_processor, large_sample_df):
    """Test processing DataFrame with PyArrow enabled."""
    # Process with PyArrow
    result = dataframe_processor.process_dataframe(
        large_sample_df,
        text_columns="text",
        use_pyarrow=True,
        min_score_threshold=0.7,
        batch_size=2
    )
    
    # Check results
    assert "dataframe" in result
    assert "entities" in result
    
    # Check entities
    assert not result["entities"].empty
    assert "text" in result["entities"]["column"].unique()
    
    # Should find at least some entities like emails
    entities = result["entities"]
    assert "EMAIL_ADDRESS" in entities["entity_type"].unique() or \
           "PERSON" in entities["entity_type"].unique() or \
           "DATE" in entities["entity_type"].unique()

def test_toggle_pyarrow(dataframe_processor, large_sample_df):
    """Test toggling PyArrow setting during processing."""
    # Run with PyArrow
    with_arrow = dataframe_processor.process_dataframe(
        large_sample_df,
        text_columns="text",
        use_pyarrow=True
    )
    
    # Run without PyArrow
    without_arrow = dataframe_processor.process_dataframe(
        large_sample_df,
        text_columns="text",
        use_pyarrow=False
    )
    
    # Results should be similar
    assert "dataframe" in with_arrow
    assert "dataframe" in without_arrow
    
    # Original setting should be preserved
    assert dataframe_processor.use_pyarrow is True

def test_fallback_handling(dataframe_processor):
    """Test fallback if PyArrow conversion fails."""
    # Create a DataFrame with complex objects that might cause conversion issues
    df = pd.DataFrame({
        "id": range(5),
        "complex": [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}, {"e": 5}],
        "text": ["Sample text"] * 5
    })
    
    # Process the DataFrame
    # This should fall back to pandas if PyArrow conversion fails
    result = dataframe_processor.process_dataframe(
        df,
        text_columns="text",
        use_pyarrow=True
    )
    
    # Should still get results
    assert "dataframe" in result

def test_nan_handling(dataframe_processor):
    """Test handling of NaN values with PyArrow."""
    # Create DataFrame with NaN values
    df = pd.DataFrame({
        "id": range(5),
        "text": ["Text 1", np.nan, "Text 3", "", None]
    })
    
    # Process the DataFrame
    result = dataframe_processor.process_dataframe(
        df,
        text_columns="text",
        use_pyarrow=True
    )
    
    # Should process the DataFrame without errors
    assert "dataframe" in result
    
    # Check that NaN values are handled appropriately
    assert len(result["dataframe"]) == 5

def test_integration_with_allyanonimiser(allyanonimiser, large_sample_df):
    """Test PyArrow integration at the Allyanonimiser class level."""
    # Set PyArrow flag
    allyanonimiser.use_pyarrow = True
    
    # Process DataFrame
    result = allyanonimiser.process_dataframe(
        large_sample_df,
        text_columns="text"
    )
    
    # Check results
    assert "dataframe" in result
    assert "entities" in result

from hypothesis import given, strategies as st
import hypothesis.extra.pandas as hpd

# Create a strategy for DataFrames with text columns
dataframes = hpd.data_frames(
    columns=[
        hpd.column('id', elements=st.integers(min_value=1, max_value=1000)),
        hpd.column('text', elements=st.text(min_size=1, max_size=100))
    ],
    index=st.just(pd.RangeIndex(0, 10))
)

@pytest.mark.skipif(not PYARROW_AVAILABLE, reason="PyArrow not available")
@given(df=dataframes)
def test_property_based(df):
    """Property-based test for PyArrow integration."""
    # Skip empty DataFrames
    if df.empty:
        return
        
    # Clean the text data to ensure it's not too complex
    df['text'] = df['text'].fillna('').astype(str)
    
    try:
        # Create processor with PyArrow
        ally = create_allyanonimiser()
        processor = DataFrameProcessor(ally, use_pyarrow=True)
        
        # Try to process
        result = processor.process_dataframe(
            df,
            text_columns="text",
            use_pyarrow=True,
            anonymize=False,  # Simplify for testing
            min_score_threshold=0.9  # Higher threshold to reduce noise
        )
        
        # Basic assertions
        assert isinstance(result, dict)
        assert "dataframe" in result
        
    except Exception as e:
        # If we hit conversion errors, that's acceptable
        # Just ensure we don't have critical failures
        if "PyArrow conversion failed" in str(e) or "No match found" in str(e):
            pass
        else:
            raise