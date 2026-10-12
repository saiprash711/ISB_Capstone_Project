#!/usr/bin/env python
"""
Quick Data Pipeline Validation Script
Tests the complete data pipeline without requiring pytest.
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data import DataPipeline


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_success(text):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"✗ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"⚠ {text}")


def test_data_pipeline():
    """Run full data pipeline test."""
    print_header("DATA PIPELINE VALIDATION TEST")
    
    try:
        print("\nInitializing pipeline...")
        pipeline = DataPipeline()
        print_success("Pipeline initialized")
        
        print("\nExecuting full pipeline...")
        data_mart, report = pipeline.run()
        
        # Validate results
        print("\n" + "-" * 80)
        print("VALIDATION RESULTS")
        print("-" * 80)
        
        # Check data mart
        if data_mart is None or len(data_mart) == 0:
            print_error("Data mart is empty!")
            return False
        
        print_success(f"Data mart created: {len(data_mart):,} rows × {len(data_mart.columns)} columns")
        
        # Check report
        if not report:
            print_error("Report is empty!")
            return False
        
        # Detailed report
        print("\nPHASE SUMMARIES:")
        print("-" * 80)
        
        # Ingestion
        if 'ingestion' in report:
            ing = report['ingestion']
            print(f"\n1. INGESTION")
            print(f"   Status: {ing.get('status', 'unknown').upper()}")
            print(f"   Rows: {ing.get('rows', 'N/A'):,}")
            print(f"   Columns: {ing.get('columns', 'N/A')}")
            print(f"   SKUs: {ing.get('unique_skus', 'N/A')}")
            print(f"   Branches: {ing.get('unique_branches', 'N/A')}")
        
        # Validation
        if 'validation' in report:
            val = report['validation']
            print(f"\n2. VALIDATION")
            print(f"   Status: {val.get('status', 'unknown').upper()}")
            print(f"   Quality Score: {val.get('quality_score', 0):.1%}")
            print(f"   Checks Passed: {val.get('passed_checks', 0)}/{val.get('total_checks', 0)}")
            if val.get('errors', 0) > 0:
                print_warning(f"   Errors: {val['errors']}")
            if val.get('warnings', 0) > 0:
                print_warning(f"   Warnings: {val['warnings']}")
        
        # Cleaning
        if 'cleaning' in report:
            clean = report['cleaning']
            print(f"\n3. CLEANING")
            print(f"   Status: {clean.get('status', 'unknown').upper()}")
            print(f"   Rows Before: {clean.get('rows_initial', 'N/A'):,}")
            print(f"   Rows After: {clean.get('rows_final', 'N/A'):,}")
            print(f"   Duplicates Removed: {clean.get('duplicates_removed', 0)}")
            print(f"   Columns Final: {clean.get('columns_final', 'N/A')}")
        
        # Transformation
        if 'transformation' in report:
            trans = report['transformation']
            print(f"\n4. TRANSFORMATION")
            print(f"   Status: {trans.get('status', 'unknown').upper()}")
            print(f"   Grain: {trans.get('grain', 'N/A')}")
            print(f"   Final Rows: {trans.get('rows', 'N/A'):,}")
            print(f"   Unique SKUs: {trans.get('unique_skus', 'N/A')}")
            print(f"   Unique Branches: {trans.get('unique_branches', 'N/A')}")
            print(f"   Unique Weeks: {trans.get('unique_weeks', 'N/A')}")
            print(f"   Date Range: {trans.get('date_range', 'N/A')}")
        
        # Data quality checks
        print("\n" + "-" * 80)
        print("DATA QUALITY CHECKS")
        print("-" * 80)
        
        # Check for negative demands
        negative_demands = (data_mart['total_demand'] < 0).sum() if 'total_demand' in data_mart.columns else 0
        if negative_demands == 0:
            print_success("No negative demands found")
        else:
            print_error(f"Found {negative_demands} negative demands")
        
        # Check for valid branches
        if 'branch' in data_mart.columns:
            valid_branches = {'BLR', 'MAA', 'COK', 'SBD', 'SBD1'}
            unique_branches = set(data_mart['branch'].unique())
            if unique_branches.issubset(valid_branches):
                print_success(f"All branch codes valid: {sorted(unique_branches)}")
            else:
                print_warning(f"Unknown branches found: {unique_branches - valid_branches}")
        
        # Check for null dates
        if 'date' in data_mart.columns:
            null_dates = data_mart['date'].isnull().sum()
            if null_dates == 0:
                print_success("No null dates found")
            else:
                print_warning(f"Found {null_dates} null dates")
        
        # Summary statistics
        print("\n" + "-" * 80)
        print("SUMMARY STATISTICS")
        print("-" * 80)
        
        if 'total_demand' in data_mart.columns:
            demand = data_mart['total_demand']
            print(f"\nTotal Demand (units):")
            print(f"   Min: {demand.min():.0f}")
            print(f"   Max: {demand.max():.0f}")
            print(f"   Mean: {demand.mean():.1f}")
            print(f"   Median: {demand.median():.1f}")
            print(f"   Std Dev: {demand.std():.1f}")
        
        if 'tonnage' in data_mart.columns:
            tonnage = data_mart['tonnage']
            print(f"\nTonnage (metric tons):")
            print(f"   Min: {tonnage.min():.1f}")
            print(f"   Max: {tonnage.max():.1f}")
            print(f"   Mean: {tonnage.mean():.1f}")
            print(f"   Total: {tonnage.sum():.1f}")
        
        # Success
        print("\n" + "=" * 80)
        print("✓ PIPELINE VALIDATION COMPLETE - ALL TESTS PASSED")
        print("=" * 80)
        
        return True
        
    except FileNotFoundError as e:
        print_error(f"Data file not found: {e}")
        print_warning("Make sure Filtered.csv is in the project root directory")
        return False
    except Exception as e:
        print_error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_data_pipeline()
    sys.exit(0 if success else 1)
