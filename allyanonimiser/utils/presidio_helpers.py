"""
Utility functions for working with Presidio.
"""

import re
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from presidio_analyzer import PatternRecognizer, Pattern, RecognizerResult
from presidio_analyzer.predefined_recognizers import SpacyRecognizer

def create_pattern_from_regex(
    regex: str,
    score: float = 0.85,
    name: Optional[str] = None
) -> Pattern:
    """
    Create a Presidio Pattern from a regex string.
    
    Args:
        regex: Regular expression string
        score: Confidence score for matches
        name: Optional name for the pattern
        
    Returns:
        Presidio Pattern object
    """
    return Pattern(
        name=name or "custom_pattern",
        regex=regex,
        score=score
    )

def create_pattern_recognizer(
    supported_entity: str,
    patterns: List[Pattern],
    context: Optional[List[str]] = None,
    name: Optional[str] = None,
    supported_language: str = "en"
) -> PatternRecognizer:
    """
    Create a Presidio PatternRecognizer.
    
    Args:
        supported_entity: Entity type this recognizer detects
        patterns: List of Pattern objects
        context: List of context words
        name: Optional name for the recognizer
        supported_language: Language code
        
    Returns:
        Presidio PatternRecognizer object
    """
    return PatternRecognizer(
        supported_entity=supported_entity,
        patterns=patterns,
        context=context or [],
        name=name or f"custom_{supported_entity.lower()}_recognizer",
        supported_language=supported_language
    )

def combine_pattern_results(
    results_a: List[RecognizerResult],
    results_b: List[RecognizerResult],
    prefer_higher_score: bool = True
) -> List[RecognizerResult]:
    """
    Combine results from multiple recognizers, handling overlaps.
    
    Args:
        results_a: First list of results
        results_b: Second list of results
        prefer_higher_score: Whether to prefer results with higher scores in case of overlap
        
    Returns:
        Combined list of results with overlaps resolved
    """
    combined = list(results_a)
    
    for result_b in results_b:
        # Check for overlaps
        overlapping = False
        
        for i, result_a in enumerate(combined):
            # Check if results overlap
            if (result_b.start <= result_a.end and result_b.end >= result_a.start):
                overlapping = True
                
                # Handle overlap based on preference
                if prefer_higher_score:
                    if result_b.score > result_a.score:
                        # Replace with higher-scoring result
                        combined[i] = result_b
                else:
                    # Merge the results by taking the union of spans
                    start = min(result_a.start, result_b.start)
                    end = max(result_a.end, result_b.end)
                    score = max(result_a.score, result_b.score)
                    
                    # Create a new result with the merged span
                    merged = RecognizerResult(
                        entity_type=result_a.entity_type,  # Keep the original type
                        start=start,
                        end=end,
                        score=score
                    )
                    
                    combined[i] = merged
                
                break
        
        # If no overlap, add the result
        if not overlapping:
            combined.append(result_b)
    
    return combined

def filter_results_by_score(
    results: List[RecognizerResult],
    min_score: float = 0.6
) -> List[RecognizerResult]:
    """
    Filter recognizer results by confidence score.
    
    Args:
        results: List of recognizer results
        min_score: Minimum confidence score
        
    Returns:
        Filtered list of results
    """
    return [result for result in results if result.score >= min_score]

def filter_results_by_entity_type(
    results: List[RecognizerResult],
    entity_types: List[str]
) -> List[RecognizerResult]:
    """
    Filter recognizer results by entity type.
    
    Args:
        results: List of recognizer results
        entity_types: List of entity types to keep
        
    Returns:
        Filtered list of results
    """
    return [result for result in results if result.entity_type in entity_types]

def results_to_dict(results: List[RecognizerResult]) -> List[Dict[str, Any]]:
    """
    Convert recognizer results to dictionaries.
    
    Args:
        results: List of recognizer results
        
    Returns:
        List of dictionaries with result properties
    """
    return [
        {
            "entity_type": result.entity_type,
            "start": result.start,
            "end": result.end,
            "score": result.score,
            "analysis_explanation": result.analysis_explanation
        }
        for result in results
    ]

def results_to_spans(
    results: List[RecognizerResult],
    text: str
) -> List[Dict[str, Any]]:
    """
    Convert recognizer results to text spans.
    
    Args:
        results: List of recognizer results
        text: Original text
        
    Returns:
        List of dictionaries with spans and metadata
    """
    return [
        {
            "entity_type": result.entity_type,
            "start": result.start,
            "end": result.end,
            "text": text[result.start:result.end],
            "score": result.score
        }
        for result in results
    ]

