"""
Out-of-sample holdout validation of the production forecasting engine against
actual FY24-25 billing (Jul-2024 to Jun-2025), which the models never saw.

Replicates the dashboard path (ForecastService -> ModelSelector.select_and_fit)
on SKU x Branch weekly (W-MON) ODU demand and records forecasts for scoring.

Experiments
  static  : train on history to 2024-06-30, forecast 52 weeks in one shot.
  rolling : every 4 weeks, retrain on history + actuals to date and forecast
            the next 12 weeks (dashboard default horizon).

Usage:
  python validate_holdout_fy25.py prepare
  python validate_holdout_fy25.py static
  python validate_holdout_fy25.py rolling
"""
import os
import sys
import time
import logging
import warnings
from multiprocessing import Pool

import numpy as np
import pandas as pd

HOLDOUT_XLSX = r"C:\Hansei\2024 July to 2025 June.xlsx"
TRAIN_PARQUET = "Filtered.parquet"
OUT_DIR = "holdout_validation"
PANEL_PATH = os.path.join(OUT_DIR, "weekly_panel.parquet")

TRAIN_END_WEEK = pd.Timestamp("2024-07-01")   # W-MON label of last training week
HOLDOUT_END_WEEK = pd.Timestamp("2025-06-30")
ROLLING_STEP_WEEKS = 4
ROLLING_HORIZON = 12
MIN_NONZERO_WEEKS = 4

HOLDOUT_COLS = [
    'Material', 'Billing Doc.', 'Item', 'SALES OFFICE CODE', 'Region', 'EXT MAT GROUP',
    'MatGroup3', 'Star Rating', 'INV/NI', 'Segment', 'Star Rating.1', 'SBU', 'Billing Date',
    'Customer', 'Billing Quantity ODU', 'Billing Quantity IDU', 'Tonnage', 'Tr.',
    'Dealer Name', 'Dealer Segment',
]


def prepare():
    """Build a clean weekly SKU x Branch ODU panel spanning training + holdout."""
    os.makedirs(OUT_DIR, exist_ok=True)

    tr = pd.read_parquet(TRAIN_PARQUET)
    tr = tr[(tr['Data_Sheet'] == 'Historical (Sheet1)') & (tr['EXT MAT GROUP'] == 'RA-ODU')]
    tr = tr[['Material', 'SALES OFFICE CODE', 'Billing Date', 'Billing Quantity ODU', 'Tonnage', 'Star Rating.1', 'Segment']]
    tr['source'] = 'train'

    va = pd.read_excel(HOLDOUT_XLSX, sheet_name='Main Data')
    va.columns = HOLDOUT_COLS
    va = va[va['EXT MAT GROUP'] == 'RA-ODU'].copy()
    va['Billing Date'] = pd.to_datetime(va['Billing Date'])
    va['Billing Quantity ODU'] = pd.to_numeric(va['Billing Quantity ODU'], errors='coerce').fillna(0)
    n_returns = int((va['Billing Quantity ODU'] < 0).sum())
    returns_qty = float(va.loc[va['Billing Quantity ODU'] < 0, 'Billing Quantity ODU'].sum())
    # Match training cleaning: returns / credit memos removed (see ASSUMPTIONS.md)
    va = va[va['Billing Quantity ODU'] > 0]
    va['Segment'] = va['Segment'].replace({'Inv': 'Inverter'})
    va = va[['Material', 'SALES OFFICE CODE', 'Billing Date', 'Billing Quantity ODU', 'Tonnage', 'Star Rating.1', 'Segment']]
    va['source'] = 'holdout'
    print(f"Holdout returns removed: {n_returns} rows, {returns_qty:,.0f} units")

    raw = pd.concat([tr, va], ignore_index=True)
    raw['Star Rating.1'] = raw['Star Rating.1'].astype(str).str.title()

    attrs = (raw.sort_values('Billing Date')
             .groupby('Material')[['Tonnage', 'Star Rating.1', 'Segment']].last()
             .rename(columns={'Star Rating.1': 'star'}))
    attrs.to_parquet(os.path.join(OUT_DIR, "sku_attributes.parquet"))

    weekly = (raw.groupby(['Material', 'SALES OFFICE CODE', pd.Grouper(key='Billing Date', freq='W-MON')])
              ['Billing Quantity ODU'].sum().reset_index()
              .rename(columns={'Material': 'sku', 'SALES OFFICE CODE': 'branch',
                               'Billing Date': 'date', 'Billing Quantity ODU': 'total_demand'}))
    weekly.to_parquet(PANEL_PATH, index=False)
    print(f"Weekly panel: {len(weekly):,} rows, {weekly[['sku', 'branch']].drop_duplicates().shape[0]} series, "
          f"{weekly.date.min().date()} -> {weekly.date.max().date()}")


