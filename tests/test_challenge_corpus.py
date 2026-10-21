"""Integrity tests for the AU challenge corpus (bench/make_au_challenge.py).

Skipped when bench/ is absent (e.g. from an sdist).
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parent.parent / "bench"
GEN = BENCH / "make_au_challenge.py"

pytestmark = pytest.mark.skipif(not GEN.exists(), reason="bench/ not available")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load("make_au_challenge", GEN)


@pytest.fixture(scope="module")
def labels():
    return _load("au_labels", BENCH / "au_labels.py")


@pytest.fixture(scope="module")
def manifest():
    return json.loads((BENCH / "data" / "au_challenge_manifest.json").read_text())


@pytest.fixture(scope="module")
def rows():
    out = {}
    for split in ("dev", "test"):
        path = BENCH / "data" / f"au_challenge_{split}.jsonl"
        out[split] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return out


# --- Checksum helpers agree with published examples and the package ----------

@pytest.mark.parametrize("fn,valid,invalid", [
    ("tfn_valid", "123456782", "123456789"),
    ("abn_valid", "51824753556", "51824753557"),
    ("acn_valid", "004085616", "004085617"),
    ("luhn_valid", "4111111111111111", "4111111111111112"),
])
def test_checksum_helpers_on_known_values(gen, fn, valid, invalid):
    assert getattr(gen, fn)(valid)
    assert not getattr(gen, fn)(invalid)


def test_generated_identifiers_pass_package_validators(gen, rows):
    """Invariant: every non-OCR identifier the generator emits is checksum-valid,
    both by the generator's own rules and by the package's validators."""
    from allyanonimiser.core.validators import EntityValidator

    checks = {
        "AU_TFN": (gen.tfn_valid, EntityValidator.validate_tfn),
        "AU_ABN": (gen.abn_valid, EntityValidator.validate_abn),
        "AU_ACN": (gen.acn_valid, None),
        "AU_MEDICARE": (gen.medicare_valid, EntityValidator.validate_medicare_number),
        "CREDIT_CARD_NUMBER": (gen.luhn_valid, EntityValidator.validate_credit_card),
    }
    seen = 0
    for split_rows in rows.values():
        for row in split_rows:
            for span in row["spans"]:
                if span["label"] not in checks or "ocr" in span["variant"]:
                    continue
                digits = re.sub(r"\D", "", span["value"])
                own, package = checks[span["label"]]
                assert own(digits), span
                # Digits only: the package validators strip whitespace but not
                # hyphens, which is a detection gap tracked separately.
                if package is not None:
                    assert package(digits)[0], span
                seen += 1
    assert seen > 300


# --- Corpus structure ----------------------------------------------------------

def test_spans_match_text_and_use_known_labels(rows, labels):
    """Invariant: every span's offsets reproduce its value, and every label is scorable."""
    for split_rows in rows.values():
        for row in split_rows:
            for span in row["spans"]:
                assert row["text"][span["start"]:span["end"]] == span["value"]
                assert span["label"] in labels.GOLD_TO_CAT
                assert span["label"] in labels.GOLD_TO_ALLY_TYPES
                assert span["variant"]


def test_spans_do_not_overlap(rows):
    for split_rows in rows.values():
        for row in split_rows:
            spans = sorted((s["start"], s["end"]) for s in row["spans"])
            assert all(a_end <= b_start for (_, a_end), (b_start, _) in zip(spans, spans[1:])), row["id"]


def test_splits_are_family_disjoint_and_test_labels_seen_in_dev(rows):
    dev_families = {r["family"] for r in rows["dev"]}
    test_families = {r["family"] for r in rows["test"]}
    assert dev_families.isdisjoint(test_families)
    dev_labels = {s["label"] for r in rows["dev"] for s in r["spans"]}
    assert {s["label"] for r in rows["test"] for s in r["spans"]} <= dev_labels


def test_manifest_matches_files(manifest, rows):
    for split, info in manifest["splits"].items():
        data = (BENCH / "data" / info["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == info["sha256"]
        assert info["documents"] == len(rows[split])


def test_regeneration_is_deterministic(gen, manifest, rows):
    """Invariant: the generator reproduces the checked-in corpus exactly.

    Faker's name and city data can change between releases, so this only runs
    with the Faker version recorded in the manifest.
    """
    faker = pytest.importorskip("faker")
    if faker.VERSION != manifest["faker_version"]:
        pytest.skip(f"Faker {faker.VERSION} differs from manifest {manifest['faker_version']}")
    assert gen.generate() == rows
