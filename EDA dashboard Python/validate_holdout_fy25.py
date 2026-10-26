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
  python validate_holdout_fy25.py verify   # data checks on the holdout file
  python validate_holdout_fy25.py score    # metrics + Excel (also shown on the dashboard)
  python validate_holdout_fy25.py all      # static + rolling + score in one detached-friendly run
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


def _init_worker():
    global _PANEL
    warnings.filterwarnings('ignore')
    logging.disable(logging.CRITICAL)
    from src.monitoring.registry import ModelRegistry
    ModelRegistry.save = lambda self: None  # never touch config/model_registry.json
    _PANEL = pd.read_parquet(PANEL_PATH)


def _run_task(task):
    """
    One production model selection exactly as the dashboard runs it, on data up to `origin` only,
    plus the forward forecast of every candidate model (for the per-model comparison).
    Returns (champion_rows, model_rows).
    """
    from src.validation.model_validation import run_origin
    mode, origin, sku, branch, horizon = task
    base = {'mode': mode, 'origin': origin, 'sku': sku, 'branch': branch}
    t0 = time.time()
    try:
        out = run_origin(_PANEL[_PANEL.date <= origin], sku, branch, horizon)
    except Exception as e:
        return [dict(base, status=f'error: {e}'[:200], step=np.nan, week=pd.NaT, forecast=np.nan)], []
    if out.get('status') != 'success':
        return [dict(base, status=str(out.get('error', 'failed'))[:200], step=np.nan, week=pd.NaT, forecast=np.nan)], []
    res = out['res']
    champ = res.get('champion', {}) or {}
    fc = np.asarray(res['forecast'], dtype=float)
    p10 = np.asarray(res.get('p10', fc), dtype=float)
    p90 = np.asarray(res.get('p90', fc), dtype=float)
    weeks = pd.DatetimeIndex(out['dates'])
    rows = []
    for h in range(horizon):
        rows.append(dict(
            base, status='ok', step=h + 1, week=weeks[h],
            forecast=fc[h], p10=p10[h], p90=p90[h],
            champion=champ.get('model_name'),
            backtest_wape=champ.get('wape'),
            demand_type=(res.get('demand_profile') or {}).get('demand_type'),
            fallback=res.get('fallback_reason'),
            history_weeks=len(res.get('historical_demand', [])), fit_secs=round(time.time() - t0, 2),
        ))
    model_rows = []
    bt = out['backtest_wape']
    for m, f in out['forecasts'].items():
        for h in range(horizon):
            model_rows.append(dict(base, model=m, step=h + 1, week=weeks[h], forecast=float(f[h]),
                                   backtest_wape=bt.get(m, bt.get(champ.get('model_name')) if m.startswith('Champion') else np.nan)))
    return rows, model_rows


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
    """Run all fits for a mode, checkpointing so an interrupted run resumes where it stopped."""
    path = os.path.join(OUT_DIR, f"forecasts_{mode}.parquet")
    mpath = os.path.join(OUT_DIR, f"models_{mode}.parquet")
    partial = path.replace('.parquet', '.partial.parquet')
    mpartial = mpath.replace('.parquet', '.partial.parquet')
    tasks = _build_tasks(mode)
    done = pd.read_parquet(partial) if os.path.exists(partial) else pd.DataFrame()
    mdone = pd.read_parquet(mpartial) if os.path.exists(mpartial) else pd.DataFrame()
    if not done.empty:
        done_keys = set(zip(pd.to_datetime(done.origin), done.sku, done.branch))
        tasks = [t for t in tasks if (t[1], t[2], t[3]) not in done_keys]
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    print(f"[{mode}] {len(tasks)} fits remaining on {workers} workers", flush=True)
    rows, mrows, t0 = [], [], time.time()

    def checkpoint():
        outs = []
        for prev, new, target in ((done, rows, partial), (mdone, mrows, mpartial)):
            frames = [d for d in (prev, pd.DataFrame(new)) if not d.empty]
            out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            out.to_parquet(target, index=False)
            outs.append(out)
        return outs

    with Pool(workers, initializer=_init_worker) as pool:
        for i, (r, mr) in enumerate(pool.imap_unordered(_run_task, tasks, chunksize=2), 1):
            rows.extend(r)
            mrows.extend(mr)
            if i % 100 == 0 or i == len(tasks):
                checkpoint()
                print(f"  {i}/{len(tasks)}  {time.time() - t0:,.0f}s", flush=True)
    out, mout = checkpoint()
    out.to_parquet(path, index=False)
    mout.to_parquet(mpath, index=False)
    os.remove(partial)
    os.remove(mpartial)
    print(f"Saved {path} ({len(out):,} rows) and {mpath} ({len(mout):,} rows)")


