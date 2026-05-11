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

## AU insurance (enriched synthetic bench, 160 documents, ~8 PII spans/doc)

The primary use case. Templates cover claim notes, adjuster emails,
underwriting forms, medical reports, plus three new templates that mix
international PII into AU insurance contexts — expat customer claims,
payment records with credit cards on file, and business-travel claims with
US SSN, ISO timestamps, and intl phones. Values come from Faker `en_AU`
plus published test-valid TFN / Medicare / ABN / ACN, Luhn-valid credit
cards, and SSA-valid SSNs.

| Category | Allyanonimiser F1 | openai/privacy-filter F1 |
|---|---:|---:|
| PERSON | **0.954** | 0.908 |
| ADDRESS | **0.962** | 0.940 |
| EMAIL | **1.000** | 0.982 |
| PHONE | **1.000** | 0.870 |
| DATE | **0.997** | 0.964 |
| Account-like IDs (TFN, Medicare, ABN, policy, VIN, US_SSN, credit card, etc.) | **0.997** | 0.880 |
| **Overall (any PII)** | **0.950** | 0.958 |

Allyanonimiser wins **5 of 6 categories**. The AU-specific regex patterns
(TFN/Medicare/ABN checksum validation, AU phone formats, state+postcode
address anchoring) give perfect precision on AU formats. The international
patterns (PHONE_INTL, ISO_DATETIME, US_SSN, CREDIT_CARD with Luhn) cover
the expat/business-travel scenarios. `openai/privacy-filter` still leads
overall by 0.008 because of slightly better recall on multi-token PERSON
spans, but Ally is faster.

Throughput: on a 2019 Intel Mac (CPU only), Allyanonimiser ran in ~2.3s
and `openai/privacy-filter` in ~55s for the full 160-doc eval (~24×
difference). Numbers fluctuate ±10% across machines and Python versions;
re-run `bench/run_au_insurance_eval.py` locally to verify against your
environment.

## AI4Privacy open-pii-masking-500k (English validation, 1,000 rows)

General-purpose multilingual PII corpus. The international pattern additions
materially close the gap on the format-driven categories.

| Category | Allyanonimiser F1 | openai/privacy-filter F1 |
|---|---:|---:|
| PERSON | 0.653 | **0.836** |
| EMAIL | **0.990** | 0.915 |
| ADDRESS | 0.217 | **0.464** |
| PHONE | 0.802 | **0.829** |
| DATE | **0.719** | 0.642 |
| ACCOUNT | 0.177 | **0.700** |
| **Overall (any PII)** | **0.782** | 0.781 |

Allyanonimiser now matches `openai/privacy-filter` on overall ANY F1 (0.782
vs 0.781) and beats it on EMAIL and DATE. The remaining gap is ADDRESS
(no AU-style anchors for international addresses) and ACCOUNT (most
AI4Privacy ACCOUNT FNs are passport / generic-ID numbers in non-standard
formats — too high-risk to catch with regex without major AU-side FPs).

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

- **On Australian insurance data (enriched bench with international-customer scenarios), Allyanonimiser beats a state-of-the-art 1.5B-parameter model** on 5 of 6 categories, at ~24× the throughput, with no GPU and no heavy ML dependencies.
- **On general multilingual PII (AI4Privacy English split), Allyanonimiser now matches `openai/privacy-filter` overall** (0.782 vs 0.781). It still trails on PERSON (broader name training) and ADDRESS / ACCOUNT (international shapes without anchors), but EMAIL, DATE, and PHONE are competitive.
- See the [International PII patterns](patterns/international.md) page for the entity types that drove the AI4Privacy lift.
- Use both if you need broad coverage — feed the same text to each and union the spans.

All tables are live against the most recent run of `bench/run_*.py`; re-run locally to verify against your Python / spaCy / onnxruntime versions.
