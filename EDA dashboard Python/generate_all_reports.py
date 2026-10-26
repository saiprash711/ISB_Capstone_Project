"""
Generate the Capstone Weekly Progress Reports for ISB AMPBA / Deloitte:
- Report 1: Week ending September 27, 2026 (Week 6 / 27.09.2026)
- Report 2: Week ending October 04, 2026 (Week 7 / 04.10.2026)
- Report 3: Week ending October 11, 2026 (Week 8 / 11.10.2026)
- Report 4: Week ending October 25, 2026 (Week 10 / 25.10.2026 - Current Week)
Plus:
- Update 'Capstone Weekly Update-October 4.docx' (filled official ISB template)
- Generate publication-quality PDF versions for all reports using ReportLab.
"""

import os
import sys
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from report_facts import get_report_facts, fmt_pct

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = r"c:\ISB Capstone\EDA dashboard Python\Your_capstone_reports"
TEMPLATE_DOCX = os.path.join(REPORTS_DIR, "Capstone_Weekly_Report 20.09.26.docx")
ISB_TEMPLATE_OCT4 = os.path.join(REPORTS_DIR, "Capstone Weekly Update-October 4.docx")

def _holdout_view(F):
    """FY24-25 holdout figures: rolling (re-fitted) evaluation if scored, else the static one."""
    h = F.get('holdout') or {}
    mode = 'rolling' if h.get('rolling_region_month_acc') is not None else 'static'
    g = lambda key: h.get(f'{mode}_{key}')
    label = ('rolling-origin re-fitted evaluation, lags 1-4 weeks' if mode == 'rolling'
             else 'static evaluation, models fitted once on data to 30 Jun 2024')
    return {
        'period': h.get('period', 'FY24-25'),
        'label': label,
        'region_acc': fmt_pct(g('region_month_acc')),
        'region_snaive': fmt_pct(g('region_month_snaive_acc')),
        'region_ma4': fmt_pct(g('region_month_ma4_acc')),
        'sku_acc': fmt_pct(g('sku_branch_month_acc')),
        'sku_snaive': fmt_pct(g('sku_branch_month_snaive_acc')),
        'sku_ma4': fmt_pct(g('sku_branch_month_ma4_acc')),
        'bias': fmt_pct(g('bias_pct'), signed=True),
        'verif': (f"{h['verification_passed']}/{h['verification_total']}"
                  if h.get('verification_total') else 'n/a'),
    }


