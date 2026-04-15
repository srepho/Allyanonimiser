"""Shared result type used by the analyzer, recognizers, and resolvers."""

from dataclasses import dataclass


@dataclass
class RecognizerResult:
    """A class representing the result of a recognized entity."""
    entity_type: str
    start: int
    end: int
    score: float
    text: str = None

    def __post_init__(self):
        """Ensure all fields are properly initialized."""
        # Kept for parity with the original; text may be set externally.
