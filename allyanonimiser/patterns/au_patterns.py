"""
Australian patterns stub for testing.
"""

def get_au_pattern_definitions():
    """Stub function returning sample patterns."""
    return [
        {
            "entity_type": "AU_TFN",
            "patterns": [r"\b\d{3}\s*\d{3}\s*\d{3}\b"],
            "context": ["tax", "file", "number", "TFN"],
            "name": "Australian Tax File Number"
        }
    ]