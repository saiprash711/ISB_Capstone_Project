"""
Data Transformation Module
Transforms cleaned transaction data into canonical SKU × BRANCH × WEEK data mart.
"""
import pandas as pd
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transform data from transaction level to canonical time-series format."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize transformer with cleaned dataset.
        
        Args:
            df: Cleaned dataframe (after cleaning.py)
        """
        self.df = df.copy()
        self.transformation_log = []
    
    def transform_to_data_mart(self) -> Tuple[pd.DataFrame, list]:
        """
        Transform transaction data to SKU × BRANCH × WEEK data mart.
        
        Returns:
            Tuple of (data_mart_df, transformation_log)
            
        Notes:
            - Output grain: One row per (sku, branch, week)
            - Aggregates quantities and tonnage
            - Retains business dimensions (segment, star_rating, material_group)
        """
        self._log("Starting data transformation to SKU × BRANCH × WEEK data mart")
        
        # Step 1: Parse and normalize dates
        self._parse_dates()
        
        # Step 2: Extract week identifiers
        self._extract_week_identifiers()
        
        # Step 3: Create data mart through aggregation
        self._create_data_mart()
        
        # Step 4: Ensure contiguous weekly series (fill missing weeks with zero demand)
        self._fill_missing_weeks()
        
        # Step 5: Calculate derived metrics
        self._calculate_derived_metrics()
        
        # Step 6: Organize columns
        self._organize_columns()
        
        self._log("Data transformation complete")
        return self.df, self.transformation_log
    
    def _parse_dates(self):
        """Parse and validate dates."""
        if 'date' not in self.df.columns:
            self._log("WARNING: 'date' column not found")
            return
        
        # Ensure datetime type
        if self.df['date'].dtype != 'datetime64[ns]':
            try:
                self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
                self._log(f"Parsed {self.df['date'].notna().sum()} valid dates")
            except Exception as e:
                self._log(f"ERROR parsing dates: {str(e)}")
                return
        
        # Remove rows with invalid dates
        invalid_date_count = self.df['date'].isnull().sum()
        if invalid_date_count > 0:
            self.df = self.df[self.df['date'].notna()]
            self._log(f"Removed {invalid_date_count} rows with invalid dates")
    
    def _extract_week_identifiers(self):
        """Extract calendar identifiers from dates."""
        if 'date' not in self.df.columns or self.df['date'].dtype != 'datetime64[ns]':
            self._log("WARNING: Cannot extract week identifiers - 'date' column invalid")
            return
        
        # Extract calendar components
        self.df['year_actual'] = self.df['date'].dt.isocalendar().year
        self.df['week_actual'] = self.df['date'].dt.isocalendar().week
        self.df['month_actual'] = self.df['date'].dt.month
        self.df['quarter_actual'] = self.df['date'].dt.quarter
        self.df['day_of_week'] = self.df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
        
        # Create ISO week string (YYYY-W##)
        self.df['iso_week'] = self.df['date'].dt.strftime('%Y-W%V')
        
        self._log(f"Extracted week identifiers covering {self.df['iso_week'].nunique()} unique weeks")
    
    def _create_data_mart(self):
        """Create canonical SKU × BRANCH × WEEK data mart through aggregation."""
        
        if 'sku' not in self.df.columns or 'branch' not in self.df.columns or 'iso_week' not in self.df.columns:
            self._log("ERROR: Cannot create data mart - required columns missing")
            return
        
        # Group by SKU, Branch, Week and aggregate
        groupby_cols = ['iso_week', 'sku', 'branch']
        agg_dict = {
            'quantity_odu': 'sum',
            'quantity_idu': 'sum',
            'tonnage': 'sum',
        }
        
        # Add date (max = latest date in week)
        if 'date' in self.df.columns:
            agg_dict['date'] = 'max'
        
        # Add calendar components (first = all same within a week)
        for col in ['year_actual', 'week_actual', 'month_actual', 'quarter_actual']:
            if col in self.df.columns:
                agg_dict[col] = 'first'
        
        # Add categorical columns (take first value)
        for col in ['segment', 'star_rating', 'material_group', 'sbu']:
            if col in self.df.columns:
                agg_dict[col] = 'first'
        
        # Perform aggregation
        try:
            data_mart = self.df.groupby(groupby_cols, as_index=False, observed=True).agg(agg_dict)
        except Exception as e:
            self._log(f"ERROR in groupby aggregation: {str(e)}")
            # Fall back to simpler aggregation
            data_mart = self.df.groupby(groupby_cols, as_index=False).agg({
                'quantity_odu': 'sum',
                'quantity_idu': 'sum',
                'tonnage': 'sum',
            })
        
        # Create demand metric (combine ODU and IDU)
        if 'quantity_odu' in data_mart.columns and 'quantity_idu' in data_mart.columns:
            data_mart['total_demand'] = data_mart['quantity_odu'] + data_mart['quantity_idu']
        elif 'quantity_odu' in data_mart.columns:
            data_mart['total_demand'] = data_mart['quantity_odu']
        else:
            data_mart['total_demand'] = 0
            
        data_mart['total_demand'] = np.maximum(0.0, data_mart['total_demand'].fillna(0.0))
        
        self.df = data_mart
        
        initial_rows = len(self.df)
        self._log(
            f"Created data mart: {initial_rows} rows × {len(self.df.columns)} columns\n"
            f"  Grain: SKU × BRANCH × WEEK\n"
            f"  Unique SKUs: {self.df['sku'].nunique()}\n"
            f"  Unique Branches: {self.df['branch'].nunique()}\n"
            f"  Unique Weeks: {self.df['iso_week'].nunique()}"
        )
    
    def _fill_missing_weeks(self):
        """
        Ensures contiguous weekly observations per (sku, branch) between its
        first and last recorded transaction dates, filling missing weeks with 0 demand.
        """
        if 'sku' not in self.df.columns or 'branch' not in self.df.columns or 'date' not in self.df.columns:
            return
            
        try:
            self.df['date'] = pd.to_datetime(self.df['date'])
            reindexed_groups = []
            
            for (sku, branch), grp in self.df.groupby(['sku', 'branch'], observed=True):
                grp = grp.sort_values('date').drop_duplicates(subset=['iso_week'])
                min_date = grp['date'].min()
                max_date = grp['date'].max()
                
                if pd.isna(min_date) or pd.isna(max_date) or min_date == max_date:
                    reindexed_groups.append(grp)
                    continue
                
                # Generate contiguous weekly dates anchored on Monday (ISO week)
                start_mon = min_date - pd.to_timedelta(min_date.weekday(), unit='D')
                full_dates = pd.date_range(start=start_mon, end=max_date, freq='W-MON')
                if len(full_dates) <= len(grp):
                    reindexed_groups.append(grp)
                    continue
                
                skeleton = pd.DataFrame({'date': full_dates})
                skeleton['iso_week'] = skeleton['date'].dt.strftime('%Y-W%V')
                skeleton['year_actual'] = skeleton['date'].dt.isocalendar().year
                skeleton['week_actual'] = skeleton['date'].dt.isocalendar().week
                skeleton['month_actual'] = skeleton['date'].dt.month
                skeleton['quarter_actual'] = skeleton['date'].dt.quarter
                skeleton['sku'] = sku
                skeleton['branch'] = branch
                
                cols_to_drop = ['date', 'year_actual', 'week_actual', 'month_actual', 'quarter_actual']
                grp_clean = grp.drop(columns=[c for c in cols_to_drop if c in grp.columns], errors='ignore')
                merged = pd.merge(skeleton, grp_clean, on=['sku', 'branch', 'iso_week'], how='left')
                
                # Numeric fills
                for num_col in ['quantity_odu', 'quantity_idu', 'total_demand', 'tonnage']:
                    if num_col in merged.columns:
                        merged[num_col] = merged[num_col].fillna(0.0)
                        
                # Metadata fills
                for cat_col in ['segment', 'star_rating', 'material_group', 'sbu']:
                    if cat_col in merged.columns:
                        merged[cat_col] = merged[cat_col].ffill().bfill()
                        
                reindexed_groups.append(merged)
                
            if reindexed_groups:
                self.df = pd.concat(reindexed_groups, ignore_index=True)
                self._log(f"Contiguous weekly regularization complete: {len(self.df)} rows")
        except Exception as e:
            self._log(f"WARNING: Weekly regularization skipped due to error: {str(e)}")
    
    def _calculate_derived_metrics(self):
        """Calculate derived metrics from aggregated data."""
        
        # For each SKU/Branch combination, calculate time-series metrics
        # (This is just a placeholder; detailed calculations happen in features.py)
        
        # Count non-zero demands
        if 'total_demand' in self.df.columns:
            self.df['demand_nonzero'] = (self.df['total_demand'] > 0).astype(int)
        
        self._log("Calculated derived metrics")
    
    def _organize_columns(self):
        """Organize columns in logical order."""
        
        # Desired column order
        priority_cols = [
            'iso_week', 'date', 'year_actual', 'week_actual', 'month_actual', 'quarter_actual',
            'sku', 'branch', 'segment', 'star_rating', 'material_group', 'sbu',
            'quantity_odu', 'quantity_idu', 'total_demand', 'tonnage'
        ]
        
        # Only include columns that exist
        existing_priority = [col for col in priority_cols if col in self.df.columns]
        
        # Add any remaining columns
        other_cols = [col for col in self.df.columns if col not in existing_priority]
        
        # Reorder
        self.df = self.df[existing_priority + other_cols]
        
        self._log("Organized columns")
    
    def get_summary(self) -> dict:
        """Get transformation summary."""
        return {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'grain': 'SKU × BRANCH × WEEK',
            'unique_skus': self.df['sku'].nunique() if 'sku' in self.df.columns else 0,
            'unique_branches': self.df['branch'].nunique() if 'branch' in self.df.columns else 0,
            'unique_weeks': self.df['iso_week'].nunique() if 'iso_week' in self.df.columns else 0,
            'date_range': f"{self.df['date'].min()} to {self.df['date'].max()}" if 'date' in self.df.columns else "N/A",
            'operations': self.transformation_log
        }
    
    def _log(self, message: str):
        """Log a transformation operation."""
        self.transformation_log.append(message)
        logger.info(message)
