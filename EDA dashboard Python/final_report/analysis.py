"""
Final-report analysis: reproduces every number, table and figure in the
ISB AMPBA capstone final report (Demand Prediction by SKU).

Run from the repository root:
    python final_report/analysis.py

Inputs : "source data.xlsx" (Sheet1, the sponsor's raw ERP billing extract)
Outputs: final_report/results.json, final_report/tables/*.csv, final_report/figures/*.png
"""
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "final_report"
FIG = OUT / "figures"
TAB = OUT / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

SEED = 42
H = 4               # forecast horizon (weeks) per backtest fold
N_FOLDS = 8         # rolling origins, stepped by H weeks, ending at the last week
MIN_HIST = 8        # weeks of history a series needs at an origin to be scored
LEAD_TIME = 2       # replenishment lead time in weeks (config/business_config.yaml)
Z_95 = 1.645        # one-sided z for a 95% cycle service level
UNIT_COST = 25000   # indicative INR cost per unit (ASSUMPTIONS.md)
HOLD_RATE = 0.15    # annual holding-cost rate (ASSUMPTIONS.md)

R = {}  # all results written to results.json


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------------------
# 1. Load and profile the raw extract
# --------------------------------------------------------------------------
log("Loading raw extract")
cache = OUT / "cache_raw.pkl"
if cache.exists():
    raw = pd.read_pickle(cache)
else:
    raw = pd.read_excel(ROOT / "source data.xlsx", sheet_name="Sheet1")
    raw.to_pickle(cache)

q = {
    "rows": int(len(raw)),
    "columns": int(raw.shape[1]),
    "cells": int(raw.size),
    "null_cells": int(raw.isna().sum().sum()),
}
q["completeness_pct"] = round(100 * (1 - q["null_cells"] / q["cells"]), 2)
core = raw.drop(columns=["Unnamed: 1"])  # an unnamed spill-over column, 99.8% empty
q["completeness_excl_unnamed_pct"] = round(100 * (1 - core.isna().sum().sum() / core.size), 2)
q["null_by_column"] = {c: int(v) for c, v in raw.isna().sum().items() if v > 0}

raw = raw.dropna(subset=["Material"]).copy()  # one fully blank trailing row
q["blank_rows"] = q["rows"] - len(raw)
q["date_min"] = str(raw["Billing Date"].min().date())
q["date_max"] = str(raw["Billing Date"].max().date())
q["rows_by_fy"] = raw["Year"].value_counts().to_dict()
q["q1_fy25_share_pct"] = round(100 * (raw["Year"] == "24-25 Q1").mean(), 2)
dup_mask = raw.duplicated(keep="first")
q["exact_duplicates"] = int(dup_mask.sum())
q["duplicates_by_fy"] = raw.loc[dup_mask, "Year"].value_counts().to_dict()
q["duplicates_pct"] = round(100 * dup_mask.mean(), 2)
q["materials_total"] = int(raw["Material"].nunique())
q["materials_by_group"] = raw.groupby("EXT MAT GROUP")["Material"].nunique().to_dict()
q["customers"] = int(raw["Customer"].nunique())
q["dealers"] = int(raw["Dealer Name"].nunique())
q["branches"] = raw["SALES OFFICE CODE"].value_counts().to_dict()
q["neg_odu_rows"] = int((raw["Billing Quantity ODU"] < 0).sum())
q["neg_idu_rows"] = int((raw["Billing Quantity IDU"] < 0).sum())
q["gross_odu"] = float(raw["Billing Quantity ODU"].sum())
q["gross_idu"] = float(raw["Billing Quantity IDU"].sum())
q["idu_qty_before_q1"] = float(raw.loc[raw["Year"] != "24-25 Q1", "Billing Quantity IDU"].sum())
q["idu_rows_before_q1"] = int(((raw["Year"] != "24-25 Q1") & (raw["EXT MAT GROUP"] == "RA-IDU")).sum())
q["star_label_inconsistency"] = int((raw["Star Rating.1"] == "3 star").sum())
R["quality"] = q

# Data dictionary (no personal data values are written out)
desc = {
    "Material": "Product code (SKU); ODU and IDU models carry distinct codes",
    "Unnamed: 1": "Unlabelled spill-over column; header text repeated, otherwise empty",
    "Billing Doc.": "ERP billing document number",
    "Item": "Line item within the billing document",
    "SALES OFFICE CODE": "Branch / depot (BLR, COK, MAA, SBD, SBD1)",
    "EXT MAT GROUP": "Material group: RA-ODU (outdoor) or RA-IDU (indoor)",
    "MatGroup3": "Product family (RA = room air-conditioner)",
    "Star Rating": "Efficiency code (I3S, I5S, N1S, N2S, N3S, IOT)",
    "Segment": "Inverter or Non-inverter",
    "Star Rating.1": "Star rating label (1-5 Star)",
    "Stor. Location": "Storage location code",
    "SALES OFFICE CODE.1": "Duplicate of SALES OFFICE CODE",
    "SBU": "Strategic business unit (RA)",
    "Year": "Fiscal year label (22-23, 23-24, 24-25 Q1)",
    "Month": "Fiscal month label",
    "Week": "Week-of-month label (Wk 1-4)",
    "Billing Date": "Invoice date",
    "Customer": "Billed customer (masked in this report)",
    "Material.1": "Duplicate of Material",
    "Billing Quantity ODU": "Units billed of an outdoor unit (target variable)",
    "Billing Quantity IDU": "Units billed of an indoor unit",
    "Tonnage": "Cooling capacity in tons",
    "Dealer Name": "Channel dealer (masked in this report)",
    "Tonnage.1": "Duplicate of Tonnage",
}
dd_rows = []
src_for_dd = pd.read_pickle(cache)
for c in src_for_dd.columns:
    dd_rows.append({
        "Field": c, "Type": str(src_for_dd[c].dtype).replace("float64", "numeric").replace("object", "text")
        .replace("datetime64[ns]", "date"),
        "Missing %": round(100 * src_for_dd[c].isna().mean(), 1),
        "Distinct": int(src_for_dd[c].nunique()), "Description": desc.get(c, ""),
    })
pd.DataFrame(dd_rows).to_csv(TAB / "data_dictionary.csv", index=False)

