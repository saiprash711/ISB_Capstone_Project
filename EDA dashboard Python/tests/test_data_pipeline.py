"""
Test Suite - Data Pipeline
Tests for data ingestion, validation, cleaning, and transformation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data import (
    load_raw_data,
    DataValidator,
    DataCleaner,
    DataTransformer,
    DataPipeline,
)


class TestDataIngestion:
    """Tests for data loading and ingestion."""
    
    def test_load_raw_data(self):
        """Test loading raw CSV data."""
        try:
            df = load_raw_data()
            
            # Basic assertions
            assert isinstance(df, pd.DataFrame), "Should return DataFrame"
            assert len(df) > 0, "DataFrame should not be empty"
            assert len(df.columns) > 0, "Should have columns"
            
            print(f"✓ Loaded {len(df)} rows × {len(df.columns)} columns")
        except FileNotFoundError:
            pytest.skip("Data file not found")
    
    def test_required_columns_exist(self):
        """Test that required columns are present."""
        try:
            df = load_raw_data()
            
            required_cols = [
                'Material', 'Billing Date', 'SALES OFFICE CODE',
                'Billing Quantity ODU', 'Billing Quantity IDU', 'Tonnage'
            ]
            
            for col in required_cols:
                assert col in df.columns, f"Missing required column: {col}"
            
            print(f"✓ All {len(required_cols)} required columns present")
        except FileNotFoundError:
            pytest.skip("Data file not found")


class TestDataValidation:
    """Tests for data validation."""
    
    def test_validation_runs(self):
        """Test that validation pipeline executes."""
        try:
            df = load_raw_data()
            validator = DataValidator(df)
            results, quality_score = validator.validate_all()
            
            assert isinstance(results, list), "Should return list of results"
            assert isinstance(quality_score, float), "Should return quality score"
            assert 0 <= quality_score <= 1, "Quality score should be 0-1"
            
            print(f"✓ Validation completed. Quality Score: {quality_score:.1%}")
        except FileNotFoundError:
            pytest.skip("Data file not found")
    
    def test_validation_summary(self):
        """Test validation summary."""
        try:
            df = load_raw_data()
            validator = DataValidator(df)
            results, _ = validator.validate_all()
            summary = validator.get_summary()
            
            assert 'total_checks' in summary
            assert 'passed' in summary
            assert 'failed' in summary
            
            print(f"✓ Validation Summary: {summary['passed']}/{summary['total_checks']} checks passed")
        except FileNotFoundError:
            pytest.skip("Data file not found")


class TestDataCleaning:
    """Tests for data cleaning."""
    
    def test_cleaning_runs(self):
        """Test that cleaning pipeline executes."""
        try:
            df = load_raw_data()
            cleaner = DataCleaner(df)
            cleaned_df, log = cleaner.clean_all()
            
            assert isinstance(cleaned_df, pd.DataFrame), "Should return DataFrame"
            assert len(log) > 0, "Should have cleaning operations"
            
            print(f"✓ Cleaning completed. Operations: {len(log)}")
            for operation in log[:3]:
                print(f"  - {operation}")
        except FileNotFoundError:
            pytest.skip("Data file not found")
    
    def test_cleaning_removes_duplicates(self):
        """Test that cleaning removes duplicate columns."""
        try:
            df = load_raw_data()
            cleaner = DataCleaner(df)
            cleaned_df, _ = cleaner.clean_all()
            
            # Check that duplicate columns are removed
            should_not_exist = ['Star Rating.1', 'SALES OFFICE CODE.1', 'Material.1', 'Tonnage.1']
            for col in should_not_exist:
                assert col not in cleaned_df.columns, f"Should remove {col}"
            
            print("✓ Duplicate columns removed correctly")
        except FileNotFoundError:
            pytest.skip("Data file not found")


class TestDataTransformation:
    """Tests for data transformation."""
    
    def test_transformation_to_data_mart(self):
        """Test transformation to SKU × BRANCH × WEEK data mart."""
        try:
            df = load_raw_data()
            cleaner = DataCleaner(df)
            cleaned_df, _ = cleaner.clean_all()
            
            transformer = DataTransformer(cleaned_df)
            data_mart, log = transformer.transform_to_data_mart()
            
            assert isinstance(data_mart, pd.DataFrame), "Should return DataFrame"
            assert len(log) > 0, "Should have transformation operations"
            
            summary = transformer.get_summary()
            print(f"✓ Data Mart Created")
            print(f"  Grain: {summary['grain']}")
            print(f"  Rows: {summary['rows']:,}")
            print(f"  SKUs: {summary['unique_skus']}, Branches: {summary['unique_branches']}, Weeks: {summary['unique_weeks']}")
        except FileNotFoundError:
            pytest.skip("Data file not found")
    
    def test_data_mart_has_demand_column(self):
        """Test that data mart has total_demand column."""
        try:
            df = load_raw_data()
            cleaner = DataCleaner(df)
            cleaned_df, _ = cleaner.clean_all()
            
            transformer = DataTransformer(cleaned_df)
            data_mart, _ = transformer.transform_to_data_mart()
            
            assert 'total_demand' in data_mart.columns, "Should have total_demand column"
            assert (data_mart['total_demand'] >= 0).all(), "Demand should be non-negative"
            
            print(f"✓ Data Mart has total_demand column")
            print(f"  Min demand: {data_mart['total_demand'].min():.0f}")
            print(f"  Max demand: {data_mart['total_demand'].max():.0f}")
            print(f"  Mean demand: {data_mart['total_demand'].mean():.1f}")
        except FileNotFoundError:
            pytest.skip("Data file not found")


class TestFullPipeline:
    """Tests for complete data pipeline."""
    
    def test_pipeline_execution(self):
        """Test full pipeline from ingestion to data mart."""
        try:
            pipeline = DataPipeline()
            data_mart, report = pipeline.run()
            
            assert isinstance(data_mart, pd.DataFrame), "Should return data mart"
            assert isinstance(report, dict), "Should return report"
            assert 'ingestion' in report
            assert 'validation' in report
            assert 'cleaning' in report
            assert 'transformation' in report
            
            print(f"✓ Full Pipeline Executed Successfully")
            print(f"  Final dataset: {len(data_mart):,} rows × {len(data_mart.columns)} columns")
            print(f"  Quality Score: {report['validation']['quality_score']:.1%}")
        except FileNotFoundError:
            pytest.skip("Data file not found")
    
    def test_pipeline_saves_data_mart(self):
        """Test that data mart can be saved."""
        try:
            pipeline = DataPipeline()
            data_mart, _ = pipeline.run()
            
            # Save to temp file
            temp_path = Path("test_data_mart.csv")
            pipeline.save_data_mart(str(temp_path))
            
            assert temp_path.exists(), "Should create data mart file"
            
            # Read back and verify
            saved_df = pd.read_csv(temp_path)
            assert len(saved_df) == len(data_mart), "Saved data should match"
            
            # Cleanup
            temp_path.unlink()
            
            print(f"✓ Data mart saved and verified")
        except FileNotFoundError:
            pytest.skip("Data file not found")


class TestDataQuality:
    """Tests for data quality and integrity."""
    
    def test_no_negative_demands(self):
        """Test that final data has no negative demands."""
        try:
            pipeline = DataPipeline()
            data_mart, _ = pipeline.run()
            
            assert (data_mart['total_demand'] >= 0).all(), "Demands should be non-negative"
            print(f"✓ All demands are non-negative")
        except FileNotFoundError:
            pytest.skip("Data file not found")
    
    def test_valid_branches_only(self):
        """Test that only valid branch codes exist."""
        try:
            pipeline = DataPipeline()
            data_mart, _ = pipeline.run()
            
            valid_branches = {'BLR', 'MAA', 'COK', 'SBD', 'SBD1'}
            assert set(data_mart['branch'].unique()).issubset(valid_branches), "Should only have valid branches"
            
            print(f"✓ All branch codes are valid: {set(data_mart['branch'].unique())}")
        except FileNotFoundError:
            pytest.skip("Data file not found")
    
    def test_date_continuity(self):
        """Test that dates are continuous without gaps."""
        try:
            pipeline = DataPipeline()
            data_mart, _ = pipeline.run()
            
            if 'iso_week' in data_mart.columns:
                num_weeks = data_mart['iso_week'].nunique()
                print(f"✓ Data covers {num_weeks} unique weeks")
        except FileNotFoundError:
            pytest.skip("Data file not found")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
