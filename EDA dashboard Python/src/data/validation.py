"""
Data Validation Module
Comprehensive data quality checks and validation rules.
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Container for validation check results."""
    check_name: str
    passed: bool
    message: str
    severity: str = "warning"  # "error", "warning", "info"
    details: Dict = None
    affected_rows: int = 0


class DataValidator:
    """Comprehensive data validation and quality checking."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize validator with dataset.
        
        Args:
            df: Input dataframe to validate
        """
        self.df = df
        self.results = []
    
    def validate_all(self) -> Tuple[List[ValidationResult], float]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (results list, overall quality score 0-1)
        """
        self.results = []
        
        # Schema validation
        self.check_required_columns()
        self.check_column_types()
        
        # Data quality checks
        self.check_missing_values()
        self.check_duplicates()
        self.check_invalid_values()
        self.check_inconsistent_values()
        self.check_data_gaps()
        self.check_business_logic()
        
        # Calculate quality score
        quality_score = self._calculate_quality_score()
        
        return self.results, quality_score
    
    def check_required_columns(self) -> ValidationResult:
        """Verify all required columns are present."""
        required_cols = [
            'Material', 'SALES OFFICE CODE', 'Billing Date', 'Billing Quantity ODU',
            'Billing Quantity IDU', 'Tonnage', 'Segment', 'Star Rating', 'Week', 'Year', 'Month'
        ]
        
        missing = [col for col in required_cols if col not in self.df.columns]
        
        if missing:
            result = ValidationResult(
                check_name="Required Columns",
                passed=False,
                message=f"Missing columns: {missing}",
                severity="error"
            )
        else:
            result = ValidationResult(
                check_name="Required Columns",
                passed=True,
                message=f"All {len(required_cols)} required columns present"
            )
        
        self.results.append(result)
        return result
    
    def check_column_types(self) -> List[ValidationResult]:
        """Check that columns have appropriate data types."""
        type_checks = {
            'Material': 'object',  # SKU
            'SALES OFFICE CODE': 'object',  # Branch
            'Billing Date': 'datetime64',
            'Billing Quantity ODU': ('int64', 'float64'),
            'Billing Quantity IDU': ('int64', 'float64'),
            'Tonnage': ('int64', 'float64', 'object'),
        }
        
        for col, expected_type in type_checks.items():
            if col not in self.df.columns:
                continue
            
            if isinstance(expected_type, tuple):
                type_ok = self.df[col].dtype in expected_type or any(
                    pd.api.types.is_dtype_equal(self.df[col].dtype, t) for t in expected_type
                )
            else:
                type_ok = self.df[col].dtype == expected_type or pd.api.types.is_dtype_equal(
                    self.df[col].dtype, expected_type
                )
            
            if not type_ok:
                # Try to parse dates
                if col == 'Billing Date' and self.df[col].dtype == 'object':
                    type_ok = True  # We'll handle this in cleaning
            
            result = ValidationResult(
                check_name=f"Column Type: {col}",
                passed=type_ok,
                message=f"{col}: expected {expected_type}, got {self.df[col].dtype}",
                severity="warning" if not type_ok else "info"
            )
            self.results.append(result)
    
    def check_missing_values(self) -> ValidationResult:
        """Check for missing/null values."""
        missing_counts = self.df.isnull().sum()
        missing_pct = (missing_counts / len(self.df) * 100).round(2)
        missing_cols = missing_counts[missing_counts > 0]
        
        if len(missing_cols) > 0:
            message = "Missing values found:\n"
            for col, count in missing_cols.items():
                message += f"  {col}: {count} ({missing_pct[col]:.2f}%)\n"
            
            result = ValidationResult(
                check_name="Missing Values",
                passed=False,
                message=message.strip(),
                severity="warning",
                affected_rows=missing_counts.sum()
            )
        else:
            result = ValidationResult(
                check_name="Missing Values",
                passed=True,
                message="No missing values detected"
            )
        
        self.results.append(result)
        return result
    
    def check_duplicates(self) -> ValidationResult:
        """Check for duplicate records."""
        # Check for complete row duplicates
        complete_dupes = self.df.duplicated().sum()
        
        # Check for duplicate SKU/Date/Branch combinations (key duplicates)
        if all(col in self.df.columns for col in ['Material', 'Billing Date', 'SALES OFFICE CODE']):
            key_dupes = self.df.duplicated(
                subset=['Material', 'Billing Date', 'SALES OFFICE CODE'],
                keep=False
            ).sum()
        else:
            key_dupes = 0
        
        if complete_dupes > 0 or key_dupes > 0:
            message = ""
            if complete_dupes > 0:
                message += f"Complete row duplicates: {complete_dupes}\n"
            if key_dupes > 0:
                message += f"SKU/Date/Branch key duplicates: {key_dupes}"
            
            result = ValidationResult(
                check_name="Duplicates",
                passed=False,
                message=message.strip(),
                severity="warning",
                affected_rows=max(complete_dupes, key_dupes)
            )
        else:
            result = ValidationResult(
                check_name="Duplicates",
                passed=True,
                message="No duplicates detected"
            )
        
        self.results.append(result)
        return result
    
    def check_invalid_values(self) -> List[ValidationResult]:
        """Check for invalid/impossible values."""
        results = []
        
        # Check for negative quantities
        for col in ['Billing Quantity ODU', 'Billing Quantity IDU', 'Tonnage']:
            if col in self.df.columns:
                negative_count = (self.df[col] < 0).sum()
                if negative_count > 0:
                    result = ValidationResult(
                        check_name=f"Negative Values: {col}",
                        passed=False,
                        message=f"{col}: {negative_count} negative values",
                        severity="error",
                        affected_rows=negative_count
                    )
                else:
                    result = ValidationResult(
                        check_name=f"Negative Values: {col}",
                        passed=True,
                        message=f"{col}: No negative values"
                    )
                results.append(result)
        
        # Check for invalid dates
        if 'Billing Date' in self.df.columns:
            try:
                dates = pd.to_datetime(self.df['Billing Date'], dayfirst=True, errors='coerce')
                invalid_dates = dates.isnull().sum()
                if invalid_dates > 0:
                    result = ValidationResult(
                        check_name="Invalid Dates",
                        passed=False,
                        message=f"Invalid dates found: {invalid_dates}",
                        severity="error",
                        affected_rows=invalid_dates
                    )
                else:
                    result = ValidationResult(
                        check_name="Invalid Dates",
                        passed=True,
                        message="All dates valid"
                    )
                results.append(result)
            except Exception as e:
                result = ValidationResult(
                    check_name="Invalid Dates",
                    passed=False,
                    message=f"Date parsing error: {str(e)}",
                    severity="error"
                )
                results.append(result)
        
        self.results.extend(results)
        return results
    
    def check_inconsistent_values(self) -> List[ValidationResult]:
        """Check for inconsistent categorical values."""
        results = []
        
        # Check branch codes
        if 'SALES OFFICE CODE' in self.df.columns:
            valid_branches = ['BLR', 'MAA', 'COK', 'SBD', 'SBD1']
            invalid_branches = self.df[~self.df['SALES OFFICE CODE'].isin(valid_branches)]['SALES OFFICE CODE'].unique()
            
            if len(invalid_branches) > 0:
                result = ValidationResult(
                    check_name="Invalid Branch Codes",
                    passed=False,
                    message=f"Unknown branches: {invalid_branches.tolist()}",
                    severity="warning"
                )
            else:
                result = ValidationResult(
                    check_name="Invalid Branch Codes",
                    passed=True,
                    message=f"All {self.df['SALES OFFICE CODE'].nunique()} branches valid"
                )
            results.append(result)
        
        self.results.extend(results)
        return results
    
    def check_data_gaps(self) -> ValidationResult:
        """Check for missing time periods."""
        if 'Billing Date' in self.df.columns:
            try:
                dates = pd.to_datetime(self.df['Billing Date'], dayfirst=True, errors='coerce')
                date_range = (dates.max() - dates.min()).days
                expected_weeks = date_range / 7
                actual_weeks = self.df['Week'].nunique() if 'Week' in self.df.columns else 0
                
                # Check if we have good coverage
                coverage_pct = (actual_weeks / expected_weeks * 100) if expected_weeks > 0 else 0
                
                if coverage_pct < 80:
                    result = ValidationResult(
                        check_name="Time Coverage",
                        passed=False,
                        message=f"Data coverage only {coverage_pct:.1f}% (expected ~100%)",
                        severity="warning"
                    )
                else:
                    result = ValidationResult(
                        check_name="Time Coverage",
                        passed=True,
                        message=f"Good time coverage: {coverage_pct:.1f}%"
                    )
            except:
                result = ValidationResult(
                    check_name="Time Coverage",
                    passed=False,
                    message="Could not assess time coverage",
                    severity="info"
                )
        else:
            result = ValidationResult(
                check_name="Time Coverage",
                passed=False,
                message="Billing Date column not found",
                severity="warning"
            )
        
        self.results.append(result)
        return result
    
    def check_business_logic(self) -> List[ValidationResult]:
        """Check business logic constraints."""
        results = []
        
        # Check: Tonnage should roughly match quantity * weight per unit
        if all(col in self.df.columns for col in ['Billing Quantity ODU', 'Tonnage']):
            # Heuristic: if tonnage is zero when quantity is high, flag it
            zero_tonnage_nonzero_qty = (
                (self.df['Billing Quantity ODU'] > 0) & (self.df['Tonnage'] == 0)
            ).sum()
            
            if zero_tonnage_nonzero_qty > 0:
                result = ValidationResult(
                    check_name="Quantity/Tonnage Mismatch",
                    passed=False,
                    message=f"Found {zero_tonnage_nonzero_qty} rows with quantity but zero tonnage",
                    severity="warning",
                    affected_rows=zero_tonnage_nonzero_qty
                )
            else:
                result = ValidationResult(
                    check_name="Quantity/Tonnage Mismatch",
                    passed=True,
                    message="Quantity/Tonnage relationship looks reasonable"
                )
            results.append(result)
        
        self.results.extend(results)
        return results
    
    def _calculate_quality_score(self) -> float:
        """
        Calculate overall data quality score (0-1).
        
        Score = 1.0 - (error_weight * error_count + warning_weight * warning_count)
        """
        error_count = sum(1 for r in self.results if r.severity == "error" and not r.passed)
        warning_count = sum(1 for r in self.results if r.severity == "warning" and not r.passed)
        
        error_weight = 0.1  # Each error reduces score by 10%
        warning_weight = 0.03  # Each warning reduces score by 3%
        
        score = 1.0 - (error_count * error_weight + warning_count * warning_weight)
        return max(0, min(1, score))  # Clamp to [0, 1]
    
    def get_summary(self) -> Dict:
        """Get summary of validation results."""
        return {
            'total_checks': len(self.results),
            'passed': sum(1 for r in self.results if r.passed),
            'failed': sum(1 for r in self.results if not r.passed),
            'errors': sum(1 for r in self.results if r.severity == "error" and not r.passed),
            'warnings': sum(1 for r in self.results if r.severity == "warning" and not r.passed),
        }
