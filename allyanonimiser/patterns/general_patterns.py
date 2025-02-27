"""
General PII patterns for the Allyanonimiser package.
Contains regex patterns and context keywords for common PII types.
"""

from typing import Dict, List, Any

# Email Addresses
EMAIL_PATTERNS = [
    # Basic email pattern
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    # With mailto: prefix
    r'mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
]

EMAIL_CONTEXT = [
    "email", "e-mail", "electronic mail", "contact", "address", "send", "message",
    "inbox", "mail", "webmail"
]

# IP Addresses
IP_PATTERNS = [
    # IPv4
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
    # IPv6
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
    r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b',
    r'\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b',
    r'\b(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}\b',
    r'\b(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}\b',
    r'\b(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}\b',
    r'\b(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}\b',
    r'\b[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}\b',
    r'\b:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)\b'
]

IP_CONTEXT = [
    "ip", "internet protocol", "address", "network", "server", "host", "client",
    "connection", "remote", "local"
]

# URLs
URL_PATTERNS = [
    # Basic URL pattern
    r'\b(?:https?|ftp)://[^\s/$.?#].[^\s]*\b',
    # URL with www prefix but no protocol
    r'\bwww\.[^\s/$.?#].[^\s]*\b'
]

URL_CONTEXT = [
    "url", "website", "site", "web", "link", "http", "https", "www", "navigate",
    "browser", "visit"
]

# Dates
DATE_PATTERNS = [
    # ISO format (YYYY-MM-DD)
    r'\b\d{4}-\d{2}-\d{2}\b',
    # Common formats
    r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
    # Month name formats
    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
    r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'
]

DATE_CONTEXT = [
    "date", "day", "month", "year", "calendar", "scheduled", "appointment", "booking",
    "birthday", "born", "dob", "anniversary"
]

# Credit Card Numbers
CREDIT_CARD_PATTERNS = [
    # Visa
    r'\b4[0-9]{12}(?:[0-9]{3})?\b',
    # Mastercard
    r'\b5[1-5][0-9]{14}\b',
    r'\b2[2-7][0-9]{14}\b',
    # American Express
    r'\b3[47][0-9]{13}\b',
    # Discover
    r'\b6(?:011|5[0-9]{2})[0-9]{12}\b',
    # With spaces or dashes
    r'\b(?:4[0-9]{3}|5[1-5][0-9]{2}|6(?:011|5[0-9]{2})|3[47][0-9]{2})[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b'
]

CREDIT_CARD_CONTEXT = [
    "credit", "card", "payment", "visa", "mastercard", "amex", "discover", "expiry",
    "expiration", "cvv", "secure code", "transaction"
]

# Usernames
USERNAME_PATTERNS = [
    # Common username patterns
    r'\busername:?\s*\S+\b',
    r'\buser:?\s*\S+\b',
    r'\blogin:?\s*\S+\b',
    r'\bid:?\s*\S+\b'
]

USERNAME_CONTEXT = [
    "username", "user", "login", "account", "sign in", "log in", "profile", "handle",
    "id", "identifier"
]

# Age
AGE_PATTERNS = [
    # Age with units
    r'\b\d{1,3}\s*(?:years|year|yrs?|y)\s*(?:old)?\b',
    r'\bage:?\s*\d{1,3}\b',
    r'\b\d{1,3}\s*(?:years|year|yrs?|y)\s*of\s*age\b'
]

AGE_CONTEXT = [
    "age", "old", "years", "birthday", "young", "elderly", "senior", "minor", "adult",
    "teenager", "adolescent"
]

# Money/Currency
MONEY_PATTERNS = [
    # Currency symbols
    r'\b[$€£¥]\s?\d+(?:[,.]\d+)*\b',
    # Currency codes
    r'\b(?:USD|AUD|EUR|GBP|CAD|JPY|NZD)\s?\d+(?:[,.]\d+)*\b',
    # Spelled out
    r'\b\d+(?:[,.]\d+)*\s*(?:dollars|euro|pounds|yen)\b'
]

MONEY_CONTEXT = [
    "money", "payment", "cost", "price", "fee", "charge", "amount", "paid", "total",
    "balance", "currency", "financial", "dollars", "cents"
]

# Combined General Patterns dictionary
GENERAL_PATTERNS = {
    "EMAIL_ADDRESS": {
        "patterns": EMAIL_PATTERNS,
        "context": EMAIL_CONTEXT,
        "description": "Email Address"
    },
    "IP_ADDRESS": {
        "patterns": IP_PATTERNS,
        "context": IP_CONTEXT,
        "description": "IP Address"
    },
    "URL": {
        "patterns": URL_PATTERNS,
        "context": URL_CONTEXT,
        "description": "URL or Website Address"
    },
    "DATE": {
        "patterns": DATE_PATTERNS,
        "context": DATE_CONTEXT,
        "description": "Date"
    },
    "CREDIT_CARD_NUMBER": {
        "patterns": CREDIT_CARD_PATTERNS,
        "context": CREDIT_CARD_CONTEXT,
        "description": "Credit Card Number"
    },
    "USERNAME": {
        "patterns": USERNAME_PATTERNS,
        "context": USERNAME_CONTEXT,
        "description": "Username or Account ID"
    },
    "AGE": {
        "patterns": AGE_PATTERNS,
        "context": AGE_CONTEXT,
        "description": "Age"
    },
    "MONEY_AMOUNT": {
        "patterns": MONEY_PATTERNS,
        "context": MONEY_CONTEXT,
        "description": "Money or Currency Amount"
    }
}

def get_general_pattern_definitions() -> List[Dict[str, Any]]:
    """
    Get a list of general pattern definitions suitable for creating CustomPatternDefinition objects.
    
    Returns:
        List of dictionaries with pattern definition data
    """
    pattern_definitions = []
    
    for entity_type, data in GENERAL_PATTERNS.items():
        pattern_definitions.append({
            "entity_type": entity_type,
            "patterns": data["patterns"],
            "context": data["context"],
            "name": f"{entity_type.lower()}_recognizer",
            "description": data["description"]
        })
    
    return pattern_definitions