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
    """Test that the content type is automatically detected."""
    # Process different content types
    email_result = allyanonimiser_instance.process(example_texts["email"])
    claim_result = allyanonimiser_instance.process(example_texts["claim_note"])
    medical_result = allyanonimiser_instance.process(example_texts["medical_report"])
    
    # Check that the content types were detected correctly
    assert email_result.get("content_type") == "email"
    assert claim_result.get("content_type") == "claim_note"
    assert medical_result.get("content_type") in ["medical_report", "generic"]

def test_process_with_explicit_content_type(allyanonimiser_instance, example_texts):
    """Test processing with explicit content type."""
    # Process with explicit content type
    result = allyanonimiser_instance.process(
        text=example_texts["simple"],
        content_type="claim_note"
    )
    
    # Should use the specified content type
    assert result.get("content_type") == "claim_note"
    
    # Should still detect entities
    assert "entities" in result
    assert len(result["entities"]) > 0

def test_process_with_anonymization(allyanonimiser_instance, example_texts):
    """Test processing with anonymization."""
    # Process with anonymization
    result = allyanonimiser_instance.process(
        text=example_texts["simple"],
        anonymize=True
    )
    
    # Should have anonymized text
    assert "anonymized_text" in result
    assert result["anonymized_text"] != example_texts["simple"]
    
    # Should have anonymization stats
    assert "anonymization_stats" in result

def test_process_without_anonymization(allyanonimiser_instance, example_texts):
    """Test processing without anonymization."""
    # Process without anonymization
    result = allyanonimiser_instance.process(
        text=example_texts["simple"],
        anonymize=False
    )
    
    # Should not have anonymized text
    assert "anonymized_text" not in result
    assert "anonymization_stats" not in result
    
    # Should still have entities
    assert "entities" in result
    assert len(result["entities"]) > 0

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
        assert "entities" in result
        assert len(result["entities"]) > 0

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
    
    # Should have a result for each file
    assert len(results) == len(file_paths)
    
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
    
    # Process with custom operators
    result = allyanonimiser_instance.process(
        text=example_texts["claim_note"],
        anonymize=True,
        operators=operators
    )
    
    # Check that custom operators were applied
    for entity in result.get("entities", []):
        entity_type = entity.get("entity_type")
        if entity_type in operators:
            # Find the corresponding anonymized item
            for item in result.get("anonymization_stats", {}).get("items", []):
                if item.get("entity_type") == entity_type:
                    assert item.get("operator") == operators[entity_type]