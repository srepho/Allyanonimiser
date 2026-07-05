# Allyanonimiser

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

[![PyPI version](https://img.shields.io/badge/pypi-v3.5.1-blue)](https://pypi.org/project/allyanonimiser/3.5.1/)
[![Python Versions](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Release Check](https://github.com/srepho/Allyanonimiser/actions/workflows/release-check.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/release-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Allyanonimiser detects and anonymizes personally identifiable information (PII) in text, with first-class support for Australian formats (TFN, ABN, Medicare, AU phone, etc.) and insurance-industry identifiers (policy numbers, claim references, vehicle rego, VIN).

## What's new in v3.5.1

Bug-fix and precision release — AU bench unchanged from v3.5.0 (still beats `openai/privacy-filter` on 5 of 6 categories, see [Benchmarks](benchmarks.md)).

- **Per-call options no longer leak** — `analyze(active_entity_types=...)` / `min_score_threshold=...` are now true per-call parameters instead of sticky setters that silently restricted every later call (also fixed in the DataFrame and stream processors). The explicit `set_active_entity_types()` / `set_min_score_threshold()` methods remain the persistent knobs.
- **`analyze_batch()` now matches `analyze()` exactly** — the batch path previously skipped the PERSON/LOCATION/ORG false-positive filtering and entity-type mapping, so DataFrame/CSV processing missed the v3.5.0 precision improvements.
- **Label-context disambiguation** — "TFN is 123 456 789" now resolves to `AU_TFN` instead of the bare 9-digit CRN shape; an explicit label immediately before a value beats shape priority and checksum validation, and the labelled regexes tolerate filler words (`TFN is`, `ABN number:`).
- **Span-containment absorption** — DATE fragments inside DOB spans (the `lg`-model fragmentation), stray NUMBER triplets inside identifiers, and CRN-tail-of-ABN matches are absorbed by their containing span. Postcodes inside addresses are never absorbed (`keep_postcode` depends on them).

### v3.5 (prior)

- **5 new entity types loaded by default** — `PHONE_INTL`, `US_SSN`, `CREDIT_CARD` (Luhn-validated), `ISO_DATETIME`, `TIME` — see [International Patterns](patterns/international.md).
- **Validate-then-pick conflict resolution** — the resolver walks candidates from highest priority down and returns the first that passes per-type validation.
- **PERSON precision overhauled** — city / state-postcode / date-shape / acronym / label-word rejection and trailing-label trim. AU bench PERSON F1 0.836 → 0.954.

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
