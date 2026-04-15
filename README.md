# Allyanonimiser

[![PyPI version](https://img.shields.io/badge/pypi-v3.3.0-blue)](https://pypi.org/project/allyanonimiser/3.3.0/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/srepho/Allyanonimiser/branch/main/graph/badge.svg)](https://codecov.io/gh/srepho/Allyanonimiser)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-online-brightgreen.svg)](https://srepho.github.io/Allyanonimiser/)

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

📖 **[Read the full documentation](https://srepho.github.io/Allyanonimiser/)**

## Version 3.3.0 — Major Restructure

**Breaking changes** — see [Migration Guide](#migrating-from-v2x) below.

### What's New
- **Layered package structure**: `core/` (detection/anonymization), `io/` (CSV/DataFrame/stream), `patterns/`, `utils/`
- **Explicit API**: `manage_acronyms(action="add", ...)` → `add_acronyms(...)`. Same for patterns and DataFrame ops
- **Configurable entity priority**: `DEFAULT_ENTITY_PRIORITY` dict controls overlap resolution; custom patterns beat generic NER
- **Deterministic hashing**: `hash` operator uses SHA-256 instead of Python's non-deterministic `hash()`
- **No print() in library code**: all output via `logging`
- **28x faster test suite**: spaCy model cached at module level
- **Tooling**: ruff + pyright replace black/isort/flake8/mypy; pyproject.toml is single source of truth

## Installation

```bash
# Basic installation
pip install allyanonimiser==3.3.0

# With stream processing support for large files
pip install "allyanonimiser[stream]==3.3.0"
```

**Prerequisites:**
- Python 3.12 or 3.13 (spaCy does not yet ship cp314 wheels)
- A spaCy language model for Named Entity Recognition (NER). The library
  defaults to the small model — install it with:

  ```bash
  python -m spacy download en_core_web_sm   # 44 MB, fast — the default
  ```

  Switch to the large model if you need higher NER recall on names,
  places, and organisations (see the table below):

  ```bash
  python -m spacy download en_core_web_lg   # 587 MB, higher accuracy
  ```

  Then pass it explicitly:

  ```python
  from allyanonimiser import create_allyanonimiser, SPACY_MODEL_ACCURATE
  ally = create_allyanonimiser(spacy_model=SPACY_MODEL_ACCURATE)
  ```

### Choosing a spaCy model

| | `SPACY_MODEL_FAST` (`en_core_web_sm`) | `SPACY_MODEL_ACCURATE` (`en_core_web_lg`) |
|---|---|---|
| **Default in v3.3+?** | yes | no |
| Download size | 44 MB | 587 MB |
| Resident memory | ~200 MB | ~1.5 GB |
| Cold start | ~0.5s | 2 – 5s |
| Pattern detection (TFN, ABN, MEDICARE, AU_PHONE, EMAIL, dates, etc.) | identical | identical |
| `PERSON` recall on insurance text | medium (~80%) | high (~92%) |
| `LOCATION` and `ORG` recall | noticeably worse | high |
| Serverless / Azure Functions friendliness | good | poor (size + cold start) |

**TL;DR:** the default works for most pipelines. Switch to `SPACY_MODEL_ACCURATE` only when missing a person's name or a city is a real cost in your downstream workflow.

> **Note:** Pass `spacy_model=None` to disable spaCy entirely — pattern detection (emails, phones, IDs, dates, etc.) keeps working.

### Verify Your Setup

After installation, verify that everything is properly configured:

```bash
python verify_setup.py
```

Or check spaCy status programmatically:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
status = ally.check_spacy_status()

if not status['is_loaded']:
    print(status['recommendation'])
else:
    print(f"✓ spaCy model loaded: {status['model_name']}")
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

## Package Structure (v3.0)

```
allyanonimiser/
├── __init__.py          # Public API and factory functions
├── allyanonimiser.py    # Allyanonimiser facade
├── core/                # Detection and anonymization engine
│   ├── analyzer.py      # EnhancedAnalyzer, RecognizerResult
│   ├── anonymizer.py    # EnhancedAnonymizer, DEFAULT_ENTITY_PRIORITY
│   ├── pattern_manager.py
│   ├── pattern_registry.py
│   ├── context_analyzer.py
│   └── validators.py
├── io/                  # File and DataFrame adapters
│   ├── csv_processor.py
│   ├── dataframe_processor.py
│   └── stream_processor.py
├── patterns/            # Built-in pattern definitions
│   ├── au_patterns.py
│   ├── insurance_patterns.py
│   └── general_patterns.py
├── utils/               # Helpers (spaCy, settings, text processing)
├── insurance/           # Domain-specific analyzers
└── reporting.py         # Report generation
```

## Migrating from v2.x

### Import path changes

```python
# v2.x
from allyanonimiser.enhanced_analyzer import EnhancedAnalyzer
from allyanonimiser.dataframe_processor import DataFrameProcessor
from allyanonimiser.validators import validate_regex

# v3.0
from allyanonimiser.core.analyzer import EnhancedAnalyzer
from allyanonimiser.io.dataframe_processor import DataFrameProcessor
from allyanonimiser.core.validators import validate_regex

# Top-level imports still work for the main API:
from allyanonimiser import create_allyanonimiser, EnhancedAnalyzer, DataFrameProcessor
```

### API changes

```python
# v2.x — stringly-typed
ally.manage_acronyms(action="add", data={"TPD": "Total and Permanent Disability"})
ally.manage_acronyms(action="get")
ally.manage_acronyms(action="remove", data=["TPD"])
ally.manage_patterns(action="create_from_examples", entity_type="MY_ID", examples=[...])
ally.manage_patterns(action="load", filepath="patterns.json")

# v3.0 — explicit methods
ally.add_acronyms({"TPD": "Total and Permanent Disability"})
ally.get_acronyms()
ally.remove_acronyms(["TPD"])
ally.create_pattern_from_examples(entity_type="MY_ID", examples=[...])
ally.load_patterns("patterns.json")
```

### Removed

- `setup.py` — use `pyproject.toml`
- `generators/` module (was stubs only)
- `InsuranceEmailAnalyzer`, `MedicalReportAnalyzer` (were stubs only)
- All deprecated wrapper methods (`set_acronym_dictionary`, `create_dataframe_processor`, etc.)

### New: Configurable entity priority

```python
from allyanonimiser.core.anonymizer import EnhancedAnonymizer, DEFAULT_ENTITY_PRIORITY

# Override priorities for your use case
custom_priority = {**DEFAULT_ENTITY_PRIORITY, "MY_CUSTOM_TYPE": 95}
anonymizer = EnhancedAnonymizer(analyzer=analyzer, entity_priority=custom_priority)
```

## Supported Entity Types

Allyanonimiser supports **38 different entity types** across four categories:

### Complete Entity Type Reference

<details>
<summary><b>🇦🇺 Australian-Specific Entities (13 types)</b></summary>

| Entity Type | Description | Example |
|-------------|-------------|---------|
| AU_TFN | Tax File Number | 123 456 789 |
| AU_PHONE | Phone Number | 0412 345 678, (02) 9876 5432 |
| AU_MEDICARE | Medicare Number | 2123 45678 1 |
| AU_DRIVERS_LICENSE | Driver's License | VIC1234567, NSW98765 |
| AU_ADDRESS | Street Address | 123 Collins St, Melbourne VIC 3000 |
| AU_POSTCODE | Postcode | 2000, 3000, 4000 |
| AU_BSB | Bank State Branch | 062-000, 123-456 |
| AU_ACCOUNT_NUMBER | Bank Account | 1234567890 |
| AU_ABN | Business Number | 11 222 333 444 |
| AU_ACN | Company Number | 123 456 789 |
| AU_PASSPORT | Passport Number | PA1234567, AB9876543 |
| AU_CENTRELINK_CRN | Centrelink Reference | 123 456 789A |
| VEHICLE_REGISTRATION | Vehicle Rego | ABC123, 1ABC23 |

</details>

<details>
<summary><b>🏢 Insurance-Specific Entities (8 types)</b></summary>

| Entity Type | Description | Example |
|-------------|-------------|---------|
| INSURANCE_POLICY_NUMBER | Policy Number | POL-12345678, AU-98765432 |
| INSURANCE_CLAIM_NUMBER | Claim Number | CL-23456789, C-987654 |
| VEHICLE_VIN | Vehicle ID Number | 1HGCM82633A123456 |
| INVOICE_NUMBER | Invoice/Quote | INV-2024001, Q-5678 |
| BROKER_CODE | Broker Code | BRK-1234 |
| VEHICLE_DETAILS | Vehicle Description | 2022 Toyota Camry |
| INCIDENT_DATE | Date of Incident | on 15/03/2024 |
| NAME_CONSULTANT | Consultant Name | Assigned To: Sarah Johnson |

</details>

<details>
<summary><b>👤 General PII Entities (8 types)</b></summary>

| Entity Type | Description | Example |
|-------------|-------------|---------|
| CREDIT_CARD | Credit Card | 4111 1111 1111 1111 |
| PERSON | Person Name | John Smith, Dr. Sarah O'Connor |
| EMAIL_ADDRESS | Email | john@example.com |
| DATE_OF_BIRTH | Date of Birth | DOB: 01/01/1990 |
| LOCATION | Location | Sydney, New South Wales |
| DATE | General Date | 15/03/2024, March 15, 2024 |
| MONEY_AMOUNT | Money Amount | $1,234.56 |
| ORGANIZATION | Organization | ABC Pty Ltd, XYZ Limited |

</details>

<details>
<summary><b>🤖 Additional spaCy NER Entities (9 types)</b></summary>

| Entity Type | Description | Example |
|-------------|-------------|---------|
| NUMBER | Numeric Value | 42, 1234 |
| TIME | Time Expression | 3:30 PM, 14:45 |
| PERCENT | Percentage | 25%, 99.9% |
| PRODUCT | Product Name | iPhone 15, Windows 11 |
| EVENT | Event Name | Olympic Games |
| WORK_OF_ART | Title | "The Great Gatsby" |
| LAW | Legal Document | Privacy Act 1988 |
| LANGUAGE | Language | English, Spanish |
| FACILITY | Building/Airport | Sydney Opera House |

</details>

### Quick Entity Detection Test

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Test text with multiple entity types
test_text = """
Customer: John Smith (TFN: 123 456 789)
Phone: 0412 345 678
Email: john.smith@example.com
Policy: POL-12345678
Address: 123 Collins St, Melbourne VIC 3000
Payment: $1,234.56 via Credit Card 4111 1111 1111 1111
"""

results = ally.analyze(test_text)

# Display detected entities by type
from collections import Counter
entity_types = Counter(r.entity_type for r in results)
print(f"Found {len(results)} entities across {len(entity_types)} types:")
for entity_type, count in entity_types.most_common():
    print(f"  {entity_type}: {count}")
```

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

### CSV File Processing

Allyanonimiser provides comprehensive CSV processing capabilities with automatic PII detection, preview modes, and streaming support for large files.

#### Basic CSV Processing

Process CSV files directly without manual DataFrame operations:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Auto-detect and process PII columns
result = ally.process_csv_file(
    input_file="customer_data.csv",
    output_file="customer_data_clean.csv"  # Auto-generated if not specified
)

print(f"Processed {result['rows_processed']} rows")
print(f"PII columns found: {result.get('auto_detected_columns', [])}")
print(f"Entities anonymized: {result['entities_found']}")
```

#### Auto-Detect PII Columns

Automatically identify which columns contain PII before processing:

```python
# Identify which columns contain PII
pii_columns = ally.detect_pii_columns("data.csv")
print(f"Columns with PII: {pii_columns}")
# Output: ['name', 'email', 'phone', 'notes']

# Process only the detected PII columns
result = ally.process_csv_file(
    input_file="data.csv",
    columns=pii_columns,  # Use detected columns
    output_file="data_anonymized.csv"
)
```

#### Preview Changes Before Processing

Preview what will be changed before processing the entire file:

```python
# Preview what will be changed
preview = ally.preview_csv_changes(
    "customer_data.csv",
    sample_rows=5  # Number of rows to preview
)

# Display preview
for _, row in preview.iterrows():
    print(f"{row['column']}: {row['original'][:30]}... → {row['anonymized'][:30]}...")

# If satisfied with preview, process the full file
if input("Proceed with anonymization? (y/n): ").lower() == 'y':
    ally.process_csv_file("customer_data.csv")
```

#### Stream Large CSV Files

Process multi-GB files efficiently using streaming:

```python
# Process multi-GB files in chunks
result = ally.stream_process_csv(
    input_file="huge_dataset.csv",  # 10GB file
    output_file="huge_dataset_clean.csv",
    columns=["customer_notes", "comments"],  # Specific columns to process
    chunk_size=10000,  # Process 10k rows at a time
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "AU_TFN": "hash"
    }
)

print(f"Processed {result['total_rows']} rows in {result['chunks_processed']} chunks")
print(f"Processing time: {result['processing_time']:.2f} seconds")
```

#### Process All CSV Files in Directory

Batch process multiple CSV files with a single command:

```python
# Batch process multiple CSV files
results = ally.process_csv_directory(
    input_dir="./raw_data/",
    output_dir="./anonymized_data/",
    columns_to_anonymize=["notes", "description"],  # Or None for auto-detect
    recursive=True,  # Include subdirectories
    generate_report=True  # Create processing report
)

print(f"Processed {len(results['files_processed'])} files")
print(f"Total entities found: {results['total_entities_found']}")
print(f"Report saved to: {results['report_file']}")
```

#### Advanced CSV Processing with Custom Configuration

```python
from allyanonimiser import create_allyanonimiser, AnonymizationConfig

ally = create_allyanonimiser()

# Configure anonymization for different entity types
config = AnonymizationConfig(
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "AU_TFN": "hash",
        "AU_MEDICARE": "redact",
        "CREDIT_CARD": "mask",
        "DATE_OF_BIRTH": "age_bracket"
    },
    age_bracket_size=5
)

# Process with custom configuration
result = ally.process_csv_file(
    input_file="sensitive_data.csv",
    output_file="processed_data.csv",
    config=config,
    columns=None,  # Auto-detect all PII columns
    sample_before_processing=True,  # Show preview first
    generate_stats=True  # Generate statistics report
)

# Access detailed statistics
if result.get('statistics'):
    stats = result['statistics']
    print(f"Entity type distribution:")
    for entity_type, count in stats['entity_counts'].items():
        print(f"  {entity_type}: {count}")
```

### CSV Processing Tutorial

This comprehensive tutorial demonstrates how to use Allyanonimiser's CSV processing features for various scenarios.

#### Tutorial 1: Basic CSV Anonymization

```python
from allyanonimiser import create_allyanonimiser
import pandas as pd

# Create sample CSV data
data = pd.DataFrame({
    'customer_id': [1001, 1002, 1003],
    'name': ['John Smith', 'Jane Doe', 'Robert Johnson'],
    'email': ['john.smith@example.com', 'jane.doe@test.com', 'r.johnson@company.org'],
    'phone': ['0412 345 678', '(02) 9876 5432', '0499 123 456'],
    'notes': [
        'TFN: 123 456 789, Lives at 123 Collins St Melbourne',
        'Medicare: 2123 45678 1, DOB: 15/06/1980',
        'Policy POL-12345678, Claim CL-987654'
    ]
})

# Save to CSV
data.to_csv('sample_customers.csv', index=False)

# Create Allyanonimiser instance
ally = create_allyanonimiser()

# Process the CSV file
result = ally.process_csv_file(
    input_file='sample_customers.csv',
    output_file='customers_anonymized.csv'
)

# Display results
print(f"Processing complete!")
print(f"Rows processed: {result['rows_processed']}")
print(f"Columns with PII: {result.get('pii_columns', [])}")
print(f"Total entities anonymized: {result['entities_found']}")

# Read and display anonymized data
anonymized_df = pd.read_csv('customers_anonymized.csv')
print("\nAnonymized data:")
print(anonymized_df.to_string())
```

#### Tutorial 2: Selective Column Processing

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# First, detect which columns contain PII
pii_columns = ally.detect_pii_columns('sample_customers.csv')
print(f"Detected PII columns: {pii_columns}")

# Let user select which columns to anonymize
print("\nSelect columns to anonymize:")
selected_columns = []
for col in pii_columns:
    if input(f"Anonymize '{col}'? (y/n): ").lower() == 'y':
        selected_columns.append(col)

# Process only selected columns
if selected_columns:
    result = ally.process_csv_file(
        input_file='sample_customers.csv',
        output_file='selective_anonymized.csv',
        columns=selected_columns,
        operators={
            "PERSON": "replace",
            "EMAIL_ADDRESS": "mask",
            "AU_TFN": "hash"
        }
    )
    print(f"\nAnonymized {len(selected_columns)} columns")
else:
    print("No columns selected for anonymization")
```

#### Tutorial 3: Handling Large Files with Streaming

```python
from allyanonimiser import create_allyanonimiser
import time

ally = create_allyanonimiser()

# For large files, use streaming to process in chunks
print("Processing large CSV file...")
start_time = time.time()

result = ally.stream_process_csv(
    input_file='large_dataset.csv',  # Assume this is a multi-GB file
    output_file='large_dataset_clean.csv',
    chunk_size=5000,  # Process 5000 rows at a time
    columns=['customer_notes', 'description', 'comments'],  # Focus on text columns
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "AU_TFN": "hash",
        "AU_MEDICARE": "redact"
    },
    progress_callback=lambda chunk_num, total_chunks: 
        print(f"Processing chunk {chunk_num}/{total_chunks}...")
)

elapsed_time = time.time() - start_time
print(f"\nProcessing complete!")
print(f"Total rows: {result['total_rows']}")
print(f"Processing time: {elapsed_time:.2f} seconds")
print(f"Rows per second: {result['total_rows']/elapsed_time:.0f}")
```

#### Tutorial 4: Batch Processing Directory

```python
from allyanonimiser import create_allyanonimiser
import os
from pathlib import Path

ally = create_allyanonimiser()

# Setup directories
input_dir = Path('./customer_data')
output_dir = Path('./anonymized_data')
output_dir.mkdir(exist_ok=True)

# Process all CSV files in directory
print(f"Processing all CSV files in {input_dir}...")

results = ally.process_csv_directory(
    input_dir=str(input_dir),
    output_dir=str(output_dir),
    columns_to_anonymize=None,  # Auto-detect for each file
    recursive=True,  # Include subdirectories
    file_pattern='*.csv',  # Process only CSV files
    generate_report=True,
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "AU_TFN": "hash",
        "AU_MEDICARE": "redact",
        "CREDIT_CARD": "mask"
    }
)

# Display summary
print(f"\nBatch processing complete!")
print(f"Files processed: {len(results['files_processed'])}")
print(f"Files skipped: {len(results.get('files_skipped', []))}")
print(f"Total entities found: {results['total_entities_found']}")

# Display per-file statistics
print("\nPer-file statistics:")
for file_info in results['file_statistics']:
    print(f"  {file_info['filename']}: {file_info['entities_found']} entities")

# Report location
if results.get('report_file'):
    print(f"\nDetailed report saved to: {results['report_file']}")
```

#### Tutorial 5: Custom Processing with Validation

```python
from allyanonimiser import create_allyanonimiser
import pandas as pd

ally = create_allyanonimiser()

# Define custom validation function
def validate_anonymization(original_df, anonymized_df):
    """Validate that anonymization was successful"""
    issues = []
    
    # Check that no original PII remains
    pii_patterns = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'tfn': r'\b\d{3}\s*\d{3}\s*\d{3}\b',
        'medicare': r'\b\d{4}\s*\d{5}\s*\d{1}\b'
    }
    
    for col in anonymized_df.columns:
        for row_idx, value in enumerate(anonymized_df[col]):
            if pd.notna(value):
                value_str = str(value)
                for pii_type, pattern in pii_patterns.items():
                    import re
                    if re.search(pattern, value_str):
                        issues.append(f"Found {pii_type} in row {row_idx}, column '{col}'")
    
    return issues

# Load original data
original_df = pd.read_csv('sample_customers.csv')

# Process with preview first
print("Previewing changes...")
preview = ally.preview_csv_changes('sample_customers.csv', sample_rows=3)
print(preview)

# Get user confirmation
if input("\nProceed with full anonymization? (y/n): ").lower() == 'y':
    # Process the file
    result = ally.process_csv_file(
        input_file='sample_customers.csv',
        output_file='validated_output.csv',
        operators={
            "DEFAULT": "replace"  # Use replace for all entity types
        }
    )
    
    # Load and validate anonymized data
    anonymized_df = pd.read_csv('validated_output.csv')
    validation_issues = validate_anonymization(original_df, anonymized_df)
    
    if validation_issues:
        print("\nValidation issues found:")
        for issue in validation_issues:
            print(f"  - {issue}")
    else:
        print("\n✓ Validation successful: No PII detected in output")
        print(f"✓ {result['entities_found']} entities successfully anonymized")
```

#### Tutorial 6: Generating Processing Reports

```python
from allyanonimiser import create_allyanonimiser
import json

ally = create_allyanonimiser()

# Enable detailed reporting
ally.start_new_report("csv_processing_session")

# Process multiple files with reporting
files_to_process = [
    'customers.csv',
    'transactions.csv',
    'support_tickets.csv'
]

for file_path in files_to_process:
    print(f"\nProcessing {file_path}...")
    result = ally.process_csv_file(
        input_file=file_path,
        output_file=f"anonymized_{file_path}",
        generate_stats=True
    )
    
    # Add to report
    ally.add_to_report({
        'file': file_path,
        'rows': result['rows_processed'],
        'entities': result['entities_found'],
        'columns_processed': result.get('pii_columns', [])
    })

# Generate comprehensive report
report = ally.get_report()
summary = report.get_summary()

print("\n" + "="*50)
print("PROCESSING REPORT SUMMARY")
print("="*50)
print(f"Total files processed: {len(files_to_process)}")
print(f"Total entities anonymized: {summary['total_entities']}")
print(f"Average processing time: {summary['avg_processing_time']*1000:.2f} ms")

# Export detailed report
report.export_report("csv_processing_report.html", "html")
report.export_report("csv_processing_report.json", "json")

print(f"\nReports saved:")
print(f"  - csv_processing_report.html (visual report)")
print(f"  - csv_processing_report.json (detailed data)")
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