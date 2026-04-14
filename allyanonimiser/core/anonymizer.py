"""
Enhanced anonymizer for PII data anonymization.
"""

import datetime
import hashlib
import re
from typing import Any, Optional

# Default entity priority for overlap resolution.
# Higher numbers win when two entities overlap the same text span.
# Users can override via EnhancedAnonymizer(entity_priority={...}).
DEFAULT_ENTITY_PRIORITY: dict[str, int] = {
    # Australian government identifiers
    "AU_MEDICARE": 100,
    "AU_TFN": 100,
    "AU_ABN": 100,
    "AU_ACN": 100,
    # Insurance identifiers
    "INSURANCE_POLICY_NUMBER": 95,
    "INSURANCE_CLAIM_NUMBER": 95,
    # Contact info
    "EMAIL_ADDRESS": 90,
    "AU_PHONE": 85,
    "CREDIT_CARD": 85,
    # Identity documents
    "AU_DRIVERS_LICENSE": 80,
    "AU_PASSPORT": 80,
    "AU_CENTRELINK_CRN": 80,
    # Named entities
    "PERSON": 70,
    "AU_ADDRESS": 60,
    "ADDRESS": 60,
    "LOCATION": 50,
    "DATE": 40,
    "AU_POSTCODE": 30,
    "NUMBER": 20,
    # Low-priority / generic
    "VEHICLE_REGISTRATION": 15,
    "FACILITY": 10,
    "PRODUCT": 10,
    "INCIDENT_DATE": 10,
}


