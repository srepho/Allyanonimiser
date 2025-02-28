"""
Tests for the DataFrame processor functionality.
"""
import pytest
import pandas as pd
from allyanonimiser import create_allyanonimiser
from allyanonimiser.dataframe_processor import DataFrameProcessor

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': range(1, 6),
        'name': [
            'John Smith',
            'Jane Doe',
            'Bob Johnson',
            'Alice Williams',
            'Michael Brown'
        ],
        'email': [
            'john.smith@example.com',
            'jane.doe@example.com',
            'bjohnson@example.com',
            'alice.w@example.com',
            'michael.brown@example.com'
        ],
        'note': [
            'Customer called about policy POL123456 on 05/04/2023',
            'Sent email regarding claim CL789012. Phone: +61 4 1234 5678',
            'Medicare card 2123 45678 1 received for claim CL456789',
            'Australian TFN: 123 456 789. ABN: 51 824 753 556',
            'Discussed policy with Michael Brown at 42 Example St, Sydney'
        ]
    })

@pytest.fixture
def allyanonimiser():
    """Create an Allyanonimiser instance for testing."""
    return create_allyanonimiser()

@pytest.fixture
def dataframe_processor(allyanonimiser):
    """Create a DataFrameProcessor instance for testing."""
    return DataFrameProcessor(allyanonimiser)

def test_detect_pii(dataframe_processor, sample_df):
    """Test detecting PII in a DataFrame column."""
    entities_df = dataframe_processor.detect_pii(
        sample_df,
        'note',
        min_score_threshold=0.7
    )
    
    # Check that we got some results
    assert not entities_df.empty
    
    # Check that we have the expected columns
    expected_columns = ['row_index', 'entity_type', 'start', 'end', 'text', 'score']
    assert all(col in entities_df.columns for col in expected_columns)
    
    # Check that we found at least some expected entity types
    found_types = set(entities_df['entity_type'].unique())
    expected_types = {'PERSON', 'INSURANCE_POLICY_NUMBER', 'INSURANCE_CLAIM_NUMBER', 
                     'AU_MEDICARE', 'PHONE_NUMBER', 'DATE'}
    
    # We should find at least some of these types
    assert len(found_types.intersection(expected_types)) > 0

def test_anonymize_column(dataframe_processor, sample_df):
    """Test anonymizing a DataFrame column."""
    anonymized_df = dataframe_processor.anonymize_column(
        sample_df,
        'note',
        operators={
            'PERSON': 'replace',
            'EMAIL_ADDRESS': 'mask',
            'PHONE_NUMBER': 'mask',
            'INSURANCE_POLICY_NUMBER': 'redact',
            'INSURANCE_CLAIM_NUMBER': 'redact',
            'AU_MEDICARE': 'redact',
            'DATE': 'replace'
        }
    )
    
    # Check that we have the expected output column
    assert 'note_anonymized' in anonymized_df.columns
    
    # Check that the original column is unchanged
    pd.testing.assert_series_equal(anonymized_df['note'], sample_df['note'])
    
    # Check that anonymization happened (values should be different)
    assert not anonymized_df['note'].equals(anonymized_df['note_anonymized'])
    
    # Check that sensitive entities were anonymized
    anonymized_texts = anonymized_df['note_anonymized'].tolist()
    
    # Policy numbers should be redacted
    assert not any('POL123456' in text for text in anonymized_texts)
    
    # Claim numbers should be redacted
    assert not any('CL789012' in text for text in anonymized_texts)
    
    # Medicare numbers should be redacted
    assert not any('2123 45678 1' in text for text in anonymized_texts)

def test_process_dataframe(dataframe_processor, sample_df):
    """Test processing multiple columns in a DataFrame."""
    result = dataframe_processor.process_dataframe(
        sample_df,
        text_columns=['name', 'email', 'note'],
        active_entity_types=[
            'PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER',
            'INSURANCE_POLICY_NUMBER', 'INSURANCE_CLAIM_NUMBER',
            'AU_MEDICARE', 'AU_TFN', 'AU_ABN', 'ADDRESS', 'DATE'
        ],
        operators={
            'PERSON': 'replace',
            'EMAIL_ADDRESS': 'mask',
            'PHONE_NUMBER': 'mask',
            'INSURANCE_POLICY_NUMBER': 'redact',
            'INSURANCE_CLAIM_NUMBER': 'redact'
        },
        batch_size=2
    )
    
    # Check that we got the expected result keys
    assert 'dataframe' in result
    assert 'entities' in result
    
    # Check that the processed DataFrame has anonymized columns
    processed_df = result['dataframe']
    assert 'name_anonymized' in processed_df.columns
    assert 'email_anonymized' in processed_df.columns
    assert 'note_anonymized' in processed_df.columns
    
    # Check that the entities DataFrame has the expected columns
    entities_df = result['entities']
    assert not entities_df.empty
    expected_columns = ['row_index', 'column', 'entity_type', 'start', 'end', 'text', 'score']
    assert all(col in entities_df.columns for col in expected_columns)
    
    # Check that we have entities from different columns
    found_columns = entities_df['column'].unique()
    assert len(found_columns) > 1
    assert 'note' in found_columns

def test_analyze_dataframe_statistics(dataframe_processor, sample_df):
    """Test analyzing entity statistics."""
    # First get some entities
    entities_df = dataframe_processor.detect_pii(sample_df, 'note')
    
    # Then analyze statistics
    stats = dataframe_processor.analyze_dataframe_statistics(
        entities_df,
        sample_df,
        'note'
    )
    
    # Check that we got statistics
    assert not stats.empty
    
    # Check that we have the expected columns
    expected_columns = ['entity_type', 'count', 'avg_score', 'min_score', 'max_score', 
                       'unique_rows', 'percentage']
    assert all(col in stats.columns for col in expected_columns)
    
    # Check that percentages make sense
    assert all(0 <= p <= 100 for p in stats['percentage'])

def test_empty_dataframe(dataframe_processor):
    """Test handling empty DataFrames gracefully."""
    empty_df = pd.DataFrame({'text': []})
    
    # Should return empty results without error
    entities_df = dataframe_processor.detect_pii(empty_df, 'text')
    assert entities_df.empty
    
    # Should return expected columns
    expected_columns = ['row_index', 'entity_type', 'start', 'end', 'text', 'score']
    assert all(col in entities_df.columns for col in expected_columns)

def test_main_interface_methods(allyanonimiser, sample_df):
    """Test the convenience methods added to the Allyanonimiser class."""
    # Test detect_pii_in_dataframe
    entities_df = allyanonimiser.detect_pii_in_dataframe(
        sample_df,
        'note',
        min_score_threshold=0.8
    )
    assert not entities_df.empty
    
    # Test anonymize_dataframe
    anonymized_df = allyanonimiser.anonymize_dataframe(
        sample_df,
        'note'
    )
    assert 'note_anonymized' in anonymized_df.columns
    
    # Test process_dataframe
    result = allyanonimiser.process_dataframe(
        sample_df,
        text_columns='email'
    )
    assert 'dataframe' in result
    assert 'entities' in result
    
    # Test creating a processor
    processor = allyanonimiser.create_dataframe_processor()
    assert isinstance(processor, DataFrameProcessor)