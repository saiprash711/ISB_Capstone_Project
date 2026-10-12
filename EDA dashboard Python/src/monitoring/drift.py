"""
Data & Concept Drift Detection Module
Measures distribution drift between reference training window and recent operational window
using Population Stability Index (PSI) and the two-sample Kolmogorov-Smirnov test.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Any, Optional


class DriftDetector:
    """
    Detects demand distribution shift and SKU mix drift.
    """
    
    # PSI Standard Thresholds:
    # PSI < 0.10: No significant change
    # 0.10 <= PSI < 0.25: Moderate shift (Monitor / Watch)
    # PSI >= 0.25: Significant shift (Drift Confirmed / Action Required)
    PSI_NO_CHANGE = 0.10
    PSI_MODERATE = 0.25

    def calculate_psi(self, reference: np.ndarray, current: np.ndarray, num_bins: int = 5) -> float:
        """
        Compute Population Stability Index (PSI) between reference and current samples.
        """
        ref = np.asarray(reference, dtype=float)
        cur = np.asarray(current, dtype=float)
        
        ref = ref[np.isfinite(ref)]
        cur = cur[np.isfinite(cur)]
        
        if len(ref) < 4 or len(cur) < 4:
            return 0.0

        # Create quantile-based bins from reference distribution
        quantiles = np.linspace(0, 100, num_bins + 1)
        bin_edges = np.percentile(ref, quantiles)
        bin_edges[0] -= 1e-5
        bin_edges[-1] += 1e-5
        bin_edges = np.unique(bin_edges)
        
        if len(bin_edges) < 2:
            return 0.0

        ref_counts, _ = np.histogram(ref, bins=bin_edges)
        cur_counts, _ = np.histogram(cur, bins=bin_edges)

        # Convert to percentages with epsilon smoothing to prevent div-by-zero
        eps = 1e-4
        ref_pct = (ref_counts + eps) / (len(ref) + eps * len(ref_counts))
        cur_pct = (cur_counts + eps) / (len(cur) + eps * len(cur_counts))

        psi_val = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(max(0.0, psi_val))

    def detect_demand_drift(self, full_series: np.ndarray, 
                            recent_window: int = 8) -> Dict[str, Any]:
        """
        Detect whether recent demand distribution has drifted significantly from historical baseline.
        
        Args:
            full_series: Entire time series array
            recent_window: Number of recent weeks to compare as 'current'
        """
        y = np.asarray(full_series, dtype=float)
        n = len(y)
        
        if n < recent_window + 8:
            return {
                'drift_detected': False,
                'drift_status': 'Stable',
                'badge_color': 'green',
                'psi': 0.0,
                'ks_p_value': 1.0,
                'message': 'Insufficient data points to evaluate distribution drift.'
            }

        ref_data = y[:-recent_window]
        cur_data = y[-recent_window:]

        # 1. Population Stability Index (PSI)
        psi = self.calculate_psi(ref_data, cur_data)
        
        # 2. Kolmogorov-Smirnov Two-Sample Test
        ks_res = stats.ks_2samp(ref_data, cur_data)
        ks_stat = float(ks_res.statistic)
        ks_p_val = float(ks_res.pvalue)

        # 3. Mean & Volatility Shift
        ref_mean = float(np.mean(ref_data))
        cur_mean = float(np.mean(cur_data))
        mean_shift_pct = ((cur_mean - ref_mean) / ref_mean * 100.0) if ref_mean > 0 else 0.0

        ref_zero = float(np.mean(ref_data == 0) * 100.0)
        cur_zero = float(np.mean(cur_data == 0) * 100.0)

        # Status categorization
        if psi >= self.PSI_MODERATE or (ks_p_val < 0.05 and abs(mean_shift_pct) > 25.0):
            drift_detected = True
            drift_status = "Drift Detected"
            badge_color = "rose"
            action = f"Significant demand distribution shift (PSI: {psi:.3f}, Mean Shift: {mean_shift_pct:+.1f}%). Trigger model retraining."
        elif psi >= self.PSI_NO_CHANGE or ks_p_val < 0.10:
            drift_detected = False
            drift_status = "Mild Shift (Watch)"
            badge_color = "amber"
            action = f"Moderate distribution variance (PSI: {psi:.3f}, Mean Shift: {mean_shift_pct:+.1f}%). Continue monitoring."
        else:
            drift_detected = False
            drift_status = "Stable Distribution"
            badge_color = "green"
            action = f"Distribution remains stable (PSI: {psi:.3f}, KS p-value: {ks_p_val:.2f}). No drift."

        return {
            'drift_detected': drift_detected,
            'drift_status': drift_status,
            'badge_color': badge_color,
            'psi': round(psi, 3),
            'ks_statistic': round(ks_stat, 3),
            'ks_p_value': round(ks_p_val, 3),
            'ref_mean': round(ref_mean, 1),
            'cur_mean': round(cur_mean, 1),
            'mean_shift_pct': round(mean_shift_pct, 1),
            'ref_zero_pct': round(ref_zero, 1),
            'cur_zero_pct': round(cur_zero, 1),
            'action_recommendation': action
        }
