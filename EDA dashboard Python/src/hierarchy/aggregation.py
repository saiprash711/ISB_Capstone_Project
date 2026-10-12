"""
Hierarchical Aggregation Module
Structures multi-echelon business hierarchy:
Region (South) -> Branch (BLR, MAA, COK, SBD, SBD1) -> SKU
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any


class HierarchyAggregator:
    """
    Aggregates demand across hierarchical supply chain dimensions.
    """
    
    def __init__(self, region_name: str = "South Region"):
        self.region_name = region_name

    def build_hierarchy_tree(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Build a tree map of Region -> Branches -> SKUs.
        """
        tree = {
            'name': self.region_name,
            'level': 'Region',
            'branches': {}
        }
        
        for branch, b_group in df.groupby('branch', observed=True):
            skus = b_group['sku'].unique().tolist()
            tree['branches'][branch] = {
                'name': branch,
                'level': 'Branch',
                'skus': skus,
                'sku_count': len(skus)
            }
            
        return tree

    def aggregate_levels(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Produce time series aggregated at all 3 hierarchical levels:
        - 'sku': SKU x Branch x Date grain
        - 'branch': Branch x Date grain
        - 'region': Region x Date grain
        """
        sku_level = df.groupby(['date', 'branch', 'sku'], observed=True)['total_demand'].sum().reset_index()
        branch_level = df.groupby(['date', 'branch'], observed=True)['total_demand'].sum().reset_index()
        region_level = df.groupby('date')['total_demand'].sum().reset_index()
        region_level['region'] = self.region_name

        return {
            'sku_level': sku_level,
            'branch_level': branch_level,
            'region_level': region_level
        }

    def compute_historical_proportions(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Compute historical volume share proportions for top-down disaggregation:
        - Branch share of Region
        - SKU share of Branch
        """
        tot_vol = df['total_demand'].sum()
        branch_vols = df.groupby('branch', observed=True)['total_demand'].sum()
        branch_shares = (branch_vols / tot_vol).to_dict() if tot_vol > 0 else {}
        
        sku_branch_shares = {}
        for branch, b_group in df.groupby('branch', observed=True):
            b_tot = b_group['total_demand'].sum()
            sku_vols = b_group.groupby('sku', observed=True)['total_demand'].sum()
            sku_branch_shares[branch] = (sku_vols / b_tot).to_dict() if b_tot > 0 else {}
            
        return {
            'branch_shares': branch_shares,
            'sku_branch_shares': sku_branch_shares
        }
