"""
Unified analyzer for PII detection across all document types.
"""
import re
from dataclasses import dataclass
import spacy
from typing import List, Dict, Any, Optional, Union, Tuple

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
    Unified analyzer for PII detection.
    Combines pattern-based and NER-based entity detection with configurable active entities.
    """
    def __init__(self, min_score_threshold=0.7):
        self.patterns = []
        self.active_entity_types = set()  # Empty set means all types are active
        self.min_score_threshold = min_score_threshold
        
        # Initialize spaCy model for NER
        try:
            self.nlp = load_spacy_model()
            self.use_spacy = True
        except Exception as e:
            print(f"Warning: Could not load spaCy model: {e}")
            self.use_spacy = False
            
        # Entity type metadata for transparency
        self.entity_type_metadata = {
            # Generic types from spaCy
            "PERSON": {"description": "Names of people", "example": "John Smith", "source": "spaCy NER"},
            "ORGANIZATION": {"description": "Names of companies, agencies, institutions", "example": "Insurance Australia Group", "source": "spaCy NER"},
            "LOCATION": {"description": "Names of locations, countries, cities", "example": "Sydney", "source": "spaCy NER"},
            "DATE": {"description": "Calendar dates", "example": "January 1, 2023", "source": "spaCy NER"},
            
            # Insurance-specific types
            "INSURANCE_POLICY_NUMBER": {"description": "Insurance policy identifiers", "example": "POL-12345678", "source": "Pattern matching"},
            "INSURANCE_CLAIM_NUMBER": {"description": "Insurance claim identifiers", "example": "CL-12345678", "source": "Pattern matching"},
            "VEHICLE_REGISTRATION": {"description": "Vehicle registration numbers", "example": "ABC123", "source": "Pattern matching"},
            "VEHICLE_VIN": {"description": "Vehicle identification numbers", "example": "1HGCM82633A123456", "source": "Pattern matching"},
            
            # Contact information
            "EMAIL_ADDRESS": {"description": "Email addresses", "example": "person@example.com", "source": "Pattern matching"},
            "PHONE_NUMBER": {"description": "Phone numbers", "example": "0412 345 678", "source": "Pattern matching"},
            "ADDRESS": {"description": "Physical addresses", "example": "123 Main St, Sydney", "source": "Pattern matching"},
            
            # Australian-specific types
            "AU_TFN": {"description": "Australian Tax File Numbers", "example": "123 456 789", "source": "Pattern matching"},
            "AU_ABN": {"description": "Australian Business Numbers", "example": "51 824 753 556", "source": "Pattern matching"},
            "AU_MEDICARE": {"description": "Medicare card numbers", "example": "2123 45678 1", "source": "Pattern matching"},
            "AU_DRIVERS_LICENSE": {"description": "Australian driver's license numbers", "example": "12345678", "source": "Pattern matching"}
        }
    
    def add_pattern(self, pattern):
        """
        Add a pattern to the analyzer.
        
        Args:
            pattern: The pattern definition to add
            
        Returns:
            True if pattern was added, False if validation failed
        """
        self.patterns.append(pattern)
        
        # Add the entity type to metadata if not already present
        if hasattr(pattern, 'entity_type') and pattern.entity_type not in self.entity_type_metadata:
            # Determine example text from pattern
            example = "N/A"
            if hasattr(pattern, 'patterns') and pattern.patterns:
                if isinstance(pattern.patterns[0], str) and len(pattern.patterns[0]) < 50:
                    example = pattern.patterns[0]
                elif hasattr(pattern, 'name') and pattern.name:
                    example = f"Example of {pattern.name}"
            
            # Use pattern description if available
            description = f"Custom pattern for {pattern.entity_type}"
            if hasattr(pattern, 'description') and pattern.description:
                description = pattern.description
                
            self.entity_type_metadata[pattern.entity_type] = {
                "description": description,
                "example": example,
                "source": "Custom pattern"
            }
        
        return True
    
    def get_pattern(self, entity_type):
        """
        Get patterns for a specific entity type.
        
        Args:
            entity_type: Entity type to get patterns for
            
        Returns:
            List of pattern definitions for the entity type
        """
        return [p for p in self.patterns if hasattr(p, 'entity_type') and p.entity_type == entity_type]
        
    def get_supported_entities(self):
        """
        Get a list of all supported entity types.
        
        Returns:
            List of entity type strings
        """
        # Combine patterns and metadata
        entity_types = set(self.entity_type_metadata.keys())
        for pattern in self.patterns:
            if hasattr(pattern, 'entity_type'):
                entity_types.add(pattern.entity_type)
        
        return sorted(list(entity_types))
    
    def set_active_entity_types(self, entity_types=None):
        """
        Set which entity types should be active during analysis.
        
        Args:
            entity_types: List of entity type strings to activate, or None to activate all
        """
        if entity_types is None:
            self.active_entity_types = set()  # Empty set means all types are active
        else:
            self.active_entity_types = set(entity_types)
    
    def get_available_entity_types(self):
        """
        Get a list of all available entity types with their metadata.
        
        Returns:
            Dictionary of entity types and their metadata
        """
        return self.entity_type_metadata
    
    def set_min_score_threshold(self, threshold):
        """
        Set the minimum confidence score threshold for entity detection.
        
        Args:
            threshold: Float between 0 and 1.0
        """
        if 0 <= threshold <= 1.0:
            self.min_score_threshold = threshold
        else:
            raise ValueError("Threshold must be between 0 and 1.0")
    
    def analyze(self, text, language="en", score_adjustment=None):
        """
        Analyze text to detect PII entities.
        
        Args:
            text: The text to analyze
            language: The language of the text (default: en)
            score_adjustment: Optional dictionary mapping entity_type to score adjustment value
                (positive or negative float that will be added to the confidence score)
            
        Returns:
            List of RecognizerResult objects representing detected entities
        """
        if score_adjustment is None:
            score_adjustment = {}
            
        # Get results from pattern-based detection
        pattern_results = self._analyze_with_patterns(text)
        
        # Get results from spaCy NER if available
        spacy_results = []
        if self.use_spacy:
            spacy_results = self._analyze_with_spacy(text)
        
        # Add entity-specific extraction for common formats
        format_results = self._analyze_common_formats(text)
        
        # Combine results
        combined_results = pattern_results + spacy_results + format_results
        
        # Apply score adjustments
        for result in combined_results:
            if result.entity_type in score_adjustment:
                result.score += score_adjustment[result.entity_type]
                # Cap score at 1.0
                result.score = min(1.0, result.score)
        
        # Filter by active entity types, if specified
        if self.active_entity_types:
            combined_results = [r for r in combined_results if r.entity_type in self.active_entity_types]
            
        # Filter by score threshold
        combined_results = [r for r in combined_results if r.score >= self.min_score_threshold]
        
        # De-duplicate results and resolve entity conflicts
        deduplicated_results = self._deduplicate_and_resolve_conflicts(combined_results)
        
        return deduplicated_results
    
    def explain_detection(self, text, entity_result):
        """
        Explain why a particular entity was detected.
        
        Args:
            text: The original text
            entity_result: A RecognizerResult object to explain
            
        Returns:
            Dictionary with explanation details
        """
        entity_type = entity_result.entity_type
        entity_text = entity_result.text
        entity_score = entity_result.score
        
        # Build the basic explanation
        explanation = {
            "entity_type": entity_type,
            "matched_text": entity_text,
            "confidence_score": entity_score,
            "metadata": self.entity_type_metadata.get(entity_type, {"description": "Unknown entity type"}),
            "match_details": {}
        }
        
        # Add more specific details based on entity type and detection method
        if entity_type in self.entity_type_metadata and "source" in self.entity_type_metadata[entity_type]:
            source = self.entity_type_metadata[entity_type]["source"]
            
            if source == "spaCy NER":
                explanation["match_details"] = {
                    "detection_method": "spaCy Natural Language Processing",
                    "model": "en_core_web_lg" if self.use_spacy else "None",
                    "context_aware": True,
                    "context": self._get_context_around_entity(text, entity_result)
                }
            elif source == "Pattern matching":
                # Find the matching pattern
                matching_patterns = []
                for pattern in self.patterns:
                    if hasattr(pattern, 'entity_type') and pattern.entity_type == entity_type:
                        for regex in pattern.patterns:
                            if re.search(regex, entity_text):
                                matching_patterns.append(regex)
                
                explanation["match_details"] = {
                    "detection_method": "Regex pattern matching",
                    "matching_patterns": matching_patterns,
                    "context_terms": self._get_context_terms_for_entity_type(entity_type)
                }
        
        return explanation
    
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
    
    def _analyze_common_formats(self, text):
        """
        Analyze text to identify common data formats (email, phone, etc).
        
        Args:
            text: The text to analyze
            
        Returns:
            List of RecognizerResult objects for common formats
        """
        results = []
        
        # Email patterns
        email_patterns = {
            'EMAIL_ADDRESS': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        # Phone number patterns
        phone_patterns = {
            'PHONE_NUMBER': [
                r'\b(?:\+?61|0)[2378]\s*\d{4}\s*\d{4}\b',  # Australian format
                r'\b\+\d{1,3}\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # International
                r'\b\(\d{2,3}\)\s*\d{3}[-.\s]?\d{4}\b'  # (02) 1234 5678 format
            ]
        }
        
        # ID and reference number patterns
        id_patterns = {
            'INSURANCE_CLAIM_NUMBER': [
                r'(?:Claim|CL|CLM)[#:\-\s]+([A-Z0-9-]+)',
                r'(?:Claim\s+(?:Number|Reference|ID|#))[#:\-\s]+([A-Z0-9-]+)'
            ],
            'INSURANCE_POLICY_NUMBER': [
                r'(?:Policy|POL)[#:\-\s]+([A-Z0-9-]+)',
                r'(?:Policy\s+(?:Number|ID|#))[#:\-\s]+([A-Z0-9-]+)'
            ],
            'VEHICLE_REGISTRATION': [
                r'(?:Registration|Rego|REG)[#:\-\s]+([A-Z0-9-]+)',
                r'(?:Vehicle\s+(?:Registration|Rego|REG))[#:\-\s]+([A-Z0-9-]+)'
            ],
            'VEHICLE_VIN': [
                r'(?:VIN|Vehicle\s+Identification\s+Number)[#:\-\s]+([A-Z0-9]{17})'
            ]
        }
        
        # AU-specific patterns
        au_patterns = {
            'AU_TFN': [
                r'\b\d{3}\s*\d{3}\s*\d{3}\b',  # 123 456 789
                r'(?:TFN|Tax\s+File\s+Number)[#:\-\s]+(\d{3}\s*\d{3}\s*\d{3})'
            ],
            'AU_MEDICARE': [
                r'\b\d{4}\s*\d{5}\s*\d{1}\b',  # 2123 45678 1
                r'(?:Medicare|Medicare\s+Number)[#:\-\s]+(\d{4}\s*\d{5}\s*\d{1})'
            ],
            'AU_ABN': [
                r'\b\d{2}\s*\d{3}\s*\d{3}\s*\d{3}\b',  # 51 824 753 556
                r'(?:ABN|Australian\s+Business\s+Number)[#:\-\s]+(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})'
            ],
            'AU_DRIVERS_LICENSE': [
                r'(?:Driver\'?s?\s+License|DL|License\s+Number)[#:\-\s]+([A-Z0-9]{6,10})'
            ]
        }
        
        # Process email patterns
        for entity_type, pattern in email_patterns.items():
            for match in re.finditer(pattern, text):
                start = match.start()
                end = match.end()
                matched_text = match.group()
                
                results.append(RecognizerResult(
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    score=0.95,  # High confidence for email format
                    text=matched_text
                ))
        
        # Process phone patterns
        for entity_type, patterns_list in phone_patterns.items():
            for pattern in patterns_list:
                for match in re.finditer(pattern, text):
                    start = match.start()
                    end = match.end()
                    matched_text = match.group()
                    
                    results.append(RecognizerResult(
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        score=0.92,  # High confidence for phone format
                        text=matched_text
                    ))
        
        # Process ID patterns
        for entity_type, patterns_list in id_patterns.items():
            for pattern in patterns_list:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    if match.lastindex and match.lastindex > 0:
                        # Use the capturing group
                        start = match.start(1)
                        end = match.end(1)
                        matched_text = match.group(1)
                    else:
                        # Use the whole match
                        start = match.start()
                        end = match.end()
                        matched_text = match.group()
                    
                    results.append(RecognizerResult(
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        score=0.9,
                        text=matched_text
                    ))
        
        # Process AU-specific patterns
        for entity_type, patterns_list in au_patterns.items():
            for pattern in patterns_list:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    if match.lastindex and match.lastindex > 0:
                        # Use the capturing group
                        start = match.start(1)
                        end = match.end(1)
                        matched_text = match.group(1)
                    else:
                        # Use the whole match
                        start = match.start()
                        end = match.end()
                        matched_text = match.group()
                    
                    results.append(RecognizerResult(
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        score=0.93,  # High confidence for structured AU formats
                        text=matched_text
                    ))
        
        return results
    
    def _get_context_around_entity(self, text, entity_result):
        """
        Get the text surrounding an entity for context.
        
        Args:
            text: The original text
            entity_result: A RecognizerResult object
            
        Returns:
            Dictionary with before/after context
        """
        window_size = 50  # Characters of context to include
        
        start = max(0, entity_result.start - window_size)
        end = min(len(text), entity_result.end + window_size)
        
        # Get text before and after the entity
        before = text[start:entity_result.start]
        after = text[entity_result.end:end]
        
        return {
            "before": before,
            "after": after
        }
    
    def _get_context_terms_for_entity_type(self, entity_type):
        """
        Get context terms that are associated with an entity type.
        
        Args:
            entity_type: The entity type
            
        Returns:
            List of context terms
        """
        # Find context terms from patterns
        context_terms = []
        
        for pattern in self.patterns:
            if hasattr(pattern, 'entity_type') and pattern.entity_type == entity_type:
                if hasattr(pattern, 'context') and pattern.context:
                    context_terms.extend(pattern.context)
        
        return context_terms
    
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
    
    def _deduplicate_and_resolve_conflicts(self, results):
        """
        Deduplicate results and resolve entity conflicts.
        
        Args:
            results: List of RecognizerResult objects
            
        Returns:
            Deduplicated list of RecognizerResult objects
        """
        deduplicated_results = []
        seen_spans = {}  # Maps (start, end, text) to list of results
        
        # Group results by span
        for result in results:
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
        
        # Priority by score (higher score wins)
        max_score_result = max(results, key=lambda r: r.score)
        if max_score_result.score > 0.95:  # Very high confidence
            return max_score_result
        
        # Document-specific entity types have higher priority
        doc_specific_types = [
            "EMAIL_ADDRESS", "EMAIL_SUBJECT", "EMAIL_FROM", "EMAIL_TO",
            "INSURANCE_CLAIM_NUMBER", "INSURANCE_POLICY_NUMBER", "VEHICLE_REGISTRATION", "VEHICLE_VIN", "INCIDENT_DATE",
            "MEDICARE_NUMBER", "PATIENT_ID", "DOCTOR_ID", "DIAGNOSIS_CODE", "MEDICATION"
        ]
        
        for entity_type in doc_specific_types:
            matching_results = [r for r in results if r.entity_type == entity_type]
            if matching_results:
                return matching_results[0]
        
        # Pattern-based rules for common prefixes
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
            "REF": "INSURANCE_CLAIM_NUMBER",  # REF is typically a reference/claim number
            "DOB": "DATE_OF_BIRTH",
            "DOI": "DATE_OF_INCIDENT",
            "VIN": "VEHICLE_VIN",
            "ABN": "AU_ABN",
            "TFN": "AU_TFN",
            "ACN": "AU_ACN",
            "MEDICARE": "MEDICARE_NUMBER"
        }
        
        for prefix, entity_type in prefix_to_entity.items():
            if text.upper().startswith(prefix) and any(r.entity_type == entity_type for r in results):
                for r in results:
                    if r.entity_type == entity_type:
                        return r
        
        # Format-based rules
        if re.match(r'^\d{4}\s*\d{5}\s*\d{1}$', text) and any(r.entity_type == "MEDICARE_NUMBER" for r in results):
            # Medicare number format
            for r in results:
                if r.entity_type == "MEDICARE_NUMBER":
                    return r
        
        # For dates, prioritize more specific date types over generic DATE
        date_priority = ["DATE_OF_BIRTH", "DATE_OF_INCIDENT", "INCIDENT_DATE", "DATE"]
        if re.match(r'^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}$', text):
            for date_type in date_priority:
                for r in results:
                    if r.entity_type == date_type:
                        return r
        
        # For generic alphanumeric patterns, prioritize by context
        # For now, return the first result (we'll enhance this later)
        return results[0]