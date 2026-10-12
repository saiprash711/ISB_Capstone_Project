# 🎯 ISB Mid-Review Presentation Guide

## 📊 Presentation Overview

**File**: `Capstone_PPT_Enhanced.pptx`  
**Total Slides**: 15  
**Duration**: 25-30 minutes (recommended)  
**Format**: Professional dark theme with data-driven insights

---

## 📑 Slide-by-Slide Breakdown

### **Slide 1: Title Slide** 🎬
**Content**: Supply Chain Intelligence - AI Demand Forecasting & Quality Analytics  
**Key Points**:
- ISB Capstone Project branding
- Team: Sai Prashanth, Arvind, Hariharan, Vani, Vedika
- Sponsor: Deloitte

**Presenter Notes**: 
- Start strong with the business problem
- Emphasize "AI-powered" and "real-time analytics"
- Mention this is a mid-review checkpoint

---

### **Slide 2: Project Timeline & Progress** ⏱️ **[NEW]**
**Content**: 5-phase timeline with progress indicators  
**Key Achievements**:
- ✅ Fully functional 7-page dashboard deployed
- ✅ 5 forecasting models implemented (ARIMA live)
- ✅ Data quality improved 95% → 98.5%
- ✅ 82K+ records analyzed

**Current Sprint Focus**:
- ML model validation in progress
- Extending ARIMA coverage
- Building automated refresh pipeline

**Presenter Notes**:
- Show you're on track and aware of what's next
- Highlight that dashboard is already functional (not just planned)
- "We're 75% through the project with all core deliverables functional"

**Timing**: 2-3 minutes

---

### **Slide 3: Context** 🗺️
**Content**: Five hubs, 154 SKUs across South India  
**Key Stats**:
- 5 regional distribution hubs (MAA, SBD, SBD1, COK, BLR)
- 154 active SKUs
- 3 fiscal years of data (Jul 2022 - Jun 2024)

**Business Impact**:
- Better forecasts → lower safety stock
- Fewer inter-hub transfers
- Fewer stockouts in peak season

**Presenter Notes**:
- Connect forecasting to real business outcomes
- Emphasize regional complexity
- "Each hub has unique demand patterns that need SKU-level forecasting"

**Timing**: 2 minutes

---

### **Slide 4: Data** 📊
**Content**: Data quality audit results  
**Key Metrics**:
- 82,034 transaction records
- 94.99% field completeness
- 4,463 duplicate records (5.44%)
- 23,603 rows missing structurally (28.77% Q1 FY24-25 gap)

**Volume Reconciliation**:
- Gross: 909,451.5 units
- Returns: -7,060.5 units (0.78% return rate)
- Net: 902,391 units

**Presenter Notes**:
- Be honest about data challenges (shows critical thinking)
- Emphasize you've quantified the gap
- "Low return rate means we can treat returns as noise, not signal"

**Timing**: 2 minutes

---

### **Slide 5: Demand** 📈
**Content**: Demand pattern analysis  
**Key Finding**: **No SKU has smooth demand — 70% is lumpy**

**Syntetos-Boylan Classification**:
- Lumpy: 70.1% (108 SKUs)
- Intermittent: 18.8% (29 SKUs)
- Erratic: 11.0% (17 SKUs)
- Smooth: 0% (0 SKUs)

**ODU vs IDU Split**:
- Outdoor Units (ODU): 80.8% (729,297 units)
- Indoor Units (IDU): 19.2% (173,094 units)

**Presenter Notes**:
- This slide justifies your model choices
- "Empty smooth quadrant ruled out standard exponential smoothing"
- "This pushed us toward intermittent-demand methods and ML approaches"

**Timing**: 2-3 minutes

---

### **Slide 6: Distribution** 📊
**Content**: Statistical characteristics of order lines  
**Key Insight**: Order lines are small and widely dispersed

**Statistics**:
- ODU median: 3 units (mean: 8.89, std: 18.05)
- IDU median: 0 units (mean: 2.11, std: 10.35)
- Tonnage median: 1.5 (mean: 1.28, std: 0.56)

**Presenter Notes**:
- "Standard deviation is 2-5x the mean — high variability"
- "Median IDU is zero — explains the intermittent demand challenge"
- Connect this to why traditional forecasting fails

**Timing**: 2 minutes

---

### **Slide 7: Method** 🔬
**Content**: Dual-track forecasting approach  
**Models Evaluated**:

**Statistical Track**:
- ARIMA (1,1,1)
- SARIMA (1,1,1,12)
- Exponential Smoothing

**Machine Learning Track**:
- Random Forest
- Gradient Boosting

**Feature Engineering**:
- Calendar features (week, month, quarter)
- Lag features (previous 4 weeks)
- Rolling averages (2-week, 4-week windows)

