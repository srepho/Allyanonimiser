"""
Example script for analyzing and anonymizing insurance claim notes.
"""

import os
import json
from allyanonimiser import (
    create_au_insurance_analyzer,
    EnhancedAnonymizer
)
from allyanonimiser.utils.long_text_processor import (
    analyze_claim_notes,
    extract_pii_rich_segments
)

def analyze_claim_note():
    """Analyze an insurance claim note."""
    
    # Sample claim note (this would normally come from your database)
    claim_note = """
Claim Reference: CL-23456789
Customer: John Smith
Policy Number: POL-987654

Claim Details:
Customer called to report a vehicle accident that occurred on 15/07/2023. 
Customer was driving his Toyota Corolla (Registration: ABC123, VIN: 1HGCM82633A123456) 
when another vehicle collided with him at the intersection of George St and Market St, Sydney.

Customer Details:
Name: John Smith
DOB: 14/08/1985
Phone: 0412 345 678
Email: john.smith@example.com
Address: 123 Main St, Sydney NSW 2000
Medicare: 2345 67890 1
TFN: 123 456 789
License: NSW12345678

Vehicle Assessment:
Conducted vehicle inspection today. Significant damage to the front passenger side.
Repair quote from City Mechanics (Quote #: Q-9876) estimates $4,580 for repairs.
Customer has requested payment to their account (BSB: 062-000, Account: 12345678).

Discussion with Third Party:
Spoke with Jane Doe (0487 654 321) who was driving the other vehicle (Rego: XYZ789).
She accepts responsibility for the accident. Her insurance details: Sure Insurance, Policy #SI-456789.

Actions:
1. Approved repairs as per quote
2. Requested payment processing to customer's account
3. Initiated recovery process with Sure Insurance
4. Scheduled follow-up call for 25/07/2023
    """
    
    print("Analyzing Claim Note...\n")
    print("-" * 80)
    print(claim_note)
    print("-" * 80)
    
    print("\nAnalysis Results:")
    
    # Segment the text
    segments = extract_pii_rich_segments(claim_note)
    
    print("\nPII-rich segments (in order of importance):")
    for i, segment in enumerate(segments[:5]):  # Show top 5 segments
        print(f"{i+1}. PII Likelihood: {segment['pii_likelihood']:.2f}")
        print(f"   Text: {segment['text'][:100]}..." if len(segment['text']) > 100 else segment['text'])
        print(f"   Top PII types: {', '.join([f'{k} ({v:.2f})' for k, v in sorted(segment['pii_scores'].items(), key=lambda x: x[1], reverse=True)[:3]])}")
        print()
    
    # Perform detailed analysis
    analysis = analyze_claim_notes(claim_note)
    
    print("\nStructured Analysis:")
    if "section_segments" in analysis and "claim" in analysis["section_segments"]:
        print("\nClaim Details:")
        for segment in analysis["section_segments"]["claim"]:
            print(f"  - {segment['text']}")
    
    if "section_segments" in analysis and "customer" in analysis["section_segments"]:
        print("\nCustomer Details:")
        for segment in analysis["section_segments"]["customer"]:
            print(f"  - {segment['text']}")
    
    # Detect entities using the enhanced analyzer
    analyzer = create_au_insurance_analyzer()
    results = analyzer.analyze(claim_note)
    
    # Group results by entity type
    entities_by_type = {}
    for result in results:
        entity_type = result.entity_type
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        
        entities_by_type[entity_type].append({
            "text": claim_note[result.start:result.end],
            "score": result.score
        })
    
    print("\nDetected Entities:")
    for entity_type, entities in sorted(entities_by_type.items()):
        print(f"\n{entity_type}:")
        for entity in entities:
            print(f"  - {entity['text']} (Score: {entity['score']:.2f})")
    
    # Anonymize the claim note
    anonymizer = EnhancedAnonymizer(analyzer=analyzer)
    
    # Define anonymization operators
    operators = {
        "PERSON": "replace",
        "AU_PHONE": "mask",
        "AU_MEDICARE": "redact",
        "AU_TFN": "redact",
        "AU_DRIVERS_LICENSE": "hash",
        "AU_BSB_ACCOUNT": "mask",
        "AU_ADDRESS": "replace",
        "EMAIL_ADDRESS": "mask",
        "VEHICLE_REGISTRATION": "replace",
        "VEHICLE_VIN": "hash",
        "INSURANCE_POLICY_NUMBER": "replace",
        "INSURANCE_CLAIM_NUMBER": "replace",
        "INVOICE_NUMBER": "replace"
    }
    
    anonymized = anonymizer.anonymize(
        text=claim_note,
        operators=operators
    )
    
    print("\nAnonymized Claim Note:")
    print("-" * 80)
    print(anonymized["text"])
    print("-" * 80)
    
    # Save the anonymized text and analysis results
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "anonymized_claim_note.txt"), "w") as f:
        f.write(anonymized["text"])
    
    analysis_output = {
        "pii_segments": [
            {
                "text": segment["text"],
                "pii_likelihood": segment["pii_likelihood"],
                "top_pii_types": sorted(segment["pii_scores"].items(), key=lambda x: x[1], reverse=True)[:3]
            }
            for segment in segments[:5]
        ],
        "entities_by_type": {
            entity_type: [
                {
                    "text": entity["text"],
                    "score": entity["score"]
                }
                for entity in entities
            ]
            for entity_type, entities in entities_by_type.items()
        },
        "anonymized_text": anonymized["text"]
    }
    
    with open(os.path.join(output_dir, "claim_note_analysis.json"), "w") as f:
        json.dump(analysis_output, f, indent=2)
    
    print(f"\nResults saved to {output_dir} directory.")

