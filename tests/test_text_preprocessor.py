"""
Tests for the text preprocessor functionality.
"""
import pytest
from allyanonimiser.utils.text_preprocessor import (
    TextPreprocessor,
    create_text_preprocessor,
    preprocess_with_acronym_expansion
)
from allyanonimiser import create_allyanonimiser

def test_text_preprocessor_initialization():
    """Test initializing a TextPreprocessor."""
    # Default initialization
    preprocessor = TextPreprocessor()
    assert preprocessor.acronym_dict == {}
    assert preprocessor.case_sensitive is False
    
    # With custom acronyms
    acronyms = {"TP": "Third Party", "TL": "Team Leader"}
    preprocessor = TextPreprocessor(acronym_dict=acronyms)
    assert preprocessor.acronym_dict == acronyms
    
    # With case sensitivity
    preprocessor = TextPreprocessor(case_sensitive=True)
    assert preprocessor.case_sensitive is True

def test_add_acronyms():
    """Test adding acronyms to the dictionary."""
    preprocessor = TextPreprocessor()
    
    # Add initial acronyms
    preprocessor.add_acronyms({"TP": "Third Party"})
    assert preprocessor.acronym_dict == {"TP": "Third Party"}
    
    # Add more acronyms
    preprocessor.add_acronyms({"TL": "Team Leader", "MGR": "Manager"})
    assert preprocessor.acronym_dict == {
        "TP": "Third Party",
        "TL": "Team Leader",
        "MGR": "Manager"
    }
    
    # Override existing acronym
    preprocessor.add_acronyms({"TP": "Trading Partner"})
    assert preprocessor.acronym_dict["TP"] == "Trading Partner"

def test_remove_acronyms():
    """Test removing acronyms from the dictionary."""
    preprocessor = TextPreprocessor(acronym_dict={
        "TP": "Third Party",
        "TL": "Team Leader",
        "MGR": "Manager"
    })
    
    # Remove one acronym
    preprocessor.remove_acronyms(["TP"])
    assert "TP" not in preprocessor.acronym_dict
    assert "TL" in preprocessor.acronym_dict
    
    # Remove multiple acronyms
    preprocessor.remove_acronyms(["TL", "MGR"])
    assert preprocessor.acronym_dict == {}
    
    # Remove non-existent acronym (should not error)
    preprocessor.remove_acronyms(["ABC"])
    assert preprocessor.acronym_dict == {}

def test_expand_acronyms():
    """Test expanding acronyms in text."""
    acronyms = {
        "TP": "Third Party",
        "TL": "Team Leader",
        "PII": "Personally Identifiable Information"
    }
    preprocessor = TextPreprocessor(acronym_dict=acronyms)
    
    # Test basic expansion
    text = "The TP reported an issue to the TL."
    processed_text, expansions = preprocessor.expand_acronyms(text)
    
    expected_text = "The Third Party reported an issue to the Team Leader."
    assert processed_text == expected_text
    assert len(expansions) == 2
    
    # Test with no acronyms
    text = "No acronyms in this text."
    processed_text, expansions = preprocessor.expand_acronyms(text)
    assert processed_text == text
    assert len(expansions) == 0
    
    # Test with empty dictionary
    preprocessor = TextPreprocessor()
    text = "TP and TL"
    processed_text, expansions = preprocessor.expand_acronyms(text)
    assert processed_text == text
    assert len(expansions) == 0
    
    # Test with case sensitivity
    preprocessor = TextPreprocessor(acronym_dict={"TP": "Third Party"}, case_sensitive=True)
    text = "TP and tp"
    processed_text, expansions = preprocessor.expand_acronyms(text)
    assert processed_text == "Third Party and tp"
    assert len(expansions) == 1
    
    # Test with multiple occurrences
    preprocessor = TextPreprocessor(acronym_dict={"TP": "Third Party"})
    text = "TP reported to TP again"
    processed_text, expansions = preprocessor.expand_acronyms(text)
    assert processed_text == "Third Party reported to Third Party again"
    assert len(expansions) == 2

def test_word_boundaries():
    """Test that acronym expansion respects word boundaries."""
    preprocessor = TextPreprocessor(acronym_dict={"TP": "Third Party"})
    
    # Should expand
    text = "The TP filed a claim."
    processed_text, _ = preprocessor.expand_acronyms(text)
    assert processed_text == "The Third Party filed a claim."
    
    # Should not expand (part of another word)
    text = "The ATP filed a claim."
    processed_text, _ = preprocessor.expand_acronyms(text)
    assert processed_text == text
    
    text = "The TPR filed a claim."
    processed_text, _ = preprocessor.expand_acronyms(text)
    assert processed_text == text

def test_preprocess_text():
    """Test the preprocess_text method."""
    preprocessor = TextPreprocessor(acronym_dict={"TP": "Third Party"})
    
    text = "TP reported an issue."
    processed_text, metadata = preprocessor.preprocess_text(text)
    
    assert processed_text == "Third Party reported an issue."
    assert len(metadata["expansions"]) == 1
    assert metadata["expansions"][0]["acronym"] == "TP"
    assert metadata["expansions"][0]["expansion"] == "Third Party"

def test_factory_functions():
    """Test the factory functions for creating preprocessors."""
    # Test create_text_preprocessor
    acronyms = {"TP": "Third Party"}
    preprocessor = create_text_preprocessor(acronym_dict=acronyms)
    
    assert preprocessor.acronym_dict == acronyms
    assert isinstance(preprocessor, TextPreprocessor)
    
    # Test convenience function
    text = "TP reported an issue."
    processed_text = preprocess_with_acronym_expansion(text, acronyms)
    
    assert processed_text == "Third Party reported an issue."

def test_integration_with_allyanonimiser():
    """Test integration with the Allyanonimiser class."""
    # Create an Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Set acronyms
    acronyms = {
        "TP": "Third Party", 
        "TL": "Team Leader",
        "PII": "Personally Identifiable Information"
    }
    ally.set_acronym_dictionary(acronyms)
    
    # Test analyze with acronym expansion
    text = "The TP reported PII exposure to the TL."
    results = ally.analyze(text, expand_acronyms=True)
    
    # The analyzer should be working on the expanded text
    # The exact entities will depend on the analyzer configuration,
    # but we can check that analysis happened
    assert results is not None
    
    # Test anonymize with acronym expansion
    anonymized = ally.anonymize(text, expand_acronyms=True)
    
    # The anonymized text should contain expansions
    assert anonymized is not None
    assert "Third Party" in anonymized["text"] or "<PERSON>" in anonymized["text"]
    
    # Test process with acronym expansion
    result = ally.process(text, expand_acronyms=True)
    
    # Check that the preprocessing metadata is included
    assert "preprocessing" in result
    assert "expanded_acronyms" in result["preprocessing"]
    assert len(result["preprocessing"]["expanded_acronyms"]) == 3