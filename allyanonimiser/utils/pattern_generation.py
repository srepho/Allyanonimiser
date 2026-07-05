"""Generate regex patterns from example strings.

This is the engine behind ``create_pattern_from_examples`` /
``create_regex_from_examples`` in the public API. Four generalization
levels: "none" (exact OR-join), "low" (common prefix/suffix + character
classes), "medium" (format detection + structural analysis), "high"
(tokenized analysis for long examples, segment analysis for short ones).

Split out of ``spacy_helpers.py`` — nothing here needs spaCy.
"""

import os
import re


def create_regex_from_examples(examples: list[str], generalization_level: str = "none") -> str:
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

def create_simple_generalized_regex(examples: list[str]) -> str:
    r"""
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

def create_generalized_regex(examples: list[str]) -> str:
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

def create_advanced_generalized_regex(examples: list[str]) -> str:
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

    # For short examples, try fragment analysis — but only if segmentation
    # found both a fixed and a variable part.  A prefix-only result is not
    # useful and should fall through to medium-level.
    segments = segment_examples(examples)
    if len(segments) >= 2:
        pattern_parts = []
        for segment in segments:
            if is_fixed_segment(segment, examples):
                pattern_parts.append(re.escape(segment))
            else:
                var_segment_pattern = generalize_variable_segment(segment, examples)
                pattern_parts.append(var_segment_pattern)
        return ''.join(pattern_parts)

    # Fall back to medium generalization
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

def detect_common_format(examples: list[str]) -> str | None:
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

def analyze_structure_for_regex(examples: list[str]) -> str:
    """Analyze examples structurally to produce a flexible regex.

    Extracts a common prefix and suffix, then generalises the variable
    middle portion based on its character composition.
    """
    if len(examples) < 2 or any(len(ex) > 30 for ex in examples):
        return create_simple_generalized_regex(examples)

    max_len = max(len(ex) for ex in examples)
    min_len = min(len(ex) for ex in examples)
    if min_len > 0 and max_len > min_len * 2:
        return create_simple_generalized_regex(examples)

    # --- prefix ---
    prefix = os.path.commonprefix(examples)
    # --- suffix ---
    reversed_examples = [ex[::-1] for ex in examples]
    suffix = os.path.commonprefix(reversed_examples)[::-1]

    # Prevent prefix + suffix from overlapping
    if prefix and suffix and len(prefix) + len(suffix) > min_len:
        suffix = ""

    # Strip prefix/suffix to isolate the variable middle
    middles = []
    for ex in examples:
        start = len(prefix) if prefix else 0
        end = len(ex) - len(suffix) if suffix else len(ex)
        middles.append(ex[start:end])

    # Build the pattern
    parts: list[str] = []
    if prefix:
        parts.append(re.escape(prefix))

    parts.append(_generalise_parts(middles))

    if suffix:
        parts.append(re.escape(suffix))

    return "".join(parts)


def _generalise_parts(parts: list[str]) -> str:
    """Turn a list of variable-part strings into a single regex fragment."""
    non_empty = [p for p in parts if p]
    if not non_empty:
        return ""

    lengths = [len(p) for p in non_empty]
    min_len, max_len = min(lengths), max(lengths)

    if all(p.isdigit() for p in non_empty):
        if min_len == max_len:
            return fr"\d{{{min_len}}}"
        return r"\d+"
    if all(p.isalpha() and p.isupper() for p in non_empty):
        if min_len == max_len:
            return fr"[A-Z]{{{min_len}}}"
        return r"[A-Z]+"
    if all(p.isalpha() and p.islower() for p in non_empty):
        if min_len == max_len:
            return fr"[a-z]{{{min_len}}}"
        return r"[a-z]+"
    if all(p.isalpha() for p in non_empty):
        if min_len == max_len:
            return fr"[A-Za-z]{{{min_len}}}"
        return r"[A-Za-z]+"
    if all(p.isalnum() for p in non_empty):
        if max_len - min_len <= 2:
            return fr"\w{{{min_len},{max_len}}}"
        return r"\w+"

    # Fallback: enumerate if few, else wildcard
    if len(set(non_empty)) <= 5:
        return "(?:" + "|".join(re.escape(p) for p in sorted(set(non_empty))) + ")"
    return r".+?"

def create_tokenized_pattern(examples: list[str]) -> str:
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

def is_fixed_segment(segment: str, examples: list[str]) -> bool:
    """
    Check if a segment appears consistently in examples.

    Args:
        segment: Segment to check
        examples: List of examples

    Returns:
        True if segment is fixed across examples
    """
    return all(segment in example for example in examples)

def generalize_variable_segment(segment: str, examples: list[str]) -> str:
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

def segment_examples(examples: list[str]) -> list[str]:
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
