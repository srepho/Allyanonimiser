# Pattern Reference Overview

Allyanonimiser provides a comprehensive set of built-in patterns for detecting PII and sensitive information, organized into categories based on their origin and purpose.

## Pattern Categories

The patterns in Allyanonimiser are organized into four categories:

1. **Australian Patterns** - Patterns specific to Australian identifiers and formats
2. **General Patterns** - Universal PII patterns that apply across regions
3. **Insurance Patterns** - Patterns specific to the insurance industry
4. **General International Patterns** - Non-AU PII shapes that show up in
   AU-insurance data when the customer or counterparty is overseas
   (expats, business travellers) or when system audit logs leak ISO
   timestamps into claim notes — see [International PII](international.md)

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
from allyanonimiser.patterns.general_intl_patterns import (
    get_general_intl_pattern_definitions,
)
from allyanonimiser.patterns.insurance_patterns import get_insurance_pattern_definitions

# Get Australian patterns
au_patterns = get_au_pattern_definitions()

# Get general patterns
general_patterns = get_general_pattern_definitions()

# Get general international patterns (PHONE_INTL, US_SSN, CREDIT_CARD,
# ISO_DATETIME, TIME — loaded by default; see International PII page)
general_intl_patterns = get_general_intl_pattern_definitions()

# Get insurance patterns
insurance_patterns = get_insurance_pattern_definitions()

# Print all pattern entity types
for pattern in au_patterns:
    print(f"AU Pattern: {pattern['entity_type']}")
```

## Pattern categories in detail

- [Australian Patterns](australian.md) — TFN, ABN, Medicare, AU_PHONE, driver's license, Centrelink CRN, passport, postcode, addresses
- [International PII](international.md) — TIME, ISO_DATETIME, PHONE_INTL, US_SSN, CREDIT_CARD
- [Custom Patterns](custom.md) — how to register your own entity types

General and insurance-specific patterns (EMAIL_ADDRESS, INSURANCE_POLICY_NUMBER, INSURANCE_CLAIM_NUMBER, VEHICLE_REGISTRATION, VEHICLE_VIN, etc.) are included in the built-in pattern set automatically. See the [README's entity reference](https://github.com/srepho/Allyanonimiser#entity-reference) for the complete list of detected types across all categories.