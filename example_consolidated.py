"""
Consolidated example showcasing the unified interface of Allyanonimiser.

This script demonstrates how Allyanonimiser provides a consistent interface
for processing different text types with automatic content detection.
"""

import os
from allyanonimiser import create_allyanonimiser

# Create output directory
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Create the Allyanonimiser instance
allya = create_allyanonimiser()

def process_and_save(text, output_filename, title):
    """Process text and save results to file."""
    print(f"\n\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    
    # Process the text with automatic content type detection
    result = allya.process(text)
    
    # Print detected content type
    print(f"Detected Content Type: {result['content_type']}")
    
    # Summary of entities found
    entity_counts = {}
    for entity in result['analysis']['entities']:
        entity_type = entity['entity_type']
        if entity_type not in entity_counts:
            entity_counts[entity_type] = 0
        entity_counts[entity_type] += 1
    
    print("\nEntities Detected:")
    for entity_type, count in sorted(entity_counts.items()):
        print(f"  {entity_type}: {count}")
    
    # Save results
    with open(os.path.join(output_dir, output_filename), "w") as f:
        f.write(f"ORIGINAL TEXT:\n{'-' * 40}\n{text}\n\n")
        f.write(f"ANONYMIZED TEXT:\n{'-' * 40}\n{result['anonymized']}\n\n")
        f.write(f"CONTENT TYPE: {result['content_type']}\n\n")
        
        if result['structured_data']:
            f.write("STRUCTURED DATA:\n")
            f.write("-" * 40 + "\n")
            for key, value in result['structured_data'].items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                f.write(f"{key}: {value}\n")
            f.write("\n")
        
        f.write("ENTITY DETECTION:\n")
        f.write("-" * 40 + "\n")
        for entity_type, count in sorted(entity_counts.items()):
            f.write(f"{entity_type}: {count}\n")
        f.write("\n")
        
        f.write("PII SEGMENTS:\n")
        f.write("-" * 40 + "\n")
        for i, segment in enumerate(result['segments']):
            if segment['pii_likelihood'] > 0.1:
                f.write(f"Segment {i+1} (PII score: {segment['pii_likelihood']:.2f}):\n")
                f.write(f"{segment['anonymized']}\n\n")
    
    print(f"Results saved to {os.path.join(output_dir, output_filename)}")

# Example 1: Email
email_text = """
From: john.smith@example.com
To: claims@insurance.com.au
Subject: Claim CL-12345678 - Vehicle Damage

Dear Claims Team,

I would like to follow up on my claim (CL-12345678) regarding the damage to my vehicle 
(Registration: ABC-123). The incident occurred on 15/07/2023.

My policy number is POL-987654. You can reach me at 0412 345 678 or at my address 
42 Wallaby Way, Sydney NSW 2000.

My Medicare number is 2345 67890 1 and TFN is 123 456 789, which I believe you requested 
for the medical expense reimbursement.

Regards,
John Smith
"""

process_and_save(email_text, "email_results.txt", "PROCESSING EMAIL")

# Example 2: Claim Note
claim_note = """
Claim Number: CL-12345678
Policy Number: POL-987654
Customer: John Smith

Customer called to report a vehicle accident that occurred on 15/07/2023. 
Customer was driving his Toyota Corolla (Registration: ABC-123, VIN: 1HGCM82633A123456) 
when another vehicle collided with him at the intersection of George St and Market St, Sydney.

Customer Details:
Name: John Smith
DOB: 14/08/1985
Phone: 0412 345 678
Email: john.smith@example.com
Address: 42 Wallaby Way, Sydney NSW 2000
TFN: 123 456 789
"""

process_and_save(claim_note, "claim_note_results.txt", "PROCESSING CLAIM NOTE")

# Example 3: Medical Report
medical_report = """
PATIENT: John Smith
DOB: 14/08/1985
MEDICARE: 2345 67890 1

ASSESSMENT:
Patient presented with lower back pain following a vehicle accident on 15/07/2023.
X-rays show no fractures but mild disc compression at L4-L5.

TREATMENT PLAN:
1. Prescribed pain relief: Paracetamol 500mg, 2 tablets every 4-6 hours
2. Referral to physiotherapy
3. Follow-up appointment in 2 weeks

Dr. Jane Wilson
Medical Practitioner
Medicare Provider: 123456AB
"""

process_and_save(medical_report, "medical_report_results.txt", "PROCESSING MEDICAL REPORT")

# Example 4: Generic Text
generic_text = """
Australian PII examples for testing:
- Name: John Smith
- Phone: 0412 345 678
- Email: john.smith@example.com
- TFN: 123 456 789
- Medicare: 2345 67890 1
- Address: 42 Wallaby Way, Sydney NSW 2000
- Driver's License: 12345678 (NSW)
- Passport: PA1234567
- Credit Card: 4111 1111 1111 1111
"""

process_and_save(generic_text, "generic_text_results.txt", "PROCESSING GENERIC TEXT")

print("\nAll processing complete!")
print(f"Results have been saved to the {output_dir} directory.")