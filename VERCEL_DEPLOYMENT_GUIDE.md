# 🚀 100% Standalone Vercel Deployment Guide
## ISB Capstone Project: AI Intelligence & Demand Forecasting

This repository is configured for **1-Click Standalone Vercel Deployment**. It requires **no external server, no Streamlit Cloud, and zero backend maintenance**.

---

## ⚡ Architectural Overview

| Component | Platform | Role | Why? |
| :--- | :--- | :--- | :--- |
| **Interactive Web Application** | **Vercel** (`vercel.app`) | Global CDN delivery, interactive Plotly.js time-series analytics, branch and SKU filtering, deliverables download hub (PDF/PPTX/CSV), and 6-module interactive showcase. | Ultra-fast load times (<0.2s), 100% uptime, zero cold starts, zero external dependencies. |
| **Client-Side Analytical Engine** | **In-Browser (Plotly.js)** | Executes multi-dimensional filtering, ARIMA trendline rendering, regional split aggregations, and dynamic CSV slice downloads directly in the browser. | Runs client-side instantly with zero backend latency or hosting costs. |

---

## 🚀 Step-by-Step: Deploy to Vercel in 60 Seconds

### Step 1: Push Your Code to GitHub
Ensure all recent changes are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Feat: Complete 100% standalone Vercel analytics deployment"
git push origin main
```

### Step 2: Import into Vercel
1. Navigate to **[vercel.com](https://vercel.com)** and log in with your GitHub account.
2. Click **"Add New..."** ➔ **"Project"**.
3. Select your repository: `saiprash711/ISB_Capstone_Project`.
4. **Build & Output Settings**:
   - Vercel automatically detects `vercel.json` and configures:
     - **Output Directory**: `public`
     - **Framework Preset**: `Other` (Static)
5. Click **"Deploy"**.
6. Deployment completes in **under 10 seconds**! ✨
   - You will receive a live URL such as `https://isb-capstone-project.vercel.app`.

---

## 📦 What is Included in Your Vercel Application

1. **Native Interactive Forecasting & Analytics Studio**:
   - Dynamic **Branch Hub Filter** (BLR, MAA, COK, SBD, SBD1, or South Region aggregate).
   - Dynamic **Material / SKU Selector** (15 high-volume product configurations).
   - **Real-Time Dynamic KPIs**:
     - Total Forecast Units (91,504 baseline)
     - Peak Weekly Demand & Peak Week Identifier
     - Average Weekly Run-Rate
     - Active Product Configuration Count
   - **Interactive Plotly Visualizations**:
     - *Mode 1*: 📈 Time-Series Weekly Trendline with smooth splines, markers, and hover tooltips.
     - *Mode 2*: 📊 Regional Branch Allocation bar chart.
   - **Tabular Data Slice Preview**:
     - Scrollable preview of filtered records.
     - **1-Click Export Filtered CSV** directly from the browser.

2. **Executive Telemetry & KPI Cards**:
   - 54,000+ Analyzed Invoices
   - 99.8% Data Quality Score (Audited & Imputed)
   - 180-Day Forecast Horizon (ARIMA & SARIMAX)
   - 5 Regional Branch Hubs (BLR, MAA, COK, SBD, SBD1)

3. **Interactive 6-Module Showcase**:
   - High-resolution visual walkthroughs of all 6 modules:
     - 📊 Executive Cockpit
     - 🛡️ Data Quality Radar
     - 🧼 Cleaning Studio
     - 📈 Statistical Engine
     - 🔍 Detailed Explorer
     - 🔮 Predictive Forecasting

4. **Direct Executive Deliverables (1-Click Downloads)**:
   - 📄 **Executive Briefing Report** (`.pdf`, 528 KB)
   - 📊 **Presentation Slide Deck** (`.pptx`, 830 KB)
   - 📈 **ARIMA Forecast Dataset** (`.csv`, 17 KB)

---

## 🔧 Local Preview

To preview the Vercel application locally before pushing:
```bash
python -m http.server 3000 --directory public
```
Open `http://localhost:3000` in your web browser.
