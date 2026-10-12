"""
Demand Profiler and Pattern Classification Engine
Implements the Syntetos-Boylan / Kostenko-Hyndman quadrant classification
along with trend, seasonality, and intermittency analytics.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional


class DemandClassifier:
    """
    Classifies SKU-level demand patterns to dynamically route to candidate models.
    """
    
    # Syntetos-Boylan classification thresholds
    ADI_THRESHOLD = 1.32
    CV2_THRESHOLD = 0.49
    
    def __init__(self, adi_threshold: float = 1.32, cv2_threshold: float = 0.49):
        self.adi_threshold = adi_threshold
        self.cv2_threshold = cv2_threshold

    def profile_demand(self, y: np.ndarray, dates: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Compute statistical profiling metrics on a demand series.
        """
        y = np.asarray(y, dtype=float)
        n = len(y)
        if n == 0:
            return {'status': 'empty'}
            
        non_zero_mask = y > 0
        non_zero_demand = y[non_zero_mask]
        n_non_zero = len(non_zero_demand)
        zero_pct = float((n - n_non_zero) / n * 100.0)
        
        mean_demand = float(np.mean(y))
        median_demand = float(np.median(y))
        std_demand = float(np.std(y))
        volatility = float(std_demand / mean_demand) if mean_demand > 0 else 0.0
        
        # Syntetos-Boylan ADI & CV^2
        if n_non_zero > 1:
            adi = float(n / n_non_zero)
            nz_mean = np.mean(non_zero_demand)
            nz_std = np.std(non_zero_demand)
            cv2 = float((nz_std / nz_mean) ** 2) if nz_mean > 0 else 0.0
        else:
            adi = float(n) if n > 0 else 999.0
            cv2 = 1.0

        # Trend detection via simple linear regression slope
        t = np.arange(n)
        if n >= 4 and np.std(t) > 0:
            cov = np.cov(t, y)[0, 1]
            var_t = np.var(t)
            trend_slope = float(cov / var_t) if var_t > 0 else 0.0
            # Normalized slope relative to mean
            trend_strength = float(trend_slope / mean_demand) if mean_demand > 0 else 0.0
        else:
            trend_slope = 0.0
            trend_strength = 0.0

        # Seasonality detection via auto-correlation
        seasonal_strength = 0.0
        has_52w_seasonality = False
        has_12w_seasonality = False
        
        if n >= 24:
            # Check 12-week or quarterly seasonality
            lag_12 = 12
            y_diff = y - mean_demand
            var_y = np.var(y)
            if var_y > 1e-6:
                autocorr_12 = np.corrcoef(y[:-lag_12], y[lag_12:])[0, 1]
                if np.isfinite(autocorr_12) and autocorr_12 > 0.3:
                    has_12w_seasonality = True
                    seasonal_strength = max(seasonal_strength, float(autocorr_12))
                    
        if n >= 60:
            # Check 52-week annual seasonality
            lag_52 = 52
            autocorr_52 = np.corrcoef(y[:-lag_52], y[lag_52:])[0, 1]
            if np.isfinite(autocorr_52) and autocorr_52 > 0.3:
                has_52w_seasonality = True
                seasonal_strength = max(seasonal_strength, float(autocorr_52))

        # Demand Quadrant Determination
        if adi < self.adi_threshold:
            base_category = "Smooth" if cv2 < self.cv2_threshold else "Erratic"
        else:
            base_category = "Intermittent" if cv2 < self.cv2_threshold else "Lumpy"

        # Refine with temporal dynamics
        has_trend = abs(trend_strength) > 0.015 and n >= 12
        has_seasonality = (has_52w_seasonality or has_12w_seasonality)

        if base_category in ["Smooth", "Erratic"]:
            if has_seasonality and has_trend:
                primary_class = "Seasonal + Trending"
            elif has_seasonality:
                primary_class = "Seasonal"
            elif has_trend:
                primary_class = "Trending"
            else:
                primary_class = base_category
        else:
            primary_class = base_category  # Intermittent or Lumpy dominates

        # Recommend candidate models based on classification
        candidate_models = self._recommend_candidate_models(
            primary_class, n_history=n, is_intermittent=(zero_pct > 30.0 or adi >= self.adi_threshold)
        )

        return {
            'demand_type': primary_class,
            'base_quadrant': base_category,
            'mean_demand': round(mean_demand, 2),
            'median_demand': round(median_demand, 2),
            'std_demand': round(std_demand, 2),
            'volatility_cv': round(volatility, 2),
            'zero_demand_pct': round(zero_pct, 1),
            'adi': round(adi, 2),
            'cv2': round(cv2, 2),
            'trend_slope': round(trend_slope, 3),
            'trend_strength': round(trend_strength, 4),
            'seasonal_strength': round(seasonal_strength, 2),
            'has_trend': has_trend,
            'has_seasonality': has_seasonality,
            'candidate_models': candidate_models,
            'description': self._get_class_description(primary_class)
        }

    def _recommend_candidate_models(self, demand_type: str, n_history: int, 
                                   is_intermittent: bool) -> List[str]:
        """
        Dynamically map classified demand type to candidate model architectures.
        """
        candidates = ['Naive', 'Moving Average', 'Exponential Smoothing']
        
        if demand_type in ['Intermittent', 'Lumpy'] or is_intermittent:
            candidates.extend(['Croston', 'SBA', 'TSB'])
            if n_history >= 30:
                candidates.extend(['Random Forest'])
            return candidates

        if 'Seasonal' in demand_type:
            candidates.append('Seasonal Naive')
            if n_history >= 24:
                candidates.append('SARIMA')
            candidates.append('ETS')
            if n_history >= 30:
                candidates.extend(['Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM'])
            return candidates

        if demand_type == 'Trending':
            candidates.extend(['ARIMA', 'ETS'])
            if n_history >= 30:
                candidates.extend(['Random Forest', 'Gradient Boosting', 'XGBoost'])
            return candidates

        # Default Smooth / Erratic
        candidates.extend(['ARIMA', 'ETS'])
        if n_history >= 30:
            candidates.extend(['Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM'])
            
        return candidates

    def _get_class_description(self, demand_type: str) -> str:
        descriptions = {
            'Smooth': 'Regular frequency (ADI < 1.32) with low variance (CV² < 0.49). Highly forecastable using statistical & ML models.',
            'Erratic': 'Regular order frequency with high volume variance (CV² ≥ 0.49). Benefits from tree-based ensembles and smoothing.',
            'Intermittent': 'Sporadic demand gaps (ADI ≥ 1.32) with relatively consistent drop sizes (CV² < 0.49). Modeled via Croston/SBA.',
            'Lumpy': 'Sporadic demand gaps (ADI ≥ 1.32) with volatile quantities (CV² ≥ 0.49). Complex intermittent profile, handled via TSB/SBA.',
            'Seasonal': 'Significant cyclical recurrence across quarterly or annual cycles. Modeled via SARIMA, ETS, and temporal features.',
            'Trending': 'Statistically significant directional demand drift. Modeled via ARIMA drift, ETS trend, and autoregressive lags.',
            'Seasonal + Trending': 'Dual temporal dynamics with compounding cyclicality and trajectory. Requires SARIMA and ML regression.'
        }
        return descriptions.get(demand_type, 'Standard demand series.')
