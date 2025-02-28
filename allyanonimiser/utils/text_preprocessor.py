"""
Utility functions for text preprocessing before PII detection.
"""

import re
from typing import Dict, List, Optional, Tuple, Union


class TextPreprocessor:
    """
    Provides text preprocessing functionality for improving PII detection.
    """
    
    def __init__(self, acronym_dict: Optional[Dict[str, str]] = None, case_sensitive: bool = False):
        """
        Initialize the text preprocessor.
        
        Args:
            acronym_dict: Dictionary mapping acronyms to their expanded forms
            case_sensitive: Whether acronym matching should be case-sensitive
        """
        self.acronym_dict = acronym_dict or {}
        self.case_sensitive = case_sensitive
        self._compiled_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for efficient text processing."""
        compiled = {}
        
        # Sort acronyms by length (longest first) to avoid partial matches
        sorted_acronyms = sorted(self.acronym_dict.keys(), key=len, reverse=True)
        
        for acronym in sorted_acronyms:
            # Create word boundary patterns for each acronym
            if self.case_sensitive:
                pattern = r'\b' + re.escape(acronym) + r'\b'
                compiled[acronym] = re.compile(pattern)
            else:
                pattern = r'\b' + re.escape(acronym) + r'\b'
                compiled[acronym] = re.compile(pattern, re.IGNORECASE)
                
        return compiled
    
    def add_acronyms(self, acronym_dict: Dict[str, str]) -> None:
        """
        Add acronyms to the existing dictionary.
        
        Args:
            acronym_dict: Dictionary mapping acronyms to their expanded forms
        """
        self.acronym_dict.update(acronym_dict)
        self._compiled_patterns = self._compile_patterns()
        
    def remove_acronyms(self, acronyms: List[str]) -> None:
        """
        Remove acronyms from the dictionary.
        
        Args:
            acronyms: List of acronym keys to remove
        """
        for acronym in acronyms:
            if acronym in self.acronym_dict:
                del self.acronym_dict[acronym]
        self._compiled_patterns = self._compile_patterns()
        
    def expand_acronyms(self, text: str) -> Tuple[str, List[Dict[str, Union[str, int]]]]:
        """
        Expand acronyms in text based on the configured dictionary.
        
        Args:
            text: Input text to process
            
        Returns:
            Tuple containing:
                - Processed text with expanded acronyms
                - List of dictionaries with information about expansions made
        """
        if not self.acronym_dict:
            return text, []
            
        processed_text = text
        expansions = []
        
        # Track offset for positions as we modify the text
        offset = 0
        
        # Apply each pattern to the text
        for acronym, pattern in self._compiled_patterns.items():
            expansion = self.acronym_dict[acronym]
            
            # Find all matches
            for match in pattern.finditer(text):
                start, end = match.span()
                
                # Adjusted positions with offset
                adj_start = start + offset
                adj_end = end + offset
                
                # Replace in the processed text
                before = processed_text[:adj_start]
                after = processed_text[adj_end:]
                processed_text = before + expansion + after
                
                # Record the expansion details
                expansions.append({
                    'acronym': acronym,
                    'expansion': expansion,
                    'original_start': start,
                    'original_end': end,
                    'expanded_start': adj_start,
                    'expanded_end': adj_start + len(expansion)
                })
                
                # Update offset for subsequent replacements
                offset += len(expansion) - (end - start)
        
        return processed_text, expansions
    
    def preprocess_text(self, text: str) -> Tuple[str, Dict[str, List]]:
        """
        Apply all preprocessing steps to the text.
        
        Args:
            text: Input text to process
            
        Returns:
            Tuple containing:
                - Processed text
                - Dictionary with metadata about processing steps applied
        """
        metadata = {'expansions': []}
        
        # Apply acronym expansion
        processed_text, expansions = self.expand_acronyms(text)
        metadata['expansions'] = expansions
        
        # Add additional preprocessing steps here as needed
        
        return processed_text, metadata


def create_text_preprocessor(acronym_dict: Optional[Dict[str, str]] = None, 
                            case_sensitive: bool = False) -> TextPreprocessor:
    """
    Create a text preprocessor with the given configuration.
    
    Args:
        acronym_dict: Dictionary mapping acronyms to their expanded forms
        case_sensitive: Whether acronym matching should be case-sensitive
        
    Returns:
        Configured TextPreprocessor instance
    """
    return TextPreprocessor(acronym_dict=acronym_dict, case_sensitive=case_sensitive)
    

def preprocess_with_acronym_expansion(text: str, 
                                     acronym_dict: Dict[str, str], 
                                     case_sensitive: bool = False) -> str:
    """
    Convenience function to preprocess text with acronym expansion.
    
    Args:
        text: Input text to process
        acronym_dict: Dictionary mapping acronyms to their expanded forms
        case_sensitive: Whether acronym matching should be case-sensitive
        
    Returns:
        Processed text with expanded acronyms
    """
    preprocessor = TextPreprocessor(acronym_dict=acronym_dict, case_sensitive=case_sensitive)
    processed_text, _ = preprocessor.expand_acronyms(text)
    return processed_text