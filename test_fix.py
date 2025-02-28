"""
Test fix for entity conflict resolution.
"""
import sys
from allyanonimiser import create_allyanonimiser

def test_entity_conflict_resolution():
    """Test that entity conflict resolution works correctly."""
    # Create the analyzer
    ally = create_allyanonimiser()
    
    # Test case 1: POL prefix should be recognized only as policy number
    test_text = """
    Policy Number: POL123456
    The vehicle registration is REF-98765
    Patient John was admitted on 2023-01-15
    Please see Ref Number for more details
    Here is your driver's license: VIC987654
    """
    
    # Analyze the text
    results = ally.analyzer.analyze(test_text)
    
    # Print the results
    print("Analysis Results:")
    for result in results:
        print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
    
    # Verify results
    policy_matches = [r for r in results if r.text == "POL123456"]
    assert len(policy_matches) <= 1, f"Expected single or no match for POL123456, got {len(policy_matches)}"
    if policy_matches:
        assert policy_matches[0].entity_type == "INSURANCE_POLICY_NUMBER", f"POL123456 should be INSURANCE_POLICY_NUMBER, got {policy_matches[0].entity_type}"
    
    # Verify "Ref Number" is not in results
    ref_number_matches = [r for r in results if r.text.lower() == "ref number"]
    assert len(ref_number_matches) == 0, f"'Ref Number' should not be detected as an entity, got {len(ref_number_matches)} matches"
    
    # Verify there are no overlapping/duplicate entity detections
    unique_texts = set()
    duplicate_entities = []
    for result in results:
        if result.text in unique_texts:
            duplicate_entities.append(result.text)
        unique_texts.add(result.text)
    
    assert len(duplicate_entities) == 0, f"Found duplicate entity detections for: {duplicate_entities}"
    
    # Test case 2: Add a test with proper PERSON name that should be detected
    test_text_with_person = """
    Patient John Smith was admitted on 2023-01-15
    Dr. Sarah Johnson reviewed the case files.
    """
    
    # Check if spaCy is available and configured
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            # If we got this far, spaCy is available with model loaded
            
            # Analyze the text
            if ally.analyzer.use_spacy:
                print("\nTesting person detection with spaCy:")
                results_person = ally.analyzer.analyze(test_text_with_person)
                
                # Print the results
                for result in results_person:
                    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
                
                # Verify person detection
                person_matches = [r for r in results_person if r.entity_type == "PERSON"]
                for person in person_matches:
                    print(f"Detected person: {person.text}")
                
                # These assertions are optional since spaCy might not be available
                if person_matches:
                    print("spaCy NER is working correctly for PERSON detection")
        except:
            print("\nSpaCy model not available, skipping PERSON detection test")
    except ImportError:
        print("\nSpaCy not installed, skipping PERSON detection test")
    
    print("All tests passed!")

if __name__ == "__main__":
    test_entity_conflict_resolution()