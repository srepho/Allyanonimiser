"""
Tests for configuration export functionality.
"""

import os
import json
import tempfile
import pytest
from allyanonimiser import create_allyanonimiser
from allyanonimiser.utils.settings_manager import SettingsManager, export_config, create_default_settings

@pytest.fixture
def settings_manager_with_data():
    """Create a settings manager with test data."""
    manager = SettingsManager(settings=create_default_settings())
    
    # Add custom settings
    manager.set_acronyms({
        'PII': 'Personally Identifiable Information',
        'DOB': 'Date of Birth',
        'ABC': 'Australian Broadcasting Corporation'
    }, case_sensitive=True)
    
    manager.set_entity_types(['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER'])
    
    manager.set_anonymization_operators({
        'PERSON': 'replace',
        'EMAIL_ADDRESS': 'mask',
        'PHONE_NUMBER': 'mask'
    })
    
    manager.set_batch_size(2000)
    manager.set_worker_count(4)
    manager.set_value('processing.use_pyarrow', True)
    
    return manager

def test_settings_manager_export_config(settings_manager_with_data):
    """Test exporting config from the SettingsManager."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        temp_path = tmp.name
    
    try:
        # Export config with metadata
        success = settings_manager_with_data.export_config(temp_path, include_metadata=True)
        assert success, "Config export should succeed"
        
        # Read the exported file
        with open(temp_path, 'r') as f:
            config = json.load(f)
        
        # Check content
        assert 'version' in config
        assert 'description' in config
        assert 'entity_types' in config
        assert 'anonymization' in config
        assert 'processing' in config
        assert 'acronyms' in config
        assert 'metadata' in config
        
        # Check specific values
        assert config['processing']['batch_size'] == 2000
        assert config['processing']['worker_count'] == 4
        assert config['processing']['use_pyarrow'] is True
        
        # Check acronyms
        assert len(config['acronyms']['dictionary']) == 3
        assert config['acronyms']['case_sensitive'] is True
        assert 'PII' in config['acronyms']['dictionary']
        
        # Export without metadata
        success = settings_manager_with_data.export_config(temp_path, include_metadata=False)
        assert success, "Config export without metadata should succeed"
        
        # Read the exported file
        with open(temp_path, 'r') as f:
            config = json.load(f)
        
        # Metadata should not be present
        assert 'metadata' not in config
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_allyanonimiser_export_config():
    """Test exporting config from the Allyanonimiser class."""
    # Create an instance
    ally = create_allyanonimiser()
    
    # Configure some settings
    ally.set_acronym_dictionary({
        'PII': 'Personally Identifiable Information',
        'DOB': 'Date of Birth'
    })
    
    ally.settings_manager.set_entity_types(['PERSON', 'EMAIL_ADDRESS'])
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        temp_path = tmp.name
    
    try:
        # Export config
        success = ally.export_config(temp_path)
        assert success, "Config export should succeed"
        
        # Read the exported file
        with open(temp_path, 'r') as f:
            config = json.load(f)
        
        # Check content
        assert 'acronyms' in config
        assert 'PII' in config['acronyms']['dictionary']
        assert 'entity_types' in config
        assert 'PERSON' in config['entity_types']['active']
        
        # Create a new instance with exported config
        new_ally = create_allyanonimiser(settings_path=temp_path)
        
        # Check that settings were loaded correctly
        acronyms = new_ally.get_acronyms()
        entity_types = new_ally.settings_manager.get_entity_types()
        
        assert 'PII' in acronyms
        assert 'PERSON' in entity_types
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_export_config_yaml_format():
    """Test exporting config in YAML format."""
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed, skipping YAML test")
    
    ally = create_allyanonimiser()
    ally.set_acronym_dictionary({'PII': 'Personally Identifiable Information'})
    
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        temp_path = tmp.name
    
    try:
        # Export config in YAML format
        success = ally.export_config(temp_path)
        assert success, "YAML config export should succeed"
        
        # Read the exported file
        with open(temp_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check content
        assert 'acronyms' in config
        assert 'dictionary' in config['acronyms']
        assert 'PII' in config['acronyms']['dictionary']
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)