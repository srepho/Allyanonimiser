"""
Unified analyzer for PII detection across all document types.
"""
import logging
import re
import threading

import spacy

from .common_formats import analyze_common_formats
from .conflict_resolver import deduplicate_and_resolve_conflicts
from .context_analyzer import ContextAnalyzer
from .false_positives import (
    LOCATION_FP_WORDS,
    NON_LOCATION_PREFIXES,
    ORG_ABBREVIATIONS,
    PERSON_FP_WORDS,
    PERSON_TRAILING_STOP_WORDS,
    STREET_SUFFIXES,
)
from .recognizer_result import RecognizerResult

logger = logging.getLogger(__name__)

# Module-level cache so the model is loaded at most once per process.
# Protected by a lock for free-threaded Python (3.13t / 3.14t).
_spacy_model_cache: dict = {}
_spacy_model_lock = threading.Lock()


def load_spacy_model(model_name="en_core_web_sm", fallback_model="en_core_web_lg"):
    """Load a spaCy model with fallback, cached at module level (thread-safe).

    Defaults to ``en_core_web_sm`` (small, ~44 MB). The fallback is
    ``en_core_web_lg`` (large, ~587 MB); if neither is installed, falls
    back to ``spacy.blank("en")``, which disables NER entirely (only regex
    pattern detection will work).
    """
    cache_key = (model_name, fallback_model)

    # Fast path: already cached (no lock needed for dict reads in CPython,
    # but explicit lock is correct for free-threaded builds).
    if cache_key in _spacy_model_cache:
        return _spacy_model_cache[cache_key]

    with _spacy_model_lock:
        # Double-check after acquiring the lock
        if cache_key in _spacy_model_cache:
            return _spacy_model_cache[cache_key]

        try:
            nlp = spacy.load(model_name)
            nlp._allyanonimiser_loaded_as = model_name
        except OSError:
            try:
                nlp = spacy.load(fallback_model)
                nlp._allyanonimiser_loaded_as = fallback_model
                logger.warning(
                    "spaCy model %r not found; falling back to %r. "
                    "Install the requested model with: "
                    "python -m spacy download %s",
                    model_name, fallback_model, model_name,
                )
            except OSError:
                nlp = spacy.blank("en")
                # Distinct sentinel so check_spacy_status() can tell this
                # from a real model — spacy.blank('en').meta['name'] is
                # 'pipeline', which is misleadingly model-shaped.
                nlp._allyanonimiser_loaded_as = "blank_en"
                logger.warning(
                    "Neither %r nor %r is installed; falling back to "
                    "spacy.blank('en'). NER entities (PERSON, LOCATION, ORG, "
                    "etc.) will NOT be detected — only regex patterns. "
                    "Install the default model with: "
                    "python -m spacy download %s "
                    "(or %s for higher NER accuracy).",
                    model_name, fallback_model, model_name, fallback_model,
                )

        _spacy_model_cache[cache_key] = nlp
        return nlp

