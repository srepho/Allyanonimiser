# Custom Patterns

The built-in patterns cover Australian IDs, contact info, insurance
identifiers, and general PII. Real-world usage often needs one or two
organisation-specific entity types — a customer ID format, an internal
reference code, a vendor SKU. This guide walks through adding them.

## The three ways to add a pattern

1. **Pass a regex directly** via `add_pattern(CustomPatternDefinition(...))` —
   for entity types you can describe with a regex one-liner.
2. **Generate from examples** via `create_pattern_from_examples(...)` —
   give the library a handful of real examples, let it derive the regex.
3. **Bulk-import from CSV** via `import_patterns_from_csv(...)` — for
   spec sheets you already maintain elsewhere.

## 1. Direct regex registration

```python
from allyanonimiser import create_allyanonimiser, CustomPatternDefinition

ally = create_allyanonimiser()

ally.add_pattern(CustomPatternDefinition(
    entity_type="EMPLOYEE_ID",
    patterns=[r"\bEMP\d{5}\b"],
    context=["employee", "staff", "rep"],
    name="Employee ID",
    score=0.9,
))

results = ally.analyze("Case opened by EMP12345.")
# [RecognizerResult(entity_type='EMPLOYEE_ID', text='EMP12345', ...)]
```

**Fields:**

| Field | Purpose |
|---|---|
| `entity_type` | Unique type name used everywhere downstream (operators, DataFrame entities, reports). Convention: `UPPER_SNAKE_CASE`. |
| `patterns` | List of regex strings. Any match produces a hit. |
| `context` | Words that tend to appear near this entity. Boosts score when present in the surrounding text. |
| `name` | Human-readable label. |
| `score` | Base confidence (0.0–1.0). Context presence can bump this up. |

**Tips**

- Use word boundaries (`\b`) to avoid partial matches inside longer tokens.
- Escape literal special characters (`.`, `-`, `/`, `\`).
- Multiple alternative formats? List them all in `patterns`.

## 2. Generating from examples

Handy when the format varies and you don't want to hand-craft a regex.

```python
ally.create_pattern_from_examples(
    entity_type="PROJECT_CODE",
    examples=[
        "PRJ-2024-01",
        "PRJ-2024-12",
        "PRJ-2023-07",
    ],
    context=["project", "code", "milestone"],
    generalization_level="medium",
)

results = ally.analyze("Work is tracked under PRJ-2024-08.")
# [RecognizerResult(entity_type='PROJECT_CODE', text='PRJ-2024-08', ...)]
```

**`generalization_level`** controls how flexible the derived regex is:

| Level | Behavior |
|---|---|
| `"none"` | Exact match only. Rarely what you want. |
| `"low"` | Allow variation in digits but preserve everything else exactly. |
| `"medium"` *(default)* | Digits flex by count; alphabetic tokens flex in case. |
| `"high"` | Maximum flexibility — digit groups, alphabetic groups, and separators all generalized. Risks false positives. |

Start at `"medium"` and only escalate if the pattern misses valid examples.

## 3. Bulk CSV import

For teams that maintain pattern libraries in spreadsheets:

```python
ally.import_patterns_from_csv("patterns.csv")
```

**CSV format** (header row required):

```csv
entity_type,pattern,context,name,score
EMPLOYEE_ID,\bEMP\d{5}\b,"employee;staff;rep",Employee ID,0.9
PROJECT_CODE,\bPRJ-\d{4}-\d{2}\b,"project;code;milestone",Project Code,0.85
```

Context words are separated with `;`. Multiple rows per entity type merge into
a single pattern definition with multiple regexes.

## Validating before you commit

The library ships a pattern validator you can use during development:

```python
from allyanonimiser import test_pattern_against_examples

is_valid, err = test_pattern_against_examples(
    pattern=r"\bEMP\d{5}\b",
    positive_examples=["EMP12345", "EMP00001"],
    negative_examples=["EMPLOYEE", "emp12345"],
)
print(is_valid, err)
```

Returns `(True, None)` if the regex matches every positive and none of the
negatives, or `(False, error_message)` otherwise.

## Using custom entities with anonymize

Once registered, custom types work everywhere built-ins do — including
the operator dict:

```python
ally.anonymize(
    "Case opened by EMP12345 under PRJ-2024-08.",
    operators={
        "EMPLOYEE_ID":  "hash",
        "PROJECT_CODE": "replace",
    },
)
# "Case opened by HASH-a1b2c3d4e5 under <PROJECT_CODE>."
```

## Managing priority against built-ins

Custom patterns automatically get a small registration-order priority
bonus (added in v3.0) so a user-defined entity can override a generic
built-in when both match the same span. If that's not enough, inject a
priority dict directly at the anonymizer:

```python
from allyanonimiser import EnhancedAnonymizer, create_allyanonimiser

ally = create_allyanonimiser()
ally.anonymizer = EnhancedAnonymizer(
    analyzer=ally.analyzer,
    entity_priority={
        "EMPLOYEE_ID": 120,   # higher than any built-in
        "PROJECT_CODE": 110,
    },
)
```

See `DEFAULT_ENTITY_PRIORITY` in
[`core/anonymizer.py`](https://github.com/srepho/Allyanonimiser/blob/main/allyanonimiser/core/anonymizer.py)
for the full built-in priority table.

## Persisting your custom patterns

```python
ally.save_patterns("my_patterns.json")
```

Next session:

```python
ally = create_allyanonimiser(pattern_filepath="my_patterns.json")
```

This is the recommended way to share pattern libraries across teams —
check the JSON into version control alongside your anonymization config.

## What's next

- [Patterns Overview](overview.md) — how built-in patterns are structured
- [Australian Patterns](australian.md) — full reference of what ships
- [Anonymization Operators](../advanced/anonymization-operators.md) — rewriter catalogue
- [Custom Operators](../advanced/custom-operators.md) — for when "replace" / "mask" / "hash" aren't enough
