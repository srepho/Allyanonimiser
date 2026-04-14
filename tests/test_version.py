"""Tests to ensure version is consistent across the project."""

import re
from pathlib import Path


def test_version_consistency():
    """Test that version is consistent between __init__.py and pyproject.toml."""
    root = Path(__file__).parent.parent

    # Get version from __init__.py
    init_path = root / "allyanonimiser" / "__init__.py"
    init_content = init_path.read_text()
    init_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
    assert init_match, "No version found in __init__.py"

    # Get version from pyproject.toml
    pyproject_path = root / "pyproject.toml"
    pyproject_content = pyproject_path.read_text()
    pyproject_match = re.search(r'version\s*=\s*"([^"]+)"', pyproject_content)
    assert pyproject_match, "No version found in pyproject.toml"

    assert init_match.group(1) == pyproject_match.group(1), (
        f"Version mismatch: __init__.py={init_match.group(1)}, "
        f"pyproject.toml={pyproject_match.group(1)}"
    )

    # Verify semantic versioning format
    assert re.match(r"^\d+\.\d+\.\d+$", init_match.group(1))
