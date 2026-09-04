# 📊 EDA & Data Quality Dashboard

A comprehensive, interactive dashboard built with Streamlit for Exploratory Data Analysis (EDA) and Data Quality assessment of sales and distribution data.

## ✨ Features

### 🎨 Modern UI/UX
- **Gradient themes** with purple/blue color scheme
- **Animated charts** with smooth transitions
- **Responsive design** that works on all screen sizes
- **Interactive visualizations** using Plotly
- **Card-based layout** with hover effects

### 📊 Dashboard Pages

1. **🏠 Overview**
   - Key metrics cards (Total Records, Data Completeness, Duplicates, Missing Values)
   - Time series analysis of records
   - Data completeness gauge
   - Segment distribution pie chart
   - Tonnage analysis with box plots

2. **📊 Data Quality**
   - Overall quality score
   - Missing values analysis with horizontal bar charts
   - Data type distribution
   - Column-by-column quality assessment
   - Automated quality status indicators

3. **🧹 Data Cleaning**
   - Duplicate records analysis
   - Cleaning recommendations
   - Column standardization opportunities
   - Before/after metrics
   - Interactive cleaning suggestions

4. **📈 Statistical Analysis**
   - Descriptive statistics table
   - Correlation heatmap
   - Distribution charts (histograms & box plots)
   - Statistical summaries (mean, median, std dev, range)
   - Interactive column selector

5. **🔍 Detailed Exploration**
   - Column explorer with multi-select
   - Individual column deep-dive
   - Search functionality
   - Data preview (first 100 rows)
   - Value counts and unique analysis

6. **🎯 Demand Forecasting** ⭐ NEW!
   - **SKU-wise demand forecasting**
   - **Statistical Models**: ARIMA, SARIMA, Exponential Smoothing
   - **Machine Learning Models**: Random Forest, Gradient Boosting
   - Interactive forecast charts with confidence intervals
   - Performance metrics (MAE, RMSE, MAPE, Accuracy)
   - Historical pattern analysis
   - CSV export of forecasts

7. **📄 Export Report**
   - **PDF Report Generation** matching your original format
   - Excel export with summary sheet
   - CSV export
   - Text summary export
   - Includes all key metrics and findings

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download** this repository

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Dashboard

1. **Make sure your data file** (`Filtered.xlsx`) is in the same directory

2. **Run the Streamlit app**:
   ```bash
   streamlit run dashboard.py
   ```

3. **Open your browser** to the URL shown in the terminal (usually `http://localhost:8501`)

## 📁 File Structure

