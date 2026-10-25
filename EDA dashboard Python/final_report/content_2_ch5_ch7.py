# Chapters 5, 6 and 7 (executed inside build_report.py's namespace)

steps = dict(R["cleaning_steps"])
q1v = R["q1_volume"]
q1_uplift = 100 * (q1v["with_duplicates_units"] / q1v["dedup_units"] - 1)
si = EDA["season_index"]
bands = EDA["line_size_bands"]
small_lines = 100 * (bands["1"] + bands["2"]) / sum(bands.values())
TIER = R["wape_by_tier"]
BP = R["bias_peak"]
FI = R["feature_importance_pct"]
FOLD = R["wape_by_fold"]


def grp(names):
    return sum(FI.get(n, 0) for n in names)


fi_level = grp(["roll_mean_4", "roll_mean_8", "roll_mean_13", "roll_mean_26", "lag_1", "lag_2", "lag_3", "lag_4",
                "lag_6", "lag_8", "lag_12", "branch_mean_4", "portfolio_mean_4"])
fi_vol = grp(["roll_std_8", "nonzero_frac_13", "weeks_since_sale"])
fi_season = grp(["woy_sin", "woy_cos", "month_index", "target_month", "portfolio_last_year", "last_year_same_week",
                 "last_year_3wk_mean", "yoy_ratio_4"])
fi_ident = grp(["sku", "branch", "star", "tonnage", "inverter", "age", "horizon"])

# ===========================================================================
# CHAPTER 5
# ===========================================================================
W.h1("Chapter 5: Exploratory Data Analysis", chapter=5)
W.paras(f"""
Exploratory analysis answered one question for the rest of the project: what must a forecasting method cope with?
The answer has four parts: a data structure that changes in the final quarter, a seasonal profile with two peaks, a
demand base concentrated in a few models, branches and customers, and series so sparse that most weeks record no
sale at all.
""")
W.h2("5.1  Data Quality and Cleaning")
W.paras(f"""
Table 5.1 lists the quality issues we found and how each was treated, and Figure 5.1 traces the resulting reduction
from {f0(Q['rows'])} raw rows to {f0(R['clean']['odu_lines'])} positive outdoor-unit demand lines carrying
{f0(R['clean']['odu_units'])} units.
""")
W.table("Data quality issues and their treatment",
        ["Issue", "Extent", "Treatment"],
        [["Exact duplicate rows", f"{f0(Q['exact_duplicates'])} rows ({Q['duplicates_pct']}%), all Apr-Jun 2024, "
          "in groups of two to six or more identical lines", "Removed; sensitivity reported below"],
         ["Indoor-unit lines", f"{f0(R['clean']['idu_lines_set_aside'])} lines after de-duplication, all Apr-Jun 2024",
          "Set aside; IDU demand is paired with ODU demand"],
         ["Returns and credit notes", f"{f0(R['returns']['rows'])} ODU lines, {f0(R['returns']['units'])} units "
          f"({R['returns']['rate_pct']}% of units)", "Excluded from demand; reported separately"],
         ["Zero-quantity lines", f"{f0(R['clean']['zero_lines'])} ODU lines", "Removed (no demand recorded)"],
         ["Blank invoice, item, storage and dealer fields", "All 23,603 rows of Apr-Jun 2024",
          "Fields not used for modelling; flagged to sponsor"],
         ["Redundant and empty columns", "3 duplicate columns; 1 column 99.8% empty", "Dropped"],
         ["Inconsistent labels", f"{Q['star_label_inconsistency']} rows with '3 star' vs '3 Star'", "Standardised"],
         ["Blank trailing row", "1 row", "Removed"]],
        [2700, 3700, 2960], source=SRC, bold_first_col=True)
