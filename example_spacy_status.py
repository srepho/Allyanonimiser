#!/usr/bin/env python3
"""
Example script demonstrating spaCy status checking in Allyanonimiser.
"""

from allyanonimiser import create_allyanonimiser

def main():
    print("Allyanonimiser - spaCy Status Check Example")
    print("=" * 50)
    
    # Create an instance
    ally = create_allyanonimiser()
    
    # Check spaCy status
    status = ally.check_spacy_status()
    
    print("\nspaCy Status Information:")
    print(f"  Is Loaded: {'Yes' if status['is_loaded'] else 'No'}")
    print(f"  Model Name: {status['model_name'] or 'N/A'}")
    print(f"  Has NER: {'Yes' if status['has_ner'] else 'No'}")
    
    if status['is_loaded']:
        print(f"\nEntities detected by spaCy:")
        for entity_type in status['entity_types']:
            print(f"  - {entity_type}")
    else:
        print(f"\nEntities requiring spaCy (currently unavailable):")
        for entity_type in status['entity_types']:
            print(f"  - {entity_type}")
    
    print(f"\nRecommendation:")
    print(status['recommendation'])
    
    # Demonstrate the difference
    print("\n" + "=" * 50)
    print("Testing Detection Capabilities:")
    
    test_text = """
    John Smith's email is john.smith@example.com and his phone is 0412 345 678.
    He works at Insurance Australia Group and his policy number is POL-12345678.
    """
    
    results = ally.analyze(test_text)
    
    print(f"\nDetected {len(results)} entities:")
    for result in results:
        print(f"  - {result.entity_type}: {result.text} (confidence: {result.score:.2f})")
    
    # Show what patterns work without spaCy
    print("\nPattern-based detection (works without spaCy):")
    pattern_types = ['EMAIL_ADDRESS', 'PHONE_NUMBER', 'AU_PHONE', 'INSURANCE_POLICY_NUMBER']
    for ptype in pattern_types:
        count = sum(1 for r in results if r.entity_type == ptype)
        if count > 0:
            print(f"  ✓ {ptype}: {count} found")
    
    # Show what requires spaCy
    if status['is_loaded'] and status['has_ner']:
        print("\nNER-based detection (requires spaCy):")
        ner_types = ['PERSON', 'ORGANIZATION']
        for ntype in ner_types:
            count = sum(1 for r in results if r.entity_type == ntype)
            if count > 0:
                print(f"  ✓ {ntype}: {count} found")

if __name__ == "__main__":
    main()