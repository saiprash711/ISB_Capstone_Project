"""
Single source of facts for the capstone report generators.

Every number placed in a generated report comes from here: computed from the
data (Filtered.parquet), from the FY24-25 holdout validation
(holdout_validation/validated_metrics.json, written by
`python validate_holdout_fy25.py score`) or from a live pytest run.
Nothing is typed in by hand.

Usage:
    from report_facts import get_report_facts
    F = get_report_facts()
    F['data']['real_rows'], F['holdout']['rolling_region_month_acc'], ...
"""
import json
import os
import re
import subprocess
import sys
from functools import lru_cache

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
SYNTHETIC_SHEET = 'Evaluation_10_SKUs'
METRICS_PATH = os.path.join(ROOT, 'holdout_validation', 'validated_metrics.json')


def _pick(records, level, method='forecast', key='Accuracy %'):
    for r in records or []:
        if r.get('level') == level and r.get('method') == method:
            return r.get(key)
    return None


def _data_facts():
    df = pd.read_parquet(os.path.join(ROOT, 'Filtered.parquet'))
    real = df[df['Data_Sheet'] != SYNTHETIC_SHEET] if 'Data_Sheet' in df.columns else df
    odu = real[real['EXT MAT GROUP'] == 'RA-ODU']
    shares = (odu.groupby('SALES OFFICE CODE')['Billing Quantity ODU'].sum()
              / odu['Billing Quantity ODU'].sum() * 100).round(1).sort_values(ascending=False)
    dates = pd.to_datetime(real['Billing Date'])
    return {
        'real_rows': int(len(real)),
        'synthetic_rows': int(len(df) - len(real)),
        'synthetic_skus': int(df.loc[df['Data_Sheet'] == SYNTHETIC_SHEET, 'Material'].nunique()) if 'Data_Sheet' in df.columns else 0,
        'date_min': dates.min().strftime('%d %b %Y'),
        'date_max': dates.max().strftime('%d %b %Y'),
        'billing_days': int(dates.dt.date.nunique()),
        'skus': int(real['Material'].nunique()),
        'odu_skus': int(odu['Material'].nunique()),
        'idu_skus': int(real.loc[real['EXT MAT GROUP'] == 'RA-IDU', 'Material'].nunique()),
        'odu_units': float(odu['Billing Quantity ODU'].sum()),
        'idu_units': float(real['Billing Quantity IDU'].sum()),
        'branch_share_odu_pct': shares.to_dict(),
        'branches': int(real['SALES OFFICE CODE'].nunique()),
    }


def _demand_class_facts():
    """Syntetos-Boylan quadrant of every weekly ODU SKU x branch series (training period)."""
    sys.path.insert(0, ROOT)
    from src.selection.demand_classifier import DemandClassifier
    panel_path = os.path.join(ROOT, 'holdout_validation', 'weekly_panel.parquet')
    p = pd.read_parquet(panel_path)
    end = pd.Timestamp('2024-07-01')
    tr = p[p.date <= end]
    clf = DemandClassifier()
    rows = []
    for (_, _), g in tr.groupby(['sku', 'branch']):
        s = g.set_index('date')['total_demand']
        y = s.reindex(pd.date_range(s.index.min(), end, freq='W-MON'), fill_value=0.0).values
        with np.errstate(all='ignore'):
            rows.append((clf.profile_demand(y)['base_quadrant'], float(y.sum())))
    d = pd.DataFrame(rows, columns=['quadrant', 'volume'])
    vol = (d.groupby('quadrant')['volume'].sum() / d['volume'].sum() * 100).round(1)
    cnt = d['quadrant'].value_counts()
    return {q: {'volume_share_pct': float(vol.get(q, 0.0)), 'series': int(cnt.get(q, 0))}
            for q in ['Smooth', 'Erratic', 'Intermittent', 'Lumpy']} | {'total_series': int(len(d))}


