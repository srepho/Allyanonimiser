"""
General patterns for detecting common PII.
"""

def get_general_pattern_definitions():
    """Return patterns for common PII detection."""
    return [
        {
            "entity_type": "CREDIT_CARD",
            "patterns": [r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b"],
            "context": ["credit", "card", "visa", "mastercard", "payment"],
            "name": "Credit Card Number"
        },
        {
            "entity_type": "PERSON",
            "patterns": [
                r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",
                r"\bName:\s*[A-Z][a-z]+\s+[A-Z][a-z]+\b",
                r"\bCustomer:\s*[A-Z][a-z]+\s+[A-Z][a-z]+\b"
            ],
            "context": ["name", "person", "customer", "insured", "patient"],
            "name": "Person Name"
        },
        {
            "entity_type": "EMAIL_ADDRESS",
            "patterns": [r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
            "context": ["email", "contact", "mail", "@"],
            "name": "Email Address"
        },
        {
            "entity_type": "DATE_OF_BIRTH",
            "patterns": [
                r"\bDOB:\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
                r"\bDate of Birth:\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
                r"\bBirth Date:\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"
            ],
            "context": ["dob", "birth", "date", "born"],
            "name": "Date of Birth"
        },
        {
            "entity_type": "LOCATION",
            "patterns": [
                r"\b(?:Sydney|Melbourne|Brisbane|Perth|Adelaide|Hobart|Canberra|Darwin)(?:,\s*(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT))?\b",
                r"\b(?:New South Wales|Victoria|Queensland|Western Australia|South Australia|Tasmania|Northern Territory|Australian Capital Territory)\b"
            ],
            "context": ["location", "city", "state", "place", "at"],
            "name": "Location"
        },
        {
            "entity_type": "DATE",
            "patterns": [r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"],
            "context": ["date", "on", "when", "time", "day"],
            "name": "Date"
        },
        {
            "entity_type": "MONEY_AMOUNT",
            "patterns": [r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b"],
            "context": ["amount", "payment", "cost", "price", "value"],
            "name": "Money Amount"
        },
        {
            "entity_type": "ORGANIZATION",
            "patterns": [
                r"\b(?:Insurance|Insurances|Bank|Financial|Services|Motors|Mechanics)\b",
                r"\b[A-Z][a-z]+\s+(?:Insurance|Bank|Financial|Services|Motors|Mechanics)\b"
            ],
            "context": ["company", "organization", "business", "firm"],
            "name": "Organization"
        }
    ]