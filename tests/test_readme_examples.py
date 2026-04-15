"""
Tests to validate the examples in the README.md file.
This ensures that the documented examples actually work as expected.
"""

import pytest


def test_quick_start_example():
    """Test the quick start example from the README."""
    from allyanonimiser import create_analyzer

    analyzer = create_analyzer()

    results = analyzer.analyze(
        text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123.",
        language="en",
    )

    assert len(results) > 0
    entity_types = [result.entity_type for result in results]
    assert any("POLICY" in entity_type for entity_type in entity_types)
    assert any("VEHICLE" in entity_type for entity_type in entity_types)


def test_claim_notes_example():
    """Test the claim notes example from the README."""
    from allyanonimiser import analyze_claim_notes

    claim_note = """
    Claim Details:
    Spoke with the insured John Smith (TFN: 123 456 782) regarding damage to his vehicle ABC123.
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

    analysis = analyze_claim_notes(claim_note)

    assert "incident_description" in analysis
    assert "pii_segments" in analysis
    assert len(analysis["pii_segments"]) > 0

    from allyanonimiser import EnhancedAnonymizer, create_analyzer

    anonymizer = EnhancedAnonymizer(analyzer=create_analyzer())
    anonymized = anonymizer.anonymize(claim_note)

    assert "text" in anonymized
    assert "John Smith" not in anonymized["text"]


def test_creating_custom_patterns():
    """Test the custom pattern creation example from the README."""
    from allyanonimiser import create_pattern_from_examples

    pattern = create_pattern_from_examples(
        entity_type="INTERNAL_REFERENCE",
        examples=[
            "Internal reference: REF-12345",
            "Ref Number: REF-98765",
            "Reference: REF-55555",
        ],
        context=["internal", "reference", "ref"],
        pattern_type="regex",
    )

    assert pattern.entity_type == "INTERNAL_REFERENCE"
    assert len(pattern.patterns) > 0


def test_main_usage_example():
    """Test the main usage example from the README."""
    import allyanonimiser

    ally = allyanonimiser.create_allyanonimiser()

    text = "Patient John Smith with policy number POL123456 reported a claim"
    result = ally.analyze(text)

    assert len(result) > 0

    result = allyanonimiser.analyze_claim_note(text)

    assert isinstance(result, dict)
    assert "pii_entities" in result
