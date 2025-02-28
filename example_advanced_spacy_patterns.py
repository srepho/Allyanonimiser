"""
Advanced spaCy Pattern Examples for Allyanonimiser

This example demonstrates:
1. Creating advanced spaCy patterns for complex entity recognition
2. Using linguistic features like part-of-speech tags and dependencies
3. Combining token-based and phrase-based patterns
4. Creating patterns for multi-token entities
5. Fine-tuning pattern matching with weights and context
"""

import re
import spacy
from typing import List, Dict, Any, Tuple
import json

# Import the Allyanonimiser package
from allyanonimiser import (
    CustomPatternDefinition,
    EnhancedAnalyzer,
    EnhancedAnonymizer,
    create_pattern_from_examples
)
from allyanonimiser.utils.spacy_helpers import (
    create_spacy_pattern_from_examples,
    create_spacy_matcher,
    create_spacy_phrase_matcher,
    find_context_matches,
    extract_patterns_from_spans,
    get_entity_context
)


# Set up spaCy
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


def print_tokens(doc):
    """Print token information from a spaCy document."""
    print("\nToken Analysis:")
    print("-" * 60)
    headers = ["Text", "POS", "Tag", "Dep", "Lemma", "Shape", "Is Alpha", "Is Stop"]
    print(f"{headers[0]:<15} {headers[1]:<10} {headers[2]:<10} {headers[3]:<10} {headers[4]:<15} {headers[5]:<10} {headers[6]:<10} {headers[7]:<10}")
    print("-" * 60)
    
    for token in doc:
        print(f"{token.text:<15} {token.pos_:<10} {token.tag_:<10} {token.dep_:<10} {token.lemma_:<15} {token.shape_:<10} {token.is_alpha:<10} {token.is_stop:<10}")


def example_1_token_based_patterns():
    """Example of token-based patterns using spaCy."""
    print_section("1. Token-Based Patterns in spaCy")
    
    print("Creating and explaining token-based patterns...")
    
    # Sample text with different types of sensitive information
    sample_text = "The patient Jane Smith (born 15/04/1985) has been diagnosed with hypertension and prescribed Lisinopril 10mg daily."
    doc = nlp(sample_text)
    
    # Print token information to understand the document structure
    print_tokens(doc)
    
    # Define a token pattern for matching medication doses
    medication_pattern = [
        # First match a medication name (a proper noun, typically)
        {"POS": "PROPN"},
        # Then match a number
        {"LIKE_NUM": True},
        # Then match a unit (mg, ml, etc.)
        {"LOWER": {"IN": ["mg", "ml", "g", "mcg", "ug"]}}
    ]
    
    print(f"\nMedication Pattern: {json.dumps(medication_pattern, indent=2)}")
    
    # Create a matcher and add our pattern
    matcher = create_spacy_matcher(nlp, patterns={"MEDICATION": [medication_pattern]})
    
    # Find matches
    matches = matcher(doc)
    
    print("\nMatches:")
    for match_id, start, end in matches:
        span = doc[start:end]
        print(f"Match: '{span.text}' (Token indices: {start}-{end})")
    
    # Create an analyzer with this pattern
    medication_pattern_def = CustomPatternDefinition(
        entity_type="MEDICATION_DOSE",
        patterns=[medication_pattern],
        context=["prescribed", "medication", "drug", "dose", "take"],
        name="medication_dose_recognizer"
    )
    
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(medication_pattern_def)
    
    results = analyzer.analyze(sample_text)
    print_results(results)


