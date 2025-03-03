"""
Tests for error handling and user-friendly error messages.
"""

import pytest
from allyanonimiser import create_analyzer, create_allyanonimiser, EnhancedAnonymizer
import re

@pytest.fixture
def analyzer():
    """Create analyzer for testing error messages."""
    return create_analyzer()

@pytest.fixture
def anonymizer(analyzer):
    """Create anonymizer for testing error messages."""
    return EnhancedAnonymizer(analyzer=analyzer)

def test_age_bracket_invalid_parameter(anonymizer):
    """Test error handling for invalid age_bracket_size parameter."""
    operators = {"DATE_OF_BIRTH": "age_bracket"}
    
    # Test with negative bracket size
    try:
        result = anonymizer.anonymize(
            "DOB: 15/03/1980",
            operators=operators,
            age_bracket_size=-5
        )
        # Should use default value and not error
        assert result["text"] != ""
    except Exception as e:
        pytest.fail(f"Should not raise exception for negative age_bracket_size: {str(e)}")
    
    # Test with zero bracket size
    try:
        result = anonymizer.anonymize(
            "DOB: 15/03/1980",
            operators=operators,
            age_bracket_size=0
        )
        # Should use default value and not error
        assert result["text"] != ""
    except Exception as e:
        pytest.fail(f"Should not raise exception for zero age_bracket_size: {str(e)}")
    
    # Test with non-integer bracket size
    try:
        result = anonymizer.anonymize(
            "DOB: 15/03/1980",
            operators=operators,
            age_bracket_size="invalid"
        )
        # Should use default value and not error
        assert result["text"] != ""
    except Exception as e:
        pytest.fail(f"Should not raise exception for non-integer age_bracket_size: {str(e)}")

def test_keep_postcode_invalid_parameter(anonymizer):
    """Test error handling for invalid keep_postcode parameter."""
    text = "Customer lives at 123 Main St, Sydney NSW 2000."
    
    # Test with non-boolean value
    try:
        result = anonymizer.anonymize(
            text,
            keep_postcode="not_a_boolean"
        )
        # Should not error with invalid parameter
        assert result["text"] != ""
        # Don't check content since our focus is just to ensure it doesn't crash
    except Exception as e:
        pytest.fail(f"Should not raise exception for non-boolean keep_postcode: {str(e)}")

def test_analyzer_not_provided_error(anonymizer):
    """Test error handling when analyzer is not provided."""
    # Create anonymizer without analyzer
    bad_anonymizer = EnhancedAnonymizer(analyzer=None)
    
    # Should not raise exception but return original text
    result = bad_anonymizer.anonymize("Some text with John Smith and his email john@example.com")
    assert result["text"] == "Some text with John Smith and his email john@example.com"
    assert result["items"] == []

def test_combined_invalid_parameters(anonymizer):
    """Test error handling when multiple invalid parameters are provided."""
    text = "Patient: John Smith, DOB: 15/03/1980, Address: 42 Park St, Sydney NSW 2000"
    operators = {"DATE_OF_BIRTH": "age_bracket"}
    
    try:
        result = anonymizer.anonymize(
            text,
            operators=operators,
            age_bracket_size="invalid",
            keep_postcode=123
        )
        # Should not error and use default values
        assert result["text"] != ""
        # Should still have content (don't check specific values)
        assert len(result["text"]) > 0
    except Exception as e:
        pytest.fail(f"Should not raise exception for multiple invalid parameters: {str(e)}")

def test_allyanonimiser_error_handling():
    """Test Allyanonimiser interface error handling."""
    ally = create_allyanonimiser()
    
    # Test with invalid dataframe column
    import pandas as pd
    df = pd.DataFrame({'id': [1, 2], 'text': ['Text one', 'Text two']})
    
    try:
        result = ally.anonymize_dataframe(df, 'non_existent_column')
        pytest.fail("Should raise error for non-existent column")
    except KeyError as e:
        # This should raise a user-friendly error
        assert "Column 'non_existent_column' not found" in str(e) or "non_existent_column" in str(e)
    except Exception as e:
        # Other exceptions should be more user-friendly
        assert "Column" in str(e) or "column" in str(e) or "not found" in str(e)

def test_operator_invalid_error_handling(anonymizer):
    """Test error handling for invalid operator."""
    text = "DOB: 15/03/1980"
    
    # Test with invalid operator
    result = anonymizer.anonymize(
        text,
        operators={"DATE_OF_BIRTH": "invalid_operator"}
    )
    
    # Should default to replace and not error
    assert result["text"] != text
    assert "<DATE_OF_BIRTH>" in result["text"]