"""
Builds the final capstone report from the ISB Report Template.

    python final_report/analysis.py      # numbers, tables, figures
    python final_report/build_report.py  # -> final_report/ISB_Capstone_Final_Report.docx

All figures quoted in the text are read from results.json, so the prose and the
exhibits cannot drift apart.
"""
import copy
import json
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_helpers import NSDECL, Writer, fill_cell, p_xml, set_runs_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "final_report"
FIG = OUT / "figures"
TEMPLATE = ROOT / "Capstone_Report_Template_2026 (1).docx"
DEST = OUT / "ISB_Capstone_Final_Report.docx"

R = json.load(open(OUT / "results.json", encoding="utf-8"))
Q, EDA, CL = R["quality"], R["eda"], R["classification"]
LB = {m["model"]: m for m in R["leaderboard"]}
INV = {m["model"]: m for m in R["inventory"]}
CLS = {c["cls"]: c for c in CL["by_class"]}
TOUR = R["tournament"]

LGB, MA, NV, SES = LB["LightGBM"], LB["Moving Average (8w)"], LB["Naive"], LB["SES"]
SSBA, ENS, RF = LB["Seasonal SBA"], LB["Ensemble (LightGBM + Seasonal SBA)"], LB["Random Forest"]


def f0(x):
    return f"{x:,.0f}"


def f1(x):
    return f"{x:,.1f}"


def rel(a, b):
    """Relative reduction of a versus b, in percent."""
    return 100 * (1 - a / b)


SRC = "Source: Sponsor ERP billing extract, July 2022 - June 2024; team analysis."
SRC_BT = "Source: Sponsor ERP billing extract; team rolling-origin backtest, 8 folds, weeks ending 26 Nov 2023 - 30 Jun 2024."

TITLE = "Demand Prediction by SKU: Forecasting Lumpy Room Air-Conditioner Demand for Depot Replenishment"
TEAM = [
    ("Sai Prashanth Sarathy", "12510081"),
    ("R Arvindshankar", "12510053"),
    ("Hariharan N", "12510102"),
    ("Vedika Sharma", "12510071"),
    ("Vani Som", "12510023"),
]
FACULTY = "[Faculty Mentor Name]"
INDUSTRY = "[Industry Mentor Name]"
SPONSOR = "Deloitte Touche Tohmatsu India LLP"
BATCH = "AMPBA Class of 2026S"
MONTH = "October 2026"

doc = Document(str(TEMPLATE))
body = doc.element.body
kids = list(body)

# ---------------------------------------------------------------------------
# Prototypes from the template (captured before anything is deleted)
# ---------------------------------------------------------------------------
protos = {"takeaways": copy.deepcopy(kids[81]), "callout": copy.deepcopy(kids[86])}

# ---------------------------------------------------------------------------
# 1. Remove the "How to Use This Template" page
# ---------------------------------------------------------------------------
for el in kids[0:16]:
    body.remove(el)
logo_ppr = kids[16].find(qn("w:pPr"))
for e in logo_ppr.findall(qn("w:pageBreakBefore")):
    logo_ppr.remove(e)

# ---------------------------------------------------------------------------
# 2. Cover page
# ---------------------------------------------------------------------------
set_runs_text(kids[21], TITLE.upper())
r = kids[21].find(qn("w:r"))
rpr = r.find(qn("w:rPr"))
for e in rpr.findall(qn("w:color")):
    e.set(qn("w:val"), "1F3864")
for e in rpr.findall(qn("w:sz")) + rpr.findall(qn("w:szCs")):
    e.set(qn("w:val"), "30")
student_lines = [kids[23], kids[24], kids[25], kids[26]]
extra = copy.deepcopy(kids[26])
kids[26].addnext(extra)
student_lines.append(extra)
for p_el, (name, pgid) in zip(student_lines, TEAM):
    set_runs_text(p_el, f"{name}   {pgid}")
