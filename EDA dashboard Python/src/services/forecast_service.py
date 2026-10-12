"""
Canonical Production Forecast Service
Single source of truth orchestrating:
1. Demand Profiling & Classification
2. Model Selection & Walk-Forward Tournament
3. Champion Governance & Persistent Registry
4. Calibrated Conformal Prediction Intervals (P10/P50/P90)
5. Distribution-Driven Replenishment Policy & Stockout Estimation
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
import logging

from src.selection.model_selector import ModelSelector
from src.inventory.inventory_engine import InventoryEngine
from src.monitoring.registry import ModelRegistry
from src.monitoring.drift import DriftDetector
from src.monitoring.forecast_monitor import ForecastMonitor
from src.explainability.shap_analysis import ForecastExplainer

logger = logging.getLogger(__name__)


class ForecastService:
    """
    Central operational service consumed by all dashboard views, CLI runners, and pipelines.
    Guarantees that Demand Forecasting, Inventory Optimization, Monitoring, Scenarios,
    and Executive Action Queues share identical champion forecasts, uncertainty bounds,
    and governance state.
    """
    
    def __init__(self, data_df: Optional[pd.DataFrame] = None):
        self.df = data_df
        self.selector = ModelSelector()
        self.inv_engine = InventoryEngine()
        self.registry = ModelRegistry()
        self.monitor = ForecastMonitor()
        self.drift_detector = DriftDetector()
        self.explainer = ForecastExplainer()
        self._forecast_cache: Dict[str, Dict[str, Any]] = {}

    def set_data(self, df: pd.DataFrame):
        """Update dataset reference and clear ephemeral caches."""
        self.df = df
        self._forecast_cache.clear()

    def get_forecast(self, sku: str, branch: str, horizon: int = 12,
                     target_service_level: float = 0.95,
                     lead_time_weeks: int = 2,
                     current_on_hand: Optional[float] = None) -> Dict[str, Any]:
        """
        Produce a canonical end-to-end forecast package for a SKU x Branch.
        """
        cache_key = f"{sku}_{branch}_{horizon}_{target_service_level}_{lead_time_weeks}_{current_on_hand}"
        if cache_key in self._forecast_cache:
            return self._forecast_cache[cache_key]

        if self.df is None or self.df.empty:
            return {
                'status': 'INSUFFICIENT_DATA',
                'message': 'No dataset loaded into ForecastService.'
            }

        sku_col = next((c for c in ['sku', 'Material', 'material', 'Material Description'] if c in self.df.columns), None)
        branch_col = next((c for c in ['branch', 'SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Branch', 'Region'] if c in self.df.columns), None)
        
        if sku_col is None:
            return {'status': 'INSUFFICIENT_DATA', 'message': 'SKU column missing from data'}

        # Filter series
        if branch_col and branch:
            series_df = self.df[(self.df[sku_col].astype(str) == str(sku)) & (self.df[branch_col].astype(str) == str(branch))].copy()
        else:
            series_df = self.df[self.df[sku_col].astype(str) == str(sku)].copy()

        if len(series_df) < 4:
            return {
                'status': 'INSUFFICIENT_DATA',
                'sku': sku,
                'branch': branch,
                'message': f'Insufficient transaction history for {sku} ({len(series_df)} records, minimum 4 required).'
            }

        # Execute unified model selection and fitting
        res = self.selector.select_and_fit(self.df, sku=sku, branch=branch, horizon=horizon)
        if res.get('status') != 'success':
            return res

        # Derive replenishment policy strictly from the forecast error distribution
        residuals = res.get('historical_residuals')
        rmse_val = res.get('champion', {}).get('rmse', res.get('champion', {}).get('mean_rmse'))
        
        inv_policy = self.inv_engine.calculate_inventory_policy(
            forecast_values=res['p50'],
            historical_demand=res.get('historical_demand'),
            forecast_rmse=rmse_val,
            forecast_residuals=np.array(residuals) if residuals and len(residuals) >= 3 else None,
            lead_time_weeks=lead_time_weeks,
            target_service_level=target_service_level,
            current_on_hand=current_on_hand
        )

        # Health and Drift tracking against production champion
        hist_y = res.get('historical_demand', np.array([]))
        if len(hist_y) >= 4:
            drift_res = self.drift_detector.detect_demand_drift(hist_y, recent_window=min(8, max(4, len(hist_y) // 3)))
            health_res = self.monitor.evaluate_model_health(
                actuals=hist_y[-min(8, len(hist_y)):],
                forecasts=res['forecast'][:min(8, len(hist_y))],
                model_name=res['champion'].get('model_name', 'Champion')
            )
        else:
            drift_res = {'drift_detected': False, 'psi': 0.0, 'drift_status': 'Insufficient History', 'badge_color': 'green'}
            health_res = {'health_status': 'Healthy', 'tracking_signal': 0.0, 'badge_color': 'green', 'recommendation': 'Baseline operational'}

        output = {
            'status': 'success',
            'sku': sku,
            'branch': branch,
            'horizon': horizon,
            'demand_profile': res.get('demand_profile'),
            'champion': res.get('champion'),
            'challengers': res.get('challengers', []),
            'leaderboard': res.get('leaderboard'),
            'leaderboard_display': res.get('leaderboard_display'),
            'point_forecast': res.get('forecast'),
            'forward_forecast': res.get('forward_forecast'),
            'p10': res.get('p10'),
            'p50': res.get('p50'),
            'p90': res.get('p90'),
            'lower_bound': res.get('lower_bound'),
            'upper_bound': res.get('upper_bound'),
            'interval_calibration': res.get('interval_calibration'),
            'inventory_policy': inv_policy,
            'drift_analysis': drift_res,
            'model_health': health_res,
            'historical_dates': res.get('historical_dates'),
            'historical_demand': res.get('historical_demand'),
            'historical_residuals': residuals
        }
        self._forecast_cache[cache_key] = output
        return output
