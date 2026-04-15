#!/usr/bin/env python3
"""Pre-release smoke test for an Allyanonimiser sdist.

Catches the classes of release bugs that have shipped before:

1. **API regressions in the public surface** (e.g. v3.1.1's silent
   ``DataFrameProcessor.process_dataframe(expand_acronyms=...)`` no-op).
2. **Missing data files in the sdist** (e.g. v3.1.1's stripped
   ``tests/test_data/*.csv``, which left ``test_csv_import.py`` un-runnable
   from a PyPI install).
3. **Stale generated metadata** (verifies the installed version matches
   what pyproject.toml declares).

Usage
-----
::

    # Validate the dist you just built:
    python scripts/smoke_release.py

    # Or point at a specific sdist:
    python scripts/smoke_release.py path/to/allyanonimiser-X.Y.Z.tar.gz

The script creates a throwaway venv under ``/tmp``, installs the sdist into
it, and runs the assertions inside that venv. The host environment is not
modified.

Exits non-zero on any failure.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_sdist(explicit: str | None) -> Path:
    """Locate the sdist to test. Prefer the explicit arg, else newest in dist/."""
    if explicit:
        path = Path(explicit)
        if not path.exists():
            sys.exit(f"sdist not found: {explicit}")
        return path

    dist_dir = REPO_ROOT / "dist"
    if not dist_dir.exists():
        sys.exit(f"no dist/ directory at {dist_dir} — run `python -m build` first")

    candidates = sorted(dist_dir.glob("allyanonimiser-*.tar.gz"))
    if not candidates:
        sys.exit(f"no allyanonimiser sdist in {dist_dir} — run `python -m build` first")
    return candidates[-1]


def expected_version() -> str:
    """Read the version declared in pyproject.toml."""
    text = (REPO_ROOT / "pyproject.toml").read_text()
    for line in text.splitlines():
        if line.strip().startswith("version") and "=" in line:
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("could not parse version from pyproject.toml")


def assert_sdist_contains(sdist: Path, required: list[str]) -> None:
    """Fail if any required path is missing from the sdist."""
    with tarfile.open(sdist, "r:gz") as tar:
        names = set(tar.getnames())
    # Strip the top-level dir (e.g. allyanonimiser-3.1.2/) for matching.
    stripped = {n.split("/", 1)[1] for n in names if "/" in n}
    missing = [r for r in required if r not in stripped]
    if missing:
        sys.exit(
            "sdist is missing required files:\n  - "
            + "\n  - ".join(missing)
            + f"\n(check MANIFEST.in; sdist contained {len(stripped)} entries)"
        )


def run_in_venv(venv_python: Path, code: str) -> str:
    """Execute ``code`` in the venv's interpreter; return stdout, raise on failure."""
    result = subprocess.run(
        [str(venv_python), "-c", code],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(
            f"in-venv check failed (exit {result.returncode}):\n"
            f"--- code ---\n{code}\n"
            f"--- stdout ---\n{result.stdout}"
            f"--- stderr ---\n{result.stderr}"
        )
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdist", nargs="?", help="Path to the sdist (defaults to newest in dist/)")
    parser.add_argument("--keep-venv", action="store_true",
                        help="Leave the throwaway venv in place for inspection")
    args = parser.parse_args()

    sdist = find_sdist(args.sdist)
    version = expected_version()

    print(f"==> sdist:   {sdist}")
    print(f"==> version: {version}")

    # 1. Filename matches declared version.
    if version not in sdist.name:
        sys.exit(f"sdist filename {sdist.name} does not contain expected version {version}")

    # 2. Required files are inside the sdist.
    assert_sdist_contains(sdist, [
        "PKG-INFO",
        "README.md",
        "LICENSE",
        "pyproject.toml",
        "allyanonimiser/__init__.py",
        "allyanonimiser/io/dataframe_processor.py",
        "allyanonimiser/core/analyzer.py",
        "tests/test_data/test_acronyms.csv",
        "tests/test_data/test_patterns.csv",
    ])
    print("==> sdist contents: OK")

    # 3. Install into a fresh venv and exercise the public API.
    tmp = Path(tempfile.mkdtemp(prefix="ally-smoke-"))
    print(f"==> scratch venv: {tmp}")
    try:
        # Use uv if available (much faster); fall back to stdlib venv + pip.
        uv = shutil.which("uv")
        if uv:
            subprocess.run([uv, "venv", str(tmp / ".venv"), "--quiet"], check=True)
            venv_python = tmp / ".venv" / "bin" / "python"
            subprocess.run(
                [uv, "pip", "install", "--quiet", "--python", str(venv_python), str(sdist)],
                check=True,
            )
        else:
            subprocess.run([sys.executable, "-m", "venv", str(tmp / ".venv")], check=True)
            venv_python = tmp / ".venv" / "bin" / "python"
            subprocess.run([str(venv_python), "-m", "pip", "install", "--quiet", str(sdist)],
                           check=True)

        # Install the default spaCy model into the scratch venv directly
        # via the release wheel URL. We can't use `python -m spacy download`
        # here because spaCy's downloader shells out to pip, and when the
        # scratch venv was created by uv, uv's pip wrapper "audits" the
        # already-cached package without copying it into the venv's
        # site-packages — so the import then fails. The wheel URL is
        # stable per spaCy 3.8.x; bump SPACY_MODEL_WHEEL_URL when
        # upgrading the spaCy minor pin in pyproject.toml.
        SPACY_MODEL_WHEEL_URL = (
            "https://github.com/explosion/spacy-models/releases/download/"
            "en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"
        )
        if uv:
            subprocess.run(
                [uv, "pip", "install", "--quiet", "--python", str(venv_python),
                 SPACY_MODEL_WHEEL_URL],
                check=True,
            )
        else:
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--quiet",
                 SPACY_MODEL_WHEEL_URL],
                check=True,
            )
        print("==> en_core_web_sm installed in scratch venv")

        # 3a. Version reported by the installed package matches.
        out = run_in_venv(venv_python, "import allyanonimiser; print(allyanonimiser.__version__)")
        installed_version = out.strip()
        if installed_version != version:
            sys.exit(
                f"installed version {installed_version!r} != pyproject.toml version {version!r}"
            )
        print(f"==> installed version: {installed_version} (matches)")

        # 3b. Public factory accepts all advertised kwargs.
        run_in_venv(venv_python, """
from allyanonimiser import create_allyanonimiser
a = create_allyanonimiser(spacy_model=None, enable_caching=True, max_cache_size=1000)
assert a is not None
print('factory: OK')
""")
        print("==> create_allyanonimiser kwargs: OK")

        # 3b'. Default model contract: create_allyanonimiser() (no kwargs)
        # must load en_core_web_sm. v3.3.0 changed the default from lg to
        # sm; CI was previously installing only lg, which let the loader
        # silently fall back to lg and made it impossible to tell whether
        # the new default was actually wired up. Requires en_core_web_sm
        # to be installed in the venv (the release-check workflow does so).
        run_in_venv(venv_python, """
from allyanonimiser import create_allyanonimiser, SPACY_MODEL_FAST, SPACY_MODEL_ACCURATE
assert SPACY_MODEL_FAST == 'en_core_web_sm'
assert SPACY_MODEL_ACCURATE == 'en_core_web_lg'
ally = create_allyanonimiser()
loaded = ally.analyzer.spacy_model_loaded
assert loaded == 'en_core_web_sm', (
    f'expected default to load en_core_web_sm, got {loaded!r}. '
    'Either the default kwarg regressed or sm is not installed in this venv.'
)
status = ally.check_spacy_status()
assert status['is_loaded'] is True
assert status['has_ner'] is True
assert status['model_name'] == 'en_core_web_sm'
print(f'default model: OK ({loaded})')
""")
        print("==> default spaCy model is en_core_web_sm: OK")

        # 3c. expand_acronyms actually changes DataFrame output.
        # This is the regression that shipped in v3.1.1.
        run_in_venv(venv_python, """
import pandas as pd
from allyanonimiser import create_allyanonimiser
from allyanonimiser.io.dataframe_processor import DataFrameProcessor
ally = create_allyanonimiser(spacy_model=None)
ally.set_acronyms({'TL': 'Team Leader'})
df = pd.DataFrame({'text': ['TL review required']})
proc = DataFrameProcessor(ally)
no = proc.process_dataframe(df, 'text', expand_acronyms=False, progress_bar=False)
yes = proc.process_dataframe(df, 'text', expand_acronyms=True, progress_bar=False)
no_text = no['dataframe']['text_anonymized'].tolist()[0]
yes_text = yes['dataframe']['text_anonymized'].tolist()[0]
# When expansion is on, 'TL' becomes 'Team Leader' which the analyzer
# then detects (e.g. as PERSON) and anonymizes — so outputs MUST differ.
# Equality means expand_acronyms had no effect, which is the v3.1.1 bug.
assert no_text != yes_text, f'expand_acronyms had no effect: {no_text!r} == {yes_text!r}'
print(f'expand_acronyms: OK (no={no_text!r}, yes={yes_text!r})')
""")
        print("==> expand_acronyms wiring: OK")

        # 3d. Missing-column protection (v3.1.1 silent-skip regression).
        run_in_venv(venv_python, """
import pandas as pd
from allyanonimiser import create_allyanonimiser
from allyanonimiser.io.dataframe_processor import DataFrameProcessor
ally = create_allyanonimiser(spacy_model=None)
proc = DataFrameProcessor(ally)
try:
    proc.process_dataframe(pd.DataFrame({'a': ['x']}), text_columns='missing',
                           progress_bar=False)
    raise AssertionError('expected ValueError for missing column')
except ValueError as e:
    assert 'not found' in str(e)
print('missing-column: OK')
""")
        print("==> missing-column raises: OK")

    finally:
        if not args.keep_venv:
            shutil.rmtree(tmp, ignore_errors=True)

    print("\n[OK] all release smoke checks passed")


if __name__ == "__main__":
    main()
