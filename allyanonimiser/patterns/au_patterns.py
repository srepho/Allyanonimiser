"""
Australian-specific PII patterns for the Allyanonimiser package.
Contains regex patterns and context keywords for Australian PII.
"""

from typing import Dict, List, Any

# Australian Tax File Number (TFN)
# Format: 8 or 9 digits, may be separated by spaces
TFN_PATTERNS = [
    # 8 or 9 digits without separators
    r'\b\d{8,9}\b',
    # 8 or 9 digits with space separators (e.g., 123 456 789)
    r'\b\d{2,3}[ ]?\d{3}[ ]?\d{3}\b',
    # With TFN identifier
    r'\bTFN\s*(?:[:-])?\s*(\d{2,3}[ ]?\d{3}[ ]?\d{3}|\d{8,9})\b',
    r'\bTax\s+File\s+Number\s*(?:[:-])?\s*(\d{2,3}[ ]?\d{3}[ ]?\d{3}|\d{8,9})\b'
]

TFN_CONTEXT = [
    "tax", "taxation", "file", "number", "tfn", "tax file number", 
    "tax return", "ato", "australian taxation office"
]

# Australian Medicare Number
# Format: 10 or 11 digits (10 digits plus 1 reference number), may be separated by spaces or hyphens
MEDICARE_PATTERNS = [
    # 10-11 digits without separators
    r'\b\d{10,11}\b',
    # 10-11 digits with space or hyphen separators (e.g., 2123 45670 1 or 2123-45670-1)
    r'\b\d{4}[ -]?\d{5}[ -]?\d{1,2}\b',
    # With Medicare identifier
    r'\bMedicare\s*(?:card|number|no|#)?\s*(?:[:-])?\s*(\d{4}[ -]?\d{5}[ -]?\d{1,2}|\d{10,11})\b'
]

MEDICARE_CONTEXT = [
    "medicare", "health", "card", "insurance", "medical", "benefit", 
    "health insurance", "medicare number", "medicare card"
]

# Australian Driver's License
# Format varies by state, generally alphanumeric
DRIVERS_LICENSE_PATTERNS = [
    # NSW: 8-digit number (e.g., 12345678)
    r'\b\d{8}\b',
    # VIC: 9-digit number starting with X followed by 8 digits (e.g., X12345678)
    r'\b[Xx]\d{8}\b',
    # QLD: 9-digit number (e.g., 123456789)
    r'\b\d{9}\b',
    # WA: 7-digit number (e.g., 1234567)
    r'\b\d{7}\b',
    # SA: 1 letter followed by 8 digits (e.g., S12345678)
    r'\b[A-Za-z]\d{8}\b',
    # TAS: 6-digit number (e.g., 123456)
    r'\b\d{6}\b',
    # NT: 8-digit number (e.g., 12345678)
    r'\b\d{8}\b',
    # ACT: 8-digit number (e.g., 12345678)
    r'\b\d{8}\b',
    # With license identifier
    r'\b(?:Driver\'?s?|Driving)\s*(?:License|Licence)\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z]?\d{6,9}|[Xx]\d{8})\b'
]

DRIVERS_LICENSE_CONTEXT = [
    "driver", "drivers", "driver's", "driving", "license", "licence", 
    "driver license", "driver licence", "driving license", "driving licence",
    "nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act", "state"
]

# Australian Postal Codes
# Format: 4 digits, first digit indicates state
POSTCODE_PATTERNS = [
    # 4-digit postcode
    r'\b[0-9]{4}\b',
    # With postcode identifier
    r'\bPostcode\s*(?:[:-])?\s*([0-9]{4})\b',
    r'\bPost\s+code\s*(?:[:-])?\s*([0-9]{4})\b'
]

POSTCODE_CONTEXT = [
    "postcode", "post code", "postal code", "post", "postal", "zip", "zip code"
]

