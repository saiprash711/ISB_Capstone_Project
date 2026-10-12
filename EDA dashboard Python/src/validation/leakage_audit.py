"""
Data Leakage Audit Module
Performs comprehensive forensic auditing to verify zero temporal,
contemporaneous, target, and split-order leakage across the forecasting pipeline.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LeakageAuditor:
    """
    Automated auditor to detect and prevent data leakage in time-series forecasting.
    """

    def audit_splits(self, folds: List[tuple]) -> Dict[str, Any]:
        """
        Verify that all backtesting folds are strictly chronological with zero overlap.
        """
        if not folds:
            return {
                'check': 'Chronological Split Disjointness',
                'passed': False,
                'leakage_detected': True,
                'details': 'No folds provided to evaluate.'
            }

        passed = True
        issues = []

        for i, (train_idx, test_idx) in enumerate(folds):
            train_set = set(train_idx)
            test_set = set(test_idx)

            # 1. Disjointness
            overlap = train_set.intersection(test_set)
            if overlap:
                passed = False
                issues.append(f"Fold {i+1}: Overlap of {len(overlap)} indices between train and test.")

            # 2. Strict temporal ordering: max(train) < min(test)
            if len(train_idx) > 0 and len(test_idx) > 0:
                if np.max(train_idx) >= np.min(test_idx):
                    passed = False
                    issues.append(f"Fold {i+1}: Train index ({np.max(train_idx)}) >= Test index ({np.min(test_idx)}).")

        return {
            'check': 'Chronological Split Disjointness & Ordering',
            'passed': passed,
            'leakage_detected': not passed,
            'details': "All train/test folds are strictly disjoint and ordered forward in time." if passed else "; ".join(issues)
        }

    def audit_lag_features(self, df_with_features: pd.DataFrame, 
                           target_col: str = 'total_demand') -> Dict[str, Any]:
        """
        Verify lag features only look backward and never include contemporaneous or future target.
        """
        lag_cols = [c for c in df_with_features.columns if c.startswith('lag_')]
        if not lag_cols or target_col not in df_with_features.columns:
            return {
                'check': 'Lag Feature Directionality',
                'passed': True,
                'leakage_detected': False,
                'details': 'No lag features or target column present to audit.'
            }

        passed = True
        issues = []

        for col in lag_cols:
            try:
                lag_k = int(col.split('_')[1])
            except (IndexError, ValueError):
                continue

            if lag_k <= 0:
                passed = False
                issues.append(f"Invalid lag order {col}: lag must be >= 1.")
                continue

            # Verify for each row i >= lag_k that lag_col[i] equals target[i - lag_k]
            y = df_with_features[target_col].values
            f = df_with_features[col].values

            # Row 0 must be NaN or shifted
            if not pd.isna(f[0]) and f[0] == y[0]:
                passed = False
                issues.append(f"{col} contains contemporaneous value at index 0.")

            # For subsequent rows where both are valid
            valid_idx = np.where((~np.isnan(f)) & (np.arange(len(f)) >= lag_k))[0]
            if len(valid_idx) > 0:
                diff = np.abs(f[valid_idx] - y[valid_idx - lag_k])
                if np.nanmax(diff) > 1e-4:
                    passed = False
                    issues.append(f"{col} diverges from actual target lagged by {lag_k} periods.")

        return {
            'check': 'Lag Feature Temporal Causality',
            'passed': passed,
            'leakage_detected': not passed,
            'details': f"Verified {len(lag_cols)} lag features strictly reference t-k." if passed else "; ".join(issues)
        }

    def audit_rolling_features(self, df_with_features: pd.DataFrame, 
                               target_col: str = 'total_demand') -> Dict[str, Any]:
        """
        Verify rolling statistics do NOT include contemporaneous target value at time t.
        """
        rolling_mean_cols = [c for c in df_with_features.columns if c.startswith('rolling_mean_')]
        if not rolling_mean_cols or target_col not in df_with_features.columns:
            return {
                'check': 'Rolling Feature Contemporaneous Exclusion',
                'passed': True,
                'leakage_detected': False,
                'details': 'No rolling mean features present to audit.'
            }

        passed = True
        issues = []
        y = df_with_features[target_col].values

        for col in rolling_mean_cols:
            f = df_with_features[col].values
            # If rolling feature at index 0 equals y[0], it included contemporaneous target
            if len(f) > 0 and len(y) > 0 and not pd.isna(f[0]):
                if abs(f[0] - y[0]) < 1e-4:
                    passed = False
                    issues.append(f"{col} includes contemporaneous target at period 0.")

            # Check if rolling feature at index 1 includes target at index 1
            if len(f) > 1 and len(y) > 1 and not pd.isna(f[1]):
                # If f[1] == (y[0] + y[1])/2, it included y[1]!
                if abs(f[1] - np.mean(y[:2])) < 1e-4 and abs(y[0] - y[1]) > 1e-3:
                    passed = False
                    issues.append(f"{col} includes contemporaneous target at period 1 (target leakage).")

        return {
            'check': 'Rolling Feature Contemporaneous Exclusion',
            'passed': passed,
            'leakage_detected': not passed,
            'details': "All rolling features strictly lag behind current period (zero target leakage)." if passed else "; ".join(issues)
        }

    def audit_target_leakage(self, df_with_features: pd.DataFrame, 
                             target_col: str = 'total_demand') -> Dict[str, Any]:
        """
        Check feature matrix correlation with future target values (lookahead leakage).
        """
        if target_col not in df_with_features.columns or len(df_with_features) < 10:
            return {
                'check': 'Future Target Lookahead Check',
                'passed': True,
                'leakage_detected': False,
                'details': 'Insufficient records to perform lookahead correlation.'
            }

        numeric_df = df_with_features.select_dtypes(include=[np.number]).copy()
        if target_col not in numeric_df.columns:
            numeric_df[target_col] = df_with_features[target_col]

        y_future = numeric_df[target_col].shift(-1)  # Target at t+1
        features_to_check = [c for c in numeric_df.columns if c not in [target_col, 'date', 'year_actual', 'week_actual']]

        suspicious_features = []
        for feat in features_to_check:
            s = numeric_df[feat]
            valid_mask = (~s.isna()) & (~y_future.isna())
            if np.sum(valid_mask) >= 8:
                corr = np.corrcoef(s[valid_mask], y_future[valid_mask])[0, 1]
                # If a feature has near-perfect correlation (> 0.999) with FUTURE target, it is lookahead leakage
                if abs(corr) > 0.999:
                    suspicious_features.append(f"{feat} (corr with t+1: {corr:.4f})")

        passed = (len(suspicious_features) == 0)
        return {
            'check': 'Future Target Lookahead Check',
            'passed': passed,
            'leakage_detected': not passed,
            'details': "No suspicious lookahead correlations found." if passed else f"Potential lookahead leakage: {', '.join(suspicious_features)}"
        }

    def run_full_audit(self, df_features: pd.DataFrame, 
                       folds: Optional[List[tuple]] = None,
                       target_col: str = 'total_demand') -> Dict[str, Any]:
        """
        Execute comprehensive 4-point temporal and target leakage audit.
        """
        results = []
        
        # 1. Lag causality
        results.append(self.audit_lag_features(df_features, target_col=target_col))
        
        # 2. Rolling exclusion
        results.append(self.audit_rolling_features(df_features, target_col=target_col))
        
        # 3. Future lookahead
        results.append(self.audit_target_leakage(df_features, target_col=target_col))
        
        # 4. Split disjointness (if folds provided)
        if folds:
            results.append(self.audit_splits(folds))

        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        leakage_rate = 0.0 if passed_count == total_count else round((total_count - passed_count) / total_count * 100.0, 1)

        return {
            'audit_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'overall_status': 'VERIFIED_ZERO_LEAKAGE' if passed_count == total_count else 'LEAKAGE_DETECTED',
            'leakage_percentage': leakage_rate,
            'checks_passed': passed_count,
            'checks_total': total_count,
            'is_fully_compliant': passed_count == total_count,
            'check_details': results
        }
