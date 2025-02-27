"""
Pattern manager stub for testing.
"""

class CustomPatternDefinition:
    """Stub class for testing."""
    def __init__(self, **kwargs):
        self.entity_type = kwargs.get('entity_type')
        self.patterns = kwargs.get('patterns', [])
        self.context = kwargs.get('context')
        self.name = kwargs.get('name')

class PatternManager:
    """Stub class for testing."""
    def __init__(self):
        self.patterns = []