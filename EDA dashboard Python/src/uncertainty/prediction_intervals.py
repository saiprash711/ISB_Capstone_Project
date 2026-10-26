"""
Uncertainty Quantification & Probabilistic Forecasting Module
Implements empirical residual quantile calibration and conformal prediction
to generate rigorous P10, P50, and P90 prediction intervals.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional


class ProbabilisticForecastEngine:
    """
    Computes calibrated prediction intervals (P10, P50, P90) from historical residuals.
    """
    
    def __init__(self, target_coverage: float = 0.80):
        """
        Args:
            target_coverage: Target empirical coverage (0.80 corresponds to P10-P90 range)
        """
        self.target_coverage = target_coverage

    def calibrate_intervals(self, point_forecast: np.ndarray,
                            historical_residuals: Optional[np.ndarray] = None,
                            historical_actuals: Optional[np.ndarray] = None,
                            rmse_estimate: Optional[float] = None,
                            historical_predictions: Optional[np.ndarray] = None,
                            residual_horizon: int = 12) -> Dict[str, Any]:
        """
        Generate calibrated lower / P50 / upper forecast intervals at `target_coverage`
        (0.80 -> P10/P90).

        Preferred method (split-conformal, level-scaled): out-of-sample backtest residuals
        e_i = actual_i - pred_i are scaled by the forecast level, r_i = e_i / (pred_i + c)
        with c = mean historical demand, so the band widens in peak season and narrows in
        the trough. Empirical lower/upper quantiles of r (with the finite-sample conformal
        correction) give  bound_h = f_h + q * (f_h + c).  Residuals already span forecast
        steps 1..`residual_horizon`; only steps beyond that are widened by sqrt(h / H).

        Args:
            point_forecast: 1D array of expected forecast values (P50 baseline)
            historical_residuals: 1D array of backtesting residuals (actual - predicted)
            historical_actuals: Optional 1D array of actual values (level scale c)
            rmse_estimate: Optional RMSE for the parametric fallback
            historical_predictions: backtest predictions aligned with the residuals
            residual_horizon: forecast horizon covered by the backtest residuals

        Returns:
            Dict containing p10, p50, p90 (lower / median / upper) arrays and coverage metadata.
        """
        point_forecast = np.maximum(0.0, np.asarray(point_forecast, dtype=float))
        horizon = len(point_forecast)
        alpha_lo = (1.0 - self.target_coverage) / 2.0
        steps = np.arange(1, horizon + 1)
        stretch = np.sqrt(np.maximum(1.0, steps / float(max(1, residual_horizon))))
        c = float(np.mean(historical_actuals)) if historical_actuals is not None and len(historical_actuals) else 1.0
        c = max(c, 1e-6)

        res = np.asarray(historical_residuals, dtype=float) if historical_residuals is not None else np.array([])
        preds = np.asarray(historical_predictions, dtype=float) if historical_predictions is not None else None
        ok = np.isfinite(res)
        if preds is not None and len(preds) == len(res):
            ok &= np.isfinite(preds)
        n_res = int(ok.sum())

        if n_res >= 8:
            if preds is not None and len(preds) == len(res):
                scores = res[ok] / (np.maximum(preds[ok], 0.0) + c)
                scale = (point_forecast + c) * stretch
                calibration_method = "split_conformal_level_scaled"
            else:
                scores = res[ok]
                scale = stretch
                calibration_method = "split_conformal_absolute"
            # Finite-sample conformal quantile levels
            lvl_lo = max(0.0, np.floor((n_res + 1) * alpha_lo) / n_res)
            lvl_hi = min(1.0, np.ceil((n_res + 1) * (1.0 - alpha_lo)) / n_res)
            q_lo, q_hi = float(np.quantile(scores, lvl_lo)), float(np.quantile(scores, lvl_hi))
            lower = point_forecast + min(q_lo, 0.0) * scale
            upper = point_forecast + max(q_hi, 0.0) * scale
            margin = float(np.mean(upper - lower) / 2.0)
            is_calibrated = True
        else:
            # Parametric fallback with explicit disclosure
            if rmse_estimate is not None and rmse_estimate > 0:
                sigma = float(rmse_estimate)
            elif historical_actuals is not None and len(historical_actuals) > 1:
                sigma = float(np.std(historical_actuals))
            else:
                sigma = float(np.mean(point_forecast) * 0.25) if np.mean(point_forecast) > 0 else 1.0
            from scipy.stats import norm
            margin = float(norm.ppf(1.0 - alpha_lo)) * sigma
            lower = point_forecast - margin * np.sqrt(steps / float(max(1, residual_horizon)))
            upper = point_forecast + margin * np.sqrt(steps / float(max(1, residual_horizon)))
            calibration_method = "normal_approximation_uncalibrated"
            is_calibrated = False

        p10 = np.maximum(0.0, lower)
        p50 = point_forecast
        p90 = np.maximum(p50, upper)

        return {
            'point_forecast': point_forecast,
            'p10': p10,
            'p50': p50,
            'p90': p90,
            'interval_width': p90 - p10,
            'mean_interval_width': float(np.mean(p90 - p10)),
            'target_coverage_pct': self.target_coverage * 100.0,
            'calibration_method': calibration_method,
            'is_calibrated': is_calibrated,
            'residuals_used': n_res,
            'margin': round(float(margin), 2),
            'note': (f"{self.target_coverage:.0%} interval from {n_res} out-of-sample backtest errors ({calibration_method})."
                     if is_calibrated else
                     f"{self.target_coverage:.0%} interval from a normal approximation (fewer than 8 backtest errors available).")
        }

    def verify_empirical_coverage(self, actuals: np.ndarray, 
                                  p10: np.ndarray, p90: np.ndarray) -> Dict[str, Any]:
        """
        Verify historical calibration coverage: % of actuals that fell inside [P10, P90].
        """
        act = np.asarray(actuals, dtype=float)
        p10_arr = np.asarray(p10, dtype=float)
        p90_arr = np.asarray(p90, dtype=float)
        
        mask = np.isfinite(act) & np.isfinite(p10_arr) & np.isfinite(p90_arr)
        if not np.any(mask):
            return {'coverage_pct': 0.0, 'is_well_calibrated': False}
            
        inside = (act[mask] >= p10_arr[mask]) & (act[mask] <= p90_arr[mask])
        coverage_pct = float(np.mean(inside) * 100.0)
        expected_pct = self.target_coverage * 100.0
        
        # Consider calibrated if within ±15% of target
        is_calibrated = abs(coverage_pct - expected_pct) <= 15.0

        return {
            'empirical_coverage_pct': round(coverage_pct, 1),
            'target_coverage_pct': expected_pct,
            'is_well_calibrated': is_calibrated,
            'points_evaluated': int(np.sum(mask))
        }
