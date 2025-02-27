"""
Enhanced anonymizer that extends Presidio's anonymizer with additional features.
"""

from typing import List, Dict, Optional, Union, Callable, Any, Tuple
import re
import logging

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import RecognizerResult, OperatorConfig

from .enhanced_analyzer import EnhancedAnalyzer

class EnhancedAnonymizer:
    """
    Enhanced anonymizer that extends Presidio's AnonymizerEngine with additional features.
    Provides a simplified interface for analyzing and anonymizing text in one step.
    """
    
    def __init__(
        self,
        analyzer: Optional[EnhancedAnalyzer] = None,
        custom_operators: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize the EnhancedAnonymizer.
        
        Args:
            analyzer: EnhancedAnalyzer instance to use
            custom_operators: Dictionary mapping entity types to custom operator functions
        """
        self.analyzer = analyzer
        self.anonymizer_engine = AnonymizerEngine()
        self.custom_operators = custom_operators or {}
    
    def anonymize(
        self,
        text: str,
        operators: Optional[Dict[str, Union[str, OperatorConfig]]] = None,
        language: Optional[str] = None,
        entities: Optional[List[str]] = None,
        score_threshold: float = 0.3,
        return_decision_process: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze and anonymize text in one step.
        
        Args:
            text: Text to anonymize
            operators: Mapping of entity types to anonymization operators
            language: Language of the text
            entities: Specific entities to look for
            score_threshold: Minimum confidence score for results
            return_decision_process: Whether to include decision process in results
            
        Returns:
            Dictionary containing anonymized text and analysis details
        """
        if not text:
            return {"text": "", "items": []}
            
        # Analyze text to find entities
        analyzer_results = self.analyzer.analyze(
            text=text,
            language=language,
            score_threshold=score_threshold,
            entities=entities,
            return_decision_process=return_decision_process
        )
        
        # Convert back to Presidio format for anonymization
        presidio_results = []
        for result in analyzer_results:
            presidio_result = RecognizerResult(
                entity_type=result["entity_type"],
                start=result["start"],
                end=result["end"],
                score=result["score"]
            )
            presidio_results.append(presidio_result)
            
        # Apply custom operators if present
        for entity_type, operator_fn in self.custom_operators.items():
            entities_to_anonymize = [r for r in analyzer_results if r["entity_type"] == entity_type]
            for entity in entities_to_anonymize:
                text = self._apply_custom_operator(
                    text, 
                    entity["start"], 
                    entity["end"],
                    entity["text"],
                    operator_fn
                )
                
        # Apply standard operators to remaining entities
        if operators and presidio_results:
            try:
                anonymizer_result = self.anonymizer_engine.anonymize(
                    text=text,
                    analyzer_results=presidio_results,
                    operators=operators
                )
                
                return {
                    "text": anonymizer_result.text,
                    "items": [
                        {
                            "entity_type": item.entity_type,
                            "start": item.start,
                            "end": item.end,
                            "replacement": item.operator_result
                        }
                        for item in anonymizer_result.items
                    ]
                }
            except Exception as e:
                logging.error(f"Anonymization error: {str(e)}")
                return {"text": text, "items": [], "error": str(e)}
        
        return {"text": text, "items": []}
        
    def _apply_custom_operator(
        self,
        text: str,
        start: int,
        end: int,
        original_text: str,
        operator_fn: Callable
    ) -> str:
        """
        Apply a custom operator to a specific span of text.
        
        Args:
            text: Full text
            start: Start index of entity
            end: End index of entity
            original_text: Entity text
            operator_fn: Custom operator function
            
        Returns:
            Text with entity replaced
        """
        try:
            replacement = operator_fn(original_text)
            return text[:start] + replacement + text[end:]
        except Exception as e:
            logging.error(f"Error applying custom operator: {str(e)}")
            return text
    
    def process_and_anonymize(
        self,
        text: str,
        operators: Optional[Dict[str, Union[str, OperatorConfig]]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process and anonymize text in one unified operation.
        
        This method leverages the enhanced analyzer's content type detection and structured
        processing capabilities, then applies anonymization to the results.
        
        Args:
            text: Text to process and anonymize
            operators: Mapping of entity types to anonymization operators
            language: Language of the text
            
        Returns:
            Dictionary containing:
            - anonymized_text: Full anonymized text
            - content_type: Detected content type
            - structured_data: Extracted structured information
            - anonymized_segments: Segments with PII replaced
        """
        if not self.analyzer:
            raise ValueError("Analyzer must be specified for unified processing")
            
        # First, process the text to get structured data and segments
        processing_result = self.analyzer.process_text(text, language=language)
        
        # Anonymize the full text
        anonymized_result = self.anonymize(
            text=text,
            operators=operators,
            language=language
        )
        
        # Anonymize each segment individually
        anonymized_segments = []
        for segment in processing_result["segments"]:
            segment_result = self.anonymize(
                text=segment["text"],
                operators=operators,
                language=language
            )
            
            anonymized_segments.append({
                "original": segment["text"],
                "anonymized": segment_result["text"],
                "pii_likelihood": segment["pii_likelihood"],
                "anonymized_items": segment_result["items"]
            })
            
        # Return combined result
        return {
            "anonymized_text": anonymized_result["text"],
            "content_type": processing_result["content_type"],
            "structured_data": processing_result["structured_data"],
            "anonymized_segments": anonymized_segments,
            "entities": processing_result["entities"]
        }