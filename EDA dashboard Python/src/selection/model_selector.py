"""
Automated Model Selector
Orchestrates end-to-end demand profiling, candidate model generation,
rolling-origin backtesting, and champion model selection with transparent reasoning.
"""
import numpy as np
import pandas as pd
from typing import Callable, Dict, Any, List, Optional, Sequence, Union
import logging

from .demand_classifier import DemandClassifier
from .champion_challenger import ChampionChallengerManager
from src.validation.backtesting import RollingOriginBacktest
from src.validation.cross_validation import ModelLeaderboard
from src.forecasting.model_zoo import (
    ENSEMBLE_NAME, MODEL_DESCRIPTIONS, combine, forecast_models, future_week_dates, inverse_wape_weights,
)
from src.forecasting.seasonal_profile import build_seasonal_profile, pooled_weekly
from src.features import FeatureEngineer
from src.uncertainty.prediction_intervals import ProbabilisticForecastEngine
from src.monitoring.registry import ModelRegistry

logger = logging.getLogger(__name__)

SYNTHETIC_SHEET = 'Evaluation_10_SKUs'
SKU_COLS = ['sku', 'Material', 'material', 'Material Description']
BRANCH_COLS = ['branch', 'SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Branch', 'Region']
DATE_COLS = ['date', 'Billing Date', 'billing_date']
DEMAND_COLS = ['total_demand', 'Billing Quantity ODU', 'quantity_odu', 'demand']


def _first_col(df: pd.DataFrame, options: Sequence[str]) -> Optional[str]:
    return next((c for c in options if c in df.columns), None)


def _row_demand(df: pd.DataFrame, demand_col: str) -> pd.Series:
    """Per-row demand; raw SAP rows combine ODU and IDU quantities (a material carries one of them)."""
    q = pd.to_numeric(df[demand_col], errors='coerce').fillna(0.0)
    if demand_col == 'Billing Quantity ODU' and 'Billing Quantity IDU' in df.columns:
        q = q + pd.to_numeric(df['Billing Quantity IDU'], errors='coerce').fillna(0.0)
    return q


