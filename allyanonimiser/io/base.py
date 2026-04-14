"""
Base class for IO processors.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..allyanonimiser import Allyanonimiser


class BaseProcessor:
    """Common base for CSV, DataFrame, and Stream processors.

    Provides a shared constructor that accepts an optional
    ``Allyanonimiser`` instance (creating one if not supplied).
    Subclasses access the instance via ``self.ally``.
    """

    def __init__(self, allyanonimiser: "Allyanonimiser | None" = None):
        if allyanonimiser is None:
            from ..allyanonimiser import create_allyanonimiser
            allyanonimiser = create_allyanonimiser()
        self.ally = allyanonimiser
