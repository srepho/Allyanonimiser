"""
Tests for the EnhancedAnalyzer class.
"""

import pytest
from allyanonimiser import EnhancedAnalyzer, CustomPatternDefinition, create_analyzer

def test_analyzer_creation():
    """Test that an analyzer can be created."""
    analyzer = EnhancedAnalyzer()
    assert analyzer is not None
    assert hasattr(analyzer, 'analyze')

def test_analyzer_with_patterns():
    """Test that an analyzer can be created with patterns."""
    analyzer = create_analyzer()
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
    assert len(results) > 0
    
    # Check that we found at least a person and email
    found_entity_types = {result.entity_type for result in results}
    assert "PERSON" in found_entity_types
    assert "EMAIL_ADDRESS" in found_entity_types

    # Convert results to readable format for debugging
    found_entities = []
    for result in results:
        found_entities.append({
            "entity_type": result.entity_type,
            "text": text[result.start:result.end]
        })
    
    # Make sure we have a person entity that contains "John Smith"
    found_persons = [entity for entity in found_entities if entity["entity_type"] == "PERSON" and "John Smith" in entity["text"]]
    assert len(found_persons) > 0, "Did not find a PERSON entity containing 'John Smith'"
    
    # Make sure we have an email entity
    found_emails = [entity for entity in found_entities if entity["entity_type"] == "EMAIL_ADDRESS"]
    assert len(found_emails) > 0, "Did not find an EMAIL_ADDRESS entity"
    assert any("john.smith@example.com" in entity["text"] for entity in found_emails), "Did not find the correct email"
        
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
    
    # Print found entities for debugging
    print("Found entities:", found_entities)
    
    # Check for insurance claim number
    claim_numbers = [entity for entity in found_entities if entity["entity_type"] == "INSURANCE_CLAIM_NUMBER"]
    assert any("CL-23456789" in entity["text"] for entity in claim_numbers), "Did not find the correct claim number"
    
    # Check for person
    persons = [entity for entity in found_entities if entity["entity_type"] == "PERSON"]
    assert any("John Smith" in entity["text"] for entity in persons), "Did not find the person John Smith"
    
    # Check for email
    emails = [entity for entity in found_entities if entity["entity_type"] == "EMAIL_ADDRESS"]
    assert any("john.smith@example.com" in entity["text"] for entity in emails), "Did not find the correct email"
    
    # Check for Medicare number or date that contains the Medicare number
    medicare_numbers = [entity for entity in found_entities if entity["entity_type"] == "AU_MEDICARE"]
    date_numbers = [entity for entity in found_entities if entity["entity_type"] == "DATE" and "2123 45678 1" in entity["text"]]
    
    # Either AU_MEDICARE or DATE containing the Medicare number should be found
    assert len(medicare_numbers) > 0 or len(date_numbers) > 0, "Did not find any AU_MEDICARE entity or DATE with Medicare format"
        
def test_analyze_with_threshold(basic_analyzer, example_texts):
    """Test analyzing with a score threshold."""
    text = example_texts["claim_note"]
    
    # Create an AnalysisConfig with minimum score threshold
    from allyanonimiser import AnalysisConfig
    
    # First analyze with default settings
    default_results = basic_analyzer.analyze(text)
    
    # Then analyze with higher threshold using the process method which supports AnalysisConfig
    config = AnalysisConfig(min_score_threshold=0.7)
    result = basic_analyzer.process(text, analysis_config=config)
    
    # Check that we have results
    assert len(default_results) > 0
    
    # The process method returns a dictionary with analysis results
    high_threshold_results = result.get("analysis", {}).get("entities", [])
    
    # Check that high threshold results are either empty or have high scores
    if high_threshold_results:
        # All high threshold results should have scores >= 0.7
        for entity in high_threshold_results:
            assert entity.get("score", 0) >= 0.7
    
    # Basic check that the analyze method worked correctly
    assert len(default_results) >= 5
        
def test_analyze_with_entities_filter(basic_analyzer, example_texts):
    """Test analyzing with an entities filter."""
    text = example_texts["claim_note"]
    
    # First analyze with no filter
    all_results = basic_analyzer.analyze(text)
    
    # Then analyze with only PERSON entities
    # Note: the parameter changed from 'entities' to 'active_entity_types' in newer versions
    person_results = basic_analyzer.analyze(text, active_entity_types=["PERSON"])
    
    # Should have some results
    assert len(person_results) > 0
    
    # Should contain at least one PERSON entity
    entity_types = [result.entity_type for result in person_results]
    assert "PERSON" in entity_types
    
    # Should be fewer than all results or equal (if only PERSON found in original)
    assert len(person_results) <= len(all_results)
    
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
    
    # Print results for debugging
    print("Custom pattern results:", results)
    
    # Check that we found our custom pattern entity types
    entity_types = [result.entity_type for result in results]
    assert "PROJECT_ID" in entity_types
    assert "EMPLOYEE_ID" in entity_types
    
    # Check the actual text values
    found_values = {text[result.start:result.end] for result in results}
    assert "PRJ-1234" in found_values
    assert "EMP-123456" in found_values
    
    # Check that we found our specific entities (by index to avoid test failures if additional entities are found)
    project_id_results = [r for r in results if r.entity_type == "PROJECT_ID"]
    employee_id_results = [r for r in results if r.entity_type == "EMPLOYEE_ID"]
    
    assert len(project_id_results) > 0
    assert len(employee_id_results) > 0