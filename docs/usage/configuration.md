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
