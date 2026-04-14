"""
Pattern manager for handling custom PII detection patterns.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import re

class CustomPatternDefinition:
    """
    Class for defining custom PII detection patterns.
    
    Attributes:
        entity_type: The type of entity this pattern detects (e.g., "POLICY_NUMBER")
        patterns: List of regex strings or spaCy pattern dictionaries
        context: Optional list of context keywords that often appear near this entity
        name: Optional friendly name for this pattern
        score: Detection confidence score (0.0-1.0)
        language: Language this pattern applies to
        description: Description of what this pattern detects
    """
    def __init__(self, **kwargs):
        self.entity_type = kwargs.get('entity_type')
        self.patterns = kwargs.get('patterns', [])
        self.context = kwargs.get('context')
        self.name = kwargs.get('name')
        self.score = kwargs.get('score', 0.85)
        self.language = kwargs.get('language', 'en')
        self.description = kwargs.get('description', f"Custom pattern for {self.entity_type}")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the pattern definition to a dictionary.
        
        Returns:
            Dictionary representation of the pattern definition
        """
        return {
            'entity_type': self.entity_type,
            'patterns': self.patterns,
            'context': self.context,
            'name': self.name,
            'score': self.score,
            'language': self.language,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, pattern_dict: Dict[str, Any]) -> 'CustomPatternDefinition':
        """
        Create a CustomPatternDefinition from a dictionary.
        
        Args:
            pattern_dict: Dictionary with pattern definition fields
            
        Returns:
            New CustomPatternDefinition instance
        """
        return cls(**pattern_dict)

class PatternManager:
    """
    Manager for handling collections of patterns.
    
    This class provides methods for managing, applying, and converting between
    different pattern formats.
    """
    def __init__(self):
        self.patterns = []
        
    def add_pattern(self, pattern: CustomPatternDefinition) -> None:
        """
        Add a pattern to the manager.
        
        Args:
            pattern: The pattern definition to add
        """
        self.patterns.append(pattern)
        
    def get_patterns_by_entity_type(self, entity_type: str) -> List[CustomPatternDefinition]:
        """
        Get all patterns for a specific entity type.
        
        Args:
            entity_type: The entity type to get patterns for
            
        Returns:
            List of pattern definitions for the entity type
        """
        return [p for p in self.patterns if p.entity_type == entity_type]
    
    def apply_patterns(self, text: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Apply patterns to text and return matches.
        
        Args:
            text: The text to analyze
            entity_types: Optional list of entity types to restrict to
            
        Returns:
            List of match dictionaries with entity_type, start, end, text, and score
        """
        results = []
        
        # Filter patterns by entity type if specified
        patterns_to_apply = self.patterns
        if entity_types:
            patterns_to_apply = [p for p in self.patterns if p.entity_type in entity_types]
        
        # Apply each pattern
        for pattern_def in patterns_to_apply:
            entity_type = pattern_def.entity_type
            score = pattern_def.score
            
            for pattern in pattern_def.patterns:
                if isinstance(pattern, str):
                    # It's a regex pattern
                    try:
                        for match in re.finditer(pattern, text):
                            # Check if the pattern has capturing groups
                            if match.lastindex and match.lastindex > 0:
                                # Use the first capturing group
                                start = match.start(1)
                                end = match.end(1)
                                matched_text = match.group(1)
                            else:
                                # Use the entire match
                                start = match.start()
                                end = match.end()
                                matched_text = match.group()
                                
                            results.append({
                                'entity_type': entity_type,
                                'start': start,
                                'end': end,
                                'text': matched_text,
                                'score': score
                            })
                    except re.error:
                        # Skip invalid regex patterns
                        continue
                else:
                    # Skip non-regex patterns for now (spaCy patterns need spaCy model)
                    continue
                    
        return results
            
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert all patterns to a list of dictionaries.
        
        Returns:
            List of dictionaries representing all patterns
        """
        return [pattern.to_dict() for pattern in self.patterns]
    
    @classmethod
    def from_dict_list(cls, pattern_dicts: List[Dict[str, Any]]) -> 'PatternManager':
        """
        Create a PatternManager from a list of pattern dictionaries.
        
        Args:
            pattern_dicts: List of pattern definition dictionaries
            
        Returns:
            New PatternManager instance with loaded patterns
        """
        manager = cls()
        for pattern_dict in pattern_dicts:
            manager.add_pattern(CustomPatternDefinition.from_dict(pattern_dict))
        return manager