# v4 engine: design notes and status

Work happens on the `v4` branch. The v4 engine lives in `allyanonimiser/v4/`
beside the v3 facade until it is at least as good on every evaluation, then
replaces it as the public API in a major release.

## Decisions

**Implementation language: Python, with detectors behind an interface.**
Measured on the 160-document AU corpus with caching off, regex rules run at
roughly 260,000 characters per second and spaCy inference takes about 90% of
runtime when a model is used. A native rule engine cannot move the dominant
cost, and Rust's regex crate lacks look-around, which 15 built-in patterns and
many user patterns rely on. A native core stays possible later behind the
`Detector` interface if profiling of real workloads shows a rules bottleneck.

**Reuse tested detection, not rewrite it blind.** The pattern definitions,
validators, label-context rules and false-positive filters carry years of
fixes and two evaluation corpora's worth of regression tests. v4 calls them
through stateless functions (`core/detection.py`, `core/common_formats.py`,
`core/conflict_resolver.py`) and replaces what sits around them: state,
caching, overlap handling, results and the public API.

## Contracts

| Contract | Where | Tested by |
|---|---|---|
| Results are immutable and carry no source values | `v4/types.py` | `test_engine.py` |
| Offsets are code-point indices into the original text, exclusive end | `v4/types.py` | `test_engine.py`, property tests |
| No per-call state or caches; same input, bundle and policy give the same output regardless of earlier calls or batching | `v4/engine.py` | `test_engine.py` |
| Classification and masking are separate: overlaps can change a type, never shrink what is masked | `v4/resolve.py` | `test_segment_properties.py` |
| Replacements are applied once, never overlap, and their output offsets slice what was written | `v4/transform.py` | `test_segment_properties.py` |
| Policies are validated and immutable; retention (such as postcodes) is an explicit choice | `v4/policy.py` | `test_policy.py` |
| The hash operator is keyed (HMAC-SHA256); key material never appears in `repr`, digests or results | `v4/policy.py`, `v4/transform.py` | `test_policy.py`, `test_engine.py` |
| A bundle's model must load with NER; no silent fallback or downloads | `v4/detectors.py`, `v4/engine.py` | `test_engine.py` |
| Results record the bundle version and a policy digest | `v4/engine.py` | `test_engine.py` |

## API

```python
from allyanonimiser.v4 import Engine, Policy

engine = Engine.from_bundle("au-spacy-sm-v1")       # or "au-rules-v1", "au-spacy-lg-v1"
detections = engine.detect(text)                     # DetectionResult, policy-independent
result = engine.transform(text, Policy.redact({"PERSON", "AU_TFN"}))
result.text, result.replacements

for result in engine.transform_many(records, Policy(retain={"AU_POSTCODE"})):
    ...
```

Operators: `replace` (`<TYPE>`), `mask`, `redact`, keyed `hash`, and `keep`.

## Status against v3 (21–22 October 2026)

Entities fully covered, and documents still exposing any PII. Both engines
use the same detectors; differences come from resolution and masking.

| Corpus | Configuration | v3 covered | v4 covered | v3 docs exposing | v4 docs exposing |
|---|---|---|---|---|---|
| AU (160 docs) | rules / sm / lg | 1,340 of 1,340 | 1,340 of 1,340 | 0 | 0 |
| Challenge dev | rules | 2,642 | 2,643 | 113 | 112 |
| Challenge dev | `en_core_web_sm` | 2,669 | 2,671 | 106 | 104 |
| Challenge dev | `en_core_web_lg` | 2,712 | 2,718 | 87 | 83 |

Over-masking is 0.1 to 0.15 points higher in v4, the cost of never dropping
the uncovered part of an overlapping span. With spaCy, v4 is roughly 1.5 to 2
times faster because it batches through `nlp.pipe`.

## Remaining milestones

1. **Adapters:** DataFrame and CSV/streaming adapters on `transform_many`, with
   row positions separate from index labels, explicit column retention,
   staged output files and a completion manifest.
2. **Normalised views:** acronym expansion and other preprocessing through an
   offset map, so entities always land on original coordinates.
3. **Configuration:** versioned, validated bundle and policy files; custom
   patterns as part of a bundle definition.
4. **Model experiments (design-plan milestone C):** additional detector
   bundles (GLiNER, OpenMed, Privacy Filter) behind the same interface,
   compared with `bench/eval_ally.py --engine v4`.
5. **Promotion:** v4 becomes the top-level API, with a migration guide and
   thin v3 compatibility shims only where cheap and unambiguous.
