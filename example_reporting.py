#!/usr/bin/env python
"""
Example script demonstrating the new reporting capabilities in Allyanonimiser.

This script shows how to track anonymization statistics, generate reports, and
visualize entity distributions in Jupyter notebooks.
"""

from allyanonimiser import create_allyanonimiser, AnonymizationConfig
import os
import time

# Sample texts containing various PII
sample_texts = [
    """
    Customer Name: John Smith
    Policy Number: POL-12345678
    Date of Birth: 15/07/1982
    Email: john.smith@example.com
    Phone: 0412 345 678
    Address: 42 Main Street, Sydney NSW 2000
    TFN: 123 456 789
    """,
    
    """
    Claim #: CL-87654321
    Claimant: Jane Doe
    Medicare: 2345 67891 0
    Contact: jane.doe@company.org or 0423 456 789
    Incident occurred on 22/03/2023 at 123 Business Ave, Melbourne VIC 3000
    """,
    
    """
    Patient: Robert Johnson
    DOB: 10/11/1975
    Driver's License: NSW12345678
    Referred by Dr. Sarah Williams (Medical Registration: MED-98765)
    Clinical notes: Patient reports lower back pain following MVA on 05/02/2023.
    """
]

# Create output directory
os.makedirs("output", exist_ok=True)

def run_example():
    """Run the reporting example."""
    print("Allyanonimiser Reporting Example")
    print("-" * 50)
    
    # Create an Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Configure anonymization
    config = AnonymizationConfig(
        operators={
            "PERSON": "replace",
            "EMAIL_ADDRESS": "mask",
            "PHONE_NUMBER": "redact",
            "AU_ADDRESS": "replace",
            "DATE_OF_BIRTH": "age_bracket",
            "AU_TFN": "hash",
            "AU_MEDICARE": "mask"
        },
        age_bracket_size=10
    )
    
    # Start a new report session
    ally.start_new_report(session_id="example_session")
    print(f"Started new report session: {ally.get_report().session_id}")
    print()
    
    # Process each sample text
    print("Processing sample texts...")
    for i, text in enumerate(sample_texts):
        print(f"Processing sample {i+1}...")
        
        # Process the text and record statistics
        start = time.time()
        result = ally.anonymize(
            text=text,
            config=config,
            document_id=f"sample_{i+1}"
        )
        
        # Display original and anonymized text
        print("\nOriginal:")
        print(text.strip())
        print("\nAnonymized:")
        print(result["text"].strip())
        print("-" * 50)
    
    # Get report summary
    report = ally.get_report()
    summary = report.get_summary()
    
    print("\nReport Summary:")
    print(f"Total documents processed: {summary['total_documents']}")
    print(f"Total entities detected: {summary['total_entities']}")
    print(f"Entities per document: {summary['entities_per_document']:.2f}")
    print(f"Anonymization rate: {summary['anonymization_rate']*100:.2f}%")
    print(f"Average processing time: {summary['avg_processing_time']*1000:.2f} ms")
    
    print("\nEntity Type Distribution:")
    for entity_type, count in sorted(summary['entity_counts'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / summary['total_entities'] * 100
        print(f"  {entity_type}: {count} ({percentage:.1f}%)")
    
    # Export report in different formats
    print("\nExporting reports...")
    
    html_path = "output/anonymization_report.html"
    report.export_report(html_path, "html")
    print(f"HTML report saved to {html_path}")
    
    json_path = "output/anonymization_report.json"
    report.export_report(json_path, "json")
    print(f"JSON report saved to {json_path}")
    
    csv_path = "output/anonymization_stats.csv"
    report.export_report(csv_path, "csv")
    print(f"CSV statistics saved to {csv_path}")
    
    print("\nReport generation complete!")
    print("\nIn a Jupyter notebook, you can display the report with rich visualizations:")
    print("    ally.display_report_in_notebook()")
    print("\nOr process files with automatic report generation:")
    print("    result = ally.process_files(files, report=True, report_output='report.html')")

if __name__ == "__main__":
    run_example()