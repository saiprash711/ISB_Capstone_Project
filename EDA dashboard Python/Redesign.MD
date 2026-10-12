# MASTER PROMPT

## Transform the Existing Project into an Enterprise-Grade SKU-Level Demand Intelligence & Forecasting Platform

You are acting as a **Principal Data Scientist + Senior ML Engineer + Forecasting Specialist + Data Engineer + MLOps Engineer + Enterprise Analytics Architect**.

I have an existing SKU-wise demand forecasting project that currently contains a Streamlit dashboard, EDA/data-quality functionality, and an initial forecasting implementation.

Your job is **NOT to create a separate toy project**.

Your job is to **inspect the entire existing repository first, understand what already works, preserve valuable functionality, then refactor and upgrade the project into a production-quality, consulting-grade Demand Intelligence platform.**

The final result should be something that I can confidently demonstrate to a senior Deloitte analytics/consulting team.

---

# 1. NON-NEGOTIABLE RULE

## DO NOT START CODING IMMEDIATELY.

First inspect the entire repository.

Understand:

* directory structure
* source files
* data files
* current dashboard
* forecasting implementation
* preprocessing
* feature engineering
* existing models
* evaluation methodology
* visualizations
* exports
* documentation
* configuration
* dependencies
* deployment setup
* tests
* notebooks
* current bugs
* duplicated code
* architectural weaknesses

Read the relevant files completely where necessary.

Create an internal understanding of:

```text
CURRENT ARCHITECTURE
CURRENT DATA FLOW
CURRENT FORECASTING FLOW
CURRENT UI FLOW
CURRENT MODELING LIMITATIONS
CURRENT BUSINESS LOGIC
CURRENT DEPLOYMENT MODEL
```

Then produce a short:

```text
ARCHITECTURE AUDIT
```

before making major changes.

Do not destroy working functionality simply because you can implement it differently.

---

# 2. PRIMARY OBJECTIVE

Transform the project from:

> "A Streamlit dashboard with several forecasting models"

into:

> "An end-to-end SKU-level Demand Intelligence & Forecasting Platform"

The target architecture should conceptually be:

```text
                         RAW BUSINESS DATA
                                │
                                ▼
                      DATA INGESTION LAYER
                                │
                                ▼
                     DATA QUALITY & VALIDATION
                                │
                                ▼
                       DATA CLEANING LAYER
                                │
                                ▼
                  SKU × BRANCH × WEEK DATA MART
                                │
                                ▼
                       DEMAND PROFILING
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
           SMOOTH           SEASONAL        INTERMITTENT
              │                 │                 │
              ▼                 ▼                 ▼
          ETS/ARIMA          SARIMA       CROSTON/SBA/TSB
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                       ML FEATURE ENGINE
                                │
                                ▼
                    GLOBAL ML FORECASTING
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                 XGBoost     LightGBM    Random Forest
                    │           │           │
                    └───────────┼───────────┘
                                │
                                ▼
                      ROLLING BACKTESTING
                                │
                                ▼
                    CHAMPION / CHALLENGER
                                │
                                ▼
                  MODEL SELECTION / ENSEMBLE
                                │
                                ▼
                 PROBABILISTIC FORECASTING
                         P10 / P50 / P90
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
          INVENTORY ENGINE                SCENARIO ENGINE
                 │                             │
                 ▼                             ▼
       Safety Stock / ROP              What-if Analysis
       Stockout Risk                   Demand Scenarios
       Service Level
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                     DEMAND INTELLIGENCE
                            COCKPIT
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
             Executive      Forecast       Monitoring
             Dashboard      Explorer       & Drift
```

---

# 3. ARCHITECTURAL REFACTOR

The existing project currently has substantial functionality inside the Streamlit dashboard.

Refactor the project so that:

```text
UI ≠ BUSINESS LOGIC ≠ MODELING LOGIC ≠ DATA ENGINEERING
```

