#!/usr/bin/env python3
"""List all supported entity types in Allyanonimiser."""

from allyanonimiser import create_allyanonimiser
from allyanonimiser.patterns.au_patterns import get_au_pattern_definitions
from allyanonimiser.patterns.insurance_patterns import get_insurance_pattern_definitions
from allyanonimiser.patterns.general_patterns import get_general_pattern_definitions

# Get all pattern definitions
au_patterns = get_au_pattern_definitions()
insurance_patterns = get_insurance_pattern_definitions()
general_patterns = get_general_pattern_definitions()

# Create analyzer to get spaCy entities
analyzer = create_allyanonimiser()

print("ALL SUPPORTED ENTITY TYPES IN ALLYANONIMISER")
print("=" * 80)

# Organize by category
categories = {
    "Australian-Specific Entities": [],
    "Insurance-Specific Entities": [],
    "General PII Entities": [],
    "spaCy NER Entities": []
}

# Process Australian patterns
print("\n1. AUSTRALIAN-SPECIFIC ENTITIES:")
print("-" * 40)
for pattern in au_patterns:
    entity_type = pattern['entity_type']
    name = pattern['name']
    print(f"  {entity_type:<30} - {name}")
    categories["Australian-Specific Entities"].append((entity_type, name))

# Process Insurance patterns
print("\n2. INSURANCE-SPECIFIC ENTITIES:")
print("-" * 40)
for pattern in insurance_patterns:
    entity_type = pattern['entity_type']
    name = pattern['name']
    print(f"  {entity_type:<30} - {name}")
    categories["Insurance-Specific Entities"].append((entity_type, name))

# Process General patterns
print("\n3. GENERAL PII ENTITIES:")
print("-" * 40)
for pattern in general_patterns:
    entity_type = pattern['entity_type']
    name = pattern['name']
    print(f"  {entity_type:<30} - {name}")
    categories["General PII Entities"].append((entity_type, name))

# spaCy entities that are also supported
print("\n4. ADDITIONAL spaCy NER ENTITIES:")
print("-" * 40)
spacy_entities = [
    ("NUMBER", "Numeric values"),
    ("TIME", "Time expressions"),
    ("PERCENT", "Percentage values"),
    ("PRODUCT", "Product names"),
    ("EVENT", "Event names"),
    ("WORK_OF_ART", "Titles of works"),
    ("LAW", "Legal documents"),
    ("LANGUAGE", "Language names"),
    ("FACILITY", "Buildings, airports, etc.")
]
for entity_type, desc in spacy_entities:
    print(f"  {entity_type:<30} - {desc}")
    categories["spaCy NER Entities"].append((entity_type, desc))

# Count total
total = sum(len(entities) for entities in categories.values())
print(f"\n{'-' * 80}")
print(f"TOTAL ENTITY TYPES SUPPORTED: {total}")

# Generate example text for each category
print("\n" + "=" * 80)
print("EXAMPLE TEXTS FOR TESTING EACH CATEGORY:")
print("=" * 80)

# Australian examples
print("\n1. Australian-Specific Example:")
print("""
Customer Details:
Name: John Smith
Phone: 0412 345 678
Medicare: 2123 45678 1
TFN: 123 456 789
Driver's License: VIC1234567
Address: 123 Collins Street, Melbourne VIC 3000
BSB: 062-000 Account Number: 1234567890
ABN: 11 222 333 444
Passport: PA1234567
Vehicle Registration: ABC123
""")

# Insurance examples
print("\n2. Insurance-Specific Example:")
print("""
Claim Details:
Policy Number: POL-12345678
Claim Number: CL-98765432
Vehicle VIN: 1HGCM82633A123456
Invoice Number: INV-2024001
Broker Code: BRK-5678
Vehicle: 2022 Toyota Camry
Incident Date: 15/03/2024
Assigned To: Sarah Johnson
""")

# General PII examples
print("\n3. General PII Example:")
print("""
Contact Information:
Email: john.smith@example.com
Credit Card: 4111 1111 1111 1111
Date of Birth: 01/01/1990
Amount Due: $1,234.56
Company: Right2Drive Pty Ltd
Location: Sydney, New South Wales
""")

# Count examples needed
print("\n" + "=" * 80)
print("ENTITIES THAT NEED EXAMPLE COVERAGE IN README:")
print("=" * 80)

# List all entities for easy reference
all_entities = []
for category, entities in categories.items():
    for entity_type, name in entities:
        all_entities.append(entity_type)

print(f"\nTotal unique entity types: {len(set(all_entities))}")
print("\nAll entity types (for README reference):")
for i, entity in enumerate(sorted(set(all_entities)), 1):
    print(f"{i:2d}. {entity}")