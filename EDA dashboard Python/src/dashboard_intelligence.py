"""
Executive Demand Intelligence & Analytics UI Engine
Provides interactive components for:
- Executive Cockpit Action Queue (Dynamic fleet calculations)
- SKU Demand Profiling & Champion Selection Cards
- Model Lab & Backtesting Leaderboard (Real walk-forward validation)
- Inventory Decision Support & Safety Stock Sensitivity (Real forecast inputs)
- Scenario & What-If Simulator (Real base forecast inputs)
- Forecast Monitoring & Drift Radar (Real historical tracking)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

from src.selection.demand_classifier import DemandClassifier
from src.selection.champion_challenger import ChampionChallengerManager
from src.selection.model_selector import ModelSelector
from src.inventory.inventory_engine import InventoryEngine
from src.scenarios.simulator import ScenarioSimulator
from src.explainability.shap_analysis import ForecastExplainer
from src.monitoring.forecast_monitor import ForecastMonitor
from src.monitoring.drift import DriftDetector
from src.monitoring.alerts import AlertEngine
from src.forecasting.ensemble import EnsembleForecaster
from src.forecasting.baseline import BaselineForecastingModels
from src.forecasting.statistical import StatisticalModels
from src.forecasting.seasonal_profile import SeasonalIndexForecaster
from src.forecasting.model_zoo import ALL_MODELS, INTERMITTENT_MAP, ML_MAP
from src.validation.backtesting import RollingOriginBacktest
from src.validation.cross_validation import ModelLeaderboard
from src.validation.leakage_audit import LeakageAuditor
from src.hierarchy.aggregation import HierarchyAggregator
from src.hierarchy.reconciliation import HierarchicalReconciler
from src.services.forecast_service import ForecastService
from src.features import FeatureEngineer


import logging
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 1. EXECUTIVE ACTION QUEUE (EXECUTIVE COCKPIT UPGRADE)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_fleet_action_queue(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Action items for the 8 highest-volume SKU x Branch series of the latest 52 weeks.
    Health is a genuine out-of-sample check: the Seasonal Index model is fitted on data up to
    8 weeks ago and compared with the 8 weeks of billing since, judged against the same check
    one window earlier. Stock-out alerts are not raised: the billing extract has no on-hand stock.
    """
    branch_col = next((c for c in ['SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Branch', 'branch'] if c in df.columns), None)
    sku_col = next((c for c in ['Material', 'sku'] if c in df.columns), 'Material')
    demand_col = next((c for c in ['Billing Quantity ODU', 'total_demand', 'quantity_odu'] if c in df.columns), None)
    date_col = next((c for c in ['Billing Date', 'date'] if c in df.columns), None)
    if not (branch_col and sku_col and demand_col and date_col):
        return []

    dates = pd.to_datetime(df[date_col], errors='coerce')
    recent = df[dates >= dates.max() - pd.Timedelta(weeks=52)]
    top_pairs = recent.groupby([sku_col, branch_col])[demand_col].sum().sort_values(ascending=False).head(8)

    selector = ModelSelector()
    drift_detector = DriftDetector()
    monitor = ForecastMonitor()
    window = 8

    def _check(y, wk, profile_factory, end):
        """Seasonal Index forecast made at y[:end-window], scored on y[end-window:end]."""
        cut = end - window
        prof = profile_factory(wk[cut - 1]) if cut >= 5 else None
        if prof is None:
            return None, None
        si = SeasonalIndexForecaster(window=8).fit(y[:cut], prof.factors(wk[:cut]))
        return y[cut:end], si.predict(prof.factors(wk[cut:end]))

    sku_assessments = []
    for (s_val, b_val), _ in top_pairs.items():
        try:
            prep = selector.prepare_series(df, s_val, b_val)
            if prep.get('status') != 'success':
                continue
            y = prep['sku_data']['total_demand'].values.astype(float)
            wk = pd.DatetimeIndex(prep['sku_data']['date'])
            if len(y) < 2 * window + 5:
                continue
            act, fc = _check(y, wk, prep['profile_factory'], len(y))
            ref_act, ref_fc = _check(y, wk, prep['profile_factory'], len(y) - window)
            if act is None:
                continue
            ref_wape = (float(np.abs(ref_act - ref_fc).sum() / ref_act.sum() * 100)
                        if ref_act is not None and ref_act.sum() > 0 else None)
            health = monitor.evaluate_model_health(act, fc, model_name='Seasonal Index', reference_wape=ref_wape)
            drift = drift_detector.detect_demand_drift(y)
            sku_assessments.append({
                'sku': str(s_val),
                'branch': str(b_val),
                'stockout_risk_pct': None,
                'health_status': health['health_status'],
                'health_detail': health['recommendation'],
                'tracking_signal': health['tracking_signal'],
                'drift_detected': drift['drift_detected'],
                'psi': drift['psi']
            })
        except Exception as e:
            logger.debug(f"Action queue assessment failed for {s_val}/{b_val}: {e}")
            continue

    return AlertEngine.generate_action_queue(sku_assessments)