# --------------------------------------------------------------------------
# 2. Cleaning waterfall -> ODU demand lines
# --------------------------------------------------------------------------
log("Cleaning")
steps = [("Raw ERP rows", int(q["rows"]))]
df = raw
steps.append(("Blank row removed", len(df)))
df = df.drop_duplicates(keep="first")
steps.append(("Exact duplicates removed", len(df)))
idu = df[df["EXT MAT GROUP"] == "RA-IDU"]
df = df[df["EXT MAT GROUP"] == "RA-ODU"]
steps.append(("IDU component lines set aside", len(df)))
returns = df[df["Billing Quantity ODU"] < 0]
df = df[df["Billing Quantity ODU"] >= 0]
steps.append(("Return / credit lines set aside", len(df)))
zeros = df[df["Billing Quantity ODU"] == 0]
df = df[df["Billing Quantity ODU"] > 0].copy()
steps.append(("Zero-quantity lines removed", len(df)))
R["cleaning_steps"] = steps
R["returns"] = {"rows": int(len(returns)), "units": float(-returns["Billing Quantity ODU"].sum())}
R["clean"] = {
    "odu_lines": int(len(df)),
    "odu_units": float(df["Billing Quantity ODU"].sum()),
    "odu_skus": int(df["Material"].nunique()),
    "idu_lines_set_aside": int(len(idu)),
    "zero_lines": int(len(zeros)),
}
R["returns"]["rate_pct"] = round(100 * R["returns"]["units"] / (R["clean"]["odu_units"] + R["returns"]["units"]), 2)
# sensitivity: Q1 volume if duplicates were genuine repeat lines
q1_raw = raw[(raw["Year"] == "24-25 Q1") & (raw["EXT MAT GROUP"] == "RA-ODU") & (raw["Billing Quantity ODU"] > 0)]
R["q1_volume"] = {
    "dedup_units": float(df.loc[df["Year"] == "24-25 Q1", "Billing Quantity ODU"].sum()),
    "with_duplicates_units": float(q1_raw["Billing Quantity ODU"].sum()),
}

# Attributes per SKU
attrs = (df.groupby("Material")
         .agg(segment=("Segment", "first"), star=("Star Rating", "first"),
              tonnage=("Tonnage", "max")).reset_index())

# --------------------------------------------------------------------------
# 3. EDA statistics
# --------------------------------------------------------------------------
log("EDA")
df["week"] = df["Billing Date"].dt.to_period("W-SUN").dt.end_time.dt.normalize()
df["month"] = df["Billing Date"].dt.to_period("M")
weeks = pd.date_range(df["week"].min(), df["week"].max(), freq="W-SUN")
T = len(weeks)
eda = {"weeks": T, "first_week": str(weeks[0].date()), "last_week": str(weeks[-1].date())}

monthly = df.groupby("month")["Billing Quantity ODU"].sum()
monthly.index = monthly.index.astype(str)
eda["monthly_units"] = monthly.round(1).to_dict()
weekly_total = df.groupby("week")["Billing Quantity ODU"].sum().reindex(weeks, fill_value=0)
eda["weekly_mean"] = round(float(weekly_total.mean()), 1)
eda["weekly_cv"] = round(float(weekly_total.std() / weekly_total.mean()), 2)
eda["weekly_max"] = float(weekly_total.max())
eda["weekly_max_week"] = str(weekly_total.idxmax().date())
eda["weekly_min"] = float(weekly_total.min())

# like-for-like growth: Jul-Mar FY22-23 vs Jul-Mar FY23-24
m = df["Billing Date"].dt.month
p1 = df[(df["Billing Date"] >= "2022-07-01") & (df["Billing Date"] < "2023-04-01")]["Billing Quantity ODU"].sum()
p2 = df[(df["Billing Date"] >= "2023-07-01") & (df["Billing Date"] < "2024-04-01")]["Billing Quantity ODU"].sum()
eda["yoy_jul_mar"] = {"fy23": float(p1), "fy24": float(p2), "growth_pct": round(100 * (p2 / p1 - 1), 1)}
a1 = df[(df["Billing Date"] >= "2023-04-01") & (df["Billing Date"] < "2023-07-01")]["Billing Quantity ODU"].sum()
a2 = df[(df["Billing Date"] >= "2024-04-01") & (df["Billing Date"] < "2024-07-01")]["Billing Quantity ODU"].sum()
eda["yoy_apr_jun"] = {"fy24": float(a1), "fy25": float(a2), "growth_pct": round(100 * (a2 / a1 - 1), 1)}

# seasonality: calendar-month share of the July 2022 - June 2024 volume, by year
mm = df.assign(cm=m, fy=np.where(df["Billing Date"] < "2023-07-01", "Jul22-Jun23", "Jul23-Jun24"))
season = mm.groupby(["fy", "cm"])["Billing Quantity ODU"].sum().unstack(0)
season_idx = season / season.mean()
eda["season_index"] = {str(k): v for k, v in season_idx.round(2).to_dict().items()}
peak = mm.groupby("cm")["Billing Quantity ODU"].sum()
eda["peak_months_share_pct"] = round(100 * peak.loc[[2, 3, 4, 5]].sum() / peak.sum(), 1)
eda["dec_share_pct"] = round(100 * peak.loc[12] / peak.sum(), 1)

br = df.groupby("SALES OFFICE CODE")["Billing Quantity ODU"].sum().sort_values(ascending=False)
eda["branch_units"] = br.to_dict()
eda["branch_share_pct"] = (100 * br / br.sum()).round(1).to_dict()
bg = {}
for b in br.index:
    s = df[df["SALES OFFICE CODE"] == b]
    x1 = s[(s["Billing Date"] >= "2022-07-01") & (s["Billing Date"] < "2023-04-01")]["Billing Quantity ODU"].sum()
    x2 = s[(s["Billing Date"] >= "2023-07-01") & (s["Billing Date"] < "2024-04-01")]["Billing Quantity ODU"].sum()
    bg[b] = round(100 * (x2 / x1 - 1), 1)
eda["branch_growth_pct"] = bg

for col, key in [("Segment", "segment"), ("Star Rating", "star"), ("Tonnage", "tonnage")]:
    s = df.groupby(col)["Billing Quantity ODU"].sum()
    eda[f"{key}_share_pct"] = {str(k): v for k, v in (100 * s / s.sum()).round(1).items()}

sku_vol = df.groupby("Material")["Billing Quantity ODU"].sum().sort_values(ascending=False)
cum = sku_vol.cumsum() / sku_vol.sum()
eda["sku_count"] = int(len(sku_vol))
eda["skus_for_80pct"] = int((cum < 0.8).sum() + 1)
eda["top10_sku_share_pct"] = round(100 * cum.iloc[9], 1)
eda["top20pct_sku_share_pct"] = round(100 * cum.iloc[int(np.ceil(0.2 * len(cum))) - 1], 1)
eda["pareto_curve"] = [round(float(v), 4) for v in cum.values]