W.figure(FIG / "fig_cleaning_waterfall.png", "From raw ERP rows to outdoor-unit demand lines", SRC)
W.paras(f"""
The duplicate decision deserves scrutiny because it cannot be verified from the data alone. Without invoice
numbers, two identical lines in April to June 2024 could be one sale extracted twice or two genuine sales of the
same model to the same buyer on the same day. Two facts favour removal: the first 21 months, which carry invoice
numbers, contain no exact duplicates at all, and some lines repeat five or six times, which is implausible for
genuine orders. Keeping the duplicates would raise April to June 2024 outdoor-unit volume by {f0(q1_uplift)}%,
from {f0(q1v['dedup_units'])} to {f0(q1v['with_duplicates_units'])} units. We therefore treat our de-duplicated
figures as the conservative estimate, and recommend that the sponsor resolve the question from source invoices
(Chapter 9).

A related correction concerns earlier project work. Interim analyses counted all {Q['materials_total']} material
codes as separate products and added indoor-unit to outdoor-unit quantities. Because indoor lines exist only from
April 2024, that definition doubled apparent demand in the final quarter and, by adding 84 indoor codes with only
13 weeks of history, overstated the share of sparse series. All figures in this report use the corrected definition
and supersede those interim figures.
""")
W.h2("5.2  Volume over Time and Seasonality")
W.paras(f"""
Weekly demand is highly volatile even at portfolio level: the coefficient of variation of weekly volume is
{EDA['weekly_cv']}, and weekly totals ranged from {f0(EDA['weekly_min'])} to {f0(EDA['weekly_max'])} units (Figure
5.2). The business also grew rapidly: outdoor-unit volume from July to March rose {f1(EDA['yoy_jul_mar']['growth_pct'])}%
from 2022-23 to 2023-24, and April to June 2024 was {f1(EDA['yoy_apr_jun']['growth_pct'])}% above the same quarter
of 2023 even after removing duplicates. A forecasting method that anchors on last year's level, such as a seasonal
naive rule, will therefore under-forecast systematically.
""")
W.figure(FIG / "fig_weekly_total.png", "Weekly outdoor-unit demand across all branches and models", SRC)
W.paras(f"""
Figure 5.3 expresses each calendar month's volume as a ratio to the average month, separately for each year. Two
peaks are clear. The summer peak runs from February to May, which together account for
{f1(EDA['peak_months_share_pct'])}% of annual volume, with March and April at about twice the monthly average. A
second, sharp peak in December ({f1(EDA['dec_share_pct'])}% of volume) coincides with year-end billing rather than
weather, and is consistent with channel stocking by dealers. The monsoon trough is deep: July runs at
{si['Jul22-Jun23']['7']} to {si['Jul23-Jun24']['7']} times the average month. The shape is stable across the two
years, but the timing shifted: in 2024 the peak arrived earlier and was more concentrated in March and April.
""")
W.figure(FIG / "fig_seasonality.png", "Seasonal index of outdoor-unit volume by calendar month, two years compared", SRC)
W.h2("5.3  Branches")
bs, bg = EDA["branch_share_pct"], EDA["branch_growth_pct"]
W.paras(f"""
Volume is concentrated in two branches: MAA accounts for {bs['MAA']}% and SBD for {bs['SBD']}% of outdoor-unit
volume (Figure 5.4). Growth, however, is fastest in the smaller branches: COK grew {f0(bg['COK'])}% and SBD1
{f0(bg['SBD1'])}% between the July-to-March periods of the two years, compared with about 50% for the larger
branches. Fast growth erodes the value of history, because last year's pattern describes a smaller business, so
these branches are where a forecast that adapts quickly to recent levels matters most.
""")
W.figure(FIG / "fig_branches.png", "Branch share of outdoor-unit volume and year-on-year growth", SRC)
W.h2("5.4  Products and Customers")
W.paras(f"""
Demand is concentrated in a small number of models. Of {EDA['sku_count']} outdoor models,
{EDA['skus_for_80pct']} account for 80% of volume and the top ten for {f1(EDA['top10_sku_share_pct'])}% (Figure
5.5). The portfolio is dominated by inverter models ({f1(EDA['segment_share_pct']['Inverter'])}% of volume), by the
3-star and 5-star inverter ratings, and by the 1.5-ton capacity, which alone accounts for
{f1(EDA['tonnage_share_pct']['1.5'])}% (Figure 5.6). Customer demand is also concentrated: the ten largest of
{f0(EDA['customers_odu'])} customers account for {f1(EDA['top10_customer_share_pct'])}% of units and the top 50 for
{f1(EDA['top50_customer_share_pct'])}%. A single large dealer order can therefore dominate a model's week at a
branch, which is one source of the lumpiness discussed next.
""")
W.figure(FIG / "fig_pareto.png", "Cumulative share of outdoor-unit volume by SKU (Pareto curve)", SRC)
W.figure(FIG / "fig_mix.png", "Outdoor-unit volume by segment, star rating and tonnage", SRC)
W.h2("5.5  Order Sizes and Intermittency")
W.paras(f"""
Invoice lines are small and highly skewed: the median line is {f0(EDA['line_qty']['median'])} units, the mean
{EDA['line_qty']['mean']}, and the 99th percentile {f0(EDA['line_qty']['p99'])}, with a skewness of
{EDA['line_qty']['skew']} (Figure 5.7, left). {f0(small_lines)}% of lines are for one or two units. Aggregated to
weeks, most model-branch series record no sale in most weeks: the median series is zero in
{f1(CL['median_zero_share_pct'])}% of the weeks since its first sale (Figure 5.7, right). The distribution is
bimodal: a small group of core models sells nearly every week, while a large tail sells only occasionally.
""")
W.figure(FIG / "fig_distributions.png", "Invoice-line size and the share of zero-demand weeks per SKU × branch series", SRC)
W.h2("5.6  Demand Classification")
W.paras(f"""
Figure 5.8 places each of the {CL['series']} SKU × branch series on the Syntetos-Boylan axes, and Table 5.2
summarises the result. Half of the series ({CLS['Lumpy']['series_pct']}%) are lumpy and a further
{CLS['Intermittent']['series_pct']}% intermittent; only {CLS['Smooth']['series']} series are smooth. Volume tells a
different story: the {CLS['Erratic']['series']} erratic series, which sell most weeks but in widely varying
quantities, carry {CLS['Erratic']['volume_pct']}% of units, while the 65 intermittent series together carry under 1%.
At SKU level (all branches combined), {CL['sku_level'].get('Lumpy', 0)} of {CL['skus']} models are lumpy,
{CL['sku_level'].get('Erratic', 0)} erratic, {CL['sku_level'].get('Intermittent', 0)} intermittent and
{CL['sku_level'].get('Smooth', 0)} smooth.
""")
W.figure(FIG / "fig_sb_matrix.png", "Syntetos-Boylan classification of SKU × branch demand series", SRC)
W.table("Demand classes: number of series and share of volume",
        ["Demand class", "Definition", "Series", "% of series", "% of volume"],
        [[c, d, f0(CLS[c]['series']), f1(CLS[c]['series_pct']), f1(CLS[c]['volume_pct'])]
         for c, d in [("Smooth", "ADI < 1.32, CV² < 0.49"), ("Erratic", "ADI < 1.32, CV² ≥ 0.49"),
                      ("Intermittent", "ADI ≥ 1.32, CV² < 0.49"), ("Lumpy", "ADI ≥ 1.32, CV² ≥ 0.49")]]
        + [["Total", "", f0(CL['series']), "100.0", "100.0"]],
        [1800, 2960, 1400, 1600, 1600], source=SRC, bold_first_col=True)
