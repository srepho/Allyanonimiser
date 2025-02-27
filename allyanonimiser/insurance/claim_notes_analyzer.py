"""
Specialized analyzer for insurance claim notes - stub for testing.
"""

from ..utils.long_text_processor import LongTextProcessor
from ..enhanced_analyzer import EnhancedAnalyzer

# Don't import create_au_insurance_analyzer from top-level module
# Instead, create a local analyzer instance

class ClaimNotesAnalyzer:
    """
    Specialized analyzer for extracting structured information from claim notes.
    """
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or EnhancedAnalyzer()
        self.processor = LongTextProcessor()

def analyze_claim_note(note_text):
    """Stub function for testing."""
    analyzer = ClaimNotesAnalyzer()
    return {"text": note_text}