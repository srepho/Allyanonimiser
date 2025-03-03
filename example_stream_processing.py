"""
Example of stream processing very large files with Allyanonimiser using Polars.

This example demonstrates how to process CSV files that are too large to fit
in memory using streaming techniques with minimal memory impact.
"""

import os
import time
import pandas as pd
from allyanonimiser import create_allyanonimiser
from allyanonimiser.stream_processor import StreamProcessor, POLARS_AVAILABLE

# Check if Polars is available
if not POLARS_AVAILABLE:
    print("Polars is required for stream processing but is not installed.")
    print("Install with: pip install polars")
    print("Exiting example...")
    exit(1)

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Create a sample CSV file for demonstration
def create_sample_file(rows=1000, output_path="output/large_sample.csv"):
    """Create a sample CSV file with PII data for testing."""
    print(f"Creating sample file with {rows} rows...")
    
    # Create sample data with PII
    data = []
    for i in range(rows):
        data.append({
            "id": i,
            "name": f"John Doe {i}",
            "email": f"john.doe{i}@example.com",
            "phone": f"+61 4{i:02d} {i:03d} {i:03d}",
            "note": f"Customer John Doe {i} called from +61 4{i:02d} {i:03d} {i:03d} "
                   f"about their policy. They can be reached at john.doe{i}@example.com. "
                   f"Their address is 123 Main St, Sydney NSW 2000."
        })
    
    # Write to CSV
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Sample file created at {output_path}")
    return output_path

# Create the Allyanonimiser instance
print("Creating Allyanonimiser instance...")
allyanonimiser = create_allyanonimiser()

# Create StreamProcessor instance
print("Creating StreamProcessor instance...")
stream_processor = StreamProcessor(allyanonimiser=allyanonimiser, n_workers=4)

# Generate sample file
sample_file = create_sample_file(rows=10000)  # Increase for larger test

# Example 1: Process a large file with simple streaming
print("\nExample 1: Process large file with simple streaming")
print("-" * 60)

# Define entity types to detect
active_entity_types = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "ADDRESS"]

# Define anonymization operators
operators = {
    "PERSON": "replace",
    "PHONE_NUMBER": "mask",
    "EMAIL_ADDRESS": "redact",
    "ADDRESS": "replace"
}

# Process large file and measure time
start_time = time.time()

result = stream_processor.process_large_file(
    file_path=sample_file,
    text_columns=["note", "name", "email", "phone"],
    output_path="output/processed_sample.csv",
    active_entity_types=active_entity_types,
    operators=operators,
    chunk_size=1000,
    save_entities=True,
    entities_output_path="output/detected_entities.csv",
    progress_bar=True
)

end_time = time.time()
duration = end_time - start_time

print(f"\nProcessing completed in {duration:.2f} seconds")
print(f"Total rows processed: {result['total_rows_processed']}")
print(f"Total entities detected: {result['total_entities_detected']}")
print(f"Output file: {result['output_file']}")
print(f"Entities file: {result['entities_file']}")

# Example 2: Work with streaming chunks for custom processing
print("\nExample 2: Custom processing with streaming chunks")
print("-" * 60)

# Define custom processing function for each chunk
def process_stream_chunk(chunk_result):
    """Process each chunk from the stream with custom logic."""
    if 'dataframe' not in chunk_result:
        return
        
    df = chunk_result['dataframe'].to_pandas()
    
    # Example: Count entities per row
    if 'entities' in chunk_result:
        entities_df = chunk_result['entities']
        entity_counts = entities_df.groupby('row_index').size().to_dict()
        
        # Add entity count column to dataframe
        for idx in df.index:
            df.at[idx, 'entity_count'] = entity_counts.get(idx, 0)
    
    # Print summary
    print(f"Processed chunk with {len(df)} rows")
    if 'entities' in chunk_result:
        entity_types = chunk_result['entities'].groupby('entity_type').size().to_dict()
        print(f"Detected entities: {entity_types}")
    
    return df

print("\nProcessing file in streaming mode with custom handling...")
start_time = time.time()

# Stream process the file with custom handling
processed_chunks = []
for i, chunk_result in enumerate(stream_processor.stream_from_file(
    file_path=sample_file,
    text_columns=["note"],
    active_entity_types=active_entity_types,
    operators=operators,
    chunk_size=2000,
    progress_bar=True
)):
    # Custom processing for each chunk
    processed_df = process_stream_chunk(chunk_result)
    if processed_df is not None:
        processed_chunks.append(processed_df)

end_time = time.time()
duration = end_time - start_time

# Combine processed chunks if needed
if processed_chunks:
    final_df = pd.concat(processed_chunks, ignore_index=True)
    print(f"\nFinal combined dataframe has {len(final_df)} rows")
    
    # Write combined result
    final_df.to_csv("output/custom_processed.csv", index=False)
    print("Saved custom processed data to output/custom_processed.csv")

print(f"\nCustom processing completed in {duration:.2f} seconds")

# Example 3: Process specific columns from a very large file
print("\nExample 3: Process specific columns from a very large file")
print("-" * 60)

print("\nProcessing only specific columns...")
start_time = time.time()

# Only process the 'note' column to demonstrate focused processing
result = stream_processor.process_large_file(
    file_path=sample_file,
    text_columns=["note"],  # Only process notes column
    output_path="output/processed_notes_only.csv",
    active_entity_types=["PERSON", "PHONE_NUMBER"],  # Limit entity types
    operators={
        "PERSON": "replace",
        "PHONE_NUMBER": "mask"
    },
    chunk_size=2000,
    save_entities=True,
    entities_output_path="output/notes_entities.csv",
    progress_bar=True
)

end_time = time.time()
duration = end_time - start_time

print(f"\nFocused processing completed in {duration:.2f} seconds")
print(f"Total rows processed: {result['total_rows_processed']}")
print(f"Total entities detected: {result['total_entities_detected']}")

print("\nDone! Check the output directory for results.")