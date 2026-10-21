"""Generate the AU challenge corpus: harder, held-out synthetic insurance text.

Separate from ``make_au_insurance_eval.py`` by design. The original corpus was
used while fixing detection, so it can no longer show gains. This corpus has
its own templates, seed and value generators, and adds realistic noise:

* identifiers generated fresh with valid checksums (TFN, ABN, ACN, Medicare,
  Luhn cards), written spaced, compact or hyphenated;
* new identifier types: driver's licences, passports, BSB and account numbers,
  Centrelink CRNs, and insurer-style policy and claim formats;
* names from a diverse bank (accents, apostrophes, hyphens, multi-part
  surnames) in several forms ("SMITH, Jane", "Mr J. Smith", first-name-only);
* addresses with units, levels, PO boxes, line breaks and lowercase;
* document noise: lowercase notes, misspelt labels, OCR substitutions,
  non-breaking spaces and phone numbers read aloud.

Every gold span records a ``variant`` naming the surface form used, and every
document records ``tags`` for document-level noise, so the evaluator can break
results down by perturbation.

Splits are by template family. ``au_challenge_dev.jsonl`` is for development
and tuning. ``au_challenge_test.jsonl`` is held out: report its aggregate
results, but do not tune rules against its individual failures.

Run from the repository root::

    python bench/make_au_challenge.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import random
import string
import sys
import zlib
from collections import Counter
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Faker is needed only to generate, not to import the checksum helpers.
    from faker import Faker

SEED = 20261021
DOCS_PER_FAMILY = 40
OUT_DIR = Path(__file__).resolve().parent / "data"
DEV_FILE = OUT_DIR / "au_challenge_dev.jsonl"
TEST_FILE = OUT_DIR / "au_challenge_test.jsonl"
MANIFEST_FILE = OUT_DIR / "au_challenge_manifest.json"
NBSP = " "

# ---------------------------------------------------------------------------
# Checksummed identifiers (implemented independently of the package)
# ---------------------------------------------------------------------------

TFN_WEIGHTS = [1, 4, 3, 7, 5, 8, 6, 9, 10]
ABN_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
ACN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 1]
MEDICARE_WEIGHTS = [1, 3, 7, 9, 1, 3, 7, 9]


def tfn_valid(digits: str) -> bool:
    return len(digits) == 9 and sum(int(d) * w for d, w in zip(digits, TFN_WEIGHTS)) % 11 == 0


def abn_valid(digits: str) -> bool:
    if len(digits) != 11:
        return False
    nums = [int(d) for d in digits]
    nums[0] -= 1
    return sum(n * w for n, w in zip(nums, ABN_WEIGHTS)) % 89 == 0


def acn_valid(digits: str) -> bool:
    if len(digits) != 9:
        return False
    check = (10 - sum(int(d) * w for d, w in zip(digits[:8], ACN_WEIGHTS)) % 10) % 10
    return check == int(digits[8])


def medicare_valid(digits: str) -> bool:
    if len(digits) != 10 or digits[0] not in "23456" or digits[9] == "0":
        return False
    return sum(int(d) * w for d, w in zip(digits[:8], MEDICARE_WEIGHTS)) % 10 == int(digits[8])


def luhn_valid(digits: str) -> bool:
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


# ---------------------------------------------------------------------------
# Value banks
# ---------------------------------------------------------------------------

GIVEN_NAMES = [
    "Thi Hoa", "Minh", "Wei", "Xiaoling", "Priya", "Harpreet", "Arjun", "Mohammed",
    "Fatima", "Georgios", "Eleni", "Giuseppe", "Chiara", "Rania", "Jamal", "Aroha",
    "Siobhan", "Zoë", "José", "Chloé", "Aisha", "Kwame", "Yuki", "Ji-woo", "Sione",
    "Mele", "Bronwyn", "Lachlan", "Mia", "Darcy",
]
SURNAMES = [
    "Nguyen", "Tran", "Pham", "Wang", "Chen", "Zhang", "Singh", "Kaur", "Patel",
    "Sharma", "Papadopoulos", "Georgiou", "Rossi", "Bianchi", "Haddad", "Khoury",
    "O'Brien", "O’Sullivan", "McAllister", "Fitzgerald-Hayes", "Te Rangi", "Ngata",
    "Taufa", "Kim", "Yamamoto", "Nguyễn", "Müller", "Van der Berg", "D'Angelo", "MacKenzie",
]
# Real suburb / state / postcode combinations.
SUBURBS = [
    ("Parramatta", "NSW", "2150"), ("Blacktown", "NSW", "2148"), ("Dubbo", "NSW", "2830"),
    ("Wagga Wagga", "NSW", "2650"), ("Newcastle West", "NSW", "2302"), ("Kellyville", "NSW", "2155"),
    ("Ringwood", "VIC", "3134"), ("Footscray", "VIC", "3011"), ("Ballarat Central", "VIC", "3350"),
    ("Werribee", "VIC", "3030"), ("Torquay", "VIC", "3228"), ("Bendigo", "VIC", "3550"),
    ("Toowoomba City", "QLD", "4350"), ("Cairns North", "QLD", "4870"), ("Logan Central", "QLD", "4114"),
    ("Southport", "QLD", "4215"), ("Fremantle", "WA", "6160"), ("Joondalup", "WA", "6027"),
    ("Bunbury", "WA", "6230"), ("Glenelg", "SA", "5045"), ("Mount Gambier", "SA", "5290"),
    ("Elizabeth", "SA", "5112"), ("Launceston", "TAS", "7250"), ("Sandy Bay", "TAS", "7005"),
    ("Belconnen", "ACT", "2617"), ("Tuggeranong", "ACT", "2900"), ("Palmerston", "NT", "0830"),
    ("Alice Springs", "NT", "0870"),
]
STREET_NAMES = [
    "Banksia", "Wattle", "Jacaranda", "Bottlebrush", "Kookaburra", "Station", "Railway",
    "Church", "Pacific", "Ocean View", "Hilltop", "Federation", "Anzac", "Bushland",
    "Coolabah", "Lakeside", "Grevillea", "Boundary", "Mountain", "Waratah",
]
STREET_TYPES = [
    "Street", "St", "Road", "Rd", "Avenue", "Ave", "Drive", "Dr", "Court", "Ct", "Crescent",
    "Place", "Parade", "Terrace", "Close", "Way", "Grove", "Circuit", "Cct", "Esplanade",
    "Lane", "Boulevard", "Rise", "Walk", "Square", "Highway",
]
EMAIL_DOMAINS = [
    "bigpond.com", "optusnet.com.au", "gmail.com", "outlook.com.au", "icloud.com",
    "iinet.net.au", "tpg.com.au", "hotmail.com",
]
VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
BSB_PREFIXES = ["062", "063", "082", "083", "032", "033", "012", "013", "484", "733", "923"]
CAR_MODELS = ["Toyota Corolla", "Mazda CX-5", "Hyundai i30", "Ford Ranger", "Kia Cerato", "Mitsubishi Triton"]
HOSPITALS = ["Westmead Hospital", "Royal Melbourne Hospital", "Princess Alexandra Hospital", "Flinders Medical Centre"]
LABEL_TYPOS = {
    "Medicare": ["Medicre", "Medicare", "MEDICARE", "medicare"],
    "Policy": ["Polcy", "Policy", "POLICY", "pol"],
    "Address": ["Adress", "Address", "Addr", "address"],
    "Phone": ["Ph", "Phone", "Mob", "ph#"],
    "Licence": ["Licence", "License", "Lic", "DL"],
    "Claim": ["Claim", "Clm", "CLAIM", "claim"],
}
OCR_SUBS = {"0": "O", "1": "l", "5": "S", "8": "B"}
SPOKEN_DIGITS = ["oh", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

class Doc:
    """Builds one document, recording gold spans as values are written.

    ``lowercase`` lowercases every chunk; ``typo_labels`` misspells label words
    passed through :meth:`label`; ``ocr`` applies OCR-style substitutions to
    some values; ``nbsp`` uses non-breaking spaces inside some numbers.
    """

    def __init__(self, rng: random.Random, fake: Faker, tags: set[str]):
        self.rng = rng
        self.fake = fake
        self.tags = tags
        self.parts: list[str] = []
        self.spans: list[dict] = []
        self.pos = 0

    # -- writing ----------------------------------------------------------
    def _case(self, s: str) -> str:
        return s.lower() if "lowercase" in self.tags else s

    def w(self, text: str) -> None:
        text = self._case(text)
        self.parts.append(text)
        self.pos += len(text)

    def label(self, word: str) -> None:
        if "typo_labels" in self.tags and word in LABEL_TYPOS:
            word = self.rng.choice(LABEL_TYPOS[word])
        self.w(word)

    def pii(self, label: str, value: str, variant: str) -> None:
        value = self._case(value)
        if "ocr" in self.tags and self.rng.random() < 0.3 and any(c in OCR_SUBS for c in value):
            chars = list(value)
            idx = [i for i, c in enumerate(chars) if c in OCR_SUBS]
            i = self.rng.choice(idx)
            chars[i] = OCR_SUBS[chars[i]]
            value, variant = "".join(chars), f"{variant}+ocr"
        if ("nbsp" in self.tags and " " in value and any(c.isdigit() for c in value)
                and label != "AU_ADDRESS" and self.rng.random() < 0.5):
            value, variant = value.replace(" ", NBSP), f"{variant}+nbsp"
        self.parts.append(value)
        self.spans.append({"start": self.pos, "end": self.pos + len(value), "label": label,
                           "value": value, "variant": variant})
        self.pos += len(value)

    # -- value generators -------------------------------------------------
    def choose(self, options: list) -> object:
        return self.rng.choice(options)

    def person(self) -> tuple[str, str]:
        if self.rng.random() < 0.55:
            return self.fake.first_name(), self.fake.last_name()
        return self.choose(GIVEN_NAMES), self.choose(SURNAMES)

    def name(self, first: str, last: str, forms: list[str] | None = None) -> None:
        """Write a PERSON span in one of several surface forms.

        Titles are written outside the span: "Mr" is not personal data.
        """
        form = self.choose(forms or ["full", "full", "initial", "title", "surname_first", "upper", "middle"])
        if form == "full":
            self.pii("PERSON", f"{first} {last}", form)
        elif form == "initial":
            self.pii("PERSON", f"{first[0]}. {last}", form)
        elif form == "title":
            self.w(self.choose(["Mr ", "Mrs ", "Ms ", "Dr "]))
            self.pii("PERSON", self.choose([last, f"{first} {last}"]), form)
        elif form == "surname_first":
            self.pii("PERSON", f"{last.upper()}, {first}", form)
        elif form == "upper":
            self.pii("PERSON", f"{first} {last}".upper(), form)
        elif form == "middle":
            self.pii("PERSON", f"{first} {self.choose(string.ascii_uppercase)}. {last}", form)
        elif form == "first_only":
            self.pii("PERSON", first, form)
        else:  # pragma: no cover - guarded by the choices above
            raise ValueError(form)

    def date(self, start_years: int = 3, dob: bool = False) -> None:
        if dob:
            d = date(1940, 1, 1) + timedelta(days=self.rng.randint(0, 365 * 63))
        else:
            d = date(2026, 10, 1) - timedelta(days=self.rng.randint(0, max(60, 365 * start_years)))
        form = self.choose(["dmy_slash", "dmy_short", "long", "dmonY", "iso", "ordinal", "dmy_dot"])
        day = d.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        value = {
            "dmy_slash": d.strftime("%d/%m/%Y"),
            "dmy_short": f"{day}/{d.month}/{d.strftime('%y')}",
            "long": f"{day} {d.strftime('%B %Y')}",
            "dmonY": d.strftime("%d-%b-%Y"),
            "iso": d.isoformat(),
            "ordinal": f"{day}{suffix} of {d.strftime('%B %Y')}",
            "dmy_dot": d.strftime("%d.%m.%Y"),
        }[form]
        self.pii("DATE", value, form)

    def mobile(self) -> None:
        n = f"4{self.rng.randint(0, 99):02d}{self.rng.randint(0, 999999):06d}"
        form = self.choose(["spaced", "compact", "intl", "hyphen", "intl_compact"])
        value = {
            "spaced": f"0{n[:3]} {n[3:6]} {n[6:]}",
            "compact": f"0{n}",
            "intl": f"+61 {n[:3]} {n[3:6]} {n[6:]}",
            "hyphen": f"0{n[:3]}-{n[3:6]}-{n[6:]}",
            "intl_compact": f"+61{n}",
        }[form]
        self.pii("AU_PHONE", value, f"mobile_{form}")

    def landline(self) -> None:
        area = self.choose(["2", "3", "7", "8"])
        n = f"{self.rng.randint(2, 9)}{self.rng.randint(0, 9999999):07d}"
        form = self.choose(["bracket", "spaced", "intl"])
        value = {
            "bracket": f"(0{area}) {n[:4]} {n[4:]}",
            "spaced": f"0{area} {n[:4]} {n[4:]}",
            "intl": f"+61 {area} {n[:4]} {n[4:]}",
        }[form]
        self.pii("AU_PHONE", value, f"landline_{form}")

    def spoken_mobile(self) -> None:
        n = f"04{self.rng.randint(0, 99):02d}{self.rng.randint(0, 999999):06d}"
        groups = [n[:4], n[4:7], n[7:]]
        value = ", ".join(" ".join(SPOKEN_DIGITS[int(c)] for c in g) for g in groups)
        self.pii("AU_PHONE", value, "spoken")

    def intl_phone(self) -> None:
        value = self.choose([
            f"+44 7{self.rng.randint(100, 999)} {self.rng.randint(100000, 999999)}",
            f"+64 21 {self.rng.randint(100, 999)} {self.rng.randint(1000, 9999)}",
            f"+65 {self.rng.randint(8000, 9999)} {self.rng.randint(1000, 9999)}",
            f"+1 {self.rng.randint(200, 999)}-{self.rng.randint(200, 999)}-{self.rng.randint(1000, 9999)}",
        ])
        self.pii("PHONE_INTL", value, "intl")

    def email(self, first: str, last: str) -> None:
        clean = lambda s: "".join(c for c in s.lower() if c.isascii() and c.isalnum())  # noqa: E731
        f, l_ = clean(first) or "user", clean(last) or "mail"
        local = self.choose([f"{f}.{l_}", f"{f[0]}{l_}{self.rng.randint(1, 99)}", f"{f}_{l_}", f"{l_}.{f[0]}"])
        self.pii("EMAIL_ADDRESS", f"{local}@{self.choose(EMAIL_DOMAINS)}", "email")

    def address(self, forms: list[str] | None = None) -> None:
        suburb, state, pc = self.choose(SUBURBS)
        street = f"{self.choose(STREET_NAMES)} {self.choose(STREET_TYPES)}"
        num = self.rng.randint(1, 350)
        form = self.choose(forms or ["one_line", "one_line", "multi_line", "no_comma", "unit_slash",
                                     "unit_word", "level", "lower", "po_box"])
        value = {
            "one_line": f"{num} {street}, {suburb} {state} {pc}",
            "multi_line": f"{num} {street}\n{suburb} {state} {pc}",
            "no_comma": f"{num} {street} {suburb} {state} {pc}",
            "unit_slash": f"{self.rng.randint(1, 40)}/{num} {street}, {suburb} {state} {pc}",
            "unit_word": f"Unit {self.rng.randint(1, 40)}, {num} {street}, {suburb} {state} {pc}",
            "level": f"Level {self.rng.randint(1, 20)}, {num} {street}, {suburb} {state} {pc}",
            "lower": f"{num} {street}, {suburb} {state} {pc}".lower(),
            "po_box": f"PO Box {self.rng.randint(10, 9999)}, {suburb} {state} {pc}",
        }[form]
        self.pii("AU_ADDRESS", value, form)

    def _digits(self, n: int) -> str:
        return "".join(str(self.rng.randint(0, 9)) for _ in range(n))

    def _fmt_groups(self, digits: str, groups: list[int], kind: str) -> tuple[str, str]:
        form = self.choose(["spaced", "compact", "hyphen"])
        if form == "compact":
            return digits, form
        out, i = [], 0
        for g in groups:
            out.append(digits[i:i + g])
            i += g
        return (" " if form == "spaced" else "-").join(out), form

    def tfn(self) -> None:
        while True:
            d = self._digits(9)
            if d[0] != "0" and tfn_valid(d):
                break
        value, form = self._fmt_groups(d, [3, 3, 3], "tfn")
        self.pii("AU_TFN", value, form)

    def abn(self) -> None:
        while True:
            d = str(self.rng.randint(10, 99)) + self._digits(9)
            if abn_valid(d):
                break
        value, form = self._fmt_groups(d, [2, 3, 3, 3], "abn")
        self.pii("AU_ABN", value, form)

    def acn(self) -> None:
        body = self._digits(8)
        check = (10 - sum(int(c) * w for c, w in zip(body, ACN_WEIGHTS)) % 10) % 10
        d = body + str(check)
        value, form = self._fmt_groups(d, [3, 3, 3], "acn")
        self.pii("AU_ACN", value, form)

    def medicare(self) -> None:
        first = self.choose("23456")
        body = first + self._digits(7)
        check = sum(int(c) * w for c, w in zip(body, MEDICARE_WEIGHTS)) % 10
        d = body + str(check) + str(self.rng.randint(1, 9))
        value, form = self._fmt_groups(d, [4, 5, 1], "medicare")
        self.pii("AU_MEDICARE", value, form)

    def crn(self) -> None:
        d = self._digits(9)
        letter = self.choose("ABCHJKLSTVX")
        value = self.choose([f"{d[:3]} {d[3:6]} {d[6:]}{letter}", f"{d}{letter}"])
        self.pii("AU_CENTRELINK_CRN", value, "crn")

    def licence(self) -> None:
        state = self.choose(["NSW", "VIC", "QLD", "WA", "SA"])
        digits = {"NSW": 8, "VIC": 9, "QLD": 9, "WA": 7, "SA": 6}[state]
        value = self._digits(digits) if state != "SA" else self.choose("SNDTV") + self._digits(5)
        self.pii("AU_DRIVERS_LICENSE", value, f"licence_{state}")

    def passport(self) -> None:
        value = self.choose([self.choose("NPEMR") + self._digits(7),
                             self.choose(["PA", "PB", "PC", "RA"]) + self._digits(7)])
        self.pii("AU_PASSPORT", value, "passport")

    def bsb(self) -> None:
        value = f"{self.choose(BSB_PREFIXES)}-{self._digits(3)}"
        self.pii("AU_BSB", value, "bsb")

    def account(self) -> None:
        value = self.choose([self._digits(8), self._digits(9), f"{self._digits(4)} {self._digits(4)}"])
        self.pii("AU_ACCOUNT_NUMBER", value, "account")

    def card(self) -> None:
        while True:
            d = self.choose(["4", "51", "52", "53"]) + self._digits(14)
            d = d[:15]
            for last in "0123456789":
                if luhn_valid(d + last):
                    d += last
                    break
            if len(d) == 16:
                break
        value, form = self._fmt_groups(d, [4, 4, 4, 4], "card")
        self.pii("CREDIT_CARD_NUMBER", value, form)

    def policy(self) -> None:
        y = self.rng.randint(19, 26)
        value, form = self.choose([
            (f"MOT-20{y}-{self._digits(6)}", "mot_year"),
            (f"HOM{self._digits(9)}", "hom_digits"),
            (f"PL/{y}/{self._digits(6)}", "slash"),
            (f"TRV{self._digits(7)}", "trv_digits"),
            (f"POL{self._digits(8)}", "pol_digits"),
            (f"{self.choose(['AU', 'NR', 'QB'])}{self._digits(8)}", "two_letter"),
        ])
        self.pii("POLICY_NUMBER", value, form)

    def claim(self) -> None:
        value, form = self.choose([
            (f"CLM-{self._digits(7)}", "clm_hyphen"),
            (f"C20{self.rng.randint(22, 26)}/{self._digits(6)}", "c_year_slash"),
            (f"WC-{self._digits(2)}-{self._digits(6)}", "wc"),
            (f"{self._digits(8)}", "digits_only"),
        ])
        self.pii("INSURANCE_CLAIM_NUMBER", value, form)

    def rego(self) -> None:
        L = lambda n: "".join(self.choose(string.ascii_uppercase) for _ in range(n))  # noqa: E731
        value, form = self.choose([
            (f"{L(2)}{self._digits(2)}{L(2)}", "nsw"),
            (f"{self._digits(1)}{L(2)}{self._digits(1)}{L(2)}", "vic"),
            (f"{self._digits(3)}{L(3)}", "qld"),
            (f"{L(3)}-{self._digits(3)}", "hyphen"),
            (f"{L(3)} {self._digits(3)}", "spaced"),
        ])
        self.pii("VEHICLE_REGISTRATION", value, form)

    def vin(self) -> None:
        self.pii("VIN", "".join(self.choose(VIN_CHARS) for _ in range(17)), "vin")

    def amount(self) -> str:
        return f"${self.rng.randint(150, 48000):,}.{self.rng.randint(0, 99):02d}"

    def build(self) -> tuple[str, list[dict]]:
        return "".join(self.parts), self.spans


# ---------------------------------------------------------------------------
# Template families
# ---------------------------------------------------------------------------

def motor_claim_form(d: Doc) -> None:
    first, last = d.person()
    d.w("MOTOR CLAIM LODGEMENT\n\n")
    d.w("Insured name: "); d.name(first, last, ["full", "upper", "surname_first"])  # noqa: E702
    d.w("\nDate of birth: "); d.date(dob=True)  # noqa: E702
    d.w("\n"); d.label("Phone"); d.w(": "); d.mobile()  # noqa: E702
    d.w("\nEmail: "); d.email(first, last)  # noqa: E702
    d.w("\nResidential "); d.label("Address"); d.w(": "); d.address(["one_line", "unit_slash", "no_comma"])  # noqa: E702
    d.w("\n"); d.label("Policy"); d.w(" no: "); d.policy()  # noqa: E702
    d.w("\n"); d.label("Licence"); d.w(" number: "); d.licence()  # noqa: E702
    d.w(f"\nVehicle: {d.choose(CAR_MODELS)}, registration "); d.rego()  # noqa: E702
    d.w("\nVIN: "); d.vin()  # noqa: E702
    d.w("\nDate of incident: "); d.date(1)  # noqa: E702
    d.w(f"\nEstimated repair cost: {d.amount()}\n")
    d.w("Description: rear-ended at lights, other party admitted fault. Driver of other vehicle was ")
    o_first, o_last = d.person()
    d.name(o_first, o_last, ["full", "initial"])
    d.w(", rego "); d.rego(); d.w(".\n")  # noqa: E702


def call_transcript(d: Doc) -> None:
    first, last = d.person()
    agent_first, agent_last = d.person()
    d.w("Call recording transcript\n")
    d.w("Agent: Thanks for calling, you're speaking with "); d.name(agent_first, agent_last, ["first_only"]); d.w(". Who am I speaking with?\n")  # noqa: E501,E702
    d.w("Caller: It's "); d.name(first, last, ["full"]); d.w(".\n")  # noqa: E702
    d.w("Agent: Can I confirm your date of birth?\nCaller: Yeah, "); d.date(dob=True); d.w(".\n")  # noqa: E702
    d.w("Agent: And the best number to reach you on?\nCaller: ")
    if d.rng.random() < 0.5:
        d.spoken_mobile()
    else:
        d.mobile()
    d.w(".\nAgent: For ID can I take your licence or passport number?\nCaller: Passport is ")
    d.passport()
    d.w(".\nAgent: Thanks "); d.name(first, last, ["first_only"]); d.w(". And your claim number?\nCaller: ")  # noqa: E702
    d.claim()
    d.w(".\nAgent: I'll email the forms to ")
    d.email(first, last)
    d.w(", is that right?\nCaller: Yep.\n")


def home_assessor_report(d: Doc) -> None:
    first, last = d.person()
    d.w("Assessor Report - Home and Contents\n\n")
    d.w("Property: "); d.address(["multi_line", "one_line", "level", "unit_word"]); d.w("\n")  # noqa: E702
    d.w("Policyholder: "); d.name(first, last, ["full", "title", "middle"]); d.w("\n")  # noqa: E702
    d.w("Inspection date: "); d.date(1); d.w("\n")  # noqa: E702
    d.w("Claim reference: "); d.claim(); d.w("\n\n")  # noqa: E702
    d.w("Storm damage to the roof and ceiling of the rear bedroom. The insured advised the leak began ")
    d.w("after heavy rain. Builder engaged: ")
    b_first, b_last = d.person()
    d.name(b_first, b_last, ["full"])
    d.w(" trading as Coastal Roofing, ABN "); d.abn()  # noqa: E702
    d.w(f". Quote received for {d.amount()}. Contact the builder on "); d.landline(); d.w(".\n")  # noqa: E702


def workers_comp_note(d: Doc) -> None:
    first, last = d.person()
    d.w("Workers compensation file note\n")
    d.w("Worker: "); d.name(first, last, ["surname_first", "full", "upper"])  # noqa: E702
    d.w("   DOB "); d.date(dob=True)  # noqa: E702
    d.w("\nEmployer: Allied Logistics Pty Ltd (ACN "); d.acn(); d.w(")")  # noqa: E702
    d.w("\nWorker TFN for PAYG withholding: "); d.tfn()  # noqa: E702
    d.w("\nWeekly payments to BSB "); d.bsb(); d.w(" account "); d.account()  # noqa: E702
    d.w("\nInjury: lower back strain lifting stock on "); d.date(1)  # noqa: E702
    d.w(". Treating GP is Dr "); g_first, g_last = d.person(); d.name(g_first, g_last, ["full"])  # noqa: E702
    d.w(". Worker can be contacted on "); d.mobile(); d.w(".\n")  # noqa: E702


def email_thread(d: Doc) -> None:
    first, last = d.person()
    s_first, s_last = d.person()
    d.w("From: "); d.email(s_first, s_last); d.w("\nTo: "); d.email(first, last)  # noqa: E702
    d.w("\nSubject: RE: Claim "); d.claim(); d.w("\n\nHi "); d.name(first, last, ["first_only"])  # noqa: E702
    d.w(",\n\nThanks for sending the photos. We still need a copy of your Medicare card (")
    d.label("Medicare"); d.w(" no. "); d.medicare(); d.w(") and the hospital invoice.\n\n")  # noqa: E702
    d.w("Kind regards,\n"); d.name(s_first, s_last, ["full"]); d.w("\nClaims Consultant\n")  # noqa: E702
    d.landline()
    d.w("\n\n> On "); d.date(1); d.w(", "); d.name(first, last, ["full"]); d.w(" wrote:\n")  # noqa: E702
    d.w("> I'm overseas until next month, call me on "); d.intl_phone(); d.w(" if urgent.\n")  # noqa: E702


def remittance_advice(d: Doc) -> None:
    first, last = d.person()
    d.w("REMITTANCE ADVICE\n")
    d.w("Payee: "); d.name(first, last, ["upper", "full", "initial"])  # noqa: E702
    d.w("\nPaid to BSB: "); d.bsb(); d.w("  Account: "); d.account()  # noqa: E702
    d.w(f"\nAmount: {d.amount()}   Invoice INV-{d.rng.randint(10000, 99999)}")
    d.w("\nRefund of premium charged to card "); d.card()  # noqa: E702
    d.w("\nPayment date: "); d.date(1)  # noqa: E702
    d.w("\n"); d.label("Policy"); d.w(": "); d.policy()  # noqa: E702
    d.w("\nPostal address: "); d.address(["po_box", "one_line"]); d.w("\n")  # noqa: E702


def diary_entries(d: Doc) -> None:
    first, last = d.person()
    d.w("Claim diary\n")
    d.date(0); d.w(" 09:14 - spoke w insd "); d.name(first, last, ["full", "first_only"])  # noqa: E702
    d.w(" re rego "); d.rego(); d.w(", cx says other driver fled scene\n")  # noqa: E702
    d.date(0); d.w(" 11:02 - "); d.label("Phone"); d.w(" "); d.mobile(); d.w(" no answer, left vm\n")  # noqa: E702
    d.date(0); d.w(" 15:40 - insd called back, confirmed adr "); d.address(["lower", "no_comma", "one_line"])  # noqa: E702
    d.w("\n"); d.date(0); d.w(" 16:05 - centrelink crn "); d.crn(); d.w(" provided for hardship\n")  # noqa: E702


def ctp_injury_note(d: Doc) -> None:
    first, last = d.person()
    d.w("CTP injury claim - initial notification\n")
    d.w("Injured person: "); d.name(first, last, ["full", "middle", "title"])  # noqa: E702
    d.w(", aged "); d.w(str(d.rng.randint(18, 85)))  # noqa: E702
    d.w("\nAt-fault vehicle "); d.rego(); d.w(" driven by "); o_f, o_l = d.person(); d.name(o_f, o_l, ["full", "initial"])  # noqa: E702,E501
    d.w(" (licence "); d.licence(); d.w(")")  # noqa: E702
    d.w("\nAccident on "); d.date(1); d.w(" near "); d.address(["one_line", "no_comma"])  # noqa: E702
    d.w(f"\nTaken to {d.choose(HOSPITALS)}. Medicare "); d.medicare()  # noqa: E702
    d.w("\nContact: "); d.mobile(); d.w(" / "); d.email(first, last); d.w("\n")  # noqa: E702


# --- Held-out test families ---------------------------------------------------

def income_protection_medical(d: Doc) -> None:
    first, last = d.person()
    d.w("Income Protection - Attending Doctor's Statement\n\n")
    d.w("Patient: "); d.name(first, last, ["full", "surname_first", "title"]); d.w("\n")  # noqa: E702
    d.w("Date of birth: "); d.date(dob=True); d.w("   "); d.label("Medicare"); d.w(": "); d.medicare(); d.w("\n")  # noqa: E702,E501
    d.w("Home address: "); d.address(); d.w("\n")  # noqa: E702
    d.w("Policy number "); d.policy(); d.w(", claim "); d.claim(); d.w("\n\n")  # noqa: E702
    d.w("I first saw the patient on "); d.date(1); d.w(" for a work-related shoulder injury. ")  # noqa: E702
    d.w("They are unfit for work until review. Benefits are to be paid to BSB "); d.bsb()  # noqa: E702
    d.w(" account "); d.account(); d.w(". For tax purposes the TFN supplied is "); d.tfn(); d.w(".\n\n")  # noqa: E702
    doc_f, doc_l = d.person()
    d.w("Dr "); d.name(doc_f, doc_l, ["full"]); d.w("\n"); d.landline(); d.w("\n")  # noqa: E702


def complaint_letter(d: Doc) -> None:
    first, last = d.person()
    d.name(first, last, ["full", "title"]); d.w("\n")  # noqa: E702
    d.address(["multi_line"]); d.w("\n"); d.date(0); d.w("\n\n")  # noqa: E702
    d.w("Internal Dispute Resolution\n\nRe: claim "); d.claim(); d.w(" under policy "); d.policy()  # noqa: E702
    d.w("\n\nTo whom it may concern,\n\nI am writing to complain about how my claim has been handled. ")
    d.w("Your consultant "); c_f, c_l = d.person(); d.name(c_f, c_l, ["full", "first_only"])  # noqa: E702
    d.w(" promised a call back on "); d.date(0); d.w(" that never came. ")  # noqa: E702
    d.w("Please contact me on "); d.mobile(); d.w(" or at "); d.email(first, last); d.w(".\n\nYours faithfully,\n")  # noqa: E702,E501
    d.name(first, last, ["full", "initial"]); d.w("\n")  # noqa: E702


def travel_claim(d: Doc) -> None:
    first, last = d.person()
    d.w("Travel insurance claim\n")
    d.w("Traveller: "); d.name(first, last, ["full", "upper"]); d.w("  Passport: "); d.passport()  # noqa: E702
    d.w("\nDeparted "); d.date(1); d.w(", returned "); d.date(1)  # noqa: E702
    d.w("\nPolicy "); d.policy(); d.w("\nOverseas contact: "); d.intl_phone()  # noqa: E702
    d.w("\nAU mobile: "); d.mobile(); d.w("\nEmail: "); d.email(first, last)  # noqa: E702
    d.w(f"\nMedical expenses of {d.amount()} were paid by card "); d.card()  # noqa: E702
    d.w(" and reimbursement is requested.\n")


def tabular_export(d: Doc) -> None:
    d.w("name,dob,mobile,email,address,policy,tfn\n")
    for _ in range(d.rng.randint(2, 4)):
        first, last = d.person()
        d.name(first, last, ["full", "surname_first"] if d.rng.random() < 0.7 else ["upper"])
        d.w(","); d.date(dob=True); d.w(","); d.mobile(); d.w(","); d.email(first, last)  # noqa: E702
        d.w(',"'); d.address(["one_line", "unit_slash"]); d.w('",'); d.policy(); d.w(","); d.tfn(); d.w("\n")  # noqa: E702


FAMILIES: dict[str, tuple[Callable[[Doc], None], str, list[str]]] = {
    # name: (builder, split, document-level noise tags that may apply)
    "motor_claim_form": (motor_claim_form, "dev", ["typo_labels", "nbsp"]),
    "call_transcript": (call_transcript, "dev", ["lowercase"]),
    "home_assessor_report": (home_assessor_report, "dev", ["ocr"]),
    "workers_comp_note": (workers_comp_note, "dev", ["nbsp", "ocr"]),
    "email_thread": (email_thread, "dev", ["typo_labels"]),
    "remittance_advice": (remittance_advice, "dev", ["ocr", "typo_labels"]),
    "diary_entries": (diary_entries, "dev", ["lowercase", "typo_labels"]),
    "ctp_injury_note": (ctp_injury_note, "dev", ["nbsp"]),
    "income_protection_medical": (income_protection_medical, "test", ["ocr", "typo_labels"]),
    "complaint_letter": (complaint_letter, "test", ["lowercase"]),
    "travel_claim": (travel_claim, "test", ["nbsp", "typo_labels"]),
    "tabular_export": (tabular_export, "test", []),
}


def generate() -> dict[str, list[dict]]:
    """Generate both splits deterministically. Each family has its own seed."""
    from faker import Faker

    out: dict[str, list[dict]] = {"dev": [], "test": []}
    for family, (builder, split, noise) in FAMILIES.items():
        family_seed = SEED ^ zlib.crc32(family.encode())
        rng = random.Random(family_seed)
        fake = Faker("en_AU")
        fake.seed_instance(family_seed)
        for i in range(DOCS_PER_FAMILY):
            tags = {t for t in noise if rng.random() < 0.35}
            doc = Doc(rng, fake, tags)
            builder(doc)
            text, spans = doc.build()
            for s in spans:
                if text[s["start"]:s["end"]] != s["value"]:
                    raise AssertionError(f"offset mismatch in {family} #{i}: {s}")
            out[split].append({
                "id": f"{family}-{i:03d}", "family": family, "tags": sorted(tags),
                "text": text, "spans": spans,
            })
    return out


def _write_jsonl(path: Path, rows: list[dict]) -> str:
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    import faker

    splits = generate()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "seed": SEED,
        "docs_per_family": DOCS_PER_FAMILY,
        "generator": "bench/make_au_challenge.py",
        "faker_version": faker.VERSION,
        "python": platform.python_version(),
        "splits": {},
    }
    for split, path in (("dev", DEV_FILE), ("test", TEST_FILE)):
        rows = splits[split]
        manifest["splits"][split] = {
            "file": path.name,
            "sha256": _write_jsonl(path, rows),
            "documents": len(rows),
            "families": sorted({r["family"] for r in rows}),
            "labels": dict(sorted(Counter(s["label"] for r in rows for s in r["spans"]).items())),
            "variants": dict(sorted(Counter(s["variant"] for r in rows for s in r["spans"]).items())),
            "tags": dict(sorted(Counter(t for r in rows for t in r["tags"]).items())),
        }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    for split, info in manifest["splits"].items():
        print(f"{split}: {info['documents']} docs, {sum(info['labels'].values())} spans -> {info['file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
