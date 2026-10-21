"""Transformation policy: which entities to change, and how."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

OPERATORS = frozenset({"replace", "mask", "redact", "hash", "keep"})


def _frozen_map(value: Mapping | None) -> Mapping:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True)
class Policy:
    """Immutable transformation policy.

    Attributes:
        entity_types: Types to act on; ``None`` means every detected type.
        default_operator: Operator for types not in ``operators``.
        operators: Per-type operator overrides.
        min_score: Minimum entity score to act on.
        min_scores: Per-type score overrides.
        retain: Types deliberately left visible even inside other entities,
            such as ``{"AU_POSTCODE"}`` to keep postcodes inside addresses.
            Retention is an explicit choice; nothing is retained by default.
        mask_char: Character used by the ``mask`` operator.
        hash_key: Secret key for the ``hash`` operator (HMAC-SHA256). Never
            shown in ``repr`` or included in :meth:`digest`.
    """

    entity_types: frozenset[str] | None = None
    default_operator: str = "replace"
    operators: Mapping[str, str] = field(default_factory=dict)
    min_score: float = 0.7
    min_scores: Mapping[str, float] = field(default_factory=dict)
    retain: frozenset[str] = frozenset()
    mask_char: str = "*"
    hash_key: bytes | None = field(default=None, repr=False)

    def __hash__(self) -> int:
        # Mapping fields are not hashable; the digest covers every setting.
        return hash((self.digest(), self.hash_key))

    def __post_init__(self) -> None:
        object.__setattr__(self, "operators", _frozen_map(self.operators))
        object.__setattr__(self, "min_scores", _frozen_map(self.min_scores))
        object.__setattr__(self, "retain", frozenset(self.retain))
        if self.entity_types is not None:
            object.__setattr__(self, "entity_types", frozenset(self.entity_types))

        for op in (self.default_operator, *self.operators.values()):
            if op not in OPERATORS:
                raise ValueError(f"Unknown operator {op!r}; expected one of {sorted(OPERATORS)}")
        for score in (self.min_score, *self.min_scores.values()):
            if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                raise ValueError(f"Scores must be between 0 and 1, got {score!r}")
        if len(self.mask_char) != 1:
            raise ValueError("mask_char must be a single character")
        uses_hash = self.default_operator == "hash" or "hash" in self.operators.values()
        if uses_hash and not self.hash_key:
            raise ValueError("The hash operator needs hash_key: unkeyed hashes of short identifiers are reversible")
        if self.hash_key is not None and not isinstance(self.hash_key, bytes):
            raise ValueError("hash_key must be bytes")

    # -- construction helpers ----------------------------------------------
    @classmethod
    def redact(cls, entity_types: Iterable[str] | None = None, **kwargs) -> Policy:
        """Replace entities with ``<TYPE>`` placeholders."""
        return cls(entity_types=None if entity_types is None else frozenset(entity_types),
                   default_operator="replace", **kwargs)

    @classmethod
    def mask(cls, entity_types: Iterable[str] | None = None, mask_char: str = "*", **kwargs) -> Policy:
        """Replace each character of an entity with ``mask_char``."""
        return cls(entity_types=None if entity_types is None else frozenset(entity_types),
                   default_operator="mask", mask_char=mask_char, **kwargs)

    # -- queries --------------------------------------------------------------
    def applies_to(self, entity_type: str, score: float) -> bool:
        """True if an entity of this type and score is acted on (or retained)."""
        if entity_type in self.retain:
            return True
        if self.entity_types is not None and entity_type not in self.entity_types:
            return False
        return score >= self.min_scores.get(entity_type, self.min_score)

    def operator_for(self, entity_type: str) -> str:
        if entity_type in self.retain:
            return "keep"
        return self.operators.get(entity_type, self.default_operator)

    def digest(self) -> str:
        """Stable identifier of the settings. Excludes key material."""
        payload = {
            "entity_types": sorted(self.entity_types) if self.entity_types is not None else None,
            "default_operator": self.default_operator,
            "operators": dict(sorted(self.operators.items())),
            "min_score": self.min_score,
            "min_scores": dict(sorted(self.min_scores.items())),
            "retain": sorted(self.retain),
            "mask_char": self.mask_char,
            "keyed": self.hash_key is not None,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


DEFAULT_POLICY = Policy()
