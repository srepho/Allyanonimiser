# Next Session

## Current State — v3.4.0 shipped (2026-04-24)

- **PyPI**: https://pypi.org/project/allyanonimiser/3.4.0/
- **GitHub release**: https://github.com/srepho/Allyanonimiser/releases/tag/v3.4.0 (wheel + sdist attached)
- **Tag**: `v3.4.0` → commit `6b5abd0`
- **Docs site**: https://srepho.github.io/Allyanonimiser/ — new `/benchmarks/` page wired into nav
- **CI**: all 5 workflows green on Python 3.12 (Tests, Release Check, Test Coverage, Package Checks, Deploy Docs). Test Coverage and Package Checks had been silently red on v3.3.0 — fixed in this release.
- **PyPI version history**: 3.4.0 (latest), 3.3.0, 3.1.2 (unyanked fallback), 3.1.1 (yanked — had `expand_acronyms` regression)

## Headline changes in v3.4.0

Everything in this release was surfaced by a head-to-head evaluation against [`openai/privacy-filter`](https://huggingface.co/openai/privacy-filter) (a 1.5B-parameter MoE token classifier, Apache 2.0) on three datasets. See the new [Benchmarks](https://srepho.github.io/Allyanonimiser/benchmarks/) page.

1. **AU_ADDRESS over-match fixed**. Old patterns let narrative prose like *"2007 the Court decided to give notice of the application to the Government"* produce a 74-char false-positive span because `Court` is a street suffix. Two loose fallback patterns deleted; remaining two patterns (strict title-case + case-tolerant via `(?i)`) are anchored by state+postcode. On TAB: ADDRESS F1 0.131 → 0.425; FP chars 39,156 → 7,035 (−82%).
2. **AU_POSTCODE over-match fixed**. Bare `\b[1-9]\d{3}\b` pattern was matching years in dates (`15/03/2023` → `2023`) and dollar amounts (`8500`). Now requires state abbreviation or `postcode`/`post code`/`postal code` label via fixed-width lookbehind. On AU-insurance: ADDRESS FP chars 981 → 49 (−95%); ADDRESS F1 0.839 → 0.980.
3. **DATE validator expansion**. Added 11 patterns for spaCy's natural-language DATE outputs (`March 2024`, `next Monday`, `Q1 2024`, `FY24`, `yesterday`, `the 1990s`, `10:30am`, etc.) so they don't fall through to `'unknown'` and get rejected. Phone-prefix check reordered before generic 4-digit branch so `"0415"` is classified correctly. Conflict resolver reject list expanded with `phone_fragment`, `number`, `postcode`, `duration`.
4. **INSURANCE_CLAIM_NUMBER** widened to accept `CLM` prefix alongside `CL`/`C`.
5. **Benchmark suite** — new `bench/` directory with three eval scripts, a Faker-based synth AU-insurance generator, and reproduction instructions. Installable via `pip install "allyanonimiser[bench]"` (pulls `faker`, `datasets`, `huggingface_hub`, `tokenizers`, `onnxruntime`).
6. **CI fixed**. `coverage.yml` had unquoted `[3.10]` which YAML parses as `3.1` → failed on every push for weeks. `package.yml` referenced `tests/run_package_tests.py` which was deleted in the v3.0.0 restructure. Both fixed.

## Benchmark results snapshot

**AU insurance (100 synthetic docs, ~12 spans/doc)** — Allyanonimiser beats openai/privacy-filter on 4 of 6 categories at ~25× throughput:

| Category | Ally F1 | openai F1 |
|---|---:|---:|
| PERSON | 0.836 | 0.855 |
| ADDRESS | **0.980** | 0.918 |
| EMAIL | **1.000** | 0.982 |
| PHONE | **1.000** | 0.837 |
| DATE | 0.863 | 0.991 |
| ACCOUNT_LIKE | **0.877** | 0.846 |
| Overall ANY | 0.920 | 0.943 |

**AI4Privacy (1000 English rows)** — openai wins on international/multilingual PII (Ally's AU-specific patterns don't cover US/EU formats): Ally ANY 0.729 vs openai 0.781. Ally still wins EMAIL (0.990 vs 0.915).

**TAB (127 ECHR docs)** — Ally wins overall via blanket recall: ANY 0.560 vs 0.378; DATE F1 0.904 vs 0.459.

## Release process (unchanged from v3.3)

Same runbook — never `twine upload` without the smoke script and explicit user OK:

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

- **Ally PERSON precision on AU synth (0.732)** — 560 FP chars. spaCy NER mislabels organization and street fragments as PERSON. Candidates: filter spans ending in street suffixes (partially done in `_is_false_positive_person`), extend `_STREET_SUFFIXES`, or add an explicit org-name detector in front.
- **Ally DATE FP on AU synth still 380 chars** despite the validator tightening. Worth another pass with a small set of test cases sampled from the real FPs.
- **Re-run bench scripts after any future pattern change** — they live in `bench/` and report numbers against both tools side by side. Recommended as part of the release checklist for pattern-touching changes.
- **Real AU insurance data eval** — current AU bench is synthetic via Faker+templates. Numbers will inflate both tools' scores vs real documents. If you have a sanitized sample, hand-label 20–50 docs and rerun.

### Real correctness work (carried from v3.3 backlog)

- **Span-overlap rule for DATE_OF_BIRTH**. The skipped `test_age_bracket_recent_dates` fails on `lg` (the larger model splits `DD/MM/YYYY` into multiple DATE spans that don't exactly match the `DOB:` pattern span; the `(start, end, text)` dedup key treats them as different spans, so DATE_OF_BIRTH gets overridden by two `<DATE>` replacements). Fix: containment rule in `core/conflict_resolver` where a wider entity span absorbs fully-contained narrower ones.
- **Direct unit tests for `core/common_formats.py`** — only covered indirectly through `Allyanonimiser.analyze()`.
- **Configurable entity priority via settings file** — currently requires `EnhancedAnonymizer(entity_priority={...})` at construction time.

### Code-health

- 64 E501 line-too-long warnings are `ignore`d in `pyproject.toml`. Mostly long regex literals in `core/analyzer.py` and `utils/spacy_helpers.py`.
- `core/analyzer.py` is still 850 lines.
- `bench/` has `__pycache__` that's gitignored globally but shows up in `ls`. Consider `.gitignore`-ing bench-local if needed.

### CI / infra

- **Node 20 → Node 24 action bumps** still pending. Deprecation warnings on every workflow run. GitHub will force Node 24 on 2026-06-02.
- `tests/test_example_scripts.py`'s `main()` tests are `slow`-marked (`-m slow` to include).

### Deployment writeups not yet built

- **Azure Functions container image** for multi-agent PII redaction. Sketch: Docker image → Azure Container Apps or Functions Premium, HTTP trigger `{text, mode}` → `{anonymized, entities[]}`. Stateless, horizontally scalable, model loaded once per replica. The v3.3.0 `sm` default makes this realistic on Consumption Plan.

## Dev-env gotchas

- Local `.venv` uses Python 3.12. The `[bench]` extra requires `numpy<2` because the installed `torch 2.2.2` (last mac x86_64 wheel) was compiled against NumPy 1.x. If bench scripts crash on numpy initialization, check: `uv pip install "numpy<2"`.
- `bench/run_tab_eval.py` and `bench/run_ai4privacy_eval.py` download ~1 GB of openai/privacy-filter ONNX weights on first run (cached in `~/.cache/huggingface`).
- `HF_TOKEN` environment variable required for bench scripts that pull from HuggingFace.
- `mkdocs build --strict` is still required to pass for the docs workflow. Broken links fail CI.

## Files touched this session

- **Patterns**: `allyanonimiser/patterns/au_patterns.py`, `allyanonimiser/patterns/insurance_patterns.py`
- **Validation**: `allyanonimiser/core/validators.py`, `allyanonimiser/core/conflict_resolver.py`
- **Tests**: `tests/test_robust_detection.py` (+5 new test methods, 225 passing)
- **Docs**: `README.md` (Benchmarks section), `docs/benchmarks.md` (new), `docs/index.md`, `docs/getting-started/installation.md`, `mkdocs.yml`, `CHANGELOG.md`
- **CI**: `.github/workflows/coverage.yml`, `.github/workflows/package.yml`
- **Bench** (new): `bench/README.md`, `bench/run_tab_eval.py`, `bench/run_ai4privacy_eval.py`, `bench/run_au_insurance_eval.py`, `bench/make_au_insurance_eval.py`, `bench/data/au_insurance.jsonl`
- **Meta**: `pyproject.toml` (version bump, `[bench]` extra), `.gitignore` (bench outputs), `uv.lock`, `allyanonimiser/__init__.py`
