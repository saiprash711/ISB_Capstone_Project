# 🎯 Demand Forecasting Feature Guide

## Overview
The Demand Forecasting tab allows you to predict future demand for individual SKUs (Materials) using either Statistical or Machine Learning models.

## Features

### 📊 Statistical Models
These models are specifically designed for time series data and work well when you have clear temporal patterns.

1. **ARIMA (AutoRegressive Integrated Moving Average)**
   - Best for: General time series forecasting
   - Works well with: Trending data with no strong seasonality
   - Parameters: Uses order (1,1,1) for balanced performance

2. **SARIMA (Seasonal ARIMA)**
   - Best for: Data with seasonal patterns
   - Works well with: Weekly/monthly repeating patterns
   - Parameters: Includes seasonal component (1,1,1,12)

3. **Exponential Smoothing**
   - Best for: Data with trend and seasonality
   - Works well with: Smoothly varying patterns
   - Parameters: Additive trend and seasonal components

### 🧠 Machine Learning Models
These models can capture complex non-linear relationships and work with engineered features.

1. **Random Forest**
   - Best for: Robust predictions with minimal tuning
   - Works well with: Non-linear patterns, outliers
   - Features used: Time features, lags, rolling averages

2. **Gradient Boosting**
   - Best for: High accuracy predictions
   - Works well with: Complex patterns, feature interactions
   - Features used: Time features, lags, rolling averages

## How to Use

### Step 1: Filter by Branch (Sales Office)
- **Consolidated Regional Forecast**: Select `All 5 Branches (Consolidated)` to train and forecast across the entire South region.
- **Individual Branch Level**: Select any specific branch to forecast demand locally:
  - **Bangalore (`BLR`)**
  - **Chennai (`MAA`)**
  - **Cochin (`COK`)**
  - **Secunderabad (`SBD`)**
  - **Vijayawada (`SBD1`)**
- **Custom Multi-Branch Selection**: Pick any custom combination of branches (e.g. Cochin + Chennai, or Secunderabad + Vijayawada) to model clustered regional demand.
- The dashboard shows active branch volume and percentage share of regional demand.
- Expand **🏢 Branch Distribution Breakdown** to visualize how the SKU is distributed across all 5 branches with an interactive donut chart.

### Step 2: Select SKU
- Choose the Material (SKU) you want to forecast from the dropdown.
- SKU options dynamically display the total units sold in the selected branch filter.
- Use the **SKU Scope** toggle to switch between:
  - `Top 10 in Filtered Branch`: Best-selling SKUs specific to the active branch
  - `Top 10 Overall`: Best-selling SKUs across all branches
  - `All SKUs`: Browse the entire portfolio

### Step 3: Choose Model Type
- **Statistical Models**: Better for data with clear time patterns
- **Machine Learning Models**: Better for complex, non-linear patterns

### Step 4: Select Specific Model
- Pick the specific algorithm based on your data characteristics
- Refer to the descriptions above for guidance

### Step 5: Configure Parameters
- **Forecast Periods**: Number of weeks to predict (4-52 weeks)
- **Confidence Level**: Prediction confidence interval (80-99%)

### Step 6: Run Forecast
- Click "🚀 Run Forecast" to generate predictions
- View results in charts and tables labeled with the active branch
- Download forecasts as CSV including branch metadata for further analysis

## Understanding the Results

### Performance Metrics

1. **MAE (Mean Absolute Error)**
   - Average difference between predicted and actual values
   - Lower is better
   - Measured in same units as your data

2. **RMSE (Root Mean Squared Error)**
   - Similar to MAE but penalizes large errors more
   - Lower is better
   - Useful for identifying models that avoid big mistakes

3. **MAPE (Mean Absolute Percentage Error)**
   - Average percentage error
   - Lower is better
   - Easy to interpret (e.g., 10% MAPE = 10% average error)

4. **Accuracy**
   - Approximate accuracy (100% - MAPE)
   - Higher is better
   - Quick indicator of model performance

### Forecast Chart
- **Blue line**: Historical actual data
- **Red dashed line**: Predicted future values
- **Pink shaded area**: Confidence interval (uncertainty range)

### Forecast Table
Shows week-by-week predictions with:
- Date
- Forecast value (quantity)
- Lower bound (conservative estimate)
- Upper bound (optimistic estimate)
- Forecast tonnage (predicted weight)

## Best Practices

### Model Selection
1. Start with **ARIMA** for general purpose forecasting
2. Use **SARIMA** if you notice repeating seasonal patterns
3. Try **Random Forest** if statistical models don't perform well
4. Use **Gradient Boosting** for maximum accuracy

### Data Requirements
- Minimum 10 data points required
- More data = better predictions
- At least 20-30 weeks recommended for reliable forecasts

### Interpreting Confidence Intervals
- Wide intervals = more uncertainty
- Narrow intervals = more confident predictions
- Use lower bound for conservative planning
- Use upper bound for capacity planning

## Troubleshooting

### "Insufficient data" error
- Solution: Need at least 10 historical records for the selected SKU
- Try selecting a different SKU with more history

### High MAPE (>30%)
- Cause: Model struggling with data patterns
- Solution: Try different model type or check data quality

### Libraries not installed
- Error: "Required libraries not installed"
- Solution: Run `pip install -r requirements.txt`

## Technical Details

### Feature Engineering (ML Models)
The ML models use these automatically generated features:
- Time-based: day of year, week of year, month, quarter
- Lag features: Previous 4 weeks of demand
- Rolling averages: 2-week and 4-week moving averages

### Model Training
- Data is split 80/20 for training and validation
- Metrics calculated on validation set
- Final predictions use full dataset

### Confidence Intervals
- Statistical models: Calculated from model standard errors
- ML models: Approximated using prediction RMSE
- 95% confidence = 95% of actual values should fall within bounds

## Export Options
- Download forecast results as CSV
- Includes dates, predictions, bounds, and tonnage
- Can be imported into Excel or other tools

## Example Use Cases

1. **Inventory Planning**
   - Use forecast to plan stock levels
   - Lower bound = minimum stock needed
   - Upper bound = maximum stock needed

2. **Production Planning**
   - Forecast tonnage for manufacturing capacity
   - Schedule production based on predicted demand

3. **Sales Strategy**
   - Identify SKUs with growing demand
   - Plan promotions for declining SKUs

4. **Budget Allocation**
   - Allocate resources based on demand predictions
   - Plan marketing spend by SKU

---

**Need Help?** The dashboard provides contextual help tooltips throughout the interface. Hover over ℹ️ icons for additional guidance.