# Australian Phone Numbers
# Format: Various formats including mobile and landline
PHONE_PATTERNS = [
    # Mobile: 10 digits starting with 04
    r'\b04\d{2}[ -]?\d{3}[ -]?\d{3}\b',
    r'\b\+?614\d{2}[ -]?\d{3}[ -]?\d{3}\b',
    # Landline: area code (2-digit) + 8 digits
    r'\b\(?0[2378]\)?\s*\d{4}\s*\d{4}\b',
    r'\b\+?61\s*[2378]\s*\d{4}\s*\d{4}\b',
    # Service numbers
    r'\b13\s*\d{4}\b',
    r'\b1300\s*\d{6}\b',
    r'\b1800\s*\d{6}\b'
]

PHONE_CONTEXT = [
    "phone", "telephone", "mobile", "cell", "contact", "call", 
    "landline", "number", "tel", "ph"
]

# Australian Bank Account Numbers
# Format: 6-digit BSB + 8-10 digit account number
BSB_ACCOUNT_PATTERNS = [
    # BSB (6 digits, may be separated by hyphen)
    r'\b\d{3}[ -]?\d{3}\b',
    # Account number (8-10 digits)
    r'\b\d{8,10}\b',
    # BSB + Account
    r'\b\d{3}[ -]?\d{3}[ -]?\d{8,10}\b',
    # With BSB/Account identifier
    r'\bBSB\s*(?:[:-])?\s*(\d{3}[ -]?\d{3})\b',
    r'\bAccount\s*(?:Number|No|#)?\s*(?:[:-])?\s*(\d{8,10})\b'
]

BSB_ACCOUNT_CONTEXT = [
    "bsb", "account", "bank", "banking", "deposit", "direct debit", 
    "financial institution", "account number", "savings", "cheque", "checking"
]

# Australian ABN (Australian Business Number)
# Format: 11 digits, may be separated by spaces
ABN_PATTERNS = [
    # 11 digits without separators
    r'\b\d{11}\b',
    # 11 digits with space separators (e.g., 12 345 678 901)
    r'\b\d{2}[ ]?\d{3}[ ]?\d{3}[ ]?\d{3}\b',
    # With ABN identifier
    r'\bABN\s*(?:[:-])?\s*(\d{2}[ ]?\d{3}[ ]?\d{3}[ ]?\d{3}|\d{11})\b',
    r'\bAustralian\s+Business\s+Number\s*(?:[:-])?\s*(\d{2}[ ]?\d{3}[ ]?\d{3}[ ]?\d{3}|\d{11})\b'
]

ABN_CONTEXT = [
    "abn", "business", "australian business number", "business number", 
    "company", "entity", "gst", "tax"
]

# Australian Passport Number
# Format: 1 letter (usually N or E or M) followed by 8 digits
PASSPORT_PATTERNS = [
    # 1 letter followed by 8 digits
    r'\b[A-Za-z]\d{8}\b',
    # With passport identifier
    r'\bPassport\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z]\d{8})\b'
]

PASSPORT_CONTEXT = [
    "passport", "travel", "document", "international", "identification", 
    "government", "dfat", "foreign"
]

# Australian CRN (Centrelink Reference Number)
# Format: 9 digits
CRN_PATTERNS = [
    # 9 digits
    r'\b\d{9}\b',
    # With CRN identifier
    r'\bCRN\s*(?:[:-])?\s*(\d{9})\b',
    r'\bCentrelink\s+Reference\s+Number\s*(?:[:-])?\s*(\d{9})\b'
]

CRN_CONTEXT = [
    "crn", "centrelink", "reference", "welfare", "benefit", "payment", 
    "social security", "government assistance", "services australia"
]

# Australian Address Patterns
# Various formats for Australian addresses
ADDRESS_PATTERNS = [
    # Street number and name
    r'\b\d+[A-Za-z]?[\s/\\]+[A-Za-z\s]+(?:street|st|road|rd|avenue|ave|drive|dr|court|ct|place|pl|crescent|cr|highway|hwy|lane|ln|parade|pde|square|sq|circuit|cct|boulevard|blvd)\b',
    # Unit/apartment details
    r'\b(?:unit|apartment|flat|shop|suite)\s+\d+[A-Za-z]?[\s/\\]+\d+[A-Za-z]?[\s/\\]+[A-Za-z\s]+(?:street|st|road|rd|avenue|ave|drive|dr|court|ct|place|pl|crescent|cr|highway|hwy|lane|ln|parade|pde|square|sq|circuit|cct|boulevard|blvd)\b',
    # PO Box
    r'\bP\.?O\.?\s+Box\s+\d+\b'
]

