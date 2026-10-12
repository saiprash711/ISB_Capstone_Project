"""
Data Pipeline Orchestrator
Coordinates the full data pipeline from raw ingestion to canonical data mart.
"""
import pandas as pd
from typing import Tuple, Dict
import logging

# Import pipeline modules
from .ingestion import load_raw_data, get_dataset_info
from .validation import DataValidator
from .cleaning import DataCleaner
from .transformation import DataTransformer

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Full data processing pipeline.
    
    Flow:
        Raw Data → Validation → Cleaning → Transformation → Data Mart
    """
    
    def __init__(self, data_filepath: str = None):
        """
        Initialize pipeline.
        
        Args:
            data_filepath: Path to data file (auto-detected if None)
        """
        self.data_filepath = data_filepath
        self.raw_data = None
        self.validated_data = None
        self.cleaned_data = None
        self.data_mart = None
        self.pipeline_report = {}
    
    def run(self) -> Tuple[pd.DataFrame, Dict]:
        """
        Execute full pipeline.
        
        Returns:
            Tuple of (final_data_mart, comprehensive_report)
        """
        logger.info("=" * 80)
        logger.info("STARTING FULL DATA PIPELINE")
        logger.info("=" * 80)
        
        try:
            # Step 1: INGESTION
            logger.info("\n[1/4] INGESTION PHASE")
            self._run_ingestion()
            
            # Step 2: VALIDATION
            logger.info("\n[2/4] VALIDATION PHASE")
            self._run_validation()
            
            # Step 3: CLEANING
            logger.info("\n[3/4] CLEANING PHASE")
            self._run_cleaning()
            
            # Step 4: TRANSFORMATION
            logger.info("\n[4/4] TRANSFORMATION PHASE")
            self._run_transformation()
            
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETE - READY FOR FORECASTING")
            logger.info("=" * 80)
            
            return self.data_mart, self.pipeline_report
            
        except Exception as e:
            logger.error(f"PIPELINE ERROR: {str(e)}", exc_info=True)
            raise
    
    def _run_ingestion(self):
        """Step 1: Load raw data."""
        self.raw_data = load_raw_data(self.data_filepath)
        
        info = get_dataset_info(self.raw_data)
        self.pipeline_report['ingestion'] = {
            'status': 'success',
            'rows': info['rows'],
            'columns': info['columns'],
            'memory_mb': round(info['memory_mb'], 2),
            'unique_skus': info['unique_skus'],
            'unique_branches': info['unique_branches'],
        }
        
        logger.info(f"✓ Loaded {info['rows']:,} rows × {info['columns']} columns")
        logger.info(f"  Memory: {info['memory_mb']:.1f} MB")
        logger.info(f"  SKUs: {info['unique_skus']}, Branches: {info['unique_branches']}")
    
    def _run_validation(self):
        """Step 2: Validate data quality."""
        validator = DataValidator(self.raw_data)
        validation_results, quality_score = validator.validate_all()
        summary = validator.get_summary()
        
        self.pipeline_report['validation'] = {
            'status': 'success',
            'quality_score': round(quality_score, 3),
            'total_checks': summary['total_checks'],
            'passed_checks': summary['passed'],
            'failed_checks': summary['failed'],
            'errors': summary['errors'],
            'warnings': summary['warnings'],
            'detailed_results': [
                {
                    'check': r.check_name,
                    'passed': r.passed,
                    'severity': r.severity,
                    'message': r.message,
                    'affected_rows': r.affected_rows
                }
                for r in validation_results
            ]
        }
        
        logger.info(f"✓ Quality Score: {quality_score:.1%}")
        logger.info(f"  Checks: {summary['passed']}/{summary['total_checks']} passed")
        if summary['errors'] > 0:
            logger.warning(f"  Errors: {summary['errors']}")
        if summary['warnings'] > 0:
            logger.warning(f"  Warnings: {summary['warnings']}")
        
        self.validated_data = self.raw_data
    
    def _run_cleaning(self):
        """Step 3: Clean data."""
        cleaner = DataCleaner(self.validated_data)
        self.cleaned_data, cleaning_log = cleaner.clean_all()
        summary = cleaner.get_summary()
        
        # Handle missing values
        imputed_count = cleaner.handle_missing_tonnage()
        
        self.pipeline_report['cleaning'] = {
            'status': 'success',
            'rows_initial': len(self.validated_data),
            'rows_final': summary['rows_final'],
            'columns_final': summary['columns_final'],
            'duplicates_removed': len(self.validated_data) - summary['rows_final'],
            'values_imputed': imputed_count,
            'operations': cleaning_log
        }
        
        logger.info(f"✓ Rows: {len(self.validated_data):,} → {summary['rows_final']:,}")
        logger.info(f"  Duplicates removed: {len(self.validated_data) - summary['rows_final']}")
        logger.info(f"  Columns standardized: {summary['columns_final']}")
        logger.info(f"  Operations: {len(cleaning_log)}")
    
    def _run_transformation(self):
        """Step 4: Transform to data mart."""
        transformer = DataTransformer(self.cleaned_data)
        self.data_mart, transformation_log = transformer.transform_to_data_mart()
        summary = transformer.get_summary()
        
        self.pipeline_report['transformation'] = {
            'status': 'success',
            'grain': summary['grain'],
            'rows': summary['rows'],
            'columns': summary['columns'],
            'unique_skus': summary['unique_skus'],
            'unique_branches': summary['unique_branches'],
            'unique_weeks': summary['unique_weeks'],
            'date_range': summary['date_range'],
            'operations': transformation_log
        }
        
        logger.info(f"✓ Data Mart Created")
        logger.info(f"  Grain: {summary['grain']}")
        logger.info(f"  Rows: {summary['rows']:,}")
        logger.info(f"  SKUs: {summary['unique_skus']}, Branches: {summary['unique_branches']}, Weeks: {summary['unique_weeks']}")
        logger.info(f"  Date Range: {summary['date_range']}")
    
    def get_report(self) -> Dict:
        """Get full pipeline execution report."""
        return self.pipeline_report
    
    def save_data_mart(self, filepath: str) -> str:
        """
        Save data mart to CSV.
        
        Args:
            filepath: Output file path
            
        Returns:
            filepath on success
        """
        if self.data_mart is None:
            raise ValueError("Data mart not created. Run pipeline first.")
        
        self.data_mart.to_csv(filepath, index=False)
        logger.info(f"✓ Data mart saved to: {filepath}")
        return filepath
