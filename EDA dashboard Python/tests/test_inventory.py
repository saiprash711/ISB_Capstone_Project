"""
Unit Tests for Inventory Decision Engine
"""
import pytest
import numpy as np
from src.inventory.inventory_engine import InventoryEngine


def test_inventory_policy_calculation():
    engine = InventoryEngine(default_lead_time=2, default_service_level=0.95, unit_cost=20000.0)
    
    # Weekly forecast of 50 units
    forecast_values = np.full(12, 50.0)
    policy = engine.calculate_inventory_policy(
        forecast_values, forecast_rmse=10.0, lead_time_weeks=2, target_service_level=0.95
    )
    
    # LTD = 2 * 50 = 100
    assert policy['lead_time_demand'] == 100.0
    # sigma_LTD = sqrt(2) * 10 ≈ 14.14; Z_0.95 ≈ 1.645 -> SS ≈ ceil(1.645 * 14.14) = 24
    assert policy['safety_stock_units'] >= 20
    # ROP = LTD + SS
    assert policy['reorder_point_units'] == policy['lead_time_demand'] + policy['safety_stock_units']
    assert policy['target_service_level_pct'] == 95.0
    assert 'sensitivity_table' in policy


def test_stockout_risk_behavior():
    engine = InventoryEngine()
    forecast = np.full(6, 40.0)
    
    # High on-hand stock -> low stockout risk
    safe_policy = engine.calculate_inventory_policy(forecast, forecast_rmse=5.0, current_on_hand=200.0)
    assert safe_policy['stockout_risk_pct'] < 5.0
    
    # Very low on-hand stock -> high stockout risk
    risky_policy = engine.calculate_inventory_policy(forecast, forecast_rmse=15.0, current_on_hand=30.0)
    assert risky_policy['stockout_risk_pct'] > 50.0


def test_missing_on_hand_inventory():
    engine = InventoryEngine()
    forecast = np.full(6, 40.0)
    policy = engine.calculate_inventory_policy(forecast, forecast_rmse=5.0, current_on_hand=None)
    assert policy['current_on_hand'] is None
    assert policy['stockout_risk_pct'] is None
    assert policy['on_hand_status'] == "CURRENT_INVENTORY_POSITION_UNAVAILABLE"

