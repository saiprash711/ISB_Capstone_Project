"""
Scenario Analysis & What-If Simulator Module
Allows executives to test demand shocks, promotional uplifts, heatwaves,
and economic slowdowns, measuring operational and inventory impacts.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from src.inventory.inventory_engine import InventoryEngine


class ScenarioSimulator:
    """
    Simulates demand stress tests and market what-if scenarios.
    """
    
    SCENARIO_PROFILES = {
        'Base Case': {
            'description': 'Baseline statistical champion forecast with historical trajectories.',
            'multiplier': 1.0,
            'driver': 'Historical Run-Rate'
        },
        'Summer Heatwave (+30%)': {
            'description': 'Severe summer heatwave across South Region driving unseasonable AC cooling demand surge.',
            'multiplier': 1.30,
            'driver': 'Extreme Weather & Peak Cooling Season'
        },
        'Dealer Festive Scheme (+20%)': {
            'description': 'Diwali / Pongal distributor financing scheme and promotional stocking push.',
            'multiplier': 1.20,
            'driver': 'Channel Promotion & Volume Incentives'
        },
        'Supply Chain Headwind (-20%)': {
            'description': 'Component or refrigerant shortage leading to order fulfillment throttling and dampening.',
            'multiplier': 0.80,
            'driver': 'Supply Constraint & Macro Slowdown'
        },
        'Aggressive Market Expansion (+15%)': {
            'description': 'Competitor price adjustment and new dealer onboarding in Tier 2 cities.',
            'multiplier': 1.15,
            'driver': 'Market Share Capture'
        }
    }
    
    def __init__(self, inventory_engine: Optional[InventoryEngine] = None):
        self.inventory_engine = inventory_engine or InventoryEngine()

    def simulate(self, base_forecast: np.ndarray,
                 scenario_name: str = 'Base Case',
                 custom_multiplier: Optional[float] = None,
                 lead_time_weeks: int = 2,
                 service_level: float = 0.95,
                 forecast_residuals: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Execute scenario simulation on a base forecast curve.

        Scenario multipliers are planning assumptions (not estimated from the data).
        `forecast_residuals` are the champion's out-of-sample backtest errors; they set the
        safety-stock uncertainty and are scaled by the multiplier for the scenario case
        (errors assumed proportional to demand level). Without them safety stock is 0.
        """
        base_f = np.asarray(base_forecast, dtype=float)
        
        if custom_multiplier is not None:
            mult = max(0.1, float(custom_multiplier))
            desc = f"Custom scenario with {((mult - 1.0) * 100.0):+.1f}% demand adjustment."
            driver = "User-Defined Assumption"
        elif scenario_name in self.SCENARIO_PROFILES:
            profile = self.SCENARIO_PROFILES[scenario_name]
            mult = profile['multiplier']
            desc = profile['description']
            driver = profile['driver']
        else:
            mult = 1.0
            desc = "Standard baseline forecast."
            driver = "Historical Trend"

        # Apply multiplier
        scenario_forecast = np.maximum(0.0, base_f * mult)
        
        # Calculate base and scenario inventory policies
        res = np.asarray(forecast_residuals, dtype=float) if forecast_residuals is not None else None
        base_inv = self.inventory_engine.calculate_inventory_policy(
            base_f, forecast_residuals=res, lead_time_weeks=lead_time_weeks, target_service_level=service_level
        )
        scen_inv = self.inventory_engine.calculate_inventory_policy(
            scenario_forecast, forecast_residuals=None if res is None else res * mult,
            lead_time_weeks=lead_time_weeks, target_service_level=service_level
        )

        delta_total_demand = float(np.sum(scenario_forecast) - np.sum(base_f))
        delta_ss = scen_inv['safety_stock_units'] - base_inv['safety_stock_units']
        delta_rop = scen_inv['reorder_point_units'] - base_inv['reorder_point_units']
        delta_capital = scen_inv['safety_stock_capital_inr'] - base_inv['safety_stock_capital_inr']

        return {
            'scenario_name': scenario_name,
            'description': desc,
            'driver': driver,
            'multiplier': round(mult, 2),
            'base_forecast': base_f,
            'scenario_forecast': scenario_forecast,
            'base_total_volume': round(float(np.sum(base_f)), 1),
            'scenario_total_volume': round(float(np.sum(scenario_forecast)), 1),
            'delta_volume_units': round(delta_total_demand, 1),
            'delta_volume_pct': round((mult - 1.0) * 100.0, 1),
            'base_safety_stock': base_inv['safety_stock_units'],
            'scenario_safety_stock': scen_inv['safety_stock_units'],
            'delta_safety_stock': delta_ss,
            'base_rop': base_inv['reorder_point_units'],
            'scenario_rop': scen_inv['reorder_point_units'],
            'delta_rop': delta_rop,
            'base_capital_inr': base_inv['safety_stock_capital_inr'],
            'scenario_capital_inr': scen_inv['safety_stock_capital_inr'],
            'delta_capital_inr': delta_capital,
            'base_stockout_risk_pct': base_inv['stockout_risk_pct'],
            'scenario_stockout_risk_pct': scen_inv['stockout_risk_pct']
        }

    def get_all_scenarios_summary(self, base_forecast: np.ndarray,
                                  forecast_residuals: Optional[np.ndarray] = None,
                                  lead_time_weeks: int = 2, service_level: float = 0.95) -> pd.DataFrame:
        """
        Run all pre-defined scenarios and return comparative executive summary table.
        """
        rows = []
        for name in self.SCENARIO_PROFILES.keys():
            res = self.simulate(base_forecast, scenario_name=name, forecast_residuals=forecast_residuals,
                                lead_time_weeks=lead_time_weeks, service_level=service_level)
            rows.append({
                'Scenario': name,
                'Multiplier': f"{res['multiplier']:.2f}x",
                f'Total {len(base_forecast)}W Demand': f"{res['scenario_total_volume']:,.0f} units",
                'Delta Units': f"{res['delta_volume_units']:+,.0f}",
                'Required Safety Stock': f"{res['scenario_safety_stock']:,} units",
                'Delta Working Capital': f"{'₹' + format(int(res['delta_capital_inr']), ',') if res['delta_capital_inr'] >= 0 else '-₹' + format(int(abs(res['delta_capital_inr'])), ',')}"
            })
        return pd.DataFrame(rows)
