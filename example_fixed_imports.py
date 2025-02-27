"""
Example showing how to use the allyanonimiser package after installing from PyPI.

This example demonstrates using absolute imports, which is how you
should import the package when installed via pip.

Usage:
    1. Install the package: pip install allyanonimiser==0.1.2
    2. Run this script: python example_fixed_imports.py
"""

import allyanonimiser

def main():
    """Example usage of the Allyanonimiser package."""
    print(f"Using allyanonimiser version {allyanonimiser.__version__}")
    
    # Create an Allyanonimiser instance with all patterns pre-configured
    ally = allyanonimiser.create_allyanonimiser()
    
    # Example text with PII
    text = "Patient John Smith (DOB: 01/02/1980) with Medicare number 1234-56789-0 " \
           "and policy number POL123456 called regarding his claim."
    
    # In a real application, you would use ally.analyze(text) and ally.anonymize(text)
    # Since this is a stub implementation for testing, we just print the text
    print("\nExample text:")
    print(text)
    
    # Use the ClaimNotesAnalyzer directly
    # This was previously causing circular import errors in v0.1.0/v0.1.1
    claim_analyzer = allyanonimiser.ClaimNotesAnalyzer()
    
    # Use the analyze_claim_note function
    # This was also involved in the circular import problem
    result = allyanonimiser.analyze_claim_note(text)
    
    print("\nPackage imported and used successfully!")
    print("All imports working correctly, circular import issue has been fixed.")

if __name__ == "__main__":
    main()