W.paras("""
The practical message is that no single classical method suits the portfolio. Methods designed for intermittent
demand fit most series but little of the volume; methods for smooth demand fit almost none; and the erratic,
high-volume series that matter most commercially combine frequent sales with sharp swings driven by seasonality and
large orders. This mix is what motivated a method that can learn across series rather than one tuned to a single
demand class.
""")
W.takeaways([
    f"Sixteen models and two branches drive most of the volume, but three in four model-branch series are lumpy or "
    f"intermittent, and the median series records no sale in {f0(CL['median_zero_share_pct'])}% of weeks.",
    "Demand peaks twice, in February to May and in December, and the 2024 peak came earlier; methods anchored on "
    "last year's level or on recent averages will miss the turning points.",
    "The April to June 2024 duplicates change recent volume by about a quarter and must be resolved at source.",
])

# ===========================================================================
# CHAPTER 6
# ===========================================================================
W.h1("Chapter 6: Feature Selection and Engineering", chapter=6)
W.paras("""
For the statistical and intermittent-demand methods, the only input is a series' own history. The machine-learning
models, by contrast, are only as good as the features they are given, and in a time-series setting every feature
is also an opportunity to leak information from the future. This chapter explains which features we built, which
we dropped, and how we kept every feature strictly backward-looking.
""")
W.h2("6.1  Target and Training Design")
W.paras(f"""
The target is weekly outdoor-unit demand for one SKU at one branch. We use a *direct* multi-horizon design: one
model predicts demand one, two, three or four weeks after a forecast origin, using only information available at
the origin, with the horizon itself supplied as a feature. Each training example therefore pairs a feature vector
computed at some past origin with the actual demand some weeks later. At the last backtest origin, the model trains
on {f0(R['ml_training_rows_last_fold'])} such examples drawn from all series, compared with at most about a hundred
weekly observations for any single series. This pooling is what allows a global model to learn the shape of the
season from all series at once (Montero-Manso & Hyndman, 2021).

Weekly demand is non-negative, zero-inflated and right-skewed. Rather than transform the target, we trained
LightGBM with a Tweedie loss, which is designed for exactly this mix of many zeros and occasional large values,
with a variance power of 1.3. The random forest, which has no such loss, was trained on squared error.
""")
W.h2("6.2  Engineered Features")
W.p("We engineered 31 features in six groups (Table 6.1). Every feature is computed from weeks before the forecast "
    "origin, except calendar features of the target week, which are known in advance.")
