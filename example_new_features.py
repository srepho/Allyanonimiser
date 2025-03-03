#!/usr/bin/env python
"""
Example script demonstrating the new features in version 1.0.0:
1. Preserving postcodes when anonymizing addresses
2. Converting dates of birth to age brackets 
"""

from allyanonimiser import create_analyzer, create_allyanonimiser, EnhancedAnonymizer
import pandas as pd

def main():
    # Create analyzer and anonymizer
    analyzer = create_analyzer()
    anonymizer = EnhancedAnonymizer(analyzer=analyzer)

    # Example with address and postcode
    address_text = "Customer lives at 123 Main Street, Sydney, NSW 2000. Contact at 0411222333."
    
    # Regular anonymization
    result1 = anonymizer.anonymize(address_text)
    print("Regular anonymization:")
    print(result1['text'])
    print()
    
    # With postcode preservation
    result2 = anonymizer.anonymize(address_text, keep_postcode=True)
    print("Anonymization with postcode preservation:")
    print(result2['text'])
    print()

    # Example with date of birth
    dob_text = "Patient: John Smith, DOB: 15/09/1980, Medicare: 1234 56789 0"
    
    # With age bracket operator
    operators = {
        "DATE_OF_BIRTH": "age_bracket"
    }
    
    result3 = anonymizer.anonymize(dob_text, operators=operators)
    print("Anonymization with age brackets:")
    print(result3['text'])
    print()
    
    # With age bracket operator and custom bracket size
    result4 = anonymizer.anonymize(dob_text, operators=operators, age_bracket_size=10)
    print("Anonymization with larger age brackets (10 years):")
    print(result4['text'])
    print()

    # Example using the Allyanonimiser unified interface
    ally = create_allyanonimiser()
    
    # Create a simple DataFrame for testing
    df = pd.DataFrame({
        'id': range(1, 5),
        'description': [
            "Patient John Smith, DOB: 15/09/1985, lives at 42 Park Avenue, Melbourne VIC 3000.",
            "Claim for Jane Doe, born 22/01/1990, residing at 67 Queen Street, Sydney NSW 2000.",
            "Customer Bob Johnson (DOB 30/11/1975) from 89 Main Road, Perth WA 6000 called about policy POL123456.",
            "Mary Wilson, Age: 42, Address: 123 Collins Street, Brisbane QLD 4000, Phone: 0412345678."
        ]
    })
    
    # Process the DataFrame with custom operators
    operators = {
        "DATE_OF_BIRTH": "age_bracket",
        "PERSON": "replace",
        "AU_ADDRESS": "mask",
        "AU_PHONE": "redact"
    }
    
    # Process the DataFrame with the new features
    result_df = ally.anonymize_dataframe(
        df, 
        'description', 
        operators=operators,
        age_bracket_size=5,
        keep_postcode=True
    )
    
    print("DataFrame processing with new features:")
    for i, row in result_df.iterrows():
        print(f"Row {i+1}: {row['description_anonymized']}")

if __name__ == "__main__":
    main()