"""
Utility functions for working with spaCy.
"""

import os
import re
from typing import List, Dict, Any, Optional, Union, Tuple, Set
import spacy
from spacy.tokens import Doc, Span
from spacy.matcher import Matcher, PhraseMatcher
from spacy.language import Language

def load_spacy_model(model_name="en_core_web_lg", fallback_model="en_core_web_sm"):
    """
    Load a spaCy language model with fallback to a smaller model if needed.
    
    Args:
        model_name: Primary model name to load
        fallback_model: Fallback model if primary isn't available
        
    Returns:
        Loaded spaCy Language model
    """
    try:
        return spacy.load(model_name)
    except OSError:
        try:
            # Try the fallback model
            return spacy.load(fallback_model)
        except OSError:
            # If all else fails, use the blank model
            return spacy.blank("en")

def create_spacy_pattern_from_examples(
    nlp: Language,
    examples: List[str],
    pattern_type: str = "token"
) -> List[Dict[str, Any]]:
    """
    Create a spaCy pattern from example texts.
    
    Args:
        nlp: spaCy Language model
        examples: List of example texts
        pattern_type: Type of pattern to create (token or phrase)
        
    Returns:
        List of spaCy pattern dictionaries or list of Doc objects for PhraseMatcher
    """
    if pattern_type == "token":
        patterns = []
        for example in examples:
            doc = nlp(example)
            pattern = []
            
            for token in doc:
                # Create pattern element for token
                pattern_element = {
                    "LOWER": token.lower_
                }
                
                # Add optional POS, lemma, etc.
                if token.is_alpha and len(token.text) > 3:
                    pattern_element["POS"] = token.pos_
                
                pattern.append(pattern_element)
            
            patterns.append(pattern)
        
        return patterns
    
    elif pattern_type == "phrase":
        # Create Doc objects for PhraseMatcher
        return [nlp(example) for example in examples]
    
    else:
        raise ValueError(f"Unsupported pattern type: {pattern_type}")

def create_spacy_matcher(
    nlp: Language,
    patterns: List[Dict[str, Any]],
    matcher_name: str = "custom_matcher"
) -> Matcher:
    """
    Create a spaCy Matcher with patterns.
    
    Args:
        nlp: spaCy Language model
        patterns: List of pattern dictionaries
        matcher_name: Name for the matcher rule
        
    Returns:
        spaCy Matcher object
    """
    matcher = Matcher(nlp.vocab)
    matcher.add(matcher_name, patterns)
    return matcher

def create_spacy_phrase_matcher(
    nlp: Language,
    phrases: List[str],
    matcher_name: str = "custom_phrase_matcher"
) -> PhraseMatcher:
    """
    Create a spaCy PhraseMatcher with phrases.
    
    Args:
        nlp: spaCy Language model
        phrases: List of phrases to match
        matcher_name: Name for the matcher rule
        
    Returns:
        spaCy PhraseMatcher object
    """
    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp(phrase) for phrase in phrases]
    matcher.add(matcher_name, patterns)
    return matcher

def find_context_matches(
    doc: Doc,
    entity_span: Span,
    context_terms: List[str],
    window_size: int = 5
) -> List[Tuple[str, int]]:
    """
    Find context terms near an entity in a document.
    
    Args:
        doc: spaCy Doc object
        entity_span: Entity span to look for context around
        context_terms: List of context terms to look for
        window_size: Size of the context window on each side
        
    Returns:
        List of (term, distance) tuples for matched context terms
    """
    # Convert context terms to lowercase set for faster lookup
    context_set = {term.lower() for term in context_terms}
    
    # Get entity token indices
    start, end = entity_span.start, entity_span.end
    
    # Define context window
    window_start = max(0, start - window_size)
    window_end = min(len(doc), end + window_size)
    
    # Find context matches
    context_matches = []
    
    # Check tokens before entity
    for i in range(window_start, start):
        token = doc[i]
        if token.lower_ in context_set:
            distance = start - i
            context_matches.append((token.text, distance))
    
    # Check tokens after entity
    for i in range(end, window_end):
        token = doc[i]
        if token.lower_ in context_set:
            distance = i - end + 1
            context_matches.append((token.text, distance))
    
    return context_matches

