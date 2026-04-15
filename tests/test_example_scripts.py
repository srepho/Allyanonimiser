"""
Smoke tests for the example scripts shipped at the repo root.

Each script is loaded and its ``main()`` (if present) is invoked under a
stdout capture, so broken imports or API drift fail CI immediately.
"""

import importlib.util
import io
import os
import sys
from unittest.mock import patch

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
EXAMPLE_SCRIPTS = [
    "example_csv_processing.py",
    "example_spacy_status.py",
]


def _load_script(script_path: str):
    """Load a script file as a module."""
    script_name = os.path.basename(script_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[script_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("script_name", EXAMPLE_SCRIPTS)
def test_example_script_imports(script_name):
    """Every example script should at least import cleanly."""
    script_path = os.path.join(REPO_ROOT, script_name)
    assert os.path.exists(script_path), f"{script_name} missing from repo root"
    _load_script(script_path)


@pytest.mark.slow
@pytest.mark.parametrize("script_name", EXAMPLE_SCRIPTS)
def test_example_script_main_runs(script_name):
    """If the script defines ``main``, it should run without raising.

    Marked ``slow`` because example ``main()`` functions do significant I/O
    (CSV creation, full-pipeline processing). Run explicitly with
    ``pytest -m slow`` to include them.
    """
    script_path = os.path.join(REPO_ROOT, script_name)
    module = _load_script(script_path)
    main = getattr(module, "main", None)
    if main is None:
        pytest.skip(f"{script_name} has no main() to invoke")

    with patch("sys.stdout", new_callable=io.StringIO) as captured:
        main()
    assert len(captured.getvalue()) > 0, "main() produced no output"
