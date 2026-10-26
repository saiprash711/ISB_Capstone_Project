"""
Per-model out-of-sample validation against FY24-25 actual billing.

`run_origin` reproduces the production workflow at one forecast origin, using
only data up to that origin: the champion tournament (ModelSelector) plus the
forward forecast of EVERY candidate model, the backtest-weighted ensemble and
the auto-selected champion. The batch harness (validate_holdout_fy25.py) and
the dashboard's model validation panel both call it, so per-model results are
identical wherever they are shown.
"""
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from src.forecasting.model_zoo import ENSEMBLE_NAME, combine, forecast_models, future_week_dates, inverse_wape_weights
from src.selection.model_selector import ModelSelector

CHAMPION_LABEL = 'Champion (auto-selected)'


def run_origin(df_upto: pd.DataFrame, sku: Optional[str], branches: Union[str, Sequence[str], None],
               horizon: int, models: Optional[List[str]] = None, coverage: float = 0.80) -> Dict[str, Any]:
    """
    Tournament + forward forecast of every candidate at one origin (the last week in `df_upto`).

    Returns dict with status, champion result (`res`), `forecasts` {model: array} including the
    ensemble and CHAMPION_LABEL, `errors` {model: reason}, `dates` (forecast weeks) and
    `backtest_wape` {model: mean backtest WAPE at this origin}.
    """
    sel = ModelSelector(target_coverage=coverage)
    sel.registry.save = lambda: None
    prep = sel.prepare_series(df_upto, sku, branches)
    if prep.get('status') != 'success':
        return {'status': 'failed', 'error': prep.get('error')}
    sku_data = prep['sku_data']
    res = sel.select_and_fit_series(sku_data, prep['profile_factory'], sku=sku_data['sku'].iloc[0],
                                    branch=prep['branch_label'], horizon=horizon, target_coverage=coverage,
                                    candidate_models=models)
    if res.get('status') != 'success':
        return {'status': 'failed', 'error': res.get('error')}

    y = sku_data['total_demand'].values.astype(float)
    dates = pd.DatetimeIndex(sku_data['date'])
    lb = res['leaderboard'].set_index('model')
    members = [m for m in lb.index if m != ENSEMBLE_NAME]
    fwd, errs, _ = forecast_models(members, y, dates, horizon, profile=prep['profile_factory'](dates[-1]),
                                   sku_df=sku_data, feature_engineer=sel.feature_engineer)
    if ENSEMBLE_NAME in lb.index:
        ens = combine(fwd, inverse_wape_weights({m: lb.loc[m, 'mean_wape'] for m in fwd}))
        if ens is not None:
            fwd[ENSEMBLE_NAME] = ens
    fwd[CHAMPION_LABEL] = np.asarray(res['forecast'], dtype=float)
    errs.update({m: r for m, r in (res.get('model_errors') or {}).items() if m not in fwd})
    return {
        'status': 'success', 'res': res, 'forecasts': fwd, 'errors': errs,
        'dates': future_week_dates(dates, horizon),
        'backtest_wape': lb['mean_wape'].to_dict(),
        'champion': res['champion'].get('model_name'),
    }


def holdout_actuals(panel: pd.DataFrame, sku: str, branches: Union[str, Sequence[str], None],
                    start, end) -> pd.Series:
    """Weekly actual demand of a SKU over one, several or all branches between start and end (inclusive)."""
    d = panel[(panel.sku == sku) & (panel.date >= pd.Timestamp(start)) & (panel.date <= pd.Timestamp(end))]
    if branches:
        bl = [branches] if isinstance(branches, str) else list(branches)
        d = d[d.branch.isin(bl)]
    weeks = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq='W-MON')
    return d.groupby('date')['total_demand'].sum().reindex(weeks, fill_value=0.0)