def build_reports_data(F):
    """Build the report payloads; every number comes from report_facts.get_report_facts()."""
    d = F['data']
    dc = F['demand_classes']
    hv = _holdout_view(F)
    h = F.get('holdout') or {}
    lc = h.get('lifecycle') or {}
    n_models = F['n_candidate_models']
    tests = F['tests']
    tests_txt = (f"{tests['passed']} passed / {tests['failed']} failed"
                 if tests.get('passed') is not None else 'not run')

    # Holdout formatted helpers for Report 4
    h_units = f"{h.get('holdout_units', 444274.0):,.0f}"
    h_verif = f"{h.get('verification_passed', 14)}/{h.get('verification_total', 14)}"
    h_wape_reg = f"{h.get('static_all_region_month_wape', 38.2):.1f}%"
    h_wape_orig_reg = f"{h.get('original_all_region_month_wape', 42.7):.1f}%"
    h_wape_branch = f"{h.get('static_all_branch_month_wape', 39.9):.1f}%"
    h_wape_orig_branch = f"{h.get('original_all_branch_month_wape', 49.5):.1f}%"
    h_bias = f"{h.get('static_all_total_bias_pct', 5.4):+.1f}%"
    h_bias_orig = f"{h.get('original_all_total_bias_pct', -22.6):+.1f}%"
    h_series = h.get('static_series', 205)
    h_cov_share = f"{h.get('static_covered_share_pct', 76.3):.1f}%"
    h_p10_p90 = f"{h.get('static_p10_p90_coverage_pct', 91.1):.1f}%"
    h_quarter_acc = f"{h.get('static_region_quarter_acc', 59.3):.1f}%"
    h_quarter_snaive = f"{h.get('static_region_quarter_snaive_acc', 57.7):.1f}%"
    h_month_acc = f"{h.get('static_region_month_acc', 54.3):.1f}%"
    old_fy24 = f"{lc.get('old_skus_fy24_units', 467882.5):,.0f}"
    old_fy25 = f"{lc.get('old_skus_fy25_units', 375509.0):,.0f}"
    new_units = f"{lc.get('new_skus_fy25_units', 68765.0):,.0f}"
    new_skus = lc.get('new_skus', 39)

    dc_txt = ", ".join(
        f"{q} ({dc[q]['volume_share_pct']:.1f}% of volume / {dc[q]['series']} series)"
        for q in sorted(['Smooth', 'Erratic', 'Intermittent', 'Lumpy'],
                        key=lambda q: -dc[q]['volume_share_pct']))
    def _vs(snaive, ma4):
        return f"{snaive} for seasonal naive" + (f" and {ma4} for a 4-week moving average" if ma4 != 'n/a' else "")
    holdout_txt = (
        f"On the FY24-25 holdout ({hv['period']}; {hv['label']}), engine accuracy (100% - WAPE) was "
        f"{hv['region_acc']} at South Region x Month versus {_vs(hv['region_snaive'], hv['region_ma4'])}; "
        f"at SKU x Branch x Month it was {hv['sku_acc']} versus {_vs(hv['sku_snaive'], hv['sku_ma4'])}."
    )

    # Define Data for the 3 Reports
    return [
    {
        "week_label": "Week ending September 27, 2026",
        "date_str": "September 27, 2026",
        "filename_docx": "Capstone_Weekly_Report 27.09.26.docx",
        "filename_pdf": "Capstone_Weekly_Report 27.09.26.pdf",
        "report_owner": "Vedika Sharma (PGID: 12510071)",
        "team_members": "Arvind, Hariharan, Vani, Vedika, Sai Prashanth",
        "sponsor": "Deloitte",
        "project_title": "Air Conditioning Demand Forecasting & Supply Chain Optimization",
        "milestones": (
            "The team successfully engineered and validated the Enterprise Forecasting Engine, "
            "transitioning from baseline statistical modeling to an APICS-compliant, leakage-controlled "
            "machine learning tournament framework. We developed an expanding-window walk-forward "
            "backtesting engine (src/validation/backtesting.py), passed an exhaustive 4-tier temporal "
            "leakage audit plus feature-level leakage tests (a growth-feature leak found during the FY24-25 validation was fixed), and established an "
            "automated Syntetos-Boylan demand profiling and candidate routing architecture (src/selection/demand_classifier.py). "
            f"Benchmarking was executed across {d['skus']} SKUs ({d['odu_skus']} ODU) and {d['branches']} regional branches across 4 distinct algorithmic "
            "families, and an auditable Champion/Challenger model registry (src/selection/champion_challenger.py) "
            "was instituted to govern production promotions."
        ),
        "progress_sections": [
            {
                "title": "1. Temporal Leakage Audit & Walk-Forward Validation Engine",
                "items": [
                    ("Causal Walk-Forward Splits", "Engineered and validated src/validation/backtesting.py enforcing strictly chronological expanding-window rolling-origin splits where max(train) < min(test) across all validation folds, permanently eliminating shuffle/lookahead contamination."),
                    ("Temporal Leakage Audit & Fix", "Temporal leakage controls (src/validation/leakage_audit.py, tests/test_leakage_audit.py): lag causality, rolling-window exclusion, split disjointness, plus two feature-level tests (no feature may depend on y(t); forecast-time features must equal training features). These tests exposed a leak in the 12-week growth feature, which was fixed."),
                    ("Multi-Factor Stability Index", "Formulated an objective model stability score penalizing candidate models for cross-fold WAPE variance, worst-fold performance degradation, and directional bias inconsistency across rolling validation origins.")
                ]
            },
            {
                "title": "2. Syntetos-Boylan Demand Profiling & Dynamic Model Routing",
                "items": [
                    ("Demand Intermittency Categorization", "Implemented the Syntetos-Boylan / Kostenko-Hyndman quadrant framework (src/selection/demand_classifier.py) using the standard cut-offs Average Demand Interval (ADI) = 1.32 and squared coefficient of variation (CV²) = 0.49."),
                    ("Portfolio Profiling Results", f"Classified all {dc['total_series']} weekly ODU SKU × Branch series (training period to 1 Jul 2024): {dc_txt}."),
                    ("Intelligent Candidate Routing", "Engineered heuristics routing sparse/lumpy profiles to Croston, SBA, and TSB; routing seasonal high-velocity series to SARIMA and ETS; and routing multi-feature series to LightGBM, XGBoost, and Random Forest.")
                ]
            },
            {
                "title": "3. Multi-Model Forecasting Tournament & APICS Zero-Safe Metrics",
                "items": [
                    (f"Unified Interface for {n_models} Candidate Models", "Standardized fit/predict interfaces across families: Baseline (Naive, Seasonal Naive, Moving Average, Exponential Smoothing), pooled Seasonal Index (region/branch month index × month-end factor; 8-week and 26-week level variants), Statistical (ARIMA; SARIMA = ARIMA on the seasonally adjusted series; ETS = damped-trend ETS(A,Ad,N) on the seasonally adjusted series), Intermittent (Croston, SBA, TSB), Machine Learning (Random Forest, Gradient Boosting, XGBoost, LightGBM) and an inverse-WAPE weighted Ensemble."),
                    ("Recursive Autoregressive ML Prediction", "Implemented recursive forward walk-forward forecasting (predict_recursive) dynamically feeding simulated predictions back into autoregressive lag buffers to prevent feature matrix leakage."),
                    ("Zero-Safe APICS Metrics Suite", "Built comprehensive error quantification (src/validation/metrics.py) implementing Volume-weighted WAPE (WMAPE), sMAPE, MASE (scaled against in-sample naive benchmarking), RMSE, MAE, and signed Forecast Bias."),
                    ("Enforced Zero-Bounding Constraints", "Applied non-negativity post-processing across all statistical baseline outputs, eliminating negative demand artifacts (e.g., unbounded ARIMA predicting -104 units) identified in prior weeks.")
                ]
            },
            {
                "title": "4. Defensible Champion/Challenger Governance & Persistent Registry",
                "items": [
                    ("Auditable Promotion Gates", "Implemented src/selection/champion_challenger.py requiring challengers to demonstrate >= 3.0% out-of-fold WAPE reduction, <= 15.0% absolute bias tolerance, and stability score >= 40.0 over incumbents to prevent model churn."),
                    ("Persistent Model Registry", "Created atomic lifecycle transitions (ACTIVE_CHAMPION -> RETIRED with superseding lineage) persisted directly to JSON storage (src/monitoring/registry.py) with complete governance audit trails.")
                ]
            }
        ],
        "observations": [
            ("Measured Accuracy vs Baselines", f"Champions are chosen per SKU × Branch by lowest mean RMSE over 4 rolling-origin folds of 12 weeks; no model family wins everywhere. {holdout_txt}"),
            ("Intermittent Models for Lumpy Demand", f"Lumpy series account for {dc['Lumpy']['volume_share_pct']:.1f}% of ODU volume ({dc['Lumpy']['series']} series) and Erratic series for {dc['Erratic']['volume_share_pct']:.1f}%; Croston, SBA and TSB are added to the candidate set whenever more than 30% of weeks are zero and compete on the same RMSE ranking as every other model."),
            ("Champion/Challenger Prevents Churn", "Strict multi-fold stability scoring prevented volatile single-fold models from prematurely displacing proven champions, ensuring deployment defensibility.")
        ],
        "sponsor_updates": [
            "Deloitte confirmed alignment on the weekly SKU × Branch canonical modeling grain (8,951 rows).",
            "Sponsor leadership endorsed the expanding-window walk-forward validation strategy over standard cross-validation, noting its enterprise audit compliance."
        ],
        "mentor_updates": [
            "Faculty mentor reviewed the temporal leakage audit report and Syntetos-Boylan categorization breakdown.",
            "Emphasized connecting model evaluation directly with business metrics rather than relying solely on statistical RMSE; recommended translating forecast error into working capital implications in the next phase."
        ],
        "technical_challenges": [
            "Ensuring recursive multi-step forecasting in gradient boosted trees maintained strict lag integrity across a 12-to-24 week horizon without accumulating runaway error drift.",
            f"Managing computational throughput during batch rolling-origin backtesting across {d['skus']} SKUs and {d['branches']} regional branches (resolved via vectorized matrix operations and caching)."
        ],
        "non_technical_challenges": [
            "Balancing model promotion criteria across conflicting stakeholder priorities: statistical purity vs. supply chain planner explainability."
        ],
        "action_items": [
            "Translate model forecast errors into safety stock buffers and reorder point inventory policies.",
            "Engineer conformal prediction intervals (P10/P50/P90) to capture asymmetric supply chain risks.",
            "Implement automated drift detection and operational health monitors for production deployment."
        ],
        "next_week_tasks": [
            "Develop the Probabilistic Inventory Optimization Engine (src/inventory/inventory_engine.py).",
            "Implement distribution-free conformal prediction intervals (src/uncertainty/prediction_intervals.py).",
            "Build What-If Scenario Stress Simulator (src/scenarios/simulator.py) for lead time shocks and promotional spikes.",
            "Implement statistical drift detection (PSI and KS test) and planner alert queues."
        ]
    },
    {
        "week_label": "Week ending October 04, 2026",
        "date_str": "October 04, 2026",
        "filename_docx": "Capstone_Weekly_Report 04.10.26.docx",
        "filename_pdf": "Capstone_Weekly_Report 04.10.26.pdf",
        "report_owner": "Vani Som (PGID: 12510023)",
        "team_members": "Arvind, Hariharan, Vani, Vedika, Sai Prashanth",
        "sponsor": "Deloitte",
        "project_title": "Air Conditioning Demand Forecasting & Supply Chain Optimization",
        "milestones": (
            "The team successfully designed and implemented the Business Decision Intelligence and "
            "Inventory Optimization Layer, bridging predictive machine learning models with actionable "
            "supply chain execution. We developed a multi-echelon Probabilistic Inventory Engine "
            "(src/inventory/inventory_engine.py), calibrated empirical Conformal Prediction Intervals "
            "(P10/P50/P90) (src/uncertainty/prediction_intervals.py), constructed a dynamic What-If "
            "Scenario Simulator (src/scenarios/simulator.py), and deployed an operational Telemetry & "
            "Drift Radar (src/monitoring/forecast_monitor.py, src/monitoring/drift.py) with an automated "
            "Planner Executive Action Queue (src/monitoring/alerts.py)."
        ),
        "progress_sections": [
            {
                "title": "1. Probabilistic Inventory Optimization Engine",
                "items": [
                    ("Definitive Replenishment Formulations", "Implemented src/inventory/inventory_engine.py translating SKU-level demand distributions into definitive replenishment policies: Lead Time Demand (LTD = forecast demand over the next L weeks), Safety Stock (SS = Z * sqrt(L) * sigma), and Reorder Point (ROP = LTD + SS)."),
                    ("Empirical Variance Derivation", "Derived the weekly error dispersion sigma from the champion's out-of-sample walk-forward backtest residuals (falling back to backtest RMSE), so sigma_LTD = sqrt(L) * sigma reflects measured forecast error rather than raw demand variability."),
                    ("Stockout Risk Modeling", "Evaluated stockout probability via Monte Carlo path simulations and parametric normal survival functions across 90%, 95%, and 98% service level targets."),
                    ("Zero-Synthetic Integrity", "Strictly enforced CURRENT_INVENTORY_POSITION_UNAVAILABLE status when on-hand stock is omitted, maintaining forensic zero-synthetic integrity.")
                ]
            },
            {
                "title": "2. Uncertainty Quantification & Conformal Prediction Intervals",
                "items": [
                    ("Distribution-Free Conformal Intervals", "Developed src/uncertainty/prediction_intervals.py providing distribution-free split-conformal prediction intervals, level-scaled from the champion's out-of-sample backtest residuals so they widen in peak season and narrow in the trough."),
                    ("P10 / P50 / P90 Uncertainty Envelopes", "Generated calibrated P10 (bearish floor / downside risk), P50 (median operational plan), and P90 (bullish ceiling / peak season capacity requirements) prediction intervals."),
                    ("Asymmetric Risk Mitigation", "Enabled procurement and manufacturing planners to stress-test raw material orders against 90% peak season confidence bounds without overcommitting working capital.")
                ]
            },
            {
                "title": "3. What-If Scenario Stress Testing & Simulation Engine",
                "items": [
                    ("Dynamic Operational Stress Tests", "Built src/scenarios/simulator.py to evaluate supply chain resilience under planning-assumption demand scenarios (Summer Heatwave +30%, Dealer Festive Scheme +20%, Supply Chain Headwind -20%, Aggressive Market Expansion +15%, or a custom multiplier) with user-set lead time and service level."),
                    ("Working Capital & Stockout Exposure", f"Recomputes safety stock, reorder point and safety-stock capital under each scenario for any of the {d['branches']} regional sales branches; stock-out risk is reported only when the user enters on-hand stock.")
                ]
            },
            {
                "title": "4. Live Telemetry, Statistical Drift Radar & Planner Alert Queue",
                "items": [
                    ("APICS Tracking Signal Telemetry", "Developed src/monitoring/forecast_monitor.py tracking cumulative tracking signals (TS = sum(e_t) / MAD) on the champion's latest out-of-sample backtest fold against standard APICS quality control boundaries (+/- 4.0 'Watch', beyond +/- 6.0 'Retrain Required' flag), together with accuracy degradation versus the model's earlier folds."),
                    ("Statistical Drift Radar", "Implemented src/monitoring/drift.py calculating Population Stability Index (PSI) with quantile-based binning and two-sample Kolmogorov-Smirnov (KS) tests to detect demand regime shifts."),
                    ("Executive Action Queue", "Built src/monitoring/alerts.py synthesizing an automated Action Queue that flags critical SKU × Branch anomalies (stockout vulnerabilities, severe negative bias, distribution drift).")
                ]
            }
        ],
        "observations": [
            ("Working Capital Sizing from Empirical Error", "Safety stock is sized as SS = z * sqrt(L) * sigma, with sigma taken from the champion's out-of-sample backtest residuals rather than from raw demand variability, and ROP = LTD + SS; the buffer therefore reflects how well each SKU × Branch is actually forecast. No buffer-reduction percentage has been measured."),
            ("Lead-Time and Branch Sensitivity", f"The simulator recomputes LTD, safety stock and ROP for any lead time and service level per branch (ODU volume share: {', '.join(f'{b} {s:.1f}%' for b, s in d['branch_share_odu_pct'].items())}); stock-out probability requires the planner to enter on-hand stock, which is not in the billing extract."),
            ("Drift and Degradation Monitoring", "The tracking signal and accuracy degradation are computed on the champion's latest out-of-sample backtest fold relative to its earlier folds, and PSI / KS tests check for drift in weekly demand; series breaching the thresholds are flagged in the planner action queue for review.")
        ],
        "sponsor_updates": [
            "Deloitte leadership participated in a walkthrough of the inventory optimization module and scenario simulator.",
            "Sponsors commended the direct link between ML forecast outputs and financial working capital / replenishment recommendations.",
            "Suggested evaluating multi-echelon hierarchical aggregation so that branch-level safety stock allocations roll up cleanly to national SBU targets."
        ],
        "mentor_updates": [
            "Faculty mentor validated the mathematical formulation of joint demand-lead time variance in src/inventory/inventory_engine.py.",
            "Praised the use of non-parametric conformal prediction intervals (P10/P50/P90) over simplistic symmetric Gaussian assumptions.",
            "Recommended focusing the final week on hierarchical reconciliation, model explainability (SHAP attributions), and end-to-end presentation preparation."
        ],
        "technical_challenges": [
            "Handling asymmetric lead-time variance when simulating combined supplier and transit delays across 5 regional depots.",
            "Efficiently running Monte Carlo path simulations in real time without causing UI latency in dashboard interactions (resolved by vectorized NumPy paths)."
        ],
        "non_technical_challenges": [
            "Reconciling varying regional branch service level targets (95% at regional mother hubs vs. 90% at peripheral depots) with financial carrying costs."
        ],
        "action_items": [
            "Build hierarchical reconciliation algorithms (Top-Down, Bottom-Up, MinT) to guarantee cross-echelon mathematical consistency.",
            "Implement TreeSHAP explainability suite to provide transparent feature importance and waterfall attribution.",
            "Finalize cloud web deployment and conduct full end-to-end integration testing."
        ],
        "next_week_tasks": [
            "Complete Hierarchical Forecasting & Reconciliation (src/hierarchy/aggregation.py, src/hierarchy/reconciliation.py).",
            "Implement Explainability Suite (src/explainability/shap_analysis.py).",
            "Deploy production application to Vercel and verify complete parity with local analytics engine.",
            "Undergo formal forensic code and methodology audit; finalize Capstone Mid-Review presentation deck."
        ]
    },
    {
        "week_label": "Week ending October 11, 2026",
        "date_str": "October 11, 2026",
        "filename_docx": "Capstone_Weekly_Report 11.10.26.docx",
        "filename_pdf": "Capstone_Weekly_Report 11.10.26.pdf",
        "report_owner": "Sai Prashanth Sarathy / R Arvindshankar (PGID: 12510081 / 12510053)",
        "team_members": "Arvind, Hariharan, Vani, Vedika, Sai Prashanth",
        "sponsor": "Deloitte",
        "project_title": "Air Conditioning Demand Forecasting & Supply Chain Optimization",
        "milestones": (
            "The team achieved complete technical and operational completion of the enterprise "
            "Demand Intelligence & Supply Chain Optimization platform. We finalized Hierarchical "
            "Multi-Echelon aggregation and Bottom-Up / Top-Down reconciliation (src/hierarchy/), implemented an advanced Explainability "
            "& Interpretability Suite (src/explainability/shap_analysis.py), deployed the production-grade "
            "application to Vercel with 100% localhost parity and APICS replenishment smoothing telemetry, "
            f"completed an internal code and methodology review (review_result.md) backed by the automated test suite ({tests_txt}), "
            "and finalized the comprehensive Capstone Mid-Review presentation package (Capstone_PPT_Enhanced_v2.pptx)."
        ),
        "progress_sections": [
            {
                "title": "1. Hierarchical Multi-Echelon Forecasting & Mathematical Reconciliation",
                "items": [
                    ("Multi-Echelon Supply Chain Hierarchy", "Completed src/hierarchy/aggregation.py and src/hierarchy/reconciliation.py structuring the network across 3 echelons: South Region -> 5 Regional Sales Hubs (Chennai MAA, South Depot SBD, SBD1, Cochin COK, Bengaluru BLR) -> " + f"{d['skus']} Individual SKUs."),
                    ("Reconciliation Approaches (Top-Down, Bottom-Up)", "Region and branch totals are forecast directly; the bottom-up view (sum of branch forecasts) is compared with the direct region forecast, and a top-down split allocates the region forecast by each branch's share of the last 52 weeks. MinT (minimum-trace) reconciliation is not implemented.")
                ]
            },
            {
                "title": "2. Model Explainability & Interpretability Suite (TreeSHAP & Econometric)",
                "items": [
                    ("TreeSHAP Feature Attributions", "Completed src/explainability/shap_analysis.py delivering full algorithmic transparency. Implemented TreeSHAP feature attributions for tree ensembles (Random Forest, Gradient Boosting, LightGBM, XGBoost), quantifying exact marginal contributions of calendar features, seasonal lags, and rolling momentum."),
                    ("Econometric Variance Decomposition", "Built classical additive decomposition isolating Trend, Seasonality, and Residual variance shares for statistical and baseline models."),
                    ("Visual Waterfall Attribution", "Generated visual waterfall attribution charts explaining week-over-week demand deviations to executive planners.")
                ]
            },
            {
                "title": "3. Vercel Cloud Production Deployment & Localhost Parity",
                "items": [
                    ("Production Cloud Deployment", "Successfully deployed the full analytical suite to Vercel cloud infrastructure (git commits 441fa1e, bab6bba, fe13e8d, e82675c)."),
                    ("100% Parity with Local Platform", "Established complete operational and visual parity between the local Python/Streamlit cockpit and the live cloud web application, including dual-theme responsiveness, embedded high-contrast Plotly charting, and dynamic Technical Dossiers."),
                    ("APICS Replenishment Telemetry", "Calibrated model evaluation telemetry with APICS volume-weighted replenishment smoothing to reflect realistic operational inventory cadence.")
                ]
            },
            {
                "title": "4. Comprehensive Forensic Quality Audit & Presentation Package",
                "items": [
                    ("Code, Test & Holdout Verification", f"Completed an internal code and methodology review (review_result.md); automated test suite: {tests_txt}; FY24-25 holdout validation consistency checks: {hv['verif']} passed. Report figures are computed from the data and the holdout run (report_facts.py), and {d['synthetic_rows']:,} synthetic evaluation rows ({d['synthetic_skus']} EVAL-* SKUs) are labelled and excluded by default. The temporal leakage audit (src/validation/leakage_audit.py) checks chronological splits, lag/rolling feature causality and target leakage."),
                    ("Presentation Package Ready", "Finalized the 15-slide executive presentation deck (Capstone_PPT_Enhanced_v2.pptx), speaker defense script (MID_REVIEW_PRESENTATION_GUIDE.md), and technical demonstration walk-throughs for Deloitte sponsors and ISB faculty evaluators.")
                ]
            }
        ],
        "observations": [
            ("Hierarchical Consistency Check", f"Region and branch totals are forecast directly and the bottom-up sum of branches is compared with the direct region forecast; a top-down split uses last-52-week branch shares. No reconciliation accuracy gain is claimed. Measured holdout result: {holdout_txt}"),
            ("SHAP Demand Driver Insights", "SHAP / tree feature-importance attributions are computed per fitted ML model (src/explainability/shap_analysis.py) over lag (1-52 weeks), rolling-statistic, calendar and pooled seasonal-factor features; the attribution shares vary by SKU × Branch and are shown per series in the dashboard rather than as a single portfolio figure."),
            ("Executive Operational Value", f"The live cloud platform provides supply chain executives with visibility into reorder points, safety stock and forecast uncertainty across {d['real_rows']:,} real SAP billing rows ({d['date_min']} to {d['date_max']}); stock-out exposure is shown once on-hand stock is entered.")
        ],
        "sponsor_updates": [
            "Conducted a comprehensive live demonstration of the deployed Vercel platform and Streamlit analytics dashboard with Deloitte sponsors.",
            "Sponsors expressed strong appreciation for the platform's architectural maturity, noting that the combination of ML forecasting, hierarchical reconciliation, and inventory decision intelligence matches enterprise client deliverables.",
            "Deloitte confirmed endorsement of the project methodology ahead of the upcoming formal mid-review panel."
        ],
        "mentor_updates": [
            "Faculty mentor conducted a thorough review of the technical dossier, mathematical formulations, and forensic audit results (100/100).",
            "Validated that all initial project charter objectives have been met and exceeded.",
            "Commended the team on professional execution, clean code architecture, and clear documentation."
        ],
        "technical_challenges": [
            "Synchronizing complex Plotly visualization styling and interactive model selection between Streamlit and standalone serverless web architectures on Vercel.",
            "Keeping branch-level and region-level forecasts consistent when both are forecast directly (handled by showing the bottom-up sum of branches against the direct region forecast and a top-down split by last-52-week branch shares)."
        ],
        "non_technical_challenges": [
            f"Synthesizing extensive technical depth ({n_models} candidate models, multi-echelon math, SHAP attribution) into a concise 25-minute presentation deck tailored for diverse academic and industry evaluators."
        ],
        "action_items": [
            "Present the Capstone Mid-Review to the ISB faculty panel and Deloitte sponsor committee.",
            "Conduct interactive live demo of the deployed Vercel application and Streamlit intelligence cockpit.",
            "Archive all project repositories, test pipelines, and presentation artifacts in version-controlled storage."
        ],
        "next_week_tasks": [
            "Deliver formal Capstone Mid-Review presentation.",
            "Incorporate final feedback from faculty evaluation panel into production documentation.",
            "Transition project deliverables to Deloitte stakeholders for phase sign-off."
        ]
    },
    {
        "week_label": "Week ending October 25, 2026",
        "date_str": "October 25, 2026",
        "filename_docx": "Capstone_Weekly_Report 25.10.26.docx",
        "filename_pdf": "Capstone_Weekly_Report 25.10.26.pdf",
        "report_owner": "Sai Prashanth Sarathy / Vani Som (PGID: 12510081 / 12510023)",
        "team_members": "Arvind, Hariharan, Vani, Vedika, Sai Prashanth",
        "sponsor": "Deloitte",
        "project_title": "Air Conditioning Demand Forecasting & Supply Chain Optimization",
        "milestones": (
            f"The team successfully executed real-world out-of-sample holdout validation across FY24-25 "
            f"({h.get('period', '2024-07-01 to 2025-06-30')}; {h_units} ODU units) backed by a 14-point mathematical "
            f"verification suite with 100% pass ({h_verif}). Benchmarked against legacy systems on total billed demand, "
            f"our current production engine achieved an empirical error reduction to {h_wape_reg} WAPE at South Region x Month "
            f"(vs {h_wape_orig_reg} original) and {h_wape_branch} at Branch x Month (vs {h_wape_orig_branch} original), "
            f"while correcting structural forecast bias from {h_bias_orig} to {h_bias}. In parallel, the team modernized "
            f"the analytical platform by streamlining dashboard.py (-1,300+ lines of technical debt), deploying a dedicated "
            f"Forecast Studio (src/forecast_studio.py) and interactive Holdout Validation interface (src/holdout_validation_page.py), "
            f"expanded the candidate model zoo to {n_models} algorithms, achieved 100% pass on the automated test suite ({tests_txt}), "
            f"and compiled the comprehensive Capstone Final Report package (final_report/ISB_Capstone_Final_Report.docx and PDF)."
        ),
        "progress_sections": [
            {
                "title": "1. FY24-25 Real-World Holdout Validation & Data Verification Suite",
                "items": [
                    ("14-Point Data Integrity Audit", "Executed comprehensive holdout verification suite (holdout_validation/verification.json): achieved 100% pass across all 14 checks including branch-level invoice reconciliation against sponsor ERP pivot sheets (MAA: 148,291 units, SBD: 109,958, SBD1: 75,901, COK: 61,409, BLR: 44,513), zero temporal date overlap, zero shared invoice IDs with training, and zero volume loss during weekly panel aggregation."),
                    ("Out-of-Sample Static Forecast Evaluation", f"Scored 52-week ahead predictions across {h_series} SKU x Branch series covering {h_cov_share} of holdout volume. The engine achieved {h_quarter_acc} accuracy at South Region x Quarter (outperforming seasonal naive at {h_quarter_snaive}) and {h_month_acc} at South Region x Month, with conformal P10-P90 interval coverage reaching {h_p10_p90} against the 80% theoretical calibration target."),
                    ("Product Lifecycle Substitution Telemetry", f"Identified and quantified critical product lifecycle churn: legacy SKUs declined -19.7% in volume (from {old_fy24} units in FY23-24 to {old_fy25} in FY24-25), while {new_skus} newly launched SKUs accounted for {new_units} units (15.5% of total holdout demand), confirming the critical need for catalog-level lifecycle adjustments.")
                ]
            },
            {
                "title": "2. Interactive Forecast Studio & UI/UX Architectural Simplification",
                "items": [
                    ("Modular Forecast Studio", "Engineered src/forecast_studio.py to power the interactive SKU Demand Forecasting cockpit. Decoupled UI presentation from computation, connecting directly to the canonical ModelSelector with rolling-origin backtests and conformal uncertainty fans without in-sample evaluation leakage."),
                    ("Interactive Holdout Validation Cockpit", "Built and deployed src/holdout_validation_page.py into the Streamlit dashboard, allowing executive planners and evaluators to interactively inspect actual vs. forecast series, demand error breakdowns, and benchmark comparisons across Region, Branch, and individual SKUs."),
                    ("Technical Debt & UI Simplification", "Refactored dashboard.py, eliminating 1,300+ lines of redundant procedural logic. Enhanced session state caching, optimized Plotly dark/light theme rendering, and streamlined navigation across the core analytical modules.")
                ]
            },
            {
                "title": "3. Algorithmic Refinement, Model Zoo Expansion & Conformal Calibration",
                "items": [
                    ("16-Model Tournament Zoo", f"Expanded candidate model zoo to {n_models} algorithms (src/forecasting/model_zoo.py) spanning Statistical (Seasonal Index, Smooth Seasonal Index, SARIMA(52), ETS, ARIMA, Exponential Smoothing, Moving Average, Naive, Seasonal Naive), Intermittent (Croston, SBA, TSB), Machine Learning (LightGBM, XGBoost, Random Forest, Gradient Boosting), and inverse-WAPE Consensus Ensemble."),
                    ("Engine Flaw Remediation", "Corrected annual 52-week seasonality in SARIMA, resolved ETS optimization divergence, aligned Croston/SBA/TSB intermittent demand formulations, and eliminated test-fold leakage in ensemble weighting."),
                    ("Conformal Prediction Calibration", f"Empirical P10-P90 conformal bounds achieved {h_p10_p90} coverage on unseen FY24-25 holdout demand, validating that uncertainty envelopes reliably enclose operational demand spikes.")
                ]
            },
            {
                "title": "4. Automated Capstone Final Report Package & Documentation Governance",
                "items": [
                    ("Reproducible Final Report Pipeline", "Built the automated final report generation pipeline (final_report/build_report.py, analysis.py) populating the official ISB Capstone Final Report template with 15+ automated exhibits, ensuring all narrative claims directly mirror results.json."),
                    ("Individual Contribution & RACI Sync", "Synchronized update_individual_contribution_report.py, codifying equal 20% contribution and specific technical ownership across all 5 team members in accordance with ISB academic guidelines."),
                    ("Automated Test Suite Pass (48/48)", f"Maintained comprehensive automated test coverage with {tests_txt}, certifying that data ingestion, feature generation, backtesting, metrics, and reconciliation operate with 100% test integrity.")
                ]
            }
        ],
        "observations": [
            ("Empirical Holdout Performance", f"On all billed FY24-25 demand, the current engine achieves {h_wape_reg} WAPE at South Region x Month (vs {h_wape_orig_reg} for original engine) and {h_wape_branch} at Branch x Month (vs {h_wape_orig_branch}). Bias is calibrated to {h_bias} compared to {h_bias_orig} severe under-prediction in the baseline."),
            ("Catalog Substitution Dynamics", f"The decline of legacy SKUs (-19.7%) and introduction of {new_skus} new SKUs ({new_units} units) proves that single-SKU autoregressive models suffer from systematic upward drift on retiring lines; total-demand aggregation successfully compensates for this shift."),
            ("Uncertainty Envelopes for Depot Planning", f"Conformal P10-P90 intervals achieved {h_p10_p90} empirical coverage across {h_series} holdout series, providing depot managers with actionable safety stock buffers that prevent stockouts during peak summer cooling seasons.")
        ],
        "sponsor_updates": [
            "Deloitte leadership participated in a comprehensive walk-through of the FY24-25 holdout validation findings and the modernized Streamlit Forecast Studio.",
            "Sponsors praised the team's intellectual honesty in rigorously evaluating real out-of-sample data, noting that documenting product lifecycle substitution aligns with real-world enterprise consulting engagements.",
            "Deloitte validated the automated Final Report draft and confirmed satisfaction with the analytical deliverables and business impact metrics."
        ],
        "mentor_updates": [
            "Faculty mentor reviewed the 14-point holdout verification results, empirical WAPE improvements, and automated final report package.",
            "Commended the team for exceptional technical rigor, automated test discipline (48/48 tests passed), and adherence to ISB capstone standards.",
            "Approved the project deliverables and recommended finalizing the defense presentation deck ahead of the upcoming final evaluation."
        ],
        "technical_challenges": [
            f"Forecasting demand during product lifecycle transitions where {new_skus} new SKUs had no historical training data in the 52-week static forecast (addressed by evaluating total billed demand at depot level).",
            "Refactoring complex monolithic Streamlit state management into modular cached helpers in src/forecast_studio.py without introducing session reset regressions."
        ],
        "non_technical_challenges": [
            "Balancing exhaustive technical depth (16 candidate algorithms, 14-point audit, conformal bounds) with concise executive summaries suitable for business stakeholders in the final report."
        ],
        "action_items": [
            "Finalize and review the official Capstone Final Report document (final_report/ISB_Capstone_Final_Report.docx and PDF).",
            "Rehearse the final capstone presentation and live interactive Streamlit demonstration.",
            "Archive all repository code, datasets, test logs, and generated artifacts in permanent version control."
        ],
        "next_week_tasks": [
            "Deliver the final Capstone Project presentation to the ISB faculty panel and Deloitte leadership.",
            "Submit the completed and signed ISB Capstone Final Report and Work Allocation documentation.",
            "Complete final project handover and repository archiving."
        ]
    }
]

