"""
Head-to-head eval on AI4Privacy open-pii-masking-500k (English slice).

Same char-level binary masking scoring as TAB eval. AI4Privacy labels map
cleanly to both openai/privacy-filter's 8 categories and Allyanonimiser's
entity taxonomy, so all 8 categories are comparable.
"""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import onnxruntime as ort
from datasets import load_dataset
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

from allyanonimiser import create_allyanonimiser

# AI4Privacy label -> common category (aligned to openai's 8)
GOLD_TO_CAT = {
    "GIVENNAME": "PERSON", "SURNAME": "PERSON", "TITLE": "PERSON",
    "CITY": "ADDRESS", "STREET": "ADDRESS", "BUILDINGNUM": "ADDRESS",
    "ZIPCODE": "ADDRESS", "STATE": "ADDRESS", "COUNTRY": "ADDRESS",
    "EMAIL": "EMAIL",
    "TELEPHONENUM": "PHONE",
    "DATE": "DATE", "TIME": "DATE",
    "IDCARDNUM": "ACCOUNT", "TAXNUM": "ACCOUNT", "CREDITCARDNUMBER": "ACCOUNT",
    "SOCIALNUM": "ACCOUNT", "PASSPORTNUM": "ACCOUNT", "DRIVERLICENSENUM": "ACCOUNT",
    "USERNAME": "PERSON",  # closest common-category fit
}

OPENAI_TO_CAT = {
    "private_person": "PERSON",
    "private_address": "ADDRESS",
    "private_email": "EMAIL",
    "private_phone": "PHONE",
    "private_date": "DATE",
    "account_number": "ACCOUNT",
    "private_url": "URL",
    "secret": "SECRET",
}

ALLY_TO_CAT = {
    "PERSON": "PERSON",
    "LOCATION": "ADDRESS", "AU_ADDRESS": "ADDRESS", "AU_POSTCODE": "ADDRESS",
    "EMAIL_ADDRESS": "EMAIL",
    "AU_PHONE": "PHONE", "PHONE_NUMBER": "PHONE",
    "DATE": "DATE", "DATE_OF_BIRTH": "DATE", "TIME": "DATE",
    "AU_TFN": "ACCOUNT", "AU_MEDICARE": "ACCOUNT", "AU_ABN": "ACCOUNT",
    "AU_ACN": "ACCOUNT", "AU_PASSPORT": "ACCOUNT",
    "POLICY_NUMBER": "ACCOUNT", "INSURANCE_CLAIM_NUMBER": "ACCOUNT",
    "VEHICLE_REGISTRATION": "ACCOUNT", "VIN": "ACCOUNT",
    "CREDIT_CARD": "ACCOUNT", "US_SSN": "ACCOUNT",
    "URL": "URL",
    "PASSWORD": "SECRET", "API_KEY": "SECRET",
}

CATEGORIES = ["PERSON", "ADDRESS", "EMAIL", "PHONE", "DATE", "ACCOUNT", "URL", "SECRET"]


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


