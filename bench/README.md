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

## AU challenge corpus

`make_au_challenge.py` generates a harder, independent test set. The original
corpus was used while fixing detection, so it can no longer show gains.

```bash
python bench/make_au_challenge.py                          # regenerate (deterministic)
python bench/eval_ally.py --corpus challenge-dev --show-failures 30
python bench/eval_ally.py --corpus challenge-test          # held out: read aggregates only
```

**Contents.** 480 synthetic insurance documents in 12 template families, none
shared with the original corpus. Identifiers are generated fresh with valid
checksums: TFN, ABN, ACN, Medicare and Luhn cards. It adds driver's licences,
passports, BSB and account numbers, Centrelink CRNs, and insurer-style policy
and claim formats. Names come from a diverse bank with accents, apostrophes,
hyphens and multi-part surnames.

**Noise.** Each gold span records a `variant` naming its surface form, such as
`AU_TFN/hyphen`, `PERSON/surname_first`, `AU_ADDRESS/multi_line` or
`AU_PHONE/spoken`. Span-level noise is appended as `+ocr` or `+nbsp`. Documents
carry `tags` for lowercase text, misspelt labels, OCR substitutions and
non-breaking spaces. The evaluator reports coverage by variant and by noise, and
lists the weakest variants.

**Splits and protocol.**

| File | Families | Use |
|---|---|---|
| `data/au_challenge_dev.jsonl` | 8 families, 320 documents | Development. Inspect failures and tune rules here. Gated in CI, pattern-only. |
| `data/au_challenge_test.jsonl` | 4 held-out families, 160 documents | Report aggregate results at release time. Do not tune against its individual failures. |

The held-out families are a medical statement, a complaint letter, a travel
claim and a tabular export. Every label in them also appears in development.
`data/au_challenge_manifest.json` records the seed, Faker version, hashes and
counts. `tests/test_challenge_corpus.py` checks checksums against the package's
validators, offsets, split separation, the manifest hashes, and exact
regeneration when the Faker version matches.

**Results.** Starting point is v3.6.0 plus the first unreleased detection fixes. "After" is after the challenge-dev fixes; the test split was not used for tuning.

| Split | Configuration | Fully covered, start | After | Docs exposing PII, start | After |
|---|---|---|---|---|---|
| dev | pattern-only | 67% | 93% | 305 / 320 | 113 / 320 |
| dev | `en_core_web_sm` | 79% | 94% | 271 / 320 | 106 / 320 |
| dev | `en_core_web_lg` | 82% | 95% | 261 / 320 | 87 / 320 |
| test | pattern-only | 68% | 86% | 158 / 160 | 81 / 160 |
| test | `en_core_web_sm` | 73% | 85% | 145 / 160 | 74 / 160 |
| test | `en_core_web_lg` | 74% | 85% | 139 / 160 | 71 / 160 |

Over-masking with spaCy is around 10% on dev, mostly organisation names, clock
times, dollar amounts and invoice numbers, which the package masks by design.

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
- `make_au_challenge.py` — Generator for the AU challenge corpus (dev and held-out test splits)
- `data/au_challenge_{dev,test}.jsonl`, `data/au_challenge_manifest.json` — The challenge corpus and its manifest
- `baselines/au_challenge_dev_patterns.json` — Pattern-only challenge-dev baseline used by the gate

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
