"""
Intermittent Demand Forecasting Models
Croston, SBA (Syntetos-Boylan), and TSB (Teunter-Syntetos-Babai).
"""
import numpy as np
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


def _croston_states(y: np.ndarray, alpha: float) -> Tuple[float, float]:
    """
    Croston (1972) recursions: exponentially smooth the non-zero demand size z
    and the inter-demand interval p, updating only in periods with demand.
    """
    nz = np.flatnonzero(y > 0)
    z = float(y[nz[0]])
    p = float(nz[0] + 1)                 # periods until the first demand
    last = nz[0]
    for t in nz[1:]:
        z = z + alpha * (float(y[t]) - z)
        p = p + alpha * (float(t - last) - p)
        last = t
    return z, p


class CrostonModel:
    """Croston's method for intermittent demand: forecast = z / p."""

    def __init__(self, alpha: float = 0.1):
        """Initialize Croston's method.

        Args:
            alpha: Smoothing parameter (0-1) for demand size and interval
        """
        self.alpha = alpha
        self.level = None
        self.interval = None

    def fit(self, y: np.ndarray) -> Dict:
        """Fit Croston's model."""
        y = np.asarray(y, dtype=float)
        if len(y) < 2:
            return {'status': 'failed', 'error': 'Insufficient data'}
        if np.count_nonzero(y > 0) < 2:
            return {'status': 'failed', 'error': 'Insufficient non-zero values'}
        try:
            self.level, self.interval = _croston_states(y, self.alpha)
            return {'status': 'success', 'level': self.level, 'interval': self.interval}
        except Exception as e:
            logger.warning(f"Croston fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _rate(self) -> float:
        return self.level / max(self.interval, 1.0)

    def predict(self, periods: int = 12) -> np.ndarray:
        """Get forecast using Croston's method."""
        if self.level is None or self.interval is None:
            return np.full(periods, np.nan)
        return np.full(periods, self._rate())


class SBAModel(CrostonModel):
    """Syntetos-Boylan Approximation: Croston debiased by (1 - alpha/2)."""

    def predict(self, periods: int = 12) -> np.ndarray:
        """Get forecast using SBA."""
        if self.level is None or self.interval is None:
            return np.full(periods, np.nan)
        return np.full(periods, (1.0 - self.alpha / 2.0) * self._rate())


class TSBModel:
    """
    Teunter-Syntetos-Babai (2011): smooths the demand probability every period
    (so forecasts decay towards zero for obsolescent items) and the demand size
    in periods with demand. Forecast = probability x size.
    """

    def __init__(self, alpha: float = 0.1, beta: float = 0.1):
        """
        Args:
            alpha: smoothing parameter for demand size
            beta: smoothing parameter for demand probability
        """
        self.alpha = alpha
        self.beta = beta
        self.level = None
        self.demand_probability = None

    def fit(self, y: np.ndarray) -> Dict:
        """Fit TSB model."""
        y = np.asarray(y, dtype=float)
        if len(y) < 2:
            return {'status': 'failed', 'error': 'Insufficient data'}
        nz = np.flatnonzero(y > 0)
        if len(nz) < 2:
            return {'status': 'failed', 'error': 'Insufficient non-zero values'}
        try:
            z = float(y[nz[0]])
            p = len(nz) / len(y)
            for t in range(nz[0] + 1, len(y)):
                if y[t] > 0:
                    p = p + self.beta * (1.0 - p)
                    z = z + self.alpha * (float(y[t]) - z)
                else:
                    p = (1.0 - self.beta) * p
            self.level, self.demand_probability = z, p
            return {'status': 'success', 'level': z, 'probability': p}
        except Exception as e:
            logger.warning(f"TSB fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def predict(self, periods: int = 12) -> np.ndarray:
        """Get forecast using TSB."""
        if self.level is None or self.demand_probability is None:
            return np.full(periods, np.nan)
        return np.full(periods, self.level * self.demand_probability)


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
        """Get predictions from all intermittent models (NaN when a model could not be fitted)."""
        forecasts = {}
        for name, model in self.models.items():
            try:
                forecasts[name] = model.predict(periods)
            except Exception as e:
                logger.warning(f"Failed to predict with {name}: {e}")
                forecasts[name] = np.full(periods, np.nan)

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