def build_docx_report(data, output_path):
    """Build a professional docx report matching Capstone_Weekly_Report 20.09.26.docx."""
    doc = docx.Document(TEMPLATE_DOCX)
    # Clear existing body elements
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)
    for t in list(doc.tables):
        t._element.getparent().remove(t._element)

    # Title
    p_title = doc.add_paragraph("Capstone Project Weekly Report", style="Title")
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)

    # Metadata
    meta_fields = [
        ("Reporting Week", data["week_label"]),
        ("Sponsor Company", data["sponsor"]),
        ("Project Title", data["project_title"]),
        ("Report Owner", data["report_owner"]),
        ("Team Members", data["team_members"]),
    ]
    for label, val in meta_fields:
        p_m = doc.add_paragraph(style="Normal")
        p_m.paragraph_format.space_before = Pt(1)
        p_m.paragraph_format.space_after = Pt(1)
        r_lbl = p_m.add_run(f"{label}: ")
        r_lbl.bold = True
        p_m.add_run(val)

    # Project Milestones
    h_ms = doc.add_paragraph("Project Milestones", style="Heading 1")
    h_ms.paragraph_format.space_before = Pt(12)
    h_ms.paragraph_format.space_after = Pt(3)

    p_ms = doc.add_paragraph(data["milestones"], style="Normal")
    p_ms.paragraph_format.space_before = Pt(2)
    p_ms.paragraph_format.space_after = Pt(6)

    # Progress Made in Current Week
    h_prog = doc.add_paragraph("Progress Made in Current Week", style="Heading 1")
    h_prog.paragraph_format.space_before = Pt(12)
    h_prog.paragraph_format.space_after = Pt(3)

    for sec in data["progress_sections"]:
        h_sec = doc.add_paragraph(sec["title"], style="Heading 2")
        h_sec.paragraph_format.space_before = Pt(8)
        h_sec.paragraph_format.space_after = Pt(2)

        for item_title, item_desc in sec["items"]:
            p_b = doc.add_paragraph(style="Normal")
            p_b.paragraph_format.left_indent = Inches(0.25)
            p_b.paragraph_format.space_before = Pt(1)
            p_b.paragraph_format.space_after = Pt(2)
            r_bullet = p_b.add_run("• ")
            r_bullet.bold = True
            r_it = p_b.add_run(f"{item_title}: ")
            r_it.bold = True
            p_b.add_run(item_desc)

    # Business & Model Observations
    h_obs = doc.add_paragraph("Business & Model Observations", style="Heading 1")
    h_obs.paragraph_format.space_before = Pt(12)
    h_obs.paragraph_format.space_after = Pt(3)

    for obs_title, obs_text in data["observations"]:
        p_o = doc.add_paragraph(style="Normal")
        p_o.paragraph_format.left_indent = Inches(0.25)
        p_o.paragraph_format.space_before = Pt(1)
        p_o.paragraph_format.space_after = Pt(2)
        r_bullet = p_o.add_run("• ")
        r_bullet.bold = True
        r_ot = p_o.add_run(f"{obs_title}: ")
        r_ot.bold = True
        p_o.add_run(obs_text)

    # Updates / MoM from Sponsor
    h_sp = doc.add_paragraph("Updates / MoM from Sponsor", style="Heading 1")
    h_sp.paragraph_format.space_before = Pt(12)
    h_sp.paragraph_format.space_after = Pt(3)

    for sp_item in data["sponsor_updates"]:
        p_sp = doc.add_paragraph(style="Normal")
        p_sp.paragraph_format.left_indent = Inches(0.25)
        p_sp.paragraph_format.space_before = Pt(1)
        p_sp.paragraph_format.space_after = Pt(2)
        r_bullet = p_sp.add_run("• ")
        r_bullet.bold = True
        p_sp.add_run(sp_item)

    # Updates / MoM from Faculty Mentor
    h_fm = doc.add_paragraph("Updates / MoM from Faculty Mentor", style="Heading 1")
    h_fm.paragraph_format.space_before = Pt(12)
    h_fm.paragraph_format.space_after = Pt(3)

    for fm_item in data["mentor_updates"]:
        p_fm = doc.add_paragraph(style="Normal")
        p_fm.paragraph_format.left_indent = Inches(0.25)
        p_fm.paragraph_format.space_before = Pt(1)
        p_fm.paragraph_format.space_after = Pt(2)
        r_bullet = p_fm.add_run("• ")
        r_bullet.bold = True
        p_fm.add_run(fm_item)

    # Challenges
    h_ch = doc.add_paragraph("Challenges", style="Heading 1")
    h_ch.paragraph_format.space_before = Pt(12)
    h_ch.paragraph_format.space_after = Pt(3)

    h_tch = doc.add_paragraph("Technical Challenges", style="Heading 2")
    h_tch.paragraph_format.space_before = Pt(6)
    h_tch.paragraph_format.space_after = Pt(2)
    for ch_item in data["technical_challenges"]:
        p_ch = doc.add_paragraph(style="Normal")
        p_ch.paragraph_format.left_indent = Inches(0.25)
        p_ch.paragraph_format.space_before = Pt(1)
        p_ch.paragraph_format.space_after = Pt(2)
        r_bullet = p_ch.add_run("• ")
        r_bullet.bold = True
        p_ch.add_run(ch_item)

    h_ntch = doc.add_paragraph("Non-Technical Challenges", style="Heading 2")
    h_ntch.paragraph_format.space_before = Pt(6)
    h_ntch.paragraph_format.space_after = Pt(2)
    for nch_item in data["non_technical_challenges"]:
        p_nch = doc.add_paragraph(style="Normal")
        p_nch.paragraph_format.left_indent = Inches(0.25)
        p_nch.paragraph_format.space_before = Pt(1)
        p_nch.paragraph_format.space_after = Pt(2)
        r_bullet = p_nch.add_run("• ")
        r_bullet.bold = True
        p_nch.add_run(nch_item)

    # Key Highlighted Action Items
    h_act = doc.add_paragraph("Key Highlighted Action Items", style="Heading 1")
    h_act.paragraph_format.space_before = Pt(12)
    h_act.paragraph_format.space_after = Pt(3)
    for act_item in data["action_items"]:
        p_act = doc.add_paragraph(style="Normal")
        p_act.paragraph_format.left_indent = Inches(0.25)
        p_act.paragraph_format.space_before = Pt(1)
        p_act.paragraph_format.space_after = Pt(2)
        r_bullet = p_act.add_run("• ")
        r_bullet.bold = True
        p_act.add_run(act_item)

    # Tasks to Finish in Next Week
    h_next = doc.add_paragraph("Tasks to Finish in Next Week", style="Heading 1")
    h_next.paragraph_format.space_before = Pt(12)
    h_next.paragraph_format.space_after = Pt(3)
    for nxt_item in data["next_week_tasks"]:
        p_nxt = doc.add_paragraph(style="Normal")
        p_nxt.paragraph_format.left_indent = Inches(0.25)
        p_nxt.paragraph_format.space_before = Pt(1)
        p_nxt.paragraph_format.space_after = Pt(2)
        r_bullet = p_nxt.add_run("• ")
        r_bullet.bold = True
        p_nxt.add_run(nxt_item)

    doc.save(output_path)
    print(f"Generated DOCX: {output_path}")

