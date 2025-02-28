"""
Test configuration for Allyanonimiser.
"""

import os
import pytest
from allyanonimiser import create_allyanonimiser, CustomPatternDefinition

@pytest.fixture
def example_texts():
    """Return example texts for testing."""
    return {
        "simple": "John Smith's contact details are 0412 345 678 and john.smith@example.com.",
        "claim_note": """
        Claim #: CL-23456789
        Customer: John Smith
        Policy Number: POL-987654
        
        Mr. Smith reported an accident on 15/07/2023. His vehicle (Registration: ABC123) 
        was involved in a collision at George St, Sydney. His contact details are 
        0412 345 678 and john.smith@example.com.
        
        The customer's TFN (123 456 789) and Medicare number (2345 67890 1) 
        were verified for identity purposes.
        """
    }

@pytest.fixture
def example_entities():
    """Return expected entities for example texts."""
    return {
        "simple": [
            {"entity_type": "PERSON", "text": "John Smith"},
            {"entity_type": "AU_PHONE", "text": "0412 345 678"},
            {"entity_type": "EMAIL_ADDRESS", "text": "john.smith@example.com"}
        ]
    }

@pytest.fixture
def basic_analyzer():
    """Return a basic analyzer for testing."""
    return create_allyanonimiser().analyzer

@pytest.fixture
def custom_patterns():
    """Return custom patterns for testing."""
    return [
        CustomPatternDefinition(
            entity_type="TEST_ID",
            patterns=["TEST-\\d{5}"],
            context=["test", "id"],
            name="Test ID Pattern"
        ),
        CustomPatternDefinition(
            entity_type="PROJECT_ID",
            patterns=["PRJ-\\d{4}"],
            context=["project"],
            name="Project ID Pattern"
        ),
        CustomPatternDefinition(
            entity_type="ORDER_NUMBER",
            patterns=["ORD-\\d{6}"],
            context=["order", "purchase"],
            name="Order Number Pattern"
        )
    ]

@pytest.fixture
def analyzer_with_custom_patterns(basic_analyzer, custom_patterns):
    """Return an analyzer with custom patterns."""
    for pattern in custom_patterns:
        basic_analyzer.add_pattern(pattern)
    return basic_analyzer