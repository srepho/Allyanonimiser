"""The v4 engine: one immutable detector bundle behind every interface."""
from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from itertools import islice

from .. import __version__
from .detectors import Detector, RulesDetector, SpacyDetector, default_patterns
from .policy import DEFAULT_POLICY, Policy
from .resolve import resolve, segment
from .transform import apply_segments
from .types import DetectionResult, TransformResult

# Bundle name -> spaCy model (None for rules only). Bundles never download
# assets or fall back to another model: a missing model is an error.
BUNDLES: dict[str, str | None] = {
    "au-rules-v1": None,
    "au-spacy-sm-v1": "en_core_web_sm",
    "au-spacy-lg-v1": "en_core_web_lg",
}


class Engine:
    """Detects and transforms PII with a fixed detector bundle.

    An engine holds no per-call state and no caches: the same text, bundle
    and policy always give the same result, whatever was processed before
    and however inputs are batched. Construct with :meth:`from_bundle`.
    """

    def __init__(self, detectors: Sequence[Detector], bundle: str, patterns: Sequence = ()):
        if not detectors:
            raise ValueError("An engine needs at least one detector")
        self._detectors = tuple(detectors)
        self._patterns = tuple(patterns)
        self.bundle = bundle

    @classmethod
    def from_bundle(cls, name: str = "au-rules-v1", *, patterns: Sequence | None = None) -> Engine:
        """Build an engine from a named bundle.

        Args:
            name: One of :data:`BUNDLES`.
            patterns: Pattern definitions to use instead of the built-in set
                (for example the built-ins plus custom patterns).

        Raises:
            ValueError: Unknown bundle name.
            RuntimeError: The bundle's spaCy model is not installed.
        """
        if name not in BUNDLES:
            raise ValueError(f"Unknown bundle {name!r}; available: {sorted(BUNDLES)}")
        model = BUNDLES[name]
        pats = tuple(patterns) if patterns is not None else default_patterns()
        detectors: list[Detector] = [RulesDetector(pats, broad_names=model is None)]
        version = f"{name}@{__version__}"
        if model is not None:
            nlp = SpacyDetector(model)
            detectors.append(nlp)
            version += f"+{model}-{nlp.version}"
        return cls(detectors, version, pats)

    # -- detection ---------------------------------------------------------------
    def _detect_batch(self, texts: Sequence[str], entity_types: frozenset[str] | None) -> list[DetectionResult]:
        for t in texts:
            if not isinstance(t, str):
                raise TypeError(f"Expected str, got {type(t).__name__}")
        per_detector = [d.detect_many(texts) for d in self._detectors]
        results = []
        for i, text in enumerate(texts):
            candidates = [(d.name, c) for d, found in zip(self._detectors, per_detector) for c in found[i]]
            entities = resolve(text, candidates, self._patterns, entity_types)
            results.append(DetectionResult(entities=entities, text_length=len(text), bundle=self.bundle))
        return results

    def detect(self, text: str) -> DetectionResult:
        """Detect entities of every type in *text*."""
        return self._detect_batch([text], None)[0]

    # -- transformation ------------------------------------------------------------
    def _transform_one(self, text: str, detection: DetectionResult, policy: Policy) -> TransformResult:
        entities = tuple(e for e in detection.entities if policy.applies_to(e.entity_type, e.score))
        new_text, replacements = apply_segments(text, segment(text, entities, policy), policy)
        return TransformResult(text=new_text, replacements=replacements, entities=entities,
                               bundle=self.bundle, policy=policy.digest())

    def _types_for(self, policy: Policy) -> frozenset[str] | None:
        if policy.entity_types is None:
            return None
        return policy.entity_types | policy.retain

    def transform(self, text: str, policy: Policy = DEFAULT_POLICY,
                  detection: DetectionResult | None = None) -> TransformResult:
        """Transform *text* under *policy*.

        Args:
            text: Original text.
            policy: What to change and how.
            detection: Reuse an earlier :meth:`detect` result for this exact
                text and engine. Without it, detection runs restricted to the
                policy's types.

        Raises:
            ValueError: *detection* came from another bundle or text.
        """
        if detection is None:
            detection = self._detect_batch([text], self._types_for(policy))[0]
        elif detection.bundle != self.bundle or detection.text_length != len(text):
            raise ValueError("detection does not belong to this engine and text")
        return self._transform_one(text, detection, policy)

    def transform_many(self, texts: Iterable[str], policy: Policy = DEFAULT_POLICY,
                       batch_size: int = 64) -> Iterator[TransformResult]:
        """Transform texts lazily, in order, in bounded batches.

        Results are identical to calling :meth:`transform` on each text.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        types = self._types_for(policy)
        iterator = iter(texts)
        while batch := list(islice(iterator, batch_size)):
            for text, detection in zip(batch, self._detect_batch(batch, types)):
                yield self._transform_one(text, detection, policy)