def render_executive_action_queue(df: pd.DataFrame, theme: str = "dark"):
    """Render prioritized operational action items calculated dynamically from fleet metrics."""
    is_dark = (theme == "dark")
    accent_cyan = "#00E5FF" if is_dark else "#0284C7"
    accent_green = "#10B981" if is_dark else "#047857"
    
    action_items = compute_fleet_action_queue(df)
    action_count = len(action_items)
    badge_type = "kpi-badge-rose" if action_count > 0 else "kpi-badge-green"
    badge_label = f"{action_count} Action Items Required" if action_count > 0 else "Fleet Nominal (0 Alerts)"

    st.markdown(f"""
    <div class="glass-panel" style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div class="subpanel-title" style="color: {accent_cyan}; margin: 0; display: flex; align-items: center; gap: 8px;">
                <span>⚡</span> Executive Demand Action Queue (Live Fleet Intelligence)
            </div>
            <span class="kpi-badge {badge_type}">{badge_label}</span>
        </div>
        <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 14px;">
            Top 8 SKU &times; branch series of the last 52 weeks: an 8-week out-of-sample forecast check (tracking signal and error vs the previous window) and demand-distribution drift (PSI). Stock-out alerts need on-hand inventory, which is not in the billing extract.
        </p>
    """, unsafe_allow_html=True)
    
    if action_items:
        for item in action_items:
            priority = item.get('priority', 'INFO')
            badge_class = 'kpi-badge-rose' if priority == 'HIGH' else ('kpi-badge-amber' if priority == 'MEDIUM' else 'kpi-badge-cyan')
            icon = '🚨' if priority == 'HIGH' else ('⚠️' if priority == 'MEDIUM' else '📊')
            
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-glass); border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="font-size: 14px; color: var(--text-primary);">{icon} {item['title']}</strong>
                    <span class="kpi-badge {badge_class}">{priority}</span>
                </div>
                <p style="font-size: 12.5px; color: var(--text-secondary); margin: 0 0 6px 0;">{item['detail']}</p>
                <div style="font-size: 12px; color: {accent_green}; font-weight: 600;">
                    &bull; Prescribed Directive: <span style="color: var(--text-primary);">{item['recommended_action']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 20px; margin-bottom: 4px;">🛡️</div>
            <strong style="color: {accent_green}; font-size: 14px;">No forecast-health or drift alerts</strong>
            <p style="font-size: 12.5px; color: var(--text-secondary); margin: 4px 0 0 0;">
                The 8 highest-volume SKU &times; branch series show no tracking-signal breach, accuracy degradation or distribution drift in the latest 8-week check.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. MODEL LAB & BACKTESTING LEADERBOARD VIEW
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Executing walk-forward cross-validation across candidate models...")
def compute_cached_model_lab_backtest(df: pd.DataFrame, sel_branch: str, sel_sku: str, folds: int, min_train: int = 13):
    """Same series preparation, seasonal profile and 12-week folds as the production champion tournament."""
    selector = ModelSelector()
    prep = selector.prepare_series(df, sel_sku, sel_branch)
    if prep.get('status') != 'success':
        return {'leaderboard': pd.DataFrame(), 'reason': prep.get('error')}, 0
    sku_series_df = prep['sku_data']
    y = sku_series_df['total_demand'].values.astype(float)
    dates = sku_series_df['date'].values

    backtester = RollingOriginBacktest(n_folds=folds, test_weeks=12, min_train_weeks=min_train)
    bt_results = backtester.evaluate_sku_series(y, dates=dates, sku_df=sku_series_df,
                                                profile_factory=prep['profile_factory'])

    # Leakage audit on the engineered feature matrix the ML candidates are trained on
    try:
        feat_df, _ = FeatureEngineer().engineer_features(sku_series_df)
        bt_results['audit_report'] = LeakageAuditor().run_full_audit(feat_df, folds=backtester.generate_folds(len(y)))
    except Exception as e:
        logger.warning(f"Leakage audit check skipped: {e}")
        bt_results['audit_report'] = {'not_run': True, 'error': str(e)}

    return bt_results, len(y)


def render_model_lab_page(df: pd.DataFrame, theme: str = "dark"):
    """Dedicated Model Lab view with walk-forward rolling-origin benchmark leaderboard."""
    is_dark = (theme == "dark")
    accent_color = "#00E5FF" if is_dark else "#0284C7"
    
    st.markdown(f"""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🔬 Model Lab & Backtesting Leaderboard</h2>
            <p class="section-subtitle">Rolling-origin walk-forward cross-validation (12-week folds, same engine as the forecast page), ranked on RMSE, with stability scoring</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Selection Bar
    branch_col = next((c for c in ['SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Branch', 'branch'] if c in df.columns), None)
    sku_col = next((c for c in ['Material', 'sku'] if c in df.columns), 'Material')
    demand_col = next((c for c in ['Billing Quantity ODU', 'total_demand', 'quantity_odu'] if c in df.columns), None)
    date_col = next((c for c in ['Billing Date', 'date'] if c in df.columns), None)
    
    if not branch_col or not sku_col or not demand_col:
        st.error("Required dimensions (Branch, SKU, Demand) not found in dataset.")
        return

    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c1:
        branches = sorted(df[branch_col].dropna().unique().tolist())
        sel_branch = st.selectbox("Select Regional Branch:", branches, index=0)
    with c2:
        top_skus = df[df[branch_col] == sel_branch].groupby(sku_col)[demand_col].sum().sort_values(ascending=False).head(20).index.tolist()
        if not top_skus:
            top_skus = df.groupby(sku_col)[demand_col].sum().sort_values(ascending=False).head(20).index.tolist()
        sel_sku = st.selectbox("Select Target SKU:", top_skus, index=0)
    with c3:
        folds = st.slider("Walk-Forward Folds:", min_value=2, max_value=6, value=3)
        
    min_train = 13
    bt_results, len_y = compute_cached_model_lab_backtest(df, sel_branch, sel_sku, folds, min_train)
    leaderboard_df = bt_results.get('leaderboard', pd.DataFrame())
    
    # FAIL LOUDLY if history is insufficient - ZERO SYNTHETIC METRICS
    if leaderboard_df.empty:
        st.markdown(f"""
        <div class="glass-panel" style="padding: 24px; border-left: 4px solid #F43F5E; margin-top: 14px;">
            <div style="font-size: 17px; font-weight: 700; color: #F43F5E; margin-bottom: 8px;">
                ⚠️ Walk-Forward Validation Halted: Insufficient Historical Observations
            </div>
            <p style="font-size: 13.5px; color: var(--text-secondary); margin-bottom: 8px;">
                Selected series <strong>{sel_sku}</strong> at <strong>{sel_branch}</strong> contains only <strong>{len_y}</strong> weekly periods.
            </p>
            <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">
                Walk-forward cross-validation needs at least 5 weekly periods with 2 or more billing weeks
                ({folds} full 12-week folds need {min_train + folds * 12} weeks). {bt_results.get('reason') or ''}
            </p>
            <div style="font-size: 12.5px; color: {accent_color}; font-weight: 500;">
                💡 Corrective Actions: Select fewer folds (e.g. 2 folds), or choose an established SKU with ≥24 weeks of active billing history.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    lb_manager = ModelLeaderboard(leaderboard_df)
    champion = lb_manager.get_champion()
    baseline_comp = lb_manager.compare_with_baseline()
    
    audit_report = bt_results.get('audit_report') or {'not_run': True, 'error': 'audit unavailable'}
    if audit_report.get('not_run'):
        audit_value, audit_sub, audit_color = "Not run", f"Audit error: {audit_report.get('error', '')[:60]}", "#F59E0B"
    else:
        audit_value = f"{audit_report['leakage_percentage']:.1f}% Leakage"
        audit_sub = f"{audit_report['checks_passed']}/{audit_report['checks_total']} checks passed on the ML feature matrix"
        audit_color = "#00E5FF" if audit_report.get('is_fully_compliant') else "#F43F5E"
    lift = baseline_comp.get('pct_accuracy_lift', 0.0)
    
    # 4 Luxury KPI Cards for Model Lab
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-cyan">Tournament Champion</span><span>🏆</span></div>
            <div class="kpi-label">Active Champion Model</div>
            <div class="kpi-value" style="font-size: 18px !important;">{champion['model']}</div>
            <div style="font-size: 12px; color: var(--text-secondary);">Lowest RMSE ({champion['mean_rmse']:.1f}) &bull; WAPE <strong>{champion['mean_wape']:.1f}%</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-green">Benchmarked Lift</span><span>🚀</span></div>
            <div class="kpi-label">WAPE change vs {baseline_comp.get('baseline_name', 'Naive')}</div>
            <div class="kpi-value" style="color: {'#10B981' if lift > 0 else '#F43F5E'} !important;">{-lift:+.1f}%</div>
            <div style="font-size: 12px; color: var(--text-secondary);">WAPE {baseline_comp.get('champion_wape', 0):.1f}% vs <strong>{baseline_comp.get('baseline_wape', 0):.1f}%</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-amber">Stability Index</span><span>🛡️</span></div>
            <div class="kpi-label">Cross-Fold Consistency</div>
            <div class="kpi-value">{float(champion.get('stability_score', 0.0)):.1f} / 100</div>
            <div style="font-size: 12px; color: var(--text-secondary);">Std Dev across folds: <strong>±{champion.get('std_wape', 0.0):.1f}%</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-cyan">Validation Integrity</span><span>🔒</span></div>
            <div class="kpi-label">Temporal Leakage Audit</div>
            <div class="kpi-value" style="color: {audit_color} !important;">{audit_value}</div>
            <div style="font-size: 12px; color: var(--text-secondary);">{audit_sub}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Leaderboard Table
    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 8px;">
        📊 Consolidated Model Tournament Benchmark Leaderboard
    </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(lb_manager.to_display_table(), width="stretch")

    # Visual Comparison Chart (WAPE & RMSE)
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_wape = px.bar(
            leaderboard_df, x='model', y='mean_wape', error_y='std_wape',
            title="Forecast Error Rate (Mean WAPE % & Fold Dispersion)",
            labels={'mean_wape': 'Mean WAPE (%)', 'model': 'Candidate Model'},
            color='mean_wape',
            color_continuous_scale=[[0, '#10B981'], [0.5, '#F59E0B'], [1, '#F43F5E']]
        )
        fig_wape.update_layout(height=380, template='plotly_dark' if is_dark else 'plotly_white')
        st.plotly_chart(fig_wape, width="stretch")

    with chart_col2:
        fold_details = bt_results.get('fold_details', [])
        if fold_details:
            fold_chart_data = []
            for f in fold_details:
                f_num = f"Fold {f['fold']}"
                for m_name, preds in f.get('predictions', {}).items():
                    if m_name in [champion['model'], 'Naive', 'Moving Average', 'Ensemble (Consensus)']:
                        actuals_arr = np.array(f['actuals'])
                        preds_arr = np.array(preds)
                        denom = np.sum(actuals_arr) or 1.0
                        fold_wape = float(np.sum(np.abs(actuals_arr - preds_arr)) / denom * 100.0)
                        fold_chart_data.append({'Fold': f_num, 'Model': m_name, 'WAPE': fold_wape})
            if fold_chart_data:
                f_df = pd.DataFrame(fold_chart_data)
                fig_folds = px.line(
                    f_df, x='Fold', y='WAPE', color='Model', markers=True,
                    title="Fold-by-Fold Error Stability Comparison",
                    color_discrete_sequence=['#00E5FF', '#F43F5E', '#10B981', '#F59E0B']
                )
                fig_folds.update_layout(height=380, template='plotly_dark' if is_dark else 'plotly_white')
                st.plotly_chart(fig_folds, width="stretch")
            else:
                fig_rmse = px.bar(
                    leaderboard_df, x='model', y='mean_rmse',
                    title="Root Mean Squared Error (RMSE by Model)",
                    labels={'mean_rmse': 'RMSE', 'model': 'Candidate Model'},
                    color_discrete_sequence=['#00E5FF' if is_dark else '#0284C7']
                )
                fig_rmse.update_layout(height=380, template='plotly_dark' if is_dark else 'plotly_white')
                st.plotly_chart(fig_rmse, width="stretch")


# -----------------------------------------------------------------------------
# SHARED: SKU / BRANCH SELECTION + CANONICAL FORECAST
# -----------------------------------------------------------------------------
REGION_OPTION = "All branches (South Region)"


def _sku_branch_controls(df: pd.DataFrame, key: str, sku_label: str = "Select Target SKU:"):
    """SKU picker (top 20 by volume) plus an explicit branch picker; None branch = region total."""
    sku_col = next((c for c in ['Material', 'sku'] if c in df.columns), 'Material')
    branch_col = next((c for c in ['SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Branch', 'branch'] if c in df.columns), None)
    demand_col = next((c for c in ['Billing Quantity ODU', 'total_demand', 'quantity_odu'] if c in df.columns), None)
    top_skus = df.groupby(sku_col)[demand_col].sum().sort_values(ascending=False).head(20).index.tolist()
    sel_sku = st.selectbox(sku_label, top_skus, key=f"{key}_sku")
    options = [REGION_OPTION]
    if branch_col:
        vols = df[df[sku_col] == sel_sku].groupby(branch_col)[demand_col].sum().sort_values(ascending=False)
        options += [str(b) for b in vols.index]
    sel_branch = st.selectbox("Branch:", options, key=f"{key}_branch")
    return sel_sku, (None if sel_branch == REGION_OPTION else sel_branch)


@st.cache_data(show_spinner="Running the champion model tournament (out-of-sample backtest)...", max_entries=64)
def compute_cached_service_forecast(df: pd.DataFrame, sel_sku: Optional[str], branch: Optional[str], horizon: int = 12):
    """Canonical champion forecast package from ForecastService (same engine as every other page)."""
    return ForecastService(df).get_forecast(sel_sku, branch, horizon=horizon)


def _champion_caption(f_res: Dict[str, Any]) -> str:
    champ = f_res.get('champion') or {}
    return (f"Champion **{champ.get('model_name', 'n/a')}**: backtest WAPE {champ.get('wape', float('nan')):.1f}% "
            f"over {f_res.get('backtest_folds') or 0} out-of-sample 12-week fold(s).")


# -----------------------------------------------------------------------------
# 3. INVENTORY INTELLIGENCE COCKPIT VIEW
# -----------------------------------------------------------------------------
def render_inventory_page(df: pd.DataFrame, theme: str = "dark"):
    """Inventory policy from the champion forecast and its out-of-sample error distribution."""
    is_dark = (theme == "dark")

    st.markdown(f"""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">📦 Inventory Intelligence & Optimization Cockpit</h2>
            <p class="section-subtitle">Lead time demand, safety stock, reorder point & working capital from the champion forecast and its backtest errors</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not any(c in df.columns for c in ['Billing Quantity ODU', 'total_demand', 'quantity_odu']):
        st.error("Required demand or SKU columns missing.")
        return

    ic1, ic2, ic3, ic4, ic5 = st.columns([1.4, 1.2, 1, 1, 1])
    with ic1:
        sel_sku, sel_branch = _sku_branch_controls(df, "inv")
    with ic2:
        lead_time = st.slider("Replenishment Lead Time (Weeks):", 1, 8, 2, key="inv_lt")
    with ic3:
        target_sl = st.select_slider("Target Service Level:", [0.85, 0.90, 0.95, 0.98, 0.99], value=0.95,
                                     format_func=lambda x: f"{int(x*100)}%", key="inv_sl")
    with ic4:
        unit_cost = st.number_input("Unit RAC Cost (INR):", min_value=5000, max_value=150000, value=25000, step=1000,
                                    help="Planning assumption; the billing extract has no cost data.")
    with ic5:
        on_hand = st.number_input("Current on-hand (units):", min_value=0, value=None, step=10,
                                  help="Optional. Needed to estimate stock-out probability; not in the billing extract.")

    f_res = compute_cached_service_forecast(df, sel_sku, sel_branch, 12)
    if f_res.get('status') != 'success':
        st.info(f"Cannot forecast {sel_sku}: {f_res.get('message') or f_res.get('error', 'insufficient history')}")
        return

    inv_engine = InventoryEngine(default_lead_time=lead_time, default_service_level=target_sl, unit_cost=unit_cost)
    residuals = f_res.get('historical_residuals')
    policy = inv_engine.calculate_inventory_policy(
        np.asarray(f_res['p50'], dtype=float), historical_demand=f_res.get('historical_demand'),
        forecast_rmse=(f_res.get('champion') or {}).get('rmse'),
        forecast_residuals=np.asarray(residuals, dtype=float) if residuals and len(residuals) >= 3 else None,
        lead_time_weeks=lead_time, target_service_level=target_sl, current_on_hand=on_hand
    )
    st.caption(_champion_caption(f_res) + f" Safety-stock uncertainty basis: `{policy.get('uncertainty_basis', 'n/a')}`.")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-cyan">Lead Time Demand</span><span>⏱️</span></div>
            <div class="kpi-label">Demand During Lead Time</div>
            <div class="kpi-value">{policy['lead_time_demand']:,.0f} units</div>
            <div style="font-size: 12px; color: var(--text-secondary);">Next {lead_time} forecast weeks ({policy['mean_weekly_demand']:.1f}/week avg)</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-green">Safety Buffer</span><span>🛡️</span></div>
            <div class="kpi-label">Recommended Safety Stock</div>
            <div class="kpi-value" style="color: #10B981 !important;">{policy['safety_stock_units']:,} units</div>
            <div style="font-size: 12px; color: var(--text-secondary);">{policy['target_service_level_pct']:.0f}% cycle service level</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-amber">Threshold Trigger</span><span>🎯</span></div>
            <div class="kpi-label">Reorder Point (ROP)</div>
            <div class="kpi-value" style="color: #F59E0B !important;">{policy['reorder_point_units']:,} units</div>
            <div style="font-size: 12px; color: var(--text-secondary);">LTD ({policy['lead_time_demand']:.0f}) + SS ({policy['safety_stock_units']})</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-cyan">Working Capital</span><span>💰</span></div>
            <div class="kpi-label">Capital in Safety Stock</div>
            <div class="kpi-value">₹{policy['safety_stock_capital_inr']:,.0f}</div>
            <div style="font-size: 12px; color: var(--text-secondary);">At the assumed unit cost; weekly holding ₹{policy['weekly_holding_cost_inr']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    s_col1, s_col2 = st.columns([1.8, 1.2])
    with s_col1:
        st.markdown("""
        <div class="subpanel-title" style="margin-bottom: 10px;">
            📐 Service Level vs Safety Stock & Capital Sensitivity Matrix
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(policy['sensitivity_table'], width="stretch")

    with s_col2:
        risk = policy.get('stockout_risk_pct')
        if risk is None:
            st.info("Enter the current on-hand stock to estimate the probability of a stock-out within the lead time.")
        else:
            fig_risk = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk,
                number={'suffix': "%", 'font': {'size': 38, 'family': "Outfit", 'color': '#FFFFFF' if is_dark else '#0F172A'}},
                title={'text': "Stock-out Probability (lead time)", 'font': {'size': 16, 'family': "Outfit"}},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': '#10B981' if risk <= 10 else ('#F59E0B' if risk <= 25 else '#F43F5E')},
                    'steps': [
                        {'range': [0, 10], 'color': 'rgba(16, 185, 129, 0.2)'},
                        {'range': [10, 25], 'color': 'rgba(245, 158, 11, 0.2)'},
                        {'range': [25, 100], 'color': 'rgba(244, 63, 94, 0.2)'}
                    ]
                }
            ))
            fig_risk.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20), template='plotly_dark' if is_dark else 'plotly_white')
            st.plotly_chart(fig_risk, width="stretch")


