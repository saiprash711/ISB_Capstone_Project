# Chapters 8-11, references, appendices, about the authors, and saving
# (executed inside build_report.py's namespace)

BR = R["wape_by_branch"]
inv_l, inv_ma = INV["LightGBM"], INV["Moving Average (8w)"]
excess_cut = inv_ma["excess_units_per_cycle"] - inv_l["excess_units_per_cycle"]
excess_pct = rel(inv_l["excess_units_per_cycle"], inv_ma["excess_units_per_cycle"])
excess_value_cr = excess_cut * 25000 / 1e7
carry_cr = excess_value_cr * 0.15
dup_units = q1v["with_duplicates_units"] - q1v["dedup_units"]

# ===========================================================================
# CHAPTER 8
# ===========================================================================
W.h1("Chapter 8: Deployment, Validation and Responsible AI", chapter=8)
W.paras("""
A forecast that is accurate in a backtest but misused in production does more harm than no forecast at all. This
chapter describes how the model would reach planners, how it should be evaluated before it is trusted, where its
risks lie, and how it should be monitored. Because the model forecasts products rather than people, the main
responsible-AI questions concern consistency across branches and product groups, explainability to planners, and
the integrity of the numbers shown to decision-makers.
""")
W.h2("8.1  Deployment and Evaluation")
W.paras("""
**Current delivery vehicle.** The project produced a Streamlit planner dashboard with twelve views in four groups:
exploratory analysis (data quality radar, cleaning studio, statistical deep-dive and an explorer), SKU demand
forecasting (forecast view, model leaderboard and hierarchical reconciliation), operations (forecast monitoring and
drift, inventory intelligence and a scenario simulator) and executive reporting. It runs locally and has also been
deployed as a hosted web application for sponsor demonstrations.

**Proposed production path.** We recommend a weekly batch rather than an interactive model. Each Monday, the
latest week of billings is extracted, validated and appended to the weekly matrix; the global LightGBM model is
retrained on all history (about four minutes on a laptop); and forecasts for the next four weeks, with
error-based safety stocks, are written to a table that the dashboard and the planners' existing spreadsheets read.
Series with fewer than eight weeks of history receive the moving-average forecast until they qualify. Planners can
review and override forecasts, and every override is logged so that its value can be measured, as recommended by
Fildes et al. (2009).

**Evaluation before reliance.** The backtest establishes that the model beats simple rules on history; it does not
establish that it beats experienced planners. We therefore recommend a shadow pilot of at least twelve weeks,
covering the February-to-May 2027 peak, at MAA (the largest branch) and COK (the fastest-growing). During the pilot,
planners continue to decide as today while the model's forecasts are recorded alongside theirs; the comparison of
four-week-bucket WAPE, bias and stock outcomes then decides whether to scale.

**A required correction to the dashboard.** Our audit found that the dashboard's model leaderboard fits each
candidate model on a SKU's full history and scores it on the same weeks, and that its accuracy display substitutes
a bounded proxy whenever WAPE exceeds 100%. Both practices overstate accuracy relative to the out-of-sample figures
in Chapter 7. Before planners use the leaderboard, it must be rebuilt on the rolling-origin results, and the
synthetic test records noted in Section 3.3 must be removed from its data file.
""")
W.h2("8.2  Fairness, Explainability and Risk")
W.paras(f"""
**Consistency across branches and product groups.** The model makes no decisions about individuals, so classical
fairness metrics do not apply. The relevant question is whether forecast quality, and hence service, is
systematically worse for some branches or products. Table 8.1 shows that LightGBM improves on the moving average in
every branch, with WAPE ranging from {f1(min(BR['LightGBM'].values()))}% to {f1(max(BR['LightGBM'].values()))}%.
COK, the fastest-growing branch, has the highest error under both methods, which is consistent with growth eroding
the value of history. Across demand classes and volume tiers (Section 7.3), the long tail of sporadic series is
forecast poorly by every method; for these, the fair and efficient response is a simple rule and a modest buffer
rather than false precision.
""")
W.table("Weekly WAPE (%) by branch",
        ["Branch", "Share of volume %", "Naive", "Moving average (8w)", "SES", "LightGBM", "LightGBM vs moving average"],
        [[b, f1(EDA['branch_share_pct'][b]), f1(BR['Naive'][b]), f1(BR['Moving Average (8w)'][b]), f1(BR['SES'][b]),
          f1(BR['LightGBM'][b]), f"{-rel(BR['LightGBM'][b], BR['Moving Average (8w)'][b]):+.0f}%"]
         for b in EDA['branch_share_pct']],
        [1000, 1300, 1100, 1700, 1000, 1200, 2060], source=SRC_BT, bold_first_col=True)
