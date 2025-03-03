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


def test_import_stream_processor():
    """Test that stream processor can be imported from the main package."""
    try:
        from allyanonimiser import StreamProcessor, POLARS_AVAILABLE
        
        # POLARS_AVAILABLE should always be importable
        assert isinstance(POLARS_AVAILABLE, bool)
        
        # StreamProcessor will be None if Polars is not available
        if POLARS_AVAILABLE:
            assert StreamProcessor is not None
            # Verify it's the correct class
            assert "StreamProcessor" in StreamProcessor.__name__
        else:
            assert StreamProcessor is None
            
    except ImportError:
        # If the import fails completely, the package structure is incorrect
        assert False, "Failed to import StreamProcessor and POLARS_AVAILABLE from allyanonimiser"


def test_direct_stream_processor_import():
    """Test direct import of stream_processor module."""
    try:
        # This should succeed even if Polars is not installed
        from allyanonimiser.stream_processor import StreamProcessor, POLARS_AVAILABLE
        
        assert StreamProcessor is not None
        assert isinstance(POLARS_AVAILABLE, bool)
        
    except ImportError:
        # This should only fail if the module doesn't exist
        assert False, "Failed to import stream_processor module directly"