Use clean separation of concerns.

Target structure should be approximately:

```text
project/
│
├── app/
│   ├── dashboard.py
│   │
│   ├── pages/
│   │   ├── executive.py
│   │   ├── data_quality.py
│   │   ├── demand_explorer.py
│   │   ├── forecasting.py
│   │   ├── model_lab.py
│   │   ├── inventory.py
│   │   ├── scenarios.py
│   │   └── monitoring.py
│   │
│   └── components/
│       ├── charts.py
│       ├── kpi_cards.py
│       ├── tables.py
│       ├── filters.py
│       └── alerts.py
│
├── src/
│   │
│   ├── data/
│   │   ├── ingestion.py
│   │   ├── validation.py
│   │   ├── cleaning.py
│   │   ├── transformation.py
│   │   └── aggregation.py
│   │
│   ├── features/
│   │   ├── calendar_features.py
│   │   ├── lag_features.py
│   │   ├── rolling_features.py
│   │   ├── trend_features.py
│   │   └── external_features.py
│   │
│   ├── forecasting/
│   │   ├── baseline.py
│   │   ├── naive.py
│   │   ├── seasonal_naive.py
│   │   ├── arima.py
│   │   ├── sarima.py
│   │   ├── ets.py
│   │   ├── croston.py
│   │   ├── sba.py
│   │   ├── tsb.py
│   │   ├── xgboost_model.py
│   │   ├── lightgbm_model.py
│   │   ├── random_forest.py
│   │   └── ensemble.py
│   │
│   ├── validation/
│   │   ├── backtesting.py
│   │   ├── cross_validation.py
│   │   └── metrics.py
│   │
│   ├── selection/
│   │   ├── model_selector.py
│   │   ├── demand_classifier.py
│   │   └── champion_challenger.py
│   │
│   ├── hierarchy/
│   │   ├── aggregation.py
│   │   └── reconciliation.py
│   │
│   ├── uncertainty/
│   │   ├── prediction_intervals.py
│   │   └── conformal.py
│   │
│   ├── inventory/
│   │   ├── safety_stock.py
│   │   ├── reorder_point.py
│   │   ├── service_level.py
│   │   └── stockout_risk.py
│   │
│   ├── explainability/
│   │   └── shap_analysis.py
│   │
│   └── monitoring/
│       ├── forecast_monitor.py
│       ├── drift.py
│       └── alerts.py
│
├── configs/
│   ├── data_config.yaml
│   ├── model_config.yaml
│   └── business_config.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── forecasts/
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_demand_patterns.ipynb
│   ├── 04_model_benchmark.ipynb
│   └── 05_business_impact.ipynb
│
├── tests/
│   ├── test_data.py
│   ├── test_features.py
│   ├── test_models.py
│   ├── test_backtesting.py
│   └── test_pipeline.py
│
├── reports/
│   ├── model_performance/
│   ├── business_insights/
│   └── executive/
│
├── requirements.txt
├── README.md
├── Dockerfile
└── docker-compose.yml
```

Do not blindly create every file.

Only create modules that contain meaningful implementation.

---

# 4. DATA ENGINEERING LAYER

Build a canonical forecasting dataset.

The primary grain should be:

```text
SKU × BRANCH × WEEK
```

Create a standardized data mart containing fields such as:

```text
date
year
week
branch
sku
segment
star_rating
tonnage
demand_odu
demand_idu
total_demand
```

Where appropriate, retain useful business dimensions from the original dataset.

Do NOT unnecessarily delete useful columns.

Document every transformation.

---

# 5. DATA QUALITY ENGINE

Build an automated data-quality pipeline.

Check:

* missing values
* duplicate records
* duplicate SKU/date combinations
* invalid dates
* negative demand
* impossible quantities
* inconsistent SKU names
* inconsistent branch names
* inconsistent categorical values
* missing weeks
* zero-demand weeks
* extreme outliers
* sudden demand spikes
* sudden demand drops
* data gaps
* duplicate billing records

