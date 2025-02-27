"""
Direct test runner for package structure tests.
This bypasses pytest and runs the tests directly.
"""

import os
import sys
import re
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_version_consistency():
    """Test that version is consistent across files."""
    root_dir = Path(__file__).parent.parent
    version_pattern = r'(?:__version__|version)\s*=\s*[\'"]([^\'"]+)[\'"]'
    
    # Find all files that may contain version info
    files_to_check = [
        root_dir / "__init__.py",
        root_dir / "setup.py",
        root_dir / "pyproject.toml"
    ]
    
    versions = {}
    for file_path in files_to_check:
        if not file_path.exists():
            continue
            
        with open(file_path, "r") as f:
            content = f.read()
            
        match = re.search(version_pattern, content)
        if match:
            versions[file_path.name] = match.group(1)
    
    # Check that all found versions are the same
    if versions:
        first_version = next(iter(versions.values()))
        for filename, version in versions.items():
            assert version == first_version, f"Version mismatch in {filename}: {version} != {first_version}"
        print(f"✅ Version consistency test passed: All versions are {first_version}")
    else:
        print("⚠️ Version consistency test skipped: No version found in files")


def test_init_structure():
    """Test that the __init__.py file has the correct structure."""
    init_path = Path(__file__).parent.parent / "__init__.py"
    
    if not init_path.exists():
        print("⚠️ Init structure test skipped: __init__.py not found")
        return
    
    with open(init_path, "r") as f:
        content = f.read()
    
    # Check for version
    assert "__version__" in content, "Missing __version__ in __init__.py"
    
    # Check that factory functions are defined before imports
    factory_pos = content.find("def create_")
    import_pos = content.find("from .insurance")
    
    if factory_pos < 0:
        print("⚠️ Init structure test skipped: No factory functions found")
        return
        
    if import_pos < 0:
        print("⚠️ Init structure test skipped: No imports from .insurance found")
        return
        
    assert factory_pos < import_pos, "Factory functions should be defined before importing modules"
    print("✅ Init structure test passed: Factory functions are defined before importing modules")


def test_circular_imports():
    """Test for circular imports between modules."""
    # Look for specific patterns that might indicate circular imports
    root_dir = Path(__file__).parent.parent
    
    # Specific test for the circular import we fixed
    claim_notes_path = root_dir / "insurance" / "claim_notes_analyzer.py"
    if not claim_notes_path.exists():
        print("⚠️ Circular import test skipped: claim_notes_analyzer.py not found")
        return
        
    with open(claim_notes_path, "r") as f:
        content = f.read()
        
    # Check that claim_notes_analyzer.py doesn't import from parent module
    if "from allyanonimiser import create_au_insurance_analyzer" in content:
        assert False, "Circular import detected: claim_notes_analyzer.py imports from parent module"
    
    # Check for alternate import patterns that might cause issues
    if "import allyanonimiser" in content and "create_au_insurance_analyzer" in content:
        assert False, "Potential circular import: claim_notes_analyzer.py may use parent module"
        
    print("✅ Circular import test passed: No circular imports detected")


def run_all_tests():
    """Run all tests."""
    print("Running package structure tests...")
    try:
        test_version_consistency()
    except Exception as e:
        print(f"❌ Version consistency test failed: {str(e)}")
    
    try:
        test_init_structure()
    except Exception as e:
        print(f"❌ Init structure test failed: {str(e)}")
        
    try:
        test_circular_imports()
    except Exception as e:
        print(f"❌ Circular import test failed: {str(e)}")
    
    print("Package structure tests complete.")


if __name__ == "__main__":
    run_all_tests()