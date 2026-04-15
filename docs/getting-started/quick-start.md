# Quick Start

This guide will walk you through the basic usage of Allyanonimiser to detect and anonymize personally identifiable information (PII) in text.

## Creating an Allyanonimiser Instance

The first step is to create an instance of the Allyanonimiser class:

```python
from allyanonimiser import create_allyanonimiser

# Default: uses en_core_web_sm (44 MB, fast)
ally = create_allyanonimiser()
```

This instance comes pre-configured with all built-in patterns for Australian, general, and insurance-specific PII.

### Choosing a spaCy model

In v3.3+ the default spaCy model is `en_core_web_sm` — small (44 MB) and fast to load. Pattern-based detection (TFN, ABN, Medicare, AU phone, email, dates) is identical regardless of the model. If you need higher recall on `PERSON`, `LOCATION`, or `ORG` entities, opt into the larger model:

```python
from allyanonimiser import create_allyanonimiser, SPACY_MODEL_ACCURATE

ally = create_allyanonimiser(spacy_model=SPACY_MODEL_ACCURATE)  # en_core_web_lg, 587 MB
```

Pass `spacy_model=None` to disable spaCy entirely — pattern detection keeps working. See the [Installation guide](installation.md#choosing-a-spacy-model) for the full tradeoff table.

## Analyzing Text for PII

To detect PII entities in a text:

```python
# Text to analyze
text = "Please reference your policy AU-12345678 for claims related to your vehicle registration XYZ123."

# Analyze the text
results = ally.analyze(text)

# Print the results
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```

Output:
```
Entity: POLICY_NUMBER, Text: AU-12345678, Score: 0.85
Entity: VEHICLE_REGISTRATION, Text: XYZ123, Score: 0.7
```

## Anonymizing Text

To anonymize the detected PII:

```python
# Anonymize the text with specific operators for each entity type
anonymized = ally.anonymize(
    text="Please reference your policy AU-12345678 for claims related to your vehicle registration XYZ123.",
    operators={
        "POLICY_NUMBER": "mask",      # Replace with asterisks
        "VEHICLE_REGISTRATION": "replace"  # Replace with entity type
    }
)

# Print the anonymized text
print(anonymized["text"])
```

Output:
```
Please reference your policy ********** for claims related to your vehicle registration <VEHICLE_REGISTRATION>.
```

## Adding Custom Patterns

You can add your own patterns to detect additional entity types:

```python
# Add a custom pattern with regex
ally.add_pattern({
    "entity_type": "REFERENCE_CODE",
    "patterns": [r"REF-\d{6}-[A-Z]{2}", r"Reference\s+#\d{6}"],
    "context": ["reference", "code", "ref"],
    "name": "Reference Code"
})

# Test the custom pattern
text = "Your reference code is REF-123456-AB for this inquiry."
results = ally.analyze(text)

for result in results:
    print(f"Found {result.entity_type}: {result.text}")
```

Output:
```
Found REFERENCE_CODE: REF-123456-AB
```

## Generating Patterns from Examples

Allyanonimiser can also generate patterns from example strings:

```python
# Generate a pattern from examples
ally.create_pattern_from_examples(
    entity_type="EMPLOYEE_ID",
    examples=["EMP00123", "EMP45678", "EMP98765"],
    context=["employee", "staff", "id"],
    generalization_level="medium"  # Options: none, low, medium, high
)

# Test the generated pattern
text = "Employee EMP12345 submitted the request."
results = ally.analyze(text)

for result in results:
    print(f"Found {result.entity_type}: {result.text}")
```

Output:
```
Found EMPLOYEE_ID: EMP12345
```

## Next Steps

Now that you understand the basics, explore the following topics to learn more:

- [Analyzing Text](../usage/analyzing-text.md) - Learn about the analysis capabilities in depth
- [Anonymizing Text](https://github.com/srepho/Allyanonimiser#anonymization-operators) - Explore the various anonymization operators
- [Working with DataFrames](https://github.com/srepho/Allyanonimiser#dataframe-processing) - Process tabular data efficiently
- [Pattern Reference](../patterns/overview.md) - See all the built-in patterns
- [Creating Custom Patterns](https://github.com/srepho/Allyanonimiser#custom-patterns) - Learn how to create and manage custom patterns