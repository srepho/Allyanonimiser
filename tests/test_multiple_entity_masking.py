"""Test cases for masking multiple entity types simultaneously."""

import pytest
from allyanonimiser import create_allyanonimiser, AnonymizationConfig


class TestMultipleEntityMasking:
    """Test simultaneous masking of multiple entity types."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return create_allyanonimiser()
    
    def test_basic_multiple_entities(self, analyzer):
        """Test basic text with multiple entity types."""
        text = "John Smith called from 0412 345 678 about his Medicare card 2123 45678 1"
        
        config = AnonymizationConfig(
            operators={
                "PERSON": "replace",
                "AU_PHONE": "mask",
                "AU_MEDICARE": "redact"
            }
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # Should have all three entity types anonymized
        assert "<PERSON>" in result['text']
        assert "****" in result['text']  # Phone masking
        assert "[REDACTED]" in result['text']  # Medicare redaction
        
        # Original values should not appear
        assert "John Smith" not in result['text']
        assert "0412 345 678" not in result['text']
        assert "2123 45678 1" not in result['text']
    
    def test_complex_document_anonymization(self, analyzer):
        """Test anonymization of complex documents with many entity types."""
        text = """
        Claim Reference: CL-12345678
        Policy Number: POL-987654321
        
        Customer Details:
        Name: Sarah Johnson
        Phone: 0412 345 678
        Email: sarah.johnson@email.com
        DOB: 15/03/1985
        Medicare: 3456 78901 2
        """
        
        config = AnonymizationConfig(
            operators={
                "PERSON": "replace",
                "AU_PHONE": "replace",
                "EMAIL_ADDRESS": "replace",
                "AU_MEDICARE": "replace",
                "DATE": "replace",
                "INSURANCE_CLAIM_NUMBER": "replace",
                "INSURANCE_POLICY_NUMBER": "replace"
            }
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # Check that all sensitive data is anonymized
        assert "Sarah Johnson" not in result['text']
        assert "0412 345 678" not in result['text']
        assert "sarah.johnson@email.com" not in result['text']
        assert "3456 78901 2" not in result['text']
        assert "CL-12345678" not in result['text']
        assert "POL-987654321" not in result['text']
        
        # Check replacements were made
        replacements = result['items']
        entity_types = [item['entity_type'] for item in replacements]
        
        assert "PERSON" in entity_types
        assert "AU_PHONE" in entity_types
        assert "EMAIL_ADDRESS" in entity_types
        assert "AU_MEDICARE" in entity_types
        assert "INSURANCE_CLAIM_NUMBER" in entity_types
        assert "INSURANCE_POLICY_NUMBER" in entity_types
    
    def test_selective_entity_masking(self, analyzer):
        """Test masking only specific entity types."""
        text = "Contact John Smith on 0412 345 678 or email john.smith@example.com"
        
        # Only mask names and phones, leave email visible
        config = AnonymizationConfig(
            operators={
                "PERSON": "mask",
                "AU_PHONE": "mask"
            },
            active_entity_types=["PERSON", "AU_PHONE"]
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # Names and phones should be masked
        assert "John Smith" not in result['text']
        assert "0412 345 678" not in result['text']
        assert "****" in result['text']
        
        # Email should remain visible
        assert "john.smith@example.com" in result['text']
    
    def test_mixed_operators(self, analyzer):
        """Test using different anonymization operators for different entity types."""
        text = "John's phone is 0412 345 678, email: john@example.com, TFN: 123 456 789"
        
        config = AnonymizationConfig(
            operators={
                "PERSON": "replace",      # <PERSON>
                "AU_PHONE": "mask",       # ****
                "EMAIL_ADDRESS": "hash",  # SHA256 hash
                "AU_TFN": "redact"       # [REDACTED]
            }
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # Check different operator effects
        assert "<PERSON>" in result['text'] or "PERSON>" in result['text']
        assert "****" in result['text']
        assert "[REDACTED]" in result['text']
        
        # Original values should be gone
        assert "John" not in result['text']
        assert "0412 345 678" not in result['text']
        assert "john@example.com" not in result['text']
        assert "123 456 789" not in result['text']
    
    def test_consistent_replacement(self, analyzer):
        """Test that same entities are replaced consistently."""
        text = "John Smith called about John Smith's claim. Contact John Smith at 0412 345 678."
        
        config = AnonymizationConfig(
            operators={
                "PERSON": "replace",
                "AU_PHONE": "replace"
            }
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # All instances of "John Smith" should be replaced
        assert "John Smith" not in result['text']
        
        # Count PERSON replacements
        person_count = result['text'].count("<PERSON>")
        assert person_count >= 2  # At least 2 instances
    
    def test_no_text_corruption(self, analyzer):
        """Test that overlapping entities don't corrupt the text."""
        text = "Medicare number 2123 45678 1 and phone 0412 345 678"
        
        result = analyzer.anonymize(text)
        
        # Check for common corruption patterns
        assert "POSTCODE>MEDICARE>" not in result['text']
        assert "DATE>PHONE>" not in result['text']
        assert "><" not in result['text']
        
        # Check balanced brackets
        assert result['text'].count('<') == result['text'].count('>')
    
    def test_preserve_formatting(self, analyzer):
        """Test that text formatting is preserved during anonymization."""
        text = """Name:    John Smith
Phone:   0412 345 678
Email:   john@example.com"""
        
        config = AnonymizationConfig(
            operators={
                "PERSON": "replace",
                "AU_PHONE": "replace",
                "EMAIL_ADDRESS": "replace"
            }
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # Should maintain the spacing and newlines
        assert "\n" in result['text']
        assert "Name:" in result['text']
        assert "Phone:" in result['text']
        assert "Email:" in result['text']