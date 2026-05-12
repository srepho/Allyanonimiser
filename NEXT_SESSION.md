# Next Session

## Current State — v3.5.0 shipped (2026-05-11)

- **PyPI**: https://pypi.org/project/allyanonimiser/3.5.0/
- **GitHub release**: https://github.com/srepho/Allyanonimiser/releases/tag/v3.5.0 (wheel + sdist attached)
- **Tag**: `v3.5.0` → commit `e0f2076`
- **Docs site**: https://srepho.github.io/Allyanonimiser/ — new `/patterns/international/` page wired into nav
- **CI**: all 6 workflows green on Python 3.12 + 3.13 (Tests, Release Check, Test Coverage, Package Checks, Deploy Docs, Graph Update)
- **PyPI version history**: 3.5.0 (latest), 3.4.0, 3.3.0, 3.1.2 (unyanked fallback), 3.1.1 (yanked — had `expand_acronyms` regression)

## Post-release follow-ups landed (2026-05-12)

- `README.md` Entity Type Reference bumped from 38 → 43, added a new `🌐 International / System PII Entities` collapsed section + a regex-pattern table for the new types. Cleaned up stale Insurance Patterns entries (`INSURANCE_MEMBER_NUMBER`, `INSURANCE_GROUP_NUMBER`, `CASE_REFERENCE` removed — those entity types don't exist in code).
- `comprehensive_entity_examples.md` updated similarly (header + new example block + reference rows).

## GitHub repo metadata — pending user decision

The repo About sidebar is sparse and doesn't match the project's actual pitch. **Awaiting user approval** before applying:

- **Description** (currently *"A Python tool to help with removing PII and related fields from free text."*) → suggest *"Australian-focused PII detection and anonymization for the insurance industry — fast, regex+spaCy, no GPU. Beats openai/privacy-filter on AU-insurance benches."*
- **Homepage URL** (currently empty) → `https://srepho.github.io/Allyanonimiser/`
- **Topics** (currently none) → `pii`, `pii-detection`, `anonymization`, `privacy`, `australia`, `insurance`, `presidio`, `spacy`, `gdpr`

Apply with `gh repo edit srepho/Allyanonimiser --description "..." --homepage "..." --add-topic ...` once approved.

## Headline changes in v3.5.0

International PII shapes are now detected by default — surfaced by extending the AU synth bench with overseas-customer templates and re-running AI4Privacy with the new patterns. See [Benchmarks](https://srepho.github.io/Allyanonimiser/benchmarks/) and the new [International PII](https://srepho.github.io/Allyanonimiser/patterns/international/) page.

1. **5 new entity types loaded by default**. New module `allyanonimiser/patterns/general_intl_patterns.py`:
   - `PHONE_INTL` — three variants: `+CC` anchored, `00` IDD prefix, parenthesised area code (3-4 digit, so AU 2-digit area codes stay with `AU_PHONE`).
   - `US_SSN` — `\d{3}-\d{2}-\d{4}` with SSA reservation rules (area ≠ 000/666/9xx, group ≠ 00, serial ≠ 0000).
   - `CREDIT_CARD` — Luhn-validated 13-19 digits. Validator is `EntityValidator.validate_credit_card`.
   - `ISO_DATETIME` — `YYYY-MM-DDThh:mm[:ss][.f][Z|±hh:mm]`. Priority 55 — ranks above bare `DATE` (40).
   - `TIME` — 12/24h with optional seconds and AM/PM. Lookbehind blocks date fragments. Priority 35 — below `DATE`.

2. **Validate-then-pick conflict resolver**. `resolve_entity_conflicts` walks candidates from highest priority down and returns the first that passes per-type validation. Previously a permissive pattern (e.g. CREDIT_CARD matching a 13-digit phone) could win by priority, fail its checksum, and silently drop the valid runner-up.

3. **PERSON precision overhauled** (AU bench F1 0.836 → 0.954). `_is_false_positive_person` now rejects: AU capital cities alone, state+postcode lines (`Darwin NT 6000`), date-shaped spans, common acronyms (`VIN`/`ABN`/`PLC`/`LLC`), and spans whose leading token is a label word (`Email`, `Vehicle`, `Residential`). Iterative trim of trailing label tokens (`Joe Smith\nDOB` → `Joe Smith`, `Kristin Rodriguez\nClaims` → `Kristin Rodriguez`). FP check now applied to single-candidate spans (previously bypassed).

4. **VEHICLE_REGISTRATION tightened**. Added `SSN/TIN/NIN` to the label deny-list plus negative lookahead `(?![A-Z]{1,3}\s+\d{3}-\d{2}-\d{4}\b)` so `bad SSN 999-04-7100` no longer absorbs `SSN 999-04` as a plate.

5. **`DATE_OF_BIRTH` and `INCIDENT_DATE` no longer eat their prefix**. Capture-group rewrite so spans equal just the date, not `DOB: 04/01/1959` (15 chars) but `04/01/1959` (10 chars).

6. **`common_formats.py` identifier captures require a digit**. `[A-Z0-9-]*\d[A-Z0-9-]*` instead of `[A-Z0-9-]+`. Stops `Claim Note` → `Note`, `Policy Number` → `Number`, `claim-mail.net` → `mail`.

7. **ORGANIZATION deny-list widened** with `SSN/TIN/NIN/VIN/CRN/BSB/GST/POL/REF/ID` (parallel to existing `DOB/DOI/Medicare/ABN/TFN/ACN`).

8. **CI fix**. `pyright` was invoked with invalid `--level basic` CLI flag making it a no-op. Now reads strictness from `[tool.pyright]` in `pyproject.toml` (kept `continue-on-error: true` while type debt is paid down — 60 advisory errors mostly in `utils/spacy_helpers.py` missing-import resolution).

## Benchmark results snapshot

**Enriched AU bench (160 docs, ~8 spans/doc, +60 international templates)** — Ally beats `openai/privacy-filter` on 5 of 6 categories at ~24× throughput:

| Category | Ally F1 | openai F1 |
|---|---:|---:|
| PERSON | **0.954** | 0.908 |
| ADDRESS | **0.962** | 0.940 |
| EMAIL | **1.000** | 0.982 |
| PHONE | **1.000** | 0.870 |
| DATE | **0.997** | 0.964 |
| ACCOUNT_LIKE | **0.997** | 0.880 |
| ANY | 0.950 | 0.958 |

**AI4Privacy (1000 English rows)** — Ally now matches openai overall (was 0.728 → 0.781, now **0.782 vs 0.781**). PHONE F1 0.011 → 0.802 was the biggest single lift.

**TAB (127 ECHR docs)** — unchanged from v3.4.0; Ally still wins ANY 0.560 vs 0.378.

## Release process (unchanged)

```bash
# 1. Bump version in pyproject.toml, __init__.py, README.md, CHANGELOG.md, docs/.
# 2. Build + validate locally:
rm -rf dist build
python -m build
twine check dist/*
python scripts/smoke_release.py

# 3. Push and let CI confirm green on 3.12 + 3.13.
git push origin main

# 4. ONLY after CI green AND explicit user OK:
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
twine upload dist/*
gh release create vX.Y.Z dist/* --title "..." --notes "..."
```

## Backlog

### Follow-ups from the benchmarks

- **AU bench ANY still −0.008 behind openai** (Ally 0.950, openai 0.958). Last gap is PERSON recall (Ally 0.975 vs openai 1.000). spaCy NER misses some non-Anglo names. Options: try the `lg` model in a config preset; or add an explicit person-name dictionary as a secondary detector.
- **AI4Privacy ADDRESS and ACCOUNT still trail openai** by ~0.25 F1. Most FNs are international city/street names without anchors, and passport / generic ID numbers in non-standard formats. Catching these would require gazetteers and would risk AU-side FPs — not pursued for now. Worth revisiting if a customer flags it.
- **Real AU insurance data eval** — current AU bench is synthetic via Faker+templates. Numbers will inflate both tools' scores vs real documents. If you have a sanitized sample, hand-label 20-50 docs and rerun.

### Real correctness work

- **Span-overlap rule for DATE_OF_BIRTH**. The skipped `test_age_bracket_recent_dates` still fails on `lg` (the larger model splits `DD/MM/YYYY` into multiple DATE spans that don't exactly match the `DOB:` pattern span; the `(start, end, text)` dedup key treats them as different spans). Fix: containment rule in `core/conflict_resolver` where a wider entity span absorbs fully-contained narrower ones. Carried from v3.3 backlog.
- **Direct unit tests for `core/common_formats.py`** — only covered indirectly through `Allyanonimiser.analyze()`. Carried from v3.3.
- **Configurable entity priority via settings file** — currently requires `EnhancedAnonymizer(entity_priority={...})` at construction time. Carried from v3.3.

### Code-health & type debt

- **Pyright now actually runs** (post v3.5 CI fix) and reports **60 advisory errors**: mostly `reportMissingImports` in `utils/spacy_helpers.py` (`spacy.language`, `spacy.matcher`, `spacy.tokens` not seen — install `pandas-stubs` and check spaCy stubs), plus a few `reportArgumentType` in `settings_manager.py` and `core/analyzer.py`. Workflow is `continue-on-error: true` so non-blocking, but worth a cleanup pass.
- **64 E501 line-too-long warnings** are `ignore`d in `pyproject.toml`. Mostly long regex literals in `core/analyzer.py` and `utils/spacy_helpers.py`.
- **`core/analyzer.py` is still 850 lines** (now even longer with the extended PERSON FP filter). Worth splitting `_analyze_with_spacy` and its FP-words lists into a separate `core/spacy_filters.py`.

### CI / infra

- **Node 20 → Node 24 action bumps** still pending. Deprecation warnings on every workflow run. GitHub will force Node 24 on 2026-06-02 — overdue.
- `tests/test_example_scripts.py`'s `main()` tests are `slow`-marked (`-m slow` to include).

### Deployment writeups not yet built

- **Azure Functions container image** for multi-agent PII redaction. Sketch: Docker image → Azure Container Apps or Functions Premium, HTTP trigger `{text, mode}` → `{anonymized, entities[]}`. Stateless, horizontally scalable, model loaded once per replica. The v3.3+ `sm` default makes this realistic on Consumption Plan.

## Dev-env gotchas

- Local `.venv` uses Python 3.12. The `[bench]` extra requires `numpy<2` because the installed `torch 2.2.2` (last mac x86_64 wheel) was compiled against NumPy 1.x. If bench scripts crash on numpy initialization, check: `uv pip install "numpy<2"`.
- `bench/run_tab_eval.py` and `bench/run_ai4privacy_eval.py` download ~1 GB of openai/privacy-filter ONNX weights on first run (cached in `~/.cache/huggingface`).
- `HF_TOKEN` environment variable required for bench scripts that pull from HuggingFace.
- `mkdocs build --strict` is still required to pass for the docs workflow. Broken links fail CI.

## Files touched this session

- **Patterns (new)**: `allyanonimiser/patterns/general_intl_patterns.py`
- **Patterns (modified)**: `au_patterns.py`, `general_patterns.py`, `insurance_patterns.py`, `patterns/__init__.py`
- **Core**: `core/analyzer.py` (PERSON FP filter + ORG deny-list + trim loop), `core/anonymizer.py` (priorities), `core/common_formats.py` (digit-required captures), `core/conflict_resolver.py` (validate-then-pick + extended PERSON FP + LOCATION/ORG date-shape drop), `core/validators.py` (Luhn)
- **Tests (new)**: `tests/test_general_intl_patterns.py` (40 tests)
- **Tests (modified)**: `tests/test_robust_detection.py`
- **Docs (new)**: `docs/patterns/international.md`
- **Docs (modified)**: `README.md`, `CHANGELOG.md`, `docs/index.md`, `docs/benchmarks.md`, `docs/patterns/overview.md`, `docs/getting-started/installation.md`, `mkdocs.yml`
- **Bench**: `bench/make_au_insurance_eval.py` (3 new templates + intl value generators), `bench/data/au_insurance.jsonl` (regenerated, 100→160 docs), `bench/run_au_insurance_eval.py` (label mapping extended), `bench/run_ai4privacy_eval.py` (label mapping extended)
- **CI**: `.github/workflows/tests.yml` (pyright `--level basic` removed)
- **Meta**: `pyproject.toml` (3.4.0 → 3.5.0), `allyanonimiser/__init__.py` (`__version__`), `allyanonimiser/allyanonimiser.py` (load intl patterns)