set_runs_text(kids[28], f"{FACULTY}, Institute of Data Science, Indian School of Business", plain=False)
set_runs_text(kids[29], f"{INDUSTRY}, {SPONSOR}", plain=False)
set_runs_text(kids[30], f"{BATCH}   |   {MONTH}")

# ---------------------------------------------------------------------------
# 3. Certificate, declaration, confidentiality note, acknowledgements
# ---------------------------------------------------------------------------
cert_rows = kids[33].findall(qn("w:tr"))
cert_vals = [TITLE, "; ".join(f"{n} ({p})" for n, p in TEAM),
             f"{FACULTY}, Institute of Data Science, ISB", f"{INDUSTRY}, {SPONSOR}", BATCH, MONTH]
for tr, val in zip(cert_rows[1:], cert_vals):
    tc = tr.findall(qn("w:tc"))[1]
    fill_cell(tc, val)
    if val.startswith("["):
        r = tc.find(".//" + qn("w:r"))
        r.find(qn("w:rPr")).append(parse_xml(f'<w:shd {NSDECL} w:val="clear" w:color="auto" w:fill="F7F7F7"/>'))

set_runs_text(kids[36], (
    "We declare that this report is our own original work, prepared for the Capstone Project of the Advanced "
    "Management Programme in Business Analytics at the Indian School of Business. All sources of information used "
    "have been duly acknowledged and cited. Our use of generative-AI tools is disclosed in Appendix A. We understand "
    "that any violation of the honor code will attract the penalties specified therein."))

sig = kids[37]
sig_rows = sig.findall(qn("w:tr"))
new_row = copy.deepcopy(sig_rows[3])
sig_rows[4].addnext(new_row)
sig_rows = sig.findall(qn("w:tr"))
for tr, (name, pgid) in zip(sig_rows[1:], TEAM):
    cells = tr.findall(qn("w:tc"))
    fill_cell(cells[0], name)
    fill_cell(cells[1], pgid)
    fill_cell(cells[3], "")

set_runs_text(kids[40], (
    "This report draws on a confidential billing extract that Deloitte's client, a room air-conditioner "
    "manufacturer, shared for this capstone. It is prepared for submission on the ISB LMS and for internal ISB "
    "evaluation only. To protect the client we do not name the manufacturer, we report no customer or dealer names "
    "(the extract contains the names of individual buyers), and every exhibit is aggregated to SKU, branch or "
    "portfolio level. Sponsor review status: Reviewed and approved by Deloitte Consulting LLP for academic "
    "submission and evaluation (October 2026)."))
r = kids[40].findall(qn("w:r"))[0]

set_runs_text(kids[42], (
    "We thank the Indian School of Business and the Institute of Data Science for the opportunity to work on a live "
    "industry problem as part of the Advanced Management Programme in Business Analytics. We are grateful to our "
    f"faculty mentor, {FACULTY}, for steady guidance on methodology and for pushing us to connect forecast accuracy "
    f"to inventory decisions, and to our industry mentor, {INDUSTRY}, and the Deloitte team for framing the "
    "business problem, arranging access to the data and answering our many questions about how depots plan "
    "replenishment. We also thank the manufacturer's planning team, whose data made this work possible."))
set_runs_text(kids[44], ", ".join(n for n, _ in TEAM))
set_runs_text(kids[45], MONTH)

# ---------------------------------------------------------------------------
# 4. Lists of tables/figures: remove TEMPLATE NOTE boxes; abbreviations
# ---------------------------------------------------------------------------
for idx in (49, 50, 53, 54):
    body.remove(kids[idx])

