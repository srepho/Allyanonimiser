"""
Insurance-specific patterns for the Allyanonimiser package.
Contains regex patterns and context keywords for insurance-specific identifiers.
"""

from typing import Dict, List, Any

# Insurance Policy Numbers
# Format varies by insurer, generally alphanumeric
POLICY_NUMBER_PATTERNS = [
    # Generic alphanumeric patterns (8-12 characters)
    r'\b[A-Za-z0-9]{8,12}\b',
    # Pattern with hyphen separators
    r'\b[A-Za-z0-9]{2,6}[-][A-Za-z0-9]{2,6}[-]?[A-Za-z0-9]{1,6}\b',
    # With policy identifier
    r'\bPolicy\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z0-9]{2,6}[-]?[A-Za-z0-9]{2,6}[-]?[A-Za-z0-9]{1,6}|[A-Za-z0-9]{8,12})\b',
    r'\bPolicy\s*ID\s*(?:[:-])?\s*([A-Za-z0-9]{2,6}[-]?[A-Za-z0-9]{2,6}[-]?[A-Za-z0-9]{1,6}|[A-Za-z0-9]{8,12})\b',
    # With policy type prefixes
    r'\b(?:HOM|CAR|MOT|PET|LIFE|BUS|COM|HEA)[A-Za-z0-9]{5,10}\b'
]

POLICY_NUMBER_CONTEXT = [
    "policy", "insurance", "coverage", "insured", "premium", "underwriting", 
    "insurer", "certificate", "schedule", "contract", "cover"
]

# Insurance Claim Numbers
# Format varies by insurer, generally alphanumeric
CLAIM_NUMBER_PATTERNS = [
    # Generic alphanumeric patterns (8-12 characters)
    r'\b[A-Za-z0-9]{8,12}\b',
    # Pattern with hyphen or slash separators
    r'\b[A-Za-z]{1,3}[-/][0-9]{6,10}\b',
    r'\b[0-9]{2,4}[-/][0-9]{5,8}\b',
    # With claim identifier
    r'\bClaim\s*(?:Number|No|#|Reference|Ref)?\s*(?:[:-])?\s*([A-Za-z0-9]{2,6}[-/]?[A-Za-z0-9]{2,6}[-/]?[A-Za-z0-9]{1,6}|[A-Za-z0-9]{8,12})\b',
    r'\bClaim\s*ID\s*(?:[:-])?\s*([A-Za-z0-9]{2,6}[-/]?[A-Za-z0-9]{2,6}[-/]?[A-Za-z0-9]{1,6}|[A-Za-z0-9]{8,12})\b',
    # With claim type prefixes
    r'\b(?:CL|CLM|C)[/-]?[A-Za-z0-9]{6,10}\b'
]

CLAIM_NUMBER_CONTEXT = [
    "claim", "claimant", "incident", "accident", "loss", "damage", "event", 
    "lodgement", "settlement", "assessment", "adjuster", "assessor"
]

# Vehicle Registration Numbers (Australian)
# Format varies by state but generally 1-3 letters followed by 2-4 digits or vice versa
VEHICLE_REGISTRATION_PATTERNS = [
    # NSW, VIC, QLD: 3 letters + 3 digits or 1-3 letters + 2-4 digits
    r'\b[A-Za-z]{1,3}[ -]?[0-9]{2,4}\b',
    # Digit first formats: 1-4 digits + 1-3 letters
    r'\b[0-9]{1,4}[ -]?[A-Za-z]{1,3}\b',
    # With registration identifier
    r'\b(?:Vehicle|Car)?\s*Registration\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z]{1,3}[ -]?[0-9]{2,4}|[0-9]{1,4}[ -]?[A-Za-z]{1,3})\b',
    r'\bRego\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z]{1,3}[ -]?[0-9]{2,4}|[0-9]{1,4}[ -]?[A-Za-z]{1,3})\b',
    r'\bReg\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z]{1,3}[ -]?[0-9]{2,4}|[0-9]{1,4}[ -]?[A-Za-z]{1,3})\b'
]

VEHICLE_REGISTRATION_CONTEXT = [
    "rego", "registration", "vehicle", "car", "motor", "automobile", "plate", 
    "license plate", "licence plate", "number plate", "plate number", "registered"
]

# Vehicle Identification Numbers (VIN)
# Format: 17 characters (letters and numbers)
VIN_PATTERNS = [
    # 17-character VIN (excludes I, O, and Q as per standard)
    r'\b[A-HJ-NPR-Za-hj-npr-z0-9]{17}\b',
    # With separator (rare but possible)
    r'\b[A-HJ-NPR-Za-hj-npr-z0-9]{5}[ -]?[A-HJ-NPR-Za-hj-npr-z0-9]{6}[ -]?[A-HJ-NPR-Za-hj-npr-z0-9]{6}\b',
    # With VIN identifier
    r'\bVIN\s*(?:[:-])?\s*([A-HJ-NPR-Za-hj-npr-z0-9]{17}|[A-HJ-NPR-Za-hj-npr-z0-9]{5}[ -]?[A-HJ-NPR-Za-hj-npr-z0-9]{6}[ -]?[A-HJ-NPR-Za-hj-npr-z0-9]{6})\b',
    r'\bVehicle\s*Identification\s*Number\s*(?:[:-])?\s*([A-HJ-NPR-Za-hj-npr-z0-9]{17}|[A-HJ-NPR-Za-hj-npr-z0-9]{5}[ -]?[A-HJ-NPR-Za-hj-npr-z0-9]{6}[ -]?[A-HJ-NPR-Za-hj-npr-z0-9]{6})\b'
]

