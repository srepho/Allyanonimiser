"""
Comprehensive example demonstrating all features of the Allyanonimiser simplified API.

This example covers:
1. Configuration with AnalysisConfig and AnonymizationConfig
2. Pattern management for custom PII types
3. Acronym management and expansion
4. Error handling patterns
5. Custom anonymization operators
6. DataFrame processing with performance optimization
7. Batch processing
8. Structured data extraction
"""
import pandas as pd
import re 
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig

print("=== 1. Creating and configuring the Allyanonimiser ===")
# Create instance with default settings
ally = create_allyanonimiser()

# Sample text for examples
sample_text = """
Customer Information:
Name: John Smith
DOB: 15/06/1980
Email: john.smith@example.com
Phone: 0412 345 678
Address: 123 Main Street, Sydney NSW 2000
Policy: POL-12345678

The customer called regarding their TPD claim CL-87654321. 
They reported that their DOL was 10/05/2024.
"""

print("\n=== 2. Configuration Objects ===")
# Create configuration objects with specific settings
analysis_config = AnalysisConfig(
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "DATE_OF_BIRTH"],
    min_score_threshold=0.7,
    expand_acronyms=True,
    score_adjustment={"PERSON": 0.1}  # Increase confidence for PERSON entities
)

anonymization_config = AnonymizationConfig(
    operators={
        "PERSON": "replace",          # Replace with <PERSON>
        "EMAIL_ADDRESS": "mask",      # Replace with *****
        "PHONE_NUMBER": "redact",     # Replace with [REDACTED]
        "DATE_OF_BIRTH": "age_bracket"  # Replace with age bracket
    },
    age_bracket_size=10,
    keep_postcode=True
)

# Process with configuration objects
result = ally.process(
    text=sample_text,
    analysis_config=analysis_config,
    anonymization_config=anonymization_config
)

print("Anonymized text with configuration objects:")
print(result["anonymized"])

print("\nDetected entities:")
for entity in result["analysis"]["entities"]:
    print(f"{entity['entity_type']}: {entity['text']} (score: {entity['score']:.2f})")

print("\n=== 3. Acronym Management ===")
# Add insurance acronyms
ally.manage_acronyms(
    action="add",
    data={
        "TPD": "Total and Permanent Disability",
        "CTP": "Compulsory Third Party",
        "DOL": "Date of Loss"
    }
)

# Get current acronyms
acronyms = ally.manage_acronyms(action="get")
print("Current acronyms:")
for acronym, expansion in acronyms.items():
    print(f"{acronym}: {expansion}")

# Process with acronym expansion
result_with_acronyms = ally.process(
    text=sample_text,
    analysis_config=AnalysisConfig(expand_acronyms=True)
)

print("\nText with expanded acronyms:")
print(result_with_acronyms["anonymized"])

if "preprocessing" in result_with_acronyms:
    print("\nExpanded acronyms:")
    for exp in result_with_acronyms["preprocessing"]["expanded_acronyms"]:
        print(f"{exp['acronym']} → {exp['expansion']}")

print("\n=== 4. Pattern Management ===")
# Create patterns for custom entity types
policy_pattern = ally.manage_patterns(
    action="create_from_examples",
    entity_type="POLICY_NUMBER",
    examples=["POL-12345678", "POL-87654321", "POL-456789"],
    context=["policy", "number"],
    name="Policy Number Pattern",
    generalization_level="medium"  # Options: "low", "medium", "high"
)

claim_pattern = ally.manage_patterns(
    action="create_from_examples",
    entity_type="CLAIM_ID",
    examples=["CL-12345", "CL-67890", "CL-54321"],
    context=["claim", "id", "reference"],
    name="Claim ID Pattern"
)

print(f"Generated policy pattern: {policy_pattern.patterns[0]}")
print(f"Generated claim pattern: {claim_pattern.patterns[0]}")

# Test patterns
test_text = "Policy: POL-555555, Claim: CL-99999"
result_patterns = ally.process(
    text=test_text,
    analysis_config=AnalysisConfig(
        active_entity_types=["POLICY_NUMBER", "CLAIM_ID"] 
    )
)

