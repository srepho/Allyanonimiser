"""
Main interface for the Allyanonimiser package.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .core.analyzer import EnhancedAnalyzer, RecognizerResult
from .core.anonymizer import EnhancedAnonymizer
from .core.pattern_manager import CustomPatternDefinition
from .core.pattern_registry import PatternRegistry
from .io.csv_processor import CSVProcessor
from .reporting import report_manager
from .utils.long_text_processor import extract_pii_rich_segments
from .utils.settings_manager import SettingsManager, create_default_settings
from .utils.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)


@dataclass
class AnonymizationConfig:
    """Configuration for anonymization.

    Attributes:
        operators: Maps entity types to operators
            ("replace", "mask", "redact", "hash", "age_bracket").
        language: Language code (default "en").
        active_entity_types: Restrict detection to these types (None = all).
        expand_acronyms: Expand acronyms before processing.
        age_bracket_size: Bracket width for the "age_bracket" operator.
        keep_postcode: Preserve postcodes within addresses.
    """

    operators: dict[str, str] | None = None
    language: str = "en"
    active_entity_types: list[str] | None = None
    expand_acronyms: bool = False
    age_bracket_size: int = 5
    keep_postcode: bool = True


@dataclass
class AnalysisConfig:
    """Configuration for analysis / entity detection.

    Attributes:
        language: Language code (default "en").
        active_entity_types: Restrict detection to these types (None = all).
        score_adjustment: Per-entity-type score deltas (e.g. {"PERSON": 0.1}).
        min_score_threshold: Drop detections below this confidence.
        expand_acronyms: Expand acronyms before analysis.
    """

    language: str = "en"
    active_entity_types: list[str] | None = None
    score_adjustment: dict[str, float] | None = None
    min_score_threshold: float | None = None
    expand_acronyms: bool = False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_allyanonimiser(
    pattern_filepath: str | None = None,
    settings_path: str | None = None,
    enable_caching: bool = True,
    max_cache_size: int = 10_000,
    spacy_model: str | None = "en_core_web_sm",
) -> "Allyanonimiser":
    """Create a pre-configured Allyanonimiser instance.

    Args:
        pattern_filepath: Path to a JSON file with extra pattern definitions.
        settings_path: Path to a settings file (JSON / YAML).
        enable_caching: Enable result caching in the analyzer.
        max_cache_size: Maximum cached entries.
        spacy_model: spaCy model name. Defaults to ``"en_core_web_sm"`` (~44 MB,
            fast). Use ``"en_core_web_lg"`` (~587 MB) for higher NER recall on
            ``PERSON``, ``LOCATION``, and ``ORG`` entities — pattern-based
            detection (TFN/ABN/MEDICARE/AU_PHONE/EMAIL/dates/etc.) is identical
            either way. Pass ``None`` to disable spaCy entirely (pattern-only).
    """
    if settings_path:
        settings_manager = SettingsManager(settings_path=settings_path)
    else:
        settings_manager = SettingsManager(settings=create_default_settings())

    analyzer = EnhancedAnalyzer(
        enable_caching=enable_caching,
        spacy_model=spacy_model,
    )

    ally = Allyanonimiser(
        analyzer=analyzer,
        settings_manager=settings_manager,
        enable_caching=enable_caching,
    )

    if max_cache_size and hasattr(ally.analyzer, "max_cache_size"):
        ally.analyzer.max_cache_size = max_cache_size

    if pattern_filepath:
        ally.load_patterns(pattern_filepath)

    return ally


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class Allyanonimiser:
    """Facade for PII detection, anonymization, and processing.

    Composes an analyzer, anonymizer, pattern registry, text preprocessor,
    and settings manager.  Thin convenience methods delegate to these
    components; callers can also access them directly via attributes.
    """

    def __init__(
        self,
        analyzer: EnhancedAnalyzer | None = None,
        anonymizer: EnhancedAnonymizer | None = None,
        pattern_registry: PatternRegistry | None = None,
        text_preprocessor: TextPreprocessor | None = None,
        settings_manager: SettingsManager | None = None,
        enable_caching: bool = True,
    ):
        self.settings_manager = settings_manager or SettingsManager()
        self.analyzer = analyzer or EnhancedAnalyzer(enable_caching=enable_caching)
        self.anonymizer = anonymizer or EnhancedAnonymizer(analyzer=self.analyzer)
        self.pattern_registry = pattern_registry or PatternRegistry()

        if text_preprocessor:
            self.text_preprocessor = text_preprocessor
        elif self.settings_manager.get_acronyms():
            self.text_preprocessor = TextPreprocessor(
                acronym_dict=self.settings_manager.get_acronyms(),
                case_sensitive=self.settings_manager.get_acronym_case_sensitive(),
            )
        else:
            self.text_preprocessor = TextPreprocessor()

        self._configure_from_settings()
        self._load_default_patterns()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _configure_from_settings(self) -> None:
        entity_types = self.settings_manager.get_entity_types()
        if entity_types:
            self.analyzer.set_active_entity_types(entity_types)

        self.batch_size = self.settings_manager.get_batch_size()
        self.worker_count = self.settings_manager.get_worker_count()
        self.use_pyarrow = self.settings_manager.get_value(
            "processing.use_pyarrow", True
        )

    def _load_default_patterns(self) -> None:
        from .patterns.au_patterns import get_au_pattern_definitions
        from .patterns.general_intl_patterns import get_general_intl_pattern_definitions
        from .patterns.general_patterns import get_general_pattern_definitions
        from .patterns.insurance_patterns import get_insurance_pattern_definitions

        for getter in (
            get_au_pattern_definitions,
            get_insurance_pattern_definitions,
            get_general_pattern_definitions,
            get_general_intl_pattern_definitions,
        ):
            for pdef in getter():
                self.analyzer.add_pattern(CustomPatternDefinition(**pdef))

    def _preprocess(self, text: str, expand_acronyms: bool):
        """Return (processed_text, expansions_metadata)."""
        if expand_acronyms and self.text_preprocessor.acronym_dict:
            return self.text_preprocessor.expand_acronyms(text)
        return text, []

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def save_settings(self, settings_path: str) -> bool:
        """Persist current settings (including acronyms) to *settings_path*."""
        self.settings_manager.set_acronyms(
            self.text_preprocessor.acronym_dict,
            self.text_preprocessor.case_sensitive,
        )
        return self.settings_manager.save_settings(settings_path)

    def load_settings(self, settings_path: str) -> bool:
        """Load settings from *settings_path* and reconfigure components."""
        success = self.settings_manager.load_settings(settings_path)
        if success:
            self.text_preprocessor = TextPreprocessor(
                acronym_dict=self.settings_manager.get_acronyms(),
                case_sensitive=self.settings_manager.get_acronym_case_sensitive(),
            )
            self._configure_from_settings()
        return success

    def export_config(self, config_path: str, include_metadata: bool = True) -> bool:
        """Export a shareable config file (.json / .yaml)."""
        self.settings_manager.set_acronyms(
            self.text_preprocessor.acronym_dict,
            self.text_preprocessor.case_sensitive,
        )
        return self.settings_manager.export_config(config_path, include_metadata)

    # ------------------------------------------------------------------
    # Acronym management  (explicit methods, replaces manage_acronyms)
    # ------------------------------------------------------------------

    def set_acronyms(
        self, acronym_dict: dict[str, str], case_sensitive: bool = False
    ) -> None:
        """Replace the entire acronym dictionary."""
        self.text_preprocessor = TextPreprocessor(
            acronym_dict=acronym_dict, case_sensitive=case_sensitive
        )
        self.settings_manager.set_acronyms(acronym_dict, case_sensitive)

    def add_acronyms(self, acronym_dict: dict[str, str]) -> None:
        """Merge *acronym_dict* into the existing dictionary."""
        self.text_preprocessor.add_acronyms(acronym_dict)
        self.settings_manager.add_acronyms(acronym_dict)

    def remove_acronyms(self, acronyms: list[str]) -> None:
        """Remove acronyms by key."""
        self.text_preprocessor.remove_acronyms(acronyms)
        self.settings_manager.remove_acronyms(acronyms)

    def get_acronyms(self) -> dict[str, str]:
        """Return a copy of the current acronym dictionary."""
        return self.text_preprocessor.acronym_dict.copy()

    def import_acronyms_from_csv(
        self,
        csv_path: str,
        settings_path: str | None = None,
        acronym_col: str = "acronym",
        expansion_col: str = "expansion",
        case_sensitive: bool = False,
    ) -> int:
        """Import acronyms from a CSV file. Returns count imported."""
        from .utils.settings_manager import import_acronyms_from_csv

        success, count, settings = import_acronyms_from_csv(
            csv_path, settings_path, acronym_col, expansion_col, case_sensitive
        )
        if success and count > 0:
            self.text_preprocessor = TextPreprocessor(
                acronym_dict=settings.get("acronyms", {}).get("dictionary", {}),
                case_sensitive=settings.get("acronyms", {}).get(
                    "case_sensitive", False
                ),
            )
        return count

    # Keep old name as alias for backward compatibility with tests
    def set_acronym_dictionary(
        self, acronym_dict: dict[str, str], case_sensitive: bool = False
    ) -> None:
        """Alias for :meth:`set_acronyms`."""
        self.set_acronyms(acronym_dict, case_sensitive)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        text: str,
        language: str = "en",
        active_entity_types: list[str] | None = None,
        score_adjustment: dict[str, float] | None = None,
        min_score_threshold: float | None = None,
        expand_acronyms: bool = False,
        config: AnalysisConfig | None = None,
    ) -> list[RecognizerResult]:
        """Detect PII entities in *text*.

        Returns a list of ``RecognizerResult`` objects.
        """
        if config is not None:
            language = config.language
            active_entity_types = config.active_entity_types
            score_adjustment = config.score_adjustment
            min_score_threshold = config.min_score_threshold
            expand_acronyms = config.expand_acronyms

        if active_entity_types is not None:
            self.analyzer.set_active_entity_types(active_entity_types)
        if min_score_threshold is not None:
            self.analyzer.set_min_score_threshold(min_score_threshold)

        processed_text, _ = self._preprocess(text, expand_acronyms)
        return self.analyzer.analyze(processed_text, language, score_adjustment)

    def get_available_entity_types(self) -> dict[str, Any]:
        """Return metadata about all registered entity types."""
        return self.analyzer.get_available_entity_types()

    def explain_entity(self, text: str, entity: dict[str, Any]) -> dict[str, Any]:
        """Explain why *entity* was detected in *text*."""
        result = RecognizerResult(
            entity_type=entity["entity_type"],
            start=entity["start"],
            end=entity["end"],
            score=entity["score"],
            text=entity["text"],
        )
        return self.analyzer.explain_detection(text, result)

    # ------------------------------------------------------------------
    # Anonymization
    # ------------------------------------------------------------------

    def anonymize(
        self,
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
    ) -> dict[str, Any]:
        """Anonymize PII entities in *text*.

        Returns a dict with keys ``text``, ``items``, ``processing_time``,
        ``document_id``, and ``original_text``.
        """
        start_time = time.time()

        if config is not None:
            operators = config.operators
            language = config.language
            active_entity_types = config.active_entity_types
            expand_acronyms = config.expand_acronyms
            age_bracket_size = config.age_bracket_size
            keep_postcode = config.keep_postcode

        if active_entity_types is not None:
            self.analyzer.set_active_entity_types(active_entity_types)

        processed_text, _ = self._preprocess(text, expand_acronyms)

        result = self.anonymizer.anonymize(
            processed_text,
            operators,
            language,
            age_bracket_size=age_bracket_size,
            keep_postcode=keep_postcode,
        )

        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        result["document_id"] = document_id or f"doc_{int(time.time() * 1000)}"
        result["original_text"] = text

        if report:
            if not report_manager.get_current_report():
                report_manager.start_new_report()
            report_manager.get_current_report().record_anonymization(
                document_id=result["document_id"],
                original_text=text,
                anonymization_result=result,
                processing_time=processing_time,
            )

        return result

    # ------------------------------------------------------------------
    # Combined analysis + anonymization
    # ------------------------------------------------------------------

    def process(
        self,
        text: str,
        language: str = "en",
        active_entity_types: list[str] | None = None,
        score_adjustment: dict[str, float] | None = None,
        min_score_threshold: float | None = None,
        expand_acronyms: bool = False,
        operators: dict[str, str] | None = None,
        age_bracket_size: int = 5,
        keep_postcode: bool = True,
        analysis_config: AnalysisConfig | None = None,
        anonymization_config: AnonymizationConfig | None = None,
        document_id: str | None = None,
        report: bool = True,
    ) -> dict[str, Any]:
        """Analyze and anonymize *text* in one call.

        Returns a dict with ``analysis``, ``anonymized``, ``segments``,
        ``structured_data``, ``statistics``, and ``processing_time``.
        """
        start_time = time.time()

        if analysis_config is None:
            analysis_config = AnalysisConfig(
                language=language,
                active_entity_types=active_entity_types,
                score_adjustment=score_adjustment,
                min_score_threshold=min_score_threshold,
                expand_acronyms=expand_acronyms,
            )
        if anonymization_config is None:
            anonymization_config = AnonymizationConfig(
                operators=operators,
                language=language,
                active_entity_types=active_entity_types,
                expand_acronyms=expand_acronyms,
                age_bracket_size=age_bracket_size,
                keep_postcode=keep_postcode,
            )

        # Sync active_entity_types between configs
        if (
            anonymization_config.active_entity_types is None
            and analysis_config.active_entity_types is not None
        ):
            anonymization_config.active_entity_types = (
                analysis_config.active_entity_types
            )
        elif (
            analysis_config.active_entity_types is None
            and anonymization_config.active_entity_types is not None
        ):
            analysis_config.active_entity_types = (
                anonymization_config.active_entity_types
            )

        processed_text, expansions_metadata = self._preprocess(
            text, analysis_config.expand_acronyms
        )

        analysis_results = self.analyze(processed_text, config=analysis_config)
        anonymized_results = self.anonymize(
            processed_text,
            config=anonymization_config,
            document_id=document_id,
            report=report,
        )

        # PII-rich segments
        segments = extract_pii_rich_segments(processed_text)
        for segment in segments:
            anon = self.anonymize(segment["text"], config=anonymization_config, report=False)
            segment["anonymized"] = anon["text"]

        structured_data = self._extract_structured_data(analysis_results)
        processing_time = time.time() - start_time

        result: dict[str, Any] = {
            "analysis": {
                "entities": [
                    {
                        "entity_type": r.entity_type,
                        "start": r.start,
                        "end": r.end,
                        "text": (
                            processed_text[r.start : r.end]
                            if r.text is None
                            else r.text
                        ),
                        "score": r.score,
                    }
                    for r in analysis_results
                ]
            },
            "anonymized": anonymized_results["text"],
            "segments": segments,
            "structured_data": structured_data,
            "processing_time": processing_time,
            "statistics": {
                "entity_count": len(analysis_results),
                "entity_types": list({r.entity_type for r in analysis_results}),
                "entity_type_counts": {
                    et: sum(1 for r in analysis_results if r.entity_type == et)
                    for et in {r.entity_type for r in analysis_results}
                },
            },
        }

        if document_id:
            result["document_id"] = document_id
        if analysis_config.expand_acronyms and expansions_metadata:
            result["preprocessing"] = {
                "expanded_acronyms": [
                    {"acronym": e["acronym"], "expansion": e["expansion"]}
                    for e in expansions_metadata
                ]
            }

        return result

    # ------------------------------------------------------------------
    # Pattern management  (explicit methods, replaces manage_patterns)
    # ------------------------------------------------------------------

    def add_pattern(self, pattern_definition) -> bool:
        """Register a custom pattern with the analyzer and registry."""
        if isinstance(pattern_definition, dict):
            pattern = CustomPatternDefinition(**pattern_definition)
        else:
            pattern = pattern_definition
        result = self.analyzer.add_pattern(pattern)
        if result:
            self.pattern_registry.register_pattern(pattern)
        return result

    def create_pattern_from_examples(
        self,
        entity_type: str,
        examples: list[str],
        context: list[str] | None = None,
        name: str | None = None,
        generalization_level: str = "medium",
    ) -> CustomPatternDefinition:
        """Generate a regex pattern from *examples* and register it."""
        from .utils.spacy_helpers import create_regex_from_examples

        regex = create_regex_from_examples(
            examples, generalization_level=generalization_level
        )
        pattern = CustomPatternDefinition(
            entity_type=entity_type,
            patterns=[regex],
            context=context,
            name=name,
            description=(
                f"Custom pattern for {entity_type} from {len(examples)} examples"
            ),
        )
        self.add_pattern(pattern)
        return pattern

    def load_patterns(self, filepath: str) -> int:
        """Load patterns from a JSON file. Returns count loaded."""
        count = self.pattern_registry.load_patterns(filepath)
        for pattern in self.pattern_registry.get_patterns():
            self.analyzer.add_pattern(pattern)
        return count

    def import_patterns_from_csv(
        self,
        csv_path: str,
        pattern_filepath: str | None = None,
        entity_type_col: str = "entity_type",
        pattern_col: str = "pattern",
        context_col: str = "context",
        name_col: str = "name",
        score_col: str = "score",
    ) -> int:
        """Import patterns from a CSV file. Returns count imported."""
        from .utils.settings_manager import import_patterns_from_csv as _import

        success, count, settings = _import(
            csv_path,
            pattern_filepath,
            entity_type_col,
            pattern_col,
            context_col,
            name_col,
            score_col,
        )
        if success and "patterns" in settings:
            for pdef in settings["patterns"]:
                self.add_pattern(pdef)
        return count

    def save_patterns(self, filepath: str) -> str:
        """Save all registered patterns to a JSON file."""
        return self.pattern_registry.save_patterns(filepath)

    # ------------------------------------------------------------------
    # spaCy status
    # ------------------------------------------------------------------

    def check_spacy_status(self) -> dict[str, Any]:
        """Check spaCy model loading status and return guidance."""
        status: dict[str, Any] = {
            "is_loaded": False,
            "model_name": None,
            "has_ner": False,
            "entity_types": [
                "PERSON", "ORGANIZATION", "LOCATION", "DATE", "TIME", "MONEY", "PERCENT",
            ],
            "recommendation": None,
        }

        if getattr(self.analyzer, "use_spacy", False):
            status["is_loaded"] = True
            model = getattr(self.analyzer, "spacy_model_loaded", "unknown")
            status["model_name"] = model
            if model == "blank_en":
                status["has_ner"] = False
                status["recommendation"] = (
                    "Blank spaCy model — NER disabled. Install one with:\n"
                    "  python -m spacy download en_core_web_sm   # ~44 MB, fast\n"
                    "  python -m spacy download en_core_web_lg   # ~587 MB, higher PERSON/LOCATION/ORG accuracy"
                )
            else:
                status["has_ner"] = True
                if model == "en_core_web_sm":
                    status["recommendation"] = (
                        "Loaded en_core_web_sm (default). For higher NER recall on "
                        "PERSON/LOCATION/ORG, install and pass en_core_web_lg."
                    )
                else:
                    status["recommendation"] = f"Full functionality available with {model}"
        else:
            status["recommendation"] = (
                "spaCy not loaded. Install with:\n"
                "  pip install spacy && python -m spacy download en_core_web_sm"
            )

        return status

    # ------------------------------------------------------------------
    # DataFrame processing  (explicit methods)
    # ------------------------------------------------------------------

    def _make_df_processor(self, n_workers=None, use_pyarrow=None):
        from .io.dataframe_processor import DataFrameProcessor

        if use_pyarrow is None:
            use_pyarrow = getattr(self, "use_pyarrow", True)
        return DataFrameProcessor(self, n_workers=n_workers, use_pyarrow=use_pyarrow)

    def process_dataframe(
        self,
        df: pd.DataFrame,
        text_columns=None,
        column: str | None = None,
        operation: str = "process",
        n_workers: int | None = None,
        use_pyarrow: bool | None = None,
        analysis_config: AnalysisConfig | None = None,
        anonymization_config: AnonymizationConfig | None = None,
        **kwargs,
    ):
        """Process a DataFrame: detect, anonymize, or full process.

        Args:
            operation: "process", "detect", or "anonymize".
        """
        processor = self._make_df_processor(n_workers, use_pyarrow)

        if analysis_config is not None:
            if "active_entity_types" not in kwargs and analysis_config.active_entity_types:
                kwargs["active_entity_types"] = analysis_config.active_entity_types
            if "min_score_threshold" not in kwargs and analysis_config.min_score_threshold:
                kwargs["min_score_threshold"] = analysis_config.min_score_threshold

        if anonymization_config is not None:
            if "operators" not in kwargs and anonymization_config.operators:
                kwargs["operators"] = anonymization_config.operators
            if "age_bracket_size" not in kwargs:
                kwargs["age_bracket_size"] = anonymization_config.age_bracket_size
            if "keep_postcode" not in kwargs:
                kwargs["keep_postcode"] = anonymization_config.keep_postcode

        match operation:
            case "process":
                if text_columns is None:
                    raise ValueError("text_columns required for 'process'")
                return processor.process_dataframe(df, text_columns, **kwargs)
            case "detect":
                if column is None:
                    raise ValueError("column required for 'detect'")
                return processor.detect_pii(df, column, **kwargs)
            case "anonymize":
                if column is None:
                    raise ValueError("column required for 'anonymize'")
                return processor.anonymize_column(df, column, **kwargs)
            case _:
                raise ValueError(f"Unknown operation: {operation}")

    def detect_pii_in_dataframe(self, df: pd.DataFrame, column: str, **kwargs):
        """Detect PII in a single DataFrame column."""
        return self.process_dataframe(df, column=column, operation="detect", **kwargs)

    def anonymize_dataframe(self, df: pd.DataFrame, column: str, **kwargs):
        """Anonymize PII in a single DataFrame column."""
        return self.process_dataframe(df, column=column, operation="anonymize", **kwargs)

    # ------------------------------------------------------------------
    # Batch / file processing
    # ------------------------------------------------------------------

    def batch_process(
        self,
        texts: list[str],
        content_types: list[str] | None = None,
        analysis_config: AnalysisConfig | None = None,
        anonymization_config: AnonymizationConfig | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Process multiple texts. Returns a list of result dicts."""
        if analysis_config is None:
            analysis_config = AnalysisConfig(**{
                k: v for k, v in kwargs.items()
                if k in ("language", "active_entity_types", "expand_acronyms")
            })
        if anonymization_config is None:
            anonymization_config = AnonymizationConfig(**{
                k: v for k, v in kwargs.items()
                if k in ("operators", "language", "active_entity_types",
                         "expand_acronyms", "age_bracket_size", "keep_postcode")
            })

        results = []
        for i, text in enumerate(texts):
            result = self.process(
                text, analysis_config=analysis_config,
                anonymization_config=anonymization_config,
            )
            if content_types and i < len(content_types):
                result["content_type"] = content_types[i]
            results.append(result)
        return results

    def process_files(
        self,
        file_paths: list[str],
        output_dir: str | None = None,
        save_results: bool = False,
        analysis_config: AnalysisConfig | None = None,
        anonymization_config: AnonymizationConfig | None = None,
        report: bool = True,
        report_output: str | None = None,
        report_format: str = "html",
        **kwargs,
    ) -> dict[str, Any]:
        """Process multiple text files.

        Returns a dict with ``results``, ``success``, ``total_files``,
        ``successful_files``, and optionally ``report``.
        """
        import json
        import os



        if report:
            batch_report = report_manager.start_new_report()
            batch_id = batch_report.session_id
        else:
            batch_id = f"batch_{int(time.time() * 1000)}"

        if analysis_config is None:
            analysis_config = AnalysisConfig(**{
                k: v for k, v in kwargs.items()
                if k in ("language", "active_entity_types", "expand_acronyms")
            })
        if anonymization_config is None:
            anonymization_config = AnonymizationConfig(**{
                k: v for k, v in kwargs.items()
                if k in ("operators", "language", "active_entity_types",
                         "expand_acronyms", "age_bracket_size", "keep_postcode")
            })

        if save_results and output_dir:
            os.makedirs(output_dir, exist_ok=True)

        results = []
        for i, fpath in enumerate(file_paths):
            try:
                with open(fpath, encoding="utf-8") as f:
                    text = f.read()

                name = os.path.splitext(os.path.basename(fpath))[0]
                doc_id = f"{batch_id}_{i}_{name}"

                result = self.process(
                    text,
                    analysis_config=analysis_config,
                    anonymization_config=anonymization_config,
                    document_id=doc_id,
                    report=report,
                )
                result["file_info"] = {"path": fpath, "name": name}

                if save_results and output_dir:
                    anon_path = os.path.join(output_dir, f"{name}_anonymized.txt")
                    with open(anon_path, "w", encoding="utf-8") as f:
                        f.write(result["anonymized"])
                    analysis_path = os.path.join(output_dir, f"{name}_analysis.json")
                    with open(analysis_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                    result["output_files"] = {
                        "anonymized": anon_path,
                        "analysis": analysis_path,
                    }

                results.append(result)
            except Exception as exc:
                results.append({
                    "file_info": {"path": fpath, "name": os.path.basename(fpath)},
                    "error": str(exc),
                    "success": False,
                })

        response: dict[str, Any] = {
            "results": results,
            "success": True,
            "total_files": len(file_paths),
            "successful_files": sum(1 for r in results if r.get("success", True)),
        }

        if report:
            batch_report.finalize()
            response["report"] = batch_report.get_summary()
            if report_output:
                try:
                    os.makedirs(os.path.dirname(report_output), exist_ok=True)
                    response["report_file"] = batch_report.export_report(
                        report_output, report_format
                    )
                except Exception as exc:
                    response["report_error"] = str(exc)

        return response

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_report(self, session_id: str | None = None):
        """Retrieve an anonymization report."""
        if session_id:
            return report_manager.get_report(session_id)
        return report_manager.get_current_report()

    def start_new_report(self, session_id: str | None = None):
        """Start a fresh anonymization report."""
        return report_manager.start_new_report(session_id)

    def finalize_report(
        self, output_path: str | None = None, format: str = "html"
    ) -> dict[str, Any]:
        """Finalize the current report and optionally export it."""
        rpt = report_manager.get_current_report()
        if not rpt:
            return {"error": "No active report"}
        rpt.finalize()
        if output_path:
            try:
                rpt.export_report(output_path, format)
            except Exception as exc:
                return {"error": str(exc), "summary": rpt.get_summary()}
        return rpt.get_summary()

    def display_report_in_notebook(self, session_id: str | None = None) -> None:
        """Display a report with rich visualizations in Jupyter."""
        rpt = self.get_report(session_id)
        if not rpt:
            logger.warning("No report available to display.")
            return
        rpt.display_in_notebook()

    # ------------------------------------------------------------------
    # CSV processing  (delegates to CSVProcessor)
    # ------------------------------------------------------------------

    def process_csv_file(
        self,
        input_file: str,
        output_file: str | None = None,
        columns_to_anonymize: list[str] | None = None,
        operators: dict[str, str] | None = None,
        operation: str = "anonymize",
        encoding: str = "utf-8",
        delimiter: str = ",",
        generate_report: bool = True,
    ) -> dict[str, Any]:
        """Process a CSV file for PII detection / anonymization."""
        return CSVProcessor(self).process_csv_file(
            input_file=input_file,
            output_file=output_file,
            columns_to_anonymize=columns_to_anonymize,
            operators=operators,
            operation=operation,
            encoding=encoding,
            delimiter=delimiter,
            generate_report=generate_report,
        )

    def detect_pii_columns(
        self,
        data: str | pd.DataFrame,
        sample_size: int = 100,
        confidence_threshold: float = 0.7,
        min_detection_rate: float = 0.1,
    ) -> list[str]:
        """Auto-detect columns likely containing PII."""
        return CSVProcessor(self).detect_pii_columns(
            data=data,
            sample_size=sample_size,
            confidence_threshold=confidence_threshold,
            min_detection_rate=min_detection_rate,
        )

    def preview_csv_changes(
        self,
        input_file: str,
        columns: list[str] | None = None,
        operators: dict[str, str] | None = None,
        sample_rows: int = 10,
        encoding: str = "utf-8",
    ) -> pd.DataFrame:
        """Preview anonymization on a sample before processing the full file."""
        return CSVProcessor(self).preview_csv_changes(
            input_file=input_file,
            columns=columns,
            operators=operators,
            sample_rows=sample_rows,
            encoding=encoding,
        )

    def stream_process_csv(
        self,
        input_file: str,
        output_file: str,
        columns: list[str],
        operators: dict[str, str] | None = None,
        chunk_size: int = 10_000,
        encoding: str = "utf-8",
        delimiter: str = ",",
    ) -> dict[str, Any]:
        """Process a large CSV in streaming chunks."""
        return CSVProcessor(self).stream_process_csv(
            input_file=input_file,
            output_file=output_file,
            columns=columns,
            operators=operators,
            chunk_size=chunk_size,
            encoding=encoding,
            delimiter=delimiter,
        )

    def process_csv_directory(
        self,
        input_dir: str,
        output_dir: str | None = None,
        columns_to_anonymize: list[str] | None = None,
        operators: dict[str, str] | None = None,
        file_pattern: str = "*.csv",
        recursive: bool = False,
    ) -> dict[str, Any]:
        """Process all CSV files in a directory."""
        return CSVProcessor(self).process_csv_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            columns_to_anonymize=columns_to_anonymize,
            operators=operators,
            file_pattern=file_pattern,
            recursive=recursive,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_structured_data(
        analysis_results: list[RecognizerResult],
    ) -> dict[str, Any]:
        """Group detected entities into a simple structured dict."""
        groups: dict[str, list] = {}
        for r in analysis_results:
            groups.setdefault(r.entity_type, []).append(r.text)

        out: dict[str, Any] = {}
        for etype, texts in groups.items():
            key = etype.lower()
            out[key] = texts[0] if len(texts) == 1 else texts
        return out
