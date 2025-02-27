"""
Tests to validate the examples in the README.md file.
This ensures that the documented examples actually work as expected.
"""

import pytest
import os
import sys

def test_quick_start_example():
    """Test the quick start example from the README."""
    from allyanonimiser import create_au_insurance_analyzer
    
    # Create an analyzer with Australian and insurance patterns
    analyzer = create_au_insurance_analyzer()
    
    # Analyze text
    results = analyzer.analyze(
        text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123.",
        language="en"
    )
    
    # Verify we got some results
    assert len(results) > 0
    
    # Check that policy number and vehicle registration were detected
    entity_types = [result.entity_type for result in results]
    assert any("POLICY" in entity_type for entity_type in entity_types)
    assert any("VEHICLE" in entity_type for entity_type in entity_types)

def test_claim_notes_example():
    """Test the claim notes example from the README."""
    from allyanonimiser import analyze_claim_notes
    
    # Long claim note text
    claim_note = """
    Claim Details:
    Spoke with the insured John Smith (TFN: 123 456 789) regarding damage to his vehicle ABC123.
    The incident occurred on 14/05/2023 when another vehicle collided with the rear of his car.
    Policy number: POL-987654321

    Vehicle Details:
    Toyota Corolla 2020
    VIN: 1HGCM82633A123456
    Registration: ABC123

    Contact Information:
    Phone: 0412 345 678
    Email: john.smith@example.com
    Address: 123 Main St, Sydney NSW 2000
    """
    
    # Analyze the claim note
    analysis = analyze_claim_notes(claim_note)
    
    # Verify the analysis contains the expected keys
    assert "incident_description" in analysis
    assert "pii_segments" in analysis
    
    # Check PII-rich segments
    assert len(analysis["pii_segments"]) > 0
    
    # Test anonymization
    from allyanonimiser import EnhancedAnonymizer, create_au_insurance_analyzer
    anonymizer = EnhancedAnonymizer(analyzer=create_au_insurance_analyzer())
    anonymized = anonymizer.anonymize(claim_note)
    
    # Verify anonymization results
    assert "text" in anonymized
    # Make sure John Smith was anonymized (not in the text anymore)
    assert "John Smith" not in anonymized["text"]

def test_email_processing_example():
    """Test the email processing example from the README."""
    from allyanonimiser.insurance import InsuranceEmailAnalyzer
    
    email_text = """
    From: adjuster@insurance.com.au
    To: customer@example.com
    Subject: Your Claim CL-12345678

    Dear Mr. Smith,

    Thank you for your recent claim submission regarding your vehicle (Registration: XYZ123).

    We have assigned your claim number CL-12345678. Please reference this number in all future correspondence.

    Your policy POL-9876543 covers this type of damage, and we'll need the following information:
    1. Your Medicare number
    2. Additional photos of the damage
    3. The repair quote from the mechanic

    Please call me at 03 9876 5432 if you have any questions.

    Kind regards,
    Sarah Johnson
    Claims Assessor
    """
    
    email_analyzer = InsuranceEmailAnalyzer()
    analysis = email_analyzer.analyze(email_text)
    
    # Verify the analysis contains key elements
    assert "subject" in analysis
    assert "claim_number" in analysis
    assert "policy_number" in analysis
    assert "customer_name" in analysis
    assert "pii_entities" in analysis
    
    # Check that claim number was correctly extracted
    assert "CL-12345678" in analysis["claim_number"]

def test_creating_custom_patterns():
    """Test the custom pattern creation example from the README."""
    from allyanonimiser import CustomPatternDefinition, create_pattern_from_examples
    
    # Create a custom pattern for internal reference numbers
    internal_ref_examples = [
        "Internal reference: REF-12345",
        "Ref Number: REF-98765",
        "Reference: REF-55555"
    ]
    
    pattern = create_pattern_from_examples(
        entity_type="INTERNAL_REFERENCE",
        examples=internal_ref_examples,
        context=["internal", "reference", "ref"],
        pattern_type="regex"
    )
    
    # Verify pattern created correctly
    assert pattern.entity_type == "INTERNAL_REFERENCE"
    assert len(pattern.patterns) > 0

def test_main_usage_example():
    """Test the main usage example from the README."""
    import allyanonimiser
    
    # Create an Allyanonimiser instance
    ally = allyanonimiser.create_allyanonimiser()
    
    # Process a text
    text = "Patient John Smith with policy number POL123456 reported a claim"
    result = ally.analyze(text)
    
    # Verify results
    assert len(result) > 0
    
    # Test specialized analyzers
    claim_analyzer = allyanonimiser.ClaimNotesAnalyzer()
    result = allyanonimiser.analyze_claim_note(text)
    
    # Verify claim analysis
    assert isinstance(result, dict)
    assert "pii_entities" in result

if __name__ == "__main__":
    # Run the tests
    print("Running tests...")
    test_quick_start_example()
    test_claim_notes_example()
    test_email_processing_example()
    test_creating_custom_patterns()
    test_main_usage_example()
    print("All tests passed!")