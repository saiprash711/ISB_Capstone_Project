# Chapters 3 and 4 (executed inside build_report.py's namespace)

# ===========================================================================
# CHAPTER 3
# ===========================================================================
W.h1("Chapter 3: Business Context and Data", chapter=3)
W.paras("""
Before choosing a method, we needed to understand the decision the forecast must support and the data it must be
built from. In short, the decision is weekly, local and capital-intensive, and the data are richer than they first
appear but less consistent.
""")
W.h2("3.1  Business / Research Problem")
W.paras(f"""
**Who is affected.** Five branch offices, identified in the data as MAA (Chennai), SBD, SBD1, COK (Kochi) and BLR
(Bengaluru), sell to {f0(Q['dealers'])} registered dealers and around {f0(Q['customers'])} billed customers.
Branch planners place replenishment requests on the factory, central supply planners allocate scarce peak-season
output across branches, and finance carries the cost of stock that does not sell. The project configuration maps
SBD and SBD1 to the Secunderabad and Vijayawada sales offices; we refer to all branches by code.

**The decision the forecast informs.** Every week, for each model at each branch, a planner decides how many
units to request so that stock on hand plus stock in transit covers demand until the next delivery. With a lead
time of about two weeks, the forecast that matters most is demand over the next two to four weeks, and the
quantity that matters most is the buffer held against error in that forecast.

**What success looks like.** In discussions with the sponsor, success was framed in three ways: a forecast that
is demonstrably more accurate than the simple rules planners use today, evaluated on weeks the model has not seen;
a buffer policy that protects service during the peak without inflating stock afterwards; and a tool planners can
use and question. Because the extract does not contain planners' own historical forecasts, we use simple rules
(last week's sales, and moving and smoothed averages of recent weeks) as transparent proxies for current practice.
""")
W.h2("3.2  Data Available")
W.paras(f"""
The sponsor provided a single extract from the manufacturer's ERP billing system: {f0(Q['rows'])} invoice lines and
{Q['columns']} fields, covering billing dates from {pd.Timestamp(Q['date_min']):%d %B %Y} to
{pd.Timestamp(Q['date_max']):%d %B %Y}. Each line records one material billed to one customer on one date by one
branch, with its quantity, capacity (tonnage), energy rating and segment. The extract spans 103 complete weeks,
just over two summer peaks. Access was granted for the capstone only, under the sponsor's confidentiality terms.
Table 3.1 profiles the extract by fiscal-year block, and it reveals the single most important fact about the data.
""")
W.table("Profile of the raw billing extract by fiscal-year block",
        ["Fiscal block", "Billing dates", "Rows", "ODU lines", "IDU lines", "Rows without invoice no.", "Exact duplicates"],
        [["FY 2022-23 (part)", "16 Jul 2022 - 31 Mar 2023", f0(Q['rows_by_fy']['22-23']), f0(Q['rows_by_fy']['22-23']), "0", "0", "0"],
         ["FY 2023-24", "1 Apr 2023 - 31 Mar 2024", f0(Q['rows_by_fy']['23-24']), f0(Q['rows_by_fy']['23-24']), "0", "0", "0"],
         ["FY 2024-25 Q1", "3 Apr 2024 - 30 Jun 2024", f0(Q['rows_by_fy']['24-25 Q1']), "11,799", "11,804",
          f0(Q['rows_by_fy']['24-25 Q1']), f0(Q['exact_duplicates'])],
         ["Total", "16 Jul 2022 - 30 Jun 2024", f0(Q['rows'] - 1), "70,229", "11,804", "23,603", f0(Q['exact_duplicates'])]],
        [1600, 2150, 1000, 1050, 1000, 1360, 1200],
        source=SRC + " One fully blank row is excluded from the counts.", bold_first_col=True)
