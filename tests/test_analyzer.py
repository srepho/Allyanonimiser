"""
Tests for the EnhancedAnalyzer class.
"""

import pytest
from allyanonimiser import EnhancedAnalyzer, CustomPatternDefinition, create_au_insurance_analyzer

def test_analyzer_creation():
    """Test that an analyzer can be created."""
    analyzer = EnhancedAnalyzer()
    assert analyzer is not None
    assert hasattr(analyzer, 'analyze')

def test_analyzer_with_patterns():
    """Test that an analyzer can be created with patterns."""
    analyzer = create_au_insurance_analyzer()
    assert analyzer is not None
    assert hasattr(analyzer, 'analyze')
    
    # Should have patterns loaded
    assert len(analyzer.get_supported_entities()) > 0
    
def test_add_pattern():
    """Test adding a custom pattern to the analyzer."""
    analyzer = EnhancedAnalyzer()
    
    # Create a custom pattern
    pattern = CustomPatternDefinition(
        entity_type="TEST_ENTITY",
        patterns=["TEST-\\d{5}"],
        context=["test", "entity"],
        name="test_entity_recognizer"
    )
    
    analyzer.add_pattern(pattern)
    
    # Check that the pattern was added
    assert "TEST_ENTITY" in analyzer.get_supported_entities()
    
def test_analyze_simple_text(basic_analyzer, example_texts, example_entities):
    """Test analyzing simple text with standard patterns."""
    text = example_texts["simple"]
    results = basic_analyzer.analyze(text)
    
    # Check that we found the expected entities
    assert len(results) >= len(example_entities["simple"])
    
    # Check that the entities we expected are found
    found_entities = []
    for result in results:
        found_entities.append({
            "entity_type": result.entity_type,
            "text": text[result.start:result.end]
        })
    
    for expected in example_entities["simple"]:
        assert expected in found_entities, f"Expected to find {expected}"
        
def test_analyze_claim_note(basic_analyzer, example_texts):
    """Test analyzing a claim note with multiple entity types."""
    text = example_texts["claim_note"]
    results = basic_analyzer.analyze(text)
    
    # Should find numerous entities
    assert len(results) >= 5
    
    # Extract the actual text values
    found_entities = []
    for result in results:
        found_entities.append({
            "entity_type": result.entity_type,
            "text": text[result.start:result.end]
        })
    
    # Check for some specific entities we expect to find
    expected_entities = [
        {"entity_type": "INSURANCE_CLAIM_NUMBER", "text": "CL-23456789"},
        {"entity_type": "PERSON", "text": "John Smith"},
        {"entity_type": "AU_PHONE", "text": "0412 345 678"}
    ]
    
    for expected in expected_entities:
        assert expected in found_entities, f"Expected to find {expected}"
        
def test_analyze_with_threshold(basic_analyzer, example_texts):
    """Test analyzing with a score threshold."""
    text = example_texts["claim_note"]
    
    # First analyze with default threshold
    default_results = basic_analyzer.analyze(text)
    
    # Then analyze with high threshold
    high_threshold_results = basic_analyzer.analyze(text, score_threshold=0.9)
    
    # High threshold should return fewer results
    assert len(high_threshold_results) < len(default_results)
    
    # All high threshold results should have scores >= 0.9
    for result in high_threshold_results:
        assert result.score >= 0.9
        
def test_analyze_with_entities_filter(basic_analyzer, example_texts):
    """Test analyzing with an entities filter."""
    text = example_texts["claim_note"]
    
    # First analyze with no filter
    all_results = basic_analyzer.analyze(text)
    
    # Then analyze with only PERSON entities
    person_results = basic_analyzer.analyze(text, entities=["PERSON"])
    
    # Should only get PERSON entities
    assert len(person_results) > 0
    assert all(result.entity_type == "PERSON" for result in person_results)
    
    # Should be fewer than all results
    assert len(person_results) < len(all_results)
    
def test_custom_analyzer_patterns():
    """Test creating a custom analyzer with specific patterns."""
    analyzer = EnhancedAnalyzer()
    
    # Add a couple of custom patterns
    custom_patterns = [
        CustomPatternDefinition(
            entity_type="PROJECT_ID",
            patterns=["PRJ-\\d{4}"],
            context=["project", "id", "identifier"],
            name="project_id_recognizer"
        ),
        CustomPatternDefinition(
            entity_type="EMPLOYEE_ID",
            patterns=["EMP-\\d{6}"],
            context=["employee", "staff", "id", "identifier"],
            name="employee_id_recognizer"
        )
    ]
    
    for pattern in custom_patterns:
        analyzer.add_pattern(pattern)
    
    # Test with text containing these patterns
    text = "Project PRJ-1234 was assigned to employee EMP-123456 for implementation."
    results = analyzer.analyze(text)
    
    # Should find both custom entities
    assert len(results) == 2
    
    entity_types = [result.entity_type for result in results]
    assert "PROJECT_ID" in entity_types
    assert "EMPLOYEE_ID" in entity_types
    
    # Check the actual text values
    found_values = {text[result.start:result.end] for result in results}
    assert "PRJ-1234" in found_values
    assert "EMP-123456" in found_values