cust = df.groupby("Customer")["Billing Quantity ODU"].sum().sort_values(ascending=False)
eda["customers_odu"] = int(len(cust))
eda["top10_customer_share_pct"] = round(100 * cust.iloc[:10].sum() / cust.sum(), 1)
eda["top50_customer_share_pct"] = round(100 * cust.iloc[:50].sum() / cust.sum(), 1)
lines = df["Billing Quantity ODU"]
eda["line_qty"] = {"median": float(lines.median()), "mean": round(float(lines.mean()), 2),
                   "p90": float(lines.quantile(0.9)), "p99": float(lines.quantile(0.99)),
                   "max": float(lines.max()), "skew": round(float(lines.skew()), 2)}
R["eda"] = eda

# --------------------------------------------------------------------------
# 4. Weekly SKU x branch matrix and demand classification
# --------------------------------------------------------------------------
log("Weekly matrix + classification")
wk = df.groupby(["Material", "SALES OFFICE CODE", "week"])["Billing Quantity ODU"].sum()
Ydf = wk.unstack("week").reindex(columns=weeks).fillna(0.0)
keys = Ydf.index.to_frame(index=False).rename(columns={"SALES OFFICE CODE": "branch", "Material": "sku"})
Y = Ydf.values.astype(float)
S = Y.shape[0]
start = np.array([np.flatnonzero(Y[i] > 0)[0] for i in range(S)])


def classify(y):
    nz = y[y > 0]
    adi = len(y) / len(nz)
    cv2 = (nz.std() / nz.mean()) ** 2 if len(nz) > 1 else 0.0
    if adi < 1.32:
        c = "Smooth" if cv2 < 0.49 else "Erratic"
    else:
        c = "Intermittent" if cv2 < 0.49 else "Lumpy"
    return adi, cv2, c


cls_rows = []
for i in range(S):
    adi, cv2, c = classify(Y[i, start[i]:])
    cls_rows.append((adi, cv2, c, Y[i].sum(), T - start[i], float(np.mean(Y[i, start[i]:] == 0))))
keys[["adi", "cv2", "cls", "volume", "age_weeks", "zero_share"]] = pd.DataFrame(cls_rows)
keys = keys.merge(attrs, left_on="sku", right_on="Material", how="left").drop(columns="Material")
keys.to_csv(TAB / "series_classification.csv", index=False)
cc = keys.groupby("cls").agg(series=("sku", "size"), volume=("volume", "sum"))
cc["series_pct"] = (100 * cc["series"] / S).round(1)
cc["volume_pct"] = (100 * cc["volume"] / cc["volume"].sum()).round(1)
R["classification"] = {
    "series": int(S), "skus": int(keys["sku"].nunique()),
    "by_class": cc.reset_index().to_dict(orient="records"),
    "median_zero_share_pct": round(100 * float(keys["zero_share"].median()), 1),
    "series_full_history": int((start == 0).sum()),
    "series_started_q1": int((start >= T - 13).sum()),
}
sk = df.groupby(["Material", "week"])["Billing Quantity ODU"].sum().unstack().reindex(columns=weeks).fillna(0).values
sk_cls = [classify(r[np.flatnonzero(r > 0)[0]:])[2] for r in sk]
R["classification"]["sku_level"] = pd.Series(sk_cls).value_counts().to_dict()

# --------------------------------------------------------------------------
# 5. Forecasting models
# --------------------------------------------------------------------------
def f_naive(y, h):
    return np.full(h, y[-1])


def f_snaive(y_full, t0, h, fallback):
    out = []
    for k in range(h):
        j = t0 + k - 52
        out.append(y_full[j] if j >= 0 else fallback[k])
    return np.array(out)


def f_ma(y, h, w=8):
    return np.full(h, y[-w:].mean())


def f_ses(y, h, alpha=0.2):
    lvl = y[: min(4, len(y))].mean()
    for v in y:
        lvl = lvl + alpha * (v - lvl)
    return np.full(h, lvl)


def f_croston(y, h, alpha=0.1, sba=False):
    nz = np.flatnonzero(y > 0)
    if len(nz) == 0:
        return np.zeros(h)
    z = y[nz].mean()
    p = len(y) / len(nz)
    qn = 1
    for v in y[nz[0] + 1:]:
        if v > 0:
            z += alpha * (v - z)
            p += alpha * (qn - p)
            qn = 1
        else:
            qn += 1
    f = z / p
    if sba:
        f *= 1 - alpha / 2
    return np.full(h, f)


def f_tsb(y, h, alpha=0.1, beta=0.1):
    nz = y[y > 0]
    if len(nz) == 0:
        return np.zeros(h)
    prob = len(nz) / len(y)
    z = nz.mean()
    for v in y:
        if v > 0:
            prob += beta * (1 - prob)
            z += alpha * (v - z)
        else:
            prob += beta * (0 - prob)
    return np.full(h, prob * z)


def f_arima(y, h):
    from statsmodels.tsa.arima.model import ARIMA
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = ARIMA(y, order=(1, 1, 1)).fit()
        return np.maximum(0, res.forecast(h))
    except Exception:
        return f_ma(y, h)


month_of_week = weeks.month.values


def month_index(t0):
    """Calendar-month seasonal index from portfolio totals before week t0."""
    tot = Y[:, :t0].sum(axis=0)
    mo = month_of_week[:t0]
    means = pd.Series(tot).groupby(mo).mean()
    idx = means / tot.mean()
    full = np.ones(13)
    for k, v in idx.items():
        full[k] = max(0.15, v)
    return full


def f_seasonal_sba(y, t_start, t0, h, midx):
    seas = midx[month_of_week[t_start:t0]]
    base = f_croston(y / seas, h, sba=True)
    return base * midx[month_of_week[t0:t0 + h]]


# ---- global ML feature builder -----------------------------------------
b_codes = {b: i for i, b in enumerate(sorted(keys["branch"].unique()))}
s_codes = {s: i for i, s in enumerate(sorted(keys["sku"].unique()))}
seg_code = (keys["segment"] == "Inverter").astype(int).values
star_codes = {s: i for i, s in enumerate(sorted(keys["star"].astype(str).unique()))}
static = np.column_stack([
    keys["branch"].map(b_codes).values, keys["sku"].map(s_codes).values, seg_code,
    keys["star"].astype(str).map(star_codes).values, keys["tonnage"].fillna(0).values,
])
STATIC_NAMES = ["branch", "sku", "inverter", "star", "tonnage"]
TOT = Y.sum(axis=0)
BR_TOT = np.vstack([Y[keys["branch"].values == b].sum(axis=0) for b in sorted(b_codes)])
woy = weeks.isocalendar().week.values.astype(int)


def window_mean(a, lo, hi):
    lo = max(lo, 0)
    if hi <= lo:
        return np.full(a.shape[0], np.nan)
    return a[:, lo:hi].mean(axis=1)


