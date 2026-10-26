"""
Holdout (out-of-sample) validation scoring shared by the CLI runner
(validate_holdout_fy25.py) and the dashboard Holdout Validation page.

Reads precomputed artefacts from holdout_validation/:
  weekly_panel.parquet       SKU x Branch x Week (W-MON) ODU demand, train + holdout
  forecasts_static.parquet   52-week forecasts from the 30-Jun-2024 origin
  forecasts_rolling.parquet  12-week forecasts re-issued every 4 weeks
  verification.json          data verification checks on the holdout file
"""
import json
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

OUT_DIR = "holdout_validation"
PANEL_PATH = os.path.join(OUT_DIR, "weekly_panel.parquet")
VERIFICATION_PATH = os.path.join(OUT_DIR, "verification.json")
TRAIN_END_WEEK = pd.Timestamp("2024-07-01")    # W-MON label of last training week
HOLDOUT_END_WEEK = pd.Timestamp("2025-06-30")

LEVELS = {
    'SKU x Branch x Week': ['sku', 'branch', 'week'],
    'SKU x Branch x Month': ['sku', 'branch', 'month'],
    'SKU x Month (South)': ['sku', 'month'],
    'Branch x Month': ['branch', 'month'],
    'South Region x Month': ['month'],
    'South Region x Quarter': ['quarter'],
}


def forecast_path(mode: str) -> str:
    return os.path.join(OUT_DIR, f"forecasts_{mode}.parquet")


def load_panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL_PATH)


def load_verification() -> List[Dict]:
    if not os.path.exists(VERIFICATION_PATH):
        return []
    with open(VERIFICATION_PATH, encoding='utf-8') as f:
        return json.load(f)


def metrics(a, f) -> Dict[str, float]:
    a, f = np.asarray(a, float), np.asarray(f, float)
    sa = a.sum()
    wape = np.abs(a - f).sum() / sa * 100 if sa else np.nan
    return {'actual': round(sa), 'forecast': round(f.sum()), 'WAPE %': round(wape, 1),
            'Accuracy %': round(100 - wape, 1),
            'Bias %': round((f.sum() - sa) / sa * 100, 1) if sa else np.nan}


def score_levels(df: pd.DataFrame, fcols: List[str], levels: Optional[Dict] = None) -> pd.DataFrame:
    """Accuracy of each forecast column against `actual`, aggregated at each hierarchy level."""
    out = []
    for lvl_name, keys in (levels or LEVELS).items():
        g = df.groupby(keys)[['actual'] + fcols].sum()
        for fc in fcols:
            out.append(dict(level=lvl_name, method=fc, **metrics(g['actual'], g[fc])))
    return pd.DataFrame(out)


def holdout_actuals(panel: pd.DataFrame) -> pd.DataFrame:
    hold = panel[(panel.date > TRAIN_END_WEEK) & (panel.date <= HOLDOUT_END_WEEK)]
    return hold.rename(columns={'date': 'week', 'total_demand': 'actual'})[['sku', 'branch', 'week', 'actual']]


def add_periods(df: pd.DataFrame) -> pd.DataFrame:
    df['month'] = df['week'].dt.to_period('M').astype(str)
    df['quarter'] = df['week'].dt.to_period('Q-MAR').astype(str)
    return df


def _demand_lookup(panel: pd.DataFrame) -> pd.Series:
    return panel.set_index(['sku', 'branch', 'date'])['total_demand']


def build_static_grid(panel: pd.DataFrame, fc: pd.DataFrame) -> pd.DataFrame:
    """Every forecast series x every holdout week with actual, forecast, P10/P90 and seasonal naive."""
    ok = fc[fc.status == 'ok'].copy()
    ok['week'] = pd.to_datetime(ok['week'])
    series = ok[['sku', 'branch']].drop_duplicates()
    weeks = pd.date_range(TRAIN_END_WEEK + pd.Timedelta(weeks=1), HOLDOUT_END_WEEK, freq='W-MON')
    grid = series.merge(pd.DataFrame({'week': weeks}), how='cross')
    grid = grid.merge(ok[['sku', 'branch', 'week', 'forecast', 'p10', 'p90']], on=['sku', 'branch', 'week'], how='left')
    grid = grid.merge(holdout_actuals(panel), on=['sku', 'branch', 'week'], how='left').fillna({'actual': 0.0})
    ly = pd.MultiIndex.from_arrays([grid.sku, grid.branch, grid.week - pd.Timedelta(weeks=52)])
    grid['seasonal_naive'] = _demand_lookup(panel).reindex(ly).fillna(0.0).values
    return add_periods(grid)


