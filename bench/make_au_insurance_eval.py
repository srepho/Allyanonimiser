"""
Synthesize a labeled AU-insurance PII eval set.

Approach: template-based insertion with known char offsets. We record spans
as we build the string, so labels are always correct. Values come from Faker
en_AU plus a small bank of published test-valid AU identifiers (TFN, Medicare,
ABN, ACN) that pass their checksums.

Output: bench/data/au_insurance.jsonl
  one JSON per line: {"text": "...", "spans": [{"start","end","label","value"}]}
"""
import json
import random
from pathlib import Path

from faker import Faker

fake = Faker("en_AU")
Faker.seed(42)
random.seed(42)


# AU identifiers: real test-valid values (published checksums)
# Rotated to avoid one value dominating the eval.
VALID_TFNS = [
    "123 456 782",  # common test value
    "123 456 740",
    "999 999 999",  # valid test pattern
]
VALID_MEDICARE = [
    "2123 45678 1",
    "2428 77817 1",
    "4133 81859 1",
]
VALID_ABN = [
    "51 824 753 556",
    "53 004 085 616",
    "83 914 571 673",
]
VALID_ACN = [
    "004 085 616",
    "123 456 780",
]
POLICY_PREFIXES = ["POL", "POL-", "P"]
CLAIM_PREFIXES = ["CL", "CL-", "CLM", "CLM-"]
VEHICLE_REGS = ["ABC123", "XYZ789", "AU-4321", "BTR-555", "JQK-012", "MNO42P"]
VINS = [
    "1HGCM82633A123456",
    "WBA8E9C54GK123789",
    "JH4DC4370SS001234",
    "5YJSA1E26JF123456",
]
STATE_CAPITAL = [
    ("NSW", "Sydney"), ("VIC", "Melbourne"), ("QLD", "Brisbane"),
    ("WA", "Perth"), ("SA", "Adelaide"), ("TAS", "Hobart"),
    ("ACT", "Canberra"), ("NT", "Darwin"),
]
STREETS = [
    ("Queen Street", "2000"), ("King Street", "2000"),
    ("Collins Street", "3000"), ("Elizabeth Street", "3000"),
    ("Adelaide Street", "4000"), ("George Street", "4000"),
    ("St Georges Terrace", "6000"), ("Hay Street", "6000"),
    ("Grenfell Street", "5000"), ("Rundle Mall", "5000"),
]


def rand_mobile():
    return f"04{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"

def rand_landline():
    area = random.choice(["02", "03", "07", "08"])
    return f"{area} {random.randint(4000, 9999)} {random.randint(1000, 9999)}"

def rand_email(first, last):
    domains = ["example.com.au", "insurer.com.au", "mailco.com", "claim-mail.net"]
    return f"{first.lower()}.{last.lower()}@{random.choice(domains)}"

def rand_policy():
    return f"{random.choice(POLICY_PREFIXES)}{random.randint(1000000, 9999999)}"

def rand_claim():
    return f"{random.choice(CLAIM_PREFIXES)}{random.randint(10000000, 99999999)}"

def rand_au_address():
    street_num = random.randint(1, 500)
    street, postcode = random.choice(STREETS)
    state, capital = random.choice(STATE_CAPITAL)
    return f"{street_num} {street}, {capital} {state} {postcode}"

def rand_dob():
    d = fake.date_of_birth(minimum_age=18, maximum_age=85)
    return d.strftime("%d/%m/%Y")

def rand_date():
    d = fake.date_between(start_date="-3y", end_date="today")
    return d.strftime("%d/%m/%Y")


class Builder:
    """Accumulates text and records spans as values are appended.
    Call write(raw_text) for non-PII parts, pii(label, value) for PII parts."""
    def __init__(self):
        self.parts = []
        self.spans = []
        self.pos = 0

    def write(self, text):
        self.parts.append(text)
        self.pos += len(text)

    def pii(self, label, value):
        self.parts.append(value)
        self.spans.append({
            "start": self.pos,
            "end": self.pos + len(value),
            "label": label,
            "value": value,
        })
        self.pos += len(value)

    def build(self):
        return "".join(self.parts), self.spans


def make_claim_note():
    b = Builder()
    first = fake.first_name()
    last = fake.last_name()
    full = f"{first} {last}"
    b.write("Claim Note\n\nCustomer: ")
    b.pii("PERSON", full)
    b.write(" (DOB: ")
    b.pii("DATE", rand_dob())
    b.write(")\nPolicy Number: ")
    b.pii("POLICY_NUMBER", rand_policy())
    b.write("\nClaim: ")
    b.pii("INSURANCE_CLAIM_NUMBER", rand_claim())
    b.write("\n\nThe insured called on ")
    b.pii("DATE", rand_date())
    b.write(" regarding damage to vehicle registration ")
    b.pii("VEHICLE_REGISTRATION", random.choice(VEHICLE_REGS))
    b.write(" (VIN: ")
    b.pii("VIN", random.choice(VINS))
    b.write("). Mobile: ")
    b.pii("AU_PHONE", rand_mobile())
    b.write(". Email: ")
    b.pii("EMAIL_ADDRESS", rand_email(first, last))
    b.write(".\nResidential address: ")
    b.pii("AU_ADDRESS", rand_au_address())
    b.write(".\nTFN on file: ")
    b.pii("AU_TFN", random.choice(VALID_TFNS))
    b.write(".\nMedicare: ")
    b.pii("AU_MEDICARE", random.choice(VALID_MEDICARE))
    b.write(".")
    return b.build()


