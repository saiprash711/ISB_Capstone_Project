"""
Inventory Decision Engine
Translates statistical and ML demand forecasts into actionable inventory policies:
- Lead Time Demand (LTD)
- Safety Stock (SS)
- Reorder Point (ROP)
- Stockout Risk %
- Service Level Sensitivity
- Working Capital Exposure
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Any, Optional


class InventoryEngine:
    """
    Supply chain inventory optimization engine.
    """
    
    # Standard normal z-scores for service levels
    Z_LOOKUP = {
        0.80: 0.84,
        0.85: 1.04,
        0.90: 1.28,
        0.95: 1.645,
        0.98: 2.055,
        0.99: 2.326
    }
    
    def __init__(self, default_lead_time: int = 2, default_service_level: float = 0.95,
                 holding_cost_rate: float = 0.15, unit_cost: float = 25000.0):
        """
        Args:
            default_lead_time: Replenishment lead time in weeks
            default_service_level: Target service level (0.80 - 0.99)
            holding_cost_rate: Annual holding cost percentage (e.g. 0.15 = 15%/yr)
            unit_cost: Indicative unit cost in INR (e.g., RAC unit ~25,000 INR)
        """
        self.default_lead_time = default_lead_time
        self.default_service_level = default_service_level
        self.holding_cost_rate = holding_cost_rate
        self.unit_cost = unit_cost

    def calculate_inventory_policy(self, forecast_values: np.ndarray,
                                   historical_demand: Optional[np.ndarray] = None,
                                   forecast_rmse: Optional[float] = None,
                                   forecast_residuals: Optional[np.ndarray] = None,
                                   lead_time_weeks: Optional[int] = None,
                                   target_service_level: Optional[float] = None,
                                   current_on_hand: Optional[float] = None) -> Dict[str, Any]:
        """
        Compute full replenishment policy for SKU from actual forecast uncertainty distribution.
        """
        lead_time = lead_time_weeks or self.default_lead_time
        service_level = target_service_level or self.default_service_level
        
        # 1. Expected Weekly Demand & Lead Time Demand
        f_arr = np.asarray(forecast_values, dtype=float)
        mean_weekly_demand = float(np.mean(f_arr[:lead_time])) if len(f_arr) >= lead_time else float(np.mean(f_arr))
        mean_weekly_demand = max(0.0, mean_weekly_demand)
        
        lead_time_demand = mean_weekly_demand * lead_time
        
        # 2. Derive Lead-Time Uncertainty strictly from forecast error distribution
        clean_res = None
        if forecast_residuals is not None and len(forecast_residuals) >= 3:
            clean_res = np.asarray(forecast_residuals, dtype=float)
            clean_res = clean_res[np.isfinite(clean_res)]
            sigma_weekly = float(np.std(clean_res))
            uncertainty_basis = "empirical_forecast_residuals"
        elif forecast_rmse is not None and forecast_rmse > 0:
            sigma_weekly = float(forecast_rmse)
            uncertainty_basis = "backtest_forecast_rmse"
        elif historical_demand is not None and len(historical_demand) > 1:
            clean_hist = np.asarray(historical_demand, dtype=float)
            clean_hist = clean_hist[np.isfinite(clean_hist)]
            sigma_weekly = float(np.std(clean_hist))
            uncertainty_basis = "historical_demand_dispersion"
        else:
            sigma_weekly = 0.0
            uncertainty_basis = "zero_dispersion_insufficient_history"
            
        sigma_ltd = np.sqrt(lead_time) * sigma_weekly
        
        # 3. Safety Stock
        z = self._get_z_score(service_level)
        safety_stock = z * sigma_ltd
        safety_stock = max(0.0, float(np.ceil(safety_stock)))
        
        # 4. Reorder Point (ROP)
        reorder_point = float(np.ceil(lead_time_demand + safety_stock))
        
        # 5. On-Hand & Stockout Risk (Zero synthetic invention: if on_hand is missing, report N/A)
        if current_on_hand is not None:
            on_hand = float(current_on_hand)
            # If historical residuals are available, use empirical Monte Carlo LTD distribution
            if clean_res is not None and len(clean_res) >= 8:
                np.random.seed(42)
                boot_errors = np.random.choice(clean_res, size=(2000, lead_time), replace=True)
                ltd_sim = np.sum(np.maximum(0.0, f_arr[:lead_time] + boot_errors), axis=1)
                stockout_risk_pct = float(np.mean(ltd_sim > on_hand) * 100.0)
                stockout_method = "monte_carlo_empirical_forecast_paths"
            elif sigma_ltd > 0:
                z_current = (on_hand - lead_time_demand) / sigma_ltd
                stockout_risk_pct = float(stats.norm.sf(z_current) * 100.0)
                stockout_method = "parametric_normal_lead_time"
            else:
                stockout_risk_pct = 0.0 if on_hand >= lead_time_demand else 100.0
                stockout_method = "deterministic"
                
            stockout_risk_pct = round(min(100.0, max(0.0, stockout_risk_pct)), 1)
            replenishment_recommended = on_hand <= reorder_point
            recommended_order_quantity = int(max(0.0, reorder_point - on_hand + lead_time_demand))
            is_stockout_risk_high = stockout_risk_pct > 15.0
            on_hand_status = "AVAILABLE"
            display_on_hand = round(on_hand, 1)
        else:
            on_hand = None
            display_on_hand = None
            stockout_risk_pct = None
            stockout_method = "UNAVAILABLE"
            replenishment_recommended = None
            recommended_order_quantity = None
            is_stockout_risk_high = False
            on_hand_status = "CURRENT_INVENTORY_POSITION_UNAVAILABLE"
        
        # 6. Financial & Capital Exposure
        safety_stock_capital = safety_stock * self.unit_cost
        weekly_holding_cost = (safety_stock_capital * self.holding_cost_rate) / 52.0
        
        # 7. Multi-Level Service Level Sensitivity Table
        sensitivity_records = []
        for sl in [0.85, 0.90, 0.95, 0.98, 0.99]:
            z_val = self._get_z_score(sl)
            ss_val = max(0.0, float(np.ceil(z_val * sigma_ltd)))
            rop_val = float(np.ceil(lead_time_demand + ss_val))
            cap_val = ss_val * self.unit_cost
            sensitivity_records.append({
                'Service Level': f"{int(sl * 100)}%",
                'Z-Score': z_val,
                'Safety Stock (Units)': int(ss_val),
                'Reorder Point (Units)': int(rop_val),
                'Working Capital (INR)': f"₹{cap_val:,.0f}"
            })

        return {
            'lead_time_weeks': lead_time,
            'target_service_level_pct': service_level * 100.0,
            'mean_weekly_demand': round(mean_weekly_demand, 1),
            'lead_time_demand': round(lead_time_demand, 1),
            'sigma_lead_time': round(sigma_ltd, 2),
            'uncertainty_basis': uncertainty_basis,
            'safety_stock_units': int(safety_stock),
            'reorder_point_units': int(reorder_point),
            'current_on_hand': display_on_hand,
            'on_hand_status': on_hand_status,
            'stockout_risk_pct': stockout_risk_pct,
            'stockout_method': stockout_method,
            'is_stockout_risk_high': is_stockout_risk_high,
            'safety_stock_capital_inr': round(safety_stock_capital, 2),
            'weekly_holding_cost_inr': round(weekly_holding_cost, 2),
            'sensitivity_table': pd.DataFrame(sensitivity_records),
            'replenishment_recommended': replenishment_recommended,
            'recommended_order_quantity': recommended_order_quantity
        }

    def _get_z_score(self, service_level: float) -> float:
        """Get z-score from normal distribution for given service level."""
        sl = min(0.999, max(0.50, float(service_level)))
        if sl in self.Z_LOOKUP:
            return self.Z_LOOKUP[sl]
        return float(stats.norm.ppf(sl))