Generate a quality report:

```text
DATA QUALITY SCORE
COMPLETENESS
UNIQUENESS
VALIDITY
CONSISTENCY
TIMELINESS
```

Do not silently modify suspicious records.

Record transformations and assumptions.

---

# 6. DEMAND PROFILE ENGINE

Automatically profile every SKU.

Calculate:

```text
mean demand
median demand
standard deviation
coefficient of variation
zero-demand percentage
trend strength
seasonality strength
volatility
recent growth
historical growth
demand frequency
intermittency
```

Classify SKUs into useful demand types, for example:

```text
Smooth
Erratic
Intermittent
Lumpy
Seasonal
Trending
Seasonal + Trending
```

Do not force one classification method if another is more statistically appropriate.

Document the methodology.

The classification must influence model candidate selection.

---

# 7. BASELINE FORECASTING MODELS

Implement strong baselines:

```text
Naive
Seasonal Naive
Moving Average
Drift
```

These are mandatory.

Every advanced model must be evaluated against the baselines.

The project must be able to answer:

> "Does the sophisticated model actually outperform a simple forecasting strategy?"

---

# 8. STATISTICAL MODELS

Retain and improve existing statistical models:

```text
ARIMA
SARIMA
Exponential Smoothing / ETS
```

Do not use arbitrary fixed parameters everywhere.

Where computationally reasonable:

* perform parameter selection
* use AIC/BIC appropriately
* account for seasonality
* validate assumptions
* handle insufficient history gracefully

Never claim a model is "best" merely because it runs successfully.

---

# 9. INTERMITTENT DEMAND MODELS

Implement:

```text
Croston
SBA
TSB
```

Use them for appropriate intermittent/lumpy SKUs.

The system should automatically determine whether these models are candidates.

---

# 10. MACHINE LEARNING FORECASTING

Retain the current ML models but improve the feature engineering.

Implement, where dependencies and data volume allow:

```text
Random Forest
Gradient Boosting
XGBoost
LightGBM
```

Do not add libraries merely for appearance.

Only include a model if it can be properly validated.

---

# 11. FEATURE ENGINEERING

Build a reusable feature pipeline.

Include:

## Lag features

```text
lag_1
lag_2
lag_3
lag_4
lag_8
lag_12
lag_13
lag_26
lag_52
```

Only create a lag when enough history exists.

## Rolling features

```text
rolling_mean_4
rolling_mean_8
rolling_mean_12
rolling_std_4
rolling_std_12
rolling_min
rolling_max
```

## Trend features

```text
week-over-week growth
4-week growth
12-week growth
trend slope
```

## Calendar features

```text
week_of_year
month
quarter
year
season
```

## SKU/branch features

Use available business attributes such as:

```text
segment
star rating
tonnage
branch
SKU
```

Avoid target leakage.

Document every feature.

---

# 12. GLOBAL FORECASTING

Do not only build independent models for each SKU.

Experiment with global ML models that learn across:

```text
SKU
Branch
Segment
Tonnage
Historical demand
Lag features
Rolling statistics
Calendar
```

Compare:

```text
Local SKU Model
vs
Global Model
```

and determine performance through proper backtesting.

Do not assume global models are superior.

---

# 13. ROLLING-ORIGIN BACKTESTING

This is one of the most important requirements.

Do NOT use random train/test splits for time-series forecasting.

Implement rolling-origin / walk-forward validation.

Example:

```text
Fold 1
Train ──────────────── Test

Fold 2
Train ───────────────────── Test

Fold 3
Train ─────────────────────────── Test

Fold 4
Train ───────────────────────────────── Test
```

Support configurable:

```text
forecast horizon
number of folds
minimum training history
step size
```

The backtesting framework must work across SKUs.

---

# 14. FORECASTING METRICS

