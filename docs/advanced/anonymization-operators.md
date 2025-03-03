# Anonymization Operators

Allyanonimiser provides several anonymization operators that control how detected entities are transformed in the text. Each operator offers different levels of privacy protection and information preservation.

## Available Operators

| Operator | Description | Example | Result |
|----------|-------------|---------|--------|
| `replace` | Replace with entity type | "John Smith" | `<PERSON>` |
| `redact` | Fully redact the entity | "john.smith@example.com" | `[REDACTED]` |
| `mask` | Partially mask while preserving structure | "john.smith@example.com" | `j***.s****@e******.com` |
| `hash` | Replace with consistent hash | "John Smith" | `7f9d6a...` (same for all "John Smith") |
| `encrypt` | Encrypt with a key (recoverable) | "John Smith" | `AES256:a7f9c...` |
| `age_bracket` | Convert dates to age brackets | "DOB: 15/03/1980" | `DOB: 40-44` |
| `custom` | User-defined function | (depends on function) | (custom output) |

## Basic Usage

```python
from allyanonimiser import create_allyanonimiser

# Create an instance
ally = create_allyanonimiser()

# Anonymize text with different operators for different entity types
result = ally.anonymize(
    text="Customer John Smith (email: john.smith@example.com) called about policy POL-123456.",
    operators={
        "PERSON": "replace",           # Replace with <PERSON>
        "EMAIL_ADDRESS": "mask",       # Partially mask the email
        "INSURANCE_POLICY_NUMBER": "redact"  # Fully redact the policy number
    }
)

print(result["text"])
# Output: "Customer <PERSON> (email: j***.s****@e******.com) called about policy [REDACTED]."
```

## Detailed Operator Descriptions

### Replace Operator

The `replace` operator substitutes the detected entity with its entity type enclosed in angle brackets.

```python
result = ally.anonymize(
    text="John Smith lives in Sydney.",
    operators={"PERSON": "replace", "LOCATION": "replace"}
)
# Output: "<PERSON> lives in <LOCATION>."
```

This operator preserves the semantics of the text while removing all identifying information.

### Redact Operator

The `redact` operator completely removes the entity and replaces it with `[REDACTED]`.

```python
result = ally.anonymize(
    text="The credit card number is 1234 5678 9012 3456.",
    operators={"CREDIT_CARD": "redact"}
)
# Output: "The credit card number is [REDACTED]."
```

This provides the highest level of privacy by removing all traces of the sensitive information.

### Mask Operator

The `mask` operator preserves the structure and partial content of the entity while obscuring most of the information.

```python
result = ally.anonymize(
    text="Contact john.smith@example.com for more details.",
    operators={"EMAIL_ADDRESS": "mask"}
)
# Output: "Contact j***.s****@e******.com for more details."
```

By default, it:
- Preserves the first character of each segment
- Masks the rest with asterisks
- Keeps special characters (like @ and . in emails)

### Hash Operator

The `hash` operator replaces the entity with a consistent hash value, ensuring that the same entity always gets the same replacement.

```python
result = ally.anonymize(
    text="John Smith and again John Smith both called today.",
    operators={"PERSON": "hash"}
)
# Both instances of "John Smith" will be replaced with the same hash value
```

This is useful for maintaining relationships in the data without revealing identities.

### Encrypt Operator

The `encrypt` operator uses AES-256 encryption to replace the entity, allowing recovery with the right key.

```python
result = ally.anonymize(
    text="TFN: 123 456 789",
    operators={"AU_TFN": "encrypt"},
    encryption_key="my-secret-key"  # Optional: provide your own key
)
# Output: "TFN: AES256:a7f9c..."
```

To decrypt:

```python
from allyanonimiser.utils.cipher import decrypt_text

original = decrypt_text(result["entity_replacements"][0]["replacement"], "my-secret-key")
print(original)  # "123 456 789"
```

### Age Bracket Operator

The `age_bracket` operator converts dates (especially dates of birth) to age brackets.

```python
result = ally.anonymize(
    text="Patient DOB: 15/03/1980",
    operators={"DATE_OF_BIRTH": "age_bracket"},
    age_bracket_size=5  # Optional: specify the bracket size (default is 5)
)
# Output: "Patient DOB: 40-44" (assuming current year is 2023)
```

This preserves the approximate age while hiding the exact birth date.

## Configuration Options

You can configure the anonymization process with additional parameters:

```python
from allyanonimiser import create_allyanonimiser, AnonymizationConfig

ally = create_allyanonimiser()

# Create a configuration object
config = AnonymizationConfig(
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "DATE_OF_BIRTH": "age_bracket"
    },
    age_bracket_size=10,              # Size of age brackets
    mask_char="*",                    # Character to use for masking
    redaction_text="[HIDDEN]",        # Text to use for redaction
    hash_algorithm="sha256",          # Hashing algorithm to use
    hash_length=8,                    # Length of hash output
    encryption_key="my-secret-key"    # Key for encryption
)

# Use the configuration
result = ally.anonymize(
    text="John Smith (DOB: 15/03/1980) email: john.smith@example.com",
    config=config
)
```

## See Also

- [Custom Operators](custom-operators.md) - Learn how to create your own anonymization operators
- [Analyzing Text](../usage/analyzing-text.md) - Understanding the analysis capabilities
- [Basic Usage](../usage/basic-usage.md) - General usage patterns