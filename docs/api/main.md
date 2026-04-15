# Main API Reference

This page is the flat reference for the public API at the package root.
For task-oriented guides, start with
[Analyzing Text](../usage/analyzing-text.md) or
[Anonymizing Text](../usage/anonymizing-text.md) instead.

## Top-level exports

```python
from allyanonimiser import (
    # Main facade
    Allyanonimiser,
    # Configuration dataclasses
    AnalysisConfig,
    AnonymizationConfig,
    # Low-level components (rarely needed directly)
    EnhancedAnalyzer,
    EnhancedAnonymizer,
    CustomPatternDefinition,
    PatternManager,
    PatternRegistry,
    # I/O processors
    DataFrameProcessor,
    StreamProcessor,       # None if polars isn't installed
    POLARS_AVAILABLE,
    # Factories
    create_allyanonimiser,
    create_analyzer,
    create_pattern_from_examples,
    # spaCy model presets
    SPACY_MODEL_FAST,       # "en_core_web_sm"
    SPACY_MODEL_ACCURATE,   # "en_core_web_lg"
)
```

## `create_allyanonimiser(...)`

Preferred entry point. Returns a fully configured `Allyanonimiser`
instance with all built-in Australian, general, and insurance patterns
loaded.

```python
create_allyanonimiser(
    pattern_filepath: str | None = None,
    settings_path: str | None = None,
    enable_caching: bool = True,
    max_cache_size: int = 10_000,
    spacy_model: str | None = "en_core_web_sm",
) -> Allyanonimiser
```

**Arguments**

| Name | Type | Default | Description |
|---|---|---|---|
| `pattern_filepath` | `str \| None` | `None` | Optional JSON file with extra `CustomPatternDefinition`s. |
| `settings_path` | `str \| None` | `None` | Optional YAML/JSON settings file. |
| `enable_caching` | `bool` | `True` | Cache analyze() results by text hash. |
| `max_cache_size` | `int` | `10_000` | Max cached entries. |
| `spacy_model` | `str \| None` | `"en_core_web_sm"` | spaCy model name. Pass `SPACY_MODEL_ACCURATE` for `en_core_web_lg`. Pass `None` to disable spaCy (pattern-only mode). |

## `class Allyanonimiser`

The main facade. Composes an analyzer, anonymizer, pattern registry,
text preprocessor, and settings manager.

### Core detection and anonymization

```python
analyze(
    text: str,
    language: str = "en",
    active_entity_types: list[str] | None = None,
    score_adjustment: dict[str, float] | None = None,
    min_score_threshold: float | None = None,
    expand_acronyms: bool = False,
    config: AnalysisConfig | None = None,
) -> list[RecognizerResult]
```

Detects PII in `text`. Returns a list of `RecognizerResult` objects with
`entity_type`, `text`, `start`, `end`, and `score` fields.

```python
anonymize(
    text: str,
    operators: dict[str, str] | None = None,
    language: str = "en",
    active_entity_types: list[str] | None = None,
    expand_acronyms: bool = False,
    age_bracket_size: int = 5,
    keep_postcode: bool = True,
    config: AnonymizationConfig | None = None,
    document_id: str | None = None,
    report: bool = True,
) -> dict[str, Any]
```

Detects then rewrites `text`. Returns `{"text": anonymized_text,
"items": [...]}`. See [Anonymizing Text](../usage/anonymizing-text.md)
for the full operator catalogue.

```python
process(text, ...) -> dict[str, Any]
```

Combined analyze + anonymize in one call, returning both the detected
entities and the anonymized text.

```python
batch_process(
    texts: list[str],
    content_types: list[str] | None = None,
    analysis_config: AnalysisConfig | None = None,
    anonymization_config: AnonymizationConfig | None = None,
    **kwargs,
) -> list[dict[str, Any]]
```

### Pattern management

| Method | Purpose |
|---|---|
| `add_pattern(pattern_definition)` | Register a single `CustomPatternDefinition`. |
| `create_pattern_from_examples(entity_type, examples, context=None, name=None, generalization_level="medium")` | Build a pattern from example strings and register it. |
| `load_patterns(filepath)` | Load patterns from a JSON file. |
| `save_patterns(filepath)` | Dump registered patterns to JSON. |
| `import_patterns_from_csv(csv_path, ...)` | Bulk-import from a CSV. |
| `get_available_entity_types()` | Dict of `entity_type -> {count, patterns}`. |

### Acronym handling

