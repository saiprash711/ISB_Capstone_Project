"""
Forecasting Evaluation Metrics Module
Provides APICS/industry-standard zero-safe metric computations:
- WAPE (Weighted Absolute Percentage Error)
- sMAPE (Symmetric Mean Absolute Percentage Error)
- MASE (Mean Absolute Scaled Error)
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- Bias & Tracking Signal (Forecast Bias %)
"""
import numpy as np
from typing import Dict, Optional, Union, List


def calculate_wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Weighted Absolute Percentage Error (WAPE).
    WAPE = sum(|y_true - y_pred|) / sum(|y_true|) * 100
    
    Zero-safe: If sum of actuals is 0:
      - 0.0 if sum of predictions is also 0
      - 100.0 if predictions exist for zero actuals
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    # Filter non-finite pairs
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(mask):
        return 0.0
        
    yt = y_true[mask]
    yp = y_pred[mask]
    
    denom = np.sum(np.abs(yt))
    num = np.sum(np.abs(yt - yp))
    
    if denom == 0:
        return 0.0 if num == 0 else 100.0
        
    return float((num / denom) * 100.0)


def calculate_smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Symmetric Mean Absolute Percentage Error (sMAPE).
    sMAPE = 100% / n * sum( 2 * |y_true - y_pred| / (|y_true| + |y_pred|) )
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(mask):
        return 0.0
        
    yt = y_true[mask]
    yp = y_pred[mask]
    
    denom = (np.abs(yt) + np.abs(yp)) / 2.0
    zero_mask = denom == 0.0
    
    ratios = np.zeros_like(yt)
    ratios[~zero_mask] = np.abs(yt[~zero_mask] - yp[~zero_mask]) / denom[~zero_mask]
    
    return float(np.mean(ratios) * 100.0)


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Error (MAE)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(mask):
        return 0.0
        
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask])))


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Squared Error (RMSE)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(mask):
        return 0.0
        
    return float(np.sqrt(np.mean((y_true[mask] - y_pred[mask]) ** 2)))


def calculate_mase(y_true: np.ndarray, y_pred: np.ndarray, y_train: Optional[np.ndarray] = None, 
                   m: int = 1) -> float:
    """
    Calculate Mean Absolute Scaled Error (MASE).
    Scales error by in-sample 1-step naive (or seasonal naive of period m) error.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(mask):
        return 1.0
        
    mae_eval = np.mean(np.abs(y_true[mask] - y_pred[mask]))
    
    if y_train is not None and len(y_train) > m:
        yt_arr = np.asarray(y_train, dtype=float)
        yt_finite = yt_arr[np.isfinite(yt_arr)]
        if len(yt_finite) > m:
            scale = np.mean(np.abs(yt_finite[m:] - yt_finite[:-m]))
            if scale > 1e-6:
                return float(mae_eval / scale)
                
    # Fallback to test naive scaling
    if len(y_true[mask]) > 1:
        diffs = np.abs(np.diff(y_true[mask]))
        scale = np.mean(diffs)
        if scale > 1e-6:
            return float(mae_eval / scale)
            
    return 1.0


def calculate_bias(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Mean Forecast Bias (signed error).
    Positive = over-forecasting, Negative = under-forecasting.
    Bias = mean(y_pred - y_true)
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(mask):
        return 0.0
        
    return float(np.mean(y_pred[mask] - y_true[mask]))


def calculate_bias_pct(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Percentage Forecast Bias.
    Bias % = sum(y_pred - y_true) / sum(y_true) * 100
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(mask):
        return 0.0
        
    denom = np.sum(y_true[mask])
    if denom == 0:
        return 0.0
        
    return float((np.sum(y_pred[mask] - y_true[mask]) / denom) * 100.0)


def calculate_all_metrics(y_true: np.ndarray, y_pred: np.ndarray, 
                          y_train: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Calculate consolidated suite of forecasting evaluation metrics.
    
    Returns:
        Dict with keys: WAPE, sMAPE, MAE, RMSE, MASE, Bias, Bias_pct
    """
    return {
        'WAPE': round(calculate_wape(y_true, y_pred), 2),
        'sMAPE': round(calculate_smape(y_true, y_pred), 2),
        'MAE': round(calculate_mae(y_true, y_pred), 2),
        'RMSE': round(calculate_rmse(y_true, y_pred), 2),
        'MASE': round(calculate_mase(y_true, y_pred, y_train=y_train), 3),
        'Bias': round(calculate_bias(y_true, y_pred), 2),
        'Bias_pct': round(calculate_bias_pct(y_true, y_pred), 2)
    }
