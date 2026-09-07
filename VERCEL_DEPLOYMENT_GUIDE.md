# 🚀 Vercel & Streamlit Dual Deployment Guide
## ISB Capstone Project: Daikin AI Intelligence & Demand Forecasting

This repository is configured for **1-Click Vercel Deployment** with a companion **Streamlit Community Cloud** engine.

---

## ⚡ Architectural Overview

| Component | Platform | Role | Why? |
| :--- | :--- | :--- | :--- |
| **Executive Web Portal** | **Vercel** (`vercel.app`) | Global CDN delivery, executive KPI overview, deliverables download hub (PDF/PPTX/CSV), interactive module tour, and live engine viewer. | Ultra-fast load times (<0.5s), 100% uptime, zero cold starts, global edge caching. |
| **Analytics & ML Engine** | **Streamlit Cloud** (`streamlit.app`) | Full 2,800-line Python backend, Plotly visual rendering, ARIMA(1,1,1), SARIMAX, Random Forest ML, and dynamic data filtering. | Stateful Python runtime, persistent WebSockets, multi-threaded ML execution. |

---

## 🚀 Quick Step-by-Step: Deploy to Vercel in 2 Minutes

### Step 1: Push Your Code to GitHub
Ensure all recent changes are pushed to your GitHub repository:
```bash
git add .
git commit -m "Feat: Add Vercel deployment configuration, executive portal, and assets"
git push origin main
```

### Step 2: Import into Vercel
1. Navigate to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **"Add New..."** ➔ **"Project"**.
3. Select your repository: `saiprash711/ISB_Capstone_Project`.
4. **Build & Output Settings**:
   - Vercel automatically detects `vercel.json` and sets:
     - **Output Directory**: `public`
     - **Framework Preset**: `Other` (Static)
5. Click **"Deploy"**.
6. Deployment completes in **under 10 seconds**! ✨
   - You will receive a live URL such as `https://isb-capstone-project.vercel.app`.

---

## ☁️ Companion Step: Deploy the Streamlit Engine (Free)

To connect the live interactive Python engine into your Vercel portal:

1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
2. Click **"New app"**.
3. Configure the fields:
   - **Repository**: `saiprash711/ISB_Capstone_Project`
   - **Branch**: `main`
   - **Main file path**: `EDA dashboard Python/dashboard.py`
4. Click **"Deploy!"**.
5. Once your Streamlit app is live (e.g. `https://daikin-forecasting.streamlit.app`):
   - Visit your Vercel URL.
   - Under the **"Live Analytics & Forecasting Dashboard"** section, paste your Streamlit Cloud URL into the connection bar.
   - Click **"Connect"** (your URL will be remembered in your browser).
   - The interactive Python engine is now embedded seamlessly inside your Vercel portal!

---

## 📦 What is Included in Your Vercel Portal

1. **Executive Telemetry & KPI Cards**:
   - 54,000+ Analyzed Invoices
   - 99.8% Data Quality Score (Audited & Imputed)
   - 180-Day Forecast Horizon (ARIMA & SARIMAX)
   - 5 Regional Branch Hubs (BLR, MAA, COK, SBD, SBD1)
2. **Interactive Module Showcase**:
   - High-resolution visual walkthroughs of all 6 modules:
     - 📊 Executive Cockpit
     - 🛡️ Data Quality Radar
     - 🧼 Cleaning Studio
     - 📈 Statistical Engine
     - 🔍 Detailed Explorer
     - 🔮 Predictive Forecasting
3. **Direct Executive Deliverables (1-Click Downloads)**:
   - 📄 **Executive Briefing Report** (`.pdf`, 528 KB)
   - 📊 **Presentation Slide Deck** (`.pptx`, 830 KB)
   - 📈 **ARIMA Forecast Dataset** (`.csv`, 17 KB)
4. **Live Engine Controller**:
   - Embedded iframe with instant fullscreen toggle, reload, and new-tab launcher.

---

## 🔧 Local Preview

To preview the Vercel portal locally before deploying:
```bash
python -m http.server 3000 --directory public
```
Open `http://localhost:3000` in your web browser.

To run the Streamlit dashboard locally:
```bash
cd "EDA dashboard Python"
streamlit run dashboard.py
```
Open `http://localhost:8501`.
