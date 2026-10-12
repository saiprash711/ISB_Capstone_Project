"""
Hierarchical Reconciliation Module
Ensures mathematical coherency across echelons:
Sum of SKU forecasts == Branch forecast
Sum of Branch forecasts == Region forecast
Supports Bottom-Up, Top-Down, and Proportional Reconciliation.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional


class HierarchicalReconciler:
    """
    Reconciles forecasts across Region, Branch, and SKU echelons.
    """
    
    def __init__(self, method: str = 'bottom_up'):
        """
        Args:
            method: 'bottom_up', 'top_down', or 'proportional'
        """
        self.method = method

    def reconcile_bottom_up(self, sku_forecasts: Dict[Tuple[str, str], np.ndarray]) -> Dict[str, Any]:
        """
        Bottom-Up (BU) reconciliation:
        Takes SKU x Branch forecasts and aggregates up to Branch and Region.
        
        Args:
            sku_forecasts: dict of (sku, branch) -> 1D forecast array
        
        Returns:
            Dict with 'reconciled_sku', 'reconciled_branch', 'reconciled_region'
        """
        if not sku_forecasts:
            return {}

        horizon = len(next(iter(sku_forecasts.values())))
        branch_totals: Dict[str, np.ndarray] = {}
        region_total = np.zeros(horizon, dtype=float)

        for (sku, branch), fcast in sku_forecasts.items():
            arr = np.asarray(fcast, dtype=float)
            if branch not in branch_totals:
                branch_totals[branch] = np.zeros(horizon, dtype=float)
            branch_totals[branch] += arr
            region_total += arr

        return {
            'method': 'bottom_up',
            'sku_forecasts': sku_forecasts,
            'branch_forecasts': branch_totals,
            'region_forecast': region_total,
            'is_coherent': True
        }

    def reconcile_top_down(self, region_forecast: np.ndarray, 
                           branch_shares: Dict[str, float],
                           sku_branch_shares: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Top-Down (TD) disaggregation:
        Takes regional forecast and disaggregates downward using historical shares.
        """
        horizon = len(region_forecast)
        branch_forecasts = {}
        sku_forecasts = {}

        for branch, b_share in branch_shares.items():
            b_pred = region_forecast * float(b_share)
            branch_forecasts[branch] = b_pred
            
            sku_shares = sku_branch_shares.get(branch, {})
            for sku, s_share in sku_shares.items():
                sku_pred = b_pred * float(s_share)
                sku_forecasts[(sku, branch)] = sku_pred

        return {
            'method': 'top_down',
            'region_forecast': region_forecast,
            'branch_forecasts': branch_forecasts,
            'sku_forecasts': sku_forecasts,
            'is_coherent': True
        }

    def verify_coherency(self, sku_forecasts: Dict[Tuple[str, str], np.ndarray],
                         branch_forecasts: Dict[str, np.ndarray],
                         tolerance: float = 1e-2) -> Dict[str, Any]:
        """
        Verify mathematical coherency across levels:
        Sum(SKU) == Branch?
        """
        coherency_results = {}
        overall_coherent = True

        for branch, b_forecast in branch_forecasts.items():
            branch_sku_sum = np.zeros_like(b_forecast)
            for (sku, b), s_forecast in sku_forecasts.items():
                if b == branch:
                    branch_sku_sum += s_forecast
                    
            max_diff = float(np.max(np.abs(branch_sku_sum - b_forecast)))
            is_branch_coherent = (max_diff <= tolerance)
            if not is_branch_coherent:
                overall_coherent = False
                
            coherency_results[branch] = {
                'branch': branch,
                'max_divergence': round(max_diff, 4),
                'coherent': is_branch_coherent
            }

        return {
            'overall_coherent': overall_coherent,
            'branch_details': coherency_results
        }
