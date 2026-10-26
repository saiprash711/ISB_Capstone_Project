"""
Formal Temporal Leakage Audit Tests
Verifies that all feature engineering, fold generation, and validation methods
strictly preserve temporal causality with zero future information leakage.
"""
import pytest
import numpy as np
import pandas as pd
from src.features.engineering import FeatureEngineer
from src.validation.backtesting import RollingOriginBacktest


def test_no_future_information_in_lag_features():
    """Verify lag features only use information strictly prior to current period."""
    engineer = FeatureEngineer()
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=20, freq='W'),
        'sku': ['SKU_TEST'] * 20,
        'branch': ['MAA'] * 20,
        'total_demand': np.arange(1, 21, dtype=float)
    })
    
    df_feat, f_cols = engineer.engineer_features(df)
    
    # Check lag 1
    assert 'lag_1' in df_feat.columns
    # Period 0 lag 1 must be NaN or shift
    assert pd.isna(df_feat.loc[0, 'lag_1'])
    # Period 5 lag 1 must equal total_demand at period 4
    assert df_feat.loc[5, 'lag_1'] == df.loc[4, 'total_demand']
    # Period 10 lag 4 must equal total_demand at period 6
    assert df_feat.loc[10, 'lag_4'] == df.loc[6, 'total_demand']


def test_no_future_information_in_rolling_features():
    """Verify rolling statistics strictly exclude contemporaneous target at period t (shift 1)."""
    engineer = FeatureEngineer()
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=15, freq='W'),
        'sku': ['SKU_TEST'] * 15,
        'branch': ['MAA'] * 15,
        'total_demand': np.array([10.0, 20.0, 30.0, 40.0, 50.0] * 3)
    })
    
    df_feat, f_cols = engineer.engineer_features(df)
    
    # 4-week rolling mean at index 3 must strictly equal mean of preceding indices 0..2 (excluding index 3)
    expected_mean = np.mean([10.0, 20.0, 30.0])
    assert abs(df_feat.loc[3, 'rolling_mean_4'] - expected_mean) < 1e-4
    # At index 4, it must equal mean of indices 0..3
    expected_mean_4 = np.mean([10.0, 20.0, 30.0, 40.0])
    assert abs(df_feat.loc[4, 'rolling_mean_4'] - expected_mean_4) < 1e-4


def _series_with_zeros(n=40):
    y = np.array([0, 5, 0, 12, 30, 0, 0, 8, 50, 3] * (n // 10), dtype=float)[:n]
    return pd.DataFrame({'date': pd.date_range('2023-01-02', periods=n, freq='W-MON'),
                         'sku': 'SKU_TEST', 'branch': 'MAA', 'total_demand': y})


def test_no_feature_uses_current_period_target():
    """Changing y(t) must not change any feature in row t (catches every contemporaneous leak)."""
    engineer = FeatureEngineer()
    df = _series_with_zeros()
    base, cols = engineer.engineer_features(df)
    for t in [15, 25, 33]:
        bumped = df.copy()
        bumped.loc[t, 'total_demand'] = bumped.loc[t, 'total_demand'] * 10 + 999
        feat, _ = engineer.engineer_features(bumped)
        a = base.loc[t, cols].astype(float).fillna(0).values
        b = feat.loc[t, cols].astype(float).fillna(0).values
        leaking = [c for c, x, z in zip(cols, a, b) if not np.isclose(x, z)]
        assert not leaking, f"features at t={t} depend on y(t): {leaking}"


def test_forecast_features_match_training_features():
    """Recursive forecasting must build exactly the features the models were trained on."""
    engineer = FeatureEngineer()
    df = _series_with_zeros()
    feat, cols = engineer.engineer_features(df)
    hist = df['total_demand']
    for t in [14, 20, 30, 39]:
        step = engineer.generate_step_features(hist.iloc[:t].reset_index(drop=True), target_date=df.loc[t, 'date'])
        for c in cols:
            train_val = float(np.nan_to_num(feat.loc[t, c], nan=0.0))
            assert np.isclose(step.get(c, 0.0), train_val), f"{c} at t={t}: forecast {step.get(c)} vs training {train_val}"


def test_strict_chronological_splits_zero_leakage():
    """Verify walk-forward splits have strictly disjoint indices and no reverse leakage."""
    bt = RollingOriginBacktest(n_folds=5, test_weeks=4, min_train_weeks=26, step_size=4)
    n_samples = 60
    folds = bt.generate_folds(n_samples)
    
    assert len(folds) >= 1
    for fold_idx, (train_idx, test_idx) in enumerate(folds):
        # 1. No overlap
        assert len(set(train_idx).intersection(set(test_idx))) == 0
        # 2. Strict chronological order
        assert np.max(train_idx) < np.min(test_idx)
        # 3. Test set contiguous
        assert np.all(np.diff(test_idx) == 1)
        # 4. Train set contiguous
        assert np.all(np.diff(train_idx) == 1)


def test_leakage_auditor_full_audit():
    """Verify LeakageAuditor certifies complete pipeline as zero leakage."""
    from src.validation.leakage_audit import LeakageAuditor
    engineer = FeatureEngineer()
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=40, freq='W'),
        'sku': ['SKU_TEST'] * 40,
        'branch': ['MAA'] * 40,
        'total_demand': np.sin(np.linspace(0, 10, 40)) * 20 + 50
    })
    df_feat, f_cols = engineer.engineer_features(df)
    
    bt = RollingOriginBacktest(n_folds=3, test_weeks=4, min_train_weeks=20)
    folds = bt.generate_folds(len(df))
    
    auditor = LeakageAuditor()
    report = auditor.run_full_audit(df_feat, folds=folds)
    
    assert report['is_fully_compliant'] is True
    assert report['overall_status'] == 'VERIFIED_ZERO_LEAKAGE'
    assert report['leakage_percentage'] == 0.0
    assert report['checks_passed'] == report['checks_total']

