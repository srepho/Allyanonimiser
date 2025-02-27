"""
Tools for publishing generated datasets to HuggingFace Hub and other repositories.
"""

import os
import json
import glob
import csv
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import time
import datetime
import uuid

try:
    from datasets import Dataset, DatasetDict
    from huggingface_hub import HfApi, login
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False


class DatasetPublisher:
    """
    Tools for formatting and publishing generated datasets to various repositories.
    """
    
    def __init__(self, dataset_name: str, description: str = "", author: str = ""):
        """
        Initialize a dataset publisher.
        
        Args:
            dataset_name: Name of the dataset
            description: Optional dataset description
            author: Optional author name
        """
        self.dataset_name = dataset_name
        self.description = description
        self.author = author
        self.metadata = {
            "name": dataset_name,
            "description": description,
            "author": author,
            "created_at": datetime.datetime.now().isoformat(),
            "version": "1.0.0",
            "license": "CC BY-SA 4.0",
        }
    
    def create_from_json_files(
        self, 
        directory: str, 
        pattern: str = "*.json", 
        split: str = "train"
    ) -> Union[Dict[str, Any], None]:
        """
        Create a dataset from a directory of JSON files.
        
        Args:
            directory: Directory containing JSON files
            pattern: File pattern to match
            split: Dataset split name
            
        Returns:
            Dataset dictionary if HuggingFace is available, else None
        """
        if not HUGGINGFACE_AVAILABLE:
            print("HuggingFace datasets not available. Install with pip install datasets huggingface_hub")
            return None
        
        # Get all matching files
        json_files = glob.glob(os.path.join(directory, pattern))
        
        if not json_files:
            print(f"No JSON files found matching pattern {pattern} in {directory}")
            return None
        
        # Read and combine all JSON files
        all_examples = []
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different formats - single object or list
                    if isinstance(data, list):
                        all_examples.extend(data)
                    else:
                        all_examples.append(data)
            except Exception as e:
                print(f"Error reading {file_path}: {str(e)}")
        
        # Create a HuggingFace dataset
        dataset = Dataset.from_list(all_examples)
        dataset_dict = DatasetDict({split: dataset})
        
        return dataset_dict
    
    def create_from_directory(
        self,
        directory: str,
        splits: List[str] = ["train", "validation", "test"],
        split_ratios: List[float] = [0.8, 0.1, 0.1]
    ) -> Union[Dict[str, Any], None]:
        """
        Create a dataset from a directory structure, auto-splitting the data.
        
        Args:
            directory: Directory containing example files
            splits: Split names to use
            split_ratios: Ratio for each split
            
        Returns:
            Dataset dictionary if HuggingFace is available, else None
        """
        if not HUGGINGFACE_AVAILABLE:
            print("HuggingFace datasets not available. Install with pip install datasets huggingface_hub")
            return None
        
        # Find all JSON files
        json_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            print(f"No JSON files found in {directory}")
            return None
        
        # Read all examples from all files
        all_examples = []
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different formats - single object or list
                    if isinstance(data, list):
                        all_examples.extend(data)
                    else:
                        all_examples.append(data)
            except Exception as e:
                print(f"Error reading {file_path}: {str(e)}")
        
        # Create a unified dataset
        dataset = Dataset.from_list(all_examples)
        
        # Split the dataset
        split_dataset = dataset.train_test_split(
            test_size=split_ratios[1] + split_ratios[2]
        )
        
        # If we have a validation split, split the test portion
        if len(splits) > 2:
            # Calculate the validation ratio from the test portion
            validation_ratio = split_ratios[1] / (split_ratios[1] + split_ratios[2])
            
            # Split the test to get validation
            test_valid_split = split_dataset["test"].train_test_split(
                test_size=1 - validation_ratio
            )
            
            # Create final dataset dictionary
            dataset_dict = DatasetDict({
                splits[0]: split_dataset["train"],
                splits[1]: test_valid_split["train"],
                splits[2]: test_valid_split["test"]
            })
        else:
            # Just train/test split
            dataset_dict = DatasetDict({
                splits[0]: split_dataset["train"],
                splits[1]: split_dataset["test"]
            })
        
        return dataset_dict
    
    def create_from_challenging_examples(
        self,
        all_examples_file: str,
        metadata: Optional[Dict[str, Any]] = None,
        entity_type_files: bool = True,
        splits: List[str] = ["train", "validation", "test"],
        split_ratios: List[float] = [0.7, 0.15, 0.15]
    ) -> Union[Dict[str, Any], None]:
        """
        Create a dataset from challenging examples generated by the LLMAugmenter.
        
        Args:
            all_examples_file: Path to the 'all_examples.json' file
            metadata: Optional additional metadata
            entity_type_files: Whether to also look for entity-specific files
            splits: Split names to use
            split_ratios: Ratio for each split
            
        Returns:
            Dataset dictionary if HuggingFace is available, else None
        """
        if not HUGGINGFACE_AVAILABLE:
            print("HuggingFace datasets not available. Install with pip install datasets huggingface_hub")
            return None
        
        # Load the main examples file
        try:
            with open(all_examples_file, 'r', encoding='utf-8') as f:
                all_examples = json.load(f)
        except Exception as e:
            print(f"Error reading {all_examples_file}: {str(e)}")
            return None
        
        # If enabled, look for entity-specific files in the same directory
        if entity_type_files:
            directory = os.path.dirname(all_examples_file)
            entity_files = glob.glob(os.path.join(directory, "*_examples.json"))
            
            for file_path in entity_files:
                # Skip the all_examples.json file
                if os.path.basename(file_path) == "all_examples.json":
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entity_examples = json.load(f)
                        
                    # Add examples that aren't already in all_examples
                    entity_ids = {self._example_id(e) for e in all_examples}
                    for example in entity_examples:
                        if self._example_id(example) not in entity_ids:
                            all_examples.append(example)
                            entity_ids.add(self._example_id(example))
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
        
        # Ensure all examples have required fields
        for example in all_examples:
            if "id" not in example:
                example["id"] = str(uuid.uuid4())
            
            # Convert format if needed
            if "entity_value" in example and "entity_text" not in example:
                example["entity_text"] = example["entity_value"]
            
            # Add metadata if provided
            if metadata:
                for key, value in metadata.items():
                    if key not in example:
                        example[key] = value
        
        # Create a unified dataset
        dataset = Dataset.from_list(all_examples)
        
        # Split the dataset
        datasets = dataset.train_test_split(
            test_size=split_ratios[1] + split_ratios[2]
        )
        
        # If we have a validation split, split the test portion
        if len(splits) > 2:
            # Calculate the validation ratio from the test portion
            validation_ratio = split_ratios[1] / (split_ratios[1] + split_ratios[2])
            
            # Split the test to get validation
            test_valid_split = datasets["test"].train_test_split(
                test_size=1 - validation_ratio
            )
            
            # Create final dataset dictionary
            dataset_dict = DatasetDict({
                splits[0]: datasets["train"],
                splits[1]: test_valid_split["train"],
                splits[2]: test_valid_split["test"]
            })
        else:
            # Just train/test split
            dataset_dict = DatasetDict({
                splits[0]: datasets["train"],
                splits[1]: datasets["test"]
            })
        
        return dataset_dict
    
    def create_from_synthetic_data(
        self,
        dataset_dir: str,
        metadata: Optional[Dict[str, Any]] = None,
        splits: List[str] = ["train", "validation", "test"],
        split_ratios: List[float] = [0.7, 0.15, 0.15]
    ) -> Union[Dict[str, Any], None]:
        """
        Create a dataset from synthetic data generated by AustralianSyntheticDataGenerator.
        
        Args:
            dataset_dir: Directory containing synthetic data files
            metadata: Optional additional metadata
            splits: Split names to use
            split_ratios: Ratio for each split
            
        Returns:
            Dataset dictionary if HuggingFace is available, else None
        """
        if not HUGGINGFACE_AVAILABLE:
            print("HuggingFace datasets not available. Install with pip install datasets huggingface_hub")
            return None
        
        # Look for document files
        document_files = glob.glob(os.path.join(dataset_dir, "document_*.json"))
        
        if not document_files:
            print(f"No document JSON files found in {dataset_dir}")
            return None
        
        # Load all documents
        documents = []
        
        for file_path in document_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                    
                    # Add ID if not present
                    if "id" not in document:
                        document["id"] = os.path.basename(file_path).replace("document_", "").replace(".json", "")
                    
                    # Add metadata if provided
                    if metadata:
                        for key, value in metadata.items():
                            if key not in document:
                                document[key] = value
                    
                    documents.append(document)
            except Exception as e:
                print(f"Error reading {file_path}: {str(e)}")
        
        # Create a dataset
        dataset = Dataset.from_list(documents)
        
        # Split the dataset
        datasets = dataset.train_test_split(
            test_size=split_ratios[1] + split_ratios[2]
        )
        
        # If we have a validation split, split the test portion
        if len(splits) > 2:
            # Calculate the validation ratio from the test portion
            validation_ratio = split_ratios[1] / (split_ratios[1] + split_ratios[2])
            
            # Split the test to get validation
            test_valid_split = datasets["test"].train_test_split(
                test_size=1 - validation_ratio
            )
            
            # Create final dataset dictionary
            dataset_dict = DatasetDict({
                splits[0]: datasets["train"],
                splits[1]: test_valid_split["train"],
                splits[2]: test_valid_split["test"]
            })
        else:
            # Just train/test split
            dataset_dict = DatasetDict({
                splits[0]: datasets["train"],
                splits[1]: datasets["test"]
            })
        
        return dataset_dict
    
    def push_to_hub(
        self,
        dataset_dict: Dict[str, Any],
        repo_id: str,
        token: Optional[str] = None,
        readme_content: Optional[str] = None,
        private: bool = False
    ) -> bool:
        """
        Push a dataset to the HuggingFace Hub.
        
        Args:
            dataset_dict: Dataset dictionary to push
            repo_id: Repository ID on HuggingFace (username/dataset_name)
            token: HuggingFace API token
            readme_content: Optional README content
            private: Whether the repository should be private
            
        Returns:
            Boolean indicating success
        """
        if not HUGGINGFACE_AVAILABLE:
            print("HuggingFace datasets not available. Install with pip install datasets huggingface_hub")
            return False
        
        try:
            # Login to HuggingFace
            if token:
                login(token)
            
            # Generate README if not provided
            if readme_content is None:
                readme_content = self._generate_readme(dataset_dict)
            
            # Push to hub
            dataset_dict.push_to_hub(
                repo_id=repo_id,
                private=private,
                readme_content=readme_content
            )
            
            print(f"Dataset pushed to https://huggingface.co/datasets/{repo_id}")
            return True
            
        except Exception as e:
            print(f"Error pushing to HuggingFace Hub: {str(e)}")
            return False
    
    def export_to_csv(
        self,
        dataset_dict: Dict[str, Any],
        output_dir: str,
        dataset_name: Optional[str] = None
    ) -> bool:
        """
        Export a dataset to CSV files.
        
        Args:
            dataset_dict: Dataset dictionary to export
            output_dir: Directory to save CSV files
            dataset_name: Optional dataset name for file prefix
            
        Returns:
            Boolean indicating success
        """
        if not HUGGINGFACE_AVAILABLE:
            print("HuggingFace datasets not available. Install with pip install datasets huggingface_hub")
            return False
        
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Use dataset name if provided, otherwise use the one from metadata
            name = dataset_name or self.dataset_name or "dataset"
            
            # Export each split
            for split_name, split_dataset in dataset_dict.items():
                # Convert to pandas and save as CSV
                df = split_dataset.to_pandas()
                csv_path = os.path.join(output_dir, f"{name}_{split_name}.csv")
                df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL)
                print(f"Exported {split_name} split to {csv_path}")
            
            # Export metadata
            metadata_path = os.path.join(output_dir, f"{name}_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
            return False
    
    def export_to_jsonl(
        self,
        dataset_dict: Dict[str, Any],
        output_dir: str,
        dataset_name: Optional[str] = None
    ) -> bool:
        """
        Export a dataset to JSONL files (one JSON object per line).
        
        Args:
            dataset_dict: Dataset dictionary to export
            output_dir: Directory to save JSONL files
            dataset_name: Optional dataset name for file prefix
            
        Returns:
            Boolean indicating success
        """
        if not HUGGINGFACE_AVAILABLE:
            print("HuggingFace datasets not available. Install with pip install datasets huggingface_hub")
            return False
        
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Use dataset name if provided, otherwise use the one from metadata
            name = dataset_name or self.dataset_name or "dataset"
            
            # Export each split
            for split_name, split_dataset in dataset_dict.items():
                jsonl_path = os.path.join(output_dir, f"{name}_{split_name}.jsonl")
                
                # Convert to list of records and save as JSONL
                records = split_dataset.to_dict()
                with open(jsonl_path, 'w', encoding='utf-8') as f:
                    # Get the length of any value to determine number of examples
                    num_examples = len(next(iter(records.values())))
                    
                    # Create a record for each example
                    for i in range(num_examples):
                        record = {key: values[i] for key, values in records.items()}
                        f.write(json.dumps(record) + '\n')
                
                print(f"Exported {split_name} split to {jsonl_path}")
            
            # Export metadata
            metadata_path = os.path.join(output_dir, f"{name}_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting to JSONL: {str(e)}")
            return False
    
    def _example_id(self, example: Dict[str, Any]) -> str:
        """Generate a unique ID for an example based on its content."""
        if "id" in example:
            return example["id"]
        
        # Create a hash of text + start + end + entity_type if available
        id_parts = []
        
        if "text" in example:
            id_parts.append(example["text"][:50])  # Use first 50 chars of text
        
        if "start" in example and "end" in example:
            id_parts.append(f"{example['start']}:{example['end']}")
        
        if "entity_type" in example:
            id_parts.append(example["entity_type"])
        
        if id_parts:
            return str(hash("".join(str(p) for p in id_parts)))
        
        # Fallback to a random UUID
        return str(uuid.uuid4())
    
    def _generate_readme(self, dataset_dict: Dict[str, Any]) -> str:
        """Generate a README for the dataset."""
        splits_info = []
        
        for split_name, split_dataset in dataset_dict.items():
            splits_info.append(f"- **{split_name}**: {len(split_dataset)} examples")
        
        splits_text = "\n".join(splits_info)
        
        # Sample a few examples
        examples_text = ""
        for split_name, split_dataset in dataset_dict.items():
            if len(split_dataset) > 0:
                examples_text += f"\n### Example from {split_name} split\n\n```json\n"
                example = split_dataset[0]
                # Convert to JSON for display
                example_json = json.dumps(example, indent=2)
                examples_text += example_json + "\n```\n"
                break
        
        # Get fields in the dataset
        sample_example = next(iter(dataset_dict.values()))[0]
        fields = list(sample_example.keys())
        fields_text = ", ".join(f"`{field}`" for field in fields)
        
        # Build the README
        readme = f"""# {self.dataset_name}

{self.description}

## Dataset Description

- **Author:** {self.author}
- **License:** CC BY-SA 4.0
- **Created:** {datetime.datetime.now().strftime("%Y-%m-%d")}
- **Fields:** {fields_text}

## Dataset Structure

{splits_text}

{examples_text}

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("{self.dataset_name}")

# Print first example from train split
print(dataset["train"][0])
```

## Citation

```
@misc{{{self.dataset_name.lower().replace(' ', '_')}},
  author = {{{self.author}}},
  title = {{{self.dataset_name}}},
  year = {{{datetime.datetime.now().year}}},
  howpublished = {{HuggingFace Datasets}},
  url = {{https://huggingface.co/datasets/{self.dataset_name.lower().replace(' ', '-')}}}
}
```
"""
        return readme