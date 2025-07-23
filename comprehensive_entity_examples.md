# Comprehensive Entity Type Examples

## All Supported Entity Types (38 Total)

### 1. Australian-Specific Entities (13 types)

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Example text with all Australian entities
au_text = """
Customer Information:
- Name: John Smith
- Phone: 0412 345 678 (mobile) or (02) 9876 5432 (landline)
- Medicare Number: 2123 45678 1
- Tax File Number: 123 456 789
- Driver's License: VIC1234567 or NSW98765
- Home Address: 123 Collins Street, Melbourne VIC 3000
- Postal Address: PO Box 456, Sydney NSW 2000
- BSB: 062-000 Account Number: 1234567890
- ABN: 11 222 333 444
- ACN: 123 456 789
- Passport: PA1234567
- Centrelink CRN: 123 456 789A
- Vehicle Registration: ABC123 or 1ABC23
"""

results = ally.analyze(au_text)

# Group by entity type
from collections import defaultdict
entities_by_type = defaultdict(list)
for result in results:
    entities_by_type[result.entity_type].append(result.text)

# Display found entities
for entity_type, examples in sorted(entities_by_type.items()):
    print(f"{entity_type}: {', '.join(set(examples))}")
```

### 2. Insurance-Specific Entities (8 types)

```python
# Example text with all insurance entities
insurance_text = """
Claim Documentation:
- Policy Number: POL-12345678 or AU-98765432
- Claim Number: CL-23456789 or C-987654
- Vehicle VIN: 1HGCM82633A123456
- Invoice Number: INV-2024001 or Q-5678
- Broker Code: BRK-1234
- Vehicle Details: 2022 Toyota Camry, 2023 Ford Ranger
- Date of Incident: on 15/03/2024
- Assigned To: Sarah Johnson (Consultant)
- Handler: Michael Brown
- Agent: Lisa Wong
"""

results = ally.analyze(insurance_text)
```

### 3. General PII Entities (8 types)

```python
# Example text with general PII
general_text = """
Contact Details:
- Email: john.smith@example.com, support@company.com.au
- Credit Card: 4111 1111 1111 1111
- Date of Birth: DOB: 01/01/1990
- Various Dates: 15/03/2024, 2024-03-15, March 15, 2024
- Money Amounts: $1,234.56, $999,999.99
- Organizations: Right2Drive Pty Ltd, ABC Services Limited, XYZ Corp
- Locations: Sydney, Melbourne, Brisbane, New South Wales
- Person Names: John Smith, Sarah O'Connor, Dr. Michael Brown-Jones
"""

results = ally.analyze(general_text)
```

### 4. Additional spaCy NER Entities (9 types)

```python
# Example text with spaCy entities
spacy_text = """
Additional Information:
- Numbers: 42, 1234, 999
- Time: 3:30 PM, 14:45, midnight
- Percentages: 25%, 99.9%
- Products: iPhone 15, Windows 11, Toyota Camry
- Events: Olympic Games, Annual Conference
- Works of Art: "The Great Gatsby", Mona Lisa
- Laws: Privacy Act 1988, Section 45
- Languages: English, Mandarin, Spanish
- Facilities: Sydney Opera House, Melbourne Airport, Queen Victoria Building
"""