class ModelSelector:
    """
    Automated decision engine for selecting the champion model for a SKU x Branch.
    """

    def __init__(self, config: Optional[Any] = None, n_folds: Optional[int] = None,
                 test_weeks: Optional[int] = None, min_train_weeks: Optional[int] = None,
                 target_coverage: float = 0.80):
        self.classifier = DemandClassifier()
        self.backtester = RollingOriginBacktest(
            config=config, n_folds=n_folds, test_weeks=test_weeks, min_train_weeks=min_train_weeks
        )
        self.governance = ChampionChallengerManager()
        self.feature_engineer = FeatureEngineer()
        self.target_coverage = target_coverage
        self.registry = ModelRegistry()

    # ------------------------------------------------------------------ data preparation
    def prepare_series(self, df: pd.DataFrame, sku: Optional[str],
                       branch: Union[str, Sequence[str], None] = None) -> Dict[str, Any]:
        """
        Build the weekly (W-MON) demand series for a SKU at one branch, a set of branches
        (aggregated) or the whole region, plus a leakage-safe seasonal-profile factory.
        `sku=None` aggregates all SKUs (outdoor units only, so IDU rows are not double counted).

        The series runs from the SKU's first sale to the dataset's as-of week, with
        zero-demand weeks filled, so forecasts always start after the latest data
        even for SKUs that have stopped selling.
        """
        sku_col, branch_col = _first_col(df, SKU_COLS), _first_col(df, BRANCH_COLS)
        date_col, demand_col = _first_col(df, DATE_COLS), _first_col(df, DEMAND_COLS)
        if sku_col is None or date_col is None or demand_col is None:
            return {'status': 'failed', 'error': 'SKU, date or demand dimension missing from dataset'}

        branches = None if branch in (None, '', 'All') else ([branch] if isinstance(branch, str) else list(branch))
        keep = [sku_col, branch_col, date_col, demand_col, 'Billing Quantity IDU', 'Data_Sheet', 'EXT MAT GROUP']
        work = df[list(dict.fromkeys(c for c in keep if c and c in df.columns))].copy()
        work['_date'] = pd.to_datetime(work[date_col], errors='coerce')
        work = work.dropna(subset=['_date'])
        if work.empty:
            return {'status': 'failed', 'error': 'No dated records'}
        work['_q'] = _row_demand(work, demand_col)
        as_of = work['_date'].max()
        if date_col != 'date':            # raw billing dates -> W-MON label of the latest week
            as_of = pd.Timestamp(as_of).to_period('W-MON').end_time.normalize()

        if sku is None:
            mask = pd.Series(True, index=work.index)
            if 'EXT MAT GROUP' in work.columns and (work['EXT MAT GROUP'] == 'RA-ODU').any():
                mask &= work['EXT MAT GROUP'] == 'RA-ODU'
        else:
            mask = work[sku_col].astype(str) == str(sku)
        if branches is not None and branch_col is not None:
            mask &= work[branch_col].astype(str).isin([str(b) for b in branches])
        sub = work[mask]
        weekly = sub.groupby(pd.Grouper(key='_date', freq='W-MON'))['_q'].sum().clip(lower=0.0)
        weekly = weekly[weekly.index <= as_of]
        nz = weekly[weekly > 0]
        if nz.empty:
            return {'status': 'failed', 'error': f"No positive demand for {sku or 'the selection'}"}
        idx = pd.date_range(nz.index.min(), as_of, freq='W-MON')
        y = weekly.reindex(idx, fill_value=0.0)
        label = ', '.join(branches) if branches else 'All'
        sku_label = 'All SKUs' if sku is None else str(sku)
        sku_data = pd.DataFrame({'date': idx, 'total_demand': y.values.astype(float), 'sku': sku_label, 'branch': label})

        # Pooled seasonal profile: real outdoor-unit billing only. Synthetic evaluation rows are
        # excluded, and so are IDU rows, which the source extract carries for Apr-Jun 2024 only
        # (pooling them would double that quarter and distort the seasonal shape).
        pool = work
        if 'Data_Sheet' in pool.columns:
            pool = pool[pool['Data_Sheet'].astype(str) != SYNTHETIC_SHEET]
        if 'EXT MAT GROUP' in pool.columns and (pool['EXT MAT GROUP'] == 'RA-ODU').any():
            pool = pool[pool['EXT MAT GROUP'] == 'RA-ODU']
        pw = pooled_weekly(pool, '_date', '_q', branch_col)
        region = pw['__region__']
        if branches is not None and branch_col is not None:
            parts = [pw[str(b)] for b in branches if str(b) in pw]
            branch_series = pd.concat(parts, axis=1).fillna(0.0).sum(axis=1) if parts else None
        else:
            branch_series = None
        cache: Dict[pd.Timestamp, Any] = {}

        def profile_factory(cutoff) -> Any:
            key = pd.Timestamp(cutoff)
            if key not in cache:
                cache[key] = build_seasonal_profile(region, branch_series, as_of=key, branch_weight=0.5)
            return cache[key]

        return {'status': 'success', 'sku_data': sku_data, 'as_of': as_of, 'branch_label': label,
                'profile_factory': profile_factory, 'n_records': int(mask.sum())}

    # ------------------------------------------------------------------ selection
    def select_and_fit(self, df: pd.DataFrame, sku: Optional[str], branch: Union[str, Sequence[str], None] = None,
                       horizon: int = 12, target_coverage: Optional[float] = None,
                       candidate_models: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute full automated model selection workflow:
        1. Extract & prepare the SKU x Branch weekly series (to the data as-of week)
        2. Profile demand & classify pattern
        3. Rolling-origin backtest of all applicable candidates (12-week folds)
        4. Rank candidates & assign Champion / Challengers
        5. Forward forecast from the Champion with calibrated intervals
        """
        prep = self.prepare_series(df, sku, branch)
        if prep.get('status') != 'success':
            return {'status': 'failed', 'sku': sku, 'branch': branch, 'error': prep.get('error')}
        return self.select_and_fit_series(prep['sku_data'], prep['profile_factory'], sku=prep['sku_data']['sku'].iloc[0],
                                          branch=prep['branch_label'], horizon=horizon,
                                          target_coverage=target_coverage, candidate_models=candidate_models)

    def select_and_fit_series(self, sku_data: pd.DataFrame, profile_factory: Optional[Callable] = None,
                              sku: str = '', branch: str = '', horizon: int = 12,
                              target_coverage: Optional[float] = None,
                              candidate_models: Optional[List[str]] = None) -> Dict[str, Any]:
        """Model selection on a prepared weekly frame with columns date, total_demand."""
        y = np.maximum(0.0, pd.to_numeric(sku_data['total_demand'], errors='coerce').fillna(0.0).values.astype(float))
        dates = pd.DatetimeIndex(sku_data['date'])
        if len(y) < 5 or np.count_nonzero(y) < 2:
            return {'status': 'failed', 'sku': sku, 'branch': branch,
                    'error': f'Insufficient history ({len(y)} weeks, {np.count_nonzero(y)} with demand)'}

        profile = profile_factory(dates[-1]) if profile_factory else None
        demand_profile = self.classifier.profile_demand(y, dates=dates.values)
        candidates = candidate_models or self.backtester.default_candidates(y, sku_data)
        demand_profile['candidate_models'] = candidates
        if profile is not None:
            demand_profile['pooled_seasonal_amplitude'] = round(max(profile.month_index.values()) /
                                                                max(1e-6, min(profile.month_index.values())), 2)

        bt = self.backtester.evaluate_sku_series(y, dates=dates, sku_df=sku_data,
                                                 candidate_models=candidates, profile_factory=profile_factory)
        leaderboard_df = bt.get('leaderboard', pd.DataFrame())
        if leaderboard_df.empty:
            return {'status': 'failed', 'sku': sku, 'branch': branch,
                    'error': bt.get('reason', 'No candidate model completed every backtest fold')}

        gov_entry = self.governance.register_evaluation(sku, branch, leaderboard_df, demand_profile)
        champion_meta = dict(gov_entry.get('champion', {}))
        ranked = leaderboard_df['model'].tolist()

        # Forward forecast: the ensemble needs every member; otherwise only the champion
        members = [m for m in ranked if m != ENSEMBLE_NAME]
        champion_name = champion_meta.get('model_name', ranked[0])
        to_fit = members if champion_name == ENSEMBLE_NAME else [champion_name]
        fwd, fwd_err, details = forecast_models(to_fit, y, dates, horizon, profile=profile, sku_df=sku_data,
                                                feature_engineer=self.feature_engineer)
        point_forecast, fallback_reason = None, None
        if champion_name == ENSEMBLE_NAME:
            wapes = leaderboard_df.set_index('model')['mean_wape'].to_dict()
            point_forecast = combine(fwd, inverse_wape_weights({m: wapes[m] for m in fwd if m in wapes}))
            details[ENSEMBLE_NAME] = {'weights': {m: round(w, 4) for m, w in
                                                  inverse_wape_weights({m: wapes[m] for m in fwd if m in wapes}).items()}}
        else:
            point_forecast = fwd.get(champion_name)
        if point_forecast is None:
            # Champion could not be refitted on the full history: next-ranked model, disclosed
            for alt in [m for m in members if m != champion_name]:
                f2, _, d2 = forecast_models([alt], y, dates, horizon, profile=profile, sku_df=sku_data,
                                            feature_engineer=self.feature_engineer)
                if alt in f2:
                    fallback_reason = (f"{champion_name} failed on full history "
                                       f"({fwd_err.get(champion_name, 'no forecast')}); using next-ranked {alt}.")
                    champion_meta.update({'model_name': alt, 'fallback_reason': fallback_reason})
                    point_forecast, details = f2[alt], {**details, **d2}
                    champion_name = alt
                    break
        if point_forecast is None:
            return {'status': 'failed', 'sku': sku, 'branch': branch, 'error': 'No model could produce a forward forecast'}

        # Out-of-sample backtest residuals of the champion calibrate the intervals
        residuals, res_preds = [], []
        for fold in bt.get('fold_details', []):
            acts = np.array(fold.get('actuals', []), dtype=float)
            preds = np.array(fold.get('predictions', {}).get(champion_name, []), dtype=float)
            if len(acts) == len(preds) and len(acts) > 0:
                residuals.extend((acts - preds).tolist())
                res_preds.extend(preds.tolist())
        coverage = target_coverage or self.target_coverage
        calib = ProbabilisticForecastEngine(target_coverage=coverage).calibrate_intervals(
            point_forecast=point_forecast,
            historical_residuals=np.array(residuals) if residuals else None,
            historical_predictions=np.array(res_preds) if res_preds else None,
            historical_actuals=y,
            rmse_estimate=champion_meta.get('rmse'),
            residual_horizon=self.backtester.test_weeks,
        )

        try:
            self.registry.register_model(
                sku=sku, branch=branch, model_name=champion_name, validation_metrics=champion_meta,
                hyperparameters={'horizon': horizon, 'n_folds': bt.get('n_folds', 0),
                                 'test_weeks': self.backtester.test_weeks},
                feature_list=list(sku_data.columns), demand_class=demand_profile.get('demand_type', 'Standard'),
                status=champion_meta.get('status', 'ACTIVE_CHAMPION'))
        except Exception as e:
            logger.debug(f"Registry persist skipped: {e}")

        lb_manager = ModelLeaderboard(leaderboard_df)
        return {
            'status': 'success',
            'sku': sku,
            'branch': branch,
            'horizon': horizon,
            'demand_profile': demand_profile,
            'candidate_models': candidates,
            'backtest_folds': bt.get('n_folds', 0),
            'backtest_test_weeks': self.backtester.test_weeks,
            'fold_details': bt.get('fold_details', []),
            'model_errors': {k: v for f in bt.get('fold_details', []) for k, v in f.get('model_errors', {}).items()},
            'leaderboard': leaderboard_df,
            'leaderboard_display': lb_manager.to_display_table(),
            'champion': champion_meta,
            'champion_description': MODEL_DESCRIPTIONS.get(champion_name, ''),
            'model_details': details.get(champion_name, details),
            'challengers': gov_entry.get('challengers', []),
            'baseline_comparison': lb_manager.compare_with_baseline(),
            'forecast': point_forecast,
            'forward_forecast': calib['p50'],
            'forecast_dates': future_week_dates(dates, horizon),
            'lower_bound': calib['p10'],
            'upper_bound': calib['p90'],
            'p10': calib['p10'],
            'p50': calib['p50'],
            'p90': calib['p90'],
            'interval_calibration': calib,
            'seasonal_profile': ({'month_index': profile.month_index, 'month_end_ratio': profile.last_week_ratio,
                                  'years_pooled': profile.n_years} if profile is not None else None),
            'selection_reason': champion_meta.get('selection_reason', 'Top backtested accuracy'),
            'fallback_reason': fallback_reason,
            'historical_dates': dates.values,
            'historical_demand': y,
            'historical_residuals': residuals,
            'historical_residual_predictions': res_preds,
        }
