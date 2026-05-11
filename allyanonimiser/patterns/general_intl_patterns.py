"""
General-purpose international PII patterns.

These patterns supplement the AU-focused defaults and are designed to catch
PII shapes that show up in real AU-insurance data when the customer or
counterparty is overseas (expats, business travel, dual coverage), or when
system audit logs leak ISO timestamps into claim notes.

Each pattern is anchored on a structural feature that does NOT collide with
any existing AU identifier (e.g. ``+`` country-code prefix for ``PHONE_INTL``,
``T`` separator for ``ISO_DATETIME``, the ``\\d{3}-\\d{2}-\\d{4}`` segment
shape for ``US_SSN``). Credit-card matches are validated by a Luhn checksum
in :mod:`allyanonimiser.core.validators` so random 16-digit blocks (policy
numbers, claim references) do not slip through.
"""


def get_general_intl_pattern_definitions():
    """Return non-AU patterns for international/system-generated PII shapes."""
    return [
        {
            "entity_type": "TIME",
            "patterns": [
                # 24h: 00:00, 23:59, 23:59:59
                # 12h: 1:30 PM, 12:00 am, 6:52 p.m.
                # Lookbehind blocks DD/MM/YYYY-style dates whose colons could
                # otherwise read as time fragments.
                r"(?<![/\d])\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?:\s*[AaPp]\.?[Mm]\.?)?\b",
            ],
            "context": ["time", "at", "scheduled", "appointment", "by"],
            "name": "Time of Day",
        },
        {
            "entity_type": "ISO_DATETIME",
            "patterns": [
                # 2024-05-22T14:32:00, 2024-05-22T14:32:00Z, 2024-05-22T14:32:00+10:00
                r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b",
            ],
            "context": ["timestamp", "logged", "occurred", "audit", "event"],
            "name": "ISO 8601 Datetime",
        },
        {
            "entity_type": "PHONE_INTL",
            "patterns": [
                # +CC anchored. Requires leading + so we cannot fire on a bare
                # 9-digit TFN or 10-digit Medicare. Allows space, dot, dash,
                # parentheses as separators between digits.
                r"(?<!\d)\+\d{1,3}[\s.\-()]*\d[\d\s.\-()]{6,18}\d(?!\d)",
                # IDD 00-prefix form (international dialling code without +).
                # Same separator alphabet as the +CC form. Requires a separator
                # between IDD and the body so a stray leading-zero number
                # ("0012345...") doesn't fire spuriously.
                r"(?<!\d)00\d{1,3}[\s.\-()]+\d[\d\s.\-()]{6,16}\d(?!\d)",
                # Parenthesised area code: (NNN) NNN-NNNN (US/Canada),
                # (NNN)-NNNNNNN (some Latin American formats). Require 3-4
                # digits in the area code so AU 2-digit forms ("(03) 9876
                # 5432") stay with AU_PHONE rather than being absorbed by
                # the generic intl pattern. \b doesn't fire between two
                # non-word chars so we use a negative lookbehind for digits.
                r"(?<!\d)\(\d{3,4}\)[\s.\-]?\d{3,4}[\s.\-]?\d{4,7}\b",
            ],
            "context": ["phone", "mobile", "tel", "contact", "international"],
            "name": "International Phone Number",
        },
        {
            "entity_type": "US_SSN",
            "patterns": [
                # NNN-NN-NNNN with the SSA reservation rules: area cannot be
                # 000/666/9xx, group cannot be 00, serial cannot be 0000.
                r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
            ],
            "context": ["ssn", "social", "security", "tax id"],
            "name": "US Social Security Number",
        },
        {
            "entity_type": "CREDIT_CARD",
            "patterns": [
                # 13-19 digits with optional separators between 4-digit groups.
                # Luhn validation happens in
                # :class:`EntityValidator.validate_credit_card`, called from
                # :func:`core.conflict_resolver._is_valid_single`. Random
                # 16-digit blocks (e.g. policy numbers) will not survive Luhn.
                r"\b(?:\d[ -]?){12,18}\d\b",
            ],
            "context": ["card", "credit", "visa", "mastercard", "amex", "payment"],
            "name": "Credit Card Number",
        },
    ]
