# Custom Anonymization Operators

While Allyanonimiser provides several built-in anonymization operators, you can also create custom operators to meet specific requirements. Custom operators give you complete control over how detected entities are transformed.

## Creating a Custom Operator

A custom operator is a function that takes two parameters:
1. `entity_text` - The text of the detected entity
2. `entity_type` - The type of the detected entity (e.g., "PERSON", "EMAIL_ADDRESS")

The function should return the transformed text that will replace the original entity.

### Basic Example

```python
from allyanonimiser import create_allyanonimiser

# Define a simple custom operator
def reverse_text(entity_text, entity_type):
    """Reverse the text of the entity."""
    return entity_text[::-1]

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Use the custom operator
result = ally.anonymize(
    text="Customer John Smith sent an email about their policy.",
    operators={
        "PERSON": reverse_text  # Pass the function directly
    }
)

print(result["text"])
# Output: "Customer htimS nhoJ sent an email about their policy."
```

## Advanced Custom Operator Examples

### Randomized Name Replacement

This example replaces detected person names with random names from a predefined list, while maintaining consistency:

```python
from allyanonimiser import create_allyanonimiser
import hashlib

def randomize_names(entity_text, entity_type):
    """Replace person names with random names from a predefined list."""
    if entity_type != "PERSON":
        return entity_text
        
    # Simple list of random replacement names
    replacements = ["Alex Taylor", "Sam Johnson", "Jordan Lee", "Casey Brown", 
                   "Morgan Smith", "Jamie Williams", "Riley Garcia", "Taylor Wilson"]
    
    # Use hash of original name to consistently select the same replacement
    hash_val = int(hashlib.md5(entity_text.encode()).hexdigest(), 16)
    index = hash_val % len(replacements)
    
    return replacements[index]

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Use the custom operator
result = ally.anonymize(
    text="Customer John Smith contacted Mary Johnson about their policy.",
    operators={
        "PERSON": randomize_names
    }
)

print(result["text"])
# Output might be: "Customer Alex Taylor contacted Sam Johnson about their policy."
```

### Format-Preserving Encryption

This operator preserves the format of credit card numbers while anonymizing them:

```python
from allyanonimiser import create_allyanonimiser
import hashlib

def format_preserving_cc(entity_text, entity_type):
    """
    Replace credit card numbers with fake ones that pass Luhn check
    but preserve the format and issuer prefix.
    """
    if entity_type != "CREDIT_CARD":
        return entity_text
    
    # Remove all non-digits
    digits = ''.join(c for c in entity_text if c.isdigit())
    
    # Preserve the first 6 digits (issuer identification)
    prefix = digits[:6]
    
    # Generate replacement digits for the rest
    hash_obj = hashlib.md5((digits + "salt").encode())
    hash_hex = hash_obj.hexdigest()
    
    # Convert hex hash to decimal digits
    hash_dec = ''.join(str(int(c, 16) % 10) for c in hash_hex)
    
    # Create new number with preserved prefix
    new_digits = prefix + hash_dec[:(len(digits) - 6 - 1)]
    
    # Generate a valid Luhn check digit
    check_digit = generate_luhn_digit(new_digits)
    new_digits += str(check_digit)
    
    # Reapply the original formatting
    result = ''
    digit_index = 0
    for char in entity_text:
        if char.isdigit() and digit_index < len(new_digits):
            result += new_digits[digit_index]
            digit_index += 1
        else:
            result += char
    
    return result

# Helper function for Luhn algorithm
def generate_luhn_digit(partial_number):
    """Generate the last digit for a number to make it pass the Luhn check."""
    digits = [int(d) for d in partial_number]
    
    # Double every second digit from right to left
    for i in range(len(digits) - 1, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    
    # Calculate check digit
    total = sum(digits)
    return (10 - (total % 10)) % 10

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Use the custom operator
result = ally.anonymize(
    text="Payment made with card 4111-2222-3333-4444 expiring 12/25",
    operators={
        "CREDIT_CARD": format_preserving_cc
    }
)

print(result["text"])
# Output preserves format: "Payment made with card 4111-XXXX-XXXX-XXXX expiring 12/25"
```

