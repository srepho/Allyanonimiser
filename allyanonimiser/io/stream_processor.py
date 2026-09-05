"""
Stream processing utilities for Allyanonimiser.

This module provides streaming capabilities for processing very large files
using Polars for maximum efficiency and minimal memory usage.
"""

import logging
import os
from collections.abc import Generator
from contextlib import ExitStack, closing
from pathlib import Path
from typing import Any

import pandas as pd

from .base import BaseProcessor

logger = logging.getLogger(__name__)

# Polars support is optional
POLARS_AVAILABLE = False
try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    # Define dummy objects to avoid NameErrors when Polars is not available
    class DummyModule:
        DataFrame = object
        LazyFrame = object

        def scan_csv(*args, **kwargs):
            pass

        def read_csv(*args, **kwargs):
            pass

        class Config:
            @staticmethod
            def set_streaming_chunk_size(*args, **kwargs):
                pass

    pl = DummyModule()


class StreamProcessor(BaseProcessor):
    """Streaming processor for very large files using Polars."""

    def __init__(self, allyanonimiser=None, n_workers=None, chunk_size=None):
        if not POLARS_AVAILABLE:
            logger.warning(
                "Polars is required for stream processing but is not available. "
                "Install with: pip install polars"
            )
        super().__init__(allyanonimiser)

        # Use values from settings if not explicitly provided
        if n_workers is None and hasattr(self.ally, 'worker_count'):
            self.n_workers = self.ally.worker_count
        else:
            self.n_workers = n_workers or os.cpu_count()

        if chunk_size is None:
            chunk_size = getattr(self.ally, "chunk_size", 10000)
        self._validate_chunk_size(chunk_size)
        self.chunk_size = chunk_size

    @staticmethod
    def _validate_chunk_size(size):
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise ValueError("chunk_size must be a positive integer")

    @staticmethod
    def _validate_paths(*paths):
        paths = [Path(p).resolve() for p in paths if p is not None]
        for i, path in enumerate(paths):
            for other in paths[:i]:
                if path == other or (path.exists() and other.exists() and path.samefile(other)):
                    raise ValueError("Input, output and entity paths must be distinct")

    def _check_polars_available(self):
        """Check if Polars is available and raise an error if not."""
        if not POLARS_AVAILABLE:
            raise ImportError(
                "Polars is required for stream processing but is not available. "
                "Install with: pip install polars"
            )

    def stream_from_file(
        self,
        file_path: str,
        text_columns: str | list[str],
        active_entity_types: list[str] | None = None,
        operators: dict[str, str] | None = None,
        min_score_threshold: float = 0.7,
        anonymize: bool = True,
        chunk_size: int | None = None,
        output_path: str | None = None,
        progress_bar: bool = True,
        csv_options: dict[str, Any] | None = None,
        age_bracket_size: int = 5,
        keep_postcode: bool = True
    ) -> Generator[dict[str, Any], None, None]:
        """
        Stream process a large CSV file with minimal memory usage.

        Args:
            file_path: Path to the CSV file to process
            text_columns: Column name(s) containing text to process
            active_entity_types: Optional list of entity types to activate
            operators: Dict mapping entity_type to anonymization operator
            min_score_threshold: Minimum confidence score threshold
            anonymize: Whether to perform anonymization
            chunk_size: Number of rows to process in each chunk (overrides instance setting)
            output_path: Optional path to write processed chunks (enables true streaming)
            progress_bar: Whether to display a progress bar
            csv_options: Optional dict of CSV parsing options for Polars
            age_bracket_size: Size of age brackets when using "age_bracket" operator
            keep_postcode: Whether to keep postcodes when anonymizing addresses

        Yields:
            Dict with row_count and entity_count for every batch, entities
            when detected, and a Polars dataframe when output_path is omitted.

        Notes:
            Requires Polars >= 1.37. CSV columns default to strings to preserve
            identifiers; csv_options can explicitly enable type inference.
            Per-document reports are disabled for this bounded streaming path.
            Files may contain partial results if processing fails. Consumers
            stopping early should close the generator (e.g. contextlib.closing).
        """
        self._check_polars_available()

        import polars as pl
        from tqdm import tqdm

        chunk_size = self.chunk_size if chunk_size is None else chunk_size
        self._validate_chunk_size(chunk_size)
        self._validate_paths(file_path, output_path)
        if isinstance(text_columns, str):
            text_columns = [text_columns]
        if not text_columns:
            raise ValueError("text_columns must contain at least one column")

        # Read strings by default so identifiers retain leading zeroes and
        # later rows cannot invalidate a schema inferred from the first batch.
        options = {"infer_schema_length": 0, "low_memory": True, "glob": False}
        options.update(csv_options or {})
        lf = pl.scan_csv(file_path, **options)
        schema = lf.collect_schema()
        for column in text_columns:
            if column not in schema:
                raise ValueError(f"Column '{column}' not found in CSV file")

        with ExitStack() as stack:
            output = None
            if output_path is not None:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                output = stack.enter_context(open(output_path, "w", encoding="utf-8", newline=""))
            progress = stack.enter_context(tqdm(desc="Processing rows", unit="rows",
                                                disable=not progress_bar))
            batches = lf.collect_batches(chunk_size=chunk_size, maintain_order=True, lazy=True)
            row_offset = 0
            wrote_header = False
            for chunk in batches:
                result = self._process_chunk(
                    chunk, text_columns, active_entity_types, operators,
                    min_score_threshold, anonymize, age_bracket_size, keep_postcode,
                )
                entities = result["entities"]
                for entity in entities:
                    entity["row_index"] += row_offset
                frame = result["dataframe"]
                if output is not None:
                    frame.write_csv(output, include_header=not wrote_header)
                    output.flush()
                    wrote_header = True
                chunk_result = {"row_count": len(frame), "entity_count": len(entities)}
                if output is None:
                    chunk_result["dataframe"] = frame
                if entities:
                    chunk_result["entities"] = pd.DataFrame(entities)
                row_offset += len(frame)
                progress.update(len(frame))
                yield chunk_result

            # A header-only input still produces a usable output file.
            if output is not None and not wrote_header:
                empty = pl.DataFrame(schema=schema)
                if anonymize:
                    empty = empty.with_columns([
                        pl.Series(f"{column}_anonymized", [], dtype=pl.String)
                        for column in text_columns
                    ])
                empty.write_csv(output)

    def _process_chunk(
        self,
        chunk,
        text_columns: list[str],
        active_entity_types: list[str] | None = None,
        operators: dict[str, str] | None = None,
        min_score_threshold: float = 0.7,
        anonymize: bool = True,
        age_bracket_size: int = 5,
        keep_postcode: bool = True,
    ) -> dict[str, Any]:
        """Process a single chunk using Polars-native operations where possible."""
        import polars as pl

        # Ensure we have a Polars DataFrame
        if isinstance(chunk, pd.DataFrame):
            chunk = pl.from_pandas(chunk)

        all_entities: list = []
        result = chunk.clone()

        for column in text_columns:
            if column not in chunk.columns:
                continue

            texts = chunk[column].to_list()

            # Use batch analysis to pre-warm spaCy cache
            batch_results = self.ally.analyzer.analyze_batch(
                [str(t) if t is not None else "" for t in texts],
                active_entity_types=active_entity_types,
                min_score_threshold=min_score_threshold,
            )

            anonymized_texts: list = []
            for row_idx, (text, entities) in enumerate(zip(texts, batch_results)):
                if text is None:
                    anonymized_texts.append(None)
                    continue

                text_str = str(text)
                for e in entities:
                    all_entities.append({
                        "row_index": row_idx,
                        "column": column,
                        "entity_type": e.entity_type,
                        "start": e.start,
                        "end": e.end,
                        "text": e.text or text_str[e.start:e.end],
                        "score": e.score,
                    })

                if anonymize:
                    r = self.ally.anonymize(
                        text_str,
                        operators=operators,
                        active_entity_types=active_entity_types,
                        age_bracket_size=age_bracket_size,
                        keep_postcode=keep_postcode,
                        analysis_results=entities,
                        report=False,
                    )
                    anonymized_texts.append(r["text"])
                else:
                    anonymized_texts.append(text_str)

            if anonymize:
                result = result.with_columns(
                    pl.Series(f"{column}_anonymized", anonymized_texts, dtype=pl.String)
                )

        return {
            'dataframe': result,
            'entities': all_entities,
        }

    def process_large_file(
        self,
        file_path: str,
        text_columns: str | list[str],
        output_path: str,
        active_entity_types: list[str] | None = None,
        operators: dict[str, str] | None = None,
        min_score_threshold: float = 0.7,
        anonymize: bool = True,
        chunk_size: int | None = None,
        save_entities: bool = True,
        entities_output_path: str | None = None,
        csv_options: dict[str, Any] | None = None,
        age_bracket_size: int = 5,
        keep_postcode: bool = True,
        progress_bar: bool = True
    ) -> dict[str, Any]:
        """
        Process a very large file with minimal memory impact, writing results directly to disk.

        This is the preferred method for extremely large files where holding the
        entire dataset in memory is impractical.

        Args:
            file_path: Path to the CSV file to process
            text_columns: Column name(s) containing text to process
            output_path: Path to write the processed CSV file
            active_entity_types: Optional list of entity types to activate
            operators: Dict mapping entity_type to anonymization operator
            min_score_threshold: Minimum confidence score threshold
            anonymize: Whether to perform anonymization
            chunk_size: Number of rows to process in each chunk (overrides instance setting)
            save_entities: Whether to save detected entities
            entities_output_path: Path to write entities CSV (if save_entities=True)
            csv_options: Optional dict of CSV parsing options for Polars
            age_bracket_size: Size of age brackets when using "age_bracket" operator
            keep_postcode: Whether to keep postcodes when anonymizing addresses
            progress_bar: Whether to display a progress bar

        Returns:
            Dict with processing statistics
        """
        self._check_polars_available()

        # Set default entities output path if not provided
        if save_entities and entities_output_path is None:
            base_dir = os.path.dirname(output_path)
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            entities_output_path = os.path.join(base_dir, f"{base_name}_entities.csv")

        self._validate_paths(file_path, output_path,
                             entities_output_path if save_entities else None)
        total_rows = 0
        total_entities = 0
        entity_columns = ["row_index", "column", "entity_type", "start", "end", "text", "score"]

        with ExitStack() as stack:
            entity_output = None
            # Open entity output only after the first successful batch, so
            # invalid input does not truncate an existing entity file.
            chunks = stack.enter_context(closing(self.stream_from_file(
                file_path=file_path, text_columns=text_columns,
                active_entity_types=active_entity_types, operators=operators,
                min_score_threshold=min_score_threshold, anonymize=anonymize,
                chunk_size=chunk_size, output_path=output_path,
                progress_bar=progress_bar, csv_options=csv_options,
                age_bracket_size=age_bracket_size, keep_postcode=keep_postcode,
            )))
            for chunk_result in chunks:
                total_rows += chunk_result["row_count"]
                total_entities += chunk_result["entity_count"]
                if save_entities and entities_output_path is not None:
                    if entity_output is None:
                        Path(entities_output_path).parent.mkdir(parents=True, exist_ok=True)
                        entity_output = stack.enter_context(open(
                            entities_output_path, "w", encoding="utf-8", newline=""
                        ))
                        pd.DataFrame(columns=entity_columns).to_csv(entity_output, index=False)
                    if "entities" in chunk_result:
                        chunk_result["entities"].to_csv(entity_output, index=False, header=False)
                        entity_output.flush()
            if save_entities and entities_output_path is not None and entity_output is None:
                Path(entities_output_path).parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(columns=entity_columns).to_csv(entities_output_path, index=False)

        return {
            'total_rows_processed': total_rows,
            'total_entities_detected': total_entities,
            'output_file': output_path,
            'entities_file': entities_output_path if save_entities else None
        }
