"""Detectors produce candidate entities; they hold no per-call state.

A detector is anything with a ``name`` and ``detect_many(texts)`` returning
one candidate list per text. Candidates use the shared
:class:`~allyanonimiser.core.recognizer_result.RecognizerResult` so the
validation and conflict rules already tested in v3 apply unchanged.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from ..core.common_formats import analyze_common_formats
from ..core.detection import match_patterns, spacy_doc_to_results
from ..core.pattern_manager import CustomPatternDefinition
from ..core.recognizer_result import RecognizerResult
from ..patterns import (
    get_au_pattern_definitions,
    get_general_intl_pattern_definitions,
    get_general_pattern_definitions,
    get_insurance_pattern_definitions,
)


class Detector(Protocol):
    """Interface every detector implements."""

    name: str

    def detect_many(self, texts: Sequence[str]) -> list[list[RecognizerResult]]:
        """Return candidates for each text, in order."""
        ...


def default_patterns() -> tuple[CustomPatternDefinition, ...]:
    """The built-in AU, insurance and general pattern definitions."""
    definitions = [
        *get_au_pattern_definitions(),
        *get_insurance_pattern_definitions(),
        *get_general_pattern_definitions(),
        *get_general_intl_pattern_definitions(),
    ]
    return tuple(CustomPatternDefinition(**d) for d in definitions)


class RulesDetector:
    """Regex patterns, labelled-identifier formats and their validators.

    Args:
        patterns: Pattern definitions; defaults to the built-in set.
        broad_names: Run the broad two-capitalised-words PERSON pattern. Turn
            off when a NER detector supplies names, as it over-matches.
    """

    def __init__(self, patterns: Sequence[CustomPatternDefinition] | None = None, *, broad_names: bool = True):
        self.patterns: tuple[CustomPatternDefinition, ...] = tuple(patterns) if patterns is not None else default_patterns()
        self.broad_names = broad_names
        self.name = "rules"

    def detect_many(self, texts: Sequence[str]) -> list[list[RecognizerResult]]:
        return [
            match_patterns(self.patterns, t, skip_broad_person=not self.broad_names) + analyze_common_formats(t)
            for t in texts
        ]


class SpacyDetector:
    """spaCy NER for names, places and organisations.

    The requested model must load with an NER component: there is no silent
    fallback to another model or to rules only.

    Raises:
        RuntimeError: If the model is not installed or has no NER pipe.
    """

    def __init__(self, model: str, *, batch_size: int = 64):
        import spacy

        try:
            self.nlp: Any = spacy.load(model)
        except OSError as e:
            raise RuntimeError(
                f"spaCy model {model!r} is not installed. Install it with: python -m spacy download {model}"
            ) from e
        if "ner" not in self.nlp.pipe_names:
            raise RuntimeError(f"spaCy model {model!r} has no NER component")
        self.model = model
        self.version = self.nlp.meta.get("version", "unknown")
        self.batch_size = batch_size
        self.name = f"spacy:{model}"

    def detect_many(self, texts: Sequence[str]) -> list[list[RecognizerResult]]:
        return [spacy_doc_to_results(doc) for doc in self.nlp.pipe(texts, batch_size=self.batch_size)]
