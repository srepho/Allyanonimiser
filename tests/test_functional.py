"""
Functional tests for Allyanonimiser package.

These tests verify that the key functions and interfaces in the package
work correctly when called with valid inputs.
"""

from allyanonimiser import (
    Allyanonimiser,
    EnhancedAnalyzer,
    analyze_claim_notes,
    create_allyanonimiser,
    create_analyzer,
)


def test_create_analyzer():
    """Test create_analyzer factory function."""
    analyzer = create_analyzer()
    assert isinstance(analyzer, EnhancedAnalyzer)
    assert len(analyzer.patterns) > 0


def test_create_allyanonimiser():
    """Test create_allyanonimiser factory function."""
    ally = create_allyanonimiser()
    assert isinstance(ally, Allyanonimiser)
    assert hasattr(ally, "process")
    assert hasattr(ally, "analyze")
    assert hasattr(ally, "anonymize")


def test_analyze_returns_results():
    """Test that analyze returns entity results."""
    ally = create_allyanonimiser()
    results = ally.analyze("John Smith called from 0412 345 678")
    assert len(results) > 0
    entity_types = {r.entity_type for r in results}
    assert "PERSON" in entity_types or "AU_PHONE" in entity_types


def test_anonymize_replaces_entities():
    """Test that anonymize replaces detected entities."""
    ally = create_allyanonimiser()
    result = ally.anonymize("Please contact John Smith at john.smith@example.com")
    assert "text" in result
    assert "John Smith" not in result["text"]


def test_process_returns_full_result():
    """Test that process returns analysis + anonymized text."""
    ally = create_allyanonimiser()
    result = ally.process("John Smith's email is john.smith@example.com")
    assert "analysis" in result
    assert "anonymized" in result
    assert "entities" in result["analysis"]


def test_analyze_claim_notes():
    """Test the claim notes analysis function."""
    result = analyze_claim_notes(
        "Spoke with insured John Smith regarding policy POL-123456"
    )
    assert isinstance(result, dict)
    assert "pii_segments" in result
