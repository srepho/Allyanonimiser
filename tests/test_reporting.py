"""
Tests for the reporting module.

This module tests the functionality of the AnonymizationReport and ReportingManager classes.
"""

import os
import json
import pytest
import pandas as pd
from allyanonimiser import reporting
from allyanonimiser.reporting import AnonymizationReport, ReportingManager, report_manager


@pytest.fixture
def sample_report():
    """Create a sample report with predefined data for testing."""
    report = AnonymizationReport(session_id="test_session")
    
    # Add data for three documents
    report.record_anonymization(
        document_id="doc1",
        original_text="John Smith's email is john@example.com",
        anonymization_result={
            "items": [
                {"entity_type": "PERSON", "original": "John Smith", "operator": "replace"},
                {"entity_type": "EMAIL_ADDRESS", "original": "john@example.com", "operator": "mask"}
            ]
        },
        processing_time=0.1
    )
    
    report.record_anonymization(
        document_id="doc2",
        original_text="Jane Doe's phone is 0412 345 678",
        anonymization_result={
            "items": [
                {"entity_type": "PERSON", "original": "Jane Doe", "operator": "replace"},
                {"entity_type": "PHONE_NUMBER", "original": "0412 345 678", "operator": "redact"}
            ]
        },
        processing_time=0.15
    )
    
    report.record_anonymization(
        document_id="doc3",
        original_text="Robert Johnson lives at 123 Main St, Sydney NSW 2000",
        anonymization_result={
            "items": [
                {"entity_type": "PERSON", "original": "Robert Johnson", "operator": "replace"},
                {"entity_type": "AU_ADDRESS", "original": "123 Main St, Sydney NSW 2000", "operator": "replace"}
            ]
        },
        processing_time=0.12
    )
    
    return report


def test_report_creation():
    """Test that a report can be created."""
    report = AnonymizationReport()
    assert report is not None
    assert hasattr(report, 'record_anonymization')
    assert hasattr(report, 'get_summary')
    assert report.total_documents == 0
    assert report.total_entities == 0


def test_record_anonymization():
    """Test recording an anonymization operation."""
    report = AnonymizationReport(session_id="test_session")
    report.record_anonymization(
        document_id="doc123",
        original_text="John Smith's email is john@example.com",
        anonymization_result={
            "items": [
                {"entity_type": "PERSON", "original": "John Smith"},
                {"entity_type": "EMAIL_ADDRESS", "original": "john@example.com"}
            ]
        },
        processing_time=0.1
    )
    
    # Check that stats are recorded
    assert report.total_documents == 1
    assert report.total_entities == 2
    assert report.entity_counts["PERSON"] == 1
    assert report.entity_counts["EMAIL_ADDRESS"] == 1
    assert len(report.processing_times) == 1
    assert report.processing_times[0] == 0.1


def test_report_summary(sample_report):
    """Test generating a report summary."""
    summary = sample_report.get_summary()
    
    # Check basic metrics
    assert summary["total_documents"] == 3
    assert summary["total_entities"] == 6
    assert summary["entities_per_document"] == 2.0
    
    # Check entity counts
    assert summary["entity_counts"]["PERSON"] == 3
    assert summary["entity_counts"]["EMAIL_ADDRESS"] == 1
    assert summary["entity_counts"]["PHONE_NUMBER"] == 1
    assert summary["entity_counts"]["AU_ADDRESS"] == 1
    
    # Check operator counts
    assert summary["operator_counts"]["replace"] == 4
    assert summary["operator_counts"]["mask"] == 1
    assert summary["operator_counts"]["redact"] == 1
    
    # Check entity distribution
    assert abs(summary["entity_distribution"]["PERSON"] - 50.0) < 0.1  # Should be 50%
    
    # Check processing time
    avg_time = (0.1 + 0.15 + 0.12) / 3
    assert abs(summary["avg_processing_time"] - avg_time) < 0.001


def test_detailed_report(sample_report):
    """Test generating a detailed report."""
    detailed = sample_report.get_detailed_report()
    
    # Check that document stats are included
    assert "document_stats" in detailed
    assert len(detailed["document_stats"]) == 3
    
    # Check that document reports are included
    assert "document_reports" in detailed
    assert len(detailed["document_reports"]) == 3
    
    # Check content of first document report
    doc1 = detailed["document_reports"][0]
    assert doc1["document_id"] == "doc1"
    assert len(doc1["entities"]) == 2
    assert doc1["entities"][0]["entity_type"] == "PERSON"
    assert doc1["entities"][0]["original"] == "John Smith"


def test_report_finalization(sample_report):
    """Test finalizing a report."""
    # Report should not be finalized yet
    assert sample_report.end_time is None
    
    # Finalize the report
    sample_report.finalize()
    
    # Check that end time is set
    assert sample_report.end_time is not None
    
    # Check that elapsed time is calculated in summary
    summary = sample_report.get_summary()
    assert "elapsed_time_seconds" in summary
    assert summary["elapsed_time_seconds"] > 0


