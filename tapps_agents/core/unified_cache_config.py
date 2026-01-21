"""
Unified Cache Configuration - Configuration management for unified cache.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from .hardware_profiler import HardwareProfile


@dataclass
class UnifiedCacheConfig:
    """Unified cache configuration."""

    enabled: bool = True
    storage_root: str = ".tapps-agents/kb/unified-cache"

    # Adaptive settings
    adaptive_enabled: bool = True
    adaptive_check_interval: int = 60

    # Tiered context settings
    tiered_context_enabled: bool = True
    tiered_context_namespace: str = "tiered-context"

    # Context7 KB settings
    context7_kb_enabled: bool = True
    context7_kb_namespace: str = "context7-kb"

    # RAG knowledge settings
    rag_knowledge_enabled: bool = True
    rag_knowledge_namespace: str = "rag-knowledge"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnifiedCacheConfig:
        """Create from dictionary."""
        return cls(**data)


class UnifiedCacheConfigManager:
    """Manages unified cache configuration."""

    def __init__(self, config_path: Path | None = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config file (defaults to .tapps-agents/unified-cache-config.yaml)
        """
        if config_path is None:
            config_path = Path(".tapps-agents/unified-cache-config.yaml")

        self.config_path = Path(config_path)
        self._config: UnifiedCacheConfig | None = None

    def load(self) -> UnifiedCacheConfig:
        """
        Load configuration from file.

        Returns:
            UnifiedCacheConfig instance
        """
        if self._config:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data and "unified_cache" in data:
                    config_data = data["unified_cache"]
                    # Map nested structure to flat structure
                    config = UnifiedCacheConfig(
                        enabled=config_data.get("enabled", True),
                        storage_root=config_data.get(
                            "storage_root", ".tapps-agents/kb/unified-cache"
                        ),
                        adaptive_enabled=config_data.get("adaptive", {}).get(
                            "enabled", True
                        ),
                        adaptive_check_interval=config_data.get("adaptive", {}).get(
                            "check_interval", 60
                        ),
                        tiered_context_enabled=config_data.get(
                            "tiered_context", {}
                        ).get("enabled", True),
                        tiered_context_namespace=config_data.get(
                            "tiered_context", {}
                        ).get("namespace", "tiered-context"),
                        context7_kb_enabled=config_data.get("context7_kb", {}).get(
                            "enabled", True
                        ),
                        context7_kb_namespace=config_data.get("context7_kb", {}).get(
                            "namespace", "context7-kb"
                        ),
                        rag_knowledge_enabled=config_data.get("rag_knowledge", {}).get(
                            "enabled", True
                        ),
                        rag_knowledge_namespace=config_data.get(
                            "rag_knowledge", {}
                        ).get("namespace", "rag-knowledge"),
                    )
                else:
                    config = UnifiedCacheConfig()
            except Exception:
                config = UnifiedCacheConfig()
        else:
            config = UnifiedCacheConfig()

        self._config = config
        return config

    def save(self, config: UnifiedCacheConfig | None = None):
        """
        Save configuration to file.

        Args:
            config: Configuration to save (uses loaded config if not provided)
        """
        if config is None:
            config = self.load()

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to nested structure for YAML
        data = {
            "unified_cache": {
                "enabled": config.enabled,
                "storage_root": config.storage_root,
                "adaptive": {
                    "enabled": config.adaptive_enabled,
                    "check_interval": config.adaptive_check_interval,
                },
                "tiered_context": {
                    "enabled": config.tiered_context_enabled,
                    "namespace": config.tiered_context_namespace,
                },
                "context7_kb": {
                    "enabled": config.context7_kb_enabled,
                    "namespace": config.context7_kb_namespace,
                },
                "rag_knowledge": {
                    "enabled": config.rag_knowledge_enabled,
                    "namespace": config.rag_knowledge_namespace,
                },
            }
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        self._config = config

    def get_hardware_profile(self) -> HardwareProfile:
        """
        Return hardware profile. Always WORKSTATION (taxonomy removed).
        Kept for API compatibility.
        """
        return HardwareProfile.WORKSTATION
