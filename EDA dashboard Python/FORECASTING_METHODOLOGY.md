# Forecasting Methodology & Modeling Framework

## 1. Overview of Implemented Model Families

The platform implements 14 distinct forecasting algorithms spanning 4 core model families, ensuring rigorous candidate evaluation across diverse demand profiles:

### A. Baseline Forecasters (Mandatory Benchmarks)
- **Naive (Random Walk)**: Repeats the most recently observed weekly demand value ($\hat{y}_{t+h} = y_t$).
- **Seasonal Naive**: Projects the value observed exactly 52 weeks prior ($\hat{y}_{t+h} = y_{t+h-52}$), benchmarking seasonality.
- **Moving Average (SMA)**: Rolling mean of the preceding 4 weeks.
- **Simple Exponential Smoothing (SES)**: Level smoothing with configurable attenuation ($\alpha = 0.3$).

### B. Statistical & Econometric Models
- **ARIMA $(p, d, q)$**: Auto-order selection via Akaike Information Criterion (AIC) or fixed parameter specification.
- **SARIMA $(p, d, q)(P, D, Q)_s$**: Seasonal autoregressive integrated moving average with 12/52-week seasonal orders.
- **Exponential Smoothing (ETS)**: State-space formulation supporting additive error, trend, and seasonal components.

### C. Intermittent & Lumpy Demand Models
- **Croston's Method**: Decomposes intermittent series into demand level $z_t$ and inter-arrival interval $p_t$ ($\hat{y} = z / p$).
- **Syntetos-Boylan Approximation (SBA)**: Deflates Croston's forecast by $(1 - \alpha / 2)$ to eliminate over-forecasting bias.
- **Teunter-Syntetos-Babai (TSB)**: Updates demand probability $\beta_t$ at every period, handling product obsolescence.

### D. Machine Learning Regression Models
- **Random Forest Regressor**: 100 orthogonal trees across 40+ multi-resolution lags and rolling statistics.
- **Gradient Boosting Regressor**: Sequentially penalized boosted trees minimizing mean squared error.
- **XGBoost**: Regularized gradient boosting with L1/L2 shrinkage.
- **LightGBM**: Fast leaf-wise histogram tree boosting.

### E. Ensemble Strategies
- **Inverse-WAPE Weighted Ensemble**: Allocates weights inversely proportional to walk-forward validation error:
  $$w_i = \frac{1 / (\text{WAPE}_i + \epsilon)}{\sum_j 1 / (\text{WAPE}_j + \epsilon)}$$
- **Median Ensemble**: Outlier-resilient consensus forecast.

---

## 2. Demand Profiling & Categorization (Syntetos-Boylan)

Every SKU is dynamically profiled across two statistical dimensions:
1. **Average Demand Interval (ADI)**: Average number of periods between non-zero order arrivals:
   $$\text{ADI} = \frac{N}{N_{\text{non-zero}}}$$
2. **Squared Coefficient of Variation ($CV^2$)**: Relative dispersion of non-zero quantities:
   $$CV^2 = \left(\frac{\sigma_{\text{non-zero}}}{\mu_{\text{non-zero}}}\right)^2$$

### Quadrant Rules:
- **Smooth**: $\text{ADI} < 1.32, CV^2 < 0.49 \implies$ ARIMA, ETS, ML
- **Erratic**: $\text{ADI} < 1.32, CV^2 \ge 0.49 \implies$ Random Forest, Smoothing
- **Intermittent**: $\text{ADI} \ge 1.32, CV^2 < 0.49 \implies$ Croston, SBA
- **Lumpy**: $\text{ADI} \ge 1.32, CV^2 \ge 0.49 \implies$ TSB, SBA

---

## 3. Rolling-Origin Backtesting Framework

Validation strictly enforces **chronological walk-forward expanding folds** without future leakage:

```
Fold 1:  [ Train: W01 - W26 ] ───────> [ Test: W27 - W30 ]
Fold 2:  [ Train: W01 - W30 ] ─────────────> [ Test: W31 - W34 ]
Fold 3:  [ Train: W01 - W34 ] ───────────────────> [ Test: W35 - W38 ]
Fold 4:  [ Train: W01 - W38 ] ─────────────────────────> [ Test: W39 - W42 ]
```

### Metrics Computed:
- **WAPE**: $\frac{\sum |y - \hat{y}|}{\sum y} \times 100$
- **sMAPE**: $\frac{100\%}{n} \sum \frac{2|y - \hat{y}|}{|y| + |\hat{y}|}$
- **MASE**: Scaled relative to in-sample naive difference.
- **RMSE & MAE**: Quadratic and linear error penalties.
- **Bias %**: Directional over/under forecasting percentage.

---

## 4. Hierarchical Reconciliation

Multi-echelon reconciliation enforces coherency across:
$$\text{South Region} \longrightarrow \text{Branches (BLR, MAA, COK, SBD, SBD1)} \longrightarrow \text{SKUs}$$

Mathematical coherency guarantees:
$$\sum_{\text{SKU} \in \text{Branch}} \hat{y}_{\text{SKU}} = \hat{y}_{\text{Branch}} \quad \text{and} \quad \sum_{\text{Branch}} \hat{y}_{\text{Branch}} = \hat{y}_{\text{Region}}$$
Both **Bottom-Up (BU)** summation and **Top-Down (TD)** historical share disaggregation are supported.
