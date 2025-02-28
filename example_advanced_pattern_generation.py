"""
Example demonstrating the enhanced pattern generation capabilities of Allyanonimiser.

This example shows how to use different generalization levels to create more flexible
pattern matching for various types of entities in insurance and PII data.
"""

import re
from allyanonimiser import (
    create_pattern_from_examples, 
    create_au_insurance_analyzer,
    EnhancedAnalyzer
)
from utils.spacy_helpers import create_regex_from_examples

def demo_basic_pattern_generation():
    """Demonstrate basic pattern generation with no generalization."""
    print("\n=== Basic Pattern Generation (No Generalization) ===")
    
    examples = ["REF-12345", "REF-67890", "REF-54321"]
    
    # Create a basic pattern with no generalization
    pattern = create_regex_from_examples(examples, generalization_level="none")
    
    print(f"Examples: {examples}")
    print(f"Generated Pattern: {pattern}")
    
    # Test the pattern
    test_examples = examples + ["REF-98765", "REF12345", "ref-12345"]
    print("\nPattern Matching Results:")
    for example in test_examples:
        match = re.match(pattern, example)
        print(f"  '{example}': {'Match' if match else 'No match'}")

def demo_low_generalization():
    """Demonstrate low-level pattern generalization."""
    print("\n=== Low-Level Pattern Generalization ===")
    
    examples = ["REF-12345", "REF-67890", "REF-54321"]
    
    # Create a pattern with low generalization
    pattern = create_regex_from_examples(examples, generalization_level="low")
    
    print(f"Examples: {examples}")
    print(f"Generated Pattern: {pattern}")
    
    # Test the pattern
    test_examples = examples + ["REF-98765", "REF12345", "ref-12345"]
    print("\nPattern Matching Results:")
    for example in test_examples:
        match = re.match(pattern, example)
        print(f"  '{example}': {'Match' if match else 'No match'}")

def demo_medium_generalization():
    """Demonstrate medium-level pattern generalization."""
    print("\n=== Medium-Level Pattern Generalization ===")
    
    # Example date formats
    date_examples = ["01/02/2023", "15/06/2022", "31/12/2021"]
    date_pattern = create_regex_from_examples(date_examples, generalization_level="medium")
    print(f"Date Examples: {date_examples}")
    print(f"Generated Date Pattern: {date_pattern}")
    
    # Test date pattern
    date_test_examples = date_examples + ["05/07/2024", "10-11-2020", "2023/01/15"]
    print("\nDate Pattern Matching Results:")
    for example in date_test_examples:
        match = re.match(date_pattern, example)
        print(f"  '{example}': {'Match' if match else 'No match'}")
    
    # Example ID formats
    id_examples = ["ABC-12345", "DEF-67890", "XYZ-54321"]
    id_pattern = create_regex_from_examples(id_examples, generalization_level="medium")
    print(f"\nID Examples: {id_examples}")
    print(f"Generated ID Pattern: {id_pattern}")
    
    # Test ID pattern
    id_test_examples = id_examples + ["PQR-98765", "AB-12345", "ABCD-12345", "ABC-123"]
    print("\nID Pattern Matching Results:")
    for example in id_test_examples:
        match = re.match(id_pattern, example)
        print(f"  '{example}': {'Match' if match else 'No match'}")

def demo_high_generalization():
    """Demonstrate high-level pattern generalization."""
    print("\n=== High-Level Pattern Generalization ===")
    
    # Example complex formats
    complex_examples = [
        "Customer ID: ABC-123 (2023)",
        "Customer ID: XYZ-456 (2022)",
        "Customer ID: PQR-789 (2024)"
    ]
    complex_pattern = create_regex_from_examples(complex_examples, generalization_level="high")
    print(f"Complex Examples: {complex_examples}")
    print(f"Generated Complex Pattern: {complex_pattern}")
    
    # Test complex pattern
    complex_test_examples = complex_examples + [
        "Customer ID: LMN-321 (2025)",
        "Customer ID: ABC-123 (2020)",
        "Customer ID: DEF-456"  # Missing year
    ]
    print("\nComplex Pattern Matching Results:")
    for example in complex_test_examples:
        match = re.match(complex_pattern, example)
        print(f"  '{example}': {'Match' if match else 'No match'}")

