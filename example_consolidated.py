"""
Consolidated example showing how to use the Allyanonimiser interface.
"""

import os
import json
from allyanonimiser import create_allyanonimiser

def process_single_text():
    """Process a single text with auto-detection of content type."""
    # Create the main interface
    allyanon = create_allyanonimiser()
    
    # Sample text (this could be any type - email, claim note, medical report, etc.)
    text = """
From: agent@insurance.com.au
To: john.smith@example.com
Subject: Your Claim CL-12345678

Dear Mr. Smith,

Thank you for your recent claim submission regarding your vehicle (Registration: XYZ123).

We have assigned your claim number CL-12345678. Please reference this number in all future correspondence.

Your policy POL-9876543 covers this type of damage, and we'll need the following information:
1. Your Medicare number
2. Additional photos of the damage
3. The repair quote from the mechanic

Please call me at 03 9876 5432 if you have any questions.

Kind regards,
Sarah Johnson
Claims Assessor
"""
    
    # Process the text - automatically detects content type and anonymizes
    print("Processing text with automatic content detection...\n")
    result = allyanon.process(text)
    
    # Print content type that was detected
    print(f"Detected content type: {result.get('content_type', 'unknown')}")
    
    # Print detected entities
    print("\nDetected entities:")
    for entity in result.get("entities", []):
        entity_text = entity.get("text", "")
        entity_type = entity.get("entity_type", "")
        entity_score = entity.get("score", 0)
        print(f"  - {entity_type}: {entity_text} (Score: {entity_score:.2f})")
    
    # Print anonymized text
    print("\nAnonymized text:")
    print("-" * 80)
    print(result.get("anonymized_text", ""))
    print("-" * 80)
    
    # Print anonymization statistics
    stats = result.get("anonymization_stats", {})
    print(f"\nTotal entities anonymized: {stats.get('total_items', 0)}")
    
    # Entity type counts
    print("\nEntities by type:")
    for entity_type, count in stats.get("entity_type_counts", {}).items():
        print(f"  - {entity_type}: {count}")
    
    return result

def process_multiple_text_types():
    """Process multiple text types with different configurations."""
    # Create the main interface
    allyanon = create_allyanonimiser()
    
    # Sample texts of different types
    texts = {
        "email": """
From: agent@insurance.com.au
To: jane.doe@example.com
Subject: Policy Renewal POL-789012

Dear Ms. Doe,

Your insurance policy POL-789012 is due for renewal on 15/06/2024.
Please contact us at 1800 123 456 to discuss your options.

Regards,
Insurance Team
""",
        "claim_note": """
Claim Reference: CL-23456789
Customer: John Smith

Customer called to report water damage in his bathroom.
Incident occurred on 10/05/2024 due to a burst pipe.
Policy POL-987654 covers water damage.

Customer Details:
Phone: 0412 345 678
Email: john.smith@example.com
Address: 123 Main St, Sydney NSW 2000
""",
        "medical_report": """
PATIENT: Alice Brown
DOB: 22/08/1975
MEDICARE: 2345 67890 1

ASSESSMENT:
Patient presented with lower back pain following a fall.
X-rays show no fractures.

TREATMENT PLAN:
1. Rest and ice
2. Paracetamol 500mg as needed
3. Follow-up in 2 weeks

Dr. Robert Lee
Medical Practitioner
"""
    }
    
    # Process each text with specific configurations
    results = {}
    
    print("Processing multiple text types with different configurations...\n")
    
    # Process email - redact all entities
    print("Processing email with redaction...")
    results["email"] = allyanon.process(
        texts["email"],
        content_type="email",  # Explicitly set content type
        operators={
            "EMAIL_ADDRESS": "redact",
            "PHONE_NUMBER": "redact",
            "AU_PHONE": "redact",
            "PERSON": "redact",
            "DATE": "redact",
            "INSURANCE_POLICY_NUMBER": "redact"
        }
    )
    
    # Process claim note - replace entities with realistic values
    print("\nProcessing claim note with realistic replacements...")
    results["claim_note"] = allyanon.process(
        texts["claim_note"],
        content_type="claim_note",
        operators={
            "PERSON": "replace",
            "AU_PHONE": "replace",
            "EMAIL_ADDRESS": "replace",
            "AU_ADDRESS": "replace",
            "INSURANCE_POLICY_NUMBER": "replace",
            "INSURANCE_CLAIM_NUMBER": "replace",
            "DATE": "replace"
        }
    )
    
    # Process medical report - custom masking
    print("\nProcessing medical report with custom masking...")
    results["medical_report"] = allyanon.process(
        texts["medical_report"],
        content_type="medical_report",
        mask_char="X",  # Use X instead of * for masking
        operators={
            "PERSON": "mask",
            "AU_MEDICARE": "mask_preserve_last_4",  # Keep last 4 digits
            "DATE": "replace"  # Replace dates with realistic values
        }
    )
    
    # Print anonymized texts
    for text_type, result in results.items():
        print(f"\n{text_type.upper()} - Anonymized:")
        print("-" * 80)
        print(result.get("anonymized_text", ""))
        print("-" * 80)
    
    return results

