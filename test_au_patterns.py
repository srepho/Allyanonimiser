from allyanonimiser.patterns import get_au_pattern_definitions

try:
    # Get Australian pattern definitions
    au_patterns = get_au_pattern_definitions()
    
    # Print the pattern types
    print("Australian pattern types:")
    for pattern in au_patterns:
        print(f"- {pattern.entity_type}")
except Exception as e:
    print(f'Error: {e}')
