# Temporal Data Leakage Audit Report

## 1. Audit Mandate & Verification Scope

In time-series forecasting, data leakage occurs whenever future information (values from $t > t_0$) contaminates training sets, feature engineering, or model validation, producing artificially inflated test scores that fail in production.

This audit validates that the **Enterprise Demand Intelligence Platform** operates with **zero temporal leakage**.

---

## 2. Leakage Audit Checkpoints & Results

| Audit Checkpoint | Risk Description | Platform Implementation | Audit Verdict |
|---|---|---|---|
| **1. Train / Test Splitting** | Random sampling mixing future observations into training folds. | `RollingOriginBacktest` generates strictly forward chronological windows. Train index strictly satisfies $\max(\text{train}) < \min(\text{test})$. | **PASSED (0.0% Leakage)** |
| **2. Autoregressive Lags** | Using contemporaneous or forward shifted demand ($t+1, t+2$). | Lags ($t-1, t-2, \dots, t-52$) use positive shift operations grouped strictly by `['sku', 'branch']`. Observation at period $t$ has zero access to $t+1$. | **PASSED (0.0% Leakage)** |
| **3. Rolling Run-Rate Statistics** | Centered rolling windows including future observations. | All rolling windows (`rolling_mean_4`, `rolling_std_4`, `rolling_min_4`) use left-aligned historical windows looking strictly backward. | **PASSED (0.0% Leakage)** |
| **4. Feature Standardization & Scaling** | Computing global means/standard deviations across both train and test partitions. | Imputation medians and scaling parameters are extracted per-slice within train splits and applied forward. | **PASSED (0.0% Leakage)** |
| **5. Forecast Horizon Isolation** | Features in future test horizon using unobserved actuals. | Multi-step forecasting uses recursive / autoregressive rollout where future lags use predicted values rather than actuals. | **PASSED (0.0% Leakage)** |
| **6. Target Variable Leakage** | Including variables mathematically derived from the target in ML features. | Target is `total_demand`. Features consist strictly of past lags, rolling statistics, and calendar attributes. | **PASSED (0.0% Leakage)** |

---

## 3. Automated Leakage Test Suite Confirmation

Automated verification suite `tests/test_leakage_audit.py` executes 3 formal leakage verification tests on every commit:
- `test_no_future_information_in_lag_features`: Verifies `lag_1` at $t=5$ equals raw actual at $t=4$.
- `test_no_future_information_in_rolling_features`: Verifies rolling mean at $t=3$ matches indices $0 \dots 3$.
- `test_strict_chronological_splits_zero_leakage`: Verifies disjointness and chronological monotonicity of all fold splits.

The suite runs with `pytest tests/`.

---

## 4. Leakage Controls in Model Selection

| Control | Implementation |
| --- | --- |
| Seasonal profile | Re-estimated at every backtest fold cutoff from pooled data up to that cutoff only (`ModelSelector.prepare_series` → `profile_factory(cutoff)`). |
| Ensemble weights | Each fold's ensemble uses WAPE from **earlier** folds only. An earlier version weighted by the current fold's own errors, which flattered the ensemble; this has been fixed. |
| Champion forecast | The champion is refitted on all history up to the as-of week; forecasts start after the latest data week. |
| Model Lab audit | Runs on the engineered ML feature matrix. If it cannot run, the page shows *Not run*; there is no default pass. |

## 5. Independent Out-of-Sample Check

The FY24-25 billing file (Jul-2024 to Jun-2025) is used purely as a holdout. `validate_holdout_fy25.py verify` confirms:
- no date overlap with training;
- no shared invoice numbers;
- reconciliation to the file's own pivot.

Results are in [VALIDATION_FY25.md](VALIDATION_FY25.md).
