"""
Australian patterns for detecting Australian-specific PII.
"""

def get_au_pattern_definitions():
    """Return patterns for Australian-specific PII."""
    return [
        {
            "entity_type": "AU_TFN",
            "patterns": [
                r"(?:TFN|Tax\s+File\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b"
            ],
            "context": ["tax", "file", "number", "TFN"],
            "name": "Australian Tax File Number"
        },
        {
            "entity_type": "AU_PHONE",
            "patterns": [
                r"\b(?:\+61|0)4\d{2}[\s-]?\d{3}[\s-]?\d{3}\b",  # Mobile with flexible spacing
                r"\b(?:\+61|0)[2378][\s-]?\d{4}[\s-]?\d{4}\b",  # Landline with flexible spacing
                r"\(\d{2}\)\s*\d{4}[\s-]?\d{4}\b",              # (02) 1234 5678 format
                r"\b13\d{2}\s*\d{2}\b",                          # 13xx xx format
                r"\b1300\s*\d{3}\s*\d{3}\b",                     # 1300 xxx xxx
                r"\b1800\s*\d{3}\s*\d{3}\b"                      # 1800 xxx xxx
            ],
            "context": ["phone", "mobile", "call", "contact", "telephone", "ph", "tel"],
            "name": "Australian Phone Number"
        },
        {
            "entity_type": "AU_MEDICARE",
            "patterns": [
                r"\b[2-6]\d{3}\s*\d{5}\s*\d{1}\b",  # More specific first digit
                r"(?:Medicare|Medicare\s+Number)[:\s]*([2-6]\d{3}\s*\d{5}\s*\d{1})\b"
            ],
            "context": ["medicare", "health", "card", "insurance"],
            "name": "Australian Medicare Number"
        },
        {
            "entity_type": "AU_DRIVERS_LICENSE",
            "patterns": [
                r"\b[A-Z]{2,3}\d{5,8}\b",
                r"\b(?:License|Licence):\s*[A-Z0-9]{5,10}\b"
            ],
            "context": ["license", "licence", "driver", "driving"],
            "name": "Australian Driver's License"
        },
        {
            "entity_type": "AU_ADDRESS",
            "patterns": [
                # Full address with street, suburb/city, state and postcode
                r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Place|Pl|Court|Ct|Crescent|Cr),?\s*[A-Za-z\s]*,?\s*(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s*\d{4}\b",
                # Address with just street and suburb/city
                r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Place|Pl|Court|Ct|Crescent|Cr),?\s*[A-Za-z\s]+(?:,\s*(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT))?\b",
                # Simple street address
                r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Place|Pl|Court|Ct|Crescent|Cr)\b"
            ],
            "context": ["address", "street", "road", "suburb", "live", "residence"],
            "name": "Australian Address"
        },
        {
            "entity_type": "AU_POSTCODE",
            "patterns": [
                r"\b(?:0[289]\d{2}|[1-9]\d{3})\b",  # Valid Australian postcode ranges
                r"(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s+(\d{4})\b"  # State followed by postcode
            ],
            "context": ["postcode", "postal", "code", "zip", "post code"],
            "name": "Australian Postcode"
        },
        {
            "entity_type": "AU_BSB_ACCOUNT",
            "patterns": [
                r"\b\d{3}-\d{3}\s*\d{6,10}\b",
                r"\bBSB:\s*\d{3}-\d{3}\b",
                r"\bAccount:\s*\d{6,10}\b"
            ],
            "context": ["bsb", "account", "bank", "payment", "deposit"],
            "name": "Australian BSB and Account Number"
        },
        {
            "entity_type": "AU_ABN",
            "patterns": [
                r"(?:ABN|Australian\s+Business\s+Number)[:\s]*(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})\b"
            ],
            "context": ["abn", "australian business number", "business", "company"],
            "name": "Australian Business Number"
        },
        {
            "entity_type": "AU_ACN",
            "patterns": [
                r"(?:ACN|Australian\s+Company\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3})\b"
            ],
            "context": ["acn", "australian company number", "company"],
            "name": "Australian Company Number"
        },
        {
            "entity_type": "AU_PASSPORT",
            "patterns": [
                r"\b[A-Z][0-9]{7}\b",  # Current format
                r"\b[A-Z]{2}[0-9]{6}\b",  # Older format
                r"(?:Passport|Passport\s+Number)[:\s]*([A-Z][0-9]{7})\b"
            ],
            "context": ["passport", "travel", "document"],
            "name": "Australian Passport Number"
        },
        {
            "entity_type": "AU_CENTRELINK_CRN",
            "patterns": [
                r"\b\d{3}\s*\d{3}\s*\d{3}[A-Z]?\b",  # 9 digits with optional letter
                r"(?:CRN|Centrelink\s+Reference\s+Number)[:\s]*(\d{3}\s*\d{3}\s*\d{3}[A-Z]?)\b"
            ],
            "context": ["centrelink", "crn", "reference", "welfare"],
            "name": "Centrelink Customer Reference Number"
        },
        {
            "entity_type": "VEHICLE_REGISTRATION",
            "patterns": [
                r"\b(?!AU-\d+\b)[A-Z]{1,3}[-\s]?[A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3}\b",  # Must start with at least one letter, and exclude policy numbers like AU-12345678
                r"\b(?:Registration|Rego)(?:\.|\:|\s)+\s*([A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3})\b",  # Match after the word Registration/Rego with capturing group
                r"\brego\s+([A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3}[-\s]?[A-Z0-9]{1,3})\b"   # Match after lowercase "rego" with capturing group
            ],
            "context": ["registration", "rego", "vehicle", "car", "plate"],
            "name": "Vehicle Registration"
        }
    ]