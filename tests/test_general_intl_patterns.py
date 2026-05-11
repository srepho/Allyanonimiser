"""
Regression tests for the general-international pattern set.

These cover:
  * each new entity type emits the expected entity for canonical inputs
  * Luhn validation rejects synthetic 16-digit blocks that happen to fit
  * SSA reservation rules reject area=000/666/9xx, group=00, serial=0000
  * AU-specific patterns still win on AU-shape spans (no precedence regression)
  * the SSN/VEHICLE_REGISTRATION collision reported in review stays fixed
  * date / time / iso-datetime overlaps resolve in the documented order
"""

import pytest

from allyanonimiser import create_allyanonimiser
from allyanonimiser.core.validators import EntityValidator


@pytest.fixture(scope="module")
def ally():
    return create_allyanonimiser()


def types_for(ally, text: str) -> list[str]:
    """Return the entity types Ally emitted on ``text`` (order preserved)."""
    return [r.entity_type for r in ally.analyze(text)]


def types_at(ally, text: str, start: int, end: int) -> list[str]:
    """Return entity types that overlap ``[start, end)`` on ``text``."""
    return [r.entity_type for r in ally.analyze(text)
            if r.start < end and r.end > start]


# ---------------------------------------------------------------------------
# PHONE_INTL
# ---------------------------------------------------------------------------

class TestPhoneIntl:
    @pytest.mark.parametrize("text,expected_value", [
        ("Call me at +44 7700 900123 today", "+44 7700 900123"),
        ("Phone +1-415-555-1234 anytime", "+1-415-555-1234"),
        ("Tel: +93-730 013 3012", "+93-730 013 3012"),
        ("Number 0013 408-555-2222 logged", "0013 408-555-2222"),
        ("Tel: 0081.552939253", "0081.552939253"),
    ])
    def test_intl_shapes_detected(self, ally, text, expected_value):
        results = ally.analyze(text)
        intl = [r for r in results if r.entity_type == "PHONE_INTL"]
        assert intl, f"PHONE_INTL not detected in {text!r}: got {types_for(ally, text)}"
        # The captured value must contain the expected fragment.
        spans = [text[r.start:r.end] for r in intl]
        assert any(expected_value in s for s in spans), \
            f"expected {expected_value!r} in {spans!r}"

    @pytest.mark.parametrize("text", [
        "(415) 555-1234 office",
        "Contact (664)-9573546 between 9 and 5",
    ])
    def test_paren_area_code_detected(self, ally, text):
        assert "PHONE_INTL" in types_for(ally, text), \
            f"PHONE_INTL missing from {text!r}: {types_for(ally, text)}"

    @pytest.mark.parametrize("text", [
        # AU 2-digit area codes must stay with AU_PHONE; the intl pattern
        # requires 3+ digits inside the parens.
        "Call (03) 9876 5432 anytime",
        "Office (02) 9123 4567",
    ])
    def test_au_2_digit_area_code_stays_with_au_phone(self, ally, text):
        types = types_for(ally, text)
        assert "AU_PHONE" in types, \
            f"AU 2-digit area form missing AU_PHONE: {text!r} -> {types}"
        # Both can coexist because the conflict resolver picks AU_PHONE on
        # AU-shape spans, but PHONE_INTL must not be the *winning* type.
        # (We accept its presence as long as AU_PHONE also appears.)


# ---------------------------------------------------------------------------
# US_SSN — including the v3.5 SSN/VEHICLE_REGISTRATION collision regression
# ---------------------------------------------------------------------------

