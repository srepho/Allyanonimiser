"""Offline Allyanonimiser evaluation and detection-regression gate.

Runs Allyanonimiser alone on a labelled JSONL corpus. It needs no competitor
weights, network access or dataset downloads, so it can run in CI.

What is measured, on the text actually replaced by ``anonymize()``:

* Entity outcomes per gold span: fully covered, partially exposed, or entirely
  missed (by any replacement), plus whether the covering type is correct.
* Documents with any gold character left exposed.
* Over-masking: characters replaced outside every gold span, and replacements
  that touch no gold span at all.
* Character-level precision/recall/F1 per coarse category (supporting only).
* Cold start and warm throughput (recorded, never gated).

Every run writes a receipt with corpus hash, split, source revision,
configuration, model and runtime versions, and CPU details. ``--baseline``
compares against an earlier receipt and exits 1 on a quality regression.

Usage::

    python bench/eval_ally.py                                   # pattern-only, all docs
    python bench/eval_ally.py --spacy-model en_core_web_lg --split test
    python bench/eval_ally.py --baseline bench/baselines/au_insurance_patterns.json
    python bench/eval_ally.py --out bench/baselines/au_insurance_patterns.json  # refresh

The checked-in corpus is synthetic and templated. It is a regression check,
not evidence of accuracy on real claim notes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from au_labels import (  # noqa: E402
    ALLY_TO_CAT,
    CATEGORIES,
    FAMILIES,
    GOLD_TO_ALLY_TYPES,
    GOLD_TO_CAT,
    TEST_FAMILIES,
)

RECEIPT_SCHEMA = 1
DEFAULT_CORPUS = Path(__file__).resolve().parent / "data" / "au_insurance.jsonl"
REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------

def load_corpus(path: Path, split: str = "all") -> tuple[list[dict[str, Any]], str]:
    """Load rows for *split* and return them with the whole file's SHA-256.

    Args:
        path: JSONL file with ``text``, ``spans`` and optional ``family``.
        split: ``all``, ``dev`` (non-held-out families) or ``test``.

    Returns:
        The selected rows and the corpus hash.
    """
    raw = path.read_bytes()
    rows = []
    for i, line in enumerate(raw.decode("utf-8").splitlines()):
        if not line.strip():
            continue
        row = json.loads(line)
        row.setdefault("family", FAMILIES[i % len(FAMILIES)])
        row["row"] = i
        for span in row["spans"]:
            if row["text"][span["start"]:span["end"]] != span.get("value", row["text"][span["start"]:span["end"]]):
                raise ValueError(f"Row {i}: span offsets do not match recorded value")
        rows.append(row)
    if split == "dev":
        rows = [r for r in rows if r["family"] not in TEST_FAMILIES]
    elif split == "test":
        rows = [r for r in rows if r["family"] in TEST_FAMILIES]
    elif split != "all":
        raise ValueError(f"Unknown split: {split}")
    return rows, hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_document(text: str, gold: list[dict[str, Any]], replaced: list[tuple[int, int, str]]) -> dict[str, Any]:
    """Score one document's replacements against its gold spans.

    Args:
        text: Source text (offsets refer to it).
        gold: Gold spans with ``start``, ``end`` and ``label``.
        replaced: ``(start, end, entity_type)`` regions replaced in the source.

    Returns:
        Per-entity outcomes, character counts and spurious replacements.
    """
    n = len(text)
    masked = [False] * n
    masked_cat: dict[str, list[bool]] = {c: [False] * n for c in CATEGORIES}
    owner: list[set[str]] = [set() for _ in range(n)]
    for start, end, etype in replaced:
        cat = ALLY_TO_CAT.get(etype)
        for i in range(max(0, start), min(n, end)):
            masked[i] = True
            owner[i].add(etype)
            if cat:
                masked_cat[cat][i] = True

    gold_any = [False] * n
    gold_cat: dict[str, list[bool]] = {c: [False] * n for c in CATEGORIES}
    entities = []
    for span in gold:
        s, e, label = span["start"], span["end"], span["label"]
        covered = sum(masked[s:e])
        if covered == e - s:
            outcome = "covered"
        elif covered:
            outcome = "partial"
        else:
            outcome = "missed"
        types_seen = set().union(*owner[s:e]) if e > s else set()
        entities.append({
            "label": label,
            "outcome": outcome,
            "type_correct": bool(types_seen & GOLD_TO_ALLY_TYPES.get(label, set())),
            "exposed_chars": (e - s) - covered,
        })
        for i in range(s, e):
            gold_any[i] = True
            cat = GOLD_TO_CAT.get(label)
            if cat:
                gold_cat[cat][i] = True

    char_counts = {}
    for cat in CATEGORIES:
        tp = sum(g and m for g, m in zip(gold_cat[cat], masked_cat[cat]))
        fp = sum(m and not g for g, m in zip(gold_cat[cat], masked_cat[cat]))
        fn = sum(g and not m for g, m in zip(gold_cat[cat], masked_cat[cat]))
        char_counts[cat] = (tp, fp, fn)

    spurious = [etype for start, end, etype in replaced if not any(gold_any[max(0, start):min(n, end)])]
    return {
        "entities": entities,
        "char_counts": char_counts,
        "overmasked_chars": sum(m and not g for m, g in zip(masked, gold_any)),
        "non_gold_chars": n - sum(gold_any),
        "spurious": spurious,
    }


def _prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4)}


def aggregate(scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine per-document scores into the receipt's ``metrics`` section."""
    by_label: dict[str, Counter] = defaultdict(Counter)
    for doc in scored:
        for ent in doc["entities"]:
            c = by_label[ent["label"]]
            c["total"] += 1
            c[ent["outcome"]] += 1
            c["exposed_chars"] += ent["exposed_chars"]
            if ent["outcome"] == "covered" and ent["type_correct"]:
                c["covered_correct_type"] += 1

    labels = {}
    for label in sorted(by_label):
        c = by_label[label]
        labels[label] = {
            "total": c["total"],
            "covered": c["covered"],
            "partial": c["partial"],
            "missed": c["missed"],
            "covered_correct_type": c["covered_correct_type"],
            "exposed_chars": c["exposed_chars"],
            "full_coverage_rate": round(c["covered"] / c["total"], 4),
        }

    totals = Counter()
    for c in by_label.values():
        totals.update({k: c[k] for k in ("total", "covered", "partial", "missed", "covered_correct_type")})

    char = {}
    for cat in CATEGORIES:
        tp = sum(d["char_counts"][cat][0] for d in scored)
        fp = sum(d["char_counts"][cat][1] for d in scored)
        fn = sum(d["char_counts"][cat][2] for d in scored)
        char[cat] = {**_prf(tp, fp, fn), "tp": tp, "fp": fp, "fn": fn}

    overmasked = sum(d["overmasked_chars"] for d in scored)
    non_gold = sum(d["non_gold_chars"] for d in scored)
    spurious = Counter(t for d in scored for t in d["spurious"])
    leaked_docs = sum(any(e["outcome"] != "covered" for e in d["entities"]) for d in scored)
    return {
        "entities": {
            "total": totals["total"],
            "covered": totals["covered"],
            "partial": totals["partial"],
            "missed": totals["missed"],
            "covered_correct_type": totals["covered_correct_type"],
            "full_coverage_rate": round(totals["covered"] / totals["total"], 4) if totals["total"] else 0.0,
        },
        "documents": {"total": len(scored), "with_exposed_pii": leaked_docs},
        "overmasking": {
            "chars": overmasked,
            "rate": round(overmasked / non_gold, 4) if non_gold else 0.0,
            "spurious_replacements": sum(spurious.values()),
            "spurious_by_type": dict(sorted(spurious.items())),
        },
        "by_label": labels,
        "char_level": char,
    }


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

