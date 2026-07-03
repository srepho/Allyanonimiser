"""Regression tests: per-call analysis options must not leak into later calls.

Historically, ``Allyanonimiser.analyze(active_entity_types=...)`` and
``min_score_threshold=...`` were applied via sticky setters on the shared
``EnhancedAnalyzer``, so a single filtered call silently restricted every
subsequent call. These tests pin the fixed behavior: per-call options are
per-call only, while the explicit ``set_*`` methods remain sticky.
"""

import pytest

from allyanonimiser import create_allyanonimiser

SAMPLE_TEXT = (
    "John Smith emailed jane.doe@example.com about claim CL-12345678. "
    "His TFN is 123 456 789."
)


@pytest.fixture
def ally():
    return create_allyanonimiser()


def _entity_types(results):
    return {r.entity_type for r in results}


class TestAnalyzeStateIsolation:
    def test_active_entity_types_does_not_leak(self, ally):
        baseline = _entity_types(ally.analyze(SAMPLE_TEXT))
        assert "EMAIL_ADDRESS" in baseline
        assert len(baseline) > 1

        filtered = _entity_types(
            ally.analyze(SAMPLE_TEXT, active_entity_types=["EMAIL_ADDRESS"])
        )
        assert filtered == {"EMAIL_ADDRESS"}

        # A later unfiltered call must see everything again.
        after = _entity_types(ally.analyze(SAMPLE_TEXT))
        assert after == baseline

    def test_min_score_threshold_does_not_leak(self, ally):
        baseline = ally.analyze(SAMPLE_TEXT)
        assert baseline

        strict = ally.analyze(SAMPLE_TEXT, min_score_threshold=0.99)
        assert all(r.score >= 0.99 for r in strict)

        after = ally.analyze(SAMPLE_TEXT)
        assert len(after) == len(baseline)
        assert ally.analyzer.min_score_threshold == pytest.approx(0.7)

    def test_invalid_threshold_rejected(self, ally):
        with pytest.raises(ValueError):
            ally.analyze(SAMPLE_TEXT, min_score_threshold=1.5)

    def test_anonymize_active_entity_types_does_not_leak(self, ally):
        filtered = ally.anonymize(
            SAMPLE_TEXT, active_entity_types=["EMAIL_ADDRESS"]
        )
        filtered_types = {i["entity_type"] for i in filtered["items"]}
        assert filtered_types == {"EMAIL_ADDRESS"}

        # Unfiltered anonymize afterwards must again mask other entities.
        after = ally.anonymize(SAMPLE_TEXT)
        after_types = {i["entity_type"] for i in after["items"]}
        assert "EMAIL_ADDRESS" in after_types
        assert len(after_types) > 1

    def test_explicit_setter_is_still_sticky(self, ally):
        """set_active_entity_types is the documented persistent config knob."""
        ally.analyzer.set_active_entity_types(["EMAIL_ADDRESS"])
        assert _entity_types(ally.analyze(SAMPLE_TEXT)) == {"EMAIL_ADDRESS"}

        # Per-call override wins for that call only.
        override = _entity_types(
            ally.analyze(SAMPLE_TEXT, active_entity_types=["PERSON"])
        )
        assert override == {"PERSON"}
        assert _entity_types(ally.analyze(SAMPLE_TEXT)) == {"EMAIL_ADDRESS"}

        # Reset restores full detection.
        ally.analyzer.set_active_entity_types(None)
        assert len(_entity_types(ally.analyze(SAMPLE_TEXT))) > 1


class TestBatchSingleParity:
    """analyze_batch must produce identical results to per-text analyze()."""

    TEXTS = [
        # PERSON false-positive material: status words spaCy can tag as PERSON
        "Awaiting repairs at the workshop. Excess payment pending.",
        # Genuine PII
        "John Smith of 42 Queen St, Sydney NSW 2000 called about his claim.",
        # LOCATION false-positive material
        "Claim CL-98765432 approved. Pickup scheduled from storage.",
        # ORG deny-list material
        "DOB: 04/01/1959, TFN 123 456 789, contact jane.doe@example.com",
        # Duplicate text (exercises the dedup in the batch pre-warm)
        "John Smith of 42 Queen St, Sydney NSW 2000 called about his claim.",
        "",
    ]

    @staticmethod
    def _as_tuples(results):
        return sorted((r.entity_type, r.start, r.end, r.score) for r in results)

    def test_batch_matches_single(self, ally):
        batch = ally.analyzer.analyze_batch(self.TEXTS)

        # Fresh instance so the single path can't just replay the batch cache.
        single_ally = create_allyanonimiser()
        singles = [single_ally.analyzer.analyze(t) for t in self.TEXTS]

        assert len(batch) == len(singles)
        for text, b, s in zip(self.TEXTS, batch, singles):
            assert self._as_tuples(b) == self._as_tuples(s), (
                f"batch/single divergence for text: {text!r}"
            )

    def test_batch_respects_per_call_filters(self, ally):
        batch = ally.analyzer.analyze_batch(
            self.TEXTS, active_entity_types=["EMAIL_ADDRESS"]
        )
        types = {r.entity_type for results in batch for r in results}
        assert types <= {"EMAIL_ADDRESS"}

        # And the filter must not leak into subsequent calls either.
        after = _entity_types(ally.analyze(SAMPLE_TEXT))
        assert len(after) > 1
