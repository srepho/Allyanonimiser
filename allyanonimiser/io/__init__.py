"""
IO adapters for CSV, DataFrame, and streaming processing.
"""

from .csv_processor import CSVProcessor
from .dataframe_processor import DataFrameProcessor

# StreamProcessor requires polars (optional)
try:
    from .stream_processor import StreamProcessor, POLARS_AVAILABLE
except ImportError:
    POLARS_AVAILABLE = False
    StreamProcessor = None

__all__ = [
    "CSVProcessor",
    "DataFrameProcessor",
    "StreamProcessor",
    "POLARS_AVAILABLE",
]
