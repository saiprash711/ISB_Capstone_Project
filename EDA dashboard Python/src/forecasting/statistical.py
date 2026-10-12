"""
Statistical Forecasting Models
ARIMA, SARIMA, and Exponential Smoothing models.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional
import logging
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing

logger = logging.getLogger(__name__)


class ARIMAModel:
    """ARIMA forecasting model."""
    
    def __init__(self, order: Tuple = (1, 1, 1), auto: bool = True):
        """Initialize ARIMA with optional auto order selection."""
        self.order = order
        self.auto = auto
        self.model = None
        self.fitted_model = None
    
    def fit(self, y: np.ndarray) -> Dict:
        """Fit ARIMA model."""
        if len(y) < 3:
            return {'status': 'failed', 'error': 'Insufficient data'}
        
        try:
            if self.auto:
                # Auto-select order using AIC
                best_aic = np.inf
                best_order = (0, 0, 0)
                
                for p in range(3):
                    for d in range(2):
                        for q in range(3):
                            try:
                                model = ARIMA(y, order=(p, d, q))
                                fitted = model.fit()
                                if fitted.aic < best_aic:
                                    best_aic = fitted.aic
                                    best_order = (p, d, q)
                                    self.fitted_model = fitted
                            except:
                                pass
                
                self.order = best_order
                return {'status': 'success', 'order': best_order, 'aic': best_aic}
            else:
                # Use specified order
                model = ARIMA(y, order=self.order)
                self.fitted_model = model.fit()
                return {'status': 'success', 'order': self.order}
        
        except Exception as e:
            logger.warning(f"ARIMA fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, periods: int = 12) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get forecast with confidence intervals."""
        if self.fitted_model is None:
            return np.full(periods, np.nan), np.full(periods, np.nan), np.full(periods, np.nan)
        
        try:
            forecast = self.fitted_model.get_forecast(steps=periods)
            pred_df = forecast.conf_int(alpha=0.05)
            
            # Handle both Series and ndarray
            pred_mean_obj = forecast.predicted_mean
            if hasattr(pred_mean_obj, 'values'):
                pred_mean = pred_mean_obj.values
            else:
                pred_mean = np.asarray(pred_mean_obj)
            
            if hasattr(pred_df, 'iloc'):
                pred_lower = pred_df.iloc[:, 0].values
                pred_upper = pred_df.iloc[:, 1].values
            else:
                pred_lower = np.asarray(pred_df)[:, 0]
                pred_upper = np.asarray(pred_df)[:, 1]
            return pred_mean, pred_lower, pred_upper
        except Exception as e:
            logger.warning(f"ARIMA prediction failed: {e}")
            return np.full(periods, np.nan), np.full(periods, np.nan), np.full(periods, np.nan)