W.paras(f"""
Until March 2024, the extract contains only outdoor-unit (ODU) lines; the indoor-unit quantity field is zero on
every row. From April 2024, every outdoor unit is accompanied by a separate indoor-unit (IDU) line for the matching
indoor model; the invoice number, line item, storage location and dealer fields are blank; and
{f0(Q['exact_duplicates'])} rows ({Q['duplicates_pct']}% of the extract, all in this quarter) are exact copies of
another row. The final quarter, {Q['q1_fy25_share_pct']}% of all rows, is therefore a structurally different
extract appended to the first two years. Figure 3.1 shows that the volume pattern is nonetheless continuous once
the indoor lines are set aside and the duplicates removed.
""")
W.figure(FIG / "fig_monthly_volume.png", "Monthly outdoor-unit billings after cleaning", SRC)
W.h3("Notable features in the data")
W.paras(f"""
The extract describes {Q['materials_total']} material codes, but these are two different things:
{Q['materials_by_group']['RA-ODU']} outdoor-unit models and {Q['materials_by_group']['RA-IDU']} indoor-unit models.
A split air-conditioner is sold as one outdoor and one indoor unit, so the outdoor unit is the natural unit of
demand, and we model the {CL['skus']} outdoor models that recorded positive sales. Table 3.2 lists the fields we
used and how; the full data dictionary appears in Appendix B (Table B.1).
""")
W.table("Fields used in the analysis and their role",
        ["Field", "Content", "Role in the analysis"],
        [["Material", f"Product code; {Q['materials_by_group']['RA-ODU']} ODU and {Q['materials_by_group']['RA-IDU']} IDU codes",
          "SKU key (ODU codes only)"],
         ["SALES OFFICE CODE", "Branch: BLR, COK, MAA, SBD, SBD1", "Branch key"],
         ["Billing Date", "Invoice date", "Aggregated to weeks ending Sunday"],
         ["Billing Quantity ODU", "Units billed; negative for returns", "Demand target (positive lines)"],
         ["EXT MAT GROUP", "RA-ODU or RA-IDU", "Separates outdoor and indoor lines"],
         ["Segment, Star Rating, Tonnage", "Inverter / non-inverter; energy rating; capacity",
          "Product attributes and model features"],
         ["Billing Doc., Item", "Invoice number and line", "Duplicate diagnosis (blank in Apr-Jun 2024)"],
         ["Customer, Dealer Name", "Buyer and channel partner",
          "Concentration statistics only; excluded from models and outputs"]],
        [2300, 3500, 3560], source=SRC, bold_first_col=True)
W.paras(f"""
Three further features shaped our choices. First, {f0(Q['neg_odu_rows'])} outdoor lines carry negative quantities,
which are returns or credit notes rather than demand. Second, three fields (Material.1, SALES OFFICE CODE.1 and
Tonnage.1) are exact copies of others, and one unlabelled column is almost entirely empty; together with the blank
fields of the final quarter, these explain why the extract is only {Q['completeness_pct']}% complete overall but
{Q['completeness_excl_unnamed_pct']}% complete once the empty column is excluded. Third, minor inconsistencies such
as "3 star" alongside "3 Star" ({Q['star_label_inconsistency']} rows) indicate manual entry in places, which we
standardised.
""")
W.h2("3.3  Data Governance and Ethics")
W.paras("""
**Personal data.** The customer field contains the names of individual buyers as well as companies. We treated
the field as personally identifiable information: it was used only to compute anonymous concentration statistics,
was excluded from every model, and appears in no table, figure or output file. All exhibits in this report are
aggregated to SKU, branch or portfolio level, and the manufacturer is not named.

**Approvals and handling.** The extract was shared through Deloitte for the capstone and handled only by team
members. The code repository described in Appendix C contains the analysis scripts; the raw data file must not be
published with it. [Team to confirm: the date of the sponsor's data-handling approval and that the repository is
private or excludes the data files.]

**Known biases.** Billing data record shipments to dealers, not consumer purchases. When a branch ran out of a
model, the lost demand is invisible, so history understates true peak demand for the models most likely to stock
out. Dealer ordering also amplifies consumer demand (Lee et al., 1997): the December spike visible in Figure 3.1,
outside any weather-driven season, is most plausibly year-end channel stocking. Finally, the change in extract
structure in April 2024 means that the most recent, and most relevant, quarter is also the least verifiable.

**Synthetic test records.** During our final audit we found that a working copy of the data used by the project
dashboard ("Filtered.xlsx") contains a second sheet of 5,100 synthetic rows for ten artificial evaluation SKUs,
generated with a fixed random seed to test the dashboard. These rows were never part of the sponsor's data, and we
excluded them from all analysis in this report. Any planning use of the dashboard must exclude them too.
""")
W.takeaways([
    "The forecast informs one weekly decision: how much of each model each branch should request against a "
    "two-week lead time, and how large a buffer to hold.",
    "The outdoor unit is the true unit of demand; the April to June 2024 quarter is structurally different and must "
    "be repaired before it is fully trusted.",
])

