import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RegistryPersistenceError(RuntimeError):
    """Raised when model registry fails to persist state to disk."""
    pass


class ModelRegistry:
    """
    Lightweight, transactional model registry for SKU forecast models.
    Enforces exactly one ACTIVE_CHAMPION per SKU x Branch.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "config/model_registry.json"
        self.models: Dict[str, Dict[str, Any]] = {}
        self.load()

    def get_next_version(self, sku: str, branch: str) -> int:
        """Compute the next monotonically increasing version number for a SKU x Branch."""
        existing = [
            m.get('version', 1) for m in self.models.values()
            if m.get('sku') == sku and m.get('branch') == branch
        ]
        return (max(existing) + 1) if existing else 1

    def register_model(self, sku: str, branch: str, model_name: str,
                       version: Optional[int] = None, 
                       validation_metrics: Optional[Dict[str, float]] = None,
                       hyperparameters: Optional[Dict[str, Any]] = None,
                       feature_list: Optional[List[str]] = None,
                       demand_class: Optional[str] = None,
                       status: str = "ACTIVE_CHAMPION") -> Dict[str, Any]:
        """
        Register or update a model record.
        Enforces atomic champion transition: any previous active champion is retired.
        """
        actual_version = version if (version is not None and version > 0) else self.get_next_version(sku, branch)
        model_id = f"{sku}_{branch}_{model_name}_v{actual_version}".replace(" ", "_")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Atomic governance: retire any currently active champion for this SKU x Branch
        if status == "ACTIVE_CHAMPION":
            for m in self.models.values():
                if m.get('sku') == sku and m.get('branch') == branch and m.get('status') == "ACTIVE_CHAMPION":
                    m['status'] = "RETIRED"
                    m['retired_at'] = now_str
                    m['superseded_by'] = model_id

        record = {
            'model_id': model_id,
            'sku': sku,
            'branch': branch,
            'model_name': model_name,
            'version': actual_version,
            'demand_class': demand_class or "Standard",
            'registered_at': now_str,
            'validation_metrics': validation_metrics or {},
            'hyperparameters': hyperparameters or {},
            'feature_list': feature_list or [],
            'status': status
        }
        self.models[model_id] = record
        self.save()
        return record

    def get_champion(self, sku: str, branch: str) -> Optional[Dict[str, Any]]:
        """Retrieve the active champion for a given SKU x Branch."""
        for m in self.models.values():
            if m['sku'] == sku and m['branch'] == branch and m['status'] == "ACTIVE_CHAMPION":
                return m
        return None

    def list_models_df(self) -> pd.DataFrame:
        """Return registry records as a formatted DataFrame."""
        if not self.models:
            return pd.DataFrame()
            
        rows = []
        for m in self.models.values():
            vm = m.get('validation_metrics', {})
            rows.append({
                'Model ID': m['model_id'],
                'SKU': m['sku'],
                'Branch': m['branch'],
                'Architecture': m['model_name'],
                'Version': f"v{m['version']}",
                'Demand Class': m.get('demand_class', 'Standard'),
                'Registered Date': m['registered_at'],
                'WAPE (%)': f"{vm.get('mean_wape', vm.get('WAPE', 0.0)):.1f}%",
                'RMSE': f"{vm.get('mean_rmse', vm.get('RMSE', 0.0)):.1f}",
                'Status': m['status']
            })
        return pd.DataFrame(rows)

    def save(self):
        """Persist registry to disk with error checking."""
        try:
            parent_dir = os.path.dirname(self.storage_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.models, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist model registry to {self.storage_path}: {e}")
            raise RegistryPersistenceError(f"Registry write failure: {e}") from e

    def load(self):
        """Load registry from disk if exists."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.models = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing registry: {e}. Starting fresh.")
                self.models = {}