def example_2_phrase_based_patterns():
    """Example of phrase-based patterns using spaCy."""
    print_section("2. Phrase-Based Patterns in spaCy")
    
    print("Creating and demonstrating phrase-based patterns...")
    
    # List of medical condition phrases to match
    medical_conditions = [
        "hypertension",
        "diabetes mellitus",
        "coronary artery disease",
        "chronic obstructive pulmonary disease",
        "rheumatoid arthritis",
        "major depressive disorder"
    ]
    
    print(f"Medical conditions to match: {', '.join(medical_conditions)}")
    
    # Create a phrase matcher for these conditions
    phrase_matcher = create_spacy_phrase_matcher(nlp, patterns={"MEDICAL_CONDITION": medical_conditions})
    
    # Sample text
    sample_text = """
    Patient history includes hypertension, diabetes mellitus type 2, and episodes of major depressive disorder.
    No history of coronary artery disease or chronic kidney disease.
    """
    
    doc = nlp(sample_text)
    
    # Find matches
    matches = phrase_matcher(doc)
    
    print("\nPhrase Matches:")
    for match_id, start, end in matches:
        span = doc[start:end]
        print(f"Match: '{span.text}' (Token indices: {start}-{end})")
    
    # Create an analyzer with this pattern
    medical_pattern_def = CustomPatternDefinition(
        entity_type="MEDICAL_CONDITION",
        patterns=medical_conditions,
        context=["diagnosed", "history", "patient", "condition", "disease"],
        name="medical_condition_recognizer"
    )
    
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(medical_pattern_def)
    
    results = analyzer.analyze(sample_text)
    print_results(results)


def example_3_complex_linguistic_patterns():
    """Example of patterns that use linguistic features."""
    print_section("3. Complex Linguistic Patterns")
    
    print("Creating patterns that use part-of-speech and dependency parsing...")
    
    # Sample text with job title information
    sample_text = """
    Sarah Johnson is the Chief Executive Officer at Acme Corporation.
    Michael Williams works as a Senior Software Engineer for XYZ Tech.
    Dr. Emily Brown, the Director of Research, will be leading the project.
    """
    
    # Create a document to analyze the structure
    doc = nlp(sample_text)
    
    # Print the token information for the first sentence
    first_sentence = list(doc.sents)[0]
    print(f"Analyzing sentence: '{first_sentence.text}'")
    print_tokens(first_sentence)
    
    # Define a complex pattern for job titles based on linguistic features
    job_title_patterns = [
        # Pattern 1: "is the/a [TITLE]" (capturing titles after copular verbs)
        [
            {"LEMMA": "be"},
            {"LOWER": {"IN": ["the", "a", "an"]}},
            {"LOWER": {"IN": ["chief", "senior", "junior", "lead", "head", "principal"]}},
            {"POS": "NOUN"},
            {"LOWER": {"IN": ["officer", "manager", "director", "engineer", "developer"]}, "OP": "?"}
        ],
        
        # Pattern 2: "works as a/the [TITLE]" (capturing titles after "works as")
        [
            {"LEMMA": "work"},
            {"LOWER": "as"},
            {"LOWER": {"IN": ["the", "a", "an"]}},
            {"POS": "ADJ", "OP": "?"},
            {"POS": "NOUN"},
            {"POS": "NOUN", "OP": "?"}
        ],
        
        # Pattern 3: Titles in apposition (like "Dr. Emily Brown, the Director of Research")
        [
            {"POS": "PUNCT"},
            {"LOWER": {"IN": ["the", "a", "an"]}},
            {"POS": "NOUN"},
            {"LOWER": "of", "OP": "?"},
            {"POS": "NOUN", "OP": "?"},
            {"POS": "PUNCT"}
        ]
    ]
    
    print("\nJob Title Patterns:")
    for i, pattern in enumerate(job_title_patterns):
        print(f"Pattern {i+1}: {json.dumps(pattern, indent=2)}")
    
    # Create a matcher and add our patterns
    matcher = create_spacy_matcher(nlp, patterns={"JOB_TITLE": job_title_patterns})
    
    # Find matches
    matches = matcher(doc)
    
    print("\nMatches:")
    for match_id, start, end in matches:
        span = doc[start:end]
        print(f"Match: '{span.text}' (Token indices: {start}-{end})")
    
    # Create a custom pattern for job titles
    job_title_pattern_def = CustomPatternDefinition(
        entity_type="JOB_TITLE",
        patterns=job_title_patterns,
        context=["works", "position", "role", "title", "hired", "appointed"],
        name="job_title_recognizer"
    )
    
    # Create an analyzer with our patterns
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(job_title_pattern_def)
    
    # Test with our sample text
    results = analyzer.analyze(sample_text)
    print_results(results)