def run(rows: list[dict[str, Any]], spacy_model: str | None, keep_postcode: bool,
        repeats: int) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], list]:
    """Anonymize every row and score it.

    Returns:
        Per-document scores, timing, analyzer details and per-row replacements.
    """
    from allyanonimiser import create_allyanonimiser

    t0 = time.perf_counter()
    ally = create_allyanonimiser(spacy_model=spacy_model, enable_caching=False)
    init_s = time.perf_counter() - t0

    def one_pass() -> list[list[tuple[int, int, str]]]:
        out = []
        for row in rows:
            result = ally.anonymize(row["text"], keep_postcode=keep_postcode)
            out.append([(it["start"], it["end"], it["entity_type"]) for it in result["items"]])
        return out

    if rows:
        ally.anonymize(rows[0]["text"])  # warm lazily initialised components
    run_times, replaced = [], []
    for _ in range(max(1, repeats)):
        t0 = time.perf_counter()
        current = one_pass()
        run_times.append(time.perf_counter() - t0)
        if replaced and current != replaced:
            raise RuntimeError("Non-deterministic output across repeated passes")
        replaced = current

    scored = [score_document(r["text"], r["spans"], rep) for r, rep in zip(rows, replaced)]
    median = statistics.median(run_times)
    chars = sum(len(r["text"]) for r in rows)
    timing = {
        "init_seconds": round(init_s, 3),
        "warm_pass_seconds_median": round(median, 3),
        "passes": len(run_times),
        "docs_per_second": round(len(rows) / median, 1) if median else None,
        "chars_per_second": round(chars / median) if median else None,
    }
    analyzer = {
        "spacy_model_requested": spacy_model,
        "spacy_model_loaded": ally.analyzer.spacy_model_loaded if ally.analyzer.use_spacy else None,
        "min_score_threshold": ally.analyzer.min_score_threshold,
        "pattern_count": len(ally.analyzer.patterns),
    }
    return scored, timing, analyzer, replaced


