"""
Forecast Monitor & Model Health Tracking Module
Monitors operational forecast tracking, cumulative error, tracking signals (TS),
and flags performance degradation with automated health state classifications.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from src.validation.metrics import calculate_wape, calculate_mae, calculate_rmse, calculate_bias


class ForecastMonitor:
    """
    Monitors live forecast performance against actual sales velocity.
    """
    
    # Standard APICS Tracking Signal Thresholds
    TS_HEALTHY_MAX = 4.0
    TS_WATCH_MAX = 6.0
    
    WAPE_HEALTHY_MAX = 25.0
    WAPE_WATCH_MAX = 35.0

    def evaluate_model_health(self, actuals: np.ndarray, 
                              forecasts: np.ndarray,
                              model_name: str = "Champion Model") -> Dict[str, Any]:
        """
        Evaluate forecast tracking signal and health status over time.
        
        Args:
            actuals: Array of realized historical actual demands
            forecasts: Array of corresponding generated forecasts
            model_name: Name of evaluated model
        """
        y = np.asarray(actuals, dtype=float)
        y_hat = np.asarray(forecasts, dtype=float)
        
        mask = np.isfinite(y) & np.isfinite(y_hat)
        if not np.any(mask) or len(y[mask]) < 2:
            return {
                'health_status': 'Healthy',
                'tracking_signal': 0.0,
                'status_color': 'green',
                'recommendation': 'Insufficient live telemetry; monitoring initialized.'
            }

        yt = y[mask]
        yh = y_hat[mask]
        errors = yh - yt  # signed error (positive = over-forecast)
        abs_errors = np.abs(errors)
        
        cumulative_error = float(np.sum(errors))
        mad = float(np.mean(abs_errors))
        
        # Tracking Signal = Cumulative Error / MAD
        tracking_signal = float(cumulative_error / mad) if mad > 1e-4 else 0.0
        abs_ts = abs(tracking_signal)
        
        wape = calculate_wape(yt, yh)
        rmse = calculate_rmse(yt, yh)
        bias = calculate_bias(yt, yh)
        
        # Determine Health State
        if abs_ts <= self.TS_HEALTHY_MAX and wape <= self.WAPE_HEALTHY_MAX:
            health_status = "Healthy"
            badge_color = "green"
            rec = f"Model '{model_name}' is performing within statistical control limits (WAPE: {wape:.1f}%, TS: {tracking_signal:+.2f})."
        elif abs_ts <= self.TS_WATCH_MAX and wape <= self.WAPE_WATCH_MAX:
            health_status = "Watch"
            badge_color = "amber"
            rec = f"Model '{model_name}' exhibits mild tracking bias (TS: {tracking_signal:+.2f}, WAPE: {wape:.1f}%). Monitor closely next cycle."
        else:
            health_status = "Retrain Required"
            badge_color = "rose"
            rec = f"Model '{model_name}' has breached operational thresholds (TS: {tracking_signal:+.2f}, WAPE: {wape:.1f}%). Immediate retraining recommended."

        # Compute period-by-period tracking signal trajectory
        ts_trajectory = []
        running_sum_err = 0.0
        for i in range(len(errors)):
            running_sum_err += errors[i]
            cur_mad = np.mean(abs_errors[:i + 1])
            cur_ts = float(running_sum_err / cur_mad) if cur_mad > 1e-4 else 0.0
            ts_trajectory.append(round(cur_ts, 2))

        return {
            'model_name': model_name,
            'health_status': health_status,
            'badge_color': badge_color,
            'tracking_signal': round(tracking_signal, 2),
            'wape': round(wape, 2),
            'rmse': round(rmse, 2),
            'bias': round(bias, 2),
            'cumulative_error': round(cumulative_error, 1),
            'mad': round(mad, 2),
            'recommendation': rec,
            'ts_trajectory': ts_trajectory,
            'n_periods_evaluated': int(len(yt))
        }
