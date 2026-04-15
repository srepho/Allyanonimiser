"""Direct unit tests for ``allyanonimiser.core.conflict_resolver``.

The conflict resolver was previously only exercised indirectly through
``Allyanonimiser.analyze()``. These tests cover the module-level functions
in isolation so regressions in priority logic, validation, or false-positive
suppression are caught at the unit level.
"""

from allyanonimiser.core.conflict_resolver import (
    deduplicate_and_resolve_conflicts,
    resolve_entity_conflicts,
)
from allyanonimiser.core.recognizer_result import RecognizerResult


def _r(entity_type: str, text: str, score: float = 0.9, start: int = 0) -> RecognizerResult:
    """Build a RecognizerResult for the given text. End is computed."""
    return RecognizerResult(
        entity_type=entity_type, start=start, end=start + len(text),
        score=score, text=text,
    )


# ---------------------------------------------------------------------------
# Single-result path: validators must filter invalid IDs.
# ---------------------------------------------------------------------------

class TestSingleResultValidation:
    def test_valid_tfn_kept(self):
        # 123456782 satisfies the modulus-11 weighted checksum.
        out = deduplicate_and_resolve_conflicts([_r("AU_TFN", "123456782")], patterns=[])
        assert len(out) == 1
        assert out[0].entity_type == "AU_TFN"

    def test_invalid_tfn_dropped(self):
        # 123456789 fails the checksum.
        out = deduplicate_and_resolve_conflicts([_r("AU_TFN", "123456789")], patterns=[])
        assert out == []

    def test_tfn_with_spaces_validates_normalised(self):
        out = deduplicate_and_resolve_conflicts([_r("AU_TFN", "123 456 782")], patterns=[])
        assert len(out) == 1

    def test_valid_abn_kept(self):
        # 51824753556 is the ATO published test ABN.
        out = deduplicate_and_resolve_conflicts([_r("AU_ABN", "51824753556")], patterns=[])
        assert len(out) == 1

    def test_invalid_abn_dropped(self):
        out = deduplicate_and_resolve_conflicts([_r("AU_ABN", "51824753557")], patterns=[])
        assert out == []

    def test_unknown_entity_passes_through(self):
        # Entities without a registered validator should be kept as-is.
        out = deduplicate_and_resolve_conflicts(
            [_r("EMAIL_ADDRESS", "foo@bar.com")], patterns=[],
        )
        assert len(out) == 1


# ---------------------------------------------------------------------------
# Multi-result path: winner picked by priority, then validated.
# ---------------------------------------------------------------------------

class TestMultiResultResolution:
    def test_invalid_winner_after_resolution_is_dropped(self):
        """The fix that motivated this test file.

        When the same span is matched by multiple sources (e.g. patterns +
        common_formats), ``resolve_entity_conflicts`` picks a winner by
        priority. Without the post-resolution validation step, an invalid
        TFN would survive whenever it had competition (which it usually
        does, because TFN and CENTRELINK_CRN share a 9-digit shape).
        """
        results = [
            _r("AU_TFN", "123456789", score=0.9),
            _r("AU_TFN", "123456789", score=1.0),  # Same span, second source.
            _r("AU_CENTRELINK_CRN", "123456789", score=0.85),
        ]
        out = deduplicate_and_resolve_conflicts(results, patterns=[])
        # AU_TFN wins on priority but fails checksum; CENTRELINK_CRN has
        # no validator and so it's never picked over the higher-priority TFN.
        # Net result: span is dropped entirely.
        assert all(r.entity_type != "AU_TFN" for r in out)

    def test_valid_winner_is_kept(self):
        results = [
            _r("AU_TFN", "123456782", score=0.9),
            _r("AU_TFN", "123456782", score=1.0),
        ]
        out = deduplicate_and_resolve_conflicts(results, patterns=[])
        assert len(out) == 1
        assert out[0].entity_type == "AU_TFN"


# ---------------------------------------------------------------------------
# Direct resolve_entity_conflicts tests.
# ---------------------------------------------------------------------------

class TestResolveEntityConflicts:
    def test_label_suffix_drops_span(self):
        # "policy number" is a label, not PII.
        winner = resolve_entity_conflicts(
            [_r("PERSON", "policy number")],
            text="policy number",
            patterns=[],
        )
        assert winner is None

    def test_person_false_positive_filtered(self):
        # spaCy sometimes mis-tags street addresses as PERSON.
        winner = resolve_entity_conflicts(
            [
                _r("PERSON", "Queen St"),
                _r("LOCATION", "Queen St"),
            ],
            text="Queen St",
            patterns=[],
        )
        assert winner is not None
        assert winner.entity_type == "LOCATION"

    def test_person_false_positive_no_replacement_returns_none(self):
        # If the only candidate is the PERSON false-positive, drop the span.
        winner = resolve_entity_conflicts(
            [_r("PERSON", "Queen St")],
            text="Queen St",
            patterns=[],
        )
        assert winner is None

    def test_higher_priority_wins(self):
        # AU_MEDICARE has a higher base priority than DATE.
        winner = resolve_entity_conflicts(
            [
                _r("DATE", "2123 45678 1", score=0.7),
                _r("AU_MEDICARE", "2123 45678 1", score=0.7),
            ],
            text="2123 45678 1",
            patterns=[],
        )
        assert winner is not None
        assert winner.entity_type == "AU_MEDICARE"

    def test_score_breaks_priority_ties(self):
        # Two same-priority entities resolve to the higher-scoring one.
        winner = resolve_entity_conflicts(
            [
                _r("EMAIL_ADDRESS", "foo@bar.com", score=0.7),
                _r("EMAIL_ADDRESS", "foo@bar.com", score=0.95),
            ],
            text="foo@bar.com",
            patterns=[],
        )
        assert winner is not None
        assert winner.score == 0.95
