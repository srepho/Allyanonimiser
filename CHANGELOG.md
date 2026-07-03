# Changelog

## Unreleased

### Fixed — per-call options no longer leak into later calls

- **`analyze()` / `anonymize()` state leakage**: passing `active_entity_types` or `min_score_threshold` used to call sticky setters on the shared `EnhancedAnalyzer`, silently restricting every subsequent call (e.g. one `analyze(text, active_entity_types=["PERSON"])` made all later `anonymize()` calls PERSON-only). Per-call options are now threaded through as parameters and never mutate instance state. The explicit `set_active_entity_types()` / `set_min_score_threshold()` methods remain the documented persistent knobs. The same fix applies to `DataFrameProcessor` and `StreamProcessor`, which previously also stomped analyzer state (including unconditionally resetting the score threshold to their own default). New regression suite: `tests/test_state_isolation.py`.
- **`analyze_batch()` now produces identical results to per-text `analyze()`**: the batch fast-path previously cached spaCy entities without the PERSON/LOCATION/ORGANIZATION false-positive filtering and without entity-type mapping (raw `GPE`/`ORG` labels), so batch users missed the v3.5.0 precision improvements. Both paths now share one `_doc_to_results()` conversion. Also removed an O(n²) index lookup in the batch pre-warm loop.

### Changed — internal consolidation (no behavior change; AU bench verified identical)

- New `patterns/shared_regex.py`: single source for the AU identifier regexes (TFN/Medicare/ABN/ACN/passport/CRN labelled forms, the 6 AU_PHONE variants, EMAIL) that were previously duplicated — and already drifting (`1300\s+` vs `1300\s*`) — between `patterns/au_patterns.py` and `core/common_formats.py`.
- New `core/false_positives.py`: single source for the PERSON/LOCATION/ORGANIZATION false-positive word lists and span-shape checks previously duplicated between `core/analyzer.py` (inline lists) and `core/conflict_resolver.py` (frozensets). Moves ~140 lines of word lists out of `core/analyzer.py`.
- Removed the duplicate loose `CREDIT_CARD` pattern from `general_patterns.py`; the Luhn-validated 13-19-digit pattern in `general_intl_patterns.py` is a strict superset.

### Performance

- `ContextAnalyzer` is built once per analyzer instead of once per `analyze()` call.
- Result caches now evict the oldest half when full instead of clearing entirely (the old code cleared 100% of entries at the "LRU" comment).
- `analyze_batch` pre-warm deduplicates repeated texts before the `nlp.pipe()` call.

### Packaging / CI

- `build-system` now requires `setuptools>=77` (needed for the PEP 639 string-form `license = "MIT"`; the old `>=42` pin could misbuild metadata).
- Coverage upload folded into the main Tests workflow using the full suite; the stale `coverage.yml` (which reported coverage from only 4 test files) is deleted. `codecov-action` bumped v3 → v5, remaining `checkout`/`setup-python` pins bumped to v4/v5.
- `NEXT_SESSION.md` (internal session log) untracked from the public repo and gitignored; `MANIFEST.in` now also prunes `bench/`, `docs/`, `site/` from the sdist.

## 3.5.0 (2026-05-11)

International PII coverage added to the default pipeline (PHONE_INTL, US_SSN, CREDIT_CARD with Luhn, ISO_DATETIME, TIME), PERSON precision overhauled, and the conflict resolver no longer silently drops valid runner-ups when a permissive pattern wins by priority and then fails validation. Bench performance: on the enriched AU bench (160 docs, 1340 spans, including expat/payment/business-travel templates) Ally now beats `openai/privacy-filter` on 5 of 6 categories. On AI4Privacy English (1000 docs) Ally matches openai overall (ANY F1 0.782 vs 0.781) — up from 0.728.

### New — international entity types (loaded by default)

- **`PHONE_INTL`** — three variants: `+CC` anchored (`+44 7700 900123`, `+1-415-555-1234`), `00`-prefix IDD form (`0013 408-555-2222`), and parenthesised area code with 3-4 digits (`(415) 555-1234`, `(664)-9573546`). AU 2-digit area codes (`(03) 9876 5432`) stay with `AU_PHONE`.
- **`US_SSN`** — `\d{3}-\d{2}-\d{4}` with the SSA reservation rules (area ≠ 000/666/9xx, group ≠ 00, serial ≠ 0000).
- **`CREDIT_CARD`** — 13-19 digit blocks with optional 4-digit grouping, Luhn-validated via the new `EntityValidator.validate_credit_card`. Random multi-digit blocks fail the checksum and are dropped.
- **`ISO_DATETIME`** — `YYYY-MM-DDThh:mm[:ss][.f][Z|±hh:mm]`. Ranks above bare `DATE` (priority 55 vs 40).
- **`TIME`** — 12/24h with optional seconds and AM/PM. Lookbehind blocks DD/MM/YYYY date fragments from being read as times.

New `docs/patterns/international.md` documents the precedence rules and tuning options. New module `allyanonimiser/patterns/general_intl_patterns.py`.

### Fixes — conflict resolver

