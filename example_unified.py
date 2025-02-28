"""
Example of using the unified Allyanonimiser interface.
"""

from allyanonimiser import (
    create_allyanonimiser,
    CustomPatternDefinition
)

def example_unified_interface():
    """Demonstrate using the unified analyzer interface."""
    print("Allyanonimiser - Unified Interface Example")
    print("="*80)
    
    # Create a single unified analyzer
    allyanonimiser = create_allyanonimiser()
    
    # Sample text to analyze
    text = """
    Claim #: CL-12345678
    Customer: John Smith
    Policy Number: POL-987654
    
    Mr. Smith reported an accident on 15/07/2023. His vehicle (Registration: ABC123) 
    was involved in a collision at George St, Sydney. His contact details are 
    0412 345 678 and john.smith@example.com.
    
    The customer's TFN (123 456 789) and Medicare number (2345 67890 1) 
    were verified for identity purposes.
    """
    
    print("Original Text:")
    print("-"*80)
    print(text)
    print("-"*80)
    
    # 1. Basic analysis with all entities
    print("\n1. Basic Analysis (All Entity Types)")
    results = allyanonimiser.analyze(text)
    
    # Display detected entities
    print("\nDetected Entities:")
    for result in results:
        print(f"  - {result.entity_type}: {result.text} (Score: {result.score:.2f})")
    
    # 2. Filtering entity types
    print("\n2. Filtered Analysis (Only Specific Entity Types)")
    selected_entities = ["PERSON", "AU_PHONE", "EMAIL_ADDRESS", "INSURANCE_CLAIM_NUMBER"]
    filtered_results = allyanonimiser.analyze(text, active_entity_types=selected_entities)
    
    print("\nFiltered Entities:")
    for result in filtered_results:
        print(f"  - {result.entity_type}: {result.text} (Score: {result.score:.2f})")
    
    # 3. Score adjustment
    print("\n3. Analysis with Score Adjustment")
    # Boost the score of TFN and Medicare detections
    score_adjustments = {
        "AU_TFN": 0.1,        # Increase TFN detection confidence
        "AU_MEDICARE": 0.1,   # Increase Medicare detection confidence
        "PERSON": -0.1,       # Slightly reduce PERSON detection confidence
    }
    
    adjusted_results = allyanonimiser.analyze(
        text, 
        score_adjustment=score_adjustments,
        min_score_threshold=0.8  # Only show entities with confidence >= 0.8
    )
    
    print("\nAdjusted Entities (min score 0.8):")
    for result in adjusted_results:
        print(f"  - {result.entity_type}: {result.text} (Score: {result.score:.2f})")
    
    # 4. Entity explanation
    print("\n4. Entity Explanation")
    # Explain a detected entity (e.g., TFN)
    tfn_entities = [r for r in results if r.entity_type == "AU_TFN"]
    if tfn_entities:
        tfn = tfn_entities[0]
        explanation = allyanonimiser.explain_entity(text, {
            "entity_type": tfn.entity_type,
            "start": tfn.start,
            "end": tfn.end,
            "text": tfn.text,
            "score": tfn.score
        })
        
        print("\nExplanation for TFN detection:")
        print(f"  Entity Type: {explanation['entity_type']}")
        print(f"  Matched Text: {explanation['matched_text']}")
        print(f"  Confidence: {explanation['confidence_score']:.2f}")
        print(f"  Description: {explanation['metadata']['description']}")
        
        if "match_details" in explanation and "matching_patterns" in explanation["match_details"]:
            print("\n  Matching Pattern(s):")
            for pattern in explanation["match_details"]["matching_patterns"]:
                print(f"    - {pattern}")
    
    # 5. Custom pattern
    print("\n5. Adding Custom Pattern")
    # Create a custom pattern for order numbers
    order_pattern = CustomPatternDefinition(
        entity_type="ORDER_NUMBER",
        patterns=[r"ORD-\d{6}", r"Order\s+#\s*([A-Z0-9-]{8,12})"],
        context=["order", "purchase", "transaction"],
        name="Order Number Pattern"
    )
    
    # Add the pattern to the analyzer
    allyanonimiser.add_pattern(order_pattern)
    
    # Test with text containing an order number
    order_text = "Your order ORD-123456 has been processed and will ship by Friday."
    order_results = allyanonimiser.analyze(order_text)
    
    print("\nAnalysis with Custom Pattern:")
    print(f"Text: {order_text}")
    print("\nDetected Entities:")
    for result in order_results:
        print(f"  - {result.entity_type}: {result.text} (Score: {result.score:.2f})")
    
    # 6. Using available entity types information
    print("\n6. Available Entity Types")
    entity_types = allyanonimiser.get_available_entity_types()
    
    print(f"\nTotal supported entity types: {len(entity_types)}")
    print("\nSample entity types and their metadata:")
    
    # Display a subset of entity types
    sample_types = ["PERSON", "AU_TFN", "AU_MEDICARE", "INSURANCE_POLICY_NUMBER", "ORDER_NUMBER"]
    for entity_type in sample_types:
        if entity_type in entity_types:
            metadata = entity_types[entity_type]
            print(f"\n  {entity_type}:")
            print(f"    Description: {metadata['description']}")
            print(f"    Example: {metadata['example']}")
            print(f"    Source: {metadata['source']}")
    
    # 7. One-step processing
    print("\n7. One-step Process (Analysis + Anonymization)")
    
    # Process the text in one step
    processed = allyanonimiser.process(text)
    
    # Show anonymized text
    print("\nAnonymized Text:")
    print("-"*80)
    print(processed["anonymized"])
    print("-"*80)
    
    # Show structured data extracted from entities
    print("\nStructured Data Extracted:")
    for key, value in processed["structured_data"].items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    example_unified_interface()