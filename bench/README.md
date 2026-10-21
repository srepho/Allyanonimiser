# Allyanonimiser Benchmarks

## Offline evaluation and regression gate

`eval_ally.py` evaluates Allyanonimiser alone on the synthetic AU insurance
corpus. It needs only the core package: no competitor weights, network access
or dataset downloads.

```bash
python bench/eval_ally.py                                        # pattern-only, all 160 docs
python bench/eval_ally.py --spacy-model en_core_web_lg --split test
python bench/eval_ally.py --show-failures 20                     # list missed/partial/mistyped spans
python bench/eval_ally.py --baseline bench/baselines/au_insurance_patterns.json
```

It scores what `anonymize()` actually replaced, not raw detections. For each
gold span it records whether the span was fully covered, partially exposed or
entirely missed, and whether a correct entity type covered it. It also reports
documents with any exposed PII, over-masking of non-PII text, character-level
P/R/F1 per category, and cold-start and warm throughput.

Postcodes are masked during evaluation by default so detector coverage is
measured cleanly. `--keep-postcode` uses the library default, which leaves
postcodes visible and so counts them as exposed.

**Receipts.** `--out` writes a JSON receipt recording the corpus hash, split,
git revision, configuration, package and model versions, CPU and timings.

**Gate.** `tests/test_detection_regression.py` runs the pattern-only evaluation
in the normal test suite and fails if any gold label gains missed or partial
entities, loses correctly typed coverage, more documents expose PII, or
over-masking rises. Timing is recorded but never gated. When a change improves
results, refresh the baseline deliberately:

```bash
python bench/eval_ally.py --out bench/baselines/au_insurance_patterns.json
```

Pattern-only mode is gated because it is deterministic. spaCy results differ
between `en_core_web_sm` and `en_core_web_lg`, so compare model runs against
receipts made with the same model.

**Splits.** Each row carries a `family` naming the template that generated it.
`--split test` holds out the `expat_claim` and `payment_record` families;
`--split dev` is the other six. Every label in the test families also appears in
dev, so rules tuned on dev can be checked on unseen templates.

**Limits.** The corpus is synthetic and templated, with 20 documents per family.
It catches regressions; it does not establish accuracy on real claim notes.

## Head-to-head comparisons

Head-to-head evaluations of Allyanonimiser against `openai/privacy-filter` on three
PII datasets. Scoring is character-level binary masking (precision/recall/F1) per
category; see each `run_*.py` script for label mappings.

## Setup

```bash
uv pip install -e ".[bench]"
```

This pulls `faker`, `datasets`, `huggingface_hub`, `tokenizers`, and
`onnxruntime` on top of the core package. A `HF_TOKEN` is required for the TAB
and AI4Privacy downloads.

## Running

```bash
# ~4 min on CPU — downloads ~1GB of ONNX weights first time
python bench/run_tab_eval.py                              # TAB dev (127 ECHR docs)
python bench/run_ai4privacy_eval.py --n 1000              # AI4Privacy 500k, English
python bench/make_au_insurance_eval.py                    # regenerate synth AU data
python bench/run_au_insurance_eval.py                     # 160 synth AU insurance docs
```

Results land in `bench/results_*.json` (gitignored — regenerate on demand).

## Files

- `run_tab_eval.py` — Text Anonymization Benchmark (ECHR legal text)
- `run_ai4privacy_eval.py` — AI4Privacy open-pii-500k (general PII, multi-lingual)
- `run_au_insurance_eval.py` — Synthetic AU insurance (the primary use case)
- `make_au_insurance_eval.py` — Faker-based synthesizer for the AU eval set
- `data/au_insurance.jsonl` — Checked-in synthetic eval data (160 rows, 8 template families)
- `eval_ally.py` — Offline Ally-only evaluator and regression gate
- `au_labels.py` — Label mappings and split definitions shared by the AU runners
- `baselines/au_insurance_patterns.json` — Pattern-only baseline receipt used by the gate

## Model comparison notes

`openai/privacy-filter` is a 1.5B-parameter MoE token classifier (Apache 2.0).
We use the q4 ONNX variant via `onnxruntime` so no GPU or recent torch is
required. CPU inference is ~1-2 seconds per document; Allyanonimiser is
~25× faster per document on the same hardware.

The TAB and AI4Privacy evals surface a taxonomy-mismatch reality: each dataset
defines "PII" differently (legal quasi-identifiers vs multilingual person/
address), and no dataset covers AU-specific entities (TFN, Medicare, ABN).
`run_au_insurance_eval.py` is the only one that exercises Allyanonimiser's
primary domain.
