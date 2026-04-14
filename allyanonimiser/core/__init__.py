"""
Core detection and anonymization engine.
"""

from .analyzer import EnhancedAnalyzer, RecognizerResult
from .anonymizer import DEFAULT_ENTITY_PRIORITY, EnhancedAnonymizer
from .pattern_manager import CustomPatternDefinition, PatternManager
from .pattern_registry import PatternRegistry
from .validators import (
    validate_regex,
    validate_pattern_definition,
    check_pattern_against_examples,
)

__all__ = [
    "EnhancedAnalyzer",
    "RecognizerResult",
    "EnhancedAnonymizer",
    "CustomPatternDefinition",
    "PatternManager",
    "PatternRegistry",
    "validate_regex",
    "validate_pattern_definition",
    "check_pattern_against_examples",
]
