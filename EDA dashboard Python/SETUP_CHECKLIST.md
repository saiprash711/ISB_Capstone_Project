# 📋 Setup Checklist - Demand Forecasting Feature

## Pre-Installation Check

- [ ] Python 3.8 or higher installed
- [ ] pip package manager available
- [ ] Existing dashboard working (v1.0)
- [ ] Data file (Filtered.csv/xlsx) present

## Installation Steps

### Step 1: Install Required Libraries
```bash
pip install statsmodels scikit-learn
```

**Expected Output:**
```
Successfully installed statsmodels-X.X.X scikit-learn-X.X.X
```

- [ ] statsmodels installed successfully
- [ ] scikit-learn installed successfully
- [ ] No error messages during installation

### Step 2: Verify Installation
```bash
python verify_installation.py
```

**Expected Output:**
```
Core Libraries:
✅ Streamlit - Installed
✅ Pandas - Installed
✅ NumPy - Installed
✅ Plotly - Installed
✅ OpenPyXL - Installed
✅ FPDF - Installed

Forecasting Libraries (NEW):
✅ Statsmodels - Installed
✅ Scikit-learn - Installed

All dependencies installed! Dashboard is ready to run.
```

- [ ] All core libraries show ✅
- [ ] All forecasting libraries show ✅
- [ ] Success message displayed

### Step 3: Launch Dashboard
```bash
streamlit run dashboard.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

- [ ] Dashboard starts without errors
- [ ] Browser opens automatically or can be opened manually
- [ ] Dashboard loads successfully

## Feature Verification

### Navigation Check
- [ ] Sidebar shows 7 navigation options (was 6 before)
- [ ] "🎯 Demand Forecasting" option is visible
- [ ] Can navigate to the new tab

### UI Check
In the Demand Forecasting tab:

**Left Panel (Configuration)**
- [ ] "🎛️ Configuration" header visible
- [ ] SKU dropdown populated with materials
- [ ] "Model Selection" section present
- [ ] Radio buttons for "Statistical" vs "ML" models
- [ ] Model-specific dropdown appears
- [ ] "Parameters" section with two sliders:
  - [ ] Forecast periods (4-52 weeks)
  - [ ] Confidence level (80-99%)
- [ ] "🚀 Run Forecast" button visible and clickable

**Right Panel (Results)**
- [ ] SKU analysis header shows selected material
- [ ] Historical data metrics displayed (if not forecast yet)
- [ ] Historical trend chart shows (if not forecast yet)

### Functionality Check

**Test Case 1: Statistical Model**
1. [ ] Select any SKU from dropdown
2. [ ] Select "📊 Statistical Models"
3. [ ] Choose "ARIMA" from model dropdown
4. [ ] Set forecast periods to 12 weeks
5. [ ] Set confidence level to 95%
6. [ ] Click "Run Forecast"
7. [ ] Wait for spinner to complete

**Expected Results:**
- [ ] 4 metric cards appear (MAE, RMSE, MAPE, Accuracy)
- [ ] Interactive forecast chart displays with:
  - [ ] Blue historical line
  - [ ] Red forecast line
  - [ ] Pink confidence interval
- [ ] Forecast table shows 12 rows (one per week)
- [ ] Download button appears
- [ ] No error messages

**Test Case 2: Machine Learning Model**
1. [ ] Select same or different SKU
2. [ ] Select "🧠 Machine Learning Models"
3. [ ] Choose "Random Forest" from model dropdown
4. [ ] Set different forecast periods (e.g., 8 weeks)
5. [ ] Click "Run Forecast"

**Expected Results:**
- [ ] Model runs successfully
- [ ] Results display similar to Test Case 1
- [ ] Metrics show reasonable values
- [ ] Chart renders properly
- [ ] Table has 8 rows

**Test Case 3: Export Functionality**
1. [ ] Run any forecast
2. [ ] Click "📥 Download Forecast as CSV"
3. [ ] Check downloaded file

**Expected Results:**
- [ ] CSV file downloads
- [ ] Filename includes SKU, model, and date
- [ ] File opens in Excel or text editor
- [ ] Contains columns: Date, Forecast, Lower_Bound, Upper_Bound, Forecast_Tonnage
- [ ] Data looks reasonable

**Test Case 4: Error Handling**
1. [ ] Select a SKU with very little data (if available)
2. [ ] Try to run forecast

**Expected Results:**
- [ ] Clear error message about insufficient data
- [ ] No crash or blank screen
- [ ] Can still select other SKUs and retry

## Chart Interaction Check

- [ ] Hover over chart shows exact values
- [ ] Can zoom by clicking and dragging
- [ ] Double-click resets zoom
- [ ] Camera icon downloads chart as PNG
- [ ] Chart is responsive to window size

## Performance Check

- [ ] Forecast completes within 10 seconds (for most SKUs)
- [ ] No lag when changing selections
- [ ] Dashboard remains responsive
- [ ] No memory warnings

## Documentation Check

Verify all documentation files are present:
- [ ] README.md (updated)
- [ ] FEATURES.md (updated)
- [ ] FORECASTING_GUIDE.md (new)
- [ ] UPDATE_INSTRUCTIONS.md (new)
- [ ] WHATS_NEW.md (new)
- [ ] IMPLEMENTATION_SUMMARY.md (new)
- [ ] SETUP_CHECKLIST.md (this file)
- [ ] verify_installation.py (new)

## Troubleshooting

### Issue: "Required libraries not installed" message
**Fix:**
```bash
pip install statsmodels scikit-learn
```
- [ ] Re-run verification script

### Issue: "Insufficient data for SKU"
**Fix:**
- [ ] Select different SKU with more history
- [ ] Check if selected SKU has at least 10 data points

### Issue: Import errors
**Fix:**
```bash
pip install -r requirements.txt --upgrade
```
- [ ] Restart dashboard

### Issue: Charts not displaying
**Fix:**
- [ ] Clear browser cache
- [ ] Try different browser
- [ ] Check browser console for errors

### Issue: Very high MAPE (>50%)
**This is normal for:**
- [ ] Erratic demand patterns
- [ ] New products with limited history
- [ ] SKUs with external factors

**Try:**
- [ ] Different model
- [ ] More forecast periods
- [ ] Different SKU for testing

## Final Verification

### All Systems Go ✅
- [ ] Dashboard launches without errors
- [ ] All 7 tabs accessible
- [ ] Forecasting tab fully functional
- [ ] Statistical models work
- [ ] ML models work
- [ ] Charts render properly
- [ ] Metrics display correctly
- [ ] Export works
- [ ] Documentation readable

## Success! 🎉

If all items are checked, your Demand Forecasting feature is ready to use!

### Next Steps
1. Read `FORECASTING_GUIDE.md` for detailed usage instructions
2. Try forecasting different SKUs
3. Compare statistical vs ML models
4. Use forecasts for planning

### Quick Reference

**File to run:** `streamlit run dashboard.py`

**Navigate to:** 🎯 Demand Forecasting

**Documentation:** 
- Quick guide: `WHATS_NEW.md`
- Full guide: `FORECASTING_GUIDE.md`
- Features: `FEATURES.md`

**Need help?** Run `python verify_installation.py` first!

---

**Checklist Version:** 1.0
**Last Updated:** 2024
**Feature:** Demand Forecasting v2.0
