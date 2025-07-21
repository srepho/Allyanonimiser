"""Test cases for handling overlapping entities during anonymization."""

import pytest
from allyanonimiser import create_allyanonimiser, AnonymizationConfig


class TestOverlappingEntities:
    """Test that overlapping entities are handled correctly."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return create_allyanonimiser()
    
    def test_nested_entities(self, analyzer):
        """Test handling of nested entities (one entity completely inside another)."""
        # Medicare number contains a postcode
        text = "Medicare: 2123 45678 1"
        result = analyzer.anonymize(text)
        
        # Should not have corrupted replacements
        assert "<AU_POSTCODE>MEDICARE>" not in result['text']
        assert "AU_MEDICARE>" in result['text'] or "AU_POSTCODE>" in result['text']
        
    def test_partially_overlapping_entities(self, analyzer):
        """Test handling of partially overlapping entities."""
        # Phone number detected as both AU_PHONE and DATE
        text = "Call me on 0412 345 678"
        result = analyzer.anonymize(text)
        
        # Should handle the phone number correctly
        assert "<DATE>" not in result['text'] or "<AU_PHONE>" not in result['text']
        # Should not have corrupted text
        assert "DATE>PHONE>" not in result['text']
        
    def test_multiple_overlapping_entities(self, analyzer):
        """Test handling when multiple entities overlap at the same position."""
        text = "Policy POL-123456"
        
        # Analyze to see what's detected
        entities = analyzer.analyze(text)
        entity_types = [(e.entity_type, e.start, e.end, text[e.start:e.end]) for e in entities]
        print(f"Detected entities: {entity_types}")
        
        result = analyzer.anonymize(text)
        
        # Should have one clean replacement
        assert result['text'].count('<') == result['text'].count('>')
        
    def test_priority_of_longer_matches(self, analyzer):
        """Test that longer, more specific matches take priority."""
        text = "Australian Business Number: 51 824 753 556"
        
        config = AnonymizationConfig(
            operators={
                "AU_ABN": "replace",
                "NUMBER": "replace"
            }
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # Should prioritize AU_ABN over generic NUMBER
        assert "<AU_ABN>" in result['text']
        
    def test_email_name_overlap(self, analyzer):
        """Test email addresses that might overlap with person names."""
        text = "Contact john.smith@example.com for details"
        
        result = analyzer.anonymize(text)
        
        # Should handle email properly without name overlap
        assert "@" not in result['text']  # Email should be anonymized
        
    def test_consistent_anonymization_with_overlaps(self, analyzer):
        """Test that overlapping entities are consistently anonymized."""
        text = "John Smith (Medicare: 2123 45678 1) and John Smith (TFN: 123 456 789)"
        
        config = AnonymizationConfig(
            operators={
                "PERSON": "replace",
                "AU_MEDICARE": "replace", 
                "AU_TFN": "replace",
                "AU_POSTCODE": "replace"
            }
        )
        
        result = analyzer.anonymize(text, config=config)
        
        # Both instances of "John Smith" should be replaced the same way
        assert result['text'].count("<PERSON>") == 2
        
        # Should not have corrupted text
        assert "POSTCODE>MEDICARE" not in result['text']
        assert "TFN>" in result['text'] or "AU_TFN>" in result['text']
        
    def test_address_component_overlap(self, analyzer):
        """Test overlapping address components."""
        text = "123 Main Street, Sydney NSW 2000"
        
        result = analyzer.anonymize(text)
        
        # Check for clean replacements
        assert result['text'].count('<') == result['text'].count('>')
        
        # Should handle address properly
        assert "NSW 2000" not in result['text'] or "<" in result['text']