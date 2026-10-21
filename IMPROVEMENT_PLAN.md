# Package improvement plan

Prepared 2026-09-05 against local commit `92aaf9a` (package metadata: 3.5.1).
Scope: implementation planning; no runtime changes or release actions.

## Implementation progress — 2026-09-05

The first correctness batch was pushed as `ce337c8`; all five GitHub workflows passed. No package release was made.

- Item 1: replaced collection with ordered Polars batches, corrected counts and absolute row indices, incrementally wrote entity output, handled header-only files and relative paths, validated chunk sizes and path collisions, and disabled unbounded session-report accumulation. Real CSV tests replace fabricated streaming tests.
- Item 2: stream and DataFrame anonymization now reuse detections with the same prepared text and per-call threshold. DataFrame batching remains a later performance improvement.
- Compatibility: stream extra now requires Polars >= 1.37.0; CSV columns default to strings. Documentation and changelog explain the output contract and partial-file behavior.
- Validation: 318 default tests passed, 7 opt-in tests deselected; Ruff clean. The targeted streaming/parity tests also pass with Polars 1.37.0. A CI job now exercises that minimum version without NER models.
- Memory observation using `bench/check_stream_memory.py`, pattern-only mode, default caches, chunk size 500: 2,000 rows / 1.75 MiB input used 285.64 MiB peak RSS (3.15 s); 20,000 rows / 17.51 MiB input used 337.06 MiB (31.02 s). Both runs had exact row/entity counts. This is a local measurement, not a universal memory bound; larger-scale and NER measurements remain useful follow-up.
- Configuration batch (item 3): implemented complete live regex snapshots, analyzer settings, priorities, version validation, safe serialization checks, and JSON/YAML behavior round trips. Existing per-call operator/score-adjustment semantics are retained and documented. Factory arguments explicitly override saved model/cache settings. Legacy unversioned files still load, and patterns in them now register correctly.
- Configuration validation: 333 default tests passed, 7 deselected; Ruff and strict documentation build passed. Pyright remains advisory (55 errors in the local check); this batch does not undertake the type backlog.
- Operational controls (item 4): implemented opt-in `minimal_output` across facade, DataFrame, CSV and streaming outputs; suppressed session reporting and disabled/cleared analyzer caches. Added strict requested-model NER loading through `require_spacy_model`, with JSON/YAML persistence and explicit factory overrides. Existing defaults and hash operators remain unchanged.
- Operational-controls validation: 357 default tests passed, 7 opt-in tests deselected; Ruff and strict documentation build passed. New regressions cover sentinel absence in returned/file outputs, report suppression, caches, empty/null data, configuration reload, and requested/fallback/missing-model behavior. These changes are local and unreleased.
- Remaining: optional DataFrame batching, larger/NER memory measurements, and items 5–6; keyed pseudonymization remains separate optional scope.

## Verified baseline

- Default local suite: **301 passed, 7 deselected** (`.venv/bin/python -m pytest -q`). Slow and performance suites were not run.
- Ruff: clean for `allyanonimiser/` and `tests/`.
- Real CSV reproduction with installed Polars 1.42.1, pattern-only mode, two rows, `chunk_size=1`, and `csv_options={}`: `stream_from_file()` raises `AttributeError: 'Series' object has no attribute 'columns'`.
- Settings export reproduction: a custom pattern is absent from the exported JSON; only its count and type appear in metadata.
- Existing CI already covers Python 3.12/3.13, stream dependencies, lint, coverage, distribution builds, and an sdist smoke check. Extend these checks instead of duplicating them.
- Remote branches, published releases, and external dependency support were not checked. July handoff notes are historical context, not current release evidence.

## 1. Repair real streaming and its tests — highest priority

Evidence: `allyanonimiser/io/stream_processor.py:187` iterates over `lf.collect(streaming=True)`. The collected DataFrame iterates as columns, not row batches. Collection also materializes the result. Several tests in `tests/test_stream_processor.py` construct expected output directly or substitute the stream rather than exercising file ingestion.

Implementation:

- Replace collection with an actual bounded row-batch reader; verify the chosen API against supported dependency versions before implementation.
- Define a stable chunk result containing row count, processed data where applicable, and entity records. File-output mode currently yields entities without the DataFrame, while `process_large_file()` counts only DataFrames.
- Maintain absolute source row identifiers across chunks; `_process_chunk()` currently restarts row indices at zero.
- Write entity records incrementally; `process_large_file()` currently accumulates them until the end.
- Support output filenames without directory components, validate positive chunk sizes, reject conflicting input/output paths, and close resources on failure or early generator termination.
- Preserve CSV string values, nulls, quoting, and multiline fields explicitly.

Acceptance:

- Unmocked CSV-to-output tests process 23 rows with chunk size 5, preserve row order and all rows, and report exactly 23 processed rows with and without entity export.
- Test both default CSV options and explicit options, zero-entity input, header-only input, multiple text columns, relative output paths, and malformed input.
- A separate subprocess memory benchmark shows bounded memory as input size grows at fixed chunk size, with caches/report retention controlled and the baseline recorded.

Estimated effort: 3–5 engineering days.

## 2. Make detection and replacement use the same results

Evidence: both `io/dataframe_processor.py` and `io/stream_processor.py` apply `min_score_threshold` during detection, then call anonymization without those results. The second detection uses the analyzer's configured threshold. The facade already supports `analysis_results`, and `process()` already uses it.

Implementation:

- Prepare each text once and carry that exact text and its detections through replacement and entity reporting.
- Reuse `analysis_results` in tabular processors, taking care that acronym expansion changes offsets.
- Use bounded batch analysis for DataFrames where it improves throughput; avoid repeating detection per cell.