def _test_facts():
    """Run the automated test suite and report the real pass count."""
    try:
        out = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests'],
                             cwd=ROOT, capture_output=True, text=True, timeout=900).stdout
    except Exception as e:
        return {'passed': None, 'failed': None, 'summary': f'not run: {e}'}
    passed = re.search(r'(\d+) passed', out)
    failed = re.search(r'(\d+) failed', out)
    return {'passed': int(passed.group(1)) if passed else 0, 'failed': int(failed.group(1)) if failed else 0,
            'summary': out.strip().splitlines()[-1] if out.strip() else ''}


def _holdout_facts():
    if not os.path.exists(METRICS_PATH):
        return None
    m = json.load(open(METRICS_PATH, encoding='utf-8'))
    st, ro = m.get('static', {}), m.get('rolling', {})
    orig = m.get('static_original_engine', {})
    f = {
        'period': m['holdout_period'],
        'verification_passed': m['verification']['passed'],
        'verification_total': m['verification']['total'],
        'holdout_units': m['holdout_odu_units'],
        'lifecycle': m['lifecycle'],
        'static_series': st.get('series'),
        'static_covered_share_pct': round(st.get('covered_share', 0) * 100, 1),
        'static_p10_p90_coverage_pct': round(st.get('p10_p90_coverage', 0) * 100, 1),
        'static_champions': st.get('champions', []),
        'raw': m,
    }
    for name, recs in [('static', st.get('levels')), ('original', orig.get('levels')),
                       ('rolling', ro.get('lag_1_4'))]:
        for lvl, tag in [('SKU x Branch x Week', 'sku_branch_week'), ('SKU x Branch x Month', 'sku_branch_month'),
                         ('Branch x Month', 'branch_month'), ('South Region x Month', 'region_month'),
                         ('South Region x Quarter', 'region_quarter')]:
            f[f'{name}_{tag}_wape'] = _pick(recs, lvl, key='WAPE %')
            f[f'{name}_{tag}_acc'] = _pick(recs, lvl)
            f[f'{name}_{tag}_snaive_acc'] = _pick(recs, lvl, 'seasonal_naive')
            f[f'{name}_{tag}_ma4_acc'] = _pick(recs, lvl, 'moving_avg_4w')
        f[f'{name}_bias_pct'] = _pick(recs, 'South Region x Month', key='Bias %')
    for name, recs in [('static', st.get('all_skus')), ('original', orig.get('all_skus')),
                       ('rolling', ro.get('lag_1_4_all_skus'))]:
        f[f'{name}_all_region_month_wape'] = _pick(recs, 'South Region x Month (all SKUs)', key='WAPE %')
        f[f'{name}_all_branch_month_wape'] = _pick(recs, 'Branch x Month (all SKUs)', key='WAPE %')
        f[f'{name}_all_total_bias_pct'] = _pick(recs, 'South Region x Month (all SKUs)', key='Bias %')
    f['has_rolling'] = bool(ro)
    return f


def _n_candidate_models() -> int:
    """Models in src/forecasting/model_zoo.ALL_MODELS plus the inverse-WAPE ensemble."""
    sys.path.insert(0, ROOT)
    from src.forecasting.model_zoo import ALL_MODELS
    return len(ALL_MODELS) + 1


@lru_cache(maxsize=1)
def get_report_facts(run_tests: bool = True) -> dict:
    return {
        'data': _data_facts(),
        'demand_classes': _demand_class_facts(),
        'tests': _test_facts() if run_tests else {'passed': None, 'failed': None, 'summary': 'not run'},
        'holdout': _holdout_facts(),
        'n_candidate_models': _n_candidate_models(),
    }


def fmt_pct(v, nd=1, signed=False):
    """Format a percentage that may be missing."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'n/a'
    return f"{v:+.{nd}f}%" if signed else f"{v:.{nd}f}%"


if __name__ == '__main__':
    facts = get_report_facts()
    facts['holdout'] = {k: v for k, v in (facts['holdout'] or {}).items() if k != 'raw'}
    print(json.dumps(facts, indent=2, default=str))