W.table("Engineered features, rationale and leakage control",
        ["Group", "Features", "Rationale", "Leakage control"],
        [["Recent level", "Demand lags of 1, 2, 3, 4, 6, 8 and 12 weeks; rolling means over 4, 8, 13 and 26 weeks",
          "Captures the current run-rate at several speeds", "All windows end the week before the origin"],
         ["Volatility and intermittency", "8-week rolling standard deviation; share of non-zero weeks in 13 weeks; "
          "weeks since last sale", "Lets the model temper forecasts for sporadic series", "Computed on pre-origin weeks"],
         ["Seasonality", "Same week last year; 3-week mean around it; year-on-year ratio of recent level; calendar-month "
          "seasonal index; week-of-year sine and cosine; target month",
          "Encodes the two seasonal peaks and growth", "Last-year values lie at least 48 weeks before the origin; "
          "the month index uses pre-origin data only"],
         ["Network context", "Portfolio 4-week mean; portfolio volume same week last year; branch 4-week mean",
          "Shares signal from the wider network, e.g. an early season", "Pre-origin weeks only"],
         ["Product and branch", "SKU, branch and star rating (categorical); tonnage; inverter flag",
          "Lets the model learn persistent differences", "Static attributes"],
         ["Life-cycle and horizon", "Weeks since the series' first sale; forecast horizon (1-4)",
          "Distinguishes new from mature models; error grows with horizon", "Known at origin"]],
        [1700, 3000, 2460, 2200], source="Source: Team analysis.", bold_first_col=True)
W.h2("6.3  Features Dropped and Encoding Choices")
W.paras("""
We deliberately excluded several fields. Customer and dealer identities were excluded both because they are
personal or commercially sensitive and because the identity of next week's buyers is not known in advance.
Invoice and line numbers, storage location, the constant product-family fields (SBU and MatGroup3), the duplicated
columns and the text labels for year, month and week carry no information beyond the billing date. Indoor-unit
quantities were excluded because they exist only in the final quarter and mirror outdoor-unit quantities.

Because both machine-learning models are tree ensembles, no scaling or normalisation was needed: trees split on
thresholds and are unaffected by monotonic transformations. LightGBM handled SKU, branch and star rating natively as
categorical variables; for the random forest we used integer codes. Lags that reach back before a series' first
sale were left missing for LightGBM, which learns a default direction for missing values, and set to a sentinel
value for the random forest. We did not use dimensionality reduction: with 31 interpretable features and tens of
thousands of training rows, it would have cost interpretability without a clear gain.
""")
W.h2("6.4  Which Features Mattered")
W.paras(f"""
Figure 6.1 ranks the features by their share of LightGBM's total split gain, averaged over the eight training
folds. Recent level dominates: the rolling means and lags together account for {f0(fi_level)}% of the gain, led by
the 8-week rolling mean alone at {f1(FI['roll_mean_8'])}%. Product and branch identity contribute {f0(fi_ident)}%,
seasonality and calendar features {f0(fi_season)}%, and volatility {f0(fi_vol)}%. Two observations follow. First,
smoothed run-rates are far more informative than any single lag: one week's sales is too noisy to anchor a forecast,
which is also why the naive rule performs poorly beyond one week. Second, the seasonal features, although smaller in
aggregate, are what allow the model to anticipate the end of the peak; Chapter 7 shows that this is precisely where
it gains most over simple averages.
""")
W.figure(FIG / "fig_feature_importance.png", "LightGBM feature importance: share of split gain, mean of eight folds",
         SRC_BT)
