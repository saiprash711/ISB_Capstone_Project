"""
Automated Model Selector
Orchestrates end-to-end demand profiling, candidate model generation,
rolling-origin backtesting, and champion model selection with transparent reasoning.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging

from .demand_classifier import DemandClassifier
from .champion_challenger import ChampionChallengerManager
from src.validation.backtesting import RollingOriginBacktest
from src.validation.cross_validation import ModelLeaderboard
from src.forecasting.baseline import BaselineForecastingModels
from src.forecasting.statistical import StatisticalModels
from src.forecasting.intermittent import IntermittentDemandModels
from src.forecasting.ml_models import MLModels
from src.features import FeatureEngineer

from src.uncertainty.prediction_intervals import ProbabilisticForecastEngine
from src.monitoring.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Automated decision engine for selecting the champion model for a SKU x Branch.
    """
    
    def __init__(self, config: Optional[Any] = None, n_folds: Optional[int] = None, 
                 test_weeks: Optional[int] = None, min_train_weeks: Optional[int] = None):
        self.classifier = DemandClassifier()
        self.backtester = RollingOriginBacktest(
            config=config, n_folds=n_folds, test_weeks=test_weeks, min_train_weeks=min_train_weeks
        )
        self.governance = ChampionChallengerManager()
        self.feature_engineer = FeatureEngineer()
        self.probabilistic_engine = ProbabilisticForecastEngine(target_coverage=0.80)
        self.registry = ModelRegistry()

    def select_and_fit(self, df: pd.DataFrame, sku: str, branch: str, 
                       horizon: int = 12) -> Dict[str, Any]:
        """
        Execute full automated model selection workflow:
        1. Extract & prepare SKU × Branch series
        2. Profile demand & classify pattern
        3. Identify candidate models
        4. Execute rolling-origin backtest
        5. Rank candidates & assign Champion / Challengers
        6. Generate forward forecast from Champion with calibrated P10/P50/P90 intervals
        """
        # 1. Resolve column names flexibly across both clean data mart and raw transaction frames
        sku_col = next((c for c in ['sku', 'Material', 'material', 'Material Description'] if c in df.columns), None)
        branch_col = next((c for c in ['branch', 'SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Branch', 'Region'] if c in df.columns), None)
        date_col = next((c for c in ['date', 'Billing Date', 'billing_date'] if c in df.columns), None)
        demand_col = next((c for c in ['total_demand', 'Billing Quantity ODU', 'quantity_odu', 'demand'] if c in df.columns), None)

        if sku_col is None:
            return {'status': 'failed', 'sku': sku, 'branch': branch, 'error': 'SKU dimension missing from dataset'}

        if branch_col is not None and branch:
            subset = df[(df[sku_col].astype(str) == str(sku)) & (df[branch_col].astype(str) == str(branch))].copy()
        else:
            subset = df[df[sku_col].astype(str) == str(sku)].copy()

        if len(subset) < 4:
            return {
                'status': 'failed',
                'sku': sku,
                'branch': branch,
                'error': f'Insufficient records ({len(subset)})'
            }

        # Check if already aggregated weekly by date (e.g. standard data mart)
        if 'total_demand' in subset.columns and 'date' in subset.columns and not subset.duplicated(subset=['date']).any():
            sku_data = subset.copy()
            if 'sku' not in sku_data.columns:
                sku_data['sku'] = sku
            if 'branch' not in sku_data.columns:
                sku_data['branch'] = branch
            sku_data = sku_data.sort_values('date').reset_index(drop=True)
        elif date_col is not None and demand_col is not None:
            subset[date_col] = pd.to_datetime(subset[date_col], errors='coerce')
            subset = subset.dropna(subset=[date_col])
            
            # Combine ODU and IDU if present in raw transaction frame
            if 'Billing Quantity IDU' in subset.columns and demand_col == 'Billing Quantity ODU':
                subset['_calc_demand'] = pd.to_numeric(subset['Billing Quantity ODU'], errors='coerce').fillna(0) + \
                                         pd.to_numeric(subset['Billing Quantity IDU'], errors='coerce').fillna(0)
                metric_col = '_calc_demand'
            else:
                metric_col = demand_col
                subset[metric_col] = pd.to_numeric(subset[metric_col], errors='coerce').fillna(0)

            weekly = subset.groupby(pd.Grouper(key=date_col, freq='W-MON'))[metric_col].sum().reset_index()
            weekly = weekly.sort_values(date_col).reset_index(drop=True)
            weekly['sku'] = sku
            weekly['branch'] = branch
            weekly = weekly.rename(columns={date_col: 'date', metric_col: 'total_demand'})
            sku_data = weekly
        else:
            sku_data = subset.copy()
            if demand_col and demand_col != 'total_demand':
                sku_data['total_demand'] = pd.to_numeric(sku_data[demand_col], errors='coerce').fillna(0)
            if 'sku' not in sku_data.columns:
                sku_data['sku'] = sku
            if 'branch' not in sku_data.columns:
                sku_data['branch'] = branch

        if len(sku_data) < 4:
            return {
                'status': 'failed',
                'sku': sku,
                'branch': branch,
                'error': f'Insufficient records after temporal aggregation ({len(sku_data)})'
            }

        sku_data['total_demand'] = np.maximum(0.0, pd.to_numeric(sku_data['total_demand'], errors='coerce').fillna(0.0))
        y = sku_data['total_demand'].values.astype(float)
        dates = sku_data['date'].values if 'date' in sku_data.columns else None
        
        # 2. Demand Profiling
        profile = self.classifier.profile_demand(y, dates=dates)
        candidates = profile.get('candidate_models', ['Naive', 'Moving Average', 'Exponential Smoothing'])
        
        # 3. Rolling-Origin Backtesting
        bt_results = self.backtester.evaluate_sku_series(
            y, dates=dates, sku_df=sku_data, candidate_models=candidates
        )
        leaderboard_df = bt_results.get('leaderboard', pd.DataFrame())
        
        # 4. Governance & Champion Selection
        gov_entry = self.governance.register_evaluation(sku, branch, leaderboard_df, profile)
        champion_meta = gov_entry.get('champion', {})
        champion_name = champion_meta.get('model_name', 'Moving Average')
        
        # 5. Fit Champion on entire history to produce final forward point forecast
        point_forecast = self._generate_champion_point_forecast(
            champion_name, y, sku_data, horizon
        )
        
        # Extract backtest residuals for champion to calibrate P10, P50, P90
        residuals = []
        for fold in bt_results.get('fold_details', []):
            acts = np.array(fold.get('actuals', []))
            preds = np.array(fold.get('predictions', {}).get(champion_name, []))
            if len(acts) == len(preds) and len(acts) > 0:
                residuals.extend((acts - preds).tolist())
                
        calib_res = self.probabilistic_engine.calibrate_intervals(
            point_forecast=point_forecast,
            historical_residuals=np.array(residuals) if len(residuals) >= 4 else None,
            historical_actuals=y,
            rmse_estimate=champion_meta.get('mean_rmse')
        )
        
        p10 = calib_res['p10']
        p50 = calib_res['p50']
        p90 = calib_res['p90']
        
        # Register Champion in persistent ModelRegistry with demand classification
        try:
            self.registry.register_model(
                sku=sku,
                branch=branch,
                model_name=champion_name,
                validation_metrics=champion_meta,
                hyperparameters={'horizon': horizon, 'n_folds': bt_results.get('n_folds', 0)},
                feature_list=list(sku_data.columns),
                demand_class=profile.get('demand_type', 'Standard'),
                status=champion_meta.get('status', 'ACTIVE_CHAMPION')
            )
        except Exception as e:
            logger.debug(f"Registry persist skipped: {e}")
        
        # Baseline lift comparison
        lb_manager = ModelLeaderboard(leaderboard_df)
        baseline_comp = lb_manager.compare_with_baseline()
        
        return {
            'status': 'success',
            'sku': sku,
            'branch': branch,
            'horizon': horizon,
            'demand_profile': profile,
            'candidate_models': candidates,
            'backtest_folds': bt_results.get('n_folds', 0),
            'leaderboard': leaderboard_df,
            'leaderboard_display': lb_manager.to_display_table(),
            'champion': champion_meta,
            'challengers': gov_entry.get('challengers', []),
            'baseline_comparison': baseline_comp,
            'forecast': point_forecast,
            'forward_forecast': p50,
            'lower_bound': p10,
            'upper_bound': p90,
            'p10': p10,
            'p50': p50,
            'p90': p90,
            'interval_calibration': calib_res,
            'selection_reason': champion_meta.get('selection_reason', 'Top backtested accuracy'),
            'historical_dates': dates,
            'historical_demand': y,
            'historical_residuals': residuals
        }

    def _generate_champion_point_forecast(self, model_name: str, y: np.ndarray, 
                                          sku_data: pd.DataFrame, horizon: int) -> np.ndarray:
        """Fit specified champion model on all available history and return true forward forecast."""
        # Baseline family
        b_map = {
            'Naive': 'naive',
            'Seasonal Naive': 'seasonal_naive',
            'Moving Average': 'moving_average',
            'Exponential Smoothing': 'exponential_smoothing'
        }
        if model_name in b_map:
            bm = BaselineForecastingModels()
            bm.fit_all(y)
            preds = bm.predict_all(horizon)
            pred = preds.get(b_map[model_name])
            if pred is not None and len(pred) == horizon and not np.any(np.isnan(pred)):
                return np.maximum(0.0, np.array(pred, dtype=float))
            
        # Statistical family
        s_map = {'ARIMA': 'arima', 'SARIMA': 'sarima', 'ETS': 'ets'}
        if model_name in s_map:
            sm = StatisticalModels()
            sm.fit_all(y)
            preds = sm.predict_all(horizon)
            pred_obj = preds.get(s_map[model_name])
            if isinstance(pred_obj, dict):
                pred = pred_obj.get('forecast')
            elif isinstance(pred_obj, (tuple, list)):
                pred = pred_obj[0]
            else:
                pred = pred_obj
            if pred is not None and len(pred) == horizon and not np.any(np.isnan(pred)):
                return np.maximum(0.0, np.array(pred, dtype=float))
            
        # Intermittent family
        i_map = {'Croston': 'croston', 'SBA': 'sba', 'TSB': 'tsb'}
        if model_name in i_map:
            im = IntermittentDemandModels()
            im.fit_all(y)
            preds = im.predict_all(horizon)
            pred_obj = preds.get(i_map[model_name])
            pred = pred_obj[0] if isinstance(pred_obj, (tuple, list)) else pred_obj
            if pred is not None and len(pred) == horizon and not np.any(np.isnan(pred)):
                return np.maximum(0.0, np.array(pred, dtype=float))
            
        # ML family (True recursive walk-forward forecasting)
        ml_map = {
            'Random Forest': 'random_forest',
            'Gradient Boosting': 'gradient_boosting',
            'XGBoost': 'xgboost',
            'LightGBM': 'lightgbm'
        }
        if model_name in ml_map:
            try:
                X_df, f_cols = self.feature_engineer.engineer_features(sku_data)
                num_cols = [c for c in f_cols if c in X_df.columns and pd.api.types.is_numeric_dtype(X_df[c])]
                if not num_cols:
                    num_cols = ['lag_1']
                    X_df['lag_1'] = pd.Series(y).shift(1).bfill().fillna(0)
                X_mat = X_df[num_cols].to_numpy(dtype=np.float32)
                X_mat[~np.isfinite(X_mat)] = 0.0
                
                ml_hub = MLModels()
                ml_hub.fit_all(X_mat, y)
                ml_key = ml_map[model_name]
                if ml_key in ml_hub.models:
                    base_date = sku_data['date'].iloc[-1] if 'date' in sku_data.columns and len(sku_data) > 0 else None
                    pred = self.feature_engineer.predict_recursive(
                        model=ml_hub.models[ml_key],
                        history_series=pd.Series(y),
                        horizon=horizon,
                        feature_cols=num_cols,
                        base_date=base_date
                    )
                    if pred is not None and len(pred) == horizon and not np.any(np.isnan(pred)):
                        return np.maximum(0.0, pred)
            except Exception as e:
                logger.warning(f"ML forecast error: {e}")

        # Legitimate fallback to robust Moving Average if specific architecture failed to converge
        bm = BaselineForecastingModels()
        bm.fit_all(y)
        preds = bm.predict_all(horizon)
        ma_pred = preds.get('moving_average', preds.get('naive'))
        if ma_pred is not None and len(ma_pred) == horizon and not np.any(np.isnan(ma_pred)):
            return np.maximum(0.0, np.array(ma_pred, dtype=float))
            
        return np.maximum(0.0, np.full(horizon, float(np.mean(y)) if len(y) > 0 else 0.0))
