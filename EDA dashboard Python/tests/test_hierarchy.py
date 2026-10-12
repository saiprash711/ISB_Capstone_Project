"""
Unit Tests for Hierarchical Forecasting & Reconciliation
"""
import pytest
import numpy as np
import pandas as pd
from src.hierarchy.aggregation import HierarchyAggregator
from src.hierarchy.reconciliation import HierarchicalReconciler


def test_hierarchical_aggregation_and_proportions():
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=4, freq='W').tolist() * 4,
        'branch': ['BLR', 'BLR', 'MAA', 'MAA'] * 4,
        'sku': ['SKU_1', 'SKU_2', 'SKU_1', 'SKU_2'] * 4,
        'total_demand': [10.0, 20.0, 30.0, 40.0] * 4
    })
    
    aggregator = HierarchyAggregator(region_name="South Region")
    levels = aggregator.aggregate_levels(df)
    
    assert 'sku_level' in levels
    assert 'branch_level' in levels
    assert 'region_level' in levels
    
    # Check that region level demand equals sum of branch level demand
    assert levels['region_level']['total_demand'].sum() == levels['branch_level']['total_demand'].sum()


def test_bottom_up_reconciliation_coherency():
    reconciler = HierarchicalReconciler(method='bottom_up')
    
    sku_forecasts = {
        ('SKU_1', 'BLR'): np.array([10.0, 12.0, 15.0]),
        ('SKU_2', 'BLR'): np.array([20.0, 22.0, 25.0]),
        ('SKU_1', 'MAA'): np.array([30.0, 32.0, 35.0]),
        ('SKU_2', 'MAA'): np.array([40.0, 42.0, 45.0])
    }
    
    res = reconciler.reconcile_bottom_up(sku_forecasts)
    branch_forecasts = res['branch_forecasts']
    
    # BLR should equal SKU_1(BLR) + SKU_2(BLR)
    expected_blr = np.array([30.0, 34.0, 40.0])
    np.testing.assert_allclose(branch_forecasts['BLR'], expected_blr)
    
    # Verify coherency
    coherency = reconciler.verify_coherency(sku_forecasts, branch_forecasts)
    assert coherency['overall_coherent'] is True
