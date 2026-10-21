"""Policy validation, immutability and key handling."""
import dataclasses

import pytest

from allyanonimiser.v4 import Policy


def test_policy_is_immutable():
    policy = Policy()
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.min_score = 0.1
    with pytest.raises(TypeError):
        policy.operators["PERSON"] = "mask"


@pytest.mark.parametrize("kwargs,match", [
    ({"default_operator": "shred"}, "Unknown operator"),
    ({"operators": {"PERSON": "shred"}}, "Unknown operator"),
    ({"min_score": 1.5}, "between 0 and 1"),
    ({"min_scores": {"DATE": -0.1}}, "between 0 and 1"),
    ({"mask_char": "**"}, "single character"),
    ({"default_operator": "hash"}, "hash_key"),
    ({"operators": {"AU_TFN": "hash"}}, "hash_key"),
    ({"default_operator": "hash", "hash_key": "not-bytes"}, "bytes"),
])
def test_invalid_policies_rejected(kwargs, match):
    with pytest.raises(ValueError, match=match):
        Policy(**kwargs)


def test_hash_key_never_exposed():
    key = b"super-secret-key-material-123456"
    policy = Policy(default_operator="hash", hash_key=key)
    assert "super-secret" not in repr(policy)
    other = Policy(default_operator="hash", hash_key=b"another-key-entirely-0000000000")
    assert policy.digest() == other.digest()          # digest excludes key material
    assert policy.digest() != Policy().digest()


def test_digest_is_stable_and_order_independent():
    a = Policy(entity_types={"PERSON", "AU_TFN"}, operators={"PERSON": "mask", "AU_TFN": "redact"})
    b = Policy(entity_types={"AU_TFN", "PERSON"}, operators={"AU_TFN": "redact", "PERSON": "mask"})
    assert a.digest() == b.digest()


def test_applies_to_and_retain():
    policy = Policy(entity_types={"PERSON"}, min_scores={"PERSON": 0.9}, retain={"AU_POSTCODE"})
    assert policy.applies_to("PERSON", 0.95)
    assert not policy.applies_to("PERSON", 0.85)
    assert not policy.applies_to("EMAIL_ADDRESS", 1.0)
    assert policy.applies_to("AU_POSTCODE", 0.1)       # retained types always claim their characters
    assert policy.operator_for("AU_POSTCODE") == "keep"


def test_constructors():
    assert Policy.redact({"PERSON"}).entity_types == frozenset({"PERSON"})
    assert Policy.mask(mask_char="#").default_operator == "mask"


def test_policies_are_hashable_and_hash_matches_equality():
    a = Policy(operators={"PERSON": "mask"})
    b = Policy(operators={"PERSON": "mask"})
    assert a == b and hash(a) == hash(b)
    assert len({a, b, Policy()}) == 2
    k1 = Policy(default_operator="hash", hash_key=b"1" * 32)
    k2 = Policy(default_operator="hash", hash_key=b"2" * 32)
    assert k1 != k2
