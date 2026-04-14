"""
Allyanonimiser - Australian-focused PII detection and anonymization for the insurance industry.
"""

__version__ = "3.0.0"

# Core classes
from .core.pattern_manager import CustomPatternDefinition, PatternManager
from .core.analyzer import EnhancedAnalyzer
from .core.anonymizer import EnhancedAnonymizer
from .core.pattern_registry import PatternRegistry

# Pre-defined patterns
from .patterns.au_patterns import get_au_pattern_definitions
from .patterns.insurance_patterns import get_insurance_pattern_definitions
from .patterns.general_patterns import get_general_pattern_definitions

# Config and main class
from .allyanonimiser import (
    Allyanonimiser,
    AnonymizationConfig,
    AnalysisConfig,
)

# IO processors
from .io.dataframe_processor import DataFrameProcessor

try:
    from .io.stream_processor import StreamProcessor, POLARS_AVAILABLE
except ImportError:
    POLARS_AVAILABLE = False
    StreamProcessor = None

# Long text processing
from .utils.long_text_processor import (
    LongTextProcessor,
    segment_long_text,
    extract_pii_rich_segments,
    analyze_claim_notes,
)

# Validators
from .core.validators import (
    validate_regex,
    validate_spacy_pattern,
    validate_context_list,
    validate_entity_type,
    validate_pattern_definition,
    check_pattern_against_examples,
    test_pattern_against_examples,
)

# Insurance-specific
from .insurance.claim_notes_analyzer import ClaimNotesAnalyzer, analyze_claim_note

# Pattern helpers
from .utils.spacy_helpers import (
    create_spacy_pattern_from_examples,
    create_regex_from_examples,
    detect_common_format,
)

from .utils.presidio_helpers import (
    create_pattern_from_regex,
    create_pattern_recognizer,
    filter_results_by_score,
    filter_results_by_entity_type,
    results_to_dict,
)


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def create_analyzer() -> EnhancedAnalyzer:
    """Create an analyzer pre-loaded with all default patterns."""
    analyzer = EnhancedAnalyzer()
    for getter in (
        get_au_pattern_definitions,
        get_insurance_pattern_definitions,
        get_general_pattern_definitions,
    ):
        for pdef in getter():
            analyzer.add_pattern(CustomPatternDefinition(**pdef))
    return analyzer


# Alias
create_unified_analyzer = create_analyzer


def create_allyanonimiser(
    pattern_filepath=None, settings_path=None
) -> Allyanonimiser:
    """Create a fully configured Allyanonimiser instance."""
    from .allyanonimiser import create_allyanonimiser as _create
    return _create(pattern_filepath, settings_path)


def create_pattern_from_examples(
    entity_type: str,
    examples: list,
    context: list = None,
    name: str = None,
    pattern_type: str = "regex",
    generalization_level: str = "none",
) -> CustomPatternDefinition:
    """Create a pattern definition from example strings."""
    if pattern_type == "regex":
        from .utils.spacy_helpers import create_regex_from_examples as _create_regex
        pattern = _create_regex(examples, generalization_level=generalization_level)
        patterns = [pattern]
    else:
        import spacy
        try:
            nlp = spacy.load("en_core_web_lg")
        except OSError:
            nlp = spacy.load("en_core_web_sm")
        patterns = create_spacy_pattern_from_examples(nlp, examples, "token")

    return CustomPatternDefinition(
        entity_type=entity_type,
        patterns=patterns,
        context=context,
        name=name,
    )
