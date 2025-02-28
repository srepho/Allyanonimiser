"""
Example demonstrating custom pattern creation and usage in Allyanonimiser.
"""

import os
from allyanonimiser import (
    create_allyanonimiser,
    CustomPatternDefinition
)
from allyanonimiser.validators import test_pattern_against_examples

def demo_basic_custom_pattern():
    """Demonstrate basic custom pattern creation and usage."""
    print("Basic Custom Pattern Example")
    print("="*80)
    
    # Create the Allyanonimiser instance
    ally = create_allyanonimiser()
    
    # Create a custom pattern for detecting invoice numbers
    invoice_pattern = CustomPatternDefinition(
        entity_type="INVOICE_NUMBER",
        patterns=[
            r"INV-\d{6}",                           # INV-123456
            r"INVOICE[#:\-\s]+([A-Z0-9-]{6,12})"    # INVOICE: ABC123456
        ],
        context=["invoice", "bill", "payment", "due"],
        name="Invoice Number Pattern",
        description="Detects invoice numbers in various formats"
    )
    
    # Add the custom pattern to the analyzer
    ally.add_pattern(invoice_pattern)
    
    # Text containing an invoice number
    text = """
    Please find attached invoice INV-245789 for your recent purchase.
    Payment is due within 30 days.
    
    The invoice details are as follows:
    - Purchase Date: 2023-05-15
    - Invoice: INV-245789
    - Amount: $1,234.56
    
    For any queries, please contact billing@example.com or call 0412 345 678.
    """
    
    # Analyze the text
    results = ally.analyze(text)
    
    # Display detected entities
    print("\nDetected Entities:")
    for result in results:
        print(f"  - Type: {result.entity_type}")
        print(f"    Text: {result.text}")
        print(f"    Confidence: {result.score:.2f}")
        print()
    
    # Get explanation for a detected entity
    invoice_entities = [r for r in results if r.entity_type == "INVOICE_NUMBER"]
    if invoice_entities:
        explanation = ally.explain_entity(text, {
            "entity_type": invoice_entities[0].entity_type,
            "start": invoice_entities[0].start,
            "end": invoice_entities[0].end,
            "text": invoice_entities[0].text,
            "score": invoice_entities[0].score
        })
        
        print("\nEntity Explanation:")
        print(f"  Entity Type: {explanation['entity_type']}")
        print(f"  Matched Text: {explanation['matched_text']}")
        print(f"  Confidence: {explanation['confidence_score']:.2f}")
        print(f"  Description: {explanation['metadata']['description']}")
        
        if "match_details" in explanation and "matching_patterns" in explanation["match_details"]:
            print("\n  Matching Pattern(s):")
            for pattern in explanation["match_details"]["matching_patterns"]:
                print(f"    - {pattern}")

def demo_pattern_from_examples():
    """Demonstrate creating patterns from examples."""
    print("\n\nPattern Generation from Examples")
    print("="*80)
    
    # Define example strings for membership IDs
    membership_examples = [
        "MEM-12345", 
        "MEM-78901", 
        "MEM-A12B34",
        "MEMBER-12345"
    ]
    
    # Test using different generalization levels
    print("Testing different generalization levels:")
    
    for level in ["none", "low", "medium", "high"]:
        # Generate a test pattern
        from allyanonimiser.utils.spacy_helpers import create_regex_from_examples
        regex = create_regex_from_examples(membership_examples, generalization_level=level)
        
        print(f"\nGeneralization level: {level}")
        print(f"Generated pattern: {regex}")
        
        # Test the pattern against examples
        test_examples = membership_examples + ["MEM-56789", "MEM-C45D67"]
        negative_examples = ["MEMO-12345", "12345-MEM", "Policy-12345"]
        
        try:
            results = test_pattern_against_examples(regex, test_examples, negative_examples)
            
            if isinstance(results, dict) and 'positive_matches' in results:
                print(f"Matches all positive examples: {len(results['positive_matches']) == len(test_examples)}")
                print(f"Precision: {results['metrics']['precision']:.2f}")
                print(f"Recall: {results['metrics']['recall']:.2f}")
            else:
                print(f"Pattern validation result: {results}")
        except Exception as e:
            print(f"Pattern test error: {e}")
            # Continue to next example
    
    # Now create a pattern with the Allyanonimiser interface
    print("\nCreating and registering a pattern from examples:")
    ally = create_allyanonimiser()
    
    # Create and add the pattern
    pattern = ally.create_pattern_from_examples(
        entity_type="MEMBERSHIP_NUMBER",
        examples=membership_examples,
        context=["member", "membership", "subscriber"],
        name="Membership Number Pattern",
        generalization_level="medium"
    )
    
    print(f"Created pattern: {pattern.patterns[0]}")
    
    # Test with text containing membership numbers
    text = """
    We've updated your membership details for member MEM-23456.
    Your subscription benefits will continue through 2023.
    
    For reference, your membership numbers are:
    Primary: MEM-23456
    Secondary: MEMBER-78901
    Family Add-on: MEM-A12B34
    
    For any questions about your membership benefits, please contact us.
    """
    
    # Analyze with the new pattern
    results = ally.analyze(text)
    
    # Filter for membership numbers
    membership_entities = [r for r in results if r.entity_type == "MEMBERSHIP_NUMBER"]
    
    print(f"\nDetected {len(membership_entities)} membership numbers:")
    for entity in membership_entities:
        print(f"  - {entity.text} (Score: {entity.score:.2f})")

