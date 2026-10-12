"""
Champion / Challenger Governance Framework
Manages champion model state, tracks challenger performance,
and applies auditable promotion rules for model governance.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime


class ChampionChallengerManager:
    """
    Maintains production model status and validates replacement criteria.
    """
    
    def __init__(self, min_wape_lift: float = 3.0, max_bias_tolerance: float = 15.0,
                 min_stability_threshold: float = 40.0):
        """
        Args:
            min_wape_lift: Minimum WAPE reduction (%) required to dethrone a Champion
            max_bias_tolerance: Maximum allowable absolute forecast bias %
            min_stability_threshold: Minimum acceptable stability score (0-100)
        """
        self.min_wape_lift = min_wape_lift
        self.max_bias_tolerance = max_bias_tolerance
        self.min_stability_threshold = min_stability_threshold
        self.registry: Dict[str, Dict[str, Any]] = {}

    def register_evaluation(self, sku: str, branch: str, 
                            leaderboard_df, demand_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate candidate models from backtesting, assign Champion and Challengers.
        Applies strict quality gates on initial assignment and challenger promotion.
        """
        key = f"{sku}_{branch}"
        if leaderboard_df.empty:
            return {'status': 'error', 'message': 'Empty leaderboard'}

        ranked_models = leaderboard_df.to_dict(orient='records')
        top_candidate = ranked_models[0]
        challengers = ranked_models[1:4] if len(ranked_models) > 1 else []

        current_entry = self.registry.get(key)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cand_wape = float(top_candidate['mean_wape'])
        cand_bias = abs(float(top_candidate.get('mean_bias_pct', 0.0)))
        cand_stab = float(top_candidate.get('stability_score', 60.0))

        if current_entry is None:
            # Quality gate for initial champion assignment
            is_acceptable = (cand_wape <= 100.0 and cand_bias <= 50.0 and cand_stab >= self.min_stability_threshold)
            status = 'ACTIVE_CHAMPION' if is_acceptable else 'PROVISIONAL_CHAMPION'
            reason = (
                f"Tournament winner with lowest WAPE ({cand_wape:.1f}%) and stability {cand_stab:.1f}."
                if is_acceptable else
                f"Tournament winner assigned provisionally: WAPE ({cand_wape:.1f}%) or bias ({cand_bias:.1f}%) requires manual operational review."
            )
            champion = {
                'model_name': top_candidate['model'],
                'version': 1,
                'assigned_date': now_str,
                'wape': cand_wape,
                'rmse': float(top_candidate['mean_rmse']),
                'bias_pct': cand_bias,
                'stability_score': cand_stab,
                'demand_type': demand_profile.get('demand_type', 'Standard'),
                'selection_reason': reason,
                'status': status
            }
            action = "INITIAL_ASSIGNMENT"
        else:
            prev_champ = current_entry['champion']
            prev_wape = float(prev_champ['wape'])
            wape_improvement = prev_wape - cand_wape
            
            # Comprehensive promotion governance check: WAPE lift + Bias control + Stability
            has_wape_lift = wape_improvement >= self.min_wape_lift
            has_bias_control = cand_bias <= self.max_bias_tolerance
            has_stability = cand_stab >= self.min_stability_threshold
            is_different_model = top_candidate['model'] != prev_champ.get('model_name', prev_champ.get('model'))
            
            is_valid_challenger = is_different_model and has_wape_lift and has_bias_control and has_stability

            if is_valid_challenger:
                champion = {
                    'model_name': top_candidate['model'],
                    'version': prev_champ['version'] + 1,
                    'assigned_date': now_str,
                    'wape': cand_wape,
                    'rmse': float(top_candidate['mean_rmse']),
                    'bias_pct': cand_bias,
                    'stability_score': cand_stab,
                    'demand_type': demand_profile.get('demand_type', 'Standard'),
                    'selection_reason': (
                        f"Dethroned {prev_champ.get('model_name', 'Previous Champion')} with {wape_improvement:.1f}% WAPE lift "
                        f"({cand_wape:.1f}% vs {prev_wape:.1f}%), bias ({cand_bias:.1f}%), and stability ({cand_stab:.1f})."
                    ),
                    'status': 'ACTIVE_CHAMPION'
                }
                action = "CHAMPION_PROMOTED"
            else:
                # Retain previous champion with auditable rationale
                reasons = []
                if not is_different_model:
                    reasons.append("same architecture as incumbent")
                if not has_wape_lift:
                    reasons.append(f"insufficient WAPE lift ({wape_improvement:+.1f}% vs required {self.min_wape_lift}%)")
                if not has_bias_control:
                    reasons.append(f"excessive bias ({cand_bias:.1f}% vs limit {self.max_bias_tolerance}%)")
                if not has_stability:
                    reasons.append(f"stability score ({cand_stab:.1f} vs threshold {self.min_stability_threshold})")
                    
                champion = prev_champ
                champion['retention_audit'] = f"Incumbent retained; challenger rejected: {', '.join(reasons)}."
                action = "CHAMPION_RETAINED"

        formatted_challengers = []
        for c in challengers:
            gap = float(c['mean_wape']) - float(champion['wape'])
            formatted_challengers.append({
                'model_name': c['model'],
                'wape': float(c['mean_wape']),
                'rmse': float(c['mean_rmse']),
                'gap_to_champion': round(gap, 2),
                'status': 'CHALLENGER'
            })

        entry = {
            'sku': sku,
            'branch': branch,
            'demand_type': demand_profile.get('demand_type', 'Standard'),
            'champion': champion,
            'challengers': formatted_challengers,
            'action': action,
            'last_evaluated': now_str
        }
        self.registry[key] = entry
        return entry
