# MASTER PROMPT — FINAL GAP-CLOSURE & PRODUCTION HARDENING

You are acting as a **Principal ML Engineer + Senior Time-Series Forecasting Architect + MLOps Engineer + Supply Chain Analytics Consultant**.

You are working on an existing **SKU-wise Demand Forecasting & Demand Intelligence Platform** intended for an **ISB AMPBA capstone project and Deloitte-level demonstration**.

## CRITICAL INSTRUCTION

**DO NOT REBUILD THE PROJECT FROM SCRATCH.**

The repository already contains substantial implementations for:

* data pipeline
* feature engineering
* forecasting models
* rolling-origin backtesting
* forecasting metrics
* demand classification
* model selection
* champion/challenger
* ensemble forecasting
* hierarchical forecasting
* inventory optimization
* scenario simulation
* probabilistic forecasting
* explainability
* monitoring
* drift detection
* model registry
* alert generation
* Streamlit dashboard
* tests
* documentation

Your job is to perform a **forensic implementation audit** and then **FIX ONLY THE GAPS, WEAKNESSES, FAKE/DEMO LOGIC, incomplete integrations, bugs, and production-readiness issues**.

The final result must be a **real, executable, data-driven forecasting platform**, not a visually impressive prototype containing hardcoded results.

---

# 1. FIRST: FORENSIC AUDIT

Before modifying anything:

1. Inspect the complete repository.
2. Inspect:

   * `dashboard.py`
   * `src/`
   * `tests/`
   * `config/`
   * forecasting modules
   * validation modules
   * selection modules
   * inventory modules
   * scenario modules
   * uncertainty modules
   * explainability modules
   * monitoring modules
   * hierarchy modules
   * documentation
   * requirements
   * Docker/deployment files
3. Trace actual execution paths.
4. Determine which features are:

   * fully implemented
   * partially implemented
   * implemented but not connected
   * UI-only
   * hardcoded
   * synthetic/demo
   * fallback-only
   * incorrectly calculated
   * insufficiently tested

DO NOT assume that a module existing means the feature is correctly implemented.

Verify actual execution.

---

# 2. ABSOLUTELY REMOVE SYNTHETIC / FABRICATED RESULTS

This is the highest-priority gap.

Search the entire repository for:

* hardcoded WAPE
* hardcoded RMSE
* hardcoded MAE
* hardcoded MASE
* hardcoded bias
* hardcoded rankings
* hardcoded champion models
* hardcoded stockout probabilities
* hardcoded safety stock
* hardcoded reorder points
* hardcoded forecast values
* hardcoded SKU recommendations
* hardcoded action queues
* synthetic leaderboard metrics
* fake KPI values
* demo scenario outputs
* placeholder predictions
* fake "0% leakage"
* fake model stability scores
* static executive recommendations

Especially inspect any fallback such as:

```python
if leaderboard_df.empty:
    # synthetic metrics
```

This must NOT display fabricated forecasting results.

If real model evaluation fails:

```text
FAIL LOUDLY
↓
Explain why
↓
Show insufficient-data/error state
↓
Do NOT invent numbers
```

The application must never represent synthetic values as actual business/model results.

---

# 3. REMOVE HARDCODED EXECUTIVE INTELLIGENCE

Any executive action displayed in the dashboard must originate from actual calculations.

Bad:

```text
SKU X
Stockout probability = 24.2%
Expedite 450 units
```

unless those values were actually calculated from the current dataset and model.

Correct architecture:

```text
Raw Data
   ↓
Canonical Data Mart
   ↓
SKU × Branch × Week
   ↓
Demand Profile
   ↓
Forecast
   ↓
Uncertainty
   ↓
Inventory Engine
   ↓
Risk Calculation
   ↓
Alert Engine
   ↓
Executive Action Queue
```

The executive cockpit must consume the real `AlertEngine`, `InventoryEngine`, `ForecastMonitor`, model-selection outputs, etc.

No hardcoded SKU names, percentages, quantities, or recommendations.

---

# 4. MAKE THE FORECASTING PIPELINE TRULY END-TO-END

Verify that the actual production flow is:

