# Model Cards: Forecasting Model Portfolio

## 1. Portfolio Summary

| Model Family | Algorithms Implemented | Primary Data Suitability |
|---|---|---|
| **Baselines** | Naive, Seasonal Naive, Moving Average, Exponential Smoothing | Benchmark, short history (<12W), cold-start SKUs |
| **Statistical** | ARIMA $(p,d,q)$, SARIMA $(p,d,q)(P,D,Q)_{12}$, ETS | Smooth demand, quarterly/annual seasonality, econometric confidence |
| **Intermittent** | Croston's Method, SBA, TSB | Sporadic demand (>30% zeros), spare parts, low-velocity RAC models |
| **Machine Learning** | Random Forest, Gradient Boosting, XGBoost, LightGBM | High-volume SKUs (>30W history), complex non-linear lag interactions |
| **Ensemble** | Inverse-WAPE Weighted Consensus, Median Consensus | Critical high-capital SKUs benefiting from cross-architecture diversity |

---

## 2. Model Specifications

### Model: SARIMAX Seasonal Econometric Forecaster
- **Input Variables**: Weekly aggregated univariate demand series (`Billing Quantity ODU`).
- **Seasonal Periodicity**: $s = 12$ (Quarterly) or $s = 52$ (Annual HVAC summer cycle).
- **Hyperparameters**: Non-seasonal $(1, 1, 1)$, Seasonal $(0, 1, 1)_{12}$.
- **Uncertainty Quantification**: Exact state-space Gaussian Kalman filter confidence intervals.
- **Intended Use**: Seasonal RAC cooling demand exhibiting regular summer pulses.
- **Limitations**: Requires $\ge 24$ weeks of continuous historical billing records.

### Model: Random Forest Regressor (ML Ensemble)
- **Input Features**: 40+ features (Lags 1, 2, 3, 4, 8, 12, 26; Rolling Means 4W, 8W, 12W; Rolling Volatility; Cyclical Sine/Cosine Calendar Harmonics; Festival Flags; Branch Encoding).
- **Architecture**: 100 decision trees, max depth 15, minimum samples split 5.
- **Explainability**: Gini impurity feature importance ranking & Waterfall decomposition.
- **Intended Use**: High-volume, erratic, or promotional SKUs with complex non-linear patterns.
- **Limitations**: Tree ensembles cannot extrapolate linear trends beyond historical maximums without trend de-trending.

### Model: Syntetos-Boylan Approximation (SBA)
- **Input Variables**: Intermittent order quantities and inter-arrival intervals.
- **Deflation Factor**: $(1 - \alpha / 2)$ applied to Croston rate.
- **Smoothing Parameter**: $\alpha = 0.1$.
- **Intended Use**: Lumpy or intermittent SKUs with high zero-order frequency ($\text{ADI} \ge 1.32$).
- **Limitations**: Produces flat forward run-rate without explicit seasonality.
