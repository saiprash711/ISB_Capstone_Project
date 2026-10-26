# ❄️ Enterprise SKU Demand Intelligence & Forecasting Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)]()
[![Methodology](https://img.shields.io/badge/validation-walk--forward%20rolling--origin-success.svg)]()
[![Architecture](https://img.shields.io/badge/design-consulting--grade%20enterprise-blueviolet.svg)]()

A production-quality, consulting-grade **SKU-Level Demand Intelligence & Multi-Branch Forecasting Platform** developed for Daikin South Region HVAC commercial operations. Built with strict separation of concerns, zero temporal data leakage, multi-echelon reconciliation, inventory optimization, scenario stress testing, and real-time model monitoring.

---

## 🏛️ Executive Summary & Platform Capabilities

This platform transforms supply chain planning from disconnected spreadsheet forecasting into an end-to-end operational intelligence suite:

1. **Enterprise Data Engineering**: Ingests SAP transactional data, enforces non-negative constraints, standardizes 8,951 canonical SKU-Branch-Week observations (`Filtered.csv`), and performs automated data health audits.
2. **Syntetos-Boylan Demand Profiling**: Categorizes demand curves into **Smooth, Erratic, Intermittent, and Lumpy** regimes using Average Demand Interval (ADI) and squared coefficient of variation ($CV^2$), automatically routing SKUs to optimal algorithmic families.
3. **17 Candidate Models**: classical baselines, a pooled **Seasonal Index** model (region/branch seasonal profile × SKU level), ARIMA, seasonal ARIMA and damped-trend ETS on seasonally adjusted demand, Croston/SBA/TSB, tree-based ML (Random Forest, Gradient Boosting, LightGBM, XGBoost) and an inverse-WAPE ensemble.
4. **Leakage-Free Rolling-Origin Backtesting**: 4 chronological folds × 12 weeks; the seasonal profile is re-estimated at each fold cutoff. Champion = lowest RMSE; WAPE, sMAPE, MASE and bias are reported. Validated out-of-sample on FY24-25 billing: see [VALIDATION_FY25.md](VALIDATION_FY25.md).
5. **Automated Champion/Challenger Governance**: Transparent tournament selection promoting models based on out-of-sample WAPE lift ($\ge 3\%$) and bias tolerance ($\le 15\%$) against naive baselines.
6. **Multi-Echelon Hierarchical Reconciliation**: Guarantees mathematical coherency between aggregate South Region projections, Branch allocations, and SKU-level forecasts via Bottom-Up and Top-Down disaggregation.
7. **Business Inventory Engine**: Converts statistical predictions into operational inventory policies, computing Lead Time Demand, Safety Stock ($SS = Z \times \sigma_{LTD}$), Reorder Points, and service level sensitivity matrices (85%–99%).
8. **What-If Scenario Simulator**: Simulates forward demand shocks (+30% Summer Heatwave, +20% Dealer Promotions, -20% Supply Disruptions) and recalculates working capital exposure.
9. **Explainability & Model Health Radar**: Decomposes forecasts into additive baseline, inertia, seasonality, and promotional drivers, while actively monitoring Tracking Signals ($\pm 4.0$ MAD) and Population Stability Index (PSI) drift.

---

## 🖥️ Platform Navigation (11 Executive Views)

The Streamlit UI (`dashboard.py`) features 11 dedicated operational consoles:

| # | Console View | Core Functionality |
|---|--------------|-------------------|
| 1 | **🏠 Overview** | High-level KPI cards, total volume, data completeness gauge, and dynamic **Executive Action Queue**. |
| 2 | **📊 Data Quality** | Column-by-column missingness, zero-demand rates, type checks, and quality health score (0–100). |
| 3 | **🧹 Data Cleaning** | Duplicate elimination, negative demand clipping, SKU standardization, and before/after audit metrics. |
| 4 | **📈 Statistical Analysis** | Descriptive statistics, demand distribution histograms, box plots, and feature correlation heatmaps. |
| 5 | **🔍 Detailed Exploration** | Deep-dive search engine across 82,000+ raw transactions and canonical aggregated weekly demand series. |
| 6 | **🎯 Demand Forecasting** | SKU-level interactive forecasting with automated Syntetos-Boylan profiling, ARIMA, ML, and **AutoML Champion**. |
| 7 | **🏆 Model Lab & Tournament** | Multi-model leaderboard, rolling-origin backtesting metrics, baseline lift comparison, and champion governance. |
| 8 | **📦 Inventory Intelligence** | Lead Time Demand, Safety Stock, Reorder Points, working capital risk, and service level sensitivity grid. |
| 9 | **⚡ Scenario Simulator** | Stress-testing forward curves with custom percentage shocks (+30% Heatwave, +20% Promo) and capital impact. |
| 10 | **📡 Monitoring & Drift Radar** | Live Tracking Signal ($TS$), Cumulative Sum of Errors (CUSUM), PSI distribution drift, and model retraining triggers. |
| 11 | **📄 Export Report** | Automated PDF executive summary generation, Excel reporting, and audit trail export. |

---

## 📂 Repository Structure

```text
EDA dashboard Python/
├── dashboard.py                       # Main Streamlit application (11 navigation views)
├── Filtered.csv                       # Canonical aggregated data mart (8,951 rows)
├── Filtered.xlsx                      # Raw SAP transactions
├── requirements.txt                   # Production dependencies
├── Start.bat                          # One-click Windows launch script
│
├── src/                               # Modular Python Package
│   ├── __init__.py
│   ├── dashboard_intelligence.py      # Streamlit components for Intelligence Views
│   ├── data/                          # Layer 1: Ingestion, Cleaning, Mart Transformation
│   │   ├── cleaning.py
│   │   ├── ingestion.py
│   │   ├── quality.py
│   │   └── transformation.py
│   ├── features/                      # Layer 2: Time Series & Lag Feature Engineering
│   │   └── engineering.py
│   ├── forecasting/                   # Layer 3: Statistical, ML & Ensemble Forecasters
│   │   ├── baselines.py
│   │   ├── ensemble.py
│   │   ├── forecaster.py
│   │   ├── ml_models.py
│   │   └── statistical.py
│   ├── validation/                    # Layer 4: APICS Metrics & Rolling-Origin Backtesting
│   │   ├── backtesting.py
│   │   ├── cross_validation.py
│   │   └── metrics.py
│   ├── selection/                     # Layer 5: Syntetos-Boylan Profiling & Champion Governance
│   │   ├── champion_challenger.py
│   │   ├── demand_classifier.py
│   │   └── model_selector.py
│   ├── hierarchy/                     # Layer 6: Hierarchical Aggregation & Reconciliation
│   │   ├── aggregation.py
│   │   └── reconciliation.py
│   ├── uncertainty/                   # Layer 7: Probabilistic Bounds (P10, P50, P90)
│   │   └── prediction_intervals.py
│   ├── inventory/                     # Layer 8: Safety Stock, LTD, ROP & Working Capital
│   │   └── inventory_engine.py
│   ├── scenarios/                     # Layer 9: What-If Stress Testing Simulator
│   │   └── simulator.py
│   ├── explainability/                # Layer 10: Additive Attribution & Feature Drivers
│   │   └── shap_analysis.py
│   └── monitoring/                    # Layer 11: Tracking Signal, PSI Drift & Model Registry
│       ├── alerts.py
│       ├── drift.py
│       ├── forecast_monitor.py
│       └── registry.py
│
├── tests/                             # Automated Test Suite (pytest)
│   ├── test_backtesting.py
│   ├── test_hierarchy.py
│   ├── test_inventory.py
│   ├── test_leakage_audit.py
│   ├── test_metrics.py
│   ├── test_monitoring.py
│   ├── test_scenarios.py
│   └── test_selection.py
│
└── docs/ & root documentation:
    ├── ARCHITECTURE.md                # System design & separation of concerns
    ├── FORECASTING_METHODOLOGY.md     # Mathematical formulations & backtesting
    ├── LEAKAGE_AUDIT.md               # Formal zero temporal data leakage audit
    ├── MODEL_CARD.md                  # Intended use, data, model and limitations
    ├── ASSUMPTIONS.md                 # Business & operational assumptions
    └── PHASE_COMPLETION_REPORT.md     # Full consulting audit & delivery sign-off
```

---

## 🚀 Quick Start

### 1. Installation & Environment Setup

Ensure Python 3.10+ is installed:

```bash
# Clone the repository and navigate to root
cd "c:\ISB Capstone\EDA dashboard Python"

# Install production dependencies
pip install -r requirements.txt
```

### 2. Run the Automated Verification Suite

Run the test suite (metrics, rolling-origin backtesting, demand classification, hierarchy, inventory, scenarios, leakage checks):

```bash
python -m pytest tests/ -v
```

Expected output:
```text
======================== 41 passed in 17.50s ========================
```

### 3. Launch the Executive Dashboard

Launch the interactive platform:

```bash
python -m streamlit run dashboard.py
```

Or on Windows, simply double-click **`Start.bat`**.

---

## 📈 Forecasting Model Portfolio

| Algorithmic Category | Implemented Models | Primary Use Case |
|----------------------|--------------------|------------------|
| **Baselines** | Naive (Random Walk), Seasonal Naive (52W Lag), Moving Average (SMA 4W), SES | Benchmark standards & lift calculation |
| **Seasonal** | Seasonal Index (8-week and 26-week level windows) | Pooled annual cycle + month-end billing push |
| **Statistical** | ARIMA (min-AIC order), seasonal ARIMA and damped-trend ETS on seasonally adjusted demand | Trended and seasonal series |
| **Intermittent** | Croston's Method, Syntetos-Boylan (SBA), Teunter-Syntetos-Babai (TSB) | Sparse, zero-inflated, and lumpy demand |
| **Machine Learning** | Random Forest, Gradient Boosting, XGBoost, LightGBM | Non-linear relationships & multi-lag interactions |
| **Ensemble** | Inverse-WAPE weighted ensemble (weights from earlier backtest folds) | Blended multi-model risk minimization |

---

## 📋 Technical Documentation Suite

For comprehensive methodology, mathematics, and operational guides, consult the detailed documentation:

- 📐 [ARCHITECTURE.md](ARCHITECTURE.md) &ndash; System architecture, modular boundaries, and data flow.
- 📊 [FORECASTING_METHODOLOGY.md](FORECASTING_METHODOLOGY.md) &ndash; Mathematical formulations, backtesting protocols, and metric formulas.
- 🛡️ [LEAKAGE_AUDIT.md](LEAKAGE_AUDIT.md) &ndash; Formal temporal data leakage audit with empirical proofs.
- 🏷️ [MODEL_CARD.md](MODEL_CARD.md) &ndash; Intended use, data, model and limitations.
- ✅ [VALIDATION_FY25.md](VALIDATION_FY25.md) &ndash; Out-of-sample results on FY24-25 billing (generated).
- 📑 [ASSUMPTIONS.md](ASSUMPTIONS.md) &ndash; Lead times, unit costs, review periods, and service levels.
- 🏁 [PHASE_COMPLETION_REPORT.md](PHASE_COMPLETION_REPORT.md) &ndash; Comprehensive final phase completion and sign-off report.

---

## 👥 Authors & Academic Context
* **Program**: Indian School of Business (ISB) &ndash; Advanced Analytics Capstone Project
* **Industry Focus**: HVAC Multi-Branch Commercial Demand Planning (Daikin South Region)
* **Status**: Production-Ready / Consulting-Grade Release (Version 3.0)
