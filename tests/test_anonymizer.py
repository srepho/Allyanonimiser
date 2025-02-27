"""
Tests for the EnhancedAnonymizer class.
"""

import pytest
from allyanonimiser import EnhancedAnonymizer, EnhancedAnalyzer, create_au_insurance_analyzer

def test_anonymizer_creation():
    """Test that an anonymizer can be created."""
    analyzer = EnhancedAnalyzer()
    anonymizer = EnhancedAnonymizer(analyzer=analyzer)
    assert anonymizer is not None
    assert hasattr(anonymizer, 'anonymize')

def test_anonymize_simple_text(basic_anonymizer, example_texts):
    """Test anonymizing simple text with standard patterns."""
    text = example_texts["simple"]
    result = basic_anonymizer.anonymize(text)
    
    # Check that the result has expected keys
    assert "text" in result
    assert "items" in result
    
    # Check that anonymized text is not the same as original
    assert result["text"] != text
    
    # Check that the anonymized text no longer contains the original PII
    assert "John Smith" not in result["text"]
    assert "john.smith@example.com" not in result["text"]
    
    # Check that items were replaced
    assert len(result["items"]) > 0
    
def test_anonymize_claim_note(basic_anonymizer, example_texts):
    """Test anonymizing a claim note with multiple entity types."""
    text = example_texts["claim_note"]
    result = basic_anonymizer.anonymize(text)
    
    # Check that the anonymized text is not the same as original
    assert result["text"] != text
    
    # Check that the specific PII is not in the anonymized text
    sensitive_info = [
        "John Smith",
        "0412 345 678",
        "john.smith@example.com",
        "123 Main St, Sydney NSW 2000",
        "123 456 789"  # TFN
    ]
    
    for info in sensitive_info:
        assert info not in result["text"], f"Found '{info}' in anonymized text"
    
    # Check that we have items in the result
    assert len(result["items"]) > 0
    
def test_anonymize_with_custom_operators(basic_analyzer, example_texts):
    """Test anonymizing with custom operators."""
    anonymizer = EnhancedAnonymizer(analyzer=basic_analyzer)
    text = example_texts["simple"]
    
    # Define custom operators to use different strategies
    operators = {
        "PERSON": "replace",           # Replace with another name
        "EMAIL_ADDRESS": "mask",       # Mask with asterisks
        "PHONE_NUMBER": "redact",      # Completely remove
        "AU_ADDRESS": "hash"           # Replace with hash
    }
    
    result = anonymizer.anonymize(text, operators=operators)
    
    # Check that the anonymized text is not the same as original
    assert result["text"] != text
    
    # Check items were anonymized according to the operators
    for item in result["items"]:
        if item["entity_type"] == "PERSON":
            assert item["operator"] == "replace"
        elif item["entity_type"] == "EMAIL_ADDRESS":
            assert item["operator"] == "mask"
            # Masked email should contain asterisks
            replacement = result["text"][item["start"]:item["end"]]
            assert "*" in replacement
    
def test_anonymize_with_custom_mask_char(basic_analyzer, example_texts):
    """Test anonymizing with custom mask character."""
    anonymizer = EnhancedAnonymizer(analyzer=basic_analyzer)
    text = example_texts["simple"]
    
    # Use custom mask character and different operators
    result = anonymizer.anonymize(
        text=text,
        mask_char="X",
        operators={
            "PERSON": "mask",
            "EMAIL_ADDRESS": "mask"
        }
    )
    
    # Check that masked items use X instead of *
    for item in result["items"]:
        if item["operator"] == "mask":
            replacement = result["text"][item["start"]:item["end"]]
            assert "X" in replacement
            assert "*" not in replacement
            
def test_anonymize_with_preservation(basic_analyzer, example_texts):
    """Test anonymizing with partial data preservation."""
    anonymizer = EnhancedAnonymizer(analyzer=basic_analyzer)
    text = example_texts["email"]
    
    # Configure anonymizer to preserve parts of some entities
    result = anonymizer.anonymize(
        text=text,
        operators={
            "EMAIL_ADDRESS": "mask_preserve_domain",  # Preserve domain part
            "PHONE_NUMBER": "mask_preserve_last_4"    # Preserve last 4 digits
        }
    )
    
    # Check that domain parts are preserved in email addresses
    for item in result["items"]:
        if item["entity_type"] == "EMAIL_ADDRESS":
            replacement = result["text"][item["start"]:item["end"]]
            # Should mask the local part but preserve domain
            assert "@" in replacement
            assert "example.com" in replacement
            
        if item["entity_type"] == "AU_PHONE" or item["entity_type"] == "PHONE_NUMBER":
            if item["operator"] == "mask_preserve_last_4":
                # Last 4 digits should be preserved
                original = text[item["original_start"]:item["original_end"]]
                replacement = result["text"][item["start"]:item["end"]]
                assert original[-4:] in replacement
                
def test_anonymize_with_consistency(basic_analyzer, example_texts):
    """Test that anonymization is consistent for the same entities."""
    anonymizer = EnhancedAnonymizer(analyzer=basic_analyzer)
    text = example_texts["claim_note"]
    
    # The name "John Smith" appears multiple times in the text
    result = anonymizer.anonymize(
        text=text,
        operators={"PERSON": "replace"}
    )
    
    # Find all the replacements for "John Smith"
    replacements = []
    for item in result["items"]:
        if item["entity_type"] == "PERSON" and text[item["original_start"]:item["original_end"]] == "John Smith":
            replacements.append(result["text"][item["start"]:item["end"]])
    
    # Should have multiple replacements
    assert len(replacements) > 1
    
    # All replacements should be the same (consistency)
    assert len(set(replacements)) == 1, "Replacements for the same entity are not consistent"
    
def test_anonymize_statistics(basic_anonymizer, example_texts):
    """Test that anonymization statistics are generated correctly."""
    text = example_texts["claim_note"]
    result = basic_anonymizer.anonymize(text)
    
    # Should include statistics
    assert "statistics" in result
    stats = result["statistics"]
    
    # Check statistics content
    assert "total_items" in stats
    assert stats["total_items"] > 0
    assert "entity_type_counts" in stats
    assert len(stats["entity_type_counts"]) > 0
    assert "operator_counts" in stats
    assert len(stats["operator_counts"]) > 0
    
def test_anonymize_custom_replacements(basic_analyzer, example_texts):
    """Test anonymizing with custom replacement values."""
    anonymizer = EnhancedAnonymizer(analyzer=basic_analyzer)
    text = example_texts["simple"]
    
    # Define custom replacement values
    custom_replacements = {
        "PERSON": ["REDACTED_NAME"],
        "EMAIL_ADDRESS": ["user@anon.com"]
    }
    
    result = anonymizer.anonymize(
        text=text,
        operators={"PERSON": "replace", "EMAIL_ADDRESS": "replace"},
        custom_replace_values=custom_replacements
    )
    
    # Check that custom replacements were used
    for item in result["items"]:
        if item["entity_type"] == "PERSON":
            replacement = result["text"][item["start"]:item["end"]]
            assert replacement == "REDACTED_NAME"
        
        if item["entity_type"] == "EMAIL_ADDRESS":
            replacement = result["text"][item["start"]:item["end"]]
            assert replacement == "user@anon.com"