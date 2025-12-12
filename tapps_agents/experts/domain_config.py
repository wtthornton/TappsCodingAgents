"""
Domain Configuration System

Parses domains.md files and generates expert configurations.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .weight_distributor import ExpertWeightMatrix, WeightDistributor


@dataclass
class Domain:
    """Represents a single domain definition."""

    name: str
    description: list[str]
    primary_expert_id: str
    key_concepts: list[str]


@dataclass
class DomainConfig:
    """Complete domain configuration for a project."""

    project_name: str
    domains: list[Domain]
    weight_matrix: ExpertWeightMatrix

    def get_expert_primary_map(self) -> dict[str, str]:
        """Get mapping of expert_id -> primary_domain."""
        return {domain.primary_expert_id: domain.name for domain in self.domains}

    def get_domain_names(self) -> list[str]:
        """Get list of domain names."""
        return [domain.name for domain in self.domains]

    def get_expert_ids(self) -> list[str]:
        """Get list of expert IDs."""
        return [domain.primary_expert_id for domain in self.domains]


class DomainConfigParser:
    """
    Parses domains.md files into DomainConfig objects.

    Expected format:
    ```markdown
    # domains.md

    ## Project: [Project Name]

    ### Domain 1: [Domain Name]
    - [Description point 1]
    - [Description point 2]
    - Primary Expert: expert-domain-1

    ### Domain 2: [Domain Name]
    ...
    ```
    """

    @staticmethod
    def parse(domains_file: Path) -> DomainConfig:
        """
        Parse a domains.md file.

        Args:
            domains_file: Path to domains.md file

        Returns:
            DomainConfig object with parsed domains and weight matrix

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If parsing fails
        """
        if not domains_file.exists():
            raise FileNotFoundError(
                f"Domain configuration file not found: {domains_file}"
            )

        content = domains_file.read_text(encoding="utf-8")

        # Extract project name
        project_match = re.search(
            r"##\s+Project:\s*(.+?)(?:\n|$)", content, re.IGNORECASE
        )
        project_name = (
            project_match.group(1).strip() if project_match else "Unknown Project"
        )

        # Extract domains
        domains = DomainConfigParser._extract_domains(content)

        if not domains:
            raise ValueError(f"No domains found in {domains_file}")

        # Build expert-primary mapping
        expert_primary_map = {
            domain.primary_expert_id: domain.name for domain in domains
        }

        # Calculate weight matrix
        domain_names = [domain.name for domain in domains]
        weight_matrix = WeightDistributor.calculate_weights(
            domains=domain_names, expert_primary_map=expert_primary_map
        )

        return DomainConfig(
            project_name=project_name, domains=domains, weight_matrix=weight_matrix
        )

    @staticmethod
    def _extract_domains(content: str) -> list[Domain]:
        """
        Extract domain definitions from markdown content.

        Expected format:
        ### Domain 1: [Name]
        - [Point 1]
        - [Point 2]
        - Primary Expert: expert-id
        """
        domains = []

        # Split by domain headers (### Domain X: or ### [Name])
        domain_pattern = r"###\s*(?:Domain\s+\d+:\s*)?(.+?)(?:\n|$)"
        domain_sections = re.split(domain_pattern, content)

        # Skip first element (content before first domain)
        for i in range(1, len(domain_sections), 2):
            if i + 1 >= len(domain_sections):
                break

            domain_name = domain_sections[i].strip()
            domain_content = domain_sections[i + 1]

            # Extract description points (bullet lists)
            description_points = re.findall(
                r"^[-*]\s*(.+?)(?:\n|$)", domain_content, re.MULTILINE
            )

            # Extract primary expert
            primary_expert_match = re.search(
                r"Primary\s+Expert:\s*(.+?)(?:\n|$)", domain_content, re.IGNORECASE
            )
            primary_expert_id = (
                primary_expert_match.group(1).strip() if primary_expert_match else None
            )

            if not primary_expert_id:
                # Try alternative format: "Primary Expert: expert-*"
                primary_expert_match = re.search(
                    r"expert-[a-z0-9-]+", domain_content, re.IGNORECASE
                )
                primary_expert_id = (
                    primary_expert_match.group(0) if primary_expert_match else None
                )

            if not primary_expert_id:
                # Generate default expert ID from domain name
                domain_slug = re.sub(r"[^a-z0-9-]", "-", domain_name.lower())
                primary_expert_id = f"expert-{domain_slug}"

            # Filter out the "Primary Expert" line from description
            description_points = [
                point
                for point in description_points
                if not re.match(r"Primary\s+Expert:", point, re.IGNORECASE)
            ]

            # Extract key concepts (lines starting with "- Key:", "Key:", etc.)
            key_concepts = []
            for point in description_points:
                concept_match = re.match(
                    r"(?:Key|Concept)[:\s]*(.+)", point, re.IGNORECASE
                )
                if concept_match:
                    key_concepts.append(concept_match.group(1).strip())

            domains.append(
                Domain(
                    name=domain_name,
                    description=description_points,
                    primary_expert_id=primary_expert_id,
                    key_concepts=key_concepts,
                )
            )

        return domains

    @staticmethod
    def generate_expert_config(
        domain_config: DomainConfig,
        output_dir: Path,
        expert_template: str | None = None,
    ) -> dict[str, Path]:
        """
        Generate expert configuration files from domain config.

        Args:
            domain_config: Parsed domain configuration
            output_dir: Directory to write expert configs
            expert_template: Optional template for expert configs

        Returns:
            Dictionary mapping expert_id -> config_file_path
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        expert_configs = {}

        for domain in domain_config.domains:
            expert_id = domain.primary_expert_id
            weights = domain_config.weight_matrix.weights[expert_id]

            # Generate YAML config
            config_content = DomainConfigParser._generate_expert_yaml(
                expert_id=expert_id, domain=domain, weights=weights
            )

            config_file = output_dir / f"{expert_id}.yaml"
            config_file.write_text(config_content, encoding="utf-8")

            expert_configs[expert_id] = config_file

        # Generate weight matrix file
        weight_matrix_file = output_dir / "expert_weights.yaml"
        weight_matrix_content = DomainConfigParser._generate_weight_matrix_yaml(
            domain_config
        )
        weight_matrix_file.write_text(weight_matrix_content, encoding="utf-8")

        return expert_configs

    @staticmethod
    def _generate_expert_yaml(
        expert_id: str, domain: Domain, weights: dict[str, float]
    ) -> str:
        """Generate YAML configuration for an expert."""
        confidence_matrix = ",\n      ".join(
            f"{d}: {w:.3f}" for d, w in weights.items()
        )

        return f"""# Expert Configuration: {expert_id}

expert:
  id: {expert_id}
  name: "{domain.name} Expert"
  primary_domain: {domain.name}
  
  confidence_matrix:
    {confidence_matrix}
  
  description: |
    {chr(10).join(f"    {point}" for point in domain.description)}
  
  key_concepts:
{chr(10).join(f"    - {concept}" for concept in domain.key_concepts)}
  
  capabilities:
    - RAG integration
    - Domain knowledge consultation
    - Artifact validation
    - Context provision
  
  permissions:
    - Read
    - Grep
    - Glob
"""

    @staticmethod
    def _generate_weight_matrix_yaml(domain_config: DomainConfig) -> str:
        """Generate weight matrix YAML file."""
        lines = [
            "# Expert Weight Matrix",
            "# Auto-generated from domains.md",
            "",
            "expert_count:",
            f"  count: {len(domain_config.domains)}",
            "",
            "domain_count:",
            f"  count: {len(domain_config.domains)}",
            "",
            "weight_formula:",
            "  primary: 0.51",
            "  other: 0.49 / (expert_count - 1)",
            "",
            "weights:",
        ]

        for expert_id in domain_config.get_expert_ids():
            lines.append(f"  {expert_id}:")
            for domain_name in domain_config.get_domain_names():
                weight = domain_config.weight_matrix.get_expert_weight(
                    expert_id, domain_name
                )
                marker = "  # PRIMARY" if weight >= 0.51 else ""
                lines.append(f"    {domain_name}: {weight:.3f}{marker}")

        lines.append("")
        lines.append("validation:")
        lines.append("  each_column_sum: 1.00")
        lines.append("  each_domain_has_primary: true")
        lines.append("  primary_weight_minimum: 0.51")

        return "\n".join(lines)
