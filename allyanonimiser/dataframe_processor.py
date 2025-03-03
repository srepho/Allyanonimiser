"""
DataFrame processing utilities for Allyanonimiser.
"""

import pandas as pd
from typing import Union, List, Dict, Optional, Callable, Tuple
import concurrent.futures
from tqdm import tqdm

# PyArrow support is optional
PYARROW_AVAILABLE = False
try:
    import pyarrow as pa
    import pyarrow.compute as pc
    PYARROW_AVAILABLE = True
except ImportError:
    # Define dummy objects to avoid NameErrors when PyArrow is not available
    class DummyModule:
        Table = object
    pa = DummyModule()


class DataFrameProcessor:
    """
    Provides efficient pandas DataFrame processing capabilities for Allyanonimiser.
    """
    
    def __init__(self, allyanonimiser=None, n_workers=None, batch_size=None, use_pyarrow=None):
        """
        Initialize the DataFrame processor.
        
        Args:
            allyanonimiser: An existing Allyanonimiser instance or None to create a new one
            n_workers: Number of worker processes for parallel processing (default: None = sequential)
            batch_size: Number of rows to process in each batch (default: None = use from settings)
            use_pyarrow: Whether to use PyArrow for DataFrame conversions (default: None = auto-detect)
        """
        from .allyanonimiser import create_allyanonimiser
        self.analyzer = allyanonimiser or create_allyanonimiser()
        
        # Use values from settings if not explicitly provided
        if n_workers is None and hasattr(self.analyzer, 'worker_count'):
            self.n_workers = self.analyzer.worker_count
        else:
            self.n_workers = n_workers
            
        # Use batch size from settings if available
        if batch_size is None and hasattr(self.analyzer, 'batch_size'):
            self.batch_size = self.analyzer.batch_size
        else:
            self.batch_size = batch_size or 1000
            
        # PyArrow configuration
        if use_pyarrow is None:
            self.use_pyarrow = PYARROW_AVAILABLE
        else:
            self.use_pyarrow = use_pyarrow and PYARROW_AVAILABLE
            
        if self.use_pyarrow and not PYARROW_AVAILABLE:
            import logging
            logging.getLogger(__name__).warning(
                "PyArrow was requested but is not available. Install with: pip install pyarrow"
            )
        
    def detect_pii(self, 
                  df: pd.DataFrame, 
                  column: str,
                  active_entity_types: Optional[List[str]] = None,
                  min_score_threshold: float = 0.7,
                  batch_size: int = 1000) -> pd.DataFrame:
        """
        Detect PII in a DataFrame column and return results as a new DataFrame.
        
        Args:
            df: Input DataFrame
            column: Column name containing text to analyze
            active_entity_types: Optional list of entity types to activate
            min_score_threshold: Minimum confidence score threshold
            batch_size: Number of rows to process in each batch
            
        Returns:
            DataFrame with detected entities, one row per entity
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
            
        # Configure analyzer settings
        if active_entity_types is not None:
            self.analyzer.analyzer.set_active_entity_types(active_entity_types)
        
        self.analyzer.analyzer.set_min_score_threshold(min_score_threshold)
        
        # Process in batches for memory efficiency
        results = []
        
        # Define processing function for a single text
        def process_text(text, idx):
            if pd.isna(text):
                return []
                
            entities = self.analyzer.analyze(text)
            return [
                {
                    'row_index': idx,
                    'entity_type': entity.entity_type,
                    'start': entity.start,
                    'end': entity.end,
                    'text': entity.text or text[entity.start:entity.end],
                    'score': entity.score
                }
                for entity in entities
            ]
            
        # Process in batches with parallel execution
        total_rows = len(df)
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]
            
            if self.n_workers and self.n_workers > 1:
                # Parallel processing for batch
                with concurrent.futures.ProcessPoolExecutor(max_workers=self.n_workers) as executor:
                    batch_results = list(executor.map(
                        process_text,
                        batch[column].tolist(),
                        batch.index.tolist()
                    ))
            else:
                # Sequential processing for batch
                batch_results = [
                    process_text(text, idx) 
                    for text, idx in zip(batch[column].tolist(), batch.index.tolist())
                ]
                
            # Flatten results
            for entities in batch_results:
                results.extend(entities)
                
        # Convert to DataFrame
        if not results:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'row_index', 'entity_type', 'start', 'end', 'text', 'score'
            ])
            
        return pd.DataFrame(results)
        
    def anonymize_column(self,
                        df: pd.DataFrame,
                        column: str,
                        operators: Optional[Dict[str, str]] = None,
                        active_entity_types: Optional[List[str]] = None,
                        inplace: bool = False,
                        output_column: Optional[str] = None,
                        batch_size: int = 1000,
                        age_bracket_size: int = 5,
                        keep_postcode: bool = True) -> pd.DataFrame:
        """
        Anonymize PII in a DataFrame column.
        
        Args:
            df: Input DataFrame
            column: Column name containing text to anonymize
            operators: Dict mapping entity_type to anonymization operator
                       (e.g., "PERSON": "replace", "PHONE_NUMBER": "mask")
            active_entity_types: Optional list of entity types to activate
            inplace: If True, modify the DataFrame in place
            output_column: Optional name for the output column (if None, uses f"{column}_anonymized")
            batch_size: Number of rows to process in each batch
            age_bracket_size: Size of age brackets when using "age_bracket" operator (default: 5)
            keep_postcode: Whether to keep postcodes when anonymizing addresses (default: True)
            
        Returns:
            DataFrame with anonymized text
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
            
        # Determine output column name
        if output_column is None:
            output_column = f"{column}_anonymized"
            
        # Make a copy of the DataFrame if not inplace
        result_df = df if inplace else df.copy()
        
        # Configure analyzer settings
        if active_entity_types is not None:
            self.analyzer.analyzer.set_active_entity_types(active_entity_types)
            
        # Define processing function for a single text
        def anonymize_text(text):
            if pd.isna(text):
                return text
                
            result = self.analyzer.anonymize(
                text, 
                operators=operators,
                age_bracket_size=age_bracket_size,
                keep_postcode=keep_postcode
            )
            return result['text']
            
        # Process in batches
        total_rows = len(df)
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]
            
            if self.n_workers and self.n_workers > 1:
                # Parallel processing
                with concurrent.futures.ProcessPoolExecutor(max_workers=self.n_workers) as executor:
                    anonymized_texts = list(executor.map(
                        anonymize_text,
                        batch[column].tolist()
                    ))
            else:
                # Sequential processing
                anonymized_texts = [anonymize_text(text) for text in batch[column].tolist()]
                
            # Update the DataFrame
            result_df.loc[batch.index, output_column] = anonymized_texts
            
        return result_df
        
    def _to_arrow_table(self, df: pd.DataFrame) -> pa.Table:
        """
        Convert pandas DataFrame to PyArrow Table for performance optimization.
        Uses zero-copy conversion when possible for maximum performance.
        
        Args:
            df: Input pandas DataFrame
            
        Returns:
            PyArrow Table
        """
        if self.use_pyarrow and PYARROW_AVAILABLE:
            try:
                # Use zero-copy whenever possible
                return pa.Table.from_pandas(df, preserve_index=True, nthreads=self.n_workers or 1)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to convert DataFrame to Arrow Table: {str(e)}. Falling back to pandas."
                )
                self.use_pyarrow = False
                return None
        return None
        
    def _get_column_from_arrow(self, table: pa.Table, column: str, batch_indices=None) -> Union[List, None]:
        """
        Extract a column from a PyArrow Table as a Python list.
        Optimized for batch processing with optional index filtering.
        
        Args:
            table: PyArrow Table
            column: Column name
            batch_indices: Optional list of indices to select (for batch processing)
            
        Returns:
            List of column values or None if PyArrow is not available
        """
        if table is not None and column in table.column_names:
            try:
                if batch_indices is not None:
                    # Create a boolean mask for the indices in this batch
                    if 'index' in table.column_names:
                        # Use the preserved pandas index column
                        index_array = table.column('index')
                        mask = pc.is_in(index_array, pa.array(batch_indices))
                        # Apply the mask to filter the table
                        filtered_table = table.filter(mask)
                        # Return the column we want
                        return filtered_table.column(column).to_pylist()
                    else:
                        # Direct slicing by position if no index column is available
                        return table.column(column).to_pylist()
                else:
                    # Return the entire column if no batch indices are specified
                    return table.column(column).to_pylist()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to extract column from Arrow Table: {str(e)}. Falling back to pandas."
                )
                return None
        return None
        
    def _batch_process_arrow(self, 
                            arrow_table: pa.Table, 
                            column: str, 
                            batch_size: int,
                            process_func: Callable,
                            progress_iterator=None) -> Tuple[List, List]:
        """
        Process a PyArrow table column in batches using optimized memory management.
        
        Args:
            arrow_table: PyArrow Table to process
            column: Column name to process
            batch_size: Number of rows in each batch
            process_func: Function to process each batch
            progress_iterator: Optional progress bar iterator
            
        Returns:
            Tuple of (all_entities, all_anonymized_texts)
        """
        if arrow_table is None or not PYARROW_AVAILABLE:
            return [], []

        try:
            total_rows = len(arrow_table)
            all_entities = []
            all_anonymized_texts = []
            
            # Get the indices column if available
            has_index = 'index' in arrow_table.column_names
            indices = arrow_table.column('index').to_pylist() if has_index else list(range(total_rows))
            
            # Process in batches
            for i in range(0, total_rows, batch_size):
                # Get batch indices
                batch_end = min(i + batch_size, total_rows)
                if progress_iterator is not None:
                    progress_iterator.update(1)
                
                # Get batch indices for filter
                batch_indices = indices[i:batch_end]
                
                # Get batch data using optimized filtering
                col_data = self._get_column_from_arrow(arrow_table, column, batch_indices)
                
                # Process the batch
                batch_entities = []
                batch_anonymized = []
                
                # Use parallel processing if enabled
                if self.n_workers and self.n_workers > 1:
                    with concurrent.futures.ProcessPoolExecutor(max_workers=self.n_workers) as executor:
                        results = list(executor.map(
                            process_func,
                            col_data,
                            batch_indices
                        ))
                        
                    # Unpack results
                    for entities, anonymized_text in results:
                        batch_entities.extend(entities)
                        batch_anonymized.append(anonymized_text)
                else:
                    # Sequential processing
                    for text, idx in zip(col_data, batch_indices):
                        entities, anonymized_text = process_func(text, idx)
                        batch_entities.extend(entities)
                        batch_anonymized.append(anonymized_text)
                
                # Collect results
                all_entities.extend(batch_entities)
                all_anonymized_texts.extend(batch_anonymized)
                
            return all_entities, all_anonymized_texts
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Error in Arrow batch processing: {str(e)}. Falling back to pandas."
            )
            return [], []
    
    def process_dataframe(self,
                          df: pd.DataFrame,
                          text_columns: Union[str, List[str]],
                          active_entity_types: Optional[List[str]] = None,
                          operators: Optional[Dict[str, str]] = None,
                          min_score_threshold: float = 0.7,
                          batch_size: int = 1000,
                          anonymize: bool = True,
                          save_entities: bool = True,
                          output_prefix: str = '',
                          progress_bar: bool = True,
                          use_pyarrow: Optional[bool] = None,
                          age_bracket_size: int = 5,
                          keep_postcode: bool = True,
                          adaptive_batch_size: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Process multiple columns of a DataFrame for comprehensive PII handling.
        Uses optimized PyArrow integration and adaptive batch sizing for maximum performance.
        
        Args:
            df: Input DataFrame
            text_columns: Column name(s) containing text to process
            active_entity_types: Optional list of entity types to activate
            operators: Dict mapping entity_type to anonymization operator
            min_score_threshold: Minimum confidence score threshold
            batch_size: Number of rows to process in each batch
            anonymize: Whether to perform anonymization
            save_entities: Whether to return detected entities
            output_prefix: Prefix for output column names
            progress_bar: Whether to display a progress bar
            use_pyarrow: Whether to use PyArrow for performance optimization (overrides instance setting)
            age_bracket_size: Size of age brackets when using "age_bracket" operator (default: 5)
            keep_postcode: Whether to keep postcodes when anonymizing addresses (default: True)
            adaptive_batch_size: Dynamically adjust batch size based on data size (default: True)
            
        Returns:
            Dict with processed DataFrame and entity DataFrame (if save_entities=True)
        """
        # Handle single column case
        if isinstance(text_columns, str):
            text_columns = [text_columns]
            
        # Validate columns
        for column in text_columns:
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in DataFrame")
                
        # Configure analyzer settings
        if active_entity_types is not None:
            self.analyzer.analyzer.set_active_entity_types(active_entity_types)
            
        self.analyzer.analyzer.set_min_score_threshold(min_score_threshold)
        
        # Override PyArrow setting if specified
        original_use_pyarrow = self.use_pyarrow
        if use_pyarrow is not None:
            self.use_pyarrow = use_pyarrow and PYARROW_AVAILABLE
        
        # Apply adaptive batch sizing if requested
        if adaptive_batch_size:
            # Adjust batch size based on DataFrame size and available workers
            row_count = len(df)
            if row_count > 100000 and batch_size < 5000:
                batch_size = min(10000, max(5000, row_count // 20))
            elif row_count < 1000 and batch_size > 100:
                batch_size = max(100, row_count // 5)
                
            # Consider number of available workers
            if self.n_workers and self.n_workers > 1:
                # Make batch size a multiple of worker count for optimal distribution
                batch_size = max(100, (batch_size // self.n_workers) * self.n_workers)
        
        # Convert to Arrow Table if enabled - only once for all columns
        arrow_table = self._to_arrow_table(df) if self.use_pyarrow else None
            
        # Create a copy of the DataFrame
        result_df = df.copy()
        all_entities = []
        
        # Process each column
        for column in text_columns:
            # Determine output column name
            output_column = f"{output_prefix}{column}_anonymized" if output_prefix else f"{column}_anonymized"
            
            # Create iterator with progress bar if requested
            total_batches = (len(df) + batch_size - 1) // batch_size
            if progress_bar:
                iterator = tqdm(range(0, total_batches), desc=f"Processing {column}", total=total_batches)
            else:
                iterator = None
            
            # Define processing function
            def process_text(text, idx):
                if pd.isna(text):
                    return [], text
                    
                # Analyze text
                entities = self.analyzer.analyze(text, 
                                                active_entity_types=active_entity_types,
                                                min_score_threshold=min_score_threshold)
                
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
                
                # Anonymize if requested
                if anonymize:
                    result = self.analyzer.anonymize(
                        text, 
                        operators=operators,
                        age_bracket_size=age_bracket_size,
                        keep_postcode=keep_postcode
                    )
                    anonymized_text = result['text']
                else:
                    anonymized_text = text
                    
                return formatted_entities, anonymized_text
            
            # Process using optimized Arrow-based batch processing if available
            if self.use_pyarrow and arrow_table is not None:
                batch_entities, batch_anonymized = self._batch_process_arrow(
                    arrow_table=arrow_table,
                    column=column,
                    batch_size=batch_size,
                    process_func=process_text,
                    progress_iterator=iterator
                )
                
                # If Arrow processing succeeded
                if batch_anonymized:
                    # Update the DataFrame with all results at once
                    if anonymize:
                        # Optimize bulk update by creating a Series and assigning once
                        result_df[output_column] = pd.Series(
                            batch_anonymized, 
                            index=arrow_table.column('index').to_pylist() if 'index' in arrow_table.column_names 
                                  else df.index
                        )
                    
                    # Save entities
                    if save_entities:
                        all_entities.extend(batch_entities)
                    
                    # Continue to next column - we've processed the entire column already
                    continue
            
            # Fall back to pandas-based processing if PyArrow is not available or failed
            if progress_bar and iterator is None:
                iterator = tqdm(range(0, len(df), batch_size), desc=f"Processing {column}", total=total_batches)
            
            # Process in batches using pandas
            batch_indices = range(0, len(df), batch_size) if iterator is None else iterator
            for i in batch_indices:
                batch = df.iloc[i:i+batch_size]
                batch_entities = []
                batch_anonymized = []
                
                # Get column data
                col_data = batch[column].tolist()
                    
                # Process the batch
                if self.n_workers and self.n_workers > 1:
                    # Parallel processing
                    with concurrent.futures.ProcessPoolExecutor(max_workers=self.n_workers) as executor:
                        results = list(executor.map(
                            process_text,
                            col_data,
                            batch.index.tolist()
                        ))
                        
                    # Unpack results
                    for entities, anonymized_text in results:
                        batch_entities.extend(entities)
                        batch_anonymized.append(anonymized_text)
                else:
                    # Sequential processing
                    for text, idx in zip(col_data, batch.index.tolist()):
                        entities, anonymized_text = process_text(text, idx)
                        batch_entities.extend(entities)
                        batch_anonymized.append(anonymized_text)
                
                # Update the DataFrame
                if anonymize:
                    result_df.loc[batch.index, output_column] = batch_anonymized
                
                # Save entities
                if save_entities:
                    all_entities.extend(batch_entities)
        
        # Prepare result
        result = {'dataframe': result_df}
        
        if save_entities and all_entities:
            result['entities'] = pd.DataFrame(all_entities)
        elif save_entities:
            result['entities'] = pd.DataFrame(columns=[
                'row_index', 'column', 'entity_type', 'start', 'end', 'text', 'score'
            ])
        
        # Restore original PyArrow setting
        if use_pyarrow is not None:
            self.use_pyarrow = original_use_pyarrow
            
        return result
        
    def analyze_dataframe_statistics(self,
                                    entity_df: pd.DataFrame,
                                    text_df: pd.DataFrame = None,
                                    text_column: str = None) -> pd.DataFrame:
        """
        Analyze statistics about detected entities in a DataFrame.
        
        Args:
            entity_df: DataFrame with detected entities
            text_df: Optional original DataFrame with text
            text_column: Optional column name in text_df
            
        Returns:
            DataFrame with entity statistics
        """
        if entity_df.empty:
            return pd.DataFrame(columns=['entity_type', 'count', 'avg_score'])
            
        # Group by entity type and compute statistics
        stats = entity_df.groupby('entity_type').agg(
            count=('entity_type', 'count'),
            avg_score=('score', 'mean'),
            min_score=('score', 'min'),
            max_score=('score', 'max')
        ).reset_index()
        
        # Calculate percentage of rows with each entity type if text_df is provided
        if text_df is not None and text_column is not None:
            total_rows = len(text_df)
            
            # Count unique rows with each entity type
            rows_with_entity = entity_df.groupby('entity_type')['row_index'].nunique()
            
            # Add percentage column
            stats = stats.merge(
                rows_with_entity.reset_index().rename(columns={'row_index': 'unique_rows'}),
                on='entity_type'
            )
            stats['percentage'] = (stats['unique_rows'] / total_rows * 100).round(2)
            
        return stats