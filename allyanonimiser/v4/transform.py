"""Apply segments to text exactly once, in source coordinates."""
from __future__ import annotations

import hashlib
import hmac
import unicodedata
from collections.abc import Sequence

from .policy import Policy
from .types import Entity, Replacement


def _render(operator: str, entity_type: str, value: str, policy: Policy) -> str:
    if operator == "replace":
        return f"<{entity_type}>"
    if operator == "mask":
        return policy.mask_char * len(value)
    if operator == "redact":
        return ""
    if operator == "hash":
        assert policy.hash_key is not None  # guaranteed by Policy validation
        # Normalise so "123 456 782" and "123-456-782" pseudonymise the same.
        normal = "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())
        digest = hmac.new(policy.hash_key, f"{entity_type}:{normal}".encode(), hashlib.sha256).hexdigest()
        return f"<{entity_type}:{digest[:12]}>"
    raise ValueError(f"Unsupported operator {operator!r}")


def apply_segments(
    text: str, segments: Sequence[tuple[int, int, Entity]], policy: Policy,
) -> tuple[str, tuple[Replacement, ...]]:
    """Build the output text and replacement records.

    Args:
        text: Original text.
        segments: Sorted, non-overlapping ``(start, end, entity)`` triples
            from :func:`~allyanonimiser.v4.resolve.segment`.
        policy: Supplies operators, the mask character and the hash key.

    Returns:
        The output text and one :class:`Replacement` per segment.
    """
    out: list[str] = []
    replacements: list[Replacement] = []
    cursor = 0
    out_len = 0
    for start, end, ent in segments:
        if start < cursor:
            raise ValueError("Segments overlap or are unsorted")
        out.append(text[cursor:start])
        out_len += start - cursor
        operator = policy.operator_for(ent.entity_type)
        rendered = _render(operator, ent.entity_type, text[start:end], policy)
        out.append(rendered)
        replacements.append(Replacement(
            entity_type=ent.entity_type, start=start, end=end,
            output_start=out_len, output_end=out_len + len(rendered), operator=operator,
        ))
        out_len += len(rendered)
        cursor = end
    out.append(text[cursor:])
    return "".join(out), tuple(replacements)
