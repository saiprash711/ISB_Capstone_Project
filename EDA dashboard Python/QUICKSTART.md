# 🚀 Quick Start Guide

## Fastest Way to Start

### Option 1: Double-Click Launch (Easiest!)
1. Double-click **`run_dashboard.bat`**
2. Wait for the browser to open automatically
3. Start exploring your data!

### Option 2: Command Line
1. Open Command Prompt or PowerShell
2. Navigate to this folder
3. Run: `streamlit run dashboard.py`

## First Time Setup (One Time Only)

If you haven't installed the requirements yet:

```bash
pip install -r requirements.txt
```

## What You'll See

When the dashboard starts:
1. Your browser will open automatically
2. You'll see the **Overview** page with:
   - 📋 Total Records: 82,034
   - ✅ Data Completeness percentage
   - 🔄 Duplicate count
   - ⚠️ Missing values count

## Navigate the Dashboard

Use the **sidebar** on the left to explore:

1. **🏠 Overview** - Quick summary with key metrics
2. **📊 Data Quality** - Deep dive into data issues
3. **🧹 Data Cleaning** - Recommendations for cleanup
4. **📈 Statistical Analysis** - Correlations and distributions
5. **🔍 Detailed Exploration** - Search and filter data
6. **📄 Export Report** - Generate PDF/Excel/CSV

## Key Features to Try

### 📊 Interactive Charts
- **Hover** over any chart for detailed values
- **Zoom** by clicking and dragging on charts
- **Download** charts as images using the camera icon

### 🔍 Data Exploration
1. Go to **Detailed Exploration**
2. Select columns to view
3. Use the search feature to find specific records

### 📄 Generate Report
1. Go to **Export Report**
2. Click **"Generate Report"** button
3. Download the PDF that matches your original format
4. Report includes: Executive Summary, Quality Assessment, Recommendations

## Stopping the Dashboard

Press **Ctrl+C** in the terminal/command prompt

## Troubleshooting

### Dashboard won't start?
- Make sure you installed requirements: `pip install -r requirements.txt`
- Check that `Filtered.xlsx` is in the same folder
- Verify Python is installed: `python --version`

### Browser doesn't open?
- Manually open: `http://localhost:8501`
- Try a different browser

### Charts not loading?
- Refresh the page (F5)
- Clear cache from sidebar menu: **Settings → Clear cache**

## Pro Tips

💡 **Use full screen** (F11) for best viewing experience

💡 **Refresh data** using the refresh button in the sidebar

💡 **Export reports regularly** to track data quality improvements

💡 **Share the dashboard** - it runs locally but can be deployed to share with team

## Need Help?

Check the full **README.md** for:
- Detailed feature documentation
- Customization options
- Advanced troubleshooting
- Code examples

---

**Enjoy exploring your data! 📊✨**
