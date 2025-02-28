#!/usr/bin/env python
"""
Example showing how to use acronym expansion with Allyanonimiser.
"""

from allyanonimiser import create_allyanonimiser
from allyanonimiser.utils.text_preprocessor import preprocess_with_acronym_expansion

# Define a dictionary of acronyms and their expanded forms
acronyms = {
    "TP": "Third Party",
    "TL": "Team Leader",
    "PII": "Personally Identifiable Information",
    "POL": "Policy",
    "CL": "Claim",
    "DOB": "Date of Birth",
    "MVA": "Motor Vehicle Accident",
    "QOL": "Quality of Life",
    "WC": "Workers Compensation"
}

# Example 1: Simple usage with the standalone function
print("Example 1: Standalone acronym expansion")
text = "The TP reported a MVA to their TL, who filed a CL."
expanded_text = preprocess_with_acronym_expansion(text, acronyms)
print(f"Original: {text}")
print(f"Expanded: {expanded_text}")
print()

# Example 2: Integration with Allyanonimiser for analysis
print("Example 2: Acronym expansion during analysis")
ally = create_allyanonimiser()

# Set the acronym dictionary on the Allyanonimiser instance
ally.set_acronym_dictionary(acronyms)

# Text with acronyms that might hide PII detection
text_with_acronyms = """
TP John Smith (DOB 15/04/1982) was involved in a MVA on Main Street.
The TL Sarah Johnson reviewed the case and approved the CL payment for POL-12345.
Contact the TP at 0412 345 678 or john.smith@example.com.
"""

# First analyze without expanding acronyms
print("Analysis WITHOUT acronym expansion:")
results_without_expansion = ally.analyze(text_with_acronyms)
print(f"Detected {len(results_without_expansion)} entities:")
for entity in results_without_expansion:
    print(f"  - {entity.entity_type}: {entity.text}")
print()

# Then analyze with acronym expansion
print("Analysis WITH acronym expansion:")
results_with_expansion = ally.analyze(text_with_acronyms, expand_acronyms=True)
print(f"Detected {len(results_with_expansion)} entities:")
for entity in results_with_expansion:
    print(f"  - {entity.entity_type}: {entity.text}")
print()

# Example 3: Anonymization with acronym expansion
print("Example 3: Anonymization with acronym expansion")
anonymized = ally.anonymize(
    text_with_acronyms,
    expand_acronyms=True,
    operators={
        'PERSON': 'replace',
        'EMAIL_ADDRESS': 'mask',
        'PHONE_NUMBER': 'mask',
        'DATE': 'replace'
    }
)
print("Anonymized text:")
print(anonymized["text"])
print()

# Example 4: Full processing with acronym expansion
print("Example 4: Full processing with acronym expansion")
result = ally.process(text_with_acronyms, expand_acronyms=True)

# Print the structured data extracted
print("Extracted structured data:")
for key, value in result["structured_data"].items():
    print(f"  - {key}: {value}")
print()

# Print information about expanded acronyms
print("Expanded acronyms:")
for expansion in result["preprocessing"]["expanded_acronyms"]:
    print(f"  - {expansion['acronym']} → {expansion['expansion']}")
print()

# Example 5: Adding and removing acronyms dynamically
print("Example 5: Managing acronyms dynamically")

# Add new acronyms
ally.add_acronyms({
    "SLA": "Service Level Agreement",
    "EOI": "Evidence of Identity"
})

# Text with new acronyms
new_text = "The TL requested EOI according to the SLA."
expanded = ally.process(new_text, expand_acronyms=True)
print(f"Expanded with new acronyms: {expanded['anonymized']}")

# Remove an acronym
ally.remove_acronyms(["TL"])
expanded = ally.process(new_text, expand_acronyms=True)
print(f"After removing 'TL' acronym: {expanded['anonymized']}")
print()

# Example 6: Case sensitivity
print("Example 6: Case sensitivity in acronym expansion")

# Create a case-sensitive preprocessor
case_sensitive_ally = create_allyanonimiser()
case_sensitive_ally.set_acronym_dictionary(
    {"TP": "Third Party", "tp": "test procedure"},
    case_sensitive=True
)

# Text with mixed case acronyms
mixed_case_text = "The TP contacted us via email, following the tp guidelines."
expanded = case_sensitive_ally.process(mixed_case_text, expand_acronyms=True)
print(f"Case-sensitive expansion: {expanded['anonymized']}")
print(f"Expansions made: {expanded['preprocessing']['expanded_acronyms']}")