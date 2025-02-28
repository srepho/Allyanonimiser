"""
Tests for the pattern generation functionality.
"""
import re
import pytest
from utils.spacy_helpers import (
    create_regex_from_examples,
    create_simple_generalized_regex,
    create_generalized_regex,
    create_advanced_generalized_regex,
    generalize_single_example,
    detect_common_format
)

class TestRegexGeneration:
    """Test regex pattern generation from examples."""
    
    def test_basic_regex_generation(self):
        """Test basic non-generalized regex pattern generation."""
        examples = ["ABC123", "DEF456"]
        pattern = create_regex_from_examples(examples, generalization_level="none")
        
        # Check that OR pattern is created correctly
        assert "(ABC123)|(DEF456)" == pattern
        
        # Check that pattern matches all examples
        for example in examples:
            assert re.match(pattern, example) is not None
    
    def test_empty_examples(self):
        """Test that empty examples list raises an error."""
        with pytest.raises(ValueError):
            create_regex_from_examples([])
    
    def test_invalid_generalization_level(self):
        """Test that invalid generalization level raises an error."""
        with pytest.raises(ValueError):
            create_regex_from_examples(["test"], generalization_level="invalid")
    
    def test_simple_generalization_single_example(self):
        """Test simple generalization with a single example."""
        example = "ABC123"
        pattern = create_regex_from_examples([example], generalization_level="low")
        
        # Check that digits are generalized
        assert "ABC\\d+" in pattern
        
        # Check that pattern matches the example
        assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(pattern, "ABC456") is not None
        assert re.match(pattern, "ABC7890") is not None
    
    def test_simple_generalization_common_prefix_suffix(self):
        """Test simple generalization with common prefix/suffix."""
        examples = ["PREFIX-123-SUFFIX", "PREFIX-456-SUFFIX"]
        pattern = create_simple_generalized_regex(examples)
        
        # Check that correct prefix and suffix are preserved
        assert pattern.startswith("PREFIX\\-")
        assert pattern.endswith("\\-SUFFIX")
        
        # Check that middle part is generalized as digits
        assert "\\d+" in pattern
        
        # Check that pattern matches all examples
        for example in examples:
            assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(pattern, "PREFIX-789-SUFFIX") is not None
    
    def test_simple_generalization_alphabetic_middle(self):
        """Test simple generalization with alphabetic middle part."""
        examples = ["PREFIX-ABC-SUFFIX", "PREFIX-DEF-SUFFIX"]
        pattern = create_simple_generalized_regex(examples)
        
        # Check that middle part is generalized as alphabetic
        assert "[A-Z]+" in pattern
        
        # Check that pattern matches all examples
        for example in examples:
            assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(pattern, "PREFIX-XYZ-SUFFIX") is not None
    
    def test_medium_generalization_date_format(self):
        """Test medium generalization with date format detection."""
        examples = ["01/02/2023", "15/06/2022", "31/12/2021"]
        pattern = create_generalized_regex(examples)
        
        # Check that pattern is a date format
        assert "\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}" == pattern
        
        # Check that pattern matches all examples
        for example in examples:
            assert re.match(pattern, example) is not None
        
        # Check that pattern matches other date formats
        assert re.match(pattern, "05/07/2024") is not None
        assert re.match(pattern, "10-11-2023") is not None
    
    def test_medium_generalization_id_format(self):
        """Test medium generalization with ID format detection."""
        examples = ["ABC-12345", "DEF-67890", "XYZ-54321"]
        pattern = create_generalized_regex(examples)
        
        # Check that pattern is an ID format
        assert "[A-Z]{2,3}-\\d{4,7}" == pattern
        
        # Check that pattern matches all examples
        for example in examples:
            assert re.match(pattern, example) is not None
        
        # Check that pattern matches other ID formats
        assert re.match(pattern, "PQR-98765") is not None
    
    def test_advanced_generalization_complex_examples(self):
        """Test advanced generalization with complex examples."""
        examples = [
            "Customer ID: ABC-123 (2023)",
            "Customer ID: XYZ-456 (2022)",
            "Customer ID: PQR-789 (2024)"
        ]
        pattern = create_advanced_generalized_regex(examples)
        
        # Check that pattern matches all examples
        for example in examples:
            assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(pattern, "Customer ID: LMN-321 (2025)") is not None
    
    def test_generalize_single_example_digits(self):
        """Test generalizing a single example with digits."""
        example = "ABC123DEF456"
        pattern = generalize_single_example(example)
        
        # Check that digits are generalized
        assert re.search(r"\\d{3}", pattern) is not None
        
        # Check that pattern matches the example
        assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(pattern, "ABC789DEF456") is not None
    
    def test_generalize_single_example_letters(self):
        """Test generalizing a single example with letter patterns."""
        example = "abc-DEF-123"
        pattern = generalize_single_example(example)
        
        # Check that letters are properly generalized
        assert re.search(r"\[a-z\]{3}", pattern) is not None
        assert re.search(r"\[A-Z\]{3}", pattern) is not None
        
        # Check that pattern matches the example
        assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(pattern, "xyz-DEF-123") is not None
        assert re.match(pattern, "abc-XYZ-123") is not None
    
    def test_detect_common_format_email(self):
        """Test detection of email addresses."""
        examples = ["user@example.com", "another@test.org"]
        pattern = detect_common_format(examples)
        
        # Check that pattern is an email format
        assert pattern is not None
        assert "user@example.com" in re.findall(pattern, "Contact user@example.com for help")
        assert "another@test.org" in re.findall(pattern, "Email another@test.org for support")
    
    def test_detect_common_format_phone(self):
        """Test detection of phone numbers."""
        examples = ["123-456-7890", "987-654-3210"]
        pattern = detect_common_format(examples)
        
        # Check that pattern is a phone number format
        assert pattern is not None
        assert "123-456-7890" in re.findall(pattern, "Call 123-456-7890 for service")
        assert "987-654-3210" in re.findall(pattern, "Phone 987-654-3210 is available")