### Differential Privacy Operator

This example adds noise to numerical values to implement differential privacy:

```python
from allyanonimiser import create_allyanonimiser
import re
import random

def differential_privacy_number(entity_text, entity_type):
    """
    Apply differential privacy to numerical values by adding
    Laplace noise proportional to the value.
    """
    if entity_type != "MONETARY_VALUE":
        return entity_text
    
    # Extract the numerical value
    match = re.search(r'[\d,.]+', entity_text)
    if not match:
        return entity_text
    
    # Convert to float
    try:
        value_str = match.group(0).replace(',', '')
        value = float(value_str)
    except ValueError:
        return entity_text
    
    # Add Laplace noise with scale proportional to the value
    epsilon = 0.1  # Privacy parameter (smaller = more privacy)
    scale = max(1.0, abs(value) * 0.05) / epsilon
    noise = random.normalvariate(0, scale)
    new_value = value + noise
    
    # Round to appropriate precision
    decimals = len(value_str.split('.')[-1]) if '.' in value_str else 0
    new_value = round(new_value, decimals)
    
    # Format with commas for thousands
    new_value_str = f"{new_value:,.{decimals}f}"
    
    # Replace the value in the original string
    return entity_text.replace(match.group(0), new_value_str)

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Use the custom operator
result = ally.anonymize(
    text="The policy premium is $1,234.56 per year.",
    operators={
        "MONETARY_VALUE": differential_privacy_number
    }
)

print(result["text"])
# Output might be: "The policy premium is $1,246.32 per year."
```

## Stateful Custom Operators

You can also create stateful operators by using closures or classes. This is useful when you need to maintain state across multiple anonymizations.

### Class-Based Operator

```python
from allyanonimiser import create_allyanonimiser

class EntityCounter:
    """A custom operator that keeps count of entity types seen."""
    
    def __init__(self):
        self.counts = {}
        
    def __call__(self, entity_text, entity_type):
        """Make the class instance callable as a function."""
        # Update count for this entity type
        self.counts[entity_type] = self.counts.get(entity_type, 0) + 1
        
        # Return a replacement with the count
        return f"<{entity_type}_{self.counts[entity_type]}>"
    
    def get_stats(self):
        """Return the current statistics."""
        return self.counts

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Create the stateful operator
counter_op = EntityCounter()

# Use the custom operator
result = ally.anonymize(
    text="John Smith and Jane Doe both live in Sydney.",
    operators={
        "PERSON": counter_op,
        "LOCATION": counter_op
    }
)

print(result["text"])
# Output: "<PERSON_1> and <PERSON_2> both live in <LOCATION_1>."

# Get statistics from the operator
print(counter_op.get_stats())
# Output: {'PERSON': 2, 'LOCATION': 1}
```

## Integration with AnonymizationConfig

You can also use custom operators with the `AnonymizationConfig` object:

```python
from allyanonimiser import create_allyanonimiser, AnonymizationConfig

# Define a custom operator
def uppercase_operator(entity_text, entity_type):
    return entity_text.upper()

# Create a configuration with the custom operator
config = AnonymizationConfig(
    operators={
        "PERSON": uppercase_operator,
        "EMAIL_ADDRESS": "mask",
        "POLICY_NUMBER": "replace"
    }
)

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Use the configuration
result = ally.anonymize(
    text="John Smith (john.smith@example.com) has policy POL-123456.",
    config=config
)

print(result["text"])
# Output: "JOHN SMITH (j***.s****@e******.com) has policy <POLICY_NUMBER>."
```

## See Also

- [Anonymization Operators](anonymization-operators.md) - Learn about built-in operators
- [Pattern Generalization](pattern-generalization.md) - Understanding pattern flexibility
- [Stream Processing](stream-processing.md) - Processing large volumes of data