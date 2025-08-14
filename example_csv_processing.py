#!/usr/bin/env python3
"""
Example demonstrating new CSV processing features in Allyanonimiser.

This example shows how to:
1. Process CSV files directly
2. Auto-detect PII columns
3. Preview changes before processing
4. Handle large files with streaming
5. Process entire directories
"""

import pandas as pd
import os
from allyanonimiser import create_allyanonimiser


def create_sample_csv():
    """Create a sample CSV file with PII data for testing."""
    data = pd.DataFrame({
        "customer_id": [1001, 1002, 1003, 1004, 1005],
        "full_name": [
            "Stephen Oates",
            "Jane Doe",
            "Alex Johnson",
            "Sarah Williams",
            "Michael Brown"
        ],
        "email": [
            "stephen.oates@example.com",
            "jane.doe@test.org",
            "alex.johnson@company.net",
            "s.williams@email.com",
            "mbrown@domain.co"
        ],
        "phone": [
            "0412 345 678",
            "02 9876 5432",
            "(03) 1234-5678",
            "0400-123-456",
            "+61 2 8765 4321"
        ],
        "address": [
            "123 Queen St, Sydney NSW 2000",
            "456 King Ave, Melbourne VIC 3000",
            "789 Prince Rd, Brisbane QLD 4000",
            "321 Duke Lane, Perth WA 6000",
            "654 Earl Court, Adelaide SA 5000"
        ],
        "notes": [
            "Customer Stephen Oates (DOB: 15/06/1980) called about policy POL-123456.",
            "Jane Doe requested refund for claim CLM-789012. Medicare: 2953 12345 1",
            "Alex Johnson from Sydney inquired about coverage. TFN: 123-456-789",
            "Sarah Williams updated her details. Email: sarah.private@gmail.com",
            "Michael Brown's credit card ending in 4532 was updated."
        ],
        "account_status": [
            "Active",
            "Pending",
            "Active",
            "Active",
            "Suspended"
        ],
        "last_updated": [
            "2024-01-15",
            "2024-02-20",
            "2024-03-10",
            "2024-04-05",
            "2024-05-12"
        ]
    })
    
    # Save to CSV
    csv_filename = "sample_customer_data.csv"
    data.to_csv(csv_filename, index=False)
    print(f"✓ Created sample CSV file: {csv_filename}")
    return csv_filename


def example_1_basic_csv_processing():
    """Example 1: Basic CSV file processing with specific columns."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic CSV Processing")
    print("="*60)
    
    # Create sample data
    csv_file = create_sample_csv()
    
    # Create Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Process specific columns
    result = ally.process_csv_file(
        input_file=csv_file,
        output_file="customer_data_anonymized.csv",
        columns_to_anonymize=["full_name", "email", "phone", "notes"],
        operators={
            "PERSON": "replace",
            "EMAIL_ADDRESS": "mask",
            "PHONE_NUMBER": "mask",
            "AU_MEDICARE": "redact",
            "AU_TFN": "redact",
            "CREDIT_CARD": "redact"
        }
    )
    
    print(f"\n✓ Processed {result['rows_processed']} rows")
    print(f"✓ Columns processed: {', '.join(result['columns_processed'])}")
    print(f"✓ Processing time: {result['processing_time_seconds']:.2f} seconds")
    
    print("\nEntities found:")
    for entity_type, count in sorted(result['entities_found'].items()):
        print(f"  • {entity_type}: {count}")
    
    print(f"\n✓ Output saved to: {result['output_file']}")
    if result.get('report_file'):
        print(f"✓ Report saved to: {result['report_file']}")


def example_2_auto_detect_pii():
    """Example 2: Auto-detect PII columns in CSV."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Auto-Detect PII Columns")
    print("="*60)
    
    csv_file = "sample_customer_data.csv"
    
    # Create Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Auto-detect PII columns
    print(f"\nAnalyzing CSV file: {csv_file}")
    pii_columns = ally.detect_pii_columns(
        csv_file,
        sample_size=5,
        min_detection_rate=0.2
    )
    
    print(f"\n✓ PII columns detected: {', '.join(pii_columns)}")
    
    # Process with auto-detected columns
    result = ally.process_csv_file(
        input_file=csv_file,
        output_file="customer_data_auto_processed.csv",
        columns_to_anonymize=None,  # Auto-detect
        generate_report=False
    )
    
    print(f"\n✓ Auto-processed {result['rows_processed']} rows")
    print(f"✓ Auto-detected columns: {', '.join(result.get('auto_detected_columns', []))}")