W.paras("""
Leakage was guarded in three ways. Every feature was computed by functions that take the forecast origin as an
argument and read only earlier weeks; training examples were restricted to target weeks before the origin; and the
seasonal index was re-estimated at each origin from earlier data only. The project codebase also contains
automated tests that check lag and rolling-window features for look-ahead (tests/test_leakage_audit.py).
""")
W.takeaways([
    f"Smoothed recent run-rates (4- to 13-week means) carry most of the signal; together with lags they account "
    f"for {f0(fi_level)}% of the model's split gain.",
    "Calendar and last-year features are a smaller share but are what let the model anticipate seasonal turning "
    "points that averages miss.",
])

# ===========================================================================
# CHAPTER 7
# ===========================================================================
W.h1("Chapter 7: Modelling and Results", chapter=7)
W.paras(f"""
The headline result is that a single global LightGBM model was the most accurate method on every aggregate
measure, reducing weekly error by {f0(rel(LGB['wape'], MA['wape']))}% relative to an eight-week moving average, but
that weekly demand at SKU × branch level remains difficult for every method. This chapter explains which models we
compared and why, which we shortlisted, and what the results mean for the sponsor.
""")
W.h2("7.1  Models and Metrics Considered")
W.table("Models and metrics considered",
        ["Model", "Brief approach", "Metric(s) and why", "Challenges"],
        [["Naive; seasonal naive", "Repeat last week, or the same week last year",
          "Benchmarks: any useful method must beat them on WAPE", "Naive chases noise; seasonal naive ignores 50-70% growth"],
         ["Moving average (8w); SES", "Average or exponentially weighted average of recent weeks",
          "Proxy for planners' current rules", "Lag behind seasonal turns; flat over the horizon"],
         ["ARIMA(1,1,1)", "Per-series autoregressive model on differenced demand",
          "WAPE and bias; classical statistical benchmark", "Unstable on short, sparse series; needed zero-bounding"],
         ["Croston; SBA; TSB", "Smooth demand size and interval (or probability) separately",
          "WAPE and MASE; designed for intermittent demand", "Flat forecasts with no seasonality"],
         ["Seasonal SBA", "SBA on deseasonalised demand, rescaled by a calendar-month index",
          "Tests whether adding seasonality rescues intermittent methods", "Month index from one to two years of data"],
         ["Random forest (global)", "Bagged regression trees on 31 features across all series",
          "WAPE and bias; non-linear benchmark", "Over-forecasts sparse series; no count-data loss"],
         ["LightGBM (global)", "Gradient-boosted trees with Tweedie loss on 31 features",
          "WAPE, bias, MASE, aggregated WAPE", "Needs feature pipeline and monitoring"],
         ["Ensemble", "Average of LightGBM and seasonal SBA", "Tests whether combining families adds robustness",
          "Inherits seasonal SBA's off-season bias"]],
        [1800, 2600, 2560, 2400], source=SRC_BT, bold_first_col=True)
W.paras("""
WAPE is our primary metric because it weights errors by volume, and units of stock are what the sponsor pays for;
it also remains defined when actual demand is zero. Bias is reported because a forecast that is systematically low
causes stock-outs at the peak however small its average error. MASE complements both by scaling each series' error
by that of a naive forecast, which gives small series equal weight. Because the replenishment decision covers two
to four weeks, we also report WAPE on four-week sums per series and on branch-week totals.
""")
W.h2("7.2  Models Chosen")
W.paras(f"""
Against these metrics we shortlisted three approaches. **LightGBM** is the primary candidate because it had the
lowest WAPE overall, on four-week buckets and on branch totals, and its advantage held across branches and volume
tiers. The **seasonal SBA and the ensemble** are retained as interpretable challengers: their logic, an intermittent
level rescaled by a seasonal index, can be explained in one sentence to a planner, and the ensemble was close to
unbiased overall ({ENS['bias']:+.1f}%) with the second-lowest WAPE. The **moving average** is retained as the fallback for series with
too little history and as the benchmark that any deployed model must continue to beat.
""")
W.h2("7.3  Results")
W.h3("Overall accuracy")
W.table("Backtest results for all twelve methods (ranked by weekly WAPE)",
        ["Model", "Weekly WAPE %", "Bias %", "MASE", "4-week bucket WAPE %", "Branch-week WAPE %"],
        [[m["model"], f1(m["wape"]), f"{m['bias']:+.1f}", f"{m['mase']:.2f}", f1(m["wape_4wk_bucket"]),
          f1(m["wape_branch_week"])] for m in R["leaderboard"]],
        [2860, 1300, 1000, 1000, 1600, 1600], source=SRC_BT, bold_first_col=True)
