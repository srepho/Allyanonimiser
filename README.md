# Allyanonimiser

[![PyPI version](https://img.shields.io/badge/pypi-v3.7.0-blue)](https://pypi.org/project/allyanonimiser/3.7.0/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/srepho/Allyanonimiser/branch/main/graph/badge.svg)](https://codecov.io/gh/srepho/Allyanonimiser)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-online-brightgreen.svg)](https://srepho.github.io/Allyanonimiser/)

Australian-focused PII detection and anonymization for the insurance industry — fast, regex + spaCy, no GPU. Detects 43 entity types (TFN, Medicare, ABN with checksums; policy/claim numbers; international phone/SSN/credit-card shapes) and anonymizes them with configurable operators, with stream processing for very large files.

📖 **[Full documentation](https://srepho.github.io/Allyanonimiser/)** · [Changelog](CHANGELOG.md)

## Version 3.7.0 — Detection Recall on Realistic Insurance Text

- **Much better recall on realistic insurance text** — on a new held-out test set, fully masked entities rose from 68% to 86% (pattern-only) and from 74% to 85% (`en_core_web_lg`).
- **Identifiers** — hyphenated TFN/ABN/ACN/Medicare, form-style labels ("Worker TFN for PAYG withholding:"), licences, two-letter passports, account numbers, and insurer policy/claim references in any format.
- **Dates and names** — written and ISO dates; reversed, all-caps, initialled and accented names; names after titles, greetings, role labels and self-introductions.
- **Addresses and phones** — unit/level prefixes, PO Box and Locked Bag addresses, "+61 ..." numbers, and mobiles read aloud.
- **Bug fixes** — dates after words such as "Incident" or "Payment" were dropped; names ending in "id" or "ref" (Reid, Al-Rashid) could vanish; labelled names were hidden when spaCy missed them.
- **New AU challenge corpus** — 480 synthetic documents with a held-out test split and per-variant results (`bench/make_au_challenge.py`).

**Behaviour change:** PERSON patterns you add yourself now run when spaCy is loaded; they were previously ignored.

### 3.6.0 (prior)

- **Streaming works on real CSV files** — `stream_from_file()` crashed on any real file in 3.5.x. It now reads ordered row batches with correct counts and row indices, and writes entity output incrementally.
- **Exported configuration reproduces behaviour** — exports now include custom patterns, analyzer settings and priorities, and reload into identical detections in JSON or YAML.
- **Opt-in sensitive-output controls** — `minimal_output=True` drops original values, source columns, caches and reports. `require_spacy_model=True` fails at start-up instead of silently running without NER.
- **State isolation fixes** — cached results can no longer be altered by callers or earlier calls, cache limits are enforced, custom pattern scores are honoured, and duplicate DataFrame index labels keep their own rows' output.
- **Reports belong to their instance** — instances no longer share one report. Pass a shared `ReportingManager` to combine them.
- **Offline detection evaluation** — `bench/eval_ally.py` plus a pattern-only regression gate in the test suite. Detection quality on the AU corpus is unchanged from 3.5.1.

**Compatibility:** the `stream` extra needs Polars 1.37 or later, and streaming reads CSV columns as strings by default.

### 3.5.1 (prior)

- **Per-call options no longer leak** — `analyze(active_entity_types=...)` / `min_score_threshold=...` are now true per-call parameters instead of sticky setters that silently restricted every later call (also fixed in the DataFrame and stream processors).
- **`analyze_batch()` now matches `analyze()` exactly** — the batch path previously skipped false-positive filtering, so DataFrame/CSV processing missed the v3.5.0 precision work.
- **Label-context disambiguation** — "TFN is 123 456 789" now resolves to `AU_TFN` instead of the bare 9-digit CRN shape; explicit labels beat shape priority and checksum validation.
- **Span-containment absorption** — DATE fragments inside DOB spans, stray NUMBER triplets inside identifiers, and CRN-tail-of-ABN matches are absorbed by their containing span.
- **Fresh-install fix** — explicit `click>=8.0` dependency shields against the upstream typer 0.26.8 break that made `import spacy` (and therefore this package) fail in newly resolved environments.

See the [changelog](CHANGELOG.md) for full details and earlier releases.

## Installation

```bash
pip install allyanonimiser==3.7.0

# With stream processing support for large files (polars + pyarrow)
pip install "allyanonimiser[stream]==3.7.0"

# spaCy model for NER (the library defaults to the small model)
python -m spacy download en_core_web_sm
```

Requires Python 3.12 or 3.13.

The default `en_core_web_sm` model (44 MB) suits most pipelines — pattern-based detection (TFN, ABN, Medicare, phones, emails, dates) is identical regardless of model. Install `en_core_web_lg` (587 MB) and pass `spacy_model=SPACY_MODEL_ACCURATE` when missing a person's name is a real cost, or `spacy_model=None` for pattern-only mode. See [Installation](https://srepho.github.io/Allyanonimiser/getting-started/installation/) for the full model tradeoff table.

## Quick Start

```python
from allyanonimiser import create_allyanonimiser

# Create the Allyanonimiser instance with default settings
ally = create_allyanonimiser()

# Analyze text
results = ally.analyze(
    text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123."
)

# Print results
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")

# Anonymize text
anonymized = ally.anonymize(
    text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123.",
    operators={
        "POLICY_NUMBER": "mask",  # Replace with asterisks
        "VEHICLE_REGISTRATION": "replace"  # Replace with <VEHICLE_REGISTRATION>
    }
)

print(anonymized["text"])
# Output: "Please reference your policy ********** for claims related to your vehicle rego <VEHICLE_REGISTRATION>."
```

### Adding Custom Patterns

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Add a custom pattern with regex
ally.add_pattern({
    "entity_type": "REFERENCE_CODE",
    "patterns": [r"REF-\d{6}-[A-Z]{2}", r"Reference\s+#\d{6}"],
    "context": ["reference", "code", "ref"],
    "name": "Reference Code"
})

# Or generate a pattern from examples
ally.create_pattern_from_examples(
    entity_type="EMPLOYEE_ID",
    examples=["EMP00123", "EMP45678", "EMP98765"],
    context=["employee", "staff", "id"],
    generalization_level="medium"  # Options: none, low, medium, high
)
```

More in the docs: [Analyzing Text](https://srepho.github.io/Allyanonimiser/usage/analyzing-text/) · [Anonymizing Text](https://srepho.github.io/Allyanonimiser/usage/anonymizing-text/) · [Working with DataFrames](https://srepho.github.io/Allyanonimiser/usage/dataframes/) · [Custom Patterns](https://srepho.github.io/Allyanonimiser/patterns/custom/)

## Features

- **Australian-focused PII**: TFN, ABN, ACN (with checksum validation), Medicare, AU phone formats, driver's licenses, addresses with state/postcode anchoring, Centrelink CRN, passport
- **Insurance domain**: policy numbers, claim references, vehicle registration, VIN, broker codes, incident dates
- **International shapes** (v3.5+): `PHONE_INTL`, `US_SSN`, Luhn-validated `CREDIT_CARD`, `ISO_DATETIME`, `TIME`
- **Flexible anonymization**: replace, mask, redact, hash (SHA-256), age-bracket operators, postcode preservation within addresses
- **Context-aware resolution**: explicit labels ("TFN is …") beat bare-shape matches; overlapping and contained entities resolved by configurable priority
- **Scale**: batch analysis via `nlp.pipe()`, pandas DataFrames with optional PyArrow backing, memory-efficient chunked stream processing via Polars
- **Reporting**: session-level statistics, entity histograms, Jupyter-native rendering

**43 entity types across five categories** — see the [pattern catalogue](https://srepho.github.io/Allyanonimiser/patterns/overview/) for the complete reference with examples, or [Australian](https://srepho.github.io/Allyanonimiser/patterns/australian/) and [International](https://srepho.github.io/Allyanonimiser/patterns/international/) pattern deep-dives.

## Benchmarks

Head-to-head against [`openai/privacy-filter`](https://huggingface.co/openai/privacy-filter) (a 1.5B-parameter token classifier) with character-level P/R/F1 scoring. On the enriched AU-insurance bench (160 synthetic docs, ~8 PII spans each), Allyanonimiser wins **5 of 6 categories** at ~24× the throughput, on CPU, without torch:

| Category | Allyanonimiser F1 | openai/privacy-filter F1 |
|---|---:|---:|
| PERSON | **0.954** | 0.908 |
| ADDRESS | **0.962** | 0.940 |
| EMAIL | **1.000** | 0.982 |
| PHONE | **1.000** | 0.870 |
| DATE | **0.997** | 0.964 |
| Account-like IDs (TFN, Medicare, ABN, policy, VIN, …) | **0.997** | 0.880 |
| **Overall (any PII)** | 0.950 | **0.958** |

On general multilingual PII (AI4Privacy, 1,000 English rows) the two are tied overall (0.782 vs 0.781); on legal text (TAB/ECHR) Allyanonimiser leads overall (0.560 vs 0.378). Full tables, methodology, and how-to-reproduce: [Benchmarks](https://srepho.github.io/Allyanonimiser/benchmarks/). Eval scripts and synthetic data are in [`bench/`](bench/).

## Migrating from v2.x

v3.0 restructured the package into layered modules and replaced the stringly-typed management methods with explicit ones. Top-level imports (`create_allyanonimiser`, `EnhancedAnalyzer`, `DataFrameProcessor`, …) are unchanged. See the [migration guide](https://srepho.github.io/Allyanonimiser/getting-started/migration/).

## Documentation

- [Installation](https://srepho.github.io/Allyanonimiser/getting-started/installation/) — prerequisites, extras, spaCy model choice
- [Quick Start](https://srepho.github.io/Allyanonimiser/getting-started/quick-start/) — 5-minute walkthrough
- [Pattern catalogue](https://srepho.github.io/Allyanonimiser/patterns/overview/) — all 43 entity types
- [Anonymization operators](https://srepho.github.io/Allyanonimiser/advanced/anonymization-operators/) — how each operator works
- [API reference](https://srepho.github.io/Allyanonimiser/api/main/) — full class and function reference
- [Benchmarks](https://srepho.github.io/Allyanonimiser/benchmarks/) — methodology and results

## License

MIT — see [LICENSE](LICENSE).
