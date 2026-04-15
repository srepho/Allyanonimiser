# Analyzing Text

This guide walks through detecting PII in text with Allyanonimiser. It starts
with the minimal call and builds up to real-world insurance scenarios.

Throughout, we'll use one running example — a claim note that holds a mix of
Australian IDs, contact details, and insurance references:

```python
CLAIM_NOTE = """
Customer John Smith (TFN: 123 456 782, DOB: 15/04/1985) reported a collision
on 03/06/2023. He can be reached at 0412 345 678 or john.smith@example.com.
Policy POL-987654 covers his vehicle (rego ABC123) garaged at 42 Main St,
Sydney NSW 2000. Claim reference CL-98765432 has been opened.
"""
```

## Minimal call

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
results = ally.analyze(CLAIM_NOTE)

for r in results:
    print(f"{r.entity_type:30} {r.text!r:30} score={r.score:.2f}")
```

Typical output (truncated):

```
PERSON                         'John Smith'                    score=0.90
AU_TFN                         '123 456 782'                   score=1.00
DATE_OF_BIRTH                  'DOB: 15/04/1985'               score=0.95
DATE                           '03/06/2023'                    score=0.90
AU_PHONE                       '0412 345 678'                  score=0.92
EMAIL_ADDRESS                  'john.smith@example.com'        score=0.95
INSURANCE_POLICY_NUMBER        'POL-987654'                    score=0.90
VEHICLE_REGISTRATION           'ABC123'                        score=0.90
AU_POSTCODE                    '2000'                          score=0.85
INSURANCE_CLAIM_NUMBER         'CL-98765432'                   score=0.95
```

Each result is a `RecognizerResult` with five fields: `entity_type`, `text`,
`start`, `end`, and `score`.

## Restricting the entity types

If you only care about a subset, pass `active_entity_types`. This both speeds
up the analyzer (skips rules that can't produce those types) and filters the
output:

```python
results = ally.analyze(
    CLAIM_NOTE,
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "AU_PHONE"],
)
```

## Raising the confidence bar

`min_score_threshold` drops detections below a confidence cutoff:

```python
results = ally.analyze(CLAIM_NOTE, min_score_threshold=0.9)
```

0.7 is the default and works well for most insurance text. Raise it if
you're seeing noisy false positives; lower it if you're missing real
entities.

## Adjusting scores per entity type

Sometimes a rule is systematically over- or under-confident in your data.
`score_adjustment` nudges the score by a delta before threshold filtering:

```python
results = ally.analyze(
    CLAIM_NOTE,
    score_adjustment={
        "PERSON": 0.1,        # boost — we trust spaCy names in our notes
        "DATE": -0.1,         # dampen — we see a lot of date-shaped refs
    },
    min_score_threshold=0.7,
)
```

## Using AnalysisConfig for reusable settings

If you call `analyze` repeatedly with the same settings, build a config
object once:

```python
from allyanonimiser import create_allyanonimiser, AnalysisConfig

config = AnalysisConfig(
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "AU_PHONE", "AU_TFN"],
    min_score_threshold=0.8,
    score_adjustment={"PERSON": 0.05},
)

ally = create_allyanonimiser()
results = ally.analyze(CLAIM_NOTE, config=config)
```

`AnalysisConfig` fields: `language`, `active_entity_types`,
`score_adjustment`, `min_score_threshold`, `expand_acronyms`.

## Expanding acronyms before detection

Insurance text is full of internal acronyms (TL = team leader, MVA = motor
vehicle accident, TP = third party). Allyanonimiser can expand them first,
which helps spaCy pick up names and locations that were hiding behind a
shorthand:

```python
ally.set_acronyms({
    "TL":  "Team Leader",
    "MVA": "Motor Vehicle Accident",
    "TP":  "Third Party",
})

results = ally.analyze(
    "TL reviewed the MVA claim; TP was at fault.",
    expand_acronyms=True,
)
```

Without expansion, "TL" and "TP" look like meaningless 2-letter tokens. With
expansion, the analyzer sees "Team Leader" and "Third Party" — spaCy may now
flag "Team Leader" as PERSON (often desirable in redaction contexts).

## Filtering and post-processing

Detection results are plain Python objects. Standard list comprehensions
work fine:

```python
# Just contact info
contacts = [r for r in results if r.entity_type in {"EMAIL_ADDRESS", "AU_PHONE"}]

# Only high-confidence Australian-specific entities
au_only = [
    r for r in results
    if r.entity_type.startswith("AU_") and r.score >= 0.9
]

# Summarize by entity type
from collections import Counter
by_type = Counter(r.entity_type for r in results)
print(by_type.most_common())
```

## Understanding overlapping-entity resolution

Multiple recognizers often match the same span. For example, `TFN: 123 456 782`
might be picked up by both the generic `AU_TFN` pattern and the insurance-
aware `AU_TFN` in `common_formats`. The analyzer automatically de-duplicates:

1. Results are grouped by `(start, end, text)`.
2. If one entity type competes, [priority-based resolution]
   picks the winner using `DEFAULT_ENTITY_PRIORITY` from
   `core/anonymizer.py`, with a small bonus for user-registered
   patterns.
3. Winners are validated (e.g. TFN/ABN checksums run here — introduced in
   v3.2.0). Invalid IDs drop out.

If you want to customize priority, pass `entity_priority={...}` to
`EnhancedAnonymizer` (the anonymizer does the final rendering, but the
priority table is shared).

## Getting the context around a hit

Sometimes you want a few tokens on either side of the match — for auditing,
or to feed downstream models:

```python
for r in results:
    left  = CLAIM_NOTE[max(0, r.start - 20):r.start]
    right = CLAIM_NOTE[r.end:r.end + 20]
    print(f"... {left}[{r.entity_type}]{right} ...")
```

## Batch analysis

For processing many documents, call `analyze` in a loop — spaCy's model is
cached at the module level so there's no reload cost per call:

```python
notes = [CLAIM_NOTE, other_note, third_note]

all_results = [ally.analyze(note) for note in notes]
```

For pandas DataFrames specifically, use the `DataFrameProcessor` — it calls
spaCy's `nlp.pipe()` under the hood for true batching. See
[Working with DataFrames](dataframes.md).

## What's next

- [Anonymizing Text](anonymizing-text.md) — turn those detections into safe output
- [Working with DataFrames](dataframes.md) — run detection+anonymization over a pandas DataFrame
- [Custom Patterns](../patterns/custom.md) — teach the analyzer a new entity type
- [Main API](../api/main.md) — the full class and function reference
