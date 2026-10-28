# DATA DICTIONARY

**Project:** Demand Intelligence & Forecasting Platform  
**Date:** 2026-09-17  
**Region:** South Region (Daikin HVAC)

---

## 1. RAW DATASET STRUCTURE (Input: Filtered.csv)

### Grain
**Transaction-level** - One row per billing line item

### Size
- **Rows:** ~104,495 (99,395 real SAP billing lines + 5,100 synthetic evaluation SKUs)
- **Columns:** 24
- **Period:** 2021-04-01 to 2024-06-30 (FY21-22, FY22-23, FY23-24, FY24-25 Q1; 170 weeks)
- **Data Mart Grain:** 36,344 canonical SKU × Branch × Week observations
- **Memory:** ~18 MB

### Column Definitions

#### Identifiers & Keys
| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `Material` | String | SKU/Product Code | RKM35UV16W | Unique product identifier |
| `Billing Doc.` | Numeric | Billing document ID | 2237005921 | Transaction reference (not used in analysis) |
| `Item` | Numeric | Item line number | 20 | Line item within document |

#### Business Dimensions
| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `SALES OFFICE CODE` | Category | Branch code (South Region) | MAA, BLR, COK, SBD, SBD1 | Distribution point |
| `SBU` | Category | Strategic Business Unit | RA | Business unit (RA = Room AC) |
| `Segment` | Category | Product segment | Inverter | Market segment |
| `Star Rating` | Category | Efficiency rating | I5S, I3S | Product rating |
| `EXT MAT GROUP` | Category | Extended material group | RA-ODU, RA-IDU | Material classification |
| `MatGroup3` | Category | Material group level 3 | RA | Aggregated group |

#### Quantities & Weight
| Column | Type | Description | Range | Unit | Notes |
|--------|------|-------------|-------|------|-------|
| `Billing Quantity ODU` | Numeric | Quantity in Original Design Units | 0+ | Units | ODU (e.g., complete systems) |
| `Billing Quantity IDU` | Numeric | Quantity in Intermediate Design Units | 0+ | Units | IDU (e.g., components) |
| `Tonnage` | Numeric | Weight/tonnage | 0+ | Metric tons | Physical weight for logistics |

#### Date & Time
| Column | Type | Description | Format | Notes |
|--------|------|-------------|--------|-------|
| `Billing Date` | Date | Transaction date | DD/MM/YYYY | Actual billing date |
| `Year` | Text | Fiscal year | "22-23", "23-24" | Fiscal year label |
| `Month` | Text | Month name | "1) Jan", "12) Mar" | Month with number prefix |
| `Week` | Text | Week identifier | "Wk 1", "Wk 4" | Week within year |

#### Customer Information (Not used in forecast analysis)
| Column | Type | Description |
|--------|------|-------------|
| `Customer` | Text | Customer/dealer name |
| `Dealer Name` | Text | Dealer name |
| `Stor. Location` | Numeric | Storage location code |

#### Duplicates (Identified in Audit)
| Column | Duplicate Of | Notes |
|--------|--------------|-------|
| `Star Rating.1` | Star Rating | Exact duplicate |
| `SALES OFFICE CODE.1` | SALES OFFICE CODE | Exact duplicate |
| `Material.1` | Material | Exact duplicate |
| `Tonnage.1` | Tonnage | Exact duplicate |

---

## 2. CLEANED DATASET STRUCTURE

### After Cleaning (cleaning.py)
Changes applied:
- Duplicate columns removed (Star Rating.1, SALES OFFICE CODE.1, Material.1, Tonnage.1)
- Unnecessary columns removed (Billing Doc., Item, Stor. Location, Customer, Dealer Name, EXT MAT GROUP)
- Column names standardized to lowercase with underscores
- Categorical values standardized (branch codes uppercase, segment title case)
- Data types properly converted (dates to datetime64, quantities to float64, branches to category)

### Resulting Columns (12 columns)
| New Name | Original | Type | Notes |
|----------|----------|------|-------|
| sku | Material | string | Product code |
| branch | SALES OFFICE CODE | category | Branch code {BLR, MAA, COK, SBD, SBD1} |
| quantity_odu | Billing Quantity ODU | float64 | Original Design Unit quantity |
| quantity_idu | Billing Quantity IDU | float64 | Intermediate Design Unit quantity |
| tonnage | Tonnage | float64 | Weight in metric tons |
| date | Billing Date | datetime64 | Transaction date |
| year | Year | string | Fiscal year label |
| month | Month | string | Month name |
| week | Week | string | Week identifier |
| segment | Segment | string | Product segment |
| star_rating | Star Rating | category | Efficiency rating |
| material_group | MatGroup3 | category | Material group |
| sbu | SBU | category | Business unit |

