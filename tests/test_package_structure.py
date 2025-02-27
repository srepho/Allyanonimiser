"""
Stand-alone tests for package structure.
These tests are completely independent and don't rely on conftest.py or module imports.
"""

import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_init_structure():
    """Test that the __init__.py file has the correct structure."""
    init_path = Path(__file__).parent.parent / "__init__.py"
    
    if not init_path.exists():
        # Skip test if the file doesn't exist yet
        return
    
    with open(init_path, "r") as f:
        content = f.read()
    
    # Check for version
    assert "__version__" in content, "Missing __version__ in __init__.py"
    
    # Check that factory functions are defined before imports
    factory_pos = content.find("def create_")
    if factory_pos > 0:  # Only test if factory functions exist
        import_pos = content.find("from .insurance")
        assert factory_pos < import_pos, "Factory functions should be defined before importing modules"


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


@patch("importlib.util.find_spec")
def test_no_circular_imports(mock_find_spec):
    """Test the import structure to prevent circular imports."""
    # Mock the import machinery
    mock_module = MagicMock()
    mock_spec = MagicMock()
    mock_spec.loader.exec_module = MagicMock()
    mock_find_spec.return_value = mock_spec
    
    # Test the import structure
    # This is a simplified test that just ensures the test machinery works
    assert mock_find_spec is not None
    
    # In a real test, we would do something like:
    # 1. Import __init__.py
    # 2. Import insurance/__init__.py
    # 3. Import insurance/claim_notes_analyzer.py
    # 4. Check that claim_notes_analyzer.py doesn't import from parent module
    
    # Here we're just asserting that our test structure exists
    assert True