"""
CSV file processing utilities for Allyanonimiser.
Provides direct CSV file handling, auto-detection, and streaming capabilities.
"""

import csv
import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Generator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVProcessor:
    """
    Handles CSV file processing with PII detection and anonymization.
    """
    
    def __init__(self, allyanonimiser=None):
        """
        Initialize CSV processor.
        
        Args:
            allyanonimiser: An existing Allyanonimiser instance or None to create a new one
        """
        from .allyanonimiser import create_allyanonimiser
        self.ally = allyanonimiser or create_allyanonimiser()
        self.processing_stats = {}
        
    def process_csv_file(
        self,
        input_file: str,
        output_file: str = None,
        columns_to_anonymize: List[str] = None,
        operators: Dict[str, str] = None,
        operation: str = "anonymize",
        encoding: str = "utf-8",
        delimiter: str = ",",
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        Process a CSV file directly without loading entire file into memory.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (if None, creates _anonymized version)
            columns_to_anonymize: List of column names to process (if None, auto-detects)
            operators: Dictionary mapping entity types to operators
            operation: "anonymize" or "analyze"
            encoding: File encoding
            delimiter: CSV delimiter
            generate_report: Whether to generate processing report
            
        Returns:
            Dictionary with processing results and statistics
        """
        # Validate input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
            
        # Set default output file
        if output_file is None:
            base_name = Path(input_file).stem
            extension = Path(input_file).suffix
            output_file = f"{base_name}_anonymized{extension}"
            
        # Set default operators if not provided
        if operators is None:
            operators = {
                "PERSON": "replace",
                "EMAIL_ADDRESS": "mask",
                "PHONE_NUMBER": "mask",
                "AU_MEDICARE": "mask",
                "AU_TFN": "redact",
                "CREDIT_CARD": "redact",
                "AU_ACN": "mask",
                "AU_ABN": "mask"
            }
            
        # Initialize statistics
        stats = {
            "input_file": input_file,
            "output_file": output_file,
            "start_time": datetime.now().isoformat(),
            "rows_processed": 0,
            "columns_processed": [],
            "entities_found": {},
            "errors": []
        }
        
        try:
            # Read CSV file
            df = pd.read_csv(input_file, encoding=encoding, delimiter=delimiter)
            stats["total_rows"] = len(df)
            stats["total_columns"] = len(df.columns)
            
            # Auto-detect columns if not specified
            if columns_to_anonymize is None:
                logger.info("Auto-detecting columns with PII...")
                columns_to_anonymize = self.detect_pii_columns(
                    df, 
                    sample_size=min(100, len(df))
                )
                stats["auto_detected_columns"] = columns_to_anonymize
                
            # Validate columns exist
            missing_columns = [col for col in columns_to_anonymize if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Columns not found in CSV: {missing_columns}")
                
            # Process each column
            for column in columns_to_anonymize:
                logger.info(f"Processing column: {column}")
                
                if operation == "anonymize":
                    # Create output column name
                    output_column = f"{column}_anonymized"
                    
                    # Process column
                    df = self.ally.process_dataframe(
                        df,
                        column=column,
                        operation="anonymize",
                        output_column=output_column,
                        operators=operators
                    )
                    
                    # Track entities found
                    for idx, row in df.iterrows():
                        if pd.notna(row.get(output_column)):
                            # Analyze original text to count entities
                            original_text = row[column]
                            if pd.notna(original_text):
                                entities = self.ally.analyze(str(original_text))
                                for entity in entities:
                                    entity_type = entity.entity_type
                                    stats["entities_found"][entity_type] = \
                                        stats["entities_found"].get(entity_type, 0) + 1
                    
                    # Replace original column with anonymized version
                    df[column] = df[output_column]
                    df = df.drop(columns=[output_column])
                    
                elif operation == "analyze":
                    # Just analyze without modifying
                    for idx, row in df.iterrows():
                        text = row[column]
                        if pd.notna(text):
                            entities = self.ally.analyze(str(text))
                            for entity in entities:
                                entity_type = entity.entity_type
                                stats["entities_found"][entity_type] = \
                                    stats["entities_found"].get(entity_type, 0) + 1
                
                stats["columns_processed"].append(column)
                
            stats["rows_processed"] = len(df)
            
            # Save output file
            if operation == "anonymize":
                df.to_csv(output_file, index=False, encoding=encoding)
                logger.info(f"Saved anonymized CSV to: {output_file}")
                
            # Calculate processing time
            stats["end_time"] = datetime.now().isoformat()
            start_time = datetime.fromisoformat(stats["start_time"])
            end_time = datetime.fromisoformat(stats["end_time"])
            stats["processing_time_seconds"] = (end_time - start_time).total_seconds()
            
            # Generate report if requested
            if generate_report:
                report_file = self._generate_report(stats, output_file)
                stats["report_file"] = report_file
                
        except Exception as e:
            stats["errors"].append(str(e))
            logger.error(f"Error processing CSV: {e}")
            raise
            
        return stats
        
    def detect_pii_columns(
        self,
        data: Union[str, pd.DataFrame],
        sample_size: int = 100,
        confidence_threshold: float = 0.7,
        min_detection_rate: float = 0.1
    ) -> List[str]:
        """
        Auto-detect columns that likely contain PII.
        
        Args:
            data: CSV file path or DataFrame
            sample_size: Number of rows to sample for detection
            confidence_threshold: Minimum confidence score for entity detection
            min_detection_rate: Minimum percentage of rows with PII to consider column
            
        Returns:
            List of column names likely containing PII
        """
        # Load data if file path provided
        if isinstance(data, str):
            df = pd.read_csv(data, nrows=sample_size)
        else:
            df = data.head(sample_size)
            
        pii_columns = []
        column_stats = {}
        
        # Check each column
        for column in df.columns:
            # Skip numeric columns
            if df[column].dtype in ['int64', 'float64']:
                continue
                
            detected_count = 0
            total_entities = 0
            entity_types = set()
            
            # Sample rows from column
            sample_data = df[column].dropna().head(sample_size)
            
            for text in sample_data:
                if pd.notna(text):
                    # Analyze text for PII
                    entities = self.ally.analyze(str(text))
                    
                    # Filter by confidence threshold
                    high_confidence_entities = [
                        e for e in entities 
                        if e.score >= confidence_threshold
                    ]
                    
                    if high_confidence_entities:
                        detected_count += 1
                        total_entities += len(high_confidence_entities)
                        entity_types.update([e.entity_type for e in high_confidence_entities])
                        
            # Calculate detection rate
            detection_rate = detected_count / len(sample_data) if len(sample_data) > 0 else 0
            
            # Store statistics
            column_stats[column] = {
                "detection_rate": detection_rate,
                "total_entities": total_entities,
                "entity_types": list(entity_types),
                "sample_size": len(sample_data)
            }
            
            # Add to PII columns if detection rate is above threshold
            if detection_rate >= min_detection_rate:
                pii_columns.append(column)
                logger.info(
                    f"Column '{column}' detected as containing PII "
                    f"(detection rate: {detection_rate:.1%}, entities: {entity_types})"
                )
                
        return pii_columns
        
    def preview_csv_changes(
        self,
        input_file: str,
        columns: List[str] = None,
        operators: Dict[str, str] = None,
        sample_rows: int = 10,
        encoding: str = "utf-8"
    ) -> pd.DataFrame:
        """
        Preview anonymization changes before processing entire file.
        
        Args:
            input_file: Path to CSV file
            columns: Columns to preview (if None, auto-detects)
            operators: Operators to use for anonymization
            sample_rows: Number of rows to preview
            encoding: File encoding
            
        Returns:
            DataFrame showing before/after comparison
        """
        # Read sample of file
        df_sample = pd.read_csv(input_file, nrows=sample_rows, encoding=encoding)
        
        # Auto-detect columns if not specified
        if columns is None:
            columns = self.detect_pii_columns(df_sample)
            
        if not columns:
            logger.warning("No PII columns detected in sample")
            return pd.DataFrame()
            
        # Set default operators if not provided
        if operators is None:
            operators = {
                "PERSON": "replace",
                "EMAIL_ADDRESS": "mask",
                "PHONE_NUMBER": "mask"
            }
            
        # Create preview dataframe
        preview_data = []
        
        for col in columns:
            if col not in df_sample.columns:
                continue
                
            for idx, original_text in enumerate(df_sample[col]):
                if pd.notna(original_text):
                    # Anonymize text
                    result = self.ally.anonymize(str(original_text), operators=operators)
                    anonymized_text = result.get("text", original_text)
                    
                    # Add to preview if changed
                    if anonymized_text != original_text:
                        preview_data.append({
                            "row": idx,
                            "column": col,
                            "original": original_text[:100] + "..." if len(str(original_text)) > 100 else original_text,
                            "anonymized": anonymized_text[:100] + "..." if len(str(anonymized_text)) > 100 else anonymized_text,
                            "entities_found": len(result.get("items", []))
                        })
                        
        preview_df = pd.DataFrame(preview_data)
        return preview_df
        
    def stream_process_csv(
        self,
        input_file: str,
        output_file: str,
        columns: List[str],
        operators: Dict[str, str] = None,
        chunk_size: int = 10000,
        encoding: str = "utf-8",
        delimiter: str = ","
    ) -> Dict[str, Any]:
        """
        Process large CSV files in chunks to handle files that don't fit in memory.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            columns: Columns to process
            operators: Operators for anonymization
            chunk_size: Number of rows to process at once
            encoding: File encoding
            delimiter: CSV delimiter
            
        Returns:
            Processing statistics
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
            
        # Set default operators
        if operators is None:
            operators = {
                "PERSON": "replace",
                "EMAIL_ADDRESS": "mask",
                "PHONE_NUMBER": "mask"
            }
            
        stats = {
            "input_file": input_file,
            "output_file": output_file,
            "start_time": datetime.now().isoformat(),
            "chunks_processed": 0,
            "rows_processed": 0,
            "entities_found": {}
        }
        
        try:
            # Process file in chunks
            first_chunk = True
            
            for chunk_df in pd.read_csv(
                input_file,
                chunksize=chunk_size,
                encoding=encoding,
                delimiter=delimiter
            ):
                # Process each column in chunk
                for column in columns:
                    if column in chunk_df.columns:
                        # Create temporary output column
                        output_column = f"{column}_temp"
                        
                        # Process column
                        chunk_df = self.ally.process_dataframe(
                            chunk_df,
                            column=column,
                            operation="anonymize",
                            output_column=output_column,
                            operators=operators
                        )
                        
                        # Replace original with anonymized
                        chunk_df[column] = chunk_df[output_column]
                        chunk_df = chunk_df.drop(columns=[output_column])
                        
                # Write chunk to output file
                if first_chunk:
                    chunk_df.to_csv(output_file, index=False, encoding=encoding, mode='w')
                    first_chunk = False
                else:
                    chunk_df.to_csv(output_file, index=False, encoding=encoding, mode='a', header=False)
                    
                stats["chunks_processed"] += 1
                stats["rows_processed"] += len(chunk_df)
                
                logger.info(f"Processed chunk {stats['chunks_processed']} ({stats['rows_processed']} total rows)")
                
            stats["end_time"] = datetime.now().isoformat()
            start_time = datetime.fromisoformat(stats["start_time"])
            end_time = datetime.fromisoformat(stats["end_time"])
            stats["processing_time_seconds"] = (end_time - start_time).total_seconds()
            
        except Exception as e:
            stats["error"] = str(e)
            logger.error(f"Error in stream processing: {e}")
            raise
            
        return stats
        
    def process_csv_directory(
        self,
        input_dir: str,
        output_dir: str = None,
        columns_to_anonymize: List[str] = None,
        operators: Dict[str, str] = None,
        file_pattern: str = "*.csv",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        Process all CSV files in a directory.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path (if None, creates _anonymized subdirectory)
            columns_to_anonymize: Columns to process
            operators: Operators for anonymization
            file_pattern: File pattern to match
            recursive: Whether to process subdirectories
            
        Returns:
            Processing statistics for all files
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
            
        # Set default output directory
        if output_dir is None:
            output_dir = input_path / "anonymized"
            
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Find all CSV files
        if recursive:
            csv_files = list(input_path.rglob(file_pattern))
        else:
            csv_files = list(input_path.glob(file_pattern))
            
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        # Process each file
        results = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "files_processed": [],
            "total_entities_found": {},
            "errors": []
        }
        
        for csv_file in csv_files:
            try:
                # Calculate relative path for subdirectories
                relative_path = csv_file.relative_to(input_path)
                output_file = output_path / relative_path
                
                # Create subdirectories if needed
                output_file.parent.mkdir(exist_ok=True, parents=True)
                
                logger.info(f"Processing: {csv_file}")
                
                # Process file
                file_stats = self.process_csv_file(
                    input_file=str(csv_file),
                    output_file=str(output_file),
                    columns_to_anonymize=columns_to_anonymize,
                    operators=operators,
                    generate_report=False
                )
                
                results["files_processed"].append({
                    "input": str(csv_file),
                    "output": str(output_file),
                    "rows": file_stats.get("rows_processed", 0),
                    "entities": file_stats.get("entities_found", {})
                })
                
                # Aggregate entity counts
                for entity_type, count in file_stats.get("entities_found", {}).items():
                    results["total_entities_found"][entity_type] = \
                        results["total_entities_found"].get(entity_type, 0) + count
                        
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
                results["errors"].append({
                    "file": str(csv_file),
                    "error": str(e)
                })
                
        return results
        
    def save_csv_config(
        self,
        config_file: str,
        config: Dict[str, Any]
    ) -> bool:
        """
        Save CSV processing configuration to file.
        
        Args:
            config_file: Path to save configuration
            config: Configuration dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved configuration to: {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def load_csv_config(
        self,
        config_file: str
    ) -> Dict[str, Any]:
        """
        Load CSV processing configuration from file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from: {config_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
            
    def process_csv_with_config(
        self,
        input_file: str,
        config_file: str,
        output_file: str = None
    ) -> Dict[str, Any]:
        """
        Process CSV file using saved configuration.
        
        Args:
            input_file: Input CSV file
            config_file: Configuration file path
            output_file: Output file path (optional)
            
        Returns:
            Processing statistics
        """
        # Load configuration
        config = self.load_csv_config(config_file)
        
        # Extract parameters
        columns = config.get("columns")
        operators = config.get("operators")
        encoding = config.get("encoding", "utf-8")
        delimiter = config.get("delimiter", ",")
        
        # Process file
        return self.process_csv_file(
            input_file=input_file,
            output_file=output_file,
            columns_to_anonymize=columns,
            operators=operators,
            encoding=encoding,
            delimiter=delimiter
        )
        
    def _generate_report(
        self,
        stats: Dict[str, Any],
        output_file: str
    ) -> str:
        """
        Generate processing report.
        
        Args:
            stats: Processing statistics
            output_file: Output file path
            
        Returns:
            Report file path
        """
        report_path = Path(output_file).parent / f"{Path(output_file).stem}_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("CSV Processing Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Input File: {stats.get('input_file')}\n")
            f.write(f"Output File: {stats.get('output_file')}\n")
            f.write(f"Processing Time: {stats.get('processing_time_seconds', 0):.2f} seconds\n\n")
            
            f.write(f"Rows Processed: {stats.get('rows_processed', 0)}\n")
            f.write(f"Columns Processed: {', '.join(stats.get('columns_processed', []))}\n\n")
            
            if stats.get('auto_detected_columns'):
                f.write(f"Auto-detected Columns: {', '.join(stats['auto_detected_columns'])}\n\n")
                
            f.write("Entities Found:\n")
            for entity_type, count in sorted(stats.get('entities_found', {}).items()):
                f.write(f"  - {entity_type}: {count}\n")
                
            if stats.get('errors'):
                f.write("\nErrors:\n")
                for error in stats['errors']:
                    f.write(f"  - {error}\n")
                    
        logger.info(f"Report saved to: {report_path}")
        return str(report_path)