def batch_process_files():
    """Process multiple files in a directory."""
    # Create the main interface
    allyanon = create_allyanonimiser()
    
    # Create sample files in a temporary directory
    temp_dir = "temp_files"
    output_dir = "anonymized_files"
    
    # Create directories if they don't exist
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample texts
    texts = {
        "email.txt": """
From: agent@insurance.com.au
To: john.smith@example.com
Subject: Your Claim CL-12345678

Dear Mr. Smith,

Thank you for your claim submission. Your policy POL-9876543 covers this.
Please call me at 03 9876 5432 if you have questions.

Regards,
Sarah Johnson
""",
        "claim_note.txt": """
Claim Reference: CL-23456789
Customer: John Smith

Customer reported water damage. Incident occurred on 10/05/2024.
Policy POL-987654 covers water damage.

Customer phone: 0412 345 678
""",
        "medical_report.txt": """
PATIENT: Alice Brown
DOB: 22/08/1975
MEDICARE: 2345 67890 1

ASSESSMENT:
Patient presented with lower back pain.

Dr. Robert Lee
Medical Practitioner
"""
    }
    
    # Write sample files
    file_paths = []
    for filename, content in texts.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "w") as f:
            f.write(content)
        file_paths.append(file_path)
    
    print(f"Created {len(file_paths)} sample files in {temp_dir}.")
    
    # Process the files
    print(f"\nProcessing files with automatic content detection...")
    results = allyanon.process_files(
        file_paths=file_paths,
        output_dir=output_dir,
        anonymize=True,
        save_results=True
    )
    
    print(f"\nProcessed {len(results)} files. Results saved to {output_dir}.")
    
    # List anonymized files
    print("\nAnonymized files:")
    for filename in os.listdir(output_dir):
        if filename.endswith("_anonymized.txt"):
            print(f"  - {filename}")
    
    # Print an example analysis summary
    print("\nExample analysis summary:")
    for filename in os.listdir(output_dir):
        if filename.endswith("_analysis.json"):
            analysis_path = os.path.join(output_dir, filename)
            with open(analysis_path, "r") as f:
                analysis = json.load(f)
            
            # Print entity counts
            if "entities" in analysis:
                entity_counts = {}
                for entity in analysis["entities"]:
                    entity_type = entity.get("entity_type", "")
                    entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                
                print(f"  {filename}: {len(analysis['entities'])} entities found")
                for entity_type, count in entity_counts.items():
                    print(f"    - {entity_type}: {count}")
            
            # Only show one example
            break
    
    return results

if __name__ == "__main__":
    print("======= SINGLE TEXT PROCESSING EXAMPLE =======")
    process_single_text()
    
    print("\n\n======= MULTIPLE TEXT TYPES EXAMPLE =======")
    process_multiple_text_types()
    
    print("\n\n======= BATCH FILE PROCESSING EXAMPLE =======")
    batch_process_files()