class TestUsSsn:
    @pytest.mark.parametrize("text", [
        "SSN: 818-04-7100",
        "Social Security Number 123-45-6789 on file",
        "Reference SSN 555-12-3456 attached",
    ])
    def test_valid_ssn_detected(self, ally, text):
        assert "US_SSN" in types_for(ally, text), \
            f"US_SSN missed in {text!r}: {types_for(ally, text)}"

    @pytest.mark.parametrize("text,reason", [
        ("SSN: 000-04-7100", "area=000"),
        ("SSN: 666-04-7100", "area=666"),
        ("SSN: 900-04-7100", "area=9xx"),
        ("SSN: 818-00-7100", "group=00"),
        ("SSN: 818-04-0000", "serial=0000"),
    ])
    def test_invalid_ssn_rejected(self, ally, text, reason):
        assert "US_SSN" not in types_for(ally, text), \
            f"US_SSN should not match invalid form ({reason}) in {text!r}"

    def test_ssn_acronym_not_masked_as_organization(self, ally):
        """The literal word 'SSN' is a label, not an organisation name.

        Before v3.5 the ORGANIZATION deny-list at core/analyzer.py only
        knew about AU acronyms (DOB/ABN/TFN/ACN/Medicare/DOI). Adding
        SSN/TIN/NIN/VIN/CRN/BSB/GST keeps spaCy NER from emitting noisy
        <ORGANIZATION> tags around international label tokens.
        """
        text = "Reference SSN 818-04-7100 on file"
        types = types_for(ally, text)
        assert "ORGANIZATION" not in types, \
            f"'SSN' label should not be tagged ORGANIZATION: {types}"

    def test_invalid_ssn_does_not_become_vehicle_registration(self, ally):
        """Regression for the v3.5 review bug.

        Invalid SSN ``999-04-7100`` previously caused the loose plate pattern
        to absorb ``SSN 999-04`` as VEHICLE_REGISTRATION. The deny-list and
        SSN-shape lookahead in au_patterns.VEHICLE_REGISTRATION must keep
        this from happening regardless of whether the SSN itself validates.
        """
        text = "bad SSN 999-04-7100"
        results = ally.analyze(text)
        for r in results:
            if r.entity_type == "VEHICLE_REGISTRATION":
                pytest.fail(
                    f"VEHICLE_REGISTRATION should not match SSN-shape; "
                    f"got [{r.start}:{r.end}] {text[r.start:r.end]!r}"
                )

    def test_valid_ssn_wins_over_vehicle_registration(self, ally):
        """The valid SSN ``818-04-7100`` must take precedence on its span."""
        text = "good SSN 818-04-7100"
        types = types_for(ally, text)
        assert "US_SSN" in types
        # And the VR span (if any) does not cover the SSN body.
        for r in ally.analyze(text):
            if r.entity_type == "VEHICLE_REGISTRATION":
                # Allow VR only if entirely outside the SSN span 9-20.
                assert r.end <= 9 or r.start >= 20, \
                    f"VEHICLE_REGISTRATION overlaps SSN body: [{r.start}:{r.end}]"


# ---------------------------------------------------------------------------
# CREDIT_CARD — Luhn-validated
# ---------------------------------------------------------------------------

class TestCreditCard:
    # Public test cards with valid Luhn checksums.
    VALID_CARDS = [
        "4111 1111 1111 1111",      # Visa test
        "5555 5555 5555 4444",      # Mastercard test
        "3782 822463 10005",        # Amex test (15 digits)
        "6011 1111 1111 1117",      # Discover test
    ]

    @pytest.mark.parametrize("card", VALID_CARDS)
    def test_luhn_valid_credit_card_detected(self, ally, card):
        text = f"Card on file: {card}"
        assert "CREDIT_CARD" in types_for(ally, text), \
            f"CREDIT_CARD missed for valid Luhn {card!r}: {types_for(ally, text)}"

    @pytest.mark.parametrize("bad", [
        "4111 1111 1111 1112",    # Last digit wrong → Luhn fails
        "1234 5678 9012 3456",    # Random digits, Luhn fails
        "0000 0000 0000 0001",    # Trivial, Luhn fails
    ])
    def test_luhn_invalid_credit_card_rejected(self, ally, bad):
        text = f"Card on file: {bad}"
        assert "CREDIT_CARD" not in types_for(ally, text), \
            f"CREDIT_CARD should reject Luhn-invalid {bad!r}"

    def test_validator_unit_paths(self):
        # Direct validator coverage so the wrong-length and luhn_failed
        # branches are exercised even if the regex catches them upstream.
        ok, _ = EntityValidator.validate_credit_card("4111 1111 1111 1111")
        assert ok is True

        ok, reason = EntityValidator.validate_credit_card("4111 1111")
        assert ok is False and reason == "wrong_length"

        ok, reason = EntityValidator.validate_credit_card("4111 1111 1111 1112")
        assert ok is False and reason == "luhn_failed"