```text
Raw transaction data
        ↓
Data validation
        ↓
Cleaning
        ↓
Date normalization
        ↓
SKU normalization
        ↓
Branch normalization
        ↓
Weekly aggregation
        ↓
Missing-week handling
        ↓
Feature engineering
        ↓
Demand classification
        ↓
Candidate model generation
        ↓
Chronological rolling-origin backtesting
        ↓
Metric calculation
        ↓
Champion/challenger evaluation
        ↓
Model selection
        ↓
Final model fitting
        ↓
12-week forecast
        ↓
Prediction intervals
        ↓
Inventory implications
        ↓
Dashboard
```

Trace the entire path in code.

Fix broken or bypassed connections.

---

# 5. ELIMINATE RANDOM TRAIN/TEST SPLITS FOR TIME-SERIES EVALUATION

Search for forecasting evaluation using:

```python
train_test_split
```

or any random/shuffled split.

Time-series forecasting evaluation must use chronological validation.

Use:

```text
Rolling-origin / walk-forward validation
```

with:

* expanding training windows
* chronological test windows
* no future observations entering training
* configurable forecast horizon
* configurable number of folds
* configurable step size

Verify this with tests.

If `train_test_split` is only used for a legitimate non-time-series auxiliary task, document why. Otherwise remove it from forecasting evaluation.

---

# 6. STRENGTHEN THE BACKTESTING ENGINE

Backtesting must be real, reproducible, and robust.

For every SKU × Branch series:

```text
Fold 1
Train → Test

Fold 2
Train + previous observations → Test

Fold 3
Expanded Train → Test

...
```

Verify:

* no overlap
* no future leakage
* correct ordering
* minimum training length
* sufficient test length
* missing-week handling
* intermittent demand handling
* graceful failure for insufficient history

Calculate at minimum:

* WAPE
* sMAPE
* MAE
* RMSE
* MASE
* Bias
* Bias %

Also calculate fold-level statistics:

* mean
* median where useful
* standard deviation
* worst-fold performance
* stability score

Do not create arbitrary stability scores without a documented formula.

---

# 7. MAKE MODEL SELECTION REAL

Verify that the `ModelSelector` actually executes:

```text
Demand classification
        ↓
Candidate model generation
        ↓
Backtesting
        ↓
Metric aggregation
        ↓
Ranking
        ↓
Champion selection
```

Candidate models should include appropriate models such as:

### Baselines

* Naive
* Seasonal Naive
* Moving Average

### Statistical

* ARIMA
* SARIMA
* ETS

### Intermittent

* Croston
* SBA
* TSB

### Machine Learning

* Random Forest
* Gradient Boosting
* XGBoost
* LightGBM

### Ensemble

* weighted ensemble where justified

Do NOT force every model onto every SKU.

Demand classification should influence candidate generation.

For example:

```text
Smooth
→ ETS / ARIMA / ML

Seasonal
→ Seasonal Naive / SARIMA / ETS

Intermittent
→ Croston / SBA / TSB

Trending
→ ARIMA / ETS / ML

Erratic
→ robust baselines / intermittent models / ensemble
```

The final selection must be based on actual historical backtest performance.

---

# 8. FIX CHAMPION / CHALLENGER GOVERNANCE

Champion/challenger must be operational rather than decorative.

For every SKU × Branch:

```text
Champion
Challenger 1
Challenger 2
Challenger 3
```

Store:

* model name
* version
* training period
* validation period
* WAPE
* RMSE
* MASE
* Bias
* stability
* timestamp
* selection reason

Promotion rules must be deterministic and documented.

Do not automatically replace a champion merely because of a tiny random difference.

Ensure the existing promotion thresholds are actually applied.

---

# 9. FIX ENSEMBLE FORECASTING

Verify that ensemble forecasting is mathematically real.

If using weighted ensemble:

```text
Forecast =
w1 × Model1
+ w2 × Model2
+ ...
```

Ensure:

```text
weights >= 0
sum(weights) = 1
```

Weights should be based on validation performance or another documented method.

Do NOT claim "ensemble" when simply averaging arbitrary forecasts.

Test ensemble performance against individual models.

---

