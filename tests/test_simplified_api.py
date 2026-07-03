"""
Tests for the API: configuration objects, acronym management,
pattern management, DataFrame processing, and custom operators.
"""

import pytest
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig


def test_configuration_objects():
    """Test that configuration objects work properly."""
    ally = create_allyanonimiser()

    analysis_config = AnalysisConfig(
        language="en",
        active_entity_types=["PERSON", "EMAIL_ADDRESS"],
        min_score_threshold=0.8,
        expand_acronyms=False,
    )

    anonymization_config = AnonymizationConfig(
        operators={"PERSON": "replace", "EMAIL_ADDRESS": "mask"},
        age_bracket_size=10,
        keep_postcode=True,
    )

    text = "John Smith (john.smith@example.com) sent an email."
    result = ally.process(
        text=text,
        analysis_config=analysis_config,
        anonymization_config=anonymization_config,
    )

    assert "<PERSON>" in result["anonymized"]
    entities = [e["entity_type"] for e in result["analysis"]["entities"]]
    assert "PERSON" in entities
    assert "EMAIL_ADDRESS" in entities


def test_configuration_object_inheritance():
    """Test that config objects override individual parameters."""
    ally = create_allyanonimiser()

    text = """
    John Smith (DOB: 15/06/1980)
    Phone: 0412 345 678
    Email: john.smith@example.com
    Address: 123 Main Street, Sydney NSW 2000
    """

    result = ally.process(
        text=text,
        active_entity_types=["PERSON"],  # should be overridden
        analysis_config=AnalysisConfig(
            active_entity_types=["EMAIL_ADDRESS", "AU_PHONE"]
        ),
    )

    entities = [e["entity_type"] for e in result["analysis"]["entities"]]
    assert "EMAIL_ADDRESS" in entities
    assert "AU_PHONE" in entities
    assert "PERSON" not in entities


def test_acronym_management():
    """Test explicit acronym management methods."""
    ally = create_allyanonimiser()

    ally.add_acronyms(
        {"TPD": "Total and Permanent Disability", "CTP": "Compulsory Third Party"}
    )

    acronyms = ally.get_acronyms()
    assert "TPD" in acronyms
    assert acronyms["TPD"] == "Total and Permanent Disability"

    ally.remove_acronyms(["TPD"])
    updated = ally.get_acronyms()
    assert "TPD" not in updated
    assert "CTP" in updated


def test_pattern_creation():
    """Test create_pattern_from_examples."""
    ally = create_allyanonimiser()

    pattern = ally.create_pattern_from_examples(
        entity_type="TEST_ID",
        examples=["TEST-123", "TEST-456"],
        generalization_level="medium",
    )

    # Verify the pattern object was created correctly
    assert pattern.entity_type == "TEST_ID"
    assert len(pattern.patterns) >= 1

    # Test with an exact match from the examples
    result = ally.process("Reference number: TEST-123")
    entities = [e["entity_type"] for e in result["analysis"]["entities"]]
    assert "TEST_ID" in entities


def test_process_dataframe():
    """Test DataFrame processing with real data."""
    import pandas as pd

    ally = create_allyanonimiser()
    df = pd.DataFrame(
        {"notes": ["John Smith called from 0412 345 678", "No PII here."]}
    )

    result = ally.process_dataframe(df=df, column="notes", operation="anonymize")
    assert result is not None
    assert len(result) == 2


def test_pyarrow_integration():
    """Test DataFrame processing works (PyArrow is optional)."""
    import pandas as pd

    ally = create_allyanonimiser()
    df = pd.DataFrame({"notes": ["Email john@example.com for details"]})

    result = ally.process_dataframe(df=df, column="notes", operation="anonymize")
    assert result is not None


def test_custom_anonymization_operator(mocker):
    """Test that custom operators are passed through correctly."""
    ally = create_allyanonimiser()

    ally.anonymizer.anonymize = mocker.MagicMock()
    ally.anonymizer.anonymize.return_value = {"text": "anonymized text"}

    custom_operators = {"PERSON": "custom", "EMAIL_ADDRESS": "mask"}
    config = AnonymizationConfig(operators=custom_operators)

    ally.anonymize("test text", config=config)

    ally.anonymizer.anonymize.assert_called_with(
        "test text",
        custom_operators,
        "en",
        age_bracket_size=5,
        keep_postcode=True,
        active_entity_types=None,
    )