Implement:

```text
MAE
RMSE
WAPE
sMAPE
MASE
Bias
Forecast Bias %
```

Avoid using MAPE as the primary metric when demand contains zeros.

Allow metric selection through configuration.

Create a consolidated benchmark table:

```text
SKU
Branch
Model
Horizon
MAE
RMSE
WAPE
sMAPE
MASE
Bias
Training Time
```

---

# 15. AUTOMATED MODEL SELECTION

This is a core requirement.

The user should NOT have to manually choose the model every time.

Build:

```text
SKU
 ↓
Demand classification
 ↓
Candidate models
 ↓
Backtesting
 ↓
Performance scoring
 ↓
Champion model
 ↓
Final forecast
```

Example:

```text
SKU: ABC123
Branch: Chennai

Demand Type:
Seasonal + Trending

Candidate Models:
SARIMA
ETS
XGBoost
LightGBM
Seasonal Naive

Champion:
SARIMA

Reason:
Lowest WAPE across rolling-origin validation
with stable bias across folds
```

The UI must show the reasoning.

---

# 16. CHAMPION / CHALLENGER FRAMEWORK

Maintain:

```text
Champion Model
Challenger Models
```

Store:

```text
model name
version
training date
validation score
WAPE
RMSE
bias
features
status
```

Allow challenger models to replace the champion only when predefined validation criteria are satisfied.

---

# 17. ENSEMBLE FORECASTING

Implement an ensemble option.

Possible methods:

```text
simple average
weighted average
validation-performance weighting
```

Compare:

```text
Best Individual Model
vs
Ensemble
```

Use historical backtesting to determine whether ensemble forecasts genuinely improve performance.

---

# 18. HIERARCHICAL FORECASTING

Recognize the natural business hierarchy:

```text
Region
  ↓
Branch
  ↓
SKU
```

Where applicable, create forecasts at:

```text
Region level
Branch level
SKU level
```

Implement reconciliation so that:

```text
SKU forecasts
sum to Branch forecasts
and Branch forecasts
sum to Region forecasts
```

Use an appropriate reconciliation method.

The dashboard should allow users to move between levels.

---

# 19. PROBABILISTIC FORECASTING

Do not show only point forecasts.

Generate:

```text
P10
P50
P90
```

or equivalent prediction intervals.

The UI should clearly distinguish:

```text
Lower bound
Expected forecast
Upper bound
```

Where appropriate, implement conformal prediction or another statistically defensible calibration approach.

Validate interval coverage.

Do not label an interval as "confidence" when it is actually a prediction interval.

---

# 20. FORECAST EXPLAINABILITY

For ML forecasts, implement explainability.

Where appropriate use SHAP.

The dashboard should answer:

> "Why is this SKU forecast increasing/decreasing?"

Show:

```text
Forecast Drivers

Recent demand       ↑
Seasonality         ↑
Lag-4 demand        ↑
12-week trend       ↑
Recent volatility   ↓
```

Only display explanations supported by the model.

Do not fabricate causal interpretations.

Clearly distinguish:

```text
model feature importance
```

from:

```text
causal business driver
```

---

# 21. SCENARIO ANALYSIS

Build a What-If / Scenario Engine.

Support scenarios where the available data genuinely allows them.

Examples:

```text
Base Case
High Demand
Low Demand
Demand Shock
Promotion uplift
Temperature scenario
```

If external variables such as weather are not available in the current dataset, do NOT pretend they are.

Design the architecture so external drivers can be added later.

The UI should clearly distinguish:

```text
Historical evidence
Model forecast
User-defined scenario assumption
```

---

# 22. INVENTORY DECISION ENGINE

Turn forecasts into business decisions.

Implement, where business parameters are available/configurable:

```text
Safety Stock
Reorder Point
Service Level
Lead Time
Expected Demand During Lead Time
Stockout Risk
```

Use configurable assumptions:

