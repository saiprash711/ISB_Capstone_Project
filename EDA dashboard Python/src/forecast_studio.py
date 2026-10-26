"""
Forecast Studio helpers for the SKU Demand Forecasting page.

Every number rendered here comes from the canonical engine (ModelSelector):
out-of-sample rolling-origin backtests, the champion's fitted parameters and
the conformal intervals. Nothing is hard-coded or scored in-sample.
"""
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import os

from src.forecasting.model_zoo import ENSEMBLE_NAME, MODEL_DESCRIPTIONS
from src.selection.model_selector import ModelSelector
from src.validation import holdout_report as _hr
from src.validation.model_validation import CHAMPION_LABEL, from_batch, score_models, validate_series

STATISTICAL_MODELS = ['Seasonal Index', 'Seasonal Index (smooth)', 'SARIMA', 'ETS', 'ARIMA',
                      'Exponential Smoothing', 'Moving Average', 'Naive', 'Seasonal Naive',
                      'Croston', 'SBA', 'TSB']
ML_MODELS = ['Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM']
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


@st.cache_data(show_spinner=False, max_entries=64, ttl=3600)
def run_engine_forecast(df: pd.DataFrame, sku: str, branches: Optional[Sequence[str]], horizon: int,
                        coverage: float, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Canonical forecast for a SKU over one branch, several branches (aggregated) or the region.
    `model=None` runs the full champion tournament; a model name evaluates only that model
    (same 12-week rolling-origin backtest) and forecasts with it.
    """
    selector = ModelSelector(target_coverage=coverage)
    selector.registry.save = lambda: None      # interactive what-if runs do not overwrite the registry
    branch_arg = list(branches) if branches else None
    return selector.select_and_fit(df, sku, branch_arg, horizon=horizon, target_coverage=coverage,
                                   candidate_models=[model] if model else None)


@st.cache_data(show_spinner=False, max_entries=64, ttl=3600)
def weekly_demand_profile(df: pd.DataFrame, sku: str, branches: Optional[Sequence[str]]) -> Dict[str, Any]:
    """Syntetos-Boylan demand profile computed on the weekly series (not on transaction rows)."""
    selector = ModelSelector()
    prep = selector.prepare_series(df, sku, list(branches) if branches else None)
    if prep.get('status') != 'success':
        return {}
    y = prep['sku_data']['total_demand'].values
    out = selector.classifier.profile_demand(y)
    out['weeks'] = len(y)
    return out


def accuracy_from_wape(wape: float) -> float:
    """Forecast accuracy = 100% - WAPE, floored at 0% (APICS convention)."""
    return max(0.0, 100.0 - float(wape))


def _fmt_params(details: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for k, v in (details or {}).items():
        if k in ('feature_importance', 'weights'):
            continue
        if isinstance(v, dict):
            rows += [{'Parameter': f'{k}.{k2}', 'Fitted value': f'{v2:.4g}' if isinstance(v2, float) else str(v2)}
                     for k2, v2 in v.items()]
        else:
            rows.append({'Parameter': k, 'Fitted value': f'{v:.4g}' if isinstance(v, float) else str(v)})
    return pd.DataFrame(rows)


def render_model_dossier(res: Dict[str, Any], sku: str, branch_label: str, is_dark: bool):
    """Technical dossier built only from the engine result: specification, fitted values, backtest evidence."""
    if not res or res.get('status') != 'success':
        return
    template = 'plotly_dark' if is_dark else 'plotly_white'
    accent = '#00E5FF' if is_dark else '#0284C7'
    champ = res['champion'].get('model_name')
    details = res.get('model_details') or {}

    st.markdown(f"""
    <div class="glass-panel" style="border-left: 5px solid {accent}; padding: 18px 22px; margin: 22px 0 14px 0;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: {accent}; text-transform: uppercase; letter-spacing: 1.2px;">Technical dossier &mdash; generated from the fitted model</div>
        <h3 style="margin: 4px 0 6px 0; font-family: 'Outfit'; font-size: 20px;">🔬 {champ}</h3>
        <p style="margin: 0; font-size: 13px; color: var(--text-secondary);">SKU <strong>{sku}</strong> &bull; {branch_label} &bull; {MODEL_DESCRIPTIONS.get(champ, '')}</p>
    </div>
    """, unsafe_allow_html=True)

    tab_spec, tab_bt, tab_method = st.tabs(["🧾 Fitted specification", "🧪 Backtest evidence", "📐 Method & limitations"])

    with tab_spec:
        c1, c2 = st.columns(2)
        with c1:
            fi = details.get('feature_importance') if isinstance(details, dict) else None
            weights = details.get('weights') if isinstance(details, dict) else None
            if fi:
                fdf = pd.DataFrame({'Feature': list(fi), 'Importance %': np.array(list(fi.values())) * 100})
                fdf = fdf.sort_values('Importance %').tail(15)
                fig = go.Figure(go.Bar(x=fdf['Importance %'], y=fdf['Feature'], orientation='h', marker_color=accent))
                fig.update_layout(template=template, height=420, title='Feature importance of the fitted model (impurity-based)',
                                  margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, width="stretch")
            elif weights:
                wdf = pd.DataFrame({'Member model': list(weights), 'Weight': list(weights.values())}).sort_values('Weight')
                fig = go.Figure(go.Bar(x=wdf['Weight'], y=wdf['Member model'], orientation='h', marker_color=accent))
                fig.update_layout(template=template, height=380, title='Ensemble weights (inverse backtest WAPE)',
                                  margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                pdf = _fmt_params(details if isinstance(details, dict) else {})
                st.markdown("**Fitted parameters**")
                if pdf.empty:
                    st.caption("This model has no estimated parameters (rule-based baseline).")
                else:
                    st.dataframe(pdf, hide_index=True, width="stretch")
        with c2:
            sp = res.get('seasonal_profile')
            if sp:
                mi = sp['month_index']
                fig = go.Figure(go.Bar(x=MONTHS, y=[mi.get(m + 1, 1.0) for m in range(12)], marker_color=accent))
                fig.add_hline(y=1.0, line_dash='dot')
                fig.update_layout(template=template, height=320, margin=dict(l=10, r=10, t=40, b=10),
                                  title=f"Pooled seasonal index ({sp['years_pooled']} yr, branch shrunk to region)",
                                  yaxis_title='x average week')
                st.plotly_chart(fig, width="stretch")
                st.caption(f"Month-end billing push: last week of a month runs at **{sp['month_end_ratio']:.2f}x** "
                           "the other weeks of the same month (pooled estimate). Used by Seasonal Index, SARIMA, ETS "
                           "and as an ML feature.")
            else:
                st.info("Seasonal profile unavailable: fewer than 52 weeks of pooled history.")
        dp = res.get('demand_profile') or {}
        st.caption(f"Demand profile: **{dp.get('demand_type', 'n/a')}** (ADI {dp.get('adi', float('nan')):.2f}, "
                   f"CV² {dp.get('cv2', float('nan')):.2f}, zero weeks {dp.get('zero_demand_pct', float('nan')):.0f}%) "
                   f"over {len(res.get('historical_demand', []))} weeks.")

    with tab_bt:
        folds = res.get('fold_details', [])
        rows, traces = [], []
        for f in folds:
            acts = np.array(f['actuals'], dtype=float)
            for m in dict.fromkeys([champ, 'Naive', 'Seasonal Naive']):
                p = f['predictions'].get(m)
                if p is None:
                    continue
                p = np.array(p, dtype=float)
                rows.append({'Fold': f['fold'], 'Test weeks': f"{f.get('test_dates', ['?'])[0]} → {f.get('test_dates', ['?'])[-1]}",
                             'Model': m, 'Actual': acts.sum(), 'Forecast': p.sum(),
                             'WAPE %': np.abs(acts - p).sum() / acts.sum() * 100 if acts.sum() else np.nan})
        if folds and 'test_dates' in folds[0]:
            fig = go.Figure()
            xs = [d for f in folds for d in f['test_dates']]
            fig.add_bar(x=xs, y=[a for f in folds for a in f['actuals']], name='Actual (held out)',
                        marker_color='#64748B' if is_dark else '#94A3B8')
            for m, col in [(champ, accent), ('Naive', '#F43F5E'), ('Seasonal Naive', '#F59E0B')]:
                ys = [v for f in folds for v in (f['predictions'].get(m) or [None] * len(f['actuals']))]
                if any(v is not None for v in ys):
                    fig.add_scatter(x=xs, y=ys, name=m, mode='lines', line=dict(color=col, width=3 if m == champ else 1.5))
            fig.update_layout(template=template, height=380, margin=dict(l=10, r=10, t=40, b=10),
                              title=f"Out-of-sample backtest: {len(folds)} folds x {res.get('backtest_test_weeks', 12)} weeks",
                              legend=dict(orientation='h', y=1.12))
            st.plotly_chart(fig, width="stretch")
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                         column_config={'Actual': st.column_config.NumberColumn(format="localized"),
                                        'Forecast': st.column_config.NumberColumn(format="localized"),
                                        'WAPE %': st.column_config.NumberColumn(format="%.1f")})
        errs = res.get('model_errors') or {}
        if errs:
            st.markdown("**Candidates disqualified** (did not produce a valid forecast in every fold)")
            st.dataframe(pd.DataFrame([{'Model': k, 'Reason': v} for k, v in errs.items()]), hide_index=True, width="stretch")

    with tab_method:
        calib = res.get('interval_calibration') or {}
        st.markdown(f"""
- **Series**: weekly (W-MON) billed ODU units from the SKU's first sale to the latest data week; weeks without billing are zeros.
- **Tournament**: every applicable model is backtested on {res.get('backtest_folds', 0)} rolling-origin folds of {res.get('backtest_test_weeks', 12)} weeks (expanding window, strictly chronological). A model must produce a valid forecast in every fold to be ranked.
- **Ranking rule**: lowest mean RMSE across folds (targets expected demand; WAPE-based ranking would favour zero forecasts on lumpy SKUs). WAPE is reported as the accuracy KPI.
- **Leakage controls**: the pooled seasonal profile is re-estimated at each fold cutoff from data up to that cutoff only; ensemble weights use errors from earlier folds only.
- **Interval**: {calib.get('note', 'n/a')}
- **Limitations**: no price, promotion, weather or stock-availability drivers are in the data; new SKUs need ≥ 5 weeks of sales before they can be forecast; with ~2 years of history, seasonality is pooled across SKUs rather than estimated per SKU.
""")


# -----------------------------------------------------------------------------
# PER-MODEL VALIDATION AGAINST FY24-25 ACTUAL BILLING
# -----------------------------------------------------------------------------
VALIDATION_MODES = {
    "📌 One-shot: trained to 30-Jun-2024, forecast all of FY24-25": 'static',
    "🔁 Re-forecast every 4 weeks (how a planner uses it)": 'rolling',
}
LAG_BANDS = {'1-4 wks': 1, '5-8 wks': 5, '9-12 wks': 9}


@st.cache_data(show_spinner=False, max_entries=4)
def _holdout_panel(_mtime: float) -> pd.DataFrame:
    return pd.read_parquet(_hr.PANEL_PATH)


@st.cache_data(show_spinner=False, max_entries=2)
def _batch_models(path: str, _mtime: float) -> pd.DataFrame:
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False, max_entries=48, ttl=6 * 3600)
def compute_model_validation(sku: str, branches: Optional[Sequence[str]], mode: str) -> Dict[str, Any]:
    """Every candidate model forecast from data up to each origin, lined up with FY24-25 actuals."""
    panel = _holdout_panel(os.path.getmtime(_hr.PANEL_PATH))
    # A single SKU x branch already run by the batch harness: identical run_origin output, read instantly
    batch = _hr.models_path(mode)
    if branches and len(branches) == 1 and os.path.exists(batch):
        hit = from_batch(_batch_models(batch, os.path.getmtime(batch)), panel, sku, branches[0], _hr.HOLDOUT_END_WEEK)
        if hit is not None:
            return hit
    if mode == 'static':
        origins, horizon = [_hr.TRAIN_END_WEEK], 52
    else:
        origins = list(pd.date_range(_hr.TRAIN_END_WEEK, _hr.HOLDOUT_END_WEEK - pd.Timedelta(weeks=1), freq='4W-MON'))
        horizon = 12
    return validate_series(panel, sku, list(branches) if branches else None, origins, horizon, _hr.HOLDOUT_END_WEEK)


def render_holdout_model_validation(sku: str, branches: Optional[Sequence[str]], branch_label: str,
                                    highlight_model: Optional[str], is_dark: bool):
    """Section: how each model would have performed on FY24-25 billing it never saw."""
    st.markdown("""
    <div class="subpanel-title" style="margin: 22px 0 6px 0;">
        ✅ Model validation on FY24-25 actual billing (out-of-sample, every model)
    </div>
    """, unsafe_allow_html=True)
    if not os.path.exists(_hr.PANEL_PATH):
        st.info("Holdout data not prepared. Run `python validate_holdout_fy25.py prepare`.")
        return
    panel = _holdout_panel(os.path.getmtime(_hr.PANEL_PATH))
    if sku not in set(panel.sku.unique()):
        st.info(f"No FY24-25 actuals for **{sku}** in the validation file (it covers real outdoor-unit SKUs only; "
                "synthetic EVAL-* and indoor-unit materials cannot be validated).")
        return

    c1, c2, c3 = st.columns([2.4, 1.3, 1])
    with c1:
        mode_label = st.segmented_control("Validation design", list(VALIDATION_MODES), key="mv_mode",
                                          default=list(VALIDATION_MODES)[0])
    mode = VALIDATION_MODES.get(mode_label or list(VALIDATION_MODES)[0])
    with c2:
        lag = st.segmented_control("Forecast lag", list(LAG_BANDS), key="mv_lag", default='1-4 wks',
                                   disabled=(mode == 'static')) or '1-4 wks'
    with c3:
        grain = st.segmented_control("Grain", ['Weekly', 'Monthly'], key="mv_grain", default='Monthly') or 'Monthly'

    msg = ("Fitting every model on data up to 30-Jun-2024..." if mode == 'static'
           else "Re-running the tournament and every model at 13 monthly origins (about a minute the first time)...")
    with st.spinner(msg):
        val = compute_model_validation(sku, tuple(branches) if branches else None, mode)
    if val.get('status') != 'success':
        st.warning(f"Validation not possible for {sku} ({branch_label}): {val.get('error')}")
        return

    fc = val['forecasts']
    if mode == 'rolling':
        lo = LAG_BANDS[lag]
        fc = fc[(fc.step >= lo) & (fc.step <= lo + 3)]
    table = score_models(fc, val.get('backtest_wape'))
    bt = table['Backtest WAPE % (pre-holdout)']
    table['Backtest rank'] = bt.rank(method='min').astype('Int64')

    models = table['Model'].tolist()
    defaults = [m for m in dict.fromkeys([highlight_model, CHAMPION_LABEL, 'Seasonal Naive', 'Moving Average']) if m in models]
    chosen = st.multiselect("Models to plot against actual billing", models, default=defaults[:4], key=f"mv_models_{sku}")

    template = 'plotly_dark' if is_dark else 'plotly_white'
    palette = ['#00E5FF', '#F59E0B', '#A855F7', '#10B981', '#F43F5E', '#3B82F6', '#EC4899', '#84CC16']
    d = fc.copy()
    d['x'] = d.week.dt.to_period('M').dt.to_timestamp() if grain == 'Monthly' else d.week
    act = d.drop_duplicates(['week']).groupby('x')['actual'].sum()
    fig = go.Figure()
    fig.add_bar(x=act.index, y=act.values, name='Actual FY24-25 billing', marker_color='#64748B' if is_dark else '#94A3B8')
    for i, m in enumerate(chosen):
        s = d[d.model == m].groupby('x')['forecast'].sum()
        fig.add_scatter(x=s.index, y=s.values, name=m, mode='lines+markers',
                        line=dict(color=palette[i % len(palette)], width=3 if m in (highlight_model, CHAMPION_LABEL) else 2))
    fig.update_layout(template=template, height=420, margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation='h', y=1.15),
                      title=f"{sku} · {branch_label}: actual vs forecast ({grain.lower()}"
                            f"{'' if mode == 'static' else ', lag ' + lag})", yaxis_title='ODU units')
    st.plotly_chart(fig, width="stretch")

    best = table.iloc[0]
    champ_rows = table[table.Model == CHAMPION_LABEL]
    champ_line = ""
    if len(champ_rows):
        cr = champ_rows.iloc[0]
        champ_line = (f" The auto-selected champion ranked **#{int(cr['Holdout rank'])} of {len(table)}** "
                      f"(monthly WAPE {cr['Monthly WAPE %']:.1f}%).")
    st.markdown(f"Best model on the holdout (lowest monthly RMSE, the tournament's rule): **{best['Model']}**, "
                f"monthly WAPE {best['Monthly WAPE %']:.1f}% (bias {best['Bias %']:+.1f}%).{champ_line}")
    st.dataframe(
        table, hide_index=True, width="stretch",
        column_config={
            'Forecast units': st.column_config.NumberColumn(format="localized"),
            'Actual units': st.column_config.NumberColumn(format="localized"),
            'Monthly accuracy %': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
        })
    n_origins = len(val.get('champions') or {})
    design = ("Each model was fitted on data up to 30-Jun-2024 only and forecast 52 weeks ahead in one shot."
              if mode == 'static' else
              f"At each of {n_origins} monthly origins every model was refitted on history plus actuals to that date; "
              f"scores use the forecasts made {lag} before each week.")
    st.caption(f"{design} Ranked on monthly RMSE, the rule the champion tournament uses; WAPE = Σ|actual − forecast| ÷ Σ actual "
               "is shown alongside but is not used for ranking because a zero forecast can minimise it on lumpy SKUs. "
               "Backtest WAPE is what the tournament saw before the holdout (4 folds × 12 weeks).")
    if val.get('errors'):
        with st.expander(f"{len(val['errors'])} model(s) or origin(s) could not be validated"):
            st.dataframe(pd.DataFrame([{'Model / origin': k, 'Reason': v} for k, v in val['errors'].items()]),
                         hide_index=True, width="stretch")
