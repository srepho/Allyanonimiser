# Allyanonimiser

[![PyPI version](https://img.shields.io/badge/pypi-v1.2.0-blue)](https://pypi.org/project/allyanonimiser/1.2.0/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

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
```

### DataFrame Processing

```python
import pandas as pd
from allyanonimiser import create_allyanonimiser

# Create a DataFrame with potentially sensitive data
df = pd.DataFrame({
    'id': range(1, 5),
    'name': ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Williams'],
    'note': [
        'Customer called about policy POL123456. DOB: 15/07/1982.',
        'Email from jane@example.com about claim CL789012. Lives at 10 Queen St, Sydney NSW 2000.',
        'Medicare number 2123 45678 1 received for claim. Patient born 1990-03-22.',
        'TFN: 123 456 789. Contact at 42 Example St, Melbourne VIC 3000. Age: 45.'
    ]
})

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Process a DataFrame (anonymize sensitive data)
anonymized_df = ally.anonymize_dataframe(
    df, 
    'note',
    operators={
        'PERSON': 'replace',
        'EMAIL_ADDRESS': 'mask',
        'INSURANCE_POLICY_NUMBER': 'redact',
        'INSURANCE_CLAIM_NUMBER': 'redact',
        'DATE_OF_BIRTH': 'age_bracket'  # Convert DOBs to age brackets
    },
    active_entity_types=[   # Only detect these entity types
        'PERSON', 'EMAIL_ADDRESS', 'INSURANCE_POLICY_NUMBER', 
        'INSURANCE_CLAIM_NUMBER', 'DATE_OF_BIRTH', 'AU_ADDRESS',
        'AU_POSTCODE', 'AU_MEDICARE', 'AU_TFN'
    ],
    age_bracket_size=5,     # Use 5-year brackets (default)
    keep_postcode=True      # Preserve postcodes in addresses (default)
)
```

### Stream Processing for Very Large Files

```python
from allyanonimiser import create_allyanonimiser, StreamProcessor

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Create a StreamProcessor for handling very large files
stream_processor = StreamProcessor(allyanonimiser=ally)

# Process a multi-gigabyte CSV file with minimal memory impact
result = stream_processor.process_large_file(
    file_path="very_large_dataset.csv",
    text_columns=["notes", "comments"],
    output_path="output/anonymized_dataset.csv",
    active_entity_types=[
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", 
        "AU_ADDRESS", "AU_MEDICARE", "AU_TFN"
    ],
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "redact",
        "PHONE_NUMBER": "mask",
        "AU_ADDRESS": "replace",
        "AU_MEDICARE": "mask",
        "AU_TFN": "redact"
    },
    chunk_size=10000,  # Process 10,000 rows at a time
    save_entities=True,
    entities_output_path="output/detected_entities.csv"
)

# Get statistics from the processing job
print(f"Processed {result['total_rows_processed']} rows")
print(f"Detected {result['total_entities_detected']} entities")
print(f"Output saved to {result['output_file']}")
print(f"Entities saved to {result['entities_file']}")
```

For more custom processing and greater control, you can use the streaming API directly:

```python
# Process a file in chunks with custom handling for each chunk
for chunk in stream_processor.stream_from_file(
    file_path="very_large_dataset.csv",
    text_columns=["notes"],
    active_entity_types=["PERSON", "EMAIL_ADDRESS"],
    operators={"PERSON": "replace", "EMAIL_ADDRESS": "mask"},
    chunk_size=5000,
    progress_bar=True
):
    # Each chunk contains processed data and detected entities
    processed_df = chunk['dataframe']
    entities_df = chunk['entities']
    
    # Perform custom processing on each chunk
    # For example, analyze entity distributions
    entity_counts = entities_df.groupby('entity_type').size()
    print(f"Entities in chunk: {entity_counts}")
    
    # Or save each chunk separately
    processed_df.to_csv(f"output/chunk_{idx}.csv", index=False)
```

### Configuration and Pattern Management

```python
from allyanonimiser import create_allyanonimiser

# Create with default settings
ally = create_allyanonimiser()

# Add a custom pattern
ally.add_pattern({
    "entity_type": "INTERNAL_REFERENCE",
    "patterns": [r"REF-\d{5}", r"Reference:\s*([A-Z0-9-]+)"],
    "context": ["internal", "reference", "ref"],
    "name": "Internal Reference Number"
})

# Save configuration for reuse by team members
ally.export_config("company_config.json")
```

### Sharing and Controlling Configurations

```python
from allyanonimiser import create_allyanonimiser

# Load a shared configuration
ally = create_allyanonimiser(settings_path="company_config.json")

# Enable only specific entity types for this session
active_entities = ["PERSON", "INTERNAL_REFERENCE", "EMAIL_ADDRESS"]
result = ally.anonymize(
    text="Reference: REF-12345 submitted by John Smith (john.smith@example.com)",
    operators={"PERSON": "redact"},
    active_entity_types=active_entities  # Only these entities will be detected
)

print(result["text"])
# Output: "Reference: <INTERNAL_REFERENCE> submitted by [REDACTED] ([REDACTED])"

# Get available entity types to selectively enable/disable
available_entities = ally.get_available_entity_types()
print(f"Available entity types: {list(available_entities.keys())}")

# Update an existing configuration with new patterns
ally.add_pattern({
    "entity_type": "PROJECT_CODE",
    "patterns": [r"PROJ-\d{4}"],
    "name": "Project Code"
})

# Export as a new version
ally.export_config("company_config_v2.json")
```

## Simplified API (v1.1.0)

Version 1.1.0 introduces a simplified API with configuration objects and unified interface methods:

```python
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig

# Create instance
ally = create_allyanonimiser()

# Use configuration objects for cleaner parameter organization
analysis_config = AnalysisConfig(
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
    min_score_threshold=0.8,
    expand_acronyms=True
)

anonymization_config = AnonymizationConfig(
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask", 
        "PHONE_NUMBER": "redact"
    },
    age_bracket_size=10,
    keep_postcode=True
)

