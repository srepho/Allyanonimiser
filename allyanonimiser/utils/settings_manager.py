"""
Settings manager for Allyanonimiser.

Allows loading, saving, and managing configuration settings.
"""

import os
import json
import csv
import yaml
from typing import Dict, Any, Optional, List, Union, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SettingsManager:
    """
    Manages configuration settings for Allyanonimiser.
    
    Supports loading and saving settings from JSON or YAML files,
    and provides access to different configuration sections.
    """
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None, settings_path: Optional[str] = None):
        """
        Initialize the settings manager.
        
        Args:
            settings: Optional dictionary with settings
            settings_path: Optional path to a settings file (JSON or YAML)
        """
        self.settings = settings or {}
        
        if settings_path:
            self.load_settings(settings_path)
            
    def load_settings(self, settings_path: str) -> bool:
        """
        Load settings from a file.
        
        Args:
            settings_path: Path to a settings file (JSON or YAML)
            
        Returns:
            Boolean indicating success
        """
        if not os.path.exists(settings_path):
            logger.error(f"Settings file not found: {settings_path}")
            return False
            
        try:
            file_ext = os.path.splitext(settings_path)[1].lower()
            
            if file_ext == '.json':
                with open(settings_path, 'r', encoding='utf-8') as f:
                    new_settings = json.load(f)
            elif file_ext in ['.yaml', '.yml']:
                try:
                    import yaml
                except ImportError:
                    logger.error("YAML support requires PyYAML. Install with: pip install pyyaml")
                    return False
                    
                with open(settings_path, 'r', encoding='utf-8') as f:
                    new_settings = yaml.safe_load(f)
            else:
                logger.error(f"Unsupported settings file format: {file_ext}")
                return False
                
            # Update settings
            self.settings.update(new_settings)
            logger.info(f"Settings loaded from {settings_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading settings from {settings_path}: {str(e)}")
            return False
            
    def save_settings(self, settings_path: str, sections: Optional[List[str]] = None) -> bool:
        """
        Save settings to a file.
        
        Args:
            settings_path: Path to save the settings file
            sections: Optional list of sections to save (saves all if None)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(settings_path)), exist_ok=True)
            
            # Filter settings if sections specified
            settings_to_save = {}
            if sections:
                for section in sections:
                    if section in self.settings:
                        settings_to_save[section] = self.settings[section]
            else:
                settings_to_save = self.settings
                
            # Save based on file extension
            file_ext = os.path.splitext(settings_path)[1].lower()
            
            if file_ext == '.json':
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_to_save, f, indent=2)
            elif file_ext in ['.yaml', '.yml']:
                try:
                    import yaml
                except ImportError:
                    logger.error("YAML support requires PyYAML. Install with: pip install pyyaml")
                    return False
                    
                with open(settings_path, 'w', encoding='utf-8') as f:
                    yaml.dump(settings_to_save, f, default_flow_style=False)
            else:
                logger.error(f"Unsupported settings file format: {file_ext}")
                return False
                
            logger.info(f"Settings saved to {settings_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings to {settings_path}: {str(e)}")
            return False

    def import_acronyms_from_csv(self, csv_path: str, acronym_col: str = 'acronym', 
                                expansion_col: str = 'expansion', 
                                case_sensitive: bool = False) -> Tuple[bool, int]:
        """
        Import acronyms from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
            acronym_col: Column name for acronyms
            expansion_col: Column name for expansions
            case_sensitive: Whether acronym matching should be case-sensitive
            
        Returns:
            Tuple of (success_bool, number_of_acronyms_imported)
        """
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False, 0
            
        try:
            acronyms = {}
            count = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if acronym_col not in reader.fieldnames or expansion_col not in reader.fieldnames:
                    logger.error(f"Required columns not found: {acronym_col}, {expansion_col}")
                    return False, 0
                    
                for row in reader:
                    acronym = row[acronym_col].strip()
                    expansion = row[expansion_col].strip()
                    
                    if acronym and expansion:
                        acronyms[acronym] = expansion
                        count += 1
            
            if count > 0:
                # Add to existing acronyms or create new dictionary
                if 'acronyms' in self.settings and 'dictionary' in self.settings['acronyms']:
                    self.settings['acronyms']['dictionary'].update(acronyms)
                else:
                    self.settings.setdefault('acronyms', {})
                    self.settings['acronyms']['dictionary'] = acronyms
                    
                self.settings['acronyms']['case_sensitive'] = case_sensitive
                logger.info(f"Imported {count} acronyms from {csv_path}")
                return True, count
            else:
                logger.warning(f"No valid acronyms found in {csv_path}")
                return False, 0
                
        except Exception as e:
            logger.error(f"Error importing acronyms from {csv_path}: {str(e)}")
            return False, 0

    def import_patterns_from_csv(self, csv_path: str, entity_type_col: str = 'entity_type',
                                pattern_col: str = 'pattern', context_col: str = 'context',
                                name_col: str = 'name', score_col: str = 'score') -> Tuple[bool, int, List[Dict[str, Any]]]:
        """
        Import pattern definitions from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
            entity_type_col: Column name for entity types
            pattern_col: Column name for regex patterns
            context_col: Column name for context words (comma-separated)
            name_col: Column name for pattern names
            score_col: Column name for confidence scores
            
        Returns:
            Tuple of (success_bool, number_of_patterns_imported, list_of_pattern_dicts)
        """
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False, 0, []
            
        try:
            patterns = []
            count = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                required_cols = [entity_type_col, pattern_col]
                
                for col in required_cols:
                    if col not in reader.fieldnames:
                        logger.error(f"Required column not found: {col}")
                        return False, 0, []
                
                for row in reader:
                    entity_type = row[entity_type_col].strip()
                    pattern = row[pattern_col].strip()
                    
                    if not entity_type or not pattern:
                        continue
                        
                    pattern_def = {
                        'entity_type': entity_type,
                        'patterns': [pattern],
                        'language': 'en'
                    }
                    
                    # Add optional fields if present
                    if context_col in row and row[context_col]:
                        context_words = [word.strip() for word in row[context_col].split(',')]
                        pattern_def['context'] = [word for word in context_words if word]
                        
                    if name_col in row and row[name_col]:
                        pattern_def['name'] = row[name_col].strip()
                        
                    if score_col in row and row[score_col]:
                        try:
                            pattern_def['score'] = float(row[score_col])
                        except ValueError:
                            pattern_def['score'] = 0.85  # Default score
                    else:
                        pattern_def['score'] = 0.85  # Default score
                    
                    patterns.append(pattern_def)
                    count += 1
            
            if count > 0:
                # Add patterns to settings
                self.settings.setdefault('patterns', [])
                self.settings['patterns'].extend(patterns)
                logger.info(f"Imported {count} patterns from {csv_path}")
                return True, count, patterns
            else:
                logger.warning(f"No valid patterns found in {csv_path}")
                return False, 0, []
                
        except Exception as e:
            logger.error(f"Error importing patterns from {csv_path}: {str(e)}")
            return False, 0, []
            
    def get_section(self, section: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a section of settings.
        
        Args:
            section: Section name
            default: Default value if section doesn't exist
            
        Returns:
            Dictionary with section settings
        """
        if default is None:
            default = {}
            
        return self.settings.get(section, default)
        
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get a specific setting value using dot notation.
        
        Args:
            path: Setting path (e.g., "acronyms.case_sensitive")
            default: Default value if setting doesn't exist
            
        Returns:
            Setting value or default
        """
        keys = path.split('.')
        value = self.settings
        
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]
            
        return value
        
    def set_value(self, path: str, value: Any) -> None:
        """
        Set a specific setting value using dot notation.
        
        Args:
            path: Setting path (e.g., "acronyms.case_sensitive")
            value: Value to set
        """
        keys = path.split('.')
        setting = self.settings
        
        # Navigate to the last dict in the path
        for key in keys[:-1]:
            if key not in setting:
                setting[key] = {}
            elif not isinstance(setting[key], dict):
                setting[key] = {}
            setting = setting[key]
            
        # Set the value
        setting[keys[-1]] = value
        
    def set_section(self, section: str, values: Dict[str, Any]) -> None:
        """
        Set an entire section of settings.
        
        Args:
            section: Section name
            values: Dictionary with section settings
        """
        self.settings[section] = values
        
    def get_acronyms(self) -> Dict[str, str]:
        """
        Get the acronym dictionary from settings.
        
        Returns:
            Dictionary mapping acronyms to their expanded forms
        """
        return self.get_section('acronyms', {}).get('dictionary', {})
        
    def get_acronym_case_sensitive(self) -> bool:
        """
        Get whether acronym matching should be case-sensitive.
        
        Returns:
            Boolean indicating case sensitivity
        """
        return self.get_section('acronyms', {}).get('case_sensitive', False)
        
    def set_acronyms(self, acronyms: Dict[str, str], case_sensitive: bool = False) -> None:
        """
        Set the acronym dictionary in settings.
        
        Args:
            acronyms: Dictionary mapping acronyms to their expanded forms
            case_sensitive: Whether acronym matching should be case-sensitive
        """
        self.settings.setdefault('acronyms', {})
        self.settings['acronyms']['dictionary'] = acronyms
        self.settings['acronyms']['case_sensitive'] = case_sensitive
        
    def add_acronyms(self, acronyms: Dict[str, str]) -> None:
        """
        Add acronyms to the existing dictionary in settings.
        
        Args:
            acronyms: Dictionary mapping acronyms to their expanded forms
        """
        current = self.get_acronyms()
        current.update(acronyms)
        self.set_value('acronyms.dictionary', current)
        
    def remove_acronyms(self, acronyms: List[str]) -> None:
        """
        Remove acronyms from the dictionary in settings.
        
        Args:
            acronyms: List of acronym keys to remove
        """
        current = self.get_acronyms()
        for acronym in acronyms:
            if acronym in current:
                del current[acronym]
        self.set_value('acronyms.dictionary', current)
        
    def get_entity_types(self) -> List[str]:
        """
        Get the list of active entity types from settings.
        
        Returns:
            List of entity type strings
        """
        return self.get_section('entity_types', {}).get('active', [])
        
    def set_entity_types(self, entity_types: List[str]) -> None:
        """
        Set the list of active entity types in settings.
        
        Args:
            entity_types: List of entity type strings
        """
        self.settings.setdefault('entity_types', {})
        self.settings['entity_types']['active'] = entity_types
        
    def get_anonymization_operators(self) -> Dict[str, str]:
        """
        Get the anonymization operators from settings.
        
        Returns:
            Dictionary mapping entity types to anonymization operators
        """
        return self.get_section('anonymization', {}).get('operators', {})
        
    def set_anonymization_operators(self, operators: Dict[str, str]) -> None:
        """
        Set the anonymization operators in settings.
        
        Args:
            operators: Dictionary mapping entity types to anonymization operators
        """
        self.settings.setdefault('anonymization', {})
        self.settings['anonymization']['operators'] = operators
        
    def get_batch_size(self) -> int:
        """
        Get the batch size for processing from settings.
        
        Returns:
            Batch size (default: 1000)
        """
        return self.get_section('processing', {}).get('batch_size', 1000)
        
    def set_batch_size(self, batch_size: int) -> None:
        """
        Set the batch size for processing in settings.
        
        Args:
            batch_size: Batch size for processing
        """
        self.settings.setdefault('processing', {})
        self.settings['processing']['batch_size'] = batch_size
        
    def get_worker_count(self) -> Optional[int]:
        """
        Get the worker count for parallel processing from settings.
        
        Returns:
            Worker count or None for sequential processing
        """
        return self.get_section('processing', {}).get('worker_count', None)
        
    def set_worker_count(self, worker_count: Optional[int]) -> None:
        """
        Set the worker count for parallel processing in settings.
        
        Args:
            worker_count: Worker count for parallel processing
        """
        self.settings.setdefault('processing', {})
        self.settings['processing']['worker_count'] = worker_count
        
    def export_config(self, config_path: str, include_metadata: bool = True) -> bool:
        """
        Export a shareable configuration file based on the current settings.
        
        This creates a simplified configuration file that includes only the essential
        settings needed to reproduce the current functionality, with optional comments 
        explaining each setting.
        
        Args:
            config_path: Path to save the configuration file (supports .json, .yaml, .yml)
            include_metadata: Whether to include descriptive comments in the output
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create a simplified version of the settings
            config = {
                'version': self.settings.get('version', '1.0.0'),
                'description': 'Allyanonimiser configuration file for sharing'
            }
            
            # Include active entity types if specified
            entity_types = self.get_entity_types()
            if entity_types:
                config['entity_types'] = {'active': entity_types}
                
            # Include anonymization operators if present
            operators = self.get_anonymization_operators()
            if operators:
                config['anonymization'] = {'operators': operators}
                
            # Include processing settings
            config['processing'] = {
                'batch_size': self.get_batch_size(),
                'worker_count': self.get_worker_count(),
                'expand_acronyms': self.get_value('processing.expand_acronyms', True),
                'use_pyarrow': self.get_value('processing.use_pyarrow', True)
            }
            
            # Include acronyms if present (but limit to 10 examples in metadata)
            acronyms = self.get_acronyms()
            if acronyms:
                config['acronyms'] = {
                    'case_sensitive': self.get_acronym_case_sensitive(),
                    'dictionary': acronyms
                }
                
                if include_metadata:
                    acronym_count = len(acronyms)
                    acronym_examples = list(acronyms.items())[:10]
                    config['metadata'] = config.get('metadata', {})
                    config['metadata']['acronyms'] = {
                        'count': acronym_count,
                        'examples': dict(acronym_examples) if acronym_count > 0 else {}
                    }
            
            # Include patterns count if present
            patterns = self.settings.get('patterns', [])
            if patterns and include_metadata:
                config['metadata'] = config.get('metadata', {})
                config['metadata']['patterns'] = {
                    'count': len(patterns),
                    'types': list(set(p['entity_type'] for p in patterns if 'entity_type' in p))
                }
            
            # Save based on file extension
            file_ext = os.path.splitext(config_path)[1].lower()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            if file_ext == '.json':
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
            elif file_ext in ['.yaml', '.yml']:
                try:
                    import yaml
                except ImportError:
                    logger.error("YAML support requires PyYAML. Install with: pip install pyyaml")
                    return False
                    
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False)
            else:
                logger.error(f"Unsupported config file format: {file_ext}")
                return False
                
            logger.info(f"Configuration exported to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configuration to {config_path}: {str(e)}")
            return False


