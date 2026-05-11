"""
Allyanonimiser - Australian-focused PII detection and anonymization for the insurance industry.
"""

# Core classes
# Config and main class
from .allyanonimiser import (
    Allyanonimiser,
    AnalysisConfig,
    AnonymizationConfig,
)
from .core.analyzer import EnhancedAnalyzer
from .core.anonymizer import EnhancedAnonymizer
from .core.pattern_manager import CustomPatternDefinition, PatternManager
from .core.pattern_registry import PatternRegistry

# IO processors
from .io.dataframe_processor import DataFrameProcessor

# Pre-defined patterns
from .patterns.au_patterns import get_au_pattern_definitions
from .patterns.general_intl_patterns import get_general_intl_pattern_definitions
from .patterns.general_patterns import get_general_pattern_definitions
from .patterns.insurance_patterns import get_insurance_pattern_definitions

try:
    from .io.stream_processor import POLARS_AVAILABLE, StreamProcessor
except ImportError:
    POLARS_AVAILABLE = False
    StreamProcessor = None

# Long text processing
# Validators
from .core.validators import (
    check_pattern_against_examples,
    test_pattern_against_examples,
    validate_context_list,
    validate_entity_type,
    validate_pattern_definition,
    validate_regex,
    validate_spacy_pattern,
)

# Insurance-specific
from .insurance.claim_notes_analyzer import ClaimNotesAnalyzer, analyze_claim_note
from .utils.long_text_processor import (
    LongTextProcessor,
    analyze_claim_notes,
    extract_pii_rich_segments,
    segment_long_text,
)
from .utils.presidio_helpers import (
    create_pattern_from_regex,
    create_pattern_recognizer,
    filter_results_by_entity_type,
    filter_results_by_score,
    results_to_dict,
)

# Pattern helpers
from .utils.spacy_helpers import (
    create_regex_from_examples,
    create_spacy_pattern_from_examples,
    detect_common_format,
)

__version__ = "3.5.0"

# Named spaCy model presets — use these instead of the bare strings to make
# the deployment-vs-accuracy tradeoff explicit at call sites.
#
# - SPACY_MODEL_FAST (en_core_web_sm, ~44 MB): the default. Pattern-based
#   detection (TFN/ABN/MEDICARE/AU_PHONE/EMAIL/dates/etc.) is unaffected.
#   NER quality drops noticeably for PERSON, LOCATION, and ORG entities.
# - SPACY_MODEL_ACCURATE (en_core_web_lg, ~587 MB): higher NER recall on
#   names, places, and organizations. Costs ~2-5s extra cold-start and
#   ~1.5 GB resident memory; not friendly to slim serverless environments.
SPACY_MODEL_FAST = "en_core_web_sm"
SPACY_MODEL_ACCURATE = "en_core_web_lg"

__all__ = [
    # Core
    "Allyanonimiser", "AnalysisConfig", "AnonymizationConfig",
    "EnhancedAnalyzer", "EnhancedAnonymizer",
    "CustomPatternDefinition", "PatternManager", "PatternRegistry",
    # IO
    "DataFrameProcessor", "StreamProcessor", "POLARS_AVAILABLE",
    # Patterns
    "get_au_pattern_definitions", "get_insurance_pattern_definitions",
    "get_general_pattern_definitions", "get_general_intl_pattern_definitions",
    # Validators
    "validate_regex", "validate_spacy_pattern", "validate_context_list",
    "validate_entity_type", "validate_pattern_definition",
    "check_pattern_against_examples", "test_pattern_against_examples",
    # Insurance
    "ClaimNotesAnalyzer", "analyze_claim_note",
    # Text processing
    "LongTextProcessor", "segment_long_text", "extract_pii_rich_segments",
    "analyze_claim_notes",
    # Helpers
    "create_spacy_pattern_from_examples", "create_regex_from_examples",
    "detect_common_format", "create_pattern_from_regex",
    "create_pattern_recognizer", "filter_results_by_score",
    "filter_results_by_entity_type", "results_to_dict",
    # Factories
    "create_analyzer", "create_unified_analyzer",
    "create_allyanonimiser", "create_pattern_from_examples",
    # spaCy model presets
    "SPACY_MODEL_FAST", "SPACY_MODEL_ACCURATE",
]

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
        get_general_intl_pattern_definitions,
    ):
        for pdef in getter():
            analyzer.add_pattern(CustomPatternDefinition(**pdef))
    return analyzer


# Alias
create_unified_analyzer = create_analyzer


def create_allyanonimiser(
    pattern_filepath: str | None = None,
    settings_path: str | None = None,
    enable_caching: bool = True,
    max_cache_size: int = 10_000,
    spacy_model: str | None = SPACY_MODEL_FAST,
) -> Allyanonimiser:
    """Create a fully configured Allyanonimiser instance.

    The default ``spacy_model`` is ``SPACY_MODEL_FAST`` (``en_core_web_sm``,
    ~44 MB). Pattern-based detection is identical regardless of model;
    ``SPACY_MODEL_ACCURATE`` (``en_core_web_lg``, ~587 MB) gives noticeably
    better NER recall for ``PERSON``, ``LOCATION``, and ``ORG`` entities at
    the cost of ~2-5s extra startup and ~1.5 GB resident memory.

    See ``allyanonimiser.allyanonimiser.create_allyanonimiser`` for the
    full parameter list. This wrapper forwards all keyword arguments.
    """
    from .allyanonimiser import create_allyanonimiser as _create
    return _create(
        pattern_filepath=pattern_filepath,
        settings_path=settings_path,
        enable_caching=enable_caching,
        max_cache_size=max_cache_size,
        spacy_model=spacy_model,
    )


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
        from .core.analyzer import load_spacy_model
        # Match the library default: try the small model first, then large
        # if installed. The shared loader already handles the blank fallback.
        nlp = load_spacy_model(SPACY_MODEL_FAST, fallback_model=SPACY_MODEL_ACCURATE)
        patterns = create_spacy_pattern_from_examples(nlp, examples, "token")

    return CustomPatternDefinition(
        entity_type=entity_type,
        patterns=patterns,
        context=context,
        name=name,
    )
