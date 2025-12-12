"""
Expert Configuration System

Provides configuration models and loaders for defining experts via YAML files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ExpertConfigModel(BaseModel):
    """
    Pydantic model for expert configuration.

    Experts are defined in YAML configuration files and instantiated
    automatically by the ExpertRegistry.
    """

    model_config = ConfigDict(extra="forbid")  # Don't allow extra fields

    expert_id: str = Field(
        ..., description="Unique expert identifier (e.g., 'expert-home-automation')"
    )
    expert_name: str = Field(..., description="Human-readable expert name")
    primary_domain: str = Field(
        ..., description="Domain where this expert has 51% authority"
    )
    rag_enabled: bool = Field(
        default=False, description="Enable RAG for knowledge retrieval"
    )
    fine_tuned: bool = Field(
        default=False, description="Use fine-tuned models (future)"
    )
    confidence_matrix: dict[str, float] | None = Field(
        default=None,
        description="Custom confidence weights per domain (usually auto-calculated from weight matrix)",
    )
    mal_config: dict[str, Any] | None = Field(
        default=None, description="Optional MAL-specific configuration for this expert"
    )


@dataclass
class ExpertsConfig:
    """Container for multiple expert configurations."""

    experts: list[ExpertConfigModel] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_file: Path) -> ExpertsConfig:
        """
        Load expert configurations from YAML file.

        Args:
            yaml_file: Path to experts.yaml file

        Returns:
            ExpertsConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid or missing required fields
        """
        if not yaml_file.exists():
            raise FileNotFoundError(f"Expert configuration file not found: {yaml_file}")

        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {yaml_file}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict at root level, got {type(data).__name__}")

        if "experts" not in data:
            raise ValueError(f"Missing 'experts' key in {yaml_file}")

        if not isinstance(data["experts"], list):
            raise ValueError(
                f"Expected 'experts' to be a list, got {type(data['experts']).__name__}"
            )

        expert_configs = []
        for idx, expert_data in enumerate(data["experts"]):
            try:
                expert_config = ExpertConfigModel(**expert_data)
                expert_configs.append(expert_config)
            except Exception as e:
                raise ValueError(
                    f"Invalid expert configuration at index {idx} in {yaml_file}: {e}"
                ) from e

        return cls(experts=expert_configs)


def load_expert_configs(config_file: Path) -> list[ExpertConfigModel]:
    """
    Load expert configurations from YAML file.

    Convenience function that returns just the list of expert configs.

    Args:
        config_file: Path to experts.yaml file

    Returns:
        List of ExpertConfigModel instances
    """
    experts_config = ExpertsConfig.from_yaml(config_file)
    return experts_config.experts