def batch_process_claim_notes(input_dir, output_dir):
    """
    Batch process multiple claim notes.
    
    Args:
        input_dir: Directory containing claim note text files
        output_dir: Directory to save the results
    """
    print(f"Batch processing claim notes from {input_dir}...")
    
    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create analyzer and anonymizer
    analyzer = create_au_insurance_analyzer()
    anonymizer = EnhancedAnonymizer(analyzer=analyzer)
    
    # Define anonymization operators
    operators = {
        "PERSON": "replace",
        "AU_PHONE": "mask",
        "AU_MEDICARE": "redact",
        "AU_TFN": "redact",
        "AU_DRIVERS_LICENSE": "hash",
        "AU_BSB_ACCOUNT": "mask",
        "AU_ADDRESS": "replace",
        "EMAIL_ADDRESS": "mask",
        "VEHICLE_REGISTRATION": "replace",
        "VEHICLE_VIN": "hash",
        "INSURANCE_POLICY_NUMBER": "replace",
        "INSURANCE_CLAIM_NUMBER": "replace",
        "INVOICE_NUMBER": "replace"
    }
    
    # Process each file in the input directory
    file_count = 0
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            
            # Read the claim note
            with open(file_path, 'r') as f:
                claim_note = f.read()
            
            # Analyze and anonymize
            analysis = analyze_claim_notes(claim_note)
            results = analyzer.analyze(claim_note)
            anonymized = anonymizer.anonymize(
                text=claim_note,
                operators=operators
            )
            
            # Save anonymized text
            anonymized_path = os.path.join(output_dir, f"anonymized_{filename}")
            with open(anonymized_path, 'w') as f:
                f.write(anonymized["text"])
            
            # Save analysis results
            analysis_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_analysis.json")
            
            # Prepare analysis output
            analysis_output = {
                "original_file": filename,
                "pii_segments": [
                    {
                        "text": segment["text"],
                        "pii_likelihood": segment["pii_likelihood"]
                    }
                    for segment in analysis["pii_segments"][:5]
                ],
                "entities": [
                    {
                        "entity_type": result.entity_type,
                        "text": claim_note[result.start:result.end],
                        "score": result.score
                    }
                    for result in results
                ]
            }
            
            with open(analysis_path, 'w') as f:
                json.dump(analysis_output, f, indent=2)
            
            file_count += 1
    
    print(f"Processed {file_count} claim notes. Results saved to {output_dir}.")

def interactive_demo():
    """Run an interactive demo for analyzing claim notes."""
    print("Allyanonimiser - Interactive Claim Notes Analyzer")
    print("=" * 50)
    print("\nThis demo allows you to analyze and anonymize claim notes.")
    
    while True:
        print("\nOptions:")
        print("1. Analyze sample claim note")
        print("2. Analyze your own claim note")
        print("3. Batch process claim notes")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            analyze_claim_note()
        elif choice == '2':
            print("\nEnter your claim note (type END on a new line when finished):")
            lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                lines.append(line)
            
            claim_note = '\n'.join(lines)
            
            # Create analyzer and anonymizer
            analyzer = create_au_insurance_analyzer()
            anonymizer = EnhancedAnonymizer(analyzer=analyzer)
            
            # Analyze
            results = analyzer.analyze(claim_note)
            
            print("\nDetected Entities:")
            for result in results:
                print(f"  - {result.entity_type}: {claim_note[result.start:result.end]} (Score: {result.score:.2f})")
            
            # Anonymize
            anonymized = anonymizer.anonymize(claim_note)
            
            print("\nAnonymized Text:")
            print(anonymized["text"])
        elif choice == '3':
            input_dir = input("\nEnter input directory path: ")
            output_dir = input("Enter output directory path: ")
            
            if os.path.isdir(input_dir):
                batch_process_claim_notes(input_dir, output_dir)
            else:
                print(f"Error: {input_dir} is not a valid directory.")
        elif choice == '4':
            print("\nExiting the demo. Thank you for using Allyanonimiser!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Run the interactive demo
    interactive_demo()