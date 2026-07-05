"""
Pattern manager for handling custom PII detection patterns.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class CustomPatternDefinition:
    """
    Class for defining custom PII detection patterns.

    Attributes:
        entity_type: The type of entity this pattern detects (e.g., "POLICY_NUMBER")
        patterns: List of regex strings or spaCy pattern dictionaries
        context: Optional list of context keywords that often appear near this entity
        name: Optional friendly name for this pattern
        score: Detection confidence score (0.0-1.0)
        language: Language this pattern applies to
        description: Description of what this pattern detects
    """
    def __init__(self, **kwargs):
        self.entity_type = kwargs.get('entity_type')
        self.patterns = kwargs.get('patterns', [])
        self.context = kwargs.get('context')
        self.name = kwargs.get('name')
        self.score = kwargs.get('score', 0.85)
        self.language = kwargs.get('language', 'en')
        self.description = kwargs.get('description', f"Custom pattern for {self.entity_type}")
        self._compiled: list[re.Pattern] = []
        self._compiled_snapshot: tuple[str, ...] | None = None

    @property
    def compiled_patterns(self) -> list[re.Pattern]:
        """Compiled forms of the string regexes in ``patterns``.

        Compiled once and cached (recompiled only if ``patterns`` is mutated).
        Invalid regexes are logged once at compile time and skipped, instead
        of raising ``re.error`` on every analyze() call. Non-string entries
        (spaCy token patterns) are ignored.
        """
        snapshot = tuple(p for p in self.patterns if isinstance(p, str))
        if snapshot != self._compiled_snapshot:
            compiled = []
            for pat in snapshot:
                try:
                    compiled.append(re.compile(pat))
                except re.error as e:
                    logger.warning(
                        "Skipping invalid regex for %s (%s): %s",
                        self.entity_type, pat[:60], e,
                    )
            self._compiled = compiled
            self._compiled_snapshot = snapshot
        return self._compiled

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the pattern definition to a dictionary.

        Returns:
            Dictionary representation of the pattern definition
        """
        return {
            'entity_type': self.entity_type,
            'patterns': self.patterns,
            'context': self.context,
            'name': self.name,
            'score': self.score,
            'language': self.language,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, pattern_dict: dict[str, Any]) -> 'CustomPatternDefinition':
        """
        Create a CustomPatternDefinition from a dictionary.

        Args:
            pattern_dict: Dictionary with pattern definition fields

        Returns:
            New CustomPatternDefinition instance
        """
        return cls(**pattern_dict)

class PatternManager:
    """
    Manager for handling collections of patterns.

    This class provides methods for managing, applying, and converting between
    different pattern formats.
    """
    def __init__(self):
        self.patterns = []

    def add_pattern(self, pattern: CustomPatternDefinition) -> None:
        """
        Add a pattern to the manager.

        Args:
            pattern: The pattern definition to add
        """
        self.patterns.append(pattern)

    def get_patterns_by_entity_type(self, entity_type: str) -> list[CustomPatternDefinition]:
        """
        Get all patterns for a specific entity type.

        Args:
            entity_type: The entity type to get patterns for

        Returns:
            List of pattern definitions for the entity type
        """
        return [p for p in self.patterns if p.entity_type == entity_type]

    def apply_patterns(self, text: str, entity_types: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Apply patterns to text and return matches.

        Args:
            text: The text to analyze
            entity_types: Optional list of entity types to restrict to

        Returns:
            List of match dictionaries with entity_type, start, end, text, and score
        """
        results = []

        # Filter patterns by entity type if specified
        patterns_to_apply = self.patterns
        if entity_types:
            patterns_to_apply = [p for p in self.patterns if p.entity_type in entity_types]

        # Apply each pattern
        for pattern_def in patterns_to_apply:
            entity_type = pattern_def.entity_type
            score = pattern_def.score

            # compiled_patterns covers the string regexes only; spaCy token
            # patterns need a spaCy model and are skipped here.
            for compiled in pattern_def.compiled_patterns:
                for match in compiled.finditer(text):
                    # Check if the pattern has capturing groups
                    if match.lastindex and match.lastindex > 0:
                        # Use the first capturing group
                        start = match.start(1)
                        end = match.end(1)
                        matched_text = match.group(1)
                    else:
                        # Use the entire match
                        start = match.start()
                        end = match.end()
                        matched_text = match.group()

                    results.append({
                        'entity_type': entity_type,
                        'start': start,
                        'end': end,
                        'text': matched_text,
                        'score': score
                    })

        return results

    def to_dict_list(self) -> list[dict[str, Any]]:
        """
        Convert all patterns to a list of dictionaries.

        Returns:
            List of dictionaries representing all patterns
        """
        return [pattern.to_dict() for pattern in self.patterns]

    @classmethod
    def from_dict_list(cls, pattern_dicts: list[dict[str, Any]]) -> 'PatternManager':
        """
        Create a PatternManager from a list of pattern dictionaries.

        Args:
            pattern_dicts: List of pattern definition dictionaries

        Returns:
            New PatternManager instance with loaded patterns
        """
        manager = cls()
        for pattern_dict in pattern_dicts:
            manager.add_pattern(CustomPatternDefinition.from_dict(pattern_dict))
        return manager
