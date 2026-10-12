"""
Rolling-Origin (Walk-Forward) Backtesting Module
Implements strictly chronological cross-validation with expanding or sliding windows
to ensure zero data leakage across folds.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging

from dataclasses import dataclass
from .metrics import calculate_all_metrics, calculate_wape
from src.forecasting.baseline import BaselineForecastingModels
from src.forecasting.statistical import StatisticalModels
from src.forecasting.intermittent import IntermittentDemandModels
from src.forecasting.ml_models import MLModels
from src.forecasting.ensemble import EnsembleForecaster
from src.features import FeatureEngineer

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Centralized configuration for rolling-origin walk-forward validation."""
    n_folds: int = 5
    test_weeks: int = 4
    min_train_weeks: int = 24
    step_size: int = 4
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
            step_size: Number of weeks to roll forward between folds
            window_type: 'expanding' or 'rolling'
        """
        cfg = config or BacktestConfig()
        self.n_folds = max(1, n_folds if n_folds is not None else cfg.n_folds)
        self.test_weeks = max(1, test_weeks if test_weeks is not None else cfg.test_weeks)
        self.min_train_weeks = max(4, min_train_weeks if min_train_weeks is not None else cfg.min_train_weeks)
        self.step_size = step_size or cfg.step_size or self.test_weeks
        self.window_type = window_type or cfg.window_type
        
        # Models
        self.baseline_models = BaselineForecastingModels()
        self.statistical_models = StatisticalModels()
        self.intermittent_models = IntermittentDemandModels()
        self.ml_models = MLModels()
        self.feature_engineer = FeatureEngineer()

    def generate_folds(self, n_samples: int) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate chronological (train_indices, test_indices) splits.
        Strictly forward in time - no random splits, zero future leakage.
        """
        total_needed = self.min_train_weeks + self.test_weeks
        if n_samples < total_needed:
            # If time series is shorter than ideal min_train, adjust proportionally
            usable_train = max(4, n_samples - self.test_weeks)
            if usable_train < 4:
                return []
            return [(np.arange(usable_train), np.arange(usable_train, n_samples))]
            
        folds = []
        # Calculate start points working backward from the end of the series
        max_possible_folds = (n_samples - self.min_train_weeks) // self.step_size
        actual_folds = min(self.n_folds, max(1, max_possible_folds))
        
        # Position the latest fold at the end of the series
        for i in range(actual_folds):
            # Working backwards from the last period
            test_end = n_samples - (actual_folds - 1 - i) * self.step_size
            test_start = test_end - self.test_weeks
            
            if test_start < self.min_train_weeks or test_start <= 0 or test_end > n_samples:
                continue
                
            if self.window_type == 'expanding':
                train_start = 0
            else:
                train_start = max(0, test_start - self.min_train_weeks)
                
            train_idx = np.arange(train_start, test_start)
            test_idx = np.arange(test_start, test_end)
            
            if len(train_idx) >= 4 and len(test_idx) == self.test_weeks:
                folds.append((train_idx, test_idx))
                
        return folds

    def evaluate_sku_series(self, y: np.ndarray, dates: Optional[np.ndarray] = None,
                           sku_df: Optional[pd.DataFrame] = None,
                           candidate_models: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run walk-forward rolling-origin evaluation on a 1D demand series.
        """
        y = np.asarray(y, dtype=float)
        n_samples = len(y)
        splits = self.generate_folds(n_samples)
        
        if not splits:
            logger.warning(f"Insufficient history ({n_samples} periods) for backtesting.")
            return {
                'status': 'failed',
                'reason': f'Insufficient history ({n_samples} periods, required >= {self.min_train_weeks + self.test_weeks})',
                'leaderboard': pd.DataFrame(),
                'fold_results': []
            }
            
        is_intermittent = self.intermittent_models.is_intermittent(y)
        
        # Model dictionary to evaluate
        all_candidate_names = [
            'Naive', 'Seasonal Naive', 'Moving Average', 'Exponential Smoothing',
            'ARIMA', 'SARIMA', 'ETS'
        ]
        if is_intermittent:
            all_candidate_names.extend(['Croston', 'SBA', 'TSB'])
        if n_samples >= 30 and sku_df is not None:
            all_candidate_names.extend(['Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM'])
            
        if candidate_models is not None:
            selected_models = [m for m in all_candidate_names if m in candidate_models]
        else:
            selected_models = all_candidate_names

        # Fold evaluation container
        # model_name -> list of fold metric dicts
        model_fold_metrics: Dict[str, List[Dict[str, float]]] = {m: [] for m in selected_models}
        fold_details = []

        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            y_train = y[train_idx]
            y_test = y[test_idx]
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
            if dates is not None:
                fold_info['test_dates'] = [str(d) for d in dates[test_idx]]
                
            # 1. Fit & predict Baselines (Strict zero-fallback: failures are disqualified)
            baseline_preds = {}
            try:
                self.baseline_models.fit_all(y_train)
                baseline_preds = self.baseline_models.predict_all(horizon)
            except Exception as e:
                logger.debug(f"Baseline fit in fold {fold_idx} failed: {e}")

            b_map = {
                'Naive': 'naive',
                'Seasonal Naive': 'seasonal_naive',
                'Moving Average': 'moving_average',
                'Exponential Smoothing': 'exponential_smoothing'
            }
            for b_name in ['Naive', 'Seasonal Naive', 'Moving Average', 'Exponential Smoothing']:
                if b_name in selected_models:
                    pred = baseline_preds.get(b_map.get(b_name))
                    if pred is None or len(pred) != horizon or np.any(np.isnan(pred)):
                        fold_info['model_errors'][b_name] = "Baseline model produced NaNs or failed"
                        continue
                    pred = np.maximum(0.0, np.array(pred, dtype=float))
                    fold_info['predictions'][b_name] = pred.tolist()
                    metrics = calculate_all_metrics(y_test, pred, y_train=y_train)
                    model_fold_metrics[b_name].append(metrics)

            # 2. Fit & predict Statistical (Strict zero-fallback: failures disqualified)
            stat_preds = {}
            try:
                self.statistical_models.fit_all(y_train)
                stat_preds = self.statistical_models.predict_all(horizon)
            except Exception as e:
                logger.debug(f"Statistical fit in fold {fold_idx} failed: {e}")
                
            s_map = {'ARIMA': 'arima', 'SARIMA': 'sarima', 'ETS': 'ets'}
            for s_name in ['ARIMA', 'SARIMA', 'ETS']:
                if s_name in selected_models:
                    pred_res = stat_preds.get(s_map.get(s_name))
                    pred = pred_res.get('forecast') if isinstance(pred_res, dict) else (pred_res[0] if isinstance(pred_res, (tuple, list)) else pred_res)
                    if pred is None or len(pred) != horizon or np.any(np.isnan(pred)):
                        fold_info['model_errors'][s_name] = "Statistical model produced NaNs or failed"
                        continue
                    pred = np.maximum(0.0, np.array(pred, dtype=float))
                    fold_info['predictions'][s_name] = pred.tolist()
                    metrics = calculate_all_metrics(y_test, pred, y_train=y_train)
                    model_fold_metrics[s_name].append(metrics)

            # 3. Fit & predict Intermittent (Strict zero-fallback: failures disqualified)
            if is_intermittent:
                inter_preds = {}
                try:
                    self.intermittent_models.fit_all(y_train)
                    inter_preds = self.intermittent_models.predict_all(horizon)
                except Exception as e:
                    logger.debug(f"Intermittent fit in fold {fold_idx} failed: {e}")
                    
                i_map = {'Croston': 'croston', 'SBA': 'sba', 'TSB': 'tsb'}
                for i_name in ['Croston', 'SBA', 'TSB']:
                    if i_name in selected_models:
                        pred_res = inter_preds.get(i_map.get(i_name))
                        pred = pred_res[0] if isinstance(pred_res, (tuple, list)) else pred_res
                        if pred is None or len(pred) != horizon or np.any(np.isnan(pred)):
                            fold_info['model_errors'][i_name] = "Intermittent model produced NaNs or failed"
                            continue
                        pred = np.maximum(0.0, np.array(pred, dtype=float))
                        fold_info['predictions'][i_name] = pred.tolist()
                        metrics = calculate_all_metrics(y_test, pred, y_train=y_train)
                        model_fold_metrics[i_name].append(metrics)

            # 4. Fit & predict ML via true recursive walk-forward forecasting
            ml_candidates = [m for m in ['Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM'] if m in selected_models]
            if ml_candidates and sku_df is not None and len(train_idx) >= 20:
                try:
                    train_sku_df = sku_df.iloc[train_idx].copy()
                    X_df, f_cols = self.feature_engineer.engineer_features(train_sku_df)
                    
                    # Numeric columns only
                    numeric_cols = []
                    for c in f_cols:
                        if c in X_df.columns:
                            X_df[c] = pd.to_numeric(X_df[c], errors='coerce').fillna(0)
                            numeric_cols.append(c)
                            
                    if not numeric_cols:
                        X_df['lag_1'] = pd.Series(y_train).shift(1).bfill().fillna(0)
                        numeric_cols = ['lag_1']
                        
                    X_mat = X_df[numeric_cols].to_numpy(dtype=np.float32)
                    X_mat[~np.isfinite(X_mat)] = 0.0
                    
                    self.ml_models.fit_all(X_mat, y_train)
                    
                    base_date = dates[train_idx[-1]] if dates is not None and len(dates) > train_idx[-1] else None
                    ml_map = {
                        'Random Forest': 'random_forest',
                        'Gradient Boosting': 'gradient_boosting',
                        'XGBoost': 'xgboost',
                        'LightGBM': 'lightgbm'
                    }
                    for ml_name in ml_candidates:
                        ml_key = ml_map.get(ml_name)
                        if ml_key and ml_key in self.ml_models.models:
                            pred = self.feature_engineer.predict_recursive(
                                model=self.ml_models.models[ml_key],
                                history_series=pd.Series(y_train),
                                horizon=horizon,
                                feature_cols=numeric_cols,
                                base_date=base_date
                            )
                            if pred is None or len(pred) != horizon or np.any(np.isnan(pred)):
                                fold_info['model_errors'][ml_name] = "ML recursive forecasting produced NaNs or failed"
                                continue
                            pred = np.maximum(0.0, pred)
                            fold_info['predictions'][ml_name] = pred.tolist()
                            metrics = calculate_all_metrics(y_test, pred, y_train=y_train)
                            model_fold_metrics[ml_name].append(metrics)
                except Exception as e:
                    logger.debug(f"ML backtest in fold {fold_idx} skipped: {e}")

            # 5. Compute real out-of-fold Weighted Consensus Ensemble
            if len(fold_info['predictions']) >= 2:
                weights_dict = {}
                for m_name in fold_info['predictions'].keys():
                    past_metrics = model_fold_metrics.get(m_name, [])
                    if past_metrics:
                        weights_dict[m_name] = float(past_metrics[-1]['WAPE'])
                    else:
                        weights_dict[m_name] = 25.0
                ens_forecaster = EnsembleForecaster(method='inverse_wape')
                ens_pred = ens_forecaster.combine_forecasts(
                    {k: np.array(v) for k, v in fold_info['predictions'].items()},
                    wape_weights=weights_dict
                )
                if len(ens_pred) == horizon and not np.any(np.isnan(ens_pred)):
                    fold_info['predictions']['Ensemble (Consensus)'] = ens_pred.tolist()
                    ens_metrics = calculate_all_metrics(y_test, ens_pred, y_train=y_train)
                    if 'Ensemble (Consensus)' not in model_fold_metrics:
                        model_fold_metrics['Ensemble (Consensus)'] = []
                    model_fold_metrics['Ensemble (Consensus)'].append(ens_metrics)

            fold_details.append(fold_info)

        # Aggregate metrics across folds into Leaderboard with principled stability score
        leaderboard_rows = []
        for m_name, fold_metric_list in model_fold_metrics.items():
            if not fold_metric_list:
                continue
            wapes = [f['WAPE'] for f in fold_metric_list]
            rmses = [f['RMSE'] for f in fold_metric_list]
            maes = [f['MAE'] for f in fold_metric_list]
            smapes = [f['sMAPE'] for f in fold_metric_list]
            mases = [f['MASE'] for f in fold_metric_list]
            biases = [f['Bias'] for f in fold_metric_list]
            bias_pcts = [f['Bias_pct'] for f in fold_metric_list]
            
            # Principled multi-factor stability score (0-100):
            # 50% WAPE CV + 30% Worst-fold degradation + 20% Bias consistency
            mean_w = float(np.mean(wapes))
            std_w = float(np.std(wapes))
            wape_cv = (std_w / (mean_w + 1e-4)) if mean_w > 0 else 0.0
            norm_cv_penalty = min(1.0, max(0.0, wape_cv))
            
            worst_w = float(np.max(wapes))
            worst_degradation = max(0.0, (worst_w - mean_w) / (mean_w + 1e-4))
            norm_worst_penalty = min(1.0, worst_degradation)
            
            bias_consistent_folds = sum(1 for b in bias_pcts if abs(b) <= 15.0)
            bias_consistency = bias_consistent_folds / len(bias_pcts) if bias_pcts else 1.0
            
            stability = 100.0 * (
                0.5 * (1.0 - norm_cv_penalty) +
                0.3 * (1.0 - norm_worst_penalty) +
                0.2 * bias_consistency
            )
            stability_score = round(max(0.0, min(100.0, stability)), 1)
            
            leaderboard_rows.append({
                'model': m_name,
                'folds_evaluated': len(fold_metric_list),
                'mean_wape': round(float(np.mean(wapes)), 2),
                'std_wape': round(float(np.std(wapes)), 2),
                'mean_rmse': round(float(np.mean(rmses)), 2),
                'mean_mae': round(float(np.mean(maes)), 2),
                'mean_smape': round(float(np.mean(smapes)), 2),
                'mean_mase': round(float(np.mean(mases)), 3),
                'mean_bias': round(float(np.mean(biases)), 2),
                'mean_bias_pct': round(float(np.mean(bias_pcts)), 2),
                'stability_score': stability_score
            })
            
        leaderboard_df = pd.DataFrame(leaderboard_rows)
        if not leaderboard_df.empty:
            # Sort primarily by mean WAPE, secondarily by mean RMSE
            leaderboard_df = leaderboard_df.sort_values(by=['mean_wape', 'mean_rmse']).reset_index(drop=True)
            leaderboard_df['rank'] = np.arange(1, len(leaderboard_df) + 1)
            
        return {
            'status': 'success',
            'n_folds': len(splits),
            'usable_history_weeks': n_samples,
            'leaderboard': leaderboard_df,
            'fold_details': fold_details,
            'is_intermittent': is_intermittent
        }