W.paras(f"""
Table 7.2 and Figure 7.1 report the results over {f0(R['backtest_points'])} scored series-weeks for
{R['backtest_series']} series. Three findings stand out.

**First, weekly SKU × branch demand is hard for every method.** Even the best method has a weekly WAPE of
{f1(LGB['wape'])}%: on average, its absolute weekly error is close to the size of demand itself. This is the
expected consequence of the sparsity documented in Chapter 5, where a single dealer order can make or break a
model's week at a branch, and it is why decisions should not be taken on single-week, single-series forecasts.
Aggregation helps substantially. Over four-week buckets, the level at which replenishment is actually committed,
LightGBM's WAPE falls to {f1(LGB['wape_4wk_bucket'])}%, and for branch-week totals to {f1(LGB['wape_branch_week'])}%.

**Second, the global LightGBM model is best on every volume-weighted measure.** Its weekly WAPE is
{f0(rel(LGB['wape'], MA['wape']))}% lower than the moving average's and {f0(rel(LGB['wape'], NV['wape']))}% lower
than the naive rule's. The margin widens with aggregation: {f0(rel(LGB['wape_4wk_bucket'], MA['wape_4wk_bucket']))}%
lower on four-week buckets and {f0(rel(LGB['wape_branch_week'], MA['wape_branch_week']))}% lower on branch-week
totals. The random forest, trained on the same features, did much worse ({f1(RF['wape'])}% WAPE, {RF['bias']:+.0f}%
bias), mainly because it over-forecast sparse series; the count-appropriate Tweedie loss appears to matter as much
as the features.

**Third, the classical intermittent-demand methods did not help.** Croston, SBA and TSB were no better than simple
smoothing, and adding a seasonal index to SBA raised its bias without reducing its error. On MASE, which gives every
series equal weight regardless of volume, LightGBM ({LGB['mase']:.2f}) merely ties the naive rule and ARIMA,
signalling that its advantage is concentrated in the series that carry volume.
""")
W.figure(FIG / "fig_leaderboard.png", "Weekly WAPE and bias by method", SRC_BT)
W.h3("Where the advantage lies")
ta, tm = TIER["LightGBM"], TIER["Moving Average (8w)"]
W.paras(f"""
Figure 7.2 breaks accuracy down by demand class. LightGBM has the lowest error for the erratic and lumpy series,
which together carry {f0(CLS['Erratic']['volume_pct'] + CLS['Lumpy']['volume_pct'])}% of volume. For the 12 smooth
series the random forest is slightly better ({f1(R['wape_by_class']['Random Forest']['Smooth'])}% against
{f1(R['wape_by_class']['LightGBM']['Smooth'])}%), and for the 65 intermittent series, which carry under 1% of
volume, the naive rule is marginally better. Table 7.3
confirms that the gain is greatest where it matters commercially. For the {R['tier_counts']['A']} "A" series that
make up 80% of volume, LightGBM's WAPE is {f1(ta['A'])}% against {f1(tm['A'])}% for the moving average, a
{f0(rel(ta['A'], tm['A']))}% reduction; in the long tail of "C" series, all methods are poor and LightGBM's
advantage disappears.
""")
W.figure(FIG / "fig_wape_by_class.png", "Weekly WAPE by demand class for three representative methods", SRC_BT)
W.table("Weekly WAPE (%) by volume tier",
        ["Volume tier", "Series", "Naive", "Moving average (8w)", "SES", "Seasonal SBA", "LightGBM"],
        [[f"{t} ({d})", f0(R['tier_counts'][t])] + [f1(TIER[m][t]) for m in
                                                   ["Naive", "Moving Average (8w)", "SES", "Seasonal SBA", "LightGBM"]]
         for t, d in [("A", "top 80% of volume"), ("B", "next 15%"), ("C", "last 5%")]],
        [2360, 900, 1100, 1500, 1100, 1300, 1100], source=SRC_BT, bold_first_col=True)
