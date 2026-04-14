# Next Session: Phase 4 — Release

## Completed

### Phase 1: Baseline Hardening
- Removed dead code, stubs, duplicate test tree, backup files
- Dropped setup.py/pytest.ini — pyproject.toml single source of truth
- Fixed CI, print→logging, hash()→hashlib.sha256, implemented real validators
- Tooling: ruff + pyright

### Phase 2: API Redesign
- allyanonimiser.py: 1,931 → 973 lines (50% reduction)
- Removed 13 deprecated wrappers
- Replaced stringly-typed manage_acronyms/manage_patterns with explicit methods
- Slimmed __init__.py: 218 → 128 lines

### Phase 3: Module Split + Structural Improvements
- **Package structure split**: `core/`, `io/`, `patterns/`, `utils/`, `insurance/`
- **BaseProcessor**: CSV/DataFrame/Stream processors share a common base class with unified `self.ally` attribute
- **Configurable entity priority**: `DEFAULT_ENTITY_PRIORITY` dict in `core/anonymizer.py`, merged with user overrides via `EnhancedAnonymizer(entity_priority={...})`
- **Pattern conflict resolution**: custom (user-added) patterns now beat generic NER (PERSON, LOCATION, etc.) when they match the same span; uses entity priority + registration-order bonus
- **Consolidated `load_spacy_model()`**: single cached implementation in `core/analyzer.py`, utils delegates to it
- **Removed empty `generators/` directory**
- **Last `print()` in library code** → `logging.warning()`
- **Test suite**: 186s → 6.7s (28x faster), 202 passed, 3 skipped, 0 failures
  - Previously 9 skipped → now 3 (fixed 6 by unskipping + fixing priority logic)

### Remaining 3 skipped tests
- `test_age_bracket_recent_dates` — dates near today detected as DATE not DATE_OF_BIRTH
- `test_custom_patterns_examples` / `test_advanced_spacy_patterns_examples` — example script files don't exist

## What's Next

### Phase 4: Release
1. Update README.md (new API, module paths, breaking changes)
2. CHANGELOG.md for v3.0.0
3. Migration guide
4. Tag release

### Future (v3.1+)
- Fix regex generation at "medium" level (currently generates `(123)|(456)` instead of `TEST-\d{3}`)
- Fix DATE vs DATE_OF_BIRTH classification for recent dates
- Migrate to uv for environment management
- Add pyright type checking to CI
