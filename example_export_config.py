"""
Example script demonstrating how to export configuration settings.

This script shows how to:
1. Configure Allyanonimiser with various settings
2. Export a shareable configuration file
3. Import a configuration file in a new instance
"""

import os
from allyanonimiser import create_allyanonimiser
from allyanonimiser.utils.settings_manager import export_config

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

# Create an instance with custom settings
ally = create_allyanonimiser()

# Configure some settings
ally.set_acronym_dictionary({
    'PII': 'Personally Identifiable Information',
    'DOB': 'Date of Birth',
    'MVA': 'Motor Vehicle Accident',
    'SSN': 'Social Security Number',
    'DL': 'Driver License',
    'POL': 'Policy',
    'CL': 'Claim'
})

# Add a custom pattern
ally.add_pattern({
    'entity_type': 'CUSTOMER_REFERENCE',
    'patterns': [r'REF-\d{6}-[A-Z]{2}'],
    'context': ['customer', 'reference', 'ref'],
    'score': 0.85
})

# Import acronyms from CSV (if the file exists)
csv_path = 'examples/acronyms.csv'
if os.path.exists(csv_path):
    count = ally.import_acronyms_from_csv(csv_path)
    print(f"Imported {count} acronyms from {csv_path}")

# Configure processing settings
ally.settings_manager.set_batch_size(2000)
ally.settings_manager.set_worker_count(4)
ally.settings_manager.set_value('processing.use_pyarrow', True)

# Activate specific entity types
ally.settings_manager.set_entity_types([
    'PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'ADDRESS',
    'AU_MEDICARE', 'AU_TFN', 'INSURANCE_POLICY_NUMBER'
])

# Set anonymization operators
ally.settings_manager.set_anonymization_operators({
    'PERSON': 'replace',
    'EMAIL_ADDRESS': 'mask',
    'PHONE_NUMBER': 'mask',
    'ADDRESS': 'replace',
    'AU_MEDICARE': 'redact',
    'AU_TFN': 'redact'
})

# Export the configuration to different formats
print("\nExporting configuration files...")

# Export to JSON with metadata
json_config_path = 'output/allyanonimiser_config.json'
success = ally.export_config(json_config_path, include_metadata=True)
if success:
    print(f"Exported configuration to {json_config_path}")

# Export to YAML without metadata (more concise)
yaml_config_path = 'output/allyanonimiser_config.yaml'
success = ally.export_config(yaml_config_path, include_metadata=False)
if success:
    print(f"Exported configuration to {yaml_config_path}")

# Demonstrate how to load a configuration in a new instance
print("\nCreating a new instance with the exported configuration...")
new_ally = create_allyanonimiser(settings_path=json_config_path)

# Verify settings were loaded
entity_types = new_ally.settings_manager.get_entity_types()
acronyms = new_ally.get_acronyms()
print(f"Loaded instance has {len(entity_types)} active entity types and {len(acronyms)} acronyms")

# Display available entity types
print("\nActive entity types:")
for entity_type in entity_types:
    print(f"- {entity_type}")

# Process a sample text to demonstrate the configuration works
sample_text = """
John Doe (johndoe@example.com) submitted a claim for his policy POL-123456.
He lives at 123 Main St, Sydney NSW 2000 and can be reached at (02) 9876 5432.
His Medicare number is 2345 6789 0 and TFN is 123 456 789.
The customer reference is REF-987654-AB.
"""

print("\nAnalyzing sample text with loaded configuration...")
analysis = new_ally.analyze(sample_text)
print(f"Detected {len(analysis)} PII entities")

# Anonymize the text
result = new_ally.anonymize(sample_text)
print("\nAnonymized text:")
print(result['text'])

print("\nConfiguration export and import demonstration completed.")