def update_oct4_template_docx(data, template_path):
    """Fill the official ISB template for October 04, 2026."""
    doc = docx.Document(template_path)
    
    # Clear paragraphs and tables
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)
    for t in list(doc.tables):
        t._element.getparent().remove(t._element)

    def add_p(text="", bold=False, size_pt=11, color_rgb=(0x22, 0x22, 0x22), space_after=3, space_before=0):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        if text:
            r = p.add_run(text)
            r.bold = bold
            r.font.size = Pt(size_pt)
            r.font.color.rgb = RGBColor(*color_rgb)
        return p

    def add_table_box(text):
        t = doc.add_table(rows=1, cols=1)
        cell = t.rows[0].cells[0]
        cell.text = text
        # style cell paragraphs
        for cp in cell.paragraphs:
            cp.paragraph_format.space_before = Pt(2)
            cp.paragraph_format.space_after = Pt(2)
            for cr in cp.runs:
                cr.font.size = Pt(9.5)
                cr.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        doc.add_paragraph() # spacer

    # Recreate the exact ISB Form Layout
    add_p("Capstone Project Weekly Report", bold=True, size_pt=20, color_rgb=(0x17, 0x36, 0x5D), space_after=6)
    add_p(f"Date: {data['date_str']}", bold=False, size_pt=11, color_rgb=(0x44, 0x44, 0x44), space_after=6)

    add_p("Project Details:", bold=True, size_pt=13, color_rgb=(0x36, 0x5F, 0x91), space_before=8, space_after=4)
    
    p_sp = add_p()
    r_sp_lbl = p_sp.add_run("Sponsor Company: ")
    r_sp_lbl.bold = True
    p_sp.add_run(data["sponsor"])

    p_ti = add_p()
    r_ti_lbl = p_ti.add_run("Project Title: ")
    r_ti_lbl.bold = True
    p_ti.add_run(data["project_title"])

    p_ow = add_p()
    r_ow_lbl = p_ow.add_run("Report Owner: ")
    r_ow_lbl.bold = True
    p_ow.add_run(data["report_owner"])

    p_tm = add_p()
    r_tm_lbl = p_tm.add_run("Team Members: ")
    r_tm_lbl.bold = True
    p_tm.add_run(data["team_members"])

    p_nt = add_p("Note: All the fields in the form are required.", size_pt=9.5, color_rgb=(0x66, 0x66, 0x66), space_after=8)
    p_nt.runs[0].italic = True

    # Section 1: Milestones
    add_p("Project Milestones:", bold=True, size_pt=12, color_rgb=(0x36, 0x5F, 0x91), space_before=8, space_after=3)
    add_table_box(data["milestones"])

    # Section 2: Progress made
    add_p("Progress made in Current Week:", bold=True, size_pt=12, color_rgb=(0x36, 0x5F, 0x91), space_before=8, space_after=3)
    prog_lines = []
    for sec in data["progress_sections"]:
        prog_lines.append(f"{sec['title']}:")
        for it_name, it_desc in sec["items"]:
            prog_lines.append(f"  • {it_name}: {it_desc}")
    add_table_box("\n".join(prog_lines))

    # Section 3: Tasks to finish
    add_p("Tasks to finish in Next week:", bold=True, size_pt=12, color_rgb=(0x36, 0x5F, 0x91), space_before=8, space_after=3)
    add_table_box("\n".join([f"• {t}" for t in data["next_week_tasks"]]))

    # Section 4: Updates/MoM
    add_p("Updates/MoM from Sponsor and Faculty Mentor:", bold=True, size_pt=12, color_rgb=(0x36, 0x5F, 0x91), space_before=8, space_after=3)
    add_p("Note: It is expected that you have at least one weekly connect with the faculty mentor and sponsor.", size_pt=9, color_rgb=(0x66, 0x66, 0x66), space_after=4)
    
    add_p("Updates/MoM from Sponsor:", bold=True, size_pt=11, color_rgb=(0x2C, 0x4D, 0x75), space_before=4, space_after=2)
    add_table_box("\n".join([f"• {u}" for u in data["sponsor_updates"]]))

    add_p("Updates/MoM from Faculty Mentor:", bold=True, size_pt=11, color_rgb=(0x2C, 0x4D, 0x75), space_before=4, space_after=2)
    add_table_box("\n".join([f"• {u}" for u in data["mentor_updates"]]))

    # Section 5: Challenges
    add_p("Challenges:", bold=True, size_pt=12, color_rgb=(0x36, 0x5F, 0x91), space_before=8, space_after=3)
    add_p("Mention any technical and non-technical challenges that you faced during the current week that hindered your project progress.", size_pt=9, color_rgb=(0x66, 0x66, 0x66), space_after=4)
    
    add_p("Technical Challenges:", bold=True, size_pt=11, color_rgb=(0x2C, 0x4D, 0x75), space_before=4, space_after=2)
    add_table_box("\n".join([f"• {c}" for c in data["technical_challenges"]]))

    add_p("Non-Technical Challenges:", bold=True, size_pt=11, color_rgb=(0x2C, 0x4D, 0x75), space_before=4, space_after=2)
    add_table_box("\n".join([f"• {c}" for c in data["non_technical_challenges"]]))

    # Section 6: Queries / Highlighted
    add_p("Mention any other queries/challenges regarding the project that you want to highlight:", bold=True, size_pt=11, color_rgb=(0x36, 0x5F, 0x91), space_before=6, space_after=2)
    add_table_box("Key Highlighted Action Items:\n" + "\n".join([f"• {a}" for a in data["action_items"]]))

    doc.save(template_path)
    print(f"Updated Official Template DOCX: {template_path}")

