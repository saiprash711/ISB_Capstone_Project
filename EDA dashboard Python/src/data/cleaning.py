"""
Data Cleaning Module
Handles data deduplication, standardization, and transformations.
"""
import pandas as pd
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Data cleaning and standardization operations."""
    
    # Valid branch codes (South Region)
    VALID_BRANCHES = {
        'BLR': 'Bangalore',
        'MAA': 'Chennai',
        'COK': 'Cochin',
        'SBD': 'Secunderabad',
        'SBD1': 'Vijayawada'
    }
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize cleaner with dataset.
        
        Args:
            df: Input dataframe to clean
        """
        self.df = df.copy()
        self.cleaning_log = []
    
    def clean_all(self) -> Tuple[pd.DataFrame, list]:
        """
        Execute full cleaning pipeline.
        
        Returns:
            Tuple of (cleaned_df, cleaning_log)
        """
        self._log("Starting data cleaning pipeline")
        
        # Step 1: Deduplication
        self._remove_duplicates()
        
        # Step 2: Column standardization
        self._standardize_columns()
        
        # Step 3: Value standardization
        self._standardize_values()
        
        # Step 4: Type conversion
        self._convert_types()
        
        # Step 5: Handle negative demands
        self._handle_negative_demands()
        
        # Step 6: Remove known duplicates
        self._remove_duplicate_columns()
        
        self._log("Cleaning pipeline complete")
        return self.df, self.cleaning_log
    
    def _remove_duplicates(self):
        """Remove duplicate records."""
        initial_rows = len(self.df)
        
        # Remove complete row duplicates
        self.df = self.df.drop_duplicates()
        
        removed = initial_rows - len(self.df)
        if removed > 0:
            self._log(f"Removed {removed} complete row duplicates")
    
    def _remove_duplicate_columns(self):
        """Remove duplicate/redundant columns identified in audit."""
        # Columns to remove (duplicates or unnecessary)
        cols_to_drop = [
            'Star Rating.1',        # Duplicate of Star Rating
            'SALES OFFICE CODE.1',  # Duplicate of SALES OFFICE CODE
            'Material.1',           # Duplicate of Material
            'Tonnage.1',            # Duplicate of Tonnage
            'Billing Doc.',         # Transaction ID, not needed for time-series
            'Item',                 # Item number, not needed
            'Stor. Location',       # Storage location, not needed
            'Customer',             # Customer name, not needed for aggregation
            'Dealer Name',          # Dealer name, could use but not essential
            'EXT MAT GROUP',        # Duplicate info (we have MatGroup3)
        ]
        
        # Only drop columns that exist
        cols_to_drop = [col for col in cols_to_drop if col in self.df.columns]
        
        if cols_to_drop:
            self.df = self.df.drop(columns=cols_to_drop)
            self._log(f"Removed {len(cols_to_drop)} duplicate/unnecessary columns: {cols_to_drop}")
    
    def _standardize_columns(self):
        """Standardize column names to lowercase with underscores."""
        original_cols = self.df.columns.tolist()
        
        new_cols = {}
        for col in original_cols:
            # Skip if already renamed
            if col in new_cols.values():
                continue
            
            # Create standardized name
            standardized = col.lower().strip().replace(' ', '_').replace('.', '')
            
            # Handle special cases
            if col == 'Material':
                standardized = 'sku'
            elif col == 'SALES OFFICE CODE':
                standardized = 'branch'
            elif col == 'Billing Date':
                standardized = 'date'
            elif col == 'Billing Quantity ODU':
                standardized = 'quantity_odu'
            elif col == 'Billing Quantity IDU':
                standardized = 'quantity_idu'
            elif col == 'MatGroup3':
                standardized = 'material_group'
            elif col == 'SBU':
                standardized = 'sbu'
            elif col == 'Star Rating':
                standardized = 'star_rating'
            elif col == 'Segment':
                standardized = 'segment'
            elif col == 'Tonnage':
                standardized = 'tonnage'
            elif col == 'Year':
                standardized = 'year'
            elif col == 'Month':
                standardized = 'month'
            elif col == 'Week':
                standardized = 'week'
            
            new_cols[col] = standardized
        
        # Only rename if there were changes
        if new_cols:
            self.df.rename(columns=new_cols, inplace=True)
            self._log(f"Standardized {len(new_cols)} column names")
    
    def _standardize_values(self):
        """Standardize categorical values."""
        # Branch standardization
        if 'branch' in self.df.columns:
            # Map to valid branches
            branch_map = {}
            for code, name in self.VALID_BRANCHES.items():
                branch_map[code] = code
                branch_map[name] = code
            
            # Handle any variations
            self.df['branch'] = self.df['branch'].str.upper().str.strip()
            invalid_branches = self.df[~self.df['branch'].isin(self.VALID_BRANCHES.keys())]['branch'].unique()
            
            if len(invalid_branches) > 0:
                self._log(f"Found unknown branch codes: {invalid_branches.tolist()}")
        
        # Segment standardization
        if 'segment' in self.df.columns:
            self.df['segment'] = self.df['segment'].str.strip().replace({
                'Non Inv': 'Non-inverter',
                'Non Inv.': 'Non-inverter',
                'Non-Inv': 'Non-inverter',
                'Non-Inverter': 'Non-inverter',
                'Non Inverter': 'Non-inverter',
                'non-inverter': 'Non-inverter',
                'Inv': 'Inverter',
                'inverter': 'Inverter'
            })
        
        # Star rating standardization
        if 'star_rating' in self.df.columns:
            self.df['star_rating'] = self.df['star_rating'].str.upper().str.strip()
        
        # Material group standardization
        if 'material_group' in self.df.columns:
            self.df['material_group'] = self.df['material_group'].str.upper().str.strip()
        
        self._log("Standardized categorical values")
    
    def _convert_types(self):
        """Convert columns to appropriate data types."""
        conversions = {}
        
        # Convert quantities and tonnage to numeric
        for col in ['quantity_odu', 'quantity_idu', 'tonnage']:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                conversions[col] = 'numeric'
        
        # Convert SKU to string
        if 'sku' in self.df.columns:
            self.df['sku'] = self.df['sku'].astype(str)
            conversions['sku'] = 'string'
        
        # Convert branch to category
        if 'branch' in self.df.columns:
            self.df['branch'] = self.df['branch'].astype('category')
            conversions['branch'] = 'category'
        
        # Parse dates
        if 'date' in self.df.columns:
            # Try parsing with different formats
            if self.df['date'].dtype == 'object':
                parsed = pd.to_datetime(self.df['date'], format='%d/%m/%Y', errors='coerce')
                if parsed.isna().mean() > 0.5:
                    parsed = pd.to_datetime(self.df['date'], errors='coerce')
                self.df['date'] = parsed
            conversions['date'] = 'datetime'
        
        # Convert year to int
        if 'year' in self.df.columns:
            self.df['year'] = pd.to_numeric(self.df['year'], errors='coerce').astype('Int64')
            conversions['year'] = 'int'
        
        if conversions:
            self._log(f"Type conversions: {conversions}")
            
    def _handle_negative_demands(self):
        """Audit and quarantine records with negative demands or quantities (returns/cancellations)."""
        cols_to_check = [c for c in ['quantity_odu', 'quantity_idu'] if c in self.df.columns]
        if cols_to_check:
            neg_mask = (self.df[cols_to_check] < 0).any(axis=1)
            neg_count = int(neg_mask.sum())
            if neg_count > 0:
                rejected = self.df[neg_mask].copy()
                rejected['rejection_reason'] = 'negative_quantity_reversal_or_cancellation'
                if not hasattr(self, 'rejection_audit') or self.rejection_audit is None:
                    self.rejection_audit = rejected
                else:
                    self.rejection_audit = pd.concat([self.rejection_audit, rejected], ignore_index=True)
                self.df = self.df[~neg_mask].copy()
                self._log(f"Quarantined {neg_count} records with negative demand into rejection_audit (returns/cancellations)")
                
    def handle_missing_tonnage(self) -> int:
        """
        Handle missing tonnage values.
        
        Strategy: If tonnage is missing but quantity exists, estimate based on quantity.
        This is a data imputation step that should be documented.
        
        Returns:
            Number of rows imputed
        """
        if 'tonnage' not in self.df.columns or 'quantity_odu' not in self.df.columns:
            return 0
        
        # Find rows where tonnage is missing but quantity exists
        missing_mask = self.df['tonnage'].isnull() & (self.df['quantity_odu'] > 0)
        missing_count = missing_mask.sum()
        
        if missing_count > 0:
            # Estimate: assume average tonnage per unit from available data
            # This is a rough heuristic; actual data quality should be verified
            avg_tonnage_per_unit = (self.df['tonnage'] / self.df['quantity_odu']).replace([np.inf, -np.inf], np.nan).mean()
            
            if not pd.isna(avg_tonnage_per_unit):
                self.df.loc[missing_mask, 'tonnage'] = (
                    self.df.loc[missing_mask, 'quantity_odu'] * avg_tonnage_per_unit
                )
                self._log(
                    f"Imputed {missing_count} missing tonnage values using average {avg_tonnage_per_unit:.2f} tons/unit"
                )
            else:
                self._log(f"Could not impute {missing_count} missing tonnage values (no reference data)")
        
        return missing_count
    
    def _log(self, message: str):
        """Log a cleaning operation."""
        self.cleaning_log.append(message)
        logger.info(message)
    
    def get_summary(self) -> dict:
        """Get cleaning summary."""
        return {
            'rows_final': len(self.df),
            'columns_final': len(self.df.columns),
            'column_names': self.df.columns.tolist(),
            'operations': self.cleaning_log
        }