def build_rolling_grid(panel: pd.DataFrame, fc: pd.DataFrame) -> pd.DataFrame:
    """Rolling forecasts with actual, 4-week moving average and seasonal naive benchmarks per origin."""
    lookup = _demand_lookup(panel)
    ro = fc[fc.status == 'ok'].copy()
    ro['week'] = pd.to_datetime(ro['week'])
    ro['origin'] = pd.to_datetime(ro['origin'])
    keys = ro[['sku', 'branch', 'origin']].drop_duplicates()
    ma = []
    for sku, br, o in keys.itertuples(index=False):
        idx = pd.MultiIndex.from_arrays([[sku] * 4, [br] * 4, pd.date_range(end=o, periods=4, freq='W-MON')])
        ma.append(lookup.reindex(idx).fillna(0).mean())
    keys['moving_avg_4w'] = ma
    ro = ro.merge(keys, on=['sku', 'branch', 'origin'], how='left')
    ly = pd.MultiIndex.from_arrays([ro.sku, ro.branch, ro.week - pd.Timedelta(weeks=52)])
    ro['seasonal_naive'] = lookup.reindex(ly).fillna(0.0).values
    ro = ro.merge(holdout_actuals(panel), on=['sku', 'branch', 'week'], how='left').fillna({'actual': 0.0})
    ro['lag_band'] = np.where(ro.step <= 4, 'lag 1-4 wks', np.where(ro.step <= 8, 'lag 5-8 wks', 'lag 9-12 wks'))
    return add_periods(ro)


def series_diagnostics(grid: pd.DataFrame, fc: pd.DataFrame) -> pd.DataFrame:
    """Per-series champion, backtest WAPE (as shown in dashboard) vs realised holdout WAPE."""
    ok = fc[fc.status == 'ok']
    meta = ok.groupby(['sku', 'branch']).agg(
        champion=('champion', 'first'), backtest_wape=('backtest_wape', 'first'),
        demand_type=('demand_type', 'first'),
        flat_forecast=('forecast', lambda s: s.round(3).nunique() == 1))

    def _one(d):
        a = d.actual.sum()
        return pd.Series({
            'actual': a, 'forecast': d.forecast.sum(),
            'holdout_wape': np.abs(d.actual - d.forecast).sum() / a * 100 if a else np.nan,
            'seasonal_naive_wape': np.abs(d.actual - d.seasonal_naive).sum() / a * 100 if a else np.nan,
            'p10_p90_coverage': ((d.actual >= d.p10) & (d.actual <= d.p90)).mean(),
        })
    err = grid.groupby(['sku', 'branch'])[['actual', 'forecast', 'seasonal_naive', 'p10', 'p90']].apply(_one)
    return meta.join(err).reset_index().sort_values('actual', ascending=False)


BASELINE_DIR = os.path.join(OUT_DIR, "baseline_v1")


def baseline_path(mode: str) -> str:
    """Forecasts of the original (pre-fix) engine, kept for the before/after comparison."""
    return os.path.join(BASELINE_DIR, f"forecasts_{mode}.parquet")


