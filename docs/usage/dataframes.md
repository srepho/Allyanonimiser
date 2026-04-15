# Working with DataFrames

Most real-world usage means processing hundreds or millions of rows from a
CSV dump or a database query. `DataFrameProcessor` batches calls through
spaCy's `nlp.pipe()` and optionally converts string columns to Arrow-backed
storage for a significant memory and speed win over `df.apply`.

## The minimal pipeline

```python
import pandas as pd
from allyanonimiser import create_allyanonimiser
from allyanonimiser.io.dataframe_processor import DataFrameProcessor

ally = create_allyanonimiser()
proc = DataFrameProcessor(ally)

df = pd.DataFrame({
    "case_id": [1, 2, 3],
    "notes": [
        "Customer John Smith called about policy POL-987654.",
        "Jane Doe filed claim CL-123456 on 03/06/2023.",
        "Email from alex@example.com regarding vehicle ABC123.",
    ],
})

result = proc.process_dataframe(df, text_columns="notes")
print(result["dataframe"][["case_id", "notes_anonymized"]])
print(result["entities"].head())
```

`result` is a dict with:

- `result["dataframe"]` — your original DataFrame, with a new
  `<column>_anonymized` column added for each processed text column.
- `result["entities"]` — a long-format entity DataFrame with one row per
  detection: `row_index`, `column`, `entity_type`, `start`, `end`,
  `text`, `score`.

## Multiple text columns

Pass a list:

```python
result = proc.process_dataframe(
    df,
    text_columns=["notes", "subject_line"],
    operators={"PERSON": "replace", "EMAIL_ADDRESS": "hash"},
)
```

Each listed column gets its own `<column>_anonymized` sibling column.

## Custom operators per run

Same operator dict as `ally.anonymize`:

```python
result = proc.process_dataframe(
    df,
    text_columns="notes",
    operators={
        "PERSON":                  "replace",
        "AU_TFN":                  "mask",
        "EMAIL_ADDRESS":           "hash",
        "INSURANCE_POLICY_NUMBER": "redact",
        "DATE_OF_BIRTH":           "age_bracket",
    },
    age_bracket_size=5,
    keep_postcode=True,
)
```

## Restricting entity types

Speed up batch runs by scoping to what you care about:

```python
result = proc.process_dataframe(
    df,
    text_columns="notes",
    active_entity_types=["PERSON", "AU_PHONE", "EMAIL_ADDRESS", "AU_TFN"],
    min_score_threshold=0.8,
)
```

## Expanding acronyms

Wire acronym expansion through (new in v3.3.0 — previously this kwarg
was silently dropped):

```python
ally.set_acronyms({"TL": "Team Leader", "MVA": "Motor Vehicle Accident"})

result = proc.process_dataframe(
    df,
    text_columns="notes",
    operators={"PERSON": "replace"},
    expand_acronyms=True,
)
```

## Missing column? Fails loud

As of v3.1.2, a missing column raises `ValueError` up front. Earlier
versions silently skipped — good for typos, bad for correctness:

```python
try:
    result = proc.process_dataframe(df, text_columns="nottes")  # typo
except ValueError as e:
    print(e)
    # Column(s) not found in DataFrame: ['nottes']. Available columns: ['case_id', 'notes']
```

## Detection-only (no anonymization)

If you just want to flag PII columns or audit, skip the rewrite step:

```python
entity_df = proc.detect_pii(
    df,
    column="notes",
    min_score_threshold=0.8,
)
```

Returns the entity DataFrame directly.

## Anonymize-in-place

For a single column:

```python
df_anon = proc.anonymize_column(
    df,
    column="notes",
    operators={"PERSON": "replace", "EMAIL_ADDRESS": "hash"},
    output_column="notes_anon",   # defaults to notes_anonymized
)
```

## Summary stats

`analyze_dataframe_statistics` takes the entity DataFrame and returns
per-entity counts, scores, and row coverage — handy for data audits or
discovery reports:

```python
entity_df = result["entities"]
stats = proc.analyze_dataframe_statistics(entity_df)
print(stats)
#   entity_type  count  avg_score  min_score  max_score  unique_rows  percentage
# 0      PERSON      3      0.91       0.85      0.95             3        25.0
# 1 INSURANCE_..     3      0.95       0.90      1.00             3        25.0
# ...
```

## Large files: stream, don't load

If the dataset doesn't fit in memory, use `stream_process_csv` instead.
It chunks through rows with polars and writes the output file
incrementally:

```python
# Requires: pip install "allyanonimiser[stream]"
ally.stream_process_csv(
    input_file="claims_raw.csv",
    output_file="claims_anon.csv",
    columns=["notes", "email"],
    operators={"PERSON": "replace", "EMAIL_ADDRESS": "hash"},
    chunk_size=10_000,
)
```

## PyArrow speedup (optional)

When `pyarrow` is installed, the processor converts string columns to
`string[pyarrow]` before processing — typically halves memory on text-
heavy columns and is noticeably faster. Install via the `[stream]` extra
(which also brings polars) or directly:

```bash
pip install pyarrow
```

The processor picks it up automatically. Disable explicitly with
`use_pyarrow=False` if you need the legacy object-dtype behavior.

## Column-schema discovery

Not sure which columns carry PII? `detect_pii_columns` samples rows and
returns a list of likely-PII columns:

```python
pii_cols = ally.detect_pii_columns(
    df,
    sample_size=100,
    min_detection_rate=0.2,   # at least 20% of sampled rows must contain PII
)
print(pii_cols)
# ['notes', 'email', 'customer_name']
```

Useful as a first pass before deciding what to anonymize.

## What's next

- [Anonymizing Text](anonymizing-text.md) — the operator catalogue that
  `process_dataframe` delegates to
- [Custom Patterns](../patterns/custom.md) — teach the analyzer a new
  entity type before running over your DataFrame
- [Main API](../api/main.md) — full method reference
