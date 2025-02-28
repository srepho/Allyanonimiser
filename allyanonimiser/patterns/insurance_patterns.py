"""
Insurance patterns for detecting insurance-specific information.
"""

def get_insurance_pattern_definitions():
    """Return patterns for insurance-specific information."""
    return [
        {
            "entity_type": "INSURANCE_POLICY_NUMBER",
            "patterns": [
                r"\b(?:POL|P|Policy)[- ]?\d{6,9}\b",
                r"\bAU[-\s]*\d{5,10}\b",                    # AU-12345678 format
                r"\bPolicy (?:Number|#):\s*[A-Za-z0-9-]{6,15}\b",
                r"\bPolicy\s*(?:Number|#|No):\s*[A-Za-z0-9-]{6,15}\b",
                r"\bPolicy:\s*[A-Za-z0-9-]{6,15}\b"
            ],
            "context": ["policy", "insurance", "coverage", "insured"],
            "name": "Insurance Policy Number"
        },
        {
            "entity_type": "INSURANCE_CLAIM_NUMBER",
            "patterns": [
                r"\b(?:CL|C)[- ]?\d{6,9}\b",
                r"\bClaim (?:Number|Reference|#):\s*[A-Za-z0-9-]{6,15}\b",
                r"\bClaim\s*(?:Number|#|No|Ref):\s*[A-Za-z0-9-]{6,15}\b",
                r"\bClaim:\s*[A-Za-z0-9-]{6,15}\b"
            ],
            "context": ["claim", "incident", "accident", "reference"],
            "name": "Insurance Claim Number"
        },
        {
            "entity_type": "VEHICLE_VIN",
            "patterns": [
                r"\b[A-HJ-NPR-Z0-9]{17}\b",
                r"\bVIN:\s*[A-HJ-NPR-Z0-9]{17}\b",
                r"\bVehicle Identification Number:\s*[A-HJ-NPR-Z0-9]{17}\b"
            ],
            "context": ["vin", "vehicle", "identification", "number", "chassis"],
            "name": "Vehicle Identification Number"
        },
        {
            "entity_type": "INVOICE_NUMBER",
            "patterns": [
                r"\bINV-\d{4,10}\b",
                r"\b(?:Quote|Invoice)\s*(?:#|Number):\s*[A-Za-z0-9-]{4,15}\b",
                r"\bQ-\d{4}\b"
            ],
            "context": ["invoice", "quote", "billing", "payment", "receipt"],
            "name": "Invoice or Quote Number"
        },
        {
            "entity_type": "BROKER_CODE",
            "patterns": [
                r"\bBRK-[0-9]{4}\b",
                r"\bBroker\s*(?:Code|ID):\s*[A-Z0-9-]{4,10}\b"
            ],
            "context": ["broker", "agent", "representative", "intermediary"],
            "name": "Insurance Broker Code"
        },
        {
            "entity_type": "VEHICLE_DETAILS",
            "patterns": [
                r"\b(?:Toyota|Honda|Mazda|Ford|Hyundai|Kia|Nissan|Volkswagen|BMW|Mercedes|Audi|Holden)\s+[A-Za-z0-9]+\s+\d{4}\b",
                r"\b\d{4}\s+(?:Toyota|Honda|Mazda|Ford|Hyundai|Kia|Nissan|Volkswagen|BMW|Mercedes|Audi|Holden)\s+[A-Za-z0-9]+\b"
            ],
            "context": ["vehicle", "car", "make", "model", "year"],
            "name": "Vehicle Details"
        },
        {
            "entity_type": "INCIDENT_DATE",
            "patterns": [
                r"\bon\s+\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
                r"\bDate of (?:incident|accident|loss|event):\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"
            ],
            "context": ["date", "occurred", "happened", "incident", "accident"],
            "name": "Incident Date"
        }
    ]