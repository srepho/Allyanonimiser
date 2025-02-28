from allyanonimiser import PatternRegistry, CustomPatternDefinition
import os

try:
    # Create a registry
    registry = PatternRegistry()
    
    # Register patterns
    registry.register_pattern(CustomPatternDefinition(
        entity_type="BROKER_CODE",
        patterns=["BRK-[0-9]{4}"],
        context=["broker", "agent", "representative"],
        name="broker_code_recognizer"
    ))
    print('Pattern registered successfully')
    
    # Export patterns
    output_file = "insurance_patterns.json"
    registry.export_patterns(output_file)
    print(f'Patterns exported to {output_file}')
    
    # Later, in another application
    new_registry = PatternRegistry()
    new_registry.import_patterns(output_file)
    print('Patterns imported successfully')
    
    # Clean up
    os.remove(output_file)
except Exception as e:
    print(f'Error: {e}')
