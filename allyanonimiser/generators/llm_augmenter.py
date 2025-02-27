"""
LLM-based augmentation tools for creating challenging datasets.
"""

import os
import json
import re
import time
import uuid
from typing import List, Dict, Any, Optional, Union, Tuple
from ..enhanced_analyzer import EnhancedAnalyzer
from ..pattern_manager import CustomPatternDefinition

class LLMAugmenter:
    """
    Use Language Models to generate challenging PII examples for testing.
    
    This class interfaces with LLM providers to create synthetic data
    with realistic PII instances that test the limits of detection systems.
    """
    
    def __init__(self, api_key: str, api_provider: str = "openai", cache_dir: Optional[str] = None):
        """
        Initialize the LLM augmenter.
        
        Args:
            api_key: API key for the LLM provider
            api_provider: Provider to use ("openai" or "anthropic")
            cache_dir: Optional directory to cache generated examples
        """
        self.api_key = api_key
        self.api_provider = api_provider
        self.cache_dir = cache_dir
        
        # Create cache directory if specified
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        
        # Set up client based on provider
        if api_provider == "openai":
            try:
                import openai
                openai.api_key = api_key
                self.client = openai
            except ImportError:
                raise ImportError("OpenAI Python package is required. Install with 'pip install openai'")
        elif api_provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("Anthropic Python package is required. Install with 'pip install anthropic'")
        else:
            raise ValueError(f"Unsupported API provider: {api_provider}. Use 'openai' or 'anthropic'")
        
        # Tracking for rate limiting
        self.last_request_time = 0
        self.request_count = 0
    
    def generate_challenging_dataset(
        self,
        entity_types: List[str],
        num_examples_per_type: int = 10,
        difficulties: List[str] = ["easy", "medium", "hard"],
        output_dir: str = "challenging_dataset",
        include_context: bool = True,
        use_cache: bool = True,
        add_unique_id: bool = True
    ) -> str:
        """
        Generate a challenging dataset using an LLM.
        
        Args:
            entity_types: List of entity types to generate examples for
            num_examples_per_type: Number of examples per entity type
            difficulties: List of difficulty levels to include
            output_dir: Directory to save the dataset
            include_context: Whether to include context around entities
            use_cache: Whether to use cached examples if available
            add_unique_id: Whether to add unique IDs to examples
            
        Returns:
            Path to the generated dataset
        """
        os.makedirs(output_dir, exist_ok=True)
        all_examples = []
        
        for entity_type in entity_types:
            print(f"Generating examples for {entity_type}...")
            
            for difficulty in difficulties:
                # Check cache first if enabled
                examples = None
                cache_path = None
                
                if use_cache and self.cache_dir:
                    cache_path = os.path.join(
                        self.cache_dir, 
                        f"{entity_type}_{difficulty}_{num_examples_per_type // len(difficulties)}.json"
                    )
                    if os.path.exists(cache_path):
                        try:
                            with open(cache_path, 'r') as f:
                                examples = json.load(f)
                                print(f"  Loaded {len(examples)} cached '{difficulty}' examples for {entity_type}")
                        except Exception as e:
                            print(f"  Error loading cache: {str(e)}")
                            examples = None
                
                # Generate examples if not loaded from cache
                if examples is None:
                    examples = self._generate_examples(
                        entity_type=entity_type,
                        num_examples=num_examples_per_type // len(difficulties),
                        difficulty=difficulty,
                        include_context=include_context
                    )
                    
                    # Save to cache if enabled
                    if use_cache and self.cache_dir and cache_path:
                        try:
                            with open(cache_path, 'w') as f:
                                json.dump(examples, f, indent=2)
                        except Exception as e:
                            print(f"  Error writing cache: {str(e)}")
                
                # Add unique IDs if requested
                if add_unique_id:
                    for example in examples:
                        if "id" not in example:
                            example["id"] = str(uuid.uuid4())
                
                all_examples.extend(examples)
        
        # Save all examples
        with open(os.path.join(output_dir, "all_examples.json"), "w") as f:
            json.dump(all_examples, f, indent=2)
        
        # Save examples by entity type
        for entity_type in entity_types:
            type_examples = [ex for ex in all_examples if ex["entity_type"] == entity_type]
            
            with open(os.path.join(output_dir, f"{entity_type.lower()}_examples.json"), "w") as f:
                json.dump(type_examples, f, indent=2)
        
        # Save examples by difficulty
        for difficulty in difficulties:
            diff_examples = [ex for ex in all_examples if ex.get("difficulty") == difficulty]
            
            with open(os.path.join(output_dir, f"{difficulty}_examples.json"), "w") as f:
                json.dump(diff_examples, f, indent=2)
        
        # Generate a dataset index
        dataset_index = {
            "dataset_name": "Challenging PII Examples",
            "num_examples": len(all_examples),
            "entity_types": entity_types,
            "difficulties": difficulties,
            "generation_date": time.strftime("%Y-%m-%d"),
            "examples_by_entity_type": {
                entity_type: len([ex for ex in all_examples if ex["entity_type"] == entity_type])
                for entity_type in entity_types
            },
            "examples_by_difficulty": {
                difficulty: len([ex for ex in all_examples if ex.get("difficulty") == difficulty])
                for difficulty in difficulties
            }
        }
        
        with open(os.path.join(output_dir, "dataset_index.json"), "w") as f:
            json.dump(dataset_index, f, indent=2)
        
        print(f"\nDataset generation complete. {len(all_examples)} examples saved to {output_dir}")
        
        return output_dir
    
    def _generate_examples(
        self,
        entity_type: str,
        num_examples: int,
        difficulty: str = "medium",
        include_context: bool = True,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate examples for a specific entity type and difficulty."""
        examples = []
        
        # Prompts for different entity types
        entity_prompts = {
            "PERSON": "person names (first and last name)",
            "EMAIL_ADDRESS": "email addresses",
            "PHONE_NUMBER": "phone numbers",
            "CREDIT_CARD_NUMBER": "credit card numbers",
            "US_SSN": "US Social Security Numbers",
            "AU_TFN": "Australian Tax File Numbers",
            "AU_MEDICARE": "Australian Medicare numbers",
            "AU_DRIVERS_LICENSE": "Australian driver's license numbers",
            "AU_PASSPORT": "Australian passport numbers",
            "AU_ADDRESS": "Australian physical addresses",
            "VEHICLE_REGISTRATION": "vehicle registration numbers",
            "VEHICLE_VIN": "vehicle identification numbers (VINs)",
            "POLICY_NUMBER": "insurance policy numbers",
            "CLAIM_NUMBER": "insurance claim numbers"
        }
        
        # Use default prompt if entity type not in the predefined list
        entity_prompt = entity_prompts.get(entity_type, f"{entity_type.lower().replace('_', ' ')}")
        
        # Difficulty descriptions
        difficulty_desc = {
            "easy": "straightforward and in standard format",
            "medium": "slightly obfuscated or in uncommon formats",
            "hard": "heavily obfuscated, split across words, or deliberately formatted to evade detection"
        }
        
        # Build the prompt
        system_prompt = f"""
You are an AI assistant helping to create a dataset of challenging {entity_prompt} examples.
Generate examples that are {difficulty_desc[difficulty]}.

For each example:
1. Create a text snippet containing the {entity_type} entity
2. Mark where the entity starts and ends in the text
3. Provide the exact entity value
4. Explain why this example might be challenging for entity detection systems
"""
        
        user_prompt = f"""
Please generate {num_examples} examples of {entity_prompt} that are {difficulty_desc[difficulty]}.

Format each example as a JSON object with these fields:
- text: The full text snippet containing the entity
- entity_value: The exact entity value to detect
- start: The character position where the entity starts
- end: The character position where the entity ends
- difficulty: "{difficulty}"
- explanation: Why this example might be challenging for detection systems

Make the examples realistic and vary the context around entities.
"""

        # Apply rate limiting
        self._apply_rate_limiting()
        
        for attempt in range(max_retries):
            try:
                # Generate examples using the appropriate API
                if self.api_provider == "openai":
                    response = self.client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    result = response.choices[0].message.content
                    
                elif self.api_provider == "anthropic":
                    response = self.client.messages.create(
                        model="claude-2",
                        system=system_prompt,
                        max_tokens=2000,
                        messages=[
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    
                    result = response.content[0].text
                
                # Parse the result
                parsed_examples = self._parse_llm_response(result)
                
                if parsed_examples:
                    # Ensure each example has the required fields
                    for example in parsed_examples:
                        example["entity_type"] = entity_type
                        
                        # Validate the example
                        if self._validate_example(example):
                            examples.append(example)
                    
                    # If we got enough examples, or close enough, break
                    if len(examples) >= num_examples * 0.8:
                        break
                    
                    # Otherwise, try again for the remaining examples
                    num_examples = num_examples - len(examples)
                    user_prompt = user_prompt.replace(f"generate {num_examples + len(examples)}", f"generate {num_examples}")
                
            except Exception as e:
                print(f"  Error in generation attempt {attempt+1}: {str(e)}")
                time.sleep(2)  # Wait before retry
        
        # Ensure we don't return more examples than requested
        return examples[:num_examples]
    
    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the LLM response text to extract JSON examples."""
        examples = []
        
        # Try different parsing strategies
        
        # Strategy 1: Try to parse the entire response as JSON
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, list):
                examples.extend(parsed)
            else:
                examples.append(parsed)
            return examples
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Look for JSON blocks within triple backticks
        json_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
        
        for block in json_blocks:
            try:
                parsed = json.loads(block)
                if isinstance(parsed, list):
                    examples.extend(parsed)
                else:
                    examples.append(parsed)
            except json.JSONDecodeError:
                # Try to find individual JSON objects within the block
                try:
                    # If it's an array without the outer brackets
                    fixed_block = f"[{block}]"
                    parsed = json.loads(fixed_block)
                    examples.extend(parsed)
                except:
                    # Find individual JSON objects
                    matches = re.finditer(r"\{[^{]*?\}", block)
                    for match in matches:
                        try:
                            example = json.loads(match.group(0))
                            examples.append(example)
                        except:
                            pass
        
        # Strategy 3: Find individual JSON objects in the text
        if not examples:
            matches = re.finditer(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", response_text)
            for match in matches:
                try:
                    example = json.loads(match.group(0))
                    examples.append(example)
                except:
                    pass
        
        return examples
    
    def _validate_example(self, example: Dict[str, Any]) -> bool:
        """Validate that an example has all required fields with appropriate values."""
        required_fields = ["text", "entity_type", "start", "end"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in example:
                return False
        
        # Check start/end are valid
        try:
            start = int(example["start"])
            end = int(example["end"])
            text = str(example["text"])
            
            # Validate indexes are within bounds
            if start < 0 or end > len(text) or start >= end:
                return False
            
            # Ensure the entity value can be extracted from the text
            entity_text = text[start:end]
            if not entity_text:
                return False
            
            # Add entity_text field if not present
            if "entity_text" not in example and "entity_value" not in example:
                example["entity_value"] = entity_text
            
        except (ValueError, TypeError):
            return False
        
        return True
    
    def _apply_rate_limiting(self):
        """Apply rate limiting to avoid hitting API limits."""
        # Simple rate limiting: no more than 10 requests per minute for OpenAI
        # No more than 5 requests per minute for Anthropic
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Reset counter if it's been more than a minute
        if time_since_last > 60:
            self.request_count = 0
        
        # Check if we need to wait
        requests_per_minute = 5 if self.api_provider == "anthropic" else 10
        
        if self.request_count >= requests_per_minute and time_since_last < 60:
            # Wait until a minute has passed since the last request
            wait_time = 60 - time_since_last
            if wait_time > 0:
                print(f"  Rate limiting: waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Update tracking
        self.last_request_time = time.time()
        self.request_count += 1
    
    def augment_with_variations(
        self, 
        example_text: str, 
        entity_type: str, 
        num_variations: int = 5,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Create variations of an example with the same entity type.
        
        Args:
            example_text: Original example text
            entity_type: Entity type to vary
            num_variations: Number of variations to create
            max_retries: Maximum number of retries
            
        Returns:
            List of variation examples
        """
        system_prompt = f"""
You are an AI assistant helping to create variations of text containing {entity_type} entities.
Given an example text, create {num_variations} variations that preserve the entity type but vary the context and presentation.
"""
        
        user_prompt = f"""
Original example: "{example_text}"

Please create {num_variations} variations of this text that:
1. Contain the same type of entity ({entity_type})
2. Vary the context, writing style, and presentation
3. Include different ways the entity might appear in text

Format each variation as a JSON object with:
- text: The varied text
- entity_value: The exact entity value to detect
- start: The character position where the entity starts
- end: The character position where the entity ends
"""
        
        variations = []
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        for attempt in range(max_retries):
            try:
                # Generate variations using the appropriate API
                if self.api_provider == "openai":
                    response = self.client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.8,
                        max_tokens=1500
                    )
                    
                    result = response.choices[0].message.content
                    
                elif self.api_provider == "anthropic":
                    response = self.client.messages.create(
                        model="claude-2",
                        system=system_prompt,
                        max_tokens=1500,
                        messages=[
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    
                    result = response.content[0].text
                
                # Parse the result
                parsed_variations = self._parse_llm_response(result)
                
                if parsed_variations:
                    # Validate and add entity type to each variation
                    for variation in parsed_variations:
                        if self._validate_example(variation):
                            variation["entity_type"] = entity_type
                            variation["difficulty"] = "generated"
                            variations.append(variation)
                    
                    # If we got enough variations, break
                    if len(variations) >= num_variations:
                        break
                    
                    # Otherwise adjust prompt for remaining variations
                    remaining = num_variations - len(variations)
                    user_prompt = user_prompt.replace(f"create {num_variations}", f"create {remaining}")
                
            except Exception as e:
                print(f"Error in variation attempt {attempt+1}: {str(e)}")
                time.sleep(2)
        
        # Add unique IDs
        for variation in variations:
            if "id" not in variation:
                variation["id"] = str(uuid.uuid4())
        
        return variations[:num_variations]
    
    def generate_domain_specific_examples(
        self,
        entity_types: List[str],
        domain: str,
        num_examples: int = 20,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate domain-specific examples (e.g., insurance, medical, financial).
        
        Args:
            entity_types: Entity types to include
            domain: Specific domain for examples
            num_examples: Number of examples to generate
            output_dir: Optional directory to save results
            
        Returns:
            List of generated examples
        """
        system_prompt = f"""
You are an AI assistant helping to create realistic examples of text from the {domain} domain that contain multiple PII entities.
Each example should:
1. Be a realistic text snippet that might appear in {domain} documents
2. Contain multiple entities from the provided list of entity types
3. Vary in complexity and context to create a diverse dataset
"""
        
        entity_types_str = ", ".join(entity_types)
        user_prompt = f"""
Please create {num_examples} realistic {domain} text examples that contain multiple PII entities from these types: {entity_types_str}.

For each example:
1. Create a realistic text snippet that might appear in a {domain} document
2. Include at least 2-3 different entity types from the provided list
3. For each entity, include its type, value, and position (start and end indices)

Format the response as JSON objects, with each object having:
- text: The full text snippet
- entities: An array of objects, each with entity_type, entity_value, start, and end

Make the examples realistic and varied in complexity and context.
"""
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        examples = []
        
        # Generate examples
        try:
            if self.api_provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=3000
                )
                
                result = response.choices[0].message.content
                
            elif self.api_provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-2",
                    system=system_prompt,
                    max_tokens=3000,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                result = response.content[0].text
            
            # Parse the result
            parsed_examples = self._parse_llm_response(result)
            
            if parsed_examples:
                # Process each example
                for example in parsed_examples:
                    if "text" in example and "entities" in example:
                        # Add domain and ID
                        example["domain"] = domain
                        example["id"] = str(uuid.uuid4())
                        
                        # Extract entities into individual examples if needed
                        entities = example.get("entities", [])
                        individual_examples = []
                        
                        for entity in entities:
                            if isinstance(entity, dict) and "entity_type" in entity:
                                individual_example = {
                                    "text": example["text"],
                                    "entity_type": entity["entity_type"],
                                    "entity_value": entity.get("entity_value", ""),
                                    "start": entity.get("start", 0),
                                    "end": entity.get("end", 0),
                                    "domain": domain,
                                    "id": str(uuid.uuid4())
                                }
                                
                                if self._validate_example(individual_example):
                                    individual_examples.append(individual_example)
                        
                        examples.append(example)
                        examples.extend(individual_examples)
        
        except Exception as e:
            print(f"Error generating domain-specific examples: {str(e)}")
        
        # Save to output directory if provided
        if output_dir and examples:
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(output_dir, f"{domain}_examples.json")
            with open(output_file, 'w') as f:
                json.dump(examples, f, indent=2)
            
            print(f"Saved {len(examples)} {domain} examples to {output_file}")
        
        return examples
    
    def analyze_detection_patterns(
        self, 
        examples: List[Dict[str, Any]], 
        analyzer: EnhancedAnalyzer
    ) -> Dict[str, Any]:
        """
        Analyze which examples are detected by the analyzer and identify patterns.
        
        Args:
            examples: List of example dictionaries with text, entity_type, etc.
            analyzer: EnhancedAnalyzer instance to test
            
        Returns:
            Analysis report
        """
        results = {
            "total_examples": len(examples),
            "detected": 0,
            "missed": 0,
            "by_entity_type": {},
            "by_difficulty": {},
            "detected_examples": [],
            "missed_examples": []
        }
        
        # Track entity types and difficulties
        entity_types = set(ex["entity_type"] for ex in examples)
        difficulties = set(ex.get("difficulty", "unknown") for ex in examples)
        
        # Initialize entity type and difficulty stats
        for entity_type in entity_types:
            results["by_entity_type"][entity_type] = {
                "total": 0,
                "detected": 0,
                "detection_rate": 0.0
            }
        
        for difficulty in difficulties:
            results["by_difficulty"][difficulty] = {
                "total": 0,
                "detected": 0,
                "detection_rate": 0.0
            }
        
        # Test each example
        for example in examples:
            text = example["text"]
            entity_type = example["entity_type"]
            true_start = example["start"]
            true_end = example["end"]
            difficulty = example.get("difficulty", "unknown")
            
            # Track counts
            results["by_entity_type"][entity_type]["total"] += 1
            results["by_difficulty"][difficulty]["total"] += 1
            
            # Analyze the text
            analysis_results = analyzer.analyze(text)
            
            # Check if the entity was detected
            detected = False
            matching_result = None
            
            for result in analysis_results:
                # Check for overlap with the true entity
                if (result.start <= true_end and result.end >= true_start):
                    detected = True
                    matching_result = {
                        "entity_type": result.entity_type,
                        "text": text[result.start:result.end],
                        "start": result.start,
                        "end": result.end,
                        "score": result.score
                    }
                    break
            
            # Record the result
            if detected:
                results["detected"] += 1
                results["by_entity_type"][entity_type]["detected"] += 1
                results["by_difficulty"][difficulty]["detected"] += 1
                
                # Add detection result
                detection_result = example.copy()
                detection_result["detected"] = True
                detection_result["matching_result"] = matching_result
                results["detected_examples"].append(detection_result)
            else:
                results["missed"] += 1
                
                # Add to missed examples
                miss_result = example.copy()
                miss_result["detected"] = False
                results["missed_examples"].append(miss_result)
        
        # Calculate detection rates
        for entity_type in entity_types:
            total = results["by_entity_type"][entity_type]["total"]
            detected = results["by_entity_type"][entity_type]["detected"]
            results["by_entity_type"][entity_type]["detection_rate"] = detected / total if total > 0 else 0
        
        for difficulty in difficulties:
            total = results["by_difficulty"][difficulty]["total"]
            detected = results["by_difficulty"][difficulty]["detected"]
            results["by_difficulty"][difficulty]["detection_rate"] = detected / total if total > 0 else 0
        
        # Calculate overall detection rate
        results["detection_rate"] = results["detected"] / results["total_examples"] if results["total_examples"] > 0 else 0
        
        return results
    
    def create_error_analysis_report(
        self, 
        analysis_results: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a detailed error analysis report from detection results.
        
        Args:
            analysis_results: Results from analyze_detection_patterns
            output_file: Optional file to save the report
            
        Returns:
            Error analysis report
        """
        # Extract missed examples from analysis results
        missed_examples = analysis_results.get("missed_examples", [])
        
        # Categorize errors
        error_categories = {
            "format_variation": [],
            "entity_boundaries": [],
            "context_confusion": [],
            "obfuscation": [],
            "entity_splitting": [],
            "unusual_format": [],
            "other": []
        }
        
        # Analyze each missed example
        for example in missed_examples:
            text = example.get("text", "")
            entity_type = example.get("entity_type", "")
            entity_value = example.get("entity_value", "")
            explanation = example.get("explanation", "")
            
            # Determine error category based on explanation and example properties
            if any(term in explanation.lower() for term in ["split", "separate", "across", "multiple", "parts"]):
                error_categories["entity_splitting"].append(example)
            elif any(term in explanation.lower() for term in ["format", "unusual", "non-standard", "uncommon"]):
                error_categories["unusual_format"].append(example)
            elif any(term in explanation.lower() for term in ["obfuscate", "mask", "hidden", "disguise"]):
                error_categories["obfuscation"].append(example)
            elif any(term in explanation.lower() for term in ["boundary", "span", "start", "end"]):
                error_categories["entity_boundaries"].append(example)
            elif any(term in explanation.lower() for term in ["context", "surrounding", "adjacent"]):
                error_categories["context_confusion"].append(example)
            elif any(term in explanation.lower() for term in ["variation", "alternative", "different"]):
                error_categories["format_variation"].append(example)
            else:
                error_categories["other"].append(example)
        
        # Create the error analysis report
        report = {
            "total_missed": len(missed_examples),
            "error_categories": {
                category: len(examples) for category, examples in error_categories.items()
            },
            "error_distribution": {
                category: round(len(examples) / len(missed_examples) * 100, 2) if missed_examples else 0
                for category, examples in error_categories.items() if examples
            },
            "entity_type_distribution": {},
            "examples_by_category": error_categories
        }
        
        # Calculate distribution by entity type
        entity_types = {}
        for example in missed_examples:
            entity_type = example.get("entity_type", "unknown")
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        report["entity_type_distribution"] = {
            entity_type: round(count / len(missed_examples) * 100, 2) if missed_examples else 0
            for entity_type, count in entity_types.items()
        }
        
        # Save report if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"Error analysis report saved to {output_file}")
            except Exception as e:
                print(f"Error saving report: {str(e)}")
        
        return report
    
    def publish_to_huggingface(
        self,
        dataset_dir: str,
        repo_id: str,
        token: str
    ) -> bool:
        """
        Publish a dataset to HuggingFace Hub.
        
        Args:
            dataset_dir: Directory containing the dataset
            repo_id: HuggingFace repository ID (username/dataset-name)
            token: HuggingFace API token
            
        Returns:
            Success status
        """
        try:
            from .dataset_publisher import DatasetPublisher
        except ImportError:
            print("Cannot import DatasetPublisher. Please ensure dataset_publisher.py is in the same directory.")
            return False
        
        try:
            # Create a dataset publisher
            publisher = DatasetPublisher(
                dataset_name="Challenging PII Examples",
                description="A dataset of challenging Personal Identifiable Information (PII) examples for testing entity detection systems",
                author="Allyanonimiser"
            )
            
            # Load the dataset
            all_examples_file = os.path.join(dataset_dir, "all_examples.json")
            dataset_dict = publisher.create_from_challenging_examples(all_examples_file)
            
            if dataset_dict:
                # Push to HuggingFace
                success = publisher.push_to_hub(
                    dataset_dict=dataset_dict,
                    repo_id=repo_id,
                    token=token
                )
                
                return success
            else:
                print("Failed to create dataset from examples")
                return False
                
        except Exception as e:
            print(f"Error publishing to HuggingFace: {str(e)}")
            return False