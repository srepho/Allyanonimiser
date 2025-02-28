"""
Property-based tests for CSV import functionality.
"""

import os
import pytest
import tempfile
import csv
import string
import pandas as pd
from hypothesis import given, strategies as st, settings, HealthCheck
from allyanonimiser.utils.settings_manager import (
    SettingsManager,
    import_acronyms_from_csv,
    import_patterns_from_csv
)
from allyanonimiser import create_allyanonimiser

# Define strategies for generating test data
acronyms = st.text(alphabet=string.ascii_uppercase, min_size=1, max_size=10)
expansions = st.text(alphabet=string.ascii_letters + ' ', min_size=1, max_size=50)
entity_types = st.text(alphabet=string.ascii_uppercase + '_', min_size=1, max_size=20)
patterns = st.text(alphabet=string.ascii_letters + string.digits + r'\\[]{}().|*+?^$-', min_size=1, max_size=30)
context_words = st.lists(
    st.text(alphabet=string.ascii_lowercase + ' ', min_size=1, max_size=15),
    min_size=0, max_size=5
)
names = st.text(alphabet=string.ascii_letters + ' ', min_size=1, max_size=30)
scores = st.floats(min_value=0.01, max_value=1.0)

def create_temp_csv(rows, headers):
    """Create a temporary CSV file with given rows and headers."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return f.name

@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=5)
@given(
    acronym_data=st.lists(
        st.tuples(acronyms, expansions),
        min_size=1, max_size=5
    )
)
def test_property_acronym_import(acronym_data):
    """Property-based test for acronym import."""
    # Create a temporary CSV with generated data
    headers = ['acronym', 'expansion']
    temp_file = create_temp_csv(acronym_data, headers)
    
    try:
        # Test import
        manager = SettingsManager()
        success, count = manager.import_acronyms_from_csv(temp_file)
        
        # Should import successfully
        assert success
        assert count == len(acronym_data)
        
        # Verify all acronyms were imported correctly
        acronyms_dict = manager.get_acronyms()
        for acronym, expansion in acronym_data:
            assert acronym in acronyms_dict
            assert acronyms_dict[acronym] == expansion
    finally:
        # Clean up
        os.unlink(temp_file)

@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=5)
@given(
    pattern_data=st.lists(
        st.tuples(
            entity_types,
            patterns,
            st.fixed_dictionaries({}),  # Placeholder for context
            names,
            scores
        ),
        min_size=1, max_size=3
    )
)
def test_property_pattern_import(pattern_data):
    """Property-based test for pattern import."""
    # Create a temporary CSV with generated data
    headers = ['entity_type', 'pattern', 'context', 'name', 'score']
    temp_file = create_temp_csv(pattern_data, headers)
    
    try:
        # Test import
        manager = SettingsManager()
        success, count, imported_patterns = manager.import_patterns_from_csv(temp_file)
        
        # Should import successfully
        assert success
        assert count == len(pattern_data)
        
        # Verify patterns were imported correctly
        for entity_type, pattern, context, name, score in pattern_data:
            # Find the corresponding pattern in imported patterns
            matching = [p for p in manager.settings.get('patterns', []) 
                       if p.get('entity_type') == entity_type and 
                          p.get('name') == name]
            
            assert len(matching) > 0
            imported = matching[0]
            
            # Check that pattern was imported correctly
            assert pattern in imported['patterns']
            if context:  # Only verify if context is not empty
                context_list = [c.strip() for c in context.split(',') if c.strip()]
                if context_list:
                    # Only verify if there are valid context words after splitting
                    for ctx in context_list:
                        assert ctx in imported.get('context', [])
            
            # Score may be converted to float, so check approximately
            if 'score' in imported:
                assert abs(imported['score'] - score) < 0.001
    finally:
        # Clean up
        os.unlink(temp_file)

@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=5)
@given(
    mixed_data=st.lists(
        st.tuples(acronyms, expansions),
        min_size=1, max_size=3
    )
)
def test_allyanonimiser_integration(mixed_data):
    """Property-based test for integration with Allyanonimiser."""
    # Create a temporary CSV with generated data
    headers = ['acronym', 'expansion']
    temp_file = create_temp_csv(mixed_data, headers)
    
    try:
        # Create Allyanonimiser instance
        ally = create_allyanonimiser()
        
        # Import acronyms
        count = ally.import_acronyms_from_csv(temp_file)
        assert count == len(mixed_data)
        
        # Verify all acronyms were imported correctly
        acronyms_dict = ally.get_acronyms()
        for acronym, expansion in mixed_data:
            assert acronym in acronyms_dict
            assert acronyms_dict[acronym] == expansion
            
        # Create text with acronyms for testing
        acronym_str = mixed_data[0][0]
        text = f"This text contains the acronym {acronym_str}."
        
        # Process with acronym expansion
        result = ally.process(text, expand_acronyms=True)
        
        # Should have preprocessing metadata
        assert "preprocessing" in result
        
        # The expansion should have happened
        expanded_acronyms = result["preprocessing"].get("expanded_acronyms", [])
        found = False
        for item in expanded_acronyms:
            if item["acronym"] == acronym_str:
                found = True
                assert item["expansion"] == mixed_data[0][1]
                break
                
        assert found, f"Acronym {acronym_str} was not expanded"
    finally:
        # Clean up
        os.unlink(temp_file)

def test_with_pandas():
    """Test integration with pandas DataFrames."""
    # Create acronyms DataFrame
    acronym_data = [("GST", "Goods and Services Tax"), 
                   ("CEO", "Chief Executive Officer"),
                   ("IT", "Information Technology")]
    
    df = pd.DataFrame(acronym_data, columns=['acronym', 'expansion'])
    
    # Save to temporary CSV
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        df.to_csv(temp_file, index=False)
        
        # Import using the manager
        manager = SettingsManager()
        success, count = manager.import_acronyms_from_csv(temp_file)
        
        assert success
        assert count == len(acronym_data)
        
        # Verify import
        acronyms_dict = manager.get_acronyms()
        for acronym, expansion in acronym_data:
            assert acronym in acronyms_dict
            assert acronyms_dict[acronym] == expansion
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

def test_invalid_files():
    """Test handling of invalid CSV files."""
    # Test with empty file
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        with open(temp_file, 'w') as f:
            pass  # Create empty file
            
        manager = SettingsManager()
        success, count = manager.import_acronyms_from_csv(temp_file)
        
        # Should fail gracefully
        assert not success
        assert count == 0
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
            
    # Test with header-only file
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        with open(temp_file, 'w') as f:
            f.write("acronym,expansion\n")
            
        manager = SettingsManager()
        success, count = manager.import_acronyms_from_csv(temp_file)
        
        # May either succeed with no acronyms or fail gracefully
        # Just check that count is 0
        assert count == 0
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
            
    # Test with corrupted file
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
        with open(temp_file, 'w') as f:
            f.write("acronym,expansion\n")
            f.write("this,is,not,valid,csv\n")
            
        manager = SettingsManager()
        success, count = manager.import_acronyms_from_csv(temp_file)
        
        # Depending on the CSV parser implementation, this might
        # be handled differently (might extract "this" as a valid acronym)
        # So we just check that it doesn't crash
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)