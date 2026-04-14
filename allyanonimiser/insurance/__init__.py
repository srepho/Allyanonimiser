"""
Insurance-specific analyzers for the Allyanonimiser package.
"""

__all__ = [
    'ClaimNotesAnalyzer',
    'analyze_claim_note',
]

from .claim_notes_analyzer import ClaimNotesAnalyzer, analyze_claim_note