```text
lead_time_weeks
target_service_level
holding_cost
stockout_cost
```

Never invent business parameters.

If actual values are unavailable, expose them as configurable assumptions and clearly label them.

Example:

```text
SKU: ABC123
Branch: Chennai

12-Week Forecast: 1,842

Safety Stock: 240
Reorder Point: 390
Target Service Level: 95%

Estimated Stockout Risk: 7.2%
```

---

# 23. EXECUTIVE DEMAND INTELLIGENCE COCKPIT

Create a premium executive dashboard.

It should NOT look like a generic Streamlit analytics template.

The first screen should immediately communicate:

```text
FORECAST ACCURACY
FORECAST BIAS
TOTAL FORECAST DEMAND
HIGH-RISK SKUs
STOCKOUT RISK
DEMAND GROWTH
MODEL HEALTH
```

Include:

### Demand outlook

12-week forecast.

### Demand risks

Examples:

```text
High volatility
Demand decline
Forecast uncertainty
Stockout risk
Model degradation
```

### Action queue

For example:

```text
Review 12 SKUs
Increase safety stock for 7 SKUs
Investigate demand decline for 4 SKUs
Retrain 3 models
```

These should be generated from actual calculations, not hardcoded text.

---

# 24. SKU FORECAST EXPLORER

Create a dedicated detailed SKU page.

User selects:

```text
Branch
SKU
Forecast horizon
```

Show:

```text
Historical demand
Forecast
P10
P50
P90
Seasonality
Trend
Demand profile
Champion model
Model performance
Forecast error
Model explanation
Inventory metrics
```

Include model comparison.

---

# 25. MODEL LAB

Create a dedicated Model Lab.

The user should be able to inspect:

```text
Model leaderboard
Backtest performance
Fold-by-fold performance
Prediction errors
Bias
Forecast stability
Training time
```

Example:

```text
MODEL BENCHMARK

Model             WAPE     RMSE     Bias
-----------------------------------------
Seasonal Naive    21.8%    42.3     +3.2%
ETS               18.6%    37.1     +1.8%
SARIMA            14.2%    29.8     +0.7%
XGBoost           16.1%    33.7     -2.1%
LightGBM          15.4%    31.9     -1.1%
Ensemble          13.7%    28.9     +0.4%
```

These numbers are illustrative only.

Never hardcode them.

---

# 26. MONITORING

Create a Forecast Monitoring page.

Track:

```text
Forecast vs Actual
WAPE over time
Bias over time
MAE over time
Model degradation
Data drift
Demand distribution drift
SKU mix drift
```

Create model health states:

```text
Healthy
Watch
Retrain Required
```

These states must be calculated using configurable thresholds.

---

# 27. DATA DRIFT

Implement monitoring for:

```text
Demand distribution
SKU mix
Branch mix
Zero-demand rate
Average demand
Demand volatility
Feature distributions
```

Compare recent data with the training/reference distribution.

Do not claim drift without a defined statistical or quantitative criterion.

---

# 28. MODEL REGISTRY

Create a lightweight model registry.

Record:

```text
model_id
model_name
version
SKU
branch
training_date
features
hyperparameters
validation_metrics
status
```

If MLflow is appropriate and practical, it may be introduced.

Otherwise use a robust local registry format.

Do not introduce unnecessary infrastructure solely for buzzwords.

---

# 29. CACHING AND PERFORMANCE

The dataset may contain tens of thousands of records.

Optimize:

* repeated data loading
* feature generation
* model training
* forecasting
* dashboard rendering

Use appropriate Streamlit caching.

Do not retrain expensive models unnecessarily every time a user changes a UI filter.

Implement a separation between:

```text
Training
Inference
Visualization
```

---

# 30. CONFIGURATION

Move important parameters out of hardcoded Python.

Use configuration files for:

```text
forecast horizon
backtest folds
minimum history
metrics
model parameters
seasonality
inventory assumptions
thresholds
```

