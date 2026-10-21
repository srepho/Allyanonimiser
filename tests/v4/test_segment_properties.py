"""Property tests for masking segmentation and replacement.

These are the coverage and offset contracts of the v4 design: overlaps may
change an entity's output type, but never shrink what is masked, and output
offsets always point at what was written.
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from allyanonimiser.v4 import Policy
from allyanonimiser.v4.resolve import segment
from allyanonimiser.v4.transform import apply_segments
from allyanonimiser.v4.types import Entity

TYPES = ["PERSON", "AU_ADDRESS", "AU_POSTCODE", "DATE", "ORGANIZATION"]
# Alphabet mixes letters, digits, whitespace, punctuation and non-ASCII so
# trimming and the alnum rule are exercised.
ALPHABET = "ab1 ,.-\né😀"


@st.composite
def text_and_entities(draw):
    text = draw(st.text(alphabet=ALPHABET, min_size=1, max_size=60))
    n = len(text)
    entities = []
    for _ in range(draw(st.integers(0, 6))):
        start = draw(st.integers(0, n - 1))
        end = draw(st.integers(start + 1, n))
        entities.append(Entity(
            entity_type=draw(st.sampled_from(TYPES)), start=start, end=end,
            score=draw(st.floats(0.0, 1.0)), detector=draw(st.sampled_from(["rules", "spacy:x"])),
            labelled=draw(st.booleans()),
        ))
    return text, entities


policies = st.builds(
    lambda retain, threshold, operator: Policy(
        retain=frozenset(retain), min_score=threshold, default_operator=operator, mask_char="#"),
    st.sets(st.sampled_from(TYPES), max_size=2),
    st.floats(0.0, 1.0),
    st.sampled_from(["replace", "mask", "redact"]),
)


@settings(max_examples=400, deadline=None)
@given(text_and_entities(), policies)
def test_segments_are_sorted_disjoint_and_in_bounds(data, policy):
    """Invariant: segments are ordered, non-overlapping and inside the text."""
    text, entities = data
    segs = segment(text, entities, policy)
    for start, end, _ in segs:
        assert 0 <= start < end <= len(text)
    assert all(a_end <= b_start for (_, a_end, _), (b_start, _, _) in zip(segs, segs[1:]))


@settings(max_examples=400, deadline=None)
@given(text_and_entities(), policies)
def test_every_accepted_alphanumeric_character_is_masked(data, policy):
    """Invariant: an alphanumeric character inside an accepted, non-retained
    entity is masked unless an accepted retained entity also covers it."""
    text, entities = data
    accepted = [e for e in entities if policy.applies_to(e.entity_type, e.score)]
    retained = [e for e in accepted if e.entity_type in policy.retain]
    masked = set()
    for start, end, _ in segment(text, entities, policy):
        masked.update(range(start, end))
    for ent in accepted:
        if ent.entity_type in policy.retain:
            continue
        for pos in range(ent.start, ent.end):
            if text[pos].isalnum() and not any(r.start <= pos < r.end for r in retained):
                assert pos in masked, (text, ent, pos)


@settings(max_examples=400, deadline=None)
@given(text_and_entities(), policies)
def test_segments_never_hide_only_punctuation_or_whitespace(data, policy):
    text, entities = data
    for start, end, _ in segment(text, entities, policy):
        assert any(c.isalnum() for c in text[start:end])
        assert not text[start].isspace() and not text[end - 1].isspace()


@settings(max_examples=400, deadline=None)
@given(text_and_entities(), policies)
def test_replacement_offsets_reconstruct_both_texts(data, policy):
    """Invariant: unreplaced text is copied unchanged, and each replacement's
    output offsets slice exactly what was written for it."""
    text, entities = data
    segs = segment(text, entities, policy)
    output, replacements = apply_segments(text, segs, policy)
    assert len(replacements) == len(segs)

    rebuilt, cursor_in, cursor_out = [], 0, 0
    for r in replacements:
        assert text[cursor_in:r.start] == output[cursor_out:r.output_start]
        written = output[r.output_start:r.output_end]
        if r.operator == "replace":
            assert written == f"<{r.entity_type}>"
        elif r.operator == "mask":
            assert written == "#" * (r.end - r.start)
        elif r.operator == "redact":
            assert written == ""
        rebuilt.append(text[cursor_in:r.end])
        cursor_in, cursor_out = r.end, r.output_end
    assert text[cursor_in:] == output[cursor_out:]