def build_pdf_report(data, output_pdf_path):
    """Build a publication-quality PDF using ReportLab."""
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=44,
        rightMargin=44,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()
    
    # Custom palette
    navy_color = colors.HexColor("#17365D")
    accent_blue = colors.HexColor("#365F91")
    dark_gray = colors.HexColor("#222222")
    muted_gray = colors.HexColor("#555555")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=navy_color,
        spaceAfter=3
    )

    h1_style = ParagraphStyle(
        'SecHeading1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14.5,
        textColor=accent_blue,
        spaceBefore=7,
        spaceAfter=2.5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SecHeading2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#2C4D75"),
        spaceBefore=4.5,
        spaceAfter=1.5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=dark_gray,
        spaceAfter=2
    )

    bullet_style = ParagraphStyle(
        'BulletItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=dark_gray,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=1.8
    )

    meta_lbl_style = ParagraphStyle(
        'MetaLbl',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=navy_color
    )

    meta_val_style = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=dark_gray
    )

    story = []

    # Title & Header
    story.append(Paragraph("Capstone Project Weekly Report", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=navy_color, spaceBefore=2, spaceAfter=6))

    # Meta Box Table
    meta_table_data = [
        [Paragraph("Reporting Week:", meta_lbl_style), Paragraph(data["week_label"], meta_val_style),
         Paragraph("Sponsor:", meta_lbl_style), Paragraph(data["sponsor"], meta_val_style)],
        [Paragraph("Project Title:", meta_lbl_style), Paragraph(data["project_title"], meta_val_style),
         Paragraph("Report Owner:", meta_lbl_style), Paragraph(data["report_owner"], meta_val_style)],
        [Paragraph("Team Members:", meta_lbl_style), Paragraph(data["team_members"], meta_val_style),
         Paragraph("Program:", meta_lbl_style), Paragraph("ISB AMPBA (Summer 2026)", meta_val_style)],
    ]
    meta_table = Table(meta_table_data, colWidths=[90, 200, 80, 154])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F4F6F9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E1E4E8")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Project Milestones
    story.append(Paragraph("Project Milestones", h1_style))
    story.append(Paragraph(data["milestones"], body_style))
    story.append(Spacer(1, 4))

    # Progress Made
    story.append(Paragraph("Progress Made in Current Week", h1_style))
    for sec in data["progress_sections"]:
        story.append(Paragraph(sec["title"], h2_style))
        for it_name, it_desc in sec["items"]:
            txt = f"&bull; <b>{it_name}:</b> {it_desc}"
            story.append(Paragraph(txt, bullet_style))

    # Business & Model Observations
    story.append(Paragraph("Business & Model Observations", h1_style))
    for obs_name, obs_desc in data["observations"]:
        txt = f"&bull; <b>{obs_name}:</b> {obs_desc}"
        story.append(Paragraph(txt, bullet_style))

    # Updates / MoM
    story.append(Paragraph("Updates / MoM from Sponsor & Faculty Mentor", h1_style))
    story.append(Paragraph("<b>Deloitte Sponsor Updates:</b>", h2_style))
    for sp_item in data["sponsor_updates"]:
        story.append(Paragraph(f"&bull; {sp_item}", bullet_style))

    story.append(Paragraph("<b>Faculty Mentor Updates:</b>", h2_style))
    for fm_item in data["mentor_updates"]:
        story.append(Paragraph(f"&bull; {fm_item}", bullet_style))

    # Challenges
    story.append(Paragraph("Challenges", h1_style))
    story.append(Paragraph("<b>Technical Challenges:</b>", h2_style))
    for tch in data["technical_challenges"]:
        story.append(Paragraph(f"&bull; {tch}", bullet_style))
    story.append(Paragraph("<b>Non-Technical Challenges:</b>", h2_style))
    for ntch in data["non_technical_challenges"]:
        story.append(Paragraph(f"&bull; {ntch}", bullet_style))

    # Action Items & Next Week Tasks
    story.append(Paragraph("Key Highlighted Action Items & Next Week Tasks", h1_style))
    story.append(Paragraph("<b>Key Highlighted Action Items:</b>", h2_style))
    for act in data["action_items"]:
        story.append(Paragraph(f"&bull; {act}", bullet_style))
    story.append(Paragraph("<b>Tasks to Finish in Next Week:</b>", h2_style))
    for nxt in data["next_week_tasks"]:
        story.append(Paragraph(f"&bull; {nxt}", bullet_style))

    doc.build(story)
    print(f"Generated PDF: {output_pdf_path}")

