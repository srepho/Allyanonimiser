"""
Smoke-test eval: Allyanonimiser vs openai/privacy-filter on TAB dev (ECHR).

Gold: union of (DIRECT + QUASI) entity_mentions across annotators per doc_id.
Scoring: character-level binary masking per category (what fraction of chars
that *should* be redacted actually were, and with what precision).

Categories compared (intersection of both tools' taxonomies with TAB gold):
  PERSON, LOCATION, DATE, CODE

Plus an overall type-agnostic score (did we mask the char at all).
"""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

from allyanonimiser import create_allyanonimiser

TAB_TO_CAT = {
    "PERSON": "PERSON",
    "LOC": "LOCATION",
    "DATETIME": "DATE",
    "CODE": "CODE",
}

OPENAI_TO_CAT = {
    "private_person": "PERSON",
    "private_address": "LOCATION",
    "private_date": "DATE",
    "account_number": "CODE",
}

ALLY_TO_CAT = {
    "PERSON": "PERSON",
    "LOCATION": "LOCATION",
    "AU_ADDRESS": "LOCATION",
    "DATE": "DATE",
    "DATE_OF_BIRTH": "DATE",
    "AU_TFN": "CODE",
    "AU_MEDICARE": "CODE",
    "AU_ABN": "CODE",
    "AU_ACN": "CODE",
    "AU_POSTCODE": "CODE",
    "POLICY_NUMBER": "CODE",
    "INSURANCE_CLAIM_NUMBER": "CODE",
    "VEHICLE_REGISTRATION": "CODE",
    "VIN": "CODE",
}

CATEGORIES = ["PERSON", "LOCATION", "DATE", "CODE"]


def load_tab_dev(path):
    data = json.load(open(path))
    by_doc = defaultdict(list)
    for rec in data:
        by_doc[rec["doc_id"]].append(rec)
    docs = []
    for doc_id, recs in by_doc.items():
        text = recs[0]["text"]
        spans = []
        for r in recs:
            for em in r["entity_mentions"]:
                if em["identifier_type"] in ("DIRECT", "QUASI"):
                    spans.append((em["start_offset"], em["end_offset"], em["entity_type"]))
        docs.append({"doc_id": doc_id, "text": text, "gold_spans": spans})
    return docs


def gold_mask_by_cat(text_len, spans):
    masks = {c: np.zeros(text_len, dtype=bool) for c in CATEGORIES}
    masks["ANY"] = np.zeros(text_len, dtype=bool)
    for s, e, t in spans:
        cat = TAB_TO_CAT.get(t)
        if cat:
            masks[cat][s:e] = True
        # ANY includes even ORG/DEM/MISC/QUANTITY since those are also PII-adjacent
        masks["ANY"][s:e] = True
    return masks


def decode_bioes(labels, offsets):
    """Greedy BIOES → (start, end, label) spans. Tolerates noise by
    treating any non-O label as a span character; merges contiguous same-label
    tokens."""
    spans = []
    cur_start = None
    cur_base = None
    cur_end = None
    for lab, (s, e) in zip(labels, offsets):
        if s == e == 0:  # special / padding
            continue
        if lab == "O":
            if cur_base is not None:
                spans.append((cur_start, cur_end, cur_base))
                cur_base = None
            continue
        # lab like "B-private_person"; we only need the base type
        base = lab.split("-", 1)[1] if "-" in lab else lab
        if cur_base is None or base != cur_base:
            if cur_base is not None:
                spans.append((cur_start, cur_end, cur_base))
            cur_start, cur_base = s, base
        cur_end = e
    if cur_base is not None:
        spans.append((cur_start, cur_end, cur_base))
    return spans


def run_openai_filter(text, sess, tok):
    enc = tok.encode(text)
    ids = np.array([enc.ids], dtype=np.int64)
    out = sess.run(None, {"input_ids": ids, "attention_mask": np.ones_like(ids)})
    preds = out[0][0].argmax(axis=-1)
    labels = [ID2LABEL[p] for p in preds]
    return decode_bioes(labels, enc.offsets)


