"""
Example script showing how to use the Allyanonimiser package with absolute imports.
This demonstrates the correct way to import the package when installed via pip.
"""

# Import the main components
import allyanonimiser

# Create an analyzer with Australian and insurance patterns pre-configured
analyzer = allyanonimiser.create_au_insurance_analyzer()

# Analyze text
text = "Please reference your policy AU-12345678 for claims related to your vehicle rego XYZ123."
results = analyzer.analyze(text, language="en")

# Print results
print("Detected entities:")
for result in results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")

# Create a unified interface for processing mixed content
anonymizer = allyanonimiser.EnhancedAnonymizer(analyzer=analyzer)
interface = allyanonimiser.Allyanonimiser(analyzer=analyzer, anonymizer=anonymizer)

# Sample text to process
claim_note = """
Claim Details:
Spoke with the insured John Smith (TFN: 123 456 789) regarding damage to his vehicle ABC123.
The incident occurred on 14/05/2023 when another vehicle collided with the rear of his car.
Policy number: POL-987654321

Vehicle Details:
Toyota Corolla 2020
VIN: 1HGCM82633A123456
Registration: ABC123

Contact Information:
Phone: 0412 345 678
Email: john.smith@example.com
Address: 123 Main St, Sydney NSW 2000
"""

# Process using the unified interface with automatic content type detection
results = interface.process(
    text=claim_note,  # Auto-detects content type if not specified
    anonymize=True
)

# Show results
print("\nProcessed claim note:")
print(f"Found {len(results['entities'])} entities")
print("\nAnonymized text:")
print(results["anonymized_text"])