"""
Holdout Validation (FY24-25) dashboard page.

Shows how the production forecasting engine performed on billing it never saw
(Jul-2024 to Jun-2025): data verification of the holdout file, accuracy by
hierarchy level against naive benchmarks, the original vs current engine,
region / branch / SKU drill-downs and model-selection diagnostics.

Reads precomputed artefacts produced by `validate_holdout_fy25.py`; no models
are fitted while the page renders.
"""
import os
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.validation import holdout_report as hr

MODE_LABELS = {
    "📌 Static 52-week holdout": "static",
    "🔁 Rolling 4-weekly re-forecast": "rolling",
}
ENGINE_LABELS = {"Current engine": "current", "Original engine (before fixes)": "baseline"}
METHOD_LABELS = {
    'forecast': 'Model (champion)',
    'seasonal_naive': 'Seasonal naive (same week LY)',
    'moving_avg_4w': '4-week moving average',
}
BRANCH_NAMES = {'BLR': 'Bangalore', 'MAA': 'Chennai', 'COK': 'Cochin', 'SBD': 'Secunderabad', 'SBD1': 'Vijayawada'}
SEASONAL_CHAMPIONS = {'Seasonal Index', 'Seasonal Index (smooth)', 'SARIMA', 'ETS', 'Ensemble (Consensus)',
                      'Seasonal Naive', 'Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM'}


def _mtime(path: str) -> float:
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


@st.cache_data(show_spinner=False, max_entries=8)
def _load_static(path: str, _mtime_key: float):
    panel = hr.load_panel()
    fc = pd.read_parquet(path)
    grid = hr.build_static_grid(panel, fc)
    return grid, fc, hr.series_diagnostics(grid, fc), hr.add_periods(hr.holdout_actuals(panel))


@st.cache_data(show_spinner=False, max_entries=4)
def _load_rolling(path: str, _mtime_key: float):
    panel = hr.load_panel()
    fc = pd.read_parquet(path)
    return hr.build_rolling_grid(panel, fc), fc


@st.cache_data(show_spinner=False, max_entries=6)
def _load_model_grid(path: str, _mtime_key: float, lag: Optional[str]):
    """Every model's forecasts (batch harness output) joined with actual billing."""
    return hr.build_model_grid(hr.load_panel(), pd.read_parquet(path), lag)


@st.cache_data(show_spinner=False, max_entries=2)
def _lifecycle(_mtime_key: float):
    """Volume of SKUs that existed in training vs new launches in the holdout year."""
    panel = hr.load_panel()
    tr = panel[panel.date <= hr.TRAIN_END_WEEK]
    act = hr.holdout_actuals(panel)
    fy24 = tr[tr.date > hr.TRAIN_END_WEEK - pd.Timedelta(weeks=52)].groupby('sku').total_demand.sum()
    fy25 = act.groupby('sku').actual.sum()
    old_fy25 = fy25.reindex(fy24.index).fillna(0).sum()
    return {'old_fy24': fy24.sum(), 'old_fy25': old_fy25, 'new_fy25': fy25.drop(fy24.index, errors='ignore').sum(),
            'n_new': int((~fy25.index.isin(fy24.index)).sum())}


def _kpi(label, value, sub, badge, badge_cls="kpi-badge-cyan", icon="📊", color=None):
    style = f' style="color: {color} !important;"' if color else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-card-top"><span class="kpi-badge {badge_cls}">{badge}</span><span>{icon}</span></div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value"{style}>{value}</div>
        <div style="font-size: 12px; color: var(--text-secondary);">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def _subtitle(text):
    st.markdown(f'<div class="subpanel-title" style="margin: 18px 0 8px 0;">{text}</div>', unsafe_allow_html=True)


def _acc_color(acc):
    if acc is None or np.isnan(acc):
        return None
    return "#10B981" if acc >= 70 else ("#F59E0B" if acc >= 40 else "#F43F5E")


