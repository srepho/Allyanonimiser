# Allyanonimiser

[![PyPI version](https://img.shields.io/badge/pypi-v0.3.3-blue)](https://pypi.org/project/allyanonimiser/0.3.3/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Australian-focused PII detection and anonymization for the insurance industry.

## Quick Start

```python
from allyanonimiser import create_analyzer

# Create an analyzer with all available patterns
analyzer = create_analyzer()

# Analyze text
results = analyzer.analyze(
    text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123.",
    language="en"
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
        'Customer called about policy POL123456',
        'Email from jane@example.com about claim CL789012',
        'Medicare number 2123 45678 1 received for claim',
        'TFN: 123 456 789. Contact at 42 Example St, Sydney'
    ]
})

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Detect PII in a specific column
entities_df = ally.detect_pii_in_dataframe(df, 'note')

# Anonymize a specific column
anonymized_df = ally.anonymize_dataframe(
    df, 
    'note',
    operators={
        'PERSON': 'replace',
        'EMAIL_ADDRESS': 'mask',
        'INSURANCE_POLICY_NUMBER': 'redact',
        'INSURANCE_CLAIM_NUMBER': 'redact'
    }
)
```

### Custom Pattern Creation

```python
from allyanonimiser import create_allyanonimiser, CustomPatternDefinition

# Create a pattern directly
ally = create_allyanonimiser()
ally.add_pattern({
    "entity_type": "INTERNAL_REFERENCE",
    "patterns": [r"REF-\d{5}", r"Reference:\s*([A-Z0-9-]+)"],
    "context": ["internal", "reference", "ref"],
    "name": "Internal Reference Number"
})

# Or create a pattern from examples
internal_ref_examples = [
    "REF-12345",
    "REF-98765",
    "Reference: REF-55555"
]

pattern = ally.create_pattern_from_examples(
    entity_type="INTERNAL_REFERENCE",
    examples=internal_ref_examples,
    context=["internal", "reference", "ref"],
    name="Internal Reference Pattern",
    generalization_level="medium"  # Determines how flexible the pattern is
)
```

## Features

- **Australian-Specific PII Detection**: Specialized recognizers for Australian TFNs, Medicare numbers, driver's licenses, and other Australian-specific identifiers.
- **Insurance Industry Focus**: Recognition of policy numbers, claim references, vehicle identifiers, and other insurance-specific data.
- **Long Text Processing**: Optimized for processing lengthy free-text fields like claim notes, medical reports, and emails.
- **Custom Pattern Creation**: Easy creation of custom entity recognizers for organization-specific data.
- **Synthetic Data Generation**: Generate realistic Australian test data for validation.
- **LLM Integration**: Use Language Models to create challenging datasets for testing.
- **Extensible Architecture**: Built on Presidio and spaCy with a modular, extensible design.

## Version History

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
pip install allyanonimiser
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

### Direct Anonymizer Usage

```python
from allyanonimiser import EnhancedAnonymizer, create_analyzer

# Create an anonymizer with a pre-configured analyzer
anonymizer = EnhancedAnonymizer(analyzer=create_analyzer())

# Anonymize text
anonymized_text = anonymizer.anonymize(
    text="Please contact John Smith at john.smith@example.com regarding TFN: 123 456 789.",
    operators={
        "PERSON": "replace",  # Replace with [PERSON]
        "EMAIL_ADDRESS": "mask",  # Apply partial masking: j***@e******.com
        "AU_TFN": "redact",  # Fully redact the TFN: [REDACTED]
    }
)

print(anonymized_text)
# Output: "Please contact [PERSON] at j***@e******.com regarding TFN: [REDACTED]."
```

### Simplified Interface

For convenience, you can use the unified `Allyanonimiser` interface:

```python
from allyanonimiser import create_analyzer
from allyanonimiser import create_allyanonimiser

# Create a complete analyzer
ally = create_allyanonimiser()

# Process text in one step
entities, anonymized_text = ally.process(
    text="My Medicare card number is 1234 56789 0. My TFN is 123 456 789.",
    operators={
        "AU_MEDICARE": "hash",  # Hash with a consistent value
        "AU_TFN": "redact",  # Fully redact the TFN
    }
)

print(anonymized_text)
# Output: "My Medicare card number is 43fb5d5cff. My TFN is [REDACTED]."
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
- `custom`: Define your own replacement function

## Creating Custom Patterns

You can create custom patterns to detect organization-specific entities:

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Add a custom pattern directly
ally.add_pattern({
    "entity_type": "CUSTOMER_ID",
    "patterns": [r"C-\d{5}-[A-Z]{2}"],
    "context": ["customer", "id", "identifier", "number"],
    "name": "Customer ID Pattern"
})

# Or create patterns from examples
examples = ["PRJ-2023-001", "PRJ-2023-002", "PRJ-2023-003"]
ally.create_pattern_from_examples(
    entity_type="PROJECT_CODE",
    examples=examples,
    context=["project", "code"],
    generalization_level="medium"  # Creates a flexible pattern that matches variations
)
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
5. **Edge Cases**: Tests for handling of boundary conditions and unusual inputs

## Contributing

Contributions are welcome! Please check the [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.