# Process text with configuration objects
result = ally.process(
    text="Customer John Smith (john.smith@example.com) called from 0412 345 678.",
    analysis_config=analysis_config,
    anonymization_config=anonymization_config
)

# Unified pattern management interface
ally.manage_patterns(
    action="create_from_examples",
    entity_type="CUSTOMER_ID",
    examples=["CID-12345", "CID-67890"],
    generalization_level="medium"
)

# Unified acronym management interface
ally.manage_acronyms(
    action="add",
    data={"POL": "Policy", "CL": "Claim", "DOB": "Date of Birth"}
)

# Unified DataFrame processing interface
df_result = ally.process_dataframe(
    df=my_dataframe,
    column="notes",
    operation="anonymize",
    analysis_config=analysis_config,
    anonymization_config=anonymization_config
)
```

See `example_simplified_api.py` for a complete demonstration of the simplified API.

## Installation

### Basic Installation

```bash
# Basic installation
pip install allyanonimiser

# Download a spaCy language model (required)
python -m spacy download en_core_web_lg  # Recommended
# OR for limited resources:
python -m spacy download en_core_web_sm  # Smaller model
```

### Optional Features

```bash
# For stream processing of very large files (recommended for large datasets)
pip install allyanonimiser[stream]

# For LLM augmentation capabilities
pip install allyanonimiser[llm]

