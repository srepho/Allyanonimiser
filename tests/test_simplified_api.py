"""
Tests for the simplified API functionality.
"""
import pytest
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig


def test_configuration_objects():
    """Test that configuration objects work properly."""
    ally = create_allyanonimiser()
    
    # Create configuration objects
    analysis_config = AnalysisConfig(
        language="en",
        active_entity_types=["PERSON", "EMAIL_ADDRESS"],
        min_score_threshold=0.8,
        expand_acronyms=False
    )
    
    anonymization_config = AnonymizationConfig(
        operators={
            "PERSON": "replace",
            "EMAIL_ADDRESS": "mask"
        },
        age_bracket_size=10,
        keep_postcode=True
    )
    
    # Test with configuration objects
    text = "John Smith (john.smith@example.com) sent an email."
    result = ally.process(
        text=text,
        analysis_config=analysis_config,
        anonymization_config=anonymization_config
    )
    
    # Check that the configuration was properly applied
    assert "<PERSON>" in result["anonymized"]
    assert "**********************" in result["anonymized"]
    
    # Verify the entities were detected with the right threshold
    entities = [e["entity_type"] for e in result["analysis"]["entities"]]
    assert "PERSON" in entities
    assert "EMAIL_ADDRESS" in entities


def test_manage_acronyms():
    """Test the unified acronym management method."""
    ally = create_allyanonimiser()
    
    # Add acronyms
    ally.manage_acronyms(
        action="add",
        data={"TPD": "Total and Permanent Disability", "CTP": "Compulsory Third Party"}
    )
    
    # Get acronyms
    acronyms = ally.manage_acronyms(action="get")
    assert "TPD" in acronyms
    assert acronyms["TPD"] == "Total and Permanent Disability"
    
    # Remove acronyms
    ally.manage_acronyms(action="remove", data=["TPD"])
    
    # Verify removal
    updated_acronyms = ally.manage_acronyms(action="get")
    assert "TPD" not in updated_acronyms
    assert "CTP" in updated_acronyms


def test_manage_patterns():
    """Test the unified pattern management method."""
    ally = create_allyanonimiser()
    
    # Create a pattern from examples
    pattern = ally.manage_patterns(
        action="create_from_examples",
        entity_type="TEST_ID",
        examples=["TEST-123", "TEST-456"],
        generalization_level="medium"
    )
    
    # Test the pattern
    text = "Reference number: TEST-789"
    result = ally.process(text)
    
    # Check if pattern was detected
    entities = [e["entity_type"] for e in result["analysis"]["entities"]]
    assert "TEST_ID" in entities


def test_process_dataframe(mocker):
    """Test the unified DataFrame processing method."""
    # Mock pandas DataFrame and DataFrameProcessor for testing without dependencies
    pd_mock = mocker.patch("allyanonimiser.dataframe_processor.pd")
    processor_mock = mocker.patch("allyanonimiser.dataframe_processor.DataFrameProcessor")
    
    # Create instance
    ally = create_allyanonimiser()
    
    # Test detect operation
    ally.process_dataframe(
        df="mock_df",
        column="notes",
        operation="detect"
    )
    processor_mock.return_value.detect_pii.assert_called_once()
    
    # Test anonymize operation
    ally.process_dataframe(
        df="mock_df",
        column="notes",
        operation="anonymize"
    )
    processor_mock.return_value.anonymize_column.assert_called_once()
    
    # Test process operation
    ally.process_dataframe(
        df="mock_df",
        text_columns="notes",
        operation="process"
    )
    processor_mock.return_value.process_dataframe.assert_called_once()