"""
Main interface for the Allyanonimiser package.
"""
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any, Tuple

from .enhanced_analyzer import EnhancedAnalyzer, RecognizerResult
from .enhanced_anonymizer import EnhancedAnonymizer
from .utils.long_text_processor import (
    extract_pii_rich_segments,
    segment_long_text
)
from .pattern_manager import CustomPatternDefinition, PatternManager
from .pattern_registry import PatternRegistry
from .utils.text_preprocessor import TextPreprocessor, create_text_preprocessor
from .utils.settings_manager import SettingsManager, create_default_settings
from .reporting import report_manager, AnonymizationReport

@dataclass
class AnonymizationConfig:
    """
    Configuration options for anonymization process.
    
    Attributes:
        operators: Dictionary mapping entity types to anonymization operators.
            Available operators: "replace", "mask", "redact", "hash", "age_bracket", "custom".
            Example: {"PERSON": "replace", "EMAIL_ADDRESS": "mask"}
        language: Language code for text processing (default: "en").
        active_entity_types: Optional list of entity types to activate. If None, all are active.
        expand_acronyms: Whether to expand acronyms before anonymization using the configured dictionary.
        age_bracket_size: Size of age brackets when using the "age_bracket" operator (default: 5).
        keep_postcode: Whether to preserve postcodes when anonymizing addresses (default: True).
    
    Example:
        ```python
        from allyanonimiser import AnonymizationConfig
        
        config = AnonymizationConfig(
            operators={
                "PERSON": "replace",
                "EMAIL_ADDRESS": "mask",
                "PHONE_NUMBER": "redact",
                "DATE_OF_BIRTH": "age_bracket"
            },
            age_bracket_size=10,
            keep_postcode=True
        )
        
        result = anonymizer.anonymize(text, config=config)
        ```
    """
    operators: Optional[Dict[str, str]] = None
    language: str = "en"
    active_entity_types: Optional[List[str]] = None
    expand_acronyms: bool = False
    age_bracket_size: int = 5
    keep_postcode: bool = True

@dataclass
class AnalysisConfig:
    """
    Configuration options for analysis process.
    
    Attributes:
        language: Language code for text processing (default: "en").
        active_entity_types: Optional list of entity types to activate. If None, all are active.
        score_adjustment: Optional dictionary mapping entity types to score adjustments.
            Example: {"PERSON": 0.1, "EMAIL_ADDRESS": -0.05} to increase person detection confidence
            and decrease email address detection confidence.
        min_score_threshold: Optional minimum confidence score threshold (0.0-1.0).
        expand_acronyms: Whether to expand acronyms before analysis using the configured dictionary.
    
    Example:
        ```python
        from allyanonimiser import AnalysisConfig
        
        config = AnalysisConfig(
            active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
            min_score_threshold=0.7,
            expand_acronyms=True
        )
        
        results = analyzer.analyze(text, config=config)
        ```
    """
    language: str = "en"
    active_entity_types: Optional[List[str]] = None
    score_adjustment: Optional[Dict[str, float]] = None
    min_score_threshold: Optional[float] = None
    expand_acronyms: bool = False

def create_allyanonimiser(pattern_filepath=None, settings_path=None, enable_caching=True, max_cache_size=10000):
    """
    Create and configure an Allyanonimiser instance.
    
    This factory function creates a pre-configured Allyanonimiser instance
    with optional pattern and settings loading.
    
    Args:
        pattern_filepath: Optional path to a JSON file with pattern definitions
        settings_path: Optional path to a settings file (JSON or YAML)
        enable_caching: Whether to enable result caching for improved performance (default: True)
        max_cache_size: Maximum number of cached entries (default: 10000)
        
    Returns:
        Configured Allyanonimiser instance
        
    Example:
        ```python
        # Create with default settings
        ally = create_allyanonimiser()
        
        # Create with custom patterns
        ally = create_allyanonimiser(pattern_filepath="custom_patterns.json")
        
        # Create with custom settings
        ally = create_allyanonimiser(settings_path="settings.yaml")
        
        # Create with both custom patterns and settings
        ally = create_allyanonimiser(
            pattern_filepath="custom_patterns.json",
            settings_path="settings.yaml"
        )
        
        # Create with caching disabled (for memory-constrained environments)
        ally = create_allyanonimiser(enable_caching=False)
        
        # Create with larger cache for high-throughput applications
        ally = create_allyanonimiser(max_cache_size=50000)
        ```
    """
    # Create settings manager
    settings_manager = None
    if settings_path:
        settings_manager = SettingsManager(settings_path=settings_path)
    else:
        # Use default settings
        settings_manager = SettingsManager(settings=create_default_settings())
    
    # Create Allyanonimiser with settings and caching configuration
    ally = Allyanonimiser(
        settings_manager=settings_manager,
        enable_caching=enable_caching
    )
    
    # Configure the analyzer's cache size if specified
    if max_cache_size and hasattr(ally.analyzer, 'max_cache_size'):
        ally.analyzer.max_cache_size = max_cache_size
    
    # Load patterns if filepath provided
    if pattern_filepath:
        ally.load_patterns(pattern_filepath)
        
    return ally

