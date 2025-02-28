"""
Performance tests for DataFrame processing in Allyanonimiser.
"""
import pytest
import time
import pandas as pd
import numpy as np
from allyanonimiser import create_allyanonimiser

# Skip these tests in CI or when running regular test suite
pytestmark = pytest.mark.skip(reason="Performance tests are slow and only run manually")

@pytest.fixture
def large_df():
    """Create a large DataFrame for performance testing."""
    # Create a list of 1000 sample texts
    texts = [
        "Customer John Smith called about policy POL123456.",
        "Claim CL789012 was filed for a vehicle accident.",
        "Email received from customer@example.com regarding their insurance.",
        "The client Jane Doe (DOB: 15/04/1985) requested a policy update.",
        "Phone call from +61 4 1234 5678 about claim CL456789.",
        "Medicare card 2123 45678 1 received for claim processing.",
        "Australian TFN: 123 456 789. ABN: 51 824 753 556.",
        "Customer visited our office at 42 Example St, Sydney NSW 2000.",
        "Case referred to Team Leader Sarah Johnson for review.",
        "Vehicle registration ABC123 involved in incident on 10/03/2023."
    ] * 100  # Repeat to get 1000 rows
    
    # Create a large DataFrame with these texts
    return pd.DataFrame({
        'id': range(len(texts)),
        'text': texts
    })

@pytest.fixture
def ally():
    """Create an Allyanonimiser instance for testing."""
    return create_allyanonimiser()

def measure_time(func, *args, **kwargs):
    """Measure execution time of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

def test_batch_size_performance(large_df, ally):
    """Test performance with different batch sizes."""
    print("\nBatch Size Performance Test")
    print("==========================")
    
    batch_sizes = [10, 50, 100, 200, 500, 1000]
    times = []
    
    for batch_size in batch_sizes:
        processor = ally.create_dataframe_processor(batch_size=batch_size)
        
        _, duration = measure_time(
            processor.detect_pii,
            large_df,
            'text',
            min_score_threshold=0.8
        )
        
        times.append(duration)
        print(f"Batch size {batch_size}: {duration:.2f} seconds")
    
    # Find the optimal batch size
    optimal_index = np.argmin(times)
    print(f"\nOptimal batch size: {batch_sizes[optimal_index]} ({times[optimal_index]:.2f} seconds)")

def test_worker_performance(large_df, ally):
    """Test performance with different numbers of workers."""
    print("\nWorker Count Performance Test")
    print("===========================")
    
    worker_counts = [None, 1, 2, 4, 8]  # None means sequential processing
    times = []
    
    for workers in worker_counts:
        processor = ally.create_dataframe_processor(n_workers=workers, batch_size=100)
        
        worker_desc = "Sequential" if workers is None else f"{workers} workers"
        
        _, duration = measure_time(
            processor.detect_pii,
            large_df,
            'text',
            min_score_threshold=0.8
        )
        
        times.append(duration)
        print(f"{worker_desc}: {duration:.2f} seconds")
    
    # Find the optimal worker count
    optimal_index = np.argmin(times)
    workers = worker_counts[optimal_index]
    worker_desc = "Sequential" if workers is None else f"{workers} workers"
    print(f"\nOptimal configuration: {worker_desc} ({times[optimal_index]:.2f} seconds)")

def test_acronym_expansion_overhead(large_df, ally):
    """Test performance overhead of acronym expansion."""
    print("\nAcronym Expansion Overhead Test")
    print("=============================")
    
    # Set up acronyms
    acronyms = {
        "TP": "Third Party",
        "TL": "Team Leader",
        "POL": "Policy",
        "CL": "Claim",
        "DOB": "Date of Birth",
        "MVA": "Motor Vehicle Accident",
        "PII": "Personally Identifiable Information"
    }
    ally.set_acronym_dictionary(acronyms)
    
    # Test without acronym expansion
    processor = ally.create_dataframe_processor(batch_size=100)
    _, no_expansion_time = measure_time(
        processor.process_dataframe,
        large_df,
        'text',
        expand_acronyms=False
    )
    
    # Test with acronym expansion
    _, with_expansion_time = measure_time(
        processor.process_dataframe,
        large_df,
        'text',
        expand_acronyms=True
    )
    
    overhead = with_expansion_time - no_expansion_time
    percentage = (overhead / no_expansion_time) * 100
    
    print(f"Without expansion: {no_expansion_time:.2f} seconds")
    print(f"With expansion: {with_expansion_time:.2f} seconds")
    print(f"Overhead: {overhead:.2f} seconds ({percentage:.1f}%)")

def test_detect_vs_process_vs_anonymize(large_df, ally):
    """Compare performance of different operations."""
    print("\nOperation Performance Comparison")
    print("==============================")
    
    processor = ally.create_dataframe_processor(batch_size=100)
    
    # Test detect_pii
    _, detect_time = measure_time(
        processor.detect_pii,
        large_df,
        'text',
        min_score_threshold=0.8
    )
    
    # Test anonymize_column
    _, anonymize_time = measure_time(
        processor.anonymize_column,
        large_df,
        'text'
    )
    
    # Test process_dataframe
    _, process_time = measure_time(
        processor.process_dataframe,
        large_df,
        'text'
    )
    
    print(f"detect_pii: {detect_time:.2f} seconds")
    print(f"anonymize_column: {anonymize_time:.2f} seconds")
    print(f"process_dataframe: {process_time:.2f} seconds")

def test_row_count_scaling(ally):
    """Test how performance scales with the number of rows."""
    print("\nRow Count Scaling Test")
    print("====================")
    
    row_counts = [100, 500, 1000, 5000, 10000]
    times = []
    
    base_text = "Customer John Smith called about policy POL123456 on 15/04/2023."
    
    for count in row_counts:
        # Create DataFrame with specified number of rows
        df = pd.DataFrame({
            'id': range(count),
            'text': [base_text] * count
        })
        
        processor = ally.create_dataframe_processor(batch_size=100)
        
        _, duration = measure_time(
            processor.detect_pii,
            df,
            'text'
        )
        
        times.append(duration)
        print(f"{count} rows: {duration:.2f} seconds")
    
    # Calculate rows per second for each test
    for i, count in enumerate(row_counts):
        rows_per_second = count / times[i]
        print(f"{count} rows: {rows_per_second:.1f} rows/second")

if __name__ == "__main__":
    # Create fixtures manually for standalone execution
    df = large_df()
    analyzer = ally()
    
    # Run all performance tests
    test_batch_size_performance(df, analyzer)
    test_worker_performance(df, analyzer)
    test_acronym_expansion_overhead(df, analyzer)
    test_detect_vs_process_vs_anonymize(df, analyzer)
    test_row_count_scaling(analyzer)