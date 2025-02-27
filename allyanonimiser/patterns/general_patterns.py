"""
General patterns stub for testing.
"""

def get_general_pattern_definitions():
    """Stub function returning sample patterns."""
    return [
        {
            "entity_type": "CREDIT_CARD",
            "patterns": [r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b"],
            "context": ["credit", "card", "visa", "mastercard"],
            "name": "Credit Card Number"
        }
    ]