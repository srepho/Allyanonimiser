"""
Example demonstrating how to create custom patterns in Allyanonimiser.

This example shows:
1. Creating simple regex patterns using Presidio
2. Creating context-aware patterns
3. Creating complex patterns using spaCy
4. Testing and validating patterns
5. Using patterns in the analyzer and anonymizer
"""

import re
import spacy
from typing import List, Dict, Any

# Import the Allyanonimiser package
from allyanonimiser import (
    CustomPatternDefinition,
    EnhancedAnalyzer,
    EnhancedAnonymizer,
    validate_pattern_definition,
    test_pattern_against_examples,
    create_pattern_from_examples
)
from allyanonimiser.utils.spacy_helpers import (
    create_spacy_pattern_from_examples,
    create_regex_from_examples
)
from allyanonimiser.utils.presidio_helpers import create_pattern_recognizer


# Set up spaCy for more complex patterns
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    print("Downloading spaCy model...")
    spacy.cli.download("en_core_web_lg")
    nlp = spacy.load("en_core_web_lg")


def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_results(results, title="Results:"):
    """Print analysis results."""
    print(f"\n{title}")
    print("-" * 40)
    for result in results:
        print(f"Entity: {result.entity_type}, Text: '{result.text}', Score: {result.score:.2f}")


def example_1_simple_regex_patterns():
    """Example of creating simple regex patterns."""
    print_section("1. Creating Simple Regex Patterns")
    
    print("Creating an analyzer with a simple project ID pattern...")
    
    # Create a custom pattern for project IDs
    project_id_pattern = CustomPatternDefinition(
        entity_type="PROJECT_ID",
        patterns=["PROJ-[0-9]{5}"],  # Simple regex pattern
        context=["project", "id", "number", "reference"],
        name="project_id_recognizer"
    )
    
    # Validate the pattern definition
    is_valid, message = validate_pattern_definition(project_id_pattern)
    print(f"Pattern validation: {is_valid}, Message: {message}")
    
    # Create an analyzer and add our pattern
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(project_id_pattern)
    
    # Test with some text
    test_text = """
    Please refer to project PROJ-12345 when submitting your timesheet.
    This is different from the reference number REF-789.
    """
    
    results = analyzer.analyze(test_text)
    print_results(results)


def example_2_context_aware_patterns():
    """Example of creating context-aware patterns."""
    print_section("2. Creating Context-Aware Patterns")
    
    print("Creating a pattern that uses context to improve accuracy...")
    
    # Create a custom pattern for account numbers that uses context
    account_number_pattern = CustomPatternDefinition(
        entity_type="ACCOUNT_NUMBER",
        patterns=["[0-9]{8}"],  # This would match many 8-digit numbers
        context=["account", "acc", "a/c", "number", "balance", "transfer"],
        name="account_number_recognizer"
    )
    
    # Create an analyzer and add our pattern
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(account_number_pattern)
    
    # Test with text that has 8-digit numbers both with and without context
    test_text = """
    Your account number is 12345678 and your balance is $500.
    The product code is 87654321 and is not sensitive information.
    Please confirm your account 11223344 for the transfer.
    """
    
    results = analyzer.analyze(test_text)
    print_results(results)
    
    print("\nNotice how the pattern only matches 8-digit numbers near context words like 'account' and 'transfer'")


def example_3_complex_spacy_patterns():
    """Example of creating complex patterns using spaCy."""
    print_section("3. Creating Complex Patterns with spaCy")
    
    print("Creating patterns that use spaCy's linguistic features...")
    
    # Create a spaCy token pattern for recognizing job titles
    job_title_examples = [
        "Senior Software Engineer",
        "Chief Executive Officer",
        "Assistant Regional Manager",
        "Data Scientist",
        "Machine Learning Engineer",
        "Junior Developer"
    ]
    
    # Create spaCy patterns from examples
    job_title_patterns = create_spacy_pattern_from_examples(nlp, job_title_examples, pattern_type="token")
    
    print(f"Generated {len(job_title_patterns)} spaCy patterns from examples:")
    for i, pattern in enumerate(job_title_patterns[:3]):
        print(f"  Pattern {i+1}: {pattern}")
    if len(job_title_patterns) > 3:
        print(f"  ... and {len(job_title_patterns) - 3} more patterns")
    
    # Create a custom pattern definition using these spaCy patterns
    job_title_pattern = CustomPatternDefinition(
        entity_type="JOB_TITLE",
        patterns=job_title_patterns,
        context=["position", "role", "job", "title", "hired", "promoted"],
        name="job_title_recognizer"
    )
    
    # Create an analyzer and add our pattern
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(job_title_pattern)
    
    # Test with some text
    test_text = """
    We are pleased to announce that Jane Doe has been promoted to Senior Data Scientist.
    She previously held the position of Data Analyst at Acme Corp.
    The HR Director will send out more details soon.
    """
    
    results = analyzer.analyze(test_text)
    print_results(results)


def example_4_pattern_from_examples():
    """Example of generating patterns automatically from examples."""
    print_section("4. Creating Patterns from Examples")
    
    print("Automatically generating patterns from example strings...")
    
    # Examples of internal document codes
    document_code_examples = [
        "DOC-2023-1234",
        "DOC-2023-5678",
        "DOC-2022-9876",
        "DOC-2024-4321",
    ]
    
    # Generate a regex pattern from these examples
    regex_pattern = create_regex_from_examples(document_code_examples)
    print(f"Generated regex pattern: {regex_pattern}")
    
    # Create a custom pattern definition using the generate regex
    document_code_pattern = create_pattern_from_examples(
        entity_type="DOCUMENT_CODE",
        examples=document_code_examples,
        context=["document", "doc", "reference", "code"],
        name="document_code_recognizer",
        pattern_type="regex"
    )
    
    # Create an analyzer and add our pattern
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(document_code_pattern)
    
    # Test with some text
    test_text = """
    Please review document DOC-2023-1234 and provide feedback by next week.
    For comparison, you may also refer to last year's document DOC-2022-9876.
    """
    
    results = analyzer.analyze(test_text)
    print_results(results)


