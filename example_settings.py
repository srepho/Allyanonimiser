#!/usr/bin/env python
"""
Example showing how to use settings files with Allyanonimiser.
"""

import os
import pandas as pd
from allyanonimiser import create_allyanonimiser
from allyanonimiser.utils.settings_manager import create_default_settings, save_settings

# Create settings directory if it doesn't exist
os.makedirs("settings", exist_ok=True)

# Example 1: Create and save default settings
print("Example 1: Creating and saving default settings")
default_settings = create_default_settings()

# Add some team-specific acronyms
default_settings['acronyms']['dictionary'].update({
    "MC": "Motor Claims",
    "PI": "Personal Injury",
    "FOS": "Financial Ombudsman Service",
    "NC": "No Claims",
    "NCB": "No Claims Bonus",
    "FOS": "Financial Ombudsman Service",
    "UW": "Underwriter",
    "RTA": "Road Traffic Accident",
    "TPD": "Total Permanent Disability",
    "STP": "Straight Through Processing"
})

# Add some team-specific entity type configurations
default_settings['entity_types']['score_adjustment'].update({
    'INSURANCE_POLICY_NUMBER': 0.2,
    'INSURANCE_CLAIM_NUMBER': 0.2
})

# Configure processing options
default_settings['processing']['batch_size'] = 500
default_settings['processing']['worker_count'] = 4
default_settings['processing']['expand_acronyms'] = True

# Save as JSON
save_settings("settings/team_settings.json", default_settings)
print("Settings saved to settings/team_settings.json")

# Example 2: Create an instance with settings
print("\nExample 2: Creating an instance with settings")
ally = create_allyanonimiser(settings_path="settings/team_settings.json")

# Show loaded acronyms
acronyms = ally.get_acronyms()
print(f"Loaded {len(acronyms)} acronyms from settings:")
for acronym, expansion in list(acronyms.items())[:5]:
    print(f"  - {acronym}: {expansion}")
print(f"  ... and {len(acronyms) - 5} more")

# Example 3: Add team-specific acronyms and save updated settings
print("\nExample 3: Adding team-specific acronyms and saving updated settings")
ally.add_acronyms({
    "CSR": "Customer Service Representative",
    "IDV": "Identity Verification",
    "IDR": "Internal Dispute Resolution"
})

# Save the updated settings
ally.save_settings("settings/updated_settings.json")
print("Updated settings saved to settings/updated_settings.json")

# Example 4: Using settings with DataFrame processing
print("\nExample 4: Using settings with DataFrame processing")

# Create a sample DataFrame
df = pd.DataFrame({
    'id': range(1, 6),
    'notes': [
        "MC team received a call from TP John Smith about his RTA claim",
        "UW Sarah Johnson approved the PI claim after reviewing medical reports",
        "Customer called about NCB discount on POL123456",
        "Case referred to FOS after IDR process was completed",
        "NC status confirmed for customer after TPD assessment"
    ]
})

# Process with settings-configured batch size and worker count
result = ally.process_dataframe(
    df,
    text_columns='notes',
    expand_acronyms=True  # Use the acronyms from settings
)

# Show the processed results
print("\nProcessed DataFrame with expanded acronyms:")
for i, row in result['dataframe'].iterrows():
    print(f"Original: {df.loc[i, 'notes']}")
    print(f"Anonymized: {row['notes_anonymized']}")
    print()

# Example 5: Sharing settings with a team
print("Example 5: Instructions for sharing settings with a team")
print("""
To share these settings with your team:

1. Share the settings file 'settings/team_settings.json' with team members
2. Team members can use it with:
   
   ```python
   from allyanonimiser import create_allyanonimiser
   
   # Create analyzer with team settings
   ally = create_allyanonimiser(settings_path="path/to/team_settings.json")
   
   # Now the analyzer is configured with all team acronyms and settings
   ```

3. For automated use, place the settings file in a standard location
   and reference it in scripts or config files
""")