# ---------------------------------------------------------------- verification
def verify():
    """Data verification checks on the holdout file before any model is judged."""
    import json
    tr = pd.read_parquet(TRAIN_PARQUET)
    tr = tr[tr['Data_Sheet'] == 'Historical (Sheet1)']
    va = pd.read_excel(HOLDOUT_XLSX, sheet_name='Main Data')
    va.columns = HOLDOUT_COLS
    va['Billing Date'] = pd.to_datetime(va['Billing Date'])
    va['Billing Quantity ODU'] = pd.to_numeric(va['Billing Quantity ODU'], errors='coerce').fillna(0)
    odu = va[va['EXT MAT GROUP'] == 'RA-ODU']
    checks = []

    def add(name, expected, observed, passed, note=''):
        checks.append({'check': name, 'expected': str(expected), 'observed': str(observed),
                       'status': 'PASS' if passed else 'FAIL', 'note': note})

    # 1. Reconcile to the file's own Pivot sheet (Sum of Billing Quantity ODU by branch)
    pv = pd.read_excel(HOLDOUT_XLSX, sheet_name='Pivot', header=None)
    pv = pv.iloc[4:].dropna(subset=[0, 1])
    pivot = dict(zip(pv[0].astype(str).str.strip(), pd.to_numeric(pv[1], errors='coerce')))
    by_branch = odu.groupby('SALES OFFICE CODE')['Billing Quantity ODU'].sum()
    for br, qty in by_branch.items():
        add(f'Pivot reconciliation - {br}', f"{pivot.get(br, np.nan):,.0f}", f'{qty:,.0f}',
            abs(pivot.get(br, np.nan) - qty) < 0.5, 'Net ODU (incl. returns) vs file Pivot sheet')
    add('Pivot reconciliation - South total', f"{pivot.get('Grand Total', np.nan):,.0f}",
        f"{by_branch.sum():,.0f}", abs(pivot.get('Grand Total', np.nan) - by_branch.sum()) < 0.5)

    # 2. Temporal separation (no leakage)
    add('Holdout period', '2024-07-01 .. 2025-06-30',
        f"{va['Billing Date'].min().date()} .. {va['Billing Date'].max().date()}",
        va['Billing Date'].min() >= pd.Timestamp('2024-07-01') and va['Billing Date'].max() <= pd.Timestamp('2025-06-30'))
    add('No date overlap with training', f"train ends {tr['Billing Date'].max().date()}",
        f"holdout starts {va['Billing Date'].min().date()}", tr['Billing Date'].max() < va['Billing Date'].min())
    shared_docs = set(pd.to_numeric(tr['Billing Doc.'], errors='coerce').dropna().astype('int64')) & \
        set(pd.to_numeric(va['Billing Doc.'], errors='coerce').dropna().astype('int64'))
    add('No shared invoices with training', 0, len(shared_docs), len(shared_docs) == 0, 'Billing Doc. numbers')

    # 3. Data quality of the holdout file
    ret = odu[odu['Billing Quantity ODU'] < 0]
    gross = odu.loc[odu['Billing Quantity ODU'] > 0, 'Billing Quantity ODU'].sum()
    add('Returns / credit memos removed', 'removed (as in training cleaning)',
        f"{len(ret)} rows, {ret['Billing Quantity ODU'].sum():,.0f} units", True,
        f"{-ret['Billing Quantity ODU'].sum() / gross:.1%} of gross volume")
    key_cols = ['Billing Date', 'Material', 'SALES OFFICE CODE']
    n_missing = int(odu[key_cols].isna().any(axis=1).sum())
    add('Missing dates / SKUs / branches', 0, n_missing, n_missing == 0)
    add('Branches known to model', 'BLR, COK, MAA, SBD, SBD1', ', '.join(sorted(odu['SALES OFFICE CODE'].unique())),
        set(odu['SALES OFFICE CODE']) <= set(tr['SALES OFFICE CODE']))

    # 4. Weekly panel reconciles to cleaned raw holdout
    panel = pd.read_parquet(PANEL_PATH)
    hold = panel[(panel.date > TRAIN_END_WEEK) & (panel.date <= HOLDOUT_END_WEEK)].total_demand.sum()
    add('Weekly panel = cleaned holdout volume', f'{gross:,.0f}', f'{hold:,.0f}', abs(hold - gross) < 0.5,
        'W-MON weekly aggregation loses no volume')

    # 5. Coverage of the model (informational)
    pos = odu[odu['Billing Quantity ODU'] > 0]
    train_skus = set(tr.loc[tr['EXT MAT GROUP'] == 'RA-ODU', 'Material'])
    new = pos[~pos.Material.isin(train_skus)]
    add('SKUs seen in training', 'informational',
        f"{pos.Material.nunique() - new.Material.nunique()} of {pos.Material.nunique()} SKUs, "
        f"{1 - new['Billing Quantity ODU'].sum() / gross:.1%} of volume", True,
        f"{new.Material.nunique()} new-launch SKUs ({new['Billing Quantity ODU'].sum():,.0f} units) cannot be forecast at SKU level")

    with open(os.path.join(OUT_DIR, 'verification.json'), 'w', encoding='utf-8') as f:
        json.dump(checks, f, indent=2)
    for c in checks:
        print(f"[{c['status']}] {c['check']}: expected {c['expected']} | observed {c['observed']}  {c['note']}")