def _engine_summary(grid, fc, actuals) -> dict:
    """Headline metrics of one engine's static run (like-for-like and all-SKU views)."""
    lv = hr.score_levels(grid, ['forecast']).set_index('level')
    al = hr.score_vs_all_actuals(grid, actuals, ['forecast']).set_index('level')
    fs = hr.fit_summary(fc)
    return {
        'SKU x Branch x Month WAPE %': lv.loc['SKU x Branch x Month', 'WAPE %'],
        'Branch x Month WAPE %': lv.loc['Branch x Month', 'WAPE %'],
        'Region x Month WAPE %': lv.loc['South Region x Month', 'WAPE %'],
        'Bias % (forecast SKUs)': lv.loc['South Region x Month', 'Bias %'],
        'Branch x Month WAPE % (all SKUs)': al.loc['Branch x Month (all SKUs)', 'WAPE %'],
        'Region x Month WAPE % (all SKUs)': al.loc['South Region x Month (all SKUs)', 'WAPE %'],
        'Total vs all billed demand %': al.loc['South Region x Month (all SKUs)', 'Bias %'],
        'P10-P90 coverage % (target 80)': round(hr.band_coverage(grid) * 100, 1),
        'Flat-line forecasts %': round(fs.flat_forecast.mean() * 100, 1),
        'Series failed': int(fc[fc.status != 'ok'][['sku', 'branch']].drop_duplicates().shape[0]),
    }


