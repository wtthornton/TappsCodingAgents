"""
Auto-Expert Generator

Automatically generates experts from suggestions with knowledge base population.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .expert_config import ExpertConfigModel
from .expert_suggester import ExpertSuggestion
from .weight_distributor import ExpertWeightMatrix, WeightDistributor

logger = logging.getLogger(__name__)


@dataclass
class GeneratedExpert:
    """Result of expert generation."""

    expert_id: str
    expert_name: str
    primary_domain: str
    config_path: Path
    knowledge_base_path: Path
    weight_matrix_updated: bool
    knowledge_files_created: list[str]


class AutoExpertGenerator:
    """
    Automatically generates experts from suggestions.
    
    Creates expert configuration, knowledge base structure, and updates
    weight matrix automatically.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize auto-expert generator.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.experts_file = self.project_root / ".tapps-agents" / "experts.yaml"
        self.knowledge_base_dir = self.project_root / ".tapps-agents" / "knowledge"

    async def generate_expert(
        self,
        suggestion: ExpertSuggestion,
        auto_approve: bool = False,
    ) -> GeneratedExpert:
        """
        Generate expert from suggestion.

        Args:
            suggestion: ExpertSuggestion to generate
            auto_approve: If True, generate without validation prompts

        Returns:
            GeneratedExpert with paths and status

        Raises:
            ValueError: If expert already exists or validation fails
        """
        # Validate suggestion
        if not auto_approve:
            self._validate_suggestion(suggestion)

        # Check if expert already exists
        if self._expert_exists(suggestion.expert_id):
            raise ValueError(f"Expert {suggestion.expert_id} already exists")

        # 1. Create expert config entry
        config_path = self._create_expert_config(suggestion)

        # 2. Generate knowledge base structure
        knowledge_base_path = self._create_knowledge_base(suggestion)

        # 3. Populate initial knowledge
        knowledge_files = await self._populate_knowledge(
            suggestion, knowledge_base_path
        )

        # 4. Update weight matrix
        weight_matrix_updated = await self._update_weight_matrix(suggestion)

        # 5. Validate configuration
        self._validate_generated_expert(suggestion)

        return GeneratedExpert(
            expert_id=suggestion.expert_id,
            expert_name=suggestion.expert_name,
            primary_domain=suggestion.primary_domain,
            config_path=config_path,
            knowledge_base_path=knowledge_base_path,
            weight_matrix_updated=weight_matrix_updated,
            knowledge_files_created=knowledge_files,
        )

    def _validate_suggestion(self, suggestion: ExpertSuggestion) -> None:
        """Validate expert suggestion before generation."""
        if not suggestion.expert_id:
            raise ValueError("Expert ID is required")
        if not suggestion.expert_name:
            raise ValueError("Expert name is required")
        if not suggestion.primary_domain:
            raise ValueError("Primary domain is required")
        if suggestion.confidence < 0.5:
            raise ValueError(
                f"Confidence too low ({suggestion.confidence:.2f}), minimum 0.5"
            )

    def _expert_exists(self, expert_id: str) -> bool:
        """Check if expert already exists."""
        if not self.experts_file.exists():
            return False

        try:
            with open(self.experts_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                experts = data.get("experts", [])
                return any(e.get("expert_id") == expert_id for e in experts)
        except Exception:
            return False

    def _create_expert_config(self, suggestion: ExpertSuggestion) -> Path:
        """Create expert configuration entry."""
        # Load existing experts
        experts = []
        if self.experts_file.exists():
            try:
                with open(self.experts_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    experts = data.get("experts", [])
            except Exception as e:
                logger.warning(f"Error loading existing experts: {e}")

        # Create new expert config
        new_expert = {
            "expert_id": suggestion.expert_id,
            "expert_name": suggestion.expert_name,
            "primary_domain": suggestion.primary_domain,
            "rag_enabled": True,  # Enable RAG by default for auto-generated experts
            "fine_tuned": False,
        }

        # Add to list
        experts.append(new_expert)

        # Write back to file
        self.experts_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.experts_file, "w", encoding="utf-8") as f:
            yaml.dump({"experts": experts}, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created expert config: {suggestion.expert_id}")
        return self.experts_file

    def _create_knowledge_base(self, suggestion: ExpertSuggestion) -> Path:
        """Create knowledge base directory structure."""
        domain_dir = self.knowledge_base_dir / suggestion.primary_domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created knowledge base: {domain_dir}")
        return domain_dir

    async def _populate_knowledge(
        self, suggestion: ExpertSuggestion, knowledge_base_path: Path
    ) -> list[str]:
        """
        Populate knowledge base with initial content.

        Sources:
        - Context7 MCP (if available)
        - Web research (2025 patterns)
        - Codebase patterns
        - Expert templates
        """
        knowledge_files = []

        # Create knowledge files from suggestions
        for knowledge_file in suggestion.suggested_knowledge:
            file_path = knowledge_base_path / knowledge_file
            if not file_path.exists():
                # Create template knowledge file
                content = self._generate_knowledge_template(
                    knowledge_file, suggestion
                )
                file_path.write_text(content, encoding="utf-8")
                knowledge_files.append(knowledge_file)
                logger.info(f"Created knowledge file: {knowledge_file}")

        # Try to populate from Context7 (if available)
        try:
            context7_files = await self._populate_from_context7(
                suggestion, knowledge_base_path
            )
            knowledge_files.extend(context7_files)
        except Exception as e:
            logger.debug(f"Context7 population failed: {e}")

        return knowledge_files

    def _generate_knowledge_template(
        self, filename: str, suggestion: ExpertSuggestion
    ) -> str:
        """Generate template knowledge file content."""
        # Extract topic from filename
        topic = filename.replace(".md", "").replace("-", " ").title()

        return f"""# {topic}

**Domain:** {suggestion.primary_domain}
**Expert:** {suggestion.expert_name}
**Auto-generated:** Yes

## Overview

This knowledge file was auto-generated for the {suggestion.expert_name}.
It will be populated with domain-specific patterns and best practices.

## Patterns

*To be populated with actual patterns and examples*

## Best Practices

*To be populated with best practices*

## Common Issues

*To be populated with common issues and solutions*

## References

*To be populated with relevant references*
"""

    async def _populate_from_context7(
        self, suggestion: ExpertSuggestion, knowledge_base_path: Path
    ) -> list[str]:
        """
        Populate knowledge from Context7 MCP (if available).

        Returns:
            List of created knowledge files
        """
        # This would integrate with Context7 MCP when available
        # For now, return empty list
        return []

    async def _update_weight_matrix(
        self, suggestion: ExpertSuggestion
    ) -> bool:
        """
        Update weight matrix with new expert.

        Returns:
            True if matrix was updated, False otherwise
        """
        # Load domain config
        domains_file = self.project_root / ".tapps-agents" / "domains.md"
        if not domains_file.exists():
            logger.warning("domains.md not found, cannot update weight matrix")
            return False

        try:
            from .domain_config import DomainConfigParser

            domain_config = DomainConfigParser.parse(domains_file)
            current_matrix = domain_config.weight_matrix

            if current_matrix:
                # Recalculate weights with new expert
                new_matrix = WeightDistributor.recalculate_on_domain_add(
                    current_matrix,
                    suggestion.primary_domain,
                    suggestion.expert_id,
                )

                # Update domains.md with new weight matrix
                # Read current content
                content = domains_file.read_text(encoding="utf-8")
                
                # Find and replace weight matrix section
                # This is a simplified approach - in production, would use proper YAML parsing
                import re
                weight_matrix_pattern = r"```yaml\nweight_matrix:.*?```"
                
                # Generate new weight matrix YAML
                new_matrix_yaml = WeightDistributor.format_matrix(new_matrix)
                
                # If pattern exists, replace it; otherwise append
                if re.search(weight_matrix_pattern, content, re.DOTALL):
                    new_content = re.sub(
                        weight_matrix_pattern,
                        f"```yaml\nweight_matrix:\n{new_matrix_yaml}\n```",
                        content,
                        flags=re.DOTALL
                    )
                else:
                    # Append weight matrix to end of file
                    new_content = content + f"\n\n```yaml\nweight_matrix:\n{new_matrix_yaml}\n```\n"
                
                domains_file.write_text(new_content, encoding="utf-8")
                logger.info(f"Updated weight matrix for expert {suggestion.expert_id}")
                return True
        except Exception as e:
            logger.warning(f"Error updating weight matrix: {e}")
            return False

    def _validate_generated_expert(self, suggestion: ExpertSuggestion) -> None:
        """Validate generated expert configuration."""
        # Load and validate expert config
        try:
            from .expert_config import load_expert_configs

            experts = load_expert_configs(self.experts_file)
            expert = next(
                (e for e in experts if e.expert_id == suggestion.expert_id), None
            )
            if not expert:
                raise ValueError(f"Expert {suggestion.expert_id} not found after generation")
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