def build_features(s, h, midx):
    """Features available at origin s (data up to s-1) for target week s+h-1."""
    t = s + h - 1
    f = {}
    for k in (1, 2, 3, 4, 6, 8, 12):
        f[f"lag_{k}"] = Y[:, s - k] if s - k >= 0 else np.full(S, np.nan)
    for k in (4, 8, 13, 26):
        f[f"roll_mean_{k}"] = window_mean(Y, s - k, s)
    f["roll_std_8"] = Y[:, max(0, s - 8):s].std(axis=1)
    f["nonzero_frac_13"] = (Y[:, max(0, s - 13):s] > 0).mean(axis=1)
    last_nz = np.array([s - 1 - np.flatnonzero(Y[i, :s][::-1] > 0)[0] if (Y[i, :s] > 0).any() else -1
                        for i in range(S)])
    f["weeks_since_sale"] = np.where(last_nz >= 0, s - last_nz, 99)
    f["age"] = s - start
    f["last_year_same_week"] = Y[:, t - 52] if t - 52 >= 0 else np.full(S, np.nan)
    f["last_year_3wk_mean"] = window_mean(Y, t - 53, t - 50) if t - 53 >= 0 else np.full(S, np.nan)
    ly_base = window_mean(Y, s - 56, s - 52)
    f["yoy_ratio_4"] = np.where(ly_base > 0, f["roll_mean_4"] / np.where(ly_base > 0, ly_base, 1), np.nan)
    f["portfolio_mean_4"] = np.full(S, TOT[max(0, s - 4):s].mean())
    f["portfolio_last_year"] = np.full(S, TOT[t - 52] if t - 52 >= 0 else np.nan)
    br_idx = keys["branch"].map(b_codes).values
    f["branch_mean_4"] = BR_TOT[br_idx, max(0, s - 4):s].mean(axis=1)
    f["month_index"] = np.full(S, midx[month_of_week[t]])
    f["target_month"] = np.full(S, month_of_week[t])
    f["woy_sin"] = np.full(S, np.sin(2 * np.pi * woy[t] / 52))
    f["woy_cos"] = np.full(S, np.cos(2 * np.pi * woy[t] / 52))
    f["horizon"] = np.full(S, h)
    X = np.column_stack([static] + [f[k] for k in f])
    return X, STATIC_NAMES + list(f)


def ml_forecasts(t0, midx, want_importance=False):
    import lightgbm as lgb
    from sklearn.ensemble import RandomForestRegressor

    Xs, ys = [], []
    for s in range(20, t0):
        for h in range(1, H + 1):
            t = s + h - 1
            if t >= t0:
                continue
            X, names = build_features(s, h, midx)
            ok = (s - start) >= 4
            Xs.append(X[ok])
            ys.append(Y[ok, t])
    Xtr = np.vstack(Xs)
    ytr = np.concatenate(ys)
    Xte, rows = [], []
    for h in range(1, H + 1):
        X, names = build_features(t0, h, midx)
        Xte.append(X)
    lgbm = lgb.LGBMRegressor(objective="tweedie", tweedie_variance_power=1.3, n_estimators=500,
                             learning_rate=0.03, num_leaves=31, min_child_samples=40, subsample=0.8,
                             subsample_freq=1, colsample_bytree=0.8, random_state=SEED, verbose=-1)
    lgbm.fit(Xtr, ytr, feature_name=names, categorical_feature=["branch", "sku", "star"])
    rf = RandomForestRegressor(n_estimators=200, max_depth=12, min_samples_leaf=5, max_features=0.5,
                               n_jobs=-1, random_state=SEED)
    rf.fit(np.nan_to_num(Xtr, nan=-1), ytr)
    p_l = np.column_stack([np.maximum(0, lgbm.predict(X)) for X in Xte])
    p_r = np.column_stack([np.maximum(0, rf.predict(np.nan_to_num(X, nan=-1))) for X in Xte])
    imp = None
    if want_importance:
        imp = dict(zip(names, lgbm.booster_.feature_importance(importance_type="gain").tolist()))
    return p_l, p_r, imp, len(ytr)


# --------------------------------------------------------------------------
# 6. Rolling-origin backtest
# --------------------------------------------------------------------------
MODELS = ["Naive", "Seasonal Naive", "Moving Average (8w)", "SES", "ARIMA(1,1,1)", "Croston", "SBA", "TSB",
          "Seasonal SBA", "Random Forest", "LightGBM", "Ensemble (LightGBM + Seasonal SBA)"]
origins = [T - H * (N_FOLDS - k) for k in range(N_FOLDS)]
R["backtest_design"] = {"origins": [str(weeks[o].date()) for o in origins], "horizon": H, "folds": N_FOLDS,
                        "test_start": str(weeks[origins[0]].date()), "test_end": str(weeks[-1].date())}
log(f"Backtest origins: {R['backtest_design']['origins']}")

records = []  # (fold, series, h, model, forecast, actual)
importances = []
train_rows = []
for fi, t0 in enumerate(origins):
    log(f"Fold {fi + 1}/{N_FOLDS} origin {weeks[t0].date()}")
    midx = month_index(t0)
    p_l, p_r, imp, ntr = ml_forecasts(t0, midx, want_importance=True)
    importances.append(imp)
    train_rows.append(ntr)
    for i in range(S):
        if t0 - start[i] < MIN_HIST:
            continue
        y = Y[i, start[i]:t0]
        act = Y[i, t0:t0 + H]
        fc = {
            "Naive": f_naive(y, H),
            "Moving Average (8w)": f_ma(y, H),
            "SES": f_ses(y, H),
            "ARIMA(1,1,1)": f_arima(y, H) if len(y) >= 16 else f_ma(y, H),
            "Croston": f_croston(y, H),
            "SBA": f_croston(y, H, sba=True),
            "TSB": f_tsb(y, H),
            "Seasonal SBA": f_seasonal_sba(y, start[i], t0, H, midx),
            "Random Forest": p_r[i],
            "LightGBM": p_l[i],
        }
        fc["Seasonal Naive"] = f_snaive(Y[i], t0, H, fc["Naive"]) if start[i] <= t0 - 52 else fc["Naive"]
        fc["Ensemble (LightGBM + Seasonal SBA)"] = 0.5 * (fc["LightGBM"] + fc["Seasonal SBA"])
        for mname in MODELS:
            for h in range(H):
                records.append((fi, i, h + 1, mname, float(fc[mname][h]), float(act[h])))

bt = pd.DataFrame(records, columns=["fold", "series", "h", "model", "forecast", "actual"])
bt["cls"] = keys["cls"].values[bt["series"]]
bt["branch"] = keys["branch"].values[bt["series"]]
bt["week_idx"] = np.array(origins)[bt["fold"]] + bt["h"] - 1
bt["err"] = bt["forecast"] - bt["actual"]
bt["abs_err"] = bt["err"].abs()
bt.to_csv(TAB / "backtest_forecasts.csv.gz", index=False, compression="gzip")


