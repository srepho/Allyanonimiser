# Allyanonimiser

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

[![PyPI version](https://img.shields.io/badge/pypi-v3.4.0-blue)](https://pypi.org/project/allyanonimiser/3.4.0/)
[![Python Versions](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Release Check](https://github.com/srepho/Allyanonimiser/actions/workflows/release-check.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/release-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Allyanonimiser detects and anonymizes personally identifiable information (PII) in text, with first-class support for Australian formats (TFN, ABN, Medicare, AU phone, etc.) and insurance-industry identifiers (policy numbers, claim references, vehicle rego, VIN).

## What's new in v3.4

Pattern precision fixes surfaced by head-to-head [benchmarks](benchmarks.md) against `openai/privacy-filter` on three datasets.

- **Tightened AU_ADDRESS** — dropped two loose fallback patterns that were absorbing narrative prose; remaining patterns are anchored by state + postcode. New case-tolerant variant accepts lowercase/mixed case.
- **Tightened AU_POSTCODE** — no longer matches bare 4-digit numbers (years, amounts). Requires state abbrev or `postcode`/`post code`/`postal code` label.
- **Expanded DATE validator** — recognizes spaCy's natural-language DATE outputs (`March 2024`, `next Monday`, `Q1 2024`, `yesterday`, etc.).
- **Widened INSURANCE_CLAIM_NUMBER** — accepts `CLM` prefix alongside `CL`/`C`.
- **New `[bench]` optional extra** — `pip install "allyanonimiser[bench]"` for the benchmark suite.

### v3.3 (prior)

- **Default spaCy model** is now `en_core_web_sm` (44 MB, fast). Previously `en_core_web_lg` (587 MB). Switch with `spacy_model=SPACY_MODEL_ACCURATE` when accuracy matters.
- **`SPACY_MODEL_FAST` / `SPACY_MODEL_ACCURATE`** constants exported for clarity.

## Key Features

- **Australian-focused PII**: TFN (with checksum), ABN (with checksum), Medicare, AU_PHONE, driver's license, Centrelink CRN, passport, postcode
- **Insurance domain**: policy numbers, claim references, vehicle registration, VIN
- **Flexible anonymization**: replace, mask, redact, hash (SHA-256), age-bracket, consistent-replacement
- **Stream processing**: memory-efficient chunked processing for very large files via Polars
- **DataFrame support**: pandas with optional PyArrow backing; expand_acronyms wiring for preprocessing
- **Reporting**: session-level statistics, entity histograms, Jupyter-native rendering

## Quick example

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()  # defaults to en_core_web_sm

results = ally.analyze(
    "Customer John Smith (TFN: 123 456 782) called about policy POL-987654."
)
for r in results:
    print(f"{r.entity_type}: {r.text!r} (score={r.score:.2f})")

out = ally.anonymize(
    "Customer John Smith (TFN: 123 456 782) called about policy POL-987654.",
    operators={
        "PERSON": "replace",
        "AU_TFN": "mask",
        "INSURANCE_POLICY_NUMBER": "hash",
    },
)
print(out["text"])
```

## Choosing a spaCy model

| | `SPACY_MODEL_FAST` (`en_core_web_sm`) | `SPACY_MODEL_ACCURATE` (`en_core_web_lg`) |
|---|---|---|
| Default in v3.3+? | yes | no |
| Download size | 44 MB | 587 MB |
| Cold start | ~0.5s | 2–5s |
| Pattern detection (TFN, ABN, MEDICARE, AU_PHONE, EMAIL, dates) | identical | identical |
| `PERSON` / `LOCATION` / `ORG` recall | medium | high |
| Serverless friendliness (Azure Functions, Lambda) | good | poor |

Opt into the accurate model when a missed name is expensive in your downstream workflow:

```python
from allyanonimiser import create_allyanonimiser, SPACY_MODEL_ACCURATE

ally = create_allyanonimiser(spacy_model=SPACY_MODEL_ACCURATE)
```

## Next steps

- [Installation](getting-started/installation.md) — prerequisites and install options
- [Quick Start](getting-started/quick-start.md) — 5-minute walkthrough
- [Analyzing Text](usage/analyzing-text.md) — detection deep-dive
- [Patterns Overview](patterns/overview.md) — the full entity catalogue
- [Anonymization Operators](advanced/anonymization-operators.md) — how each operator works
- [Main API](api/main.md) — the full class + function reference

## License

MIT — see [LICENSE](https://github.com/srepho/Allyanonimiser/blob/main/LICENSE).
