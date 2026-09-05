"""Validation shared by configuration import and export."""
import math
import re


def validate_settings(settings):
    """Raise ValueError for malformed persisted settings before applying them."""
    if not isinstance(settings, dict):
        raise ValueError("settings must be an object")
    if "schema_version" in settings and (
        type(settings["schema_version"]) is not int or settings["schema_version"] != 1
    ):
        raise ValueError("Unsupported schema_version; expected 1")
    for section in ("analyzer", "entity_types", "anonymization", "processing", "acronyms"):
        if section in settings and not isinstance(settings[section], dict):
            raise ValueError(f"{section} must be an object")

    def number(value, path, low, high):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{path} must be a finite number")
        if not low <= value <= high:
            raise ValueError(f"{path} must be between {low} and {high}")

    analyzer = settings.get("analyzer", {})
    unknown = set(analyzer) - {"min_score_threshold", "spacy_model", "enable_caching", "max_cache_size"}
    if unknown:
        raise ValueError(f"Unknown analyzer setting(s): {sorted(unknown)}")
    if "min_score_threshold" in analyzer:
        number(analyzer["min_score_threshold"], "analyzer.min_score_threshold", 0, 1)
    if "spacy_model" in analyzer and analyzer["spacy_model"] is not None:
        if not isinstance(analyzer["spacy_model"], str) or not analyzer["spacy_model"]:
            raise ValueError("analyzer.spacy_model must be a model name or null")
    if "enable_caching" in analyzer and not isinstance(analyzer["enable_caching"], bool):
        raise ValueError("analyzer.enable_caching must be a boolean")
    for section, key in (("analyzer", "max_cache_size"), ("processing", "batch_size"),
                         ("processing", "worker_count")):
        values = settings.get(section, {})
        if key not in values or (key == "worker_count" and values[key] is None):
            continue
        value = values[key]
        if type(value) is not int or value <= 0:
            raise ValueError(f"{section}.{key} must be a positive integer")

    active = settings.get("entity_types", {}).get("active", [])
    if not isinstance(active, list) or any(not isinstance(x, str) or not x for x in active):
        raise ValueError("entity_types.active must be a list of nonempty entity names")
    adjustments = settings.get("entity_types", {}).get("score_adjustment", {})
    if not isinstance(adjustments, dict):
        raise ValueError("entity_types.score_adjustment must be an object")
    for name, value in adjustments.items():
        number(value, f"entity_types.score_adjustment.{name}", -1, 1)
    operators = settings.get("anonymization", {}).get("operators", {})
    if not isinstance(operators, dict):
        raise ValueError("anonymization.operators must be an object")
    for name, operator in operators.items():
        if not isinstance(name, str) or not name or operator not in (
            "replace", "mask", "redact", "hash", "age_bracket"
        ):
            raise ValueError(f"Unsupported anonymization operator for {name}")
    priority = settings.get("anonymization", {}).get("entity_priority", {})
    if not isinstance(priority, dict) or any(
        not isinstance(k, str) or not k or type(v) is not int for k, v in priority.items()
    ):
        raise ValueError("anonymization.entity_priority must map entity names to integers")
    for key in ("use_pyarrow", "expand_acronyms"):
        processing = settings.get("processing", {})
        if key in processing and not isinstance(processing[key], bool):
            raise ValueError(f"processing.{key} must be a boolean")
    acronyms = settings.get("acronyms", {})
    dictionary = acronyms.get("dictionary", {})
    if not isinstance(dictionary, dict) or any(
        not isinstance(k, str) or not k or not isinstance(v, str) for k, v in dictionary.items()
    ):
        raise ValueError("acronyms.dictionary must map nonempty strings to strings")
    if "case_sensitive" in acronyms and not isinstance(acronyms["case_sensitive"], bool):
        raise ValueError("acronyms.case_sensitive must be a boolean")
    if settings.get("patterns_mode", "append") not in ("append", "replace"):
        raise ValueError("patterns_mode must be append or replace")
    patterns = settings.get("patterns", [])
    if not isinstance(patterns, list):
        raise ValueError("patterns must be a list")
    for index, pattern in enumerate(patterns):
        path = f"patterns[{index}]"
        if not isinstance(pattern, dict) or not isinstance(pattern.get("entity_type"), str) or not pattern["entity_type"]:
            raise ValueError(f"{path}.entity_type must be a nonempty string")
        context = pattern.get("context")
        if context is not None and (not isinstance(context, list) or any(not isinstance(x, str) for x in context)):
            raise ValueError(f"{path}.context must be a list of strings or null")
        if not isinstance(pattern.get("language", "en"), str):
            raise ValueError(f"{path}.language must be a string")
        regexes = pattern.get("patterns")
        if not isinstance(regexes, list):
            raise ValueError(f"{path}.patterns must be a list")
        for regex in regexes:
            if not isinstance(regex, str):
                raise ValueError(f"{path}: only string regex patterns can be exported and loaded")
            try:
                re.compile(regex)
            except re.error as error:
                raise ValueError(f"{path}: invalid regex: {error}") from error
        number(pattern.get("score", 0.85), f"{path}.score", 0, 1)
