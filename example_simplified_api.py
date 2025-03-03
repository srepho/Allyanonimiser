"""
Example script demonstrating the simplified API for Allyanonimiser.
"""
import pandas as pd
from allyanonimiser import create_allyanonimiser, AnonymizationConfig, AnalysisConfig

# Sample text with PII
sample_text = """
Customer: John Smith (DOB: 15/06/1980)
Policy #: POL-12345678
Phone: 0412 345 678
Email: john.smith@example.com
Address: 123 Main Street, Sydney NSW 2000

The customer called regarding the claim CL-87654321 for their vehicle (Registration: ABC123).
They reported that they had an accident on 10/05/2024 involving another driver named Jane Doe.
"""

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# 1. Demonstrate the simplified process method with configuration objects
print("=== Example 1: Process method with configuration objects ===")
analysis_config = AnalysisConfig(
    language="en",
    active_entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "ADDRESS", "DATE_OF_BIRTH"],
    min_score_threshold=0.8,
    expand_acronyms=True
)

anonymization_config = AnonymizationConfig(
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask",
        "PHONE_NUMBER": "redact",
        "ADDRESS": "replace",
        "DATE_OF_BIRTH": "age_bracket"
    },
    age_bracket_size=10,
    keep_postcode=True
)

result = ally.process(
    text=sample_text,
    analysis_config=analysis_config,
    anonymization_config=anonymization_config
)

print("Anonymized text:")
print(result["anonymized"])
print("\nDetected entities:")
for entity in result["analysis"]["entities"]:
    print(f"{entity['entity_type']}: {entity['text']} (confidence: {entity['score']:.2f})")

# 2. Demonstrate the unified pattern management
print("\n=== Example 2: Unified pattern management ===")
# Add a custom pattern for a specific type of reference number
ref_pattern = ally.manage_patterns(
    action="create_from_examples", 
    entity_type="REFERENCE_NUMBER",
    examples=["REF-123456", "REF-789012"],
    context=["reference", "ref"]
)
print(f"Created pattern: {ref_pattern}")

# New test with custom pattern
test_text = "The customer provided their reference number REF-456789."
result = ally.process(test_text)
print("\nTest with custom pattern:")
print(result["anonymized"])

# 3. Demonstrate the unified acronym management
print("\n=== Example 3: Unified acronym management ===")
# Add some insurance acronyms
ally.manage_acronyms(
    action="add",
    data={
        "TPD": "Total and Permanent Disability",
        "CTP": "Compulsory Third Party",
        "DOL": "Date of Loss"
    }
)

# Get the current acronyms
acronyms = ally.manage_acronyms(action="get")
print("Current acronyms:")
for acronym, expansion in acronyms.items():
    print(f"{acronym}: {expansion}")

# Test with acronym expansion
test_text_with_acronyms = "The customer filed a TPD claim after the accident. DOL was reported as 10/05/2024."
result = ally.process(
    test_text_with_acronyms,
    analysis_config=AnalysisConfig(expand_acronyms=True)
)
print("\nTest with acronym expansion:")
print(result["anonymized"])
if "preprocessing" in result:
    print("\nExpanded acronyms:")
    for exp in result["preprocessing"]["expanded_acronyms"]:
        print(f"{exp['acronym']} → {exp['expansion']}")

# 4. Demonstrate unified DataFrame processing
print("\n=== Example 4: Unified DataFrame processing ===")
df = pd.DataFrame({
    "id": [1, 2, 3],
    "notes": [
        "Customer John Smith (DOB: 15/06/1980) called about policy POL-123456.",
        "Jane Doe (email: jane.doe@example.com) requested a refund.",
        "Alex Johnson from Sydney NSW 2000 reported an incident."
    ]
})

# Process DataFrame with analyze operation
result_df = ally.process_dataframe(
    df, 
    column="notes", 
    operation="detect",
    min_score_threshold=0.7
)
print("Detected entities in DataFrame:")
print(result_df)

# Process DataFrame with anonymize operation
anon_df = ally.process_dataframe(
    df, 
    column="notes", 
    operation="anonymize",
    output_column="anonymized_notes",
    operators={
        "PERSON": "replace",
        "EMAIL_ADDRESS": "mask"
    }
)
print("\nAnonymized DataFrame:")
print(anon_df)