def score_vs_all_actuals(grid: pd.DataFrame, actuals: pd.DataFrame, fcols: List[str]) -> pd.DataFrame:
    """
    Branch x Month and Region x Month accuracy of the summed SKU forecasts against ALL billed
    demand, including new-launch SKUs no SKU-level model could forecast - the total a planner faces.
    """
    act = add_periods(actuals.copy()) if 'month' not in actuals.columns else actuals
    out = []
    for lvl, keys in {'Branch x Month (all SKUs)': ['branch', 'month'], 'South Region x Month (all SKUs)': ['month'],
                      'South Region x Quarter (all SKUs)': ['quarter']}.items():
        a = act.groupby(keys)['actual'].sum()
        for fc in fcols:
            f = grid.groupby(keys)[fc].sum().reindex(a.index).fillna(0.0)
            out.append(dict(level=lvl, method=fc, **metrics(a, f)))
    return pd.DataFrame(out)


CHAMPION_LABEL = 'Champion (auto-selected)'
MODEL_LEVELS = {'SKU x Branch x Week': ['sku', 'branch', 'week'], 'SKU x Branch x Month': ['sku', 'branch', 'month'],
                'Branch x Month': ['branch', 'month'], 'South Region x Month': ['month']}


def models_path(mode: str, partial: bool = False) -> str:
    return os.path.join(OUT_DIR, f"models_{mode}{'.partial' if partial else ''}.parquet")


def build_model_grid(panel: pd.DataFrame, mdf: pd.DataFrame, lag_band: Optional[str] = None) -> pd.DataFrame:
    """Every model's forecast per series x week joined with actual billing (rolling: one lag band)."""
    g = mdf.copy()
    g['week'] = pd.to_datetime(g['week'])
    if lag_band is not None:
        lo = {'lag 1-4 wks': 1, 'lag 5-8 wks': 5, 'lag 9-12 wks': 9}[lag_band]
        g = g[(g.step >= lo) & (g.step <= lo + 3)]
    g = g.merge(holdout_actuals(panel), on=['sku', 'branch', 'week'], how='left').fillna({'actual': 0.0})
    return add_periods(g)


def model_portfolio_scores(mg: pd.DataFrame) -> pd.DataFrame:
    """
    Accuracy of every model across all series it could forecast, and head-to-head against the
    auto-selected champion on exactly the same series (models are not available for every series).
    """
    champ = mg[mg.model == CHAMPION_LABEL]
    champ_vol = champ.drop_duplicates(['sku', 'branch', 'week'])['actual'].sum()
    rows = []
    for m, d in mg.groupby('model'):
        keys = d[['sku', 'branch']].drop_duplicates()
        c = champ.merge(keys, on=['sku', 'branch'])
        r = {'Model': m, 'Series': len(keys),
             'Volume covered %': round(d.drop_duplicates(['sku', 'branch', 'week'])['actual'].sum() / champ_vol * 100, 1)
             if champ_vol else np.nan}
        for lvl, k in MODEL_LEVELS.items():
            r[f'{lvl} WAPE %'] = metrics(d.groupby(k)['actual'].sum(), d.groupby(k)['forecast'].sum())['WAPE %']
        cm = c.groupby(MODEL_LEVELS['SKU x Branch x Month'])[['actual', 'forecast']].sum()
        dm = d.groupby(MODEL_LEVELS['SKU x Branch x Month'])[['actual', 'forecast']].sum()
        r['vs champion, same series (SKU x Branch x Month, pts)'] = round(
            metrics(dm['actual'], dm['forecast'])['WAPE %'] - metrics(cm['actual'], cm['forecast'])['WAPE %'], 1)
        r['Bias %'] = metrics(d['actual'], d['forecast'])['Bias %']
        rows.append(r)
    return pd.DataFrame(rows).sort_values('SKU x Branch x Month WAPE %').reset_index(drop=True)


def fit_summary(fc: pd.DataFrame) -> pd.DataFrame:
    """One row per model fit (origin x series): champion chosen and whether its forecast is a flat line."""
    ok = fc[fc.status == 'ok']
    return ok.groupby(['origin', 'sku', 'branch']).agg(
        champion=('champion', 'first'),
        flat_forecast=('forecast', lambda s: s.round(3).nunique() == 1)).reset_index()


def band_coverage(df: pd.DataFrame) -> float:
    d = df[df.p10.notna() & df.p90.notna()]
    return float(((d.actual >= d.p10) & (d.actual <= d.p90)).mean()) if len(d) else np.nan
