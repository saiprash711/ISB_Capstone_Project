"""
Statistical Forecasting Models
ARIMA, Seasonal ARIMA and Exponential Smoothing (ETS) models.

Weekly SKU x Branch series hold ~2 years of history, so a 52-week seasonal
ARIMA / Holt-Winters cannot be estimated reliably per series (two seasonal
cycles are the bare minimum). The seasonal variants therefore use the pooled
seasonal profile (see seasonal_profile.py): the series is seasonally adjusted
with the pooled weekly factors, modelled, and re-seasonalised.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional
import logging
import warnings
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

logger = logging.getLogger(__name__)

_NAN3 = lambda n: (np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan))


class ARIMAModel:
    """ARIMA forecasting model."""

    CANDIDATE_ORDERS = [(0, 1, 1), (1, 1, 1), (1, 0, 1), (1, 0, 0)]

    def __init__(self, order: Tuple = (1, 1, 1), auto: bool = True):
        """Initialize ARIMA with optional auto order selection (minimum AIC)."""
        self.order = order
        self.auto = auto
        self.fitted_model = None

    def fit(self, y: np.ndarray) -> Dict:
        """Fit ARIMA model."""
        y = np.asarray(y, dtype=float)
        self.fitted_model = None
        if len(y) < 8:
            return {'status': 'failed', 'error': 'Insufficient data'}
        orders = self.CANDIDATE_ORDERS if self.auto else [self.order]
        best_aic = np.inf
        for candidate in orders:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    trend = 'c' if candidate[1] == 0 else 'n'
                    fitted = ARIMA(y, order=candidate, trend=trend).fit()
                if np.isfinite(fitted.aic) and fitted.aic < best_aic:
                    best_aic, self.order, self.fitted_model = fitted.aic, candidate, fitted
            except Exception:
                continue
        if self.fitted_model is None:
            return {'status': 'failed', 'error': 'No ARIMA order converged'}
        return {'status': 'success', 'order': self.order, 'aic': best_aic}

    def params(self) -> Dict[str, float]:
        if self.fitted_model is None:
            return {}
        return {str(k): float(v) for k, v in zip(self.fitted_model.param_names, self.fitted_model.params)}

    def predict(self, periods: int = 12) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get forecast with 95% confidence intervals."""
        if self.fitted_model is None:
            return _NAN3(periods)
        try:
            fc = self.fitted_model.get_forecast(steps=periods)
            ci = np.asarray(fc.conf_int(alpha=0.05))
            return np.asarray(fc.predicted_mean), ci[:, 0], ci[:, 1]
        except Exception as e:
            logger.warning(f"ARIMA prediction failed: {e}")
            return _NAN3(periods)


