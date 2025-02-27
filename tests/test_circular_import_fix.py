"""
Tests specifically focused on validating that the circular import issue is fixed.
"""

import pytest
import importlib
import sys
import os

def test_clean_import():
    """Test that the package can be imported without circular import errors."""
    # First, make sure the module is not already imported
    if 'allyanonimiser' in sys.modules:
        del sys.modules['allyanonimiser']
    
    # Now try to import it
    import allyanonimiser
    
    # If we get here without an error, the import was successful
    assert True

def test_claim_notes_analyzer_import():
    """Test that the specific modules involved in the circular import can be imported cleanly."""
    # First, make sure the modules are not already imported
    for module in ['allyanonimiser', 'allyanonimiser.insurance', 'allyanonimiser.insurance.claim_notes_analyzer']:
        if module in sys.modules:
            del sys.modules[module]
    
    # Import the module that was part of the circular dependency
    from allyanonimiser.insurance import claim_notes_analyzer
    
    # Verify we can access the analyzer and function
    assert hasattr(claim_notes_analyzer, 'ClaimNotesAnalyzer')
    assert hasattr(claim_notes_analyzer, 'analyze_claim_note')

def test_factory_function_import_order():
    """Test that factory functions are defined before they are used in other imports."""
    # First, make sure the module is not already imported
    if 'allyanonimiser' in sys.modules:
        del sys.modules['allyanonimiser']
    
    # Import the module
    import allyanonimiser
    
    # Check that the key factory functions exist
    assert hasattr(allyanonimiser, 'create_au_analyzer')
    assert hasattr(allyanonimiser, 'create_au_insurance_analyzer')
    assert hasattr(allyanonimiser, 'create_allyanonimiser')
    
    # Now import the insurance module directly
    from allyanonimiser.insurance import claim_notes_analyzer
    
    # Create an instance of ClaimNotesAnalyzer to make sure it works
    analyzer = claim_notes_analyzer.ClaimNotesAnalyzer()
    
    # Make sure the instance is properly initialized
    assert analyzer is not None

def test_analyze_claim_note_function():
    """Test that the analyze_claim_note function works properly after the fix."""
    # This function was part of the circular import issue
    from allyanonimiser import analyze_claim_note
    
    # Test with a basic claim note
    result = analyze_claim_note("John Smith's policy POL123456 has a claim for vehicle damage.")
    
    # Verify we get a valid result
    assert isinstance(result, dict)
    assert "pii_entities" in result

if __name__ == "__main__":
    # Run the tests
    print("Running circular import fix tests...")
    test_clean_import()
    test_claim_notes_analyzer_import()
    test_factory_function_import_order()
    test_analyze_claim_note_function()
    print("All circular import fix tests passed!")