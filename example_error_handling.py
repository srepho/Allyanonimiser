"""
Example script demonstrating error handling with the Allyanonimiser API.
"""
from allyanonimiser import create_allyanonimiser, AnalysisConfig, AnonymizationConfig

# Create an Allyanonimiser instance
ally = create_allyanonimiser()

print("=== Example 1: Handling validation errors in manage_patterns ===")
try:
    # Attempt to use manage_patterns without required parameters
    ally.manage_patterns(
        action="create_from_examples",
        # Missing entity_type and examples
    )
except ValueError as e:
    print(f"Caught expected error: {e}")

# Now with proper parameters
try:
    # Proper pattern creation
    pattern = ally.manage_patterns(
        action="create_from_examples",
        entity_type="TEST_ID",
        examples=["TEST-123", "TEST-456"]
    )
    print(f"Successfully created pattern with entity type: {pattern.entity_type}")
except ValueError as e:
    print(f"Unexpected error: {e}")

print("\n=== Example 2: Handling errors in manage_acronyms ===")
try:
    # Attempt to use an invalid action
    ally.manage_acronyms(
        action="invalid_action",
        data={"TPD": "Total and Permanent Disability"}
    )
except ValueError as e:
    print(f"Caught expected error: {e}")

# Now with proper action
try:
    # Add acronyms with proper parameters
    ally.manage_acronyms(
        action="add",
        data={"TPD": "Total and Permanent Disability"}
    )
    print("Successfully added acronym")
    
    # Try to import from CSV without required path
    ally.manage_acronyms(
        action="import"
        # Missing csv_path
    )
except ValueError as e:
    print(f"Caught expected error: {e}")

print("\n=== Example 3: Handling configuration errors ===")
# Invalid configuration (passing an invalid operator)
text = "John Smith contacted us about policy POL-123456."
try:
    # Define configuration with invalid operator
    anonymization_config = AnonymizationConfig(
        operators={
            "PERSON": "invalid_operator"  # Invalid operator type
        }
    )
    
    # Try to use the invalid configuration
    result = ally.process(
        text=text,
        anonymization_config=anonymization_config
    )
except Exception as e:
    print(f"Caught operator error: {e}")

print("\n=== Example 4: Handling DataFrame errors ===")
try:
    # Missing required parameters for DataFrame processing
    ally.process_dataframe(
        df=None,  # Missing DataFrame
        operation="detect"
        # Missing column parameter
    )
except ValueError as e:
    print(f"Caught DataFrame error: {e}")

print("\n=== Example 5: Graceful error handling with try/except blocks ===")
# Function demonstrating proper error handling patterns
def process_with_error_handling(text, entity_types=None):
    try:
        # Create configs with validation
        if entity_types and not isinstance(entity_types, list):
            raise ValueError("entity_types must be a list")
            
        analysis_config = AnalysisConfig(
            active_entity_types=entity_types,
            min_score_threshold=0.7
        )
        
        # Process the text
        return ally.process(text, analysis_config=analysis_config)
    except ValueError as e:
        print(f"Configuration error: {e}")
        # Use default configuration as fallback
        return ally.process(text)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Test with invalid configuration (should use fallback)
result = process_with_error_handling("John Smith sent an email", entity_types="PERSON")
if result:
    print("Successfully processed with fallback configuration")
    
# Test with valid configuration
result = process_with_error_handling("John Smith sent an email", entity_types=["PERSON"])
if result:
    print("Successfully processed with provided configuration")