"""
Data Ingestion Module
Handles loading, caching, and initial data reading.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging

try:
    import streamlit as st
    cache_data_decorator = st.cache_data(show_spinner="Loading enterprise dataset...")
except (ImportError, ModuleNotFoundError):
    def cache_data_decorator(func):
        return func

logger = logging.getLogger(__name__)


@cache_data_decorator
def load_raw_data(filepath: str = None) -> pd.DataFrame:
    """
    Load raw billing data from CSV or Excel.
    
    Args:
        filepath: Path to data file. If None, auto-detects Filtered.csv or Filtered.xlsx
        
    Returns:
        pd.DataFrame: Raw dataset
        
    Notes:
        - Dataset grain: Transaction level (one row per billing line)
        - Size: ~82K rows × 23 columns
        - No modifications to raw data
    """
    
    if filepath is None:
        # Auto-detect common filenames
        possible_paths = [
            Path("Filtered.csv"),
            Path("Filtered.xlsx"),
            Path("data/Filtered.csv"),
            Path("data/Filtered.xlsx"),
        ]
        
        for path in possible_paths:
            if path.exists():
                filepath = str(path)
                break
        
        if filepath is None:
            raise FileNotFoundError("Could not find Filtered.csv or Filtered.xlsx")
    
    logger.info(f"Loading data from: {filepath}")
    
    # Load based on extension
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath, low_memory=False)
    elif filepath.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")
    
    logger.info(f"Loaded {len(df)} rows × {len(df.columns)} columns")
    return df


def get_dataset_info(df: pd.DataFrame) -> dict:
    """Get basic information about the dataset."""
    # Handle date range safely
    date_range = "N/A"
    if 'Billing Date' in df.columns:
        try:
            dates = pd.to_datetime(df['Billing Date'], dayfirst=True, errors='coerce')
            date_range = f"{dates.min()} to {dates.max()}"
        except:
            date_range = "Unable to parse dates"
    
    return {
        'rows': len(df),
        'columns': len(df.columns),
        'memory_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
        'date_range': date_range,
        'unique_skus': df['Material'].nunique() if 'Material' in df.columns else 0,
        'unique_branches': df['SALES OFFICE CODE'].nunique() if 'SALES OFFICE CODE' in df.columns else 0,
    }
