# Exporting and reloading configuration

Use `export_config()` to save a snapshot of the standard analyzer's live
configuration. JSON and YAML exports include the complete registered regex
pattern set, active entities, detection threshold, requested spaCy model,
cache settings, acronym dictionary, processing settings, and anonymizer
entity priorities.

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser(spacy_model=None)
ally.add_pattern({
    "entity_type": "REFERENCE_CODE",
    "patterns": [r"REF-[A-Z]{4}"],
    "score": 0.8,
})
ally.analyzer.set_active_entity_types(["REFERENCE_CODE"])
ally.analyzer.set_min_score_threshold(0.75)

if not ally.export_config("config.json", include_metadata=False):
    raise RuntimeError("Configuration export failed; see the logged error")

restored = create_allyanonimiser(settings_path="config.json")
assert restored.anonymize("Use REF-ABCD", report=False)["text"] == "Use <REFERENCE_CODE>"
```

YAML requires PyYAML. `include_metadata=False` removes the descriptive counts
and examples; it does not remove functional configuration or pattern definitions.
Exports include custom regexes and acronyms, so review their contents before
sharing them.

## Defaults and precedence

Without a configuration, factory behavior is unchanged: the small spaCy model,
caching enabled, and 10,000 entries per cache. With a configuration, omitted
factory arguments inherit the saved model and cache settings. Explicit
`spacy_model`, `enable_caching`, and `max_cache_size` arguments override the
saved values. Explicit `spacy_model=None` selects pattern-only mode.

The facade exports current analyzer settings. Editing the settings manager's
stored values alone does not reconfigure a running analyzer; use its setters
or load a settings file first. `SettingsManager.export_config()` exports its
stored values directly. `save_settings()` remains the existing stored-settings
API; use the facade's `export_config()` for a live snapshot.

Saved operator maps and score adjustments are preserved as configuration data.
They retain their existing per-call semantics: pass them when invoking the
relevant method, for example:

```python
results = restored.analyze(
    text="Use REF-ABCD",
    score_adjustment=restored.settings_manager.get_value("entity_types.score_adjustment", {}),
)
output = restored.anonymize(
    text="Use REF-ABCD",
    analysis_results=results,
    operators=restored.settings_manager.get_anonymization_operators(),
    report=False,
)
```

Per-call options are not captured as persistent state. To reproduce results,
use the same per-call arguments, package/dependency versions, and installed
spaCy models. Exports contain model names, not model weights, and model fallback
behavior still applies.

## Schema and validation

New exports have `schema_version: 1`. Older files without this field still load.
The existing `version` field is retained separately for compatibility.

Facade snapshots use `patterns_mode: replace`, so loading one restores its
complete pattern set without adding the package defaults a second time.
Ordinary legacy pattern lists append to the built-in patterns. Repeated loads
of the same exported snapshot do not duplicate patterns.

Settings loading validates the schema version, regexes, configuration shapes,
operator names, and numeric ranges before updating stored settings. Unsupported
versions and malformed settings return `False` from `load_settings()` and log
a reason. The factory raises `ValueError` when its requested settings file
cannot be loaded, instead of silently continuing with a different configuration.

Export rejects unsupported custom analyzer/anonymizer subclasses, non-string
pattern definitions, and nonserializable settings. Serialization validation
happens before opening the output file. Arbitrary Python callbacks and
third-party components cannot be reproduced by this format.


## Sensitive-output controls

Both controls are opt-in; existing output shapes and model fallback remain the defaults.

```python
from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser(
    minimal_output=True,
    spacy_model="en_core_web_sm",
    require_spacy_model=True,
)
result = ally.process("Contact sentinel.private@example.com")
```

`minimal_output=True` applies to the facade and its DataFrame, CSV, and stream
processors:

- `anonymize()` omits `original_text` and each item's `original` value.
- `analyze()` returns entity offsets, types, and scores with `text=None`.
  `process()` omits entity text, segments, structured source values, and acronym
  expansion metadata. Batch and text-file helpers use the same profile.
- DataFrame and Polars processing drop selected source columns and omit entity
  text from entity tables/files. Anonymized columns remain. Detection-only
  DataFrame processing drops selected source columns too; Polars streaming
  requires `anonymize=True` in this profile.
- CSV helpers replace selected columns in place, as before. CSV previews omit
  the original-value column. Aggregate CSV statistics remain available.
- Automatic session reports are suppressed even when `report=True`.
  `get_report()` and `start_new_report()` return `None`; finalization reports no
  active report. Existing global reports from other instances are neither read
  through this instance nor cleared or modified.
- All three analyzer result caches are cleared when the profile is applied and
  disabled, even if `enable_caching=True` is also supplied. The model itself can
  remain resident in memory.
- `explain_entity()` is unavailable because its explanation includes source data.

This is an output/retention policy, not a new detector or operator. Unselected
columns, caller-supplied identifiers, filenames, and paths are not sanitized.
Undetected text and content deliberately preserved by operators (such as
postcodes) can remain in anonymized text. Select every sensitive source column;
column auto-detection samples rows and can miss sparse PII. Inputs and temporary
processing objects still exist in memory. Direct use of low-level components
such as `ally.analyzer` or `ally.anonymizer` bypasses facade output filtering.
Use the public configuration APIs rather than mutating component attributes.
The existing hash operator is unchanged; this profile adds no keyed pseudonyms.

`require_spacy_model=True` requires the **requested** model to load with a `ner`
pipeline. Initialization raises `RuntimeError` when it is missing or lacks NER,
even if the usual fallback model is installed or a permissive fallback was
previously cached. `spacy_model=None` remains an explicit pattern-only choice;
combining it with the strict requirement raises `ValueError`.

Both options round-trip through `export_config()` in JSON/YAML:

```json
{
  "schema_version": 1,
  "processing": {"minimal_output": true},
  "analyzer": {
    "spacy_model": "en_core_web_sm",
    "require_spacy_model": true,
    "enable_caching": false
  }
}
```

Omitted factory options inherit saved settings. Explicit boolean arguments
allow overriding them. Minimal output always takes precedence over enabling
caching. For pattern-only use, set `spacy_model=None` and leave
`require_spacy_model=False`.
