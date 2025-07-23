# Allyanonimiser

[![PyPI version](https://img.shields.io/badge/pypi-v2.3.0-blue)](https://pypi.org/project/allyanonimiser/2.3.0/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/srepho/Allyanonimiser/branch/main/graph/badge.svg)](https://codecov.io/gh/srepho/Allyanonimiser)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-online-brightgreen.svg)](https://srepho.github.io/Allyanonimiser/)

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

📖 **[Read the full documentation](https://srepho.github.io/Allyanonimiser/)**

## Version 2.3.0 - Comprehensive False Positive Filtering & Enhanced Pattern Detection

### What's New in v2.3.0
- **Enhanced False Positive Filtering**: Comprehensive filtering for PERSON and LOCATION entities eliminates common misdetections
- **Improved Pattern Detection**: Fixed BSB/Account Number detection, enhanced Organization detection for Pty Ltd companies
- **NAME_CONSULTANT Pattern**: New pattern for detecting consultant/agent names with proper boundary detection
- **Refined Vehicle Registration**: More accurate detection with reduced false positives from all-caps text
- **Better Medicare Support**: Fixed Medicare number detection and validation
- **Enhanced Date Handling**: Improved date validation to avoid false positives (e.g., "NSW 2000" no longer detected as DATE)
- **Service Number Detection**: Added support for Australian service numbers (1300, 1800, 13xx)
- **Context-Aware Detection**: New context analyzer improves entity detection accuracy
- **Multiple Entity Masking**: Robust support for masking multiple entity types simultaneously

## Installation

```bash
# Basic installation
pip install allyanonimiser==2.3.0

# With stream processing support for large files
pip install "allyanonimiser[stream]==2.3.0"

# With LLM integration for advanced pattern generation
pip install "allyanonimiser[llm]==2.3.0"

# Complete installation with all optional dependencies
pip install "allyanonimiser[stream,llm]==2.3.0"
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
    generalization_level="medium"  # Options: none, low, medium, high
)

# Test custom patterns
text = "Employee EMP12345 created REF-123456-AB for the project."
results = ally.analyze(text)
for result in results:
    print(f"Found {result.entity_type}: {result.text}")
```

## Built-in Pattern Reference

### Australian Patterns

| Entity Type | Description | Example Pattern | Pattern File |
|-------------|-------------|----------------|-------------|
| AU_TFN | Australian Tax File Number | `\b\d{3}\s*\d{3}\s*\d{3}\b` | au_patterns.py |
| AU_PHONE | Australian Phone Number | `\b(?:\+?61\|0)4\d{2}\s*\d{3}\s*\d{3}\b` | au_patterns.py |
| AU_MEDICARE | Australian Medicare Number | `\b\d{4}\s*\d{5}\s*\d{1}\b` | au_patterns.py |
| AU_DRIVERS_LICENSE | Australian Driver's License | Various formats including<br>`\b\d{8}\b` (NSW)<br>`\b\d{4}[a-zA-Z]{2}\b` (NSW legacy) | au_patterns.py |
| AU_ADDRESS | Australian Address | Address patterns with street names | au_patterns.py |
| AU_POSTCODE | Australian Postcode | `\b\d{4}\b` | au_patterns.py |
| AU_BSB_ACCOUNT | Australian BSB and Account Number | `\b\d{3}-\d{3}\s*\d{6,10}\b` | au_patterns.py |
| AU_ABN | Australian Business Number | `\b\d{2}\s*\d{3}\s*\d{3}\s*\d{3}\b` | au_patterns.py |
| AU_PASSPORT | Australian Passport Number | `\b[A-Za-z]\d{8}\b` | au_patterns.py |

### General Patterns

| Entity Type | Description | Example Pattern | Pattern File |
|-------------|-------------|----------------|-------------|
| CREDIT_CARD | Credit Card Number | `\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b` | general_patterns.py |
| PERSON | Person Name | Name patterns with context | general_patterns.py |
| EMAIL_ADDRESS | Email Address | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z\|a-z]{2,}\b` | general_patterns.py |
| DATE_OF_BIRTH | Date of Birth | `\bDOB:\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b` | general_patterns.py |
| LOCATION | Location | City and location patterns | general_patterns.py |
| DATE | Date | `\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b` | general_patterns.py |
| MONETARY_VALUE | Money Amount | `\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b` | general_patterns.py |
| ORGANIZATION | Organization | Organization name patterns | general_patterns.py |

### Insurance Patterns

| Entity Type | Description | Example Pattern | Pattern File |
|-------------|-------------|----------------|-------------|
| INSURANCE_POLICY_NUMBER | Insurance Policy Number | `\b(?:POL\|P\|Policy)[- ]?\d{6,9}\b` | insurance_patterns.py |
| INSURANCE_CLAIM_NUMBER | Insurance Claim Number | `\b(?:CL\|C)[- ]?\d{6,9}\b` | insurance_patterns.py |
| INSURANCE_MEMBER_NUMBER | Insurance Member Number | Member ID patterns | insurance_patterns.py |
| INSURANCE_GROUP_NUMBER | Group Policy Number | Group policy patterns | insurance_patterns.py |
| VEHICLE_IDENTIFIER | Vehicle ID (VIN, plates) | `\b[A-HJ-NPR-Z0-9]{17}\b` | insurance_patterns.py |
| CASE_REFERENCE | Case Reference Numbers | Case ID patterns | insurance_patterns.py |
| VEHICLE_DETAILS | Vehicle Details | Make/model patterns | insurance_patterns.py |

## Features

- **Australian-Focused PII Detection**: Specialized patterns for TFNs, Medicare numbers, vehicle registrations, addresses, and more
- **Insurance Industry Specialization**: Detect policy numbers, claim references, and other industry-specific identifiers
- **Multiple Entity Types**: Comprehensive detection of general and specialized PII
- **Flexible Anonymization**: Multiple anonymization operators (replace, mask, redact, hash, and more)
- **Stream Processing**: Memory-efficient processing of large files with chunking support
- **Reporting System**: Comprehensive tracking and visualization of anonymization activities
- **Jupyter Integration**: Rich visualization capabilities in notebook environments
- **DataFrame Support**: Process pandas DataFrames with batch processing and multi-processing support
- **Robust Detection**: Enhanced validation and context-aware detection to reduce false positives
- **Overlapping Entity Handling**: Smart resolution of overlapping entities for clean anonymization
- **Pattern Loading**: Automatic loading of all default patterns (Australian, Insurance, General)
- **Improved Medicare Detection**: Fixed detection and validation for Australian Medicare numbers
- **Multiple Entity Masking**: Simultaneous masking of multiple entity types with different operators

## Usage Examples

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

### Working with DataFrames

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

## Pattern Generalization Levels

When creating patterns from examples using `create_pattern_from_examples()`, you can specify a generalization level that controls how flexible the resulting pattern will be:

| Level | Description | Example Input | Generated Pattern | Will Match |
|-------|-------------|--------------|------------------|------------|
| `none` | Exact matching only | "EMP12345" | `\bEMP12345\b` | Only "EMP12345" |
| `low` | Basic generalization | "EMP12345" | `\bEMP\d{5}\b` | "EMP12345", "EMP67890", but not "EMP123" |
| `medium` | Moderate flexibility | "EMP12345" | `\bEMP\d+\b` | "EMP12345", "EMP123", "EMP9", but not "EMPLOYEE12345" |
| `high` | Maximum flexibility | "EMP12345" | `\b[A-Z]{3}\d+\b` | "EMP12345", "ABC123", etc. |

Higher generalization levels detect more variants but may increase false positives. Choose the appropriate level based on your needs for precision vs. recall.

## Anonymization Operators

The package supports several anonymization operators that control how detected entities are transformed:

| Operator | Description | Example | Result |
|----------|-------------|---------|--------|
| `replace` | Replace with entity type | "John Smith" | `<PERSON>` |
| `redact` | Fully redact the entity | "john.smith@example.com" | `[REDACTED]` |
| `mask` | Partially mask while preserving structure | "john.smith@example.com" | `j***.s****@e******.com` |
| `hash` | Replace with consistent hash | "John Smith" | `7f9d6a...` (same for all "John Smith") |
| `encrypt` | Encrypt with a key (recoverable) | "John Smith" | `AES256:a7f9c...` |
| `age_bracket` | Convert dates to age brackets | "DOB: 15/03/1980" | `DOB: 40-44` |
| `custom` | User-defined function | (depends on function) | (custom output) |

Example usage:

```python
result = ally.anonymize(
    text="Please contact John Smith at john.smith@example.com",
    operators={
        "PERSON": "replace",       # Replace with entity type
        "EMAIL_ADDRESS": "mask",   # Partially mask the email
        "PHONE_NUMBER": "redact",  # Fully redact phone numbers
        "DATE_OF_BIRTH": "age_bracket"  # Convert DOB to age bracket
    }
)
```

### Custom Operator Example

The custom operator allows you to define your own transformation function:

```python
from allyanonimiser import create_allyanonimiser

# Create a custom transformation function
def randomize_names(entity_text, entity_type):
    """Replace person names with random names from a predefined list."""
    if entity_type != "PERSON":
        return entity_text
        
    # Simple list of random replacement names
    replacements = ["Alex Taylor", "Sam Johnson", "Jordan Lee", "Casey Brown"]
    
    # Use hash of original name to consistently select the same replacement
    import hashlib
    hash_val = int(hashlib.md5(entity_text.encode()).hexdigest(), 16)
    index = hash_val % len(replacements)
    
    return replacements[index]

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Use the custom operator
result = ally.anonymize(
    text="Customer John Smith sent an email to Mary Johnson about policy POL-123456.",
    operators={
        "PERSON": randomize_names,  # Pass the function directly
        "POLICY_NUMBER": "mask"     # Other operators work as usual
    }
)

print(result["text"])
# Output: "Customer Alex Taylor sent an email to Sam Johnson about policy ***-******."
```

Custom operators are powerful for specialized anonymization needs like:
- Generating synthetic but realistic replacements
- Contextual anonymization based on entity values
- Domain-specific transformations (e.g., preserving data distributions)
- Implementing differential privacy mechanisms

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

## Advanced Features

### Generating Reports

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
print(f"Average processing time: {result['report']['report']['avg_processing_time']*1000:.2f} ms")
```

### Comprehensive Reporting System

Allyanonimiser includes a comprehensive reporting system that allows you to track, analyze, and visualize anonymization activities.

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
```

### In Jupyter Notebooks

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

## What's New in Version 2.1.0

- Added support for NSW legacy driver's license pattern
- Improved pattern recognition for Australian TFNs
- Enhanced handling of date formats
- Fixed issues with BSB recognition
- Added more comprehensive test suite for Australian patterns
- Performance improvements for large file processing

For older versions and detailed change history, see the [CHANGELOG.md](CHANGELOG.md) file.

## Documentation

For complete documentation, examples, and advanced usage, visit our [documentation site](https://srepho.github.io/Allyanonimiser/):

- [Installation Guide](https://srepho.github.io/Allyanonimiser/getting-started/installation/)
- [Quick Start Tutorial](https://srepho.github.io/Allyanonimiser/getting-started/quick-start/)
- [Pattern Reference](https://srepho.github.io/Allyanonimiser/patterns/overview/)
- [Anonymization Operators](https://srepho.github.io/Allyanonimiser/advanced/anonymization-operators/)
- [API Reference](https://srepho.github.io/Allyanonimiser/api/main/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.