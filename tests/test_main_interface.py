"""
Tests for the main Allyanonimiser interface.
"""

import pytest
import os
from allyanonimiser import Allyanonimiser

def test_allyanonimiser_creation():
    """Test that the main interface can be created."""
    allyanon = Allyanonimiser()
    assert allyanon is not None
    assert hasattr(allyanon, 'process')
    assert hasattr(allyanon, 'batch_process')
    assert hasattr(allyanon, 'process_files')

def test_auto_content_detection(allyanonimiser_instance, example_texts):
    """Test that the text is properly processed with different content."""
    # Process different content types
    email_result = allyanonimiser_instance.process(example_texts["email"])
    claim_result = allyanonimiser_instance.process(example_texts["claim_note"])
    medical_result = allyanonimiser_instance.process(example_texts["medical_report"])
    
    # Check that we have entities in the results
    assert "analysis" in email_result
    assert "entities" in email_result["analysis"]
    assert len(email_result["analysis"]["entities"]) > 0
    
    assert "analysis" in claim_result
    assert "entities" in claim_result["analysis"]
    assert len(claim_result["analysis"]["entities"]) > 0
    
    assert "analysis" in medical_result
    assert "entities" in medical_result["analysis"]
    assert len(medical_result["analysis"]["entities"]) > 0

def test_process_with_active_entity_types(allyanonimiser_instance, example_texts):
    """Test processing with explicit entity types."""
    # Process with specific entity types
    result = allyanonimiser_instance.process(
        text=example_texts["simple"],
        active_entity_types=["PERSON", "EMAIL_ADDRESS"]
    )
    
    # Should only detect PERSON and EMAIL_ADDRESS entities
    assert "analysis" in result
    assert "entities" in result["analysis"]
    
    # Check that we only have the specified entity types
    for entity in result["analysis"]["entities"]:
        assert entity["entity_type"] in ["PERSON", "EMAIL_ADDRESS"]
        
    # Ensure we found at least one entity
    assert len(result["analysis"]["entities"]) > 0

def test_process_with_anonymization(allyanonimiser_instance, example_texts):
    """Test processing with anonymization."""
    # Process with anonymization
    result = allyanonimiser_instance.process(
        text=example_texts["simple"]
    )
    
    # Should have anonymized text
    assert "anonymized" in result
    assert result["anonymized"] != example_texts["simple"]
    
    # Should have detected entities
    assert "analysis" in result
    assert "entities" in result["analysis"]
    assert len(result["analysis"]["entities"]) > 0

def test_with_expanded_acronyms(allyanonimiser_instance, example_texts):
    """Test processing with acronym expansion."""
    # Add acronyms to the instance
    acronyms = {
        "DOB": "Date of Birth",
        "ID": "Identification",
        "SSN": "Social Security Number"
    }
    allyanonimiser_instance.set_acronym_dictionary(acronyms)
    
    # Create text with acronyms
    text_with_acronyms = "Patient DOB: 01/01/1980. SSN: 123-45-6789"
    
    # Process with acronym expansion
    result = allyanonimiser_instance.process(
        text=text_with_acronyms,
        expand_acronyms=True
    )
    
    # Should have expanded acronyms in preprocessing
    assert "preprocessing" in result
    assert "expanded_acronyms" in result["preprocessing"]
    
    # Verify at least one acronym was expanded
    assert len(result["preprocessing"]["expanded_acronyms"]) > 0

def test_batch_process(allyanonimiser_instance, example_texts):
    """Test batch processing of multiple texts."""
    # Create a list of texts to process
    texts = [
        example_texts["simple"],
        example_texts["email"],
        example_texts["claim_note"]
    ]
    
    # Batch process
    results = allyanonimiser_instance.batch_process(texts)
    
    # Should have a result for each text
    assert len(results) == len(texts)
    
    # Each result should have entities
    for result in results:
        assert "analysis" in result
        assert "entities" in result["analysis"]
        assert len(result["analysis"]["entities"]) > 0

def test_batch_process_with_content_types(allyanonimiser_instance, example_texts):
    """Test batch processing with explicit content types."""
    # Create a list of texts to process
    texts = [
        example_texts["simple"],
        example_texts["email"],
        example_texts["claim_note"]
    ]
    
    # Define content types
    content_types = [
        "generic",
        "email",
        "claim_note"
    ]
    
    # Batch process with content types
    results = allyanonimiser_instance.batch_process(
        texts=texts,
        content_types=content_types
    )
    
    # Should have used the specified content types
    for i, result in enumerate(results):
        assert result.get("content_type") == content_types[i]
        
    # Should have entities in each result
    for result in results:
        assert "analysis" in result
        assert "entities" in result["analysis"]

def test_process_files(allyanonimiser_instance, example_texts, tmp_path):
    """Test processing files."""
    # Create some test files
    file_paths = []
    for name, content in example_texts.items():
        file_path = tmp_path / f"{name}.txt"
        with open(file_path, "w") as f:
            f.write(content)
        file_paths.append(str(file_path))
    
    # Create output directory
    output_dir = tmp_path / "output"
    
    # Process files
    results = allyanonimiser_instance.process_files(
        file_paths=file_paths,
        output_dir=str(output_dir),
        anonymize=True,
        save_results=True
    )
    
    # Check results structure - should have a 'results' key with a list of results
    assert 'results' in results
    assert len(results['results']) == len(file_paths)
    
    # Output directory should contain files
    assert os.path.exists(output_dir)
    
    # Should have anonymized text files and analysis JSON files
    for name in example_texts.keys():
        anon_file = output_dir / f"{name}_anonymized.txt"
        analysis_file = output_dir / f"{name}_analysis.json"
        
        assert os.path.exists(anon_file) or os.path.exists(str(anon_file))
        assert os.path.exists(analysis_file) or os.path.exists(str(analysis_file))

def test_custom_operators(allyanonimiser_instance, example_texts):
    """Test processing with custom operators."""
    # Define custom operators
    operators = {
        "PERSON": "hash",
        "EMAIL_ADDRESS": "redact",
        "AU_PHONE": "mask_preserve_last_4"
    }
    
    # Process with custom operators - create anonymization config
    from allyanonimiser import AnonymizationConfig
    anon_config = AnonymizationConfig(operators=operators)
    
    # Process with custom operators through config
    result = allyanonimiser_instance.process(
        text=example_texts["claim_note"],
        anonymization_config=anon_config
    )
    
    # Check that custom operators were applied
    for entity in result.get("entities", []):
        entity_type = entity.get("entity_type")
        if entity_type in operators:
            # Find the corresponding anonymized item
            for item in result.get("anonymization_stats", {}).get("items", []):
                if item.get("entity_type") == entity_type:
                    assert item.get("operator") == operators[entity_type]