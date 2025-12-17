"""
Expert Synthesizer

Automatically creates project-specific experts from repo signals.
Generates expert configs and knowledge skeletons without manual setup.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .domain_detector import DomainStackDetector, StackDetectionResult
from .domain_utils import sanitize_domain_for_path
from .expert_config import ExpertConfigModel, ExpertsConfig, load_expert_configs


@dataclass
class ExpertSynthesisResult:
    """Result of expert synthesis operation."""

    experts_created: list[str]  # Expert IDs created
    experts_updated: list[str]  # Expert IDs updated
    knowledge_skeletons_created: list[str]  # Domain paths created
    technical_experts: list[str]  # Technical expert IDs
    project_experts: list[str]  # Project/business expert IDs


class ExpertSynthesizer:
    """
    Automatically synthesizes experts from repo signals.

    Creates expert configs and knowledge skeletons based on detected
    domains and project structure.
    """

    # Technical domains (framework-controlled)
    TECHNICAL_DOMAINS = {
        "python",
        "typescript",
        "javascript",
        "react",
        "django",
        "fastapi",
        "nodejs",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "terraform",
        "ansible",
    }

    # Knowledge skeleton templates
    KNOWLEDGE_TEMPLATES = {
        "overview.md": """# {domain_name} Overview

## Domain Description

{domain_description}

## Key Concepts

- Concept 1: Description
- Concept 2: Description

## Related Domains

- Related domain 1
- Related domain 2
""",
        "glossary.md": """# {domain_name} Glossary

## Terms

| Term | Definition |
|------|------------|
| Term 1 | Definition 1 |
| Term 2 | Definition 2 |
""",
        "decisions.md": """# {domain_name} Architecture Decisions

## ADR-001: Decision Title

**Status:** Proposed

**Context:** Decision context

**Decision:** Decision made

**Consequences:** Impact and consequences
""",
        "pitfalls.md": """# {domain_name} Common Pitfalls

## Pitfall 1: Title

**Description:** Description of the pitfall

**How to Avoid:** Guidance on avoiding this pitfall

**Example:** Example scenario
""",
        "constraints.md": """# {domain_name} Constraints

## Technical Constraints

- Constraint 1: Description
- Constraint 2: Description

## Business Constraints

