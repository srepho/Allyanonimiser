# Allyanonimiser

[![PyPI version](https://img.shields.io/pypi/v/allyanonimiser)](https://pypi.org/project/allyanonimiser/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Australian-focused PII detection and anonymization for the insurance industry.

## Version 0.1.4 - Added Functional Processing Capabilities

This version adds fully functional processing capabilities to the package while maintaining compatibility with previous versions. Key improvements include:

### New Features

1. **Enhanced Analyzer Implementation**:
   - Added a functional `analyze` method to `EnhancedAnalyzer` that can detect PII entities using regex patterns
   - Implemented `RecognizerResult` class to store and return detection results

2. **Anonymization Capabilities**:
   - Improved `EnhancedAnonymizer` with a full implementation of the `anonymize` method
   - Added support for different anonymization strategies: replace, mask, redact, and hash

3. **Long Text Processing**:
   - Added intelligent text segmentation to handle long documents
   - Implemented PII-rich segment detection with scoring
   - Added pattern-based claim note analysis with section detection

4. **Content Type Detection**:
   - Added automatic detection of document types (emails, claim notes, medical reports)
   - Specialized processing for each document type

5. **Unified Interface**:
   - Expanded `Allyanonimiser` class with comprehensive interface methods
   - Added the `process` method for one-step analysis, anonymization, and structuring

### Benefits

- Complete end-to-end functionality for PII detection and anonymization
- Improved handling of different document types
- Structured data extraction from unstructured text
- Better organization of code with clear module responsibilities
- Functional implementation while maintaining API compatibility

## Features

- **Australian-Specific PII Detection**: Specialized recognizers for Australian TFNs, Medicare numbers, driver's licenses, and other Australian-specific identifiers.
- **Insurance Industry Focus**: Recognition of policy numbers, claim references, vehicle identifiers, and other insurance-specific data.
- **Long Text Processing**: Optimized for processing lengthy free-text fields like claim notes, medical reports, and emails.
- **Custom Pattern Creation**: Easy creation of custom entity recognizers for organization-specific data.
- **Synthetic Data Generation**: Generate realistic Australian test data for validation.
- **LLM Integration**: Use Language Models to create challenging datasets for testing.
- **Extensible Architecture**: Built on Presidio and spaCy with a modular, extensible design.

## Installation

[![PyPI install](https://img.shields.io/pypi/v/allyanonimiser?label=pip%20install&logo=pypi)](https://pypi.org/project/allyanonimiser/)

```bash
# Install from PyPI
pip install allyanonimiser==0.1.4

# Install the required spaCy model
python -m spacy download en_core_web_lg
```

Requires Python 3.8 or higher.

## Quick Start

```python
from allyanonimiser import create_au_insurance_analyzer

# Create an analyzer with Australian and insurance patterns
analyzer = create_au_insurance_analyzer()

# Analyze text
results = analyzer.analyze(
    text="Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123.",
    language="en"
)

# Print results
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```

## Processing Insurance Documents

### Claim Notes

```python
from allyanonimiser import analyze_claim_notes

# Long claim note text
claim_note = """
Claim Details:
Spoke with the insured John Smith (TFN: 123 456 789) regarding damage to his vehicle ABC123.
The incident occurred on 14/05/2023 when another vehicle collided with the rear of his car.
Policy number: POL-987654321

Vehicle Details:
Toyota Corolla 2020
VIN: 1HGCM82633A123456
Registration: ABC123

Contact Information:
Phone: 0412 345 678
Email: john.smith@example.com
Address: 123 Main St, Sydney NSW 2000
"""

# Analyze the claim note
analysis = analyze_claim_notes(claim_note)

# Access structured information
print("Incident Description:", analysis["incident_description"])
print("\nPII-rich segments:")
for segment in analysis["pii_segments"]:
    print(f"  - {segment['text'][:50]}... (PII likelihood: {segment['pii_likelihood']:.2f})")

# Anonymize the text
from allyanonimiser import EnhancedAnonymizer
anonymizer = EnhancedAnonymizer(analyzer=create_au_insurance_analyzer())
anonymized = anonymizer.anonymize(claim_note)
print("\nAnonymized text:")
print(anonymized["text"])
```

### Processing Emails

```python
from allyanonimiser.insurance import InsuranceEmailAnalyzer

email_text = """
From: adjuster@insurance.com.au
To: customer@example.com
Subject: Your Claim CL-12345678

Dear Mr. Smith,

Thank you for your recent claim submission regarding your vehicle (Registration: XYZ123).

We have assigned your claim number CL-12345678. Please reference this number in all future correspondence.

Your policy POL-9876543 covers this type of damage, and we'll need the following information:
1. Your Medicare number
2. Additional photos of the damage
3. The repair quote from the mechanic

Please call me at 03 9876 5432 if you have any questions.

Kind regards,
Sarah Johnson
Claims Assessor
"""

email_analyzer = InsuranceEmailAnalyzer()
analysis = email_analyzer.analyze(email_text)

print("Email Subject:", analysis["subject"])
print("Claim Number:", analysis["claim_number"])
print("Policy Number:", analysis["policy_number"])
print("Customer Name:", analysis["customer_name"])
print("Identified PII:", analysis["pii_entities"])
```

## Creating Custom Patterns

```python
from allyanonimiser import CustomPatternDefinition, create_pattern_from_examples

# Create a custom pattern for internal reference numbers
internal_ref_examples = [
    "Internal reference: REF-12345",
    "Ref Number: REF-98765",
    "Reference: REF-55555"
]

pattern = create_pattern_from_examples(
    entity_type="INTERNAL_REFERENCE",
    examples=internal_ref_examples,
    context=["internal", "reference", "ref"],
    pattern_type="regex"
)

# Add to an existing analyzer
analyzer.add_pattern(pattern)
```

## Using the Pattern Registry

```python
from allyanonimiser import PatternRegistry, CustomPatternDefinition

# Create a registry
registry = PatternRegistry()

# Register patterns
registry.register_pattern(CustomPatternDefinition(
    entity_type="BROKER_CODE",
    patterns=["BRK-[0-9]{4}"],
    context=["broker", "agent", "representative"],
    name="broker_code_recognizer"
))

# Share patterns across applications
registry.export_patterns("insurance_patterns.json")

# Later, in another application
registry.import_patterns("insurance_patterns.json")
```

## Working with Australian Data

```python
from allyanonimiser.patterns import get_au_pattern_definitions

# Get all Australian pattern definitions
au_patterns = get_au_pattern_definitions()

# Print information about each pattern
for pattern in au_patterns:
    print(f"Entity Type: {pattern['entity_type']}")
    print(f"Description: {pattern['description']}")
    print(f"Example Patterns: {pattern['patterns'][:2]}")
    print("Context Terms:", ", ".join(pattern['context'][:5]))
    print()
```

## Generating Australian Test Data

```python
from allyanonimiser.generators import AustralianSyntheticDataGenerator

# Create a data generator
generator = AustralianSyntheticDataGenerator()

# Generate a dataset of Australian insurance documents
generator.generate_dataset(
    num_documents=50,
    output_dir="au_insurance_dataset",
    include_annotations=True
)
```

## Development and Testing

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_imports.py -v
pytest tests/test_version.py -v

# Run tests with coverage
pytest --cov=allyanonimiser
```

### Automated Testing

This project uses GitHub Actions for continuous integration:

1. **Tests Workflow**: Automatically runs imports tests and test suite
2. **Package Checks**: Ensures consistent versioning and valid packaging

### Package Structure Tests

We have implemented specific tests to prevent common issues:

1. **Circular Import Prevention**: Tests to detect and prevent circular imports
2. **Version Consistency**: Checks that version numbers match across all files
3. **Import Structure Tests**: Validates that the package can be imported correctly

You can run these tests with:

```bash
# Run all structure tests
python tests/run_package_tests.py

# Run during build
python setup.py structure_test

# Run functional tests
python tests/run_functional_tests.py

# Run specific test file
python tests/run_functional_tests.py test_circular_import_fix.py
```

These tests help prevent issues like:

- Circular imports between modules (e.g., parent module importing from child and child importing from parent)
- Inconsistent versioning between `__init__.py`, `setup.py`, and `pyproject.toml`
- Import order issues that can cause dependency problems

#### Functional Tests

Functional tests verify the behavior of key components:

1. **Factory Functions**: Tests that the factory functions like `create_au_insurance_analyzer` work correctly
2. **Circular Import Fix**: Specifically tests that the circular import issue is fixed properly
3. **Interface Tests**: Tests that the main interfaces can be instantiated and used correctly

These tests are designed to be lightweight and run without requiring a full package installation.

## Usage

```python
import allyanonimiser

# Create an Allyanonimiser instance
ally = allyanonimiser.create_allyanonimiser()

# Process a text
text = "Patient John Smith with policy number POL123456 reported a claim"
result = ally.analyze(text)

# Alternatively, use specialized analyzers
claim_analyzer = allyanonimiser.ClaimNotesAnalyzer()
result = allyanonimiser.analyze_claim_note(text)
```

See `example_fixed_imports.py` for a complete example.

## For Package Maintainers

When making changes to imports in this package, keep these rules in mind:

1. Define factory functions before using them (top to bottom)
2. Don't import from parent modules in child modules if possible
3. If a module depends on another, make sure dependencies go in one direction

## License

MIT License