class EnhancedAnonymizer:
    """PII anonymizer with configurable overlap resolution.

    Args:
        analyzer: The ``EnhancedAnalyzer`` that supplies entity detections.
        entity_priority: Optional dict mapping entity types to integer
            priorities.  Merged on top of ``DEFAULT_ENTITY_PRIORITY``.
    """

    def __init__(self, analyzer=None, entity_priority: Optional[dict[str, int]] = None):
        self.analyzer = analyzer
        self.entity_priority = {**DEFAULT_ENTITY_PRIORITY}
        if entity_priority:
            self.entity_priority.update(entity_priority)

    def anonymize(
        self,
        text: str,
        operators: Optional[dict[str, str]] = None,
        language: str = "en",
        age_bracket_size: int = 5,
        keep_postcode: bool = True,
    ) -> dict[str, Any]:
        """Anonymize PII entities in *text*.

        Returns a dict with ``text`` (anonymized) and ``items`` (replacements).
        """
        if text is None:
            return {"text": "", "items": []}
        if not isinstance(text, str):
            text = str(text)
        if not isinstance(age_bracket_size, int) or age_bracket_size <= 0:
            age_bracket_size = 5
        keep_postcode = bool(keep_postcode)

        if not self.analyzer:
            return {"text": text, "items": []}

        results = self.analyzer.analyze(text, language)
        operators = operators or {}

        # Collect postcode / address info for postcode preservation
        postcode_entities: list[tuple] = []
        address_entities: list[tuple] = []
        if keep_postcode:
            for r in results:
                if r.entity_type == "AU_POSTCODE":
                    postcode_entities.append((r.start, r.end, text[r.start : r.end]))
                elif r.entity_type == "AU_ADDRESS":
                    address_entities.append((r.start, r.end))

        # Build replacement entities
        anonymization_entities: list[dict[str, Any]] = []
        for r in results:
            entity_type = r.entity_type
            start, end = r.start, r.end
            original = text[start:end]

            # Skip postcodes inside addresses when preserving
            if keep_postcode and entity_type == "AU_POSTCODE":
                if any(a_s <= start and end <= a_e for a_s, a_e in address_entities):
                    continue

            replacement = self._apply_operator(
                entity_type, original, operators, age_bracket_size
            )

            # Preserve postcode within address replacement
            if keep_postcode and entity_type == "AU_ADDRESS":
                replacement = self._preserve_postcode_in_address(
                    replacement, start, postcode_entities
                )

            anonymization_entities.append({
                "entity_type": entity_type,
                "start": start,
                "end": end,
                "original": original,
                "replacement": replacement,
            })

        # Resolve overlaps then apply replacements end→start
        anonymization_entities = self._remove_overlapping_entities(anonymization_entities)
        anonymization_entities.sort(key=lambda e: e["start"], reverse=True)

        anonymized_text = text
        replacements: list[dict[str, Any]] = []
        for entity in anonymization_entities:
            anonymized_text = (
                anonymized_text[: entity["start"]]
                + entity["replacement"]
                + anonymized_text[entity["end"] :]
            )
            replacements.append(entity)

        return {"text": anonymized_text, "items": replacements}

    # ------------------------------------------------------------------
    # Operator dispatch
    # ------------------------------------------------------------------

    def _apply_operator(
        self,
        entity_type: str,
        original: str,
        operators: dict[str, str],
        age_bracket_size: int,
    ) -> str:
        match operators.get(entity_type, "replace"):
            case "replace":
                return f"<{entity_type}>"
            case "mask":
                return "*" * len(original)
            case "redact":
                return "[REDACTED]"
            case "hash":
                digest = hashlib.sha256(original.encode()).hexdigest()[:10]
                return f"HASH-{digest}"
            case "age_bracket" if entity_type == "DATE_OF_BIRTH":
                age = self._extract_age_from_date(original)
                if age is not None:
                    lo = (age // age_bracket_size) * age_bracket_size
                    return f"{lo}-{lo + age_bracket_size - 1}"
                return f"<{entity_type}>"
            case _:
                return f"<{entity_type}>"

    # ------------------------------------------------------------------
    # Postcode preservation
    # ------------------------------------------------------------------

    @staticmethod
    def _preserve_postcode_in_address(
        replacement: str, addr_start: int, postcode_entities: list[tuple]
    ) -> str:
        postcodes = [
            (s, e, t) for s, e, t in postcode_entities if s >= addr_start
        ]
        if not postcodes:
            return replacement
        postcodes.sort(key=lambda x: x[0], reverse=True)
        for pc_start, pc_end, pc_text in postcodes:
            rel_start = pc_start - addr_start
            rel_end = pc_end - addr_start
            replacement = (
                replacement[:rel_start] + f" {pc_text} " + replacement[rel_end:]
            )
        return replacement

    # ------------------------------------------------------------------
    # Overlap resolution
    # ------------------------------------------------------------------

    def _remove_overlapping_entities(
        self, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Keep the highest-priority entity when spans overlap."""
        if not entities:
            return entities

        sorted_entities = sorted(
            entities, key=lambda e: (e["start"], -(e["end"] - e["start"]))
        )

        result: list[dict[str, Any]] = []
        for entity in sorted_entities:
            overlaps = False
            for selected in result:
                if entity["start"] < selected["end"] and entity["end"] > selected["start"]:
                    ep = self.entity_priority.get(entity["entity_type"], 0)
                    sp = self.entity_priority.get(selected["entity_type"], 0)

                    should_replace = False
                    if ep > sp and not (
                        entity["start"] >= selected["start"]
                        and entity["end"] <= selected["end"]
                    ):
                        should_replace = True
                    elif ep == sp and (entity["end"] - entity["start"]) > (
                        selected["end"] - selected["start"]
                    ):
                        should_replace = True

                    if should_replace:
                        result.remove(selected)
                        result.append(entity)

                    overlaps = True
                    break

            if not overlaps:
                result.append(entity)

        return result

    # ------------------------------------------------------------------
    # Date → age extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_age_from_date(date_string: str) -> Optional[int]:
        """Parse a date string and return age in years, or None."""
        patterns = [
            (r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", "dmy"),
            (r"(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})", "ymd"),
            (r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2})", "dmy_short"),
        ]

        for pattern, fmt in patterns:
            match = re.search(pattern, date_string)
            if not match:
                continue
            try:
                g1, g2, g3 = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if fmt == "ymd":
                    year, month, day = g1, g2, g3
                else:
                    day, month, year = g1, g2, g3
                if year < 100:
                    year = 2000 + year if year < 30 else 1900 + year

                birth = datetime.date(year, month, day)
                today = datetime.date.today()
                return today.year - birth.year - (
                    (today.month, today.day) < (birth.month, birth.day)
                )
            except (ValueError, IndexError):
                continue

        # Direct "Age: NN" pattern
        age_match = re.search(r"Age:\s*(\d+)", date_string)
        if age_match:
            try:
                return int(age_match.group(1))
            except (ValueError, IndexError):
                pass

        return None