def example_4_contextual_patterns():
    """Example of using context to improve pattern matching."""
    print_section("4. Using Context to Improve Matching")
    
    print("Demonstrating how context can improve pattern matching accuracy...")
    
    # Sample text with project numbers that could be confused with other numbers
    sample_text = """
    Project #12345 is scheduled for completion by June 2023.
    The budget for project #67890 is $150,000.
    The room number is 12345 and the zip code is 67890.
    Please refer to project ID #54321 in all correspondence.
    """
    
    # Create a pattern for project numbers based on context
    project_pattern_def = CustomPatternDefinition(
        entity_type="PROJECT_NUMBER",
        patterns=["#[0-9]{5}"],  # Simple pattern that would match many things
        context=["project", "ID", "reference", "refer"],  # Context words to disambiguate
        name="project_number_recognizer"
    )
    
    # Create an analyzer with and without context
    analyzer_with_context = EnhancedAnalyzer()
    analyzer_with_context.add_pattern(project_pattern_def)
    
    # Create another pattern without context
    no_context_pattern = CustomPatternDefinition(
        entity_type="PROJECT_NUMBER",
        patterns=["#[0-9]{5}"],
        context=[],  # Empty context
        name="project_number_no_context"
    )
    
    analyzer_no_context = EnhancedAnalyzer()
    analyzer_no_context.add_pattern(no_context_pattern)
    
    # Analyze with both analyzers
    results_with_context = analyzer_with_context.analyze(sample_text)
    results_no_context = analyzer_no_context.analyze(sample_text)
    
    print_results(results_with_context, "Results with Context:")
    print_results(results_no_context, "Results without Context:")
    
    # Explain the difference
    print("\nExplanation:")
    print("Without context, the pattern matches all instances of '#' followed by 5 digits.")
    print("With context, it only matches those near words like 'project' or 'ID'.")


def example_5_entity_relationship_patterns():
    """Example of patterns that capture entity relationships."""
    print_section("5. Entity Relationship Patterns")
    
    print("Creating patterns that capture relationships between entities...")
    
    # Sample text with person-company relationships
    sample_text = """
    John Smith is employed by Acme Corporation since 2018.
    Acme Corporation's CEO, Jane Doe, announced the new initiative.
    XYZ Tech has hired Michael Johnson as their CTO.
    """
    
    doc = nlp(sample_text)
    
    # Print the token information for understanding
    print_tokens(doc)
    
    # Define a pattern for employment relationships
    employment_patterns = [
        # "Person is employed by Company"
        [
            {"POS": "PROPN"},  # First name
            {"POS": "PROPN", "OP": "?"},  # Optional last name
            {"LEMMA": "be"},
            {"LEMMA": "employ"},
            {"LOWER": "by"},
            {"POS": "PROPN"},  # Company first word
            {"POS": "PROPN", "OP": "?"}  # Company second word
        ],
        
        # "Company's Position, Person"
        [
            {"POS": "PROPN"},  # Company first word
            {"POS": "PROPN", "OP": "?"},  # Company second word
            {"LOWER": "'s"},
            {"POS": "NOUN"},  # Position
            {"LOWER": ","},
            {"POS": "PROPN"},  # Person first name
            {"POS": "PROPN", "OP": "?"}  # Person last name
        ],
        
        # "Company has hired Person as Position"
        [
            {"POS": "PROPN"},  # Company first word
            {"POS": "PROPN", "OP": "?"},  # Company second word
            {"LEMMA": "have"},
            {"LEMMA": "hire"},
            {"POS": "PROPN"},  # Person first name
            {"POS": "PROPN", "OP": "?"},  # Person last name
            {"LOWER": "as"},
            {"LOWER": {"IN": ["their", "its", "the"]}},
            {"POS": {"IN": ["NOUN", "PROPN"]}}  # Position
        ]
    ]
    
    # Create a matcher
    matcher = create_spacy_matcher(nlp, patterns={"EMPLOYMENT_RELATION": employment_patterns})
    
    # Find matches
    matches = matcher(doc)
    
    print("\nEmployment Relationship Matches:")
    for match_id, start, end in matches:
        span = doc[start:end]
        print(f"Match: '{span.text}' (Token indices: {start}-{end})")
        
        # Extract entities from the match
        if "employed by" in span.text:
            person = span[:2].text  # First two tokens should be the person
            company = span[5:].text  # Tokens after "employed by"
            print(f"  - Person: {person}, Company: {company}, Relation: employed by")
        elif "'s" in span.text:
            company = span[:2].text  # Company name before 's
            position = span[3].text  # Position after 's
            person = span[5:].text  # Person after comma
            print(f"  - Person: {person}, Company: {company}, Position: {position}")
        elif "hired" in span.text:
            company = span[:2].text  # Company before "has hired"
            person = span[4:6].text  # Person after "has hired"
            position = span[-1].text  # Position at the end
            print(f"  - Person: {person}, Company: {company}, Position: {position}")
    
    # Create a custom pattern definition
    employment_pattern_def = CustomPatternDefinition(
        entity_type="EMPLOYMENT_RELATION",
        patterns=employment_patterns,
        context=["employee", "employer", "company", "hired", "works", "position"],
        name="employment_relation_recognizer"
    )
    
    # Create an analyzer and add our pattern
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(employment_pattern_def)
    
    # Test with our sample text
    results = analyzer.analyze(sample_text)
    print_results(results)