# 10. HIERARCHICAL FORECASTING MUST BE COHERENT

The hierarchy should support at least:

```text
Region
  ↓
Branch
  ↓
SKU
```

Verify:

```text
Region forecast
=
sum of branch forecasts
```

and:

```text
Branch forecast
=
sum of SKU forecasts
```

after reconciliation.

Validate the reconciliation method.

If using Bottom-Up, document it.

If other methods exist, ensure they actually work before exposing them.

Add coherence tests.

---

# 11. FIX PROBABILISTIC FORECASTING

Prediction intervals must be real.

Do not label deterministic confidence bands as probabilistic forecasts unless justified.

Implement/verify:

```text
P10
P50
P90
```

or equivalent:

```text
80% interval
95% interval
```

Verify:

* lower ≤ median ≤ upper
* non-negative demand
* reasonable interval width
* empirical coverage on validation data
* calibration

If conformal prediction is used, verify that the conformal methodology is actually implemented correctly.

If quantile forecasting is used, verify the quantile models and loss functions.

Display:

```text
P10
P50
P90
```

on the forecast chart.

---

# 12. FIX INVENTORY OPTIMIZATION

The inventory engine must consume the actual forecast and uncertainty.

Verify calculations for:

### Lead-time demand

```text
Lead Time Demand
```

### Safety stock

Based on:

* forecast uncertainty
* lead time
* service level

### Reorder point

```text
ROP =
Lead Time Demand + Safety Stock
```

### Stockout risk

Calculate from actual forecast distribution/uncertainty rather than arbitrary percentages.

Expose assumptions:

* lead time
* service level
* unit cost
* demand variability

Avoid pretending that unknown business inputs are known.

If a business input is unavailable, expose it as configurable.

---

# 13. FIX SCENARIO SIMULATION

Scenario simulation must be driven by the actual base forecast.

Support scenarios such as:

* base case
* demand uplift
* demand decline
* seasonal surge
* supply constraint
* custom multiplier

For every scenario calculate:

```text
Demand
Forecast
Safety Stock
ROP
Stockout Risk
Inventory Requirement
Working Capital Impact
```

Do not hardcode outputs.

Show the delta relative to baseline.

Clearly label scenario assumptions as assumptions rather than historical facts.

---

# 14. FIX SHAP / EXPLAINABILITY

Verify that explainability is connected to the actual forecasting model.

For ML models:

```text
Forecast
↓
Feature contribution
↓
SHAP values
```

Show useful drivers such as:

* lag demand
* rolling mean
* rolling std
* seasonality
* month/week
* trend
* branch
* SKU attributes

Do NOT show SHAP explanations for a model that does not support them without a valid alternative explanation method.

For statistical models, provide appropriate explanations such as:

* trend
* seasonality
* recent demand
* residual behavior

Clearly distinguish:

```text
Model explanation
```

from:

```text
Business interpretation
```

---

# 15. FIX MONITORING

Monitoring must use actual forecast vs actual data.

Track:

* WAPE
* Bias
* Tracking Signal
* MAE
* forecast error
* data drift
* model drift
* forecast distribution changes

Define documented thresholds.

Monitoring should identify:

```text
Healthy
Watch
Retrain Required
```

based on actual calculations.

No hardcoded health states.

---

# 16. FIX DRIFT DETECTION

Verify actual statistical drift calculations.

Potential methods:

* PSI
* KS test
* distribution comparison
* rolling statistics
* feature drift

Do not merely compare arbitrary averages and call it "drift."

Store:

```text
metric
baseline
current
threshold
status
timestamp
```

---

# 17. FIX RETRAINING TRIGGERS

Retraining logic should be connected to monitoring.

Example:

```text
Forecast degradation
        ↓
Threshold breached
        ↓
Retrain flag
        ↓
Run candidate models
        ↓
Backtest
        ↓
Compare against champion
        ↓
Promote only if governance rule passes
```

Do not automatically promote an unvalidated model.

---

# 18. FIX MODEL REGISTRY

The registry must track:

* SKU
* Branch
* model
* model version
* training timestamp
* training range
* validation range
* metrics
* feature version
* configuration version
* status
* champion/challenger state

