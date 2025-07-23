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
    Includes result caching for improved performance with repetitive content.
    """
    def __init__(self, min_score_threshold=0.7, enable_caching=True, max_cache_size=10000):
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
            
        # Result caching system
        self.enable_caching = enable_caching
        self.max_cache_size = max_cache_size
        self._result_cache = {}
        self._pattern_result_cache = {}
        self._spacy_result_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
            
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
        if not text:
            return []
            
        if score_adjustment is None:
            score_adjustment = {}
            
        # Check result cache for exact text match if caching is enabled
        if self.enable_caching:
            # Create a cache key that includes active entity types and score adjustment
            cache_key = self._create_cache_key(text, score_adjustment)
            
            # Check if we have a cached result
            if cache_key in self._result_cache:
                self._cache_hits += 1
                # Return a deep copy to prevent modification of cached results
                return [RecognizerResult(**result.__dict__) for result in self._result_cache[cache_key]]
                
            self._cache_misses += 1
            
        # Check if we have cached pattern results
        pattern_results = []
        if self.enable_caching and text in self._pattern_result_cache:
            pattern_results = self._pattern_result_cache[text].copy()
        else:
            # Get results from pattern-based detection
            pattern_results = self._analyze_with_patterns(text)
            # Cache pattern results if caching is enabled
            if self.enable_caching:
                self._pattern_result_cache[text] = pattern_results.copy()
                # Limit pattern cache size
                if len(self._pattern_result_cache) > self.max_cache_size:
                    self._pattern_result_cache = {}
        
        # Check if we have cached spaCy results
        spacy_results = []
        if self.use_spacy:
            if self.enable_caching and text in self._spacy_result_cache:
                spacy_results = self._spacy_result_cache[text].copy()
            else:
                # Get results from spaCy NER
                spacy_results = self._analyze_with_spacy(text)
                # Cache spaCy results if caching is enabled
                if self.enable_caching:
                    self._spacy_result_cache[text] = spacy_results.copy()
                    # Limit spaCy cache size
                    if len(self._spacy_result_cache) > self.max_cache_size:
                        self._spacy_result_cache = {}
        
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
        
        # Apply context-aware filtering
        from .context_analyzer import ContextAnalyzer
        context_analyzer = ContextAnalyzer()
        
        filtered_results = []
        for result in deduplicated_results:
            # Check if likely false positive based on context
            if not context_analyzer.is_likely_false_positive(text, result.entity_type, result.start, result.end):
                # Analyze context for confidence boost
                context_analysis = context_analyzer.analyze_context(text, result.entity_type, result.start, result.end)
                
                # Apply confidence boost if context matches
                if context_analysis['confidence_boost'] > 0:
                    result.score = min(1.0, result.score + context_analysis['confidence_boost'])
                
                filtered_results.append(result)
        
        # Cache the final result if caching is enabled
        if self.enable_caching:
            # Manage cache size
            if len(self._result_cache) >= self.max_cache_size:
                # Simple LRU implementation: clear half the cache when full
                self._result_cache = {}
                
            # Store a copy of the results
            self._result_cache[cache_key] = filtered_results.copy()
            
        return filtered_results
        
    def _create_cache_key(self, text, score_adjustment=None):
        """
        Create a unique cache key for the given text and parameters.
        
        Args:
            text: The text to analyze
            score_adjustment: Optional score adjustment dictionary
            
        Returns:
            A hashable cache key
        """
        # For very long texts, use a truncated version + hash to save memory
        if len(text) > 200:
            import hashlib
            # Use first 100 chars + hash of full text
            text_hash = hashlib.md5(text.encode()).hexdigest()
            text_key = f"{text[:100]}...{text_hash}"
        else:
            text_key = text
            
        # Include active entity types in the key
        entity_types_key = tuple(sorted(self.active_entity_types)) if self.active_entity_types else "all"
        
        # Include score adjustment in the key if provided
        if score_adjustment:
            adj_items = tuple(sorted(score_adjustment.items()))
            return (text_key, entity_types_key, adj_items, self.min_score_threshold)
        
        return (text_key, entity_types_key, None, self.min_score_threshold)
        
    def get_cache_statistics(self):
        """
        Get statistics about the cache usage.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enable_caching:
            return {"caching_enabled": False}
            
        total_lookups = self._cache_hits + self._cache_misses
        hit_rate = 0 if total_lookups == 0 else (self._cache_hits / total_lookups)
        
        return {
            "caching_enabled": True,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "result_cache_size": len(self._result_cache),
            "pattern_cache_size": len(self._pattern_result_cache),
            "spacy_cache_size": len(self._spacy_result_cache),
            "max_cache_size": self.max_cache_size
        }
        
    def clear_cache(self):
        """
        Clear all caches.
        
        Returns:
            Number of cached items cleared
        """
        total_cleared = len(self._result_cache) + len(self._pattern_result_cache) + len(self._spacy_result_cache)
        self._result_cache = {}
        self._pattern_result_cache = {}
        self._spacy_result_cache = {}
        return total_cleared
    
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
                # Check for policy/claim patterns
                if (lc_text.startswith("policy") or 
                    lc_text.startswith("ref") or 
                    lc_text.startswith("claim") or
                    "number" in lc_text):
                    continue
                    
                # Check for street/place suffixes
                if any(ent.text.lower().endswith(suffix) for suffix in [" st", " street", " rd", " road", 
                                                                        " ave", " avenue", " dr", " drive", 
                                                                        " ln", " lane", " pl", " place",
                                                                        " ct", " court", " cr", " crescent"]):
                    continue
                
                # Check for common false positive words
                false_positive_words = [
                    # Status and state words
                    "balance", "outstanding", "await", "awaiting", "pending", "completed", 
                    "processed", "received", "submitted", "approved", "declined", "rejected", 
                    "cancelled", "closed", "open", "active", "inactive", "suspended", 
                    "terminated", "expired", "current", "previous", "ongoing", "finished",
                    
                    # Action words often misdetected
                    "review", "update", "check", "verify", "confirm", "validate", "process",
                    "submit", "approve", "decline", "reject", "cancel", "close", "complete",
                    "advised", "notify", "inform", "contact", "follow", "proceed", "continue",
                    
                    # Business/Insurance specific terms
                    "excess", "premium", "deductible", "coverage", "liability", "claim",
                    "policy", "payment", "invoice", "receipt", "refund", "credit", "debit",
                    "assessment", "evaluation", "inspection", "investigation", "settlement",
                    
                    # Service/Repair terms
                    "repairer", "repairs", "service", "maintenance", "workshop", "garage",
                    "parts", "replacement", "installation", "removal", "diagnostic", "estimate",
                    
                    # Communication status
                    "unreachable", "unavailable", "contactable", "available", "busy", "engaged",
                    
                    # Common single words that aren't names
                    "drop", "pickup", "delivery", "collection", "dispatch", "arrival",
                    "departure", "transfer", "forward", "return", "exchange", "replace",
                    
                    # Document/Form related
                    "form", "document", "report", "statement", "declaration", "certificate",
                    "authorization", "approval", "confirmation", "acknowledgment", "notice",
                    
                    # Time-related terms
                    "today", "tomorrow", "yesterday", "daily", "weekly", "monthly", "yearly",
                    "immediate", "urgent", "routine", "scheduled", "overdue", "expired",
                    
                    # Quality/Condition terms
                    "new", "used", "damaged", "repaired", "replaced", "original", "genuine",
                    "aftermarket", "compatible", "suitable", "adequate", "insufficient"
                ]
                
                # Check if entire text is a false positive
                if lc_text in false_positive_words:
                    continue
                
                # Check if text contains multiple false positive words
                words = lc_text.split()
                if any(word in false_positive_words for word in words):
                    continue
                
                # Check for boundary issues - words that shouldn't be part of names
                stop_words = ["subject", "matter", "issue", "claim", "policy", "number", 
                              "date", "time", "amount", "status", "type", "category"]
                
                # If person name ends with a stop word, trim it
                text_parts = ent.text.split()
                if len(text_parts) > 1 and text_parts[-1].lower() in stop_words:
                    # Recalculate the text without the stop word
                    trimmed_text = " ".join(text_parts[:-1])
                    # Calculate new end position based on original start
                    new_end = ent.start_char + len(trimmed_text)
                    # Create a new result with corrected boundaries
                    result = RecognizerResult(
                        entity_type=entity_type,
                        start=ent.start_char,
                        end=new_end,
                        score=0.9,
                        text=trimmed_text
                    )
                    results.append(result)
                    continue
                    
            # Skip ORGANIZATION false positives
            if entity_type == "ORGANIZATION":
                lc_text = ent.text.lower()
                # Common abbreviations that shouldn't be organizations
                if lc_text in ["dob", "doi", "medicare", "abn", "tfn", "acn"]:
                    continue
            
            # Skip LOCATION false positives
            if entity_type == "LOCATION":
                lc_text = ent.text.lower()
                
                # Common words that are NOT locations
                location_false_positives = [
                    # Action words
                    "await", "awaiting", "awaits", "awaited",
                    "repair", "repairs", "repairing", "repaired",
                    "service", "services", "servicing", "serviced",
                    "process", "processing", "processed",
                    "update", "updates", "updating", "updated",
                    "review", "reviews", "reviewing", "reviewed",
                    "submit", "submits", "submitting", "submitted",
                    "pending", "complete", "completed", "completing",
                    
                    # Status words
                    "open", "closed", "active", "inactive",
                    "approved", "declined", "rejected", "cancelled",
                    "available", "unavailable", "occupied", "vacant",
                    
                    # Business/Insurance terms
                    "claim", "claims", "policy", "policies",
                    "coverage", "liability", "excess", "premium",
                    "payment", "balance", "outstanding", "overdue",
                    
                    # Department/Service terms
                    "workshop", "workshops", "garage", "garages",
                    "parts", "spares", "supplies", "inventory",
                    "storage", "warehouse", "facility", "facilities",
                    
                    # Common misdetections
                    "drop", "drops", "pickup", "delivery",
                    "arrival", "departure", "transit", "shipping"
                ]
                
                # Check if the entire text is a false positive
                if lc_text in location_false_positives:
                    continue
                
                # Check if it's a single word that's clearly not a location
                if len(lc_text.split()) == 1:
                    # Single words that start with these are usually not locations
                    non_location_prefixes = ["await", "repair", "serv", "proc", "updat", "review", 
                                           "submit", "pend", "complet", "approv", "declin", "reject"]
                    if any(lc_text.startswith(prefix) for prefix in non_location_prefixes):
                        continue
                
                # Check for patterns that indicate it's not a location
                # e.g., "Repairs in progress" - "Repairs" is not a location
                if lc_text.endswith("s") and lc_text[:-1] in location_false_positives:
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
        
        # Phone number patterns - improved for Australian numbers
        phone_patterns = {
            'AU_PHONE': [
                r'\b(?:\+61|0)4\d{2}[\s-]?\d{3}[\s-]?\d{3}\b',  # Mobile
                r'\b(?:\+61|0)[2378][\s-]?\d{4}[\s-]?\d{4}\b',  # Landline
                r'\(\d{2}\)\s*\d{4}[\s-]?\d{4}\b',              # (02) 1234 5678
                r'\b13\d{2}\s*\d{2}\b',                          # 13xx xx
                r'\b1300\s+\d{3}\s+\d{3}\b',                     # 1300 xxx xxx
                r'\b1800\s*\d{3}\s*\d{3}\b'                      # 1800 xxx xxx
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
        
        # AU-specific patterns with improved detection
        au_patterns = {
            'AU_TFN': [
                r'(?:TFN|Tax\s+File\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b'
            ],
            'AU_MEDICARE': [
                r'(?:Medicare|Medicare\s+Number)[:\s]*([2-6]\d{3}\s*\d{5}\s*\d{1})\b'
            ],
            'AU_ABN': [
                r'(?:ABN|Australian\s+Business\s+Number)[:\s]*(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})\b'
            ],
            'AU_ACN': [
                r'(?:ACN|Australian\s+Company\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b'
            ],
            'AU_DRIVERS_LICENSE': [
                r'(?:Driver\'?s?\s+License|Licence|DL)[:\s#]*([A-Z0-9]{6,10})\b',
                r'(?:NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\s+License[:\s]*(\d{6,10})\b'
            ],
            'AU_PASSPORT': [
                r'(?:Passport|Passport\s+Number)[:\s]*([A-Z][0-9]{7})\b'
            ],
            'AU_CENTRELINK_CRN': [
                r'(?:CRN|Centrelink\s+Reference\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3}[A-Z]?)\b'
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
        # Import validator here to avoid circular imports
        from .validators import EntityValidator
        
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
                # Only one entity type for this span, validate it
                result = span_results[0]
                
                # Apply validation based on entity type
                if result.entity_type == 'DATE':
                    is_valid, date_type = EntityValidator.validate_date(result.text)
                    if not is_valid and date_type in ['state_postcode', 'phone_prefix', 'phone_suffix', 'medicare_number', 'service_number']:
                        continue  # Skip false positive dates
                        
                elif result.entity_type == 'NUMBER':
                    is_valid, num_type = EntityValidator.validate_number(result.text)
                    if not is_valid:
                        continue  # Skip invalid numbers
                        
                elif result.entity_type == 'AU_PHONE':
                    is_valid, phone_type = EntityValidator.validate_phone_number(result.text)
                    if not is_valid:
                        continue  # Skip invalid phone numbers
                        
                elif result.entity_type == 'AU_MEDICARE':
                    # Remove spaces before validation
                    medicare_text = result.text.replace(' ', '')
                    is_valid, error = EntityValidator.validate_medicare_number(medicare_text)
                    if not is_valid:
                        continue  # Skip invalid Medicare numbers
                        
                elif result.entity_type == 'AU_TFN':
                    # Remove spaces before validation
                    tfn_text = result.text.replace(' ', '')
                    is_valid, error = EntityValidator.validate_tfn(tfn_text)
                    if not is_valid:
                        continue  # Skip invalid TFNs
                        
                elif result.entity_type == 'AU_ABN':
                    # Remove spaces before validation
                    abn_text = result.text.replace(' ', '')
                    is_valid, error = EntityValidator.validate_abn(abn_text)
                    if not is_valid:
                        continue  # Skip invalid ABNs
                
                deduplicated_results.append(result)
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
            upper_text = text.upper()
            
            # Check for common false positive patterns
            false_positive_patterns = [
                lower_text.startswith("policy"),
                lower_text.startswith("ref"),
                lower_text.startswith("claim"),
                upper_text.startswith("POL-"),  # Policy numbers
                upper_text.startswith("CL-"),   # Claim numbers
                upper_text.startswith("CLM-"),  # Claim numbers
                "number" in lower_text,
                # Common street/place suffixes that might be misidentified as person names
                any(text.lower().endswith(suffix) for suffix in [" st", " street", " rd", " road", " ave", " avenue", 
                                                                " dr", " drive", " ln", " lane", " pl", " place",
                                                                " ct", " court", " cr", " crescent"]),
                # Medicare/insurance terms
                lower_text == "medicare",
                lower_text == "dob",  # Date of birth abbreviation
                lower_text == "doi"   # Date of incident abbreviation
            ]
            
            if any(false_positive_patterns):
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
        
        # Special handling for service numbers that might be detected as DATE
        if any(r.entity_type == 'AU_PHONE' for r in results) and any(r.entity_type == 'DATE' for r in results):
            # Check if it's a service number pattern
            if re.match(r'^(1300|1800|13\d{2})\s+', text):
                # Prefer AU_PHONE over DATE for service numbers
                for r in results:
                    if r.entity_type == 'AU_PHONE':
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