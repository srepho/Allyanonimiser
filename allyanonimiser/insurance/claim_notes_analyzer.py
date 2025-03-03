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
    """Analyze a claim note for PII entities and structured information."""
    analyzer = ClaimNotesAnalyzer()
    
    # Analyze the text for entities
    entities = analyzer.analyzer.analyze(note_text)
    
    # Convert entities to a dictionary format
    pii_entities = [
        {"entity_type": entity.entity_type, "text": entity.text, "score": entity.score}
        for entity in entities
    ]
    
    return {
        "text": note_text,
        "pii_entities": pii_entities,
        "incident_description": note_text[:100] + "..." if len(note_text) > 100 else note_text
    }