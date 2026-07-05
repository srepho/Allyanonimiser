"""
Comprehensive test suite for robust entity detection.
"""

import pytest
import re
from allyanonimiser import create_allyanonimiser
from allyanonimiser.core.validators import EntityValidator
from allyanonimiser.core.context_analyzer import ContextAnalyzer


class TestRobustDetection:
    """Test robust detection improvements."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return create_allyanonimiser()
    
    def test_date_false_positives(self, analyzer):
        """Test that common date false positives are correctly handled."""
        # State + postcode should not be detected as dates
        test_cases = [
            ("NSW 2000", []),
            ("VIC 3000", [("NUMBER", "3000")]),
            ("QLD 4000", [("NUMBER", "4000")]),
            ("Lives in NSW 2000", [("NUMBER", "2000")])
        ]
        
        for text, expected in test_cases:
            results = analyzer.analyze(text)
            detected = [(r.entity_type, text[r.start:r.end]) for r in results if r.entity_type == 'DATE']
            
            # Check no DATE entities were detected
            assert len(detected) == 0, f"False positive DATE detected in '{text}': {detected}"
    
    def test_phone_number_detection(self, analyzer):
        """Test improved phone number detection."""
        test_cases = [
            ("0412 345 678", "AU_PHONE", True),
            ("(03) 9876-5432", "AU_PHONE", True),
            ("0423 456 789", "AU_PHONE", True),
            ("1300 123 456", "AU_PHONE", True),
            ("131 450", None, False),  # Too short for AU_PHONE
        ]
        
        for text, expected_type, should_detect in test_cases:
            results = analyzer.analyze(text)
            
            if should_detect:
                phone_entities = [r for r in results if r.entity_type == expected_type]
                assert len(phone_entities) > 0, f"Failed to detect phone number: {text}"
            else:
                phone_entities = [r for r in results if r.entity_type == 'AU_PHONE']
                assert len(phone_entities) == 0, f"False positive phone detected: {text}"
    
    def test_medicare_number_validation(self, analyzer):
        """Test Medicare number detection and validation."""
        test_cases = [
            # Valid Medicare numbers (starting with 2-6)
            ("Medicare: 2123 45678 1", True),
            ("Medicare: 3123 45678 1", True),
            ("Medicare: 4123 45678 1", True),
            ("Medicare: 5123 45678 1", True),
            ("Medicare: 6123 45678 1", True),
            # Invalid Medicare numbers
            ("Medicare: 1123 45678 1", False),  # Starts with 1
            ("Medicare: 7123 45678 1", False),  # Starts with 7
            # IRN 0 fails validation, but the explicit "Medicare:" label
            # overrides it (label-context rule): a mistyped real Medicare
            # number must still be masked. Leaking beats over-masking here.
            ("Medicare: 2123 45678 0", True),
        ]
        
        for text, should_be_valid in test_cases:
            results = analyzer.analyze(text)
            medicare_entities = [r for r in results if r.entity_type == 'AU_MEDICARE']

            if should_be_valid:
                assert medicare_entities, f"Failed to detect valid Medicare: {text}"
            else:
                assert not medicare_entities, (
                    f"Should not have detected invalid Medicare: {text} "
                    f"(found {[r.text for r in medicare_entities]})"
                )
    
    def test_context_aware_detection(self, analyzer):
        """Test context-aware entity detection."""
        test_cases = [
            # Context should help identify entities
            # Use checksum-valid examples so detection is not filtered:
            # 123456782 is a valid TFN, 51824753556 is the ATO test ABN.
            ("TFN: 123 456 782", "AU_TFN"),
            ("ABN: 51 824 753 556", "AU_ABN"),
            ("Policy number POL-12345678", "INSURANCE_POLICY_NUMBER"),
            ("Claim number CL-98765432", "INSURANCE_CLAIM_NUMBER"),
            ("Medicare number 2123 45678 1", "AU_MEDICARE"),
        ]
        
        for text, expected_type in test_cases:
            results = analyzer.analyze(text)
            entity_types = [r.entity_type for r in results]
            
            assert expected_type in entity_types, \
                f"Failed to detect {expected_type} in context: '{text}'. Found: {entity_types}"
    
    def test_number_word_false_positives(self, analyzer):
        """Test that number words are not detected as NUMBER entities."""
        test_cases = [
            "quarter panel",
            "half price",
            "third party"
        ]
        
        for text in test_cases:
            results = analyzer.analyze(text)
            number_entities = [r for r in results if r.entity_type == 'NUMBER']
            
            assert len(number_entities) == 0, \
                f"False positive NUMBER detected in '{text}': {[text[r.start:r.end] for r in number_entities]}"
    
    def test_street_name_handling(self, analyzer):
        """Test that street names are not incorrectly detected as PERSON."""
        test_cases = [
            "456 Queen St",
            "Lives on Main Street",
            "Corner of King Rd and Queen St"
        ]
        
        for text in test_cases:
            results = analyzer.analyze(text)
            # Should not detect street names as PERSON
            person_entities = [r for r in results if r.entity_type == 'PERSON' 
                             and any(suffix in text[r.start:r.end].lower() 
                                   for suffix in [' st', ' street', ' rd', ' road'])]
            
            assert len(person_entities) == 0, \
                f"Street name incorrectly detected as PERSON in '{text}'"
    
    def test_au_postcode_no_false_positive_on_years_or_amounts(self, analyzer):
        """AU_POSTCODE must not fire on bare 4-digit numbers (years, amounts,
        case numbers). Previously 'The incident occurred on 15/03/2023' tagged
        '2023' as AU_POSTCODE and '8500 dollars' matched too, leaking into
        ADDRESS precision on real AU eval data."""
        negatives = [
            "The incident occurred on 15/03/2023 at 10:30am.",
            "The claim amount was 8500 dollars.",
            "In 2023 the policy was renewed.",
            "Case reference 1234 was filed.",
        ]
        for text in negatives:
            results = analyzer.analyze(text)
            pc = [r for r in results if r.entity_type == "AU_POSTCODE"]
            assert not pc, (
                f"AU_POSTCODE FP in {text!r}: "
                f"{[(r.start, r.end, text[r.start:r.end]) for r in pc]}"
            )

    def test_au_postcode_matches_with_state_or_label(self, analyzer):
        """AU_POSTCODE must still match when state abbrev or 'postcode' label
        precedes the 4-digit code. Includes label variants ('post code',
        'postal code') and mixed case."""
        positives = [
            "Send mail to Sydney NSW 2000.",
            "Office in Perth WA 6000.",
            "Send to postcode 3000.",
            "42 Queen St, Sydney NSW 2000.",
            "Post code 3000",
            "postal code 3000",
            "Postal Code 3000",
        ]
        for text in positives:
            results = analyzer.analyze(text)
            pc = [r for r in results if r.entity_type == "AU_POSTCODE"]
            assert pc, f"AU_POSTCODE missed in {text!r}"

    def test_au_address_no_false_positive_on_narrative(self, analyzer):
        """AU_ADDRESS must not absorb narrative prose that happens to contain
        year + street-suffix-lookalike words ('Court', 'Place', 'Drive'). This
        was a regression surfaced by running Allyanonimiser over ECHR legal text
        where spans like '2007 the Court decided to give notice of the application
        to the Government' were being tagged as AU_ADDRESS (74 chars)."""
        negatives = [
            "On 15 May 2007 the Court decided to give notice of the application to the Government.",
            "In 1997 the General Directorate of National Roads and Highways started construction.",
            "On 3 November 2000 the Tunceli Court asked the Forensic Medicine Institute to clarify.",
            "The case concerns events that took place in the Drive of the Prime Minister in 1998.",
            "The applicant complained that 42 days after his release he was re-arrested.",
        ]
        for text in negatives:
            results = analyzer.analyze(text)
            addr = [r for r in results if r.entity_type == "AU_ADDRESS"]
            assert not addr, (
                f"AU_ADDRESS false positive in {text!r}: "
                f"{[(r.start, r.end, text[r.start:r.end]) for r in addr]}"
            )

    def test_au_address_still_matches_real_addresses(self, analyzer):
        """Full AU addresses with street + suburb + state (+ optional postcode)
        must still be detected as a single span."""
        positives = [
            "The applicant lives at 123 Queen St, Sydney NSW 2000.",
            "Please send mail to 42 Wallaby Way, Sydney NSW 2000.",
            "Our office is located at 456 Elizabeth Street, Melbourne VIC 3000.",
            "15 Smith Road, Brisbane QLD 4000",
            "Unit 5, 23 Bourke Court, Canberra ACT 2600",
            "Customer lives at 42 Park Avenue, Brisbane QLD.",  # no postcode
        ]
        for text in positives:
            results = analyzer.analyze(text)
            addr = [r for r in results if r.entity_type == "AU_ADDRESS"]
            assert addr, f"AU_ADDRESS missed in {text!r}"
            # No more overlapping same-type spans for a single address
            assert len(addr) == 1, (
                f"Expected 1 AU_ADDRESS span, got {len(addr)} in {text!r}: "
                f"{[(r.start, r.end, text[r.start:r.end]) for r in addr]}"
            )

    def test_au_address_case_tolerance(self, analyzer):
        """AU_ADDRESS must match real-world case variants (lowercase suburb,
        all-caps, mixed) when the state+postcode anchor is present. Users
        don't consistently title-case addresses."""
        positives = [
            "123 Main Street, sydney NSW 2000",       # lowercase suburb
            "42 queen st, melbourne vic 3000",        # all lowercase
            "Unit 5, 23 BOURKE COURT, CANBERRA ACT 2600",  # all caps
        ]
        for text in positives:
            results = analyzer.analyze(text)
            addr = [r for r in results if r.entity_type == "AU_ADDRESS"]
            assert addr, f"AU_ADDRESS missed in {text!r}"

    def test_natural_language_dates_still_detected(self, analyzer):
        """spaCy NER tags phrases like 'March 2024', 'next Monday', 'Q1 2024'
        as DATE. They must not be dropped by the tightened DATE validator."""
        positives = [
            "The incident happened in March 2024.",
            "I'll be there next Monday.",
            "Data from January 1990 onwards.",
            "Results for Q1 2024 are in.",
            "She arrived yesterday.",
            "Filed on Monday.",
        ]
        for text in positives:
            results = analyzer.analyze(text)
            dates = [r for r in results if r.entity_type in ("DATE", "DATE_OF_BIRTH")]
            assert dates, f"DATE missed in {text!r}"

    def test_labelled_ids_do_not_fall_through_to_vehicle_registration(self, analyzer):
        """Labelled IDs with invalid values must not be rescued by the broad
        vehicle-registration recognizer. This preserves the precision gain from
        requiring claim/policy IDs to contain at least one digit."""
        negatives = [
            "Claim Number: ABCDEF",
            "Claim Number: Note",
            "Policy Number: Number",
            "Vehicle DOB30 recorded",
            "DOB30 noted in the claim diary",
        ]
        for text in negatives:
            results = analyzer.analyze(text)
            vehicle_regs = [r for r in results if r.entity_type == "VEHICLE_REGISTRATION"]
            assert not vehicle_regs, (
                f"VEHICLE_REGISTRATION false positive in {text!r}: "
                f"{[(r.start, r.end, text[r.start:r.end]) for r in vehicle_regs]}"
            )

        positives = [
            ("Claim Number: ABC123", "INSURANCE_CLAIM_NUMBER"),
            ("Policy Number: P12345", "INSURANCE_POLICY_NUMBER"),
            ("Rego: ABC123", "VEHICLE_REGISTRATION"),
            ("Registration: DOB30", "VEHICLE_REGISTRATION"),
        ]
        for text, expected_type in positives:
            results = analyzer.analyze(text)
            entity_types = [r.entity_type for r in results]
            assert expected_type in entity_types, (
                f"{expected_type} missed in {text!r}. Found: {entity_types}"
            )

    def test_incident_date_is_case_tolerant_and_specific(self, analyzer):
        """Incident-date labels are often lower or mixed case; keep their more
        specific entity type rather than falling back to generic DATE."""
        positives = [
            "Date of incident: 15/01/2023",
            "date of loss: 15/01/2023",
            "DATE OF ACCIDENT: 15/01/2023",
            "The crash happened on 15/01/2023.",
        ]
        for text in positives:
            results = analyzer.analyze(text)
            incident_dates = [r for r in results if r.entity_type == "INCIDENT_DATE"]
            assert incident_dates, f"INCIDENT_DATE missed in {text!r}: {results}"

    def test_australian_specific_patterns(self, analyzer):
        """Test Australian-specific pattern improvements."""
        test_cases = [
            ("Passport: N1234567", "AU_PASSPORT"),
            ("CRN: 123 456 789K", "AU_CENTRELINK_CRN"),
            ("ACN: 123 456 789", "AU_ACN"),
            ("NSW License: 12345678", "AU_DRIVERS_LICENSE"),
        ]
        
        for text, expected_type in test_cases:
            results = analyzer.analyze(text)
            entity_types = [r.entity_type for r in results]
            
            assert expected_type in entity_types, \
                f"Failed to detect {expected_type}: '{text}'. Found: {entity_types}"
    
    def test_validator_functions(self):
        """Test individual validator functions."""
        # Test date validation
        assert EntityValidator.validate_date("NSW 2000")[0] == False
        assert EntityValidator.validate_date("15/01/2023")[0] == True
        assert EntityValidator.validate_date("0412")[0] == False  # Phone prefix
        
        # Test phone validation
        assert EntityValidator.validate_phone_number("0412345678")[0] == True
        assert EntityValidator.validate_phone_number("123")[0] == False
        
        # Test Medicare validation
        assert EntityValidator.validate_medicare_number("2123456781")[0] == True
        assert EntityValidator.validate_medicare_number("1123456781")[0] == False
        
        # TFN: 9-digit weighted modulus-11 checksum.
        # 123456782 satisfies the algorithm; 123456789 does not.
        assert EntityValidator.validate_tfn("123456782")[0] is True
        assert EntityValidator.validate_tfn("123456789")[0] is False
        # Whitespace variants should normalise.
        assert EntityValidator.validate_tfn("123 456 782")[0] is True

        # ABN: 11-digit modulus-89 checksum (subtract 1 from first digit).
        # 51824753556 is the ATO's published test ABN.
        assert EntityValidator.validate_abn("51824753556")[0] is True
        assert EntityValidator.validate_abn("51824753557")[0] is False
        assert EntityValidator.validate_abn("51 824 753 556")[0] is True
    
    def test_context_analyzer(self):
        """Test context analyzer functionality."""
        analyzer = ContextAnalyzer()
        
        # Test context extraction
        text = "Medicare number 2123 45678 1 for patient"
        context_before, context_after = analyzer.get_context_window(text, 16, 28, window_size=20)
        
        assert "medicare number" in context_before.lower()
        assert "for patient" in context_after.lower()
        
        # Test context analysis
        analysis = analyzer.analyze_context(text, "AU_MEDICARE", 16, 28)
        
        assert analysis['pattern_match'] == True
        assert analysis['confidence_boost'] > 0
        
        # Test false positive detection
        text2 = "NSW 2000"
        is_fp = analyzer.is_likely_false_positive(text2, "DATE", 0, 8)
        assert is_fp == True
    
    def test_complex_document_processing(self, analyzer):
        """Test processing of complex documents with multiple entity types."""
        document = """
        Patient: John Smith (DOB: 15/06/1980)
        Medicare: 2123 45678 1
        TFN: 123 456 782
        
        Address: 123 Main Street, Sydney NSW 2000
        Phone: 0412 345 678
        Email: john.smith@example.com
        
        Policy Number: POL-12345678
        Claim #: CL-98765432
        
        Treatment at Melbourne Medical Centre on 15/01/2023.
        Cost: $1,250 (including GST)
        """
        
        result = analyzer.process(document)
        
        # Check that key entities are detected
        entity_types = result['statistics']['entity_types']
        
        assert 'PERSON' in entity_types
        assert 'AU_MEDICARE' in entity_types
        assert 'AU_TFN' in entity_types
        assert 'AU_PHONE' in entity_types
        assert 'EMAIL_ADDRESS' in entity_types
        assert 'INSURANCE_POLICY_NUMBER' in entity_types
        assert 'INSURANCE_CLAIM_NUMBER' in entity_types
        
        # Check that false positives are avoided
        entities = result['analysis']['entities']
        
        # NSW 2000 should not be detected as DATE
        date_entities = [e for e in entities if e['entity_type'] == 'DATE' 
                        and e['text'] == 'NSW 2000']
        assert len(date_entities) == 0
        
        # Street names should not be PERSON
        person_entities = [e for e in entities if e['entity_type'] == 'PERSON']
        street_names = [e for e in person_entities 
                       if any(suffix in e['text'].lower() 
                            for suffix in [' street', ' st'])]
        assert len(street_names) == 0