W.paras("""
**Explainability.** A planner needs to understand why a forecast is high or low before acting on it. Three layers
of explanation are available. Globally, the feature importances in Chapter 6 show that the model is driven mainly
by recent run-rates, adjusted for seasonality and product identity, which matches planners' own intuition. For an
individual forecast, the dashboard can show the inputs that matter most (the 4-, 8- and 13-week averages, last
year's demand in the same weeks and the seasonal index) next to the forecast, and SHAP values (Lundberg & Lee,
2017) can attribute a specific forecast to its features. Finally, the seasonal SBA challenger provides a
transparent cross-check: where the two disagree sharply, the forecast should be reviewed.

**Risks the sponsor should know about.**
""")
W.bullets([
    "**Censored demand:** billings understate demand when stock ran out, so the model learns to under-forecast "
    "exactly the models that sell out; peak-season bias of about -17% is partly this effect.",
    "**Structural breaks:** the April 2024 change in extract structure shows that upstream system changes can "
    "silently alter the data; automated checks (Section 8.3) must catch such breaks before retraining.",
    "**Season-start lag:** in an early or unusually hot season, the model adapts with a lag; peak buffers should be "
    "set from peak-season errors, and planners should be able to apply an explicit seasonal uplift.",
    "**New products:** models with little history are forecast by a fallback rule; launches need planner input.",
    "**Automation bias:** a confident-looking dashboard can lead planners to accept forecasts uncritically; showing "
    "error bands and logging overrides keeps judgement in the loop.",
])
W.h2("8.3  Monitoring Plan")
W.paras("""
The project codebase already contains drift and tracking-signal monitors, but their default health thresholds
(for example, WAPE below 25% counts as healthy) were set without reference to the achievable accuracy for this
portfolio and would flag every series permanently. We recommend relative thresholds, anchored on the backtest, as
set out in Table 8.2.
""")
W.table("Monitoring metrics, triggers and actions",
        ["What is monitored", "Frequency", "Trigger", "Action"],
        [["Data integrity: duplicates, blank invoice numbers, ODU/IDU structure, negative quantities", "Every load",
          "Any exact duplicate, blank key field or new line type", "Block the load; alert data owner"],
         ["4-week-bucket WAPE by branch vs. moving-average benchmark", "Weekly (rolling 8 weeks)",
          "Model worse than benchmark for 2 consecutive periods", "Planner review; investigate features and data"],
         ["Bias by branch, peak vs. off-peak", "Weekly", "Tracking signal beyond ±4 (cumulative error ÷ mean absolute error)",
          "Recalibrate buffers; consider seasonal uplift"],
         ["Demand distribution drift", "Monthly", "Population stability index above 0.25 vs. training window",
          "Retrain and re-run backtest before release"],
         ["Achieved cycle service and fill rate", "Monthly", "Cycle service more than 3 points below target",
          "Recompute safety stocks from recent errors"],
         ["Planner overrides", "Monthly", "Overrides that worsen accuracy on balance", "Review override guidance"]],
        [2900, 1500, 2600, 2360], source="Source: Team analysis.", bold_first_col=True)
W.paras("""
The model is retrained weekly as part of the batch. A full rolling-origin backtest should be repeated monthly and
before any change to features or parameters, so that each released model version carries out-of-sample evidence.
""")
W.takeaways([
    "The single biggest deployment risk is false confidence: the dashboard currently shows in-sample accuracy and "
    "contains synthetic test records, both of which must be fixed before planners rely on it.",
    "Mitigation: release forecasts through a weekly batch with out-of-sample monitoring, and prove value in a shadow "
    "pilot at MAA and COK through the 2027 peak.",
])