def find_false_positives(
    results: List[RecognizerResult],
    ground_truth: List[Dict[str, Any]],
    text: str,
    match_partial: bool = False
) -> List[Dict[str, Any]]:
    """
    Find false positive results by comparing to ground truth.
    
    Args:
        results: List of recognizer results
        ground_truth: List of ground truth entities
        text: Original text
        match_partial: Whether to count partial overlaps as matches
        
    Returns:
        List of false positive entities
    """
    false_positives = []
    
    for result in results:
        # Check if this result matches any ground truth
        is_match = False
        
        for gt in ground_truth:
            if result.entity_type == gt.get("entity_type"):
                # Check for exact or partial span match
                if match_partial:
                    # Partial match - spans overlap
                    if (result.start < gt.get("end") and result.end > gt.get("start")):
                        is_match = True
                        break
                else:
                    # Exact match - spans are identical
                    if result.start == gt.get("start") and result.end == gt.get("end"):
                        is_match = True
                        break
        
        # If no match found, this is a false positive
        if not is_match:
            false_positives.append({
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "text": text[result.start:result.end],
                "score": result.score
            })
    
    return false_positives

def find_false_negatives(
    results: List[RecognizerResult],
    ground_truth: List[Dict[str, Any]],
    text: str,
    match_partial: bool = False
) -> List[Dict[str, Any]]:
    """
    Find false negative results by comparing to ground truth.
    
    Args:
        results: List of recognizer results
        ground_truth: List of ground truth entities
        text: Original text
        match_partial: Whether to count partial overlaps as matches
        
    Returns:
        List of false negative entities
    """
    false_negatives = []
    
    for gt in ground_truth:
        # Check if this ground truth matches any result
        is_match = False
        
        for result in results:
            if result.entity_type == gt.get("entity_type"):
                # Check for exact or partial span match
                if match_partial:
                    # Partial match - spans overlap
                    if (result.start < gt.get("end") and result.end > gt.get("start")):
                        is_match = True
                        break
                else:
                    # Exact match - spans are identical
                    if result.start == gt.get("start") and result.end == gt.get("end"):
                        is_match = True
                        break
        
        # If no match found, this is a false negative
        if not is_match:
            false_negatives.append({
                "entity_type": gt.get("entity_type"),
                "start": gt.get("start"),
                "end": gt.get("end"),
                "text": text[gt.get("start"):gt.get("end")],
                "score": gt.get("score", 1.0)
            })
    
    return false_negatives

def evaluate_results(
    results: List[RecognizerResult],
    ground_truth: List[Dict[str, Any]],
    text: str,
    match_partial: bool = False
) -> Dict[str, Any]:
    """
    Evaluate recognizer results against ground truth.
    
    Args:
        results: List of recognizer results
        ground_truth: List of ground truth entities
        text: Original text
        match_partial: Whether to count partial overlaps as matches
        
    Returns:
        Dictionary with evaluation metrics
    """
    # Find false positives and false negatives
    false_positives = find_false_positives(results, ground_truth, text, match_partial)
    false_negatives = find_false_negatives(results, ground_truth, text, match_partial)
    
    # Count true positives
    true_positives = []
    
    for result in results:
        for gt in ground_truth:
            if result.entity_type == gt.get("entity_type"):
                # Check for exact or partial span match
                if match_partial:
                    # Partial match - spans overlap
                    if (result.start < gt.get("end") and result.end > gt.get("start")):
                        true_positives.append({
                            "entity_type": result.entity_type,
                            "start": result.start,
                            "end": result.end,
                            "text": text[result.start:result.end],
                            "score": result.score,
                            "ground_truth_start": gt.get("start"),
                            "ground_truth_end": gt.get("end"),
                            "ground_truth_text": text[gt.get("start"):gt.get("end")]
                        })
                        break
                else:
                    # Exact match - spans are identical
                    if result.start == gt.get("start") and result.end == gt.get("end"):
                        true_positives.append({
                            "entity_type": result.entity_type,
                            "start": result.start,
                            "end": result.end,
                            "text": text[result.start:result.end],
                            "score": result.score
                        })
                        break
    
    # Calculate metrics
    tp = len(true_positives)
    fp = len(false_positives)
    fn = len(false_negatives)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Calculate entity-type specific metrics
    entity_types = set(gt.get("entity_type") for gt in ground_truth)
    entity_metrics = {}
    
    for entity_type in entity_types:
        # Count entity-specific metrics
        entity_tp = sum(1 for tp in true_positives if tp["entity_type"] == entity_type)
        entity_fp = sum(1 for fp in false_positives if fp["entity_type"] == entity_type)
        entity_fn = sum(1 for fn in false_negatives if fn["entity_type"] == entity_type)
        
        entity_precision = entity_tp / (entity_tp + entity_fp) if (entity_tp + entity_fp) > 0 else 0
        entity_recall = entity_tp / (entity_tp + entity_fn) if (entity_tp + entity_fn) > 0 else 0
        entity_f1 = 2 * (entity_precision * entity_recall) / (entity_precision + entity_recall) if (entity_precision + entity_recall) > 0 else 0
        
        entity_metrics[entity_type] = {
            "true_positives": entity_tp,
            "false_positives": entity_fp,
            "false_negatives": entity_fn,
            "precision": entity_precision,
            "recall": entity_recall,
            "f1": entity_f1
        }
    
    return {
        "overall": {
            "true_positives": tp,
            "false_positives": fp, 
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1
        },
        "entity_metrics": entity_metrics,
        "details": {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        }
    }