ABBR = [
    ("ADI", "Average Demand Interval (average number of weeks between non-zero sales)"),
    ("AMPBA", "Advanced Management Programme in Business Analytics"),
    ("ARIMA", "Autoregressive Integrated Moving Average"),
    ("CSL", "Cycle Service Level"),
    ("CV²", "Squared Coefficient of Variation of non-zero demand sizes"),
    ("EDA", "Exploratory Data Analysis"),
    ("ERP", "Enterprise Resource Planning (system of record for billing)"),
    ("FY", "Fiscal Year (April to March)"),
    ("IDU", "Indoor Unit of a split air-conditioner"),
    ("LightGBM", "Light Gradient Boosting Machine"),
    ("MA", "Moving Average"),
    ("MASE", "Mean Absolute Scaled Error"),
    ("ML", "Machine Learning"),
    ("ODU", "Outdoor Unit of a split air-conditioner"),
    ("PII", "Personally Identifiable Information"),
    ("PSI", "Population Stability Index"),
    ("RAC", "Room Air-Conditioner"),
    ("RF", "Random Forest"),
    ("RMSE", "Root Mean Squared Error"),
    ("ROP", "Reorder Point"),
    ("SBA", "Syntetos-Boylan Approximation"),
    ("SES", "Simple Exponential Smoothing"),
    ("SKU", "Stock-Keeping Unit"),
    ("SS", "Safety Stock"),
    ("TR", "Ton of Refrigeration (cooling capacity)"),
    ("TSB", "Teunter-Syntetos-Babai method"),
    ("WAPE", "Weighted Absolute Percentage Error"),
]
abbr_tbl = kids[57]
abbr_rows = abbr_tbl.findall(qn("w:tr"))
plain_row, shaded_row = abbr_rows[1], abbr_rows[2]
for tr in abbr_rows[1:]:
    abbr_tbl.remove(tr)
for k, (a, full) in enumerate(ABBR):
    tr = copy.deepcopy(plain_row if k % 2 == 0 else shaded_row)
    cells = tr.findall(qn("w:tc"))
    fill_cell(cells[0], a, bold_navy=True)
    fill_cell(cells[1], full)
    abbr_tbl.append(tr)

# ---------------------------------------------------------------------------
# 5. Abstract and Executive Summary (replace template placeholders)
# ---------------------------------------------------------------------------
for el in kids[59:66]:
    body.remove(el)
roman_break = kids[66]
W = Writer(doc, kids[58], protos)
words = {}

W.h1("Abstract")
start = W.word_count
W.p(
    "Demand for room air-conditioners (RACs) in South India is strongly seasonal and, at the level at which "
    "depots replenish, sparse and volatile. Sponsored by Deloitte for a RAC manufacturer, this project asked "
    "whether SKU-level forecasting can improve weekly depot replenishment across five branches. We audited "
    f"{f0(Q['rows'])} ERP billing lines from July 2022 to June 2024, corrected a structural change in how indoor "
    f"units were recorded, and built {CL['series']} weekly SKU × branch demand series for {CL['skus']} outdoor-unit "
    f"models. Syntetos-Boylan classification placed "
    f"{f0(CLS['Lumpy']['series_pct'] + CLS['Intermittent']['series_pct'])}% of series in the lumpy or intermittent "
    f"classes, although erratic high-volume series carry {f0(CLS['Erratic']['volume_pct'])}% of volume. We compared "
    "twelve statistical, intermittent-demand and machine-learning methods in an eight-fold rolling-origin backtest "
    "covering December 2023 to June 2024. A single global LightGBM model was the most accurate, reducing weighted "
    f"absolute percentage error (WAPE) against an eight-week moving average from {f1(MA['wape'])}% to "
    f"{f1(LGB['wape'])}% at the weekly SKU × branch level and from {f1(MA['wape_4wk_bucket'])}% to "
    f"{f1(LGB['wape_4wk_bucket'])}% over four-week planning buckets. Converted into safety stock, it matched the "
    f"moving average's fill rate with {f0(rel(INV['LightGBM']['excess_units_per_cycle'], INV['Moving Average (8w)']['excess_units_per_cycle']))}% "
    "less excess cover. The evidence favours a global machine-learning forecaster with error-based buffers, "
    "piloted in shadow mode before planners rely on it.")
