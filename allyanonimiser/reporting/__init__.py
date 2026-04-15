"""
Reporting subpackage for Allyanonimiser.

Public API:
    AnonymizationReport — collects and renders per-run statistics.
    ReportingManager    — manages multiple reports across a session.
    report_manager      — module-level singleton (convenience).
"""

from .manager import ReportingManager
from .report import AnonymizationReport

# Singleton instance used by the rest of the library.
report_manager = ReportingManager()

__all__ = ["AnonymizationReport", "ReportingManager", "report_manager"]
