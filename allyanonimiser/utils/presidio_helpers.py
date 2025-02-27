"""
Presidio helpers for the Allyanonimiser package - stub for testing.
"""

def create_pattern_from_regex(pattern, name, score=1.0):
    """Stub function for testing."""
    return {"pattern": pattern, "name": name, "score": score}

def create_pattern_recognizer(patterns, entity_type, context=None, supported_language="en"):
    """Stub function for testing."""
    return None

def combine_pattern_results(results_a, results_b):
    """Stub function for testing."""
    return []

def filter_results_by_score(results, min_score=0.7):
    """Stub function for testing."""
    return []

def filter_results_by_entity_type(results, entity_types):
    """Stub function for testing."""
    return []

def results_to_dict(results):
    """Stub function for testing."""
    return {}

def results_to_spans(results, text):
    """Stub function for testing."""
    return []

def evaluate_results(true_positives, false_positives, false_negatives):
    """Stub function for testing."""
    return {"precision": 1.0, "recall": 1.0, "f1": 1.0}