def wape(g):
    return 100 * g["abs_err"].sum() / g["actual"].sum()


def bias(g):
    return 100 * g["err"].sum() / g["actual"].sum()


# MASE scale: in-sample one-step naive MAE before the first origin
scale = np.array([np.mean(np.abs(np.diff(Y[i, start[i]:origins[0]]))) if origins[0] - start[i] > 2 else np.nan
                  for i in range(S)])

summary = []
for mname, g in bt.groupby("model"):
    ser = g.groupby("series")["abs_err"].mean()
    sc = scale[ser.index]
    ok = np.isfinite(sc) & (sc > 0)
    # 4-week planning bucket: sum forecast and actual over each fold's 4 weeks
    b4 = g.groupby(["fold", "series"])[["forecast", "actual"]].sum()
    b4w = 100 * (b4["forecast"] - b4["actual"]).abs().sum() / b4["actual"].sum()
    bw = g.groupby(["branch", "week_idx"])[["forecast", "actual"]].sum()
    bww = 100 * (bw["forecast"] - bw["actual"]).abs().sum() / bw["actual"].sum()
    summary.append({"model": mname, "wape": wape(g), "bias": bias(g),
                    "mase": float(np.mean(ser.values[ok] / sc[ok])), "wape_4wk_bucket": b4w,
                    "wape_branch_week": bww})
summ = pd.DataFrame(summary).sort_values("wape").reset_index(drop=True)
summ.round(2).to_csv(TAB / "model_leaderboard.csv", index=False)
R["leaderboard"] = summ.round(2).to_dict(orient="records")
R["backtest_points"] = int(len(bt) / len(MODELS))
R["backtest_series"] = int(bt["series"].nunique())
R["backtest_actual_units"] = float(bt[bt.model == "Naive"]["actual"].sum())
R["ml_training_rows_last_fold"] = int(train_rows[-1])

by_cls = bt.groupby(["model", "cls"]).apply(wape).unstack()
by_cls.round(1).to_csv(TAB / "wape_by_class.csv")
R["wape_by_class"] = {m: by_cls.loc[m].round(1).to_dict() for m in by_cls.index}
by_h = bt.groupby(["model", "h"]).apply(wape).unstack()
R["wape_by_horizon"] = {m: by_h.loc[m].round(1).to_dict() for m in by_h.index}
by_br = bt.groupby(["model", "branch"]).apply(wape).unstack()
R["wape_by_branch"] = {m: by_br.loc[m].round(1).to_dict() for m in by_br.index}
by_fold = bt.groupby(["model", "fold"]).apply(wape).unstack()
R["wape_by_fold"] = {m: by_fold.loc[m].round(1).to_dict() for m in by_fold.index}

# Volume tiers: A = series making up the top 80% of volume, B = next 15%, C = last 5%
vol_rank = keys["volume"].sort_values(ascending=False)
cumv = vol_rank.cumsum() / vol_rank.sum()
tier = pd.Series(np.where(cumv <= 0.80, "A", np.where(cumv <= 0.95, "B", "C")), index=vol_rank.index)
keys["tier"] = tier.reindex(keys.index).values
bt["tier"] = keys["tier"].values[bt["series"]]
by_tier = bt.groupby(["model", "tier"]).apply(wape).unstack()
R["wape_by_tier"] = {m: by_tier.loc[m].round(1).to_dict() for m in by_tier.index}
R["tier_counts"] = keys["tier"].value_counts().to_dict()
R["tier_backtest_counts"] = bt[bt.model == "Naive"].groupby("tier")["series"].nunique().to_dict()
# Peak (Feb-May) vs off-peak bias for key models
bt["peak"] = np.isin(weeks.month.values[bt["week_idx"]], [2, 3, 4, 5])
R["bias_peak"] = {m: {("peak" if k else "off_peak"): round(bias(g), 1) for k, g in gm.groupby("peak")}
                  for m, gm in bt[bt.model.isin(["LightGBM", "Moving Average (8w)", "Seasonal SBA", "Naive"])].groupby("model")}