Example:

```yaml
forecast:
  horizon: 12
  frequency: W

validation:
  folds: 5
  metric: WAPE

inventory:
  service_level: 0.95
  lead_time_weeks: 2
```

Never hardcode business assumptions without documenting them.

---

# 31. TESTING

Create automated tests.

At minimum test:

### Data

* schema validation
* missing values
* aggregation
* duplicate detection

### Features

* lag correctness
* rolling features
* no future leakage

### Forecasting

* model execution
* forecast horizon
* missing data handling

### Backtesting

* chronological splits
* no leakage
* metric calculations

### Pipeline

* end-to-end execution

Add assertions for impossible outputs.

For example:

```text
forecast < 0
```

should be handled according to the chosen model/business logic.

---

# 32. DATA LEAKAGE AUDIT

This is mandatory.

Perform an explicit leakage audit.

Verify:

```text
No future demand in features
No future information in training
No random train/test split
No target-derived feature leakage
No validation contamination
```

Document the result.

Create:

```text
LEAKAGE_AUDIT.md
```

---

# 33. REPRODUCIBILITY

The project should be reproducible.

Add:

```text
requirements.txt
configuration
random seeds
model versions
training metadata
```

Document:

```text
How to install
How to run
How to train
How to forecast
How to run tests
How to deploy
```

---

# 34. DOCKER / DEPLOYMENT

Where practical, add:

```text
Dockerfile
docker-compose.yml
```

Ensure Streamlit can run cleanly.

Do not break the existing deployment.

If the project is already configured for Streamlit Cloud, preserve that compatibility.

---

# 35. DOCUMENTATION

Rewrite the README as an enterprise-quality project document.

It should include:

```text
Executive Summary
Business Problem
Business Objectives
Dataset
Architecture
Data Pipeline
Demand Profiling
Forecasting Methodology
Backtesting
Model Selection
Hierarchical Forecasting
Probabilistic Forecasting
Explainability
Inventory Optimization
Monitoring
Deployment
Limitations
Future Improvements
```

Also create:

```text
ARCHITECTURE.md
FORECASTING_METHODOLOGY.md
MODEL_CARD.md
DATA_DICTIONARY.md
LEAKAGE_AUDIT.md
ASSUMPTIONS.md
```

Documentation must describe what is ACTUALLY implemented.

Never claim functionality that doesn't exist.

---

# 36. NOTEBOOKS

Create clean analytical notebooks:

```text
01_data_audit.ipynb
02_eda.ipynb
03_demand_patterns.ipynb
04_model_benchmark.ipynb
05_business_impact.ipynb
```

The notebooks should support the project scientifically.

They should not duplicate the entire production codebase.

Production logic should remain in `src/`.

---

# 37. BUSINESS IMPACT ANALYSIS

Create a business-impact module.

Measure, where data allows:

```text
forecast accuracy improvement
bias reduction
stockout-risk reduction
inventory-risk reduction
forecast coverage
SKU coverage
```

Compare:

```text
Baseline forecasting
vs
Automated forecasting
```

Do not invent monetary benefits.

If financial inputs are unavailable, present operational metrics instead.

---

# 38. UI / UX DESIGN

The dashboard should look like an **enterprise analytics product**, not a student project.

Design principles:

* clean
* premium
* minimal
* professional
* data-dense but readable
* consistent typography
* excellent spacing
* meaningful colors
* strong visual hierarchy
* no unnecessary animations
* no excessive emojis
* no decorative charts without analytical purpose

Use a consistent corporate design system.

Prioritize:

```text
Information hierarchy
Decision relevance
Readability
Professionalism
```

The dashboard should feel closer to an enterprise consulting deliverable than a generic Streamlit app.

---

# 39. REMOVE WEAK / REDUNDANT FEATURES

During the audit identify:

