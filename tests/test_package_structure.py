"""
Tests for package structure and imports.
"""

import re
from pathlib import Path


def test_init_has_version():
    """Test that __init__.py defines __version__."""
    import allyanonimiser

    assert hasattr(allyanonimiser, "__version__")
    assert re.match(r"\d+\.\d+\.\d+", allyanonimiser.__version__)


def test_version_consistency():
    """Test that version is consistent between __init__.py and pyproject.toml."""
    import allyanonimiser

    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject.read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    assert match, "No version found in pyproject.toml"
    assert match.group(1) == allyanonimiser.__version__


def test_core_imports():
    """Test that core public API is importable."""
    from allyanonimiser import (
        Allyanonimiser,
        EnhancedAnalyzer,
        EnhancedAnonymizer,
        create_allyanonimiser,
        create_analyzer,
    )

    assert Allyanonimiser is not None
    assert EnhancedAnalyzer is not None
    assert EnhancedAnonymizer is not None
    assert callable(create_allyanonimiser)
    assert callable(create_analyzer)


def test_pattern_imports():
    """Test that pattern modules are importable."""
    from allyanonimiser.patterns.au_patterns import get_au_pattern_definitions
    from allyanonimiser.patterns.general_patterns import get_general_pattern_definitions
    from allyanonimiser.patterns.insurance_patterns import get_insurance_pattern_definitions

    assert len(get_au_pattern_definitions()) > 0
    assert len(get_insurance_pattern_definitions()) > 0
    assert len(get_general_pattern_definitions()) > 0


def test_stream_processor_import():
    """Test that stream processor can be imported from the main package."""
    from allyanonimiser import POLARS_AVAILABLE

    assert isinstance(POLARS_AVAILABLE, bool)

    if POLARS_AVAILABLE:
        from allyanonimiser import StreamProcessor

        assert StreamProcessor is not None