def example_3_preview_changes():
    """Example 3: Preview changes before processing."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Preview Changes Before Processing")
    print("="*60)
    
    csv_file = "sample_customer_data.csv"
    
    # Create Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Preview changes
    print(f"\nPreviewing changes for: {csv_file}")
    preview_df = ally.preview_csv_changes(
        csv_file,
        columns=["full_name", "email", "notes"],
        sample_rows=3
    )
    
    if not preview_df.empty:
        print("\nPreview of changes:")
        print("-" * 40)
        for idx, row in preview_df.iterrows():
            print(f"\nRow {row['row']}, Column: {row['column']}")
            print(f"  Original: {row['original'][:50]}...")
            print(f"  Anonymized: {row['anonymized'][:50]}...")
            print(f"  Entities found: {row['entities_found']}")
    else:
        print("No changes detected in preview")


def example_4_streaming_large_files():
    """Example 4: Stream process large CSV files."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Streaming Large CSV Files")
    print("="*60)
    
    # Create a larger CSV file for demonstration
    large_data = pd.DataFrame({
        "id": range(1, 10001),
        "name": [f"Person {i}" for i in range(1, 10001)],
        "email": [f"user{i}@example.com" for i in range(1, 10001)],
        "notes": [f"Customer Person {i} called about issue #{i*100}" for i in range(1, 10001)]
    })
    
    large_csv = "large_customer_data.csv"
    large_data.to_csv(large_csv, index=False)
    print(f"\n✓ Created large CSV with 10,000 rows: {large_csv}")
    
    # Create Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Stream process the large file
    print("\nStream processing large file...")
    result = ally.stream_process_csv(
        input_file=large_csv,
        output_file="large_data_anonymized.csv",
        columns=["name", "email", "notes"],
        chunk_size=1000  # Process 1000 rows at a time
    )
    
    print(f"\n✓ Processed {result['rows_processed']} rows in {result['chunks_processed']} chunks")
    print(f"✓ Processing time: {result['processing_time_seconds']:.2f} seconds")
    
    # Cleanup large files
    os.remove(large_csv)
    os.remove("large_data_anonymized.csv")


def example_5_process_directory():
    """Example 5: Process all CSV files in a directory."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Process Directory of CSV Files")
    print("="*60)
    
    # Create test directory with multiple CSV files
    os.makedirs("csv_files", exist_ok=True)
    
    for i in range(3):
        df = pd.DataFrame({
            "customer": [f"Customer {i}-{j}" for j in range(5)],
            "email": [f"cust{i}_{j}@example.com" for j in range(5)],
            "phone": [f"0400 {i}{j}0 000" for j in range(5)]
        })
        df.to_csv(f"csv_files/batch_{i}.csv", index=False)
    
    print("\n✓ Created test directory with 3 CSV files")
    
    # Create Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Process entire directory
    print("\nProcessing all CSV files in directory...")
    result = ally.process_csv_directory(
        input_dir="csv_files",
        output_dir="csv_files_anonymized",
        columns_to_anonymize=["customer", "email", "phone"]
    )
    
    print(f"\n✓ Processed {len(result['files_processed'])} files")
    print(f"✓ Total entities found:")
    for entity_type, count in sorted(result['total_entities_found'].items()):
        print(f"  • {entity_type}: {count}")
    
    # Cleanup
    import shutil
    shutil.rmtree("csv_files")
    shutil.rmtree("csv_files_anonymized")


def cleanup_example_files():
    """Clean up all example files created."""
    files_to_remove = [
        "sample_customer_data.csv",
        "customer_data_anonymized.csv",
        "customer_data_anonymized_report.txt",
        "customer_data_auto_processed.csv"
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    
    print("\n✓ Cleaned up example files")


def main():
    """Run all examples."""
    print("="*60)
    print("ALLYANONIMISER CSV PROCESSING EXAMPLES")
    print("="*60)
    
    try:
        # Run examples
        example_1_basic_csv_processing()
        example_2_auto_detect_pii()
        example_3_preview_changes()
        example_4_streaming_large_files()
        example_5_process_directory()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60)
        
    finally:
        # Clean up
        cleanup_example_files()


if __name__ == "__main__":
    main()