Acceptance:

- Parameterized single-text, DataFrame, CSV, and stream tests agree on detected spans and replacements at thresholds above and below the instance default.
- Acronym expansion, duplicate text, nulls, multiple columns, and empty detections preserve the same contract.
- Verify one detection per prepared text, and retain existing per-call state-isolation tests.

Estimated effort: 2–3 days; coordinate with item 1.

## 3. Make exported configuration reproduce behavior

Evidence: `utils/settings_manager.py:export_config()` exports pattern metadata but omits pattern definitions and entity score adjustments. Current export tests check selected fields, not equivalent detection behavior after reload.

Implementation:

- Define a versioned schema covering patterns, active entities, thresholds/score adjustments, operators, model selection, acronyms, and processing options.
- Export effective live configuration, including patterns added through the public API, rather than only the settings manager's initial state.
- Validate entity names, operator names, regex syntax, and numeric ranges with actionable errors.
- Document serialization limits for nonserializable custom behavior; fail explicitly rather than silently losing it.
- Preserve loading of existing configurations with documented defaults.

Acceptance:

- Export/reload JSON and YAML into a fresh instance and obtain identical detections and replacements on a fixture corpus including custom patterns and score adjustments.
- Unknown schema versions and invalid settings produce useful errors.
- Existing configuration fixtures continue to load.

Estimated effort: 2–4 days.

## 4. Add explicit controls for sensitive output and model availability

Evidence: anonymization responses include `original_text` and original entity values; reports retain original entity values; tabular output retains original columns alongside anonymized columns. Analyzer caches use raw input text as keys. Model loading can warn and continue in pattern-only mode when NER models are absent.

Implementation:

- Add an opt-in minimal-output profile that omits original text/entity values, drops source text columns from exported files, disables raw-value reports, and sets an explicit cache policy.
- Expose a strict model requirement so a deployment requiring NER can fail at initialization instead of continuing with reduced detection.
- Document current defaults and which outputs retain source data. Preserve default API behavior initially; consider default changes only with a migration path.
- Treat the current unkeyed, truncated hash operator as a separate compatibility contract. If cross-record pseudonyms are needed, design a keyed operator with explicit key ownership and rotation.

Acceptance:

- Synthetic sentinel strings are absent from the minimal profile's returned structures, written files, and retained report records.
- Tests cover requested model present, fallback model present, neither present, and explicitly selected pattern-only mode.
- Existing callers retain their current output shape unless they select the new profile.

Estimated effort: 3–5 days; keyed pseudonymization is optional follow-up scope.

## 5. Turn benchmarks into detection regression gates

Evidence: the repository has a seeded AU synthetic corpus and comparison runners, but the standard test workflow does not gate corpus-level recall. `bench/README.md` describes 100 rows while the main README describes 160 documents.

Implementation:

- Add a local Ally-only benchmark mode requiring neither competitor weights nor external dataset downloads.
- Record corpus identity, configuration, model/dependency versions, seed, per-entity precision/recall, full-span coverage, and throughput.
- Establish measured regression tolerances, with special attention to completely missed identifiers and names; avoid selecting arbitrary F1 targets before measuring a baseline.
- Add held-out variations for typos, OCR noise, Unicode, ambiguous labels, adjacent entities, and overlap boundaries.
- Later, evaluate an access-controlled, human-labelled sample of representative claim notes. Do not commit private records to the repository.
- Generate documentation tables from versioned summaries and reconcile corpus counts.

Acceptance:

- CI runs a deterministic offline corpus check and reports entity-level regressions clearly.
- Dataset generation and evaluation splits are documented, and held-out examples remain separate from tuning fixtures.
- Accuracy gates are separate from scheduled throughput/memory checks to avoid hardware-sensitive PR failures.

Estimated effort: 2–4 days for the harness; representative-data annotation is separate and depends on data availability.

## 6. Strengthen compatibility and maintainability incrementally

Evidence: pyright is advisory (`continue-on-error: true`); distribution validation focuses on Python 3.12; declared runtime dependency ranges are broad. No current pyright error count was measured in this review.

Implementation:

- Measure the current type-error baseline and fix public result/configuration types and optional model handling first. Introduce a blocking gate for cleaned modules, then expand it.
- Exercise installed artifacts outside the source tree on both supported Python versions; extend the existing smoke script.
- Add minimum-supported and freshly resolved dependency checks, including the stream extra and missing-model behavior.
- Decide Python version expansion from actual consumer needs and verified dependency compatibility. Do not widen support solely because an old handoff proposed it.
- Benchmark import/startup cost before considering a lightweight pattern-only installation extra.

Acceptance:

- Public interfaces have consistent types, and agreed type-check scope blocks regressions.
- Wheel/sdist smoke tests load the installed artifact and exercise detection plus replacement on each supported interpreter.
- Every advertised dependency range and Python version has an explicit validation strategy.

Estimated effort: 2–4 days for an initial bounded pass.

## Suggested delivery order

1. **Correctness batch:** items 1 and 2 as small coordinated PRs. Start with failing real-I/O and threshold-parity regressions.
2. **Configuration batch:** item 3, with round-trip behavior tests and migration notes.
3. **Operational controls:** item 4, introduced as opt-in behavior.
4. **Ongoing assurance:** items 5 and 6, with the offline regression harness pulled earlier if detection logic changes.

Estimates are rough implementation effort, exclude review and release time, and should be revised after the first failing regression tests. Each batch should pass the default suite and relevant targeted checks; choose version numbers only after checking current release state and compatibility impact.
