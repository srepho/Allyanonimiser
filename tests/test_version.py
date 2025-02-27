"""Tests to ensure version is consistent across the project."""

import configparser
import re
from pathlib import Path


def get_version_from_init():
    """Extract version from __init__.py file."""
    init_path = Path(__file__).parent.parent / "__init__.py"
    with open(init_path, "r") as f:
        content = f.read()
    
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    return None


def get_version_from_pyproject():
    """Extract version from pyproject.toml file."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    return None


def get_version_from_setup():
    """Extract version from setup.py file if it exists."""
    setup_path = Path(__file__).parent.parent / "setup.py"
    if not setup_path.exists():
        return None
        
    with open(setup_path, "r") as f:
        content = f.read()
    
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    return None


def test_version_consistency():
    """Test that version is consistent across all files."""
    init_version = get_version_from_init()
    pyproject_version = get_version_from_pyproject()
    setup_version = get_version_from_setup()
    
    versions = [v for v in [init_version, pyproject_version, setup_version] if v is not None]
    
    assert len(versions) >= 2, "Could not find version in at least two files"
    
    # Check all versions are the same
    for v in versions[1:]:
        assert v == versions[0], f"Version mismatch: {versions[0]} != {v}"
    
    # Verify version follows semantic versioning format
    assert re.match(r'^\d+\.\d+\.\d+', versions[0]), f"Version {versions[0]} does not follow semantic versioning"