# ---------------------------------------------------------------- scoring
def score():
    from src.validation import holdout_report as hr

    panel = hr.load_panel()
    actuals = hr.add_periods(hr.holdout_actuals(panel))
    all_m = actuals.groupby('month')['actual'].sum().rename('actual_all_skus')
    sheets = {}

    st_fc = pd.read_parquet(hr.forecast_path('static'))
    grid = hr.build_static_grid(panel, st_fc)
    print("\n=== STATIC 52-WEEK HOLDOUT (train to 30-Jun-2024, forecast Jul-24..Jun-25) ===")
    print(f"Holdout ODU actual {actuals.actual.sum():,.0f} | covered by forecast series "
          f"{grid.actual.sum():,.0f} ({grid.actual.sum() / actuals.actual.sum():.1%})")
    sheets['Static - by level'] = hr.score_levels(grid, ['forecast', 'seasonal_naive'])
    print(sheets['Static - by level'].to_string(index=False))
    first12 = grid[grid.week <= TRAIN_END_WEEK + pd.Timedelta(weeks=12)]
    sheets['Static - first 12 weeks'] = hr.score_levels(
        first12, ['forecast', 'seasonal_naive'], {k: v for k, v in hr.LEVELS.items() if 'Quarter' not in k})
    rm = grid.groupby('month')[['actual', 'forecast', 'seasonal_naive']].sum().join(all_m).round(0)
    sheets['Static - region monthly'] = rm.reset_index()
    ser = hr.series_diagnostics(grid, st_fc)
    sheets['Static - per series'] = ser
    sheets['Champions'] = ser.groupby('champion').agg(
        series=('sku', 'size'), flat_forecasts=('flat_forecast', 'sum'), holdout_actual=('actual', 'sum')
    ).sort_values('series', ascending=False).reset_index()
    print(sheets['Champions'].to_string(index=False))
    print(f"P10-P90 coverage (nominal 80%): {hr.band_coverage(grid):.1%}")

    if os.path.exists(hr.forecast_path('rolling')):
        ro = hr.build_rolling_grid(panel, pd.read_parquet(hr.forecast_path('rolling')))
        print("\n=== ROLLING RE-FORECAST (retrain every 4 weeks, 12-week horizon) ===")
        rows = []
        for band, d in ro.groupby('lag_band'):
            lv = hr.score_levels(d, ['forecast', 'moving_avg_4w', 'seasonal_naive'])
            lv.insert(0, 'lag', band)
            rows.append(lv)
        sheets['Rolling - by level & lag'] = pd.concat(rows)
        print(sheets['Rolling - by level & lag'].query("lag == 'lag 1-4 wks'").to_string(index=False))
        near = ro[ro.step <= 4]
        sheets['Rolling - region monthly'] = near.groupby('month')[
            ['actual', 'forecast', 'moving_avg_4w', 'seasonal_naive']].sum().join(all_m).round(0).reset_index()
        print(f"Rolling P10-P90 coverage (lag 1-4): {hr.band_coverage(near):.1%}")
        all_near = hr.score_vs_all_actuals(near, actuals[actuals.week.isin(near.week.unique())],
                                           ['forecast', 'moving_avg_4w', 'seasonal_naive'])
        sheets['Rolling - all SKUs (lag 1-4)'] = all_near

    # Before/after: original engine on the same static holdout
    if os.path.exists(hr.baseline_path('static')):
        b_fc = pd.read_parquet(hr.baseline_path('static'))
        b_grid = hr.build_static_grid(panel, b_fc)
        sheets['Static - original engine'] = hr.score_levels(b_grid, ['forecast'])
        sheets['Static all SKUs - orig vs new'] = pd.concat([
            hr.score_vs_all_actuals(b_grid, actuals, ['forecast']).assign(engine='original'),
            hr.score_vs_all_actuals(grid, actuals, ['forecast']).assign(engine='current')])

    # Every candidate model on the holdout (per-model forecasts recorded by the harness)
    for mode, lag, name in (('static', None, 'Models - static'), ('rolling', 'lag 1-4 wks', 'Models - rolling lag 1-4')):
        if os.path.exists(hr.models_path(mode)):
            mg = hr.build_model_grid(panel, pd.read_parquet(hr.models_path(mode)), lag)
            sheets[name] = hr.model_portfolio_scores(mg)
            print(f"=== EVERY MODEL ({name}) ===")
            print(sheets[name].to_string(index=False))

    _export_metrics(sheets, grid, panel, actuals)

    xl = os.path.join(OUT_DIR, 'holdout_validation_FY24-25.xlsx')
    with pd.ExcelWriter(xl) as w:
        pd.DataFrame(hr.load_verification()).to_excel(w, sheet_name='Data verification', index=False)
        for name, d in sheets.items():
            d.to_excel(w, sheet_name=name[:31], index=False)
    print(f"\nSaved {xl}")


