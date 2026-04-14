# Next Session

## Current State (v3.0.0 — committed, not pushed)

Two commits on `main` ahead of origin:
- `741ec7d` — Major restructure (59 files, -6,270/+1,760 lines)
- `845d248` — README + CHANGELOG docs

**Tests: 202 passed, 3 skipped, 0 failures, 6.8s**

## What Was Done This Session

### Phase 1: Baseline Hardening
- Removed dead code: stubs, duplicate test tree (`allyanonimiser/tests/`), backup files, obsolete test runners
- Dropped `setup.py` and `pytest.ini` — `pyproject.toml` single source of truth
- Fixed CI (`tests.yml`) to fail hard on test failures (was swallowing with `|| echo`)
- Replaced `print()` with `logging` in all library code
- Replaced `hash()` with `hashlib.sha256` for deterministic anonymization
- Implemented real `validators.py` functions (were broken stubs importing from nonexistent `pattern_validators`)
- Fixed `test_imports.py` that was injecting MagicMock into `sys.modules` and cascading failures
- Tooling: ruff + pyright replace black/isort/flake8/mypy

### Phase 2: API Redesign
- `allyanonimiser.py`: 1,931 → 973 lines (50% reduction)
- Removed 13 deprecated wrapper methods
- Replaced `manage_acronyms(action=...)` with explicit methods: `set_acronyms()`, `add_acronyms()`, `remove_acronyms()`, `get_acronyms()`, `import_acronyms_from_csv()`
- Replaced `manage_patterns(action=...)` with explicit methods: `add_pattern()`, `create_pattern_from_examples()`, `load_patterns()`, `import_patterns_from_csv()`, `save_patterns()`
- Slimmed `__init__.py`: 218 → 128 lines

### Phase 3: Module Split + Structural Improvements
- **Package split**: `core/` (analyzer, anonymizer, pattern_manager, pattern_registry, context_analyzer, validators), `io/` (csv_processor, dataframe_processor, stream_processor with BaseProcessor), `patterns/`, `utils/`, `insurance/`
- **Configurable entity priority**: `DEFAULT_ENTITY_PRIORITY` dict in `core/anonymizer.py`; user overrides via `EnhancedAnonymizer(entity_priority={...})`
- **Pattern conflict resolution**: custom patterns now beat generic NER (PERSON, LOCATION, etc.) using priority dict + registration-order bonus
- **Consolidated `load_spacy_model()`**: single cached implementation in `core/analyzer.py`, `utils/spacy_helpers.py` delegates to it
- **BaseProcessor**: shared base class for CSV/DataFrame/Stream with unified `self.ally`
- **spaCy model caching**: module-level cache → test suite 186s → 6.8s
- Removed empty `generators/` directory

### Phase 4: Docs
- README updated with migration guide (v2.x → v3.0), package structure diagram, new API examples
- CHANGELOG.md entry for v3.0.0

## Remaining 3 Skipped Tests
- `test_age_bracket_recent_dates` — dates near today detected as DATE not DATE_OF_BIRTH
- `test_custom_patterns_examples` / `test_advanced_spacy_patterns_examples` — example script files don't exist on disk

## What's Next

### Immediate (before/after push)
- Push to origin: `git push`
- Consider tagging: `git tag v3.0.0`
- Build and upload to PyPI if desired

### v3.1 Candidates
- **Regex generation bug**: "medium" generalization for `["TEST-123", "TEST-456"]` produces `(123)|(456)` instead of `TEST-\d{3}` — root cause is in `utils/spacy_helpers.py`'s `create_regex_from_examples()`
- **DATE vs DATE_OF_BIRTH**: recent dates not classified as DOB even with "DOB:" context prefix
- **`core/analyzer.py` is still 1,100 lines** — `_deduplicate_and_resolve_conflicts` (80 lines of hardcoded rules) and `_analyze_common_formats` could be extracted
- **Move `reporting.py` into `reporting/`** subpackage
- **Add pyright/ruff to CI** workflow
- **Migrate to uv** for environment management
- **Update example scripts** to match new v3.0 API (currently reference old imports)
- **Performance tests** (`test_performance.py`) reference `create_dataframe_processor()` which was removed — needs updating
