"""
Unit Tests for Rolling-Origin Backtesting Module
Verifies chronological order, absence of future leakage, and leaderboard generation.
"""
import pytest
import numpy as np
import pandas as pd
from src.validation.backtesting import RollingOriginBacktest
from src.validation.cross_validation import ModelLeaderboard


def test_fold_generation_chronological_order():
    bt = RollingOriginBacktest(n_folds=3, test_weeks=4, min_train_weeks=20, step_size=4)
    n_samples = 50
    folds = bt.generate_folds(n_samples)
    
    assert len(folds) == 3
    
    for train_idx, test_idx in folds:
        # Train and test must be non-overlapping
        assert set(train_idx).isdisjoint(set(test_idx))
        # Train must be strictly before test
        assert train_idx[-1] < test_idx[0]
        # Test length must match test_weeks
        assert len(test_idx) == 4
        # Train must be >= min_train_weeks
        assert len(train_idx) >= 20


def test_backtest_execution_on_synthetic_series():
    bt = RollingOriginBacktest(n_folds=2, test_weeks=3, min_train_weeks=15)
    np.random.seed(42)
    y = np.random.poisson(lam=40, size=30).astype(float)
    
    res = bt.evaluate_sku_series(y)
    assert res['status'] == 'success'
    assert res['n_folds'] == 2
    
    leaderboard = res['leaderboard']
    assert isinstance(leaderboard, pd.DataFrame)
    assert not leaderboard.empty
    assert 'model' in leaderboard.columns
    assert 'mean_wape' in leaderboard.columns
    assert 'rank' in leaderboard.columns
    # Ranking is on RMSE (mean-targeting loss); rank 1 has the lowest RMSE
    if len(leaderboard) >= 2:
        assert leaderboard['mean_rmse'].is_monotonic_increasing
        assert list(leaderboard['rank']) == list(range(1, len(leaderboard) + 1))


def test_model_leaderboard_champion_and_lift():
    df = pd.DataFrame([
        {'model': 'SARIMA', 'mean_wape': 15.0, 'mean_rmse': 20.0, 'std_wape': 1.2},
        {'model': 'Seasonal Naive', 'mean_wape': 25.0, 'mean_rmse': 35.0, 'std_wape': 3.0},
        {'model': 'Naive', 'mean_wape': 30.0, 'mean_rmse': 40.0, 'std_wape': 4.0}
    ])
    lb = ModelLeaderboard(df)
    champion = lb.get_champion()
    assert champion['model'] == 'SARIMA'
    
    comp = lb.compare_with_baseline()
    assert comp['outperforms_baseline'] is True
    assert comp['wape_reduction_points'] == 10.0  # 25 - 15
    assert comp['pct_accuracy_lift'] == 40.0      # 10 / 25 * 100
