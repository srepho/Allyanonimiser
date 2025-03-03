# Allyanonimiser

[![PyPI version](https://img.shields.io/badge/pypi-v2.0.0-blue)](https://pypi.org/project/allyanonimiser/2.0.0/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

## Installation

```bash
# Basic installation
pip install allyanonimiser==2.0.0

# With stream processing support for large files
pip install "allyanonimiser[stream]==2.0.0"

# With LLM integration for advanced pattern generation
pip install "allyanonimiser[llm]==2.0.0"

# Complete installation with all optional dependencies
pip install "allyanonimiser[stream,llm]==2.0.0"
```

**Prerequisites:**
- Python 3.10 or higher
- A spaCy language model (recommended):
  ```bash
  python -m spacy download en_core_web_lg  # Recommended
  # OR for limited resources:
  python -m spacy download en_core_web_sm  # Smaller model
  ```

## Quick Start

```python
from allyanonimiser import create_allyanonimiser

# Create the Allyanonimiser instance with default settings
ally = create_allyanonimiser()

# Analyze text
results = ally.analyze(
    text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123."
)

# Print results
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")

# Anonymize text
anonymized = ally.anonymize(
    text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123.",
    operators={
        "POLICY_NUMBER": "mask",  # Replace with asterisks
        "VEHICLE_REGISTRATION": "replace"  # Replace with <VEHICLE_REGISTRATION>
    }
)

print(anonymized["text"])
# Output: "Please reference your policy ********** for claims related to your vehicle rego <VEHICLE_REGISTRATION>."
```

### Adding Custom Patterns

```python
from allyanonimiser import create_allyanonimiser

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Add a custom pattern with regex
ally.add_pattern({
    "entity_type": "REFERENCE_CODE",
    "patterns": [r"REF-\d{6}-[A-Z]{2}", r"Reference\s+#\d{6}"],
    "context": ["reference", "code", "ref"],
    "name": "Reference Code"
})

# Generate a pattern from examples
ally.create_pattern_from_examples(
    entity_type="EMPLOYEE_ID",
    examples=["EMP00123", "EMP45678", "EMP98765"],
    context=["employee", "staff", "id"],
    generalization_level="medium"
)

# Test custom patterns
text = "Employee EMP12345 created REF-123456-AB for the project."
results = ally.analyze(text)
for result in results:
    print(f"Found {result.entity_type}: {result.text}")
```

## New in Version 2.0.0: Comprehensive Reporting System

Allyanonimiser now includes a comprehensive reporting system that allows you to track, analyze, and visualize anonymization activities.

```python
from allyanonimiser import create_allyanonimiser

# Create instance
ally = create_allyanonimiser()

# Start a new report session
ally.start_new_report("my_session")

# Process multiple texts
texts = [
    "Customer John Smith (DOB: 15/06/1980) called about claim CL-12345.",
    "Jane Doe (email: jane.doe@example.com) requested policy information.",
    "Claims assessor reviewed case for Robert Johnson (ID: 987654321)."
]

for i, text in enumerate(texts):
    ally.anonymize(
        text=text,
        operators={
            "PERSON": "replace",
            "EMAIL_ADDRESS": "mask",
            "DATE_OF_BIRTH": "age_bracket"
        },
        document_id=f"doc_{i+1}"
    )

# Get report summary
report = ally.get_report()
summary = report.get_summary()

print(f"Total documents processed: {summary['total_documents']}")
print(f"Total entities detected: {summary['total_entities']}")
print(f"Entities per document: {summary['entities_per_document']:.2f}")
print(f"Anonymization rate: {summary['anonymization_rate']*100:.2f}%")
print(f"Average processing time: {summary['avg_processing_time']*1000:.2f} ms")

# Export report to different formats
report.export_report("report.html", "html")  # Rich HTML visualization
report.export_report("report.json", "json")  # Detailed JSON data
report.export_report("report.csv", "csv")    # CSV statistics

# In Jupyter notebooks, display rich visualizations
# ally.display_report_in_notebook()
```

## Features

- **Australian-Focused PII Detection**: Specialized patterns for TFNs, Medicare numbers, vehicle registrations, addresses, and more
- **Insurance Industry Specialization**: Detect policy numbers, claim references, and other industry-specific identifiers
- **Multiple Entity Types**: Comprehensive detection of general and specialized PII
- **Flexible Anonymization**: Multiple anonymization operators (replace, mask, redact, hash, and more)
- **Stream Processing**: Memory-efficient processing of large files with chunking support
- **Reporting System**: Comprehensive tracking and visualization of anonymization activities
- **Jupyter Integration**: Rich visualization capabilities in notebook environments
- **DataFrame Support**: Process pandas DataFrames with batch processing and multi-processing support
- **Configuration Export**: Share settings between environments with export/import functionality
- **Pattern Generation**: Create patterns from examples with various generalization levels
- **Customizable**: Extend with your own patterns and entity types

## Usage Examples

### Pattern Management

```python
from allyanonimiser import create_allyanonimiser

# Create an instance
ally = create_allyanonimiser()

# 1. Adding pattern to an existing group in pattern files
# If you want to contribute a new pattern to the codebase,
# edit the appropriate file in patterns/ directory:
#  - patterns/au_patterns.py: For Australian-specific patterns
#  - patterns/general_patterns.py: For general PII patterns 
#  - patterns/insurance_patterns.py: For insurance-specific patterns

# 2. Using custom patterns without modifying code
# Add a custom pattern with detailed options
ally.add_pattern({
    "entity_type": "COMPANY_PROJECT_ID",
    "patterns": [
        r"PRJ-\d{4}-[A-Z]{3}",       # Format: PRJ-1234-ABC
        r"Project\s+ID:\s*(\d{4})"   # Format: Project ID: 1234
    ],
    "context": ["project", "id", "identifier", "code"],
    "name": "Company Project ID",
    "score": 0.85,                   # Confidence score (0-1)
    "language": "en",                # Language code
    "description": "Internal project identifier format"
})

# 3. Save patterns for reuse
ally.export_config("company_patterns.json")

# 4. Load saved patterns in another session
new_ally = create_allyanonimiser(settings_path="company_patterns.json")

# 5. Pattern testing and validation
from allyanonimiser.validators import test_pattern_against_examples

# Test if a pattern works against examples
results = test_pattern_against_examples(
    pattern=r"PRJ-\d{4}-[A-Z]{3}",
    positive_examples=["PRJ-1234-ABC", "PRJ-5678-XYZ"],
    negative_examples=["PRJ-123-AB", "PROJECT-1234"]
)
print(f"Pattern is valid: {results['is_valid']}")
print(f"Diagnostic info: {results['message']}")
```

### Analyze Text for PII Entities

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Analyze text
results = ally.analyze(
    text="Customer John Smith (TFN: 123 456 789) reported an incident on 15/06/2023 at his residence in Sydney NSW 2000."
)

# Print detected entities
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```

### Anonymize Text with Different Operators

```python
from allyanonimiser import create_allyanonimiser, AnonymizationConfig

ally = create_allyanonimiser()

# Using configuration object
config = AnonymizationConfig(
    operators={
        "PERSON": "replace",           # Replace with <PERSON>
        "AU_TFN": "hash",              # Replace with SHA-256 hash
        "DATE": "redact",              # Replace with [REDACTED]
        "AU_ADDRESS": "mask",          # Replace with *****
        "DATE_OF_BIRTH": "age_bracket" # Replace with age bracket (e.g., <40-45>)
    },
    age_bracket_size=5  # Size of age brackets
)

# Anonymize text
anonymized = ally.anonymize(
    text="Customer John Smith (TFN: 123 456 789) reported an incident on 15/06/2023. He was born on 05/08/1982 and lives at 42 Main St, Sydney NSW 2000.",
    config=config
)

print(anonymized["text"])
```

### Process Text with Analysis and Anonymization

```python
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig

ally = create_allyanonimiser()

# Configure analysis
analysis_config = AnalysisConfig(
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "DATE_OF_BIRTH"],
    min_score_threshold=0.7
)

# Configure anonymization
anonymization_config = AnonymizationConfig(
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "PHONE_NUMBER": "redact",
        "DATE_OF_BIRTH": "age_bracket"
    }
)

