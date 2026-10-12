"""
Feature Engineering Module
Generates features for machine learning models and statistical analysis.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Engineer features from time series data for forecasting."""
    
    def __init__(self, config: Dict = None):
        """Initialize feature engineer with optional config."""
        self.config = config or {}
        self.lag_periods = self.config.get('lags', [1, 2, 3, 4, 8, 12, 26, 52])
        self.rolling_windows = self.config.get('rolling_windows', [4, 8, 12])
        self.seasonal_period = self.config.get('seasonal_period', 52)
    
    def engineer_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Engineer all features for time series forecasting.
        
        Args:
            df: DataFrame with time series data (must have 'demand' or 'total_demand' column)
        
        Returns:
            DataFrame with added features, list of feature names
        """
        if df.empty:
            return df, []
        
        df = df.copy()
        feature_cols = []
        
        # Calendar features
        calendar_feats = self._add_calendar_features(df)
        feature_cols.extend(calendar_feats)
        
        # Lag features
        lag_feats = self._add_lag_features(df)
        feature_cols.extend(lag_feats)
        
        # Rolling features
        rolling_feats = self._add_rolling_features(df)
        feature_cols.extend(rolling_feats)
        
        # Trend features
        trend_feats = self._add_trend_features(df)
        feature_cols.extend(trend_feats)
        
        # Seasonal features
        seasonal_feats = self._add_seasonal_features(df)
        feature_cols.extend(seasonal_feats)
        
        logger.info(f"Engineered {len(feature_cols)} features")
        return df, feature_cols
    
    def _add_calendar_features(self, df: pd.DataFrame) -> List[str]:
        """Add calendar-based features."""
        features = []
        
        if 'date' not in df.columns:
            return features
        
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Already have these in data mart, but ensure they exist
        if 'week_of_year' not in df.columns:
            df['week_of_year'] = df['date'].dt.isocalendar().week
            features.append('week_of_year')
        
        if 'month_of_year' not in df.columns:
            df['month_of_year'] = df['date'].dt.month
            features.append('month_of_year')
        
        if 'quarter' not in df.columns:
            df['quarter'] = df['date'].dt.quarter
            features.append('quarter')
        
        if 'day_of_week' not in df.columns:
            df['day_of_week'] = df['date'].dt.dayofweek
            features.append('day_of_week')
        
        # Cyclical encoding for week/month
        if 'week_sin' not in df.columns:
            df['week_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
            df['week_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)
            features.extend(['week_sin', 'week_cos'])
        
        if 'month_sin' not in df.columns:
            df['month_sin'] = np.sin(2 * np.pi * df['month_of_year'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month_of_year'] / 12)
            features.extend(['month_sin', 'month_cos'])
        
        return features
    
    def _add_lag_features(self, df: pd.DataFrame) -> List[str]:
        """Add lagged demand features."""
        features = []
        demand_col = 'total_demand' if 'total_demand' in df.columns else 'demand'
        
        if demand_col not in df.columns:
            return features
        
        for lag in self.lag_periods:
            col_name = f'lag_{lag}'
            if col_name not in df.columns:
                # Group by SKU and branch before lagging
                if 'sku' in df.columns and 'branch' in df.columns:
                    df[col_name] = df.groupby(['sku', 'branch'], observed=True)[demand_col].shift(lag)
                else:
                    df[col_name] = df[demand_col].shift(lag)
                features.append(col_name)
        
        return features
    
    def _add_rolling_features(self, df: pd.DataFrame) -> List[str]:
        """Add rolling window features strictly shifted to prevent contemporaneous target leakage."""
        features = []
        demand_col = 'total_demand' if 'total_demand' in df.columns else 'demand'
        
        if demand_col not in df.columns:
            return features
        
        for window in self.rolling_windows:
            # Group by SKU/branch for rolling operations with strict 1-period shift
            if 'sku' in df.columns and 'branch' in df.columns:
                grouped = df.groupby(['sku', 'branch'], observed=True)
                
                # Mean (strictly lagged)
                col_mean = f'rolling_mean_{window}'
                if col_mean not in df.columns:
                    df[col_mean] = grouped[demand_col].transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
                    features.append(col_mean)
                
                # Std (strictly lagged)
                col_std = f'rolling_std_{window}'
                if col_std not in df.columns:
                    df[col_std] = grouped[demand_col].transform(lambda x: x.shift(1).rolling(window, min_periods=1).std())
                    features.append(col_std)
                
                # Min/Max (strictly lagged)
                col_min = f'rolling_min_{window}'
                if col_min not in df.columns:
                    df[col_min] = grouped[demand_col].transform(lambda x: x.shift(1).rolling(window, min_periods=1).min())
                    features.append(col_min)
                
                col_max = f'rolling_max_{window}'
                if col_max not in df.columns:
                    df[col_max] = grouped[demand_col].transform(lambda x: x.shift(1).rolling(window, min_periods=1).max())
                    features.append(col_max)
            else:
                # Fallback without grouping with strict 1-period shift
                df[f'rolling_mean_{window}'] = df[demand_col].shift(1).rolling(window, min_periods=1).mean()
                df[f'rolling_std_{window}'] = df[demand_col].shift(1).rolling(window, min_periods=1).std()
                features.extend([f'rolling_mean_{window}', f'rolling_std_{window}'])
        
        return features
    
    def _add_trend_features(self, df: pd.DataFrame) -> List[str]:
        """Add trend-based features strictly shifted to avoid target leakage."""
        features = []
        demand_col = 'total_demand' if 'total_demand' in df.columns else 'demand'
        
        if demand_col not in df.columns:
            return features
        
        # Week-over-week growth (lagged by 1)
        col_wow = 'wow_growth'
        if col_wow not in df.columns:
            if 'sku' in df.columns and 'branch' in df.columns:
                df[col_wow] = df.groupby(['sku', 'branch'], observed=True)[demand_col].transform(
                    lambda x: x.shift(1).pct_change()
                )
            else:
                df[col_wow] = df[demand_col].shift(1).pct_change()
            features.append(col_wow)
        
        # 4-week growth (lagged by 1)
        col_4w = 'growth_4w'
        if col_4w not in df.columns:
            if 'sku' in df.columns and 'branch' in df.columns:
                df[col_4w] = df.groupby(['sku', 'branch'], observed=True)[demand_col].transform(
                    lambda x: x.shift(1).pct_change(periods=4)
                )
            else:
                df[col_4w] = df[demand_col].pct_change(periods=4)
            features.append(col_4w)
        
        # 12-week growth
        col_12w = 'growth_12w'
        if col_12w not in df.columns:
            if 'sku' in df.columns and 'branch' in df.columns:
                df[col_12w] = df.groupby(['sku', 'branch'], observed=True)[demand_col].pct_change(periods=12)
            else:
                df[col_12w] = df[demand_col].pct_change(periods=12)
            features.append(col_12w)
        
        return features
    
    def _add_seasonal_features(self, df: pd.DataFrame) -> List[str]:
        """Add seasonal features."""
        features = []
        demand_col = 'total_demand' if 'total_demand' in df.columns else 'demand'
        
        if demand_col not in df.columns:
            return features
        
        # Seasonal (same week last year)
        col_seasonal = 'seasonal_lag'
        if col_seasonal not in df.columns:
            if 'sku' in df.columns and 'branch' in df.columns:
                df[col_seasonal] = df.groupby(['sku', 'branch'], observed=True)[demand_col].shift(self.seasonal_period)
            else:
                df[col_seasonal] = df[demand_col].shift(self.seasonal_period)
            features.append(col_seasonal)
        
        return features
    
    def get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Extract feature importance from trained model."""
        importance_dict = {}
        
        try:
            if hasattr(model, 'feature_importances_'):
                for name, importance in zip(feature_names, model.feature_importances_):
                    importance_dict[name] = importance
            elif hasattr(model, 'coef_'):
                for name, coef in zip(feature_names, model.coef_):
                    importance_dict[name] = abs(coef)
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
        
        return importance_dict

    def generate_step_features(self, history_series: pd.Series, target_date: Optional[pd.Timestamp] = None) -> pd.Series:
        """
        Generate feature row for step t+h given autoregressive history up to t+h-1 and target date.
        """
        feats = {}
        if target_date is not None:
            t_dt = pd.to_datetime(target_date)
            woy = int(t_dt.isocalendar().week)
            moy = int(t_dt.month)
            feats['week_of_year'] = woy
            feats['month_of_year'] = moy
            feats['quarter'] = int(t_dt.quarter)
            feats['day_of_week'] = int(t_dt.dayofweek)
            feats['week_sin'] = float(np.sin(2 * np.pi * woy / 52))
            feats['week_cos'] = float(np.cos(2 * np.pi * woy / 52))
            feats['month_sin'] = float(np.sin(2 * np.pi * moy / 12))
            feats['month_cos'] = float(np.cos(2 * np.pi * moy / 12))
        else:
            feats['week_of_year'] = 1
            feats['month_of_year'] = 1
            feats['quarter'] = 1
            feats['day_of_week'] = 0
            feats['week_sin'] = 0.0
            feats['week_cos'] = 1.0
            feats['month_sin'] = 0.0
            feats['month_cos'] = 1.0

        n = len(history_series)
        # Lag features
        for lag in self.lag_periods:
            feats[f'lag_{lag}'] = float(history_series.iloc[-lag]) if n >= lag else 0.0

        # Rolling window statistics
        for window in self.rolling_windows:
            w_slice = history_series.iloc[-window:] if n >= window else history_series
            feats[f'rolling_mean_{window}'] = float(w_slice.mean()) if len(w_slice) > 0 else 0.0
            feats[f'rolling_std_{window}'] = float(w_slice.std()) if len(w_slice) > 1 else 0.0
            feats[f'rolling_min_{window}'] = float(w_slice.min()) if len(w_slice) > 0 else 0.0
            feats[f'rolling_max_{window}'] = float(w_slice.max()) if len(w_slice) > 0 else 0.0

        # Growth metrics
        if n >= 2:
            p1 = float(history_series.iloc[-1])
            p2 = float(history_series.iloc[-2])
            feats['wow_growth'] = (p1 - p2) / (p2 + 1e-5)
        else:
            feats['wow_growth'] = 0.0

        if n >= 5:
            feats['growth_4w'] = (float(history_series.iloc[-1]) - float(history_series.iloc[-5])) / (float(history_series.iloc[-5]) + 1e-5)
        else:
            feats['growth_4w'] = 0.0

        if n >= 13:
            feats['growth_12w'] = (float(history_series.iloc[-1]) - float(history_series.iloc[-13])) / (float(history_series.iloc[-13]) + 1e-5)
        else:
            feats['growth_12w'] = 0.0

        feats['seasonal_lag'] = float(history_series.iloc[-self.seasonal_period]) if n >= self.seasonal_period else 0.0
        return pd.Series(feats)

    def predict_recursive(self, model: Any, history_series: pd.Series, horizon: int,
                          feature_cols: List[str], base_date: Optional[Any] = None) -> np.ndarray:
        """
        True multi-step recursive walk-forward prediction.
        At each forecast step h=1..H:
          1. Dynamically constructs features at t+h using autoregressive history.
          2. Predicts step demand y_hat_{t+h}.
          3. Recursively appends y_hat_{t+h} to history for subsequent lag/rolling updates.
        """
        sim_history = history_series.copy().astype(float)
        predictions = []
        cur_date = pd.to_datetime(base_date) if base_date is not None else None

        for step in range(1, horizon + 1):
            next_date = (cur_date + pd.Timedelta(weeks=step)) if cur_date is not None else None
            step_feats = self.generate_step_features(sim_history, target_date=next_date)
            
            # Align features with training columns
            x_row = []
            for col in feature_cols:
                x_row.append(step_feats.get(col, 0.0))
                
            x_mat = np.array([x_row], dtype=np.float32)
            x_mat[~np.isfinite(x_mat)] = 0.0
            
            try:
                y_hat = float(model.predict(x_mat)[0])
            except Exception:
                y_hat = float(sim_history.iloc[-1]) if len(sim_history) > 0 else 0.0
                
            y_hat = max(0.0, y_hat)
            predictions.append(y_hat)
            
            # Append recursive prediction into history
            sim_history = pd.concat([sim_history, pd.Series([y_hat])], ignore_index=True)
            
        return np.array(predictions, dtype=float)