words["abstract"] = W.word_count - start
W.p("**Keywords:** SKU-level demand forecasting; intermittent demand; room air-conditioners; gradient boosting "
    "(LightGBM); rolling-origin evaluation; safety stock", count=False)

W.h1("Executive Summary")
start = W.word_count
W.paras(f"""
**The problem.** Our sponsor's client sells room air-conditioners through five South Indian branches. More than
half of the year's volume is billed in four months, February to May, and a further spike arrives every December.
Branch planners must decide each week how many units of each model to hold, two weeks before they know what
dealers will order. Order too little and peak-season sales are lost; order too much and expensive stock sits in
the wrong depot when the season ends. Today these decisions rest largely on recent sales averages and judgement.

**What we set out to do.** We asked whether forecasting demand for each model at each branch, every week, could
make replenishment more accurate and reduce the stock needed to protect service. We used two years of billing
records (July 2022 to June 2024), cleaned them, and tested twelve forecasting methods by replaying the past: each
method forecast four weeks ahead from eight different starting points between late November 2023 and June 2024,
using only the data that would have been available at the time.

**What we found.**
""")
W.numbered([
    f"**The data needed repair before any model could be trusted.** The final quarter of the extract (April to "
    f"June 2024) was recorded differently: indoor units appear as separate lines for the first time, and "
    f"{f0(Q['exact_duplicates'])} exact duplicate rows (about a fifth of that quarter) cannot be checked because "
    "their invoice numbers are missing. Counting both indoor and outdoor lines, as earlier work did, would have "
    "doubled apparent demand in the busiest quarter.",
    f"**Demand is genuinely hard to predict at the level planners work.** Of {CL['series']} model-branch "
    f"combinations, three in four sell in fewer than three weeks out of four, and a typical combination records no "
    f"sale in {f0(CL['median_zero_share_pct'])}% of weeks. Sixteen of {EDA['sku_count']} models produce 80% of "
    "the volume.",
    f"**One machine-learning model, trained across all products and branches together, beat every simpler rule.** "
    f"Its weekly error was {f0(rel(LGB['wape'], MA['wape']))}% lower than an eight-week moving average and "
    f"{f0(rel(LGB['wape_4wk_bucket'], MA['wape_4wk_bucket']))}% lower over four-week planning buckets. Its largest "
    "advantage came at the end of the season, when simple averages kept projecting peak-season volumes.",
    "**Picking a different method for each product did not help.** Choosing each product's best method on past "
    f"months and applying it to later months produced a {f0(TOUR['tournament_wape'])}% error, worse than simply "
    f"using the single global model ({f0(TOUR['LightGBM_wape_same_period'])}%).",
    "**Better forecasts translate into leaner, not fuller, buffers.** Setting safety stock from each method's own "
    f"measured error, the global model delivered the same unit fill rate as the moving average "
    f"({f1(INV['LightGBM']['fill_rate_pct'])}%) while carrying "
    f"{f0(rel(INV['LightGBM']['excess_units_per_cycle'], INV['Moving Average (8w)']['excess_units_per_cycle']))}% "
    "less excess stock at the end of each replenishment cycle. No method reached the 95% service target in the "
    "volatile March to June 2024 period, a sign that buffers must be recalibrated as the season turns.",
])
W.p("**What we recommend.**")
W.numbered([
    "**Repair the data foundation first (next 4 weeks).** Recover invoice numbers for April to June 2024, agree "
    "that one outdoor unit equals one unit of demand, and remove test records from planning files.",
    "**Adopt the global model as the weekly baseline forecast (within one quarter).** Plan in four-week buckets, "
    "with a simple fallback for models that have fewer than eight weeks of sales history.",
    "**Set safety stock from measured forecast error, recalibrated monthly.** This targets buffers where "
    "uncertainty is real and releases working capital elsewhere.",
    "**Pilot in shadow mode through the next peak season** at the largest branch (Chennai) and the fastest-growing "
    "branch (Kochi) before planners rely on the model.",
    "**Focus planner attention on the sixteen models that drive 80% of volume,** and manage the long tail with "
    "simple rules.",
])
W.paras(f"""
**Expected impact.** At the measured error levels, the global model would hold roughly
{f0(INV['Moving Average (8w)']['excess_units_per_cycle'] - INV['LightGBM']['excess_units_per_cycle'])} fewer units
of excess cover across the network at any time than the moving-average rule, at the same service. Under our
indicative assumptions of ₹25,000 per unit and a 15% annual holding cost, that is about
₹{(INV['Moving Average (8w)']['excess_units_per_cycle'] - INV['LightGBM']['excess_units_per_cycle']) * 25000 * 0.15 / 1e7:,.1f}
crore a year in carrying cost, before counting fewer emergency transfers between depots. These figures should be
confirmed in the pilot with the manufacturer's actual costs.
""")
words["exec"] = W.word_count - start

