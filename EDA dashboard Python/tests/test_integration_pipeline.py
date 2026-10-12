"""
End-to-End Forecasting & Intelligence Integration Pipeline Test
Verifies the complete flow:
DataMart -> Features -> LeakageAudit -> Classification -> Backtesting -> 
Champion Selection -> Uncertainty Calibration -> Inventory Optimization -> 
Scenario Simulation -> Monitoring & Alert Action Queue.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.transformation import DataTransformer
from src.features.engineering import FeatureEngineer
from src.validation.leakage_audit import LeakageAuditor
from src.selection.demand_classifier import DemandClassifier
from src.selection.model_selector import ModelSelector
from src.uncertainty.prediction_intervals import ProbabilisticForecastEngine
from src.inventory.inventory_engine import InventoryEngine
from src.scenarios.simulator import ScenarioSimulator
from src.monitoring.forecast_monitor import ForecastMonitor
from src.monitoring.alerts import AlertEngine


def generate_synthetic_hvac_transactions(n_weeks: int = 40) -> pd.DataFrame:
    """Generate realistic synthetic transaction data for integration testing."""
    np.random.seed(42)
    start_date = datetime(2023, 1, 2)
    records = []
    
    sku = "RKM50UV16VA"
    branch = "BLR"
    
    for w in range(n_weeks):
        dt = start_date + timedelta(weeks=w)
        # Seasonal summer peak around weeks 12-24
        base_demand = 100 + 40 * np.sin(2 * np.pi * (w - 8) / 40)
        noise = np.random.normal(0, 8)
        qty = max(10.0, float(base_demand + noise))
        
        records.append({
            'date': dt,
            'sku': sku,
            'branch': branch,
            'quantity_odu': qty,
            'quantity_idu': qty * 0.95,
            'tonnage': qty * 1.5,
            'segment': 'RESIDENTIAL',
            'star_rating': '5-STAR',
            'material_group': 'INVERTER',
            'sbu': 'RAC'
        })
        
    return pd.DataFrame(records)


class TestIntegrationPipeline:
    """Comprehensive test validating the end-to-end chain with zero synthetic shortcuts."""

    def test_full_pipeline_chain(self):
        # 1. Raw Data -> Data Mart
        raw_df = generate_synthetic_hvac_transactions(40)
        transformer = DataTransformer(raw_df)
        data_mart, t_log = transformer.transform_to_data_mart()
        
        assert isinstance(data_mart, pd.DataFrame)
        assert len(data_mart) >= 35
        assert 'total_demand' in data_mart.columns
        assert (data_mart['total_demand'] >= 0).all()

        # 2. Data Mart -> Feature Engineering
        engineer = FeatureEngineer(config={'lags': [1, 2, 4], 'rolling_windows': [4, 8]})
        df_feat, feat_cols = engineer.engineer_features(data_mart)
        assert 'lag_1' in df_feat.columns
        assert 'rolling_mean_4' in df_feat.columns

        # 3. Leakage Audit Certification
        auditor = LeakageAuditor()
        audit_res = auditor.run_full_audit(
            df_feat, 
            folds=[(np.arange(0, 24), np.arange(24, 32)), (np.arange(0, 32), np.arange(32, 40))],
            target_col='total_demand'
        )
        assert audit_res['overall_status'] == 'VERIFIED_ZERO_LEAKAGE'
        assert audit_res['leakage_percentage'] == 0.0

        # 4. Demand Classification
        classifier = DemandClassifier()
        sku_series = data_mart['total_demand'].values
        profile = classifier.profile_demand(sku_series)
        assert profile['base_quadrant'] in ["Smooth", "Intermittent", "Lumpy", "Erratic"]
        assert profile['adi'] >= 1.0
        assert profile['cv2'] >= 0

        # 5 & 6. End-to-End Model Selection, Backtesting & Probabilistic Calibration
        selector = ModelSelector(n_folds=2, test_weeks=4, min_train_weeks=20)
        selection_result = selector.select_and_fit(data_mart, sku="RKM50UV16VA", branch="BLR", horizon=12)
        
        assert selection_result['status'] == 'success'
        assert 'champion' in selection_result
        assert 'forward_forecast' in selection_result
        assert len(selection_result['forward_forecast']) == 12
        assert 'p10' in selection_result and 'p90' in selection_result
        assert (selection_result['p10'] <= selection_result['p50']).all()
        assert (selection_result['p50'] <= selection_result['p90']).all()
        assert not selection_result['leaderboard'].empty

        # 7. Inventory Optimization Policy
        inv_engine = InventoryEngine(default_lead_time=2, default_service_level=0.95, unit_cost=20000.0)
        forecast_p50 = selection_result['p50']
        rmse_val = float(selection_result['champion'].get('mean_rmse', 15.0))
        
        policy = inv_engine.calculate_inventory_policy(
            forecast_values=forecast_p50,
            forecast_rmse=rmse_val,
            lead_time_weeks=2,
            target_service_level=0.95,
            current_on_hand=float(np.mean(forecast_p50) * 1.5)
        )
        assert policy['safety_stock_units'] >= 0
        assert policy['reorder_point_units'] >= policy['safety_stock_units']
        assert 0.0 <= policy['stockout_risk_pct'] <= 100.0

        # 8. Scenario Shock Simulator
        simulator = ScenarioSimulator()
        heatwave_res = simulator.simulate(forecast_p50, scenario_name='Summer Heatwave (+30%)')
        assert heatwave_res['multiplier'] == 1.30
        assert heatwave_res['delta_volume_units'] > 0
        assert heatwave_res['scenario_total_volume'] > heatwave_res['base_total_volume']

        # 9. Monitoring & Alert Action Queue
        monitor = ForecastMonitor()
        simulated_actuals = forecast_p50 + np.random.normal(0, 5, size=12)
        health_res = monitor.evaluate_model_health(simulated_actuals, forecast_p50)
        assert 'tracking_signal' in health_res
        assert 'health_status' in health_res

        sku_assessments = [{
            'sku': 'RKM50UV16VA',
            'branch': 'BLR',
            'stockout_risk_pct': policy['stockout_risk_pct'],
            'health_status': health_res['health_status'],
            'tracking_signal': health_res['tracking_signal'],
            'model': selection_result['champion']['model_name']
        }]
        action_queue = AlertEngine.generate_action_queue(sku_assessments)
        assert isinstance(action_queue, list)
        assert len(action_queue) > 0
        assert 'recommended_action' in action_queue[0]
        assert 'priority' in action_queue[0]
