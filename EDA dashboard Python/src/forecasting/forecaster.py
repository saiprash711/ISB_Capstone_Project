"""
Forecasting Orchestrator
Coordinates all forecasting models and provides unified interface.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

from .baseline import BaselineForecastingModels
from .statistical import StatisticalModels
from .intermittent import IntermittentDemandModels
from .ml_models import MLModels
from src.features import FeatureEngineer

logger = logging.getLogger(__name__)


class ForecastingEngine:
    """Unified forecasting engine combining multiple model families."""
    
    def __init__(self, config: Dict = None):
        """Initialize forecasting engine with config."""
        self.config = config or {}
        self.forecast_horizon = self.config.get('forecast_horizon', 12)
        self.confidence_level = self.config.get('confidence_level', 0.95)
        
        # Initialize model families
        self.baseline_models = BaselineForecastingModels()
        self.statistical_models = StatisticalModels()
        self.intermittent_models = IntermittentDemandModels()
        self.ml_models = MLModels()
        
        # Feature engineer
        self.feature_engineer = FeatureEngineer(config)
        
        # Results storage
        self.last_forecast_results = None
        self.last_fit_stats = None
    
    def fit_and_forecast(self, df: pd.DataFrame, sku: str, branch: str, 
                        periods: Optional[int] = None) -> Dict:
        """Fit all models and generate forecasts for specific SKU × Branch.
        
        Args:
            df: Data mart with SKU × BRANCH × WEEK grain
            sku: Product SKU
            branch: Branch code
            periods: Forecast horizon (default from config)
        
        Returns:
            Dictionary with forecasts from all model families
        """
        periods = periods or self.forecast_horizon
        
        # Filter data for specific SKU and branch
        sku_data = df[(df['sku'] == sku) & (df['branch'] == branch)].copy()
        
        if len(sku_data) < 3:
            logger.warning(f"Insufficient data for {sku}/{branch}: {len(sku_data)} rows")
            return {'error': 'Insufficient data', 'sku': sku, 'branch': branch}
        
        # Sort by date and extract demand
        sku_data = sku_data.sort_values('date')
        y = sku_data['total_demand'].values
        dates = sku_data['date'].values
        
        # Store for diagnostics
        fit_stats = {
            'sku': sku,
            'branch': branch,
            'n_observations': len(y),
            'demand_mean': np.mean(y),
            'demand_std': np.std(y),
            'zero_count': np.sum(y == 0),
            'date_range': f"{dates[0]} to {dates[-1]}"
        }
        
        forecasts = {
            'sku': sku,
            'branch': branch,
            'horizon': periods,
            'fit_stats': fit_stats,
            'models': {}
        }
        
        # Fit baseline models
        try:
            self.baseline_models.fit_all(y)
            baseline_pred = self.baseline_models.predict_all(periods)
            forecasts['models']['baseline'] = baseline_pred
            logger.info(f"Baseline models fitted for {sku}/{branch}")
        except Exception as e:
            logger.warning(f"Baseline models failed: {e}")
            forecasts['models']['baseline'] = {}
        
        # Fit statistical models
        try:
            self.statistical_models.fit_all(y)
            statistical_pred = self.statistical_models.predict_all(periods)
            forecasts['models']['statistical'] = statistical_pred
            logger.info(f"Statistical models fitted for {sku}/{branch}")
        except Exception as e:
            logger.warning(f"Statistical models failed: {e}")
            forecasts['models']['statistical'] = {}
        
        # Fit intermittent models (if applicable)
        try:
            if self.intermittent_models.is_intermittent(y):
                self.intermittent_models.fit_all(y)
                intermittent_pred = self.intermittent_models.predict_all(periods)
                forecasts['models']['intermittent'] = intermittent_pred
                forecasts['fit_stats']['demand_type'] = 'intermittent'
                logger.info(f"Intermittent models fitted for {sku}/{branch}")
            else:
                forecasts['fit_stats']['demand_type'] = 'regular'
        except Exception as e:
            logger.warning(f"Intermittent models failed: {e}")
            forecasts['models']['intermittent'] = {}
        
        # Fit ML models (if sufficient data)
        if len(y) >= 30:
            try:
                # Engineer features
                X, feature_cols = self._prepare_ml_data(sku_data, y)
                
                if X.shape[0] > 10:
                    self.ml_models.fit_all(X, y)
                    ml_predictions = self._forecast_ml(X[-1:], feature_cols, periods)
                    forecasts['models']['ml'] = ml_predictions
                    logger.info(f"ML models fitted for {sku}/{branch}")
            except Exception as e:
                logger.warning(f"ML models failed: {e}")
                forecasts['models']['ml'] = {}
        
        self.last_forecast_results = forecasts
        self.last_fit_stats = fit_stats
        
        return forecasts
    
    def _prepare_ml_data(self, sku_data: pd.DataFrame, y: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Prepare feature matrix for ML models."""
        # Engineer features
        X_df, feature_cols = self.feature_engineer.engineer_features(sku_data)
        
        # Select numeric feature columns only
        numeric_features = []
        for col in feature_cols:
            if col in X_df.columns:
                X_df[col] = pd.to_numeric(X_df[col], errors='coerce')
                median_val = X_df[col].median()
                if pd.isna(median_val):
                    median_val = 0.0
                X_df[col] = X_df[col].fillna(median_val)
                numeric_features.append(col)
        
        available_features = numeric_features
        if not available_features:
            # Use basic lags if no features available
            y_series = pd.Series(y)
            X_df['lag_1'] = y_series.shift(1).bfill().fillna(0)
            X_df['lag_4'] = y_series.shift(4).bfill().fillna(0)
            X_df['lag_12'] = y_series.shift(12).bfill().fillna(0)
            available_features = ['lag_1', 'lag_4', 'lag_12']
        
        X_data = X_df[available_features].to_numpy(dtype=np.float32)
        X_data[~np.isfinite(X_data)] = 0.0
        return X_data, available_features
    
    def _forecast_ml(self, X_last: np.ndarray, feature_cols: List[str], periods: int) -> Dict:
        """Generate ML forecasts using step-ahead autoregressive projection."""
        ml_forecasts = {}
        
        for model_name, model in self.ml_models.models.items():
            try:
                cur_feat = X_last.copy()
                preds = []
                for _ in range(periods):
                    p = float(model.predict(cur_feat)[0])
                    p = max(0.0, float(np.nan_to_num(p, nan=0.0)))
                    preds.append(p)
                    # Update lag_1 feature for next recursive step if present
                    if 'lag_1' in feature_cols:
                        idx = feature_cols.index('lag_1')
                        cur_feat[0, idx] = p
                ml_forecasts[model_name] = np.array(preds)
            except Exception as e:
                logger.warning(f"ML forecast failed for {model_name}: {e}")
                ml_forecasts[model_name] = np.full(periods, np.nan)
        
        return ml_forecasts
    
    def get_ensemble_forecast(self, forecasts: Dict, method: str = 'mean') -> np.ndarray:
        """Generate ensemble forecast from multiple models.
        
        Args:
            forecasts: Dictionary of forecasts from fit_and_forecast
            method: 'mean', 'median', or 'weighted'
        
        Returns:
            Ensemble forecast array
        """
        all_forecasts = []
        
        # Collect all forecasts
        for model_family, predictions in forecasts.get('models', {}).items():
            if isinstance(predictions, dict):
                for model_name, forecast in predictions.items():
                    if isinstance(forecast, np.ndarray) and not np.all(np.isnan(forecast)):
                        all_forecasts.append(forecast)
            elif isinstance(predictions, np.ndarray):
                if not np.all(np.isnan(predictions)):
                    all_forecasts.append(predictions)
        
        if not all_forecasts:
            return np.full(self.forecast_horizon, np.nan)
        
        # Stack forecasts
        forecast_matrix = np.column_stack(all_forecasts)
        
        # Calculate ensemble
        if method == 'mean':
            ensemble = np.nanmean(forecast_matrix, axis=1)
        elif method == 'median':
            ensemble = np.nanmedian(forecast_matrix, axis=1)
        elif method == 'weighted':
            # Simple weighted average (equal weights for now)
            weights = np.ones(forecast_matrix.shape[1]) / forecast_matrix.shape[1]
            ensemble = np.nanmean(forecast_matrix * weights, axis=1)
        else:
            ensemble = np.nanmean(forecast_matrix, axis=1)
        
        return ensemble
    
    def forecast_batch(self, df: pd.DataFrame, sku_list: List[str] = None,
                       branch_list: List[str] = None) -> List[Dict]:
        """Generate forecasts for multiple SKU × Branch combinations.
        
        Args:
            df: Data mart
            sku_list: List of SKUs (default: all unique)
            branch_list: List of branches (default: all unique)
        
        Returns:
            List of forecast dictionaries
        """
        if sku_list is None:
            sku_list = df['sku'].unique()
        if branch_list is None:
            branch_list = df['branch'].unique()
        
        results = []
        total = len(sku_list) * len(branch_list)
        processed = 0
        
        for sku in sku_list:
            for branch in branch_list:
                try:
                    forecast = self.fit_and_forecast(df, sku, branch)
                    if 'error' not in forecast:
                        results.append(forecast)
                except Exception as e:
                    logger.warning(f"Batch forecast failed for {sku}/{branch}: {e}")
                
                processed += 1
                if processed % 100 == 0:
                    logger.info(f"Processed {processed}/{total} SKU×Branch combinations")
        
        logger.info(f"Batch forecasting complete. Generated {len(results)} forecasts.")
        return results
    
    def export_forecasts(self, forecasts: List[Dict], output_format: str = 'csv') -> pd.DataFrame:
        """Export forecasts to DataFrame format.
        
        Args:
            forecasts: List of forecast dictionaries
            output_format: 'csv', 'long', or 'wide'
        
        Returns:
            DataFrame with forecasts
        """
        rows = []
        
        for forecast in forecasts:
            if 'error' in forecast:
                continue
            
            sku = forecast['sku']
            branch = forecast['branch']
            horizon = forecast['horizon']
            
            # Get ensemble forecast
            ensemble = self.get_ensemble_forecast(forecast)
            
            # Create rows
            for period in range(horizon):
                row = {
                    'sku': sku,
                    'branch': branch,
                    'forecast_period': period + 1,
                    'forecast_value': ensemble[period] if not np.isnan(ensemble[period]) else 0,
                }
                rows.append(row)
        
        return pd.DataFrame(rows)