# ---------------------------------------------------------------- workers
_PANEL = None
_SELECTOR = None


def _init_worker():
    global _PANEL, _SELECTOR
    warnings.filterwarnings('ignore')
    logging.disable(logging.CRITICAL)
    from src.monitoring.registry import ModelRegistry
    ModelRegistry.save = lambda self: None  # never touch config/model_registry.json
    from src.selection.model_selector import ModelSelector
    _PANEL = pd.read_parquet(PANEL_PATH)
    _SELECTOR = ModelSelector()


def _series_to_origin(sku, branch, origin):
    s = _PANEL[(_PANEL.sku == sku) & (_PANEL.branch == branch) & (_PANEL.date <= origin)]
    s = s[s.total_demand > 0]
    if s.empty:
        return None, 0
    idx = pd.date_range(s.date.min(), origin, freq='W-MON')
    y = s.set_index('date')['total_demand'].reindex(idx, fill_value=0.0)
    frame = pd.DataFrame({'date': idx, 'total_demand': y.values, 'sku': sku, 'branch': branch})
    return frame, int((y > 0).sum())


def _run_task(task):
    mode, origin, sku, branch, horizon = task
    base = {'mode': mode, 'origin': origin, 'sku': sku, 'branch': branch}
    frame, nz = _series_to_origin(sku, branch, origin)
    if frame is None or nz < MIN_NONZERO_WEEKS:
        return [dict(base, status='insufficient_history', step=np.nan, week=pd.NaT, forecast=np.nan)]
    t0 = time.time()
    try:
        res = _SELECTOR.select_and_fit(frame, sku=sku, branch=branch, horizon=horizon)
    except Exception as e:
        return [dict(base, status=f'error: {e}'[:200], step=np.nan, week=pd.NaT, forecast=np.nan)]
    if res.get('status') != 'success':
        return [dict(base, status=res.get('error', 'failed'), step=np.nan, week=pd.NaT, forecast=np.nan)]
    champ = res.get('champion', {}) or {}
    fc = np.asarray(res['forecast'], dtype=float)
    p10 = np.asarray(res.get('p10', fc), dtype=float)
    p90 = np.asarray(res.get('p90', fc), dtype=float)
    rows = []
    for h in range(horizon):
        rows.append(dict(
            base, status='ok', step=h + 1, week=origin + pd.Timedelta(weeks=h + 1),
            forecast=fc[h], p10=p10[h], p90=p90[h],
            champion=champ.get('model_name'),
            backtest_wape=champ.get('mean_wape', champ.get('wape')),
            demand_type=(res.get('demand_profile') or {}).get('demand_type'),
            history_weeks=len(frame), fit_secs=round(time.time() - t0, 2),
        ))
    return rows