def load_settings(settings_path: str) -> Dict[str, Any]:
    """
    Load settings from a file.
    
    Args:
        settings_path: Path to a settings file (JSON or YAML)
        
    Returns:
        Dictionary with settings
    """
    manager = SettingsManager()
    if manager.load_settings(settings_path):
        return manager.settings
    return {}
    
    
def save_settings(settings_path: str, settings: Dict[str, Any]) -> bool:
    """
    Save settings to a file.
    
    Args:
        settings_path: Path to save the settings file
        settings: Dictionary with settings
        
    Returns:
        Boolean indicating success
    """
    manager = SettingsManager(settings)
    return manager.save_settings(settings_path)


def import_acronyms_from_csv(csv_path: str, settings_path: str = None, 
                            acronym_col: str = 'acronym', expansion_col: str = 'expansion',
                            case_sensitive: bool = False) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Import acronyms from a CSV file and save to settings.
    
    Args:
        csv_path: Path to the CSV file
        settings_path: Optional path to save the settings file
        acronym_col: Column name for acronyms
        expansion_col: Column name for expansions
        case_sensitive: Whether acronym matching should be case-sensitive
        
    Returns:
        Tuple of (success_bool, number_of_acronyms_imported, settings_dict)
    """
    manager = SettingsManager()
    success, count = manager.import_acronyms_from_csv(
        csv_path, acronym_col, expansion_col, case_sensitive
    )
    
    if success and settings_path:
        manager.save_settings(settings_path)
        
    return success, count, manager.settings


def import_patterns_from_csv(csv_path: str, settings_path: str = None,
                            entity_type_col: str = 'entity_type',
                            pattern_col: str = 'pattern', 
                            context_col: str = 'context',
                            name_col: str = 'name', 
                            score_col: str = 'score') -> Tuple[bool, int, Dict[str, Any]]:
    """
    Import pattern definitions from a CSV file and save to settings.
    
    Args:
        csv_path: Path to the CSV file
        settings_path: Optional path to save the settings file
        entity_type_col: Column name for entity types
        pattern_col: Column name for regex patterns
        context_col: Column name for context words (comma-separated)
        name_col: Column name for pattern names
        score_col: Column name for confidence scores
        
    Returns:
        Tuple of (success_bool, number_of_patterns_imported, settings_dict)
    """
    manager = SettingsManager()
    success, count, patterns = manager.import_patterns_from_csv(
        csv_path, entity_type_col, pattern_col, context_col, name_col, score_col
    )
    
    if success and settings_path:
        manager.save_settings(settings_path)
        
    return success, count, manager.settings
    
    
def export_config(settings: Dict[str, Any], config_path: str, include_metadata: bool = True) -> bool:
    """
    Export a shareable configuration file based on provided settings.
    
    Args:
        settings: Dictionary with settings
        config_path: Path to save the configuration file
        include_metadata: Whether to include descriptive metadata in the output
        
    Returns:
        Boolean indicating success
    """
    manager = SettingsManager(settings)
    return manager.export_config(config_path, include_metadata)


def create_default_settings() -> Dict[str, Any]:
    """
    Create default settings.
    
    Returns:
        Dictionary with default settings
    """
    return {
        'acronyms': {
            'dictionary': {
                'TP': 'Third Party',
                'TL': 'Team Leader',
                'PII': 'Personally Identifiable Information',
                'POL': 'Policy',
                'CL': 'Claim',
                'DOB': 'Date of Birth',
                'MVA': 'Motor Vehicle Accident'
            },
            'case_sensitive': False
        },
        'entity_types': {
            'active': [],  # Empty means all types are active
            'score_adjustment': {
                'PERSON': 0.1,
                'EMAIL_ADDRESS': 0.1
            }
        },
        'anonymization': {
            'operators': {
                'PERSON': 'replace',
                'EMAIL_ADDRESS': 'mask',
                'PHONE_NUMBER': 'mask',
                'INSURANCE_POLICY_NUMBER': 'redact',
                'INSURANCE_CLAIM_NUMBER': 'redact',
                'AU_MEDICARE': 'redact',
                'AU_TFN': 'redact',
                'AU_ABN': 'redact',
                'ADDRESS': 'replace',
                'DATE': 'replace'
            }
        },
        'processing': {
            'batch_size': 1000,
            'worker_count': None,  # None means sequential processing
            'expand_acronyms': True,
            'use_pyarrow': True   # Use PyArrow for DataFrame optimization if available
        }
    }