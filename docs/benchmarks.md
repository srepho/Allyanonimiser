# Benchmarks

Head-to-head evaluations of Allyanonimiser against [`openai/privacy-filter`](https://huggingface.co/openai/privacy-filter) — a 1.5B-parameter MoE token classifier released by OpenAI under Apache 2.0.

## Methodology

- **Scoring**: character-level binary masking. For each category, we compute precision / recall / F1 on which characters should be masked as PII and whether each tool actually masked them.
- **Runtime**: both tools on CPU. `openai/privacy-filter` via the int4-quantized ONNX build (`onnx/model_q4.onnx`) through `onnxruntime` — no torch or GPU required.
- **Reproducibility**: all scripts and the synthetic AU-insurance fixture live under `bench/` in the repo.

```bash
pip install "allyanonimiser[bench]"

python bench/run_tab_eval.py           # 127 ECHR docs
python bench/run_ai4privacy_eval.py    # 1000 English rows
python bench/run_au_insurance_eval.py  # 100 synth docs
```

## AU insurance (synthetic, 100 documents, ~12 PII spans/doc)

The primary use case. Templates cover claim notes, adjuster emails, underwriting forms, and medical reports, with Faker `en_AU` names, emails, and addresses plus published test-valid TFN / Medicare / ABN / ACN values.

| Category | Allyanonimiser F1 | openai/privacy-filter F1 |
|---|---:|---:|
| PERSON | 0.836 | **0.855** |
| ADDRESS | **0.980** | 0.918 |
| EMAIL | **1.000** | 0.982 |
| PHONE | **1.000** | 0.837 |
| DATE | 0.863 | **0.991** |
| Account-like IDs (TFN, Medicare, ABN, policy, VIN, etc.) | **0.877** | 0.846 |
| **Overall (any PII)** | 0.920 | **0.943** |

Allyanonimiser wins 4 of 6 categories. The AU-specific regex patterns (TFN/Medicare/ABN checksum validation, AU phone formats, state+postcode address anchoring) give perfect recall on formats that `openai/privacy-filter` was not trained to recognise as PII. `openai/privacy-filter` wins PERSON (broader training on English names) and DATE (stricter matching that our generalised DATE pattern trades off for recall on fuzzy forms).

Throughput: Allyanonimiser ran in 1.4s, `openai/privacy-filter` in 36s for the full 100-doc eval on the same CPU (~25× difference).

## AI4Privacy open-pii-masking-500k (English validation, 1,000 rows)

General-purpose multilingual PII corpus. Categories map cleanly to both tools' taxonomies but include non-AU phone and ID formats Allyanonimiser is not built for.

| Category | Allyanonimiser F1 | openai/privacy-filter F1 |
|---|---:|---:|
| PERSON | 0.653 | **0.836** |
| EMAIL | **0.990** | 0.915 |
| ADDRESS | 0.216 | **0.464** |
| PHONE | 0.011 | **0.829** |
| DATE | 0.490 | **0.642** |
| ACCOUNT | 0.074 | **0.700** |
| **Overall (any PII)** | 0.729 | **0.781** |

PHONE and ACCOUNT are near-zero because Allyanonimiser's regexes target AU mobile prefixes (`04xx`) and AU-specific IDs. Use Allyanonimiser if your data is AU-centric; use `openai/privacy-filter` (or a domain-tuned general detector) for multilingual/international PII.

## Text Anonymization Benchmark (TAB, 127 ECHR legal docs)

Real multi-annotator court cases from the European Court of Human Rights. TAB's `CODE` label covers legal case numbers (e.g. `40593/04`) that neither tool is designed for; `LOC` covers country/city names which `openai/privacy-filter` doesn't emit as `private_address`.

| Category | Allyanonimiser F1 | openai/privacy-filter F1 |
|---|---:|---:|
| PERSON | 0.761 | **0.805** |
| DATE | **0.904** | 0.459 |
| LOCATION | 0.424 | 0.000 |
| CODE | 0.012 | 0.077 |
| **Overall (any PII)** | **0.560** | 0.378 |

Allyanonimiser's DATE wins decisively because TAB `DATETIME` includes bare years (`1997`), relative phrases (`14 days`), and month/year combos — all of which the v3.4 validator now accepts. `openai/privacy-filter` is extremely precise on DATE (P=0.988) but narrow.

## How to read this

- **On Australian insurance data, Allyanonimiser is competitive with or beats a state-of-the-art 1.5B-parameter model** on 4 of 6 categories, at ~25× the throughput, with no GPU and no heavy ML dependencies.
- **On general multilingual PII, `openai/privacy-filter` is stronger** because its training data covers phone/address/account formats Allyanonimiser's regexes don't target.
- Use both if you need broad coverage — feed the same text to each and union the spans.

All tables are live against the most recent run of `bench/run_*.py`; re-run locally to verify against your Python / spaCy / onnxruntime versions.
