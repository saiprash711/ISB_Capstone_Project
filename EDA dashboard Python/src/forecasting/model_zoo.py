"""
Model Zoo - single entry point that fits any candidate model on a weekly
history and returns its forward forecast.

Used by both the rolling-origin backtest (on each fold's training window) and
the champion's forward forecast, so the model that is validated is exactly the
model that is deployed.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

from src.forecasting.baseline import BaselineForecastingModels
from src.forecasting.statistical import StatisticalModels
from src.forecasting.intermittent import IntermittentDemandModels
from src.forecasting.ml_models import MLModels
from src.forecasting.seasonal_profile import SeasonalProfile, SeasonalIndexForecaster
from src.features import FeatureEngineer

logger = logging.getLogger(__name__)

BASELINE_MAP = {'Naive': 'naive', 'Seasonal Naive': 'seasonal_naive',
                'Moving Average': 'moving_average', 'Exponential Smoothing': 'exponential_smoothing'}
STAT_MAP = {'ARIMA': 'arima', 'SARIMA': 'sarima', 'ETS': 'ets'}
INTERMITTENT_MAP = {'Croston': 'croston', 'SBA': 'sba', 'TSB': 'tsb'}
ML_MAP = {'Random Forest': 'random_forest', 'Gradient Boosting': 'gradient_boosting',
          'XGBoost': 'xgboost', 'LightGBM': 'lightgbm'}
SEASONAL_INDEX_MAP = {'Seasonal Index': 8, 'Seasonal Index (smooth)': 26}
ENSEMBLE_NAME = 'Ensemble (Consensus)'

MODEL_DESCRIPTIONS = {
    'Naive': 'Repeats the last observed week.',
    'Seasonal Naive': 'Repeats the same week of last year (needs >= 52 weeks of history).',
    'Moving Average': 'Flat average of the last 4 weeks.',
    'Exponential Smoothing': 'Simple exponential smoothing level (alpha = 0.3), flat forecast.',
    'ARIMA': 'Non-seasonal ARIMA; order chosen by minimum AIC from (0,1,1), (1,1,1), (1,0,1), (1,0,0).',
    'SARIMA': 'Seasonal ARIMA via pooled seasonal adjustment: ARIMA (min-AIC order) on demand / seasonal factor, re-seasonalised.',
    'ETS': 'Damped-trend exponential smoothing ETS(A,Ad,N) on seasonally adjusted demand, re-seasonalised.',
    'Croston': "Croston's method: smoothed demand size / smoothed inter-demand interval (alpha = 0.1).",
    'SBA': 'Syntetos-Boylan approximation: Croston x (1 - alpha/2) to remove its upward bias.',
    'TSB': 'Teunter-Syntetos-Babai: smoothed demand probability x size; decays for dying items.',
    'Random Forest': 'Random forest on lags, rolling statistics, calendar and pooled seasonal factor; recursive multi-step.',
    'Gradient Boosting': 'Gradient boosting on the same feature set; recursive multi-step.',
    'XGBoost': 'XGBoost on the same feature set; recursive multi-step.',
    'LightGBM': 'LightGBM on the same feature set; recursive multi-step.',
    'Seasonal Index': 'Pooled seasonal profile (region shrunk to branch: month cycle x month-end push) x SKU level of the last 8 weeks.',
    'Seasonal Index (smooth)': 'Pooled seasonal profile x SKU seasonally adjusted level of the last 26 weeks.',
    ENSEMBLE_NAME: 'Inverse-WAPE weighted average of all candidate forecasts (weights from earlier backtest folds only).',
}

ALL_MODELS = list(BASELINE_MAP) + list(STAT_MAP) + list(INTERMITTENT_MAP) + list(ML_MAP) + list(SEASONAL_INDEX_MAP)


def future_week_dates(dates, horizon: int) -> pd.DatetimeIndex:
    last = pd.Timestamp(pd.DatetimeIndex(dates)[-1])
    return pd.date_range(last + pd.Timedelta(weeks=1), periods=horizon, freq='W-MON')


def _valid(pred, horizon: int) -> Optional[np.ndarray]:
    if pred is None:
        return None
    arr = np.asarray(pred, dtype=float)
    if arr.shape != (horizon,) or not np.all(np.isfinite(arr)):
        return None
    return np.maximum(0.0, arr)


def forecast_models(names: List[str], y: np.ndarray, dates, horizon: int,
                    profile: Optional[SeasonalProfile] = None,
                    sku_df: Optional[pd.DataFrame] = None,
                    feature_engineer: Optional[FeatureEngineer] = None
                    ) -> Tuple[Dict[str, np.ndarray], Dict[str, str], Dict[str, Dict[str, Any]]]:
    """
    Fit each named model on history `y` (weekly, W-MON `dates`) and forecast `horizon` weeks ahead.

    Returns:
        forecasts: model name -> forecast array (only models that fitted successfully)
        errors:    model name -> reason a model was disqualified
        details:   model name -> fitted parameters / diagnostics for transparency
    """
    y = np.asarray(y, dtype=float)
    dates = pd.DatetimeIndex(dates)
    fut = future_week_dates(dates, horizon)
    hist_f = profile.factors(dates) if profile is not None else None
    fut_f = profile.factors(fut) if profile is not None else None
    forecasts, errors, details = {}, {}, {}

    def _put(name, pred, info=None):
        v = _valid(pred, horizon)
        if v is None:
            errors[name] = errors.get(name, 'produced no valid forecast')
        else:
            forecasts[name] = v
            if info:
                details[name] = info

    # Baselines
    req = [n for n in names if n in BASELINE_MAP]
    if req:
        bm = BaselineForecastingModels()
        bm.fit_all(y)
        preds = bm.predict_all(horizon)
        for n in req:
            if n == 'Seasonal Naive' and len(y) < 52:
                errors[n] = 'needs >= 52 weeks of history'
                continue
            _put(n, preds.get(BASELINE_MAP[n]))

    # Statistical
    req = [n for n in names if n in STAT_MAP]
    if req:
        sm = StatisticalModels()
        keys = [STAT_MAP[n] for n in req]
        fits = sm.fit_all(y, hist_factors=hist_f, names=keys)
        preds = sm.predict_all(horizon, future_factors=fut_f, names=keys)
        for n in req:
            k = STAT_MAP[n]
            if fits.get(k, {}).get('status') != 'success':
                errors[n] = fits.get(k, {}).get('error', 'fit failed')
                continue
            mdl = sm.models[k]
            info = {'params': mdl.params()}
            if getattr(mdl, 'order', None) is not None:
                info['order'] = tuple(mdl.order)
            _put(n, preds[k]['forecast'], info)

    # Intermittent
    req = [n for n in names if n in INTERMITTENT_MAP]
    if req:
        im = IntermittentDemandModels()
        fits = im.fit_all(y)
        preds = im.predict_all(horizon)
        for n in req:
            k = INTERMITTENT_MAP[n]
            if fits.get(k, {}).get('status') != 'success':
                errors[n] = fits.get(k, {}).get('error', 'fit failed')
                continue
            _put(n, preds[k], {k2: round(float(v), 4) for k2, v in fits[k].items()
                               if isinstance(v, (int, float, np.floating)) and k2 != 'status'})

    # Pooled seasonal index
    for n in [n for n in names if n in SEASONAL_INDEX_MAP]:
        if profile is None:
            errors[n] = 'seasonal profile unavailable (needs >= 52 weeks of pooled history)'
            continue
        si = SeasonalIndexForecaster(window=SEASONAL_INDEX_MAP[n]).fit(y, hist_f)
        _put(n, si.predict(fut_f), {'level_per_week': round(si.level, 3), 'window_weeks': si.window})

    # Machine learning (recursive multi-step)
    req = [n for n in names if n in ML_MAP]
    if req:
        if sku_df is None or len(y) < 20:
            for n in req:
                errors[n] = 'needs >= 20 weeks of history'
        else:
            fe = feature_engineer or FeatureEngineer()
            try:
                frame = sku_df[['date', 'total_demand', 'sku', 'branch']].copy().reset_index(drop=True)
                if hist_f is not None:
                    frame['seasonal_index'] = hist_f
                X_df, f_cols = fe.engineer_features(frame)
                cols = [c for c in f_cols if c in X_df.columns]
                X_df[cols] = X_df[cols].apply(pd.to_numeric, errors='coerce')
                X = X_df[cols].to_numpy(dtype=np.float32)
                X[~np.isfinite(X)] = 0.0
                ml = MLModels()
                keys = [ML_MAP[n] for n in req if ML_MAP[n] in ml.models]
                fits = ml.fit_all(X, y, names=keys)
                for n in req:
                    k = ML_MAP[n]
                    if fits.get(k, {}).get('status') != 'success':
                        errors[n] = fits.get(k, {}).get('error', 'library unavailable or fit failed')
                        continue
                    pred = fe.predict_recursive(ml.models[k], pd.Series(y), horizon, cols,
                                                base_date=dates[-1], future_factors=fut_f)
                    imp = getattr(ml.models[k].model, 'feature_importances_', None)
                    info = {'feature_importance': dict(zip(cols, np.asarray(imp, dtype=float).tolist()))} if imp is not None else None
                    _put(n, pred, info)
            except Exception as e:
                for n in req:
                    errors.setdefault(n, f'ML pipeline failed: {e}')

    for n in names:
        if n not in forecasts and n not in errors and n != ENSEMBLE_NAME:
            errors[n] = 'unknown model'
    return forecasts, errors, details


def inverse_wape_weights(wapes: Dict[str, float]) -> Dict[str, float]:
    """Normalised inverse-WAPE weights (WAPE floored at 1% to avoid division blow-ups)."""
    inv = {m: 1.0 / max(1.0, float(w)) for m, w in wapes.items() if np.isfinite(w)}
    tot = sum(inv.values())
    return {m: v / tot for m, v in inv.items()} if tot > 0 else {}


def combine(forecasts: Dict[str, np.ndarray], weights: Optional[Dict[str, float]] = None) -> Optional[np.ndarray]:
    """Weighted (or equal-weight) combination of member forecasts."""
    members = [m for m in forecasts if weights is None or m in weights]
    if len(members) < 2:
        return None
    w = np.array([weights[m] if weights else 1.0 for m in members], dtype=float)
    w = w / w.sum()
    return np.maximum(0.0, np.column_stack([forecasts[m] for m in members]) @ w)