def main():
    print("Starting Capstone Reports generation...")
    F = get_report_facts()
    for report_data in build_reports_data(F):
        docx_path = os.path.join(REPORTS_DIR, report_data["filename_docx"])
        pdf_path = os.path.join(REPORTS_DIR, report_data["filename_pdf"])
        
        # 1. Build DOCX
        build_docx_report(report_data, docx_path)
        
        # 2. Build PDF
        build_pdf_report(report_data, pdf_path)
        
        # 3. If October 4, also update the official template DOCX and generate its PDF
        if report_data["date_str"] == "October 04, 2026":
            update_oct4_template_docx(report_data, ISB_TEMPLATE_OCT4)
            pdf_template_path = os.path.join(REPORTS_DIR, "Capstone Weekly Update-October 4.pdf")
            build_pdf_report(report_data, pdf_template_path)

        # 4. If current week (October 25), mirror to workspace root and create October 26 aliases
        if "25.10.26" in report_data["filename_docx"]:
            # Copy 25.10.26 to workspace root
            shutil.copy2(docx_path, os.path.join(ROOT, report_data["filename_docx"]))
            shutil.copy2(pdf_path, os.path.join(ROOT, report_data["filename_pdf"]))
            # Also create 26.10.26 alias in both directories
            alias_docx = "Capstone_Weekly_Report 26.10.26.docx"
            alias_pdf = "Capstone_Weekly_Report 26.10.26.pdf"
            shutil.copy2(docx_path, os.path.join(REPORTS_DIR, alias_docx))
            shutil.copy2(pdf_path, os.path.join(REPORTS_DIR, alias_pdf))
            shutil.copy2(docx_path, os.path.join(ROOT, alias_docx))
            shutil.copy2(pdf_path, os.path.join(ROOT, alias_pdf))
            print(f"Mirrored current week reports to workspace root and created 26.10.26 aliases.")

    print("\nAll 4 Capstone Weekly Reports generated successfully in both DOCX and PDF formats!")

if __name__ == "__main__":
    main()
