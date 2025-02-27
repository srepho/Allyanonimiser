"""
Main interface for the Allyanonimiser package - stub for testing.
"""

from .enhanced_analyzer import EnhancedAnalyzer
from .enhanced_anonymizer import EnhancedAnonymizer
from .utils.long_text_processor import (
    analyze_claim_notes,
    extract_pii_rich_segments,
    segment_long_text
)

class Allyanonimiser:
    """
    Main interface for PII detection and anonymization of mixed content - stub for testing.
    """
    def __init__(self, analyzer=None, anonymizer=None):
        self.analyzer = analyzer or EnhancedAnalyzer()
        self.anonymizer = anonymizer or EnhancedAnonymizer(analyzer=self.analyzer)