# ===========================================================================
# CHAPTER 9
# ===========================================================================
W.h1("Chapter 9: Business Impact and Recommendations", chapter=9)
W.paras(f"""
For the manufacturer, a forecast is worth what it changes in inventory and service. The clearest measurable effect
of moving from the moving-average rule to the global model is less excess stock at the same service: about
{f0(excess_cut)} fewer units of surplus cover across the network at the end of each two-week cycle, roughly
{f0(excess_pct)}% less. This chapter quantifies that effect, sets out our recommendations, and lays out a roadmap.
""")
W.h2("9.1  Recommendations and Business Impact")
W.h3("Quantifying the inventory effect")
W.paras(f"""
Using the method described in Section 4.2, we set safety stocks from each method's own forecast errors in
December 2023 to February 2024 and tested them from March to June 2024 across {R['inventory_series']} series with
sufficient history. Table 9.1 and Figure 9.1 summarise the results.
""")
W.table("Out-of-sample inventory performance of error-based safety stocks, March to June 2024",
        ["Forecast method", "Safety stock (units)", "Cycle service %", "Unit fill rate %", "Excess cover per cycle (units)"],
        [[m, f0(INV[m]['safety_stock_units']), f1(INV[m]['cycle_service_pct']), f1(INV[m]['fill_rate_pct']),
          f0(INV[m]['excess_units_per_cycle'])] for m in INV],
        [3060, 1600, 1500, 1500, 1700],
        source=SRC_BT + " Lead time 2 weeks; 95% target cycle service level.", bold_first_col=True)
W.figure(FIG / "fig_inventory.png", "Excess cover and fill rate by forecast method, March to June 2024", SRC_BT)
W.paras(f"""
Three results matter. First, the global model achieves the same fill rate as the moving average
({f1(inv_l['fill_rate_pct'])}%) with slightly less safety stock and {f0(excess_pct)}% less excess cover: the gain
comes mainly from not over-forecasting after the peak, the error pattern documented in Chapter 7. Second, no method
reached the 95% cycle-service target in this period; the best achieved {f1(max(v['cycle_service_pct'] for v in INV.values()))}%.
The March-to-June 2024 window contained the earliest and steepest peak in the data, so buffers calibrated on the
preceding winter were too small, which is why buffers must be recalibrated as the season turns. Third, the
classical intermittent methods (SBA and seasonal SBA) delivered worse service with more stock, confirming that the
accuracy ranking carries through to inventory outcomes.

**Financial translation (indicative).** At the project's working assumption of ₹25,000 per unit, {f0(excess_cut)}
fewer units of surplus cover correspond to about ₹{excess_value_cr:,.1f} crore less stock positioned at any time,
and, at a 15% annual holding cost, about ₹{carry_cr:,.1f} crore a year in carrying cost. These figures exclude two
benefits we could not measure from billing data, fewer emergency inter-branch transfers and fewer lost peak-season
sales, and depend on assumptions that the manufacturer should replace with its own costs.
""")
W.h3("Recommendations")
W.numbered([
    "**Repair the data foundation before scaling.** Recover invoice numbers for April to June 2024 to settle "
    f"whether the {f0(Q['exact_duplicates'])} duplicate lines ({f0(dup_units)} units, about a quarter of that "
    "quarter's volume) are real; formally adopt the outdoor unit as the unit of demand; and add automated integrity "
    "checks to every data load. *Impact:* removes the largest single uncertainty in recent demand.",
    "**Adopt the global LightGBM model as the weekly baseline forecast.** Run it as a weekly batch at SKU × branch "
    "level, with the moving average as fallback for series with fewer than eight weeks of history, and commit "
    "replenishment on four-week buckets. *Impact:* about "
    f"{f0(rel(LGB['wape_4wk_bucket'], MA['wape_4wk_bucket']))}% lower four-week-bucket error than the moving average.",
    "**Set safety stocks from measured forecast error, recalibrated monthly and separately for the peak.** Use each "
    "series' recent out-of-sample errors (or their empirical quantiles) rather than fixed cover rules. *Impact:* "
    f"about {f0(excess_pct)}% less excess cover at equal fill rate; indicatively ₹{carry_cr:,.1f} crore a year in "
    "carrying cost.",
    "**Pilot in shadow mode at MAA and COK through the February-to-May 2027 peak** before planners rely on the "
    "model. *Impact:* tests the model against planners' actual forecasts rather than proxies.",
    "**Correct the dashboard before wider use.** Replace the in-sample leaderboard with rolling-origin results, "
    "remove the synthetic test records and adopt the relative monitoring thresholds in Table 8.2. *Impact:* "
    "prevents overstated accuracy from reaching decision-makers.",
    f"**Concentrate planner attention where volume is.** The {EDA['skus_for_80pct']} models that make up 80% of "
    "volume merit weekly review; the long tail of sporadic series should run on simple rules with modest buffers. "
    "*Impact:* better use of scarce planning time.",
])
W.h2("9.2  Implementation Roadmap")
W.table("Implementation roadmap",
        ["Recommendation", "Owner", "Timeline", "Expected impact"],
        [["1. Repair data foundation", "Manufacturer IT / data owner, with Deloitte", "Weeks 1-4",
          "Resolves ~26% uncertainty in latest-quarter volume"],
         ["5. Correct the dashboard", "Project team / Deloitte analytics", "Weeks 1-6",
          "Only out-of-sample accuracy shown to planners"],
         ["2. Weekly LightGBM baseline with fallback", "Deloitte analytics with central supply planning", "Weeks 4-12",
          f"~{f0(rel(LGB['wape_4wk_bucket'], MA['wape_4wk_bucket']))}% lower four-week-bucket error"],
         ["3. Error-based safety stocks", "Central supply planning", "Weeks 8-16",
          f"~{f0(excess_pct)}% less excess cover at equal fill rate"],
         ["4. Shadow pilot at MAA and COK", "Branch planners (MAA, COK); Deloitte", "Jan-Jun 2027 (peak season)",
          "Go / no-go evidence for network roll-out"],
         ["6. Focus planner review on top models", "Central supply planning", "From pilot onwards",
          "Planner time aligned with 80% of volume"]],
        [2800, 2500, 1700, 2360], source="Source: Team analysis.", bold_first_col=True)