class EnhancedAnalyzer:
    """Unified analyzer for PII detection.

    Combines pattern-based and NER-based entity detection with configurable
    active entities.  Includes result caching for improved performance with
    repetitive content.

    .. note:: Instances are **not thread-safe**.  In multi-threaded code,
       create one ``EnhancedAnalyzer`` per thread.  The underlying spaCy
       model is shared safely via the module-level cache.
    """
    def __init__(
        self,
        min_score_threshold: float = 0.7,
        enable_caching: bool = True,
        max_cache_size: int = 10_000,
        spacy_model: str | None = "en_core_web_sm",
    ):
        self.patterns: list = []
        self.active_entity_types: set = set()
        self.min_score_threshold = min_score_threshold

        # Initialize spaCy model for NER.
        # Pass spacy_model=None to disable spaCy entirely (pattern-only mode).
        self.spacy_model_loaded: str | None = None
        if spacy_model is None:
            self.use_spacy = False
            self.nlp = None
        else:
            try:
                self.nlp = load_spacy_model(spacy_model)
                # Use the loader-attached sentinel: spacy.blank('en') reports
                # meta['name'] = 'pipeline', which misleads check_spacy_status.
                self.spacy_model_loaded = getattr(
                    self.nlp, "_allyanonimiser_loaded_as", spacy_model,
                )
                # use_spacy reflects whether real NER is available — blank
                # has no NER pipe and should not be advertised as healthy.
                self.use_spacy = self.spacy_model_loaded != "blank_en"
                if self.use_spacy:
                    logger.info("spaCy model loaded: %s", self.spacy_model_loaded)
            except Exception as e:
                logger.warning("Could not load spaCy model: %s", e)
                self.use_spacy = False
                self.nlp = None

        # Context-aware false-positive filter, built once (constructing it
        # rebuilds all context pattern/keyword tables).
        self._context_analyzer = ContextAnalyzer()

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

    def analyze(
        self,
        text,
        language="en",
        score_adjustment=None,
        active_entity_types=None,
        min_score_threshold=None,
    ):
        """
        Analyze text to detect PII entities.

        Args:
            text: The text to analyze
            language: The language of the text (default: en)
            score_adjustment: Optional dictionary mapping entity_type to score adjustment value
                (positive or negative float that will be added to the confidence score)
            active_entity_types: Optional list of entity types to detect for this
                call only. Falls back to the instance-level setting
                (``set_active_entity_types``) when None.
            min_score_threshold: Optional confidence threshold for this call only.
                Falls back to the instance-level setting when None.

        Returns:
            List of RecognizerResult objects representing detected entities
        """
        if not text:
            return []

        if score_adjustment is None:
            score_adjustment = {}

        # Resolve per-call overrides without mutating instance state, so one
        # call's filters can never leak into the next.
        if active_entity_types is not None:
            active_entity_types = set(active_entity_types)
        else:
            active_entity_types = self.active_entity_types
        if min_score_threshold is None:
            min_score_threshold = self.min_score_threshold
        elif not 0 <= min_score_threshold <= 1.0:
            raise ValueError("Threshold must be between 0 and 1.0")

        # Check result cache for exact text match if caching is enabled
        if self.enable_caching:
            # Create a cache key that includes active entity types and score adjustment
            cache_key = self._create_cache_key(
                text, score_adjustment, active_entity_types, min_score_threshold
            )

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
                self._evict_oldest(self._pattern_result_cache, self.max_cache_size)
                self._pattern_result_cache[text] = pattern_results.copy()

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
                    self._evict_oldest(self._spacy_result_cache, self.max_cache_size)
                    self._spacy_result_cache[text] = spacy_results.copy()

        # Add entity-specific extraction for common formats
        format_results = analyze_common_formats(text)

        # Combine results
        combined_results = pattern_results + spacy_results + format_results

        # Apply score adjustments
        for result in combined_results:
            if result.entity_type in score_adjustment:
                result.score += score_adjustment[result.entity_type]
                # Cap score at 1.0
                result.score = min(1.0, result.score)

        # Filter by active entity types, if specified
        if active_entity_types:
            combined_results = [r for r in combined_results if r.entity_type in active_entity_types]

        # Filter by score threshold
        combined_results = [r for r in combined_results if r.score >= min_score_threshold]

        # De-duplicate results and resolve entity conflicts
        deduplicated_results = deduplicate_and_resolve_conflicts(
            combined_results, self.patterns, full_text=text,
        )

        # Apply context-aware filtering
        context_analyzer = self._context_analyzer

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
            self._evict_oldest(self._result_cache, self.max_cache_size)

            # Store a copy of the results
            self._result_cache[cache_key] = filtered_results.copy()

        return filtered_results

    def analyze_batch(
        self,
        texts: list[str],
        language: str = "en",
        score_adjustment=None,
        active_entity_types=None,
        min_score_threshold=None,
    ) -> list[list["RecognizerResult"]]:
        """Analyze a batch of texts. Returns a list of result lists.

        Uses spaCy's ``nlp.pipe()`` for efficient batch NER when available,
        while still leveraging the per-text cache. Results are identical to
        calling :meth:`analyze` on each text individually.
        """
        # Pre-warm spaCy NER cache for uncached texts in one pipe() call.
        # Only useful when caching is on — analyze() reads spaCy results from
        # the cache, so without it the pipe() work would just be redone.
        if self.use_spacy and self.enable_caching:
            uncached = [
                t for t in dict.fromkeys(texts)
                if t and t not in self._spacy_result_cache
            ]
            if uncached:
                docs = self.nlp.pipe(uncached, batch_size=min(256, len(uncached)))
                for raw_text, doc in zip(uncached, docs):
                    self._evict_oldest(self._spacy_result_cache, self.max_cache_size)
                    self._spacy_result_cache[raw_text] = self._doc_to_results(doc)

        return [
            self.analyze(
                t, language, score_adjustment,
                active_entity_types=active_entity_types,
                min_score_threshold=min_score_threshold,
            )
            for t in texts
        ]

    @staticmethod
    def _evict_oldest(cache: dict, max_size: int) -> None:
        """Evict the oldest half of *cache* once it reaches *max_size*.

        Dicts preserve insertion order, so the first keys are the oldest
        entries. Evicting half (rather than clearing everything) keeps the
        most recent results warm.
        """
        if len(cache) >= max_size:
            for key in list(cache)[: max_size // 2]:
                del cache[key]

    def _create_cache_key(
        self, text, score_adjustment=None, active_entity_types=None,
        min_score_threshold=None,
    ):
        """
        Create a unique cache key for the given text and parameters.

        Args:
            text: The text to analyze
            score_adjustment: Optional score adjustment dictionary
            active_entity_types: Effective entity-type filter for this call
            min_score_threshold: Effective score threshold for this call

        Returns:
            A hashable cache key
        """
        if active_entity_types is None:
            active_entity_types = self.active_entity_types
        if min_score_threshold is None:
            min_score_threshold = self.min_score_threshold
        # For very long texts, use a truncated version + hash to save memory
        if len(text) > 200:
            import hashlib
            # Use first 100 chars + hash of full text
            text_hash = hashlib.md5(text.encode()).hexdigest()
            text_key = f"{text[:100]}...{text_hash}"
        else:
            text_key = text

        # Include active entity types in the key
        entity_types_key = tuple(sorted(active_entity_types)) if active_entity_types else "all"

        # Include score adjustment in the key if provided
        if score_adjustment:
            adj_items = tuple(sorted(score_adjustment.items()))
            return (text_key, entity_types_key, adj_items, min_score_threshold)

        return (text_key, entity_types_key, None, min_score_threshold)

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
                    "model": self.spacy_model_loaded or "None",
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

            # Use pre-compiled regexes when the pattern object provides them
            # (CustomPatternDefinition does); fall back to raw strings for
            # foreign pattern objects.
            regexes = getattr(pattern, 'compiled_patterns', None)
            if regexes is None:
                regexes = [p for p in pattern.patterns if isinstance(p, str)]

            for regex_pattern in regexes:
                try:
                    finditer = (
                        regex_pattern.finditer(text)
                        if isinstance(regex_pattern, re.Pattern)
                        else re.finditer(regex_pattern, text)
                    )
                    # Find all matches
                    for match in finditer:
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
                    logger.debug("Error processing pattern %s: %s", regex_pattern, e)
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
        return self._doc_to_results(self.nlp(text))

    def _doc_to_results(self, doc) -> list["RecognizerResult"]:
        """Convert a spaCy Doc to a filtered RecognizerResult list.

        Shared by the single-text path (:meth:`_analyze_with_spacy`) and the
        batch path (:meth:`analyze_batch`) so both apply identical entity-type
        mapping and false-positive suppression.
        """
        results = []

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
                if any(ent.text.lower().endswith(suffix) for suffix in STREET_SUFFIXES):
                    continue

                # Check if entire text is a false positive
                if lc_text in PERSON_FP_WORDS:
                    continue

                # Check if text contains multiple false positive words
                words = lc_text.split()
                if any(word in PERSON_FP_WORDS for word in words):
                    continue

                # Check for boundary issues - words that shouldn't be part of
                # names. Iteratively pop trailing stop-word tokens (spaCy's
                # split() handles \n as a separator, so newline-absorbed labels
                # match with the same single rule).
                text_parts = ent.text.split()
                trimmed_changed = False
                while len(text_parts) > 1 and text_parts[-1].lower() in PERSON_TRAILING_STOP_WORDS:
                    text_parts.pop()
                    trimmed_changed = True

                if trimmed_changed:
                    # Re-locate the trimmed text inside the original span so the
                    # offsets stay anchored to the start. The last surviving
                    # token always appears as a prefix of ent.text after a
                    # split/join, so end = start + position of (last token end)
                    # in the original text.
                    new_end = ent.start_char + ent.text.find(text_parts[-1]) + len(text_parts[-1])
                    result = RecognizerResult(
                        entity_type=entity_type,
                        start=ent.start_char,
                        end=new_end,
                        score=0.9,
                        text=ent.text[:new_end - ent.start_char],
                    )
                    results.append(result)
                    continue

            # Skip ORGANIZATION false positives
            if entity_type == "ORGANIZATION":
                lc_text = ent.text.lower()
                # Common abbreviations that shouldn't be organizations
                if lc_text in ORG_ABBREVIATIONS:
                    continue

            # Skip LOCATION false positives
            if entity_type == "LOCATION":
                lc_text = ent.text.lower()

                # Check if the entire text is a false positive
                if lc_text in LOCATION_FP_WORDS:
                    continue

                # Check if it's a single word that's clearly not a location
                if len(lc_text.split()) == 1:
                    if any(lc_text.startswith(prefix) for prefix in NON_LOCATION_PREFIXES):
                        continue

                # Check for patterns that indicate it's not a location
                # e.g., "Repairs in progress" - "Repairs" is not a location
                if lc_text.endswith("s") and lc_text[:-1] in LOCATION_FP_WORDS:
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