def example_5_testing_and_validation():
    """Example of testing and validating patterns."""
    print_section("5. Testing and Validating Patterns")
    
    print("Testing pattern performance with positive and negative examples...")
    
    # Define a pattern for employee IDs
    employee_id_pattern = "EMP-[0-9]{6}"
    
    # Define positive examples (should match)
    positive_examples = [
        "EMP-123456",
        "EMP-987654",
        "My employee ID is EMP-112233"
    ]
    
    # Define negative examples (should not match)
    negative_examples = [
        "EMP-12345",  # Too short
        "EMP-1234567",  # Too long
        "EMPL-123456",  # Wrong prefix
        "emp-123456"    # Case sensitive
    ]
    
    # Test the pattern against examples
    results = test_pattern_against_examples(
        pattern=employee_id_pattern,
        positive_examples=positive_examples,
        negative_examples=negative_examples
    )
    
    print(f"Pattern: {employee_id_pattern}")
    print(f"True positives: {results['true_positives']} / {len(positive_examples)}")
    print(f"False negatives: {results['false_negatives']} / {len(positive_examples)}")
    print(f"True negatives: {results['true_negatives']} / {len(negative_examples)}")
    print(f"False positives: {results['false_positives']} / {len(negative_examples)}")
    print(f"Accuracy: {results['accuracy']:.2f}")
    print(f"F1 Score: {results['f1_score']:.2f}")
    
    # If there are errors, show which examples failed
    if results['false_positives'] > 0:
        print("\nFalse positives (should not match but did):")
        for example in results['false_positive_examples']:
            print(f"  - {example}")
    
    if results['false_negatives'] > 0:
        print("\nFalse negatives (should match but didn't):")
        for example in results['false_negative_examples']:
            print(f"  - {example}")


def example_6_complete_workflow():
    """Example of a complete pattern creation and usage workflow."""
    print_section("6. Complete Workflow: Create, Test, Analyze, Anonymize")
    
    print("Demonstrating a complete workflow for creating and using custom patterns...")
    
    # 1. Define patterns - different types for illustration
    
    # Product code pattern (simple regex)
    product_code_pattern = CustomPatternDefinition(
        entity_type="PRODUCT_CODE",
        patterns=["[A-Z]{3}-[0-9]{4}-[A-Z]{2}"],
        context=["product", "code", "item", "catalog"],
        name="product_code_recognizer"
    )
    
    # Client reference pattern - created from examples
    client_ref_examples = [
        "Client #12345",
        "Client #67890",
        "Client #54321",
        "Client number 98765"
    ]
    client_ref_pattern = create_pattern_from_examples(
        entity_type="CLIENT_REFERENCE",
        examples=client_ref_examples,
        context=["client", "reference", "customer", "number"],
        name="client_reference_recognizer"
    )
    
    # Location pattern using spaCy
    # This leverages spaCy's built-in entity recognition for locations
    location_context = ["office", "branch", "located", "location", "address", "headquarters"]
    location_pattern = CustomPatternDefinition(
        entity_type="OFFICE_LOCATION",
        patterns=[r"\b(?:in|at|our)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:office|branch|location)"],
        context=location_context,
        name="office_location_recognizer"
    )
    
    # 2. Create and configure the analyzer with our patterns
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(product_code_pattern)
    analyzer.add_pattern(client_ref_pattern)
    analyzer.add_pattern(location_pattern)
    
    # 3. Create the anonymizer with custom operators
    anonymizer = EnhancedAnonymizer(analyzer=analyzer)
    
    # Define custom replacement operators
    operators = {
        "PRODUCT_CODE": "hash",            # Use hash for product codes
        "CLIENT_REFERENCE": "replace",     # Use replacement for client refs
        "OFFICE_LOCATION": "redact"        # Use redaction for locations
    }
    
    # 4. Test with a sample text
    sample_text = """
    Sales Report - Confidential
    
    For Client #54321 (Priority customer)
    
    Product ABC-1234-XY has been our top seller this quarter at our Sydney office.
    We also saw strong performance of product XYZ-9876-PQ in the Melbourne branch.
    
    Client #98765 has placed a large order for product ABC-5678-UV to be delivered
    to their Chicago location next month.
    """
    
    # 5. Analyze the text
    analysis_results = analyzer.analyze(sample_text)
    print("Analysis Results:")
    print_results(analysis_results)
    
    # 6. Anonymize the text
    anonymized = anonymizer.anonymize(sample_text, operators=operators)
    
    print("\nOriginal Text:")
    print("-" * 40)
    print(sample_text)
    
    print("\nAnonymized Text:")
    print("-" * 40)
    print(anonymized["text"])
    
    print("\nReplacements Made:")
    print("-" * 40)
    for item in anonymized["items"]:
        print(f"{item['entity_type']}: '{item['original']}' -> '{item['replacement']}'")


def run_all_examples():
    """Run all examples."""
    example_1_simple_regex_patterns()
    example_2_context_aware_patterns()
    example_3_complex_spacy_patterns()
    example_4_pattern_from_examples()
    example_5_testing_and_validation()
    example_6_complete_workflow()


if __name__ == "__main__":
    print("Allyanonimiser Custom Pattern Examples")
    print("This script demonstrates how to create and use custom patterns.")
    print("Each example can be run individually or you can run all examples.")
    
    run_all_examples()