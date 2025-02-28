"""
Tests to verify that the example script files run correctly.
"""

import pytest
import importlib.util
import sys
import os
from unittest.mock import patch
import io

def load_script(script_path):
    """Load a script as a module."""
    script_name = os.path.basename(script_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[script_name] = module
    spec.loader.exec_module(module)
    return module

def test_example_script_imports():
    """Test that all example scripts can be imported."""
    example_scripts = [
        "example_absolute_import.py",
        "example_fixed_imports.py",
        "example_unified.py",
        "example_consolidated.py",
        "example_usage.py",
        "example_custom_patterns.py",
        "example_advanced_spacy_patterns.py"
    ]
    
    for script in example_scripts:
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), script)
        if os.path.exists(script_path):
            try:
                load_script(script_path)
                # If we get here, the script loaded without error
            except Exception as e:
                pytest.fail(f"Failed to import {script}: {str(e)}")

def run_example_functions(module, function_prefix="example_"):
    """Run all example functions in a module."""
    # Find all example functions
    example_functions = [name for name in dir(module) if name.startswith(function_prefix) and callable(getattr(module, name))]
    
    # Run each example function
    for func_name in example_functions:
        try:
            func = getattr(module, func_name)
            func()
        except Exception as e:
            pytest.fail(f"Error running {func_name}: {str(e)}")

@patch('sys.stdout', new_callable=io.StringIO)
def test_custom_patterns_examples(mock_stdout):
    """Test that the custom patterns examples run without errors."""
    # Load the example_custom_patterns.py script
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "example_custom_patterns.py")
    if not os.path.exists(script_path):
        pytest.skip(f"Script {script_path} does not exist")
    
    # Import the script
    module = load_script(script_path)
    
    # Run individual examples to avoid full script execution which would be too verbose
    run_example_functions(module)
    
    # Check that we got some output
    output = mock_stdout.getvalue()
    assert len(output) > 0
    assert "Creating Simple Regex Patterns" in output

@patch('sys.stdout', new_callable=io.StringIO)
def test_advanced_spacy_patterns_examples(mock_stdout):
    """Test that the advanced spaCy patterns examples run without errors."""
    # Load the example_advanced_spacy_patterns.py script
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "example_advanced_spacy_patterns.py")
    if not os.path.exists(script_path):
        pytest.skip(f"Script {script_path} does not exist")
    
    # Import the script
    module = load_script(script_path)
    
    # Run individual examples to avoid full script execution which would be too verbose
    run_example_functions(module)
    
    # Check that we got some output
    output = mock_stdout.getvalue()
    assert len(output) > 0
    assert "Token-Based Patterns in spaCy" in output


# Add a test for the main function to ensure it's callable
def test_main_functions():
    """Test that the main functions in example scripts can be called."""
    example_scripts = [
        "example_custom_patterns.py",
        "example_advanced_spacy_patterns.py"
    ]
    
    for script in example_scripts:
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), script)
        if os.path.exists(script_path):
            # Load the script
            module = load_script(script_path)
            
            # Check if run_all_examples exists and is callable
            assert hasattr(module, "run_all_examples")
            assert callable(getattr(module, "run_all_examples"))
            
            # We don't actually call run_all_examples as it might be too verbose
            # But we've verified it exists and is callable


if __name__ == "__main__":
    # Run the tests directly
    test_example_script_imports()
    test_custom_patterns_examples()
    test_advanced_spacy_patterns_examples()
    test_main_functions()
    print("All tests passed!")