"""
Operational Alert & Action Queue Generator
Translates model diagnostics, stockout risks, and drift signals into an
enterprise consulting action queue for demand planners.
"""
from typing import Dict, List, Any
import pandas as pd


class AlertEngine:
    """
    Synthesizes operational alerts across forecasting, inventory, and drift.
    """
    
    @staticmethod
    def generate_action_queue(sku_assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate prioritized operational action items from SKU fleet metrics.
        
        Each item has:
        - priority: 'HIGH', 'MEDIUM', 'INFO'
        - category: 'INVENTORY', 'MODEL_DRIFT', 'RETRAIN', 'DEMAND_SHOCK'
        - title: Short actionable title
        - detail: Quantitative reason
        - recommended_action: What the planner should do
        """
        queue = []
        
        for item in sku_assessments:
            sku = item.get('sku', 'SKU')
            branch = item.get('branch', 'Branch')
            
            # 1. Stockout risk check
            stockout_risk = item.get('stockout_risk_pct')   # None when no on-hand stock is known
            if stockout_risk is not None and stockout_risk > 20.0:
                queue.append({
                    'priority': 'HIGH',
                    'category': 'INVENTORY',
                    'sku': sku,
                    'branch': branch,
                    'title': f"Elevated Stockout Risk ({stockout_risk:.1f}%) on {sku}",
                    'detail': f"Projected lead time demand exceeds target safety stock buffer at {branch}.",
                    'recommended_action': f"Expedite purchase order or reallocate stock from adjacent hub."
                })
            elif stockout_risk is not None and stockout_risk > 10.0:
                queue.append({
                    'priority': 'MEDIUM',
                    'category': 'INVENTORY',
                    'sku': sku,
                    'branch': branch,
                    'title': f"Safety Stock Warning on {sku}",
                    'detail': f"Current buffer at {branch} operates near minimum safety threshold.",
                    'recommended_action': f"Review next replenishment order quantity."
                })
                
            # 2. Model health / Retraining check
            health = item.get('health_status', 'Healthy')
            if health == 'Retrain Required':
                ts = item.get('tracking_signal', 0.0)
                queue.append({
                    'priority': 'HIGH',
                    'category': 'RETRAIN',
                    'sku': sku,
                    'branch': branch,
                    'title': f"Model Degradation on {sku} ({branch})",
                    'detail': item.get('health_detail') or f"Tracking signal ({ts:+.2f}) has breached statistical control limits (±6.0).",
                    'recommended_action': f"Trigger automatic model selector and promote top challenger."
                })
            elif health == 'Watch':
                queue.append({
                    'priority': 'MEDIUM',
                    'category': 'MODEL_HEALTH',
                    'sku': sku,
                    'branch': branch,
                    'title': f"Forecast Bias Drift on {sku}",
                    'detail': item.get('health_detail') or "Mild tracking signal deviation detected. Forecast tending to over/under-shoot.",
                    'recommended_action': f"Log variance and inspect promotional calendar alignment."
                })
                
            # 3. Data drift check
            if item.get('drift_detected', False):
                psi = item.get('psi', 0.0)
                queue.append({
                    'priority': 'HIGH',
                    'category': 'DATA_DRIFT',
                    'sku': sku,
                    'branch': branch,
                    'title': f"Demand Distribution Shift on {sku}",
                    'detail': f"Population Stability Index (PSI = {psi:.3f}) indicates structural shift in recent order sizes.",
                    'recommended_action': f"Re-profile demand quadrant and retrain lag features."
                })

        # Sort: HIGH first, then MEDIUM
        priority_rank = {'HIGH': 0, 'MEDIUM': 1, 'INFO': 2}
        queue.sort(key=lambda x: priority_rank.get(x['priority'], 9))
        return queue