class Allyanonimiser:
    """
    Main interface for PII detection and anonymization of content.
    This class provides a unified interface for processing all types of content.
    """
    def __init__(self, analyzer=None, anonymizer=None, pattern_registry=None, 
                text_preprocessor=None, settings_manager=None, enable_caching=True):
        self.settings_manager = settings_manager or SettingsManager()
        self.analyzer = analyzer or EnhancedAnalyzer(enable_caching=enable_caching)
        self.anonymizer = anonymizer or EnhancedAnonymizer(analyzer=self.analyzer)
        self.pattern_registry = pattern_registry or PatternRegistry()
        
        # Initialize text preprocessor from settings if available
        if text_preprocessor:
            self.text_preprocessor = text_preprocessor
        elif self.settings_manager.get_acronyms():
            self.text_preprocessor = TextPreprocessor(
                acronym_dict=self.settings_manager.get_acronyms(),
                case_sensitive=self.settings_manager.get_acronym_case_sensitive()
            )
        else:
            self.text_preprocessor = TextPreprocessor()
            
        # Configure from settings
        self._configure_from_settings()
        
        # Load default patterns
        self._load_default_patterns()
    
    def _configure_from_settings(self):
        """Configure the analyzer, anonymizer, and other components from settings."""
        # Configure active entity types if specified
        entity_types = self.settings_manager.get_entity_types()
        if entity_types:
            self.analyzer.set_active_entity_types(entity_types)
            
        # Configure score adjustments if specified
        score_adjustments = self.settings_manager.get_value('entity_types.score_adjustment')
        if score_adjustments:
            # Will be applied during analysis
            pass
            
        # Configure batch size for DataFrame processing
        self.batch_size = self.settings_manager.get_batch_size()
        self.worker_count = self.settings_manager.get_worker_count()
        
        # Get PyArrow setting if available
        self.use_pyarrow = self.settings_manager.get_value('processing.use_pyarrow', True)
    
    def _load_default_patterns(self):
        """Load default patterns from pattern modules."""
        from .patterns.au_patterns import get_au_pattern_definitions
        from .patterns.insurance_patterns import get_insurance_pattern_definitions
        from .patterns.general_patterns import get_general_pattern_definitions
        
        # Load Australian patterns
        for pattern_def in get_au_pattern_definitions():
            self.analyzer.add_pattern(CustomPatternDefinition(**pattern_def))
        
        # Load insurance patterns
        for pattern_def in get_insurance_pattern_definitions():
            self.analyzer.add_pattern(CustomPatternDefinition(**pattern_def))
        
        # Load general patterns
        for pattern_def in get_general_pattern_definitions():
            self.analyzer.add_pattern(CustomPatternDefinition(**pattern_def))
    
    def save_settings(self, settings_path):
        """
        Save current settings to a file.
        
        Args:
            settings_path: Path to save the settings
            
        Returns:
            Boolean indicating success
        """
        # Update settings from current state
        self.settings_manager.set_acronyms(
            self.text_preprocessor.acronym_dict,
            self.text_preprocessor.case_sensitive
        )
        
        # Save settings
        return self.settings_manager.save_settings(settings_path)
    
    def load_settings(self, settings_path):
        """
        Load settings from a file.
        
        Args:
            settings_path: Path to a settings file
            
        Returns:
            Boolean indicating success
        """
        success = self.settings_manager.load_settings(settings_path)
        
        if success:
            # Update components from new settings
            self.text_preprocessor = TextPreprocessor(
                acronym_dict=self.settings_manager.get_acronyms(),
                case_sensitive=self.settings_manager.get_acronym_case_sensitive()
            )
            self._configure_from_settings()
        
        return success
    
    def manage_acronyms(self, action, data=None, case_sensitive=False, csv_path=None, settings_path=None, 
                      acronym_col='acronym', expansion_col='expansion'):
        """
        Unified method for managing acronyms with multiple operations.
        
        Args:
            action: The action to perform ('set', 'add', 'remove', 'get', 'import')
            data: Dictionary mapping acronyms to their expanded forms or list of acronyms to remove
            case_sensitive: Whether acronym matching should be case-sensitive
            csv_path: Path to CSV file (for 'import' action)
            settings_path: Optional path to save settings (for 'import' action)
            acronym_col: Column name for acronyms (for 'import' action)
            expansion_col: Column name for expansions (for 'import' action)
            
        Returns:
            Dictionary of acronyms for 'get' action,
            Number of acronyms for 'import' action,
            None for other actions
            
        Raises:
            ValueError: If action is not recognized
            
        Examples:
            ```python
            # Set the acronym dictionary
            ally.manage_acronyms(
                action="set",
                data={"TPD": "Total and Permanent Disability", "CTP": "Compulsory Third Party"},
                case_sensitive=False
            )
            
            # Add acronyms to the existing dictionary
            ally.manage_acronyms(
                action="add",
                data={"DOL": "Date of Loss", "NTD": "Notice to Driver"}
            )
            
            # Remove acronyms
            ally.manage_acronyms(
                action="remove",
                data=["NTD"]
            )
            
            # Get current acronyms
            acronyms = ally.manage_acronyms(action="get")
            print(acronyms)  # {'TPD': 'Total and Permanent Disability', 'CTP': '...', 'DOL': '...'}
            
            # Import acronyms from CSV
            count = ally.manage_acronyms(
                action="import",
                csv_path="acronyms.csv",
                acronym_col="short_form",
                expansion_col="long_form"
            )
            print(f"Imported {count} acronyms")
            ```
        """
        if action == 'set':
            self.text_preprocessor = TextPreprocessor(acronym_dict=data, case_sensitive=case_sensitive)
            self.settings_manager.set_acronyms(data, case_sensitive)
            return None
            
        elif action == 'add':
            self.text_preprocessor.add_acronyms(data)
            self.settings_manager.add_acronyms(data)
            return None
            
        elif action == 'remove':
            self.text_preprocessor.remove_acronyms(data)
            self.settings_manager.remove_acronyms(data)
            return None
            
        elif action == 'get':
            return self.text_preprocessor.acronym_dict.copy()
            
        elif action == 'import':
            from .utils.settings_manager import import_acronyms_from_csv
            
            if not csv_path:
                raise ValueError("csv_path is required for 'import' action")
                
            success, count, settings = import_acronyms_from_csv(
                csv_path, settings_path, acronym_col, expansion_col, case_sensitive
            )
            
            if success and count > 0:
                # Update the text preprocessor with the new acronyms
                self.text_preprocessor = TextPreprocessor(
                    acronym_dict=settings.get('acronyms', {}).get('dictionary', {}),
                    case_sensitive=settings.get('acronyms', {}).get('case_sensitive', False)
                )
                
            return count
            
        else:
            raise ValueError(f"Unknown acronym action: {action}. " 
                             f"Valid actions are: 'set', 'add', 'remove', 'get', 'import'")
    
    # Backward compatibility methods - these will be deprecated in future versions
    
    def set_acronym_dictionary(self, acronym_dict, case_sensitive=False):
        """
        Set the acronym dictionary for text preprocessing.
        DEPRECATED: Use manage_acronyms('set', data=acronym_dict, case_sensitive=case_sensitive) instead.
        """
        return self.manage_acronyms('set', data=acronym_dict, case_sensitive=case_sensitive)
    
    def add_acronyms(self, acronym_dict):
        """
        Add acronyms to the existing acronym dictionary.
        DEPRECATED: Use manage_acronyms('add', data=acronym_dict) instead.
        """
        return self.manage_acronyms('add', data=acronym_dict)
        
    def import_acronyms_from_csv(self, csv_path, settings_path=None, acronym_col='acronym',
                               expansion_col='expansion', case_sensitive=False):
        """
        Import acronyms from a CSV file.
        DEPRECATED: Use manage_acronyms('import', csv_path=csv_path, ...) instead.
        """
        return self.manage_acronyms(
            'import', 
            csv_path=csv_path, 
            settings_path=settings_path,
            acronym_col=acronym_col,
            expansion_col=expansion_col,
            case_sensitive=case_sensitive
        )
    
    def remove_acronyms(self, acronyms):
        """
        Remove acronyms from the dictionary.
        DEPRECATED: Use manage_acronyms('remove', data=acronyms) instead.
        """
        return self.manage_acronyms('remove', data=acronyms)
        
    def get_acronyms(self):
        """
        Get the current acronym dictionary.
        DEPRECATED: Use manage_acronyms('get') instead.
        """
        return self.manage_acronyms('get')
    
    def analyze(self, text, language="en", active_entity_types=None, score_adjustment=None, 
                min_score_threshold=None, expand_acronyms=False, config=None):
        """
        Analyze text to detect PII entities.
        
        Args:
            text: The text to analyze
            language: The language of the text (default: en)
            active_entity_types: Optional list of entity types to activate (all are active if None)
            score_adjustment: Optional dict mapping entity_type to score adjustment
            min_score_threshold: Optional minimum score threshold (0.0-1.0)
            expand_acronyms: Whether to expand acronyms using the configured dictionary
            config: Optional AnalysisConfig object (overrides individual parameters)
            
        Returns:
            List of detected entities (RecognizerResult objects)
            
        Example:
            ```python
            from allyanonimiser import create_allyanonimiser, AnalysisConfig
            
            # Create instance
            ally = create_allyanonimiser()
            
            # Analyze text with direct parameters
            text = "My name is John Smith and my email is john.smith@example.com"
            results = ally.analyze(
                text,
                active_entity_types=["PERSON", "EMAIL_ADDRESS"],
                min_score_threshold=0.7
            )
            
            # Display detected entities
            for entity in results:
                print(f"Found {entity.entity_type}: {entity.text} (score: {entity.score:.2f})")
            
            # Using configuration object
            config = AnalysisConfig(
                active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
                min_score_threshold=0.8,
                score_adjustment={"PERSON": 0.1}  # Increase confidence for PERSON entities
            )
            
            results = ally.analyze(text, config=config)
            
            # Output:
            # Found PERSON: John Smith (score: 0.85)
            # Found EMAIL_ADDRESS: john.smith@example.com (score: 0.95)
            ```
        """
        # Use config object if provided
        if config is not None:
            language = config.language
            active_entity_types = config.active_entity_types
            score_adjustment = config.score_adjustment
            min_score_threshold = config.min_score_threshold
            expand_acronyms = config.expand_acronyms
        
        # Configure the analyzer
        if active_entity_types is not None:
            self.analyzer.set_active_entity_types(active_entity_types)
            
        if min_score_threshold is not None:
            self.analyzer.set_min_score_threshold(min_score_threshold)
        
        # Preprocess the text if needed
        processed_text = text
        if expand_acronyms and self.text_preprocessor.acronym_dict:
            processed_text, _ = self.text_preprocessor.expand_acronyms(text)
            
        # Run the analysis
        return self.analyzer.analyze(processed_text, language, score_adjustment)
    
    def anonymize(self, text, operators=None, language="en", active_entity_types=None, 
                 expand_acronyms=False, age_bracket_size=5, keep_postcode=True, config=None,
                 document_id=None, report=True):
        """
        Anonymize PII entities in text.
        
        Args:
            text: The text to anonymize
            operators: Dict of entity_type to anonymization operator
                Available operators: "replace", "mask", "redact", "hash", "age_bracket", "custom"
            language: The language of the text (default: en)
            active_entity_types: Optional list of entity types to activate (all are active if None)
            expand_acronyms: Whether to expand acronyms using the configured dictionary
            age_bracket_size: Size of age brackets when using "age_bracket" operator (default: 5)
            keep_postcode: Whether to keep postcodes when anonymizing addresses (default: True)
            config: Optional AnonymizationConfig object (overrides individual parameters)
            document_id: Optional identifier for the document (for reporting)
            report: Whether to record this operation in the reporting system (default: True)
            
        Returns:
            Dict with anonymized text and other metadata
            
        Example:
            ```python
            from allyanonimiser import create_allyanonimiser, AnonymizationConfig
            
            # Create instance
            ally = create_allyanonimiser()
            
            # Anonymize text with direct parameters
            text = "My name is John Smith, I was born on 15/6/1980 and my email is john.smith@example.com"
            result = ally.anonymize(
                text,
                operators={
                    "PERSON": "replace",          # Replace with <PERSON>
                    "DATE_OF_BIRTH": "age_bracket",  # Replace with age bracket
                    "EMAIL_ADDRESS": "mask"       # Replace with *****
                },
                age_bracket_size=10,
                active_entity_types=["PERSON", "EMAIL_ADDRESS", "DATE_OF_BIRTH"]
            )
            
            print(result["text"])
            # Output: "My name is <PERSON>, I was born on <40-50> and my email is *******************"
            
            # Using configuration object
            config = AnonymizationConfig(
                operators={
                    "PERSON": "replace",
                    "EMAIL_ADDRESS": "mask",
                    "DATE_OF_BIRTH": "age_bracket"
                },
                age_bracket_size=10,
                keep_postcode=True
            )
            
            result = ally.anonymize(text, config=config)
            print(result["text"])
            ```
            
        Available Operators:
            - "replace": Replace entity with entity type (e.g., <PERSON>)
            - "mask": Replace with asterisks of the same length (e.g., ********)
            - "redact": Replace with [REDACTED]
            - "hash": Replace with SHA-256 hash of the entity
            - "age_bracket": Replace age/DOB with age bracket (e.g., <40-45>)
            - "custom": Use a custom function (defined separately)
        """
        # Record start time for performance tracking
        start_time = time.time()
        
        # Use config object if provided
        if config is not None:
            operators = config.operators
            language = config.language
            active_entity_types = config.active_entity_types
            expand_acronyms = config.expand_acronyms
            age_bracket_size = config.age_bracket_size
            keep_postcode = config.keep_postcode
            
        # Configure the analyzer if active entity types are specified
        if active_entity_types is not None:
            self.analyzer.set_active_entity_types(active_entity_types)
            
        # Preprocess the text if needed
        processed_text = text
        if expand_acronyms and self.text_preprocessor.acronym_dict:
            processed_text, _ = self.text_preprocessor.expand_acronyms(text)
            
        # Perform anonymization
        result = self.anonymizer.anonymize(
            processed_text, 
            operators, 
            language, 
            age_bracket_size=age_bracket_size,
            keep_postcode=keep_postcode
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Add processing time to result
        result["processing_time"] = processing_time
        
        # Add document_id to the result for tracking
        if document_id:
            result["document_id"] = document_id
        else:
            # Generate a document ID if not provided
            result["document_id"] = f"doc_{int(time.time()*1000)}"
            
        # Add original text to the result for reporting purposes
        result["original_text"] = text
        
        # Record the anonymization in the reporting system if enabled
        if report:
            # Ensure we have an active report
            if not report_manager.get_current_report():
                report_manager.start_new_report()
                
            # Record this anonymization operation
            report_manager.get_current_report().record_anonymization(
                document_id=result["document_id"],
                original_text=text,
                anonymization_result=result,
                processing_time=processing_time
            )
        
        return result
    
    def process(self, text, language="en", active_entity_types=None, score_adjustment=None, 
              min_score_threshold=None, expand_acronyms=False, operators=None, 
              age_bracket_size=5, keep_postcode=True, analysis_config=None, anonymization_config=None,
              document_id=None, report=True):
        """
        Process text to analyze and anonymize in a single operation.
        
        This comprehensive method performs analysis and anonymization in one step,
        returning detailed results including detected entities, anonymized text,
        PII-rich segments, and structured data extraction.
        
        Args:
            text: The text to process
            language: The language of the text (default: en)
            active_entity_types: Optional list of entity types to activate (all are active if None)
            score_adjustment: Optional dict mapping entity_type to score adjustment
            min_score_threshold: Optional minimum score threshold (0.0-1.0)
            expand_acronyms: Whether to expand acronyms using the configured dictionary
            operators: Dict of entity_type to anonymization operator
            age_bracket_size: Size of age brackets when using "age_bracket" operator (default: 5)
            keep_postcode: Whether to keep postcodes when anonymizing addresses (default: True)
            analysis_config: Optional AnalysisConfig object (overrides individual analysis parameters)
            anonymization_config: Optional AnonymizationConfig object (overrides individual anonymization parameters)
            document_id: Optional identifier for the document (for reporting)
            report: Whether to record this operation in the reporting system (default: True)
            
        Returns:
            Dict with the following keys:
            - analysis: Dict containing detected entities
            - anonymized: The anonymized text
            - segments: List of PII-rich segments with their anonymized versions
            - structured_data: Extracted structured data from entities
            - preprocessing: (if acronyms expanded) Information about expanded acronyms
            - processing_time: Time taken to process the document (in seconds)
            
        Example:
            ```python
            from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig
            
            # Create instance
            ally = create_allyanonimiser()
            
            # Process text with configuration objects
            text = "Customer: John Smith (DOB: 15/6/1980)\nPolicy #: POL-12345678\nEmail: john.smith@example.com\nPhone: 0412-345-678\n\nCustomer reported an accident on 10/5/2024."
            
            analysis_config = AnalysisConfig(
                active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "DATE_OF_BIRTH"],
                min_score_threshold=0.7,
                expand_acronyms=True
            )
            
            anonymization_config = AnonymizationConfig(
                operators={
                    "PERSON": "replace",
                    "EMAIL_ADDRESS": "mask",
                    "PHONE_NUMBER": "redact",
                    "DATE_OF_BIRTH": "age_bracket"
                },
                age_bracket_size=10
            )
            
            result = ally.process(text, analysis_config=analysis_config, anonymization_config=anonymization_config)
            
            # Access different parts of the result
            print("Anonymized text:")
            print(result["anonymized"])
            
            print("\nDetected entities:")
            for entity in result["analysis"]["entities"]:
                print(f"{entity['entity_type']}: {entity['text']} (score: {entity['score']:.2f})")
            
            print("\nPII-rich segments:")
            for segment in result["segments"]:
                print(f"Original: {segment['text']}")
                print(f"Anonymized: {segment['anonymized']}")
            
            print("\nStructured data:")
            for key, value in result["structured_data"].items():
                print(f"{key}: {value}")
        """
        # Record start time for performance tracking
        start_time = time.time()
        
        # Create config objects if not provided
        if analysis_config is None:
            analysis_config = AnalysisConfig(
                language=language,
                active_entity_types=active_entity_types,
                score_adjustment=score_adjustment,
                min_score_threshold=min_score_threshold,
                expand_acronyms=expand_acronyms
            )
            
        if anonymization_config is None:
            anonymization_config = AnonymizationConfig(
                operators=operators,
                language=language,
                active_entity_types=active_entity_types,
                expand_acronyms=expand_acronyms,
                age_bracket_size=age_bracket_size,
                keep_postcode=keep_postcode
            )
        
        # Ensure the same active_entity_types are used for both operations
        if anonymization_config.active_entity_types is None and analysis_config.active_entity_types is not None:
            anonymization_config.active_entity_types = analysis_config.active_entity_types
        elif analysis_config.active_entity_types is None and anonymization_config.active_entity_types is not None:
            analysis_config.active_entity_types = anonymization_config.active_entity_types
        
        # Preprocess the text if needed
        processed_text = text
        expansions_metadata = []
        if analysis_config.expand_acronyms and self.text_preprocessor.acronym_dict:
            processed_text, expansions_metadata = self.text_preprocessor.expand_acronyms(text)
        
        # Analyze the text using config object
        analysis_results = self.analyze(
            processed_text, 
            config=analysis_config
        )
        
        # Anonymize the text using config object - pass document_id and report flags through
        anonymized_results = self.anonymize(
            processed_text, 
            config=anonymization_config,
            document_id=document_id,
            report=report
        )
        
        # Get PII-rich segments
        segments = extract_pii_rich_segments(processed_text)
        
        # Add anonymized versions of segments
        for segment in segments:
            segment_text = segment['text']
            # Don't report these segment anonymizations separately
            anonymized_segment = self.anonymize(
                segment_text, 
                config=anonymization_config,
                report=False
            )
            segment['anonymized'] = anonymized_segment['text']
        
        # Extract structured data from entities
        structured_data = self._extract_structured_data(analysis_results)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        result = {
            'analysis': {
                'entities': [
                    {
                        'entity_type': result.entity_type,
                        'start': result.start,
                        'end': result.end,
                        'text': processed_text[result.start:result.end] if result.text is None else result.text,
                        'score': result.score
                    }
                    for result in analysis_results
                ]
            },
            'anonymized': anonymized_results['text'],
            'segments': segments,
            'structured_data': structured_data,
            'processing_time': processing_time
        }
        
        # Add document_id if provided
        if document_id:
            result['document_id'] = document_id
        
        # Add preprocessing metadata if acronyms were expanded
        if analysis_config.expand_acronyms and expansions_metadata:
            result['preprocessing'] = {
                'expanded_acronyms': [
                    {
                        'acronym': exp['acronym'],
                        'expansion': exp['expansion']
                    }
                    for exp in expansions_metadata
                ]
            }
        
        # Add statistics about entities found
        result['statistics'] = {
            'entity_count': len(analysis_results),
            'entity_types': list(set(r.entity_type for r in analysis_results)),
            'entity_type_counts': {
                entity_type: sum(1 for r in analysis_results if r.entity_type == entity_type)
                for entity_type in set(r.entity_type for r in analysis_results)
            }
        }
            
        return result
    
    def get_available_entity_types(self):
        """
        Get information about all available entity types.
        
        Returns:
            Dictionary of entity types and their metadata
        """
        return self.analyzer.get_available_entity_types()
    
    def explain_entity(self, text, entity):
        """
        Explain why a particular entity was detected.
        
        Args:
            text: The original text
            entity: A detected entity (dictionary with entity_type, start, end, text, score)
            
        Returns:
            Explanation dictionary
        """
        # Convert entity dict to RecognizerResult
        entity_result = RecognizerResult(
            entity_type=entity['entity_type'],
            start=entity['start'],
            end=entity['end'],
            score=entity['score'],
            text=entity['text']
        )
        
        return self.analyzer.explain_detection(text, entity_result)
        
    def manage_patterns(self, action, data=None, filepath=None, entity_type=None, examples=None, 
                      context=None, name=None, generalization_level="medium", csv_path=None, 
                      entity_type_col='entity_type', pattern_col='pattern', context_col='context',
                      name_col='name', score_col='score'):
        """
        Unified method for managing patterns with multiple operations.
        
        Args:
            action: The action to perform ('add', 'create_from_examples', 'load', 'import', 'save')
            data: Pattern definition for 'add' action
            filepath: Path to JSON file for 'load' and 'save' actions
            entity_type: Entity type name for 'create_from_examples'
            examples: List of example strings for 'create_from_examples'
            context: Optional list of context words for 'create_from_examples'
            name: Optional pattern name for 'create_from_examples'
            generalization_level: Level of pattern generalization for 'create_from_examples'
                Options: "low" (exact match), "medium" (balanced), "high" (more general)
            csv_path: Path to CSV file for 'import' action
            entity_type_col: Column name for entity types in CSV
            pattern_col: Column name for patterns in CSV
            context_col: Column name for context in CSV
            name_col: Column name for pattern names in CSV
            score_col: Column name for confidence scores in CSV
            
        Returns:
            - For 'add': True if pattern was added successfully, False otherwise
            - For 'create_from_examples': The created pattern definition
            - For 'load': Number of patterns loaded
            - For 'import': Number of patterns imported
            - For 'save': Path where patterns were saved
            
        Raises:
            ValueError: If action is not recognized or required parameters are missing
            
        Examples:
            ```python
            # Add a custom pattern manually
            success = ally.manage_patterns(
                action="add",
                data={
                    "entity_type": "POLICY_NUMBER",
                    "patterns": ["POL-\\d{8}"],
                    "context": ["policy", "number"],
                    "name": "Policy number format"
                }
            )
            
            # Create pattern from examples
            pattern = ally.manage_patterns(
                action="create_from_examples",
                entity_type="CLAIM_ID",
                examples=["CL-12345", "CL-67890", "CL-54321"],
                context=["claim", "id", "number"],
                name="Claim ID Pattern",
                generalization_level="medium"  # Options: "low", "medium", "high"
            )
            print(f"Generated pattern: {pattern.patterns[0]}")
            
            # Load patterns from JSON file
            count = ally.manage_patterns(
                action="load",
                filepath="/path/to/patterns.json"
            )
            print(f"Loaded {count} patterns")
            
            # Import patterns from CSV
            count = ally.manage_patterns(
                action="import",
                csv_path="/path/to/patterns.csv",
                entity_type_col="type",
                pattern_col="regex"
            )
            
            # Save patterns to JSON file
            filepath = ally.manage_patterns(
                action="save",
                filepath="/path/to/output_patterns.json"
            )
            print(f"Saved patterns to {filepath}")
            ```
            
        CSV Format for 'import' action:
            ```csv
            entity_type,pattern,context,name,score
            POLICY_NUMBER,POL-\\d{8},"policy,number",Policy number format,0.8
            CLAIM_ID,CL-\\d{5},"claim,id",Claim ID pattern,0.75
            ```
        """
        if action == 'add':
            if data is None:
                raise ValueError("data is required for 'add' action")
                
            # Convert dict to CustomPatternDefinition if needed
            if isinstance(data, dict):
                pattern = CustomPatternDefinition(**data)
            else:
                pattern = data
                
            # Add to analyzer
            result = self.analyzer.add_pattern(pattern)
            
            # Also register with pattern registry
            if result:
                self.pattern_registry.register_pattern(pattern)
                
            return result
            
        elif action == 'create_from_examples':
            if entity_type is None or examples is None:
                raise ValueError("entity_type and examples are required for 'create_from_examples' action")
                
            from .utils.spacy_helpers import create_regex_from_examples
            
            # Generate regex pattern from examples
            regex = create_regex_from_examples(examples, generalization_level=generalization_level)
            
            # Create pattern definition
            pattern = CustomPatternDefinition(
                entity_type=entity_type,
                patterns=[regex],
                context=context,
                name=name,
                description=f"Custom pattern for {entity_type} generated from {len(examples)} examples"
            )
            
            # Add to analyzer and registry
            self.manage_patterns('add', data=pattern)
            
            return pattern
            
        elif action == 'load':
            if filepath is None:
                raise ValueError("filepath is required for 'load' action")
                
            count = self.pattern_registry.load_patterns(filepath)
            
            # Add loaded patterns to analyzer
            for pattern in self.pattern_registry.get_patterns():
                self.analyzer.add_pattern(pattern)
                
            return count
            
        elif action == 'import':
            if csv_path is None:
                raise ValueError("csv_path is required for 'import' action")
                
            from .utils.settings_manager import import_patterns_from_csv as import_patterns
            
            success, count, settings = import_patterns(
                csv_path, filepath, 
                entity_type_col, pattern_col, context_col, name_col, score_col
            )
            
            # Add patterns to analyzer
            if success and 'patterns' in settings:
                for pattern_def in settings['patterns']:
                    self.manage_patterns('add', data=pattern_def)
                    
            return count
            
        elif action == 'save':
            if filepath is None:
                raise ValueError("filepath is required for 'save' action")
                
            return self.pattern_registry.save_patterns(filepath)
            
        else:
            raise ValueError(f"Unknown pattern action: {action}. "
                             f"Valid actions are: 'add', 'create_from_examples', 'load', 'import', 'save'")
    
    # Backward compatibility methods - these will be deprecated in future versions
    
    def add_pattern(self, pattern_definition):
        """
        Add a custom pattern to the analyzer.
        DEPRECATED: Use manage_patterns('add', data=pattern_definition) instead.
        """
        return self.manage_patterns('add', data=pattern_definition)
        
    def create_pattern_from_examples(self, entity_type, examples, context=None, name=None, 
                                    generalization_level="medium"):
        """
        Create and add a custom pattern from example strings.
        DEPRECATED: Use manage_patterns('create_from_examples', entity_type=..., examples=...) instead.
        """
        return self.manage_patterns(
            'create_from_examples',
            entity_type=entity_type,
            examples=examples,
            context=context,
            name=name,
            generalization_level=generalization_level
        )
        
    def load_patterns(self, filepath):
        """
        Load patterns from a JSON file.
        DEPRECATED: Use manage_patterns('load', filepath=filepath) instead.
        """
        return self.manage_patterns('load', filepath=filepath)
        
    def import_patterns_from_csv(self, csv_path, pattern_filepath=None, entity_type_col='entity_type',
                              pattern_col='pattern', context_col='context', 
                              name_col='name', score_col='score'):
        """
        Import pattern definitions from a CSV file.
        DEPRECATED: Use manage_patterns('import', csv_path=csv_path, ...) instead.
        """
        return self.manage_patterns(
            'import',
            csv_path=csv_path,
            filepath=pattern_filepath,
            entity_type_col=entity_type_col,
            pattern_col=pattern_col,
            context_col=context_col,
            name_col=name_col,
            score_col=score_col
        )
        
    def save_patterns(self, filepath):
        """
        Save all patterns to a JSON file.
        DEPRECATED: Use manage_patterns('save', filepath=filepath) instead.
        """
        return self.manage_patterns('save', filepath=filepath)
    
    def export_config(self, config_path, include_metadata=True):
        """
        Export a shareable configuration file based on current settings.
        
        This creates a simplified configuration file that includes only the essential
        settings needed to reproduce the current functionality.
        
        Args:
            config_path: Path to save the configuration file (supports .json, .yaml, .yml)
            include_metadata: Whether to include descriptive metadata in the output
            
        Returns:
            Boolean indicating success
            
        Example:
            ```python
            from allyanonimiser import create_allyanonimiser
            
            # Create and configure instance
            ally = create_allyanonimiser()
            
            # Add acronyms
            ally.manage_acronyms(
                action="add",
                data={
                    "TPD": "Total and Permanent Disability",
                    "CTP": "Compulsory Third Party"
                }
            )
            
            # Add patterns
            ally.manage_patterns(
                action="create_from_examples",
                entity_type="POLICY_NUMBER",
                examples=["POL-12345", "POL-67890"]
            )
            
            # Export configuration to JSON
            ally.export_config("config.json")
            
            # Export configuration to YAML
            ally.export_config("config.yaml")
            
            # Export without metadata (more compact)
            ally.export_config("config_minimal.json", include_metadata=False)
            ```
            
        The exported configuration can be used to create a new instance with the same settings:
        
            ```python
            # Create new instance with exported config
            ally_new = create_allyanonimiser(settings_path="config.json")
            ```
        """
        # Update settings from current state to ensure they're up to date
        self.settings_manager.set_acronyms(
            self.text_preprocessor.acronym_dict,
            self.text_preprocessor.case_sensitive
        )
        
        return self.settings_manager.export_config(config_path, include_metadata)
    
    def process_dataframe(self, df, text_columns=None, column=None, operation='process', 
                          n_workers=None, use_pyarrow=None, analysis_config=None, 
                          anonymization_config=None, **kwargs):
        """
        Unified method for processing DataFrames with various operations.
        
        Args:
            df: Input DataFrame
            text_columns: Column name(s) containing text to process for 'process' operation
            column: Column name for 'detect' and 'anonymize' operations
            operation: The operation to perform ('process', 'detect', 'anonymize')
            n_workers: Number of worker processes for parallel processing
            use_pyarrow: Whether to use PyArrow for performance optimization
            analysis_config: Optional AnalysisConfig object
            anonymization_config: Optional AnonymizationConfig object
            **kwargs: Additional arguments to pass to the underlying DataFrame processor
                For 'anonymize': output_column, operators, age_bracket_size, keep_postcode
                For 'detect': min_score_threshold, active_entity_types, score_adjustment
            
        Returns:
            - For 'process': Dict with processed DataFrame and entity DataFrame
            - For 'detect': DataFrame with detected entities
            - For 'anonymize': DataFrame with anonymized text
            
        Raises:
            ValueError: If operation is not recognized or required parameters are missing
            
        Examples:
            ```python
            import pandas as pd
            from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig
            
            # Create DataFrame
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "notes": [
                    "Customer John Smith (DOB: 15/6/1980) called about policy POL-123456.",
                    "Jane Doe (email: jane.doe@example.com) requested a refund.",
                    "Alex Johnson from Sydney NSW 2000 reported an incident."
                ]
            })
            
            # Create Allyanonimiser
            ally = create_allyanonimiser()
            
            # 1. Process DataFrame with detection
            entities_df = ally.process_dataframe(
                df, 
                column="notes", 
                operation="detect",
                min_score_threshold=0.7,
                active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
            )
            # Result: DataFrame with columns for entity_type, text, score, start, end, source_id
            
            # 2. Anonymize specific column
            anonymized_df = ally.process_dataframe(
                df, 
                column="notes", 
                operation="anonymize",
                output_column="anonymized_notes",  # New column for anonymized text
                operators={
                    "PERSON": "replace",
                    "EMAIL_ADDRESS": "mask",
                    "PHONE_NUMBER": "redact"
                }
            )
            # Result: Original DataFrame with new 'anonymized_notes' column
            
            # 3. Full processing of multiple columns
            result = ally.process_dataframe(
                df,
                text_columns=["notes"],  # Can be a list of columns
                operation="process",
                n_workers=4,             # Parallel processing
                use_pyarrow=True         # Use PyArrow for performance
            )
            # Result: Dict with 'df' (processed DataFrame) and 'entities' (entity DataFrame)
            
            # 4. Using configuration objects
            analysis_config = AnalysisConfig(
                active_entity_types=["PERSON", "EMAIL_ADDRESS"],
                min_score_threshold=0.7
            )
            
            anonymization_config = AnonymizationConfig(
                operators={
                    "PERSON": "replace",
                    "EMAIL_ADDRESS": "mask"
                }
            )
            
            result = ally.process_dataframe(
                df,
                text_columns=["notes"],
                operation="process",
                analysis_config=analysis_config,
                anonymization_config=anonymization_config
            )
            ```
            
        Performance Tips:
            - Set `n_workers` to the number of CPU cores for parallel processing
            - Enable `use_pyarrow=True` for large DataFrames (requires PyArrow to be installed)
            - Process DataFrames in batches if they are very large
            - Use specific `active_entity_types` to reduce processing time
        """
        from .dataframe_processor import DataFrameProcessor
        
        # Use instance setting if not explicitly provided
        if use_pyarrow is None and hasattr(self, 'use_pyarrow'):
            use_pyarrow = self.use_pyarrow
            
        # Create processor
        processor = DataFrameProcessor(self, n_workers=n_workers, use_pyarrow=use_pyarrow)
        
        # Extract config parameters if provided
        if analysis_config is not None:
            if 'active_entity_types' not in kwargs and analysis_config.active_entity_types is not None:
                kwargs['active_entity_types'] = analysis_config.active_entity_types
            if 'min_score_threshold' not in kwargs and analysis_config.min_score_threshold is not None:
                kwargs['min_score_threshold'] = analysis_config.min_score_threshold
        
        if anonymization_config is not None:
            if 'operators' not in kwargs and anonymization_config.operators is not None:
                kwargs['operators'] = anonymization_config.operators
            if 'age_bracket_size' not in kwargs:
                kwargs['age_bracket_size'] = anonymization_config.age_bracket_size
            if 'keep_postcode' not in kwargs:
                kwargs['keep_postcode'] = anonymization_config.keep_postcode
        
        # Perform requested operation
        if operation == 'process':
            if text_columns is None:
                raise ValueError("text_columns is required for 'process' operation")
            return processor.process_dataframe(df, text_columns, **kwargs)
            
        elif operation == 'detect':
            if column is None:
                raise ValueError("column is required for 'detect' operation")
            return processor.detect_pii(df, column, **kwargs)
            
        elif operation == 'anonymize':
            if column is None:
                raise ValueError("column is required for 'anonymize' operation")
            return processor.anonymize_column(df, column, **kwargs)
            
        else:
            raise ValueError(f"Unknown DataFrame operation: {operation}. "
                             f"Valid operations are: 'process', 'detect', 'anonymize'")
    
    # Backward compatibility methods - these will be deprecated in future versions
    
    def create_dataframe_processor(self, n_workers=None, use_pyarrow=None):
        """
        Create a DataFrame processor for handling pandas DataFrames.
        DEPRECATED: Use process_dataframe() directly instead.
        """
        from .dataframe_processor import DataFrameProcessor
        
        # Use instance setting if not explicitly provided
        if use_pyarrow is None and hasattr(self, 'use_pyarrow'):
            use_pyarrow = self.use_pyarrow
            
        return DataFrameProcessor(self, n_workers=n_workers, use_pyarrow=use_pyarrow)
    
    def detect_pii_in_dataframe(self, df, column, **kwargs):
        """
        Detect PII in a DataFrame column.
        DEPRECATED: Use process_dataframe(df, column=column, operation='detect', **kwargs) instead.
        """
        return self.process_dataframe(df, column=column, operation='detect', **kwargs)
    
    def anonymize_dataframe(self, df, column, **kwargs):
        """
        Anonymize PII in a DataFrame column.
        DEPRECATED: Use process_dataframe(df, column=column, operation='anonymize', **kwargs) instead.
        """
        return self.process_dataframe(df, column=column, operation='anonymize', **kwargs)
        
    def batch_process(self, texts, content_types=None, anonymize=True, operators=None, 
                     language="en", active_entity_types=None, expand_acronyms=False,
                     analysis_config=None, anonymization_config=None):
        """
        Process multiple texts in batch mode.
        
        Args:
            texts: List of texts to process
            content_types: Optional list of content types (one per text)
            anonymize: Whether to anonymize the texts
            operators: Dict of entity_type to anonymization operator
            language: The language of the texts (default: en)
            active_entity_types: Optional list of entity types to activate
            expand_acronyms: Whether to expand acronyms
            analysis_config: Optional AnalysisConfig object (overrides individual analysis parameters)
            anonymization_config: Optional AnonymizationConfig object (overrides individual anonymization parameters)
            
        Returns:
            List of result dictionaries, one per input text
        """
        # Create config objects if not provided
        if analysis_config is None:
            analysis_config = AnalysisConfig(
                language=language,
                active_entity_types=active_entity_types,
                expand_acronyms=expand_acronyms
            )
            
        if anonymization_config is None and anonymize:
            anonymization_config = AnonymizationConfig(
                operators=operators,
                language=language,
                active_entity_types=active_entity_types,
                expand_acronyms=expand_acronyms
            )
            
        results = []
        
        for i, text in enumerate(texts):
            # Get content type for this text if provided
            content_type = None
            if content_types and i < len(content_types):
                content_type = content_types[i]
                
            # Process this text
            result = self.process(
                text=text,
                analysis_config=analysis_config,
                anonymization_config=anonymization_config
            )
            
            # Set content type if provided
            if content_type:
                result["content_type"] = content_type
                
            # Add to results
            results.append(result)
            
        return results
        
    def process_files(self, file_paths, output_dir=None, anonymize=True, operators=None,
                     language="en", active_entity_types=None, expand_acronyms=False,
                     save_results=False, analysis_config=None, anonymization_config=None,
                     report=True, report_output=None, report_format="html"):
        """
        Process multiple files.
        
        Args:
            file_paths: List of file paths to process
            output_dir: Directory to save output files (required if save_results=True)
            anonymize: Whether to anonymize the texts
            operators: Dict of entity_type to anonymization operator
            language: The language of the texts (default: en)
            active_entity_types: Optional list of entity types to activate
            expand_acronyms: Whether to expand acronyms
            save_results: Whether to save results to output_dir
            analysis_config: Optional AnalysisConfig object (overrides individual analysis parameters)
            anonymization_config: Optional AnonymizationConfig object (overrides individual anonymization parameters)
            report: Whether to generate a processing report (default: True)
            report_output: Path to save the report file (if None, only return the report)
            report_format: Format for the report file ("html", "json", or "csv")
            
        Returns:
            Dict containing:
              - 'results': List of result dictionaries, one per input file
              - 'report': Report summary if report=True
        """
        import os
        import json
        
        # Start batch processing timer
        batch_start_time = time.time()
        
        # Start a new report if requested
        if report:
            batch_report = report_manager.start_new_report()
            batch_id = batch_report.session_id
        else:
            batch_id = f"batch_{int(time.time()*1000)}"
        
        # Create config objects if not provided
        if analysis_config is None:
            analysis_config = AnalysisConfig(
                language=language,
                active_entity_types=active_entity_types,
                expand_acronyms=expand_acronyms
            )
            
        if anonymization_config is None and anonymize:
            anonymization_config = AnonymizationConfig(
                operators=operators,
                language=language,
                active_entity_types=active_entity_types,
                expand_acronyms=expand_acronyms
            )
        
        # Create output directory if it doesn't exist
        if save_results and output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        results = []
        
        for i, file_path in enumerate(file_paths):
            try:
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
                # Get file basename for output
                basename = os.path.basename(file_path)
                name, _ = os.path.splitext(basename)
                
                # Generate document ID
                document_id = f"{batch_id}_{i}_{name}"
                    
                # Process file
                result = self.process(
                    text=text,
                    analysis_config=analysis_config,
                    anonymization_config=anonymization_config,
                    document_id=document_id,
                    report=report
                )
                
                # Add file info to result
                result["file_info"] = {
                    "path": file_path,
                    "name": name
                }
                
                # Save results if requested
                if save_results and output_dir:
                    # Save anonymized text
                    anon_path = os.path.join(output_dir, f"{name}_anonymized.txt")
                    with open(anon_path, 'w', encoding='utf-8') as f:
                        f.write(result["anonymized"])
                        
                    # Save analysis results
                    analysis_path = os.path.join(output_dir, f"{name}_analysis.json")
                    with open(analysis_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2)
                        
                    # Add output paths to result
                    result["output_files"] = {
                        "anonymized": anon_path,
                        "analysis": analysis_path
                    }
                    
                # Add to results
                results.append(result)
                
            except Exception as e:
                # Record the error in results
                error_result = {
                    "file_info": {
                        "path": file_path,
                        "name": os.path.basename(file_path)
                    },
                    "error": str(e),
                    "success": False
                }
                results.append(error_result)
        
        # Create response dictionary
        response = {
            "results": results,
            "success": True,
            "total_files": len(file_paths),
            "successful_files": sum(1 for r in results if r.get("success", True))
        }
        
        # Add report if requested
        if report:
            # Finalize the report
            batch_report.finalize()
            
            # Add report summary to response
            response["report"] = batch_report.get_summary()
            
            # Save report file if path provided
            if report_output:
                try:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(report_output), exist_ok=True)
                    
                    # Export report in requested format
                    report_file = batch_report.export_report(report_output, report_format)
                    response["report_file"] = report_file
                except Exception as e:
                    response["report_error"] = str(e)
        
        return response
        
    def _extract_structured_data(self, analysis_results):
        """
        Extract structured data from detected entities.
        
        Args:
            analysis_results: Results from the analyzer
            
        Returns:
            Dict with structured data grouped by entity type
        """
        structured_data = {}
        
        # Group entities by type
        entity_groups = {}
        for result in analysis_results:
            entity_type = result.entity_type
            
            if entity_type not in entity_groups:
                entity_groups[entity_type] = []
                
            entity_groups[entity_type].append({
                'text': result.text,
                'score': result.score
            })
        
        # Convert to a simpler structure
        for entity_type, entities in entity_groups.items():
            # Use snake_case for field names
            field_name = entity_type.lower()
            
            # For single entities, store just the text
            if len(entities) == 1:
                structured_data[field_name] = entities[0]['text']
            # For multiple entities, store the list
            else:
                structured_data[field_name] = [e['text'] for e in entities]
        
        return structured_data
    
    def get_report(self, session_id=None):
        """
        Get a report of anonymization operations.
        
        Args:
            session_id: Optional session ID to retrieve a specific report
        
        Returns:
            AnonymizationReport object or None if not found
        """
        if session_id:
            return report_manager.get_report(session_id)
        return report_manager.get_current_report()
    
    def start_new_report(self, session_id=None):
        """
        Start a new anonymization report.
        
        Args:
            session_id: Optional session ID for the report
        
        Returns:
            The new AnonymizationReport object
        """
        return report_manager.start_new_report(session_id)
    
    def finalize_report(self, output_path=None, format="html"):
        """
        Finalize the current report and optionally save it to a file.
        
        Args:
            output_path: Optional path to save the report
            format: Format for the report file (html, json, or csv)
        
        Returns:
            Dict with report summary
        """
        report = report_manager.get_current_report()
        if not report:
            return {"error": "No active report to finalize"}
        
        # Finalize the report
        report.finalize()
        
        # Export the report if a path is provided
        if output_path:
            try:
                report.export_report(output_path, format)
            except Exception as e:
                return {
                    "error": f"Failed to save report: {str(e)}",
                    "summary": report.get_summary()
                }
        
        return report.get_summary()
    
    def display_report_in_notebook(self, session_id=None):
        """
        Display a report in a Jupyter notebook.
        
        This method generates rich visualizations in a notebook environment.
        
        Args:
            session_id: Optional session ID to display a specific report
        """
        report = self.get_report(session_id)
        if not report:
            print("No report available to display.")
            return
        
        # Display the report in the notebook
        report.display_in_notebook()