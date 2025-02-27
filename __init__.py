"""
Allyanonimiser - Australian-focused PII detection and anonymization for the insurance industry
"""

__version__ = "0.1.3"

# First, define factory functions to avoid circular imports
def create_au_analyzer(patterns=None):
    """Create an analyzer with Australian patterns."""
    from .patterns.au_patterns import get_au_pattern_definitions
    from .enhanced_analyzer import EnhancedAnalyzer
    
    au_patterns = patterns or get_au_pattern_definitions()
    return EnhancedAnalyzer(patterns=au_patterns, language="en")

def create_insurance_analyzer(patterns=None):
    """Create an analyzer with insurance-specific patterns."""
    from .patterns.insurance_patterns import get_insurance_pattern_definitions
    from .enhanced_analyzer import EnhancedAnalyzer
    
    insurance_patterns = patterns or get_insurance_pattern_definitions()
    return EnhancedAnalyzer(patterns=insurance_patterns, language="en")

def create_au_insurance_analyzer(patterns=None):
    """Create an analyzer with both Australian and insurance patterns."""
    from .patterns.au_patterns import get_au_pattern_definitions
    from .patterns.insurance_patterns import get_insurance_pattern_definitions
    from .enhanced_analyzer import EnhancedAnalyzer
    
    au_patterns = get_au_pattern_definitions()
    insurance_patterns = get_insurance_pattern_definitions()
    combined_patterns = au_patterns + insurance_patterns
    
    if patterns:
        combined_patterns.extend(patterns)
        
    return EnhancedAnalyzer(patterns=combined_patterns, language="en")

def create_pattern_from_examples(entity_type, examples, context=None, pattern_type="regex"):
    """Create a custom pattern definition from examples."""
    from .pattern_manager import CustomPatternDefinition
    from .utils.spacy_helpers import create_regex_from_examples
    
    if pattern_type == "regex":
        patterns = [create_regex_from_examples(examples)]
    else:
        patterns = examples
        
    return CustomPatternDefinition(
        entity_type=entity_type,
        patterns=patterns,
        context=context or [],
        name=f"{entity_type.lower()}_recognizer"
    )

def create_allyanonimiser(analyzer=None, custom_operators=None):
    """Create an Allyanonimiser instance with default configuration."""
    from .allyanonimiser import Allyanonimiser
    from .enhanced_anonymizer import EnhancedAnonymizer
    
    if analyzer is None:
        analyzer = create_au_insurance_analyzer()
        
    anonymizer = EnhancedAnonymizer(analyzer=analyzer, custom_operators=custom_operators)
    return Allyanonimiser(analyzer=analyzer, anonymizer=anonymizer)

# Then, regular imports
from .pattern_manager import CustomPatternDefinition, PatternManager
from .enhanced_analyzer import EnhancedAnalyzer
from .enhanced_anonymizer import EnhancedAnonymizer
from .pattern_registry import PatternRegistry
from .allyanonimiser import Allyanonimiser

# Import pre-defined patterns
from .patterns.au_patterns import get_au_pattern_definitions
from .patterns.insurance_patterns import get_insurance_pattern_definitions
from .patterns.general_patterns import get_general_pattern_definitions

# Import insurance module
from .insurance import (
    ClaimNotesAnalyzer,
    analyze_claim_note,
    InsuranceEmailAnalyzer,
    analyze_insurance_email,
    MedicalReportAnalyzer,
    analyze_medical_report
)

# Import utilities
from .utils.spacy_helpers import (
    create_spacy_pattern_from_examples,
    create_spacy_matcher,
    create_spacy_phrase_matcher,
    find_context_matches,
    extract_patterns_from_spans,
    create_regex_from_examples,
    get_entity_context,
    auto_generate_context_terms
)

# Import generators
from .generators.au_synthetic_data import AustralianSyntheticDataGenerator
from .generators.llm_augmenter import LLMAugmenter