class SARIMAModel:
    """SARIMA forecasting model with seasonality."""
    
    def __init__(self, order: Tuple = (1, 1, 1), seasonal_order: Tuple = (0, 1, 1, 12)):
        """Initialize SARIMA with order and seasonal order."""
        self.order = order
        self.seasonal_order = seasonal_order
        self.fitted_model = None
    
    def fit(self, y: np.ndarray) -> Dict:
        """Fit SARIMA model."""
        if len(y) < 2 * self.seasonal_order[3]:
            return {'status': 'failed', 'error': 'Insufficient data for seasonality'}
        
        try:
            model = SARIMAX(y, order=self.order, seasonal_order=self.seasonal_order)
            self.fitted_model = model.fit(disp=False)
            return {'status': 'success', 'order': self.order, 'seasonal_order': self.seasonal_order}
        except Exception as e:
            logger.warning(f"SARIMA fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, periods: int = 12) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get forecast with confidence intervals."""
        if self.fitted_model is None:
            return np.full(periods, np.nan), np.full(periods, np.nan), np.full(periods, np.nan)
        
        try:
            forecast = self.fitted_model.get_forecast(steps=periods)
            pred_df = forecast.conf_int(alpha=0.05)
            
            # Handle both Series and ndarray
            pred_mean_obj = forecast.predicted_mean
            if hasattr(pred_mean_obj, 'values'):
                pred_mean = pred_mean_obj.values
            else:
                pred_mean = np.asarray(pred_mean_obj)
            
            if hasattr(pred_df, 'iloc'):
                pred_lower = pred_df.iloc[:, 0].values
                pred_upper = pred_df.iloc[:, 1].values
            else:
                pred_lower = np.asarray(pred_df)[:, 0]
                pred_upper = np.asarray(pred_df)[:, 1]
            return pred_mean, pred_lower, pred_upper
        except Exception as e:
            logger.warning(f"SARIMA prediction failed: {e}")
            return np.full(periods, np.nan), np.full(periods, np.nan), np.full(periods, np.nan)


class ETSModel:
    """Exponential Smoothing (ETS) model."""
    
    def __init__(self, error: str = 'add', trend: str = 'add', seasonal: str = 'add', 
                 seasonal_periods: int = 52):
        """Initialize ETS model.
        
        Args:
            error: 'add' or 'mul' for additive/multiplicative error
            trend: 'add', 'mul', or None
            seasonal: 'add', 'mul', or None
            seasonal_periods: Number of periods in season
        """
        self.error = error
        self.trend = trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods
        self.fitted_model = None
    
    def fit(self, y: np.ndarray) -> Dict:
        """Fit ETS model."""
        if len(y) < 2 * self.seasonal_periods:
            return {'status': 'failed', 'error': 'Insufficient data for seasonality'}
        
        try:
            # Ensure no negative values
            if (y < 0).any():
                return {'status': 'failed', 'error': 'Cannot fit with negative values'}
            
            model = ExponentialSmoothing(
                y,
                error_type=self.error,
                trend=self.trend,
                seasonal=self.seasonal,
                seasonal_periods=self.seasonal_periods
            )
            self.fitted_model = model.fit(optimized=True)
            return {'status': 'success', 'aic': self.fitted_model.aic}
        except Exception as e:
            logger.warning(f"ETS fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, periods: int = 12) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get forecast with confidence intervals."""
        if self.fitted_model is None:
            return np.full(periods, np.nan), np.full(periods, np.nan), np.full(periods, np.nan)
        
        try:
            pred_mean = self.fitted_model.forecast(steps=periods).values
            # Simple confidence intervals (±1 std)
            residuals = self.fitted_model.resid
            std = np.std(residuals)
            pred_lower = pred_mean - 1.96 * std
            pred_upper = pred_mean + 1.96 * std
            return pred_mean, pred_lower, pred_upper
        except Exception as e:
            logger.warning(f"ETS prediction failed: {e}")
            return np.full(periods, np.nan), np.full(periods, np.nan), np.full(periods, np.nan)


class StatisticalModels:
    """Wrapper for statistical forecasting models."""
    
    def __init__(self):
        """Initialize all statistical models."""
        self.models = {
            'arima': ARIMAModel(),
            'sarima': SARIMAModel(),
            'ets': ETSModel(),
        }
    
    def fit_all(self, y: np.ndarray) -> Dict:
        """Fit all statistical models."""
        results = {}
        for name, model in self.models.items():
            try:
                result = model.fit(y)
                results[name] = result
            except Exception as e:
                results[name] = {'status': 'failed', 'error': str(e)}
                logger.warning(f"Failed to fit {name}: {e}")
        
        return results
    
    def predict_all(self, periods: int = 12) -> Dict[str, Dict[str, np.ndarray]]:
        """Get predictions from all statistical models."""
        forecasts = {}
        for name, model in self.models.items():
            try:
                pred_mean, pred_lower, pred_upper = model.predict(periods)
                forecasts[name] = {
                    'forecast': pred_mean,
                    'lower': pred_lower,
                    'upper': pred_upper
                }
            except Exception as e:
                logger.warning(f"Failed to predict with {name}: {e}")
                forecasts[name] = {
                    'forecast': np.full(periods, np.nan),
                    'lower': np.full(periods, np.nan),
                    'upper': np.full(periods, np.nan)
                }
        
        return forecasts
