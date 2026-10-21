"""Immutable result records for the v4 engine.

Offsets are Python string indices (Unicode code points) into the original
text, with an exclusive end. Records never carry the matched source text: a
caller who needs it slices the original string they already hold.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Entity:
    """One detected entity in source coordinates.

    Attributes:
        entity_type: Entity type name, such as ``"AU_TFN"``.
        start: Start offset in the original text.
        end: Exclusive end offset in the original text.
        score: Detector score after context adjustment. Heuristic, not a
            calibrated probability.
        detector: Name of the detector that produced it, such as
            ``"rules"`` or ``"spacy:en_core_web_sm"``.
        labelled: True when an explicit label ("TFN:", "Medicare no.")
            directly precedes the value.
    """

    entity_type: str
    start: int
    end: int
    score: float
    detector: str
    labelled: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.start < self.end:
            raise ValueError(f"Invalid span [{self.start}, {self.end})")


@dataclass(frozen=True, slots=True)
class Replacement:
    """One region of the original text replaced in the output.

    Attributes:
        entity_type: Entity type the region was replaced as.
        start: Start offset in the original text.
        end: Exclusive end offset in the original text.
        output_start: Start offset of the replacement in the output text.
        output_end: Exclusive end offset of the replacement in the output.
        operator: Operator applied: ``replace``, ``mask``, ``redact`` or ``hash``.
    """

    entity_type: str
    start: int
    end: int
    output_start: int
    output_end: int
    operator: str


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Entities detected in one text, independent of any policy.

    Overlapping entities of different types may both appear; how overlaps are
    masked is decided by :meth:`Engine.transform`.
    """

    entities: tuple[Entity, ...]
    text_length: int
    bundle: str


@dataclass(frozen=True, slots=True)
class TransformResult:
    """Output of transforming one text under a policy.

    Attributes:
        text: The transformed text.
        replacements: Replaced regions in source order; they never overlap.
        entities: The policy-filtered entities the replacements came from.
        bundle: Detector bundle name and version.
        policy: Digest identifying the policy settings (never key material).
    """

    text: str
    replacements: tuple[Replacement, ...]
    entities: tuple[Entity, ...]
    bundle: str
    policy: str
