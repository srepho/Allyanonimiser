"""
DataFrame processing utilities for Allyanonimiser.
"""

import logging
from typing import Any

import pandas as pd
from tqdm import tqdm

from .base import BaseProcessor

logger = logging.getLogger(__name__)

# PyArrow support is optional but recommended for pandas 2+
PYARROW_AVAILABLE = False
try:
    import pyarrow as pa  # noqa: F401

    PYARROW_AVAILABLE = True
except ImportError:
    pass


def _use_arrow_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Convert object-dtype string columns to ``string[pyarrow]`` in-place.

    This halves memory for large text columns and avoids Python-object overhead.
    Falls back silently if pyarrow is not available.
    """
    if not PYARROW_AVAILABLE:
        return df
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = df[col].astype("string[pyarrow]")
            except (TypeError, pa.ArrowInvalid):
                pass  # mixed-type column, leave as object
    return df


class DataFrameProcessor(BaseProcessor):
    """Efficient pandas DataFrame processing for Allyanonimiser.

    Key design choices:
    - Uses ``Series.apply()`` instead of ``iterrows()`` for ~5x speedup.
    - Converts string columns to ``string[pyarrow]`` dtype when available
      to reduce memory usage.
    - Supports optional parallel processing via ``n_workers``.
    """

    def __init__(
        self,
        allyanonimiser=None,
        n_workers: int | None = None,
        batch_size: int | None = None,
        use_pyarrow: bool | None = None,
    ):
        super().__init__(allyanonimiser)

        if n_workers is None and hasattr(self.ally, "worker_count"):
            self.n_workers = self.ally.worker_count
        else:
            self.n_workers = n_workers

        if batch_size is None and hasattr(self.ally, "batch_size"):
            self.batch_size = self.ally.batch_size
        else:
            self.batch_size = batch_size or 1000

        if use_pyarrow is None:
            self.use_pyarrow = PYARROW_AVAILABLE
        else:
            self.use_pyarrow = use_pyarrow and PYARROW_AVAILABLE

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_pii(
        self,
        df: pd.DataFrame,
        column: str,
        active_entity_types: list[str] | None = None,
        min_score_threshold: float = 0.7,
        batch_size: int = 1000,
    ) -> pd.DataFrame:
        """Detect PII entities in *column*. Returns one row per entity."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

        if active_entity_types is not None:
            self.ally.analyzer.set_active_entity_types(active_entity_types)
        self.ally.analyzer.set_min_score_threshold(min_score_threshold)

        records: list = []
        series = df[column].fillna("")
        texts = [str(t) for t in series]
        indices = series.index.tolist()

        # Batch analysis: pre-warms spaCy cache via nlp.pipe()
        batch_results = self.ally.analyzer.analyze_batch(texts)

        for idx, text_str, entities in zip(indices, texts, batch_results):
            if not text_str:
                continue
            for e in entities:
                records.append({
                    "row_index": idx,
                    "entity_type": e.entity_type,
                    "start": e.start,
                    "end": e.end,
                    "text": e.text or text_str[e.start : e.end],
                    "score": e.score,
                })

        if not records:
            return pd.DataFrame(
                columns=["row_index", "entity_type", "start", "end", "text", "score"]
            )
        return pd.DataFrame(records)

    def anonymize_column(
        self,
        df: pd.DataFrame,
        column: str,
        operators: dict[str, str] | None = None,
        active_entity_types: list[str] | None = None,
        inplace: bool = False,
        output_column: str | None = None,
        batch_size: int = 1000,
        age_bracket_size: int = 5,
        keep_postcode: bool = True,
    ) -> pd.DataFrame:
        """Anonymize PII in *column*. Adds an ``_anonymized`` column."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

        output_column = output_column or f"{column}_anonymized"
        result_df = df if inplace else df.copy()

        if active_entity_types is not None:
            self.ally.analyzer.set_active_entity_types(active_entity_types)

        def _anonymize(text):
            if pd.isna(text):
                return text
            r = self.ally.anonymize(
                str(text),
                operators=operators,
                age_bracket_size=age_bracket_size,
                keep_postcode=keep_postcode,
            )
            return r["text"]

        result_df[output_column] = result_df[column].apply(_anonymize)
        return result_df

    def process_dataframe(
        self,
        df: pd.DataFrame,
        text_columns: str | list[str],
        active_entity_types: list[str] | None = None,
        operators: dict[str, str] | None = None,
        min_score_threshold: float = 0.7,
        batch_size: int = 1000,
        anonymize: bool = True,
        save_entities: bool = True,
        output_prefix: str = "",
        progress_bar: bool = True,
        use_pyarrow: bool | None = None,
        age_bracket_size: int = 5,
        keep_postcode: bool = True,
        adaptive_batch_size: bool = True,
        expand_acronyms: bool = False,
    ) -> dict[str, Any]:
        """Full processing: detect + anonymize across one or more columns.

        Returns a dict with ``dataframe`` (processed DataFrame) and
        ``entities`` (entity DataFrame).
        """
        if isinstance(text_columns, str):
            text_columns = [text_columns]

        missing = [c for c in text_columns if c not in df.columns]
        if missing:
            raise ValueError(
                f"Column(s) not found in DataFrame: {missing}. "
                f"Available columns: {list(df.columns)}"
            )

        # Optionally convert string columns to Arrow-backed strings
        should_use_pyarrow = use_pyarrow if use_pyarrow is not None else self.use_pyarrow
        if should_use_pyarrow:
            df = _use_arrow_strings(df)

        if active_entity_types is not None:
            self.ally.analyzer.set_active_entity_types(active_entity_types)
        self.ally.analyzer.set_min_score_threshold(min_score_threshold)

        result_df = df.copy()
        all_entities: list = []

        for column in text_columns:

            output_column = f"{output_prefix}{column}_anonymized"

            col_series = df[column].dropna()
            iterator = tqdm(
                col_series.items(), total=len(col_series), desc=f"Processing {column}"
            ) if progress_bar else col_series.items()

            for idx, text in iterator:
                text_str = str(text)
                entities = self.ally.analyze(text_str, expand_acronyms=expand_acronyms)

                if save_entities:
                    for e in entities:
                        all_entities.append(
                            {
                                "row_index": idx,
                                "column": column,
                                "entity_type": e.entity_type,
                                "start": e.start,
                                "end": e.end,
                                "text": e.text or text_str[e.start : e.end],
                                "score": e.score,
                            }
                        )

                if anonymize:
                    r = self.ally.anonymize(
                        text_str,
                        operators=operators,
                        age_bracket_size=age_bracket_size,
                        keep_postcode=keep_postcode,
                        expand_acronyms=expand_acronyms,
                    )
                    result_df.at[idx, output_column] = r["text"]

        entity_df = pd.DataFrame(all_entities) if all_entities else pd.DataFrame(
            columns=["row_index", "column", "entity_type", "start", "end", "text", "score"]
        )

        return {"dataframe": result_df, "entities": entity_df}

    def analyze_dataframe_statistics(
        self,
        entity_df: pd.DataFrame,
        text_df: pd.DataFrame | None = None,
        text_column: str | None = None,
    ) -> pd.DataFrame:
        """Generate summary statistics from an entity DataFrame."""
        if entity_df.empty:
            return pd.DataFrame(
                columns=["entity_type", "count", "avg_score", "min_score",
                         "max_score", "unique_rows", "percentage"]
            )

        total = len(entity_df)
        stats = (
            entity_df.groupby("entity_type")
            .agg(
                count=("entity_type", "size"),
                avg_score=("score", "mean"),
                min_score=("score", "min"),
                max_score=("score", "max"),
                unique_rows=("row_index", "nunique"),
            )
            .reset_index()
            .sort_values("count", ascending=False)
        )
        stats["percentage"] = (stats["count"] / total * 100).round(2)
        return stats
