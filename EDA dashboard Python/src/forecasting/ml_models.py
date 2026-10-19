"""
Machine Learning Forecasting Models
Random Forest, Gradient Boosting, XGBoost, and LightGBM.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available")


class RandomForestForecaster:
    """Random Forest time series forecasting."""
    
    def __init__(self, n_estimators: int = 50, max_depth: int = 12):
        """Initialize Random Forest forecaster."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for Random Forest")
        
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42
        )
        self.feature_cols = None
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Fit Random Forest model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target values
        
        Returns:
            Fit status dictionary
        """
        try:
            if X.shape[0] < 10:
                return {'status': 'failed', 'error': 'Insufficient training data'}
            
            self.model.fit(X, y)
            return {'status': 'success', 'n_samples': X.shape[0], 'n_features': X.shape[1]}
        except Exception as e:
            logger.warning(f"Random Forest fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get predictions."""
        try:
            return self.model.predict(X)
        except Exception as e:
            logger.warning(f"Random Forest prediction failed: {e}")
            return np.full(X.shape[0], np.nan)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance."""
        if self.model is None:
            return {}
        
        return {f'feature_{i}': imp for i, imp in enumerate(self.model.feature_importances_)}


class GradientBoostingForecaster:
    """Gradient Boosting Machine time series forecasting."""
    
    def __init__(self, n_estimators: int = 50, learning_rate: float = 0.1, max_depth: int = 4):
        """Initialize Gradient Boosting forecaster."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for Gradient Boosting")
        
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Fit Gradient Boosting model."""
        try:
            if X.shape[0] < 10:
                return {'status': 'failed', 'error': 'Insufficient training data'}
            
            self.model.fit(X, y)
            return {'status': 'success', 'n_samples': X.shape[0], 'n_features': X.shape[1]}
        except Exception as e:
            logger.warning(f"Gradient Boosting fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get predictions."""
        try:
            return self.model.predict(X)
        except Exception as e:
            logger.warning(f"Gradient Boosting prediction failed: {e}")
            return np.full(X.shape[0], np.nan)


class XGBoostForecaster:
    """XGBoost time series forecasting."""
    
    def __init__(self, n_estimators: int = 50, learning_rate: float = 0.1, max_depth: int = 4):
        """Initialize XGBoost forecaster."""
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost required")
        
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42,
            verbosity=0
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Fit XGBoost model."""
        try:
            if X.shape[0] < 10:
                return {'status': 'failed', 'error': 'Insufficient training data'}
            
            self.model.fit(X, y, verbose=False)
            return {'status': 'success', 'n_samples': X.shape[0], 'n_features': X.shape[1]}
        except Exception as e:
            logger.warning(f"XGBoost fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get predictions."""
        try:
            return self.model.predict(X)
        except Exception as e:
            logger.warning(f"XGBoost prediction failed: {e}")
            return np.full(X.shape[0], np.nan)


class LightGBMForecaster:
    """LightGBM time series forecasting."""
    
    def __init__(self, n_estimators: int = 50, learning_rate: float = 0.05, max_depth: int = 4):
        """Initialize LightGBM forecaster."""
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM required")
        
        self.model = lgb.LGBMRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42,
            verbosity=-1
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Fit LightGBM model."""
        try:
            if X.shape[0] < 10:
                return {'status': 'failed', 'error': 'Insufficient training data'}
            
            self.model.fit(X, y)
            return {'status': 'success', 'n_samples': X.shape[0], 'n_features': X.shape[1]}
        except Exception as e:
            logger.warning(f"LightGBM fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get predictions."""
        try:
            return self.model.predict(X)
        except Exception as e:
            logger.warning(f"LightGBM prediction failed: {e}")
            return np.full(X.shape[0], np.nan)


class MLModels:
    """Wrapper for machine learning forecasting models."""
    
    def __init__(self):
        """Initialize ML models that are available."""
        self.models = {}
        
        if SKLEARN_AVAILABLE:
            self.models['random_forest'] = RandomForestForecaster()
            self.models['gradient_boosting'] = GradientBoostingForecaster()
        
        if XGBOOST_AVAILABLE:
            self.models['xgboost'] = XGBoostForecaster()
        
        if LIGHTGBM_AVAILABLE:
            self.models['lightgbm'] = LightGBMForecaster()
        
        if not self.models:
            logger.warning("No ML libraries available. Install sklearn, xgboost, or lightgbm.")
    
    def fit_all(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Fit all available ML models."""
        results = {}
        for name, model in self.models.items():
            try:
                result = model.fit(X, y)
                results[name] = result
            except Exception as e:
                results[name] = {'status': 'failed', 'error': str(e)}
                logger.warning(f"Failed to fit {name}: {e}")
        
        return results
    
    def predict_all(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Get predictions from all ML models."""
        forecasts = {}
        for name, model in self.models.items():
            try:
                forecast = model.predict(X)
                forecasts[name] = forecast
            except Exception as e:
                logger.warning(f"Failed to predict with {name}: {e}")
                forecasts[name] = np.full(X.shape[0], np.nan)
        
        return forecasts
