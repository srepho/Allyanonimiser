"""
Enhanced analyzer for PII detection.
"""
import re
from dataclasses import dataclass

@dataclass
class RecognizerResult:
    """A class representing the result of a recognized entity."""
    entity_type: str
    start: int
    end: int
    score: float
    text: str = None
    
    def __post_init__(self):
        """Ensure all fields are properly initialized."""
        # We don't need to do anything here as text can be populated externally

class EnhancedAnalyzer:
    """
    Enhanced analyzer for PII detection.
    This is a wrapper around Presidio Analyzer with additional functionality.
    """
    def __init__(self):
        self.patterns = []
    
    def add_pattern(self, pattern):
        """Add a pattern to the analyzer."""
        self.patterns.append(pattern)
    
    def analyze(self, text, language="en"):
        """
        Analyze text to detect PII entities.
        
        Args:
            text: The text to analyze
            language: The language of the text (default: en)
            
        Returns:
            List of RecognizerResult objects representing detected entities
        """
        # This is a stub implementation that will actually do basic pattern matching
        results = []
        
        for pattern in self.patterns:
            if not hasattr(pattern, 'patterns') or not pattern.patterns:
                continue
                
            entity_type = pattern.entity_type
            
            # Go through each regex pattern
            for regex_pattern in pattern.patterns:
                try:
                    # Find all matches
                    for match in re.finditer(regex_pattern, text):
                        # Check if the pattern has capturing groups
                        if match.lastindex and match.lastindex > 0:
                            # Use the first capturing group to get the actual value
                            start = match.start(1)
                            end = match.end(1)
                            matched_text = match.group(1)
                        else:
                            # Use the entire match
                            start = match.start()
                            end = match.end()
                            matched_text = match.group()
                        
                        # Create a result object
                        result = RecognizerResult(
                            entity_type=entity_type,
                            start=start,
                            end=end,
                            score=0.85,  # Default score
                            text=matched_text  # Set the actual matched text
                        )
                        
                        results.append(result)
                except re.error:
                    # Skip invalid regex patterns
                    continue
                except Exception as e:
                    # Skip any other errors
                    print(f"Error processing pattern {regex_pattern}: {e}")
                    continue
        
        # De-duplicate results
        deduplicated_results = []
        seen_entities = set()
        
        for result in results:
            # Create a key using entity_type, text, start, end
            key = (result.entity_type, result.text, result.start, result.end)
            
            if key not in seen_entities:
                seen_entities.add(key)
                deduplicated_results.append(result)
        
        return deduplicated_results