def pred_mask_by_cat(text_len, spans, label_to_cat):
    masks = {c: np.zeros(text_len, dtype=bool) for c in CATEGORIES}
    masks["ANY"] = np.zeros(text_len, dtype=bool)
    for s, e, t in spans:
        cat = label_to_cat.get(t)
        if cat:
            masks[cat][s:e] = True
        masks["ANY"][s:e] = True
    return masks


def score(gold, pred):
    tp = int((gold & pred).sum())
    fp = int((~gold & pred).sum())
    fn = int((gold & ~pred).sum())
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return tp, fp, fn, p, r, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0, help="0 = all docs")
    ap.add_argument("--out", default="bench/results_tab.json")
    args = ap.parse_args()

    print("Loading TAB dev...")
    docs = load_tab_dev("bench/data/echr_dev/echr_dev.json")
    if args.sample:
        docs = sorted(docs, key=lambda d: len(d["text"]))[: args.sample]
    print(f"  {len(docs)} docs, {sum(len(d['text']) for d in docs):,} chars total")

    print("Loading openai/privacy-filter (q4 ONNX)...")
    t0 = time.time()
    sess = ort.InferenceSession(
        hf_hub_download("openai/privacy-filter", "onnx/model_q4.onnx"),
        providers=["CPUExecutionProvider"],
    )
    tok = Tokenizer.from_file(hf_hub_download("openai/privacy-filter", "tokenizer.json"))
    global ID2LABEL
    cfg = json.load(open(hf_hub_download("openai/privacy-filter", "config.json")))
    ID2LABEL = {int(k): v for k, v in cfg["id2label"].items()}
    print(f"  loaded in {time.time()-t0:.1f}s")

    print("Loading Allyanonimiser...")
    t0 = time.time()
    ally = create_allyanonimiser()
    print(f"  loaded in {time.time()-t0:.1f}s")

    totals = {"openai": defaultdict(lambda: [0, 0, 0]),
              "ally":   defaultdict(lambda: [0, 0, 0])}
    timings = {"openai": 0.0, "ally": 0.0}

    for i, d in enumerate(docs):
        text, tlen = d["text"], len(d["text"])
        gold = gold_mask_by_cat(tlen, d["gold_spans"])

        t0 = time.time()
        oai_spans = run_openai_filter(text, sess, tok)
        timings["openai"] += time.time() - t0
        oai_mask = pred_mask_by_cat(tlen, oai_spans, OPENAI_TO_CAT)

        t0 = time.time()
        ally_results = ally.analyze(text)
        ally_spans = [(r.start, r.end, r.entity_type) for r in ally_results]
        timings["ally"] += time.time() - t0
        ally_mask = pred_mask_by_cat(tlen, ally_spans, ALLY_TO_CAT)

        for cat in CATEGORIES + ["ANY"]:
            for name, mask in [("openai", oai_mask[cat]), ("ally", ally_mask[cat])]:
                tp, fp, fn, *_ = score(gold[cat], mask)
                totals[name][cat][0] += tp
                totals[name][cat][1] += fp
                totals[name][cat][2] += fn

        if (i + 1) % 10 == 0 or i == len(docs) - 1:
            print(f"  {i+1}/{len(docs)} done  (openai {timings['openai']:.0f}s, ally {timings['ally']:.0f}s)")

    def prf(tp, fp, fn):
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        return p, r, f

    print("\n" + "=" * 78)
    print(f"{'Category':<12} {'Tool':<8} {'P':>7} {'R':>7} {'F1':>7}   {'TP':>8} {'FP':>8} {'FN':>8}")
    print("-" * 78)
    summary = {}
    for cat in CATEGORIES + ["ANY"]:
        for name in ("openai", "ally"):
            tp, fp, fn = totals[name][cat]
            p, r, f = prf(tp, fp, fn)
            print(f"{cat:<12} {name:<8} {p:7.3f} {r:7.3f} {f:7.3f}   {tp:>8} {fp:>8} {fn:>8}")
            summary.setdefault(cat, {})[name] = {"P": p, "R": r, "F1": f, "TP": tp, "FP": fp, "FN": fn}
        print()

    print("-" * 78)
    print(f"Time: openai={timings['openai']:.1f}s   ally={timings['ally']:.1f}s   docs={len(docs)}")
    Path(args.out).write_text(json.dumps({
        "n_docs": len(docs),
        "timings": timings,
        "summary": summary,
    }, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