def example_6_auto_generating_patterns():
    """Example of automatically generating patterns from examples."""
    print_section("6. Auto-Generating Patterns from Examples")
    
    print("Demonstrating how to auto-generate patterns from examples...")
    
    # Examples of proprietary code references
    code_examples = [
        "XJ-2023-1234-A",
        "XJ-2022-5678-B",
        "XJ-2023-9876-C",
        "XJ-2024-4321-D"
    ]
    
    print(f"Example code references: {', '.join(code_examples)}")
    
    # Auto-generate patterns from examples
    token_patterns = create_spacy_pattern_from_examples(nlp, code_examples, pattern_type="token")
    
    print("\nGenerated Token Patterns:")
    for i, pattern in enumerate(token_patterns[:3]):
        print(f"Pattern {i+1}: {json.dumps(pattern, indent=2)}")
    
    # Create a pattern from examples with the helper function
    code_pattern = create_pattern_from_examples(
        entity_type="PROPRIETARY_CODE",
        examples=code_examples,
        context=["code", "reference", "proprietary", "identifier"],
        name="proprietary_code_recognizer",
        pattern_type="spacy"  # Use spaCy patterns instead of regex
    )
    
    # Test with a sample text
    sample_text = """
    Our new product with code XJ-2023-1234-A is ready for testing.
    Please also review the older version XJ-2022-5678-B for comparison.
    The document reference is DOC-2023-456 which is unrelated.
    """
    
    # Create an analyzer with our pattern
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(code_pattern)
    
    # Test with our sample text
    results = analyzer.analyze(sample_text)
    print_results(results)


