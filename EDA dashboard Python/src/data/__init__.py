"""
Data Engineering Module
Complete data pipeline for Demand Intelligence Platform.

Modules:
  - ingestion: Load raw data
  - validation: Data quality checks
  - cleaning: Data deduplication and standardization
  - transformation: Aggregate to SKU × BRANCH × WEEK data mart
  - pipeline: Orchestrate full pipeline
"""

from .ingestion import load_raw_data, get_dataset_info
from .validation import DataValidator, ValidationResult
from .cleaning import DataCleaner
from .transformation import DataTransformer
from .pipeline import DataPipeline

__all__ = [
    'load_raw_data',
    'get_dataset_info',
    'DataValidator',
    'ValidationResult',
    'DataCleaner',
    'DataTransformer',
    'DataPipeline',
]
