# 📊 ISB Capstone Project: Daikin Sales & Distribution EDA & Analytics Dashboard

An enterprise-grade, interactive analytics and forecasting dashboard built with **Streamlit**, **Plotly**, and **Python** for Exploratory Data Analysis (EDA), Data Quality auditing, and Predictive Demand Forecasting.

---

## 🌟 Overview

This project provides an end-to-end data analytics workflow for analyzing sales, tonnage, orders, and product distributions:
- **Cockpit & Overview**: High-level KPIs, monthly volume/tonnage trends, channel distribution, and performance metrics.
- **Data Quality Radar**: Automated health scoring, missing value profiling, duplicate detection, and schema validation.
- **Data Cleaning Studio**: Duplicate handling, imputation rules, outlier filtering, and one-click data transformation.
- **Statistical Engine**: Multi-variable distributions, correlation matrix, hypothesis checks, and segment breakdown.
- **Detailed Explorer**: Drill-down search, multi-column filters, and raw data examination.
- **Predictive Forecasting**: ARIMA/SARIMA time-series models with confidence intervals and scenario planning.
- **Executive Reporting**: One-click professional PDF and CSV export generation for executive presentations.

---

## 📁 Repository Structure

```plaintext
ISB_Capstone_Project/
├── 2024 July to 2025 June.xlsx              # Raw baseline sales dataset (July 2024 - June 2025)
├── Capstone Weekly Update- Format.docx      # Weekly project documentation & update template
├── Daikin Capstone Weekly Report (1).pdf    # Project milestones & weekly briefing report
├── requirements.txt                         # Root Python dependencies
├── .streamlit/
│   └── config.toml                          # Global Streamlit theming & server configuration
│
└── EDA dashboard Python/                    # Core Dashboard Application & Assets
    ├── dashboard.py                         # Complete interactive Streamlit dashboard application
    ├── Start.bat                            # Windows batch launcher
    ├── requirements.txt                     # Dashboard dependencies
    ├── Filtered.csv / Filtered.xlsx         # Processed and curated datasets
    ├── ARIMA_Forecast_Results.csv           # Model forecasting outputs
    ├── .streamlit/config.toml               # Module-level Streamlit theme configuration
    ├── README.md                            # In-depth dashboard documentation
    ├── QUICKSTART.md                        # Quickstart instructions
    ├── FEATURES.md                          # Detailed breakdown of dashboard modules
    ├── FORECASTING_GUIDE.md                 # Time-series modeling documentation
    ├── verify_installation.py               # Dependency and environment health check script
    ├── verify_all_views.py                  # Automated headless view verification
    └── assets / screenshots (.png)          # Visual demonstrations and view captures
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/saiprash711/ISB_Capstone_Project.git
cd ISB_Capstone_Project
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Dashboard
You can launch directly via the batch script (Windows) or via Streamlit CLI:

**Windows Batch:**
Double-click `EDA dashboard Python\Start.bat`

**Command Line:**
```bash
cd "EDA dashboard Python"
streamlit run dashboard.py
```

Open `http://localhost:8501` in your browser.

---

## 🛠️ Tech Stack & Libraries

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **Visualizations**: [Plotly Graph Objects & Express](https://plotly.com/python/)
- **Data Wrangling**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Forecasting & ML**: [Statsmodels](https://www.statsmodels.org/), [Scikit-Learn](https://scikit-learn.org/)
- **Spreadsheet Processing**: [openpyxl](https://openpyxl.readthedocs.io/)
- **Document Generation**: [FPDF](https://pyfpdf.readthedocs.io/)

---

## 👤 Author
- **Sai Sarathy** ([@saiprash711](https://github.com/saiprash711))
- Indian School of Business (ISB)
