"""
Allyanonimiser - Australian-focused PII detection and anonymization for the insurance industry.
"""

__version__ = "0.1.8"

# First import the base classes and utilities
from .pattern_manager import CustomPatternDefinition, PatternManager
from .enhanced_analyzer import EnhancedAnalyzer
from .enhanced_anonymizer import EnhancedAnonymizer
from .pattern_registry import PatternRegistry

# Import pre-defined patterns
from .patterns.au_patterns import get_au_pattern_definitions
from .patterns.insurance_patterns import get_insurance_pattern_definitions
from .patterns.general_patterns import get_general_pattern_definitions

# Define factory functions for analyzers first
def create_au_analyzer():
    """
    Create an analyzer with Australian-specific patterns pre-configured.
    
    Returns:
        EnhancedAnalyzer with Australian patterns
    """
    analyzer = EnhancedAnalyzer()
    
    # Add Australian patterns
    au_patterns = get_au_pattern_definitions()
    for pattern_def in au_patterns:
        analyzer.add_pattern(CustomPatternDefinition(**pattern_def))
    
    return analyzer

def create_insurance_analyzer():
    """
    Create an analyzer with insurance-specific patterns pre-configured.
    
    Returns:
        EnhancedAnalyzer with insurance patterns
    """
    analyzer = EnhancedAnalyzer()
    
    # Add insurance patterns
    insurance_patterns = get_insurance_pattern_definitions()
    for pattern_def in insurance_patterns:
        analyzer.add_pattern(CustomPatternDefinition(**pattern_def))
    
    return analyzer

def create_au_insurance_analyzer():
    """
    Create an analyzer with both Australian and insurance patterns pre-configured.
    
    Returns:
        EnhancedAnalyzer with Australian and insurance patterns
    """
    analyzer = create_au_analyzer()
    
    # Add insurance patterns
    insurance_patterns = get_insurance_pattern_definitions()
    for pattern_def in insurance_patterns:
        analyzer.add_pattern(CustomPatternDefinition(**pattern_def))
    
    # Add general patterns
    general_patterns = get_general_pattern_definitions()
    for pattern_def in general_patterns:
        analyzer.add_pattern(CustomPatternDefinition(**pattern_def))
    
    return analyzer

# Now that factory functions are defined, import the remaining components
from .allyanonimiser import Allyanonimiser

# Import generators
from .generators.au_synthetic_data import AustralianSyntheticDataGenerator
from .generators.llm_augmenter import LLMAugmenter

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

from .utils.presidio_helpers import (
    create_pattern_from_regex,
    create_pattern_recognizer,
    combine_pattern_results,
    filter_results_by_score,
    filter_results_by_entity_type,
    results_to_dict,
    results_to_spans,
    evaluate_results
)

from .utils.long_text_processor import (
    LongTextProcessor,
    segment_long_text,
    extract_pii_rich_segments,
    analyze_claim_notes
)

from .validators import (
    validate_regex,
    validate_spacy_pattern,
    validate_context_list,
    validate_entity_type,
    validate_pattern_definition,
    test_pattern_against_examples
)

# Import insurance-specific utilities AFTER all factory functions are defined
from .insurance.claim_notes_analyzer import ClaimNotesAnalyzer, analyze_claim_note
from .insurance.email_analyzer import InsuranceEmailAnalyzer, analyze_insurance_email
from .insurance.medical_report_analyzer import MedicalReportAnalyzer, analyze_medical_report

# Create the primary interface
def create_allyanonimiser():
    """
    Create an Allyanonimiser instance with all patterns pre-configured.
    
    Returns:
        Allyanonimiser instance
    """
    analyzer = create_au_insurance_analyzer()
    anonymizer = EnhancedAnonymizer(analyzer=analyzer)
    return Allyanonimiser(analyzer=analyzer, anonymizer=anonymizer)

def create_pattern_from_examples(
    entity_type,
    examples,
    context=None,
    name=None,
    pattern_type="regex"
):
    """
    Create a custom pattern definition from examples.
    
    Args:
        entity_type: Entity type this pattern detects
        examples: List of example strings
        context: Optional list of context words
        name: Optional name for the pattern
        pattern_type: Type of pattern to create (regex or spacy)
        
    Returns:
        CustomPatternDefinition
    """
    if pattern_type == "regex":
        pattern = create_regex_from_examples(examples)
        patterns = [pattern]
    else:
        # Import here to avoid circular imports
        import spacy
        try:
            nlp = spacy.load("en_core_web_lg")
        except OSError:
            # Fallback to smaller model if large model not available
            nlp = spacy.load("en_core_web_sm")
        patterns = create_spacy_pattern_from_examples(nlp, examples, "token")
    
    return CustomPatternDefinition(
        entity_type=entity_type,
        patterns=patterns,
        context=context,
        name=name
    )