"""
Utility functions for working with spaCy.
"""

import re
from typing import List, Dict, Any, Optional, Union, Tuple, Set
import spacy
from spacy.tokens import Doc, Span
from spacy.matcher import Matcher, PhraseMatcher
from spacy.language import Language

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

def create_regex_from_examples(examples: List[str]) -> str:
    """
    Create a regex pattern from example strings.
    
    Args:
        examples: List of example strings
        
    Returns:
        Regex pattern string
    """
    # Escape special regex characters
    escaped_examples = [re.escape(example) for example in examples]
    
    # Join with OR
    return '|'.join(f'({example})' for example in escaped_examples)

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