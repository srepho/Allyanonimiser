"""
Pattern registry for storing and retrieving patterns.

This module provides a registry for pattern definitions that can be saved,
loaded, and shared between analyzer instances.
"""

import os
import json
from typing import Dict, List, Any, Optional
from .pattern_manager import CustomPatternDefinition, PatternManager

class PatternRegistry:
    """
    Registry for pattern definitions.
    
    This class provides persistent storage for patterns, with methods to save
    and load patterns from disk.
    """
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize a pattern registry.
        
        Args:
            storage_path: Optional path to store pattern files
        """
        self.patterns = {}  # Dict of entity_type -> list of pattern definitions
        self.storage_path = storage_path
        
    def register_pattern(self, pattern: CustomPatternDefinition) -> None:
        """
        Register a pattern with the registry.
        
        Args:
            pattern: Pattern definition to register
        """
        entity_type = pattern.entity_type
        if entity_type not in self.patterns:
            self.patterns[entity_type] = []
            
        # Add if not already registered
        if pattern not in self.patterns[entity_type]:
            self.patterns[entity_type].append(pattern)
            
    def get_patterns(self, entity_type: Optional[str] = None) -> List[CustomPatternDefinition]:
        """
        Get patterns from the registry.
        
        Args:
            entity_type: Optional entity type to filter by
            
        Returns:
            List of pattern definitions
        """
        if entity_type:
            return self.patterns.get(entity_type, [])
        else:
            # Return all patterns
            all_patterns = []
            for patterns_list in self.patterns.values():
                all_patterns.extend(patterns_list)
            return all_patterns
            
    def save_patterns(self, filepath: Optional[str] = None) -> str:
        """
        Save pattern definitions to a JSON file.
        
        Args:
            filepath: Optional path to save to (defaults to storage_path/patterns.json)
            
        Returns:
            Path where patterns were saved
        """
        if not filepath and not self.storage_path:
            raise ValueError("No filepath provided and no storage_path set")
            
        path = filepath or os.path.join(self.storage_path, "patterns.json")
        
        # Create containing directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        # Convert patterns to serializable format
        pattern_dicts = []
        for entity_patterns in self.patterns.values():
            for pattern in entity_patterns:
                pattern_dicts.append(pattern.to_dict())
                
        # Save to JSON file
        with open(path, 'w') as file:
            json.dump(pattern_dicts, file, indent=2)
            
        return path
            
    def load_patterns(self, filepath: Optional[str] = None) -> int:
        """
        Load pattern definitions from a JSON file.
        
        Args:
            filepath: Optional path to load from (defaults to storage_path/patterns.json)
            
        Returns:
            Number of patterns loaded
        """
        if not filepath and not self.storage_path:
            raise ValueError("No filepath provided and no storage_path set")
            
        path = filepath or os.path.join(self.storage_path, "patterns.json")
        
        if not os.path.exists(path):
            return 0
            
        # Load from JSON file
        with open(path, 'r') as file:
            pattern_dicts = json.load(file)
            
        # Register each pattern
        count = 0
        for pattern_dict in pattern_dicts:
            pattern = CustomPatternDefinition.from_dict(pattern_dict)
            self.register_pattern(pattern)
            count += 1
            
        return count
            
    def clear(self) -> None:
        """Clear all patterns from the registry."""
        self.patterns = {}
        
    def import_patterns(self, pattern_manager: PatternManager) -> int:
        """
        Import patterns from a PatternManager.
        
        Args:
            pattern_manager: PatternManager instance to import from
            
        Returns:
            Number of patterns imported
        """
        count = 0
        for pattern in pattern_manager.patterns:
            self.register_pattern(pattern)
            count += 1
        return count
        
    def export_to_manager(self) -> PatternManager:
        """
        Export all patterns to a new PatternManager.
        
        Returns:
            PatternManager instance with all registered patterns
        """
        manager = PatternManager()
        for pattern in self.get_patterns():
            manager.add_pattern(pattern)
        return manager