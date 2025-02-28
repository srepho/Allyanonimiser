#!/usr/bin/env python
"""
Runner script for all tests. This can be used to run tests without having to install pytest.
"""

import os
import sys
import importlib

def run_module_tests(module_name):
    """Run all tests in a given module."""
    print(f"\nRunning tests in {module_name}...")
    try:
        module = importlib.import_module(module_name)
        # Find all functions that start with "test_"
        test_functions = [
            name for name in dir(module) 
            if name.startswith('test_') and callable(getattr(module, name))
        ]
        
        if not test_functions:
            print(f"No test functions found in {module_name}")
            return 0
        
        # Run each test function
        failed = 0
        for test_name in test_functions:
            test_func = getattr(module, test_name)
            try:
                print(f"  Running {test_name}...", end="")
                test_func()
                print(" ✓")
            except Exception as e:
                print(f" ✗ - {e}")
                failed += 1
        
        return failed
    except Exception as e:
        print(f"Failed to import module {module_name}: {e}")
        return 1

def main():
    """Run all tests in the tests directory."""
    # Add the parent directory to the path so we can import the modules
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Find all Python files in the tests directory that start with "test_"
    test_modules = []
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(tests_dir):
        if filename.startswith('test_') and filename.endswith('.py'):
            module_name = f"tests.{filename[:-3]}"  # Remove .py extension
            test_modules.append(module_name)
    
    if not test_modules:
        print("No test modules found")
        return 1
    
    print(f"Found {len(test_modules)} test modules")
    
    # Run all test modules
    failed = 0
    for module_name in test_modules:
        failed += run_module_tests(module_name)
    
    if failed:
        print(f"\n{failed} tests failed")
        return 1
    else:
        print("\nAll tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())