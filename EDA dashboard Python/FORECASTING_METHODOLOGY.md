# Forecasting Methodology

This describes the engine as implemented in `src/` (entry point `ModelSelector.select_and_fit`, used by every dashboard page through `ForecastService`). Out-of-sample results on FY24-25 are in [VALIDATION_FY25.md](VALIDATION_FY25.md).

## 1. Data and series

- **Unit of forecasting:** weekly (W-MON) billed outdoor-unit (ODU) quantity per SKU × branch, or an aggregate of branches.
- **Series window:** from the SKU's first sale to the dataset's latest week. Weeks with no billing are zeros, so a SKU that stopped selling is forecast from the latest week, not from its last sale.
- **Excluded from modelling inputs:**
  - **Synthetic SKUs.** The 10 `EVAL-*` SKUs (`Data_Sheet = Evaluation_10_SKUs`) are generated test series. The dashboard excludes them unless the user switches them on.
  - **IDU rows in pooled statistics.** The extract carries indoor-unit (IDU) rows for Apr–Jun 2024 only, so pooling them would double that quarter.

## 2. Pooled seasonal profile

Room-AC demand is strongly seasonal. In the training data, April runs at about 2–2.6× the average week and July at about 0.2–0.3×. A month-end billing push also makes the last week of a month about 1.4× the other weeks. Each SKU × branch series has only about two years of noisy weekly history, which is too little to estimate a 52-week season per series. The profile is therefore estimated from pooled demand (`src/forecasting/seasonal_profile.py`):

```text
S(week) = MonthIndex(month) × PositionFactor(last week of month or not)
MonthIndex = 0.5 × branch index + 0.5 × region index    (averaged over complete 52-week blocks, up to 3 years)
```

The profile is re-estimated **at every backtest fold cutoff using only data up to that cutoff**, so the backtest has no look-ahead. The design choices (window, branch shrinkage, month-end factor) were made on an inner validation that used training data only (origins in FY23-24), never on the FY24-25 holdout.

## 3. Candidate models (`src/forecasting/model_zoo.py`)

| Family | Model | Specification |
| --- | --- | --- |
| Baseline | Naive | Last observed week |
| Baseline | Seasonal Naive | Same week last year (requires ≥ 52 weeks) |
| Baseline | Moving Average | Mean of last 4 weeks |
| Baseline | Exponential Smoothing | SES level, α = 0.3 |
| Seasonal | **Seasonal Index** | SKU level over last 8 weeks ÷ seasonal factors × future factors |
| Seasonal | **Seasonal Index (smooth)** | Same, 26-week level window |
| Statistical | ARIMA | Non-seasonal; order by min AIC from (0,1,1), (1,1,1), (1,0,1), (1,0,0) |
| Statistical | SARIMA | ARIMA (min-AIC order) on the seasonally adjusted series, re-seasonalised |
| Statistical | ETS | Damped-trend ETS(A,Ad,N) on the seasonally adjusted series, re-seasonalised |
| Intermittent | Croston / SBA / TSB | Croston (1972); SBA ×(1 − α/2); TSB with per-period probability update (α = β = 0.1) |
| ML | Random Forest, Gradient Boosting, XGBoost, LightGBM | Lags 1–52, rolling statistics, calendar and the pooled seasonal factor; recursive multi-step |
| Ensemble | Ensemble (Consensus) | Inverse-WAPE weighted average of all candidates (weights from earlier folds only) |

- **Intermittent models** are added when more than 30% of weeks are zero.
- **ML models** need at least 20 weeks of training data in every fold.

## 4. Model selection (`src/validation/backtesting.py`, `src/selection/model_selector.py`)

- **Rolling-origin backtest:**
  - 4 folds with 12-week test windows, stepped 12 weeks apart, on an expanding window. The folds cover the most recent year, so every model is judged across the seasonal cycle and at the dashboard's 12-week horizon.
  - A model must produce a valid forecast in **every** fold to be ranked.
  - Short series get a single shortened fold, with at least 5 weeks of history and 2 billing weeks.
- **Ranking rule: lowest mean RMSE across folds.** RMSE is minimised by the mean (expected demand), which replenishment needs. WAPE/MAE is minimised by the median, which for lumpy series is often zero, so a "forecast nothing" model would win. WAPE stays the reported accuracy KPI (accuracy = 100% − WAPE, floored at 0).
- **Forward forecast:** the champion is refitted on the full history.
  - If the ensemble wins, every member is refitted and combined with weights based on backtest WAPE.
  - If the champion cannot be refitted, the next-ranked model is used, and the substitution is disclosed in `fallback_reason`.

## 5. Prediction intervals (`src/uncertainty/prediction_intervals.py`)

Split-conformal and level-scaled:

1. Take the champion's out-of-sample backtest residuals and scale each by `forecast + mean demand`.
2. Take their empirical (1−c)/2 and (1+c)/2 quantiles, with the finite-sample conformal correction.
3. Apply them to the forward forecast.

The interval therefore widens in peak season and narrows in the trough. Beyond the 12-week backtest horizon it widens further by √(h/12). With fewer than 8 residuals, a normal approximation is used and labelled as uncalibrated.

## 6. Downstream use

- **Inventory:**
  - LTD = sum of the next L weeks of forecast.
  - SS = z × √L × σ, where σ is the standard deviation of the champion's backtest residuals.
  - ROP = LTD + SS.
  - Stock-out probability needs on-hand stock, which the user enters; it isn't in the billing extract.
- **Monitoring:** the tracking signal and accuracy degradation are measured on the champion's latest out-of-sample fold, relative to its WAPE in earlier folds. PSI and KS tests check drift in weekly demand.
- **Hierarchy:** region and branch totals are forecast directly. The page compares bottom-up (sum of branches) with the direct region forecast, and shows top-down (region × branch share of the last 52 weeks). MinT reconciliation is **not** implemented.

## 7. Known limitations

- No price, promotion, weather or stock-availability data, so the engine cannot anticipate demand shocks or product substitution.
- New SKUs can be forecast only after about 5 weeks of sales. The FY24-25 holdout shows how much this matters, because new launches took volume from existing SKUs.
- About two years of history: seasonality is pooled across SKUs, not estimated per SKU.
