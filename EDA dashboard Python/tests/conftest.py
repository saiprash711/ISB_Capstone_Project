"""Shared test fixtures."""
import pytest

from src.monitoring import registry as registry_module


@pytest.fixture(autouse=True)
def isolated_model_registry(tmp_path, monkeypatch):
    """Point every ModelRegistry at a temporary file so tests never rewrite config/*.json."""
    original_init = registry_module.ModelRegistry.__init__

    def _init(self, storage_path=None):
        original_init(self, storage_path=str(tmp_path / "model_registry.json"))

    monkeypatch.setattr(registry_module.ModelRegistry, "__init__", _init)
