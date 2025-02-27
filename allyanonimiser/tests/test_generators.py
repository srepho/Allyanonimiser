"""
Tests for the generator modules.
"""

import pytest
import os
import json
from allyanonimiser.generators.au_synthetic_data import AustralianSyntheticDataGenerator

def test_au_synthetic_data_generator_creation(au_synthetic_data_generator):
    """Test that the synthetic data generator can be created."""
    assert au_synthetic_data_generator is not None
    assert isinstance(au_synthetic_data_generator, AustralianSyntheticDataGenerator)

def test_generate_australian_name(au_synthetic_data_generator):
    """Test generating Australian names."""
    name = au_synthetic_data_generator.generate_australian_name()
    assert name is not None
    assert isinstance(name, str)
    assert len(name.split()) == 2  # First and last name
    
def test_generate_australian_address(au_synthetic_data_generator):
    """Test generating Australian addresses."""
    address = au_synthetic_data_generator.generate_australian_address()
    assert address is not None
    assert isinstance(address, str)
    assert any(state in address for state in au_synthetic_data_generator.states)
    
def test_generate_australian_phone(au_synthetic_data_generator):
    """Test generating Australian phone numbers."""
    phone = au_synthetic_data_generator.generate_australian_phone()
    assert phone is not None
    assert isinstance(phone, str)
    # Should start with a valid Australian prefix
    assert any(phone.startswith(prefix) for prefix in ["02", "03", "04", "07", "08"])
    
def test_generate_tfn(au_synthetic_data_generator):
    """Test generating Australian TFNs."""
    tfn = au_synthetic_data_generator.generate_tfn()
    assert tfn is not None
    assert isinstance(tfn, str)
    assert len(tfn.replace(" ", "")) == 9  # 9 digits without spaces
    
def test_generate_medicare_number(au_synthetic_data_generator):
    """Test generating Australian Medicare numbers."""
    medicare = au_synthetic_data_generator.generate_medicare_number()
    assert medicare is not None
    assert isinstance(medicare, str)
    assert len(medicare.replace(" ", "").replace("-", "")) == 10  # 10 digits without spaces/dashes
    
def test_generate_drivers_license(au_synthetic_data_generator):
    """Test generating Australian driver's licenses."""
    license_no = au_synthetic_data_generator.generate_drivers_license(state="NSW")
    assert license_no is not None
    assert isinstance(license_no, str)
    assert license_no.startswith("NSW")
    
def test_generate_policy_number(au_synthetic_data_generator):
    """Test generating insurance policy numbers."""
    policy = au_synthetic_data_generator.generate_policy_number()
    assert policy is not None
    assert isinstance(policy, str)
    assert any(policy.startswith(prefix) for prefix in ["POL", "P-", "P", "INS"])
    
def test_generate_claim_number(au_synthetic_data_generator):
    """Test generating insurance claim numbers."""
    claim = au_synthetic_data_generator.generate_claim_number()
    assert claim is not None
    assert isinstance(claim, str)
    assert any(claim.startswith(prefix) for prefix in ["CL", "C", "CLM"])
    
def test_generate_person(au_synthetic_data_generator):
    """Test generating complete person profiles."""
    person = au_synthetic_data_generator.generate_person()
    assert person is not None
    assert isinstance(person, dict)
    
    # Check that all expected fields are present
    expected_fields = ["name", "address", "phone", "tfn", "medicare", "drivers_license", "bsb_account", "email"]
    for field in expected_fields:
        assert field in person
        assert person[field] is not None
        
def test_generate_insurance_claim(au_synthetic_data_generator):
    """Test generating synthetic insurance claims."""
    claim = au_synthetic_data_generator.generate_insurance_claim()
    assert claim is not None
    assert isinstance(claim, dict)
    
    # Check that all expected fields are present
    expected_fields = ["customer", "policy_number", "claim_number", "claim_date", "claim_type", "claim_status", "insurer"]
    for field in expected_fields:
        assert field in claim
        assert claim[field] is not None
    
    # Check customer details
    assert "customer" in claim
    assert isinstance(claim["customer"], dict)
    assert "name" in claim["customer"]
    
    # Check if it's a motor vehicle claim
    if claim["claim_type"] == "Motor Vehicle":
        assert "vehicle" in claim
        assert isinstance(claim["vehicle"], dict)
        assert "make" in claim["vehicle"]
        assert "model" in claim["vehicle"]
        assert "registration" in claim["vehicle"]
        