def mask_by_cat(text_len, spans, label_to_cat):
    masks = {c: np.zeros(text_len, dtype=bool) for c in CATEGORIES}
    masks["ANY"] = np.zeros(text_len, dtype=bool)
    for s, e, t in spans:
        cat = label_to_cat.get(t)
        if cat:
            masks[cat][s:e] = True
        masks["ANY"][s:e] = True
    return masks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000, help="number of English rows to evaluate")
    ap.add_argument("--split", default="validation", choices=["train", "validation"])
    ap.add_argument("--out", default="bench/results_ai4privacy.json")
    args = ap.parse_args()

    print(f"Loading AI4Privacy open-pii-500k ({args.split} split, English)...")
    ds = load_dataset("ai4privacy/open-pii-masking-500k-ai4privacy", split=args.split, streaming=True)
    rows = []
    for r in ds:
        if r.get("language") == "en":
            rows.append(r)
            if len(rows) >= args.n:
                break
    print(f"  {len(rows)} English rows")

    print("Loading openai/privacy-filter (q4 ONNX)...")
    t0 = time.time()
    sess = ort.InferenceSession(
        hf_hub_download("openai/privacy-filter", "onnx/model_q4.onnx"),
        providers=["CPUExecutionProvider"],
    )
    tok = Tokenizer.from_file(hf_hub_download("openai/privacy-filter", "tokenizer.json"))
    cfg = json.load(open(hf_hub_download("openai/privacy-filter", "config.json")))
    id2label = {int(k): v for k, v in cfg["id2label"].items()}
    print(f"  loaded in {time.time()-t0:.1f}s")

    print("Loading Allyanonimiser...")
    t0 = time.time()
    ally = create_allyanonimiser()
    print(f"  loaded in {time.time()-t0:.1f}s")

    totals = {"openai": defaultdict(lambda: [0, 0, 0]),
              "ally":   defaultdict(lambda: [0, 0, 0])}
    timings = {"openai": 0.0, "ally": 0.0}

    for i, row in enumerate(rows):
        text = row["source_text"]
        tlen = len(text)
        pm = row.get("privacy_mask") or []
        if isinstance(pm, str):
            pm = json.loads(pm)
        gold_spans = [(m["start"], m["end"], m["label"]) for m in pm]
        gold = mask_by_cat(tlen, gold_spans, GOLD_TO_CAT)

        t0 = time.time()
        enc = tok.encode(text)
        ids = np.array([enc.ids], dtype=np.int64)
        out = sess.run(None, {"input_ids": ids, "attention_mask": np.ones_like(ids)})
        preds = out[0][0].argmax(axis=-1)
        oai_labels = [id2label[p] for p in preds]
        oai_spans = decode_bioes(oai_labels, enc.offsets)
        timings["openai"] += time.time() - t0
        oai_mask = mask_by_cat(tlen, oai_spans, OPENAI_TO_CAT)

        t0 = time.time()
        ally_res = ally.analyze(text)
        ally_spans = [(r.start, r.end, r.entity_type) for r in ally_res]
        timings["ally"] += time.time() - t0
        ally_mask = mask_by_cat(tlen, ally_spans, ALLY_TO_CAT)

        for cat in CATEGORIES + ["ANY"]:
            for name, mask in [("openai", oai_mask[cat]), ("ally", ally_mask[cat])]:
                tp = int((gold[cat] & mask).sum())
                fp = int((~gold[cat] & mask).sum())
                fn = int((gold[cat] & ~mask).sum())
                totals[name][cat][0] += tp
                totals[name][cat][1] += fp
                totals[name][cat][2] += fn

        if (i + 1) % 200 == 0 or i == len(rows) - 1:
            print(f"  {i+1}/{len(rows)}  (openai {timings['openai']:.0f}s, ally {timings['ally']:.0f}s)")

    def prf(tp, fp, fn):
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        return p, r, f

    print("\n" + "=" * 82)
    print(f"{'Category':<10} {'Tool':<8} {'P':>7} {'R':>7} {'F1':>7}   {'TP':>8} {'FP':>8} {'FN':>8}")
    print("-" * 82)
    summary = {}
    for cat in CATEGORIES + ["ANY"]:
        for name in ("openai", "ally"):
            tp, fp, fn = totals[name][cat]
            p, r, f = prf(tp, fp, fn)
            print(f"{cat:<10} {name:<8} {p:7.3f} {r:7.3f} {f:7.3f}   {tp:>8} {fp:>8} {fn:>8}")
            summary.setdefault(cat, {})[name] = {"P": p, "R": r, "F1": f, "TP": tp, "FP": fp, "FN": fn}
        print()

    print("-" * 82)
    print(f"Time: openai={timings['openai']:.1f}s   ally={timings['ally']:.1f}s   n={len(rows)}")
    Path(args.out).write_text(json.dumps({
        "n": len(rows),
        "split": args.split,
        "timings": timings,
        "summary": summary,
    }, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
