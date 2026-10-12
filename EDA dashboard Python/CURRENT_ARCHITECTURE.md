# CURRENT ARCHITECTURE AUDIT

**Date:** 2026-09-17  
**Project:** ISB Capstone - EDA & Demand Forecasting Dashboard  
**Status:** PHASE 0 AUDIT COMPLETE

---

## EXECUTIVE SUMMARY

### Current State
The project is a **Streamlit-based analytics dashboard** with:
- Interactive EDA visualizations
- Data quality assessment
- Basic demand forecasting with statistical and ML models
- PDF/CSV export functionality
- Dark/light theme support

### Dataset
- **Size:** 82,034 rows × 23 columns
- **Grain:** Individual transactions (Material/SKU, Branch, Billing Date, Quantities)
- **Time Coverage:** Years spanning 2022-2023
- **Key Dimensions:** Material (SKU), Branch/SALES OFFICE CODE, Week, Month, Year, Segment, Star Rating, Tonnage

### Assessment
**CURRENT LEVEL:** Entry-level analytics dashboard with basic forecasting capability  
**TARGET LEVEL:** Enterprise-grade Demand Intelligence & Forecasting Platform  
**GAP:** Significant - requires substantial refactoring and new modules

---

## CURRENT ARCHITECTURE

```
PROJECT STRUCTURE (EXISTING)
│
├── dashboard.py (single 2300+ line monolith)
│   ├── Theme/CSS injection
│   ├── Data loading & caching
│   ├── Data quality calculations
│   ├── Visualization functions
│   ├── Statistical forecasting (ARIMA, SARIMA, ETS)
│   ├── ML forecasting (Random Forest, Gradient Boosting)
│   ├── Metrics calculation
│   ├── PDF report generation
│   └── Streamlit UI pages
│
├── data/
│   ├── Filtered.csv (82K rows)
│   ├── Filtered.xlsx
│   ├── ARIMA_Forecast_Results.csv
│   └── [various screenshots]
│
├── requirements.txt (minimal)
│   ├── streamlit
│   ├── pandas, numpy
│   ├── plotly
│   ├── statsmodels
│   └── scikit-learn
│
└── documentation/
    ├── README.md
    ├── Redesign.MD (master blueprint)
    ├── FEATURES.md
    ├── Various guide documents
    └── Screenshots & presentations
```

### Current Data Flow

```
Filtered.csv
    ↓
Load & Cache (st.cache_data)
    ↓
Display in Multiple Pages:
├── Overview (KPIs, time series, segments)
├── Data Quality (quality score, missing values)
├── Data Cleaning (duplicates, recommendations)
├── Statistical Analysis (descriptive stats, heatmap)
├── Detailed Exploration (column analysis)
├── Demand Forecasting (ARIMA, SARIMA, ETS, RF, GB)
└── Export Reports (PDF, CSV, Excel)
```

### Current Forecasting Flow

```
SELECT SKU → AGGREGATE BY WEEK/BRANCH
    ↓
HISTORICAL DEMAND TIME SERIES
    ↓
    ├─→ ARIMA(1,1,1)
    ├─→ SARIMA(1,1,1)(0,1,1,12)
    ├─→ Exponential Smoothing (Triple)
    ├─→ Random Forest (13 engineered features)
    └─→ Gradient Boosting (13 engineered features)
    ↓
FORECAST + CONFIDENCE INTERVALS
    ↓
DISPLAY CHART + METRICS + EXPORT
```

---

## WHAT WORKS WELL ✅

1. **Data Loading & Caching**
   - Efficient use of `@st.cache_data`
   - Handles dataset size well (82K rows)

2. **Interactive Visualizations**
   - Plotly integration for interactive charts
   - Dark/light theme system
   - Professional CSS styling with glassmorphism

3. **Forecasting Models Implemented**
   - ARIMA with automatic parameter selection
   - SARIMA with seasonality handling
   - Exponential Smoothing (ETS)
   - Random Forest with feature engineering
   - Gradient Boosting implementation
   - Confidence intervals/prediction intervals

