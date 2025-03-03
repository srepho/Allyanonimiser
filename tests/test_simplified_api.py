"""
Tests for the simplified API functionality.

This test module covers the main features of the simplified API,
including configuration objects, acronym management, pattern management,
DataFrame processing, and custom operators.
"""
import pytest
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig
from allyanonimiser.pattern_manager import CustomPatternDefinition


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

def test_configuration_object_inheritance():
    """Test that configuration objects correctly override individual parameters."""
    ally = create_allyanonimiser()
    
    # Create a text with multiple entity types
    text = """
    John Smith (DOB: 15/06/1980)
    Phone: 0412 345 678
    Email: john.smith@example.com
    Address: 123 Main Street, Sydney NSW 2000
    """
    
    # Test that config values override direct parameters
    result1 = ally.process(
        text=text,
        active_entity_types=["PERSON"], # Should be overridden
        analysis_config=AnalysisConfig(
            active_entity_types=["EMAIL_ADDRESS", "PHONE_NUMBER"]
        )
    )
    
    # Verify only email and phone were detected
    entities1 = [e["entity_type"] for e in result1["analysis"]["entities"]]
    assert "EMAIL_ADDRESS" in entities1
    assert "PHONE_NUMBER" in entities1
    assert "PERSON" not in entities1
    
    # Test age_bracket_size in anonymization config
    result2 = ally.process(
        text=text,
        age_bracket_size=5, # Should be overridden 
        anonymization_config=AnonymizationConfig(
            operators={"DATE_OF_BIRTH": "age_bracket"},
            age_bracket_size=20
        )
    )
    
    # Verify age bracket size (20-year bracket should contain 1980)
    assert "<1980-2000>" in result2["anonymized"] or "<1960-1980>" in result2["anonymized"]


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
    
def test_pattern_generalization_levels():
    """Test different generalization levels for pattern creation."""
    ally = create_allyanonimiser()
    
    # Create patterns with different generalization levels
    pattern_low = ally.manage_patterns(
        action="create_from_examples",
        entity_type="POLICY_LOW",
        examples=["POL-123", "POL-456", "POL-789"],
        generalization_level="low"
    )
    
    pattern_medium = ally.manage_patterns(
        action="create_from_examples",
        entity_type="POLICY_MED",
        examples=["POL-123", "POL-456", "POL-789"],
        generalization_level="medium"
    )
    
    pattern_high = ally.manage_patterns(
        action="create_from_examples",
        entity_type="POLICY_HIGH",
        examples=["POL-123", "POL-456", "POL-789"],
        generalization_level="high"
    )
    
    # Test different patterns with exact and variant examples
    exact_match = "POL-123"
    variant_match = "POL-ABC"
    
    # Analyze text with all patterns
    result = ally.analyze(exact_match)
    result_types = [r.entity_type for r in result]
    
    # Low generalization should match exact examples
    assert "POLICY_LOW" in result_types
    
    # Medium generalization should match exact examples
    assert "POLICY_MED" in result_types
    
    # High generalization should match exact examples
    assert "POLICY_HIGH" in result_types
    
    # Test variant example
    result = ally.analyze(variant_match)
    result_types = [r.entity_type for r in result]
    
    # High generalization should be more likely to match variants
    assert "POLICY_HIGH" in result_types


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

def test_pyarrow_integration(mocker):
    """Test DataFrame processing with PyArrow integration."""
    # Mock pandas DataFrame and DataFrameProcessor for testing PyArrow integration
    pd_mock = mocker.patch("allyanonimiser.dataframe_processor.pd")
    processor_mock = mocker.patch("allyanonimiser.dataframe_processor.DataFrameProcessor")
    
    # Create instance
    ally = create_allyanonimiser()
    
    # Test with PyArrow enabled
    ally.process_dataframe(
        df="mock_df",
        text_columns="notes",
        operation="process",
        use_pyarrow=True
    )
    # Verify DataFrameProcessor was created with use_pyarrow=True
    processor_mock.assert_called_with(mocker.ANY, n_workers=None, use_pyarrow=True)

def test_custom_anonymization_operator(mocker):
    """Test using a custom anonymization operator."""
    # Create instance
    ally = create_allyanonimiser()
    
    # Mock the anonymizer
    ally.anonymizer.anonymize = mocker.MagicMock()
    ally.anonymizer.anonymize.return_value = {"text": "anonymized text"}
    
    # Define a custom operator for the test
    custom_operators = {
        "PERSON": "custom",  # Using the custom operator type
        "EMAIL_ADDRESS": "mask"
    }
    
    # Configure a custom operator function
    config = AnonymizationConfig(
        operators=custom_operators
    )
    
    # Call anonymize with the custom operator
    ally.anonymize("test text", config=config)
    
    # Verify the anonymizer was called with the custom operators
    ally.anonymizer.anonymize.assert_called_with(
        "test text", 
        custom_operators, 
        "en",
        age_bracket_size=5, 
        keep_postcode=True
    )