print("\nTest with custom patterns:")
print(result_patterns["anonymized"])
for entity in result_patterns["analysis"]["entities"]:
    print(f"{entity['entity_type']}: {entity['text']} (score: {entity['score']:.2f})")

print("\n=== 5. Error Handling ===")
# Example error handling function
def process_with_error_handling(text, entity_types=None):
    try:
        # Input validation
        if entity_types and not isinstance(entity_types, list):
            raise ValueError("entity_types must be a list")
            
        # Configure
        analysis_config = AnalysisConfig(
            active_entity_types=entity_types,
            min_score_threshold=0.7
        )
        
        # Process
        return ally.process(text, analysis_config=analysis_config)
    except ValueError as e:
        print(f"Configuration error: {e}")
        # Fallback to default configuration
        return ally.process(text)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Test error handling
print("Testing error handling with invalid configuration:")
result_error = process_with_error_handling("John Smith sent an email", entity_types="PERSON")  # Invalid entity_types
if result_error:
    print("Successfully processed with fallback configuration")

print("\n=== 6. Custom Operators ===")
# Define custom operator functions
def custom_name_operator(text, entity_data):
    """Custom operator that replaces names with first initial and asterisks."""
    if not text:
        return "<NAME>"
    
    first_char = text[0]
    rest_length = len(text) - 1
    return f"{first_char}{'*' * rest_length}"

def custom_policy_operator(text, entity_data):
    """Custom operator for policy numbers that preserves prefix but hashes numbers."""
    if not text:
        return "<POLICY>"
    
    match = re.match(r'(POL)-(\d+)', text)
    if match:
        prefix = match.group(1)
        numbers = match.group(2)
        return f"{prefix}-{'#' * len(numbers)}"
    
    return "<POLICY>"

# Register custom operators
ally.anonymizer.register_custom_operator("PERSON", custom_name_operator)
ally.anonymizer.register_custom_operator("POLICY_NUMBER", custom_policy_operator)

# Process with custom operators
custom_config = AnonymizationConfig(
    operators={
        "PERSON": "custom",           # Use our custom name operator
        "POLICY_NUMBER": "custom",    # Use our custom policy operator
        "EMAIL_ADDRESS": "mask"       # Use built-in mask operator
    }
)

result_custom = ally.process(
    text=sample_text,
    anonymization_config=custom_config
)

print("Anonymized text with custom operators:")
print(result_custom["anonymized"])

print("\n=== 7. DataFrame Processing ===")
# Create sample DataFrame
df = pd.DataFrame({
    "id": [1, 2, 3],
    "notes": [
        "Customer John Smith (DOB: 15/06/1980) called about policy POL-123456.",
        "Jane Doe (email: jane.doe@example.com) requested a refund.",
        "Alex Johnson from Sydney NSW 2000 reported an incident."
    ]
})

print("Original DataFrame:")
print(df)

# Process DataFrame - detection only
print("\nDetecting entities in DataFrame:")
entities_df = ally.process_dataframe(
    df,
    column="notes",
    operation="detect",
    min_score_threshold=0.7
)
print(entities_df.head())

# Process DataFrame - anonymization
print("\nAnonymizing DataFrame:")
anon_df = ally.process_dataframe(
    df,
    column="notes",
    operation="anonymize",
    output_column="anonymized_notes",
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "POLICY_NUMBER": "custom"  # Uses our registered custom operator
    }
)
print(anon_df)

print("\n=== 8. Structured Data Extraction ===")
# Process text and extract structured data
result_structured = ally.process(
    text=sample_text,
    analysis_config=analysis_config,
    anonymization_config=anonymization_config
)

print("Extracted structured data:")
for key, value in result_structured["structured_data"].items():
    print(f"{key}: {value}")

print("\nPII-rich segments:")
for segment in result_structured["segments"]:
    print(f"Original: {segment['text']}")
    print(f"Anonymized: {segment['anonymized']}")
    print("")

print("\n=== 9. Configuration Export and Reuse ===")
# Export current configuration
ally.export_config("output/allyanonimiser_config.json")
print("Exported configuration to output/allyanonimiser_config.json")
print("To reuse: create_allyanonimiser(settings_path='output/allyanonimiser_config.json')")

print("\n=== Complete Example Finished ===")