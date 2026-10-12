"""
Unit Tests for Monitoring & Drift Detection Modules
"""
import pytest
import numpy as np
from src.monitoring.forecast_monitor import ForecastMonitor
from src.monitoring.drift import DriftDetector
from src.monitoring.alerts import AlertEngine
from src.monitoring.registry import ModelRegistry


def test_forecast_monitor_tracking_signal():
    monitor = ForecastMonitor()
    actuals = np.array([50.0, 50.0, 50.0, 50.0, 50.0])
    # Perfect forecast
    perfect_res = monitor.evaluate_model_health(actuals, actuals)
    assert perfect_res['tracking_signal'] == 0.0
    assert perfect_res['health_status'] == 'Healthy'
    
    # Persistent over-forecasting -> high positive tracking signal
    over_forecasts = np.array([70.0, 70.0, 70.0, 70.0, 70.0])
    over_res = monitor.evaluate_model_health(actuals, over_forecasts)
    assert over_res['tracking_signal'] > 0.0
    assert over_res['health_status'] in ['Watch', 'Retrain Required']


def test_drift_detector_psi():
    detector = DriftDetector()
    # Identical distributions
    ref = np.array([10.0, 20.0, 30.0, 40.0, 50.0] * 10)
    cur = np.array([10.0, 20.0, 30.0, 40.0, 50.0] * 10)
    psi = detector.calculate_psi(ref, cur)
    assert psi < 0.10  # No drift
    
    # Drastic shift in demand distribution
    cur_shifted = np.array([100.0, 150.0, 200.0, 250.0, 300.0] * 10)
    psi_shifted = detector.calculate_psi(ref, cur_shifted)
    assert psi_shifted > 0.25  # Significant drift


def test_alert_engine_action_queue():
    sku_assessments = [
        {'sku': 'SKU_X', 'branch': 'BLR', 'stockout_risk_pct': 25.0, 'health_status': 'Healthy'},
        {'sku': 'SKU_Y', 'branch': 'MAA', 'stockout_risk_pct': 5.0, 'health_status': 'Retrain Required', 'tracking_signal': 6.5},
        {'sku': 'SKU_Z', 'branch': 'COK', 'stockout_risk_pct': 2.0, 'health_status': 'Healthy', 'drift_detected': True, 'psi': 0.32}
    ]
    queue = AlertEngine.generate_action_queue(sku_assessments)
    assert len(queue) >= 3
    # Verify high priorities exist
    assert any(q['priority'] == 'HIGH' for q in queue)


def test_model_registry():
    registry = ModelRegistry(storage_path="config/test_registry.json")
    record = registry.register_model(
        sku="TEST_SKU",
        branch="BLR",
        model_name="SARIMA",
        version=1,
        validation_metrics={'mean_wape': 14.5, 'mean_rmse': 22.0}
    )
    assert record['status'] == "ACTIVE_CHAMPION"
    champ = registry.get_champion("TEST_SKU", "BLR")
    assert champ is not None
    assert champ['model_name'] == "SARIMA"
