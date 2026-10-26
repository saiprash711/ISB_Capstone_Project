"""
Pooled Seasonal Profile & Seasonal Index Forecaster
Room-AC demand has a strong annual cycle (Mar-May peak, Jul-Nov trough, Dec
year-end push) and a month-end billing push, but individual SKU x Branch series
carry only ~2 years of noisy weekly history - too short to estimate a 52-week
season on their own. The profile is therefore estimated from pooled demand
(region total, shrunk towards the branch) and applied to each SKU's recent
seasonally-adjusted level.

All estimates use data up to an explicit `as_of` week only, so the same code
is leakage-free inside walk-forward backtest folds.
"""
from typing import Dict, Optional

import numpy as np
import pandas as pd

WEEK_FREQ = 'W-MON'


def _mid_week(dates) -> pd.DatetimeIndex:
    """W-MON labels mark the week's last day; the mid-week day decides the calendar month."""
    return pd.DatetimeIndex(dates) - pd.Timedelta(days=3)


def _is_last_week_of_month(dates) -> np.ndarray:
    mid = _mid_week(dates)
    return np.asarray((mid + pd.Timedelta(days=7)).month != mid.month)


def _weeks_in_month(dates) -> np.ndarray:
    """Number of W-MON weeks whose mid-week day falls in the same calendar month (4 or 5)."""
    mid = _mid_week(dates)
    first = mid - pd.to_timedelta((mid.day - 1) // 7 * 7, unit='D')    # first same-weekday of month
    n = np.full(len(mid), 4)
    n[np.asarray((first + pd.Timedelta(days=28)).month == mid.month)] = 5
    return n


class SeasonalProfile:
    """Multiplicative weekly seasonal factors = month index x month-end position factor."""

    def __init__(self, month_index: Dict[int, float], last_week_ratio: float = 1.0,
                 as_of: Optional[pd.Timestamp] = None, n_years: int = 0):
        self.month_index = month_index
        self.last_week_ratio = last_week_ratio
        self.as_of = as_of
        self.n_years = n_years

    def factors(self, dates) -> np.ndarray:
        dates = pd.DatetimeIndex(dates)
        if len(dates) == 0:
            return np.array([], dtype=float)
        m = np.asarray(_mid_week(dates).month)
        month_f = np.array([self.month_index.get(int(k), 1.0) for k in m])
        k = _weeks_in_month(dates)
        r = self.last_week_ratio
        other = k / (k - 1 + r)          # keeps the mean factor within each month at 1
        pos_f = np.where(_is_last_week_of_month(dates), r * other, other)
        return np.maximum(1e-3, month_f * pos_f)

    def future_dates(self, last_date, horizon: int) -> pd.DatetimeIndex:
        return pd.date_range(pd.Timestamp(last_date) + pd.Timedelta(weeks=1), periods=horizon, freq=WEEK_FREQ)


def _month_index_and_ratio(weekly: pd.Series):
    """Month index and month-end ratio from complete 52-week blocks of a weekly series."""
    n_blocks = len(weekly) // 52
    month_idx, ratios = [], []
    for b in range(n_blocks):
        blk = weekly.iloc[len(weekly) - (b + 1) * 52: len(weekly) - b * 52]
        if blk.sum() <= 0:
            continue
        months = np.asarray(_mid_week(blk.index).month)
        dfb = pd.DataFrame({'y': blk.values, 'm': months, 'last': _is_last_week_of_month(blk.index)})
        mm = dfb.groupby('m')['y'].mean()
        month_idx.append(mm / dfb['y'].mean())
        rel = dfb['y'] / dfb['m'].map(mm).replace(0, np.nan)
        last_mean, other_mean = rel[dfb['last']].mean(), rel[~dfb['last']].mean()
        if np.isfinite(last_mean) and np.isfinite(other_mean) and other_mean > 0:
            ratios.append(last_mean / other_mean)
    if not month_idx:
        return None, None
    mi = pd.concat(month_idx, axis=1).mean(axis=1).reindex(range(1, 13)).fillna(1.0)
    return mi, (float(np.mean(ratios)) if ratios else 1.0)


def build_seasonal_profile(region_weekly: pd.Series, branch_weekly: Optional[pd.Series] = None,
                           as_of=None, branch_weight: float = 0.5, max_years: int = 3,
                           month_end_effect: bool = True) -> Optional[SeasonalProfile]:
    """
    Estimate a seasonal profile from pooled weekly demand observed up to `as_of`.

    Args:
        region_weekly: weekly (W-MON) pooled demand of the whole region
        branch_weekly: weekly pooled demand of the SKU's branch (optional)
        as_of: last week label that may be used (fold cutoff / data as-of date)
        branch_weight: shrinkage weight of the branch profile vs the region profile
        max_years: number of most recent complete years to average
        month_end_effect: include the month-end billing-push position factor
    Returns:
        SeasonalProfile, or None when less than one complete year of pooled history exists.
    """
    def _prep(s):
        if s is None or len(s) == 0:
            return None
        s = s.sort_index()
        if as_of is not None:
            s = s[s.index <= pd.Timestamp(as_of)]
        if len(s) == 0:
            return None
        s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq=WEEK_FREQ), fill_value=0.0)
        return s.iloc[-max_years * 52:]

    reg = _prep(region_weekly)
    if reg is None or len(reg) < 52:
        return None
    reg_mi, ratio = _month_index_and_ratio(reg)
    if reg_mi is None:
        return None
    mi = reg_mi
    br = _prep(branch_weekly)
    if br is not None and len(br) >= 52 and branch_weight > 0:
        br_mi, _ = _month_index_and_ratio(br)
        if br_mi is not None:
            mi = branch_weight * br_mi + (1.0 - branch_weight) * reg_mi
    ratio = float(np.clip(ratio, 0.5, 3.0)) if month_end_effect else 1.0
    return SeasonalProfile({int(k): float(v) for k, v in mi.items()}, ratio,
                           as_of=reg.index.max(), n_years=len(reg) // 52)


class SeasonalIndexForecaster:
    """
    Forecast = recent seasonally-adjusted level x pooled seasonal factor.
    level = sum(y over last `window` weeks) / sum(seasonal factor over the same weeks)
    """

    def __init__(self, window: int = 13):
        self.window = window
        self.level = None

    def fit(self, y: np.ndarray, hist_factors: np.ndarray):
        y = np.asarray(y, dtype=float)
        f = np.asarray(hist_factors, dtype=float)
        k = min(self.window, len(y))
        denom = f[-k:].sum() if k > 0 else 0.0
        self.level = float(y[-k:].sum() / denom) if denom > 0 else float(np.mean(y[-k:])) if k > 0 else 0.0
        return self

    def predict(self, future_factors: np.ndarray) -> np.ndarray:
        if self.level is None:
            return np.full(len(future_factors), np.nan)
        return np.maximum(0.0, self.level * np.asarray(future_factors, dtype=float))


def pooled_weekly(df: pd.DataFrame, date_col: str, value_col: str,
                  branch_col: Optional[str] = None) -> Dict[str, pd.Series]:
    """Region and per-branch weekly (W-MON) demand totals used to estimate seasonal profiles."""
    d = df[[c for c in [date_col, value_col, branch_col] if c]].copy()
    d[date_col] = pd.to_datetime(d[date_col], errors='coerce')
    d[value_col] = pd.to_numeric(d[value_col], errors='coerce').fillna(0.0).clip(lower=0.0)
    d = d.dropna(subset=[date_col])
    out = {'__region__': d.groupby(pd.Grouper(key=date_col, freq=WEEK_FREQ))[value_col].sum()}
    if branch_col:
        for br, g in d.groupby(branch_col):
            out[str(br)] = g.groupby(pd.Grouper(key=date_col, freq=WEEK_FREQ))[value_col].sum()
    return out