W.takeaways([
    "Act first on the data: until the April to June 2024 duplicates are resolved at source, about a quarter of "
    "recent demand is uncertain, and every forecast inherits that uncertainty.",
    f"Then deploy the global model with error-based buffers: at equal fill rate it carries about {f0(excess_pct)}% "
    "less surplus stock than the moving-average rule.",
])

# ===========================================================================
# CHAPTER 10
# ===========================================================================
W.h1("Chapter 10: Limitations and Future Scope", chapter=10)
W.paras("""
Our results are more modest, and in some respects more uncertain, than a reader of the project's interim
materials might expect. We state the limitations plainly because the sponsor's decisions depend on knowing where
the evidence is strong and where it is not.
""")
W.h2("10.1  Limitations")
W.paras(f"""
**Billing is not demand.** The history records shipments to dealers. Stock-outs suppress recorded demand, dealer
ordering amplifies and shifts it (Lee et al., 1997), and the December spike is probably channel stocking rather than
consumption. A model trained on billings learns to reproduce these distortions, including under-forecasting models
that habitually sell out.

**Short history and a structural break.** With 103 weeks, the data contain barely two summer peaks, so seasonal
patterns are estimated from one or two observations per week of the year. The last quarter, the most relevant for
forecasting 2024, was recorded differently, lacks invoice numbers, and contains duplicates whose status we could
not verify; our results would change if those {f0(Q['exact_duplicates'])} lines prove genuine.

**A single test season.** The 32 test weeks cover one winter and one summer. Model rankings were consistent across
branches, classes and tiers, but one season cannot reveal how the methods behave in an unusually cool or late
summer.

**No external drivers.** We had no weather, price, promotion, dealer-scheme or competitor data. Temperature in
particular is a plausible leading indicator of the timing of the peak, which is the model's main weakness.

**Simplified inventory analysis.** Our safety-stock analysis assumes a fixed two-week lead time, ignores minimum
order quantities, factory allocation limits and transfers between branches, and values stock at an indicative
₹25,000 per unit. The ranking of methods is robust to these simplifications; the rupee figures are not.

**Limited tuning and scope.** To avoid overfitting a short history, we fixed model settings in advance rather than
tuning them on the test folds; tuning on a separate validation period might improve LightGBM further. We did not
evaluate hierarchical reconciliation, probabilistic (quantile) forecasts, or indoor-unit demand as a separate
stream, and the analysis covers one region of one manufacturer.
""")
W.h2("10.2  Future Scope")
W.bullets([
    "**Add leading indicators:** daily temperature forecasts by city, dealer secondary sales or sell-out data, and "
    "scheme calendars, to anticipate the timing of the peak rather than react to it.",
    "**Forecast distributions, not points:** quantile LightGBM or conformal intervals would give planners direct "
    "service-level quantiles and handle the asymmetric cost of peak-season shortages (Kolassa, 2016).",
    "**Reconcile across the hierarchy:** evaluating MinT reconciliation (Wickramasuriya et al., 2019) would align "
    "SKU, branch and regional plans with the factory's production plan.",
    "**Extend the history and the network:** each additional season roughly doubles the information about "
    "seasonality; extending to other regions would test whether the global model transfers.",
    "**Optimise, not just forecast:** a multi-echelon inventory model with factory allocation constraints would "
    "translate forecasts into network-wide replenishment and transfer decisions.",
])
W.takeaways([
    "The limitation most likely to matter if this work is extended is that billings are censored, amplified "
    "demand; sell-out data and weather drivers would address the model's main weakness, the timing of the peak.",
])

