# Model Card: SKU × Branch Weekly Demand Forecasting Engine

## Intended use

- **Output:** 1–52 week forecasts of billed outdoor-unit (ODU) quantity for room air conditioners, per SKU × branch (BLR, COK, MAA, SBD, SBD1), for a set of branches, or for the South region. Each forecast comes with a calibrated prediction interval.
- **Planning use:** inventory parameters (lead-time demand, safety stock, reorder point) and monitoring.
- **Not intended for:**
  - Forecasting SKUs with fewer than 5 weeks of sales.
  - Anticipating launches, discontinuations, price changes or promotions, which are absent from the data.

## Training data

- **Source:** SAP billing extract, 16-Jul-2022 to 30-Jun-2024: 80,299 real rows, 70 ODU SKUs, 5 branches.
- **Excluded:**
  - 5,100 synthetic `EVAL-*` rows.
  - Return and credit-memo rows.
  - IDU rows from pooled statistics, because they exist for Apr–Jun 2024 only.
- **Grain:** weekly (W-MON) SKU × branch series, zero-filled to the latest data week.

## Model

There is no single global model. Per series, an out-of-sample tournament selects a champion from up to 17 candidates:

- naive and seasonal baselines;
- the pooled **Seasonal Index** (two level windows);
- ARIMA, seasonal ARIMA and ETS;
- Croston, SBA and TSB;
- RF, GBM, XGBoost and LightGBM;
- an inverse-WAPE ensemble.

Details are in [FORECASTING_METHODOLOGY.md](FORECASTING_METHODOLOGY.md).

| Item | Setting |
| --- | --- |
| Seasonality | Pooled region/branch month index × month-end factor, re-estimated at every fold cutoff |
| Selection | 4 rolling-origin folds × 12 weeks; lowest mean RMSE |
| Accuracy KPI | WAPE (accuracy = 100% − WAPE, floored at 0) |
| Intervals | Split-conformal on level-scaled backtest residuals (default 80%) |

## Evaluation

Holdout: FY24-25 billing (Jul-2024 to Jun-2025), which was never used for training or design decisions. Results, including the before/after comparison with the original engine, are in [VALIDATION_FY25.md](VALIDATION_FY25.md) and on the dashboard page *AI Demand Forecasting → Holdout Validation (FY24-25)*.

## Limitations and risks

- **Product lifecycle.** In FY24-25, new launches replaced older SKUs. A forecast made from an old SKU's history overshoots when that SKU is being phased out. Re-forecasting monthly, as in the rolling evaluation, limits this but cannot remove it.
- **Weekly granularity.** Weekly SKU × branch demand is very lumpy (bulk dealer orders), and weekly errors are large at that grain. Aggregate to month or branch for planning decisions.
- **Interval assumptions.** Interval coverage assumes future errors resemble the backtest errors. A structural break, such as a weak or early season, widens real errors beyond the band.