W.paras(f"""
Timing matters as much as product. Figure 7.3 overlays the aggregate forecasts on actual demand across the 32 test
weeks. During the ramp-up from February to April 2024, the moving average and SES were as accurate as LightGBM
(fold WAPEs of {f1(FOLD['SES']['4'])}% for SES and {f1(FOLD['LightGBM']['4'])}% for LightGBM in the fold starting
17 March). The difference appears at the turning points. When the season ended in May and June, the averaging
methods kept projecting peak-season volume, with fold WAPEs of {f0(FOLD['Moving Average (8w)']['6'])}% and
{f0(FOLD['Moving Average (8w)']['7'])}% for the moving average, while LightGBM, informed by calendar and last-year
features, followed demand down ({f0(FOLD['LightGBM']['6'])}% and {f0(FOLD['LightGBM']['7'])}%). For a seasonal
business, the end of the season is exactly when excess stock is created, so this is where accuracy is worth most.
""")
W.figure(FIG / "fig_actual_vs_forecast.png",
         "Actual versus forecast demand, all series combined, across the eight backtest folds", SRC_BT)
W.paras(f"""
LightGBM's main weakness is bias at the peak. It under-forecast February-to-May demand by
{abs(BP['LightGBM']['peak']):.0f}% while over-forecasting the off-season by {BP['LightGBM']['off_peak']:.0f}%,
whereas the moving average was nearly unbiased at the peak ({BP['Moving Average (8w)']['peak']:+.0f}%) but
over-forecast the off-season by {BP['Moving Average (8w)']['off_peak']:.0f}%. In 2024 the peak was earlier and
steeper than in 2023, and a model that learns partly from last year's pattern adapts with a lag. The practical
remedy, adopted in our recommendations, is to set peak-season buffers from errors measured in the peak itself.

Accuracy also decays with horizon (Figure 7.4). LightGBM's WAPE is about {f0(R['wape_by_horizon']['LightGBM']['1'])}%
one and two weeks ahead and rises to about {f0(R['wape_by_horizon']['LightGBM']['4'])}% three and four weeks ahead.
One week ahead, the naive rule is almost as good ({f1(R['wape_by_horizon']['Naive']['1'])}%), but it deteriorates
quickly thereafter. With a two-week lead time, the one- and two-week horizons are the ones that drive replenishment.
""")
W.figure(FIG / "fig_wape_by_horizon.png", "Weekly WAPE by forecast horizon", SRC_BT)
W.h3("Does choosing a model per series help?")
W.paras(f"""
A common design, and the one used in the project dashboard's model tournament, picks the best method for each
series from past accuracy. We tested this honestly: for each series we selected the method with the lowest error
over the first four folds, then measured it on the last four. Naive and the moving average were selected most often
({TOUR['selected_model_counts'].get('Naive', 0)} and {TOUR['selected_model_counts'].get('Moving Average (8w)', 0)}
series), LightGBM for {TOUR['selected_model_counts'].get('LightGBM', 0)}. The per-series selection achieved a WAPE of
{f1(TOUR['tournament_wape'])}% over the last four folds, worse than applying LightGBM to every series
({f1(TOUR['LightGBM_wape_same_period'])}%). With only a few months of sparse history per series, past winners are
largely winners by chance; a single global model is both more accurate and simpler to govern.
""")
W.takeaways([
    f"A single global LightGBM model is the most accurate method: {f0(rel(LGB['wape_4wk_bucket'], MA['wape_4wk_bucket']))}% "
    f"lower four-week-bucket error than the moving average, and {f0(rel(ta['A'], tm['A']))}% lower weekly error on "
    "the series that carry 80% of volume.",
    "Its edge is greatest at seasonal turning points, where averages over-forecast; its weakness is a lag at the "
    "start of an early, steep peak.",
    "Choosing a model per series on past accuracy is worse than one global model; weekly SKU × branch forecasts "
    "should inform, not dictate, decisions taken over four-week buckets.",
])
