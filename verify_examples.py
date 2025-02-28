#!/usr/bin/env python
"""
Script to verify that our example scripts run without errors.
This is a standalone script that doesn't depend on the test infrastructure.
"""

import os
import sys
import importlib.util
import subprocess


def load_script(script_path):
    """Load a script as a module."""
    print(f"Loading script: {script_path}")
    script_name = os.path.basename(script_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[script_name] = module
    spec.loader.exec_module(module)
    return module


def run_example_functions(module, function_prefix="example_"):
    """Run all example functions in a module."""
    # Find all example functions
    example_functions = [name for name in dir(module) if name.startswith(function_prefix) and callable(getattr(module, name))]
    
    # Run each example function
    print(f"Found {len(example_functions)} example functions")
    for func_name in example_functions:
        print(f"Running {func_name}...")
        try:
            func = getattr(module, func_name)
            func()
            print(f"✅ {func_name} completed successfully")
        except Exception as e:
            print(f"❌ Error running {func_name}: {str(e)}")
            return False
    return True


def test_custom_patterns_examples():
    """Test that the custom patterns examples run without errors."""
    script_path = os.path.join(os.path.dirname(__file__), "example_custom_patterns.py")
    if not os.path.exists(script_path):
        print(f"Script {script_path} does not exist")
        return False
    
    # Import the script
    try:
        module = load_script(script_path)
        print("Successfully loaded the custom patterns example script")
        
        # Run individual examples
        return run_example_functions(module)
    except Exception as e:
        print(f"Failed to import or run {script_path}: {str(e)}")
        return False


def test_advanced_spacy_patterns_examples():
    """Test that the advanced spaCy patterns examples run without errors."""
    script_path = os.path.join(os.path.dirname(__file__), "example_advanced_spacy_patterns.py")
    if not os.path.exists(script_path):
        print(f"Script {script_path} does not exist")
        return False
    
    # Import the script
    try:
        module = load_script(script_path)
        print("Successfully loaded the advanced spaCy patterns example script")
        
        # Run individual examples
        return run_example_functions(module)
    except Exception as e:
        print(f"Failed to import or run {script_path}: {str(e)}")
        return False


def run_all_tests():
    """Run all tests."""
    results = {
        "custom_patterns": test_custom_patterns_examples(),
        "advanced_spacy_patterns": test_advanced_spacy_patterns_examples()
    }
    
    print("\n===== TEST RESULTS =====")
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        all_passed = all_passed and passed
    
    return all_passed


if __name__ == "__main__":
    print("Verifying example scripts...")
    success = run_all_tests()
    if success:
        print("\nAll examples verified successfully!")
        sys.exit(0)
    else:
        print("\nSome examples failed verification. See log for details.")
        sys.exit(1)