# For development and testing
pip install allyanonimiser[dev]
```

## Features

- **Australian-Specific PII Detection**: Specialized recognizers for Australian TFNs, Medicare numbers, driver's licenses, and other Australian-specific identifiers.
- **Insurance Industry Focus**: Recognition of policy numbers, claim references, vehicle identifiers, and other insurance-specific data.
- **Long Text Processing**: Optimized for processing lengthy free-text fields like claim notes, medical reports, and emails.
- **DataFrames and Large Files**: Process pandas DataFrames with PyArrow acceleration and stream very large files with Polars integration.
- **Stream Processing**: Memory-efficient handling of multi-gigabyte CSV files with chunk-by-chunk processing.
- **Custom Pattern Creation**: Easy creation of custom entity recognizers for organization-specific data.
- **Synthetic Data Generation**: Generate realistic Australian test data for validation.
- **LLM Integration**: Use Language Models to create challenging datasets for testing.
- **Extensible Architecture**: Built on Presidio and spaCy with a modular, extensible design.

## Version History

### Version 1.2.0 - Stream Processing for Large Files

This version introduces a simplified, more consistent API and adds powerful stream processing capabilities for very large files.

#### Key Features

1. **Unified Interface Methods**:
   - Added `manage_acronyms(action, data, ...)` to replace multiple acronym methods
   - Added `manage_patterns(action, data, ...)` to replace multiple pattern methods
   - Added unified `process_dataframe(operation, ...)` to consolidate DataFrame methods
   - Reduced total API method count while preserving all functionality
   
2. **Configuration Objects**:
   - Added `AnalysisConfig` for grouping analysis parameters
   - Added `AnonymizationConfig` for grouping anonymization parameters
   - Improved parameter organization and reduced parameter count in method signatures
   - Enhanced readability and maintainability
   
3. **Stream Processing for Very Large Files**:
   - Added `StreamProcessor` class for memory-efficient processing
   - Implemented chunk-by-chunk processing with minimal memory impact
   - Added adaptive chunk sizing based on data volume
   - Created low-level streaming API for custom chunk processing
   - Added comprehensive error handling for stream processing failures
   - Implemented graceful fallbacks when Polars is not available
   - Added stream processing example in `example_stream_processing.py`
   
4. **Improved Developer Experience**:
   - New example scripts demonstrating the simplified API and stream processing
   - Maintained backward compatibility with deprecated method support
   - Comprehensive docstrings for all new methods
   - Consolidated parameter handling for better code organization

### Version 1.0.0 - Simplified API and Enhanced Features

This version introduces a simplified API with cleaner function names and adds powerful new features for more flexible anonymization. This is a breaking change from previous versions.

#### Key Updates

1. **Simplified API**:
   - Removed legacy analyzer factory functions (`create_au_analyzer`, `create_insurance_analyzer`, `create_au_insurance_analyzer`) 
   - Added cleaner `create_analyzer()` function as the main entry point
   - Streamlined and simplified internal implementation
   
2. **New Features**:
   - **Address Postcode Preservation**: Preserve postcodes when anonymizing addresses with the `keep_postcode` parameter
   - **Age Bracketing**: Convert dates of birth to age brackets with configurable bracket sizes using the `age_bracket` operator
   - Improved error handling with informative error messages
   - Enhanced input validation for more robust operation
   
3. **Major Version Upgrade**:
   - Increased major version number to 1.0.0 to indicate production readiness
   - Removed backward compatibility with 0.x versions
   - Improved documentation and examples

### Version 0.3.3 - Python 3.10+ Compatibility

This version updates the package to ensure compatibility with Python 3.10 and newer versions, addressing dependency changes and improving CI/CD workflows.

#### Key Updates

1. **Python Version Requirements**:
   - Updated minimum Python version to 3.10+
   - Added support for Python 3.11 and 3.12
   - Removed support for Python 3.8 and 3.9 due to dependency requirements
   
2. **Improved Compatibility**:
   - Fixed circular import issues in the insurance module
   - Enhanced batch processing capabilities
   - Addressed issues with newer NumPy (2.0+) requirements
   
3. **CI/CD Improvements**:
   - Updated GitHub Actions workflows to test on Python 3.10-3.12
   - Fixed failing tests and improved test coverage
   - Enhanced build process for PyPI deployment

### Version 0.3.2 - Configuration Sharing and PyArrow Integration

This version adds functionality to export configuration settings to shareable files and improves DataFrame performance with optional PyArrow integration.

#### Key Features

1. **Configuration Export/Import**:
   - Export settings to JSON or YAML files for sharing with team members
   - Load exported configuration in new instances
   - Include optional metadata for documentation
   - Seamless integration with existing settings management
   
   ```python
   from allyanonimiser import create_allyanonimiser
   
   # Export configuration to share with team members
   ally = create_allyanonimiser()
   ally.set_acronym_dictionary({'POL': 'Policy', 'CL': 'Claim'})
   ally.settings_manager.set_entity_types(['PERSON', 'EMAIL_ADDRESS'])
   ally.export_config("my_config.json")
   
   # Team members can load the configuration
   shared_ally = create_allyanonimiser(settings_path="my_config.json")
   ```

2. **PyArrow Integration**:
   - Optional PyArrow support for improved DataFrame performance
   - Graceful fallback when PyArrow isn't available
   - Configurable through settings with sensible defaults
   - Enhanced DataFrame processing speed for large datasets

### Version 0.3.1 - DataFrame Processing and Batch Operations

This version adds comprehensive DataFrame processing capabilities, enabling efficient analysis and anonymization of data stored in pandas DataFrames.

#### Key Features

1. **DataFrame Processing**:
   - Process pandas DataFrames with optimized memory usage
   - Batch operations for efficient handling of large datasets
   - Parallel processing for improved performance
   - Progress tracking for long-running operations

2. **Anonymization and Analysis**:
   - Anonymize specific columns or entire DataFrames
   - Extract entities from text columns
   - Generate statistical reports on detected entities
   - Configure entity types and anonymization operators

### Version 0.3.0 - Custom Pattern Support and Pattern Management

This version adds comprehensive custom pattern creation and management capabilities, enabling users to define, test, save, and load their own PII detection patterns.

#### Key Features

1. **Custom Pattern Creation**:
   - Create and manage custom pattern definitions
   - Generate patterns from examples with different generalization levels
   - Save and load pattern definitions for reuse
   - Add patterns directly to analyzers or pattern registries

2. **Pattern Testing and Verification**:
   - Test patterns against positive and negative examples
   - Validate pattern structure and components
   - Get diagnostic information for pattern matching
   - Identify and fix issues in pattern definitions

## Installation

```bash
# Basic installation
pip install allyanonimiser==1.1.0