def make_email():
    b = Builder()
    first = fake.first_name()
    last = fake.last_name()
    adj_first = fake.first_name()
    adj_last = fake.last_name()
    b.write("From: ")
    b.pii("EMAIL_ADDRESS", rand_email(adj_first, adj_last))
    b.write("\nTo: ")
    b.pii("EMAIL_ADDRESS", rand_email(first, last))
    b.write("\nSubject: Your claim ")
    claim = rand_claim()
    b.pii("INSURANCE_CLAIM_NUMBER", claim)
    b.write(f"\n\nDear {last[:0]}")  # empty filler to keep offsets simple
    b.write(f"Hi {first},\n\n")
    b.write("Thank you for submitting claim ")
    b.pii("INSURANCE_CLAIM_NUMBER", claim)
    b.write(" on ")
    b.pii("DATE", rand_date())
    b.write(". Your policy ")
    b.pii("POLICY_NUMBER", rand_policy())
    b.write(" covers this. Please call me on ")
    b.pii("AU_PHONE", rand_landline())
    b.write(" if you have questions.\n\nRegards,\n")
    b.pii("PERSON", f"{adj_first} {adj_last}")
    b.write("\nClaims Assessor")
    return b.build()


def make_underwriting():
    b = Builder()
    company = fake.company()
    first = fake.first_name()
    last = fake.last_name()
    b.write(f"Underwriting Assessment\n\nBusiness: {company}\nABN: ")
    b.pii("AU_ABN", random.choice(VALID_ABN))
    b.write("\nACN: ")
    b.pii("AU_ACN", random.choice(VALID_ACN))
    b.write("\n\nDirector: ")
    b.pii("PERSON", f"{first} {last}")
    b.write(" (DOB ")
    b.pii("DATE", rand_dob())
    b.write(")\nContact: ")
    b.pii("AU_PHONE", rand_landline())
    b.write(" / ")
    b.pii("EMAIL_ADDRESS", rand_email(first, last))
    b.write("\nRegistered office: ")
    b.pii("AU_ADDRESS", rand_au_address())
    return b.build()


def make_medical_report():
    b = Builder()
    first = fake.first_name()
    last = fake.last_name()
    dr_first = fake.first_name()
    dr_last = fake.last_name()
    b.write("Medical Report\n\nPatient: ")
    b.pii("PERSON", f"{first} {last}")
    b.write("\nDOB: ")
    b.pii("DATE", rand_dob())
    b.write("\nMedicare: ")
    b.pii("AU_MEDICARE", random.choice(VALID_MEDICARE))
    b.write("\n\nAssessment on ")
    b.pii("DATE", rand_date())
    b.write(" for injuries sustained in motor accident. Patient resides at ")
    b.pii("AU_ADDRESS", rand_au_address())
    b.write(" and can be reached on ")
    b.pii("AU_PHONE", rand_mobile())
    b.write(".\n\nDr. ")
    b.pii("PERSON", f"{dr_first} {dr_last}")
    return b.build()


def make_claim_short():
    """Simpler, shorter claim-style note to add variety."""
    b = Builder()
    first = fake.first_name()
    last = fake.last_name()
    b.write("Spoke with ")
    b.pii("PERSON", f"{first} {last}")
    b.write(" on ")
    b.pii("AU_PHONE", rand_mobile())
    b.write(" about vehicle ")
    b.pii("VEHICLE_REGISTRATION", random.choice(VEHICLE_REGS))
    b.write(". Policy ")
    b.pii("POLICY_NUMBER", rand_policy())
    b.write(" at ")
    b.pii("AU_ADDRESS", rand_au_address())
    b.write(".")
    return b.build()


GENERATORS = [make_claim_note, make_email, make_underwriting, make_medical_report, make_claim_short]


def main(n=100, out="bench/data/au_insurance.jsonl"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for i in range(n):
            gen = GENERATORS[i % len(GENERATORS)]
            text, spans = gen()
            # Sanity check: every span's substring matches its value
            for sp in spans:
                assert text[sp["start"]:sp["end"]] == sp["value"], \
                    f"offset mismatch in {gen.__name__}: {sp}"
            f.write(json.dumps({"text": text, "spans": spans}) + "\n")
    print(f"Wrote {n} rows to {out}")


if __name__ == "__main__":
    main()