4. **Feature Engineering**
   - Lag features (1, 2, 3, 4, 8, 12, 13, 26, 52 weeks)
   - Rolling statistics (mean, std dev)
   - Trend features (growth rates)
   - Calendar features (week_of_year, month, etc.)

5. **Metrics Calculation**
   - MAE, RMSE, MAPE, R² calculated
   - Bias calculations
   - Model comparison capability

6. **Export Functionality**
   - PDF report generation
   - CSV export
   - Excel support

---

## CRITICAL ISSUES TO ADDRESS ❌

### 1. **Data Quality & Preparation (Missing/Weak)**
- ❌ NO canonical SKU × BRANCH × WEEK data mart
- ❌ NO automated data quality pipeline
- ❌ NO validation checks for impossible values
- ❌ NO demand profiling/classification engine
- ❌ Raw transaction data used directly without aggregation

### 2. **Forecasting Rigor (Incomplete)**
- ❌ NO rolling-origin / walk-forward backtesting
- ❌ Random train/test split used (INCORRECT for time-series)
- ❌ NO demand classification (intermittent, seasonal, etc.)
- ⚠️ Model selection appears manual/arbitrary
- ❌ NO baseline models (Naive, Seasonal Naive, etc.)
- ❌ NO intermittent demand models (Croston, SBA, TSB)

### 3. **Validation & Testing (Absent)**
- ❌ NO comprehensive backtesting framework
- ❌ NO cross-validation methodology
- ❌ NO test suite (unit, integration, data quality)
- ❌ NO leakage audit
- ⚠️ Metrics hardcoded or calculated on single train/test split

### 4. **Architectural Problems (Code Quality)**
- ❌ Single 2300+ line monolith (no separation of concerns)
- ❌ UI logic, business logic, and forecasting mixed together
- ❌ No modular data pipeline
- ❌ No separate configuration layer
- ❌ Hardcoded parameters scattered throughout

### 5. **Intelligence & Automation (Missing)**
- ❌ NO automatic model selection
- ❌ NO champion/challenger framework
- ❌ NO ensemble forecasting
- ❌ NO hierarchical reconciliation
- ❌ NO automatic demand classification

### 6. **Business Features (Absent)**
- ❌ NO inventory optimization
- ❌ NO safety stock calculation
- ❌ NO reorder point logic
- ❌ NO scenario analysis/what-if engine
- ❌ NO probabilistic forecasting (only confidence intervals)
- ❌ NO explainability (SHAP, feature importance context)

### 7. **Monitoring & MLOps (Missing)**
- ❌ NO forecast monitoring dashboard
- ❌ NO data drift detection
- ❌ NO model drift detection
- ❌ NO model registry
- ❌ NO retraining triggers
- ❌ NO health scoring

### 8. **Documentation (Incomplete)**
- ⚠️ Basic README only
- ❌ NO architecture documentation
- ❌ NO data dictionary
- ❌ NO forecasting methodology doc
- ❌ NO assumptions/limitations doc
- ❌ NO model cards

---

## CURRENT DATA STRUCTURE

### Available Fields (23 columns)
```
Material              → SKU identifier
Billing Doc.         → Transaction ID
Item                 → Item number
SALES OFFICE CODE    → Branch identifier (SBD1, MAA, BLR, COK, SBD)
EXT MAT GROUP        → Material group (RA-ODU, RA-IDU)
MatGroup3            → Material group level 3 (RA)
Star Rating          → Product rating (I5S, I3S, etc.)
Segment              → Product segment (Inverter, etc.)
Star Rating.1        → Duplicate field
Stor. Location       → Storage location
SALES OFFICE CODE.1  → Duplicate field
SBU                  → Strategic Business Unit (RA)
Year                 → Year (22-23, 23-24, etc.)
Month                → Month text (12) Mar, etc.)
Week                 → Week text (Wk 1, Wk 2, etc.)
Billing Date         → Transaction date
Customer             → Customer name
Material.1           → Duplicate SKU field
Billing Quantity ODU → Quantity in ODU (Original Design Unit)
Billing Quantity IDU → Quantity in IDU (Intermediate Design Unit)
Tonnage              → Weight/tonnage
Dealer Name          → Dealer/partner name
Tonnage.1            → Duplicate tonnage field
```

