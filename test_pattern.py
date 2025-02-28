from allyanonimiser import CustomPatternDefinition, create_pattern_from_examples, create_au_insurance_analyzer

try:
    # Create a custom pattern for internal reference numbers
    internal_ref_examples = [
        "Internal reference: REF-12345",
        "Ref Number: REF-98765",
        "Reference: REF-55555"
    ]
    
    pattern = create_pattern_from_examples(
        entity_type="INTERNAL_REFERENCE",
        examples=internal_ref_examples,
        context=["internal", "reference", "ref"],
        pattern_type="regex"
    )
    print('Pattern created successfully')
    
    # Add to an existing analyzer
    analyzer = create_au_insurance_analyzer()
    analyzer.add_pattern(pattern)
    print('Pattern added to analyzer successfully')
except Exception as e:
    print(f'Error: {e}')
