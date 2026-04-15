# Australian Patterns

Allyanonimiser includes specialized patterns for detecting Australian-specific PII and identifiers.

## Australian Tax File Number (AU_TFN)

Tax File Numbers are unique identifiers issued by the Australian Taxation Office.

**Pattern Example:**
- `123 456 782` *(checksum-valid — use this shape in tests)*
- `TFN: 123 456 782`

**Regex Pattern:**
```
\b\d{3}\s*\d{3}\s*\d{3}\b
```

**Contexts:**
"tax", "file", "number", "tfn"

> **Checksum validation** *(since v3.2.0)*: detected TFNs are re-checked
> against the ATO's modulus-11 weighted algorithm. Numbers that match the
> regex but fail the checksum — like `123 456 789` — are filtered out.
> Use `123 456 782` in your own test data.

## Australian Phone Number (AU_PHONE)

Australian mobile and landline phone numbers.

**Pattern Example:**
- `0412 345 678`
- `+61 412 345 678`
- `(02) 9876 5432`

**Regex Pattern:**
```
\b(?:\+?61|0)4\d{2}\s*\d{3}\s*\d{3}\b
```

**Contexts:**
"phone", "mobile", "call", "contact"

## Australian Medicare Number (AU_MEDICARE)

Medicare numbers issued by Services Australia. The first digit must be
2–6 and the last digit (the individual reference number, IRN) must be
1–9.

**Pattern Example:**
- `2123 45678 1` *(starts with 2, IRN is 1)*
- `5123 45678 1`
- `Medicare: 2345 67890 1`

**Regex Pattern:**
```
\b[2-6]\d{3}\s*\d{5}\s*[1-9]\b
```

**Contexts:**
"medicare", "card", "health", "insurance"

> **Validation**: detected candidates are re-checked against the format
> rules (first digit 2–6, IRN 1–9). Numbers like `1234 56789 1` (starts
> with 1) or `2123 45678 0` (IRN is 0) are filtered out.

## Australian Driver's License (AU_DRIVERS_LICENSE)

Driver's license numbers from various Australian states.

**Pattern Example:**
- `12345678` (NSW)
- `1234AB` (NSW legacy)

**Regex Patterns:**
```
\b\d{8}\b
\b\d{4}[a-zA-Z]{2}\b
```

**Contexts:**
"license", "licence", "driver", "driving"

## Australian Address (AU_ADDRESS)

Australian address formats including street addresses and postal codes.

**Pattern Example:**
- `42 Main St, Sydney NSW 2000`
- `Unit 5, 123 Example Road, Melbourne VIC 3000`

**Regex Patterns:**
Multiple complex patterns for detecting address components.

**Contexts:**
"street", "road", "avenue", "address", "suburb"

## Australian Postcode (AU_POSTCODE)

Four-digit Australian postcodes.

**Pattern Example:**
- `2000`
- `3000`
- `NSW 2000`

**Regex Pattern:**
```
\b\d{4}\b
```

**Contexts:**
"postcode", "post", "code", "postal"

## Australian BSB and Account Number (AU_BSB_ACCOUNT)

BSB (Bank-State-Branch) and account number combinations.

**Pattern Example:**
- `123-456 12345678`
- `123456 12345678`

**Regex Pattern:**
```
\b\d{3}-\d{3}\s*\d{6,10}\b
```

**Contexts:**
"bsb", "account", "banking", "bank"

## Australian Business Number (AU_ABN)

Australian Business Numbers issued by the Australian Business Register.

**Pattern Example:**
- `51 824 753 556` *(the ATO's published test ABN — checksum-valid)*
- `ABN: 51 824 753 556`

**Regex Pattern:**
```
\b\d{2}\s*\d{3}\s*\d{3}\s*\d{3}\b
```

**Contexts:**
"abn", "business", "number", "australian"

## Australian Passport Number (AU_PASSPORT)

Australian passport numbers.

**Pattern Example:**
- `N1234567`
- `PA1234567`

**Regex Pattern:**
```
\b[A-Za-z]\d{8}\b
```

**Contexts:**
"passport", "travel", "document", "international"

## Usage Example

```python
from allyanonimiser import create_allyanonimiser

# Create the analyzer
ally = create_allyanonimiser()

# Example text with Australian PII
text = """
The customer John Smith with TFN 123 456 782 and Medicare 1234 56789 1 
called from 0412 345 678 regarding their policy. They live at 
42 Main St, Sydney NSW 2000 and their ABN is 12 345 678 901.
"""

# Analyze the text
results = ally.analyze(text)

# Filter for Australian patterns only
au_results = [r for r in results if r.entity_type.startswith("AU_")]

# Print the results
for result in au_results:
    print(f"Entity: {result.entity_type}, Text: {result.text}, Score: {result.score}")
```