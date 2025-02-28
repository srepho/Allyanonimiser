#!/usr/bin/env python
"""
Example showing how to use Allyanonimiser with pandas DataFrames.
"""

import pandas as pd
from allyanonimiser import create_allyanonimiser

# Create a sample DataFrame with PII data
data = {
    'id': range(1, 6),
    'name': [
        'John Smith',
        'Jane Doe',
        'Bob Johnson',
        'Alice Williams',
        'Michael Brown'
    ],
    'email': [
        'john.smith@example.com',
        'jane.doe@example.com',
        'bjohnson@example.com',
        'alice.w@example.com',
        'michael.brown@example.com'
    ],
    'note': [
        'Customer called about policy POL123456 on 05/04/2023',
        'Sent email regarding claim CL789012. Customer phone number is +61 4 1234 5678',
        'Medicare card 2123 45678 1 received for claim CL456789',
        'Australian TFN: 123 456 789. ABN: 51 824 753 556',
        'Discussed policy updates with Michael Brown at 42 Example St, Sydney NSW 2000'
    ]
}

df = pd.DataFrame(data)
print("Original DataFrame:")
print(df[['id', 'name', 'note']].head())
print("\n")

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

# Method 1: Detect PII in a specific column
print("Method 1: Detect PII in the 'note' column")
entities_df = ally.detect_pii_in_dataframe(
    df, 
    'note',
    min_score_threshold=0.7  # Adjust confidence threshold
)

# Display entity type counts
print(f"Detected {len(entities_df)} entities")
print(entities_df.groupby('entity_type').size())
print("\n")

# Method 2: Anonymize a specific column
print("Method 2: Anonymize the 'note' column")
anonymized_df = ally.anonymize_dataframe(
    df, 
    'note',
    operators={
        'PERSON': 'replace',
        'EMAIL_ADDRESS': 'mask',
        'PHONE_NUMBER': 'mask',
        'INSURANCE_POLICY_NUMBER': 'redact',
        'INSURANCE_CLAIM_NUMBER': 'redact',
        'AU_MEDICARE': 'redact',
        'DATE': 'replace'
    }
)

# Display original vs anonymized
comparison = pd.DataFrame({
    'Original': df['note'],
    'Anonymized': anonymized_df['note_anonymized']
})
print(comparison)
print("\n")

# Method 3: Process multiple columns with comprehensive analysis
print("Method 3: Process multiple columns")
result = ally.process_dataframe(
    df,
    text_columns=['name', 'email', 'note'],
    active_entity_types=[
        'PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER',
        'INSURANCE_POLICY_NUMBER', 'INSURANCE_CLAIM_NUMBER',
        'AU_MEDICARE', 'AU_TFN', 'AU_ABN', 'ADDRESS', 'DATE'
    ],
    operators={
        'PERSON': 'replace',
        'EMAIL_ADDRESS': 'mask',
        'PHONE_NUMBER': 'mask', 
        'INSURANCE_POLICY_NUMBER': 'redact',
        'INSURANCE_CLAIM_NUMBER': 'redact',
        'AU_MEDICARE': 'redact',
        'AU_TFN': 'redact',
        'AU_ABN': 'redact',
        'ADDRESS': 'replace',
        'DATE': 'replace'
    },
    batch_size=2,  # Process in small batches (for demonstration)
    progress_bar=True  # Show progress
)

# Access processed DataFrame
processed_df = result['dataframe']
print("Processed DataFrame:")
print(processed_df.head())
print("\n")

# Access all detected entities
all_entities = result['entities']
print(f"All detected entities: {len(all_entities)}")
print(all_entities.groupby(['column', 'entity_type']).size())
print("\n")

# Calculate entity statistics
processor = ally.create_dataframe_processor()
stats = processor.analyze_dataframe_statistics(all_entities, df, 'note')
print("Entity Statistics:")
print(stats)

# Demonstrate batch processing performance
# For larger datasets, adjust batch size and worker count
print("\nPerformance with larger dataset:")
large_df = pd.DataFrame({
    'id': range(100),
    'text': data['note'] * 20  # Repeat our sample data
})

# Process efficiently with parallel workers and appropriate batch size
large_result = ally.process_dataframe(
    large_df,
    text_columns='text',
    batch_size=25,  # Larger batch size for better performance
    n_workers=2,    # Use parallel processing
    progress_bar=True
)

print(f"Processed {len(large_df)} rows with {len(large_result['entities'])} detected entities")