| Method | Purpose |
|---|---|
| `set_acronyms(acronym_dict, case_sensitive=False)` | Replace the acronym dictionary. |
| `add_acronyms(acronym_dict)` | Merge into the existing dictionary. |
| `remove_acronyms(acronyms)` | Delete by key list. |
| `get_acronyms()` | Return the current dictionary. |
| `import_acronyms_from_csv(csv_path, ...)` | Bulk-import from a CSV. |

`set_acronym_dictionary(...)` is a legacy alias for `set_acronyms`.

### DataFrames and files

| Method | Purpose |
|---|---|
| `process_dataframe(df, text_columns=...)` | Full detect+anonymize across one or more columns. See [Working with DataFrames](../usage/dataframes.md). |
| `anonymize_dataframe(df, column, **kwargs)` | Anonymize a single column. |
| `detect_pii_in_dataframe(df, column, **kwargs)` | Entity DataFrame only. |
| `detect_pii_columns(data, ...)` | Infer which columns likely contain PII (for schema discovery). |
| `process_csv_file(input_file, output_file=None, ...)` | Full-file CSV pipeline. |
| `process_csv_directory(input_dir, output_dir=None, ...)` | Recursively process every CSV under a directory. |
| `preview_csv_changes(input_file, ...)` | Dry-run on the first N rows. |
| `stream_process_csv(input_file, output_file, columns, ...)` | Chunked row-by-row for files too big to load. Requires `polars` (install with `pip install "allyanonimiser[stream]"`). |
| `process_files(file_paths, ...)` | Batch plain text files. |

### Configuration and persistence

| Method | Purpose |
|---|---|
| `load_settings(settings_path)` | Load a YAML/JSON settings bundle. |
| `save_settings(settings_path)` | Dump current settings. |
| `export_config(config_path, include_metadata=True)` | Export patterns + acronyms + settings in one bundle. |

### Reporting

| Method | Purpose |
|---|---|
| `start_new_report(session_id=None)` | Begin tracking a batch run. |
| `get_report(session_id=None)` | Retrieve a report. |
| `finalize_report(output_path=None, format="html")` | Render and optionally save. |
| `display_report_in_notebook(session_id=None)` | Jupyter-native rendering. |

### Diagnostics

| Method | Purpose |
|---|---|
| `check_spacy_status()` | Dict with `is_loaded`, `model_name`, `has_ner`, `entity_types`, `recommendation`. Use this to diagnose model-install issues. |
| `explain_entity(text, entity)` | Return a dict explaining why a specific detection fired. |

## `class AnalysisConfig`

Reusable analysis settings.

```python
AnalysisConfig(
    language: str = "en",
    active_entity_types: list[str] | None = None,
    score_adjustment: dict[str, float] | None = None,
    min_score_threshold: float | None = None,
    expand_acronyms: bool = False,
)
```

Pass via `ally.analyze(text, config=cfg)`.

## `class AnonymizationConfig`

Reusable anonymization settings.

```python
AnonymizationConfig(
    operators: dict[str, str] | None = None,
    language: str = "en",
    active_entity_types: list[str] | None = None,
    expand_acronyms: bool = False,
    age_bracket_size: int = 5,
    keep_postcode: bool = True,
)
```

Pass via `ally.anonymize(text, config=cfg)`.

## `RecognizerResult`

Returned by `analyze`. Imported from
[`allyanonimiser.core.recognizer_result`](https://github.com/srepho/Allyanonimiser/blob/main/allyanonimiser/core/recognizer_result.py):

```python
@dataclass
class RecognizerResult:
    entity_type: str
    start: int
    end: int
    score: float
    text: str | None = None
```

## `class CustomPatternDefinition`

Spec for registering a new entity type. Build via
`create_pattern_from_examples(...)` or pass directly:

```python
from allyanonimiser import CustomPatternDefinition

pattern = CustomPatternDefinition(
    entity_type="EMPLOYEE_ID",
    patterns=[r"EMP\d{5}"],
    context=["employee", "staff", "id"],
    name="Employee ID",
    score=0.85,
)
ally.add_pattern(pattern)
```

## Further reading

- [Analyzing Text](../usage/analyzing-text.md) — detection walkthrough
- [Anonymizing Text](../usage/anonymizing-text.md) — operator catalogue
- [Working with DataFrames](../usage/dataframes.md) — pandas pipeline
- [Custom Patterns](../patterns/custom.md) — extending detection
- [Anonymization Operators](../advanced/anonymization-operators.md) — per-operator reference
- [Source on GitHub](https://github.com/srepho/Allyanonimiser)