ADDRESS_CONTEXT = [
    "address", "street", "road", "avenue", "drive", "court", "place", 
    "crescent", "highway", "lane", "parade", "square", "circuit", "boulevard",
    "unit", "apartment", "flat", "shop", "suite", "po box", "postal", "suburb",
    "town", "city", "state", "territory"
]

# Australian Medicare Provider Number
# Format: 6 digits + 1 letter or 6 digits + 2 characters
MEDICARE_PROVIDER_PATTERNS = [
    # 6 digits + 1 letter or 6 digits + 2 characters
    r'\b\d{6}[A-Za-z]\b',
    r'\b\d{6}[A-Za-z0-9]{2}\b',
    # With provider identifier
    r'\b(?:Medicare\s+)?Provider\s*(?:Number|No|#)?\s*(?:[:-])?\s*(\d{6}[A-Za-z]|\d{6}[A-Za-z0-9]{2})\b'
]

MEDICARE_PROVIDER_CONTEXT = [
    "provider", "medicare", "doctor", "practitioner", "specialist", 
    "health provider", "medical", "healthcare", "health care"
]

# Combined Australian Patterns dictionary
AUSTRALIAN_PATTERNS = {
    "AU_TFN": {
        "patterns": TFN_PATTERNS,
        "context": TFN_CONTEXT,
        "description": "Australian Tax File Number"
    },
    "AU_MEDICARE": {
        "patterns": MEDICARE_PATTERNS,
        "context": MEDICARE_CONTEXT,
        "description": "Australian Medicare Number"
    },
    "AU_DRIVERS_LICENSE": {
        "patterns": DRIVERS_LICENSE_PATTERNS,
        "context": DRIVERS_LICENSE_CONTEXT,
        "description": "Australian Driver's License"
    },
    "AU_POSTCODE": {
        "patterns": POSTCODE_PATTERNS,
        "context": POSTCODE_CONTEXT,
        "description": "Australian Postcode"
    },
    "AU_PHONE": {
        "patterns": PHONE_PATTERNS,
        "context": PHONE_CONTEXT,
        "description": "Australian Phone Number"
    },
    "AU_BSB_ACCOUNT": {
        "patterns": BSB_ACCOUNT_PATTERNS,
        "context": BSB_ACCOUNT_CONTEXT,
        "description": "Australian BSB and Account Number"
    },
    "AU_ABN": {
        "patterns": ABN_PATTERNS,
        "context": ABN_CONTEXT,
        "description": "Australian Business Number"
    },
    "AU_PASSPORT": {
        "patterns": PASSPORT_PATTERNS,
        "context": PASSPORT_CONTEXT,
        "description": "Australian Passport Number"
    },
    "AU_CRN": {
        "patterns": CRN_PATTERNS,
        "context": CRN_CONTEXT,
        "description": "Centrelink Reference Number"
    },
    "AU_ADDRESS": {
        "patterns": ADDRESS_PATTERNS,
        "context": ADDRESS_CONTEXT,
        "description": "Australian Address"
    },
    "AU_MEDICARE_PROVIDER": {
        "patterns": MEDICARE_PROVIDER_PATTERNS,
        "context": MEDICARE_PROVIDER_CONTEXT,
        "description": "Medicare Provider Number"
    }
}

def get_au_pattern_definitions() -> List[Dict[str, Any]]:
    """
    Get a list of Australian pattern definitions suitable for creating CustomPatternDefinition objects.
    
    Returns:
        List of dictionaries with pattern definition data
    """
    pattern_definitions = []
    
    for entity_type, data in AUSTRALIAN_PATTERNS.items():
        pattern_definitions.append({
            "entity_type": entity_type,
            "patterns": data["patterns"],
            "context": data["context"],
            "name": f"{entity_type.lower()}_recognizer",
            "description": data["description"]
        })
    
    return pattern_definitions