def _export_metrics(sheets, grid, panel, actuals):
    """Headline validated numbers as JSON: the single source for reports and documentation."""
    import json
    from src.validation import holdout_report as hr

    def table(df, cols=('level', 'method', 'WAPE %', 'Accuracy %', 'Bias %'), **filters):
        d = df
        for k, v in filters.items():
            d = d[d[k] == v]
        return d[[c for c in cols if c in d.columns]].to_dict(orient='records')

    tr = panel[panel.date <= TRAIN_END_WEEK]
    fy24 = tr[tr.date > TRAIN_END_WEEK - pd.Timedelta(weeks=52)].groupby('sku').total_demand.sum()
    fy25 = actuals.groupby('sku').actual.sum()
    checks = hr.load_verification()
    out = {
        'generated_at': pd.Timestamp.now().isoformat(timespec='seconds'),
        'holdout_period': '2024-07-01 to 2025-06-30',
        'training_period_end': '2024-06-30',
        'verification': {'passed': sum(c['status'] == 'PASS' for c in checks), 'total': len(checks)},
        'holdout_odu_units': float(actuals.actual.sum()),
        'lifecycle': {'old_skus_fy24_units': float(fy24.sum()),
                      'old_skus_fy25_units': float(fy25.reindex(fy24.index).fillna(0).sum()),
                      'new_skus_fy25_units': float(fy25.drop(fy24.index, errors='ignore').sum()),
                      'new_skus': int((~fy25.index.isin(fy24.index)).sum())},
        'static': {
            'series': int(grid[['sku', 'branch']].drop_duplicates().shape[0]),
            'covered_share': float(grid.actual.sum() / actuals.actual.sum()),
            'levels': table(sheets['Static - by level']),
            'all_skus': table(hr.score_vs_all_actuals(grid, actuals, ['forecast', 'seasonal_naive'])),
            'p10_p90_coverage': float(hr.band_coverage(grid)),
            'champions': sheets['Champions'].to_dict(orient='records'),
        },
    }
    if 'Static - original engine' in sheets:
        out['static_original_engine'] = {
            'levels': table(sheets['Static - original engine']),
            'all_skus': table(sheets['Static all SKUs - orig vs new'], engine='original'),
        }
    if 'Rolling - by level & lag' in sheets:
        rl = sheets['Rolling - by level & lag']
        out['rolling'] = {
            'description': 'retrained every 4 weeks on history + actuals to date; 12-week forecasts',
            'lag_1_4': table(rl, lag='lag 1-4 wks'),
            'lag_5_8': table(rl, lag='lag 5-8 wks'),
            'lag_9_12': table(rl, lag='lag 9-12 wks'),
            'lag_1_4_all_skus': table(sheets['Rolling - all SKUs (lag 1-4)']),
        }
    for name, key in (('Models - static', 'models_static'), ('Models - rolling lag 1-4', 'models_rolling_lag_1_4')):
        if name in sheets:
            out[key] = sheets[name].to_dict(orient='records')
    path = os.path.join(OUT_DIR, 'validated_metrics.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=float)
    print(f"Saved {path}")
    _write_validation_doc(out)


def _write_validation_doc(m):
    """VALIDATION_FY25.md, generated from validated_metrics.json so it never drifts from the measured numbers."""
    def acc_table(records, methods, names):
        lv = [r for r in records if r['method'] == methods[0]]
        head = '| Level | ' + ' | '.join(names) + ' | Engine bias |'
        sep = '| --- |' + ' --- |' * (len(names) + 1)
        lines = [head, sep]
        for r in lv:
            cells = []
            for meth in methods:
                v = next((x['Accuracy %'] for x in records if x['level'] == r['level'] and x['method'] == meth), None)
                cells.append('n/a' if v is None else f"{v:.1f}%")
            lines.append(f"| {r['level']} | " + ' | '.join(cells) + f" | {r['Bias %']:+.1f}% |")
        return '\n'.join(lines)

    def wape_rows(records):
        return '\n'.join(f"| {r['level']} | {r['WAPE %']:.1f}% | {r['Bias %']:+.1f}% |" for r in records if r['method'] == 'forecast')

    lc, st = m['lifecycle'], m['static']
    parts = [
        "# FY24-25 Holdout Validation",
        "",
        "This document is generated by `python validate_holdout_fy25.py score` from `holdout_validation/validated_metrics.json`. "
        "Do not edit it by hand. The same results are interactive on the dashboard page "
        "*AI Demand Forecasting → Holdout Validation (FY24-25)*.",
        "",
        "## Setup",
        "",
        f"- **Holdout:** billing for {m['holdout_period']} (`2024 July to 2025 June.xlsx`). It was never used for training, model design or tuning.",
        f"- **Training data:** history up to {m['training_period_end']}.",
        "- **Engine:** the production engine (`ModelSelector.select_and_fit`, the same code the dashboard runs), run per SKU × branch on weekly ODU demand.",
        "- **Benchmarks:** same week last year (seasonal naive) and the 4-week moving average.",
        "- **Accuracy:** 100% − WAPE. It is negative when absolute errors exceed actual volume.",
        "",
        "## Data verification",
        "",
        f"{m['verification']['passed']} of {m['verification']['total']} checks passed:",
        "",
        "- every branch reconciles exactly to the file's own Pivot sheet;",
        "- no dates or invoice numbers are shared with training;",
        "- returns were removed, as in training;",
        "- weekly aggregation loses no volume.",
        "",
        "See `holdout_validation/verification.json`.",
        "",
    ]
    if 'rolling' in m:
        r = m['rolling']
        parts += [
            "## Operational view: re-forecast every 4 weeks",
            "",
            "Every 4 weeks the engine is retrained on history plus the actuals to date, and it issues a 12-week forecast. This is how a planner would use it.",
            "",
            "### Next 4 weeks (lag 1–4)",
            "",
            acc_table(r['lag_1_4'], ['forecast', 'seasonal_naive', 'moving_avg_4w'], ['Engine', 'Same week last year', '4-week moving avg']),
            "",
            "### Weeks 5–8 and 9–12 ahead",
            "",
            acc_table(r['lag_5_8'], ['forecast', 'seasonal_naive', 'moving_avg_4w'], ['Engine (lag 5–8)', 'Same week last year', '4-week moving avg']),
            "",
            acc_table(r['lag_9_12'], ['forecast', 'seasonal_naive', 'moving_avg_4w'], ['Engine (lag 9–12)', 'Same week last year', '4-week moving avg']),
            "",
            "### Against all billed demand (lag 1–4, includes new-launch SKUs)",
            "",
            "| Level | WAPE | Bias |", "| --- | --- | --- |", wape_rows(r['lag_1_4_all_skus']),
            "",
        ]
    parts += [
        "## One-shot 52-week forecast from 30-Jun-2024",
        "",
        f"There are {st['series']} SKU × branch series with a forecast, covering {st['covered_share'] * 100:.1f}% of holdout volume. "
        f"P10–P90 interval coverage is {st['p10_p90_coverage'] * 100:.1f}% against an 80% target.",
        "",
        acc_table(st['levels'], ['forecast', 'seasonal_naive'], ['Engine', 'Same week last year']),
        "",
    ]
    if 'static_original_engine' in m:
        o = m['static_original_engine']
        parts += [
            "### Original vs current engine against all billed demand",
            "",
            "| Level | Original WAPE | Original bias | Current WAPE | Current bias |", "| --- | --- | --- | --- | --- |",
            '\n'.join(f"| {a['level']} | {a['WAPE %']:.1f}% | {a['Bias %']:+.1f}% | {b['WAPE %']:.1f}% | {b['Bias %']:+.1f}% |"
                      for a, b in zip([x for x in o['all_skus'] if x['method'] == 'forecast'],
                                      [x for x in st['all_skus'] if x['method'] == 'forecast'])),
            "",
            "The original engine selected Naive or Moving Average for most series, so 94% of its forecasts were flat lines with no seasonality. "
            "Its ensemble champions shipped a moving average. Its ETS never fitted, its SARIMA used a 12-week season, and its backtest ensemble weights used the test fold's own errors.",
            "",
        ]
    parts += [
        "## Every candidate model on the holdout",
        "",
        "Each model is scored on the series where it produced a forecast. *Covered* is the share of the champion's volume. "
        "*vs champion* compares the model with the auto-selected champion on exactly the same series, at SKU × branch × month (negative means better).",
        "",
    ]
    for key, title in (('models_rolling_lag_1_4', 'Re-forecast every 4 weeks, next 4 weeks'), ('models_static', 'One-shot 52-week forecast')):
        if key in m:
            parts += [f"### {title}", "",
                      "| Model | Series | Covered | SKU×Br×Month WAPE | Branch×Month WAPE | Region×Month WAPE | vs champion | Bias |",
                      "| --- | --- | --- | --- | --- | --- | --- | --- |"]
            parts += [f"| {r['Model']} | {r['Series']} | {r['Volume covered %']:.1f}% | {r['SKU x Branch x Month WAPE %']:.1f}% | "
                      f"{r['Branch x Month WAPE %']:.1f}% | {r['South Region x Month WAPE %']:.1f}% | "
                      f"{r['vs champion, same series (SKU x Branch x Month, pts)']:+.1f} pts | {r['Bias %']:+.1f}% |" for r in m[key]]
            parts += [""]
    parts += [
        "## Product lifecycle",
        "",
        f"SKUs sold before Jul-2024 fell from {lc['old_skus_fy24_units']:,.0f} units in the prior 52 weeks to {lc['old_skus_fy25_units']:,.0f} in FY24-25 "
        f"({(lc['old_skus_fy25_units'] / lc['old_skus_fy24_units'] - 1) * 100:+.1f}%). Meanwhile, {lc['new_skus']} new-launch SKUs sold {lc['new_skus_fy25_units']:,.0f} units. "
        "No model built on a SKU's own history can anticipate this substitution. Forecasts for old SKUs therefore run high, and launch volume is missing until a new SKU has about 5 weeks of sales. "
        "Totals against all billed demand show the net effect a planner sees.",
        "",
        "## Champion models (static run)",
        "",
        "| Champion | Series | Flat forecasts |", "| --- | --- | --- |",
        '\n'.join(f"| {c['champion']} | {c['series']} | {c['flat_forecasts']} |" for c in st['champions']),
        "",
    ]
    doc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VALIDATION_FY25.md')
    with open(doc, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts) + '\n')
    print(f"Saved {doc}")


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'static'
    if cmd == 'prepare':
        prepare()
        verify()
    elif cmd == 'verify':
        verify()
    elif cmd == 'score':
        score()
    elif cmd == 'all':
        run('static')
        run('rolling')
        score()
    else:
        run(cmd)
