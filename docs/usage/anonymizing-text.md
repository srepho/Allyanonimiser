# Anonymizing Text

Detection tells you *where* the PII is. Anonymization rewrites the text so
you can ship it downstream (to an LLM, into a dataset, to another team)
without the sensitive parts. This guide walks through the built-in
operators with real examples.

We'll use the same running claim note as in
[Analyzing Text](analyzing-text.md):

```python
CLAIM_NOTE = """
Customer John Smith (TFN: 123 456 782, DOB: 15/04/1985) reported a collision
on 03/06/2023. He can be reached at 0412 345 678 or john.smith@example.com.
Policy POL-987654 covers his vehicle (rego ABC123) garaged at 42 Main St,
Sydney NSW 2000. Claim reference CL-98765432 has been opened.
"""
```

## The minimal call

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
result = ally.anonymize(CLAIM_NOTE)

print(result["text"])
```

With no operators specified, Allyanonimiser defaults to `replace` —
every detected entity becomes `<ENTITY_TYPE>`:

```
Customer <PERSON> (TFN: <AU_TFN>, <DATE_OF_BIRTH>) reported a collision
on <DATE>. He can be reached at <AU_PHONE> or <EMAIL_ADDRESS>.
Policy <INSURANCE_POLICY_NUMBER> covers his vehicle (rego <VEHICLE_REGISTRATION>) garaged at 42 Main St,
Sydney NSW <AU_POSTCODE>. Claim reference <INSURANCE_CLAIM_NUMBER> has been opened.
```

The return value is a dict:

- `result["text"]` — the anonymized string.
- `result["items"]` — per-replacement records (`entity_type`, `original`,
  `replacement`, `operator`) you can log or audit.

## Per-entity operators

Pass `operators={entity_type: operator}` to pick what happens per type:

```python
result = ally.anonymize(
    CLAIM_NOTE,
    operators={
        "PERSON":                    "replace",       # <PERSON>
        "AU_TFN":                    "mask",          # ***********
        "EMAIL_ADDRESS":             "hash",          # HASH-a1b2c3d4e5
        "DATE_OF_BIRTH":             "age_bracket",   # 40-45
        "INSURANCE_POLICY_NUMBER":   "redact",        # [REDACTED]
    },
)
```

### Operator catalogue

| Operator | What it does | Output example |
|---|---|---|
| `replace` | Substitute with `<ENTITY_TYPE>` | `John Smith` → `<PERSON>` |
| `mask` | Replace every character with `*` | `0412 345 678` → `************` |
| `redact` | Replace with `[REDACTED]` | `POL-987654` → `[REDACTED]` |
| `hash` | SHA-256 prefix (stable across a run) | `john@example.com` → `HASH-a1b2c3d4e5` |
| `age_bracket` | Convert a birthdate to an age band | `DOB: 15/04/1985` → `40-45` |

Hashing is deterministic within a single run — the same input always
hashes to the same output — so relationships in the text survive (e.g.
two mentions of the same email get the same hash).

## Age bracketing

When `DATE_OF_BIRTH` entities use the `age_bracket` operator, the
anonymizer computes an age from today and emits a bracket. Adjust the
bracket width via `age_bracket_size`:

```python
result = ally.anonymize(
    CLAIM_NOTE,
    operators={"DATE_OF_BIRTH": "age_bracket"},
    age_bracket_size=5,   # default; "40-45", "45-50", etc.
)

# Wider brackets for stronger k-anonymity:
result = ally.anonymize(
    CLAIM_NOTE,
    operators={"DATE_OF_BIRTH": "age_bracket"},
    age_bracket_size=10,  # "40-50"
)
```

## Keeping postcodes in addresses

Postcodes often carry aggregated signal (metro/regional, premium zones)
that's useful to retain even after scrubbing the street address. The
default behavior keeps them:

```python
result = ally.anonymize(
    "42 Main St, Sydney NSW 2000",
    operators={"AU_ADDRESS": "replace"},
    keep_postcode=True,   # default
)
# "42 Main St, Sydney NSW 2000" → "<AU_ADDRESS> 2000"
```

Set `keep_postcode=False` to scrub the full address including the postcode.

## Restricting which entities get anonymized

If you only want to scrub a subset, pass `active_entity_types`. Other
detected entities pass through untouched:

```python
result = ally.anonymize(
    CLAIM_NOTE,
    active_entity_types=["PERSON", "EMAIL_ADDRESS"],
    operators={
        "PERSON":        "replace",
        "EMAIL_ADDRESS": "hash",
    },
)
```

TFNs, phone numbers, policy numbers, etc. survive unchanged. Useful when
you want to keep internal identifiers visible to analysts but remove
customer names and contact info.

## Expanding acronyms before anonymization

Same mechanism as in the analyzer — expand internal shorthand before
detection runs so anonymization catches what was hiding:

```python
ally.set_acronyms({"TL": "Team Leader", "MVA": "Motor Vehicle Accident"})

result = ally.anonymize(
    "TL Jane Doe reviewed the MVA claim.",
    operators={"PERSON": "replace"},
    expand_acronyms=True,
)
# Before: "TL Jane Doe reviewed the MVA claim."
# After:  "Team Leader <PERSON> reviewed the Motor Vehicle Accident claim."
```

## Reusable settings via AnonymizationConfig

If you're making the same call repeatedly, build a config once:

```python
from allyanonimiser import create_allyanonimiser, AnonymizationConfig

config = AnonymizationConfig(
    operators={
        "PERSON":        "replace",
        "AU_TFN":        "mask",
        "AU_PHONE":      "mask",
        "EMAIL_ADDRESS": "hash",
        "DATE_OF_BIRTH": "age_bracket",
    },
    age_bracket_size=5,
    keep_postcode=True,
)

ally = create_allyanonimiser()
for note in claim_notes:
    result = ally.anonymize(note, config=config)
    ...
```

## Auditing what was replaced

`result["items"]` gives you a per-replacement log — useful for
debugging, reporting, or compliance evidence:

```python
result = ally.anonymize(CLAIM_NOTE, operators={"PERSON": "replace", "AU_TFN": "mask"})

for item in result["items"]:
    print(f"{item['entity_type']:30} {item['operator']:15} "
          f"{item['original']!r:30} -> {item['replacement']!r}")
```

Sample output:

```
PERSON                         replace         'John Smith'                  -> '<PERSON>'
AU_TFN                         mask            '123 456 782'                 -> '***********'
```

## What's next

- [Working with DataFrames](dataframes.md) — scale this to pandas
- [Anonymization Operators (Advanced)](../advanced/anonymization-operators.md) — deep dive per operator
- [Custom Operators](../advanced/custom-operators.md) — register your own rewriter
- [Custom Patterns](../patterns/custom.md) — detect entity types the library doesn't ship
