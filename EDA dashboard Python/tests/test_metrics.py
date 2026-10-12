"""
Unit Tests for Forecasting Metrics Module
Verifies calculation accuracy, zero-safe division, and boundary cases.
"""
import pytest
import numpy as np
from src.validation.metrics import (
    calculate_wape,
    calculate_smape,
    calculate_mae,
    calculate_rmse,
    calculate_mase,
    calculate_bias,
    calculate_bias_pct,
    calculate_all_metrics
)


def test_wape_perfect_prediction():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([10.0, 20.0, 30.0])
    assert calculate_wape(y_true, y_pred) == 0.0


def test_wape_standard_case():
    y_true = np.array([100.0, 200.0])
    y_pred = np.array([110.0, 180.0])
    # num = |10| + |-20| = 30; denom = 300; WAPE = 10.0%
    assert calculate_wape(y_true, y_pred) == 10.0


def test_wape_zero_actuals_zero_pred():
    y_true = np.array([0.0, 0.0, 0.0])
    y_pred = np.array([0.0, 0.0, 0.0])
    assert calculate_wape(y_true, y_pred) == 0.0


def test_wape_zero_actuals_positive_pred():
    y_true = np.array([0.0, 0.0])
    y_pred = np.array([10.0, 5.0])
    assert calculate_wape(y_true, y_pred) == 100.0


def test_smape_bounds():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([15.0, 20.0, 25.0])
    smape = calculate_smape(y_true, y_pred)
    assert 0.0 <= smape <= 200.0


def test_mae_and_rmse():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 32.0])
    assert calculate_mae(y_true, y_pred) == 2.0
    assert calculate_rmse(y_true, y_pred) == 2.0


def test_bias_direction():
    y_true = np.array([100.0, 100.0])
    y_over = np.array([110.0, 120.0])
    y_under = np.array([80.0, 90.0])
    
    assert calculate_bias(y_true, y_over) > 0.0  # Over-forecasting is positive
    assert calculate_bias(y_true, y_under) < 0.0  # Under-forecasting is negative


def test_mase_with_in_sample():
    y_train = np.array([10.0, 12.0, 14.0, 16.0, 18.0])
    y_true = np.array([20.0, 22.0])
    y_pred = np.array([21.0, 23.0])
    # in-sample naive diff is 2.0, MAE is 1.0 -> MASE should be 0.5
    mase = calculate_mase(y_true, y_pred, y_train=y_train)
    assert round(mase, 2) == 0.5


def test_calculate_all_metrics():
    y_true = np.array([50.0, 60.0, 70.0, 80.0])
    y_pred = np.array([55.0, 58.0, 72.0, 75.0])
    res = calculate_all_metrics(y_true, y_pred)
    
    for key in ['WAPE', 'sMAPE', 'MAE', 'RMSE', 'MASE', 'Bias', 'Bias_pct']:
        assert key in res
        assert isinstance(res[key], (int, float))