```
EDA dashboard Python/
├── dashboard.py          # Main dashboard application
├── Filtered.xlsx         # Your data file
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 📦 Dependencies

### Core Libraries
- **streamlit** - Web framework for the dashboard
- **pandas** - Data manipulation and analysis
- **plotly** - Interactive charts and visualizations
- **numpy** - Numerical computing
- **openpyxl** - Excel file handling
- **fpdf** - PDF report generation

### Forecasting Libraries (NEW)
- **statsmodels** - Statistical time series models (ARIMA, SARIMA, Exponential Smoothing)
- **scikit-learn** - Machine learning models (Random Forest, Gradient Boosting)

> **Note**: To use the Demand Forecasting feature, install all dependencies with:
> ```bash
> pip install -r requirements.txt
> ```
>
> Or verify your installation:
> ```bash
> python verify_installation.py
> ```

## 🎯 Key Metrics Tracked

- **Total Records**: 82,034 records
- **Total Columns**: 23 columns
- **Data Completeness**: Percentage of non-missing values
- **Duplicate Records**: Count and percentage of duplicates
- **Missing Values**: Total and per-column analysis
- **Data Quality Score**: Overall assessment (0-100)

## 📊 Visualizations

### Interactive Charts
- 📅 **Time Series**: Records over time with animated lines
- 🎯 **Gauge Charts**: Data completeness with color coding
- 🏢 **Pie Charts**: Segment distribution with hover details
- ⚖️ **Box Plots**: Tonnage distribution and outliers
- 🔗 **Heatmaps**: Correlation analysis
- 📊 **Histograms**: Value distributions
- 📈 **Bar Charts**: Top values and missing data

### Color Schemes
- Purple/Blue gradients (#667eea → #764ba2)
- Viridis and Set3 color palettes
- Red-Yellow-Green for quality indicators

## 📄 Report Export

The dashboard can generate a professional PDF report that includes:

1. **Executive Summary**
   - Dataset overview
   - Key findings
   - Date range and record counts

2. **Data Quality Assessment**
   - Missing values analysis
   - Data types distribution
   - Quality metrics

3. **Recommendations**
   - Data cleaning strategies
   - Standardization suggestions
   - Monitoring guidelines

4. **Conclusion**
   - Overall assessment
   - Next steps

**Note**: The report states "Generated from Dashboard" to distinguish it from manually created reports.

## 🎯 Demand Forecasting (NEW!)

The dashboard now includes advanced demand forecasting capabilities for SKU-wise predictions:

### Features
- **Choose Your Model**: Statistical (ARIMA, SARIMA, Exp. Smoothing) or Machine Learning (Random Forest, Gradient Boosting)
- **Interactive Configuration**: Select SKU, forecast periods (4-52 weeks), confidence levels
- **Visual Forecasts**: Interactive charts with historical data, predictions, and confidence intervals
- **Performance Metrics**: MAE, RMSE, MAPE, and Accuracy scores
- **Export**: Download forecasts as CSV for further analysis

### Use Cases
- 📦 **Inventory Planning**: Optimize stock levels based on predicted demand
- 🏭 **Production Planning**: Schedule manufacturing based on forecasts
- 💰 **Budget Allocation**: Allocate resources by predicted SKU performance
- 📈 **Sales Strategy**: Plan promotions for high-demand periods

### Quick Start
1. Navigate to "🎯 Demand Forecasting" tab
2. Select a SKU (Material) from dropdown
3. Choose model type (Statistical or ML)
4. Configure forecast parameters
5. Click "Run Forecast"
6. Analyze results and download

For detailed guide, see: [FORECASTING_GUIDE.md](FORECASTING_GUIDE.md)

## 🎨 Customization

### Changing Colors
Edit the CSS in the `st.markdown()` section of `dashboard.py`:
```python
# Main gradient
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

# Chart colors
marker_color='#667eea'
```

### Adding New Pages
Add a new option to the sidebar radio button and create a corresponding function:
```python
page = st.sidebar.radio("Navigate to:", [..., "🆕 New Page"])

if page == "🆕 New Page":
    show_new_page(df, metrics)
```

## 🔧 Troubleshooting

### Dashboard won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that `Filtered.xlsx` is in the same directory
- Verify Python version: `python --version` (should be 3.8+)

### Visualizations not showing
- Check browser console for errors
- Try a different browser
- Clear Streamlit cache: `streamlit cache clear`

### PDF export not working
- Ensure fpdf is installed: `pip install fpdf`
- Check file permissions in the output directory

## 💡 Tips for Best Experience

1. **Use full-screen mode** for better visualization (F11)
2. **Explore all pages** to see different perspectives of your data
3. **Hover over charts** for detailed information
4. **Use the search feature** in Detailed Exploration for specific records
5. **Export reports regularly** to track data quality over time

## 🤝 Contributing

Feel free to enhance this dashboard:
- Add new visualizations
- Improve UI/UX
- Add more data quality checks
- Enhance PDF report formatting

## 📝 License

This project is created for educational and analytical purposes.

## 🙋 Support

For issues or questions about the dashboard:
1. Check the troubleshooting section
2. Review the code comments in `dashboard.py`
3. Ensure all dependencies are correctly installed

---

**Built with ❤️ using Streamlit, Plotly, and Python**

*Dashboard Version: 2.0* (NEW: Demand Forecasting!)
*Last Updated: 2024*