def demo_entity_detection_with_generalization():
    """Demonstrate entity detection with generalized patterns."""
    print("\n=== Entity Detection with Generalized Patterns ===")
    
    # Create an analyzer
    analyzer = EnhancedAnalyzer()
    
    # Add patterns with different generalization levels
    reference_examples = ["REF-12345", "REF-67890", "REF-54321"]
    reference_pattern = create_pattern_from_examples(
        entity_type="REFERENCE_NUMBER",
        examples=reference_examples,
        context=["reference", "ref", "number"],
        name="reference_pattern",
        generalization_level="medium"
    )
    analyzer.add_pattern(reference_pattern)
    
    date_examples = ["01/02/2023", "15/06/2022", "31/12/2021"]
    date_pattern = create_pattern_from_examples(
        entity_type="DATE",
        examples=date_examples,
        context=["date", "on", "dated"],
        name="date_pattern",
        generalization_level="medium"
    )
    analyzer.add_pattern(date_pattern)
    
    # Create test text
    test_text = """
    Claim Details:
    Reference: REF-98765
    Date of Incident: 05/07/2024
    Customer ID: LMN-321 (2025)
    """
    
    # Analyze the text
    results = analyzer.analyze(test_text)
    
    # Print results
    print("Test Text:")
    print(test_text)
    print("\nDetected Entities:")
    for result in results:
        print(f"  Entity: {result.entity_type}, Text: {result.text}, Score: {result.score:.2f}")

def demo_format_detection():
    """Demonstrate automatic format detection for common patterns."""
    print("\n=== Automatic Format Detection ===")
    
    formats = [
        {
            "name": "Dates",
            "examples": ["01/02/2023", "15/06/2022", "31/12/2021"]
        },
        {
            "name": "Phone Numbers",
            "examples": ["123-456-7890", "987-654-3210", "(123) 456-7890"]
        },
        {
            "name": "Email Addresses",
            "examples": ["user@example.com", "another.user@test.org", "john.doe@company.co.uk"]
        },
        {
            "name": "IP Addresses",
            "examples": ["192.168.0.1", "10.0.0.1", "172.16.0.1"]
        },
        {
            "name": "URLs",
            "examples": ["https://example.com", "http://test.org/page", "https://company.co.uk/products"]
        },
        {
            "name": "Money Amounts",
            "examples": ["$123.45", "$1,234.56", "$12.00"]
        }
    ]
    
    for format_info in formats:
        pattern = create_regex_from_examples(format_info["examples"], generalization_level="medium")
        print(f"\n{format_info['name']}:")
        print(f"  Examples: {format_info['examples']}")
        print(f"  Detected Pattern: {pattern}")
        
        # Test with a new example
        new_example = {
            "Dates": "10/11/2025",
            "Phone Numbers": "555-123-4567",
            "Email Addresses": "new.user@domain.net",
            "IP Addresses": "8.8.8.8",
            "URLs": "https://newsite.net/path",
            "Money Amounts": "$9,999.99"
        }[format_info["name"]]
        
        match = re.match(pattern, new_example)
        print(f"  New example '{new_example}': {'Match' if match else 'No match'}")

def main():
    """Run all the pattern generation demos."""
    print("ENHANCED PATTERN GENERATION EXAMPLES")
    print("====================================")
    
    demo_basic_pattern_generation()
    demo_low_generalization()
    demo_medium_generalization()
    demo_high_generalization()
    demo_entity_detection_with_generalization()
    demo_format_detection()

if __name__ == "__main__":
    main()
