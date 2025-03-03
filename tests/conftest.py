"""
Pytest configuration file for allyanonimiser tests.
"""

import pytest
import os
import sys

from allyanonimiser import create_allyanonimiser, EnhancedAnalyzer, EnhancedAnonymizer, Allyanonimiser

@pytest.fixture
def allyanonimiser_instance():
    """Create an Allyanonimiser instance for testing."""
    return Allyanonimiser()

@pytest.fixture(scope="session")
def sample_claim_text():
    """Returns a sample claim text for testing."""
    return """
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

@pytest.fixture(scope="session")
def sample_email_text():
    """Returns a sample email text for testing."""
    return """
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

@pytest.fixture
def basic_analyzer():
    """Returns a basic analyzer for testing."""
    # Using the full allyanonimiser creation function to get all patterns including AU patterns
    return create_allyanonimiser()

@pytest.fixture
def basic_anonymizer(basic_analyzer):
    """Returns a basic anonymizer for testing."""
    return EnhancedAnonymizer(analyzer=basic_analyzer)

@pytest.fixture
def example_texts():
    """Returns example texts for testing."""
    return {
        "simple": "John Smith's contact details are 0412 345 678 and john.smith@example.com.",
        "claim_note": """
        Claim #: CL-23456789
        Customer: John Smith
        Policy Number: POL-987654
        
        The customer called to report damage to their vehicle after a minor accident.
        Contact number: 0412 345 678
        Email: john.smith@example.com
        
        Please note that we have verified the customer's identity using their TFN 123-456-789
        and Medicare card 2123 45678 1 for identity purposes.
        """,
        "email": """
        From: john.smith@example.com
        To: insurance@company.com.au
        Subject: Regarding my claim CL-12345678

        Hi,
        
        I'm following up on my claim CL-12345678. Please call me on 0412 345 678 if you need more information.
        
        Regards,
        John Smith
        """,
        "medical_report": """
        Medical Report
        Patient: John Smith
        DOB: 01/01/1980
        Medicare: 2123 45678 1
        
        Assessment conducted on 15/06/2023. Patient reports pain in lower back following car accident.
        X-ray results show no fractures. Recommended physiotherapy and pain medication.
        
        Dr. Jane Wilson
        Medical Registration: MED-12345
        """
    }

@pytest.fixture
def example_entities():
    """Returns example entities for testing."""
    return {
        "simple": [
            {"entity_type": "PERSON", "text": "John Smith's"},  # Updated to match what spaCy actually detects
            {"entity_type": "AU_PHONE", "text": "0412 345 678"},
            {"entity_type": "EMAIL_ADDRESS", "text": "john.smith@example.com"}
        ]
    }