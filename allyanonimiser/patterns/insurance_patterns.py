"""
Insurance patterns stub for testing.
"""

def get_insurance_pattern_definitions():
    """Stub function returning sample patterns."""
    return [
        {
            "entity_type": "POLICY_NUMBER",
            "patterns": [r"\b(?:POL|P-)\d{6}\b"],
            "context": ["policy", "insurance", "coverage"],
            "name": "Insurance Policy Number"
        }
    ]