### Data Issues Identified
- **Duplicates:** Multiple columns repeat data (Star Rating.1, Billing Doc., Material.1, Tonnage.1, SALES OFFICE CODE.1)
- **Grain:** Transaction-level (one row per billing)
- **Aggregation Needed:** Must aggregate to SKU × BRANCH × WEEK grain
- **Time Parsing:** Week/Month/Year need proper parsing to date

---

## FORECASTING MODELS CURRENTLY IMPLEMENTED

### Statistical Models
1. **ARIMA(1,1,1)** ✅ Implemented
   - Box-Jenkins univariate baseline
   - Fixed parameters (no auto-selection)
   - Good for trending data
   - Status: Working but basic

2. **SARIMA(1,1,1)(0,1,1,12)** ✅ Implemented
   - Handles seasonality (12-week season)
   - More sophisticated than ARIMA
   - Status: Working but parameters hardcoded

3. **Exponential Smoothing (ETS - Triple Additive)** ✅ Implemented
   - Level + Trend + Seasonal components
   - Fast convergence
   - Status: Working

### Machine Learning Models
1. **Random Forest Regressor** ✅ Implemented
   - 13 engineered features
   - No hyperparameter tuning
   - Status: Working but basic

2. **Gradient Boosting Regressor** ✅ Implemented
   - Similar to Random Forest
   - Status: Working but basic

### Models NOT Implemented (Per Redesign Blueprint)
- ❌ Naive baseline
- ❌ Seasonal Naive baseline
- ❌ Croston (intermittent demand)
- ❌ SBA (Syntetos-Boylan approximation)
- ❌ TSB (Teunter-Syntetos-Babai)
- ❌ XGBoost
- ❌ LightGBM
- ❌ Ensemble methods

---

## METRICS CALCULATION

### Currently Calculated
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error) — ⚠️ problematic with zero demand
- R² (Coefficient of Determination)
- Bias calculation

### NOT Calculated (Per Redesign Blueprint)
- ❌ WAPE (Weighted Absolute Percentage Error)
- ❌ sMAPE (Symmetric MAPE)
- ❌ MASE (Mean Absolute Scaled Error)
- ❌ Fold-by-fold backtesting metrics
- ❌ Bias % (percentage format)

---

## VALIDATION METHODOLOGY (CURRENT)

### Problem: Incorrect for Time-Series
```
Current Approach (WRONG):
├── Random train/test split (70/30)
└── Single model evaluation

Required Approach (CORRECT):
├── Rolling-origin / Walk-forward validation
├── Multiple folds
├── Proper chronological ordering
├── No future information leakage
└── Consistent metrics across folds
```

---

## CONFIGURATION & PARAMETERS (Current)

### Hardcoded Throughout dashboard.py
- ARIMA order: (1,1,1)
- SARIMA order: (1,1,1)(0,1,1,12)
- Lag features: hardcoded list
- Forecast horizon: typically 12 weeks
- Random seed: not set consistently
- Model parameters: scattered, not centralized

---

## STRENGTHS TO PRESERVE ✅

1. **Data loading efficiency** - `@st.cache_data` is well-used
2. **Forecasting model implementations** - Core ARIMA/SARIMA/ETS work
3. **Feature engineering foundation** - Lag and rolling features exist
4. **Visualization capability** - Plotly integration is solid
5. **Theme system** - Professional CSS/styling foundation
6. **Export functionality** - PDF/CSV working
7. **Metrics framework** - Basic metrics calculation infrastructure

---

## FILES TO PRESERVE (With Refactoring)

```
✅ Filtered.csv / Filtered.xlsx (RAW DATA - will not modify)
✅ dashboard.py (WILL REFACTOR - extract into modules)
✅ requirements.txt (WILL EXPAND - add new dependencies)
```

---

## FILES TO CREATE (Per Phase 0-9 Plan)

### Phase 1 - Foundation
```
src/
├── data/
│   ├── __init__.py
│   ├── ingestion.py (load & cache)
│   ├── validation.py (quality checks)
│   ├── cleaning.py (dedupe, standardize)
│   ├── transformation.py (aggregation to SKU×BRANCH×WEEK)
│   └── aggregation.py (hierarchical)
│
config/
├── data_config.yaml
├── model_config.yaml
└── business_config.yaml

tests/
├── test_data.py
├── test_features.py
└── test_pipeline.py

LEAKAGE_AUDIT.md
ARCHITECTURE.md
DATA_DICTIONARY.md
```