Make the registry persistent.

Avoid in-memory-only governance if the project claims production readiness.

---

# 19. DATA QUALITY MUST BE PRODUCTION-GRADE

Validate:

### Schema

* required columns
* data types

### Business rules

* non-negative demand
* valid branches
* valid SKU
* valid dates

### Time

* duplicate weeks
* missing weeks
* chronological ordering
* frequency consistency

### Transactions

* duplicate billing documents
* duplicate records
* impossible quantities

Generate a data-quality report.

Do not silently drop problematic data.

Log what was removed/transformed and why.

---

# 20. SKU-WISE FORECASTING MUST REALLY BE SKU-WISE

Ensure forecasts are generated at:

```text
SKU × Branch × Week
```

not accidentally:

```text
SKU only
```

or:

```text
Regional aggregate
```

unless explicitly requested.

The fallback behavior for insufficient SKU × Branch history must NOT silently replace the requested series with a regional aggregate and present that forecast as the SKU × Branch forecast.

Instead:

```text
Insufficient history
↓
Flag series
↓
Apply documented fallback model
OR
aggregate only if explicitly configured
↓
Clearly label fallback
```

---

# 21. FIX DASHBOARD ARCHITECTURE

The dashboard should be a presentation layer.

Avoid putting substantial forecasting business logic directly inside `dashboard.py`.

Prefer:

```text
dashboard.py
      ↓
service/orchestration layer
      ↓
domain modules
```

The dashboard should call real services rather than calculate business results itself.

Remove duplicated implementations.

Remove obsolete forecasting code.

Remove dead imports.

Remove unused functions.

---

# 22. DASHBOARD MUST SHOW REAL-TIME DATA FROM THE PIPELINE

Every KPI must be generated from current data.

Examples:

```text
Total SKUs
Forecast horizon
Champion accuracy
Average WAPE
Stockout-risk SKUs
Forecast bias
Models deployed
Drift alerts
```

No static numbers.

---

# 23. EXECUTIVE COCKPIT

Build the executive experience around decisions, not just charts.

Show:

### Demand outlook

* next 4 weeks
* next 8 weeks
* next 12 weeks

### Forecast accuracy

* WAPE
* Bias
* MASE

### Risk

* stockout risk
* excess inventory risk
* demand surge

### Model health

* champion model
* challenger
* drift
* retraining status

### Actions

Generate actions dynamically.

Every action must have:

```text
Priority
SKU
Branch
Reason
Metric
Recommended action
```

---

# 24. MODEL LAB

The Model Lab must contain ONLY real backtest results.

Show:

* candidate models
* mean WAPE
* WAPE dispersion
* RMSE
* MASE
* Bias
* stability
* champion
* challengers
* fold-by-fold results

Allow the user to select:

```text
Branch
SKU
Number of folds
Forecast horizon
```

But ensure every displayed number is generated from actual execution.

If execution fails:

```text
Show error / insufficient data
```

Never show fake benchmark numbers.

---

# 25. TEST SUITE

Run the complete test suite.

At minimum test:

### Data

* ingestion
* schema
* cleaning
* aggregation
* missing weeks
* duplicate detection

### Forecasting

* each model
* edge cases
* zero demand
* constant demand
* short series
* intermittent demand

### Backtesting

* chronological ordering
* no overlap
* leakage prevention
* fold generation

### Metrics

* WAPE
* sMAPE
* MAE
* RMSE
* MASE
* Bias

### Model selection

* demand classification
* candidate selection
* champion selection
* challenger logic

### Ensemble

* weights
* normalization
* output

### Hierarchy

* aggregation
* reconciliation
* coherence

### Inventory

* safety stock
* ROP
* stockout risk

### Probabilistic forecasts

* quantile ordering
* interval validity
* coverage

### Monitoring

* drift
* forecast degradation
* retraining trigger

### Scenarios

* multiplier
* downstream inventory effects

---

# 26. ADD INTEGRATION TESTS

This is mandatory.

Create tests that execute:

```text
Raw data
→ pipeline
→ feature engineering
→ demand classification
→ model selection
→ backtesting
→ champion
→ forecast
→ uncertainty
→ inventory
→ scenario
→ monitoring
```

