"""
Expert Configuration Generator

Generates expert YAML configurations based on detected domains.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ..experts.domain_detector import DomainMapping
from ..experts.expert_config import (
    ExpertsConfig,
    load_expert_configs,
)

logger = logging.getLogger(__name__)


@dataclass
class ExpertConfig:
    """Expert configuration to be written to YAML."""

    expert_id: str
    expert_name: str
    primary_domain: str
    rag_enabled: bool = True
    knowledge_base_dir: Path | None = None
    confidence_matrix: dict[str, float] | None = None
    metadata: dict[str, Any] | None = None


class ExpertConfigGenerator:
    """
    Generates expert YAML configurations based on detected domains.

    Usage:
        generator = ExpertConfigGenerator(project_root)
        configs = generator.generate_expert_configs(domains)
        generator.write_expert_configs(configs, merge=True)
    """

    def __init__(
        self,
        project_root: Path,
        expert_registry: Any | None = None,  # ExpertRegistry type hint
    ) -> None:
        """
        Initialize generator.

        Args:
            project_root: Root directory of project
            expert_registry: Optional ExpertRegistry for validation
        """
        self.project_root = Path(project_root).resolve()
        self.config_dir = self.project_root / ".tapps-agents"
        self.experts_yaml = self.config_dir / "experts.yaml"
        self.expert_registry = expert_registry

    def generate_expert_configs(
        self, domains: list[DomainMapping]
    ) -> list[ExpertConfig]:
        """
        Generate expert configurations for detected domains.

        Args:
            domains: List of DomainMapping objects from domain detection

        Returns:
            List of ExpertConfig objects ready to be written
        """
        configs = []
        existing_expert_ids = self._get_existing_expert_ids()

        for domain_mapping in domains:
            domain = domain_mapping.domain
            confidence = domain_mapping.confidence

            # Skip if confidence is too low
            if confidence < 0.3:
                logger.debug(f"Skipping domain {domain} (confidence {confidence} too low)")
                continue

            # Generate expert ID
            expert_id = f"expert-{domain.replace('_', '-')}"

            # Skip if expert already exists
            if expert_id in existing_expert_ids:
                logger.info(f"Expert {expert_id} already exists, skipping")
                continue

            # Generate expert name
            expert_name = self._generate_expert_name(domain)

            # Create knowledge base directory path
            kb_dir = self.config_dir / "kb" / expert_id

            # Build confidence matrix from domain mapping
            confidence_matrix = {domain: confidence}

            # Add metadata
            metadata = {
                "created_by": "brownfield-review",
                "created_at": datetime.now().isoformat(),
                "detected_domains": [domain],
                "confidence": confidence,
                "signals": len(domain_mapping.signals),
            }

            config = ExpertConfig(
                expert_id=expert_id,
                expert_name=expert_name,
                primary_domain=domain,
                rag_enabled=True,
                knowledge_base_dir=kb_dir,
                confidence_matrix=confidence_matrix,
                metadata=metadata,
            )

            configs.append(config)
            logger.info(f"Generated config for expert {expert_id} (domain: {domain})")

        return configs

    def write_expert_configs(
        self, configs: list[ExpertConfig], merge: bool = True
    ) -> None:
        """
        Write expert configurations to experts.yaml.

        Args:
            configs: List of ExpertConfig objects to write
            merge: If True, merge with existing configs; if False, overwrite
        """
        if not configs:
            logger.info("No expert configs to write")
            return

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing configs if merging
        existing_data: dict[str, Any] = {"experts": []}
        if merge and self.experts_yaml.exists():
            try:
                existing_configs = ExpertsConfig.from_yaml(self.experts_yaml)
                existing_data = {
                    "experts": [
                        expert.model_dump(exclude_none=True)
                        for expert in existing_configs.experts
                    ]
                }
            except Exception as e:
                logger.warning(f"Failed to load existing experts.yaml: {e}")
                logger.info("Creating new experts.yaml file")

        # Convert new configs to dict format
        new_expert_dicts = []
        for config in configs:
            expert_dict = {
                "expert_id": config.expert_id,
                "expert_name": config.expert_name,
                "primary_domain": config.primary_domain,
                "rag_enabled": config.rag_enabled,
            }

            # Add knowledge_base_dir if specified
            if config.knowledge_base_dir:
                expert_dict["knowledge_base_dir"] = str(
                    config.knowledge_base_dir.relative_to(self.project_root)
                )

            # Add confidence_matrix if specified
            if config.confidence_matrix:
                expert_dict["confidence_matrix"] = config.confidence_matrix

            # Add metadata as comment or separate field (YAML doesn't support comments easily)
            # Store in a way that can be preserved
            if config.metadata:
                # We'll store metadata separately or in a comment-like structure
                pass  # Metadata can be added later if needed

            new_expert_dicts.append(expert_dict)

        # Merge if requested
        if merge:
            # Get existing expert IDs
            existing_ids = {
                expert.get("expert_id") for expert in existing_data["experts"]
            }

            # Only add new experts (don't overwrite existing)
            for new_expert in new_expert_dicts:
                if new_expert["expert_id"] not in existing_ids:
                    existing_data["experts"].append(new_expert)
                else:
                    logger.info(
                        f"Skipping {new_expert['expert_id']} (already exists)"
                    )

            final_data = existing_data
        else:
            final_data = {"experts": new_expert_dicts}

        # Write to YAML file
        try:
            with open(self.experts_yaml, "w", encoding="utf-8") as f:
                yaml.dump(final_data, f, default_flow_style=False, sort_keys=False)

            logger.info(
                f"Wrote {len(new_expert_dicts)} expert configs to {self.experts_yaml}"
            )
        except Exception as e:
            logger.error(f"Failed to write experts.yaml: {e}")
            raise

    def validate_config(self, config: ExpertConfig) -> bool:
        """
        Validate expert configuration.

        Args:
            config: ExpertConfig to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not config.expert_id:
            logger.error("Expert ID is required")
            return False

        if not config.expert_name:
            logger.error("Expert name is required")
            return False

        if not config.primary_domain:
            logger.error("Primary domain is required")
            return False

        # Validate expert ID format
        if not config.expert_id.startswith("expert-"):
            logger.warning(
                f"Expert ID '{config.expert_id}' should start with 'expert-'"
            )

        # Validate domain name
        if not config.primary_domain.replace("_", "-").replace("-", "").isalnum():
            logger.warning(
                f"Domain '{config.primary_domain}' contains invalid characters"
            )

        return True

    def _load_existing_configs(self) -> dict[str, Any]:
        """Load existing expert configurations from YAML."""
        if not self.experts_yaml.exists():
            return {"experts": []}

        try:
            with open(self.experts_yaml, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {"experts": []}
        except Exception as e:
            logger.warning(f"Failed to load existing configs: {e}")
            return {"experts": []}

    def _get_existing_expert_ids(self) -> set[str]:
        """Get set of existing expert IDs."""
        if not self.experts_yaml.exists():
            return set()

        try:
            existing_configs = load_expert_configs(self.experts_yaml)
            return {expert.expert_id for expert in existing_configs}
        except Exception:
            return set()

    def _generate_expert_name(self, domain: str) -> str:
        """
        Generate human-readable expert name from domain.

        Args:
            domain: Domain name (e.g., "python", "api-design-integration")

        Returns:
            Human-readable name (e.g., "Python Expert", "API Design Integration Expert")
        """
        # Replace hyphens/underscores with spaces and title case
        name = domain.replace("_", "-").replace("-", " ").title()
        return f"{name} Expert"