# ===========================================================================
# CHAPTER 4
# ===========================================================================
W.h1("Chapter 4: Methodology: Assumptions and Approach", chapter=4)
W.paras("""
Our methodology rests on a small number of explicit assumptions and a single principle: every method is judged
in exactly the way it would be used, forecasting weeks it has not seen from information available at the time.
This chapter states the assumptions, explains why each is reasonable, and then sets out the analytical approach
and tools.
""")
W.h2("4.1  Assumptions")
W.table("Material assumptions, treatment and justification",
        ["Area", "Assumption / treatment", "Justification"],
        [["Demand definition", "Positive ODU billing quantity per SKU, branch and week is the demand to forecast.",
          "Each split system ships one ODU and one IDU; IDU lines exist only from April 2024, so adding them would "
          "double-count the latest quarter."],
         ["Billings as demand", "Shipments to dealers are treated as demand.",
          "The only signal available; its censoring and amplification biases are acknowledged (Sections 3.3 and 10.1)."],
         ["Duplicates", f"The {f0(Q['exact_duplicates'])} exact duplicate rows in Apr-Jun 2024 are removed.",
          "No earlier period contains a single exact duplicate; identical lines with blank invoice numbers are more "
          "plausibly extraction artefacts. A sensitivity figure is reported in Section 5.1."],
         ["Returns", "Negative quantities are excluded from demand and reported separately.",
          f"Returns are {R['returns']['rate_pct']}% of units and relate to past sales, not future demand."],
         ["Time grain", "Weekly buckets ending Sunday; weeks with no sales are recorded as zero.",
          "Matches the weekly replenishment cycle; daily data are too sparse and monthly data too coarse for a "
          "two-week lead time."],
         ["Series start", "A series begins at its first sale; earlier weeks are not counted as zero demand.",
          "Models launched mid-period were not available before launch, so earlier zeros are not true zero demand."],
         ["Independence of errors", "Weekly forecast errors are treated as independent when scaled to the lead time.",
          "Standard in safety-stock practice (Silver et al., 2017); error size is measured empirically, not assumed."],
         ["Lead time and costs", f"Lead time {R['inventory_assumptions']['lead_time_weeks']} weeks; 95% target cycle "
          "service; ₹25,000 per unit; 15% annual holding cost.",
          "Team configuration agreed for the project; indicative, to be replaced with the manufacturer's figures."]],
        [1650, 3700, 4010], source="Source: Team analysis.", bold_first_col=True)
W.paras("""
Of these, the demand definition and the duplicate treatment matter most, because they change the level of demand
in the most recent quarter, which every model relies on most heavily when forecasting the 2024 peak. We return to
their sensitivity in Chapter 5.
""")
W.h2("4.2  Approach and Tools")
W.paras(f"""
Figure 4.1 summarises the analytical pipeline. Raw billing lines are audited and cleaned, aggregated into a weekly
matrix of {CL['series']} SKU × branch series, and profiled using the Syntetos-Boylan classification. Twelve
forecasting methods are then compared in a rolling-origin backtest, and the errors of the leading methods are
converted into safety-stock requirements. The final step, delivery, is the project's planner dashboard, described
in Chapter 8.
""")
W.figure(FIG / "fig_pipeline.png", "Analytical pipeline from raw billing lines to replenishment policy",
         "Source: Team analysis.")
W.h3("Candidate methods")
W.p("We selected candidates to span the families the literature recommends for this kind of demand (Chapter 2), "
    "from the simplest rules a planner might use to a global machine-learning model:")
