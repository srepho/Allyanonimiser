"""
Enhanced anonymizer that extends Presidio's anonymizer with additional features.
"""

from typing import List, Dict, Optional, Union, Callable, Any
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
        Initialize the enhanced anonymizer.
        
        Args:
            analyzer: Optional EnhancedAnalyzer instance
            custom_operators: Optional dictionary of custom anonymization operators
        """
        self.analyzer = analyzer or EnhancedAnalyzer()
        self.anonymizer = AnonymizerEngine()
        
        # Store custom operators
        self.custom_operators = custom_operators or {}
        
    def add_custom_operator(self, operator_name: str, operator_function: Callable) -> None:
        """
        Add a custom anonymization operator.
        
        Args:
            operator_name: Name of the operator
            operator_function: Function that implements the operator
        """
        self.custom_operators[operator_name] = operator_function
        
    def anonymize(
        self,
        text: str,
        analyzer_results: Optional[List[RecognizerResult]] = None,
        operators: Optional[Dict[str, Union[str, OperatorConfig]]] = None,
        language: str = "en",
        entities: Optional[List[str]] = None,
        score_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        Analyze and anonymize text in one step.
        
        Args:
            text: The text to anonymize
            analyzer_results: Optional pre-computed analyzer results
            operators: Optional dictionary mapping entity types to operator configs
            language: Language of the text
            entities: List of entities to analyze
            score_threshold: Minimum confidence score threshold
            
        Returns:
            Dictionary with the anonymized text and additional metadata
        """
        # Analyze if results not provided
        if analyzer_results is None:
            analyzer_results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=entities,
                score_threshold=score_threshold
            )
            
        # Prepare operators if provided
        anonymizer_config = {}
        if operators:
            for entity_type, operator in operators.items():
                # Check if this is a custom operator
                if isinstance(operator, str) and operator in self.custom_operators:
                    # Apply custom operator manually
                    for result in analyzer_results:
                        if result.entity_type == entity_type:
                            # Get the text to anonymize
                            start, end = result.start, result.end
                            entity_text = text[start:end]
                            
                            # Apply the custom operator
                            anonymized_text = self.custom_operators[operator](entity_text)
                            
                            # Replace in the original text
                            text = text[:start] + anonymized_text + text[end:]
                            
                            # Adjust other results' positions if necessary
                            for other_result in analyzer_results:
                                if other_result.start > end:
                                    length_diff = len(anonymized_text) - len(entity_text)
                                    other_result.start += length_diff
                                    other_result.end += length_diff
                            
                            # Update this result's end position
                            result.end = start + len(anonymized_text)
                else:
                    # Standard Presidio operator
                    anonymizer_config[entity_type] = operator
        
        # Anonymize using Presidio anonymizer
        anonymizer_results = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=anonymizer_config
        )
        
        return anonymizer_results.to_dict()
    
    def anonymize_with_custom_config(
        self,
        text: str,
        config: Dict[str, Any],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Anonymize text using a custom configuration.
        
        Args:
            text: The text to anonymize
            config: Configuration dictionary with entities and operators
            language: Language of the text
            
        Returns:
            Dictionary with the anonymized text and additional metadata
        """
        # Extract config parameters
        entities = config.get("entities")
        score_threshold = config.get("score_threshold", 0.0)
        operators = config.get("operators", {})
        
        # Analyze and anonymize
        return self.anonymize(
            text=text,
            language=language,
            entities=entities,
            score_threshold=score_threshold,
            operators=operators
        )