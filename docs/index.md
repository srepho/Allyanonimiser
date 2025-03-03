# Allyanonimiser

Australian-focused PII detection and anonymization for the insurance industry with support for stream processing of very large files.

[![PyPI version](https://img.shields.io/badge/pypi-v2.1.0-blue)](https://pypi.org/project/allyanonimiser/2.1.0/)
[![Python Versions](https://img.shields.io/pypi/pyversions/allyanonimiser.svg)](https://pypi.org/project/allyanonimiser/)
[![Tests](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/tests.yml)
[![Package](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml/badge.svg)](https://github.com/srepho/Allyanonimiser/actions/workflows/package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Allyanonimiser is a specialized library for detecting and anonymizing personally identifiable information (PII) in text data, with a focus on Australian formats and insurance industry-specific content.

### Key Features

- **Australian-Focused PII Detection**: Specialized patterns for TFNs, Medicare numbers, vehicle registrations, addresses, and more
- **Insurance Industry Specialization**: Detect policy numbers, claim references, and other industry-specific identifiers
- **Multiple Entity Types**: Comprehensive detection of general and specialized PII
- **Flexible Anonymization**: Multiple anonymization operators (replace, mask, redact, hash, and more)
- **Stream Processing**: Memory-efficient processing of large files with chunking support
- **Reporting System**: Comprehensive tracking and visualization of anonymization activities
- **Jupyter Integration**: Rich visualization capabilities in notebook environments
- **DataFrame Support**: Process pandas DataFrames with batch processing and multi-processing support

## Quick Example

```python
from allyanonimiser import create_allyanonimiser

# Create the Allyanonimiser instance
ally = create_allyanonimiser()

# Analyze text
results = ally.analyze(
    text="Customer John Smith (TFN: 123 456 789) reported an incident on 15/06/2023 in Sydney NSW 2000."
)

# Print detected entities
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")

# Anonymize text
anonymized = ally.anonymize(
    text="Customer John Smith (TFN: 123 456 789) reported an incident on 15/06/2023 in Sydney NSW 2000.",
    operators={
        "PERSON": "replace",       # Replace with <PERSON>
        "AU_TFN": "mask",          # Partially mask the TFN
        "DATE": "redact",          # Replace date with [REDACTED]
        "AU_ADDRESS": "replace"    # Replace with <AU_ADDRESS>
    }
)

print(anonymized["text"])
# Output: "Customer <PERSON> (TFN: ***-***-***) reported an incident on [REDACTED] in <AU_ADDRESS>."
```

## Getting Started

Check out the [Installation](getting-started/installation.md) guide to get started with Allyanonimiser. Then, follow the [Quick Start](getting-started/quick-start.md) guide to learn the basics of using the library.

## Use Cases

Allyanonimiser is particularly useful for:

- Insurance claim processing and data analysis
- Medical report anonymization
- Customer service data management
- Regulatory compliance with Australian privacy laws
- Processing large datasets containing sensitive information
- Creating anonymized training data for machine learning models

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/srepho/Allyanonimiser/blob/main/LICENSE) file for details.