W.bullets([
    "**Baselines:** naive (next week equals last week), seasonal naive (same week last year), an eight-week moving "
    "average, and simple exponential smoothing (SES) with a smoothing constant of 0.2.",
    "**Statistical:** ARIMA(1,1,1), fitted to each series separately (Box et al., 2015).",
    "**Intermittent-demand:** Croston's method, SBA and TSB, each with a smoothing constant of 0.1, plus a seasonal "
    "SBA that applies SBA to deseasonalised demand and rescales the result with a calendar-month index estimated "
    "from portfolio totals.",
    "**Machine learning:** a global LightGBM model and a global random forest, each trained on all series at once "
    "using the features described in Chapter 6.",
    "**Ensemble:** the simple average of LightGBM and the seasonal SBA, defined before any results were seen.",
])
W.h3("Rolling-origin evaluation")
W.paras(f"""
Each method forecasts one to four weeks ahead from eight forecast origins spaced four weeks apart, the first in the
week ending {pd.Timestamp(R['backtest_design']['origins'][0]):%d %B %Y} and the last in the week ending
{pd.Timestamp(R['backtest_design']['origins'][-1]):%d %B %Y} (Figure 4.2). At each origin, a method sees only data
from earlier weeks: statistical models are refitted, and the machine-learning models are retrained on examples
whose target weeks fall entirely before the origin; this is the time-series analogue of cross-validation (Hyndman &
Athanasopoulos, 2021). The test windows together cover 32 consecutive weeks spanning
the December spike, the 2024 summer peak and the post-season decline, the periods in which forecasting matters
most. A series is scored at an origin once it has at least eight weeks of sales history; newer series are handled
by a fallback rule in deployment.
""")
W.figure(FIG / "fig_folds.png",
         "Rolling-origin backtest design: eight expanding training windows, each followed by a four-week test window",
         "Source: Team analysis.")
W.h3("Metrics and selection")
W.paras("""
Our primary metric is WAPE, computed across all scored series and weeks so that high-volume series carry
proportionate weight. We also report bias (total forecast minus total actual, as a percentage of actual) to show
whether a method systematically over- or under-forecasts, and MASE to compare errors on a scale-free basis
(Hyndman & Koehler, 2006). Because planners act on lead-time totals rather than single weeks, we also compute WAPE
on four-week sums per series and on branch-week totals. We did not use MAPE, which is undefined whenever actual
demand is zero. The overall winner is the method with the lowest WAPE across all folds; separately, we test
whether choosing a method for each series on the first four folds beats a single method on the last four.
""")
W.h3("From forecast error to safety stock")
W.paras("""
For each leading method, we estimated each series' weekly forecast error from the first four folds and set a
safety stock of z × σ × √L, where σ is the root-mean-square weekly error, L is the two-week lead time and z = 1.645
corresponds to a 95% cycle service level (Silver et al., 2017). We then tested these buffers on the last four folds,
March to June 2024, recording how often two-week demand exceeded forecast plus buffer (the achieved cycle service
level), the share of units served from cover (fill rate), and the stock left over at the end of each cycle. This
calibrate-then-test design ensures that buffer performance is also measured out of sample.
""")
W.h3("Tools and technologies")
W.paras("""
All analysis was carried out in Python. We used pandas for data preparation, statsmodels for ARIMA (Seabold &
Perktold, 2010), scikit-learn for the random forest (Pedregosa et al., 2011), LightGBM for gradient boosting (Ke et
al., 2017) and matplotlib for exhibits. The planner dashboard is built in Streamlit with Plotly charts. We chose
this stack because it is open-source, widely supported and runs on a standard laptop: the full backtest of twelve
methods across eight folds completes in about four minutes, short enough to rerun every week.

We considered and set aside two alternatives. Deep-learning sequence models generally need far longer histories
than 103 weeks to outperform tree ensembles, and are harder for planners to interrogate. Hierarchical reconciliation
(for example, MinT; Wickramasuriya et al., 2019) is implemented in the project codebase but was not part of the
final evaluation, because the immediate decision is at SKU × branch level, where bottom-up branch and regional
totals are coherent by construction.
""")
W.takeaways([
    "Every method was judged the way it would be used: forecasting four unseen weeks from eight successive origins "
    "spanning the 2023-24 season.",
    "The assumption most likely to move the results is the treatment of the April to June 2024 duplicates, which "
    "changes recent demand by about a quarter.",
])