def _build_tasks(mode):
    panel = pd.read_parquet(PANEL_PATH)
    if mode == 'static':
        origins, horizon = [TRAIN_END_WEEK], 52
    else:
        origins = list(pd.date_range(TRAIN_END_WEEK, HOLDOUT_END_WEEK - pd.Timedelta(weeks=1),
                                     freq=f'{ROLLING_STEP_WEEKS}W-MON'))
        horizon = ROLLING_HORIZON
    tasks = []
    for o in origins:
        hist = panel[(panel.date <= o) & (panel.total_demand > 0)]
        nz = hist.groupby(['sku', 'branch']).size()
        for (sku, branch), n in nz.items():
            if n >= MIN_NONZERO_WEEKS:
                h = horizon if mode == 'static' else min(horizon, int((HOLDOUT_END_WEEK - o).days // 7))
                tasks.append((mode, o, sku, branch, h))
    return tasks


def run(mode, workers=None):
    tasks = _build_tasks(mode)
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    print(f"[{mode}] {len(tasks)} fits on {workers} workers", flush=True)
    rows, t0 = [], time.time()
    with Pool(workers, initializer=_init_worker) as pool:
        for i, r in enumerate(pool.imap_unordered(_run_task, tasks, chunksize=2), 1):
            rows.extend(r)
            if i % 50 == 0 or i == len(tasks):
                print(f"  {i}/{len(tasks)}  {time.time() - t0:,.0f}s", flush=True)
    out = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, f"forecasts_{mode}.parquet")
    out.to_parquet(path, index=False)
    print(f"Saved {path} ({len(out):,} rows)")


# ---------------------------------------------------------------- scoring
def _metrics(a, f):
    a, f = np.asarray(a, float), np.asarray(f, float)
    sa = a.sum()
    wape = np.abs(a - f).sum() / sa * 100 if sa else np.nan
    return {'actual': round(sa), 'forecast': round(f.sum()), 'WAPE %': round(wape, 1),
            'Accuracy %': round(100 - wape, 1), 'Bias %': round((f.sum() - sa) / sa * 100, 1) if sa else np.nan}


def _score_levels(df, fcols, levels):
    """df has actual + forecast columns keyed by sku, branch, week, month."""
    out = []
    for lvl_name, keys in levels.items():
        g = df.groupby(keys)[['actual'] + fcols].sum()
        for fc in fcols:
            out.append(dict(level=lvl_name, method=fc, **_metrics(g['actual'], g[fc])))
    return pd.DataFrame(out)


LEVELS = {
    'SKU x Branch x Week': ['sku', 'branch', 'week'],
    'SKU x Branch x Month': ['sku', 'branch', 'month'],
    'SKU x Month (South)': ['sku', 'month'],
    'Branch x Month': ['branch', 'month'],
    'South Region x Month': ['month'],
    'South Region x Quarter': ['quarter'],
}


def _actuals_grid(panel):
    hold = panel[(panel.date > TRAIN_END_WEEK) & (panel.date <= HOLDOUT_END_WEEK)]
    return hold.rename(columns={'date': 'week', 'total_demand': 'actual'})[['sku', 'branch', 'week', 'actual']]


def _add_periods(df):
    df['month'] = df['week'].dt.to_period('M').astype(str)
    df['quarter'] = df['week'].dt.to_period('Q-MAR').astype(str)
    return df


def score():
    panel = pd.read_parquet(PANEL_PATH)
    lookup = panel.set_index(['sku', 'branch', 'date'])['total_demand']
    actuals = _actuals_grid(panel)
    sheets = {}

    # ---------- Static 52-week holdout
    st = pd.read_parquet(os.path.join(OUT_DIR, 'forecasts_static.parquet'))
    ok = st[st.status == 'ok'].copy()
    ok['week'] = pd.to_datetime(ok['week'])
    series = ok[['sku', 'branch']].drop_duplicates()
    weeks = pd.date_range(TRAIN_END_WEEK + pd.Timedelta(weeks=1), HOLDOUT_END_WEEK, freq='W-MON')
    grid = series.merge(pd.DataFrame({'week': weeks}), how='cross')
    grid = grid.merge(ok[['sku', 'branch', 'week', 'forecast', 'p10', 'p90']], on=['sku', 'branch', 'week'], how='left')
    grid = grid.merge(actuals, on=['sku', 'branch', 'week'], how='left').fillna({'actual': 0.0})
    ly = pd.MultiIndex.from_arrays([grid.sku, grid.branch, grid.week - pd.Timedelta(weeks=52)])
    grid['seasonal_naive'] = lookup.reindex(ly).fillna(0.0).values
    _add_periods(grid)

    total_actual = actuals.actual.sum()
    covered_actual = grid.actual.sum()
    print("\n=== STATIC 52-WEEK HOLDOUT (train to 30-Jun-2024, forecast Jul-24..Jun-25) ===")
    print(f"Series forecast: {len(series)} | holdout ODU actual {total_actual:,.0f} | "
          f"covered by forecast series {covered_actual:,.0f} ({covered_actual / total_actual:.1%})")
    static_lv = _score_levels(grid, ['forecast', 'seasonal_naive'], LEVELS)
    print(static_lv.to_string(index=False))
    sheets['Static - by level'] = static_lv

    first12 = grid[grid.week <= TRAIN_END_WEEK + pd.Timedelta(weeks=12)]
    s12 = _score_levels(first12, ['forecast', 'seasonal_naive'],
                        {k: v for k, v in LEVELS.items() if 'Quarter' not in k})
    print("\n-- Static, first 12 weeks only (Jul-Sep 2024, dashboard horizon) --")
    print(s12.to_string(index=False))
    sheets['Static - first 12 weeks'] = s12

    # Region month view (all actuals incl. SKUs the model could not forecast)
    all_m = _add_periods(actuals.copy()).groupby('month')['actual'].sum().rename('actual_all_skus')
    rm = grid.groupby('month')[['actual', 'forecast', 'seasonal_naive']].sum().join(all_m).round(0)
    rm['fc_err_%'] = ((rm.forecast - rm.actual) / rm.actual * 100).round(1)
    print("\n-- South region by month (static) --")
    print(rm.to_string())
    sheets['Static - region monthly'] = rm.reset_index()

    # Champions, fallback, backtest honesty, interval coverage
    meta = ok.groupby(['sku', 'branch']).first()[['champion', 'backtest_wape', 'demand_type']]
    ser_err = grid.groupby(['sku', 'branch']).apply(
        lambda d: pd.Series({'actual': d.actual.sum(),
                             'holdout_wape': np.abs(d.actual - d.forecast).sum() / d.actual.sum() * 100 if d.actual.sum() else np.nan,
                             'sn_wape': np.abs(d.actual - d.seasonal_naive).sum() / d.actual.sum() * 100 if d.actual.sum() else np.nan,
                             'in_band': ((d.actual >= d.p10) & (d.actual <= d.p90)).mean()}))
    ser = meta.join(ser_err).reset_index().sort_values('actual', ascending=False)
    sheets['Static - per series'] = ser
    champ = ser.groupby('champion').agg(series=('sku', 'size'), holdout_actual=('actual', 'sum')).sort_values('series', ascending=False)
    print("\n-- Champion models selected --")
    print(champ.to_string())
    sheets['Champions'] = champ.reset_index()
    vol = ser[ser.actual > 0]
    w = vol.actual / vol.actual.sum()
    print(f"\nBacktest WAPE (shown in dashboard), volume-weighted: {np.nansum(vol.backtest_wape * w):.1f}%  vs "
          f"realised holdout WAPE: {np.nansum(vol.holdout_wape * w):.1f}%")
    print(f"P10-P90 band coverage (nominal 80%): {grid.loc[grid.p10.notna()].pipe(lambda d: ((d.actual >= d.p10) & (d.actual <= d.p90)).mean()):.1%}")
    print(f"Series where model beats seasonal naive (holdout WAPE): {(vol.holdout_wape < vol.sn_wape).mean():.0%} of {len(vol)}")

    # ---------- Rolling re-forecast
    rpath = os.path.join(OUT_DIR, 'forecasts_rolling.parquet')
    if os.path.exists(rpath):
        ro = pd.read_parquet(rpath)
        ro = ro[ro.status == 'ok'].copy()
        ro['week'] = pd.to_datetime(ro['week'])
        ro['origin'] = pd.to_datetime(ro['origin'])
        ma4 = {}
        for (sku, br, o) in ro[['sku', 'branch', 'origin']].drop_duplicates().itertuples(index=False):
            idx = pd.MultiIndex.from_arrays([[sku] * 4, [br] * 4, pd.date_range(end=o, periods=4, freq='W-MON')])
            ma4[(sku, br, o)] = lookup.reindex(idx).fillna(0).mean()
        ro['moving_avg_4w'] = [ma4[k] for k in zip(ro.sku, ro.branch, ro.origin)]
        ly = pd.MultiIndex.from_arrays([ro.sku, ro.branch, ro.week - pd.Timedelta(weeks=52)])
        ro['seasonal_naive'] = lookup.reindex(ly).fillna(0.0).values
        ro = ro.merge(actuals, on=['sku', 'branch', 'week'], how='left').fillna({'actual': 0.0})
        ro['lag_band'] = np.where(ro.step <= 4, 'lag 1-4 wks', np.where(ro.step <= 8, 'lag 5-8 wks', 'lag 9-12 wks'))
        _add_periods(ro)

        print("\n=== ROLLING RE-FORECAST (retrain every 4 weeks, 12-week horizon) ===")
        rows = []
        for band, d in ro.groupby('lag_band'):
            lv = _score_levels(d, ['forecast', 'moving_avg_4w', 'seasonal_naive'], LEVELS)
            lv.insert(0, 'lag', band)
            rows.append(lv)
        roll_lv = pd.concat(rows)
        print(roll_lv[roll_lv.lag == 'lag 1-4 wks'].to_string(index=False))
        sheets['Rolling - by level & lag'] = roll_lv

        near = ro[ro.step <= 4]
        rm2 = near.groupby('month')[['actual', 'forecast', 'moving_avg_4w', 'seasonal_naive']].sum().join(all_m).round(0)
        rm2['fc_err_%'] = ((rm2.forecast - rm2.actual) / rm2.actual * 100).round(1)
        print("\n-- South region by month, next-4-week forecasts --")
        print(rm2.to_string())
        sheets['Rolling - region monthly'] = rm2.reset_index()
        print(f"Rolling P10-P90 band coverage (lag 1-4): {((near.actual >= near.p10) & (near.actual <= near.p90)).mean():.1%}")
        rc = near.groupby('champion').size().sort_values(ascending=False)
        sheets['Rolling - champions'] = rc.rename('forecast_weeks').reset_index()

    xl = os.path.join(OUT_DIR, 'holdout_validation_FY24-25.xlsx')
    with pd.ExcelWriter(xl) as w:
        for name, d in sheets.items():
            d.to_excel(w, sheet_name=name[:31], index=False)
    print(f"\nSaved {xl}")


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'static'
    if cmd == 'prepare':
        prepare()
    elif cmd == 'score':
        score()
    else:
        run(cmd)
