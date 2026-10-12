"""
Baseline Forecasting Models
Simple baselines for comparison.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class NaiveForecaster:
    """Naive forecast - uses last value."""
    
    def __init__(self):
        self.last_value = None
    
    def fit(self, y: np.ndarray):
        """Fit by storing last value."""
        self.last_value = y[-1] if len(y) > 0 else 0
        return self
    
    def predict(self, periods: int = 1) -> np.ndarray:
        """Predict using last value."""
        return np.full(periods, self.last_value)


class SeasonalNaiveForecaster:
    """Seasonal naive - uses value from same period last year."""
    
    def __init__(self, seasonal_period: int = 52):
        """Initialize with seasonal period (default 52 weeks)."""
        self.seasonal_period = seasonal_period
        self.seasonal_values = None
    
    def fit(self, y: np.ndarray):
        """Fit by storing seasonal values."""
        if len(y) >= self.seasonal_period:
            self.seasonal_values = y[-self.seasonal_period:]
        else:
            self.seasonal_values = y
        return self
    
    def predict(self, periods: int = 1) -> np.ndarray:
        """Predict using seasonal pattern."""
        if self.seasonal_values is None:
            return np.zeros(periods)
        
        forecast = []
        for i in range(periods):
            idx = i % len(self.seasonal_values)
            forecast.append(self.seasonal_values[idx])
        
        return np.array(forecast)


class MovingAverageForecaster:
    """Simple moving average forecaster."""
    
    def __init__(self, window: int = 4):
        """Initialize with window size."""
        self.window = window
        self.mean_value = None
    
    def fit(self, y: np.ndarray):
        """Fit by computing average."""
        if len(y) >= self.window:
            self.mean_value = np.mean(y[-self.window:])
        else:
            self.mean_value = np.mean(y)
        return self
    
    def predict(self, periods: int = 1) -> np.ndarray:
        """Predict using mean."""
        return np.full(periods, self.mean_value)


class ExponentialSmoothingForecaster:
    """Simple exponential smoothing."""
    
    def __init__(self, alpha: float = 0.3):
        """Initialize with smoothing parameter."""
        self.alpha = alpha
        self.level = None
    
    def fit(self, y: np.ndarray):
        """Fit exponential smoothing."""
        self.level = y[-1] if len(y) > 0 else 0
        
        # Apply smoothing to learn level
        for value in y:
            self.level = self.alpha * value + (1 - self.alpha) * self.level
        
        return self
    
    def predict(self, periods: int = 1) -> np.ndarray:
        """Predict using learned level."""
        return np.full(periods, self.level)


class BaselineForecastingModels:
    """Wrapper for all baseline models."""
    
    def __init__(self):
        """Initialize all baseline models."""
        self.models = {
            'naive': NaiveForecaster(),
            'seasonal_naive': SeasonalNaiveForecaster(),
            'moving_average': MovingAverageForecaster(),
            'exponential_smoothing': ExponentialSmoothingForecaster(),
        }
    
    def fit_all(self, y: np.ndarray) -> Dict:
        """Fit all baseline models."""
        results = {}
        for name, model in self.models.items():
            try:
                model.fit(y)
                results[name] = {'status': 'success', 'model': model}
            except Exception as e:
                results[name] = {'status': 'failed', 'error': str(e)}
                logger.warning(f"Failed to fit {name}: {e}")
        
        return results
    
    def predict_all(self, periods: int = 12) -> Dict[str, np.ndarray]:
        """Get predictions from all baseline models."""
        forecasts = {}
        for name, model in self.models.items():
            try:
                forecast = model.predict(periods)
                forecasts[name] = forecast
            except Exception as e:
                logger.warning(f"Failed to predict with {name}: {e}")
                forecasts[name] = np.full(periods, np.nan)
        
        return forecasts
    
    def get_best_naive_forecast(self, y: np.ndarray, periods: int = 12, 
                                metric: str = 'mape') -> Tuple[str, np.ndarray]:
        """Select best naive model and return forecast.
        
        Args:
            y: Historical demand
            periods: Forecast horizon
            metric: 'mape', 'mae', or 'rmse'
        
        Returns:
            Tuple of (model_name, forecast_array)
        """
        self.fit_all(y)
        
        # For naive models, use simple heuristics
        # Seasonal naive works well for seasonal data
        if len(y) >= 52:
            # Likely has seasonality
            forecast = self.models['seasonal_naive'].predict(periods)
            return 'seasonal_naive', forecast
        else:
            # Use naive for limited history
            forecast = self.models['naive'].predict(periods)
            return 'naive', forecast
