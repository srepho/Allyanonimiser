"""
Main interface for the Allyanonimiser package.
"""
import re
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

def create_allyanonimiser(pattern_filepath=None, settings_path=None):
    """
    Create and configure an Allyanonimiser instance.
    
    Args:
        pattern_filepath: Optional path to a JSON file with pattern definitions
        settings_path: Optional path to a settings file (JSON or YAML)
        
    Returns:
        Configured Allyanonimiser instance
    """
    # Create settings manager
    settings_manager = None
    if settings_path:
        settings_manager = SettingsManager(settings_path=settings_path)
    else:
        # Use default settings
        settings_manager = SettingsManager(settings=create_default_settings())
    
    # Create Allyanonimiser with settings
    ally = Allyanonimiser(settings_manager=settings_manager)
    
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
                text_preprocessor=None, settings_manager=None):
        self.settings_manager = settings_manager or SettingsManager()
        self.analyzer = analyzer or EnhancedAnalyzer()
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
    
    def set_acronym_dictionary(self, acronym_dict, case_sensitive=False):
        """
        Set the acronym dictionary for text preprocessing.
        
        Args:
            acronym_dict: Dictionary mapping acronyms to their expanded forms
            case_sensitive: Whether acronym matching should be case-sensitive
            
        Returns:
            None
        """
        self.text_preprocessor = TextPreprocessor(acronym_dict=acronym_dict, case_sensitive=case_sensitive)
        
        # Update settings
        self.settings_manager.set_acronyms(acronym_dict, case_sensitive)
    
    def add_acronyms(self, acronym_dict):
        """
        Add acronyms to the existing acronym dictionary.
        
        Args:
            acronym_dict: Dictionary mapping acronyms to their expanded forms
            
        Returns:
            None
        """
        self.text_preprocessor.add_acronyms(acronym_dict)
        
        # Update settings
        self.settings_manager.add_acronyms(acronym_dict)
        
    def import_acronyms_from_csv(self, csv_path, settings_path=None, acronym_col='acronym',
                               expansion_col='expansion', case_sensitive=False):
        """
        Import acronyms from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
            settings_path: Optional path to save the settings
            acronym_col: Column name for acronyms
            expansion_col: Column name for expansions
            case_sensitive: Whether acronym matching should be case-sensitive
            
        Returns:
            Number of acronyms imported
        """
        from .utils.settings_manager import import_acronyms_from_csv
        
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
    
    def remove_acronyms(self, acronyms):
        """
        Remove acronyms from the dictionary.
        
        Args:
            acronyms: List of acronym keys to remove
            
        Returns:
            None
        """
        self.text_preprocessor.remove_acronyms(acronyms)
        
        # Update settings
        self.settings_manager.remove_acronyms(acronyms)
        
    def get_acronyms(self):
        """
        Get the current acronym dictionary.
        
        Returns:
            Dictionary mapping acronyms to their expanded forms
        """
        return self.text_preprocessor.acronym_dict.copy()
    
    def analyze(self, text, language="en", active_entity_types=None, score_adjustment=None, 
                min_score_threshold=None, expand_acronyms=False):
        """
        Analyze text to detect PII entities.
        
        Args:
            text: The text to analyze
            language: The language of the text (default: en)
            active_entity_types: Optional list of entity types to activate (all are active if None)
            score_adjustment: Optional dict mapping entity_type to score adjustment
            min_score_threshold: Optional minimum score threshold (0.0-1.0)
            expand_acronyms: Whether to expand acronyms using the configured dictionary
            
        Returns:
            List of detected entities
        """
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
    
    def anonymize(self, text, operators=None, language="en", active_entity_types=None, expand_acronyms=False):
        """
        Anonymize PII entities in text.
        
        Args:
            text: The text to anonymize
            operators: Dict of entity_type to anonymization operator
            language: The language of the text (default: en)
            active_entity_types: Optional list of entity types to activate (all are active if None)
            expand_acronyms: Whether to expand acronyms using the configured dictionary
            
        Returns:
            Dict with anonymized text and other metadata
        """
        # Configure the analyzer if active entity types are specified
        if active_entity_types is not None:
            self.analyzer.set_active_entity_types(active_entity_types)
            
        # Preprocess the text if needed
        processed_text = text
        if expand_acronyms and self.text_preprocessor.acronym_dict:
            processed_text, _ = self.text_preprocessor.expand_acronyms(text)
            
        return self.anonymizer.anonymize(processed_text, operators, language)
    
    def process(self, text, language="en", active_entity_types=None, score_adjustment=None, 
              min_score_threshold=None, expand_acronyms=False):
        """
        Process text to analyze and anonymize in a single operation.
        
        Args:
            text: The text to process
            language: The language of the text (default: en)
            active_entity_types: Optional list of entity types to activate (all are active if None)
            score_adjustment: Optional dict mapping entity_type to score adjustment
            min_score_threshold: Optional minimum score threshold (0.0-1.0)
            expand_acronyms: Whether to expand acronyms using the configured dictionary
            
        Returns:
            Dict with analysis, anonymized text, and other metadata
        """
        # Configure the analyzer
        if active_entity_types is not None:
            self.analyzer.set_active_entity_types(active_entity_types)
            
        if min_score_threshold is not None:
            self.analyzer.set_min_score_threshold(min_score_threshold)
        
        # Preprocess the text if needed
        processed_text = text
        expansions_metadata = []
        if expand_acronyms and self.text_preprocessor.acronym_dict:
            processed_text, expansions_metadata = self.text_preprocessor.expand_acronyms(text)
        
        # Analyze the text
        analysis_results = self.analyze(
            processed_text, 
            language, 
            active_entity_types, 
            score_adjustment, 
            min_score_threshold
        )
        
        # Anonymize the text
        anonymized_results = self.anonymize(
            processed_text, 
            language=language, 
            active_entity_types=active_entity_types
        )
        
        # Get PII-rich segments
        segments = extract_pii_rich_segments(processed_text)
        
        # Add anonymized versions of segments
        for segment in segments:
            segment_text = segment['text']
            anonymized_segment = self.anonymize(
                segment_text, 
                language=language, 
                active_entity_types=active_entity_types
            )
            segment['anonymized'] = anonymized_segment['text']
        
        # Extract structured data from entities
        structured_data = self._extract_structured_data(analysis_results)
        
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
            'structured_data': structured_data
        }
        
        # Add preprocessing metadata if acronyms were expanded
        if expand_acronyms and expansions_metadata:
            result['preprocessing'] = {
                'expanded_acronyms': [
                    {
                        'acronym': exp['acronym'],
                        'expansion': exp['expansion']
                    }
                    for exp in expansions_metadata
                ]
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
        
    def add_pattern(self, pattern_definition):
        """
        Add a custom pattern to the analyzer.
        
        Args:
            pattern_definition: Either a CustomPatternDefinition object or a dictionary
                with entity_type, patterns, and optional fields
                
        Returns:
            True if pattern was added successfully, False otherwise
        """
        # Convert dict to CustomPatternDefinition if needed
        if isinstance(pattern_definition, dict):
            pattern = CustomPatternDefinition(**pattern_definition)
        else:
            pattern = pattern_definition
            
        # Add to analyzer
        result = self.analyzer.add_pattern(pattern)
        
        # Also register with pattern registry
        if result:
            self.pattern_registry.register_pattern(pattern)
            
        return result
        
    def create_pattern_from_examples(self, entity_type, examples, context=None, name=None, 
                                    generalization_level="medium"):
        """
        Create and add a custom pattern from example strings.
        
        Args:
            entity_type: The entity type name (e.g., "CUSTOMER_ID")
            examples: List of example strings that match this pattern
            context: Optional list of context words often found near this entity
            name: Optional friendly name for this pattern
            generalization_level: Level of pattern generalization (none, low, medium, high)
            
        Returns:
            The created pattern definition
        """
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
        self.add_pattern(pattern)
        
        return pattern
        
    def load_patterns(self, filepath):
        """
        Load patterns from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Number of patterns loaded
        """
        count = self.pattern_registry.load_patterns(filepath)
        
        # Add loaded patterns to analyzer
        for pattern in self.pattern_registry.get_patterns():
            self.analyzer.add_pattern(pattern)
            
        return count
        
    def import_patterns_from_csv(self, csv_path, pattern_filepath=None, entity_type_col='entity_type',
                              pattern_col='pattern', context_col='context', 
                              name_col='name', score_col='score'):
        """
        Import pattern definitions from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
            pattern_filepath: Optional path to save imported patterns
            entity_type_col: Column name for entity types
            pattern_col: Column name for regex patterns
            context_col: Column name for context words (comma-separated)
            name_col: Column name for pattern names
            score_col: Column name for confidence scores
            
        Returns:
            Number of patterns imported
        """
        from .utils.settings_manager import import_patterns_from_csv as import_patterns
        
        success, count, settings = import_patterns(
            csv_path, pattern_filepath, 
            entity_type_col, pattern_col, context_col, name_col, score_col
        )
        
        # Add patterns to analyzer
        if success and 'patterns' in settings:
            for pattern_def in settings['patterns']:
                self.add_pattern(pattern_def)
                
        return count
        
    def save_patterns(self, filepath):
        """
        Save all patterns to a JSON file.
        
        Args:
            filepath: Path to save the JSON file
            
        Returns:
            Path where patterns were saved
        """
        return self.pattern_registry.save_patterns(filepath)
    
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
        """
        # Update settings from current state to ensure they're up to date
        self.settings_manager.set_acronyms(
            self.text_preprocessor.acronym_dict,
            self.text_preprocessor.case_sensitive
        )
        
        return self.settings_manager.export_config(config_path, include_metadata)
    
    def create_dataframe_processor(self, n_workers=None, use_pyarrow=None):
        """
        Create a DataFrame processor for handling pandas DataFrames.
        
        Args:
            n_workers: Number of worker processes for parallel processing
            use_pyarrow: Whether to use PyArrow for performance optimization
            
        Returns:
            DataFrameProcessor instance
        """
        from .dataframe_processor import DataFrameProcessor
        
        # Use instance setting if not explicitly provided
        if use_pyarrow is None and hasattr(self, 'use_pyarrow'):
            use_pyarrow = self.use_pyarrow
            
        return DataFrameProcessor(self, n_workers=n_workers, use_pyarrow=use_pyarrow)
    
    def detect_pii_in_dataframe(self, df, column, **kwargs):
        """
        Detect PII in a DataFrame column.
        
        Args:
            df: Input DataFrame
            column: Column name containing text to analyze
            **kwargs: Additional arguments to pass to DataFrameProcessor.detect_pii
            
        Returns:
            DataFrame with detected entities
        """
        processor = self.create_dataframe_processor()
        return processor.detect_pii(df, column, **kwargs)
    
    def anonymize_dataframe(self, df, column, **kwargs):
        """
        Anonymize PII in a DataFrame column.
        
        Args:
            df: Input DataFrame
            column: Column name containing text to anonymize
            **kwargs: Additional arguments to pass to DataFrameProcessor.anonymize_column
            
        Returns:
            DataFrame with anonymized text
        """
        processor = self.create_dataframe_processor()
        return processor.anonymize_column(df, column, **kwargs)
    
    def process_dataframe(self, df, text_columns, **kwargs):
        """
        Process a DataFrame for comprehensive PII handling.
        
        Args:
            df: Input DataFrame
            text_columns: Column name(s) containing text to process
            **kwargs: Additional arguments to pass to DataFrameProcessor.process_dataframe
            
        Returns:
            Dict with processed DataFrame and entity DataFrame
        """
        processor = self.create_dataframe_processor()
        return processor.process_dataframe(df, text_columns, **kwargs)
        
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