# ===========================================================================
# CHAPTER 11
# ===========================================================================
W.h1("Chapter 11: Conclusion", chapter=11)
W.paras(f"""
We asked whether a SKU-level weekly forecast, evaluated honestly on unseen data, could predict branch demand
materially better than simple rules, and whether that accuracy would translate into leaner safety stocks at the
same service. The answer is a qualified yes.

A single LightGBM model trained across all {CL['series']} model-branch series was the most accurate of twelve
methods in an eight-fold rolling-origin backtest. It reduced error by {f0(rel(LGB['wape'], MA['wape']))}% against
an eight-week moving average at the weekly SKU × branch level and by
{f0(rel(LGB['wape_4wk_bucket'], MA['wape_4wk_bucket']))}% over the four-week buckets in which replenishment is
committed, with the largest gains on the high-volume series and at the end of the season. Converted into
error-based safety stocks, it matched the moving average's fill rate with about {f0(excess_pct)}% less excess cover.

The qualification matters as much as the result. Weekly demand for an individual model at an individual branch
remains intrinsically hard to predict: even the best method's weekly error is close to the size of demand, the
classical intermittent-demand methods offered no advantage, and choosing a different method for each series made
results worse. The value of the forecast lies in aggregate planning quantities and in calibrated buffers, not in
single-week precision.

Finally, the project showed that the data foundation is itself a business issue. Separating indoor from outdoor
units and resolving duplicate lines changed the picture of recent demand by more than any choice of model. With
those repairs made, the global model and error-based buffers deployed through a shadow pilot, and honest monitoring
in place, the manufacturer has a credible path to planning its next peak season with less stock in the wrong place.
""")

