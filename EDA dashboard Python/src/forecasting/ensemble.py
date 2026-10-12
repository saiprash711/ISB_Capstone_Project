"""
Ensemble Forecasting Module
Implements multi-model combination strategies:
- Performance-weighted ensemble (Inverse-WAPE)
- Simple average ensemble
- Median ensemble
Provides comparative benchmarking against individual champion models.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any


class EnsembleForecaster:
    """
    Combines individual forecasts using statistical weighting and robust averaging.
    """
    
    def __init__(self, method: str = 'inverse_wape'):
        """
        Args:
            method: 'inverse_wape', 'mean', or 'median'
        """
        self.method = method

    def combine_forecasts(self, forecast_dict: Dict[str, np.ndarray], 
                          wape_weights: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        Combine multiple model forecasts into a consensus forecast.
        
        Args:
            forecast_dict: dict of model_name -> forecast array (all of length H)
            wape_weights: optional dict of model_name -> historical WAPE %
        
        Returns:
            1D numpy array of ensemble forecast
        """
        valid_models = []
        forecast_matrix = []
        
        for name, fcast in forecast_dict.items():
            if fcast is not None and len(fcast) > 0:
                arr = np.asarray(fcast, dtype=float)
                if not np.all(np.isnan(arr)):
                    valid_models.append(name)
                    # Impute internal NaNs with mean of valid values
                    nan_mask = np.isnan(arr)
                    if np.any(nan_mask):
                        val_mean = np.nanmean(arr) if not np.all(nan_mask) else 0.0
                        arr[nan_mask] = val_mean
                    forecast_matrix.append(arr)
                    
        if not forecast_matrix:
            return np.array([])
            
        mat = np.column_stack(forecast_matrix)  # shape: (horizon, n_models)
        
        if self.method == 'median':
            return np.maximum(0.0, np.nanmedian(mat, axis=1))
            
        if self.method == 'mean' or wape_weights is None:
            return np.maximum(0.0, np.nanmean(mat, axis=1))
            
        # Inverse-WAPE Weighting
        inv_weights = []
        for name in valid_models:
            w = wape_weights.get(name, 25.0)
            w = max(1.0, float(w))  # Avoid zero division
            inv_weights.append(1.0 / w)
            
        weights = np.array(inv_weights)
        norm_weights = weights / np.sum(weights)
        
        # Weighted dot product
        ensemble_pred = np.dot(mat, norm_weights)
        return np.maximum(0.0, ensemble_pred)

    def benchmark_ensemble_vs_champion(self, champion_name: str, champion_forecast: np.ndarray,
                                       champion_wape: float,
                                       forecast_dict: Dict[str, np.ndarray],
                                       wape_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare Champion model against the consensus ensemble based on actual metrics.
        """
        ensemble_pred = self.combine_forecasts(forecast_dict, wape_weights=wape_dict)
        n_models = len(forecast_dict)
        
        # Check if actual backtested ensemble WAPE is available
        if 'Ensemble (Consensus)' in wape_dict:
            ensemble_wape = round(float(wape_dict['Ensemble (Consensus)']), 2)
            metric_basis = "measured_backtest_folds"
        elif wape_dict:
            # Calculate mathematically weighted expectation: sum(w_i * wape_i)
            inv_w = [1.0 / max(1.0, float(wape_dict.get(m, 25.0))) for m in forecast_dict.keys()]
            tot_w = sum(inv_w) or 1.0
            norm_w = [w / tot_w for w in inv_w]
            weighted_wape = sum(norm_w[i] * float(wape_dict.get(m, 25.0)) for i, m in enumerate(forecast_dict.keys()))
            ensemble_wape = round(float(weighted_wape), 2)
            metric_basis = "inverse_wape_weighted_expectation"
        else:
            ensemble_wape = round(float(champion_wape), 2)
            metric_basis = "champion_parity"
        
        diff = np.mean(np.abs(champion_forecast - ensemble_pred))
        pct_divergence = (diff / np.mean(champion_forecast) * 100.0) if np.mean(champion_forecast) > 0 else 0.0
        
        return {
            'champion_model': champion_name,
            'champion_wape': champion_wape,
            'ensemble_method': self.method,
            'models_included': list(forecast_dict.keys()),
            'ensemble_wape': ensemble_wape,
            'metric_basis': metric_basis,
            'forecast_divergence_pct': round(float(pct_divergence), 2),
            'ensemble_forecast': ensemble_pred,
            'recommendation': (
                f"Ensemble consensus of {n_models} models tracks champion with {pct_divergence:.1f}% divergence "
                f"(Ensemble WAPE: {ensemble_wape:.1f}%, Champion WAPE: {champion_wape:.1f}%)."
            )
        }
