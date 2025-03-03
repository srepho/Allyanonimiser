"""
Stream processing utilities for Allyanonimiser.

This module provides streaming capabilities for processing very large files
using Polars for maximum efficiency and minimal memory usage.
"""

import os
from typing import Union, List, Dict, Optional, Callable, Tuple, Generator, Iterable, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Polars support is optional
POLARS_AVAILABLE = False
try:
    import polars as pl
    # Use the proper typing module
    try:
        # New approach (preferred)
        from polars._typing import IntoExpr
    except ImportError:
        # Fallback to deprecated approach
        from polars.type_aliases import IntoExpr
        
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


class StreamProcessor:
    """
    Provides streaming processing capabilities for very large files using Polars.
    
    This class enables Allyanonimiser to process extremely large datasets
    with minimal memory impact by using Polars' lazy evaluation and streaming
    capabilities, processing data in chunks.
    """
    
    def __init__(self, allyanonimiser=None, n_workers=None, chunk_size=None):
        """
        Initialize the stream processor.
        
        Args:
            allyanonimiser: An existing Allyanonimiser instance or None to create a new one
            n_workers: Number of worker processes for parallel processing (default: None = use CPU count)
            chunk_size: Number of rows to process in each chunk (default: 10,000)
        """
        if not POLARS_AVAILABLE:
            logger.warning(
                "Polars is required for stream processing but is not available. "
                "Install with: pip install polars"
            )
            
        from .allyanonimiser import create_allyanonimiser
        self.analyzer = allyanonimiser or create_allyanonimiser()
        
        # Use values from settings if not explicitly provided
        if n_workers is None and hasattr(self.analyzer, 'worker_count'):
            self.n_workers = self.analyzer.worker_count
        else:
            self.n_workers = n_workers or os.cpu_count()
            
        # Use chunk size from settings or default
        if chunk_size is None and hasattr(self.analyzer, 'chunk_size'):
            self.chunk_size = self.analyzer.chunk_size
        else:
            self.chunk_size = chunk_size or 10000
            
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
        text_columns: Union[str, List[str]],
        active_entity_types: Optional[List[str]] = None,
        operators: Optional[Dict[str, str]] = None,
        min_score_threshold: float = 0.7,
        anonymize: bool = True,
        chunk_size: Optional[int] = None,
        output_path: Optional[str] = None,
        progress_bar: bool = True,
        csv_options: Optional[Dict[str, Any]] = None,
        age_bracket_size: int = 5,
        keep_postcode: bool = True
    ) -> Generator[Dict[str, Union[pd.DataFrame, List]], None, None]:
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
            Dict with processed chunk as DataFrame and entity DataFrame
            
        Note: For true streaming with minimal memory impact, provide output_path
        parameter so each processed chunk is written to disk immediately.
        """
        self._check_polars_available()
        
        # Import polars here to ensure it's available in this function scope
        import polars as pl
        
        # Use instance chunk_size if not provided
        chunk_size = chunk_size or self.chunk_size
        
        # Default CSV options
        if csv_options is None:
            csv_options = {
                "infer_schema_length": chunk_size,
                "n_rows": None,  # Process all rows
                "low_memory": True
            }
            
        # Configure analyzer settings
        if active_entity_types is not None:
            self.analyzer.analyzer.set_active_entity_types(active_entity_types)
            
        self.analyzer.analyzer.set_min_score_threshold(min_score_threshold)
        
        # Handle single column case
        if isinstance(text_columns, str):
            text_columns = [text_columns]
            
        # Configure Polars streaming chunk size
        try:
            pl.Config.set_streaming_chunk_size(chunk_size)
        except Exception as e:
            logger.warning(f"Failed to set Polars streaming chunk size: {e}")
            
        # Create LazyFrame for streaming
        lf = pl.scan_csv(file_path, **csv_options)
        
        # Validate columns are in the file
        available_columns = lf.columns
        for column in text_columns:
            if column not in available_columns:
                raise ValueError(f"Column '{column}' not found in CSV file")
        
        # Create output directories if needed
        if output_path and not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Process in chunks
        chunk_counter = 0
        entities_buffer = []
        
        # Setup progress tracking if enabled
        if progress_bar:
            try:
                from tqdm import tqdm
            except ImportError:
                logger.warning("tqdm not installed, progress bar disabled")
                progress_bar = False
                
        # Determine total number of chunks for progress bar
        if progress_bar:
            # Get file size and estimate number of chunks
            file_size = os.path.getsize(file_path)
            # Check for header to estimate rows
            with open(file_path, 'r') as f:
                header = f.readline()
            avg_row_size = len(header)  # Use header as initial estimate
            est_rows = max(10, file_size // max(1, avg_row_size))
            est_chunks = (est_rows + chunk_size - 1) // chunk_size
            
            progress = tqdm(total=est_chunks, desc="Processing chunks")
        
        # Stream through the file with lazy evaluation
        # Configure Polars streaming chunk size
        try:
            import polars as pl
            pl.Config.set_streaming_chunk_size(chunk_size)
        except Exception as e:
            logger.warning(f"Failed to set Polars streaming chunk size: {e}")
            
        # Use streaming mode without explicit chunk_size parameter
        for chunk in lf.collect(streaming=True):
            # Process this chunk
            result = self._process_chunk(
                chunk=chunk,
                text_columns=text_columns,
                active_entity_types=active_entity_types,
                operators=operators,
                min_score_threshold=min_score_threshold,
                anonymize=anonymize,
                age_bracket_size=age_bracket_size,
                keep_postcode=keep_postcode
            )
            
            # Extract entities and processed data
            processed_chunk = result['dataframe']
            if 'entities' in result:
                entities_buffer.extend(result['entities'].to_pandas().to_dict('records'))
            
            # Write to output file if path provided (streaming mode)
            if output_path:
                # Determine write mode based on chunk number
                mode = "w" if chunk_counter == 0 else "a"
                header = chunk_counter == 0
                
                # Convert to pandas for consistent CSV writing
                pandas_chunk = processed_chunk.to_pandas()
                pandas_chunk.to_csv(output_path, mode=mode, header=header, index=False)
                
                # Only yield entities if they exist
                if entities_buffer:
                    yield {
                        'entities': pd.DataFrame(entities_buffer)
                    }
                    entities_buffer = []  # Clear buffer after yielding
            else:
                # If not streaming to file, yield the processed chunk
                yield_result = {'dataframe': processed_chunk}
                
                # Include entities if they exist
                if entities_buffer:
                    yield_result['entities'] = pd.DataFrame(entities_buffer)
                    entities_buffer = []  # Clear buffer after yielding
                
                yield yield_result
            
            # Update progress
            if progress_bar:
                progress.update(1)
                
            chunk_counter += 1
            
        # Close progress bar
        if progress_bar:
            progress.close()
                
        # Yield any remaining entities
        if entities_buffer:
            yield {'entities': pd.DataFrame(entities_buffer)}
    
    def _process_chunk(
        self,
        chunk: Union[pl.DataFrame, pd.DataFrame],
        text_columns: List[str],
        active_entity_types: Optional[List[str]] = None,
        operators: Optional[Dict[str, str]] = None,
        min_score_threshold: float = 0.7,
        anonymize: bool = True,
        age_bracket_size: int = 5,
        keep_postcode: bool = True
    ) -> Dict[str, Union[pl.DataFrame, pd.DataFrame, List[Dict[str, Any]]]]:
        """
        Process a single chunk of data.
        
        Args:
            chunk: Polars DataFrame or pandas DataFrame chunk to process
            text_columns: Column name(s) containing text to process
            active_entity_types: Optional list of entity types to activate
            operators: Dict mapping entity_type to anonymization operator
            min_score_threshold: Minimum confidence score threshold
            anonymize: Whether to perform anonymization
            age_bracket_size: Size of age brackets when using "age_bracket" operator
            keep_postcode: Whether to keep postcodes when anonymizing addresses
            
        Returns:
            Dict with processed chunk and entity list
        """
        # Convert to pandas for processing with Allyanonimiser
        # We'll add native Polars processing in a future version
        if hasattr(chunk, 'to_pandas'):
            try:
                pd_chunk = chunk.to_pandas()
            except Exception as e:
                logger.warning(f"Failed to convert Polars DataFrame to pandas: {e}. Using direct pandas processing.")
                # If we can't convert to pandas, use pandas directly if it's a DataFrame
                if isinstance(chunk, pd.DataFrame):
                    pd_chunk = chunk
                else:
                    # Try a different approach - convert to dict and then to pandas
                    try:
                        import pandas as pd
                        dict_data = {col: chunk[col].to_list() for col in chunk.columns}
                        pd_chunk = pd.DataFrame(dict_data)
                    except Exception as e2:
                        raise ValueError(f"Could not process chunk data: {e2}")
        else:
            # If it's already a pandas DataFrame
            pd_chunk = chunk
        
        # Create a copy to avoid modifying the original
        result_df = pd_chunk.copy()
        all_entities = []
        
        # Process each text column
        for column in text_columns:
            # Skip if column doesn't exist
            if column not in pd_chunk.columns:
                continue
                
            # Determine output column name for anonymized text
            output_column = f"{column}_anonymized"
            
            # Process each row in the chunk
            for idx, row in pd_chunk.iterrows():
                text = row[column]
                
                # Skip None/NaN values
                if pd.isna(text):
                    continue
                    
                # Analyze text
                entities = self.analyzer.analyze(
                    text, 
                    active_entity_types=active_entity_types,
                    min_score_threshold=min_score_threshold
                )
                
                # Format entities
                formatted_entities = [
                    {
                        'row_index': idx,
                        'column': column,
                        'entity_type': entity.entity_type,
                        'start': entity.start,
                        'end': entity.end,
                        'text': entity.text or text[entity.start:entity.end],
                        'score': entity.score
                    }
                    for entity in entities
                ]
                all_entities.extend(formatted_entities)
                
                # Anonymize if requested
                if anonymize:
                    result = self.analyzer.anonymize(
                        text, 
                        operators=operators,
                        age_bracket_size=age_bracket_size,
                        keep_postcode=keep_postcode
                    )
                    result_df.at[idx, output_column] = result['text']
        
        # Try to convert back to Polars for consistent return
        if POLARS_AVAILABLE:
            try:
                import polars as pl
                result_pl = pl.from_pandas(result_df)
                return {
                    'dataframe': result_pl,
                    'entities': all_entities
                }
            except Exception as e:
                logger.warning(f"Failed to convert pandas DataFrame to Polars: {e}. Returning pandas DataFrame.")
        
        # Default to pandas if Polars conversion fails
        return {
            'dataframe': result_df,
            'entities': all_entities
        }
                
    def process_large_file(
        self,
        file_path: str,
        text_columns: Union[str, List[str]],
        output_path: str,
        active_entity_types: Optional[List[str]] = None,
        operators: Optional[Dict[str, str]] = None,
        min_score_threshold: float = 0.7,
        anonymize: bool = True,
        chunk_size: Optional[int] = None,
        save_entities: bool = True,
        entities_output_path: Optional[str] = None,
        csv_options: Optional[Dict[str, Any]] = None,
        age_bracket_size: int = 5,
        keep_postcode: bool = True,
        progress_bar: bool = True
    ) -> Dict[str, Any]:
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
        
        # Stream process the file
        total_rows = 0
        total_entities = 0
        entities_buffer = []
        
        for chunk_result in self.stream_from_file(
            file_path=file_path,
            text_columns=text_columns,
            active_entity_types=active_entity_types,
            operators=operators,
            min_score_threshold=min_score_threshold,
            anonymize=anonymize,
            chunk_size=chunk_size,
            output_path=output_path,
            progress_bar=progress_bar,
            csv_options=csv_options,
            age_bracket_size=age_bracket_size,
            keep_postcode=keep_postcode
        ):
            # Update statistics
            if 'dataframe' in chunk_result:
                total_rows += len(chunk_result['dataframe'])
                
            # Collect entities if saving
            if save_entities and 'entities' in chunk_result:
                entities_df = chunk_result['entities']
                entities_buffer.extend(entities_df.to_dict('records'))
                total_entities += len(entities_df)
        
        # Save collected entities if requested
        if save_entities and entities_output_path and entities_buffer:
            entities_df = pd.DataFrame(entities_buffer)
            entities_df.to_csv(entities_output_path, index=False)
        
        return {
            'total_rows_processed': total_rows,
            'total_entities_detected': total_entities,
            'output_file': output_path,
            'entities_file': entities_output_path if save_entities else None
        }