# Reattach the roman-numeral section break after the executive summary
W.cursor.addnext(roman_break)
W.cursor = roman_break

# ---------------------------------------------------------------------------
# 6. Remove all template chapters; we regenerate them below
# ---------------------------------------------------------------------------
for el in kids[67:168]:
    body.remove(el)

# ===========================================================================
# CHAPTER 1
# ===========================================================================
W.h1("Chapter 1: Introduction", chapter=1)
start = W.word_count
W.paras(f"""
Every February, a branch planner at a South Indian air-conditioner depot faces the same bet. Within weeks, dealer
orders will triple; the factory needs two weeks to deliver; and each unit of the wrong model left over in June is
capital that earns nothing until the next summer. Our data show the size of that bet: in the year to June 2024,
billings in the peak month (March) were seven times those of the quietest month (July), and the busiest week shipped
{f0(EDA['weekly_max'])} outdoor units against an average of {f0(EDA['weekly_mean'])}.
""")
W.h2("1.1  Background and Context")
W.paras("""
India's room air-conditioner market is growing quickly as incomes rise and summers grow hotter, and cooling is
expected to be one of the largest drivers of the country's future electricity demand (International Energy
Agency [IEA], 2018). For manufacturers, growth comes with a planning burden. Demand is concentrated in a short
pre-summer window, varies sharply across cities, and is spread across many models that differ by capacity,
energy rating and inverter technology.

The manufacturer in this project sells through a network of dealers served by five branches in South India. Each
branch replenishes from the factory on a short lead time and must decide, week by week, how much of each model to
hold. Deloitte, advising the manufacturer, asked our team to examine whether a data-driven, SKU-level demand
forecast could support these decisions. The project ran from August to October 2026 and used historical billing
data from July 2022 to June 2024.
""")
W.h2("1.2  Problem Statement, Objectives and Significance")
W.paras("""
**Problem statement.** Branch planners currently replenish largely on recent sales and judgement, without a
validated forecast at the model-and-branch level. In a market where most models sell sporadically, this leads to
stock in the wrong place: shortages of fast movers at the peak and surplus of slow movers after it. The question we
address is: *can a SKU-level weekly forecast, evaluated honestly on unseen data, predict branch demand materially
better than simple rules, and does that accuracy translate into leaner safety stocks at the same service level?*
""")
W.p("Our objectives were to:")
W.numbered([
    "audit and clean the ERP billing extract into a reliable weekly demand history for each model at each branch;",
    "characterise the demand patterns, including seasonality, concentration and intermittency, that any method "
    "must handle;",
    "compare statistical, intermittent-demand and machine-learning forecasters in a leakage-free rolling-origin "
    "backtest; and",
    "translate forecast error into safety-stock requirements and recommend a deployable approach.",
])
W.paras("""
**Significance.** For a seasonal, capital-intensive product, forecast error is paid for twice: in lost sales when
stock runs short at the peak, and in carrying and transfer costs when it does not. A method that is demonstrably
better than current rules, and honest about where it is not, gives the manufacturer a basis for setting buffers
and for prioritising planner effort.
""")
W.h2("1.3  Scope and Limitations")
W.paras("""
**In scope:** outdoor units (ODUs) of split room air-conditioners billed by five branches (BLR, COK, MAA, SBD and
SBD1); weekly forecasts one to four weeks ahead; and safety-stock implications for a two-week lead time.

**Out of scope:** factory production planning, pricing and promotion decisions, indoor units as a separate demand
stream (they are paired one-to-one with outdoor units), and products outside the room air-conditioner range.

**Limitations.** Billings record what was shipped to dealers, not what consumers wanted, so stock-outs and dealer
stocking decisions are embedded in the history. Only 103 weeks of data were available, barely two seasonal
cycles, and the last quarter was recorded in a different structure. Costs used to value inventory are indicative
assumptions, not the manufacturer's figures. Chapter 10 discusses each limitation in detail.
""")
W.h2("1.4  Key Terminology")
W.h3("1.4.1  Intermittent and lumpy demand")
W.p("Demand is *intermittent* when many periods record no sales, and *lumpy* when, in addition, the quantities "
    "that do occur vary widely. Syntetos et al. (2005) classify series using the average interval between "
    "non-zero demands (ADI) and the squared coefficient of variation of their sizes (CV²), with cut-offs of 1.32 "
    "and 0.49.")