results = ally.analyze(spacy_text)
```

## Complete Entity Reference Table

| Entity Type | Description | Example |
|-------------|-------------|---------|
| **Australian-Specific** | | |
| AU_TFN | Tax File Number | 123 456 789 |
| AU_PHONE | Phone Number | 0412 345 678, (02) 9876 5432 |
| AU_MEDICARE | Medicare Number | 2123 45678 1 |
| AU_DRIVERS_LICENSE | Driver's License | VIC1234567, NSW98765 |
| AU_ADDRESS | Street Address | 123 Collins St, Melbourne VIC 3000 |
| AU_POSTCODE | Postcode | 2000, 3000, 4000 |
| AU_BSB | Bank State Branch | 062-000, 123-456 |
| AU_ACCOUNT_NUMBER | Bank Account | 1234567890 |
| AU_ABN | Business Number | 11 222 333 444 |
| AU_ACN | Company Number | 123 456 789 |
| AU_PASSPORT | Passport Number | PA1234567, AB9876543 |
| AU_CENTRELINK_CRN | Centrelink Reference | 123 456 789A |
| VEHICLE_REGISTRATION | Vehicle Rego | ABC123, 1ABC23 |
| **Insurance-Specific** | | |
| INSURANCE_POLICY_NUMBER | Policy Number | POL-12345678, AU-98765432 |
| INSURANCE_CLAIM_NUMBER | Claim Number | CL-23456789, C-987654 |
| VEHICLE_VIN | Vehicle ID Number | 1HGCM82633A123456 |
| INVOICE_NUMBER | Invoice/Quote | INV-2024001, Q-5678 |
| BROKER_CODE | Broker Code | BRK-1234 |
| VEHICLE_DETAILS | Vehicle Description | 2022 Toyota Camry |
| INCIDENT_DATE | Date of Incident | on 15/03/2024 |
| NAME_CONSULTANT | Consultant Name | Assigned To: Sarah Johnson |
| **General PII** | | |
| CREDIT_CARD | Credit Card | 4111 1111 1111 1111 |
| PERSON | Person Name | John Smith, Dr. Sarah O'Connor |
| EMAIL_ADDRESS | Email | john@example.com |
| DATE_OF_BIRTH | Date of Birth | DOB: 01/01/1990 |
| LOCATION | Location | Sydney, New South Wales |
| DATE | General Date | 15/03/2024, March 15, 2024 |
| MONEY_AMOUNT | Money Amount | $1,234.56 |
| ORGANIZATION | Organization | ABC Pty Ltd, XYZ Limited |
| **Additional spaCy** | | |
| NUMBER | Numeric Value | 42, 1234 |
| TIME | Time Expression | 3:30 PM, 14:45 |
| PERCENT | Percentage | 25%, 99.9% |
| PRODUCT | Product Name | iPhone 15, Windows 11 |
| EVENT | Event Name | Olympic Games |
| WORK_OF_ART | Title | "The Great Gatsby" |
| LAW | Legal Document | Privacy Act 1988 |
| LANGUAGE | Language | English, Spanish |
| FACILITY | Building/Airport | Sydney Opera House |

## Testing All Entities at Once

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()

# Comprehensive test text
comprehensive_text = """
INSURANCE CLAIM REPORT
Claim #: CL-23456789
Policy: POL-12345678
Date: 15/03/2024 at 3:30 PM

Customer Details:
Name: Dr. Sarah O'Connor
DOB: 01/01/1990
Email: sarah.oconnor@email.com
Phone: 0412 345 678
Address: 123 Collins Street, Melbourne VIC 3000
TFN: 123 456 789
Medicare: 2123 45678 1
License: VIC1234567
Passport: PA1234567

Financial Information:
BSB: 062-000 Account: 1234567890
Credit Card: 4111 1111 1111 1111
ABN: 11 222 333 444
Amount Claimed: $15,750.50 (GST inclusive - 10%)

Vehicle Information:
Registration: ABC123
VIN: 1HGCM82633A123456
Details: 2022 Toyota Camry Hybrid

Incident Details:
Location: Sydney Opera House, Sydney NSW
Date of Incident: on 10/03/2024
Assigned To: John Smith (Senior Consultant)
Broker: BRK-5678
Invoice: INV-2024001

Company: Right2Drive Pty Ltd
Language of Report: English
Relevant Law: Motor Accident Injuries Act 2017
Processing System: Windows 11
Event: Annual Safety Review
Reference Document: "Insurance Policy Guidelines"
Processing Time: 45 minutes
Success Rate: 99.5%
Items Processed: 1,234
"""

# Analyze and display all detected entities
results = ally.analyze(comprehensive_text)

# Create a summary of detections
entity_summary = {}
for result in results:
    if result.entity_type not in entity_summary:
        entity_summary[result.entity_type] = []
    entity_summary[result.entity_type].append({
        'text': result.text,
        'position': f"{result.start}-{result.end}",
        'confidence': f"{result.score:.2f}"
    })

# Print summary
print(f"Total entities detected: {len(results)}")
print(f"Unique entity types: {len(entity_summary)}")
print("\nDetection Summary:")
for entity_type, detections in sorted(entity_summary.items()):
    print(f"\n{entity_type} ({len(detections)} found):")
    for detection in detections[:3]:  # Show first 3 examples
        print(f"  - '{detection['text']}' at {detection['position']} (confidence: {detection['confidence']})")
    if len(detections) > 3:
        print(f"  ... and {len(detections) - 3} more")

# Anonymize with different operators for each entity type
config = {
    # Australian entities
    "AU_TFN": "hash",
    "AU_MEDICARE": "redact",
    "AU_PHONE": "mask",
    "AU_ADDRESS": "replace",
    "AU_BSB": "replace",
    "AU_ACCOUNT_NUMBER": "mask",
    
    # Sensitive identifiers
    "CREDIT_CARD": "redact",
    "EMAIL_ADDRESS": "replace",
    "PERSON": "replace",
    "DATE_OF_BIRTH": "redact",
    
    # Keep some for reference
    "ORGANIZATION": "keep",
    "LOCATION": "keep",
    "DATE": "keep"
}

anonymized = ally.anonymize(comprehensive_text, operators=config)
print("\nAnonymized Result Preview:")
print(anonymized['text'][:500] + "...")
```

## Pattern Validation Examples

```python
# Validate specific patterns
test_cases = {
    "AU_TFN": ["123 456 789", "123456789", "not a tfn"],
    "AU_MEDICARE": ["2123 45678 1", "5999 12345 9", "1234567890"],
    "AU_BSB": ["062-000", "123-456", "123456"],
    "EMAIL_ADDRESS": ["test@example.com", "user@company.com.au", "notanemail"],
    "CREDIT_CARD": ["4111 1111 1111 1111", "5500-0000-0000-0004", "1234"]
}

for entity_type, examples in test_cases.items():
    print(f"\nTesting {entity_type}:")
    for example in examples:
        results = ally.analyze(example)
        found = any(r.entity_type == entity_type for r in results)
        print(f"  '{example}': {'✓ Detected' if found else '✗ Not detected'}")
```