### Phase 2-6 - Core Forecasting & Intelligence
```
src/
├── features/
│   ├── __init__.py
│   ├── calendar_features.py
│   ├── lag_features.py
│   ├── rolling_features.py
│   └── trend_features.py
│
├── forecasting/
│   ├── __init__.py
│   ├── baseline.py
│   ├── arima.py
│   ├── sarima.py
│   ├── ets.py
│   ├── croston.py
│   ├── xgboost_model.py
│   └── lightgbm_model.py
│
├── validation/
│   ├── __init__.py
│   ├── backtesting.py
│   ├── metrics.py
│   └── cross_validation.py
│
├── selection/
│   ├── __init__.py
│   ├── demand_classifier.py
│   ├── model_selector.py
│   └── champion_challenger.py
│
├── inventory/
│   ├── __init__.py
│   ├── safety_stock.py
│   └── service_level.py
│
└── monitoring/
    ├── __init__.py
    ├── forecast_monitor.py
    └── drift.py
```

### Phase 7 - Refactored UI
```
app/
├── dashboard.py (entry point)
├── pages/
│   ├── executive.py
│   ├── data_quality.py
│   ├── demand_explorer.py
│   ├── forecasting.py
│   ├── model_lab.py
│   ├── inventory.py
│   ├── monitoring.py
│   └── scenarios.py
│
└── components/
    ├── charts.py
    ├── kpi_cards.py
    ├── filters.py
    └── alerts.py
```

### Phase 8-9 - Tests & Documentation
```
notebooks/
├── 01_data_audit.ipynb
├── 02_eda.ipynb
├── 03_demand_patterns.ipynb
└── 04_model_benchmark.ipynb

FORECASTING_METHODOLOGY.md
MODEL_CARD.md
ASSUMPTIONS.md
DEPLOYMENT_GUIDE.md
```

---

## DATA FLOW TRANSFORMATION

### CURRENT STATE
```
Raw Transaction Data (82K rows)
    ↓
Load once → cache → display across all pages
```

### TARGET STATE
```
Raw Billing Data (Filtered.csv)
    ↓
INGESTION LAYER
    ↓
VALIDATION LAYER (Quality Checks)
    ↓
CLEANING LAYER (Deduplication, Standardization)
    ↓
TRANSFORMATION LAYER (Parse dates, extract weeks)
    ↓
SKU × BRANCH × WEEK DATA MART (Canonical Dataset)
    ↓
DEMAND PROFILING (Classification: Smooth, Seasonal, Intermittent, etc.)
    ↓
FEATURE ENGINEERING (Lags, rolling, trends, calendar)
    ↓
FORECASTING ENGINE (Multi-model, auto-selection)
    ↓
BACKTESTING (Rolling-origin validation)
    ↓
CHAMPION SELECTION (Best model per SKU/branch)
    ↓
INFERENCE (Generate forecasts + intervals)
    ↓
BUSINESS LOGIC (Inventory, scenarios, risk)
    ↓
VISUALIZATION LAYER (Dashboard pages)
    ↓
MONITORING (Drift, degradation, alerts)
```

---

## CRITICAL IMPROVEMENTS NEEDED

### TIER 1 (Must Have - Project Foundation)
1. **Canonical Data Mart** - Aggregate to SKU × BRANCH × WEEK
2. **Data Quality Pipeline** - Automated validation
3. **Rolling-Origin Backtesting** - Proper time-series validation
4. **Baseline Models** - Naive, Seasonal Naive mandatory
5. **Model Leakage Audit** - Explicit documentation
6. **Configuration System** - YAML-based parameters

### TIER 2 (High Priority - Intelligence)
1. **Automatic Demand Classification** - Profile each SKU
2. **Automatic Model Selection** - Champion per SKU
3. **Intermittent Demand Models** - Croston, SBA, TSB
4. **Probabilistic Forecasting** - P10/P50/P90
5. **Ensemble Methods** - Compare vs individual models