def test_generate_dataset(au_synthetic_data_generator, temp_dataset_dir):
    """Test generating a complete dataset."""
    # Generate a small dataset for testing
    au_synthetic_data_generator.generate_dataset(
        num_documents=5,
        output_dir=temp_dataset_dir,
        include_annotations=True
    )
    
    # Check that the output directory contains files
    assert os.path.exists(temp_dataset_dir)
    
    # Should have dataset index file
    assert os.path.exists(os.path.join(temp_dataset_dir, "dataset_index.json"))
    
    # Should have document files
    document_count = len([f for f in os.listdir(temp_dataset_dir) if f.startswith("document_")])
    assert document_count == 5
    
    # Check the content of a document file
    document_file = os.path.join(temp_dataset_dir, "document_0001.json")
    assert os.path.exists(document_file)
    
    with open(document_file, "r") as f:
        document = json.load(f)
        
    # Check document structure
    assert "id" in document
    assert "type" in document
    assert "text" in document
    assert "metadata" in document
    assert "annotations" in document
    
    # Check annotations
    assert isinstance(document["annotations"], list)
    if len(document["annotations"]) > 0:
        annotation = document["annotations"][0]
        assert "entity_type" in annotation
        assert "start" in annotation
        assert "end" in annotation
        assert "text" in annotation

@pytest.mark.skip(reason="Requires API key and network access")
def test_llm_augmenter():
    """Test the LLM augmenter for generating challenging examples."""
    from allyanonimiser.generators.llm_augmenter import LLMAugmenter
    import os
    
    # Skip if no API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("No OpenAI API key available")
    
    # Create the augmenter
    augmenter = LLMAugmenter(api_key=api_key, api_provider="openai")
    
    # Generate a small dataset
    output_dir = augmenter.generate_challenging_dataset(
        entity_types=["PERSON", "EMAIL_ADDRESS"],
        num_examples_per_type=2,
        difficulties=["easy"],
        output_dir="test_challenging_dataset"
    )
    
    # Check that files were created
    assert os.path.exists(output_dir)
    assert os.path.exists(os.path.join(output_dir, "all_examples.json"))
    
    # Clean up
    import shutil
    shutil.rmtree(output_dir)

@pytest.mark.skip(reason="Requires datasets and huggingface_hub packages")
def test_dataset_publisher():
    """Test the dataset publisher functionality."""
    from allyanonimiser.generators.dataset_publisher import DatasetPublisher
    import tempfile
    
    # Create a temporary directory with sample data
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample examples file
        examples = [
            {
                "id": "1",
                "text": "My name is John Smith",
                "entity_type": "PERSON",
                "entity_value": "John Smith",
                "start": 11,
                "end": 21,
                "difficulty": "easy"
            },
            {
                "id": "2",
                "text": "Contact me at j.smith@example.com",
                "entity_type": "EMAIL_ADDRESS",
                "entity_value": "j.smith@example.com",
                "start": 14,
                "end": 33,
                "difficulty": "easy"
            }
        ]
        
        examples_file = os.path.join(temp_dir, "all_examples.json")
        with open(examples_file, "w") as f:
            json.dump(examples, f)
        
        # Create a publisher
        publisher = DatasetPublisher(
            dataset_name="Test PII Examples",
            description="Test dataset for PII detection",
            author="Test Author"
        )
        
        # Create a dataset from the examples
        dataset_dict = publisher.create_from_challenging_examples(examples_file)
        
        # Check that the dataset was created
        assert dataset_dict is not None
        assert "train" in dataset_dict
        
        # Export to CSV
        output_dir = os.path.join(temp_dir, "csv_output")
        success = publisher.export_to_csv(dataset_dict, output_dir)
        
        if success:
            assert os.path.exists(output_dir)
            assert os.path.exists(os.path.join(output_dir, "Test PII Examples_train.csv"))