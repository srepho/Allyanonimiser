"""
Pytest configuration file for Allyanonimiser tests.
"""

import os
import sys
import pytest

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def example_texts():
    """Fixture providing example texts with PII for testing."""
    return {
        "simple": "My name is John Smith and my email is john.smith@example.com.",
        "claim_note": """
            Claim Reference: CL-23456789
            Customer: John Smith
            Policy Number: POL-987654

            Customer called to report a vehicle accident that occurred on 15/07/2023. 
            Customer was driving his Toyota Corolla (Registration: ABC123, VIN: 1HGCM82633A123456) 
            when another vehicle collided with him at the intersection of George St and Market St, Sydney.

            Customer Details:
            Name: John Smith
            DOB: 14/08/1985
            Phone: 0412 345 678
            Email: john.smith@example.com
            Address: 123 Main St, Sydney NSW 2000
            TFN: 123 456 789
            """,
        "email": """
            From: adjuster@insurance.com.au
            To: john.smith@example.com
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
            """,
        "medical_report": """
            PATIENT: John Smith
            DOB: 14/08/1985
            MEDICARE: 2345 67890 1
            
            ASSESSMENT:
            Patient presented with lower back pain following a vehicle accident on 15/07/2023.
            X-rays show no fractures but mild disc compression at L4-L5.
            
            TREATMENT PLAN:
            1. Prescribed pain relief: Paracetamol 500mg, 2 tablets every 4-6 hours
            2. Referral to physiotherapy
            3. Follow-up appointment in 2 weeks
            
            Dr. Jane Wilson
            Medical Practitioner
            Medicare Provider: 123456AB
            """
    }

@pytest.fixture
def example_entities():
    """Fixture providing expected entity detection results for examples."""
    return {
        "simple": [
            {"entity_type": "PERSON", "text": "John Smith"},
            {"entity_type": "EMAIL_ADDRESS", "text": "john.smith@example.com"}
        ],
        "claim_note": [
            {"entity_type": "INSURANCE_CLAIM_NUMBER", "text": "CL-23456789"},
            {"entity_type": "PERSON", "text": "John Smith"},
            {"entity_type": "INSURANCE_POLICY_NUMBER", "text": "POL-987654"},
            {"entity_type": "DATE", "text": "15/07/2023"},
            {"entity_type": "VEHICLE_REGISTRATION", "text": "ABC123"},
            {"entity_type": "VEHICLE_VIN", "text": "1HGCM82633A123456"},
            {"entity_type": "AU_ADDRESS", "text": "123 Main St, Sydney NSW 2000"},
            {"entity_type": "AU_PHONE", "text": "0412 345 678"},
            {"entity_type": "EMAIL_ADDRESS", "text": "john.smith@example.com"},
            {"entity_type": "AU_TFN", "text": "123 456 789"}
        ]
    }

@pytest.fixture
def challenging_examples():
    """Fixture providing challenging examples for testing."""
    return [
        {
            "text": "You can reach me at j.o.h.n.smith@exa-mple.com for any questions",
            "entity_type": "EMAIL_ADDRESS",
            "entity_value": "j.o.h.n.smith@exa-mple.com",
            "start": 19,
            "end": 44,
            "difficulty": "hard",
            "explanation": "This email has periods between each letter of the name and a hyphen in the domain, which could confuse some detectors."
        },
        {
            "text": "The policy number is P-O-L-1-2-3-4-5-6-7 (with dashes for clarity)",
            "entity_type": "INSURANCE_POLICY_NUMBER",
            "entity_value": "P-O-L-1-2-3-4-5-6-7",
            "start": 20,
            "end": 38,
            "difficulty": "hard",
            "explanation": "This policy number has dashes between each character, which can confuse pattern matching."
        },
        {
            "text": "The vehicle with reg ABC 123 (that's A as in Alpha, B as in Bravo, C as in Charlie) was involved in an accident.",
            "entity_type": "VEHICLE_REGISTRATION",
            "entity_value": "ABC 123",
            "start": 21,
            "end": 28,
            "difficulty": "medium",
            "explanation": "The registration is followed by a phonetic explanation of the letters, which might confuse systems that check for context."
        }
    ]

@pytest.fixture
def au_synthetic_data_generator():
    """Fixture for the Australian Synthetic Data Generator."""
    from allyanonimiser.generators.au_synthetic_data import AustralianSyntheticDataGenerator
    return AustralianSyntheticDataGenerator()

@pytest.fixture
def temp_dataset_dir(tmpdir):
    """Fixture providing a temporary directory for datasets."""
    dataset_dir = tmpdir.mkdir("test_dataset")
    return str(dataset_dir)

@pytest.fixture
def basic_analyzer():
    """Fixture providing a basic analyzer with Australian patterns."""
    from allyanonimiser import create_au_insurance_analyzer
    return create_au_insurance_analyzer()

@pytest.fixture
def basic_anonymizer(basic_analyzer):
    """Fixture providing a basic anonymizer."""
    from allyanonimiser import EnhancedAnonymizer
    return EnhancedAnonymizer(analyzer=basic_analyzer)

@pytest.fixture
def allyanonimiser_instance():
    """Fixture providing an instance of the main Allyanonimiser interface."""
    from allyanonimiser import Allyanonimiser, create_au_insurance_analyzer
    analyzer = create_au_insurance_analyzer()
    return Allyanonimiser(analyzer=analyzer)