VIN_CONTEXT = [
    "vin", "vehicle identification number", "chassis", "chassis number", 
    "manufacturer", "vehicle details", "compliance plate"
]

# Medical Procedure Codes (MBS)
# Format: 5-digit number
MBS_PATTERNS = [
    # 5-digit MBS item number
    r'\b[0-9]{5}\b',
    # With MBS identifier
    r'\bMBS\s*(?:Item|Number|No|#|Code)?\s*(?:[:-])?\s*([0-9]{5})\b',
    r'\bMedical\s+Benefits\s+Schedule\s*(?:Item|Number|No|#|Code)?\s*(?:[:-])?\s*([0-9]{5})\b'
]

MBS_CONTEXT = [
    "mbs", "medical benefits schedule", "medicare", "procedure", "service", 
    "item", "medical", "health", "treatment", "consultation", "rebate"
]

# Hospital/Medical Provider Numbers
# Format: Various, typically alphanumeric
PROVIDER_NUMBER_PATTERNS = [
    # Alphanumeric 8-10 characters
    r'\b[A-Za-z0-9]{8,10}\b',
    # With provider identifier
    r'\bProvider\s*(?:Number|No|#|ID)?\s*(?:[:-])?\s*([A-Za-z0-9]{8,10})\b',
    r'\bHospital\s*(?:Number|No|#|ID)?\s*(?:[:-])?\s*([A-Za-z0-9]{8,10})\b'
]

PROVIDER_NUMBER_CONTEXT = [
    "provider", "hospital", "medical center", "medical centre", "clinic", 
    "facility", "healthcare provider", "health care provider", "practitioner"
]

# Invoice and Quote Numbers
# Format: Various, typically alphanumeric
INVOICE_NUMBER_PATTERNS = [
    # Alphanumeric with possible separators
    r'\b[A-Za-z0-9]{2,5}[-/]?[0-9]{4,8}\b',
    r'\bINV[-/]?[0-9]{4,8}\b',
    r'\bQUOTE[-/]?[0-9]{4,8}\b',
    # With invoice/quote identifier
    r'\bInvoice\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z0-9]{2,5}[-/]?[0-9]{4,8}|[A-Za-z0-9]{6,12})\b',
    r'\bQuote\s*(?:Number|No|#)?\s*(?:[:-])?\s*([A-Za-z0-9]{2,5}[-/]?[0-9]{4,8}|[A-Za-z0-9]{6,12})\b'
]

INVOICE_NUMBER_CONTEXT = [
    "invoice", "quote", "billing", "bill", "receipt", "tax invoice", 
    "quotation", "estimate", "payment", "account", "reference"
]

# Credit Card Last 4 Digits
# Format: 4 digits, often with "ending in" or similar prefix
CREDIT_CARD_LAST4_PATTERNS = [
    # With reference to last 4 digits
    r'\bcard\s+ending\s+(?:in|with)\s+([0-9]{4})\b',
    r'\bend(?:ing|s)\s+(?:in|with)\s+([0-9]{4})\b',
    r'\blast\s+four\s+(?:digits|numbers)\s+([0-9]{4})\b'
]

CREDIT_CARD_LAST4_CONTEXT = [
    "card", "credit", "debit", "mastercard", "visa", "amex", "payment", 
    "transaction", "charge", "purchase", "authorization", "authorisation"
]

# Combined Insurance Patterns dictionary
INSURANCE_PATTERNS = {
    "INSURANCE_POLICY_NUMBER": {
        "patterns": POLICY_NUMBER_PATTERNS,
        "context": POLICY_NUMBER_CONTEXT,
        "description": "Insurance Policy Number"
    },
    "INSURANCE_CLAIM_NUMBER": {
        "patterns": CLAIM_NUMBER_PATTERNS,
        "context": CLAIM_NUMBER_CONTEXT,
        "description": "Insurance Claim Number"
    },
    "VEHICLE_REGISTRATION": {
        "patterns": VEHICLE_REGISTRATION_PATTERNS,
        "context": VEHICLE_REGISTRATION_CONTEXT,
        "description": "Vehicle Registration Number"
    },
    "VEHICLE_VIN": {
        "patterns": VIN_PATTERNS,
        "context": VIN_CONTEXT,
        "description": "Vehicle Identification Number (VIN)"
    },
    "MEDICAL_PROCEDURE_CODE": {
        "patterns": MBS_PATTERNS,
        "context": MBS_CONTEXT,
        "description": "Medical Benefits Schedule (MBS) Code"
    },
    "MEDICAL_PROVIDER_NUMBER": {
        "patterns": PROVIDER_NUMBER_PATTERNS,
        "context": PROVIDER_NUMBER_CONTEXT,
        "description": "Medical Provider or Hospital Number"
    },
    "INVOICE_NUMBER": {
        "patterns": INVOICE_NUMBER_PATTERNS,
        "context": INVOICE_NUMBER_CONTEXT,
        "description": "Invoice or Quote Number"
    },
    "CREDIT_CARD_LAST4": {
        "patterns": CREDIT_CARD_LAST4_PATTERNS,
        "context": CREDIT_CARD_LAST4_CONTEXT,
        "description": "Credit Card Last 4 Digits"
    }
}

def get_insurance_pattern_definitions() -> List[Dict[str, Any]]:
    """
    Get a list of insurance pattern definitions suitable for creating CustomPatternDefinition objects.
    
    Returns:
        List of dictionaries with pattern definition data
    """
    pattern_definitions = []
    
    for entity_type, data in INSURANCE_PATTERNS.items():
        pattern_definitions.append({
            "entity_type": entity_type,
            "patterns": data["patterns"],
            "context": data["context"],
            "name": f"{entity_type.lower()}_recognizer",
            "description": data["description"]
        })
    
    return pattern_definitions