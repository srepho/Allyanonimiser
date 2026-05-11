"""
Head-to-head on the synthetic AU-insurance eval.

Same char-level P/R/F1 scoring. Categories are chosen around the AU insurance
domain: PERSON, ADDRESS, EMAIL, PHONE, DATE, and ACCOUNT_LIKE (covers TFN,
Medicare, ABN, ACN, policy, claim, vehicle reg, VIN).
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

GOLD_TO_CAT = {
    "PERSON": "PERSON",
    "AU_ADDRESS": "ADDRESS",
    "EMAIL_ADDRESS": "EMAIL",
    "AU_PHONE": "PHONE",
    "PHONE_INTL": "PHONE",
    "DATE": "DATE",
    "ISO_DATETIME": "DATE",
    "TIME": "DATE",
    "AU_TFN": "ACCOUNT_LIKE",
    "AU_MEDICARE": "ACCOUNT_LIKE",
    "AU_ABN": "ACCOUNT_LIKE",
    "AU_ACN": "ACCOUNT_LIKE",
    "POLICY_NUMBER": "ACCOUNT_LIKE",
    "INSURANCE_CLAIM_NUMBER": "ACCOUNT_LIKE",
    "VEHICLE_REGISTRATION": "ACCOUNT_LIKE",
    "VIN": "ACCOUNT_LIKE",
    "US_SSN": "ACCOUNT_LIKE",
    "CREDIT_CARD_NUMBER": "ACCOUNT_LIKE",
}

OPENAI_TO_CAT = {
    "private_person": "PERSON",
    "private_address": "ADDRESS",
    "private_email": "EMAIL",
    "private_phone": "PHONE",
    "private_date": "DATE",
    "account_number": "ACCOUNT_LIKE",
}

ALLY_TO_CAT = {
    "PERSON": "PERSON",
    "AU_ADDRESS": "ADDRESS",
    "LOCATION": "ADDRESS",
    "EMAIL_ADDRESS": "EMAIL",
    "AU_PHONE": "PHONE",
    "PHONE_INTL": "PHONE", "PHONE_NUMBER": "PHONE",
    "DATE": "DATE", "DATE_OF_BIRTH": "DATE", "INCIDENT_DATE": "DATE",
    "ISO_DATETIME": "DATE", "TIME": "DATE",
    "AU_TFN": "ACCOUNT_LIKE",
    "AU_MEDICARE": "ACCOUNT_LIKE",
    "AU_ABN": "ACCOUNT_LIKE",
    "AU_ACN": "ACCOUNT_LIKE",
    "AU_CENTRELINK_CRN": "ACCOUNT_LIKE",
    "INSURANCE_POLICY_NUMBER": "ACCOUNT_LIKE",
    "INSURANCE_CLAIM_NUMBER": "ACCOUNT_LIKE",
    "VEHICLE_REGISTRATION": "ACCOUNT_LIKE",
    "VEHICLE_VIN": "ACCOUNT_LIKE",
    "AU_POSTCODE": "ADDRESS",
    "US_SSN": "ACCOUNT_LIKE",
    "CREDIT_CARD": "ACCOUNT_LIKE",
    "CREDIT_CARD_NUMBER": "ACCOUNT_LIKE",
}

CATEGORIES = ["PERSON", "ADDRESS", "EMAIL", "PHONE", "DATE", "ACCOUNT_LIKE"]


def mask_runs(mask):
    """Return contiguous true regions from a boolean mask."""
    runs = []
    start = None
    for i, value in enumerate(mask):
        if value and start is None:
            start = i
        elif not value and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(mask)))
    return runs


def snippet(text, start, end, window=48):
    before = max(0, start - window)
    after = min(len(text), end + window)
    prefix = "..." if before else ""
    suffix = "..." if after < len(text) else ""
    return prefix + text[before:after] + suffix


def collect_examples(examples, tool, cat, kind, text, mask, row_idx):
    for start, end in mask_runs(mask):
        examples[tool][cat][kind].append({
            "row": row_idx,
            "start": start,
            "end": end,
            "length": end - start,
            "text": text[start:end],
            "context": snippet(text, start, end),
        })


def trim_examples(examples, limit):
    if limit <= 0:
        return {}

    out = {}
    for tool, tool_examples in examples.items():
        out[tool] = {}
        for cat, cat_examples in tool_examples.items():
            out[tool][cat] = {}
            for kind, values in cat_examples.items():
                out[tool][cat][kind] = sorted(
                    values,
                    key=lambda item: item["length"],
                    reverse=True,
                )[:limit]
    return out


def decode_bioes(labels, offsets):
    spans, cur_start, cur_base, cur_end = [], None, None, None
    for lab, (s, e) in zip(labels, offsets):
        if s == e == 0:
            continue
        if lab == "O":
            if cur_base is not None:
                spans.append((cur_start, cur_end, cur_base))
                cur_base = None
            continue
        base = lab.split("-", 1)[1] if "-" in lab else lab
        if cur_base is None or base != cur_base:
            if cur_base is not None:
                spans.append((cur_start, cur_end, cur_base))
            cur_start, cur_base = s, base
        cur_end = e
    if cur_base is not None:
        spans.append((cur_start, cur_end, cur_base))
    return spans


def mask_by_cat(tlen, spans, label_to_cat):
    masks = {c: np.zeros(tlen, dtype=bool) for c in CATEGORIES}
    masks["ANY"] = np.zeros(tlen, dtype=bool)
    for s, e, t in spans:
        cat = label_to_cat.get(t)
        if cat:
            masks[cat][s:e] = True
        masks["ANY"][s:e] = True
    return masks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="bench/data/au_insurance.jsonl")
    ap.add_argument("--out", default="bench/results_au_insurance.json")
    ap.add_argument(
        "--examples",
        type=int,
        default=5,
        help="number of longest FP/FN examples to include per tool/category",
    )
    args = ap.parse_args()

    rows = [json.loads(line) for line in open(args.data)]
    print(f"Loaded {len(rows)} rows")

    t0 = time.time()
    sess = ort.InferenceSession(
        hf_hub_download("openai/privacy-filter", "onnx/model_q4.onnx"),
        providers=["CPUExecutionProvider"],
    )
    tok = Tokenizer.from_file(hf_hub_download("openai/privacy-filter", "tokenizer.json"))
    cfg = json.load(open(hf_hub_download("openai/privacy-filter", "config.json")))
    id2label = {int(k): v for k, v in cfg["id2label"].items()}
    print(f"openai loaded in {time.time()-t0:.1f}s")

    t0 = time.time()
    ally = create_allyanonimiser()
    print(f"ally loaded in {time.time()-t0:.1f}s")

    totals = {"openai": defaultdict(lambda: [0, 0, 0]),
              "ally":   defaultdict(lambda: [0, 0, 0])}
    timings = {"openai": 0.0, "ally": 0.0}
    examples = {
        tool: {
            cat: {"false_positives": [], "false_negatives": []}
            for cat in CATEGORIES + ["ANY"]
        }
        for tool in ("openai", "ally")
    }

    for i, row in enumerate(rows):
        text = row["text"]
        tlen = len(text)
        gold_spans = [(s["start"], s["end"], s["label"]) for s in row["spans"]]
        gold = mask_by_cat(tlen, gold_spans, GOLD_TO_CAT)

        t0 = time.time()
        enc = tok.encode(text)
        ids = np.array([enc.ids], dtype=np.int64)
        out = sess.run(None, {"input_ids": ids, "attention_mask": np.ones_like(ids)})
        preds = out[0][0].argmax(axis=-1)
        oai_spans = decode_bioes([id2label[p] for p in preds], enc.offsets)
        timings["openai"] += time.time() - t0
        oai_mask = mask_by_cat(tlen, oai_spans, OPENAI_TO_CAT)

        t0 = time.time()
        ally_res = ally.analyze(text)
        ally_spans = [(r.start, r.end, r.entity_type) for r in ally_res]
        timings["ally"] += time.time() - t0
        ally_mask = mask_by_cat(tlen, ally_spans, ALLY_TO_CAT)

        for cat in CATEGORIES + ["ANY"]:
            for name, mask in [("openai", oai_mask[cat]), ("ally", ally_mask[cat])]:
                fp_mask = ~gold[cat] & mask
                fn_mask = gold[cat] & ~mask
                tp = int((gold[cat] & mask).sum())
                fp = int(fp_mask.sum())
                fn = int(fn_mask.sum())
                totals[name][cat][0] += tp
                totals[name][cat][1] += fp
                totals[name][cat][2] += fn
                if args.examples:
                    collect_examples(examples, name, cat, "false_positives", text, fp_mask, i)
                    collect_examples(examples, name, cat, "false_negatives", text, fn_mask, i)

        if (i + 1) % 25 == 0 or i == len(rows) - 1:
            print(f"  {i+1}/{len(rows)}  (openai {timings['openai']:.0f}s, ally {timings['ally']:.0f}s)")

    def prf(tp, fp, fn):
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        return p, r, f

    print("\n" + "=" * 86)
    print(f"{'Category':<14} {'Tool':<8} {'P':>7} {'R':>7} {'F1':>7}   {'TP':>8} {'FP':>8} {'FN':>8}")
    print("-" * 86)
    summary = {}
    for cat in CATEGORIES + ["ANY"]:
        for name in ("openai", "ally"):
            tp, fp, fn = totals[name][cat]
            p, r, f = prf(tp, fp, fn)
            print(f"{cat:<14} {name:<8} {p:7.3f} {r:7.3f} {f:7.3f}   {tp:>8} {fp:>8} {fn:>8}")
            summary.setdefault(cat, {})[name] = {"P": p, "R": r, "F1": f, "TP": tp, "FP": fp, "FN": fn}
        print()

    print("-" * 86)
    print(f"Time: openai={timings['openai']:.1f}s   ally={timings['ally']:.1f}s   n={len(rows)}")
    Path(args.out).write_text(json.dumps({
        "n": len(rows),
        "timings": timings,
        "summary": summary,
        "examples": trim_examples(examples, args.examples),
    }, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
