"""Tests for label-context disambiguation and span-containment absorption.

Covers two conflict-resolver behaviors added after v3.5.0:

1. An explicit label immediately before a span ("TFN is ...") beats
   bare-shape competitors (the 9-digit CRN pattern) and per-type checksum
   validation — a labelled-but-mistyped TFN is still a TFN.
2. A winner fully contained in a wider winner's span is absorbed unless it
   outranks the container or is on the never-absorb list (AU_POSTCODE, which
   the anonymizer's keep_postcode feature depends on).
"""

import pytest

from allyanonimiser import create_allyanonimiser
from allyanonimiser.core.conflict_resolver import _absorb_contained
from allyanonimiser.core.recognizer_result import RecognizerResult

# 123 456 782 passes the TFN mod-11 checksum; 123 456 789 fails it.
VALID_TFN = "123 456 782"
INVALID_TFN = "123 456 789"


@pytest.fixture(scope="module")
def ally():
    return create_allyanonimiser()


def _types(results):
    return {r.entity_type for r in results}


class TestLabelDisambiguation:
    def test_labelled_tfn_with_filler_word(self, ally):
        """'TFN is <digits>' must resolve to AU_TFN, not the bare CRN shape."""
        results = ally.analyze(f"His TFN is {VALID_TFN}.")
        assert _types(results) == {"AU_TFN"}

    def test_labelled_tfn_colon_form_still_works(self, ally):
        results = ally.analyze(f"TFN: {VALID_TFN}")
        assert _types(results) == {"AU_TFN"}

    def test_labelled_tfn_overrides_checksum(self, ally):
        """A labelled but checksum-invalid TFN is still masked as a TFN."""
        results = ally.analyze(f"His TFN is {INVALID_TFN}.")
        assert _types(results) == {"AU_TFN"}

    def test_labelled_crn_still_wins(self, ally):
        results = ally.analyze("CRN: 123 456 789A")
        assert _types(results) == {"AU_CENTRELINK_CRN"}

    def test_labelled_crn_with_filler(self, ally):
        results = ally.analyze("Centrelink Reference Number is 123 456 789")
        assert _types(results) == {"AU_CENTRELINK_CRN"}

    def test_unlabelled_nine_digits_stay_crn(self, ally):
        """No label: the bare-shape CRN detection is unchanged."""
        results = ally.analyze("Contact 123 456 789 for details")
        assert _types(results) == {"AU_CENTRELINK_CRN"}

    def test_labelled_abn_with_filler_no_crn_fragment(self, ally):
        """The bare CRN pattern matches the ABN's last 9 digits; the
        contained fragment must be absorbed by the wider ABN span."""
        results = ally.analyze("ABN number is 51 824 753 556")
        assert _types(results) == {"AU_ABN"}

    def test_labelled_medicare_with_filler(self, ally):
        results = ally.analyze("Medicare number is 2123 45678 1")
        assert _types(results) == {"AU_MEDICARE"}

    def test_number_fragment_absorbed_inside_identifier(self, ally):
        """No stray NUMBER sub-span alongside the identifier span."""
        results = ally.analyze(f"His TFN is {INVALID_TFN}.")
        assert "NUMBER" not in _types(results)


def _r(entity_type, start, end):
    return RecognizerResult(
        entity_type=entity_type, start=start, end=end,
        score=0.85, text="x" * (end - start),
    )


class TestAbsorbContained:
    """Direct unit tests for _absorb_contained (model-independent — pins the
    en_core_web_lg fragmentation case without needing the lg model)."""

    def test_date_fragments_absorbed_by_dob(self):
        # lg splits "15/03/1980" inside a DOB span into DATE fragments.
        dob = _r("DATE_OF_BIRTH", 10, 20)
        frag1 = _r("DATE", 10, 15)
        frag2 = _r("DATE", 16, 20)
        assert _absorb_contained([dob, frag1, frag2]) == [dob]

    def test_crn_tail_absorbed_by_abn(self):
        abn = _r("AU_ABN", 0, 14)
        crn_tail = _r("AU_CENTRELINK_CRN", 3, 14)
        assert _absorb_contained([abn, crn_tail]) == [abn]

    def test_postcode_inside_address_survives(self):
        """keep_postcode depends on contained AU_POSTCODE entities."""
        address = _r("AU_ADDRESS", 0, 40)
        postcode = _r("AU_POSTCODE", 36, 40)
        assert _absorb_contained([address, postcode]) == [address, postcode]

    def test_higher_priority_contained_entity_survives(self):
        # PERSON (70) inside an ADDRESS-shaped span (60) must not be absorbed.
        address = _r("AU_ADDRESS", 0, 40)
        person = _r("PERSON", 5, 15)
        assert _absorb_contained([address, person]) == [address, person]

    def test_non_contained_overlap_untouched(self):
        # Partial overlap (not containment) is left for the anonymizer's
        # overlap resolution.
        a = _r("DATE", 0, 10)
        b = _r("DATE_OF_BIRTH", 5, 15)
        assert _absorb_contained([a, b]) == [a, b]

    def test_ner_junk_container_does_not_absorb(self):
        """spaCy junk like ORGANIZATION('DOB 30/06/1944') must not eat the
        real DATE inside it — only pattern-derived types may absorb."""
        junk_org = _r("ORGANIZATION", 0, 14)
        date = _r("DATE", 4, 14)
        assert _absorb_contained([junk_org, date]) == [junk_org, date]

    def test_equal_spans_never_absorb_each_other(self):
        # Dedup guarantees distinct spans, but the rule itself must require
        # a strictly wider container.
        a = _r("DATE", 0, 10)
        b = _r("DATE_OF_BIRTH", 0, 10)
        assert _absorb_contained([a, b]) == [a, b]


class TestAnonymizeLabelledIdentifiers:
    def test_anonymize_masks_labelled_tfn_as_tfn(self, ally):
        result = ally.anonymize(f"His TFN is {INVALID_TFN}.")
        assert "<AU_TFN>" in result["text"]
        assert INVALID_TFN not in result["text"]

    def test_postcode_preserved_in_address_end_to_end(self, ally):
        """Containment absorption must not break keep_postcode."""
        text = "Lives at 42 Queen St, Sydney NSW 2000."
        result = ally.anonymize(text, keep_postcode=True)
        assert "2000" in result["text"]
        assert "Queen St" not in result["text"]