# Per-series tournament: select on folds 1-4, evaluate on folds 5-8
early = bt[bt.fold < N_FOLDS // 2]
late = bt[bt.fold >= N_FOLDS // 2]
sel = early.groupby(["series", "model"])["abs_err"].sum().unstack().idxmin(axis=1)
late_sel = late[late.apply(lambda r: sel.get(r["series"]) == r["model"], axis=1)]
covered = set(sel.index)
late_cov = late[late.series.isin(covered)]
tour = {"selected_model_counts": sel.value_counts().to_dict(),
        "tournament_wape": round(wape(late_sel), 2), "tournament_bias": round(bias(late_sel), 2)}
for mname in ["LightGBM", "Seasonal SBA", "Ensemble (LightGBM + Seasonal SBA)", "Naive", "Moving Average (8w)"]:
    tour[f"{mname}_wape_same_period"] = round(wape(late_cov[late_cov.model == mname]), 2)
R["tournament"] = tour

# Feature importance (mean gain share across folds)
imp = pd.DataFrame(importances).mean()
imp = (100 * imp / imp.sum()).sort_values(ascending=False)
R["feature_importance_pct"] = imp.round(2).to_dict()

# --------------------------------------------------------------------------
# 7. Inventory translation: safety stock calibrated on folds 1-4, tested on 5-8
# --------------------------------------------------------------------------
log("Inventory analysis")
inv = []
full_series = [i for i in range(S) if origins[0] - start[i] >= MIN_HIST]
for mname in ["Naive", "Moving Average (8w)", "SBA", "Seasonal SBA", "LightGBM", "Ensemble (LightGBM + Seasonal SBA)"]:
    g = bt[(bt.model == mname) & bt.series.isin(full_series)]
    e = g[g.fold < N_FOLDS // 2]
    sigma = e.groupby("series")["err"].apply(lambda v: np.sqrt(np.mean(v ** 2)))
    ss = Z_95 * sigma * np.sqrt(LEAD_TIME)
    lt = g[(g.fold >= N_FOLDS // 2) & (g.h <= LEAD_TIME)].groupby(["fold", "series"])[["forecast", "actual"]].sum()
    lt = lt.join(ss.rename("ss"), on="series")
    cover = lt["forecast"] + lt["ss"]
    short = np.maximum(0, lt["actual"] - cover)
    inv.append({"model": mname, "safety_stock_units": float(ss.sum()),
                "cycle_service_pct": round(100 * float((lt["actual"] <= cover).mean()), 1),
                "fill_rate_pct": round(100 * (1 - short.sum() / lt["actual"].sum()), 1),
                "excess_units_per_cycle": round(float(np.maximum(0, cover - lt["actual"]).sum() / (N_FOLDS // 2)), 0)})
invdf = pd.DataFrame(inv)
base = invdf.loc[invdf.model == "Moving Average (8w)", "safety_stock_units"].iloc[0]
invdf["ss_change_vs_ma_pct"] = (100 * (invdf["safety_stock_units"] / base - 1)).round(1)
invdf["ss_value_inr_cr"] = (invdf["safety_stock_units"] * UNIT_COST / 1e7).round(2)
invdf["annual_holding_inr_lakh"] = (invdf["safety_stock_units"] * UNIT_COST * HOLD_RATE / 1e5).round(1)
invdf.to_csv(TAB / "inventory_comparison.csv", index=False)
R["inventory"] = invdf.to_dict(orient="records")
R["inventory_series"] = len(full_series)
R["inventory_assumptions"] = {"lead_time_weeks": LEAD_TIME, "z": Z_95, "unit_cost_inr": UNIT_COST,
                              "holding_rate": HOLD_RATE}

# --------------------------------------------------------------------------
# 8. Figures
# --------------------------------------------------------------------------
log("Figures")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#a8a7a1", "#e4e3df"
plt.rcParams.update({
    "font.family": "Calibri", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlecolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 220, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(FIG / name, facecolor="white")
    plt.close(fig)


def thousands(x, _=None):
    return f"{x / 1000:,.0f}k" if abs(x) >= 1000 else f"{x:,.0f}"


from matplotlib.ticker import FuncFormatter

# Fig: monthly billings with structural break shaded
fig, ax = plt.subplots(figsize=(7.2, 3.2))
mo = pd.Series(eda["monthly_units"])
x = np.arange(len(mo))
ax.bar(x, mo.values, color=BLUE, width=0.72)
q1pos = [k for k, lab in enumerate(mo.index) if lab >= "2024-04"]
ax.bar(q1pos, mo.values[q1pos], color=ORANGE, width=0.72, label="Apr-Jun 2024 (restructured extract)")
ax.set_xticks(x[::2])
ax.set_xticklabels([pd.Period(p).strftime("%b %y") for p in mo.index[::2]], rotation=0, fontsize=8.5)
ax.yaxis.set_major_formatter(FuncFormatter(thousands))
ax.set_ylabel("ODU units billed (after cleaning)")
ax.legend(loc="upper left", fontsize=8.5)
for k in [x[mo.index.get_loc("2023-04")], x[mo.index.get_loc("2024-03")]]:
    ax.annotate(f"{mo.values[k] / 1000:,.1f}k", (k, mo.values[k]), ha="center", va="bottom", fontsize=8, color=INK2,
                xytext=(0, 2), textcoords="offset points")
save(fig, "fig_monthly_volume.png")

# Fig: cleaning waterfall
fig, ax = plt.subplots(figsize=(7.2, 3.0))
labels = [s[0] for s in steps]
vals = [s[1] for s in steps]
ax.barh(range(len(vals))[::-1], vals, color=[BLUE] + [MUTED] * (len(vals) - 2) + [AQUA], height=0.62)
for k, v in enumerate(vals):
    ax.text(v + 600, len(vals) - 1 - k, f"{v:,}", va="center", fontsize=9, color=INK)
ax.set_yticks(range(len(vals))[::-1])
ax.set_yticklabels(labels)
ax.xaxis.set_major_formatter(FuncFormatter(thousands))
ax.set_xlabel("Rows remaining")
ax.set_xlim(0, max(vals) * 1.13)
ax.grid(axis="y", visible=False)
save(fig, "fig_cleaning_waterfall.png")

# Fig: weekly portfolio demand
fig, ax = plt.subplots(figsize=(7.2, 3.0))
ax.plot(weeks, weekly_total.values, color=BLUE, lw=1.6)
ax.fill_between(weeks, weekly_total.values, color=BLUE, alpha=0.08)
ax.axvspan(pd.Timestamp("2024-04-01"), weeks[-1], color=ORANGE, alpha=0.10, lw=0)
ax.text(pd.Timestamp("2024-04-08"), weekly_total.max() * 0.96, "Apr-Jun 2024", color=INK2, fontsize=8.5)
ax.yaxis.set_major_formatter(FuncFormatter(thousands))
ax.set_ylabel("ODU units per week")
save(fig, "fig_weekly_total.png")

# Fig: seasonal index by month
fig, ax = plt.subplots(figsize=(7.2, 3.0))
order = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
names = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]
xi = np.arange(12)
for col, colr, off, lab in [("Jul22-Jun23", BLUE, -0.19, "Jul 2022 - Jun 2023"), ("Jul23-Jun24", ORANGE, 0.19, "Jul 2023 - Jun 2024")]:
    ax.bar(xi + off, season_idx.loc[order, col].values, width=0.36, color=colr, label=lab)
ax.axhline(1, color=INK2, lw=0.8, ls="--")
ax.set_xticks(xi)
ax.set_xticklabels(names)
ax.set_ylabel("Seasonal index (1.0 = average month)")
ax.legend(loc="upper left", fontsize=8.5)
save(fig, "fig_seasonality.png")

# Fig: branch share and growth
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
bs = pd.Series(eda["branch_share_pct"])
axes[0].barh(bs.index[::-1], bs.values[::-1], color=BLUE, height=0.6)
for k, v in enumerate(bs.values[::-1]):
    axes[0].text(v + 0.6, k, f"{v:.1f}%", va="center", fontsize=9)
axes[0].set_xlim(0, bs.max() * 1.25)
axes[0].set_title("Share of ODU volume", loc="left", fontsize=10)
axes[0].grid(axis="y", visible=False)
gr = pd.Series(eda["branch_growth_pct"]).reindex(bs.index)
axes[1].barh(gr.index[::-1], gr.values[::-1], color=AQUA, height=0.6)
for k, v in enumerate(gr.values[::-1]):
    axes[1].text(v + 2, k, f"+{v:.0f}%", va="center", fontsize=9)
axes[1].set_xlim(0, gr.max() * 1.25)
axes[1].set_title("Growth, Jul-Mar FY24 vs FY23", loc="left", fontsize=10)
axes[1].grid(axis="y", visible=False)
fig.tight_layout()
save(fig, "fig_branches.png")

# Fig: Pareto
fig, ax = plt.subplots(figsize=(7.2, 2.9))
pc = np.array(eda["pareto_curve"]) * 100
ax.plot(np.arange(1, len(pc) + 1), pc, color=BLUE, lw=2)
k80 = eda["skus_for_80pct"]
ax.axhline(80, color=MUTED, lw=0.8, ls="--")
ax.axvline(k80, color=MUTED, lw=0.8, ls="--")
ax.plot([k80], [pc[k80 - 1]], "o", color=ORANGE, ms=7, mec="white", mew=1.5)
ax.annotate(f"{k80} of {len(pc)} SKUs = 80% of volume", (k80, pc[k80 - 1]), xytext=(10, -22),
            textcoords="offset points", fontsize=9, color=INK)
ax.set_xlabel("ODU SKUs ranked by volume")
ax.set_ylabel("Cumulative share of volume (%)")
ax.set_ylim(0, 102)
save(fig, "fig_pareto.png")

# Fig: ADI vs CV2
fig, ax = plt.subplots(figsize=(7.2, 3.6))
sz = 8 + 140 * np.sqrt(keys["volume"] / keys["volume"].max())
ax.scatter(keys["adi"], keys["cv2"], s=sz, color=BLUE, alpha=0.55, edgecolor="white", lw=0.6)
ax.axvline(1.32, color=INK2, lw=0.9, ls="--")
ax.axhline(0.49, color=INK2, lw=0.9, ls="--")
ax.set_xscale("log")
ax.set_xlabel("Average demand interval, ADI (weeks, log scale)")
ax.set_ylabel("Squared coefficient of variation, CV²")
cnt = keys["cls"].value_counts()
ymax = keys["cv2"].quantile(0.99) * 1.1
ax.set_ylim(-0.05, ymax)
ax.set_xlim(0.7, 130)
ax.text(1.27, ymax * 0.97, "Erratic", fontsize=9, fontweight="bold", ha="right", va="top")
ax.text(1.27, 0.52, "Smooth", fontsize=9, fontweight="bold", ha="right", va="bottom")
ax.text(1.40, ymax * 0.97, "Lumpy", fontsize=9, fontweight="bold", ha="left", va="top")
ax.text(1.40, 0.52, "Intermittent", fontsize=9, fontweight="bold", ha="left", va="bottom")
ax.text(0.985, 0.96, "Series per quadrant\n"
        f"Smooth {cnt.get('Smooth', 0)}  ·  Erratic {cnt.get('Erratic', 0)}\n"
        f"Intermittent {cnt.get('Intermittent', 0)}  ·  Lumpy {cnt.get('Lumpy', 0)}",
        transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=INK,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRID))
ax.text(0.985, 0.06, "Bubble area proportional to series volume", transform=ax.transAxes, ha="right",
        fontsize=8, color=INK2)
save(fig, "fig_sb_matrix.png")

# Fig: order-line size distribution and zero share
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
edges = [0, 1, 2, 5, 10, 20, 50, 100, np.inf]
blabels = ["1", "2", "3-5", "6-10", "11-20", "21-50", "51-100", ">100"]
bands = pd.cut(lines, edges, labels=blabels, right=True).value_counts().reindex(blabels)
axes[0].bar(blabels, bands.values / 1000, color=BLUE, width=0.7)
axes[0].set_xlabel("Units per invoice line")
axes[0].set_ylabel("Invoice lines (thousands)")
axes[0].tick_params(axis="x", labelsize=8)
axes[0].grid(axis="x", visible=False)
eda["line_size_bands"] = bands.astype(int).to_dict()
axes[0].set_title("Invoice-line size", loc="left", fontsize=10)
axes[1].hist(100 * keys["zero_share"], bins=20, color=AQUA, edgecolor="white", lw=0.5)
axes[1].set_xlabel("Share of weeks with zero sales (%)")
axes[1].set_ylabel("SKU × branch series")
axes[1].set_title("Zero-demand weeks per series", loc="left", fontsize=10)
fig.tight_layout()
save(fig, "fig_distributions.png")

# Fig: product mix
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))
for ax, key, title in [(axes[0], "segment_share_pct", "Segment"), (axes[1], "star_share_pct", "Star rating"),
                       (axes[2], "tonnage_share_pct", "Tonnage (TR)")]:
    s = pd.Series(eda[key]).sort_values()
    s = s[s >= 0.5]
    ax.barh([str(i) for i in s.index], s.values, color=BLUE, height=0.6)
    for k, v in enumerate(s.values):
        ax.text(v + 1, k, f"{v:.0f}%", va="center", fontsize=8.5)
    ax.set_xlim(0, s.max() * 1.35)
    ax.set_title(title, loc="left", fontsize=10)
    ax.grid(axis="y", visible=False)
    ax.set_xticks([])
fig.tight_layout()
save(fig, "fig_mix.png")

# Fig: model leaderboard
fig, ax = plt.subplots(figsize=(7.2, 3.6))
lb = summ.sort_values("wape", ascending=False)
colors = [AQUA if m in ("LightGBM", "Ensemble (LightGBM + Seasonal SBA)", "Random Forest") else
          (ORANGE if m == "Seasonal SBA" else BLUE) for m in lb["model"]]
colors = [AQUA if m in ("LightGBM", "Ensemble (LightGBM + Seasonal SBA)", "Random Forest") else BLUE
          for m in lb["model"]]
ax.barh(lb["model"], lb["wape"], color=colors, height=0.62)
for k, (v, b) in enumerate(zip(lb["wape"], lb["bias"])):
    ax.text(v + 1, k, f"{v:.1f}%  (bias {b:+.0f}%)", va="center", fontsize=8.5)
ax.set_xlim(0, lb["wape"].max() * 1.32)
ax.set_xlabel("WAPE, weekly SKU × branch, Dec 2023 - Jun 2024 (%)")
ax.grid(axis="y", visible=False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=AQUA, label="Machine learning (global)"),
                   Patch(color=BLUE, label="Statistical / baseline (per series)")],
          loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=8.5)
save(fig, "fig_leaderboard.png")

# Fig: WAPE by class for key models
fig, ax = plt.subplots(figsize=(7.2, 3.0))
key_models = [("Moving Average (8w)", BLUE), ("Seasonal SBA", ORANGE), ("LightGBM", AQUA)]
classes = ["Smooth", "Erratic", "Intermittent", "Lumpy"]
xi = np.arange(len(classes))
for k, (mname, colr) in enumerate(key_models):
    vals = [by_cls.loc[mname].get(c, np.nan) for c in classes]
    ax.bar(xi + (k - 1) * 0.26, vals, width=0.24, color=colr, label=mname)
ax.set_xticks(xi)
ax.set_xticklabels(classes)
ax.set_ylabel("WAPE (%)")
ax.legend(fontsize=8.5, loc="upper left", ncol=3)
ax.set_ylim(0, np.nanmax(by_cls.loc[[m for m, _ in key_models], classes].values) * 1.18)
save(fig, "fig_wape_by_class.png")

# Fig: aggregate actual vs forecast over the test window
fig, ax = plt.subplots(figsize=(7.2, 3.1))
agg = bt[bt.model.isin(["Moving Average (8w)", "Seasonal SBA", "LightGBM"])].groupby(["model", "week_idx"])[["forecast", "actual"]].sum()
wi = sorted(bt["week_idx"].unique())
dates = weeks[wi]
ax.plot(dates, agg.loc["LightGBM"]["actual"].values, color=INK, lw=2, label="Actual")
for mname, colr in key_models:
    ax.plot(dates, agg.loc[mname]["forecast"].values, color=colr, lw=1.6, label=mname)
for o in origins:
    ax.axvline(weeks[o], color=GRID, lw=0.8, zorder=0)
import matplotlib.dates as mdates
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.yaxis.set_major_formatter(FuncFormatter(thousands))
ax.set_ylabel("ODU units per week (all series)")
ax.legend(fontsize=8.5, loc="upper left", ncol=2)
save(fig, "fig_actual_vs_forecast.png")

# Fig: feature importance
fig, ax = plt.subplots(figsize=(7.2, 3.2))
top = imp.head(12)[::-1]
ax.barh(top.index, top.values, color=AQUA, height=0.62)
for k, v in enumerate(top.values):
    ax.text(v + 0.3, k, f"{v:.1f}%", va="center", fontsize=8.5)
ax.set_xlim(0, top.max() * 1.2)
ax.set_xlabel("Share of total split gain, mean across folds (%)")
ax.grid(axis="y", visible=False)
save(fig, "fig_feature_importance.png")

# Fig: WAPE by horizon
fig, ax = plt.subplots(figsize=(7.2, 2.7))
for mname, colr in key_models:
    v = by_h.loc[mname]
    ax.plot(v.index, v.values, "-o", color=colr, lw=2, ms=6, mec="white", mew=1.2, label=mname)
ax.set_xticks(range(1, H + 1))
ax.set_xlabel("Weeks ahead")
ax.set_ylabel("WAPE (%)")
ax.legend(fontsize=8.5, ncol=3, loc="upper left")
save(fig, "fig_wape_by_horizon.png")

# Fig: inventory comparison
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
ivv = invdf.set_index("model")
names_short = {"Naive": "Naive", "Moving Average (8w)": "Moving avg (8w)", "SBA": "SBA",
               "Seasonal SBA": "Seasonal SBA", "LightGBM": "LightGBM",
               "Ensemble (LightGBM + Seasonal SBA)": "Ensemble"}
lab = [names_short[m] for m in ivv.index]
ex = ivv["excess_units_per_cycle"].values[::-1]
axes[0].barh(lab[::-1], ex, color=BLUE, height=0.6)
for k, v in enumerate(ex):
    axes[0].text(v + 300, k, f"{v:,.0f}", va="center", fontsize=8.5)
axes[0].set_xlim(0, ex.max() * 1.3)
axes[0].set_title("Excess cover per 2-week cycle (units)", loc="left", fontsize=10)
axes[0].xaxis.set_major_formatter(FuncFormatter(thousands))
axes[0].grid(axis="y", visible=False)
fr = ivv["fill_rate_pct"].values[::-1]
axes[1].hlines(range(len(fr)), 80, fr, color=GRID, lw=1)
axes[1].plot(fr, range(len(fr)), "o", color=AQUA, ms=8, mec="white", mew=1.5)
for k, v in enumerate(fr):
    axes[1].text(v + 0.4, k, f"{v:.1f}%", va="center", fontsize=8.5)
axes[1].set_yticks(range(len(fr)))
axes[1].set_yticklabels(lab[::-1])
axes[1].set_xlim(80, 92)
axes[1].set_xlabel("Unit fill rate (%) - axis starts at 80%", fontsize=8.5)
axes[1].set_title("Fill rate achieved, Mar-Jun 2024", loc="left", fontsize=10)
axes[1].grid(axis="y", visible=False)
fig.tight_layout()
save(fig, "fig_inventory.png")

# Fig: pipeline diagram
fig, ax = plt.subplots(figsize=(7.2, 1.9))
ax.set_xlim(0, 100)
ax.set_ylim(0, 33)
ax.axis("off")
boxes = [("ERP billing\nextract\n82,034 rows", BLUE), ("Audit &\ncleaning", BLUE), ("Weekly\nSKU × branch\nmatrix", BLUE),
         ("Demand\nclassification\n(ADI / CV²)", ORANGE), ("12-model\nrolling-origin\nbacktest", AQUA),
         ("Safety stock &\nreorder\npolicy", AQUA), ("Planner\ndashboard", INK2)]
w, gap = 11.2, 3.2
for k, (txt, colr) in enumerate(boxes):
    x0 = 1 + k * (w + gap)
    ax.add_patch(FancyBboxPatch((x0, 9), w, 21, boxstyle="round,pad=0.3,rounding_size=1.2", fc="white", ec=colr, lw=1.6))
    ax.text(x0 + w / 2, 19.5, txt, ha="center", va="center", fontsize=7.8, color=INK)
    if k < len(boxes) - 1:
        ax.annotate("", xy=(x0 + w + gap - 0.1, 19.5), xytext=(x0 + w + 0.5, 19.5),
                    arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2, mutation_scale=9))
ax.text(1, 1.5, "Box outline:  blue = data engineering,  orange = diagnosis,  aqua = modelling and decision,  "
        "grey = delivery", fontsize=7.8, color=INK2)
save(fig, "fig_pipeline.png")

# Fig: fold diagram
fig, ax = plt.subplots(figsize=(7.2, 2.7))
for k, o in enumerate(origins):
    yk = N_FOLDS - k
    ax.add_patch(Rectangle((0, yk - 0.35), o, 0.7, color=BLUE, alpha=0.75, lw=0))
    ax.add_patch(Rectangle((o, yk - 0.35), H, 0.7, color=ORANGE, lw=0))
ax.set_xlim(0, T + 1)
ax.set_ylim(0.3, N_FOLDS + 1.1)
ax.set_yticks(range(1, N_FOLDS + 1))
ax.set_yticklabels([f"Fold {N_FOLDS - k + 1}" for k in range(1, N_FOLDS + 1)], fontsize=8.5)
tick_w = [0, 24, 50, 76, 102]
ax.set_xticks(tick_w)
ax.set_xticklabels([weeks[t].strftime("%b %Y") for t in tick_w])
ax.grid(False)
ax.add_patch(Rectangle((2, N_FOLDS + 0.62), 3, 0.28, color=BLUE, alpha=0.75, lw=0))
ax.text(6, N_FOLDS + 0.76, "Training window (expanding)", va="center", fontsize=8.5)
ax.add_patch(Rectangle((36, N_FOLDS + 0.62), 3, 0.28, color=ORANGE, lw=0))
ax.text(40, N_FOLDS + 0.76, "4-week test window", va="center", fontsize=8.5)
save(fig, "fig_folds.png")

with open(OUT / "results.json", "w", encoding="utf-8") as fh:
    json.dump(R, fh, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
log("Done")
