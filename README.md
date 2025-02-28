# Allyanonimiser

[![PyPI version](https://img.shields.io/pypi/v/allyanonimiser)](https://pypi.org/project/allyanonimiser/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Australian-focused PII detection and anonymization for the insurance industry.

## Version 0.3.2 - Configuration Sharing and PyArrow Integration

This version adds functionality to export configuration settings to shareable files and improves DataFrame performance with optional PyArrow integration.

### Key Features

1. **Configuration Export/Import**:
   - Export settings to JSON or YAML files for sharing with team members
   - Load exported configuration in new instances
   - Include optional metadata for documentation
   - Seamless integration with existing settings management
   
   ```python
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

## Version 0.3.1 - DataFrame Processing and Batch Operations

This version adds comprehensive DataFrame processing capabilities, enabling efficient analysis and anonymization of data stored in pandas DataFrames. It includes batch processing, parallel execution, and statistical analysis of results.

### Key Features

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

3. **Performance Optimizations**:
   - Process data in configurable batches
   - Use multiprocessing for CPU-intensive operations
   - Efficiently handle large datasets with minimal memory usage
   - Vectorized operations where possible

4. **Integrated Interface**:
   - Simple methods added to main Allyanonimiser class
   - Complete example code in example_dataframe.py
   - Comprehensive test suite for DataFrame processing
   - Detailed documentation and usage examples

## Version 0.3.0 - Custom Pattern Support and Pattern Management

This version adds comprehensive custom pattern creation and management capabilities, enabling users to define, test, save, and load their own PII detection patterns. It includes pattern generation from examples, serialization, and integration with the existing analyzer.

### Key Features

1. **Custom Pattern Creation**:
   - Create custom patterns for detecting organization-specific PII
   - Define patterns using regex or provide example strings
   - Support for context keywords to improve detection accuracy
   - Create patterns with different levels of generalization
   
   ```python
   # Create a custom pattern directly
   pattern = CustomPatternDefinition(
       entity_type="PROJECT_ID",
       patterns=["PRJ-\d{4}"],  # Regex patterns
       context=["project", "task"],  # Context words
       name="Project ID Pattern"
   )
   analyzer.add_pattern(pattern)
   
   # Or generate a pattern from examples
   ally = create_allyanonimiser()
   ally.create_pattern_from_examples(
       entity_type="MEMBERSHIP_NUMBER",
       examples=["MEM-12345", "MEM-78901", "MEMBER-12345"],
       context=["member", "membership"],
       generalization_level="medium"  # none, low, medium, high
   )
   ```

2. **Pattern Persistence**:
   - Save custom patterns to JSON files
   - Load patterns from files into new analyzer instances
   - Share patterns between applications
   
   ```python
   # Save patterns to a file
   ally.save_patterns("my_custom_patterns.json")
   
   # Load patterns in another instance
   new_ally = create_allyanonimiser()
   new_ally.load_patterns("my_custom_patterns.json")
   ```

3. **Pattern Testing and Validation**:
   - Test patterns against positive and negative examples
   - Get precision, recall, and F1 scores for patterns
   - Validate pattern definitions
   
   ```python
   from allyanonimiser.validators import test_pattern_against_examples
   
   results = test_pattern_against_examples(
       pattern=r"PRJ-\d{4}",
       positive_examples=["PRJ-1234", "PRJ-5678"],
       negative_examples=["PR-1234", "PROJECT-1234"]
   )
   print(f"Precision: {results['metrics']['precision']}")
   print(f"Recall: {results['metrics']['recall']}")
   ```

4. **Pattern Generation**:
   - Generate patterns from example strings
   - Multiple generalization levels for flexibility
   - Format detection for common patterns
   
   ```python
   # Different levels of generalization
   from allyanonimiser.utils.spacy_helpers import create_regex_from_examples
   
   # Exact matching - only matches exactly these examples
   create_regex_from_examples(["ABC-123", "ABC-456"], "none")
   # Result: (ABC\-123)|(ABC\-456)
   
   # Medium generalization - more flexible pattern
   create_regex_from_examples(["ABC-123", "ABC-456"], "medium")
   # Result: ABC-\d{3}
   ```

## Version 0.2.2 - spaCy NER Integration for Improved Entity Detection

This version integrates spaCy's Named Entity Recognition (NER) system to dramatically improve entity detection accuracy, particularly for PERSON entities. It reduces false positives and resolves entity type conflicts through a sophisticated hybrid approach.

### Key Improvements

1. **spaCy NER Integration**:
   - Added direct integration with spaCy's pre-trained NER models for entity detection
   - Prioritizes spaCy's contextual understanding for PERSON entity detection
   - Maintains pattern-based detection for specialized Australian and insurance entities
   - Configurable to use different spaCy models depending on accuracy requirements

2. **Reduced False Positives**:
   - Fixed issue where phrases like "Ref Number" were incorrectly identified as PERSON entities
   - Added contextual filters to improve detection accuracy
   - Implemented hierarchical entity type resolution with configurable priorities
   - Significantly reduced rate of false positives in real-world insurance documents

3. **Entity Type Conflict Resolution**:
   - Added sophisticated entity conflict resolution system when multiple entity types match the same text
   - Created context-based and prefix-based prioritization rules
   - Implemented scoring to prioritize the most appropriate entity type
   - Fixed issues with duplicate entity detections for the same text span
   
   ```python
   # The analyzer now correctly handles conflicts like this:
   results = analyzer.analyze("Policy POL123456 was reviewed by John Smith")
   # POL123456 is correctly identified as INSURANCE_POLICY_NUMBER, not as a PERSON
   # John Smith is correctly identified as a PERSON
   ```

4. **Enhanced Entity Type Mapping**:
   - Added comprehensive mapping between spaCy and custom entity types
   - Support for 17 entity types from spaCy's standard model
   - Confidence scoring to prioritize high-quality matches
   - Maintains backward compatibility with existing pattern definitions
   
   ```python
   # The mapping now supports these spaCy entity types:
   mapping = {
       "PERSON": "PERSON",
       "ORG": "ORGANIZATION",
       "GPE": "LOCATION",
       "LOC": "LOCATION",
       "DATE": "DATE",
       "TIME": "TIME",
       "MONEY": "MONEY",
       # And many more...
   }
   ```

5. **Improved Person Detection**:
   - Leverages spaCy's contextual understanding for more accurate person name detection
   - Better handling of name variations, titles, and multi-word names
   - Improved accuracy for non-English and multicultural names
   - Reduced false positives from words that might appear similar to names

### Benefits

- Much more comprehensive PII detection in Australian contexts
- Greater accuracy in identifying sensitive information
- Reduced false negatives in document processing
- Better demonstration of package capabilities
- Improved real-world usability for Australian organizations

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
pip install allyanonimiser==0.3.2

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
from allyanonimiser import CustomPatternDefinition, create_allyanonimiser

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

# Test with text
text = "Please reference REF-78901 in all future correspondence."
results = ally.analyze(text)
```

## Pattern Persistence and Sharing

```python
from allyanonimiser import create_allyanonimiser, CustomPatternDefinition

# Create an analyzer with custom patterns
ally = create_allyanonimiser()

# Add company-specific patterns
ally.add_pattern(CustomPatternDefinition(
    entity_type="BROKER_CODE",
    patterns=["BRK-[0-9]{4}"],
    context=["broker", "agent", "representative"],
    name="Broker Code Pattern"
))

ally.add_pattern(CustomPatternDefinition(
    entity_type="CUSTOMER_ID",
    patterns=["CUST-[A-Z]{2}[0-9]{4}"],
    context=["customer", "client", "id"],
    name="Customer ID Pattern"
))

# Save patterns to a file
ally.save_patterns("company_patterns.json")

# Later, in another application
new_ally = create_allyanonimiser()
new_ally.load_patterns("company_patterns.json")
```

## Testing and Validating Patterns

```python
from allyanonimiser.validators import test_pattern_against_examples, validate_pattern_definition

# Test a pattern against examples
pattern = r"PROJ-\d{4}-[A-Z]{2}"
positive_examples = ["PROJ-1234-AB", "PROJ-5678-XY"]
negative_examples = ["PROJ-123-AB", "PROJECT-1234-AB"]

results = test_pattern_against_examples(pattern, positive_examples, negative_examples)
print(f"Precision: {results['metrics']['precision']:.2f}")
print(f"Recall: {results['metrics']['recall']:.2f}")
print(f"F1 Score: {results['metrics']['f1']:.2f}")

# Validate a complete pattern definition
pattern_def = {
    "entity_type": "PROJECT_CODE",
    "patterns": ["PROJ-\\d{4}-[A-Z]{2}"],
    "context": ["project", "code"],
    "name": "Project Code Pattern"
}

validation = validate_pattern_definition(pattern_def)
if validation["is_valid"]:
    print("Pattern definition is valid!")
else:
    print("Pattern definition errors:", validation["errors"])
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

## Configuration Sharing

Allyanonimiser supports sharing configurations across teams through settings files and export functionality:

```python
from allyanonimiser import create_allyanonimiser
from allyanonimiser.utils.settings_manager import create_default_settings, save_settings

# Create and save team settings
settings = create_default_settings()

# Add team-specific acronyms
settings['acronyms']['dictionary'].update({
    "MC": "Motor Claims",
    "PI": "Personal Injury",
    "FOS": "Financial Ombudsman Service",
    "UW": "Underwriter",
    "RTA": "Road Traffic Accident"
})

# Configure processing options
settings['processing']['batch_size'] = 500
settings['processing']['worker_count'] = 4
settings['processing']['expand_acronyms'] = True
settings['processing']['use_pyarrow'] = True

# Save for team use
save_settings("team_settings.json", settings)

# Team members can load these settings
ally = create_allyanonimiser(settings_path="team_settings.json")

# Export a shareable configuration with just the essential settings
ally.export_config("shareable_config.json", include_metadata=True)

# Users can import the shareable configuration
shared_ally = create_allyanonimiser(settings_path="shareable_config.json")
```

### Exporting Configuration

Export configuration settings to share with other users:

```python
from allyanonimiser import create_allyanonimiser

# Create and configure an Allyanonimiser instance
ally = create_allyanonimiser()

# Configure features
ally.set_acronym_dictionary({'POL': 'Policy', 'CL': 'Claim'})
ally.settings_manager.set_entity_types(['PERSON', 'EMAIL_ADDRESS'])
ally.settings_manager.set_value('processing.use_pyarrow', True)

# Export configuration to JSON or YAML
ally.export_config("my_config.json")  # JSON format
ally.export_config("my_config.yaml")  # YAML format (requires PyYAML)

# Export minimal configuration (without metadata)
ally.export_config("minimal_config.json", include_metadata=False)
```

The exported configuration file includes:
- Active entity types
- Anonymization operators
- Processing settings (batch size, worker count, PyArrow usage)
- Configured acronym dictionary
- Optional metadata for documentation

## Acronym Expansion

Allyanonimiser can expand acronyms before PII detection to improve entity recognition:

```python
from allyanonimiser import create_allyanonimiser

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Set up acronym dictionary
acronyms = {
    "TP": "Third Party",
    "TL": "Team Leader",
    "POL": "Policy",
    "CL": "Claim",
    "DOB": "Date of Birth"
}
ally.set_acronym_dictionary(acronyms)

# Text with acronyms that might hide PII detection
text = "TP John Smith (DOB 15/04/1982) contacted TL Sarah Jones."

# Analyze with acronym expansion
results = ally.analyze(text, expand_acronyms=True)

# Process with acronym expansion
result = ally.process(text, expand_acronyms=True)
print(f"Expanded acronyms: {result['preprocessing']['expanded_acronyms']}")

# Add new acronyms dynamically
ally.add_acronyms({"MVA": "Motor Vehicle Accident"})

# Remove acronyms
ally.remove_acronyms(["TL"])
```

## DataFrame Processing

Allyanonimiser provides powerful support for efficiently processing pandas DataFrames:

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

# Method 1: Detect PII in a specific column
entities_df = ally.detect_pii_in_dataframe(df, 'note')

# Method 2: Anonymize a specific column
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

# Method 3: Process multiple columns with comprehensive analysis
result = ally.process_dataframe(
    df,
    text_columns=['name', 'note'],
    batch_size=100,  # Process in batches for large DataFrames
    n_workers=4      # Use parallel processing for better performance
)

# Access processed DataFrame and entity information
processed_df = result['dataframe']
all_entities = result['entities']

# Calculate entity statistics
processor = ally.create_dataframe_processor()
stats = processor.analyze_dataframe_statistics(all_entities, df, 'note')
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