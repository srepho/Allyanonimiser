# Analyzing Text for PII

This guide explains how to use Allyanonimiser to detect personally identifiable information (PII) in text.

## Basic Analysis

To analyze text for PII, use the `analyze` method:

```python
from allyanonimiser import create_allyanonimiser

# Create the analyzer
ally = create_allyanonimiser()

# Text to analyze
text = """Customer John Smith (TFN: 123 456 789) reported an incident on 15/06/2023
regarding their policy AU-12345678. They can be reached at 0412 345 678 or
john.smith@example.com. They live at 42 Main St, Sydney NSW 2000."""

# Analyze the text
results = ally.analyze(text)

# Print the results
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```

Example output:

```
Entity: PERSON, Text: John Smith, Score: 0.85
Entity: AU_TFN, Text: 123 456 789, Score: 0.75
Entity: DATE, Text: 15/06/2023, Score: 0.8
Entity: POLICY_NUMBER, Text: AU-12345678, Score: 0.9
Entity: AU_PHONE, Text: 0412 345 678, Score: 0.85
Entity: EMAIL_ADDRESS, Text: john.smith@example.com, Score: 0.95
Entity: AU_ADDRESS, Text: 42 Main St, Sydney NSW 2000, Score: 0.7
```

## Filtering by Entity Type

You can filter results to focus on specific entity types:

```python
# Filter results by entity type
contact_info = [r for r in results if r.entity_type in ["EMAIL_ADDRESS", "AU_PHONE"]]

for info in contact_info:
    print(f"Contact info found: {info.text} ({info.entity_type})")
```

## Configuring the Analysis

For more control over the analysis process, use the `AnalysisConfig` class:

```python
from allyanonimiser import create_allyanonimiser, AnalysisConfig

# Create the analyzer
ally = create_allyanonimiser()

# Configure analysis to only detect specific entity types with higher confidence
config = AnalysisConfig(
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "AU_PHONE"],
    min_score_threshold=0.7
)

# Analyze with the configuration
results = ally.analyze(
    text="John Smith can be reached at john.smith@example.com or 0412 345 678.",
    config=config
)

for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```

## Adding Context Words

You can improve detection accuracy by providing additional context words for specific entity types:

```python
from allyanonimiser import create_allyanonimiser, AnalysisConfig

# Create the analyzer
ally = create_allyanonimiser()

# Add context words to help with detection
config = AnalysisConfig(
    context_words={
        "INSURANCE_POLICY_NUMBER": ["reference", "contract", "insurance"],
        "PERSON": ["customer", "client", "representative"]
    }
)

# Analyze with additional context
results = ally.analyze(
    text="The client Jane Doe referenced contract A-987654.",
    config=config
)

for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```

## Working with Detection Results

The analysis results are returned as objects with useful attributes:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
results = ally.analyze("John Smith's TFN is 123 456 789.")

# Each result object contains detailed information
for result in results:
    print(f"Entity type: {result.entity_type}")
    print(f"Text: {result.text}")
    print(f"Start position: {result.start}")
    print(f"End position: {result.end}")
    print(f"Confidence score: {result.score}")
    print(f"Pattern source: {result.pattern_name}")
    print("---")
```

## Handling Overlapping Entities

Sometimes entities can overlap in the text. You can control how overlapping entities are handled:

```python
from allyanonimiser import create_allyanonimiser, AnalysisConfig

ally = create_allyanonimiser()

# Configure analysis to prefer longer entities when overlapping
config = AnalysisConfig(
    resolve_overlaps="longest",  # Options: "longest", "highest_score", "all"
)

# Text with potentially overlapping entities
text = "Reference number POL-123456-AU was submitted by the customer."

results = ally.analyze(text, config=config)
```

## Analyzing Specific Document Types

Allyanonimiser has specialized analyzers for specific document types:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Analyze a claim note (optimized for insurance claim notes)
claim_note = """
Claim Note: Customer John Smith reported a vehicle accident on 15/06/2023.
Damage to front bumper and headlight. Policy AU-12345678, Claim Reference CL-87654.
"""

claim_results = ally.analyze_claim_note(claim_note)

for result in claim_results:
    print(f"Entity: {result.entity_type}, Text: {result.text}")

# Analyze an insurance email
email = """
From: customer@example.com
To: claims@insurance.com
Subject: Claim Update - Policy AU-12345678

My name is Jane Doe and I'm writing about my recent claim CL-87654.
"""

email_results = ally.analyze_insurance_email(email)

for result in email_results:
    print(f"Entity: {result.entity_type}, Text: {result.text}")
```

## Batch Processing Multiple Texts

For efficiency when processing multiple texts:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Multiple texts to analyze
texts = [
    "John Smith called about claim CL-12345.",
    "Jane Doe emailed about policy AU-67890.",
    "Alex Johnson reported an incident at 42 Main St, Sydney."
]

# Process all texts
all_results = []
for text in texts:
    results = ally.analyze(text)
    all_results.append(results)

# Count entities by type
entity_counts = {}
for results in all_results:
    for result in results:
        entity_type = result.entity_type
        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

print("Entity type counts:")
for entity_type, count in entity_counts.items():
    print(f"{entity_type}: {count}")
```

## Performance Considerations

For optimal performance when analyzing large amounts of text:

- Use `batch_size` parameter for large texts
- Consider creating a more focused configuration with only necessary entity types
- Use the appropriate spaCy model (en_core_web_sm for speed, en_core_web_lg for accuracy)

```python
from allyanonimiser import create_allyanonimiser, AnalysisConfig

# Create focused configuration
config = AnalysisConfig(
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
    min_score_threshold=0.7
)

# Create analyzer
ally = create_allyanonimiser()

# Analyze with chunking for efficiency
results = ally.analyze(
    text=very_long_text,
    config=config,
    batch_size=4096  # Process in 4KB chunks
)
```

## Next Steps

- [Anonymizing Text](anonymizing-text.md) - Learn how to anonymize the detected entities
- [Working with DataFrames](dataframes.md) - Process tabular data efficiently
- [Pattern Reference](../patterns/overview.md) - Explore all the built-in patterns