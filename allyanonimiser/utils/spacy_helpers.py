"""
spaCy helpers for the Allyanonimiser package - stub for testing.
"""

def load_spacy_model(model_name="en_core_web_lg", fallback_model="en_core_web_sm"):
    """Stub function for testing."""
    return None

def create_spacy_pattern_from_examples(nlp, examples, pattern_type="token"):
    """Stub function for testing."""
    return [{"LOWER": "test"}]

def create_spacy_matcher(nlp, patterns, entity_type):
    """Stub function for testing."""
    return None

def create_spacy_phrase_matcher(nlp, phrases, entity_type):
    """Stub function for testing."""
    return None

def find_context_matches(doc, context_terms):
    """Stub function for testing."""
    return []

def extract_patterns_from_spans(spans):
    """Stub function for testing."""
    return []

def create_regex_from_examples(examples):
    """Stub function for testing."""
    return r"test"

def get_entity_context(doc, entity_span, window_size=5):
    """Stub function for testing."""
    return ""

def auto_generate_context_terms(examples, n=5):
    """Stub function for testing."""
    return ["test"]