def validate_series(panel: pd.DataFrame, sku: str, branches: Union[str, Sequence[str], None],
                    origins: Sequence[pd.Timestamp], horizon: int, holdout_end: pd.Timestamp,
                    models: Optional[List[str]] = None, progress=None) -> Dict[str, Any]:
    """
    Forecast every model from each origin (data up to the origin only) and line the forecasts
    up with actual billing. One origin = one-shot holdout; several = rolling re-forecast.
    """
    rows, errors, backtest, champions = [], {}, {}, {}
    for i, o in enumerate(origins):
        h = min(horizon, int((pd.Timestamp(holdout_end) - pd.Timestamp(o)).days // 7))
        if h < 1:
            continue
        out = run_origin(panel[panel.date <= o], sku, branches, h, models)
        if progress:
            progress((i + 1) / len(origins))
        if out['status'] != 'success':
            errors[str(pd.Timestamp(o).date())] = out.get('error')
            continue
        champions[pd.Timestamp(o)] = out['champion']
        if not backtest:
            backtest = dict(out['backtest_wape'])
            backtest[CHAMPION_LABEL] = backtest.get(out['champion'], np.nan)
        errors.update(out['errors'])
        for m, f in out['forecasts'].items():
            for step, (wk, v) in enumerate(zip(out['dates'], f), 1):
                rows.append({'origin': pd.Timestamp(o), 'model': m, 'step': step, 'week': wk, 'forecast': float(v)})
    fc = pd.DataFrame(rows)
    if fc.empty:
        return {'status': 'failed', 'error': next(iter(errors.values()), 'no forecasts'), 'errors': errors}
    act = holdout_actuals(panel, sku, branches, fc.week.min(), fc.week.max())
    fc['actual'] = fc.week.map(act).fillna(0.0)
    return {'status': 'success', 'forecasts': fc, 'actuals': act, 'errors': errors,
            'backtest_wape': backtest, 'champions': champions}


def from_batch(mdf: pd.DataFrame, panel: pd.DataFrame, sku: str, branch: str, holdout_end) -> Optional[Dict[str, Any]]:
    """Same structure as validate_series, built from the batch harness output (models_<mode>.parquet)."""
    d = mdf[(mdf.sku == sku) & (mdf.branch == branch)]
    if d.empty:
        return None
    fc = d[['origin', 'model', 'step', 'week', 'forecast']].copy()
    fc['origin'], fc['week'] = pd.to_datetime(fc['origin']), pd.to_datetime(fc['week'])
    act = holdout_actuals(panel, sku, branch, fc.week.min(), min(fc.week.max(), pd.Timestamp(holdout_end)))
    fc['actual'] = fc.week.map(act).fillna(0.0)
    first = fc.origin.min()
    bt = d[pd.to_datetime(d.origin) == first].groupby('model')['backtest_wape'].first().dropna().to_dict()
    return {'status': 'success', 'forecasts': fc, 'actuals': act, 'errors': {}, 'backtest_wape': bt,
            'champions': {o: None for o in fc.origin.unique()}, 'source': 'batch'}


def score_models(fc: pd.DataFrame, backtest_wape: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """
    Per-model accuracy on the holdout at weekly and monthly grain (rolling: pass one lag band).

    Ranked on monthly RMSE - the same mean-targeting rule the champion tournament uses. WAPE is
    minimised by the median, so on lumpy SKUs a model that forecasts zero would 'win' on WAPE;
    such models are flagged in the 'Note' column.
    """
    def _w(a, f):
        return np.abs(a - f).sum() / a.sum() * 100 if a.sum() else np.nan

    out = []
    for m, d in fc.groupby('model'):
        wk = d.groupby('week')[['actual', 'forecast']].sum()
        mo = d.assign(month=d.week.dt.to_period('M')).groupby('month')[['actual', 'forecast']].sum()
        w_wk, w_mo = _w(wk.actual, wk.forecast), _w(mo.actual, mo.forecast)
        out.append({
            'Model': m,
            'Weekly WAPE %': round(w_wk, 1),
            'Monthly WAPE %': round(w_mo, 1),
            'Monthly accuracy %': round(max(0.0, 100 - w_mo), 1) if np.isfinite(w_mo) else np.nan,
            'Bias %': round((wk.forecast.sum() - wk.actual.sum()) / wk.actual.sum() * 100, 1) if wk.actual.sum() else np.nan,
            'Monthly RMSE': round(float(np.sqrt(np.mean((mo.actual - mo.forecast) ** 2))), 1),
            'Weeks scored': int(len(wk)),
            'Forecast units': round(wk.forecast.sum()),
            'Actual units': round(wk.actual.sum()),
            'Backtest WAPE % (pre-holdout)': round(backtest_wape[m], 1) if backtest_wape and m in backtest_wape else np.nan,
        })
    t = pd.DataFrame(out).sort_values(['Monthly RMSE', 'Monthly WAPE %']).reset_index(drop=True)
    t.insert(0, 'Holdout rank', range(1, len(t) + 1))
    near_zero = t['Forecast units'] <= 0.05 * t['Actual units'].clip(lower=1)
    t['Note'] = np.where(near_zero, 'forecasts ~zero', '')
    return t