* redundant pages
* meaningless charts
* decorative metrics
* duplicated logic
* unnecessary dependencies
* hardcoded values
* misleading accuracy calculations
* unsupported claims
* unused imports
* dead code

Remove or refactor them.

Do not remove useful existing functionality merely for aesthetics.

---

# 40. CRITICAL FORECASTING PRINCIPLE

Do not optimize the project for the number of algorithms.

Optimize it for:

```text
Forecast reliability
Validation rigor
Business usefulness
Interpretability
Reproducibility
Maintainability
```

A simple model that wins rigorous backtesting must be allowed to beat a complex model.

The system must never artificially favor sophisticated models.

---

# 41. NO FAKE AI

Do NOT use words such as:

```text
AI-powered
Intelligent
Smart
Advanced
Enterprise-grade
Production-ready
```

unless the underlying implementation actually justifies them.

Every claim must be supported by the implementation.

---

# 42. EXECUTION STRATEGY

Implement in phases.

## PHASE 0 — AUDIT

Inspect everything.

Produce:

```text
CURRENT_ARCHITECTURE.md
```

Then identify:

```text
What works
What should remain
What must change
What should be removed
What should be added
```

---

## PHASE 1 — FOUNDATION

Implement:

```text
data pipeline
canonical SKU × branch × week dataset
validation
cleaning
demand profiling
configuration
project structure
```

Run tests.

---

## PHASE 2 — FORECASTING ENGINE

Implement:

```text
baselines
ARIMA
SARIMA
ETS
Croston
SBA
TSB
Random Forest
Gradient Boosting
XGBoost
LightGBM
```

Only retain models that execute reliably.

---

## PHASE 3 — VALIDATION

Implement:

```text
rolling-origin backtesting
WAPE
sMAPE
MASE
MAE
RMSE
Bias
```

Create model leaderboard.

---

## PHASE 4 — INTELLIGENCE

Implement:

```text
demand classification
automatic model selection
champion/challenger
ensemble
hierarchical forecasting
prediction intervals
```

---

## PHASE 5 — BUSINESS DECISION ENGINE

Implement:

```text
inventory optimization
safety stock
reorder point
service level
stockout risk
scenario analysis
```

---

## PHASE 6 — EXPLAINABILITY + MONITORING

Implement:

```text
SHAP
forecast monitoring
data drift
model drift
model registry
```

---

## PHASE 7 — DASHBOARD

Rebuild the UI around the underlying intelligence.

Pages:

```text
Executive Cockpit
Data Quality
Demand Explorer
Forecast Explorer
Model Lab
Inventory Intelligence
Scenario Simulator
Monitoring
Reports
```

---

## PHASE 8 — TESTING

Run:

```text
unit tests
integration tests
forecast leakage tests
data validation
end-to-end pipeline
```

Fix all important errors.

---

## PHASE 9 — DOCUMENTATION

Update:

```text
README
Architecture
Methodology
Model Cards
Data Dictionary
Assumptions
Leakage Audit
Deployment Guide
```

---

# 43. FINAL VALIDATION

Before declaring completion, perform a complete project audit.

Check:

```text
Does the application launch?
Does the data pipeline work?
Does every page work?
Do forecasts generate?
Does backtesting work?
Are metrics correct?
Is there leakage?
Does automatic model selection work?
Does the champion model logic work?
Do prediction intervals work?
Does inventory calculation work?
Does monitoring work?
Do exports work?
Do tests pass?
Does Docker build?
Does deployment work?
```

Fix problems instead of merely reporting them.

---

# 44. IMPORTANT SAFETY RULE FOR THE EXISTING PROJECT

Before modifying files:

Create a safe backup or use version control.

Do not overwrite the only copy of working code.

Prefer incremental refactoring.

After every major phase:

```text
RUN TESTS
RUN APPLICATION
VERIFY FUNCTIONALITY
```

---

# 45. PERFORMANCE REQUIREMENT

