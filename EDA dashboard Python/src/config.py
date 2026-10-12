"""
Configuration Management
Loads and manages YAML configuration files.
"""
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and access."""
    
    # Default config directory
    CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Path to config directory (auto-detects if None)
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = self.CONFIG_DIR
        
        self.configs = {}
        self._load_all()
    
    def _load_all(self):
        """Load all configuration files."""
        config_files = {
            'data': 'data_config.yaml',
            'model': 'model_config.yaml',
            'business': 'business_config.yaml',
        }
        
        for config_name, filename in config_files.items():
            filepath = self.config_dir / filename
            if filepath.exists():
                self.configs[config_name] = self._load_yaml(filepath)
                logger.info(f"✓ Loaded config: {config_name}")
            else:
                logger.warning(f"✗ Config not found: {filepath}")
                self.configs[config_name] = {}
    
    @staticmethod
    def _load_yaml(filepath: Path) -> Dict[str, Any]:
        """Load YAML file."""
        with open(filepath, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Top-level config section (data, model, business)
            key: Nested key (dot-separated for nested access)
            default: Default value if key not found
            
        Returns:
            Configuration value
            
        Examples:
            cfg.get('data', 'min_history_weeks')
            cfg.get('model', 'forecast.horizon')
            cfg.get('business', 'inventory.target_service_level')
        """
        if section not in self.configs:
            return default
        
        config = self.configs[section]
        
        if key is None:
            return config
        
        # Handle nested keys (dot-separated)
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_data_config(self) -> Dict:
        """Get full data configuration."""
        return self.configs.get('data', {})
    
    def get_model_config(self) -> Dict:
        """Get full model configuration."""
        return self.configs.get('model', {})
    
    def get_business_config(self) -> Dict:
        """Get full business configuration."""
        return self.configs.get('business', {})
    
    def validate(self) -> bool:
        """
        Validate configuration completeness.
        
        Returns:
            True if all required configs are loaded
        """
        required_sections = {'data', 'model', 'business'}
        loaded_sections = set(self.configs.keys())
        
        missing = required_sections - loaded_sections
        if missing:
            logger.warning(f"Missing config sections: {missing}")
            return False
        
        return True


# Global configuration instance
_config_instance = None


def get_config(config_dir: str = None) -> ConfigManager:
    """
    Get global configuration instance (singleton pattern).
    
    Args:
        config_dir: Path to config directory (for initial load)
        
    Returns:
        ConfigManager instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigManager(config_dir)
    
    return _config_instance
