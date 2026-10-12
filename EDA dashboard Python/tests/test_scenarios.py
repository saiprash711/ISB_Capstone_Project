"""
Unit Tests for Scenario Simulator Module
"""
import pytest
import numpy as np
from src.scenarios.simulator import ScenarioSimulator


def test_scenario_simulation_multipliers():
    simulator = ScenarioSimulator()
    base_forecast = np.array([100.0, 100.0, 100.0, 100.0])
    
    # Base Case
    res_base = simulator.simulate(base_forecast, scenario_name='Base Case')
    assert res_base['multiplier'] == 1.0
    assert res_base['delta_volume_units'] == 0.0
    
    # Heatwave (+30%)
    res_heat = simulator.simulate(base_forecast, scenario_name='Summer Heatwave (+30%)')
    assert res_heat['multiplier'] == 1.30
    assert res_heat['delta_volume_units'] == 120.0  # (130 - 100) * 4
    assert res_heat['scenario_safety_stock'] >= res_base['base_safety_stock']
    
    # Custom Multiplier (+50%)
    res_custom = simulator.simulate(base_forecast, custom_multiplier=1.50)
    assert res_custom['multiplier'] == 1.50
    assert res_custom['delta_volume_units'] == 200.0


def test_scenario_summary_table():
    simulator = ScenarioSimulator()
    base_forecast = np.array([50.0] * 12)
    summary_df = simulator.get_all_scenarios_summary(base_forecast)
    
    assert not summary_df.empty
    assert 'Scenario' in summary_df.columns
    assert 'Multiplier' in summary_df.columns
    assert len(summary_df) >= 4
