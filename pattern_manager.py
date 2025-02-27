"""
Core module for managing custom entity patterns in Presidio.
Provides an easy-to-use interface for defining, registering, and applying custom patterns.
"""

import re
import json
from typing import Dict, List, Optional, Union, Callable, Pattern, Any
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from presidio_analyzer import PatternRecognizer, Pattern, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngine, SpacyNlpEngine

class CustomPatternDefinition:
    """Class for defining custom patterns to be used with Presidio."""
    
    def __init__(
        self,
        entity_type: str,
        patterns: List[Union[str, Dict[str, Any], Pattern]],
        context: Optional[List[str]] = None,
        score: float = 0.85,
        name: Optional[str] = None,
        supported_language: str = "en",
        description: str = ""
    ):
        """
        Initialize a custom pattern definition.
        
        Args:
            entity_type: The entity type this pattern detects (e.g., "CUSTOM_ID", "MEDICAL_RECORD")
            patterns: List of patterns. Can be regex strings, regex Pattern objects, or spaCy pattern dicts
            context: List of contextual words that strengthen the match (e.g., ["patient", "record"])
            score: Confidence score for matches (0.0 to 1.0)
            name: Optional name for the pattern recognizer
            supported_language: Language code (default "en")
            description: Human-readable description of what this pattern detects
        """
        self.entity_type = entity_type
        self.name = name or f"custom_{entity_type.lower()}_recognizer"
        self.patterns = patterns
        self.context = context or []
        self.score = score
        self.supported_language = supported_language
        self.description = description or f"Custom recognizer for {entity_type}"
        
    def to_presidio_pattern(self) -> List[Pattern]:
        """Convert the pattern definition to Presidio Pattern objects."""
        presidio_patterns = []
        
        for pattern in self.patterns:
            if isinstance(pattern, str):
                # Regex string
                presidio_patterns.append(
                    Pattern(
                        name=f"{self.name}_pattern",
                        regex=pattern,
                        score=self.score
                    )
                )
            elif isinstance(pattern, Pattern):
                # Already a Presidio Pattern
                presidio_patterns.append(pattern)
            elif isinstance(pattern, dict):
                # This is a spaCy pattern dict, we'll handle this separately
                # in the PatternManager
                continue
                
        return presidio_patterns
    
    def to_dict(self) -> Dict:
        """Convert the pattern definition to a dictionary for serialization."""
        return {
            "entity_type": self.entity_type,
            "name": self.name,
            "patterns": [p if isinstance(p, str) else str(p) for p in self.patterns],
            "context": self.context,
            "score": self.score,
            "supported_language": self.supported_language,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomPatternDefinition':
        """Create a pattern definition from a dictionary."""
        return cls(
            entity_type=data["entity_type"],
            name=data.get("name"),
            patterns=data["patterns"],
            context=data.get("context", []),
            score=data.get("score", 0.85),
            supported_language=data.get("supported_language", "en"),
            description=data.get("description", "")
        )


class PatternManager:
    """Manager for custom patterns to be used with Presidio and spaCy."""
    
    def __init__(self, nlp_engine: Optional[NlpEngine] = None):
        """
        Initialize the pattern manager.
        
        Args:
            nlp_engine: Optional pre-configured Presidio NLP engine
        """
        self.pattern_definitions = {}
        self.presidio_recognizers = {}
        self.spacy_matchers = {}
        
        # Create NLP engine if not provided
        if nlp_engine is None:
            self.nlp_engine = SpacyNlpEngine()
        else:
            self.nlp_engine = nlp_engine
            
        # Get the spaCy model
        self.nlp = self.nlp_engine.nlp_engine
        
    def add_pattern(self, pattern_def: CustomPatternDefinition) -> None:
        """
        Add a new pattern definition to the manager.
        
        Args:
            pattern_def: CustomPatternDefinition object
        """
        # Store the pattern definition
        self.pattern_definitions[pattern_def.name] = pattern_def
        
        # Create and store a Presidio recognizer
        presidio_patterns = pattern_def.to_presidio_pattern()
        if presidio_patterns:
            recognizer = PatternRecognizer(
                supported_entity=pattern_def.entity_type,
                name=pattern_def.name,
                patterns=presidio_patterns,
                context=pattern_def.context,
                supported_language=pattern_def.supported_language
            )
            self.presidio_recognizers[pattern_def.name] = recognizer
        
        # Handle spaCy patterns if any
        spacy_patterns = [p for p in pattern_def.patterns if isinstance(p, dict)]
        if spacy_patterns:
            matcher = Matcher(self.nlp.vocab)
            matcher.add(pattern_def.name, spacy_patterns)
            self.spacy_matchers[pattern_def.name] = matcher
    
    def remove_pattern(self, pattern_name: str) -> bool:
        """
        Remove a pattern by name.
        
        Args:
            pattern_name: Name of the pattern to remove
            
        Returns:
            bool: True if pattern was removed, False if not found
        """
        if pattern_name not in self.pattern_definitions:
            return False
        
        # Remove from all collections
        del self.pattern_definitions[pattern_name]
        
        if pattern_name in self.presidio_recognizers:
            del self.presidio_recognizers[pattern_name]
            
        if pattern_name in self.spacy_matchers:
            del self.spacy_matchers[pattern_name]
            
        return True
    
    def get_all_recognizers(self) -> List[PatternRecognizer]:
        """Get all Presidio recognizers registered with this manager."""
        return list(self.presidio_recognizers.values())
    
    def register_with_presidio(self, registry: RecognizerRegistry) -> None:
        """
        Register all recognizers with a Presidio RecognizerRegistry.
        
        Args:
            registry: Presidio RecognizerRegistry to register with
        """
        for recognizer in self.presidio_recognizers.values():
            registry.add_recognizer(recognizer)
    
    def save_patterns(self, filepath: str) -> None:
        """
        Save all pattern definitions to a JSON file.
        
        Args:
            filepath: Path to save the patterns to
        """
        data = {name: pattern.to_dict() for name, pattern in self.pattern_definitions.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_patterns(self, filepath: str) -> None:
        """
        Load pattern definitions from a JSON file.
        
        Args:
            filepath: Path to load the patterns from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        for name, pattern_data in data.items():
            pattern_def = CustomPatternDefinition.from_dict(pattern_data)
            self.add_pattern(pattern_def)
    
    def apply_spacy_matchers(self, doc) -> List[Dict]:
        """
        Apply all spaCy matchers to a document.
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            List of match dictionaries with entity_type, start, end, and text
        """
        matches = []
        
        for name, matcher in self.spacy_matchers.items():
            pattern_def = self.pattern_definitions[name]
            for match_id, start, end in matcher(doc):
                matches.append({
                    "entity_type": pattern_def.entity_type,
                    "start": start,
                    "end": end,
                    "text": doc[start:end].text,
                    "score": pattern_def.score,
                    "source": name
                })
                
        return matches