class SARIMAModel:
    """
    Seasonal ARIMA via pooled seasonal adjustment:
        z_t = y_t / S_t  ->  ARIMA(p,d,q) on z (order by minimum AIC)  ->  y_hat = z_hat x S_{t+h}
    where S_t are the pooled weekly seasonal factors (month cycle x month-end push).
    """

    def __init__(self):
        self.arima = ARIMAModel(auto=True)
        self.order = None

    def fit(self, y: np.ndarray, hist_factors: Optional[np.ndarray] = None) -> Dict:
        """Fit ARIMA on the seasonally adjusted series."""
        self.order = None
        if hist_factors is None:
            self.arima.fitted_model = None
            return {'status': 'failed', 'error': 'Seasonal profile unavailable (needs >= 52 weeks of pooled history)'}
        z = np.asarray(y, dtype=float) / np.maximum(np.asarray(hist_factors, dtype=float), 1e-3)
        res = self.arima.fit(z)
        self.order = self.arima.order if res.get('status') == 'success' else None
        return res

    def params(self) -> Dict[str, float]:
        return self.arima.params()

    def predict(self, periods: int = 12, future_factors: Optional[np.ndarray] = None
                ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get re-seasonalised forecast with confidence intervals."""
        if future_factors is None or self.arima.fitted_model is None:
            return _NAN3(periods)
        m, lo, hi = self.arima.predict(periods)
        f = np.asarray(future_factors, dtype=float)
        return m * f, lo * f, hi * f


class ETSModel:
    """
    Exponential smoothing with additive damped trend, ETS(A,Ad,N), fitted on the
    seasonally adjusted series when pooled seasonal factors are supplied and
    re-seasonalised for the forecast. Without factors it is a non-seasonal
    damped-trend Holt model.
    """

    def __init__(self, damped_trend: bool = True):
        self.damped_trend = damped_trend
        self.fitted_model = None
        self.seasonal = False

    def fit(self, y: np.ndarray, hist_factors: Optional[np.ndarray] = None) -> Dict:
        """Fit ETS model."""
        y = np.asarray(y, dtype=float)
        self.fitted_model = None
        if len(y) < 10:
            return {'status': 'failed', 'error': 'Insufficient data (< 10 weeks)'}
        if (y < 0).any():
            return {'status': 'failed', 'error': 'Cannot fit with negative values'}
        self.seasonal = hist_factors is not None
        z = y / np.maximum(np.asarray(hist_factors, dtype=float), 1e-3) if self.seasonal else y
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                self.fitted_model = ExponentialSmoothing(
                    z, trend='add', damped_trend=self.damped_trend, seasonal=None,
                    initialization_method='estimated').fit(optimized=True)
            return {'status': 'success', 'aic': float(self.fitted_model.aic), 'seasonal_adjusted': self.seasonal}
        except Exception as e:
            logger.warning(f"ETS fit failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def params(self) -> Dict[str, float]:
        if self.fitted_model is None:
            return {}
        p = self.fitted_model.params
        keys = {'smoothing_level': 'alpha', 'smoothing_trend': 'beta', 'damping_trend': 'phi'}
        return {v: float(p[k]) for k, v in keys.items() if k in p and p[k] is not None}

    def predict(self, periods: int = 12, future_factors: Optional[np.ndarray] = None
                ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get forecast with approximate 95% intervals from in-sample residual spread."""
        if self.fitted_model is None or (self.seasonal and future_factors is None):
            return _NAN3(periods)
        try:
            m = np.asarray(self.fitted_model.forecast(steps=periods), dtype=float)
            std = float(np.std(self.fitted_model.resid))
            lo, hi = m - 1.96 * std, m + 1.96 * std
            if self.seasonal:
                f = np.asarray(future_factors, dtype=float)
                m, lo, hi = m * f, lo * f, hi * f
            return m, lo, hi
        except Exception as e:
            logger.warning(f"ETS prediction failed: {e}")
            return _NAN3(periods)


class StatisticalModels:
    """Wrapper for statistical forecasting models."""

    def __init__(self):
        """Initialize all statistical models."""
        self.models = {
            'arima': ARIMAModel(),
            'sarima': SARIMAModel(),
            'ets': ETSModel(),
        }

    def fit_all(self, y: np.ndarray, hist_factors: Optional[np.ndarray] = None,
                names: Optional[list] = None) -> Dict:
        """Fit statistical models (optionally only `names`); seasonal variants use `hist_factors`."""
        results = {}
        for name, model in self.models.items():
            if names is not None and name not in names:
                continue
            try:
                results[name] = model.fit(y) if name == 'arima' else model.fit(y, hist_factors)
            except Exception as e:
                results[name] = {'status': 'failed', 'error': str(e)}
                logger.warning(f"Failed to fit {name}: {e}")
        return results

    def predict_all(self, periods: int = 12, future_factors: Optional[np.ndarray] = None,
                    names: Optional[list] = None) -> Dict[str, Dict[str, np.ndarray]]:
        """Get predictions from statistical models."""
        forecasts = {}
        for name, model in self.models.items():
            if names is not None and name not in names:
                continue
            try:
                m, lo, hi = model.predict(periods) if name == 'arima' else model.predict(periods, future_factors)
            except Exception as e:
                logger.warning(f"Failed to predict with {name}: {e}")
                m, lo, hi = _NAN3(periods)
            forecasts[name] = {'forecast': m, 'lower': lo, 'upper': hi}
        return forecasts