def render_holdout_validation_page(theme: str = "dark"):
    is_dark = (theme == "dark")
    template = 'plotly_dark' if is_dark else 'plotly_white'
    accent = "#00E5FF" if is_dark else "#0284C7"
    colors = {'actual': '#64748B' if is_dark else '#94A3B8', 'forecast': accent,
              'seasonal_naive': '#F59E0B', 'moving_avg_4w': '#A855F7'}

    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">✅ Holdout Validation &mdash; FY24-25 Actuals</h2>
            <p class="section-subtitle">Out-of-sample test of the production champion forecasts against Jul-2024 &rarr; Jun-2025 billing the models never saw (source: <em>2024 July to 2025 June.xlsx</em>)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not os.path.exists(hr.forecast_path('static')):
        st.warning("No holdout results found. Generate them with:\n\n"
                   "`python validate_holdout_fy25.py prepare` → `static` → `rolling` → `score`")
        return

    grid_s, fc_s, ser_s, actuals = _load_static(hr.forecast_path('static'), _mtime(hr.forecast_path('static')))

    # ------------------------------------------------------------------ 1. Data verification
    checks = hr.load_verification()
    n_pass = sum(c['status'] == 'PASS' for c in checks)
    with st.expander(f"🛡️ Data verification of the holdout file — {n_pass}/{len(checks)} checks passed", expanded=False):
        st.caption("Run before any model is judged: the file must reconcile to its own Pivot sheet, "
                   "share no dates or invoices with the training data, and be cleaned the same way as training.")
        if checks:
            vdf = pd.DataFrame(checks)
            vdf['status'] = vdf['status'].map({'PASS': '✅ PASS', 'FAIL': '❌ FAIL'})
            st.dataframe(vdf[['status', 'check', 'expected', 'observed', 'note']], hide_index=True, width="stretch")
        else:
            st.info("Run `python validate_holdout_fy25.py verify` to generate verification checks.")

    # ------------------------------------------------------------------ 2. Before vs after
    if os.path.exists(hr.baseline_path('static')):
        grid_b, fc_b, _, _ = _load_static(hr.baseline_path('static'), _mtime(hr.baseline_path('static')))
        cmp = pd.DataFrame({'Original engine': _engine_summary(grid_b, fc_b, actuals),
                            'Current engine': _engine_summary(grid_s, fc_s, actuals)})
        _subtitle("🔧 Original vs current engine on the same holdout (static 52-week run)")
        st.dataframe(cmp, width="stretch")
        lc = _lifecycle(_mtime(hr.PANEL_PATH))
        st.caption(
            f"Lower WAPE is better; bias and coverage should be near 0% / 80%. "
            f"Product lifecycle matters for the SKU-level rows: SKUs sold before Jul-2024 fell from "
            f"{lc['old_fy24']:,.0f} to {lc['old_fy25']:,.0f} units ({(lc['old_fy25'] / lc['old_fy24'] - 1) * 100:+.1f}%) "
            f"while {lc['n_new']} new-launch SKUs sold {lc['new_fy25']:,.0f} units. A one-shot 52-week SKU forecast "
            f"cannot anticipate that substitution; the all-SKU rows measure the total a planner actually faces.")

    # ------------------------------------------------------------------ 3. Experiment selector
    c1, c2 = st.columns([2.2, 2])
    with c1:
        mode_label = st.segmented_control("Validation experiment", list(MODE_LABELS), key="holdout_mode",
                                          default=list(MODE_LABELS)[0])
    mode = MODE_LABELS.get(mode_label or list(MODE_LABELS)[0])

    if mode == 'static':
        with c2:
            engine_label = st.segmented_control("Engine", list(ENGINE_LABELS), key="holdout_engine",
                                                default=list(ENGINE_LABELS)[0])
        use_baseline = ENGINE_LABELS.get(engine_label or list(ENGINE_LABELS)[0]) == 'baseline' \
            and os.path.exists(hr.baseline_path('static'))
        if use_baseline:
            grid, fc, ser = grid_b, fc_b, hr.series_diagnostics(grid_b, fc_b)
        else:
            grid, fc, ser = grid_s, fc_s, ser_s
        methods = ['forecast', 'seasonal_naive']
        lag = None
        st.caption("Models trained on history up to **30-Jun-2024**, then forecast all 52 weeks of FY24-25 in one shot "
                   "(no refits). Benchmark: *seasonal naive* = same week last year.")
    else:
        final = hr.forecast_path('rolling')
        partial = final.replace('.parquet', '.partial.parquet')
        path = final if os.path.exists(final) else (partial if os.path.exists(partial) else None)
        if path is None:
            st.info("Rolling re-forecast results not generated yet. Run `python validate_holdout_fy25.py rolling`.")
            return
        try:
            grid, fc = _load_rolling(path, _mtime(path))
        except Exception:
            st.info("Rolling results are being written right now — refresh in a few seconds.")
            return
        ser = None
        with c2:
            lag = st.segmented_control("Forecast lag", ['lag 1-4 wks', 'lag 5-8 wks', 'lag 9-12 wks'],
                                       key="holdout_lag", default='lag 1-4 wks') or 'lag 1-4 wks'
        if path == partial:
            n_fits = fc[['origin', 'sku', 'branch']].drop_duplicates().shape[0]
            st.warning(f"⏳ Rolling run still in progress — showing {n_fits:,} completed fits "
                       f"(origins up to {pd.to_datetime(fc.origin).max():%d-%b-%Y}). Refresh for more.")
        grid = grid[grid.lag_band == lag]
        methods = ['forecast', 'moving_avg_4w', 'seasonal_naive']
        st.caption("Every 4 weeks the models are retrained on history **plus actuals to date** and issue a fresh "
                   "12-week forecast — how a planner would use the engine. New SKUs enter once they have 4 weeks of sales.")

    if grid.empty:
        st.info("No forecasts available for this selection yet.")
        return

    levels = hr.score_levels(grid, methods)
    acc = levels.set_index(['level', 'method'])

    # ------------------------------------------------------------------ 4. KPI cards
    def a(level, method='forecast'):
        return float(acc.loc[(level, method), 'Accuracy %'])

    total_bias = float(acc.loc[('South Region x Month', 'forecast'), 'Bias %'])
    cov = hr.band_coverage(grid)
    reg_m, sn_m = a('South Region x Month'), a('South Region x Month', 'seasonal_naive')
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        _kpi("South Region × Month", f"{reg_m:.1f}%", f"Seasonal naive: <strong>{sn_m:.1f}%</strong>",
             "Accuracy (1-WAPE)", icon="🌐", color=_acc_color(reg_m))
    with k2:
        v = a('Branch x Month')
        _kpi("Branch × Month", f"{v:.1f}%", f"Seasonal naive: <strong>{a('Branch x Month', 'seasonal_naive'):.1f}%</strong>",
             "Accuracy (1-WAPE)", icon="🏢", color=_acc_color(v))
    with k3:
        v = a('SKU x Branch x Month')
        _kpi("SKU × Branch × Month", f"{v:.1f}%", f"Weekly grain: <strong>{a('SKU x Branch x Week'):.1f}%</strong>",
             "Planning grain", "kpi-badge-amber", icon="📦", color=_acc_color(v))
    with k4:
        _kpi("Total Forecast Bias", f"{total_bias:+.1f}%",
             f"{grid.forecast.sum():,.0f} fcst vs {grid.actual.sum():,.0f} actual",
             "Over / under", "kpi-badge-green" if abs(total_bias) <= 10 else "kpi-badge-rose", icon="⚖️",
             color="#10B981" if abs(total_bias) <= 10 else "#F43F5E")
    with k5:
        _kpi("P10–P90 Band Coverage", f"{cov:.1%}" if not np.isnan(cov) else "n/a", "Nominal target: <strong>80%</strong>",
             "Interval calibration", "kpi-badge-cyan" if abs(cov - 0.8) <= 0.05 else "kpi-badge-amber", icon="🎯")

    st.caption(f"Like-for-like scoring on {grid[['sku', 'branch']].drop_duplicates().shape[0]} SKU × branch series that "
               f"had a forecast ({grid.actual.sum() / actuals.loc[actuals.week.isin(grid.week.unique()), 'actual'].sum():.1%} "
               f"of the billed volume in these weeks). See the all-SKU table below for total demand including new launches.")

    # ------------------------------------------------------------------ 5. Region monthly chart + level tables
    _subtitle("🌐 South region — monthly actual vs forecast")
    rm = grid.groupby('month')[['actual'] + methods].sum()
    all_m = actuals[actuals.week.isin(grid.week.unique())].groupby('month')['actual'].sum().reindex(rm.index)
    fig = go.Figure()
    fig.add_bar(x=rm.index, y=rm['actual'], name='Actual — forecast SKUs', marker_color=colors['actual'])
    fig.add_scatter(x=rm.index, y=all_m, name='Actual — all SKUs incl. new launches', mode='markers',
                    marker=dict(symbol='line-ew-open', size=26, color='#F43F5E', line=dict(width=3)))
    for m in methods:
        fig.add_scatter(x=rm.index, y=rm[m], name=METHOD_LABELS[m], mode='lines+markers',
                        line=dict(color=colors[m], width=3 if m == 'forecast' else 2,
                                  dash='solid' if m == 'forecast' else 'dash'))
    fig.update_layout(height=420, template=template, legend=dict(orientation='h', y=1.14),
                      yaxis_title='ODU units', margin=dict(t=50, b=10))
    st.plotly_chart(fig, width="stretch")

    _subtitle("📊 Accuracy by hierarchy level — model vs naive benchmarks (forecast SKUs)")
    lv = levels.copy()
    lv['method'] = lv['method'].map(METHOD_LABELS)
    pv = lv.pivot(index='level', columns='method', values='Accuracy %').reindex(list(hr.LEVELS)).dropna(how='all')
    pv['Best method'] = pv.idxmax(axis=1)
    bias = lv.pivot(index='level', columns='method', values='Bias %').reindex(pv.index)
    pv['Model bias %'] = bias[METHOD_LABELS['forecast']]
    st.dataframe(pv.reset_index(), hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(c, format="%.1f%%") for c in pv.columns if c != 'Best method'})
    st.caption("Accuracy = 1 − WAPE, where WAPE = Σ|actual − forecast| ÷ Σ actual at that grain. "
               "Negative accuracy means the absolute errors exceed the actual volume.")

    _subtitle("🧾 Against all billed demand (includes new-launch SKUs that no SKU model could forecast)")
    al = hr.score_vs_all_actuals(grid, actuals[actuals.week.isin(grid.week.unique())], methods)
    al['method'] = al['method'].map(METHOD_LABELS)
    st.dataframe(al.rename(columns={'actual': 'actual (all SKUs)'}), hide_index=True, width="stretch")

    # ------------------------------------------------------------------ 6. Branch view
    _subtitle("🏢 Branch performance (monthly grain, forecast SKUs)")
    rows = []
    for br, d in grid.groupby('branch'):
        g = d.groupby('month')[['actual'] + methods].sum()
        row = {'Branch': f"{br} — {BRANCH_NAMES.get(br, br)}", 'Actual': g['actual'].sum()}
        for m in methods:
            row[f"{METHOD_LABELS[m]} acc %"] = hr.metrics(g['actual'], g[m])['Accuracy %']
        row['Model bias %'] = hr.metrics(g['actual'], g['forecast'])['Bias %']
        rows.append(row)
    bdf = pd.DataFrame(rows).sort_values('Actual', ascending=False)
    bc1, bc2 = st.columns([1.3, 1])
    with bc1:
        figb = go.Figure()
        for m in methods:
            figb.add_bar(x=bdf['Branch'], y=bdf[f"{METHOD_LABELS[m]} acc %"], name=METHOD_LABELS[m], marker_color=colors[m])
        figb.update_layout(barmode='group', height=360, template=template, yaxis_title='Monthly accuracy %',
                           legend=dict(orientation='h', y=1.15), margin=dict(t=40, b=10))
        st.plotly_chart(figb, width="stretch")
    with bc2:
        st.dataframe(bdf, hide_index=True, width="stretch",
                     column_config={'Actual': st.column_config.NumberColumn(format="localized"),
                                    **{c: st.column_config.NumberColumn(format="%.1f") for c in bdf.columns[2:]}})

    # ------------------------------------------------------------------ 6b. Every model on the holdout
    _subtitle("🏁 Every model on the holdout — accuracy of each candidate across all SKU × branch series")
    mg = None
    m_final, m_partial = hr.models_path(mode), hr.models_path(mode, partial=True)
    m_path = m_final if os.path.exists(m_final) else (m_partial if os.path.exists(m_partial) else None)
    if mode == 'static' and use_baseline:
        st.info("Per-model results are recorded for the current engine only. Switch the engine selector to *Current engine*.")
    elif m_path is None:
        st.info("Per-model results not generated yet. Run `python validate_holdout_fy25.py all`.")
    else:
        try:
            mg = _load_model_grid(m_path, _mtime(m_path), lag)
        except Exception:
            st.info("Per-model results are being written right now — refresh in a few seconds.")
        if mg is not None and not mg.empty:
            if m_path == m_partial:
                st.warning(f"⏳ Showing {mg[['origin', 'sku', 'branch']].drop_duplicates().shape[0]:,} completed fits; "
                           "the run is still in progress.")
            ms = hr.model_portfolio_scores(mg)
            figm = go.Figure(go.Bar(
                x=ms['SKU x Branch x Month WAPE %'], y=ms['Model'], orientation='h',
                marker_color=[accent if m == hr.CHAMPION_LABEL else ('#64748B' if is_dark else '#94A3B8') for m in ms['Model']],
                text=[f"{v:.1f}%" for v in ms['SKU x Branch x Month WAPE %']], textposition='outside'))
            figm.update_layout(template=template, height=max(320, 28 * len(ms)), margin=dict(l=10, r=40, t=40, b=10),
                               title="SKU × branch × month WAPE by model (lower is better)", yaxis=dict(autorange='reversed'))
            mc1, mc2 = st.columns([1, 1.6])
            with mc1:
                st.plotly_chart(figm, width="stretch")
            with mc2:
                st.dataframe(ms, hide_index=True, width="stretch",
                             column_config={c: st.column_config.NumberColumn(format="%.1f") for c in ms.columns
                                            if c not in ('Model', 'Series')})
            st.caption("Each model is scored on the series where it produced a forecast; 'Volume covered' shows how much of "
                       "the champion's volume that is (ML models need ≥ 20 weeks, seasonal naive ≥ 52, intermittent models "
                       "only run on intermittent series). 'vs champion' compares the model with the auto-selected champion "
                       "on exactly the same series: negative means the model beat the champion.")
            options = ms['Model'].tolist()
            pick = st.multiselect("Compare models month by month (common series only)", options, key="holdout_model_pick",
                                  default=[m for m in [hr.CHAMPION_LABEL, 'Seasonal Index', 'Seasonal Naive', 'Moving Average']
                                           if m in options])
            if pick:
                common = None
                for m in pick:
                    k = set(map(tuple, mg.loc[mg.model == m, ['sku', 'branch']].drop_duplicates().values))
                    common = k if common is None else common & k
                cm = mg[mg[['sku', 'branch']].apply(tuple, axis=1).isin(common)] if common else mg.iloc[0:0]
                figc = go.Figure()
                act_m = cm[cm.model == pick[0]].groupby('month')['actual'].sum()
                figc.add_bar(x=act_m.index, y=act_m.values, name='Actual', marker_color=colors['actual'])
                palette = [accent, '#F59E0B', '#A855F7', '#10B981', '#F43F5E', '#3B82F6']
                for i, m in enumerate(pick):
                    sm = cm[cm.model == m].groupby('month')['forecast'].sum()
                    figc.add_scatter(x=sm.index, y=sm.values, name=m, mode='lines+markers',
                                     line=dict(color=palette[i % len(palette)], width=3 if m == hr.CHAMPION_LABEL else 2))
                figc.update_layout(template=template, height=380, legend=dict(orientation='h', y=1.15),
                                   margin=dict(t=40, b=10), yaxis_title='ODU units',
                                   title=f"South region monthly, {len(common or [])} series where all selected models forecast")
                st.plotly_chart(figc, width="stretch")

    # ------------------------------------------------------------------ 7. SKU x Branch drill-down
    _subtitle("🔎 SKU × branch drill-down — weekly actual vs forecast")
    vol = grid.groupby(['branch', 'sku'])['actual'].sum().sort_values(ascending=False)
    d1, d2 = st.columns([1, 2])
    with d1:
        sel_branch = st.selectbox("Branch", sorted(grid.branch.unique()), key="holdout_branch",
                                  format_func=lambda b: f"{b} — {BRANCH_NAMES.get(b, b)}")
    with d2:
        skus = vol.loc[sel_branch].index.tolist()
        sel_sku = st.selectbox("SKU (sorted by FY24-25 volume)", skus, key="holdout_sku",
                               format_func=lambda s: f"{s}  ·  {vol.loc[(sel_branch, s)]:,.0f} units")
    sd = grid[(grid.branch == sel_branch) & (grid.sku == sel_sku)].sort_values('week')
    if mode == 'rolling':
        sd = sd.drop_duplicates('week', keep='last')
    fit = fc[(fc.sku == sel_sku) & (fc.branch == sel_branch) & (fc.status == 'ok')]
    figs = go.Figure()
    if sd.p10.notna().any():
        figs.add_scatter(x=sd.week, y=sd.p90, line=dict(width=0), showlegend=False, hoverinfo='skip')
        figs.add_scatter(x=sd.week, y=sd.p10, fill='tonexty', line=dict(width=0), name='P10–P90 band',
                         fillcolor='rgba(0,229,255,0.15)' if is_dark else 'rgba(2,132,199,0.15)')
    figs.add_bar(x=sd.week, y=sd.actual, name='Actual', marker_color=colors['actual'])
    for m in methods:
        figs.add_scatter(x=sd.week, y=sd[m], name=METHOD_LABELS[m], mode='lines',
                         line=dict(color=colors[m], width=3 if m == 'forecast' else 1.5,
                                   dash='solid' if m == 'forecast' else 'dot'))
    if mg is not None and not mg.empty:
        sm_all = mg[(mg.sku == sel_sku) & (mg.branch == sel_branch)]
        if mode == 'rolling':
            sm_all = sm_all.sort_values('origin').drop_duplicates(['model', 'week'], keep='last')
        overlay = st.multiselect("Overlay other models for this SKU × branch", sorted(sm_all.model.unique()),
                                 key="holdout_overlay")
        palette = ['#A855F7', '#10B981', '#F43F5E', '#3B82F6', '#EC4899', '#84CC16']
        for i, m in enumerate(overlay):
            o = sm_all[sm_all.model == m].sort_values('week')
            figs.add_scatter(x=o.week, y=o.forecast, name=m, mode='lines',
                             line=dict(color=palette[i % len(palette)], width=2))
            mm = hr.metrics(o.actual, o.forecast)
            st.caption(f"{m}: weekly WAPE {mm['WAPE %']:.1f}%, bias {mm['Bias %']:+.1f}% for this SKU × branch.")
    figs.update_layout(height=380, template=template, legend=dict(orientation='h', y=1.15),
                       yaxis_title='ODU units / week', margin=dict(t=40, b=10))
    st.plotly_chart(figs, width="stretch")
    m_model, m_sn = hr.metrics(sd.actual, sd.forecast), hr.metrics(sd.actual, sd.seasonal_naive)
    champs = fit.groupby('origin')['champion'].first()
    bt = fit.groupby('origin')['backtest_wape'].first()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Champion model", champs.iloc[-1] if len(champs) else "n/a",
              help="Model chosen by the walk-forward tournament" + (" at the latest origin" if mode == 'rolling' else ""))
    s2.metric("Backtest WAPE (shown in Model Lab)", f"{bt.mean():.1f}%" if len(bt) and bt.notna().any() else "n/a")
    s3.metric("Realised holdout WAPE (weekly)", f"{m_model['WAPE %']:.1f}%",
              delta=f"{m_model['WAPE %'] - m_sn['WAPE %']:+.1f} pts vs seasonal naive", delta_color="inverse")
    s4.metric("Forecast bias", f"{m_model['Bias %']:+.1f}%" if not pd.isna(m_model['Bias %']) else "n/a")

    # ------------------------------------------------------------------ 8. Model-selection diagnostics
    _subtitle("🧪 Model-selection diagnostics")
    fs = hr.fit_summary(fc)
    champ = fs.groupby('champion').agg(fits=('sku', 'size'), flat_forecasts=('flat_forecast', 'sum'))
    champ['flat %'] = (champ.flat_forecasts / champ.fits * 100).round(0)
    champ = champ.sort_values('fits', ascending=False).reset_index()
    seasonal_share = fs.champion.isin(SEASONAL_CHAMPIONS).mean()
    failed = fc[fc.status != 'ok'][['origin', 'sku', 'branch', 'status']].drop_duplicates(['origin', 'sku', 'branch'])
    errors = failed[failed.status.astype(str).str.startswith('error')]
    findings = [
        f"<strong>{fs.flat_forecast.mean():.0%}</strong> of champion forecasts are flat lines; "
        f"<strong>{seasonal_share:.0%}</strong> of tournaments were won by a model that carries the seasonal cycle "
        f"(Seasonal Index, SARIMA, ETS, ensemble, seasonal naive or ML with the seasonal feature).",
        f"P10&ndash;P90 bands contain <strong>{cov:.0%}</strong> of actuals vs an 80% target &mdash; "
        + ('too wide: safety stock from these bands would be overstated.' if cov > 0.85 else
           ('too narrow: service-level risk would be understated.' if cov < 0.75 else 'well calibrated.')),
        f"{len(failed)} fit(s) produced no forecast ({len(errors)} with a code error); the rest were "
        f"rejected for insufficient history (fewer than 5 weeks or 2 billing weeks).",
    ]
    if ser is not None:
        vols = ser[ser.actual > 0]
        w = vols.actual / vols.actual.sum()
        findings.insert(1, f"Backtest WAPE shown in Model Lab (volume-weighted <strong>{np.nansum(vols.backtest_wape * w):.0f}%</strong>) "
                           f"vs realised holdout WAPE <strong>{np.nansum(vols.holdout_wape * w):.0f}%</strong> over the 52-week horizon "
                           f"(the backtest scores 12-week horizons, so a gap is expected).")
    g1, g2 = st.columns([1, 1.2])
    with g1:
        st.dataframe(champ, hide_index=True, width="stretch")
    with g2:
        items = ''.join(f'<li>{f}</li>' for f in findings)
        st.markdown(f"""
        <div class="glass-panel" style="padding: 18px 20px;">
            <div style="font-size: 15px; font-weight: 700; margin-bottom: 10px;">Key findings (computed from this run)</div>
            <ul style="font-size: 13px; color: var(--text-secondary); line-height: 1.7; margin: 0; padding-left: 18px;">{items}</ul>
        </div>
        """, unsafe_allow_html=True)

    xl = os.path.join(hr.OUT_DIR, 'holdout_validation_FY24-25.xlsx')
    if os.path.exists(xl):
        with open(xl, 'rb') as f:
            st.download_button("📥 Download full validation workbook (.xlsx)", f.read(),
                               file_name='holdout_validation_FY24-25.xlsx',
                               mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
