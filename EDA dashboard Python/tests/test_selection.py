"""
Unit Tests for Demand Classification & Model Selection
"""
import pytest
import numpy as np
import pandas as pd
from src.selection.demand_classifier import DemandClassifier
from src.selection.champion_challenger import ChampionChallengerManager


def test_demand_classifier_smooth():
    classifier = DemandClassifier()
    # Continuous positive demand with low variance
    y = np.array([50.0, 52.0, 48.0, 51.0, 49.0, 50.0, 53.0, 47.0] * 3)
    profile = classifier.profile_demand(y)
    
    assert profile['base_quadrant'] == 'Smooth'
    assert profile['adi'] == 1.0  # Zero gaps
    assert profile['cv2'] < 0.49
    assert 'ARIMA' in profile['candidate_models'] or 'ETS' in profile['candidate_models']


def test_demand_classifier_intermittent():
    classifier = DemandClassifier()
    # Frequent zeros with sporadic orders
    y = np.array([0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 12.0, 0.0, 0.0, 11.0, 0.0, 0.0] * 2)
    profile = classifier.profile_demand(y)
    
    assert profile['base_quadrant'] in ['Intermittent', 'Lumpy']
    assert profile['zero_demand_pct'] > 50.0
    assert 'Croston' in profile['candidate_models'] or 'SBA' in profile['candidate_models']


def test_champion_challenger_governance():
    mgr = ChampionChallengerManager(min_wape_lift=3.0)
    
    # Round 1
    lb_df = pd.DataFrame([
        {'model': 'SARIMA', 'mean_wape': 18.0, 'mean_rmse': 25.0, 'mean_bias_pct': 2.0},
        {'model': 'Random Forest', 'mean_wape': 20.0, 'mean_rmse': 28.0, 'mean_bias_pct': -1.0}
    ])
    entry = mgr.register_evaluation("SKU_A", "MAA", lb_df, {'demand_type': 'Seasonal'})
    assert entry['champion']['model_name'] == 'SARIMA'
    assert entry['action'] == 'INITIAL_ASSIGNMENT'
    
    # Round 2: Challenger wins by 4% (> min_wape_lift 3%)
    lb_df2 = pd.DataFrame([
        {'model': 'LightGBM', 'mean_wape': 13.5, 'mean_rmse': 20.0, 'mean_bias_pct': 1.0},
        {'model': 'SARIMA', 'mean_wape': 18.0, 'mean_rmse': 25.0, 'mean_bias_pct': 2.0}
    ])
    entry2 = mgr.register_evaluation("SKU_A", "MAA", lb_df2, {'demand_type': 'Seasonal'})
    assert entry2['champion']['model_name'] == 'LightGBM'
    assert entry2['action'] == 'CHAMPION_PROMOTED'