# With stream processing support for large files
pip install "allyanonimiser[stream]==1.1.0"

# With LLM integration for advanced pattern generation
pip install "allyanonimiser[llm]==1.1.0"

# Complete installation with all optional dependencies
pip install "allyanonimiser[stream,llm]==1.1.0"
```

### Prerequisites

1. Python 3.10 or higher
2. For optimal performance, also install a spaCy model:
   ```bash
   python -m spacy download en_core_web_lg
   ```

## Usage Examples

### Direct Analyzer Usage

```python
from allyanonimiser import create_analyzer, EnhancedAnalyzer

# Use the factory function for a pre-configured analyzer
analyzer = create_analyzer()

# Analyze some text
results = analyzer.analyze(
    text="My policy number is POL-123456. My claim reference is CLM/2023/78901.",
    language="en"
)

# Print the results
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```

### Text Anonymization

```python
from allyanonimiser import create_allyanonimiser

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Analyze and anonymize text
result = ally.anonymize(
    text="Please contact John Smith at john.smith@example.com regarding TFN: 123 456 789.",
    operators={
        "PERSON": "replace",  # Replace with [PERSON]
        "EMAIL_ADDRESS": "mask",  # Apply partial masking: j***@e******.com
        "AU_TFN": "redact",  # Fully redact the TFN: [REDACTED]
    }
)

print(result["text"])
# Output: "Please contact [PERSON] at j***@e******.com regarding TFN: [REDACTED]."
```

### Advanced Features

```python
from allyanonimiser import create_allyanonimiser

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Preserve postcodes in addresses
result = ally.anonymize(
    text="The customer lives at 42 Main St, Sydney NSW 2000.",
    keep_postcode=True  # Default is True
)

print(result["text"])
# Output: "The customer lives at <AU_ADDRESS> 2000."

# Convert dates of birth to age brackets
result = ally.anonymize(
    text="Patient: Jane Doe, DOB: 15/03/1980, Medicare: 1234 56789 0",
    operators={
        "DATE_OF_BIRTH": "age_bracket",  # Convert to 5-year brackets by default
        "PERSON": "replace"
    }
)

print(result["text"])
# Output: "Patient: <PERSON>, DOB: 40-44, Medicare: <AU_MEDICARE>"