### TIER 3 (Important - Business Value)
1. **Inventory Optimization** - Safety stock, ROP
2. **Explainability** - SHAP for ML models
3. **Scenario Analysis** - What-if engine
4. **Monitoring Dashboard** - Drift, degradation tracking
5. **Model Registry** - Version tracking

### TIER 4 (Polish - Enterprise Ready)
1. **Hierarchical Reconciliation** - Branch/Region/SKU alignment
2. **Advanced Explainability** - Business driver narratives
3. **Automated Alerts** - Model health, data issues
4. **Performance Optimization** - Caching, parallelization

---

## EXECUTION PLAN

### Phase 0: AUDIT ✅ COMPLETE
- [x] Inspect repository
- [x] Understand current architecture
- [x] Identify gaps
- [x] Document findings

### Phase 1: FOUNDATION (1-2 weeks)
- Build data pipeline (ingestion → validation → cleaning → aggregation)
- Create SKU × BRANCH × WEEK data mart
- Implement data quality checks
- Create configuration system
- Setup project structure & tests

### Phase 2: FORECASTING ENGINE (1-2 weeks)
- Implement all baseline models
- Improve existing models (ARIMA, SARIMA, ETS)
- Add intermittent demand models (Croston, SBA, TSB)
- Implement Random Forest, Gradient Boosting properly
- Add XGBoost, LightGBM

### Phase 3: VALIDATION (1 week)
- Implement rolling-origin backtesting framework
- Add all required metrics (WAPE, sMAPE, MASE, Bias %)
- Create model benchmark table
- Validate against baselines

### Phase 4: INTELLIGENCE (1 week)
- Build demand classification engine
- Implement automatic model selection logic
- Add champion/challenger framework
- Implement ensemble methods

### Phase 5: BUSINESS FEATURES (3-4 days)
- Inventory optimization (safety stock, ROP)
- Service level calculations
- Scenario analysis framework

### Phase 6: MONITORING (3-4 days)
- Forecast monitoring dashboard
- Data drift detection
- Model health scoring
- Alerts framework

### Phase 7: DASHBOARD REBUILD (1-2 weeks)
- Refactor monolith into modular pages
- Build new pages (Executive, Model Lab, etc.)
- Update visualizations for new data/models
- Implement new UI components

### Phase 8: TESTING (3-4 days)
- Unit tests for data pipeline
- Feature engineering tests
- Model execution tests
- End-to-end pipeline test

### Phase 9: DOCUMENTATION (3-4 days)
- Update README
- Write ARCHITECTURE.md
- Create DATA_DICTIONARY.md
- Write FORECASTING_METHODOLOGY.md
- Create MODEL_CARDS
- Document assumptions

---

## RISK MITIGATION

### Key Risks
1. **Data Loss** → Use version control, keep backups
2. **Breaking Existing Functionality** → Incremental refactoring, preserve working code
3. **Performance Degradation** → Test with full dataset, optimize caching
4. **Leakage Introduction** → Explicit audit before/after
5. **Overfitting Complex Models** → Rigorous backtesting framework

### Mitigation Strategies
- Keep original dashboard.py as backup
- Use git for version control
- Run full application tests after each phase
- Document all assumptions
- Test on full 82K row dataset

---

## SUCCESS CRITERIA

### Phase 0 Audit: ✅ COMPLETE
- [x] Current architecture documented
- [x] Strengths/weaknesses identified
- [x] Data structure understood
- [x] Migration plan clear

### Final Delivery: READY TO DEMO
- [ ] All 50 design principles satisfied
- [ ] Complete forecasting pipeline working
- [ ] Automatic model selection functioning
- [ ] Enterprise-quality dashboard rendering
- [ ] All tests passing
- [ ] Complete documentation
- [ ] Can demo end-to-end flow to Deloitte team

---

## NEXT STEP

→ **PROCEED TO PHASE 1: FOUNDATION**

Implement the data pipeline, canonical data mart, and configuration system.

---

**Audit Prepared By:** AI Code Assistant  
**Status:** Ready for Phase 1 Implementation