def _git_revision() -> dict[str, Any]:
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "allyanonimiser"],
                                    cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip())
        return {"revision": rev, "package_dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"revision": None, "package_dirty": None}


def _versions() -> dict[str, str | None]:
    from importlib.metadata import PackageNotFoundError, version

    import allyanonimiser

    out: dict[str, str | None] = {"allyanonimiser": allyanonimiser.__version__}
    for dist in ("spacy", "en_core_web_sm", "en_core_web_lg", "presidio-analyzer", "pandas"):
        try:
            out[dist] = version(dist)
        except PackageNotFoundError:
            out[dist] = None
    return out


def build_receipt(args: argparse.Namespace, rows: list[dict[str, Any]], corpus_hash: str) -> tuple[dict[str, Any], list]:
    """Run the evaluation and assemble a reproducibility receipt."""
    scored, timing, analyzer, replaced = run(rows, args.spacy_model, args.keep_postcode, args.repeats)
    receipt = {
        "receipt_schema": RECEIPT_SCHEMA,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "corpus": {
            "path": os.path.relpath(args.corpus, REPO_ROOT),
            "sha256": corpus_hash,
            "split": args.split,
            "documents": len(rows),
            "families": dict(sorted(Counter(r["family"] for r in rows).items())),
        },
        "config": {
            **analyzer,
            "keep_postcode": args.keep_postcode,
            "enable_caching": False,
        },
        "source": _git_revision(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or None,
            "cpu_count": os.cpu_count(),
            "versions": _versions(),
        },
        "timing": timing,
        "metrics": aggregate(scored),
    }
    return receipt, replaced


# ---------------------------------------------------------------------------
# Regression comparison
# ---------------------------------------------------------------------------

def compare(current: dict[str, Any], baseline: dict[str, Any],
            overmask_tolerance: float = 0.0) -> tuple[list[str], list[str], list[str]]:
    """Compare quality metrics against a baseline receipt.

    A regression is any gold label with more missed or partially exposed
    entities, fewer correctly typed covered entities, more documents with
    exposed PII, or an over-masking rate above baseline plus tolerance.
    Timing is never compared.

    Returns:
        ``(regressions, improvements, warnings)`` as readable messages.
    """
    regressions, improvements, warnings = [], [], []
    for key in ("sha256", "split"):
        if current["corpus"][key] != baseline["corpus"][key]:
            warnings.append(f"corpus {key} differs from baseline; comparison may be meaningless")
    for key in ("spacy_model_loaded", "keep_postcode"):
        if current["config"].get(key) != baseline["config"].get(key):
            warnings.append(f"config {key}: baseline {baseline['config'].get(key)!r}, "
                            f"current {current['config'].get(key)!r}")

    cur, base = current["metrics"], baseline["metrics"]
    labels = sorted(set(cur["by_label"]) | set(base["by_label"]))
    for label in labels:
        c = cur["by_label"].get(label)
        b = base["by_label"].get(label)
        if c is None or b is None:
            warnings.append(f"{label}: present in only one receipt")
            continue
        for field, worse_if_higher in (("missed", True), ("partial", True), ("covered_correct_type", False)):
            delta = c[field] - b[field]
            if not delta:
                continue
            worse = delta > 0 if worse_if_higher else delta < 0
            msg = f"{label}: {field} {b[field]} -> {c[field]}"
            (regressions if worse else improvements).append(msg)

    d = cur["documents"]["with_exposed_pii"] - base["documents"]["with_exposed_pii"]
    if d:
        msg = f"documents with exposed PII {base['documents']['with_exposed_pii']} -> {cur['documents']['with_exposed_pii']}"
        (regressions if d > 0 else improvements).append(msg)

    rate_c, rate_b = cur["overmasking"]["rate"], base["overmasking"]["rate"]
    if rate_c > rate_b + overmask_tolerance:
        regressions.append(f"over-masking rate {rate_b} -> {rate_c} (tolerance {overmask_tolerance})")
    elif rate_c < rate_b:
        improvements.append(f"over-masking rate {rate_b} -> {rate_c}")
    return regressions, improvements, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_summary(receipt: dict[str, Any]) -> None:
    """Print a compact human-readable summary of a receipt."""
    m = receipt["metrics"]
    cfg = receipt["config"]
    print(f"Corpus: {receipt['corpus']['documents']} docs, split={receipt['corpus']['split']}, "
          f"sha256={receipt['corpus']['sha256'][:12]}")
    print(f"Model: {cfg['spacy_model_loaded'] or 'pattern-only'}   keep_postcode={cfg['keep_postcode']}")
    print()
    print(f"{'Gold label':<24} {'total':>6} {'covered':>8} {'partial':>8} {'missed':>7} {'type ok':>8}")
    print("-" * 66)
    for label, c in m["by_label"].items():
        print(f"{label:<24} {c['total']:>6} {c['covered']:>8} {c['partial']:>8} {c['missed']:>7} "
              f"{c['covered_correct_type']:>8}")
    e = m["entities"]
    print("-" * 66)
    print(f"{'ALL':<24} {e['total']:>6} {e['covered']:>8} {e['partial']:>8} {e['missed']:>7} "
          f"{e['covered_correct_type']:>8}")
    print()
    print(f"Documents with exposed PII: {m['documents']['with_exposed_pii']} / {m['documents']['total']}")
    o = m["overmasking"]
    print(f"Over-masking: {o['chars']} chars ({o['rate']:.2%} of non-PII text), "
          f"{o['spurious_replacements']} replacements touching no gold span")
    t = receipt["timing"]
    print(f"Timing: init {t['init_seconds']}s, warm pass {t['warm_pass_seconds_median']}s "
          f"({t['docs_per_second']} docs/s, median of {t['passes']})")


def print_failures(rows: list[dict[str, Any]], replaced: list, limit: int) -> None:
    """Print missed and partial gold spans with context. Synthetic corpora only."""
    shown = 0
    for row, rep in zip(rows, replaced):
        doc = score_document(row["text"], row["spans"], rep)
        for span, ent in zip(row["spans"], doc["entities"]):
            if ent["outcome"] == "covered" and ent["type_correct"]:
                continue
            if shown >= limit:
                return
            s, e = span["start"], span["end"]
            ctx = row["text"][max(0, s - 30):e + 30].replace("\n", " ")
            types = sorted({t for a, b, t in rep if a < e and b > s}) or ["-"]
            print(f"  row {row['row']:>3} {row['family']:<22} {span['label']:<22} "
                  f"{ent['outcome']:<8} got={','.join(types):<28} ...{ctx}...")
            shown += 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all")
    parser.add_argument("--spacy-model", default=None,
                        help="spaCy model name; omit for pattern-only detection")
    parser.add_argument("--keep-postcode", action="store_true",
                        help="Use the library default of retaining postcodes (counts them as exposed)")
    parser.add_argument("--repeats", type=int, default=3, help="Timed passes (median reported)")
    parser.add_argument("--out", type=Path, help="Write the receipt JSON here")
    parser.add_argument("--baseline", type=Path, help="Fail if quality regresses against this receipt")
    parser.add_argument("--overmask-tolerance", type=float, default=0.0,
                        help="Allowed absolute increase in over-masking rate")
    parser.add_argument("--show-failures", type=int, default=0, metavar="N",
                        help="Print up to N missed, partial or mistyped spans (synthetic data only)")
    args = parser.parse_args(argv)

    logging.disable(logging.WARNING)
    rows, corpus_hash = load_corpus(args.corpus, args.split)
    receipt, replaced = build_receipt(args, rows, corpus_hash)
    print_summary(receipt)
    if args.show_failures:
        print("\nFailures:")
        print_failures(rows, replaced, args.show_failures)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"\nWrote {args.out}")

    if args.baseline:
        baseline = json.loads(args.baseline.read_text())
        regressions, improvements, warnings = compare(receipt, baseline, args.overmask_tolerance)
        print(f"\nCompared with {args.baseline}:")
        for w in warnings:
            print(f"  WARNING  {w}")
        for msg in improvements:
            print(f"  improved {msg}")
        for msg in regressions:
            print(f"  REGRESSED {msg}")
        if regressions:
            return 1
        if improvements:
            print("  No regressions. Refresh the baseline with --out to lock in improvements.")
        else:
            print("  No changes in quality metrics.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
