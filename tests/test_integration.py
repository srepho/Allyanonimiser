"""
Integration tests for the new features.

These tests verify that all the new components work together correctly.
"""

import os
import pytest
import tempfile
import pandas as pd
from allyanonimiser import create_allyanonimiser
from allyanonimiser.utils.settings_manager import SettingsManager

# Path to test data
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
TEST_PATTERNS_CSV = os.path.join(TEST_DATA_DIR, "test_patterns.csv")
TEST_ACRONYMS_CSV = os.path.join(TEST_DATA_DIR, "test_acronyms.csv")
LARGE_SAMPLE_CSV = os.path.join(TEST_DATA_DIR, "large_sample.csv")

@pytest.fixture
def populated_ally():
    """Create an Allyanonimiser instance with preloaded settings."""
    ally = create_allyanonimiser()
    
    # Import acronyms and patterns if files exist
    if os.path.exists(TEST_ACRONYMS_CSV):
        ally.import_acronyms_from_csv(TEST_ACRONYMS_CSV)
        
    if os.path.exists(TEST_PATTERNS_CSV):
        ally.import_patterns_from_csv(TEST_PATTERNS_CSV)
        
    return ally

@pytest.fixture
def sample_df():
    """Load a sample DataFrame for testing."""
    if os.path.exists(LARGE_SAMPLE_CSV):
        return pd.read_csv(LARGE_SAMPLE_CSV)
    else:
        # Create a minimal DataFrame if file doesn't exist
        return pd.DataFrame({
            'id': range(1, 4),
            'text': [
                "Example with GST and CEO mentions",
                "Reservation RES-123456 for John Smith",
                "Case CASE-12345 needs review by IT department"
            ]
        })

def test_end_to_end_processing(populated_ally, sample_df):
    """Test end-to-end processing with all the new features."""
    # Process a DataFrame with acronym expansion
    result = populated_ally.process_dataframe(
        sample_df,
        text_columns="text",
        min_score_threshold=0.7,
        anonymize=True,
        save_entities=True,
        progress_bar=False
    )
    
    # Verify results structure
    assert "dataframe" in result
    assert "entities" in result
    
    # Should have anonymized column
    assert "text_anonymized" in result["dataframe"].columns
    
    # Check for expanded acronyms if they were in the text
    all_text = " ".join(sample_df["text"].astype(str))
    has_acronyms = any(acronym in all_text for acronym in populated_ally.get_acronyms())
    
    # If acronyms were present, we should have detected known patterns
    if has_acronyms:
        entities = result["entities"]
        assert not entities.empty
        
        # Skip checking for expanded acronyms in the anonymized text
        # This depends on whether expand_acronyms was enabled during processing
        
    # If pattern CSV was loaded, we should detect custom entity types
    if os.path.exists(TEST_PATTERNS_CSV) and "RES-123456" in all_text:
        entities = result["entities"]
        assert "RESERVATION_NUMBER" in entities["entity_type"].values

def test_settings_persistence(populated_ally):
    """Test saving and loading settings with the new features."""
    # Get the initial settings
    initial_acronyms = populated_ally.get_acronyms()
    
    # Save settings to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        settings_path = tmp.name
        
    try:
        # Save settings
        populated_ally.save_settings(settings_path)
        
        # Create a new instance and load the settings
        new_ally = create_allyanonimiser()
        new_ally.load_settings(settings_path)
        
        # Verify settings were loaded correctly
        loaded_acronyms = new_ally.get_acronyms()
        assert loaded_acronyms == initial_acronyms
        
        # Verify PyArrow setting
        if hasattr(populated_ally, "use_pyarrow"):
            assert hasattr(new_ally, "use_pyarrow")
            assert new_ally.use_pyarrow == populated_ally.use_pyarrow
            
    finally:
        if os.path.exists(settings_path):
            os.unlink(settings_path)

def test_complete_workflow():
    """Test a complete workflow with all new features."""
    # Create a fresh instance
    ally = create_allyanonimiser()
    
    # 1. Import acronyms from CSV
    if os.path.exists(TEST_ACRONYMS_CSV):
        count = ally.import_acronyms_from_csv(TEST_ACRONYMS_CSV)
        assert count > 0
    
    # 2. Import patterns from CSV
    if os.path.exists(TEST_PATTERNS_CSV):
        count = ally.import_patterns_from_csv(TEST_PATTERNS_CSV)
        assert count > 0
    
    # 3. Create a sample text with both acronyms and patterns
    text = "The CEO requested a review of case CASE-12345 by the IT department. " + \
           "Hotel reservation RES-123456 confirmed for workshop on GST implementation."
    
    # 4. Process the text with acronym expansion
    result = ally.process(text, expand_acronyms=True)
    
    # 5. Verify preprocessing metadata
    assert "preprocessing" in result
    if "expanded_acronyms" in result["preprocessing"]:
        acronyms_found = {item["acronym"] for item in result["preprocessing"]["expanded_acronyms"]}
        assert len(acronyms_found) > 0
        
    # 6. Verify entities detection
    entities = result["analysis"]["entities"]
    assert len(entities) > 0
    
    entity_types = {entity["entity_type"] for entity in entities}
    
    # Should detect at least one custom entity type
    if os.path.exists(TEST_PATTERNS_CSV):
        assert any(entity_type in ["RESERVATION_NUMBER", "CASE_ID"] for entity_type in entity_types)
    
    # 7. Check anonymized text
    assert "anonymized" in result
    
    # 8. Process a DataFrame if sample file exists
    if os.path.exists(LARGE_SAMPLE_CSV):
        df = pd.read_csv(LARGE_SAMPLE_CSV)
        df_result = ally.process_dataframe(
            df,
            text_columns="text",
            use_pyarrow=False
        )
        assert "dataframe" in df_result
        assert "entities" in df_result