def extract_patterns_from_spans(
    doc: Doc,
    spans: List[Span],
    generalize: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract patterns from entity spans that can be used for matching similar entities.
    
    Args:
        doc: spaCy Doc object
        spans: List of entity spans
        generalize: Whether to generalize the patterns
        
    Returns:
        List of spaCy pattern dictionaries
    """
    patterns = []
    
    for span in spans:
        pattern = []
        
        for token in span:
            # Create basic pattern element
            pattern_element = {}
            
            if generalize:
                # Generalize based on token properties
                if token.is_digit:
                    pattern_element["IS_DIGIT"] = True
                elif token.like_num:
                    pattern_element["LIKE_NUM"] = True
                elif token.is_alpha:
                    if token.is_lower:
                        pattern_element["IS_LOWER"] = True
                    elif token.is_upper:
                        pattern_element["IS_UPPER"] = True
                    elif token.is_title:
                        pattern_element["IS_TITLE"] = True
                    
                    if len(token.text) > 3:
                        pattern_element["POS"] = token.pos_
                else:
                    # Special characters or mixed
                    pattern_element["ORTH"] = token.text
            else:
                # Exact matching
                pattern_element["LOWER"] = token.lower_
            
            pattern.append(pattern_element)
        
        patterns.append(pattern)
    
    return patterns

def create_regex_from_examples(examples: List[str], generalization_level: str = "none") -> str:
    """
    Create a regex pattern from example strings with optional generalization.
    
    This function generates regular expression patterns with different levels of flexibility
    based on the provided examples. Higher generalization levels create patterns that can
    match more variations of the examples.
    
    Args:
        examples (List[str]): List of example strings to generate pattern from
        generalization_level (str, optional): Level of pattern generalization:
            - "none": Exact match only (OR-joined escaped examples)
            - "low": Basic generalization (common structure with digit/letter classes)
            - "medium": Smart pattern with format detection for common formats
            - "high": Advanced generalization with structural analysis
        
    Returns:
        str: Regex pattern string that can be used with re.match/re.search
        
    Examples:
        >>> # Exact matching (no generalization)
        >>> create_regex_from_examples(["REF-12345", "REF-67890"], "none")
        '(REF\\-12345)|(REF\\-67890)'
        
        >>> # Low generalization - preserves structure but generalizes digits
        >>> create_regex_from_examples(["REF-12345", "REF-67890"], "low")
        'REF\\-\\d+'
        
        >>> # Medium generalization - detects common formats
        >>> create_regex_from_examples(["ABC-12345", "DEF-67890"], "medium")
        '[A-Z]{3}-\\d{5}'
        
        >>> # High generalization - advanced structural analysis
        >>> create_regex_from_examples(["Customer: ABC (2023)", "Customer: XYZ (2024)"], "high")
        'Customer: [A-Z]+ \\(\\d{4}\\)'
        
        >>> # Automatic format detection (works at medium+ levels)
        >>> create_regex_from_examples(["user@example.com", "john.doe@company.org"], "medium")
        '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'
    
    Raises:
        ValueError: If examples list is empty or generalization_level is not supported
    """
    if not examples:
        raise ValueError("At least one example string is required")
    
    # Just use exact matching for non-generalized patterns
    if generalization_level == "none":
        # Escape special regex characters
        escaped_examples = [re.escape(example) for example in examples]
        
        # Join with OR
        return '|'.join(f'({example})' for example in escaped_examples)
    
    # For generalized patterns, we need to analyze the examples
    if generalization_level == "low":
        return create_simple_generalized_regex(examples)
    elif generalization_level == "medium":
        return create_generalized_regex(examples)
    elif generalization_level == "high":
        return create_advanced_generalized_regex(examples)
    else:
        raise ValueError(f"Unsupported generalization level: {generalization_level}")

def create_simple_generalized_regex(examples: List[str]) -> str:
    """
    Create a simple generalized regex by detecting common character classes.
    
    This low-level generalization replaces digits with \d and preserves structure.
    
    Args:
        examples: List of example strings
        
    Returns:
        Generalized regex pattern
    """
    if len(examples) == 1:
        # With just one example, replace digits and leave the rest
        return re.sub(r'\d+', r'\\d+', re.escape(examples[0]))
    
    # Find common prefixes and suffixes among examples
    prefix = os.path.commonprefix(examples)
    
    # Reverse strings to find common suffix
    reversed_examples = [example[::-1] for example in examples]
    suffix_reversed = os.path.commonprefix(reversed_examples)
    suffix = suffix_reversed[::-1]
    
    # For very short examples or no common parts, fall back to OR pattern
    if len(prefix) < 2 and len(suffix) < 2:
        return create_regex_from_examples(examples, generalization_level="none")
    
    # Extract variable middle parts
    middle_parts = []
    for example in examples:
        if prefix and suffix:
            if prefix + suffix == example:  # Edge case: prefix and suffix overlap
                middle = ""
            else:
                middle = example[len(prefix):-len(suffix) if suffix else None]
        elif prefix:
            middle = example[len(prefix):]
        elif suffix:
            middle = example[:-len(suffix)]
        else:
            middle = example
        middle_parts.append(middle)
    
    # Analyze middle parts to create a pattern
    if all(middle.isdigit() for middle in middle_parts if middle):
        # All middle parts are numeric
        middle_pattern = r'\d+'
    elif all(middle.isalpha() for middle in middle_parts if middle):
        # All middle parts are alphabetic
        if all(middle.isupper() for middle in middle_parts if middle):
            middle_pattern = r'[A-Z]+'
        elif all(middle.islower() for middle in middle_parts if middle):
            middle_pattern = r'[a-z]+'
        else:
            middle_pattern = r'[A-Za-z]+'
    else:
        # Mixed content
        if len(set(middle_parts)) <= 3:
            # Small set of values, use enumeration
            middle_pattern = '|'.join(f'({re.escape(middle)})' for middle in set(middle_parts))
        else:
            # Many values, use wildcard
            middle_pattern = r'.*?'
    
    # Build the final pattern
    pattern = ''
    if prefix:
        pattern += re.escape(prefix)
    if middle_pattern:
        if '|' in middle_pattern:
            pattern += f'({middle_pattern})'
        else:
            pattern += middle_pattern
    if suffix:
        pattern += re.escape(suffix)
    
    return pattern

def create_generalized_regex(examples: List[str]) -> str:
    """
    Create a medium-level generalized regex by analyzing patterns in the examples.
    
    This analyzes structure across examples to create more flexible patterns.
    
    Args:
        examples: List of example strings
        
    Returns:
        Generalized regex pattern
    """
    # Identify common formats like dates, phone numbers, IDs
    format_pattern = detect_common_format(examples)
    if format_pattern:
        return format_pattern
    
    # Split examples into character-by-character sequences for analysis
    if len(examples) == 1:
        # With a single example, do character class generalization
        return generalize_single_example(examples[0])
    
    # Try structure-based generalization for multiple examples
    return analyze_structure_for_regex(examples)

def create_advanced_generalized_regex(examples: List[str]) -> str:
    """
    Create a highly-generalized regex by combining multiple techniques.
    
    This uses advanced pattern detection with tokenization and semantic analysis.
    
    Args:
        examples: List of example strings
        
    Returns:
        Generalized regex pattern
    """
    # Check for common formats (like create_generalized_regex)
    format_pattern = detect_common_format(examples)
    if format_pattern:
        return format_pattern
    
    # If examples are long/complex, tokenize and analyze
    if any(len(ex) > 15 for ex in examples):
        return create_tokenized_pattern(examples)
    
    # For short examples, try fragment analysis
    segments = segment_examples(examples)
    if segments:
        pattern_parts = []
        for segment in segments:
            # Analyze segment patterns across examples
            if is_fixed_segment(segment, examples):
                pattern_parts.append(re.escape(segment))
            else:
                var_segment_pattern = generalize_variable_segment(segment, examples)
                pattern_parts.append(var_segment_pattern)
        return ''.join(pattern_parts)
    
    # Fall back to medium generalization if segmentation failed
    return create_generalized_regex(examples)

def generalize_single_example(example: str) -> str:
    """
    Generalize a single example by replacing character classes.
    
    Args:
        example: Example string to generalize
        
    Returns:
        Generalized regex pattern
    """
    pattern = ''
    # Process the example character by character
    i = 0
    while i < len(example):
        char = example[i]
        
        # Count repeated characters
        repeat_count = 1
        while i + repeat_count < len(example) and example[i + repeat_count] == char:
            repeat_count += 1
        
        # Create pattern segment based on character type
        if char.isdigit():
            if repeat_count > 1:
                pattern += fr'\d{{{repeat_count}}}'
            else:
                # Look ahead for more digits
                j = i + 1
                while j < len(example) and example[j].isdigit():
                    j += 1
                digit_count = j - i
                if digit_count > 1:
                    pattern += fr'\d{{{digit_count}}}'
                    i = j - 1  # Adjust index (subtract 1 because of the later increment)
                else:
                    pattern += r'\d'
        elif char.isalpha():
            if char.isupper():
                if repeat_count > 1:
                    pattern += fr'[A-Z]{{{repeat_count}}}'
                else:
                    # Look ahead for more uppercase letters
                    j = i + 1
                    while j < len(example) and example[j].isalpha() and example[j].isupper():
                        j += 1
                    upper_count = j - i
                    if upper_count > 1:
                        pattern += fr'[A-Z]{{{upper_count}}}'
                        i = j - 1  # Adjust index
                    else:
                        pattern += r'[A-Z]'
            elif char.islower():
                if repeat_count > 1:
                    pattern += fr'[a-z]{{{repeat_count}}}'
                else:
                    # Look ahead for more lowercase letters
                    j = i + 1
                    while j < len(example) and example[j].isalpha() and example[j].islower():
                        j += 1
                    lower_count = j - i
                    if lower_count > 1:
                        pattern += fr'[a-z]{{{lower_count}}}'
                        i = j - 1  # Adjust index
                    else:
                        pattern += r'[a-z]'
            else:
                pattern += r'[A-Za-z]'
        elif char.isspace():
            pattern += r'\s'
        else:
            # Special character
            pattern += re.escape(char)
        
        i += 1
    
    return pattern

def detect_common_format(examples: List[str]) -> Optional[str]:
    """
    Detect if examples match common formats and return appropriate regex.
    
    Args:
        examples: List of examples to analyze
        
    Returns:
        Regex for the detected format or None if no common format detected
    """
    # List of (check_function, regex_pattern) tuples
    format_checkers = [
        # Date formats
        (lambda ex: re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$', ex), r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
        (lambda ex: re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$', ex), r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'),
        
        # Phone numbers
        (lambda ex: re.match(r'^(\+\d{1,3}|\(\d{1,3}\))?\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$', ex), 
         r'(\+\d{1,3}|\(\d{1,3}\))?\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'),
        
        # Email addresses
        (lambda ex: re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', ex),
         r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        
        # IP addresses
        (lambda ex: re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ex), r'(\d{1,3}\.){3}\d{1,3}'),
        
        # URLs
        (lambda ex: re.match(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?$', ex),
         r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?'),
        
        # ID formats (like XX-12345)
        (lambda ex: re.match(r'^[A-Z]{2,3}-\d{4,7}$', ex), r'[A-Z]{2,3}-\d{4,7}'),
        
        # Money amounts
        (lambda ex: re.match(r'^\$\d{1,3}(,\d{3})*(\.\d{2})?$', ex), r'\$\d{1,3}(,\d{3})*(\.\d{2})?'),
    ]
    
    # Check if all examples match a specific format
    for check_func, pattern in format_checkers:
        if all(check_func(ex) for ex in examples):
            return pattern
    
    return None

def analyze_structure_for_regex(examples: List[str]) -> str:
    """
    Analyze the structure of examples to generate a flexible regex.
    
    Args:
        examples: List of examples to analyze
        
    Returns:
        Generalized regex pattern
    """
    # For short examples with reasonable variation, try positional analysis
    if all(len(ex) < 30 for ex in examples) and len(examples) > 1:
        # Try to align examples and analyze character distributions at each position
        max_len = max(len(ex) for ex in examples)
        min_len = min(len(ex) for ex in examples)
        
        # If length variance is too high, fall back to simpler pattern
        if max_len > min_len * 2:
            return create_simple_generalized_regex(examples)
        
        # Analyze positional patterns
        pattern_parts = []
        
        # Handle prefixes/suffixes first
        prefix = os.path.commonprefix(examples)
        if prefix and len(prefix) > 1:
            pattern_parts.append(re.escape(prefix))
            # Remove prefix from examples for further analysis
            examples = [ex[len(prefix):] for ex in examples]
        
        # Reverse strings to find common suffix
        reversed_examples = [ex[::-1] for ex in examples]
        suffix_reversed = os.path.commonprefix(reversed_examples)
        suffix = suffix_reversed[::-1]
        
        # If we have both clear prefix and suffix, analyze the middle
        if prefix and suffix and len(suffix) > 1:
            middles = [ex[:-len(suffix)] for ex in examples]
            if all(middles) or not any(middles):  # All have middle or none have middle
                if all(middle.isdigit() for middle in middles if middle):
                    pattern_parts.append(r'\d+')
                elif all(middle.isalpha() for middle in middles if middle):
                    if all(middle.isupper() for middle in middles if middle):
                        pattern_parts.append(r'[A-Z]+')
                    elif all(middle.islower() for middle in middles if middle):
                        pattern_parts.append(r'[a-z]+')
                    else:
                        pattern_parts.append(r'[A-Za-z]+')
                else:
                    # Mixed or complex content
                    length_range = [len(middle) for middle in middles if middle]
                    if length_range:
                        min_mid_len, max_mid_len = min(length_range), max(length_range)
                        if max_mid_len - min_mid_len <= 2:  # Small variance
                            pattern_parts.append(fr'\w{{{min_mid_len},{max_mid_len}}}')
                        else:
                            pattern_parts.append(r'\w+')
                    else:
                        pattern_parts.append(r'\w*')
            else:
                # Inconsistent middle parts
                pattern_parts.append(r'.*?')
            
            pattern_parts.append(re.escape(suffix))
            return ''.join(pattern_parts)
    
    # Fall back to simple generalization for complex cases
    return create_simple_generalized_regex(examples)

def create_tokenized_pattern(examples: List[str]) -> str:
    """
    Create a pattern by tokenizing examples and analyzing token patterns.
    
    Args:
        examples: List of example strings
        
    Returns:
        Generalized regex pattern
    """
    # Simple tokenization by splitting on whitespace and punctuation
    tokenized_examples = []
    for example in examples:
        # Split on whitespace and keep separators
        tokens = []
        for part in re.split(r'(\s+)', example):
            if part:
                # Further split on punctuation and keep separators
                subparts = re.split(r'([^\w\s])', part)
                tokens.extend(subpart for subpart in subparts if subpart)
        tokenized_examples.append(tokens)
    
    # Create pattern segments for each position
    pattern_parts = []
    max_tokens = max(len(tokens) for tokens in tokenized_examples)
    
    for pos in range(max_tokens):
        tokens_at_pos = [tokens[pos] if pos < len(tokens) else None for tokens in tokenized_examples]
        tokens_at_pos = [t for t in tokens_at_pos if t is not None]
        
        if not tokens_at_pos:
            continue
        
        if len(set(tokens_at_pos)) == 1:
            # Same token in all examples
            pattern_parts.append(re.escape(tokens_at_pos[0]))
        elif all(token.isdigit() for token in tokens_at_pos):
            # All tokens are numeric
            length_range = [len(token) for token in tokens_at_pos]
            min_len, max_len = min(length_range), max(length_range)
            if min_len == max_len:
                pattern_parts.append(fr'\d{{{min_len}}}')
            else:
                pattern_parts.append(fr'\d{{{min_len},{max_len}}}')
        elif all(token.isalpha() for token in tokens_at_pos):
            # All tokens are alphabetic
            if all(token.isupper() for token in tokens_at_pos):
                pattern_parts.append(r'[A-Z]+')
            elif all(token.islower() for token in tokens_at_pos):
                pattern_parts.append(r'[a-z]+')
            else:
                pattern_parts.append(r'[A-Za-z]+')
        elif all(token.isspace() for token in tokens_at_pos):
            # All tokens are whitespace
            pattern_parts.append(r'\s+')
        elif all(re.match(r'^[^\w\s]$', token) for token in tokens_at_pos):
            # All tokens are single punctuation
            if len(set(tokens_at_pos)) <= 3:
                punct_chars = set(tokens_at_pos)
                pattern_parts.append(f'[{"".join(re.escape(c) for c in punct_chars)}]')
            else:
                pattern_parts.append(r'[^\w\s]')
        else:
            # Mixed content or variable tokens
            length_range = [len(token) for token in tokens_at_pos]
            min_len, max_len = min(length_range), max(length_range)
            if min_len == max_len and min_len <= 2:
                # Short tokens of fixed length - could be separators or codes
                pattern_parts.append(fr'.{{{min_len}}}')
            else:
                # Longer variable tokens
                pattern_parts.append(r'\S+')
    
    return ''.join(pattern_parts)

def is_fixed_segment(segment: str, examples: List[str]) -> bool:
    """
    Check if a segment appears consistently in examples.
    
    Args:
        segment: Segment to check
        examples: List of examples
        
    Returns:
        True if segment is fixed across examples
    """
    return all(segment in example for example in examples)

def generalize_variable_segment(segment: str, examples: List[str]) -> str:
    """
    Create a pattern for a variable segment across examples.
    
    Args:
        segment: Segment to generalize
        examples: List of examples
        
    Returns:
        Generalized pattern for the segment
    """
    # Extract corresponding segments from examples
    segment_variants = []
    for example in examples:
        # This is a simplified approach - in a real implementation, 
        # you would need more sophisticated segment matching
        if segment in example:
            segment_variants.append(segment)
        else:
            # Find similar segments using fuzzy matching
            # For now, just using a simplistic approach
            for i in range(len(example) - len(segment) + 1):
                candidate = example[i:i+len(segment)]
                if len(set(candidate) & set(segment)) / len(segment) > 0.7:
                    segment_variants.append(candidate)
                    break
    
    if not segment_variants:
        return r'\S+'
    
    # Analyze segment variants
    if all(var.isdigit() for var in segment_variants):
        return r'\d+'
    elif all(var.isalpha() for var in segment_variants):
        if all(var.isupper() for var in segment_variants):
            return r'[A-Z]+'
        elif all(var.islower() for var in segment_variants):
            return r'[a-z]+'
        else:
            return r'[A-Za-z]+'
    else:
        return r'\S+'

def segment_examples(examples: List[str]) -> List[str]:
    """
    Segment examples into common parts for analysis.
    
    Args:
        examples: List of examples
        
    Returns:
        List of common segments or empty list if segmentation failed
    """
    # This is a placeholder for a more sophisticated segmentation algorithm
    # In a real implementation, you would use techniques like:
    # - Longest common subsequence
    # - Multiple sequence alignment
    # - Character n-gram analysis
    
    # For now, we'll use a simple approach with common prefix/suffix
    prefix = os.path.commonprefix(examples)
    if not prefix or len(prefix) < 2:
        return []
    
    # Remove prefix and check for common suffix
    examples_without_prefix = [ex[len(prefix):] for ex in examples]
    reversed_examples = [ex[::-1] for ex in examples_without_prefix]
    suffix_reversed = os.path.commonprefix(reversed_examples)
    suffix = suffix_reversed[::-1]
    
    if not suffix or len(suffix) < 2:
        if prefix:
            return [prefix]
        return []
    
    # Return segments
    return [prefix, suffix]

def get_entity_context(
    doc: Doc,
    entity_spans: List[Span],
    window_size: int = 5
) -> Dict[str, List[str]]:
    """
    Extract context words around entities.
    
    Args:
        doc: spaCy Doc object
        entity_spans: List of entity spans
        window_size: Size of context window on each side
        
    Returns:
        Dictionary mapping entity text to list of context words
    """
    context_dict = {}
    
    for span in entity_spans:
        # Get entity text
        entity_text = span.text
        
        # Define context window
        start, end = span.start, span.end
        window_start = max(0, start - window_size)
        window_end = min(len(doc), end + window_size)
        
        # Extract context words
        context_words = []
        
        # Add words before entity
        for i in range(window_start, start):
            token = doc[i]
            if token.is_alpha and not token.is_stop:
                context_words.append(token.lemma_)
        
        # Add words after entity
        for i in range(end, window_end):
            token = doc[i]
            if token.is_alpha and not token.is_stop:
                context_words.append(token.lemma_)
        
        # Store context
        if entity_text not in context_dict:
            context_dict[entity_text] = []
            
        context_dict[entity_text].extend(context_words)
    
    return context_dict

def auto_generate_context_terms(
    docs: List[Doc],
    entity_type: str,
    top_n: int = 20
) -> List[str]:
    """
    Automatically generate context terms for an entity type from a corpus.
    
    Args:
        docs: List of spaCy Doc objects
        entity_type: Entity type to find context for
        top_n: Number of top context terms to return
        
    Returns:
        List of context terms
    """
    # Collect all entity spans of the target type
    entity_spans = []
    for doc in docs:
        for ent in doc.ents:
            if ent.label_ == entity_type:
                entity_spans.append(ent)
    
    # No entities found
    if not entity_spans:
        return []
    
    # Get context for all entities
    all_context = []
    for doc in docs:
        entity_context = get_entity_context(doc, [span for span in doc.ents if span.label_ == entity_type])
        for context_words in entity_context.values():
            all_context.extend(context_words)
    
    # Count term frequencies
    term_counts = {}
    for term in all_context:
        term_counts[term] = term_counts.get(term, 0) + 1
    
    # Sort by frequency
    sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N terms
    return [term for term, count in sorted_terms[:top_n]]