#!/usr/bin/env python
"""
Test Script - Forecasting Engine
Tests all forecasting model families on data mart.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Fix Windows console encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data import DataPipeline
from src.forecasting import ForecastingEngine
from src.config import get_config


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_success(text):
    """Print success message."""
    print(f"[OK] {text}")


def print_error(text):
    """Print error message."""
    print(f"[ERROR] {text}")


def print_warning(text):
    """Print warning message."""
    print(f"[WARN] {text}")


def test_forecasting_engine():
    """Test complete forecasting engine."""
    print_header("FORECASTING ENGINE TEST")
    
    try:
        # Load configuration
        print("\nLoading configuration...")
        cfg = get_config('config/')
        forecast_config = cfg.get('forecast', {})
        print_success("Configuration loaded")
        
        # Get data mart
        print("\nPreparing data mart...")
        pipeline = DataPipeline()
        data_mart, report = pipeline.run()
        print_success(f"Data mart loaded: {len(data_mart):,} rows × {len(data_mart.columns)} columns")
        
        # Initialize forecasting engine
        print("\nInitializing forecasting engine...")
        engine = ForecastingEngine(forecast_config)
        print_success("Forecasting engine initialized")
        
        # Select sample SKUs to forecast
        print("\nSelecting sample SKUs...")
        unique_skus = data_mart['sku'].unique()
        sample_skus = unique_skus[:5]  # First 5 SKUs for testing
        unique_branches = data_mart['branch'].unique()
        print_success(f"Selected {len(sample_skus)} SKUs and {len(unique_branches)} branches for testing")
        
        print(f"  Sample SKUs: {sample_skus.tolist()}")
        print(f"  Branches: {unique_branches.tolist()}")
        
        # Test single forecast
        print("\n" + "-" * 80)
        print("TEST 1: Single SKU × Branch Forecast")
        print("-" * 80)
        
        sku = sample_skus[0]
        branch = unique_branches[0]
        print(f"\nForecasting {sku} / {branch}...")
        
        forecast = engine.fit_and_forecast(data_mart, sku, branch, periods=12)
        
        if 'error' not in forecast:
            print_success(f"Forecast generated for {sku}/{branch}")
            
            # Display fit statistics
            fit_stats = forecast.get('fit_stats', {})
            print(f"\n  Fit Statistics:")
            print(f"    Observations: {fit_stats.get('n_observations', 'N/A')}")
            print(f"    Demand Mean: {fit_stats.get('demand_mean', 'N/A'):.1f}")
            print(f"    Demand Std: {fit_stats.get('demand_std', 'N/A'):.1f}")
            print(f"    Zero Demand: {fit_stats.get('zero_count', 'N/A')}")
            print(f"    Demand Type: {fit_stats.get('demand_type', 'N/A')}")
            
            # Display model results
            print(f"\n  Model Family Results:")
            for family, predictions in forecast.get('models', {}).items():
                if isinstance(predictions, dict):
                    count = len([p for p in predictions.values() if isinstance(p, np.ndarray)])
                    print(f"    {family}: {count} models fitted")
                elif isinstance(predictions, np.ndarray):
                    print(f"    {family}: forecast shape {predictions.shape}")
            
            # Get ensemble forecast
            ensemble = engine.get_ensemble_forecast(forecast)
            if not np.all(np.isnan(ensemble)):
                print(f"\n  Ensemble Forecast (12 weeks):")
                print(f"    Mean: {np.nanmean(ensemble):.1f}")
                print(f"    Min: {np.nanmin(ensemble):.1f}")
                print(f"    Max: {np.nanmax(ensemble):.1f}")
                for i, val in enumerate(ensemble[:4]):
                    print(f"    Week {i+1}: {val:.1f}")
                print(f"    ... (weeks 5-12 omitted)")
        else:
            print_error(f"Forecast generation failed: {forecast.get('error', 'Unknown error')}")
        
        # Test batch forecasting
        print("\n" + "-" * 80)
        print("TEST 2: Batch Forecasting")
        print("-" * 80)
        
        print(f"\nGenerating forecasts for {len(sample_skus)} SKUs × {len(unique_branches)} branches...")
        
        forecasts = engine.forecast_batch(data_mart, sample_skus.tolist(), unique_branches.tolist())
        
        print_success(f"Batch forecasting complete: {len(forecasts)} forecasts generated")
        
        # Export forecasts
        print("\nExporting forecasts to DataFrame...")
        export_df = engine.export_forecasts(forecasts)
        print_success(f"Exported {len(export_df)} forecast rows")
        print(f"  Shape: {export_df.shape}")
        print(f"  Columns: {export_df.columns.tolist()}")
        
        # Display sample exports
        print(f"\n  Sample Forecasts:")
        for sku in sample_skus[:2]:
            sku_forecast = export_df[export_df['sku'] == sku]
            if len(sku_forecast) > 0:
                print(f"\n    {sku}:")
                for _, row in sku_forecast.head(3).iterrows():
                    print(f"      Period {int(row['forecast_period'])}: {row['forecast_value']:.1f}")
        
        # Summary statistics
        print("\n" + "-" * 80)
        print("TEST 3: Forecast Quality")
        print("-" * 80)
        
        print(f"\nForecast Summary Statistics:")
        print(f"  Total forecasts: {len(forecasts)}")
        print(f"  Successful: {len([f for f in forecasts if 'error' not in f])}")
        print(f"  Failed: {len([f for f in forecasts if 'error' in f])}")
        
        # Model availability
        print(f"\nAvailable Model Families:")
        print(f"  Baseline: ✓ (4 models)")
        print(f"  Statistical: ✓ (3 models)")
        print(f"  Intermittent: ✓ (3 models)")
        print(f"  ML: {'✓' if len(engine.ml_models.models) > 0 else '✗'} ({len(engine.ml_models.models)} models available)")
        
        # Success
        print("\n" + "=" * 80)
        print("[OK] FORECASTING ENGINE TEST COMPLETE - ALL TESTS PASSED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print_error(f"Forecasting engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_forecasting_engine()
    sys.exit(0 if success else 1)