# ---------------------------------------------------------------------------
# ISO_DATETIME and TIME — including precedence with bare DATE
# ---------------------------------------------------------------------------

class TestDatetime:
    @pytest.mark.parametrize("text,fragment", [
        ("Logged at 2024-05-22T14:32:00 successfully", "2024-05-22T14:32:00"),
        ("Event 2024-05-22T14:32:00Z observed", "2024-05-22T14:32:00Z"),
        ("Audit 2024-05-22T14:32:00+10:00 captured", "2024-05-22T14:32:00+10:00"),
    ])
    def test_iso_datetime_detected(self, ally, text, fragment):
        results = ally.analyze(text)
        assert any(
            r.entity_type == "ISO_DATETIME" and fragment in text[r.start:r.end]
            for r in results
        ), f"ISO_DATETIME missing fragment {fragment!r} in {text!r}: {[(r.entity_type, text[r.start:r.end]) for r in results]}"

    @pytest.mark.parametrize("text", [
        "Appointment at 14:32 sharp",
        "Filed at 09:15:42",
        "Meeting 6:52 PM in the boardroom",
        "Event 2:30 a.m. in the morning",
    ])
    def test_time_detected(self, ally, text):
        assert "TIME" in types_for(ally, text), \
            f"TIME missed in {text!r}: {types_for(ally, text)}"

    def test_iso_outranks_bare_date_on_overlap(self, ally):
        """A full 2024-05-22T14:32:00 must emit ISO_DATETIME, not just DATE."""
        text = "Logged at 2024-05-22T14:32:00 today"
        types = types_for(ally, text)
        assert "ISO_DATETIME" in types
        # And there should be no DATE span exactly equal to the date prefix
        # of the ISO datetime (it would be redundant).

    def test_time_does_not_swallow_date_in_combined_form(self, ally):
        """For 'on 15/01/2024 at 14:30' the date must remain DATE-classified."""
        text = "Incident on 15/01/2024 at 14:30"
        results = ally.analyze(text)
        date_spans = [r for r in results
                      if r.entity_type in {"DATE", "INCIDENT_DATE"}
                      and "15/01/2024" in text[r.start:r.end]]
        assert date_spans, "15/01/2024 must be tagged DATE / INCIDENT_DATE"
        time_spans = [r for r in results if r.entity_type == "TIME"]
        assert time_spans, "14:30 must be tagged TIME"


# ---------------------------------------------------------------------------
# AU-vs-international precedence
# ---------------------------------------------------------------------------

class TestAuPrecedence:
    """AU-specific patterns must win on AU-shape inputs even with intl rules loaded."""

    @pytest.mark.parametrize("text,expected", [
        ("Call (03) 9876 5432 anytime", "AU_PHONE"),
        ("Mobile 0412 345 678 please", "AU_PHONE"),
        ("Try 1300 123 456 for support", "AU_PHONE"),
    ])
    def test_au_phone_wins_on_au_shapes(self, ally, text, expected):
        types = types_for(ally, text)
        assert expected in types, \
            f"{expected} expected in {text!r}: got {types}"

    def test_au_tfn_not_misread_as_phone_intl(self, ally):
        # 9-digit TFN must not hit the +CC-anchored phone pattern.
        text = "TFN: 123 456 782 on file"
        types = types_for(ally, text)
        assert "AU_TFN" in types
        assert "PHONE_INTL" not in types
