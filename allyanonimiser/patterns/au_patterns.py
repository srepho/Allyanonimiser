"""
Australian patterns for detecting Australian-specific PII.
"""

def get_au_pattern_definitions():
    """Return patterns for Australian-specific PII."""
    return [
        {
            "entity_type": "AU_TFN",
            "patterns": [r"\b\d{3}\s*\d{3}\s*\d{3}\b"],
            "context": ["tax", "file", "number", "TFN"],
            "name": "Australian Tax File Number"
        },
        {
            "entity_type": "AU_PHONE",
            "patterns": [
                r"\b(?:\+?61|0)4\d{2}\s*\d{3}\s*\d{3}\b",  # Mobile
                r"\b(?:\+?61|0)[2378]\s*\d{4}\s*\d{4}\b",  # Landline
                r"\b(?:\+?61|0)\d\s*\d{4}\s*\d{4}\b"       # General format
            ],
            "context": ["phone", "mobile", "call", "contact", "telephone"],
            "name": "Australian Phone Number"
        },
        {
            "entity_type": "AU_MEDICARE",
            "patterns": [r"\b\d{4}\s*\d{5}\s*\d{1}\b"],
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
                r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Place|Pl|Court|Ct|Crescent|Cr),\s*[A-Za-z\s]+,\s*(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)\s*\d{4}\b",
                r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Place|Pl|Court|Ct|Crescent|Cr)\b"
            ],
            "context": ["address", "street", "road", "suburb", "live", "residence"],
            "name": "Australian Address"
        },
        {
            "entity_type": "AU_POSTCODE",
            "patterns": [r"\b\d{4}\b"],
            "context": ["postcode", "postal", "code", "zip"],
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
            "patterns": [r"\b\d{2}\s*\d{3}\s*\d{3}\s*\d{3}\b"],
            "context": ["abn", "australian business number", "business", "company"],
            "name": "Australian Business Number"
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