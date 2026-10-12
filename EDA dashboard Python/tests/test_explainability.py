"""
Unit Tests for Explainability and SHAP Feature Attribution
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from src.explainability.shap_analysis import ForecastExplainer


def test_forecast_explainer_tree_shap():
    explainer = ForecastExplainer()
    
    # Generate synthetic training data
    np.random.seed(42)
    X = pd.DataFrame({
        'lag_1': np.random.uniform(10, 50, 40),
        'lag_4': np.random.uniform(10, 50, 40),
        'rolling_mean_4': np.random.uniform(10, 50, 40),
        'month': np.random.randint(1, 13, 40)
    })
    y = X['lag_1'] * 0.5 + X['rolling_mean_4'] * 0.3 + np.random.normal(0, 2, 40)
    
    rf = RandomForestRegressor(n_estimators=20, random_state=42)
    rf.fit(X, y)
    
    res = explainer.explain_tree_model(rf, X)
    
    assert 'feature_importances' in res
    assert 'mean_shap' in res
    assert res['method'] in ['TreeSHAP', 'Gini_Impurity_Feature_Importance']
    assert len(res['feature_importances']) == 4
    
    # Importance scores should sum to approx 100%
    total_pct = sum(res['feature_importances'].values())
    assert abs(total_pct - 100.0) < 1.0


def test_forecast_explainer_statistical_decomposition():
    explainer = ForecastExplainer()
    
    # Generate time series with trend and seasonality
    t = np.arange(36)
    trend = 2.0 * t
    seasonal = 10.0 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(0, 1, 36)
    y = 50.0 + trend + seasonal + noise
    
    decomp = explainer.explain_statistical_series(y, period=12)
    
    assert 'trend_contribution_pct' in decomp
    assert 'seasonality_contribution_pct' in decomp
    assert 'residual_contribution_pct' in decomp
    assert decomp['trend_contribution_pct'] > 0
    assert decomp['seasonality_contribution_pct'] > 0


def test_waterfall_attribution():
    explainer = ForecastExplainer()
    
    importances = {
        'lag_1': 45.0,
        'rolling_mean_4': 35.0,
        'month': 20.0
    }
    
    waterfall = explainer.compute_waterfall_attribution(
        final_forecast=65.0,
        historical_mean=50.0,
        feature_importances=importances
    )
    
    assert len(waterfall) >= 3
    assert waterfall[0]['category'] == 'Base'
    assert waterfall[0]['impact'] == 50.0
    assert waterfall[-1]['category'] == 'Result'
    assert waterfall[-1]['impact'] == 65.0


def test_importance_table_format():
    explainer = ForecastExplainer()
    importances = {'lag_1': 55.4, 'rolling_mean_4': 44.6}
    table = explainer.format_importance_table(importances)
    
    assert isinstance(table, pd.DataFrame)
    assert len(table) == 2
    assert 'Feature Attribute' in table.columns
    assert 'Importance Score (%)' in table.columns
