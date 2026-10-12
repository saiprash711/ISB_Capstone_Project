"""
Model Leaderboard and Cross-Validation Diagnostics Module
Formats model comparisons, evaluates baseline vs advanced lift,
and generates standardized validation cards.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any


class ModelLeaderboard:
    """
    Manages model comparison leaderboard and diagnostic analytics.
    """
    
    def __init__(self, leaderboard_df: pd.DataFrame):
        self.df = leaderboard_df.copy() if isinstance(leaderboard_df, pd.DataFrame) else pd.DataFrame()
        if not self.df.empty and 'rank' not in self.df.columns:
            self.df = self.df.sort_values(by=['mean_wape', 'mean_rmse']).reset_index(drop=True)
            self.df['rank'] = np.arange(1, len(self.df) + 1)

    def get_champion(self) -> Optional[Dict[str, Any]]:
        """Return details of the top-ranked model."""
        if self.df.empty:
            return None
        return self.df.iloc[0].to_dict()

    def get_challengers(self, top_n: int = 3) -> List[Dict[str, Any]]:
        """Return the next top N challenger models."""
        if len(self.df) <= 1:
            return []
        return self.df.iloc[1:1 + top_n].to_dict(orient='records')

    def compare_with_baseline(self) -> Dict[str, Any]:
        """
        Evaluate if advanced models outperform simple baseline strategies.
        Addresses the core consulting question:
        'Does the sophisticated model actually outperform a simple forecasting strategy?'
        """
        if self.df.empty:
            return {'has_lift': False, 'message': 'No models evaluated'}
            
        naive_rows = self.df[self.df['model'].str.lower().isin(['naive', 'seasonal naive'])]
        if naive_rows.empty:
            naive_wape = float(self.df['mean_wape'].max())
            naive_name = "Benchmark"
        else:
            best_naive = naive_rows.sort_values('mean_wape').iloc[0]
            naive_wape = float(best_naive['mean_wape'])
            naive_name = str(best_naive['model'])

        champion = self.get_champion()
        champ_wape = float(champion['mean_wape'])
        champ_name = str(champion['model'])

        wape_lift = naive_wape - champ_wape
        pct_improvement = (wape_lift / naive_wape * 100.0) if naive_wape > 0 else 0.0

        is_sophisticated = champ_name not in ['Naive', 'Seasonal Naive', 'Moving Average']
        outperforms_baseline = (wape_lift > 0.5)

        return {
            'champion_name': champ_name,
            'champion_wape': champ_wape,
            'baseline_name': naive_name,
            'baseline_wape': naive_wape,
            'wape_reduction_points': round(wape_lift, 2),
            'pct_accuracy_lift': round(pct_improvement, 2),
            'outperforms_baseline': outperforms_baseline,
            'is_sophisticated': is_sophisticated,
            'verdict': (
                f"Champion '{champ_name}' achieves {round(pct_improvement, 1)}% error reduction "
                f"over {naive_name} baseline (WAPE {champ_wape:.1f}% vs {naive_wape:.1f}%)."
                if outperforms_baseline else
                f"Simple {naive_name} baseline performs competitively against complex alternatives."
            )
        }

    def to_display_table(self) -> pd.DataFrame:
        """Format leaderboard for high-density UI rendering."""
        if self.df.empty:
            return pd.DataFrame()
            
        cols = [
            'rank', 'model', 'mean_wape', 'std_wape', 'mean_rmse', 
            'mean_mase', 'mean_bias', 'stability_score'
        ]
        available_cols = [c for c in cols if c in self.df.columns]
        table = self.df[available_cols].copy()
        table.rename(columns={
            'rank': 'Rank',
            'model': 'Forecasting Model',
            'mean_wape': 'WAPE (%)',
            'std_wape': 'WAPE Std Dev',
            'mean_rmse': 'RMSE',
            'mean_mase': 'MASE',
            'mean_bias': 'Mean Bias',
            'stability_score': 'Stability (0-100)'
        }, inplace=True)
        return table
