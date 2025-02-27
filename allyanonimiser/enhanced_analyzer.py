"""
Enhanced analyzer that extends Presidio's analyzer with custom pattern support.
"""

from typing import List, Dict, Optional, Union, Any
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngine

from .pattern_manager import PatternManager, CustomPatternDefinition

class EnhancedAnalyzer:
    """
    Enhanced analyzer that extends Presidio's AnalyzerEngine with custom pattern support.
    Combines results from both Presidio's built-in recognizers and custom spaCy patterns.
    """
    
    def __init__(
        self,
        pattern_manager: Optional[PatternManager] = None,
        registry: Optional[RecognizerRegistry] = None,
        nlp_engine: Optional[NlpEngine] = None,
        supported_languages: Optional[List[str]] = None
    ):
        """
        Initialize the enhanced analyzer.
        
        Args:
            pattern_manager: Optional PatternManager instance
            registry: Optional RecognizerRegistry instance
            nlp_engine: Optional NlpEngine instance
            supported_languages: Optional list of supported language codes
        """
        # Create a pattern manager if not provided
        self.pattern_manager = pattern_manager or PatternManager(nlp_engine=nlp_engine)
        
        # Create a registry if not provided
        self.registry = registry or RecognizerRegistry()
        
        # Register our custom patterns
        self.pattern_manager.register_with_presidio(self.registry)
        
        # Create the Presidio analyzer
        self.analyzer = AnalyzerEngine(
            registry=self.registry,
            nlp_engine=self.pattern_manager.nlp_engine,
            supported_languages=supported_languages
        )
    
    def analyze(
        self,
        text: str,
        language: str = "en",
        entities: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
        score_threshold: float = 0.0,
        return_decision_process: bool = False,
        include_spacy_matches: bool = True
    ) -> List[RecognizerResult]:
        """
        Analyze text for PII entities using both Presidio and custom spaCy patterns.
        
        Args:
            text: The text to analyze
            language: Language of the text
            entities: List of entities to analyze
            correlation_id: Correlation ID for the request
            score_threshold: Minimum confidence score threshold
            return_decision_process: Whether to return the decision process
            include_spacy_matches: Whether to include matches from spaCy patterns
            
        Returns:
            List of RecognizerResult objects
        """
        # Get results from Presidio analyzer
        presidio_results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
            correlation_id=correlation_id,
            score_threshold=score_threshold,
            return_decision_process=return_decision_process
        )
        
        # Optionally get results from spaCy patterns
        if include_spacy_matches:
            # Process the text with spaCy
            doc = self.pattern_manager.nlp(text)
            
            # Apply custom spaCy matchers
            spacy_matches = self.pattern_manager.apply_spacy_matchers(doc)
            
            # Convert spaCy matches to RecognizerResult objects
            for match in spacy_matches:
                # Filter by entities if specified
                if entities and match["entity_type"] not in entities:
                    continue
                    
                # Filter by score threshold
                if match["score"] < score_threshold:
                    continue
                
                # Create RecognizerResult
                result = RecognizerResult(
                    entity_type=match["entity_type"],
                    start=match["start"],
                    end=match["end"],
                    score=match["score"],
                    analysis_explanation={"source": match["source"]}
                )
                
                presidio_results.append(result)
                
        return presidio_results
    
    def add_pattern(self, pattern_def: Union[CustomPatternDefinition, Dict[str, Any]]) -> None:
        """
        Add a new pattern definition to the analyzer.
        
        Args:
            pattern_def: CustomPatternDefinition object or dictionary
        """
        if isinstance(pattern_def, dict):
            pattern_def = CustomPatternDefinition.from_dict(pattern_def)
            
        self.pattern_manager.add_pattern(pattern_def)
        
        # Re-register with Presidio
        self.pattern_manager.register_with_presidio(self.registry)
    
    def remove_pattern(self, pattern_name: str) -> bool:
        """
        Remove a pattern by name.
        
        Args:
            pattern_name: Name of the pattern to remove
            
        Returns:
            bool: True if pattern was removed, False if not found
        """
        removed = self.pattern_manager.remove_pattern(pattern_name)
        if removed:
            # Re-create the registry to update it
            self.registry = RecognizerRegistry()
            self.pattern_manager.register_with_presidio(self.registry)
            
        return removed
    
    def save_patterns(self, filepath: str) -> None:
        """
        Save all pattern definitions to a file.
        
        Args:
            filepath: Path to save the patterns to
        """
        self.pattern_manager.save_patterns(filepath)
    
    def load_patterns(self, filepath: str) -> None:
        """
        Load pattern definitions from a file.
        
        Args:
            filepath: Path to load the patterns from
        """
        self.pattern_manager.load_patterns(filepath)
        
        # Re-register with Presidio
        self.registry = RecognizerRegistry()
        self.pattern_manager.register_with_presidio(self.registry)