- Constraint 1: Description
- Constraint 2: Description
""",
    }

    def __init__(self, project_root: Path):
        """
        Initialize Expert Synthesizer.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.config_dir = project_root / ".tapps-agents"
        self.experts_file = self.config_dir / "experts.yaml"
        self.knowledge_base_dir = self.config_dir / "knowledge"
        self.domain_detector = DomainStackDetector(project_root=project_root)

    def synthesize_experts(
        self,
        detection_result: StackDetectionResult | None = None,
        overwrite_existing: bool = False,
    ) -> ExpertSynthesisResult:
        """
        Synthesize experts from repo signals.

        Args:
            detection_result: Pre-computed detection result (if None, runs detection)
            overwrite_existing: Whether to overwrite existing expert configs

        Returns:
            ExpertSynthesisResult with created/updated experts
        """
        # Run detection if not provided
        if detection_result is None:
            detection_result = self.domain_detector.detect_stack()

        # Load existing experts
        existing_experts = self._load_existing_experts()

        # Determine which experts to create
        experts_to_create = self._determine_experts_to_create(
            detection_result, existing_experts, overwrite_existing
        )

        # Create expert configs
        experts_created = []
        experts_updated = []
        technical_experts = []
        project_experts = []

        for expert_config in experts_to_create:
            expert_id = expert_config.expert_id

            # Check if expert already exists
            existing = next(
                (e for e in existing_experts if e.expert_id == expert_id), None
            )

            if existing and not overwrite_existing:
                continue  # Skip existing experts unless overwriting

            # Determine expert type
            is_technical = expert_config.primary_domain.lower() in self.TECHNICAL_DOMAINS

            # Add to appropriate list
            if existing:
                experts_updated.append(expert_id)
            else:
                experts_created.append(expert_id)

            if is_technical:
                technical_experts.append(expert_id)
            else:
                project_experts.append(expert_id)

        # Write expert configs
        if experts_to_create:
            self._write_expert_configs(experts_to_create, existing_experts, overwrite_existing)

        # Create knowledge skeletons
        knowledge_skeletons_created = self._create_knowledge_skeletons(
            detection_result, overwrite_existing
        )

        return ExpertSynthesisResult(
            experts_created=experts_created,
            experts_updated=experts_updated,
            knowledge_skeletons_created=knowledge_skeletons_created,
            technical_experts=technical_experts,
            project_experts=project_experts,
        )

    def _load_existing_experts(self) -> list[ExpertConfigModel]:
        """Load existing expert configs."""
        if not self.experts_file.exists():
            return []

        try:
            return load_expert_configs(self.experts_file)
        except Exception:
            return []

    def _determine_experts_to_create(
        self,
        detection_result: StackDetectionResult,
        existing_experts: list[ExpertConfigModel],
        overwrite_existing: bool,
    ) -> list[ExpertConfigModel]:
        """Determine which experts to create based on detected domains."""
        experts_to_create = []
        existing_expert_ids = {e.expert_id for e in existing_experts}

        # Create experts for detected domains
        for domain_mapping in detection_result.domains:
            domain = domain_mapping.domain
            expert_id = f"expert-{domain.replace('_', '-')}"

            # Skip if exists and not overwriting
            if expert_id in existing_expert_ids and not overwrite_existing:
                continue

            # Generate expert name
            expert_name = self._generate_expert_name(domain)

            # Create expert config
            expert_config = ExpertConfigModel(
                expert_id=expert_id,
                expert_name=expert_name,
                primary_domain=domain,
                rag_enabled=True,  # Enable RAG by default
                fine_tuned=False,
            )

            experts_to_create.append(expert_config)

        return experts_to_create

    def _generate_expert_name(self, domain: str) -> str:
        """Generate human-readable expert name from domain."""
        # Convert domain to title case
        name_parts = domain.replace("_", " ").replace("-", " ").split()
        name = " ".join(word.capitalize() for word in name_parts)
        return f"{name} Expert"

    def _write_expert_configs(
        self,
        new_experts: list[ExpertConfigModel],
        existing_experts: list[ExpertConfigModel],
        overwrite_existing: bool,
    ):
        """Write expert configs to YAML file."""
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Merge existing and new experts
        expert_dict = {e.expert_id: e for e in existing_experts}

        for expert in new_experts:
            if overwrite_existing or expert.expert_id not in expert_dict:
                expert_dict[expert.expert_id] = expert

        # Convert to YAML format
        experts_list = []
        for expert in expert_dict.values():
            expert_dict_data = {
                "expert_id": expert.expert_id,
                "expert_name": expert.expert_name,
                "primary_domain": expert.primary_domain,
                "rag_enabled": expert.rag_enabled,
                "fine_tuned": expert.fine_tuned,
            }
            if expert.confidence_matrix:
                expert_dict_data["confidence_matrix"] = expert.confidence_matrix
            if expert.mal_config:
                expert_dict_data["mal_config"] = expert.mal_config

            experts_list.append(expert_dict_data)

        # Write YAML file
        config_data = {"experts": experts_list}

        with open(self.experts_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    def _create_knowledge_skeletons(
        self,
        detection_result: StackDetectionResult,
        overwrite_existing: bool,
    ) -> list[str]:
        """Create knowledge skeleton directories and files."""
        created_domains = []

        # Ensure knowledge base directory exists
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

        for domain_mapping in detection_result.domains:
            domain = domain_mapping.domain
            sanitized_domain = sanitize_domain_for_path(domain)
            domain_dir = self.knowledge_base_dir / sanitized_domain

            # Skip if exists and not overwriting
            if domain_dir.exists() and not overwrite_existing:
                continue

            # Create domain directory
            domain_dir.mkdir(parents=True, exist_ok=True)
            created_domains.append(sanitized_domain)

            # Generate expert name for templates
            expert_name = self._generate_expert_name(domain)

            # Create knowledge skeleton files
            for template_name, template_content in self.KNOWLEDGE_TEMPLATES.items():
                template_path = domain_dir / template_name

                # Skip if exists and not overwriting
                if template_path.exists() and not overwrite_existing:
                    continue

                # Format template
                content = template_content.format(
                    domain_name=expert_name,
                    domain_description=f"Knowledge base for {expert_name}",
                )

                # Write template file
                template_path.write_text(content, encoding="utf-8")

        return created_domains

    def is_technical_expert(self, domain: str) -> bool:
        """Check if domain is a technical (framework-controlled) expert."""
        return domain.lower() in self.TECHNICAL_DOMAINS

    def is_project_expert(self, domain: str) -> bool:
        """Check if domain is a project/business (project-controlled) expert."""
        return not self.is_technical_expert(domain)

