"""
Tests for CSV processor functionality.
"""

import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from allyanonimiser import create_allyanonimiser
from allyanonimiser.csv_processor import CSVProcessor


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data with PII."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": [
            "John Smith",
            "Jane Doe",
            "Alex Johnson",
            "Sarah Williams",
            "Michael Brown"
        ],
        "email": [
            "john.smith@example.com",
            "jane.doe@test.org",
            "alex.j@company.net",
            "sarah@email.com",
            "m.brown@domain.co"
        ],
        "phone": [
            "0412 345 678",
            "02 9876 5432",
            "(03) 1234-5678",
            "0400-123-456",
            "+61 2 8765 4321"
        ],
        "notes": [
            "Customer John Smith called about policy POL-123456",
            "Jane Doe requested refund for claim CLM-789012",
            "Alex Johnson from Sydney NSW 2000 inquired about coverage",
            "Sarah Williams (DOB: 15/06/1985) updated her address",
            "Michael Brown's Medicare number is 2953 12345 1"
        ],
        "non_pii_column": [
            "Product A",
            "Service B",
            "Package C",
            "Option D",
            "Plan E"
        ]
    })


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_csv_data.to_csv(f.name, index=False)
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def ally():
    """Create an Allyanonimiser instance."""
    return create_allyanonimiser()


def test_process_csv_file(ally, temp_csv_file):
    """Test basic CSV file processing."""
    output_file = temp_csv_file.replace('.csv', '_processed.csv')
    
    try:
        # Process the CSV file
        result = ally.process_csv_file(
            input_file=temp_csv_file,
            output_file=output_file,
            columns_to_anonymize=["name", "email", "phone", "notes"],
            operators={
                "PERSON": "replace",
                "EMAIL_ADDRESS": "mask",
                "PHONE_NUMBER": "mask"
            },
            generate_report=False
        )
        
        # Check results
        assert result["rows_processed"] == 5
        assert "name" in result["columns_processed"]
        assert "email" in result["columns_processed"]
        assert result["entities_found"].get("PERSON", 0) > 0
        assert result["entities_found"].get("EMAIL_ADDRESS", 0) > 0
        
        # Check output file exists
        assert os.path.exists(output_file)
        
        # Check anonymized content
        df_anonymized = pd.read_csv(output_file)
        assert len(df_anonymized) == 5
        
        # Check that PII was anonymized
        assert "<PERSON>" in df_anonymized["name"].iloc[0]
        assert "*" in df_anonymized["email"].iloc[0] or "@" in df_anonymized["email"].iloc[0]
        
    finally:
        # Cleanup
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_detect_pii_columns(ally, temp_csv_file):
    """Test PII column auto-detection."""
    # Detect PII columns
    pii_columns = ally.detect_pii_columns(
        temp_csv_file,
        sample_size=5,
        min_detection_rate=0.2
    )
    
    # Should detect columns with PII
    assert "name" in pii_columns
    assert "email" in pii_columns
    assert "notes" in pii_columns
    
    # Should not detect non-PII column
    assert "non_pii_column" not in pii_columns
    assert "id" not in pii_columns


def test_detect_pii_columns_with_dataframe(ally, sample_csv_data):
    """Test PII column detection with DataFrame input."""
    # Detect PII columns from DataFrame
    pii_columns = ally.detect_pii_columns(
        sample_csv_data,
        sample_size=5,
        min_detection_rate=0.2
    )
    
    # Should detect columns with PII
    assert "name" in pii_columns
    assert "email" in pii_columns
    assert "notes" in pii_columns


def test_preview_csv_changes(ally, temp_csv_file):
    """Test preview functionality."""
    # Preview changes
    preview = ally.preview_csv_changes(
        temp_csv_file,
        columns=["name", "email"],
        sample_rows=3
    )
    
    # Check preview structure
    assert not preview.empty
    assert "row" in preview.columns
    assert "column" in preview.columns
    assert "original" in preview.columns
    assert "anonymized" in preview.columns
    assert "entities_found" in preview.columns
    
    # Check that changes were detected
    assert len(preview) > 0
    