using a small synthetic dataset.

The goal is to prove the architecture works as one system.

---

# 27. ADD DATA-LEAKAGE AUDIT

Create an explicit leakage audit.

Check:

* future target values
* future rolling features
* future lag features
* future aggregate information
* random train/test splitting
* scaling using future data
* feature engineering before split
* target leakage

The application must not claim:

```text
0% leakage
```

unless a real audit has actually been executed.

Instead generate a real audit report.

---

# 28. PERFORMANCE

The dataset can contain tens of thousands of transaction records and many SKU × Branch combinations.

Do not repeatedly retrain every model unnecessarily.

Implement:

* caching
* reusable aggregated data
* efficient grouping
* controlled candidate models
* configurable backtesting
* parallelism only where safe
* logging of execution time

The dashboard must remain usable.

---

# 29. CONFIGURATION

Move important assumptions into configuration:

```yaml
forecast:
  horizon: 12

backtesting:
  folds: 4
  test_weeks: 4
  min_train_weeks: 24

inventory:
  service_level: 0.95
  lead_time_weeks: 2

governance:
  min_wape_lift: 3.0
  max_bias_tolerance: 15.0
```

Do not scatter magic numbers throughout the code.

---

# 30. ERROR HANDLING

Never silently fall back to fake results.

Use explicit states:

```text
SUCCESS
INSUFFICIENT_DATA
MODEL_FAILURE
DATA_QUALITY_FAILURE
CONFIGURATION_ERROR
```

Log meaningful errors.

The dashboard should explain failures to the user.

---

# 31. DOCUMENTATION

Update documentation to accurately describe the FINAL system.

Create/update:

```text
README.md
ARCHITECTURE.md
DATA_DICTIONARY.md
FORECASTING_METHODOLOGY.md
MODEL_CARDS.md
ASSUMPTIONS_AND_LIMITATIONS.md
MODEL_GOVERNANCE.md
MONITORING.md
```

Documentation must describe what the code ACTUALLY does.

Do not document features that are not implemented.

---

# 32. MODEL CARDS

Create a model card for each model family:

```text
Model
Purpose
Input
Assumptions
Strengths
Weaknesses
When used
Validation method
Metrics
Known limitations
```

Include intermittent-demand models separately.

---

# 33. REPRODUCIBILITY

Ensure:

* deterministic random seeds where applicable
* configuration captured
* model version captured
* feature version captured
* training period recorded
* validation period recorded

A Deloitte reviewer should be able to understand:

```text
Why was this model selected?
```

and reproduce the decision.

---

# 34. DO NOT OVERENGINEER

Do not introduce unnecessary:

* microservices
* databases
* Kubernetes
* cloud infrastructure
* complex distributed systems

unless the current repository genuinely requires them.

This is an analytics/forecasting platform, not a production SaaS product.

Prioritize:

```text
Correctness
+
Statistical rigor
+
Business usefulness
+
Reproducibility
+
Explainability
+
Clean architecture
```

---

# 35. FINAL FORENSIC SEARCH

After implementation, search the entire repository again for:

```text
TODO
FIXME
pass
NotImplemented
synthetic
mock
demo
placeholder
hardcoded
random
train_test_split
fake
sample
fallback
```

Review every result.

Remove or fix anything that could cause the system to present simulated results as actual forecasting results.

---

# 36. FINAL VALIDATION

Run:

```bash
pytest -q
```

Then run the actual application.

Verify:

```bash
streamlit run dashboard.py
```

Perform an end-to-end test using the actual dataset.

Select multiple:

* branches
* SKUs
* demand profiles

Verify that the numbers change according to the selected data.

Verify that:

```text
forecast
↓
metrics
↓
champion
↓
intervals
↓
inventory
↓
scenario
↓
monitoring
↓
executive actions
```

all update from the same underlying computation.

---

# 37. FINAL ACCEPTANCE CRITERIA

Do NOT declare completion merely because files exist.

The project is complete only when:

### DATA

* [ ] Real data pipeline works
* [ ] SKU × Branch × Week grain is correct
* [ ] Data quality checks work
* [ ] Missing periods are handled correctly

