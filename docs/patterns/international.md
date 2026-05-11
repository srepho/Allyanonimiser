# International PII Patterns

Allyanonimiser is AU-insurance-focused, but real claim notes routinely
include international PII: expat customers, business travellers, dual-coverage
policies, and system audit logs that leak ISO timestamps. These patterns
are loaded **by default** alongside the AU-specific recognisers.

Each pattern is anchored on a structural feature that does not collide with
any AU identifier (e.g. `+CC` for international phone, the `T` separator for
ISO datetimes, the `\d{3}-\d{2}-\d{4}` segment shape for US SSN). Credit-card
matches additionally require a Luhn checksum to pass before they're emitted.

## Entity types

| Entity | Example values |
| --- | --- |
| `TIME` | `14:32`, `14:32:05`, `2:30 PM`, `9:15 a.m.` |
| `ISO_DATETIME` | `2024-05-22T14:32:00`, `2024-05-22T14:32:00Z`, `2024-05-22T14:32:00+10:00` |
| `PHONE_INTL` | `+44 7700 900123`, `+1-415-555-1234`, `(415) 555-1234`, `0013 408-555-2222` |
| `US_SSN` | `818-04-7100` (with SSA reservation rules: area ≠ 000/666/9xx, group ≠ 00, serial ≠ 0000) |
| `CREDIT_CARD` | `4111 1111 1111 1111` (Visa/Mastercard/Amex/Discover; Luhn-validated) |

## Why these are safe to ship as defaults

- `TIME` — colon-separated 12/24h time. Doesn't collide with TFN/Medicare/policy/claim formats.
- `ISO_DATETIME` — the `T` separator is unique; no AU pattern uses it.
- `PHONE_INTL` — anchored on `+CC`, `00CC` IDD prefix, or a parenthesised
  area code of 3-4 digits. AU 2-digit area codes (`(02)`, `(03)`, `(07)`,
  `(08)`) stay with `AU_PHONE` because the intl pattern requires 3+ digits
  inside the parens.
- `US_SSN` — segment lengths `\d{3}-\d{2}-\d{4}` don't match any AU pattern
  (TFN is `\d{3} \d{3} \d{3}`, ABN is `\d{2} \d{3} \d{3} \d{3}`, Medicare is
  `\d{4} \d{5} \d`).
- `CREDIT_CARD` — 13-19-digit blocks are common, but Luhn validation drops
  random sequences. A 16-digit policy number that happens to pass Luhn is
  vanishingly rare and overlaps with `INSURANCE_POLICY_NUMBER` (priority 95)
  anyway.

## Priority order

The new entity types are weighted in `DEFAULT_ENTITY_PRIORITY` so they win
the right way on overlap:

| Entity | Priority | Notes |
| --- | --- | --- |
| `US_SSN` | 100 | Same tier as AU government identifiers |
| `CREDIT_CARD` | 85 | Same tier as `AU_PHONE` |
| `PHONE_INTL` | 85 | Same tier as `AU_PHONE` (AU_PHONE wins on AU-shape spans because the intl pattern is narrower) |
| `ISO_DATETIME` | 55 | Specific T-separated form, ranks above bare `DATE` |
| `INCIDENT_DATE` | 45 | |
| `DATE` | 40 | |
| `TIME` | 35 | Below `DATE` so `15/01/2024 at 14:30` prefers `DATE` for the date portion |

## Tuning out an entity type

If your data never contains a particular international shape, drop the
pattern at construction:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
# Remove the credit-card detector
ally.analyzer.patterns = [
    p for p in ally.analyzer.patterns if p.entity_type != "CREDIT_CARD"
]
```

Or, conversely, register only the shapes you need:

```python
from allyanonimiser import EnhancedAnalyzer, CustomPatternDefinition
from allyanonimiser.patterns.au_patterns import get_au_pattern_definitions
from allyanonimiser.patterns.general_intl_patterns import (
    get_general_intl_pattern_definitions,
)

analyzer = EnhancedAnalyzer()
for pdef in get_au_pattern_definitions():
    analyzer.add_pattern(CustomPatternDefinition(**pdef))
# Pull just TIME and ISO_DATETIME, skip the rest
for pdef in get_general_intl_pattern_definitions():
    if pdef["entity_type"] in {"TIME", "ISO_DATETIME"}:
        analyzer.add_pattern(CustomPatternDefinition(**pdef))
```

## Benchmarks

Adding the international patterns lifts measurable coverage on both the
[enriched AU bench](../benchmarks.md) (which contains expat/payment/business
travel templates) and the AI4Privacy English split. See the benchmarks page
for full numbers.
