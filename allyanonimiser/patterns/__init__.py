"""
Pattern definitions for entity recognition in Australian and insurance contexts.

This module provides pattern definitions for:
- Australian-specific identifiers (TFNs, Medicare numbers, driver's licenses)
- Insurance-specific identifiers (policy numbers, claim references)
- General patterns that work across domains
"""

from .au_patterns import get_au_pattern_definitions
from .insurance_patterns import get_insurance_pattern_definitions
from .general_patterns import get_general_pattern_definitions

__all__ = [
    'get_au_pattern_definitions',
    'get_insurance_pattern_definitions',
    'get_general_pattern_definitions'
]