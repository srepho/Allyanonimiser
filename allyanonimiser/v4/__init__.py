"""Allyanonimiser v4 engine (in development on the ``v4`` branch).

A smaller, explicit API built around immutable results and policies::

    from allyanonimiser.v4 import Engine, Policy

    engine = Engine.from_bundle("au-rules-v1")
    result = engine.transform("TFN: 123 456 782", Policy.redact())
    result.text  # 'TFN: <AU_TFN>'

See ``docs/dev/v4-design.md`` for the contracts this package keeps.
"""
from .engine import BUNDLES, Engine
from .policy import DEFAULT_POLICY, Policy
from .types import DetectionResult, Entity, Replacement, TransformResult

__all__ = [
    "BUNDLES", "DEFAULT_POLICY", "DetectionResult", "Engine", "Entity", "Policy",
    "Replacement", "TransformResult",
]