# ===========================================================================
# REFERENCES
# ===========================================================================
W.h1("References", chapter="R")
REFS = [
    "Anthropic. (2026). *Claude* (Opus 5.5) [Large language model]. https://claude.ai",
    "Babai, M. Z., Syntetos, A., & Teunter, R. (2014). Intermittent demand forecasting: An empirical study on "
    "accuracy and the risk of obsolescence. *International Journal of Production Economics, 157*, 212–219. "
    "https://doi.org/10.1016/j.ijpe.2014.08.019",
    "Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. "
    "*Information Sciences, 191*, 192–213. https://doi.org/10.1016/j.ins.2011.12.028",
    "Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M. (2015). *Time series analysis: Forecasting and "
    "control* (5th ed.). Wiley.",
    "Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. https://doi.org/10.1023/A:1010933404324",
    "Croston, J. D. (1972). Forecasting and stock control for intermittent demands. *Operational Research "
    "Quarterly, 23*(3), 289–303. https://doi.org/10.2307/3007885",
    "Fildes, R., Goodwin, P., Lawrence, M., & Nikolopoulos, K. (2009). Effective forecasting and judgmental "
    "adjustments: An empirical evaluation and strategies for improvement in supply-chain planning. *International "
    "Journal of Forecasting, 25*(1), 3–23. https://doi.org/10.1016/j.ijforecast.2008.11.010",
    "Gardner, E. S., Jr. (2006). Exponential smoothing: The state of the art—Part II. *International Journal of "
    "Forecasting, 22*(4), 637–666. https://doi.org/10.1016/j.ijforecast.2006.03.005",
    "Google. (2026). *NotebookLM* [Large language model tool]. https://notebooklm.google.com",
    "Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts. "
    "https://otexts.com/fpp3/",
    "Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International "
    "Journal of Forecasting, 22*(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001",
    "International Energy Agency. (2018). *The future of cooling: Opportunities for energy-efficient air "
    "conditioning*. https://www.iea.org/reports/the-future-of-cooling",
    "Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly "
    "efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems, 30*, 3146–3154.",
    "Kolassa, S. (2016). Evaluating predictive count data distributions in retail sales forecasting. "
    "*International Journal of Forecasting, 32*(3), 788–803. https://doi.org/10.1016/j.ijforecast.2015.12.004",
    "Kostenko, A. V., & Hyndman, R. J. (2006). A note on the categorization of demand patterns. *Journal of the "
    "Operational Research Society, 57*(10), 1256–1257. https://doi.org/10.1057/palgrave.jors.2602211",
    "Kourentzes, N. (2013). Intermittent demand forecasts with neural networks. *International Journal of "
    "Production Economics, 143*(1), 198–206. https://doi.org/10.1016/j.ijpe.2013.01.009",
    "Lee, H. L., Padmanabhan, V., & Whang, S. (1997). Information distortion in a supply chain: The bullwhip "
    "effect. *Management Science, 43*(4), 546–558. https://doi.org/10.1287/mnsc.43.4.546",
    "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *Advances in "
    "Neural Information Processing Systems, 30*, 4765–4774.",
    "Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2022). M5 accuracy competition: Results, findings, and "
    "conclusions. *International Journal of Forecasting, 38*(4), 1346–1364. "
    "https://doi.org/10.1016/j.ijforecast.2021.11.013",
    "Montero-Manso, P., & Hyndman, R. J. (2021). Principles and algorithms for forecasting groups of time series: "
    "Locality and globality. *International Journal of Forecasting, 37*(4), 1632–1653. "
    "https://doi.org/10.1016/j.ijforecast.2021.03.004",
    "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., "
    "Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. "
    "(2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.",
    "Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. In S. van "
    "der Walt & J. Millman (Eds.), *Proceedings of the 9th Python in Science Conference* (pp. 92–96). "
    "https://doi.org/10.25080/Majora-92bf1922-011",
    "Silver, E. A., Pyke, D. F., & Thomas, D. J. (2017). *Inventory and production management in supply chains* "
    "(4th ed.). CRC Press.",
    "Syntetos, A. A., Babai, Z., Boylan, J. E., Kolassa, S., & Nikolopoulos, K. (2016). Supply chain forecasting: "
    "Theory, practice, their gap and the future. *European Journal of Operational Research, 252*(1), 1–26. "
    "https://doi.org/10.1016/j.ejor.2015.11.010",
    "Syntetos, A. A., & Boylan, J. E. (2005). The accuracy of intermittent demand estimates. *International "
    "Journal of Forecasting, 21*(2), 303–314. https://doi.org/10.1016/j.ijforecast.2004.10.001",
    "Syntetos, A. A., Boylan, J. E., & Croston, J. D. (2005). On the categorization of demand patterns. *Journal of "
    "the Operational Research Society, 56*(5), 495–503. https://doi.org/10.1057/palgrave.jors.2601841",
    "Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: An analysis and review. *International "
    "Journal of Forecasting, 16*(4), 437–450. https://doi.org/10.1016/S0169-2070(00)00065-0",
    "Teunter, R. H., Syntetos, A. A., & Babai, M. Z. (2011). Intermittent demand: Linking forecasting to inventory "
    "obsolescence. *European Journal of Operational Research, 214*(3), 606–615. "
    "https://doi.org/10.1016/j.ejor.2011.05.018",
    "Wickramasuriya, S. L., Athanasopoulos, G., & Hyndman, R. J. (2019). Optimal forecast reconciliation for "
    "hierarchical and grouped time series through trace minimization. *Journal of the American Statistical "
    "Association, 114*(526), 804–819. https://doi.org/10.1080/01621459.2018.1448825",
]
for ref in REFS:
    W.p(ref, "ReferenceEntry", count=False)