**Validation Design**:
- 80/20 train-validation split
- Scored on MAE, RMSE, MAPE
- Minimum 10 observations required

**Presenter Notes**:
- "Lumpy demand forced us to build two tracks in parallel"
- "Let the data decide which model performs better per SKU"
- Show you understand model selection is data-driven, not arbitrary

**Timing**: 3 minutes

---

### **Slide 8: Results** 🎯
**Content**: Live forecasting capabilities  
**Current Deployment**:
- 12-week rolling forecast
- 42 branch-SKU series forecasted
- 15 distinct SKUs covered
- 91,504 units forecast from 26 May 2024

**Forecast Volume by Hub (ARIMA)**:
- SBD: 31,731 units (34.7%)
- MAA: 25,578 units (28.0%)
- SBD1: 17,730 units (19.4%)
- BLR: 8,398 units (9.2%)
- COK: 8,067 units (8.8%)

**Presenter Notes**:
- "SBD and MAA together absorb 63% of forecast volume"
- "This tells us where allocation and safety-stock changes will pay back first"
- Emphasize these are real, exportable forecasts

**Timing**: 2-3 minutes

---

### **Slide 9: Impact** ⚡
**Content**: Data hygiene improvements  
**Actions Taken**:
- Pruned 4,463 duplicate rows
- Imputed/isolated 94,435 null fields
- Normalized schema across 23 attributes
- Enforced ISO date standard
- Standardized casing on Segment and Material

**Post-Cleaning Projection**:
- Post-clean fleet size: 77,571 rows
- Target completeness: **98.49%** (up from 95%)
- Storage efficiency gain: +5.44%
- Model training convergence: **~18% faster**

**Presenter Notes**:
- "Cleaning the pipeline lifts completeness to 98.5%"
- "18% faster training means faster iteration cycles"
- Show quantified impact, not just "we cleaned the data"

**Timing**: 2 minutes

---

### **Slide 10: Delivery** 🖥️
**Content**: Seven-view interactive dashboard  
**Pages**:
1. **Executive Cockpit** — Health, volume, distribution telemetry
2. **AI Demand Forecasting** — Forward demand 4-52 weeks
3. **Data Quality Radar** — Completeness and diagnostics
4. **Data Cleaning Studio** — Deduplication and imputation
5. **Statistical Deep-Dive** — Distributions and correlations
6. **Intelligence Explorer** — Column profiling and search
7. **C-Suite Reports** — Automated PDF/Excel exports

**Features**:
- Dark and light themes
- Interactive visualizations (Plotly)
- Real-time analysis

**Presenter Notes**:
- "Analysis ships as a dashboard, not a static report"
- "Built for both boardroom projection and desk review"
- **Be ready to demo live if possible**

**Timing**: 2-3 minutes

---

### **Slide 11: Challenges & Learnings** 💡 **[NEW]**
**Left Column — Challenges**:
- 📊 Data Gap: 28.77% structural gap limits training window
- 📈 Lumpy Demand: 70% lumpy ruled out standard methods
- 🔄 Model Complexity: Required 5 distinct model types
- ⚡ Performance: 82K records with real-time UI requirements
- 🎯 Validation Design: Intermittent demand makes metrics tricky

**Right Column — Solutions**:
- 🔧 Hybrid Approach: Built statistical + ML tracks in parallel
- 📊 Classification First: Applied Syntetos-Boylan before model selection
- ⚡ Modular Architecture: EDA, cleaning, forecasting separated
- 🎯 Interactive Validation: Live performance metrics in dashboard
- 📄 Documentation First: 6 comprehensive guides alongside code

**Presenter Notes**:
- **This is your strongest slide for mid-review**
- Shows critical thinking and problem-solving
- "Every challenge we faced led to a technical pivot or solution"
- Demonstrates maturity: you didn't just build features, you solved real problems

**Timing**: 3-4 minutes (this is worth the time)

---

### **Slide 12: Dashboard Demo Walkthrough** 🎬 **[NEW]**
**Content**: Visual flow through all 7 dashboard pages

**Demo Flow**:
1. **Overview** → Executive metrics and trends
2. **Quality** → Missing value analysis
3. **Clean** → Duplicate removal and imputation
4. **Stats** → Correlation heatmap
5. **Forecast** → SKU selection and model comparison
6. **Explore** → Column profiling
7. **Export** → PDF/Excel downloads

**Presenter Notes**:
- Use this as your transition to live demo (if doing one)
- Or walk through the flow verbally
- "Let me walk you through a typical user journey..."
- **Recommendation**: Do a 3-minute live demo after this slide

**Timing**: 2 minutes + 3 minutes live demo = 5 minutes total

---

### **Slide 13: Technical Architecture** 🔧 **[NEW]**
**Content**: Four-layer stack