### FORECASTING

* [ ] Baselines work
* [ ] Statistical models work
* [ ] Intermittent models work
* [ ] ML models work
* [ ] Ensemble works
* [ ] Demand classification works
* [ ] Automatic model selection works

### VALIDATION

* [ ] Rolling-origin validation works
* [ ] No random forecasting split
* [ ] No leakage
* [ ] WAPE works
* [ ] sMAPE works
* [ ] MAE works
* [ ] RMSE works
* [ ] MASE works
* [ ] Bias works
* [ ] Stability is calculated honestly

### GOVERNANCE

* [ ] Champion/challenger works
* [ ] Promotion rules work
* [ ] Model registry works
* [ ] Model versioning works

### UNCERTAINTY

* [ ] P10 works
* [ ] P50 works
* [ ] P90 works
* [ ] Intervals are validated
* [ ] No fake confidence intervals

### INVENTORY

* [ ] Lead-time demand
* [ ] Safety stock
* [ ] Reorder point
* [ ] Stockout probability
* [ ] Service-level configuration

### BUSINESS INTELLIGENCE

* [ ] Scenario simulator works
* [ ] Working capital impact is calculated
* [ ] Executive action queue is dynamic
* [ ] No hardcoded recommendations

### MONITORING

* [ ] Forecast monitoring works
* [ ] Data drift works
* [ ] Model drift works
* [ ] Retraining triggers work
* [ ] Health status is calculated

### EXPLAINABILITY

* [ ] SHAP/valid explanation works
* [ ] Explanations correspond to actual model
* [ ] No fabricated feature importance

### HIERARCHY

* [ ] SKU → Branch → Region
* [ ] Reconciliation works
* [ ] Forecasts remain coherent

### QUALITY

* [ ] Full test suite passes
* [ ] Integration tests pass
* [ ] Actual dataset tested
* [ ] No synthetic production results
* [ ] No misleading hardcoded KPIs
* [ ] No silent failures
* [ ] Documentation matches implementation

---

# 38. MOST IMPORTANT RULE

If a feature is not actually working, **DO NOT FAKE IT**.

Do this:

```text
Feature incomplete
       ↓
Fix it
       ↓
If impossible within current architecture
       ↓
Disable it
       ↓
Clearly document limitation
```

Never do:

```text
Feature incomplete
       ↓
Generate believable numbers
       ↓
Display them as real
```

---

# 39. FINAL REPORT

When everything is finished, provide a concise engineering report containing:

## A. Fixed gaps

List every gap discovered and fixed.

## B. Remaining limitations

Only genuine limitations.

## C. Files modified

List every modified/new file.

## D. Tests

Show:

```text
Total tests
Passed
Failed
Skipped
```

## E. End-to-end validation

Confirm whether the actual dataset successfully passed through:

```text
Data → Forecast → Validation → Selection → Uncertainty → Inventory → Scenario → Monitoring → Dashboard
```

## F. Synthetic/hardcoded audit

Explicitly state whether any fabricated forecasting/business results remain.

Target:

```text
ZERO
```

## G. Production-readiness assessment

Provide evidence-based status:

```text
DATA PIPELINE
FORECASTING
VALIDATION
MODEL GOVERNANCE
INVENTORY
UNCERTAINTY
MONITORING
EXPLAINABILITY
DASHBOARD
TESTING
DOCUMENTATION
```

Do not inflate the assessment.

---

# FINAL COMMAND

**START NOW.**

Do not ask me to manually identify the gaps.

You have the repository.

Inspect it yourself.

Implement the fixes directly.

Preserve all working functionality.

Do not rebuild working modules.

Do not introduce fake results.

Do not stop after creating files.

Trace the actual execution paths.

Run the tests.

Run the application.

Test the actual dataset.

Fix errors.

Then perform a second forensic audit.

Only after all of this provide the final gap-closure report.

**The objective is not to make the project look enterprise-grade.**

**The objective is to make it genuinely defensible when a Deloitte data scientist or supply-chain analytics consultant asks:**

> "Show me exactly how this number was calculated."

Every number must have a real answer.
