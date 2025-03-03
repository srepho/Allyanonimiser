"""
Patterns package for the Allyanonimiser package.

This package contains predefined patterns for entity detection.
"""

from .au_patterns import get_au_pattern_definitions
from .general_patterns import get_general_pattern_definitions
from .insurance_patterns import get_insurance_pattern_definitions

__all__ = ["get_au_pattern_definitions", "get_general_pattern_definitions", "get_insurance_pattern_definitions"]