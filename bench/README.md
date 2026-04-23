# Allyanonimiser Benchmarks

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
python bench/run_au_insurance_eval.py                     # 100 synth AU insurance docs
```

Results land in `bench/results_*.json` (gitignored — regenerate on demand).

## Files

- `run_tab_eval.py` — Text Anonymization Benchmark (ECHR legal text)
- `run_ai4privacy_eval.py` — AI4Privacy open-pii-500k (general PII, multi-lingual)
- `run_au_insurance_eval.py` — Synthetic AU insurance (the primary use case)
- `make_au_insurance_eval.py` — Faker-based synthesizer for the AU eval set
- `data/au_insurance.jsonl` — Checked-in synthetic eval data (100 rows)

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
