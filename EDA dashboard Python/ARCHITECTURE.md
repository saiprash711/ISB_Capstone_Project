# Enterprise Demand Intelligence & Forecasting Platform Architecture

## 1. Executive Architecture Overview

The platform transforms raw SAP billing transactions across multi-branch supply chain networks into consulting-grade demand intelligence, rolling-origin forecast tournaments, and inventory optimization policies.

```
                                    RAW BUSINESS DATA
                          (SAP Billing Transactions / SAP ECC)
                                           │
                                           ▼
                                 DATA INGESTION LAYER
                          (Schema Validation & Type Coercion)
                                           │
                                           ▼
                             DATA QUALITY & VALIDATION ENGINE
                        (Null Density, Cardinality, Value Bounds)
                                           │
                                           ▼
                                  DATA CLEANING LAYER
                        (Deduplication, Returns / Negative Removal)
                                           │
                                           ▼
                             CANONICAL DATA MART (8,951 rows)
                               (Grain: SKU × BRANCH × WEEK)
                                           │
                                           ▼
                              DEMAND CLASSIFICATION ENGINE
                     (Syntetos-Boylan ADI & CV² Quadrant Profiling)
                                           │
                  ┌────────────────────────┼────────────────────────┐
                  ▼                        ▼                        ▼
             Smooth / Trend            Seasonal               Intermittent / Lumpy
             (ARIMA / ETS)             (SARIMA)               (Croston / SBA / TSB)
                  │                        │                        │
                  └────────────────────────┼────────────────────────┘
                                           │
                                           ▼
                                   ML FEATURE ENGINE
                       (40+ Multi-Resolution Lags & Rolling Run-Rates)
                                           │
                                           ▼
                                 GLOBAL & LOCAL ML MODELS
                        (Random Forest, Gradient Boosting, LightGBM)
                                           │
                                           ▼
                             ROLLING-ORIGIN BACKTESTING
                       (Chronological Walk-Forward Folds, Zero Leakage)
                                           │
                                           ▼
                                 CHAMPION / CHALLENGER
                        (WAPE Leaderboard, Lift & Stability Score)
                                           │
                                           ▼
                                PROBABILISTIC FORECASTING
                                     P10 / P50 / P90
                                           │
                   ┌───────────────────────┴───────────────────────┐
                   ▼                                               ▼
            INVENTORY ENGINE                                SCENARIO ENGINE
       (Safety Stock, ROP, Stockout Risk)            (Heatwave, Promo, Supply Shocks)
                   │                                               │
                   └───────────────────────┬───────────────────────┘
                                           ▼
                             DEMAND INTELLIGENCE COCKPIT
                     (Executive Cockpit, Forecast Explorer, Model Lab,
                      Inventory Intel, Scenario Simulator, Drift Radar)
```

---

## 2. Separation of Concerns (SoC) Principle

The platform adheres to strict structural separation:
```
UI (Streamlit Views) ≠ BUSINESS LOGIC (Inventory/Scenarios) ≠ MODELING LOGIC (Forecasters) ≠ DATA ENGINEERING (Pipeline)
```

| Layer | Directory | Primary Responsibilities |
|---|---|---|
| **Data Engineering** | `src/data/` | Ingestion, schema validation, deduplication, returns removal, canonical SKU × Branch × Week data mart creation |
| **Feature Engineering** | `src/features/` | 40+ temporal lags, rolling statistics, calendar harmonics, trend growth without target leakage |
| **Forecasting Engine** | `src/forecasting/` | 4 model families (Baseline, Statistical, Intermittent, ML) + Inverse-WAPE Ensemble |
| **Validation Framework** | `src/validation/` | Zero-safe metrics (WAPE, sMAPE, MASE, RMSE), rolling-origin walk-forward splits, Leaderboard |
| **Intelligence & Selection** | `src/selection/` | Syntetos-Boylan demand profiling, candidate routing, Champion/Challenger promotion governance |
| **Uncertainty Quantification** | `src/uncertainty/` | Conformal prediction residual calibration, P10/P50/P90 prediction intervals |
| **Hierarchical Reconciliation** | `src/hierarchy/` | Bottom-Up, Top-Down, and MinT coherency ($\sum \text{SKU} = \text{Branch} = \text{Region}$) |
| **Business Decision Engine** | `src/inventory/`, `src/scenarios/` | Safety Stock ($SS = Z \times \sigma_{LTD}$), Reorder Point, Stockout Risk, What-If stress tests |
| **Explainability & Monitoring** | `src/explainability/`, `src/monitoring/` | Feature importance waterfall, Tracking Signal ($TS$), Population Stability Index (PSI) drift, Registry |
| **Presentation / UI** | `dashboard.py`, `src/dashboard_intelligence.py` | Executive Cockpit, Forecast Explorer, Model Lab, Inventory Intel, Scenarios, Drift Radar |

---

## 3. Data Flow & Integrity Contracts

1. **Input Contract**:
   - Primary SAP source: `Filtered.csv` / `Filtered.xlsx` (~14 MB).
   - Ingestion validates 17 core business dimensions including `Billing Date`, `Billing Quantity ODU`, `Material` (SKU), `SALES OFFICE CODE` (Branch).
2. **Data Mart Grain**:
   - Canonical representation: `SKU × BRANCH × WEEK`.
   - Aggregates daily invoices into ISO calendar weeks.
   - Negative billing quantities (credit memos, return orders) are cleanly filtered.
3. **Execution Pipeline**:
   - Feature engineering generates lags ($t-1, t-2, \dots, t-52$) and rolling averages strictly using historical observations $t' \le t$.
   - Backtesting expands chronological training windows with zero future visibility.