**Layers**:
1. **Presentation Layer**
   - Streamlit 1.30+ (Interactive web framework)
   - Plotly 5.18+ (Dynamic visualizations)
   - Dark/Light themes

2. **Analytics Layer**
   - Pandas 2.1+ (Data manipulation)
   - NumPy 1.26+ (Numerical computing)
   - SciPy 1.11+ (Statistical functions)

3. **Forecasting Layer**
   - Statsmodels 0.14+ (ARIMA, SARIMA)
   - Scikit-learn 1.3+ (RF, GB)
   - Custom feature engineering

4. **Export Layer**
   - FPDF 1.7+ (PDF generation)
   - OpenPyXL 3.1+ (Excel export)
   - Native CSV

**Performance Optimizations**:
- Cached data loading (85% faster page loads)
- Lazy chart evaluation
- Efficient pandas operations
- Modular architecture
- Production-ready error handling

**Presenter Notes**:
- Shows production readiness, not just a prototype
- "This isn't a notebook; it's a deployable application"
- Mention version numbers to show you're using current libraries

**Timing**: 2 minutes

---

### **Slide 14: Next** 🚀
**Content**: Four moves from capstone to production tool

**Roadmap**:
1. **Run hygiene pipeline in production** → Every refresh lands at 98.5%
2. **Close Q1 FY24-25 gap** → Extend forecast window
3. **Extend coverage** → 15 SKUs → 154 SKUs hub by hub
4. **Convert forecasts** → Safety-stock and allocation targets for SBD and MAA

**Presenter Notes**:
- Shows you're thinking beyond the project
- "These four moves take the dashboard from capstone artifact to planning tool"
- Demonstrates handoff thinking

**Timing**: 2 minutes

---

### **Slide 15: Model Progress** 📊
**Content**: Model validation status table

**Model Status**:
| Model | Status | Series Scored |
|-------|--------|---------------|
| ARIMA (1,1,1) | ✅ Scored, exporting | 42 |
| SARIMA (1,1,1,12) | 🔄 In validation | — |
| Exponential Smoothing | 🔄 In validation | — |
| Random Forest | 🔧 Built, unscored | — |
| Gradient Boosting | 🔧 Built, unscored | — |

**Acceptance Gates**:
- MAPE below 20%
- Accuracy (100 - MAPE) above 80%
- MAE and RMSE: Lower is better

**Presenter Notes**:
- "ARIMA is live and scoring 42 series"
- "ML models are built but still in validation"
- "Every series is scored against held-out 20% before promotion"
- Shows rigor in model validation

**Timing**: 2 minutes

---

## 🎯 Presentation Strategy

### **Opening (Slides 1-2)** — 5 minutes
- Hook: "We're building AI-powered demand forecasting for 154 SKUs across South India"
- Context: Mid-review checkpoint, 75% complete, core deliverables functional
- Tease: "Let me show you the data challenges that shaped our approach"

### **Problem Setup (Slides 3-6)** — 8 minutes
- Build the case for why this is hard
- Use data to tell the story: lumpy demand, gaps, variability
- "This is why traditional forecasting doesn't work here"

### **Solution (Slides 7-10)** — 10 minutes
- Show your dual-track approach
- Demonstrate results (42 series, 91K units forecast)
- Highlight impact (98.5% completeness, 18% faster training)
- Show the dashboard as the delivery vehicle

### **Learnings & Demo (Slides 11-13)** — 10 minutes
- **Slide 11 is your hero slide** — spend time here
- Quick dashboard walkthrough or live demo
- Technical architecture shows production readiness

### **Wrap-Up (Slides 14-15)** — 5 minutes
- Roadmap shows you're thinking ahead
- Model progress shows current state honestly
- Q&A

---

## 💡 Presentation Tips

### **For the Mid-Review Audience**
✅ **Do**:
- Emphasize learnings and pivots (Slide 11)
- Show honesty about challenges (data gap, lumpy demand)
- Demonstrate working software (live demo)
- Quantify impact (98.5%, 18%, 42 series)
- Connect forecasts to business outcomes

❌ **Don't**:
- Oversell unfinished ML models
- Hide data quality issues
- Spend too long on theory
- Skip the demo
- Forget to mention team contributions

### **Backup Slides** (Optional)
Consider having these ready:
- Detailed ARIMA performance metrics for specific SKUs
- Sample forecast visualization from dashboard
- Data cleaning before/after comparison
- Code architecture diagram

### **If Asked About...**

**"Why are ML models not scored yet?"**
- "We prioritized getting statistical models into production first"
- "ARIMA is running live on 42 series; ML models are in validation"
- "We're validating feature engineering approach before scaling"

**"What about the 28.77% data gap?"**
- "We've documented this as a structural issue at source"
- "Our models train on available history; extending coverage is in next steps"
- "Dashboard has built-in data validation to flag future gaps"

