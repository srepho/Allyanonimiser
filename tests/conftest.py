"""
Pytest configuration file for allyanonimiser tests.
"""

import pytest
import os
import sys

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