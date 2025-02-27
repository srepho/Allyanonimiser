#!/usr/bin/env python
"""
Run functional tests for the Allyanonimiser package.

This script runs the functional tests without requiring pytest,
which is useful for checking that the package works correctly
even before all dependencies are installed.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path so we can import our test modules
parent_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def run_tests():
    """Run all functional tests."""
    print("Running Allyanonimiser functional tests...")
    
    # Create a test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test files
    test_files = [
        'test_circular_import_fix.py',
        'test_functional.py'
    ]
    
    # Current directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add tests from each file
    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        if not os.path.exists(test_path):
            print(f"Warning: Test file {test_file} not found, skipping")
            continue
            
        try:
            # Extract module name from file path
            module_name = os.path.splitext(os.path.basename(test_path))[0]
            # Import the module
            module = __import__(f"tests.{module_name}", fromlist=[''])
            # Add tests from this module
            suite.addTests(loader.loadTestsFromModule(module))
        except Exception as e:
            print(f"Error loading tests from {test_file}: {str(e)}")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if all tests passed, 1 otherwise
    return 0 if result.wasSuccessful() else 1


def run_single_test(test_file):
    """Run tests from a single file."""
    print(f"Running tests from {test_file}...")
    
    # Current directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(test_dir, test_file)
    
    if not os.path.exists(test_path):
        print(f"Error: Test file {test_file} not found")
        return 1
        
    try:
        # Extract module name from file path
        module_name = os.path.splitext(os.path.basename(test_path))[0]
        # Import the module
        module = __import__(f"tests.{module_name}", fromlist=[''])
        # Create a test suite with tests from this module
        suite = unittest.TestLoader().loadTestsFromModule(module)
        # Run the tests
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        # Return 0 if all tests passed, 1 otherwise
        return 0 if result.wasSuccessful() else 1
    except Exception as e:
        print(f"Error running tests from {test_file}: {str(e)}")
        return 1


if __name__ == "__main__":
    # If a test file is specified, run only that file
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        sys.exit(run_single_test(test_file))
    else:
        # Otherwise run all tests
        sys.exit(run_tests())