def test_export_report(sample_report, tmp_path):
    """Test exporting a report to different formats."""
    # Test JSON export
    json_path = os.path.join(tmp_path, "report.json")
    sample_report.export_report(json_path, format="json")
    assert os.path.exists(json_path)
    
    # Verify JSON content
    with open(json_path, 'r') as f:
        data = json.load(f)
        assert data["total_entities"] == 6
        assert data["entity_counts"]["PERSON"] == 3
    
    # Test CSV export
    csv_path = os.path.join(tmp_path, "report.csv")
    sample_report.export_report(csv_path, format="csv")
    assert os.path.exists(csv_path)
    
    # Verify CSV content
    df = pd.read_csv(csv_path)
    assert "document_id" in df.columns
    assert len(df) == 3  # Three documents
    
    # Test HTML export
    html_path = os.path.join(tmp_path, "report.html")
    sample_report.export_report(html_path, format="html")
    assert os.path.exists(html_path)
    
    # Verify HTML content
    with open(html_path, 'r') as f:
        html_content = f.read()
        assert "Anonymization Report" in html_content
        assert "PERSON" in html_content
        assert "EMAIL_ADDRESS" in html_content


def test_reporting_manager():
    """Test the reporting manager functionality."""
    manager = ReportingManager()
    report = manager.start_new_report("test_session")
    
    # Check that report is stored and retrievable
    assert manager.get_report("test_session") is report
    assert manager.get_current_report() is report
    
    # Test finalizing report
    summary = manager.finalize_current_report()
    assert "session_id" in summary
    assert summary["session_id"] == "test_session"


def test_generate_report_from_results():
    """Test generating a report from a list of results."""
    results = [
        {
            "document_id": "doc1",
            "original_text": "John Smith's email is john@example.com",
            "items": [
                {"entity_type": "PERSON", "original": "John Smith"},
                {"entity_type": "EMAIL_ADDRESS", "original": "john@example.com"}
            ],
            "processing_time": 0.1
        },
        {
            "document_id": "doc2",
            "original_text": "Jane Doe's phone is 0412 345 678",
            "items": [
                {"entity_type": "PERSON", "original": "Jane Doe"},
                {"entity_type": "PHONE_NUMBER", "original": "0412 345 678"}
            ],
            "processing_time": 0.15
        }
    ]
    
    manager = ReportingManager()
    report = manager.generate_report_from_results(results, "batch_test")
    
    # Check that report was generated correctly
    assert report.session_id == "batch_test"
    assert report.total_documents == 2
    assert report.total_entities == 4
    assert report.entity_counts["PERSON"] == 2


def test_integration_with_allyanonimiser():
    """Test integration with Allyanonimiser."""
    from allyanonimiser import create_allyanonimiser
    
    # Create instance
    ally = create_allyanonimiser()
    
    # Start a new report
    ally.start_new_report("integration_test")
    
    # Anonymize some text
    result = ally.anonymize(
        "John Smith's email is john@example.com",
        operators={"PERSON": "replace", "EMAIL_ADDRESS": "mask"}
    )
    
    # Get the report
    report = ally.get_report("integration_test")
    
    # Check that the anonymization was recorded
    assert report.total_documents == 1
    assert report.entity_counts["PERSON"] >= 1
    assert report.entity_counts["EMAIL_ADDRESS"] >= 1
    
    # Test finalizing report
    summary = ally.finalize_report()
    assert "total_documents" in summary
    assert summary["total_documents"] == 1


def test_batch_reporting():
    """Test batch reporting functionality."""
    from allyanonimiser import create_allyanonimiser
    
    # Create instance
    ally = create_allyanonimiser()
    
    # Process multiple texts
    texts = [
        "John Smith's email is john@example.com",
        "Jane Doe's phone is 0412 345 678",
        "Robert Johnson lives at 123 Main St, Sydney NSW 2000"
    ]
    
    # Start a new report
    ally.start_new_report("batch_test")
    
    # Process each text
    for i, text in enumerate(texts):
        ally.anonymize(
            text,
            operators={
                "PERSON": "replace", 
                "EMAIL_ADDRESS": "mask",
                "PHONE_NUMBER": "redact",
                "AU_ADDRESS": "replace"
            },
            document_id=f"doc{i+1}"
        )
    
    # Get the report
    report = ally.get_report("batch_test")
    
    # Check batch report
    assert report.total_documents == 3
    assert report.entity_counts["PERSON"] >= 3
    
    # Test report format
    summary = report.get_summary()
    assert "entity_distribution" in summary
    assert "operator_counts" in summary