# Process multiple files from a directory
results = ally.process_files(
    file_paths=["claim1.txt", "claim2.txt"],
    output_dir="anonymized_output/",
    operators={"DATE_OF_BIRTH": "age_bracket", "AU_TFN": "redact"},
    age_bracket_size=10
)
```

## Supported Entity Types

The package includes recognition for:

### Australian-Specific Entities
- `AU_TFN` (Tax File Numbers)
- `AU_MEDICARE` (Medicare card numbers)
- `AU_PASSPORT` (Australian passport numbers)
- `AU_DRIVERS_LICENSE` (Australian drivers license numbers)
- `AU_ABN` (Australian Business Numbers)
- `AU_ACN` (Australian Company Numbers)
- `AU_ADDRESS` (Australian street addresses)
- `AU_POSTCODE` (Australian postcodes)
- `AU_PHONE` (Australian phone numbers)
- `AU_REGO` (Vehicle registration numbers)

### Insurance-Specific Entities
- `INSURANCE_POLICY_NUMBER` (Policy identifiers)
- `INSURANCE_CLAIM_NUMBER` (Claim reference numbers)
- `INSURANCE_MEMBER_NUMBER` (Membership numbers)
- `INSURANCE_GROUP_NUMBER` (Group policy identifiers)
- `VEHICLE_IDENTIFIER` (VIN, chassis, license plate)
- `CASE_REFERENCE` (Internal case references)

### General PII Entities
- `PERSON` (Person names)
- `EMAIL_ADDRESS` (Email addresses)
- `PHONE_NUMBER` (Generic phone numbers)
- `CREDIT_CARD` (Credit card numbers)
- `DATE` (Calendar dates)
- `URL` (Web addresses)
- `LOCATION` (Physical locations)
- `ORGANIZATION` (Company and organization names)
- `MONETARY_VALUE` (Currency amounts)
- `ID` (Generic identification numbers)

## Anonymization Operations

The package supports several anonymization operators:

- `replace`: Replace with entity type (e.g., [PERSON])
- `redact`: Fully redact the entity (e.g., [REDACTED])
- `mask`: Partially mask while preserving structure (e.g., j***@e****.com)
- `hash`: Replace with a consistent hash value
- `encrypt`: Encrypt with a key (recoverable)
- `age_bracket`: Convert dates of birth to age brackets (e.g., 40-44)
- `custom`: Define your own replacement function

### Key Features Explained

#### Age Bracketing

The age bracketing feature converts dates of birth to age brackets for enhanced privacy:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
result = ally.anonymize(
    text="Patient: John Smith, DOB: 15/03/1980, Medicare: 1234 56789 0",
    operators={"DATE_OF_BIRTH": "age_bracket"},
    age_bracket_size=5  # Default is 5 years
)

print(result["text"])
# Output: "Patient: <PERSON>, DOB: 40-44, Medicare: <AU_MEDICARE>"
```

- Supports multiple date formats (DD/MM/YYYY, YYYY-MM-DD, etc.)
- Handles direct age mentions (e.g., "Age: 42")
- Customize bracket sizes (5, 10 years, etc.)

#### Postcode Preservation

Preserve postcodes when anonymizing addresses to maintain geographical context:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
result = ally.anonymize(
    text="Customer lives at 42 Main St, Sydney NSW 2000.",
    keep_postcode=True  # Default is True
)

print(result["text"])
# Output: "Customer lives at <AU_ADDRESS> 2000."
```

- Maintains geographic context while anonymizing specific addresses
- Works with various address formats
- Can be enabled/disabled as needed (enabled by default)

## Creating and Managing Patterns

Customize the library to detect organization-specific entities and control which patterns are active:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Method 1: Add a custom regex pattern directly
ally.add_pattern({
    "entity_type": "CUSTOMER_ID",
    "patterns": [r"C-\d{5}-[A-Z]{2}"],
    "context": ["customer", "id", "identifier", "number"],
    "name": "Customer ID Pattern"
})

# Method 2: Generate a pattern from examples
examples = ["PRJ-2023-001", "PRJ-2023-002", "PRJ-2023-003"]
ally.create_pattern_from_examples(
    entity_type="PROJECT_CODE",
    examples=examples,
    context=["project", "code"],
    generalization_level="medium"  # Controls pattern flexibility
)

# Method 3: Import patterns from a CSV file
ally.import_patterns_from_csv(
    csv_path="patterns/customer_patterns.csv",
    entity_column="entity_type",
    pattern_column="regex"
)

# Control which patterns are active for a specific analysis
# Get all available patterns first
available_entities = ally.get_available_entity_types()
print(f"Available patterns: {list(available_entities.keys())}")

# Selectively enable only certain patterns
result = ally.analyze(
    text="Customer ID: C-12345-AB, Project: PRJ-2023-001, Medicare: 1234 56789 0",
    active_entity_types=["CUSTOMER_ID", "PROJECT_CODE"]  # Only these will be detected
)

# Save all patterns for reuse
ally.export_config("patterns_repository.json")
```

## Running Tests

The package includes comprehensive tests:

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_analyzer.py tests/test_anonymizer.py

# Run with coverage report
pytest --cov=allyanonimiser
```

## Test Coverage

Test coverage focuses on several key areas:

1. **Factory Functions**: Tests that the factory functions like `create_analyzer` work correctly
2. **Entity Detection**: Tests for accurate detection of all entity types
3. **Anonymization**: Tests for proper text replacement with different operators
4. **Extensibility**: Tests for adding custom patterns and entity types
5. **Stream Processing**: Tests for the stream processor with large files and chunked processing
6. **Package Structure**: Tests for import behavior, version consistency, and API correctness
7. **Edge Cases**: Tests for handling of boundary conditions and unusual inputs

## Contributing

Contributions are welcome! Please check the [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.