def test_process_csv_with_auto_detection(ally, temp_csv_file):
    """Test CSV processing with auto column detection."""
    output_file = temp_csv_file.replace('.csv', '_auto.csv')
    
    try:
        # Process with auto-detection (columns_to_anonymize=None)
        result = ally.process_csv_file(
            input_file=temp_csv_file,
            output_file=output_file,
            columns_to_anonymize=None,  # Auto-detect
            generate_report=False
        )
        
        # Check that columns were auto-detected
        assert "auto_detected_columns" in result
        assert len(result["auto_detected_columns"]) > 0
        assert result["rows_processed"] == 5
        
        # Check output file
        assert os.path.exists(output_file)
        
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_stream_process_csv(ally, temp_csv_file):
    """Test streaming CSV processing for large files."""
    output_file = temp_csv_file.replace('.csv', '_streamed.csv')
    
    try:
        # Process with streaming
        result = ally.stream_process_csv(
            input_file=temp_csv_file,
            output_file=output_file,
            columns=["name", "email", "notes"],
            chunk_size=2  # Small chunk size for testing
        )
        
        # Check results
        assert result["chunks_processed"] > 0
        assert result["rows_processed"] == 5
        
        # Check output file
        assert os.path.exists(output_file)
        df_streamed = pd.read_csv(output_file)
        assert len(df_streamed) == 5
        
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_process_csv_directory(ally):
    """Test processing multiple CSV files in a directory."""
    # Create temporary directory with CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample CSV files
        for i in range(3):
            df = pd.DataFrame({
                "name": [f"Person {i}-{j}" for j in range(3)],
                "email": [f"user{i}-{j}@example.com" for j in range(3)],
                "data": ["Some data" for _ in range(3)]
            })
            df.to_csv(os.path.join(temp_dir, f"file_{i}.csv"), index=False)
        
        # Process directory
        output_dir = os.path.join(temp_dir, "anonymized")
        result = ally.process_csv_directory(
            input_dir=temp_dir,
            output_dir=output_dir,
            columns_to_anonymize=["name", "email"]
        )
        
        # Check results
        assert len(result["files_processed"]) == 3
        # At minimum we should have email addresses detected
        assert result["total_entities_found"].get("EMAIL_ADDRESS", 0) > 0
        # May or may not detect "Person X-Y" as PERSON depending on spaCy model
        
        # Check output files exist
        assert os.path.exists(output_dir)
        output_files = list(Path(output_dir).glob("*.csv"))
        assert len(output_files) == 3


def test_csv_processor_with_report(ally, temp_csv_file):
    """Test CSV processing with report generation."""
    output_file = temp_csv_file.replace('.csv', '_with_report.csv')
    
    try:
        # Process with report generation
        result = ally.process_csv_file(
            input_file=temp_csv_file,
            output_file=output_file,
            columns_to_anonymize=["name", "email"],
            generate_report=True
        )
        
        # Check that report was generated
        assert "report_file" in result
        report_file = result["report_file"]
        assert os.path.exists(report_file)
        
        # Check report content
        with open(report_file, 'r') as f:
            report_content = f.read()
            assert "CSV Processing Report" in report_content
            assert "Entities Found" in report_content
        
        # Cleanup report
        os.unlink(report_file)
        
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_csv_error_handling(ally):
    """Test error handling for invalid inputs."""
    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        ally.process_csv_file("non_existent_file.csv")
    
    # Test with invalid columns
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        df.to_csv(f.name, index=False)
        temp_file = f.name
    
    try:
        with pytest.raises(ValueError):
            ally.process_csv_file(
                input_file=temp_file,
                columns_to_anonymize=["non_existent_column"]
            )
    finally:
        os.unlink(temp_file)