---

## 3. CANONICAL DATA MART STRUCTURE (Output: transformation.py)

### Grain
**SKU × BRANCH × WEEK** - Aggregated to time-series format

### Creation Process
1. Parse billing dates to datetime format
2. Extract ISO week (YYYY-W##) from dates
3. Group by (sku, branch, iso_week)
4. Aggregate quantities and tonnage using SUM
5. Retain first non-null values for categorical columns

### Resulting Columns (15 columns)

#### Time Identifiers
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `iso_week` | string | ISO week (YYYY-W##) | 2023-W01, 2023-W52 |
| `date` | datetime | Latest date in week | 2023-01-08 |
| `year_actual` | int | ISO year | 2023 |
| `week_actual` | int | ISO week number | 1-52 |
| `month_actual` | int | Month (1-12) | 1, 12 |
| `quarter_actual` | int | Quarter (1-4) | 1, 4 |

#### Business Keys
| Column | Type | Description | Values |
|--------|------|-------------|--------|
| `sku` | string | Product code | RKM35UV16W, ... |
| `branch` | category | Branch code | {BLR, MAA, COK, SBD, SBD1} |

#### Aggregated Metrics
| Column | Type | Description | Unit |
|--------|------|-------------|------|
| `quantity_odu` | float64 | Total ODU quantity in week | Units |
| `quantity_idu` | float64 | Total IDU quantity in week | Units |
| `total_demand` | float64 | Combined demand (ODU + IDU) | Units |
| `tonnage` | float64 | Total tonnage in week | Metric tons |

#### Business Attributes
| Column | Type | Description |
|--------|------|-------------|
| `segment` | string | Product segment |
| `star_rating` | category | Efficiency rating |
| `material_group` | category | Material classification |
| `sbu` | category | Business unit |

### Dimensions
- **Unique SKUs:** ~500-1000 (actual: check raw data)
- **Unique Branches:** 5 (BLR, MAA, COK, SBD, SBD1)
- **Unique Weeks:** ~100-120 (2+ years of data)
- **Total Rows:** ~50,000-100,000 (SKU × BRANCH × WEEK combinations)

---

## 4. FEATURES LAYER STRUCTURE (features.py - To be implemented)

### Calendar Features
| Feature | Type | Description |
|---------|------|-------------|
| `week_of_year` | int | Week number (1-52) |
| `month_of_year` | int | Month number (1-12) |
| `quarter` | int | Quarter (1-4) |
| `day_of_week` | int | Day of week (0=Monday, 6=Sunday) |
| `is_quarter_end` | bool | Is week in quarter-end period |
| `is_year_end` | bool | Is week in year-end period |

### Lag Features
| Feature | Type | Description | Note |
|---------|------|-------------|------|
| `lag_1` | float | Demand 1 week ago | Created if history ≥ 1 week |
| `lag_2` | float | Demand 2 weeks ago | Created if history ≥ 2 weeks |
| `lag_3` | float | Demand 3 weeks ago | Created if history ≥ 3 weeks |
| `lag_4` | float | Demand 4 weeks ago | Created if history ≥ 4 weeks |
| `lag_8` | float | Demand 8 weeks ago | Created if history ≥ 8 weeks |
| `lag_12` | float | Demand 12 weeks ago | Created if history ≥ 12 weeks |
| ... | ... | ... | ... |

### Rolling Features
| Feature | Type | Description |
|---------|------|-------------|
| `rolling_mean_4` | float | 4-week moving average |
| `rolling_mean_8` | float | 8-week moving average |
| `rolling_mean_12` | float | 12-week moving average |
| `rolling_std_4` | float | 4-week moving std dev |
| `rolling_std_12` | float | 12-week moving std dev |
| `rolling_min_4` | float | 4-week minimum |
| `rolling_max_4` | float | 4-week maximum |

### Trend Features
| Feature | Type | Description |
|---------|------|-------------|
| `wow_growth` | float | Week-over-week growth rate |
| `growth_4w` | float | 4-week growth rate |
| `growth_12w` | float | 12-week growth rate |
| `trend_slope` | float | Linear trend slope |

### Business Features
| Feature | Type | Description |
|---------|------|-------------|
| `segment` | category | Product segment |
| `star_rating` | category | Efficiency rating |
| `material_group` | category | Material group |
| `branch` | category | Branch code |

---

## 5. DEMAND PROFILE STRUCTURE (To be implemented)

### Profile Metrics (Per SKU × Branch)
| Metric | Type | Description | Note |
|--------|------|-------------|------|
| `mean_demand` | float | Average demand | Basis for scaling |
| `median_demand` | float | Median demand | Robust center |
| `std_demand` | float | Demand std deviation | Variability measure |
| `cv_demand` | float | Coefficient of variation | Normalized variability |
| `zero_demand_pct` | float | % of zero-demand weeks | Intermittency indicator |
| `trend_strength` | float | 0-1 strength of trend | For trend detection |
| `seasonality_strength` | float | 0-1 strength of seasonality | For seasonal detection |
| `volatility` | float | Rolling variance | Recent variability |
| `recent_growth` | float | Last 4 weeks trend | Growth indicator |
| `historical_growth` | float | 52-week trend | Long-term trend |

### Demand Classification (Per SKU × Branch)
```
Smooth            → Low CV, low zero%, trending possible
Seasonal          → High seasonality strength
Intermittent      → High zero demand %
Lumpy             → High CV + zero demand %
Erratic           → High volatility
Seasonal+Trending → Seasonal + trend present
```

---

## 6. FORECASTING OUTPUT STRUCTURE (To be implemented)

### Forecast Columns (Per SKU × Branch × Horizon)
| Column | Type | Description |
|--------|------|-------------|
| `forecast_week` | datetime | Week being forecasted |
| `forecast_value` | float | Point forecast |
| `forecast_p10` | float | 10th percentile (lower bound) |
| `forecast_p50` | float | 50th percentile (median) |
| `forecast_p90` | float | 90th percentile (upper bound) |
| `forecast_model` | string | Model used (SARIMA, XGBoost, etc.) |
| `forecast_confidence` | float | Confidence score (0-1) |
| `forecast_error` | float | MAE from validation |
| `forecast_bias` | float | Bias from validation |

---

## 7. DATA QUALITY METRICS

### Overall Quality Score (0-1)
```
Score = 1.0 - (0.1 × errors + 0.03 × warnings)
```

### Quality Dimensions
| Dimension | Checks |
|-----------|--------|
| **Completeness** | Missing values per column |
| **Uniqueness** | Duplicate rows, key duplicates |
| **Validity** | Invalid dates, negative values, impossible values |
| **Consistency** | Invalid branch codes, inconsistent categories |
| **Timeliness** | Data freshness, gaps in time series |
| **Accuracy** | Quantity-tonnage relationship, zero demand patterns |

---

## 8. SUMMARY TABLE

| Aspect | Raw Data | Cleaned Data | Data Mart |
|--------|----------|--------------|-----------|
| Grain | Transaction | Transaction | SKU × BRANCH × WEEK |
| Rows | 82,034 | ~80,000 | ~50,000-100,000 |
| Columns | 23 | 13 | 15 |
| Duplicates | Yes | None | None |
| Date Format | DD/MM/YYYY text | datetime64 | datetime64 + iso_week |
| Quantities | Individual units | Individual units | Aggregated per week |
| Business Dims | All 6 | All 6 | All 6 retained |
| Ready for Forecasting | ❌ No | ⚠️ Partial | ✅ Yes |

---

## 9. BRANCH REFERENCE

| Code | Location | Region | Status |
|------|----------|--------|--------|
| BLR | Bangalore | South | Active |
| MAA | Chennai | South | Active |
| COK | Cochin | South | Active |
| SBD | Secunderabad | South | Active |
| SBD1 | Vijayawada | South | Active |

---

## 10. DATA GOVERNANCE

### Data Lineage
```
Source (Billing System)
    ↓
Filtered.csv (Raw Extract)
    ↓
Cleaned Data (cleaning.py)
    ↓
Data Mart (transformation.py)
    ↓
Features (features.py)
    ↓
Models & Forecasts (forecasting.py)
```

### Data Refresh
- **Frequency:** Weekly (production) / Ad-hoc (analysis)
- **Latency:** 1-2 weeks after billing period
- **Retention:** 2+ years for historical analysis

### Access Control
- **Raw data:** Read-only in Streamlit dashboard
- **Data mart:** Internal cache (Streamlit session state)
- **Forecasts:** Shared in reports and dashboard pages

### Quality Checks
- Run validation after every load
- Flag quality issues in UI
- Prevent stale data from being used

---

## 11. COMMON TRANSFORMATIONS

### Total Demand Calculation
```
Total Demand = Billing Quantity ODU + Billing Quantity IDU
```

### Aggregation (Transaction → Weekly)
```
Aggregated Field = SUM(individual_transactions)
Applied to: quantity_odu, quantity_idu, tonnage
```

### Time Boundaries
```
ISO Week Definition: Monday-Sunday
Week Identifier: YYYY-W## (e.g., 2023-W01 = Jan 2-8, 2023)
```

---

**Data Dictionary Prepared By:** AI Code Assistant  
**Last Updated:** 2026-09-17  
**Next Review:** Upon Phase 2 (when feature engineering begins)
