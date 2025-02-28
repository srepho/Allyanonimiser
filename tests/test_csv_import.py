"""
Tests for CSV import functionality.
"""

import os
import pytest
import tempfile
import json
import yaml
from allyanonimiser.utils.settings_manager import (
    SettingsManager,
    import_acronyms_from_csv,
    import_patterns_from_csv
)
from allyanonimiser import create_allyanonimiser

# Path to test data
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
TEST_PATTERNS_CSV = os.path.join(TEST_DATA_DIR, "test_patterns.csv")
TEST_ACRONYMS_CSV = os.path.join(TEST_DATA_DIR, "test_acronyms.csv")

def test_import_acronyms_from_csv():
    """Test importing acronyms from a CSV file."""
    manager = SettingsManager()
    
    # Test importing with default column names
    success, count = manager.import_acronyms_from_csv(TEST_ACRONYMS_CSV)
    assert success
    assert count > 0
    
    # Check that acronyms were imported correctly
    acronyms = manager.get_acronyms()
    assert "GST" in acronyms
    assert acronyms["GST"] == "Goods and Services Tax"
    assert "CEO" in acronyms
    assert acronyms["CEO"] == "Chief Executive Officer"
    
    # Test with custom column names
    manager = SettingsManager()
    success, count = manager.import_acronyms_from_csv(
        TEST_ACRONYMS_CSV,
        acronym_col="acronym",
        expansion_col="expansion"
    )
    assert success
    assert count > 0
    
    # Test case sensitivity setting
    manager = SettingsManager()
    success, count = manager.import_acronyms_from_csv(
        TEST_ACRONYMS_CSV,
        case_sensitive=True
    )
    assert success
    assert count > 0
    assert manager.get_acronym_case_sensitive()

def test_import_patterns_from_csv():
    """Test importing pattern definitions from a CSV file."""
    manager = SettingsManager()
    
    # Test importing with default column names
    success, count, patterns = manager.import_patterns_from_csv(TEST_PATTERNS_CSV)
    assert success
    assert count > 0
    
    # Check that patterns were imported to settings
    assert "patterns" in manager.settings
    assert len(manager.settings["patterns"]) == count
    
    # Check a specific pattern
    pattern = next((p for p in manager.settings["patterns"] if p["entity_type"] == "RESERVATION_NUMBER"), None)
    assert pattern is not None
    assert "patterns" in pattern
    assert "Hotel Reservation Pattern" in [p.get("name") for p in manager.settings["patterns"]]
    
    # Test with custom column names
    manager = SettingsManager()
    success, count, patterns = manager.import_patterns_from_csv(
        TEST_PATTERNS_CSV,
        entity_type_col="entity_type",
        pattern_col="pattern",
        context_col="context",
        name_col="name",
        score_col="score"
    )
    assert success
    assert count > 0
    
    # Test returned patterns list
    assert len(patterns) == count
    assert isinstance(patterns, list)

def test_save_imported_settings():
    """Test saving imported settings to files."""
    manager = SettingsManager()
    
    # Import both acronyms and patterns
    manager.import_acronyms_from_csv(TEST_ACRONYMS_CSV)
    manager.import_patterns_from_csv(TEST_PATTERNS_CSV)
    
    # Save to JSON file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        json_path = tmp.name
        
    try:
        success = manager.save_settings(json_path)
        assert success
        
        # Verify the saved JSON contains the imported data
        with open(json_path, "r") as f:
            saved_data = json.load(f)
            
        assert "acronyms" in saved_data
        assert "patterns" in saved_data
        assert len(saved_data["patterns"]) > 0
        assert "GST" in saved_data["acronyms"]["dictionary"]
    finally:
        if os.path.exists(json_path):
            os.unlink(json_path)
    
    # Save to YAML file
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        yaml_path = tmp.name
        
    try:
        success = manager.save_settings(yaml_path)
        assert success
        
        # Verify the saved YAML contains the imported data
        with open(yaml_path, "r") as f:
            saved_data = yaml.safe_load(f)
            
        assert "acronyms" in saved_data
        assert "patterns" in saved_data
    finally:
        if os.path.exists(yaml_path):
            os.unlink(yaml_path)

def test_module_level_functions():
    """Test the module-level functions for importing."""
    # Test importing acronyms
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        settings_path = tmp.name
    
    try:
        success, count, settings = import_acronyms_from_csv(
            TEST_ACRONYMS_CSV,
            settings_path
        )
        assert success
        assert count > 0
        assert "acronyms" in settings
        
        # Check file was saved
        assert os.path.exists(settings_path)
        with open(settings_path, "r") as f:
            saved_data = json.load(f)
            assert "acronyms" in saved_data
    finally:
        if os.path.exists(settings_path):
            os.unlink(settings_path)
    
    # Test importing patterns
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        settings_path = tmp.name
    
    try:
        success, count, settings = import_patterns_from_csv(
            TEST_PATTERNS_CSV,
            settings_path
        )
        assert success
        assert count > 0
        assert "patterns" in settings
        
        # Check file was saved
        assert os.path.exists(settings_path)
        with open(settings_path, "r") as f:
            saved_data = json.load(f)
            assert "patterns" in saved_data
    finally:
        if os.path.exists(settings_path):
            os.unlink(settings_path)

def test_integration_with_allyanonimiser():
    """Test importing CSV data with Allyanonimiser."""
    # Create instance
    ally = create_allyanonimiser()
    
    # Import acronyms
    count = ally.import_acronyms_from_csv(TEST_ACRONYMS_CSV)
    assert count > 0
    
    # Check the acronyms were added
    acronyms = ally.get_acronyms()
    assert "GST" in acronyms
    assert "CEO" in acronyms
    
    # Test acronym expansion in processing
    text = "The CEO approved the GST payment."
    result = ally.process(text, expand_acronyms=True)
    
    # Should contain expanded acronyms in preprocessing metadata
    assert "preprocessing" in result
    assert "expanded_acronyms" in result["preprocessing"]
    expansions = {item["acronym"] for item in result["preprocessing"]["expanded_acronyms"]}
    assert "CEO" in expansions
    assert "GST" in expansions
    
    # Import patterns
    count = ally.import_patterns_from_csv(TEST_PATTERNS_CSV)
    assert count > 0
    
    # The test continues here but we skip the pattern test for now
    # since it requires updating the analyzer's pattern registry
    # This will be tested in the integration tests

def test_error_handling():
    """Test error handling for CSV import."""
    manager = SettingsManager()
    
    # Test with non-existent file
    success, count = manager.import_acronyms_from_csv("non_existent_file.csv")
    assert not success
    assert count == 0
    
    # Test with invalid column names
    success, count = manager.import_acronyms_from_csv(
        TEST_ACRONYMS_CSV,
        acronym_col="non_existent_column",
        expansion_col="another_non_existent_column"
    )
    assert not success
    assert count == 0
    
    # Test pattern import with non-existent file
    success, count, patterns = manager.import_patterns_from_csv("non_existent_file.csv")
    assert not success
    assert count == 0
    assert len(patterns) == 0
    
    # Test pattern import with invalid column names
    success, count, patterns = manager.import_patterns_from_csv(
        TEST_PATTERNS_CSV,
        entity_type_col="non_existent_column"
    )
    assert not success
    assert count == 0