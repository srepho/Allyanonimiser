"""
Enhanced analyzer for PII detection.
"""
import re
from dataclasses import dataclass
import spacy

# Handle spaCy loading with fallback options
def load_spacy_model(model_name="en_core_web_lg", fallback_model="en_core_web_sm"):
    """
    Load a spaCy language model with fallback to a smaller model if needed.
    
    Args:
        model_name: Primary model name to load
        fallback_model: Fallback model if primary isn't available
        
    Returns:
        Loaded spaCy Language model
    """
    try:
        return spacy.load(model_name)
    except OSError:
        try:
            # Try the fallback model
            return spacy.load(fallback_model)
        except OSError:
            # If all else fails, use the blank model
            return spacy.blank("en")

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
        # Initialize spaCy model for NER
        try:
            self.nlp = load_spacy_model()
            self.use_spacy = True
        except Exception as e:
            print(f"Warning: Could not load spaCy model: {e}")
            self.use_spacy = False
    
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
        # Get results from pattern-based detection
        pattern_results = self._analyze_with_patterns(text)
        
        # Get results from spaCy NER if available
        spacy_results = []
        if self.use_spacy:
            spacy_results = self._analyze_with_spacy(text)
        
        # Combine results
        combined_results = pattern_results + spacy_results
        
        # De-duplicate results and resolve entity conflicts
        deduplicated_results = []
        seen_spans = {}  # Maps (start, end, text) to list of results
        
        # Group results by span
        for result in combined_results:
            span_key = (result.start, result.end, result.text)
            if span_key not in seen_spans:
                seen_spans[span_key] = []
            seen_spans[span_key].append(result)
        
        # Post-processing to resolve entity conflicts
        for span_key, span_results in seen_spans.items():
            if len(span_results) == 1:
                # Only one entity type for this span, add it directly
                deduplicated_results.append(span_results[0])
            else:
                # Multiple entity types for the same span, resolve the conflict
                resolved_result = self._resolve_entity_conflicts(span_results, span_key[2])
                if resolved_result:
                    deduplicated_results.append(resolved_result)
        
        return deduplicated_results
    
    def _analyze_with_patterns(self, text):
        """
        Analyze text using pattern-based detection.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of RecognizerResult objects
        """
        results = []
        
        for pattern in self.patterns:
            if not hasattr(pattern, 'patterns') or not pattern.patterns:
                continue
                
            entity_type = pattern.entity_type
            
            # For PERSON entity type, skip pattern-based detection if we're using spaCy
            if entity_type == "PERSON" and self.use_spacy:
                continue
                
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
                        
                        # Skip known false positives (common identifiers/labels)
                        skip_match = False
                        lc_text = matched_text.lower()
                        
                        # Skip if it's a known non-PII label
                        if lc_text in ["ref number", "reference number", "policy number", "claim number"]:
                            skip_match = True
                            
                        # Skip common patterns that shouldn't be detected as entities
                        if (entity_type == "PERSON" and 
                            ("number" in lc_text or 
                             lc_text.startswith("ref") or
                             lc_text.startswith("policy") or
                             lc_text.startswith("claim"))):
                            skip_match = True
                        
                        if not skip_match:
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
        
        return results
    
    def _analyze_with_spacy(self, text):
        """
        Analyze text using spaCy's NER.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of RecognizerResult objects
        """
        results = []
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract entities detected by spaCy
        for ent in doc.ents:
            # Map spaCy entity types to our entity types
            entity_type = self._map_spacy_entity_type(ent.label_)
            
            # Skip if not a supported entity type
            if not entity_type:
                continue
                
            # Skip common false positives
            if entity_type == "PERSON":
                lc_text = ent.text.lower()
                if (lc_text.startswith("policy") or 
                    lc_text.startswith("ref") or 
                    lc_text.startswith("claim") or
                    "number" in lc_text):
                    continue
            
            # Create result
            result = RecognizerResult(
                entity_type=entity_type,
                start=ent.start_char,
                end=ent.end_char,
                score=0.9,  # Higher confidence for spaCy entities
                text=ent.text
            )
            
            results.append(result)
        
        return results
    
    def _map_spacy_entity_type(self, spacy_entity_type):
        """
        Map spaCy entity types to our entity types.
        
        Args:
            spacy_entity_type: spaCy entity type
            
        Returns:
            Mapped entity type or None if not supported
        """
        # Define mapping
        mapping = {
            "PERSON": "PERSON",
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",
            "LOC": "LOCATION",
            "DATE": "DATE",
            "TIME": "TIME",
            "MONEY": "MONEY",
            "CARDINAL": "NUMBER",
            "ORDINAL": "NUMBER",
            "QUANTITY": "NUMBER",
            "PERCENT": "PERCENT",
            "PRODUCT": "PRODUCT",
            "EVENT": "EVENT",
            "WORK_OF_ART": "WORK_OF_ART",
            "LAW": "LAW",
            "LANGUAGE": "LANGUAGE",
            "FAC": "FACILITY"
        }
        
        return mapping.get(spacy_entity_type)
    
    def _resolve_entity_conflicts(self, results, text):
        """
        Resolve conflicts when multiple entity types match the same text span.
        
        Args:
            results: List of RecognizerResult objects for the same text span
            text: The matched text
            
        Returns:
            The most appropriate RecognizerResult
        """
        # Skip false positives (specific cases we know are problematic)
        if any(text.lower().endswith(term) for term in ["number", "ref", "#", "id", "identifier"]):
            # These are likely identifiers/labels and not PII themselves
            return None
            
        # Skip false positives for common phrases incorrectly identified as PERSON
        if any(r.entity_type == "PERSON" for r in results):
            lower_text = text.lower()
            if (lower_text.startswith("policy") or 
                lower_text.startswith("ref") or 
                lower_text.startswith("claim") or
                "number" in lower_text):
                # Filter out results that are PERSON entity types for these patterns
                filtered_results = [r for r in results if r.entity_type != "PERSON"]
                if filtered_results:
                    return filtered_results[0]
                else:
                    return None
        
        # Prioritize spaCy PERSON entities over pattern-based ones
        if any(r.entity_type == "PERSON" and r.score >= 0.9 for r in results):
            for r in results:
                if r.entity_type == "PERSON" and r.score >= 0.9:
                    return r
        
        # Rules to prioritize entity types
        
        # Pattern-based rules
        if text.startswith("POL") and any(r.entity_type == "INSURANCE_POLICY_NUMBER" for r in results):
            # POL prefix is almost certainly an insurance policy number
            for r in results:
                if r.entity_type == "INSURANCE_POLICY_NUMBER":
                    return r
        
        # Common prefixes mapping to specific entity types
        prefix_to_entity = {
            "POL": "INSURANCE_POLICY_NUMBER",
            "CL": "INSURANCE_CLAIM_NUMBER", 
            "CLM": "INSURANCE_CLAIM_NUMBER",
            "INV": "INVOICE_NUMBER",
            "REF": "INSURANCE_CLAIM_NUMBER"  # REF is typically a reference/claim number
        }
        
        for prefix, entity_type in prefix_to_entity.items():
            if text.upper().startswith(prefix) and any(r.entity_type == entity_type for r in results):
                for r in results:
                    if r.entity_type == entity_type:
                        return r
        
        # For generic alphanumeric patterns, prioritize by context
        # For now, return the first result (we'll enhance this later)
        return results[0]