# Next Session

## Current State — v3.3.0 shipped (2026-04-15)

- **PyPI**: https://pypi.org/project/allyanonimiser/3.3.0/
- **GitHub release**: https://github.com/srepho/Allyanonimiser/releases/tag/v3.3.0
- **Tag**: `v3.3.0`
- **Docs site**: https://srepho.github.io/Allyanonimiser/ (now auto-deploys on every push to main via `.github/workflows/docs.yml`)
- **CI**: all workflows green on Python 3.12 and 3.13 (Tests, Release Check, Test Coverage, Package Checks, Deploy Docs)
- **Version history on PyPI**: 3.3.0 (latest), 3.1.2 (unyanked fallback), 3.1.1 (yanked — had `expand_acronyms` regression)

## Headline changes in v3.3.0

1. **Default spaCy model switched from `lg` → `sm`** (587 MB → 44 MB, ~2-5s cold start → ~0.5s). Pattern detection (TFN/ABN/Medicare/AU_PHONE/EMAIL/dates) is identical; NER recall on `PERSON`/`LOCATION`/`ORG` drops. Constants `SPACY_MODEL_FAST` and `SPACY_MODEL_ACCURATE` exported at package root.
2. **TFN/ABN checksum validation now enforced on the conflict-resolution winner** (previously only validated uncontested spans, so invalid IDs slipped through when a second recognizer competed for the same span).
3. **Pre-release smoke gate**: `scripts/smoke_release.py` + `.github/workflows/release-check.yml` build the sdist, twine-check it, install into a scratch venv, install `en_core_web_sm`, and run 7 in-venv assertions including the default-model contract and `expand_acronyms` wiring. Would have caught v3.1.1's silent regression.
4. **Docs cleanup**: 17 "Coming soon..." stubs deleted; nav reduced to pages with real content; GH Pages deploy workflow added (site previously drifted between manual `mkdocs gh-deploy` invocations).
5. **CI now actually green**: `tests.yml` had been silently red on the lint step for 8+ consecutive commits before v3.2.0. Ruff `E501` is now `ignore`d (64 preexisting line-too-long warnings); `E402` was fixed.

## Release process (enforced)

Never `twine upload` without the smoke script. Full runbook:

```bash
# 1. Bump version in pyproject.toml, __init__.py, README.md, CHANGELOG.md.
# 2. Commit, then build + validate locally:
rm -rf dist build
python -m build
twine check dist/*
python scripts/smoke_release.py    # must pass before any push

# 3. Push and let CI (Tests + Release Check) confirm on 3.12 + 3.13.
git push origin main

# 4. ONLY after CI green AND explicit user OK:
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
twine upload dist/*
gh release create vX.Y.Z --title "..." --notes "..."
```

## Backlog

### Real correctness work
- **Span-overlap rule for DATE_OF_BIRTH**. The skipped `test_age_bracket_recent_dates` fails on `lg` (the larger model splits `DD/MM/YYYY` into multiple DATE spans that don't exactly match the `DOB:` pattern span; the `(start, end, text)` dedup key treats them as different spans, so DATE_OF_BIRTH gets overridden by two `<DATE>` replacements). Fix: containment rule in `core/conflict_resolver` where a wider entity span absorbs fully-contained narrower ones.
- **Direct unit tests for `core/common_formats.py`** — only covered indirectly through `Allyanonimiser.analyze()`. The companion module `conflict_resolver` got 13 direct tests in v3.2.0; common_formats is next.
- **Configurable entity priority via settings file** — currently requires `EnhancedAnonymizer(entity_priority={...})` at construction time.

### Code-health
- 64 E501 line-too-long warnings are `ignore`d in `pyproject.toml`. Mostly long regex literals in `core/analyzer.py` and `utils/spacy_helpers.py`. A focused style pass would let the rule be re-enabled.
- `core/analyzer.py` is still 850 lines — `_analyze_with_spacy` and `_analyze_with_patterns` are the remaining large blocks if a further split is wanted.

### CI / infra
- **Node 20 → Node 24 action bumps.** Deprecation warnings on every workflow run: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`, `actions/deploy-pages@v4`. GitHub will force Node 24 on 2026-06-02. Safe mechanical change.
- `tests/test_example_scripts.py`'s `main()` tests are marked `slow` (`-m slow` to include) because the CSV example does ~109s of I/O. Could be faster with a slimmer demo fixture.

### Deployment writeups we talked about but didn't build
- **Azure Functions container image** for multi-agent PII redaction. Sketch: Docker image → Azure Container Apps or Functions Premium, HTTP trigger `{text, mode}` → `{anonymized, entities[]}`. Stateless, horizontally scalable, model loaded once per replica. The v3.3.0 `sm` default makes this realistic on Consumption Plan.

## Dev-env gotchas
- Local `.venv` silently drifted from Python 3.12 → 3.13 during one session (unclear cause; possibly an `uv` auto-resolution). Check `python --version` after dependency operations.
- `uv venv` + `python -m spacy download` doesn't actually install the model — uv's pip wrapper audits the cache without copying into site-packages. The smoke script works around this by installing the model directly via the spaCy releases wheel URL. If you hit this elsewhere, do the same.
- `mkdocs build --strict` is required to pass for the docs workflow. Any broken link in `docs/` will fail CI.
