# Allyanonimiser

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

[![PyPI version](https://img.shields.io/badge/pypi-v3.5.0-blue)](https://pypi.org/project/allyanonimiser/3.5.0/)
[![Python Versions](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Release Check](https://github.com/srepho/Allyanonimiser/actions/workflows/release-check.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/release-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Allyanonimiser detects and anonymizes personally identifiable information (PII) in text, with first-class support for Australian formats (TFN, ABN, Medicare, AU phone, etc.) and insurance-industry identifiers (policy numbers, claim references, vehicle rego, VIN).

## What's new in v3.5

International PII coverage plus a precision overhaul. Beats `openai/privacy-filter` on 5 of 6 categories of the enriched AU bench — see [Benchmarks](benchmarks.md).

- **5 new entity types loaded by default** — `PHONE_INTL` (with `+CC`, `00` IDD prefix, and parenthesised area-code variants), `US_SSN` (with SSA reservation rules), `CREDIT_CARD` (Luhn-validated 13-19 digits), `ISO_DATETIME` (`2024-05-22T14:32:00`), `TIME` (12/24h, with/without seconds). All anchored on structural features that don't collide with AU patterns — see [International Patterns](patterns/international.md).
- **Validate-then-pick conflict resolution** — when multiple patterns match the same span, the resolver now walks candidates from highest priority down and returns the first that passes per-type validation. Previously a permissive pattern (e.g. CREDIT_CARD on a 13-digit phone) could win by priority, fail its checksum, and silently drop the valid runner-up.
- **PERSON precision overhauled** — city / state-postcode / date-shape / acronym / label-word rejection, iterative trim of trailing label tokens (`Joe Smith\nDOB` → `Joe Smith`), and the FP check now applied to single-candidate spans. AU bench PERSON F1 0.836 → 0.954.
- **VEHICLE_REGISTRATION tightened** — SSN/TIN/NIN added to the label deny-list plus an SSN-shape negative lookahead so `bad SSN 999-04-7100` no longer absorbs `SSN 999-04` as a plate.
- **DATE_OF_BIRTH / INCIDENT_DATE spans no longer eat the prefix** — capture-group rewrite so spans equal just the date (was `'DOB: 04/01/1959'`, now `'04/01/1959'`).

### v3.4 (prior)

- **Tightened AU_ADDRESS / AU_POSTCODE** — dropped loose fallbacks; bare 4-digit numbers (years, amounts) no longer match AU_POSTCODE.
- **Expanded DATE validator** — accepts spaCy's natural-language DATE outputs (`March 2024`, `next Monday`, `Q1 2024`, `yesterday`).
- **Widened INSURANCE_CLAIM_NUMBER** — accepts `CLM` prefix alongside `CL`/`C`.
- **New `[bench]` optional extra** — `pip install "allyanonimiser[bench]"` for the benchmark suite.

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