# ===========================================================================
# APPENDICES
# ===========================================================================
W.h1("Appendices", chapter="A")
W.h2("Appendix A: Use of AI Tools Statement")
W.paras("""
The team used generative-AI tools as assistants, not as authors of our reasoning. Table A.1 lists the tools, what
they were used for, and how the output was verified. All numbers in this report are produced by the analysis script
in Appendix C and were checked against its output; every reference was checked against the original source by the
team; and every modelling decision (demand definition, duplicate treatment, candidate models, metrics and the
backtest design) was taken and can be defended by the team. Text drafted with AI assistance was reviewed and
edited by the team, who take full responsibility for it. Claude (Anthropic, 2026) and NotebookLM (Google, 2026)
are cited because wording or structure they suggested was retained in revised form.
""")
ai_rows = [
    ["Claude (Anthropic), Opus 5.5", "Drafting and editing report text from the team's analysis; writing and "
     "debugging the final analysis and figure scripts; checking consistency between text and results",
     "Yes: scripts re-run and outputs checked; text reviewed by all members"],
    ["NotebookLM (Google)", "Generating presentation scripts and practice questions for the mid-review from "
     "team-written source documents", "Yes: reviewed before use; not used for report content"],
    ["[Team to add any other tools, e.g., coding assistants used during dashboard development]", "[Purpose]",
     "[Yes / No]"],
]
W.table("Generative-AI tools used, purpose and verification", ["Tool used", "Purpose", "Verified by team?"],
        ai_rows, [2600, 4360, 2400], bold_first_col=True)

W.h2("Appendix B: Additional Tables and Figures")
W.section("B")
dd = pd.read_csv(OUT / "tables" / "data_dictionary.csv")
W.table("Data dictionary of the raw billing extract",
        ["Field", "Type", "Missing %", "Distinct values", "Description"],
        [[r.Field, r.Type, f"{r._3:.1f}", f0(r.Distinct), r.Description] for r in dd.itertuples()],
        [2100, 900, 1000, 1100, 4260], source=SRC + " Distinct counts for personal fields are shown; values are not.",
        font_half_pts=17)
fold_labels = [f"{pd.Timestamp(o):%d %b %y}" for o in R["backtest_design"]["origins"]]
W.table("Weekly WAPE (%) by backtest fold (fold start date shown)",
        ["Model"] + fold_labels,
        [[m] + [f0(R["wape_by_fold"][m][str(k)]) for k in range(8)] for m in [x["model"] for x in R["leaderboard"]]],
        [2560] + [850] * 8, source=SRC_BT, bold_first_col=True, font_half_pts=17)
W.table("Weekly WAPE (%) by demand class and forecast horizon",
        ["Model", "Smooth", "Erratic", "Intermittent", "Lumpy", "h = 1", "h = 2", "h = 3", "h = 4"],
        [[m] + [f0(R["wape_by_class"][m][c]) for c in ["Smooth", "Erratic", "Intermittent", "Lumpy"]]
         + [f0(R["wape_by_horizon"][m][str(h)]) for h in range(1, 5)] for m in [x["model"] for x in R["leaderboard"]]],
        [2560] + [850] * 8, source=SRC_BT, bold_first_col=True, font_half_pts=17)