- **Validate-then-pick**: `resolve_entity_conflicts` now walks candidates from highest priority down and returns the first that passes per-type validation. Previously a permissive pattern (e.g. CREDIT_CARD matching a 13-digit phone) could win by priority, fail its checksum, and silently drop the valid runner-up.
- **PERSON FP check applied to single-candidate spans**: spaCy NER PERSON spans that don't co-occur with another entity at the exact same span now also go through `_is_false_positive_person`. Without this, address fragments and label words slipped through when nothing else competed for the span.
- **`ORGANIZATION` deny-list** widened to include label acronyms: `SSN`, `TIN`, `NIN`, `VIN`, `CRN`, `BSB`, `GST`, `POL`, `REF`, `ID` (parallel to existing `DOB`/`DOI`/`Medicare`/`ABN`/`TFN`/`ACN`).
- **Date-shaped LOCATION rejected**: spaCy occasionally tags dates like `14/07/2023` as `LOCATION`. Now dropped before priority resolution so the legitimate `DATE`/`INCIDENT_DATE` detection wins.

### Fixes — PERSON precision (AU bench PERSON F1 0.836 → 0.954)

- **City rejection**: AU capitals (`Sydney`, `Melbourne`, `Brisbane`, `Hobart`, `Darwin`, `Adelaide`, `Perth`, `Canberra`) and a handful of major cities are no longer accepted as PERSON when they appear alone.
- **State+postcode line rejection**: spans containing `(NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s+\d{3,4}` (e.g. `Darwin NT 6000`, `Sydney NSW 2000`) are always address fragments.
- **Date-shape rejection**: spaCy occasionally tags dates as PERSON when a name precedes them; date-shaped spans are now dropped.
- **Acronym + label-word rejection**: `VIN`/`ABN`/`PLC`/`LLC`/etc., and spans whose leading token is `Email`/`Phone`/`Vehicle`/`Residential`/etc.
- **Iterative trim of trailing label tokens**: `Joseph Schaefer\nDOB` → `Joseph Schaefer`, `Kristin Rodriguez\nClaims` → `Kristin Rodriguez`. The trim loops so multi-label tails like `\nClaim Number` get fully stripped.

### Fixes — VEHICLE_REGISTRATION false positives

- **SSN-shape collision fixed**: `bad SSN 999-04-7100` no longer absorbs `SSN 999-04` as a plate. Added `SSN/TIN/NIN` to the label deny-list plus a negative lookahead `(?![A-Z]{1,3}\s+\d{3}-\d{2}-\d{4}\b)`.
- **`DOB NN`, `PLC ABN` collisions fixed**: the loose `[A-Z]{1,3}[-\s]?[A-Z0-9]{2,3}[-\s]?[A-Z0-9]{1,3}` plate pattern was structurally matching label+number pairs. Now requires a digit anywhere in the upcoming match (`(?=[A-Z0-9-\s]*\d\b)`) and rejects the common label tokens.

### Fixes — `common_formats.py` identifier patterns

- Capture groups for `INSURANCE_CLAIM_NUMBER`, `INSURANCE_POLICY_NUMBER`, `VEHICLE_REGISTRATION` now require at least one digit in the identifier (`[A-Z0-9-]*\d[A-Z0-9-]*`). Stops `Claim Note` → `Note`, `Policy Number` → `Number`, `claim-mail.net` → `mail` matches.

### Fixes — date span boundaries

- **`DATE_OF_BIRTH` and `INCIDENT_DATE`** patterns rewritten with capture groups so the matched span equals just the date, not the trigger prefix. Was `'DOB: 04/01/1959'` (15 chars), now `'04/01/1959'` (10 chars). 380 FP chars eliminated on the AU bench.
- **`insurance_patterns.py` prefix-including patterns deleted**: the redundant `\bClaim:\s*[A-Za-z0-9-]{6,15}\b` / `\bPolicy Number:\s*...` / `\bVIN:\s*...` patterns are gone. `common_formats.py` already emits clean (capture-grouped) spans for the same shapes.

### Tests

- **40 new regression tests** in `tests/test_general_intl_patterns.py` covering: each new pattern's canonical inputs, SSA reservation rules for `US_SSN`, Luhn validation for `CREDIT_CARD` (valid + invalid), AU-phone precedence over PHONE_INTL on AU 2-digit area codes, ISO-vs-DATE-vs-TIME overlap precedence, and the SSN/VEHICLE_REGISTRATION collision regression.
- **Suite total: 268 passed, 8 skipped, 0 regressions.**

### Bench

- `bench/data/au_insurance.jsonl` extended from 100 → 160 docs with three new templates (expat claim, payment record, business travel claim) covering international shapes.
- `bench/make_au_insurance_eval.py` extended with international value generators (UK/US phones, US SSN, Luhn-valid credit card, ISO datetime, 12/24h time).
- `bench/run_au_insurance_eval.py` and `bench/run_ai4privacy_eval.py` label mappings extended for the new entity types.

### CI / infra

- `.github/workflows/tests.yml`: pyright was invoked with an invalid `--level basic` CLI flag making it a no-op. Now reads strictness from `[tool.pyright]` in `pyproject.toml` (kept `continue-on-error: true` while type debt is paid down).