Do not train every model for every SKU every time the Streamlit page refreshes.

Architect the system so that:

```text
Training → persisted results/models

Inference → fast

Dashboard → visualization
```

Use caching and persistence appropriately.

---

# 46. FINAL DEMONSTRATION FLOW

The finished application should support this demonstration:

```text
OPEN APPLICATION

        ↓

EXECUTIVE COCKPIT

        ↓

Select Chennai

        ↓

View demand outlook

        ↓

Select SKU

        ↓

View demand profile

        ↓

System automatically identifies
candidate models

        ↓

View backtesting results

        ↓

Champion model selected

        ↓

View 12-week P10/P50/P90 forecast

        ↓

View model explanation

        ↓

View inventory recommendation

        ↓

Run What-If scenario

        ↓

Inspect model health

        ↓

Export executive report
```

This should feel like a complete decision-support platform.

---

# 47. IMPORTANT: USE THE ACTUAL DATA

Do not create fake datasets merely to demonstrate functionality.

Use the existing project dataset.

If a required variable is unavailable:

```text
DO NOT INVENT IT.
```

Instead:

1. identify the missing variable
2. make the component configurable
3. clearly label assumptions
4. explain what additional data would be needed

---

# 48. IMPORTANT: DON'T OVERENGINEER

The final architecture should be sophisticated but maintainable.

Do NOT introduce:

* Kubernetes
* microservices
* Kafka
* Spark
* Airflow
* complex cloud infrastructure

unless the existing dataset size and project requirements genuinely justify them.

The objective is:

> **maximum analytical sophistication with reasonable engineering complexity.**

---

# 49. FINAL OUTPUTS REQUIRED

At completion provide:

## A. Architecture summary

```text
Old Architecture
vs
New Architecture
```

## B. Files created

List them.

## C. Files modified

List them.

## D. Files removed

Explain why.

## E. Forecasting models

List every implemented model.

## F. Validation methodology

Explain the backtesting approach.

## G. Champion model logic

Explain how selection works.

## H. Business features

List:

```text
Inventory
Scenario
Risk
Explainability
Monitoring
```

## I. Test results

Report:

```text
Tests passed
Tests failed
Warnings
```

## J. Deployment instructions

Give exact commands.

## K. Remaining limitations

Be honest.

---

# 50. QUALITY BAR

The final project should satisfy this standard:

### DATA SCIENCE

Rigorous.

### FORECASTING

Statistically defensible.

### MACHINE LEARNING

Properly validated.

### SOFTWARE ENGINEERING

Modular and maintainable.

### MLOPS

Reproducible and monitorable.

### BUSINESS ANALYTICS

Action-oriented.

### UX

Executive-quality.

### DOCUMENTATION

Consulting-quality.

---

# FINAL INSTRUCTION

Do not stop after creating the architecture.

Do not stop after creating files.

Do not stop after making the dashboard look good.

**Actually implement, test, integrate, and validate the complete system.**

If an advanced feature cannot be implemented correctly because the dataset lacks required information, do not fake it. Implement the correct framework/configuration point and document the limitation.

If you discover that an existing implementation is statistically incorrect, fix it.

If you discover that an existing feature is misleading, correct it.

If you discover a better architecture, use it while preserving working functionality.

At the end, the project should be something I can present as:

> **"An end-to-end SKU-level Demand Intelligence and Forecasting Platform for multi-branch demand planning, combining statistical forecasting, machine learning, automated model selection, rigorous walk-forward validation, uncertainty quantification, hierarchical reconciliation, explainability, inventory decision support, scenario analysis, and continuous forecast monitoring."**

The goal is not to make the project look impressive.

The goal is to make it **genuinely impressive because the underlying methodology and engineering are strong.**

Start with the repository audit.
Then implement systematically.
Do not rush.
Do not skip validation.
Do not fabricate results.
Do not declare completion until the application and tests have actually been run.
