# Pattern Reference Overview

Allyanonimiser provides a comprehensive set of built-in patterns for detecting PII and sensitive information, organized into categories based on their origin and purpose.

## Pattern Categories

The patterns in Allyanonimiser are organized into three main categories:

1. **Australian Patterns** - Patterns specific to Australian identifiers and formats
2. **General Patterns** - Universal PII patterns that apply across regions
3. **Insurance Patterns** - Patterns specific to the insurance industry

## Pattern Structure

Each pattern in Allyanonimiser consists of:

- **Entity Type**: A unique identifier for the pattern (e.g., `AU_TFN`, `PERSON`, `INSURANCE_POLICY_NUMBER`)
- **Patterns**: One or more regex patterns or spaCy patterns that match the entity
- **Context**: Words or phrases that often appear near the entity (improves detection accuracy)
- **Score**: Confidence score threshold for detection
- **Name**: Human-readable name for the entity type
- **Language**: Language code (usually "en" for English)

## Pattern Definition Example

Here's an example of how a pattern is defined:

```python
{
    "entity_type": "AU_TFN",
    "patterns": [
        r"\b\d{3}\s*\d{3}\s*\d{3}\b",
        r"\bTFN:?\s*\d{3}\s*\d{3}\s*\d{3}\b"
    ],
    "context": ["tax", "file", "number", "tfn"],
    "name": "Australian Tax File Number",
    "score": 0.65,
    "language": "en"
}
```

## Accessing Built-in Patterns

You can access the built-in patterns programmatically:

```python
from allyanonimiser.patterns.au_patterns import get_au_pattern_definitions
from allyanonimiser.patterns.general_patterns import get_general_pattern_definitions
from allyanonimiser.patterns.insurance_patterns import get_insurance_pattern_definitions

# Get Australian patterns
au_patterns = get_au_pattern_definitions()

# Get general patterns
general_patterns = get_general_pattern_definitions()

# Get insurance patterns
insurance_patterns = get_insurance_pattern_definitions()

# Print all pattern entity types
for pattern in au_patterns:
    print(f"AU Pattern: {pattern['entity_type']}")
```

## Pattern Categories

In the following sections, we provide detailed information about each pattern category:

- [Australian Patterns](australian.md): Patterns for Australian-specific identifiers
- [General Patterns](general.md): Universal PII patterns
- [Insurance Patterns](insurance.md): Insurance industry-specific patterns

## Custom Patterns

Learn how to create and manage your own custom patterns:

- [Creating Custom Patterns](custom.md): Guide to creating and registering custom patterns