def example_7_complete_advanced_workflow():
    """Example of a complete advanced workflow."""
    print_section("7. Complete Advanced Workflow")
    
    print("Demonstrating a complete workflow with advanced spaCy patterns...")
    
    # Define multiple pattern types for a comprehensive analyzer
    
    # 1. Person-Role Pattern (using dependency parsing features)
    person_role_pattern = [
        {"POS": "PROPN", "DEP": "compound", "OP": "?"},  # Optional first name
        {"POS": "PROPN", "DEP": "nsubj"},  # Last name as subject
        {"LEMMA": "be"},  # "is" verb
        {"LOWER": {"IN": ["a", "the", "our", "their"]}},  # Determiner
        {"POS": "ADJ", "OP": "?"},  # Optional adjective
        {"POS": "NOUN"}  # Role noun
    ]
    
    person_role_def = CustomPatternDefinition(
        entity_type="PERSON_ROLE",
        patterns=[person_role_pattern],
        context=["position", "role", "appointed", "named", "serves"],
        name="person_role_recognizer"
    )
    
    # 2. Contract Reference Pattern (based on examples)
    contract_examples = [
        "Contract #CT-2023-1234",
        "Contract #CT-2022-5678",
        "Contract Number CT-2023-9876",
        "Contract Reference CT-2024-4321"
    ]
    
    contract_pattern = create_pattern_from_examples(
        entity_type="CONTRACT_REFERENCE",
        examples=contract_examples,
        context=["contract", "agreement", "document", "reference", "signed"],
        name="contract_reference_recognizer"
    )
    
    # 3. Financial Figures Pattern
    financial_pattern = [
        {"LOWER": {"IN": ["$", "usd", "eur", "gbp", "aud"]}},
        {"LIKE_NUM": True},
        {"LOWER": {"IN": ["million", "billion", "thousand", "k", "m", "b", "t"]}, "OP": "?"}
    ]
    
    financial_def = CustomPatternDefinition(
        entity_type="FINANCIAL_FIGURE",
        patterns=[financial_pattern],
        context=["amount", "cost", "price", "value", "budget", "revenue", "profit"],
        name="financial_figure_recognizer"
    )
    
    # 4. Date Pattern (using linguistic features)
    date_patterns = [
        # US format: Month Day, Year
        [
            {"POS": "PROPN"},  # Month name
            {"SHAPE": "dd"},  # Day as digits
            {"LOWER": ","},
            {"SHAPE": "dddd"}  # Year as 4 digits
        ],
        # European format: Day Month Year
        [
            {"SHAPE": "dd"},  # Day as digits
            {"POS": "PROPN"},  # Month name
            {"SHAPE": "dddd"}  # Year as 4 digits
        ]
    ]
    
    date_def = CustomPatternDefinition(
        entity_type="DATE_REFERENCE",
        patterns=date_patterns,
        context=["dated", "date", "on", "scheduled", "due", "by"],
        name="date_reference_recognizer"
    )
    
    # Create a comprehensive analyzer with all patterns
    analyzer = EnhancedAnalyzer()
    analyzer.add_pattern(person_role_def)
    analyzer.add_pattern(contract_pattern)
    analyzer.add_pattern(financial_def)
    analyzer.add_pattern(date_def)
    
    # Create an anonymizer
    anonymizer = EnhancedAnonymizer(analyzer=analyzer)
    
    # Define custom operators for each entity type
    operators = {
        "PERSON_ROLE": "replace",
        "CONTRACT_REFERENCE": "mask",
        "FINANCIAL_FIGURE": "redact",
        "DATE_REFERENCE": "hash"
    }
    
    # Test with a comprehensive sample text
    sample_text = """
    CONFIDENTIAL MEMO
    
    John Smith is our Chief Financial Officer responsible for the Q3 financial review.
    
    Contract #CT-2023-1234 was signed on January 15, 2023, with a total value of $5.2 million.
    The agreement supersedes Contract #CT-2022-5678 dated 25 March 2022.
    
    Sarah Johnson is the Project Manager assigned to implement the new system by September 30, 2023.
    
    Budget allocation: $750,000 for the first phase, with potential additional funding of $1.2 million
    for phase two pending board approval.
    
    Next review scheduled for December 10, 2023.
    """
    
    # Analyze the text
    analysis_results = analyzer.analyze(sample_text)
    print("Analysis Results:")
    print_results(analysis_results)
    
    # Anonymize the text
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
    example_1_token_based_patterns()
    example_2_phrase_based_patterns()
    example_3_complex_linguistic_patterns()
    example_4_contextual_patterns()
    example_5_entity_relationship_patterns()
    example_6_auto_generating_patterns()
    example_7_complete_advanced_workflow()


if __name__ == "__main__":
    print("Allyanonimiser Advanced spaCy Pattern Examples")
    print("This script demonstrates advanced uses of spaCy patterns for complex entity recognition.")
    print("Each example can be run individually or you can run all examples.")
    
    run_all_examples()