# -----------------------------------------------------------------------------
# 4. SCENARIO & WHAT-IF SIMULATOR VIEW
# -----------------------------------------------------------------------------
def render_scenario_simulator_page(df: pd.DataFrame, theme: str = "dark"):
    """What-if scenarios applied to the champion forecast; uncertainty from its backtest errors."""
    is_dark = (theme == "dark")
    accent_color = "#00E5FF" if is_dark else "#0284C7"

    st.markdown(f"""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🔮 Scenario & What-If Stress Simulator</h2>
            <p class="section-subtitle">Apply assumed demand shocks (heatwave, schemes, supply constraints) to the champion forecast</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not any(c in df.columns for c in ['Billing Quantity ODU', 'total_demand', 'quantity_odu']):
        st.error("Required demand or SKU columns missing.")
        return

    sc1, sc2 = st.columns([1.5, 2.5])
    with sc1:
        sel_sku, sel_branch = _sku_branch_controls(df, "scen", "Select Focus SKU:")
        scen_choice = st.selectbox(
            "Choose Demand Scenario:",
            list(ScenarioSimulator.SCENARIO_PROFILES.keys()) + ["Custom Percentage Shock"]
        )
        multiplier = None
        if scen_choice == "Custom Percentage Shock":
            custom_pct = st.slider("Demand Adjustment Percentage (%):", -50, 100, 25, step=5)
            multiplier = 1.0 + (custom_pct / 100.0)

    f_res = compute_cached_service_forecast(df, sel_sku, sel_branch, 12)
    if f_res.get('status') != 'success':
        st.info(f"Cannot forecast {sel_sku}: {f_res.get('message') or f_res.get('error', 'insufficient history')}")
        return
    base_curve = np.array(f_res['p50'], dtype=float)
    residuals = f_res.get('historical_residuals') or None

    simulator = ScenarioSimulator()
    if multiplier is not None:
        res = simulator.simulate(base_curve, custom_multiplier=multiplier, forecast_residuals=residuals)
    else:
        res = simulator.simulate(base_curve, scenario_name=scen_choice, forecast_residuals=residuals)

    with sc2:
        st.markdown(f"""
        <div class="glass-panel" style="padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong style="color: {accent_color}; font-size: 16px;">Scenario: {res['scenario_name']}</strong>
                <span class="kpi-badge kpi-badge-cyan">{res['multiplier']:.2f}x assumed multiplier</span>
            </div>
            <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">{res['description']}</p>
            <div style="display: flex; gap: 20px; font-size: 13px;">
                <div>Primary Driver: <strong>{res['driver']}</strong></div>
                <div>Volume Delta: <strong style="color: {'#10B981' if res['delta_volume_units'] >= 0 else '#F43F5E'};">{res['delta_volume_units']:+,.0f} units ({res['delta_volume_pct']:+.1f}%)</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(_champion_caption(f_res) + " Scenario multipliers are planning assumptions, not estimated from the data.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    future_weeks = pd.to_datetime(f_res.get('forecast_dates', pd.date_range(pd.Timestamp.today(), periods=12, freq='W-MON')))
    fig_scen = go.Figure()
    fig_scen.add_trace(go.Scatter(
        x=future_weeks, y=res['base_forecast'], mode='lines+markers',
        name='Base Case (Champion Forecast)', line=dict(color='#94A3B8', dash='dash', width=2)
    ))
    fig_scen.add_trace(go.Scatter(
        x=future_weeks, y=res['scenario_forecast'], mode='lines+markers',
        name=f"Scenario ({res['scenario_name']})",
        line=dict(color='#00E5FF' if is_dark else '#0284C7', width=3.5),
        fill='tonexty', fillcolor='rgba(0, 229, 255, 0.12)' if is_dark else 'rgba(2, 132, 199, 0.12)'
    ))
    fig_scen.update_layout(
        title=f"12-Week Forward Demand: Base vs {res['scenario_name']}",
        height=380, template='plotly_dark' if is_dark else 'plotly_white'
    )
    st.plotly_chart(fig_scen, width="stretch")

    st.markdown("""
    <div class="subpanel-title" style="margin-bottom: 10px;">
        📋 Comparative Scenario Matrix & Working Capital Requirements (2-week lead time, 95% service)
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(simulator.get_all_scenarios_summary(base_curve, forecast_residuals=residuals), width="stretch")


# -----------------------------------------------------------------------------
# 5. FORECAST MONITORING & DRIFT RADAR VIEW
# -----------------------------------------------------------------------------
def render_monitoring_drift_page(df: pd.DataFrame, theme: str = "dark"):
    """Model health from the champion's latest out-of-sample period and demand-distribution drift."""
    is_dark = (theme == "dark")
    accent_color = "#00E5FF" if is_dark else "#0284C7"

    st.markdown(f"""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">📡 Forecast Monitoring & Drift Radar</h2>
            <p class="section-subtitle">Tracking signal on out-of-sample forecasts, accuracy degradation vs earlier periods, and Population Stability Index (PSI)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not any(c in df.columns for c in ['Billing Quantity ODU', 'total_demand', 'quantity_odu']):
        st.error("Required demand or SKU columns missing.")
        return

    m1, m2 = st.columns([1.5, 2.5])
    with m1:
        sel_sku, sel_branch = _sku_branch_controls(df, "mon", "Select Audited SKU:")
        eval_window = st.slider("Drift comparison window (recent weeks):", 4, 16, 8)

    f_res = compute_cached_service_forecast(df, sel_sku, sel_branch, 12)
    if f_res.get('status') != 'success':
        st.info(f"Cannot evaluate {sel_sku}: {f_res.get('message') or f_res.get('error', 'insufficient history')}")
        return

    health_res = f_res['model_health']
    y_actuals = np.asarray(f_res['historical_demand'], dtype=float)
    drift_res = DriftDetector().detect_demand_drift(y_actuals, recent_window=eval_window)

    with m2:
        st.markdown(f"""
        <div class="glass-panel" style="padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="subpanel-title" style="margin:0; font-size: 16px; color: {accent_color};">Model Health Status:</span>
                <span class="kpi-badge kpi-badge-{health_res.get('badge_color', 'cyan')}">{health_res['health_status']}</span>
            </div>
            <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 10px;">{health_res['recommendation']}</p>
            <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">Evaluated on: {health_res.get('evaluation_window', 'n/a')} (forecasts made before these weeks, compared with actual billing).</p>
            <div style="display: flex; justify-content: space-between; font-size: 12.5px; border-top: 1px solid var(--border-glass); padding-top: 8px;">
                <span>Distribution Drift Status: <strong style="color: {'#10B981' if not drift_res['drift_detected'] else '#F43F5E'};">{drift_res['drift_status']}</strong></span>
                <span>PSI Score: <strong>{drift_res['psi']:.3f}</strong> (Limit: 0.25)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    t_c1, t_c2 = st.columns(2)
    with t_c1:
        ts_traj = health_res.get('ts_trajectory', [])
        last_fold = (f_res.get('fold_details') or [{}])
        last_fold = last_fold[-1] if last_fold else {}
        periods = last_fold.get('test_dates') or [f"W{i+1}" for i in range(len(ts_traj))]
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=periods[:len(ts_traj)], y=ts_traj, mode='lines+markers', name='Tracking Signal',
            line=dict(color='#00E5FF' if is_dark else '#0284C7', width=3)
        ))
        fig_ts.add_hline(y=4.0, line_dash="dash", line_color="#F59E0B", annotation_text="Upper Watch (+4.0)")
        fig_ts.add_hline(y=-4.0, line_dash="dash", line_color="#F59E0B", annotation_text="Lower Watch (-4.0)")
        fig_ts.add_hline(y=6.0, line_dash="dash", line_color="#F43F5E", annotation_text="Upper Breach (+6.0)")
        fig_ts.add_hline(y=-6.0, line_dash="dash", line_color="#F43F5E", annotation_text="Lower Breach (-6.0)")
        fig_ts.update_layout(
            title="Tracking Signal (cumulative error / MAD) on the latest out-of-sample period",
            yaxis_title="Tracking Signal",
            height=360, template='plotly_dark' if is_dark else 'plotly_white'
        )
        st.plotly_chart(fig_ts, width="stretch")

    with t_c2:
        n = len(y_actuals)
        ref_pts = y_actuals[:-eval_window] if n > eval_window else y_actuals
        cur_pts = y_actuals[-eval_window:] if n > eval_window else y_actuals
        fig_drift = go.Figure()
        fig_drift.add_trace(go.Histogram(x=ref_pts, name=f"Baseline Reference ({len(ref_pts)}W)", opacity=0.65, marker_color='#6366F1'))
        fig_drift.add_trace(go.Histogram(x=cur_pts, name=f"Recent Window ({len(cur_pts)}W)", opacity=0.65,
                                         marker_color='#00E5FF' if is_dark else '#0284C7'))
        fig_drift.update_layout(
            title=f"Weekly demand distribution: PSI = {drift_res['psi']:.3f} (KS p-val: {drift_res['ks_p_value']:.2f})",
            barmode='overlay', height=360, template='plotly_dark' if is_dark else 'plotly_white'
        )
        st.plotly_chart(fig_drift, width="stretch")
        st.caption("Drift compares weekly billing volumes, so the seasonal cycle itself can register as drift.")


# -----------------------------------------------------------------------------
# 6. HIERARCHICAL RECONCILIATION VIEW
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Forecasting the region and each branch total with the champion engine...")
def compute_cached_hierarchy_reconciliation(df: pd.DataFrame, horizon: int = 12) -> Dict[str, Any]:
    """
    Region total and each branch total forecast directly by the champion engine (all SKUs, ODU).
    Bottom-up = sum of branch forecasts; top-down = direct region forecast split by the branches'
    last-52-week shares. SKU allocation splits each branch forecast by SKU share of its last 13 weeks.
    """
    branch_col = next((c for c in ['SALES OFFICE CODE', 'SALES OFFICE CODE.1', 'Branch', 'branch'] if c in df.columns), None)
    sku_col = next((c for c in ['Material', 'sku'] if c in df.columns), 'Material')
    demand_col = next((c for c in ['Billing Quantity ODU', 'total_demand', 'quantity_odu'] if c in df.columns), None)
    date_col = next((c for c in ['Billing Date', 'date'] if c in df.columns), None)
    if not branch_col or not demand_col or not date_col:
        return {}

    # Aggregate series are smooth and seasonal: the tournament runs every non-ML candidate
    # (the recursive ML models add minutes per series on these long aggregates)
    candidates = [m for m in ALL_MODELS if m not in ML_MAP and m not in INTERMITTENT_MAP]

    def _fit(branch):
        sel = ModelSelector()
        sel.registry.save = lambda: None
        return sel.select_and_fit(df, None, branch, horizon=horizon, candidate_models=candidates)

    region = _fit(None)
    if region.get('status') != 'success':
        return {'error': region.get('error')}
    branches = sorted(df[branch_col].dropna().astype(str).unique().tolist())
    branch_res = {b: _fit(b) for b in branches}
    branch_res = {b: r for b, r in branch_res.items() if r.get('status') == 'success'}

    work = df[[branch_col, sku_col, demand_col, date_col]].copy()
    if 'EXT MAT GROUP' in df.columns:
        work = work[df['EXT MAT GROUP'] == 'RA-ODU']
    work[date_col] = pd.to_datetime(work[date_col], errors='coerce')
    last = work[date_col].max()
    yr = work[work[date_col] > last - pd.Timedelta(weeks=52)]
    shares = (yr.groupby(branch_col)[demand_col].sum() / yr[demand_col].sum()).to_dict()
    q = work[work[date_col] > last - pd.Timedelta(weeks=13)]
    sku_shares = {b: (g.groupby(sku_col)[demand_col].sum() / g[demand_col].sum()).sort_values(ascending=False)
                  for b, g in q.groupby(branch_col)}

    region_fc = np.asarray(region['forecast'], dtype=float)
    bu = np.sum([np.asarray(r['forecast'], dtype=float) for r in branch_res.values()], axis=0)
    td = {b: region_fc * shares.get(b, 0.0) for b in branch_res}
    return {
        'region': region, 'branch_res': branch_res, 'branches': list(branch_res),
        'region_fc': region_fc, 'bottom_up': bu, 'top_down': td, 'shares': shares,
        'sku_shares': sku_shares, 'horizon': horizon,
    }


def render_hierarchy_page(df: pd.DataFrame, theme: str = "dark"):
    """Region and branch forecasts from the champion engine and how bottom-up and top-down compare."""
    is_dark = (theme == "dark")
    template = 'plotly_dark' if is_dark else 'plotly_white'

    st.markdown("""
    <div class="section-title-wrap">
        <div>
            <h2 class="section-title">🌐 Hierarchical Forecasting & Reconciliation</h2>
            <p class="section-subtitle">Region and branch totals forecast directly by the champion engine (statistical &amp; seasonal candidates) &bull; bottom-up vs top-down comparison &bull; SKU allocation</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    data = compute_cached_hierarchy_reconciliation(df, horizon=12)
    if not data or 'error' in data:
        st.error(f"Hierarchy unavailable: {data.get('error', 'branch / demand / date columns not found') if data else 'branch / demand / date columns not found'}")
        return

    region, branch_res, branches = data['region'], data['branch_res'], data['branches']
    region_fc, bu = data['region_fc'], data['bottom_up']
    dates = pd.to_datetime(region['forecast_dates'])
    gap_pct = (bu.sum() - region_fc.sum()) / region_fc.sum() * 100 if region_fc.sum() else float('nan')

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-cyan">Region (direct)</span><span>🌍</span></div>
            <div class="kpi-label">South Region 12-week forecast</div>
            <div class="kpi-value">{region_fc.sum():,.0f} units</div>
            <div style="font-size: 12px; color: var(--text-secondary);">{region['champion'].get('model_name')} &bull; backtest WAPE {region['champion'].get('wape', float('nan')):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-green">Bottom-up</span><span>🏢</span></div>
            <div class="kpi-label">Sum of {len(branches)} branch forecasts</div>
            <div class="kpi-value" style="color: #10B981 !important;">{bu.sum():,.0f} units</div>
            <div style="font-size: 12px; color: var(--text-secondary);">Each branch forecast by its own champion</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge {'kpi-badge-green' if abs(gap_pct) <= 5 else 'kpi-badge-amber'}">Coherence gap</span><span>⚖️</span></div>
            <div class="kpi-label">Bottom-up vs direct region</div>
            <div class="kpi-value">{gap_pct:+.1f}%</div>
            <div style="font-size: 12px; color: var(--text-secondary);">Unreconciled forecasts disagree by this much</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        b_wapes = [r['champion'].get('wape', np.nan) for r in branch_res.values()]
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-card-top"><span class="kpi-badge kpi-badge-amber">Branch accuracy</span><span>📏</span></div>
            <div class="kpi-label">Median branch backtest WAPE</div>
            <div class="kpi-value">{np.nanmedian(b_wapes):.1f}%</div>
            <div style="font-size: 12px; color: var(--text-secondary);">Range {np.nanmin(b_wapes):.1f}% &ndash; {np.nanmax(b_wapes):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    tab_bu, tab_td, tab_sku = st.tabs([
        "🔼 Branch forecasts & bottom-up total",
        "🔽 Top-down split of the region forecast",
        "📦 SKU allocation within a branch"
    ])
    colors = ['#00E5FF', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6']

    with tab_bu:
        fig_bu = go.Figure()
        for i, b in enumerate(branches):
            fig_bu.add_trace(go.Scatter(x=dates, y=branch_res[b]['forecast'], mode='lines+markers',
                                        name=f"{b} ({branch_res[b]['champion'].get('model_name')})",
                                        line=dict(color=colors[i % len(colors)], width=2)))
        fig_bu.add_trace(go.Scatter(x=dates, y=bu, mode='lines', name='Bottom-up total',
                                    line=dict(color='#FFFFFF' if is_dark else '#0F172A', width=3.5, dash='dash')))
        fig_bu.add_trace(go.Scatter(x=dates, y=region_fc, mode='lines', name='Direct region forecast',
                                    line=dict(color='#F43F5E', width=3)))
        fig_bu.update_layout(title="Branch forecasts, their sum and the direct region forecast", yaxis_title="Units / week",
                             height=400, template=template)
        st.plotly_chart(fig_bu, width="stretch")
        st.dataframe(pd.DataFrame([{
            'Branch': b,
            'Champion': r['champion'].get('model_name'),
            'Backtest WAPE %': round(r['champion'].get('wape', np.nan), 1),
            '12-week forecast': round(float(np.sum(r['forecast']))),
            'Top-down (region x share)': round(float(np.sum(data['top_down'][b]))),
            'Last-52-week share %': round(data['shares'].get(b, 0.0) * 100, 1),
        } for b, r in branch_res.items()]), width="stretch", hide_index=True)

    with tab_td:
        st.caption("Top-down keeps the region total fixed and splits it by each branch's share of the last 52 weeks. "
                   "It is coherent by construction but ignores branch-specific seasonality (e.g. Bangalore peaks in March).")
        fig_td = go.Figure()
        for i, b in enumerate(branches):
            fig_td.add_trace(go.Bar(x=dates, y=data['top_down'][b], name=b, marker_color=colors[i % len(colors)]))
        fig_td.update_layout(barmode='stack', title="Direct region forecast split by branch share", height=380, template=template)
        st.plotly_chart(fig_td, width="stretch")

    with tab_sku:
        sel_b = st.selectbox("Branch:", branches, key="hier_branch")
        sh = data['sku_shares'].get(sel_b, pd.Series(dtype=float)).head(10)
        b_total = float(np.sum(branch_res[sel_b]['forecast']))
        st.caption("Allocation of the branch's 12-week forecast by each SKU's share of the last 13 weeks "
                   "(proportional disaggregation, not a separate SKU forecast).")
        st.dataframe(pd.DataFrame({'SKU': sh.index, 'Share of last 13 weeks %': (sh.values * 100).round(1),
                                   'Allocated 12-week units': (sh.values * b_total).round(0)}),
                     width="stretch", hide_index=True)
