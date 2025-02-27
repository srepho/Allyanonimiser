"""
Validation utilities for pattern definitions.
"""

import re
from typing import List, Dict, Any, Optional, Union, Tuple

def validate_regex(regex: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a regular expression pattern.
    
    Args:
        regex: Regular expression to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        re.compile(regex)
        return True, None
    except re.error as e:
        return False, str(e)

def validate_spacy_pattern(pattern: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validate a spaCy token pattern.
    
    Args:
        pattern: spaCy token pattern
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(pattern, list):
        return False, "Pattern must be a list of dictionaries"
    
    if len(pattern) == 0:
        return False, "Pattern cannot be empty"
    
    for i, token_dict in enumerate(pattern):
        if not isinstance(token_dict, dict):
            return False, f"Token at position {i} must be a dictionary"
        
        # Check for known spaCy token attributes
        valid_attrs = {
            "ORTH", "TEXT", "LOWER", "UPPER", "IS_ALPHA", "IS_DIGIT", "IS_LOWER",
            "IS_UPPER", "IS_TITLE", "IS_PUNCT", "IS_SPACE", "IS_STOP", "LIKE_NUM",
            "LIKE_URL", "LIKE_EMAIL", "POS", "TAG", "DEP", "LEMMA", "SHAPE", "ENT_TYPE",
            "LENGTH", "REGEX"
        }
        
        for attr in token_dict:
            if attr not in valid_attrs:
                return False, f"Invalid token attribute '{attr}' at position {i}"
    
    return True, None

def validate_context_list(context: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a list of context words.
    
    Args:
        context: List of context words
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(context, list):
        return False, "Context must be a list of strings"
    
    for i, word in enumerate(context):
        if not isinstance(word, str):
            return False, f"Context word at position {i} must be a string"
        
        if not word.strip():
            return False, f"Context word at position {i} cannot be empty"
    
    return True, None

def validate_entity_type(entity_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an entity type string.
    
    Args:
        entity_type: Entity type to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(entity_type, str):
        return False, "Entity type must be a string"
    
    if not entity_type.strip():
        return False, "Entity type cannot be empty"
    
    # Check for valid format (alphanumeric and underscores)
    if not re.match(r'^[A-Z][A-Z0-9_]*$', entity_type):
        return False, "Entity type must start with a capital letter and contain only uppercase letters, numbers, and underscores"
    
    return True, None

def validate_pattern_definition(pattern_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a pattern definition dictionary.
    
    Args:
        pattern_def: Pattern definition dictionary
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "is_valid": True,
        "errors": {}
    }
    
    # Validate entity type
    if "entity_type" not in pattern_def:
        validation_results["is_valid"] = False
        validation_results["errors"]["entity_type"] = "Entity type is required"
    else:
        entity_valid, entity_error = validate_entity_type(pattern_def["entity_type"])
        if not entity_valid:
            validation_results["is_valid"] = False
            validation_results["errors"]["entity_type"] = entity_error
    
    # Validate patterns
    if "patterns" not in pattern_def:
        validation_results["is_valid"] = False
        validation_results["errors"]["patterns"] = "Patterns are required"
    else:
        patterns = pattern_def["patterns"]
        if not isinstance(patterns, list):
            validation_results["is_valid"] = False
            validation_results["errors"]["patterns"] = "Patterns must be a list"
        elif len(patterns) == 0:
            validation_results["is_valid"] = False
            validation_results["errors"]["patterns"] = "Patterns list cannot be empty"
        else:
            pattern_errors = []
            
            for i, pattern in enumerate(patterns):
                if isinstance(pattern, str):
                    # Validate regex pattern
                    regex_valid, regex_error = validate_regex(pattern)
                    if not regex_valid:
                        pattern_errors.append(f"Invalid regex pattern at position {i}: {regex_error}")
                elif isinstance(pattern, list):
                    # Validate spaCy pattern
                    spacy_valid, spacy_error = validate_spacy_pattern(pattern)
                    if not spacy_valid:
                        pattern_errors.append(f"Invalid spaCy pattern at position {i}: {spacy_error}")
                else:
                    pattern_errors.append(f"Pattern at position {i} must be a string (regex) or a list (spaCy pattern)")
            
            if pattern_errors:
                validation_results["is_valid"] = False
                validation_results["errors"]["patterns"] = pattern_errors
    
    # Validate context
    if "context" in pattern_def:
        context_valid, context_error = validate_context_list(pattern_def["context"])
        if not context_valid:
            validation_results["is_valid"] = False
            validation_results["errors"]["context"] = context_error
    
    # Validate name
    if "name" in pattern_def and not isinstance(pattern_def["name"], str):
        validation_results["is_valid"] = False
        validation_results["errors"]["name"] = "Name must be a string"
    
    # Validate score
    if "score" in pattern_def:
        score = pattern_def["score"]
        if not isinstance(score, (int, float)):
            validation_results["is_valid"] = False
            validation_results["errors"]["score"] = "Score must be a number"
        elif score < 0 or score > 1:
            validation_results["is_valid"] = False
            validation_results["errors"]["score"] = "Score must be between 0 and 1"
    
    return validation_results

def test_pattern_against_examples(
    pattern: str,
    positive_examples: List[str],
    negative_examples: List[str]
) -> Dict[str, Any]:
    """
    Test a regex pattern against positive and negative examples.
    
    Args:
        pattern: Regex pattern to test
        positive_examples: Examples that should match
        negative_examples: Examples that should not match
        
    Returns:
        Dictionary with test results
    """
    # Validate the pattern first
    valid, error = validate_regex(pattern)
    if not valid:
        return {
            "is_valid": False,
            "error": error,
            "positive_matches": [],
            "positive_non_matches": positive_examples,
            "negative_matches": [],
            "negative_non_matches": negative_examples
        }
    
    # Compile the pattern
    regex = re.compile(pattern)
    
    # Test positive examples
    positive_matches = []
    positive_non_matches = []
    for example in positive_examples:
        match = regex.search(example)
        if match:
            positive_matches.append({
                "text": example,
                "match": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
        else:
            positive_non_matches.append(example)
    
    # Test negative examples
    negative_matches = []
    negative_non_matches = []
    for example in negative_examples:
        match = regex.search(example)
        if match:
            negative_matches.append({
                "text": example,
                "match": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
        else:
            negative_non_matches.append(example)
    
    # Calculate accuracy metrics
    true_positives = len(positive_matches)
    false_negatives = len(positive_non_matches)
    false_positives = len(negative_matches)
    true_negatives = len(negative_non_matches)
    
    total = true_positives + false_negatives + false_positives + true_negatives
    accuracy = (true_positives + true_negatives) / total if total > 0 else 0
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "is_valid": True,
        "positive_matches": positive_matches,
        "positive_non_matches": positive_non_matches,
        "negative_matches": negative_matches,
        "negative_non_matches": negative_non_matches,
        "metrics": {
            "true_positives": true_positives,
            "false_negatives": false_negatives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    }