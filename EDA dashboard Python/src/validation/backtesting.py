"""
Rolling-Origin (Walk-Forward) Backtesting Module
Implements strictly chronological cross-validation with expanding or sliding windows
to ensure zero data leakage across folds.

Defaults are matched to the planning decision: 12-week test windows (the
dashboard forecast horizon) stepped 12 weeks apart, so four folds span the
most recent year and every candidate is judged across the full seasonal cycle
rather than only the last few weeks.
"""
import numpy as np
import pandas as pd
from typing import Callable, Dict, List, Tuple, Optional, Any
import logging

from dataclasses import dataclass
from .metrics import calculate_all_metrics
from src.forecasting.intermittent import IntermittentDemandModels
from src.forecasting.model_zoo import (
    ALL_MODELS, ENSEMBLE_NAME, INTERMITTENT_MAP, ML_MAP,
    combine, forecast_models, inverse_wape_weights,
)
from src.features import FeatureEngineer

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Centralized configuration for rolling-origin walk-forward validation."""
    n_folds: int = 4
    test_weeks: int = 12
    min_train_weeks: int = 13
    step_size: int = 12
    window_type: str = 'expanding'


class RollingOriginBacktest:
    """
    Rolling-origin walk-forward validator for SKU demand time series.
    """

    def __init__(self, config: Optional[BacktestConfig] = None,
                 n_folds: Optional[int] = None, test_weeks: Optional[int] = None,
                 min_train_weeks: Optional[int] = None, step_size: Optional[int] = None,
                 window_type: Optional[str] = None):
        """
        Args:
            config: Optional BacktestConfig instance
            n_folds: Number of walk-forward folds
            test_weeks: Forecast horizon / evaluation window per fold
            min_train_weeks: Minimum training history required before first test split
            step_size: Number of weeks to roll forward between folds (defaults to test_weeks)
            window_type: 'expanding' or 'rolling'
        """
        cfg = config or BacktestConfig()
        self.n_folds = max(1, n_folds if n_folds is not None else cfg.n_folds)
        self.test_weeks = max(1, test_weeks if test_weeks is not None else cfg.test_weeks)
        self.min_train_weeks = max(4, min_train_weeks if min_train_weeks is not None else cfg.min_train_weeks)
        if step_size is not None:
            self.step_size = step_size
        elif test_weeks is not None:
            self.step_size = self.test_weeks
        else:
            self.step_size = cfg.step_size
        self.window_type = window_type or cfg.window_type
        self.intermittent_models = IntermittentDemandModels()
        self.feature_engineer = FeatureEngineer()

    def generate_folds(self, n_samples: int) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate chronological (train_indices, test_indices) splits.
        Strictly forward in time - no random splits, zero future leakage.
        """
        total_needed = self.min_train_weeks + self.test_weeks
        if n_samples < total_needed:
            # Short series: a single fold with at least 4 training weeks and a shortened test window
            test_len = min(self.test_weeks, n_samples - 4)
            if test_len < 1:
                return []
            return [(np.arange(n_samples - test_len), np.arange(n_samples - test_len, n_samples))]

        folds = []
        max_possible_folds = (n_samples - total_needed) // self.step_size + 1
        actual_folds = min(self.n_folds, max(1, max_possible_folds))

        # Position the latest fold at the end of the series
        for i in range(actual_folds):
            test_end = n_samples - (actual_folds - 1 - i) * self.step_size
            test_start = test_end - self.test_weeks
            if test_start < self.min_train_weeks or test_end > n_samples:
                continue
            train_start = 0 if self.window_type == 'expanding' else max(0, test_start - self.min_train_weeks)
            folds.append((np.arange(train_start, test_start), np.arange(test_start, test_end)))

        return folds

    def default_candidates(self, y: np.ndarray, sku_df: Optional[pd.DataFrame] = None) -> List[str]:
        """All model families applicable to this series."""
        names = [m for m in ALL_MODELS if m not in INTERMITTENT_MAP and m not in ML_MAP]
        if self.intermittent_models.is_intermittent(y):
            names += list(INTERMITTENT_MAP)
        if len(y) >= 30 and sku_df is not None:
            names += list(ML_MAP)
        return names

    def evaluate_sku_series(self, y: np.ndarray, dates: Optional[np.ndarray] = None,
                            sku_df: Optional[pd.DataFrame] = None,
                            candidate_models: Optional[List[str]] = None,
                            profile_factory: Optional[Callable[[pd.Timestamp], Any]] = None) -> Dict[str, Any]:
        """
        Run walk-forward rolling-origin evaluation on a 1D weekly demand series.

        Args:
            y: weekly demand
            dates: W-MON week labels aligned with y (synthetic weekly dates are used when absent)
            sku_df: weekly frame with 'date' and 'total_demand' (needed for ML models)
            candidate_models: models to evaluate (default: all applicable)
            profile_factory: callable(cutoff_week) -> SeasonalProfile estimated from pooled
                             data observed up to the cutoff only (no look-ahead)
        """
        y = np.asarray(y, dtype=float)
        n_samples = len(y)
        splits = self.generate_folds(n_samples)

        if not splits:
            logger.warning(f"Insufficient history ({n_samples} periods) for backtesting.")
            return {
                'status': 'failed',
                'reason': f'Insufficient history ({n_samples} periods, required >= 5)',
                'leaderboard': pd.DataFrame(),
                'fold_details': [],
                'n_folds': 0,
            }

        has_dates = dates is not None
        dates = pd.DatetimeIndex(dates) if has_dates else pd.date_range('2000-01-03', periods=n_samples, freq='W-MON')
        if sku_df is not None:
            sku_df = sku_df.reset_index(drop=True).copy()
            sku_df['date'] = dates
            sku_df['total_demand'] = y
            for col in ('sku', 'branch'):
                if col not in sku_df.columns:
                    sku_df[col] = '_'
        is_intermittent = self.intermittent_models.is_intermittent(y)
        selected_models = [m for m in (candidate_models or self.default_candidates(y, sku_df))
                           if m != ENSEMBLE_NAME]

        model_fold_metrics: Dict[str, List[Dict[str, float]]] = {m: [] for m in selected_models}
        model_fold_metrics[ENSEMBLE_NAME] = []
        fold_details = []

        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            y_train, y_test = y[train_idx], y[test_idx]
            horizon = len(test_idx)
            fold_info = {
                'fold': fold_idx + 1,
                'train_start_idx': int(train_idx[0]),
                'train_end_idx': int(train_idx[-1]),
                'test_start_idx': int(test_idx[0]),
                'test_end_idx': int(test_idx[-1]),
                'train_size': len(train_idx),
                'test_size': len(test_idx),
                'actuals': y_test.tolist(),
                'predictions': {},
                'model_errors': {}
            }
            if has_dates:
                fold_info['test_dates'] = [str(d.date()) for d in dates[test_idx]]

            cutoff = dates[train_idx[-1]]
            profile = profile_factory(cutoff) if (profile_factory is not None and has_dates) else None
            train_df = sku_df.iloc[train_idx] if sku_df is not None else None
            preds, errs, _ = forecast_models(selected_models, y_train, dates[train_idx], horizon,
                                             profile=profile, sku_df=train_df,
                                             feature_engineer=self.feature_engineer)
            fold_info['model_errors'].update(errs)
            for m_name, pred in preds.items():
                fold_info['predictions'][m_name] = pred.tolist()
                model_fold_metrics[m_name].append(calculate_all_metrics(y_test, pred, y_train=y_train))

            # Out-of-fold ensemble: weights use WAPE from EARLIER folds only (equal weights in fold 1)
            prior = {m: float(np.mean([f['WAPE'] for f in model_fold_metrics[m][:-1]]))
                     for m in preds if len(model_fold_metrics[m]) > 1}
            weights = inverse_wape_weights(prior) if len(prior) >= 2 else None
            ens = combine(preds, weights)
            if ens is not None:
                fold_info['predictions'][ENSEMBLE_NAME] = ens.tolist()
                fold_info['ensemble_weights'] = weights or {m: 1.0 / len(preds) for m in preds}
                model_fold_metrics[ENSEMBLE_NAME].append(calculate_all_metrics(y_test, ens, y_train=y_train))

            fold_details.append(fold_info)

        # Aggregate metrics across folds into Leaderboard with principled stability score
        leaderboard_rows = []
        for m_name, fold_metric_list in model_fold_metrics.items():
            # A model must survive every fold to be ranked against the others on equal terms
            if not fold_metric_list or len(fold_metric_list) < len(splits):
                continue
            wapes = [f['WAPE'] for f in fold_metric_list]
            bias_pcts = [f['Bias_pct'] for f in fold_metric_list]

            # Principled multi-factor stability score (0-100):
            # 50% WAPE CV + 30% Worst-fold degradation + 20% Bias consistency
            mean_w = float(np.mean(wapes))
            std_w = float(np.std(wapes))
            norm_cv_penalty = min(1.0, max(0.0, (std_w / (mean_w + 1e-4)) if mean_w > 0 else 0.0))
            norm_worst_penalty = min(1.0, max(0.0, (float(np.max(wapes)) - mean_w) / (mean_w + 1e-4)))
            bias_consistency = sum(1 for b in bias_pcts if abs(b) <= 15.0) / len(bias_pcts) if bias_pcts else 1.0
            stability = 100.0 * (0.5 * (1.0 - norm_cv_penalty) + 0.3 * (1.0 - norm_worst_penalty) + 0.2 * bias_consistency)

            leaderboard_rows.append({
                'model': m_name,
                'folds_evaluated': len(fold_metric_list),
                'mean_wape': round(mean_w, 2),
                'std_wape': round(std_w, 2),
                'mean_rmse': round(float(np.mean([f['RMSE'] for f in fold_metric_list])), 2),
                'mean_mae': round(float(np.mean([f['MAE'] for f in fold_metric_list])), 2),
                'mean_smape': round(float(np.mean([f['sMAPE'] for f in fold_metric_list])), 2),
                'mean_mase': round(float(np.mean([f['MASE'] for f in fold_metric_list])), 3),
                'mean_bias': round(float(np.mean([f['Bias'] for f in fold_metric_list])), 2),
                'mean_bias_pct': round(float(np.mean(bias_pcts)), 2),
                'stability_score': round(max(0.0, min(100.0, stability)), 1)
            })

        leaderboard_df = pd.DataFrame(leaderboard_rows)
        if not leaderboard_df.empty:
            # Rank on RMSE: it is minimised by the mean (expected demand), which replenishment needs.
            # Absolute-error metrics (WAPE/MAE) are minimised by the median, which for lumpy series is
            # often zero - a 'forecast nothing' model would win. WAPE stays the reported accuracy KPI.
            leaderboard_df = leaderboard_df.sort_values(by=['mean_rmse', 'mean_wape']).reset_index(drop=True)
            leaderboard_df['rank'] = np.arange(1, len(leaderboard_df) + 1)

        return {
            'status': 'success',
            'n_folds': len(splits),
            'usable_history_weeks': n_samples,
            'leaderboard': leaderboard_df,
            'fold_details': fold_details,
            'is_intermittent': is_intermittent,
            'candidate_models': selected_models,
        }