def demo_save_load_patterns():
    """Demonstrate saving and loading patterns."""
    print("\n\nSaving and Loading Patterns")
    print("="*80)
    
    # Create allyanonimiser with custom patterns
    ally = create_allyanonimiser()
    
    # Add custom patterns
    patterns = [
        CustomPatternDefinition(
            entity_type="RESERVATION_NUMBER",
            patterns=[r"RES-\d{6}", r"BOOKING-[A-Z]{2}\d{4}"],
            context=["reservation", "booking", "hotel", "flight"],
            name="Reservation Number Pattern"
        ),
        CustomPatternDefinition(
            entity_type="CASE_ID",
            patterns=[r"CASE-\d{5}", r"SUPPORT-\d{6}"],
            context=["case", "support", "ticket", "issue"],
            name="Support Case ID Pattern"
        )
    ]
    
    for pattern in patterns:
        ally.add_pattern(pattern)
    
    # Create a directory for storing patterns
    os.makedirs("custom_patterns", exist_ok=True)
    
    # Save patterns to file
    patterns_file = "custom_patterns/my_patterns.json"
    ally.save_patterns(patterns_file)
    print(f"Saved patterns to {patterns_file}")
    
    # Create a new instance and load patterns
    new_ally = create_allyanonimiser()
    
    # Check entity types before loading
    print("\nEntity types before loading patterns:")
    print(", ".join(sorted(new_ally.get_available_entity_types().keys())))
    
    # Load patterns
    count = new_ally.load_patterns(patterns_file)
    print(f"\nLoaded {count} patterns from file")
    
    # Check entity types after loading
    print("\nEntity types after loading patterns:")
    all_types = sorted(new_ally.get_available_entity_types().keys())
    print(", ".join(all_types))
    
    # Verify our custom types were loaded
    custom_types = ["RESERVATION_NUMBER", "CASE_ID"]
    for custom_type in custom_types:
        if custom_type in all_types:
            print(f"  ✓ Found {custom_type}")
    
    # Test with text containing our custom entities
    text = """
    Your reservation RES-123456 has been confirmed for June 15-20, 2023.
    
    For any issues, please reference support case CASE-12345 in your communications.
    """
    
    results = new_ally.analyze(text)
    
    print("\nDetected entities in text:")
    for result in results:
        print(f"  - {result.entity_type}: {result.text} (Score: {result.score:.2f})")

def demo_combining_patterns_with_spacy():
    """Demonstrate combining custom patterns with spaCy NER."""
    print("\n\nCombining Custom Patterns with spaCy NER")
    print("="*80)
    
    # Create allyanonimiser
    ally = create_allyanonimiser()
    
    # Add a custom pattern for project IDs
    project_pattern = CustomPatternDefinition(
        entity_type="PROJECT_ID",
        patterns=[r"PRJ-\d{4}"],
        context=["project", "assignment", "task"],
        name="Project ID Pattern"
    )
    
    ally.add_pattern(project_pattern)
    
    # Text with both custom entities and standard entities
    text = """
    Project PRJ-1234 has been assigned to Sarah Johnson.
    
    The project team will meet on February 15, 2023 at our Melbourne office.
    
    Please contact Sarah at sarah.johnson@example.com if you have any questions.
    
    Regards,
    
    Michael Zhang
    Project Manager
    Australian Insurance Group
    """
    
    # Analyze with both custom patterns and spaCy NER
    results = ally.analyze(text)
    
    # Group by source
    custom_entities = [r for r in results if r.entity_type == "PROJECT_ID"]
    spacy_entities = [r for r in results if r.entity_type in ["PERSON", "DATE", "ORGANIZATION", "LOCATION"]]
    other_entities = [r for r in results if r not in custom_entities and r not in spacy_entities]
    
    print("\nCustom pattern entities:")
    for entity in custom_entities:
        print(f"  - {entity.entity_type}: {entity.text} (Score: {entity.score:.2f})")
    
    print("\nspaCy NER entities:")
    for entity in spacy_entities:
        print(f"  - {entity.entity_type}: {entity.text} (Score: {entity.score:.2f})")
    
    print("\nOther detected entities:")
    for entity in other_entities:
        print(f"  - {entity.entity_type}: {entity.text} (Score: {entity.score:.2f})")

if __name__ == "__main__":
    demo_basic_custom_pattern()
    demo_pattern_from_examples()
    demo_save_load_patterns()
    demo_combining_patterns_with_spacy()