### Performance

- Enriched AU bench (160 docs): Ally 2.3s vs `openai/privacy-filter` 55s on a 2019 Intel Mac (~24× faster).
- AI4Privacy English (1000 docs): Ally 8.3s vs openai 215s (~26× faster).

## 3.4.0 (2026-04-24)

Pattern precision fixes and a new benchmark suite. Surfaced by head-to-head evaluation against [`openai/privacy-filter`](https://huggingface.co/openai/privacy-filter) on three datasets (TAB, AI4Privacy open-pii-500k, synthetic AU insurance). See the README *Benchmarks* section and `bench/README.md` for methodology and full results.

### Fixes — false positives

- **AU_ADDRESS** no longer absorbs narrative prose. The two loose fallback patterns are gone. The remaining two patterns (strict title-case + case-tolerant) are anchored by a state abbreviation; the case-tolerant form additionally requires a postcode. Previously, text like *"On 15 May 2007 the Court decided to give notice of the application to the Government"* produced a 74-char `AU_ADDRESS` span because `Court` is in the street-suffix list.
- **AU_POSTCODE** no longer matches bare 4-digit numbers. It now requires either a state abbreviation or a `postcode` / `post code` / `postal code` label (via fixed-width lookbehind). This stops year-in-date matches like `"15/03/2023"` → `2023` and amount matches like `"8500 dollars"` → `8500`.
- **DATE** validator reordered so phone-prefix check runs before the generic 4-digit branch. Added `phone_fragment` pattern for space-separated mobile fragments like `"0437 159"`. Added `phone_fragment`, `number`, `postcode`, `duration` to the conflict-resolver reject list so spaCy NER mislabels don't slip through.

### Fixes — false negatives

- **AU_ADDRESS** now handles case variants: `"123 Main Street, sydney NSW 2000"`, `"42 queen st, melbourne vic 3000"`, and `"Unit 5, 23 BOURKE COURT, CANBERRA ACT 2600"` all match via a new case-insensitive pattern.
- **AU_POSTCODE** label variants now recognised: `post code 3000`, `postal code 3000`, mixed/lowercase (`Post Code`, `Postal Code`).
- **DATE** validator extended with 11 new patterns for spaCy's natural-language DATE outputs: `March 2024`, `Month/YY`, day names (`Friday`, `Mon`), relative (`next Monday`, `last week`, `this morning`), quarter/half (`Q1 2024`, `FY24`, `H1 2024`), times (`20:10:26`, `10:30am`), `yesterday`/`today`/`tomorrow`, and decade forms (`the 1990s`, `the early 2000s`).
- **INSURANCE_CLAIM_NUMBER** accepts `CLM` prefix alongside `CL`/`C`.

### New — Benchmarks

- `bench/` directory with three eval scripts, a Faker-based synth AU-insurance generator, and a README with reproduction steps.
- New `[bench]` optional dependency group (`pip install "allyanonimiser[bench]"`) pulling `faker`, `datasets`, `huggingface_hub`, `tokenizers`, `onnxruntime`.
- README *Benchmarks* section with per-dataset P/R/F1 tables and interpretation.

### Results snapshot

On synthetic AU insurance (100 documents, ~12 PII spans/doc), Allyanonimiser beats `openai/privacy-filter` on 4 of 6 categories (ADDRESS 0.980, EMAIL 1.000, PHONE 1.000, ACCOUNT-like 0.877) while running ~25× faster per document on CPU. Both tools converge on the ANY F1 metric (0.920 vs 0.943). `openai/privacy-filter` leads on the multilingual AI4Privacy benchmark, where Allyanonimiser's AU-specific phone and account-number patterns don't match US/EU formats.

### Compatibility

No API changes. Runtime behaviour changes only affect the spans that were previously mis-detected. The new optional `[bench]` extra does not affect the core install.

## 3.3.0 (2026-04-15)

### Behavior change (observable)

- **Default spaCy model is now `en_core_web_sm`** (was `en_core_web_lg`). The choice is now explicit: pass `spacy_model="en_core_web_lg"` (or the new `SPACY_MODEL_ACCURATE` constant) to opt into the larger model.

  | What gets worse if you stay on the new default | Magnitude |
  |---|---|
  | `PERSON` recall on insurance text | ~92% → ~80% (titled names, two-word edge cases more often missed) |
  | `LOCATION` recall (cities, suburbs, addresses) | noticeably worse |
  | `ORG` recall (insurance companies, repairers, hospitals) | noticeably worse |
  | Pattern detection (TFN, ABN, MEDICARE, AU_PHONE, EMAIL, dates) | unchanged — still 100% identical |

  | What gets better | |
  |---|---|
  | Cold start | ~2-5s → ~0.5s |
  | Resident memory | ~1.5 GB → ~200 MB |
  | Download size | 587 MB → 44 MB |
  | Serverless friendliness (Azure Functions, Lambda) | poor → good |

### Added
- **`SPACY_MODEL_FAST` and `SPACY_MODEL_ACCURATE`** constants exported from the top-level package, so callers can pick the model without remembering the spaCy package name:
  ```python
  from allyanonimiser import create_allyanonimiser, SPACY_MODEL_ACCURATE
  ally = create_allyanonimiser(spacy_model=SPACY_MODEL_ACCURATE)
  ```
- README and `docs/getting-started/installation.md` now lead with the small-model install and include a tradeoff table for picking between them.
- `Allyanonimiser.check_spacy_status()` now prints a nudge toward `en_core_web_lg` when the default `sm` is loaded, so users discover the upgrade path without reading docs first.

### Migration
- If you previously relied on `lg`-quality `PERSON`/`LOCATION`/`ORG` detection (e.g. you have insurance call notes where names are signal), pin the model in your factory call:
  ```python
  ally = create_allyanonimiser(spacy_model="en_core_web_lg")
  ```
- The `lg`-not-installed → `sm` fallback chain still works, so existing environments with `lg` already installed will load it when you ask for it.

## 3.2.0 (2026-04-15)

### Behavior change (mildly observable)
- **Invalid TFNs and ABNs are no longer detected.** The `EntityValidator` checksum algorithms (modulus-11 weighted sum for TFN, modulus-89 weighted sum with `digit[0] -= 1` for ABN) were always implemented, but `core.conflict_resolver.deduplicate_and_resolve_conflicts` only called the validator on results that had no competition. Whenever the same span was matched by multiple sources (e.g. AU_TFN from patterns + AU_TFN from common_formats + AU_CENTRELINK_CRN), the conflict resolver picked a winner by priority and skipped validation, letting invalid checksums through. The validator now runs on the winner regardless of how it was chosen.
- Net effect: a numerically-invalid TFN like `123 456 789` no longer gets anonymized as `<AU_TFN>` — it passes through unredacted. Anything that hit a real TFN's actual checksum is unaffected. Users with synthetic test data that happens to fail checksum should expect those values to no longer be redacted.

### Added
- **CI release-check workflow** (`.github/workflows/release-check.yml`) builds + `twine check`s + spins a fresh venv + installs the sdist + runs four smoke assertions on every push, PR, and tag. Does not publish.
- **`scripts/smoke_release.py`** — same gate for local pre-publish use. Run it before any `twine upload`.
- **`tests/test_conflict_resolver.py`** — direct unit tests for `deduplicate_and_resolve_conflicts` and `resolve_entity_conflicts`. Previously these were only exercised indirectly through `Allyanonimiser.analyze()`.

### Tests
- TFN/ABN checksum assertions in `test_robust_detection.py` re-enabled (were commented out with "skip checksum test for now").
- Test fixtures across the suite migrated from invalid-checksum TFN `123 456 789` to valid TFN `123 456 782`.
- Full suite: **220 passed**, 7 skipped, 7 deselected.

## 3.1.2 (2026-04-15)

Supersedes 3.1.1, which was yanked due to a bug in DataFrame processing and
inconsistent release metadata.

### Fixed
- **`DataFrameProcessor.process_dataframe`** now wires `expand_acronyms=` through to `ally.analyze()` and `ally.anonymize()`. In 3.1.1 (and earlier) the kwarg was silently swallowed by `**kwargs`, so `expand_acronyms=True` had no effect.

### Packaging
- **Test fixtures `tests/test_data/*.csv`** now ship in the sdist (`.gitignore` excluded them from earlier releases — tests in `test_csv_import.py` depended on them). Added a `!tests/test_data/*.csv` exception.
- **`allyanonimiser.egg-info/PKG-INFO`** removed from version control. It was tracked from a pre-3.0 build and went stale every release; `*.egg-info/` is already in `.gitignore`.

### Tests
- `tests/test_example_scripts.py` rewritten to smoke-test the two real example scripts (`example_csv_processing.py`, `example_spacy_status.py`). Slow `main()` invocations opt-in via `-m slow`.
- `pyproject.toml` excludes `slow` and `performance` markers from the default `pytest` run. Default suite: **207 passed, 7 skipped, 7 deselected** in ~8s.

### Internal
- Ruff autofix sweep: 136 fixes across 17 files (mostly `Optional[X]` → `X | None`). 64 manual line-length issues remain.

## 3.1.1 (2026-04-15) — yanked

### Fixed
- **`create_allyanonimiser` top-level wrapper** now forwards `enable_caching`, `max_cache_size`, and `spacy_model` (previously silently dropped — `from allyanonimiser import create_allyanonimiser; create_allyanonimiser(spacy_model=None)` raised `TypeError`).
- **`DataFrameProcessor.process_dataframe`** now raises `ValueError` up front when `text_columns` names a column that does not exist, instead of logging a warning and returning a "successful" result. This restores pre-v3.1 behavior and prevents typos from silently producing empty output.
- **`tests/test_pyarrow_integration.py`** rewritten to target the current API (`_use_arrow_strings`, `string[pyarrow]` dtype behavior, and missing-column regression). The old suite referenced `_to_arrow_table` / `_get_column_from_arrow`, which were removed in v3.1 — any environment with pyarrow installed would have errored on import.

### Changed
- **Python support narrowed to 3.12 – 3.13.** spaCy 3.8.x does not ship cp314 wheels on macOS x86_64, so the 3.14 classifier and the `"switch to uv + Python 3.14"` claim were not reproducible. `requires-python` is now `>=3.12,<3.14`; the 3.14 classifier has been removed.
- **CI matrix updated** from `['3.10', '3.11', '3.12']` to `['3.12', '3.13']` to match `requires-python`.
- **README / installation docs** updated from "Python 3.10 or higher" to reflect the actual supported range.

## 3.0.0 (2026-04-14)

### Breaking Changes
- **Package restructured** into `core/`, `io/`, `patterns/`, `utils/` layers
- **Import paths changed**: e.g. `allyanonimiser.enhanced_analyzer` → `allyanonimiser.core.analyzer`
- **Stringly-typed methods removed**: `manage_acronyms(action=...)` and `manage_patterns(action=...)` replaced with explicit methods (`add_acronyms()`, `add_pattern()`, `create_pattern_from_examples()`, etc.)
- **13 deprecated wrapper methods removed** (`set_acronym_dictionary`, `create_dataframe_processor`, etc.)
- **Stub modules removed**: `generators/` package, `InsuranceEmailAnalyzer`, `MedicalReportAnalyzer`
- **`setup.py` removed** — `pyproject.toml` is the single source of truth
- **Hash operator changed**: uses SHA-256 (`HASH-a1b2c3d4e5`) instead of Python `hash()` — existing hashed values will differ

### Added
- **`core/` subpackage**: analyzer, anonymizer, pattern_manager, pattern_registry, context_analyzer, validators
- **`io/` subpackage**: csv_processor, dataframe_processor, stream_processor with shared `BaseProcessor`
- **Configurable entity priority**: `DEFAULT_ENTITY_PRIORITY` dict in `core/anonymizer.py`; override via `EnhancedAnonymizer(entity_priority={...})`
- **Custom pattern priority**: user-added patterns now beat generic NER (PERSON, LOCATION, etc.) when matching the same text span
- **`check_pattern_against_examples()`**: real implementation with precision/recall/f1 metrics (was a stub)
- **`validate_pattern_definition()`**: real implementation with entity_type validation (was a stub)
- **spaCy model caching**: loaded once per process at module level

### Changed
- **`allyanonimiser.py`**: 1,931 → 973 lines (50% reduction)
- **`__init__.py`**: 218 → 128 lines; slimmed export surface
- **All `print()` in library code** replaced with `logging`
- **CI workflow**: simplified, now fails hard on test failures (no more `|| echo` swallowing)
- **Tooling**: ruff + pyright replace black/isort/flake8/mypy
- **Processor naming**: all IO processors use `self.ally` consistently (was mixed `self.analyzer`/`self.ally`)

### Fixed
- **Test suite poisoning**: removed `test_imports.py` which injected MagicMock into `sys.modules`
- **Duplicate test tree**: removed `allyanonimiser/tests/` (4 files that duplicated root `tests/`)
- **Hypothesis tests**: fixed edge cases with whitespace-only expansions and duplicate keys
- **Pattern generation tests**: fixed assertions that tested regex string representation instead of behavior
- **SPDX license expression**: fixed `pyproject.toml` to satisfy modern setuptools

### Performance
- **Test suite**: 186s → 6.7s (28x faster) via module-level spaCy model caching
- **Net code reduction**: ~5,000 lines deleted

## 2.5.0 (2025-08-14)

### Added
- **CSV Processing Module**: New `csv_processor.py` module with comprehensive CSV file handling capabilities
- **Direct CSV File Processing**: Process CSV files directly without manual DataFrame operations via `process_csv_file()`
- **PII Column Auto-Detection**: Automatically identify columns containing PII with `detect_pii_columns()`
- **Preview Mode**: Preview anonymization changes before processing with `preview_csv_changes()`
- **Streaming for Large Files**: Process multi-GB CSV files that don't fit in memory with `stream_process_csv()`
- **Directory Batch Processing**: Process all CSV files in a directory with `process_csv_directory()`
- **Processing Reports**: Generate detailed reports after CSV processing including entity counts and statistics

### Enhanced
- **Simplified CSV Workflow**: Eliminated need for manual DataFrame loading and processing
- **Intelligent Detection**: Auto-detect PII columns with configurable confidence thresholds
- **Memory Efficiency**: Stream processing for large files with configurable chunk sizes
- **Batch Operations**: Process entire directories of CSV files with aggregated statistics
- **Better User Experience**: Preview changes before committing to full processing

### Developer Experience
- **New Examples**: Added `example_csv_processing.py` demonstrating all CSV features
- **Comprehensive Tests**: New test suite for CSV processing functionality
- **Direct API Access**: All CSV methods available directly on main Allyanonimiser instance
- **Report Generation**: Automatic processing reports with entity statistics

## 2.4.0 (2025-07-25)

### Added
- **Enhanced spaCy Status Reporting**: Clear visual feedback when loading spaCy models with helpful installation guidance
- **New `check_spacy_status()` Method**: Programmatically check spaCy configuration and get specific recommendations
- **Setup Verification Script**: New `verify_setup.py` script to check all dependencies and configurations
- **spaCy Status Example**: New `example_spacy_status.py` demonstrating spaCy integration checking

### Enhanced
- **Improved Documentation**: Clearer guidance on spaCy requirements and their impact on functionality
- **Better Error Messages**: More helpful feedback when spaCy models are missing or misconfigured
- **Model Detection**: Automatically detects which spaCy model is loaded (large, small, or blank)
- **Visual Indicators**: Uses ✓ and ⚠️ symbols for clear status indication

### Developer Experience
- **Setup Verification**: Easy way to verify installation is complete and working properly
- **Clearer Prerequisites**: README now clearly explains what works with/without spaCy models
- **Programmatic Checks**: Applications can now check spaCy status and adapt behavior accordingly

## 2.3.0 (2025-07-23)

### Added
- **Comprehensive False Positive Filtering**: Added extensive filtering for PERSON and LOCATION entities with 100+ false positive words
- **NAME_CONSULTANT Pattern**: New entity type for detecting consultant/agent names with proper boundary detection
- **Enhanced BSB/Account Detection**: Split AU_BSB_ACCOUNT into separate AU_BSB and AU_ACCOUNT_NUMBER entities for better detection
- **Improved Organization Patterns**: Added support for alphanumeric company names and Australian business suffixes (Pty Ltd, Limited)

### Fixed
- **PERSON False Positives**: Words like "await", "repairs", "balance", "outstanding" are no longer detected as PERSON entities
- **LOCATION False Positives**: Common action words and business terms no longer incorrectly detected as locations
- **PERSON Boundary Issues**: Names no longer capture trailing words like "Subject", "Status", "Regarding"
- **BSB Pattern Detection**: Fixed detection of formats like "BSB : 062-000"
- **Account Number Detection**: Fixed detection of formats like "Account Number : 1617 8029"
- **Organization Detection**: "Pty Ltd" companies now properly detected (e.g., "Right2Drive Pty Ltd")
- **Vehicle Registration**: Refined patterns to reduce false positives from all-caps text

### Enhanced
- **Pattern Matching**: Better handling of labeled formats (e.g., "Payee Name : Company Pty Ltd")
- **Context Awareness**: Improved boundary detection for all entity types
- **Detection Accuracy**: Significantly reduced false positives while maintaining high recall

## 2.2.0 (2025-07-21)

### Added
- **Robust Detection System**: Enhanced validation and context-aware detection to reduce false positives
- **Overlapping Entity Resolution**: Smart handling of overlapping entities prevents text corruption during anonymization
- **Automatic Pattern Loading**: All default patterns (Australian, Insurance, General) now load automatically on initialization
- **Context Analyzer**: New `context_analyzer.py` module for context-aware entity detection
- **Entity Validators**: New `validators.py` module with validation functions for various entity types
- **Comprehensive Test Suite**: Added test files for robust detection, overlapping entities, and multiple entity masking

### Fixed
- **Medicare Number Detection**: Fixed Medicare number detection and validation for numbers starting with 2-6
- **Date False Positives**: "NSW 2000" and similar state+postcode combinations no longer detected as dates
- **Phone Number Detection**: Improved detection of Australian service numbers (1300, 1800, 13xx)
- **Overlapping Entity Handling**: Fixed text corruption when entities overlap (e.g., Medicare number containing postcode)
- **Pattern Conflicts**: Resolved conflicts between TFN, ABN, and ACN patterns by making them context-specific

### Enhanced
- **False Positive Filtering**: Added filtering for common false positives (street names as PERSON, abbreviations as ORGANIZATION)
- **Entity Priority System**: Implemented priority-based resolution for overlapping entities
- **Date Validation**: Enhanced date validation to avoid phone number prefixes and Medicare numbers
- **Multiple Entity Masking**: Improved support for simultaneous masking of multiple entity types with different operators

## 2.1.0 (2025-03-03)

### Added
- NSW legacy driver's license pattern support (licenses issued until 1990)
- Comprehensive pattern reference table in documentation
- Enhanced pattern management examples in README

### Fixed
- Fixed package build with proper dependency specifications
- Added missing dependencies in pyproject.toml (pandas, tqdm)
- Updated documentation with clearer pattern examples

## 2.0.0 (2025-03-30)

### Added
- Comprehensive reporting system with rich visualization capabilities:
  - Added `AnonymizationReport` class for tracking statistics and metrics
  - Added `ReportingManager` class for handling report sessions
  - Added integration with Jupyter notebooks for rich visualizations
  - Added multiple export formats (HTML, JSON, CSV) for report sharing
  - Added detailed entity type tracking and distribution analysis
  - Added performance metrics tracking for anonymization operations
  - Added document-level statistics and batch reporting features
  - Added visual charts for entity distribution and operator usage
  - Created example scripts demonstrating reporting capabilities

### Enhanced
- Integrated reporting system with existing functionality:
  - Added reporting to anonymize(), process(), and process_files() methods
  - Added report display capabilities for Jupyter notebook environments
  - Added methods to start, retrieve, and finalize reports
  - Added automated reporting for batch operations
  - Improved reporting of anonymization effectiveness with rate metrics
  - Enhanced documentation with comprehensive reporting examples
  - Added test suite for reporting functionality

## 1.2.0 (2025-03-29)

### Added
- Stream processing for very large files with Polars integration:
  - Implemented `StreamProcessor` class for memory-efficient processing
  - Added chunk-by-chunk processing with minimal memory footprint
  - Created streaming file reader for multi-gigabyte CSV files
  - Added streaming API for custom chunk processing
  - Added comprehensive error handling for stream processing failures
  - Implemented graceful fallbacks when Polars is not available
  - Added adaptive chunk sizing based on data volume
  - Added example script (`example_stream_processing.py`) demonstrating stream processing

### Improved
- Enhanced memory efficiency when processing multi-gigabyte datasets
- Added streaming progress bars for better user feedback
- Updated documentation with comprehensive stream processing examples
- Added tests for stream processing functionality

## 1.1.0 (2025-03-28)

### Added
- Simplified API with unified interface methods for common operations:
  - Added `manage_acronyms(action, data, ...)` to replace multiple acronym methods
  - Added `manage_patterns(action, data, ...)` to replace multiple pattern methods
  - Added unified `process_dataframe(operation, ...)` to consolidate DataFrame methods
- Added configuration objects for improved parameter organization:
  - `AnalysisConfig` for grouping analysis parameters
  - `AnonymizationConfig` for grouping anonymization parameters
- Added stream processing for very large files with Polars integration:
  - Implemented `StreamProcessor` class for memory-efficient processing
  - Added chunk-by-chunk processing with minimal memory footprint
  - Created streaming file reader for multi-gigabyte CSV files
  - Added streaming API for custom chunk processing
  - Added comprehensive error handling for stream processing failures
  - Implemented graceful fallbacks when Polars is not available
  - Added adaptive chunk sizing based on data volume
  - Added example script (`example_stream_processing.py`) demonstrating stream processing
- Created new example script (`example_simplified_api.py`) demonstrating the simplified API
- Maintained backward compatibility with deprecated method support
- Added comprehensive docstrings for all new methods

### Improved
- Reduced total public API method count while preserving all functionality
- Consolidated parameter handling for better code organization
- Enhanced code maintainability and reduced duplication
- Simplified pattern and acronym management workflows
- Optimized large file processing with adaptive chunk sizing
- Enhanced memory efficiency when processing multi-gigabyte datasets
- Added streaming progress bars for better user feedback

## 1.0.0 (2025-03-27)

### Breaking Changes
- Removed legacy analyzer factory functions (`create_au_analyzer`, `create_insurance_analyzer`, `create_au_insurance_analyzer`)
- Added cleaner `create_analyzer()` function as the main entry point
- Increased major version number to indicate production readiness
- Removed backward compatibility with 0.x versions
- Streamlined and simplified internal implementation
- Improved documentation and examples with clearer API usage

## 0.3.3 (2025-03-27)

### Changed
- Updated minimum Python version requirement to 3.10+
- Added support for Python 3.11 and 3.12
- Removed support for Python 3.8 and 3.9 due to dependency requirements (particularly NumPy 2.0+)
- Updated GitHub Actions workflows to test on Python 3.10-3.12 only

### Fixed
- Fixed circular import issues in the insurance module
- Enhanced batch processing capabilities for better performance
- Addressed compatibility issues with newer NumPy (2.0+) requirements
- Fixed package build and CI/CD processes
- Improved documentation for Python version requirements

## 0.3.2 (2025-03-25)

### Added
- Configuration export/import functionality for sharing settings between users
- Added `export_config()` method to export settings to JSON or YAML files
- Enhanced settings manager with functions to create shareable configurations
- Added support for exporting and importing configuration files
- Created example_export_config.py demonstrating configuration sharing
- Added comprehensive test suite for configuration export functionality
- Added PyArrow integration for improved DataFrame performance
- Graceful fallback for environments without PyArrow installed
- Configurable PyArrow usage through settings with sensible defaults

### Enhanced 
- Modified DataFrameProcessor class to utilize PyArrow when available
- Updated README with comprehensive documentation on configuration sharing
- Improved error handling in configuration import/export

## 0.3.1 (2025-03-20)

### Added
- DataFrameProcessor class for efficient pandas DataFrame processing
- Batch processing for handling large DataFrames with optimized memory usage
- Multi-processing capabilities for improved performance
- Comprehensive DataFrame anonymization functionality
- Statistical analysis tools for entity detection results
- Progress tracking with tqdm for long-running operations
- Extended main interface with DataFrame convenience methods
- Added example_dataframe.py demonstrating DataFrame processing

### Enhanced
- Added pandas dependency to package requirements
- Implemented test suite for DataFrame processing
- Added documentation for DataFrame processing in README
- Optimized entity detection algorithms for batched data

## 0.3.0 (2025-03-10)

### Added
- Comprehensive custom pattern creation and management functionality
- PatternManager class for handling pattern collections and application
- PatternRegistry class for saving and loading patterns
- Enhanced CustomPatternDefinition with serialization capabilities
- Support for creating patterns from examples with different generalization levels
- Added pattern creation helpers in main interface
- Implemented pattern persistence with JSON storage
- Added example script demonstrating custom pattern usage

### Enhanced
- Improved entity type metadata for custom patterns
- Enhanced pattern explanation capabilities
- Extended public API with pattern management methods
- Improved pattern testing and validation support

## 0.2.2 (2025-02-28)

### Added
- Integrated spaCy's NER system for more accurate PERSON entity detection
- Added entity type mapping between spaCy NER and custom entity types
- Improved detection of names with contextual understanding

### Fixed
- Reduced false positives by prioritizing spaCy NER results over pattern matching for PERSON entities
- Fixed issues with conflicting entity types for the same text span
- Addressed false positives for phrases like "Ref Number" being detected as PERSON entities
- Added proper entity type resolution with configurable prioritization rules

## 0.2.1 (2025-02-28)

### Fixed
- Fixed import issue with `create_simple_generalized_regex` function in package
- Corrected relative vs. absolute imports in pattern generation functionality
- Added missing pattern generation functions to package structure
- Fixed syntax errors in regex pattern matchers

## 0.2.0 (2025-02-28)

### Added
- Implemented multi-level pattern generalization system with four levels of flexibility
- Added intelligent format detection for common patterns (dates, emails, phone numbers)
- Created prefix/suffix analysis and character class recognition algorithms
- Added `generalization_level` parameter to `create_pattern_from_examples`
- Added comprehensive docstrings with detailed examples
- Created example script `example_advanced_pattern_generation.py`
- Exposed additional pattern generation helper functions

### Enhanced
- Improved pattern matching capability for variations of examples
- Made generated patterns more flexible with character classes
- Enabled automatic detection of common format patterns

### Fixed
- Fixed imports in the pattern generator modules
- Improved error handling in pattern generation functions
- Fixed path issues in the pattern creation utility functions

## 0.1.8 (2025-02-28)

### Added
- Improved package structure for better organization
- Added clearer examples for custom pattern creation
- Enhanced documentation for pattern validation
- Additional utility functions for pattern registry management

### Fixed
- Resolved installation issues on certain platforms
- Improved compatibility with different Python versions

## 0.1.7 (2025-02-28)

### Fixed
- Fixed text mangling issue in anonymizer by separating entity collection from replacement
- Improved handling of overlapping entities during anonymization
- Enhanced text replacement algorithm to maintain correct positions

## 0.1.6 (2025-02-28)

### Changed
- Optimized pattern detection performance for long documents
- Enhanced accuracy of Australian TFN and Medicare patterns
- Improved handling of edge cases in insurance pattern detection
- Bug fixes in enhanced_analyzer.py for certain pattern matches

### Fixed
- Fixed performance issues when processing large claim notes
- Resolved pattern matching inconsistencies in insurance_patterns.py
- Fixed detection issues with Australian formats in au_patterns.py
- Improved compatibility with different spaCy model versions

## 0.1.5 (2025-02-28)

### Added
- Greatly expanded pattern sets for more comprehensive PII detection
- Enhanced Australian-specific patterns for TFNs, Medicare numbers, phone numbers, addresses
- Added insurance-specific patterns for policy numbers, claim references, and vehicle identifiers
- Improved detection of general patterns such as person names, email addresses, dates, monetary amounts
- Fixed detection rates for common PII in example claim notes

### Changed
- Updated README badges to point to correct GitHub repository
- Improved pattern matching precision for Australian contexts
- Enhanced regex patterns for more accurate entity detection

## 0.1.4 (2025-02-28)

### Added
- Functional implementation of EnhancedAnalyzer with regex-based PII detection
- Added RecognizerResult class to represent detected PII entities
- Implemented anonymization functionality with multiple operator types (replace, mask, redact, hash)
- Enhanced pattern files with comprehensive patterns for Australian PII, insurance information, and general entities
- Added text segmentation and PII detection scoring in long_text_processor
- Implemented the process method in Allyanonimiser for one-step analysis and anonymization

### Changed
- Updated README with detailed description of new features
- Fixed badge URLs in README to point to correct GitHub repository
- Made minimal processing work without relying on external packages
- Improved documentation with examples of using the new functionality

## 0.1.3 (2025-02-28)

### Added
- Enhanced factory functions to accept custom patterns parameter
- Improved flexibility in function parameters with better default values
- More robust pattern creation from examples

### Changed
- Made API more flexible and customizable
- Improved handling of different pattern types
- Further enhanced code structure to avoid import issues

## 0.1.2 (2025-02-28)

### Fixed
- Fixed circular import issue between `__init__.py` and `insurance/claim_notes_analyzer.py`
- Restructured imports to ensure factory functions are defined before they are used
- Moved the import of insurance modules below the factory function definitions

## 0.1.1 (2025-02-25)

### Fixed
- Fixed package structure to work when installed from PyPI
- Fixed relative imports to use proper dot notation
- Added missing `__init__.py` files

## 0.1.0 (2025-02-15)

### Added
- Initial release
- Support for Australian PII detection
- Specialized analyzers for insurance claim notes, emails, and medical reports
- Integration with Presidio and spaCy
- Custom pattern registry and validation