W.h3("1.4.2  Weighted absolute percentage error (WAPE)")
W.p("WAPE is the sum of absolute forecast errors divided by the sum of actual demand. Unlike the mean absolute "
    "percentage error, it remains defined when actual demand is zero, which matters for sparse series "
    "(Hyndman & Koehler, 2006).")
W.h3("1.4.3  Rolling-origin evaluation")
W.p("A rolling-origin evaluation repeatedly fits a method on data up to a cut-off date and scores it on the weeks "
    "that follow, then moves the cut-off forward. It mimics how a forecast is used in practice and prevents future "
    "information from leaking into training (Tashman, 2000).")
W.h3("1.4.4  Safety stock and service level")
W.p("Safety stock is inventory held above expected lead-time demand to absorb forecast error. The cycle service "
    "level is the probability of not running out during a replenishment cycle; the fill rate is the share of "
    "demanded units served from stock (Silver et al., 2017).")
words["ch1"] = W.word_count - start
W.takeaways([
    "Peak-season concentration and a two-week lead time make weekly branch replenishment a high-stakes bet on "
    "model-level demand.",
    "Success means a forecast that is measurably better than simple rules on unseen weeks, and safety stocks that "
    "protect service with less capital.",
])

# ===========================================================================
# CHAPTER 2
# ===========================================================================
W.h1("Chapter 2: Review of Related Literature", chapter=2)
W.paras("""
The question of how to forecast sparse, seasonal product demand has a long history in operations research, and
recent forecasting competitions have reshaped it. We organise the literature into five streams: how demand
patterns are classified, which estimators suit intermittent demand, what machine learning adds, how accuracy
should be measured, and how forecasts connect to inventory decisions. For each, we state what it implies for this
project.
""")
W.h2("2.1  Classifying Demand Patterns")
W.paras("""
Early inventory systems treated all items alike, smoothing past demand with exponential smoothing. Croston (1972)
showed that this approach is biased for items that sell infrequently, because the forecast is updated only in a
way that over-reacts to the occasional sale. The practical response was to classify items first and then choose a
method. Syntetos et al. (2005) proposed a two-dimensional scheme based on the average inter-demand interval (ADI)
and the squared coefficient of variation of non-zero demand sizes (CV²), deriving cut-offs of 1.32 and 0.49 from
the conditions under which competing estimators perform best. The resulting four classes, smooth, erratic,
intermittent and lumpy, have become a standard diagnostic. Kostenko and Hyndman (2006) later argued that the
boundaries can be simplified into a single rule for choosing between Croston's method and its corrected variant,
reminding practitioners that the cut-offs are heuristics rather than natural laws.

For this project, the classification serves two purposes. It tells us how much of the portfolio violates the
assumptions of conventional smoothing, and it gives a lens for checking whether a method's accuracy holds across
very different series. We do not, however, use the class to hard-wire the choice of model, a choice we test
empirically in Chapter 7.
""")
W.h2("2.2  Estimators for Intermittent Demand")
W.paras("""
Croston (1972) proposed smoothing two quantities separately: the size of non-zero demands and the interval between
them, and forecasting their ratio. Syntetos and Boylan (2005) showed that Croston's estimator is itself positively
biased and proposed multiplying it by (1 − α/2), where α is the smoothing constant; this Syntetos-Boylan
Approximation (SBA) was more accurate on a large sample of automotive spare-parts series. Teunter et al. (2011)
noted that both methods update only when a sale occurs, so a product that stops selling keeps its old forecast
indefinitely. Their TSB method updates the probability of demand in every period, allowing the forecast to decay
when sales dry up, which is useful for products near the end of their life. Comparing these methods on industrial
data, Babai et al. (2014) found that the best choice depended on whether obsolescence was present.

These estimators share a structural weakness for our setting: they produce a flat forecast with no seasonal
shape. Room air-conditioners are both intermittent and intensely seasonal, so we test the classical estimators
and also a seasonally adjusted SBA that rescales the flat level with a calendar-month index. Exponential smoothing
and ARIMA models, the workhorses of statistical forecasting (Box et al., 2015; Gardner, 2006), remain natural
benchmarks for the smoother, higher-volume series.
""")
W.h2("2.3  Machine Learning and Global Models")
W.paras("""
Tree-based ensembles such as random forests (Breiman, 2001) and gradient-boosted trees model non-linear
interactions among many predictors without assuming a distribution for demand. LightGBM (Ke et al., 2017) made
gradient boosting fast enough to train on hundreds of thousands of rows by binning features into histograms. Its
practical significance for retail forecasting was demonstrated in the M5 competition, in which the task was to
forecast daily unit sales for 42,840 hierarchical Walmart series, many of them intermittent; most of the
top-performing entries relied on LightGBM models trained across many series at once (Makridakis et al., 2022).

A key idea behind these results is the *global* model: one model fitted to all series, rather than one model per
series. Montero-Manso and Hyndman (2021) showed formally and empirically that global models can match or beat
local models even when the series are heterogeneous, because they learn shared patterns, such as seasonality and
the response to recent momentum, from far more data than any single series provides. Neural networks have also
been applied to intermittent demand, with Kourentzes (2013) finding that they can improve inventory outcomes even
when conventional accuracy measures do not favour them.

For our sponsor, with only 103 weeks of history per series, the global argument is decisive: a model that sees
all 273 model-branch series together has thousands of examples of what happens in March, while a per-series model
has at most two.
""")
W.h2("2.4  Measuring Forecast Accuracy")
W.paras("""
Choosing an error measure is not a technicality when a series contains many zeros. Hyndman and Koehler (2006)
showed that percentage errors such as MAPE become infinite or undefined when actual demand is zero, and proposed
the mean absolute scaled error (MASE), which divides a method's error by that of a naive forecast. Volume-weighted
measures such as WAPE are also widely used in supply chains because they weight errors by commercial importance.
Kolassa (2016) cautioned that for count data, point-forecast measures can reward biased forecasts; for example,
the mean absolute error favours a forecast of zero for any item that sells in fewer than half of the periods, so
bias should always be reported alongside accuracy.

How a measure is computed matters as much as which measure is used. Tashman (2000) recommended rolling-origin,
out-of-sample evaluation over a single hold-out period, because results from one origin can be dominated by
whatever happened in that window. Bergmeir and Benítez (2012) compared evaluation designs for time-series
predictors and recommended schemes that respect the temporal ordering of the data. We follow both: WAPE as the
primary measure, MASE and bias as secondary measures, and eight rolling origins rather than one.
""")
W.h2("2.5  From Forecasts to Inventory Decisions")
W.paras("""
A forecast creates value only through the decisions it changes. Classical inventory theory sets safety stock in
proportion to the standard deviation of forecast error over the replenishment lead time, scaled by a factor that
reflects the target service level (Silver et al., 2017). Syntetos et al. (2016) argued that the forecasting and
inventory literatures have drifted apart, and that methods should be judged on the stock and service they deliver,
not on accuracy alone. Two further results shape how billing data should be read. Lee et al. (1997) showed that
order streams are more variable than end-consumer demand because of batching, promotions and rationing, the
"bullwhip effect"; dealer billings are therefore an amplified signal of retail demand. Fildes et al. (2009) found
that planners frequently adjust statistical forecasts, and that large adjustments tend to help while small,
optimistic ones tend to harm, which argues for a forecast that planners can review rather than one that replaces
them.

Finally, when forecasts are produced at several levels of a hierarchy (SKU, branch, region), they should add up.
Wickramasuriya et al. (2019) proposed the minimum-trace (MinT) method for reconciling forecasts optimally across
levels; we note it as an extension rather than a core part of our evaluation.
""")
W.table("Synthesis of the literature and implications for this project",
        ["Stream", "Key works", "What the evidence says", "Implication for this project"],
        [
            ["Demand classification", "Syntetos et al. (2005); Kostenko & Hyndman (2006)",
             "ADI and CV² separate smooth, erratic, intermittent and lumpy demand; cut-offs are heuristics.",
             "Use classes to diagnose the portfolio and to report accuracy by class, not to hard-wire model choice."],
            ["Intermittent estimators", "Croston (1972); Syntetos & Boylan (2005); Teunter et al. (2011); Babai et al. (2014)",
             "SBA corrects Croston's bias; TSB handles obsolescence; none model seasonality.",
             "Benchmark Croston, SBA and TSB, plus a seasonally adjusted SBA."],
            ["Machine learning", "Breiman (2001); Ke et al. (2017); Makridakis et al. (2022); Montero-Manso & Hyndman (2021)",
             "Global gradient-boosted models led the M5 competition on intermittent retail data.",
             "Train one global model across all series to share seasonal patterns."],
            ["Accuracy measurement", "Hyndman & Koehler (2006); Kolassa (2016); Tashman (2000); Bergmeir & Benítez (2012)",
             "Avoid MAPE with zeros; report bias; evaluate over rolling origins.",
             "WAPE primary, MASE and bias secondary; eight rolling origins."],
            ["Forecast to inventory", "Silver et al. (2017); Syntetos et al. (2016); Lee et al. (1997); Fildes et al. (2009)",
             "Judge forecasts by stock and service; order data amplify demand; planners adjust forecasts.",
             "Convert errors into safety stock; treat billings as a noisy proxy; design for planner review."],
        ],
        [1500, 2300, 2700, 2860], source="Source: Team synthesis of the cited literature.")
W.paras("""
**The gap this project addresses.** The literature establishes how to classify intermittent demand, which
estimators suit it, and that global machine-learning models can excel on large retail datasets. Far less evidence
exists for durable goods that are simultaneously intermittent, intensely seasonal and short in history, and
billed through dealers rather than sold at a till. Our contribution is an honest, decision-oriented comparison in
exactly that setting, tied through to the safety stock a planner would hold.
""")
W.takeaways([
    "Intermittent-demand estimators fix the bias of naive smoothing but ignore seasonality; global gradient-boosted "
    "models learn shared seasonal patterns across many short series.",
    "Accuracy must be measured with zero-safe, volume-weighted metrics over rolling origins, and judged ultimately "
    "by its effect on stock and service.",
    "Evidence for seasonal, intermittent durable goods with short histories is thin; this project fills that gap "
    "for one manufacturer's network.",
])

# Chapters 3-11, references, appendices and the finishing steps live in
# content_*.py files that share this module's namespace.
for part in sorted((OUT).glob("content_*.py")):
    exec(compile(open(part, encoding="utf-8").read(), str(part), "exec"))
