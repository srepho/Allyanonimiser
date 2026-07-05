"""
Utility functions for working with spaCy.

The regex-from-examples generation engine lives in
:mod:`allyanonimiser.utils.pattern_generation` (it has no spaCy
dependency); the names are re-exported here for backwards compatibility.
"""

from typing import Any

from spacy.language import Language

# Backwards-compatible re-exports: these historically lived in this module.
from .pattern_generation import (  # noqa: F401
    analyze_structure_for_regex,
    create_advanced_generalized_regex,
    create_generalized_regex,
    create_regex_from_examples,
    create_simple_generalized_regex,
    create_tokenized_pattern,
    detect_common_format,
    generalize_single_example,
    generalize_variable_segment,
    is_fixed_segment,
    segment_examples,
)


def create_spacy_pattern_from_examples(
    nlp: Language,
    examples: list[str],
    pattern_type: str = "token"
) -> list[dict[str, Any]]:
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