W.h2("Appendix C: Code and Reproducibility")
W.paras("""
**Repository.** The project code is held at https://github.com/saiprash711/ISB_Capstone_Project. The repository's
README describes the dashboard; the final-report analysis lives in the folder final_report/.

**Environment.** Python 3.11 or later with the packages in requirements.txt, plus those in
final_report/requirements-report.txt (matplotlib, python-docx and lxml). LightGBM 4, scikit-learn 1.3 or later and
statsmodels 0.14 or later are required.

**Reproducing the key results.** With the sponsor's extract saved as "source data.xlsx" in the repository root
(it is confidential and must be obtained from the sponsor), run:
""")
W.bullets([
    "python final_report/analysis.py: audits and cleans the extract, builds the weekly matrix, classifies demand, "
    "runs the twelve-model rolling-origin backtest and the safety-stock analysis, and writes results.json, the "
    "tables in final_report/tables and every figure in final_report/figures (about four minutes on a laptop);",
    "python final_report/build_report.py: regenerates this report from the ISB template, reading every quoted number "
    "from results.json.",
])
W.paras("""
All random elements (LightGBM subsampling and the random forest) use a fixed seed of 42, so results reproduce
exactly. The rolling-origin design, feature construction and safety-stock calculation are implemented in
final_report/analysis.py; the dashboard's own modules are in src/, with automated tests in tests/.
""")

# ===========================================================================
# ABOUT THE AUTHORS
# ===========================================================================
W.h1("About the Authors", chapter="Z")
BIOS = [
    ("Sai Prashanth Sarathy", "AMPBA participant (PGID 12510081). On this project he led platform architecture and "
     "deployment and built the data ingestion and cleaning pipeline that produces the weekly data mart."),
    ("R Arvindshankar", "AMPBA participant (PGID 12510053). He modelled the branch and SKU hierarchy, implemented "
     "the hierarchical reconciliation methods and the time-series decomposition analysis."),
    ("Hariharan N", "AMPBA participant (PGID 12510102). He designed and built the interactive planner dashboard and "
     "its visualisations, and led the initial data extraction and validation."),
    ("Vedika Sharma", "AMPBA participant (PGID 12510071). She developed the feature engineering, the machine-learning "
     "forecasters, the walk-forward backtesting framework and the leakage audit."),
    ("Vani Som", "AMPBA participant (PGID 12510023). She built the inventory engine, prediction intervals, scenario "
     "simulator and drift monitoring, and led the business-impact analysis."),
]
from docx_helpers import TBL_PR, CELL_MAR  # noqa: E402
_bw = [2600, 6760]


def _cell(text, w, head=False, shade=False):
    fill = ('<w:shd w:val="clear" w:color="auto" w:fill="1F3864"/>' if head else
            ('<w:shd w:val="clear" w:color="auto" w:fill="F5F7F7"/>' if shade else ""))
    style = "TableHead" if head else "TableText"
    para = p_xml(text, style).replace("<w:p " + NSDECL + ">", "<w:p>")
    return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{fill}{CELL_MAR}</w:tcPr>{para}</w:tc>'


# Uncaptioned, as in the template's About the Authors table
_trs = ['<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>'
        + "".join(_cell(h, w, head=True) for h, w in zip(["Name", "Short bio"], _bw)) + "</w:tr>"]
for k, (n_, b_) in enumerate(BIOS):
    _trs.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>'
                + "".join(_cell(v, w, shade=(k % 2 == 1)) for v, w in zip([n_, b_], _bw)) + "</w:tr>")
_grid = "".join('<w:gridCol w:w="%d"/>' % w for w in _bw)
W.raw(f"<w:tbl {NSDECL}>{TBL_PR}<w:tblGrid>{_grid}</w:tblGrid>{''.join(_trs)}</w:tbl>")
W.p("[Team to add one line of professional background for each author if opting in to book-chapter "
    "consideration; otherwise this section may be removed.]", count=False)

# ===========================================================================
# Save
# ===========================================================================
settings = doc.settings.element
if settings.find(qn("w:updateFields")) is None:
    settings.append(parse_xml(f'<w:updateFields {NSDECL} w:val="true"/>'))
doc.core_properties.title = TITLE
doc.core_properties.author = ", ".join(n for n, _ in TEAM)
doc.core_properties.subject = "ISB AMPBA Capstone Project Final Report"
doc.save(str(DEST))
words["body_total"] = W.word_count
json.dump(words, open(OUT / "word_counts.json", "w"), indent=2)
print("Saved", DEST)
print(json.dumps(words, indent=2))
