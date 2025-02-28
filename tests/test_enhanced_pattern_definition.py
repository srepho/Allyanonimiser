"""
Integration tests for enhanced pattern definition functionality.
"""
import re
import pytest
from allyanonimiser import create_pattern_from_examples
from allyanonimiser.pattern_manager import CustomPatternDefinition

class TestEnhancedPatternDefinition:
    """Test the enhanced pattern definition functionality."""
    
    def test_create_pattern_basic(self):
        """Test creating a basic pattern with no generalization."""
        examples = ["REF-12345", "REF-67890"]
        pattern_def = create_pattern_from_examples(
            entity_type="REFERENCE_NUMBER",
            examples=examples,
            context=["reference", "ref", "number"],
            name="reference_pattern",
            pattern_type="regex",
            generalization_level="none"
        )
        
        # Check that pattern definition is created correctly
        assert isinstance(pattern_def, CustomPatternDefinition)
        assert pattern_def.entity_type == "REFERENCE_NUMBER"
        assert pattern_def.name == "reference_pattern"
        assert pattern_def.context == ["reference", "ref", "number"]
        assert len(pattern_def.patterns) == 1
        
        # Check that pattern matches examples
        pattern = pattern_def.patterns[0]
        for example in examples:
            assert re.match(pattern, example) is not None
    
    def test_create_pattern_with_generalization(self):
        """Test creating a pattern with generalization."""
        examples = ["REF-12345", "REF-67890", "REF-54321"]
        pattern_def = create_pattern_from_examples(
            entity_type="REFERENCE_NUMBER",
            examples=examples,
            context=["reference", "ref", "number"],
            name="reference_pattern",
            pattern_type="regex",
            generalization_level="medium"
        )
        
        # Check that pattern definition is created correctly
        assert isinstance(pattern_def, CustomPatternDefinition)
        assert pattern_def.entity_type == "REFERENCE_NUMBER"
        
        # Check that pattern matches examples
        pattern = pattern_def.patterns[0]
        for example in examples:
            assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(pattern, "REF-98765") is not None
    
    def test_create_pattern_high_generalization(self):
        """Test creating a pattern with high generalization."""
        examples = [
            "Customer: John Doe (ID: REF-12345)",
            "Customer: Jane Smith (ID: REF-67890)",
            "Customer: Bob Johnson (ID: REF-54321)"
        ]
        pattern_def = create_pattern_from_examples(
            entity_type="CUSTOMER_REFERENCE",
            examples=examples,
            context=["customer", "id"],
            name="customer_reference_pattern",
            pattern_type="regex",
            generalization_level="high"
        )
        
        # Check that pattern definition is created correctly
        assert isinstance(pattern_def, CustomPatternDefinition)
        assert pattern_def.entity_type == "CUSTOMER_REFERENCE"
        
        # Check that pattern matches examples
        pattern = pattern_def.patterns[0]
        for example in examples:
            assert re.match(pattern, example) is not None
        
        # Check that pattern matches similar examples
        assert re.match(
            pattern, 
            "Customer: Alice Williams (ID: REF-13579)"
        ) is not None
    
    def test_create_pattern_spacy(self):
        """Test creating a spaCy-based pattern."""
        examples = ["REF-12345", "REF-67890"]
        pattern_def = create_pattern_from_examples(
            entity_type="REFERENCE_NUMBER",
            examples=examples,
            context=["reference", "ref", "number"],
            name="reference_pattern",
            pattern_type="spacy"
        )
        
        # Check that pattern definition is created correctly
        assert isinstance(pattern_def, CustomPatternDefinition)
        assert pattern_def.entity_type == "REFERENCE_NUMBER"
        
        # Check that patterns are in spaCy format (should be a list of lists of dicts)
        assert isinstance(pattern_def.patterns, list)
        for pattern in pattern_def.patterns:
            assert isinstance(pattern, list)
            for token_spec in pattern:
                assert isinstance(token_spec, dict)
