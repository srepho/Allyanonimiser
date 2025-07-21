"""
Entity validators for improving detection accuracy.
"""

import re
from datetime import datetime
from typing import Tuple, Optional, List, Dict, Any

# Import pattern validation functions from pattern_validators
try:
    from .pattern_validators import (
        validate_regex,
        validate_spacy_pattern,
        validate_context_list,
        validate_entity_type,
        validate_pattern_definition,
        test_pattern_against_examples
    )
except ImportError:
    # Define stub functions if pattern_validators doesn't exist
    def validate_regex(pattern: str) -> Tuple[bool, Optional[str]]:
        try:
            re.compile(pattern)
            return True, None
        except re.error as e:
            return False, str(e)
    
    def validate_spacy_pattern(pattern: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        return True, None
    
    def validate_context_list(context: List[str]) -> Tuple[bool, Optional[str]]:
        return True, None
    
    def validate_entity_type(entity_type: str) -> Tuple[bool, Optional[str]]:
        return True, None
    
    def validate_pattern_definition(pattern_def: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        return True, None
    
    def test_pattern_against_examples(pattern: str, positive_examples: List[str], 
                                    negative_examples: List[str]) -> Dict[str, Any]:
        return {"pattern": pattern, "results": {}}

class EntityValidator:
    """Validates detected entities to reduce false positives."""
    
    @staticmethod
    def validate_date(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a detected date is actually a date.
        
        Returns:
            (is_valid, date_type) where date_type can be 'date', 'year', 'postcode', etc.
        """
        # Common false positives for dates
        
        # State + postcode pattern (e.g., "NSW 2000")
        if re.match(r'^(NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s*\d{4}$', text, re.IGNORECASE):
            return False, 'state_postcode'
        
        # Just a 4-digit number could be postcode or year
        if re.match(r'^\d{4}$', text):
            num = int(text)
            current_year = datetime.now().year
            # Likely a year if in reasonable range
            if 1900 <= num <= current_year + 5:
                return True, 'year'
            # Likely a postcode if in Australian range
            elif 800 <= num <= 9999:
                return False, 'postcode'
            else:
                return False, 'number'
        
        # Phone number parts (e.g., "0412", "9876-5432")
        if re.match(r'^0\d{3}$', text):
            return False, 'phone_prefix'
        
        if re.match(r'^\d{4}-\d{4}$', text):
            return False, 'phone_suffix'
        
        # Medicare numbers (10 digits)
        if re.match(r'^\d{10}$', text):
            return False, 'medicare_number'
        
        # Actual date patterns
        date_patterns = [
            r'^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}$',  # DD/MM/YYYY or similar
            r'^\d{4}[/.-]\d{1,2}[/.-]\d{1,2}$',    # YYYY-MM-DD
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}$',  # Month DD, YYYY
            r'^\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}$',     # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True, 'date'
        
        # Duration patterns (e.g., "5 days")
        if re.match(r'^\d+\s+(day|week|month|year)s?$', text, re.IGNORECASE):
            return False, 'duration'
        
        # Australian service numbers (1300, 1800, 13xx)
        if re.match(r'^1300\s+\d{3}\s+\d{3}$', text):
            return False, 'service_number'
        if re.match(r'^1800\s+\d{3}\s+\d{3}$', text):
            return False, 'service_number'
        if re.match(r'^13\d{2}\s+\d{2}$', text):
            return False, 'service_number'
        
        return False, 'unknown'
    
    @staticmethod
    def validate_phone_number(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a detected phone number is valid.
        
        Returns:
            (is_valid, phone_type) where phone_type can be 'mobile', 'landline', 'service', etc.
        """
        # Remove common formatting
        cleaned = re.sub(r'[\s\-\(\)]+', '', text)
        
        # Australian mobile (04xx xxx xxx)
        if re.match(r'^(?:\+61|0)4\d{8}$', cleaned):
            return True, 'mobile'
        
        # Australian landline
        if re.match(r'^(?:\+61|0)[2378]\d{8}$', cleaned):
            return True, 'landline'
        
        # Service numbers
        if re.match(r'^(?:13\d{4}|1300\d{6}|1800\d{6})$', cleaned):
            return True, 'service'
        
        # Emergency numbers
        if cleaned in ['000', '112', '106']:
            return True, 'emergency'
        
        # International format
        if re.match(r'^\+\d{1,3}\d{7,14}$', cleaned):
            return True, 'international'
        
        # Partial patterns that aren't complete phone numbers
        if len(cleaned) < 8:
            return False, 'partial'
        
        return False, 'invalid'
    
    @staticmethod
    def validate_medicare_number(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Australian Medicare number format.
        
        Returns:
            (is_valid, error_message)
        """
        # Remove spaces
        cleaned = re.sub(r'\s+', '', text)
        
        # Medicare format: 10 digits (4+5+1)
        if not re.match(r'^\d{10}$', cleaned):
            return False, 'Medicare number must be 10 digits'
        
        # First digit should be 2-6
        if cleaned[0] not in '23456':
            return False, 'Medicare number should start with 2-6'
        
        # IRN (10th digit) should be 1-9
        if cleaned[9] == '0':
            return False, 'Invalid IRN (10th digit cannot be 0)'
        
        return True, None
    
    @staticmethod
    def validate_tfn(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Australian Tax File Number format.
        
        Returns:
            (is_valid, error_message)
        """
        # Remove spaces
        cleaned = re.sub(r'\s+', '', text)
        
        # TFN format: 9 digits
        if not re.match(r'^\d{9}$', cleaned):
            return False, 'TFN must be 9 digits'
        
        # Apply TFN algorithm (modulus 11 check)
        weights = [1, 4, 3, 7, 5, 8, 6, 9, 10]
        check_sum = sum(int(cleaned[i]) * weights[i] for i in range(9))
        
        if check_sum % 11 != 0:
            return False, 'Invalid TFN checksum'
        
        return True, None
    
    @staticmethod
    def validate_abn(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Australian Business Number format.
        
        Returns:
            (is_valid, error_message)
        """
        # Remove spaces
        cleaned = re.sub(r'\s+', '', text)
        
        # ABN format: 11 digits
        if not re.match(r'^\d{11}$', cleaned):
            return False, 'ABN must be 11 digits'
        
        # Apply ABN algorithm
        weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
        # Subtract 1 from first digit
        digits = [int(d) for d in cleaned]
        digits[0] -= 1
        
        check_sum = sum(digits[i] * weights[i] for i in range(11))
        
        if check_sum % 89 != 0:
            return False, 'Invalid ABN checksum'
        
        return True, None
    
    @staticmethod
    def validate_australian_postcode(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Australian postcode.
        
        Returns:
            (is_valid, state)
        """
        if not re.match(r'^\d{4}$', text):
            return False, None
        
        postcode = int(text)
        
        # Australian postcode ranges by state
        postcode_ranges = {
            'NSW': [(1000, 2599), (2619, 2899), (2921, 2999)],
            'VIC': [(3000, 3999), (8000, 8999)],
            'QLD': [(4000, 4999), (9000, 9999)],
            'SA': [(5000, 5999)],
            'WA': [(6000, 6999)],
            'TAS': [(7000, 7999)],
            'NT': [(800, 899)],
            'ACT': [(200, 299), (2600, 2618), (2900, 2920)]
        }
        
        for state, ranges in postcode_ranges.items():
            for start, end in ranges:
                if start <= postcode <= end:
                    return True, state
        
        return False, None
    
    @staticmethod
    def validate_number(text: str, context: str = "") -> Tuple[bool, Optional[str]]:
        """
        Validate if a detected number is meaningful or a false positive.
        
        Returns:
            (is_valid, number_type)
        """
        # Single character numbers
        if text == '#':
            return False, 'symbol'
        
        # Words that contain numbers
        if text.lower() in ['quarter', 'half', 'third']:
            return False, 'word'
        
        # Check if it's a year
        if re.match(r'^\d{4}$', text):
            num = int(text)
            current_year = datetime.now().year
            if 1900 <= num <= current_year + 5:
                return True, 'year'
        
        # Check context for better classification
        context_lower = context.lower()
        
        # Street numbers
        if any(word in context_lower for word in ['street', ' st ', 'road', ' rd ', 'avenue', ' ave ']):
            return True, 'street_number'
        
        # Medicare context
        if 'medicare' in context_lower and len(text) == 10:
            return True, 'medicare_number'
        
        # Policy/claim numbers
        if any(word in context_lower for word in ['policy', 'claim', 'reference']):
            return True, 'reference_number'
        
        # Duration
        if any(word in context_lower for word in ['days', 'weeks', 'months', 'years']):
            return True, 'duration_number'
        
        # Default validation for generic numbers
        if re.match(r'^\d+$', text):
            return True, 'generic_number'
        
        return False, 'invalid'