# Process text (analyze + anonymize)
result = ally.process(
    text="Customer Jane Doe (jane.doe@example.com) called on 0412-345-678 regarding her DOB: 22/05/1990.",
    analysis_config=analysis_config,
    anonymization_config=anonymization_config
)

# Access different parts of the result
print("Anonymized text:")
print(result["anonymized"])

print("\nDetected entities:")
for entity in result["analysis"]["entities"]:
    print(f"{entity['entity_type']}: {entity['text']} (score: {entity['score']:.2f})")

print("\nPII-rich segments:")
for segment in result["segments"]:
    print(f"Original: {segment['text']}")
    print(f"Anonymized: {segment['anonymized']}")
```

## Working with DataFrames

```python
import pandas as pd
from allyanonimiser import create_allyanonimiser

# Create DataFrame
df = pd.DataFrame({
    "id": [1, 2, 3],
    "notes": [
        "Customer John Smith (DOB: 15/6/1980) called about policy POL-123456.",
        "Jane Doe (email: jane.doe@example.com) requested a refund.",
        "Alex Johnson from Sydney NSW 2000 reported an incident."
    ]
})

# Create Allyanonimiser
ally = create_allyanonimiser()

# Anonymize a specific column
anonymized_df = ally.process_dataframe(
    df, 
    column="notes", 
    operation="anonymize",
    output_column="anonymized_notes",  # New column for anonymized text
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "PHONE_NUMBER": "redact"
    }
)

