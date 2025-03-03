"""
Example script demonstrating how to implement custom anonymization operators.
"""
import re
from allyanonimiser import create_allyanonimiser, AnonymizationConfig

# Create Allyanonimiser instance
ally = create_allyanonimiser()

# Sample text with PII
sample_text = """
Customer information:
- Name: John Smith
- DOB: 15/06/1980
- Email: john.smith@example.com
- Phone: 0412 345 678
- Address: 123 Main Street, Sydney NSW 2000
- Policy: POL-12345678
- Claim Reference: CL-87654321
"""

# 1. Define custom operator functions
def custom_name_operator(text, entity_data):
    """Custom operator that replaces names with first initial and asterisks."""
    if not text:
        return "<NAME>"
    
    # Get first character and replace rest with asterisks
    first_char = text[0]
    rest_length = len(text) - 1
    return f"{first_char}{'*' * rest_length}"

def custom_email_operator(text, entity_data):
    """Custom operator that preserves domain but masks username."""
    if not text or '@' not in text:
        return "<EMAIL>"
    
    # Split email into username and domain
    username, domain = text.split('@', 1)
    masked_username = username[0] + '...' if username else ''
    return f"{masked_username}@{domain}"

def custom_policy_operator(text, entity_data):
    """Custom operator for policy numbers that preserves prefix but hashes numbers."""
    if not text:
        return "<POLICY>"
    
    # Check if text matches expected pattern (POL-numbers)
    match = re.match(r'(POL)-(\d+)', text)
    if match:
        prefix = match.group(1)
        numbers = match.group(2)
        # Replace numbers with fixed-length hash symbols
        return f"{prefix}-{'#' * len(numbers)}"
    
    return "<POLICY>"

# 2. Register custom operators with the anonymizer
ally.anonymizer.register_custom_operator("PERSON", custom_name_operator)
ally.anonymizer.register_custom_operator("EMAIL_ADDRESS", custom_email_operator)
ally.anonymizer.register_custom_operator("POLICY_NUMBER", custom_policy_operator)

# 3. Define a pattern for policy numbers
ally.manage_patterns(
    action="create_from_examples",
    entity_type="POLICY_NUMBER",
    examples=["POL-12345678", "POL-87654321"],
    context=["policy"]
)

# 4. Create anonymization configuration using custom operators
anonymization_config = AnonymizationConfig(
    operators={
        "PERSON": "custom",            # Use our custom name operator
        "EMAIL_ADDRESS": "custom",     # Use our custom email operator
        "POLICY_NUMBER": "custom",     # Use our custom policy operator
        "PHONE_NUMBER": "mask",        # Use built-in mask operator
        "ADDRESS": "replace",          # Use built-in replace operator
        "DATE_OF_BIRTH": "age_bracket" # Use built-in age bracket operator
    },
    age_bracket_size=10  # 10-year age brackets
)

# 5. Process the text with custom operators
result = ally.process(
    text=sample_text,
    anonymization_config=anonymization_config
)

# 6. Display results
print("=== Original text ===")
print(sample_text)

print("\n=== Anonymized text with custom operators ===")
print(result["anonymized"])

print("\n=== Detected entities ===")
for entity in result["analysis"]["entities"]:
    print(f"{entity['entity_type']}: {entity['text']} (score: {entity['score']:.2f})")

# 7. Example of inline operator registration and usage
def custom_age_operator(text, entity_data):
    """Convert exact age to 'Young/Middle-aged/Senior' category."""
    if not text:
        return "<AGE>"
    
    # Try to extract a year from formats like DOB: 15/06/1980
    year_match = re.search(r'\d{2}/\d{2}/(\d{4})', text)
    if year_match:
        year = int(year_match.group(1))
        current_year = 2024  # In a real system, use current date
        age = current_year - year
        
        if age < 18:
            return "<MINOR>"
        elif age < 40:
            return "<YOUNG ADULT>"
        elif age < 65:
            return "<MIDDLE-AGED>"
        else:
            return "<SENIOR>"
    
    return "<AGE UNKNOWN>"

# Register the new custom operator
ally.anonymizer.register_custom_operator("DATE_OF_BIRTH", custom_age_operator)

# Update configuration to use the new operator
anonymization_config.operators["DATE_OF_BIRTH"] = "custom"

# Process again with the new operator
result = ally.process(
    text=sample_text,
    anonymization_config=anonymization_config
)

print("\n=== Anonymized text with age categories ===")
print(result["anonymized"])