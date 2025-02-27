"""
Registry for storing and retrieving patterns.
Provides a central repository for custom PII detection patterns.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
import glob

from .pattern_manager import CustomPatternDefinition

class PatternRegistry:
    """
    Registry for storing and retrieving custom pattern definitions.
    Provides a centralized storage mechanism for pattern definitions
    that can be shared across multiple applications.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the pattern registry.
        
        Args:
            storage_dir: Directory to store pattern definitions
        """
        self.storage_dir = storage_dir or os.path.expanduser("~/.enhanced_presidio/patterns")
        self.patterns: Dict[str, CustomPatternDefinition] = {}
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def register_pattern(self, pattern_def: CustomPatternDefinition) -> None:
        """
        Register a pattern definition.
        
        Args:
            pattern_def: Pattern definition to register
        """
        # Store in memory
        self.patterns[pattern_def.name] = pattern_def
        
        # Store on disk
        self._save_pattern(pattern_def)
        
    def unregister_pattern(self, pattern_name: str) -> bool:
        """
        Unregister a pattern definition.
        
        Args:
            pattern_name: Name of the pattern to unregister
            
        Returns:
            bool: True if pattern was unregistered, False if not found
        """
        if pattern_name not in self.patterns:
            return False
        
        # Remove from memory
        del self.patterns[pattern_name]
        
        # Remove from disk
        pattern_path = os.path.join(self.storage_dir, f"{pattern_name}.json")
        if os.path.exists(pattern_path):
            os.remove(pattern_path)
            
        return True
    
    def get_pattern(self, pattern_name: str) -> Optional[CustomPatternDefinition]:
        """
        Get a pattern definition by name.
        
        Args:
            pattern_name: Name of the pattern to get
            
        Returns:
            CustomPatternDefinition or None if not found
        """
        # Check in-memory cache first
        if pattern_name in self.patterns:
            return self.patterns[pattern_name]
        
        # Try to load from disk
        pattern_path = os.path.join(self.storage_dir, f"{pattern_name}.json")
        if os.path.exists(pattern_path):
            pattern_def = self._load_pattern(pattern_path)
            self.patterns[pattern_name] = pattern_def
            return pattern_def
            
        return None
    
    def get_all_patterns(self) -> List[CustomPatternDefinition]:
        """
        Get all registered pattern definitions.
        
        Returns:
            List of CustomPatternDefinition objects
        """
        # Load all patterns from disk
        self._load_all_patterns()
        
        return list(self.patterns.values())
    
    def get_patterns_by_entity_type(self, entity_type: str) -> List[CustomPatternDefinition]:
        """
        Get all pattern definitions for a specific entity type.
        
        Args:
            entity_type: Entity type to filter by
            
        Returns:
            List of CustomPatternDefinition objects for the entity type
        """
        # Load all patterns
        self._load_all_patterns()
        
        # Filter by entity type
        return [
            pattern for pattern in self.patterns.values()
            if pattern.entity_type == entity_type
        ]
    
    def _save_pattern(self, pattern_def: CustomPatternDefinition) -> None:
        """
        Save a pattern definition to disk.
        
        Args:
            pattern_def: Pattern definition to save
        """
        pattern_path = os.path.join(self.storage_dir, f"{pattern_def.name}.json")
        with open(pattern_path, 'w') as f:
            json.dump(pattern_def.to_dict(), f, indent=2)
    
    def _load_pattern(self, pattern_path: str) -> CustomPatternDefinition:
        """
        Load a pattern definition from disk.
        
        Args:
            pattern_path: Path to the pattern definition file
            
        Returns:
            CustomPatternDefinition object
        """
        with open(pattern_path, 'r') as f:
            pattern_data = json.load(f)
            
        return CustomPatternDefinition.from_dict(pattern_data)
    
    def _load_all_patterns(self) -> None:
        """Load all pattern definitions from disk."""
        pattern_files = glob.glob(os.path.join(self.storage_dir, "*.json"))
        
        for pattern_path in pattern_files:
            pattern_name = os.path.basename(pattern_path).split('.')[0]
            
            # Skip if already loaded
            if pattern_name in self.patterns:
                continue
                
            try:
                pattern_def = self._load_pattern(pattern_path)
                self.patterns[pattern_name] = pattern_def
            except Exception as e:
                print(f"Error loading pattern {pattern_name}: {e}")
                
    def import_patterns(self, patterns_file: str) -> int:
        """
        Import patterns from a JSON file.
        
        Args:
            patterns_file: Path to the patterns file
            
        Returns:
            Number of patterns imported
        """
        with open(patterns_file, 'r') as f:
            patterns_data = json.load(f)
        
        count = 0
        for pattern_data in patterns_data:
            try:
                pattern_def = CustomPatternDefinition.from_dict(pattern_data)
                self.register_pattern(pattern_def)
                count += 1
            except Exception as e:
                print(f"Error importing pattern: {e}")
                
        return count
    
    def export_patterns(self, output_file: str) -> int:
        """
        Export patterns to a JSON file.
        
        Args:
            output_file: Path to save the patterns
            
        Returns:
            Number of patterns exported
        """
        # Load all patterns
        self._load_all_patterns()
        
        patterns_data = [pattern.to_dict() for pattern in self.patterns.values()]
        
        with open(output_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)
            
        return len(patterns_data)