"""ReportingManager: owns the lifecycle of AnonymizationReport instances."""

import threading
from typing import Any

from .report import AnonymizationReport


class ReportingManager:
    """Manager for creating and handling anonymization reports.

    Thread-safe: all mutations are protected by a lock for free-threaded Python.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.current_report = None
        self.reports: dict[str, AnonymizationReport] = {}

    def start_new_report(self, session_id: str | None = None) -> AnonymizationReport:
        """
        Start a new anonymization report.

        Args:
            session_id: Optional identifier for this reporting session

        Returns:
            The new AnonymizationReport instance
        """
        with self._lock:
            self.current_report = AnonymizationReport(session_id)
            self.reports[self.current_report.session_id] = self.current_report
            return self.current_report

    def get_current_report(self) -> AnonymizationReport | None:
        """
        Get the current report.

        Returns:
            The current AnonymizationReport instance, or None if no report is active
        """
        return self.current_report

    def get_report(self, session_id: str) -> AnonymizationReport | None:
        """
        Get a specific report by session ID.

        Args:
            session_id: The session ID of the report to retrieve

        Returns:
            The requested AnonymizationReport instance, or None if not found
        """
        return self.reports.get(session_id)

    def finalize_current_report(self) -> dict[str, Any]:
        """
        Finalize the current report and return its summary.

        Returns:
            Dictionary containing report summary
        """
        if self.current_report:
            self.current_report.finalize()
            return self.current_report.get_summary()
        return {}

    def generate_report_from_results(self, results: list[dict[str, Any]],
                                   session_id: str | None = None) -> AnonymizationReport:
        """
        Generate a report from a list of anonymization results.

        Args:
            results: List of anonymization result dictionaries
            session_id: Optional identifier for this reporting session

        Returns:
            The generated AnonymizationReport instance
        """
        report = AnonymizationReport(session_id)

        for i, result in enumerate(results):
            document_id = result.get('document_id', f"document_{i}")
            original_text = result.get('original_text', '')
            processing_time = result.get('processing_time', 0.0)

            report.record_anonymization(
                document_id=document_id,
                original_text=original_text,
                anonymization_result=result,
                processing_time=processing_time
            )

        report.finalize()
        self.reports[report.session_id] = report
        return report
