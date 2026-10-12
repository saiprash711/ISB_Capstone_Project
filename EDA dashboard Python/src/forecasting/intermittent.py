"""
Intermittent Demand Forecasting Models
Croston, SBA (Syntetos-Boylan), and TSB (Teunter-Syntetos-Babai).
"""
import numpy as np
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class CrostonModel:
    """Croston's method for intermittent demand."""
    
    def __init__(self, alpha: float = 0.1):
        """Initialize Croston's method.
        
        Args:
            alpha: Smoothing parameter (0-1)
        """
        self.alpha = alpha
        self.level = None
        self.interval = None
    
    def fit(self, y: np.ndarray) -> Dict:
        """Fit Croston's model."""
        if len(y) < 2:
            return {'status': 'failed', 'error': 'Insufficient data'}
        
        try:
            # Non-zero values and their intervals
            nonzero_mask = y != 0
            nonzero_values = y[nonzero_mask]
            nonzero_positions = np.where(nonzero_mask)[0]
            
            if len(nonzero_values) < 2:
                return {'status': 'failed', 'error': 'Insufficient non-zero values'}
            
            # Initialize with first non-zero value
            self.level = nonzero_values[0]
            
            # Calculate intervals between demands
            intervals = np.diff(nonzero_positions)
            self.interval = np.mean(intervals)
            
            # Smooth the level using remaining values
            for value in nonzero_values[1:]:
                self.level = self.alpha * value + (1 - self.alpha) * self.level
            
            return {'status': 'success', 'level': self.level, 'interval': self.interval}
        
        except Exception as e:
            logger.warning(f"Croston fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, periods: int = 12) -> np.ndarray:
        """Get forecast using Croston's method."""
        if self.level is None or self.interval is None:
            return np.zeros(periods)
        
        # Croston: forecast = level / interval
        forecast_value = self.level / max(self.interval, 1)
        return np.full(periods, forecast_value)


class SBAModel:
    """Syntetos-Boylan Approximation for intermittent demand."""
    
    def __init__(self, alpha: float = 0.1):
        """Initialize SBA model (improvement over Croston)."""
        self.alpha = alpha
        self.level = None
        self.interval = None
    
    def fit(self, y: np.ndarray) -> Dict:
        """Fit SBA model."""
        if len(y) < 2:
            return {'status': 'failed', 'error': 'Insufficient data'}
        
        try:
            # Identify non-zero demand periods
            nonzero_mask = y != 0
            nonzero_values = y[nonzero_mask]
            nonzero_positions = np.where(nonzero_mask)[0]
            
            if len(nonzero_values) < 2:
                return {'status': 'failed', 'error': 'Insufficient non-zero values'}
            
            # Initialize level
            self.level = nonzero_values[0]
            
            # Calculate intervals between demands
            intervals = np.diff(nonzero_positions)
            self.interval = np.mean(intervals)
            
            # Smooth the level
            for value in nonzero_values[1:]:
                self.level = self.alpha * value + (1 - self.alpha) * self.level
            
            return {'status': 'success', 'level': self.level, 'interval': self.interval}
        
        except Exception as e:
            logger.warning(f"SBA fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, periods: int = 12) -> np.ndarray:
        """Get forecast using SBA (Croston adjusted by 0.95)."""
        if self.level is None or self.interval is None:
            return np.zeros(periods)
        
        # SBA bias adjustment (0.95 factor)
        forecast_value = 0.95 * (self.level / max(self.interval, 1))
        return np.full(periods, forecast_value)


class TSBModel:
    """Teunter-Syntetos-Babai for intermittent demand."""
    
    def __init__(self, alpha: float = 0.1):
        """Initialize TSB model (further improvement over SBA)."""
        self.alpha = alpha
        self.level = None
        self.interval = None
        self.demand_probability = None
    
    def fit(self, y: np.ndarray) -> Dict:
        """Fit TSB model."""
        if len(y) < 2:
            return {'status': 'failed', 'error': 'Insufficient data'}
        
        try:
            # Identify non-zero demand periods
            nonzero_mask = y != 0
            nonzero_values = y[nonzero_mask]
            nonzero_positions = np.where(nonzero_mask)[0]
            
            if len(nonzero_values) < 2:
                return {'status': 'failed', 'error': 'Insufficient non-zero values'}
            
            # Initialize level
            self.level = nonzero_values[0]
            
            # Calculate intervals and probability of demand
            intervals = np.diff(nonzero_positions)
            self.interval = np.mean(intervals)
            self.demand_probability = len(nonzero_values) / len(y)
            
            # Smooth the level
            for value in nonzero_values[1:]:
                self.level = self.alpha * value + (1 - self.alpha) * self.level
            
            return {
                'status': 'success',
                'level': self.level,
                'interval': self.interval,
                'probability': self.demand_probability
            }
        
        except Exception as e:
            logger.warning(f"TSB fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, periods: int = 12) -> np.ndarray:
        """Get forecast using TSB."""
        if self.level is None or self.interval is None:
            return np.zeros(periods)
        
        # TSB combines demand level with probability
        # forecast = (level / interval) * probability
        forecast_value = (self.level / max(self.interval, 1)) * max(self.demand_probability, 0)
        return np.full(periods, forecast_value)


class IntermittentDemandModels:
    """Wrapper for intermittent demand models."""
    
    def __init__(self):
        """Initialize all intermittent demand models."""
        self.models = {
            'croston': CrostonModel(),
            'sba': SBAModel(),
            'tsb': TSBModel(),
        }
    
    def fit_all(self, y: np.ndarray) -> Dict:
        """Fit all intermittent demand models."""
        results = {}
        for name, model in self.models.items():
            try:
                result = model.fit(y)
                results[name] = result
            except Exception as e:
                results[name] = {'status': 'failed', 'error': str(e)}
                logger.warning(f"Failed to fit {name}: {e}")
        
        return results
    
    def predict_all(self, periods: int = 12) -> Dict[str, np.ndarray]:
        """Get predictions from all intermittent models."""
        forecasts = {}
        for name, model in self.models.items():
            try:
                forecast = model.predict(periods)
                forecasts[name] = forecast
            except Exception as e:
                logger.warning(f"Failed to predict with {name}: {e}")
                forecasts[name] = np.zeros(periods)
        
        return forecasts
    
    def is_intermittent(self, y: np.ndarray, threshold: float = 0.3) -> bool:
        """Determine if demand is intermittent.
        
        Args:
            y: Demand series
            threshold: Proportion of zeros to consider intermittent
        
        Returns:
            True if intermittent, False otherwise
        """
        if len(y) == 0:
            return False
        
        zero_proportion = np.sum(y == 0) / len(y)
        return zero_proportion > threshold
