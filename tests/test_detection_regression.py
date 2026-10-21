"""Corpus-level detection regression gate and evaluator self-tests.

Runs ``bench/eval_ally.py`` pattern-only against the checked-in baseline
receipt, so results are deterministic and independent of the spaCy model
installed. Skipped when the bench directory is absent (e.g. from an sdist).
"""
import importlib.util
import json
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parent.parent / "bench"
EVAL = BENCH / "eval_ally.py"
BASELINE = BENCH / "baselines" / "au_insurance_patterns.json"

pytestmark = pytest.mark.skipif(not EVAL.exists(), reason="bench/ not available")


@pytest.fixture(scope="module")
def ev():
    spec = importlib.util.spec_from_file_location("eval_ally", EVAL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def receipt(ev, tmp_path_factory):
    out = tmp_path_factory.mktemp("eval") / "receipt.json"
    assert ev.main(["--repeats", "1", "--out", str(out)]) == 0
    return json.loads(out.read_text())


def test_no_detection_regression_against_baseline(ev, receipt):
    """Invariant: no gold label loses coverage or correct typing versus the baseline."""
    baseline = json.loads(BASELINE.read_text())
    assert receipt["corpus"]["sha256"] == baseline["corpus"]["sha256"], "corpus changed; refresh baseline"
    regressions, _, _ = ev.compare(receipt, baseline)
    assert not regressions, "Detection regressed:\n" + "\n".join(regressions)


def test_receipt_records_reproducibility_fields(receipt):
    for key in ("sha256", "split", "documents", "families"):
        assert key in receipt["corpus"]
    assert receipt["config"]["spacy_model_loaded"] is None
    assert receipt["environment"]["versions"]["allyanonimiser"]
    assert receipt["metrics"]["entities"]["total"] == sum(
        c["total"] for c in receipt["metrics"]["by_label"].values()
    )


# --- Scoring unit tests -----------------------------------------------------

def test_score_document_outcomes(ev):
    """Invariant: covered + partial + missed equals the number of gold spans."""
    text = "Name Jane Doe, TFN 123 456 782, ref ZZ."
    gold = [
        {"start": 5, "end": 13, "label": "PERSON"},
        {"start": 19, "end": 30, "label": "AU_TFN"},
        {"start": 36, "end": 38, "label": "POLICY_NUMBER"},
    ]
    replaced = [(5, 13, "PERSON"), (19, 25, "AU_CENTRELINK_CRN"), (0, 4, "PERSON")]
    doc = ev.score_document(text, gold, replaced)
    outcomes = [(e["label"], e["outcome"], e["type_correct"]) for e in doc["entities"]]
    assert outcomes == [
        ("PERSON", "covered", True),
        ("AU_TFN", "partial", False),
        ("POLICY_NUMBER", "missed", False),
    ]
    assert doc["spurious"] == ["PERSON"]
    assert doc["overmasked_chars"] == 4


def test_score_document_no_gold_no_replacements(ev):
    doc = ev.score_document("nothing here", [], [])
    assert doc["entities"] == [] and doc["overmasked_chars"] == 0 and doc["spurious"] == []


def test_compare_flags_worse_and_better(ev, receipt):
    worse = json.loads(json.dumps(receipt))
    label = next(iter(worse["metrics"]["by_label"]))
    worse["metrics"]["by_label"][label]["missed"] += 1
    worse["metrics"]["documents"]["with_exposed_pii"] += 1
    regressions, improvements, _ = ev.compare(worse, receipt)
    assert any(label in r and "missed" in r for r in regressions)
    assert any("documents" in r for r in regressions)
    regressions, improvements, _ = ev.compare(receipt, worse)
    assert not regressions and improvements


def test_compare_warns_on_corpus_or_model_mismatch(ev, receipt):
    other = json.loads(json.dumps(receipt))
    other["corpus"]["sha256"] = "different"
    other["config"]["spacy_model_loaded"] = "en_core_web_lg"
    _, _, warnings = ev.compare(other, receipt)
    assert any("sha256" in w for w in warnings)
    assert any("spacy_model_loaded" in w for w in warnings)


def test_splits_are_disjoint_and_cover_corpus(ev):
    """Invariant: dev and test partition the corpus by template family."""
    all_rows, _ = ev.load_corpus(ev.DEFAULT_CORPUS, "all")
    dev, _ = ev.load_corpus(ev.DEFAULT_CORPUS, "dev")
    test, _ = ev.load_corpus(ev.DEFAULT_CORPUS, "test")
    assert {r["row"] for r in dev}.isdisjoint({r["row"] for r in test})
    assert len(dev) + len(test) == len(all_rows)
    assert {r["family"] for r in dev}.isdisjoint({r["family"] for r in test})
    dev_labels = {s["label"] for r in dev for s in r["spans"]}
    assert {s["label"] for r in test for s in r["spans"]} <= dev_labels


def test_load_corpus_rejects_bad_offsets(ev, tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"text": "abc", "spans": [{"start": 0, "end": 2, "label": "X", "value": "zz"}]}))
    with pytest.raises(ValueError, match="offsets"):
        ev.load_corpus(bad)


def test_unknown_split_rejected(ev):
    with pytest.raises(ValueError, match="split"):
        ev.load_corpus(ev.DEFAULT_CORPUS, "train")