**"How do you handle lumpy demand?"**
- "We classified SKUs using Syntetos-Boylan before model selection"
- "Built both statistical and ML tracks to compare approaches"
- "Dashboard lets users see which model performs better per SKU"

**"Is this ready for production?"**
- "Dashboard is production-ready and deployable now"
- "ARIMA forecasts are export-ready for 42 series"
- "Next phase is scaling SKU coverage and integrating with planning tools"

---

## 📋 Pre-Presentation Checklist

### **24 Hours Before**
- [ ] Test presentation on actual projector/screen
- [ ] Check all slides render correctly
- [ ] Prepare live demo environment (dashboard running)
- [ ] Test internet connection if demo is cloud-based
- [ ] Print backup slides in case of tech failure
- [ ] Rehearse timing (aim for 25 minutes + 5 min Q&A)

### **1 Hour Before**
- [ ] Open dashboard in browser (test that it loads)
- [ ] Open presentation file
- [ ] Test HDMI/display connection
- [ ] Have backup plan (PDF export, screenshots)
- [ ] Hydrate and breathe!

### **During Presentation**
- [ ] Start strong with business context
- [ ] Make eye contact with faculty/reviewers
- [ ] Use Slide 11 (Challenges & Learnings) as your anchor
- [ ] Invite questions after demo
- [ ] Stay within time limit

---

## 🎬 Demo Script (3 minutes)

If doing a live demo after Slide 12:

**"Let me quickly show you the dashboard in action..."**

1. **Overview page** (20 sec)
   - "82K records, 23 columns, 95% complete"
   - "Time series shows seasonal peaks"

2. **Data Quality page** (20 sec)
   - "Missing values by column"
   - "Quality score calculated automatically"

3. **Forecasting page** (90 sec) ⭐
   - "Select an SKU — let's pick a high-volume one"
   - "Choose model — ARIMA for this demo"
   - "Set forecast periods — 12 weeks"
   - "Run forecast"
   - [Show chart with confidence intervals]
   - "Performance metrics: MAE, RMSE, MAPE, Accuracy"
   - "Can export to CSV for planning"

4. **Export page** (30 sec)
   - "Generate PDF report"
   - "Includes executive summary, quality assessment"
   - [Show sample PDF if time allows]

**"This entire dashboard is live and functional today."**

---

## 📊 Key Messages to Reinforce

### **Technical Rigor**
- "We classified demand patterns before selecting models"
- "Every model is validated on held-out data"
- "Built production-grade error handling"

### **Business Impact**
- "Forecasts directly inform safety stock and allocation"
- "SBD and MAA absorb 63% of volume — where ROI is highest"
- "18% faster training means faster iteration"

### **Delivery Excellence**
- "Dashboard is functional today, not a future promise"
- "6 comprehensive guides for handoff"
- "Dark and light themes for boardroom and desk use"

### **Honest Assessment**
- "28.77% data gap limits training window — we've documented this"
- "70% lumpy demand ruled out standard methods — we adapted"
- "ML models built but still in validation — we're being rigorous"

---

## 🚀 Post-Presentation Actions

### **Immediate**
- Collect feedback from reviewers
- Note questions you couldn't answer fully
- Thank Deloitte sponsor (if present)

### **Next 24 Hours**
- Send thank-you email with dashboard link
- Share any requested additional details
- Update roadmap based on feedback

### **Next Week**
- Incorporate feedback into final deliverables
- Update documentation based on questions asked
- Prepare for final presentation adjustments

---

## 📁 File Reference

| File | Purpose |
|------|---------|
| `Capstone_PPT_Enhanced.pptx` | **Use this for presentation** |
| `Capstone_PPT.pptx` | Original (backup) |
| `dashboard.py` | Main application |
| `IMPLEMENTATION_SUMMARY.md` | Technical documentation |
| `FORECASTING_GUIDE.md` | User guide for forecasting |
| `FEATURES.md` | Complete feature list |

---

## ✅ Success Criteria for Mid-Review

**You'll know you nailed it if**:
- ✅ Reviewers understand the data challenges (lumpy demand, gap)
- ✅ They see the dashboard is functional, not theoretical
- ✅ Questions focus on "what's next" not "why isn't this done"
- ✅ Business value is clear (safety stock, allocation)
- ✅ Technical rigor is evident (classification, validation)
- ✅ Live demo works smoothly
- ✅ You stay within time limit

---

**Good luck with your mid-review! You've built something impressive — now show it with confidence. 🎯**

---

*Generated for ISB Capstone Mid-Review*  
*Project: Supply Chain Intelligence - AI Demand Forecasting*  
*Team: Sai Prashanth, Arvind, Hariharan, Vani, Vedika*