# Display result
print(anonymized_df[["id", "notes", "anonymized_notes"]])
```

## Generating Reports

```python
from allyanonimiser import create_allyanonimiser
import os

# Create output directory
os.makedirs("output", exist_ok=True)

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Start a new report session
ally.start_new_report(session_id="example_session")

# Configure anonymization
anonymization_config = {
    "operators": {
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "PHONE_NUMBER": "redact",
        "AU_ADDRESS": "replace",
        "DATE_OF_BIRTH": "age_bracket",
        "AU_TFN": "hash",
        "AU_MEDICARE": "mask"
    },
    "age_bracket_size": 10
}

# Process a batch of files
result = ally.process_files(
    file_paths=["data/sample1.txt", "data/sample2.txt", "data/sample3.txt"],
    output_dir="output/anonymized",
    anonymize=True,
    operators=anonymization_config["operators"],
    report=True,
    report_output="output/report.html",
    report_format="html"
)

# Display summary
print(f"Processed {result['total_files']} files")
print(f"Detected {result['report']['total_entities']} entities")
print(f"Average processing time: {result['report']['avg_processing_time']*1000:.2f} ms")
```

## In Jupyter Notebooks

```python
from allyanonimiser import create_allyanonimiser
import pandas as pd
import matplotlib.pyplot as plt

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Start a report session and process some texts
# ... processing code ...

# Display rich interactive report
ally.display_report_in_notebook()

# Access report data programmatically
report = ally.get_report()
summary = report.get_summary()

# Create custom visualizations
entity_counts = summary['entity_counts']
plt.figure(figsize=(10, 6))
plt.bar(entity_counts.keys(), entity_counts.values())
plt.title('Entity Type Distribution')
plt.xlabel('Entity Type')
plt.ylabel('Count')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

## Documentation

For complete documentation, examples, and advanced usage, visit the [GitHub repository](https://github.com/srepho/Allyanonimiser).

## License

This project is licensed under the MIT License - see the LICENSE file for details.