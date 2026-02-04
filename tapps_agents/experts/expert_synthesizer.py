"""Expert synthesizer for auto-creating project experts."""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class ExpertSynthesizer:
    """Automatically creates/updates project experts."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.domains_file = project_root / ".tapps-agents" / "domains.md"
        self.experts_file = project_root / ".tapps-agents" / "experts.yaml"
        self.knowledge_base = project_root / ".tapps-agents" / "knowledge"

    def _generate_expert_name(self, domain: str) -> str:
        """
        Generate a human-readable expert name from a domain name.
        
        Examples:
            "python" -> "Python Expert"
            "home-automation" -> "Home Automation Expert"
            "health_care" -> "Health Care Expert"
        """
        # Replace hyphens and underscores with spaces
        name = domain.replace("-", " ").replace("_", " ")
        # Capitalize each word
        name = " ".join(word.capitalize() for word in name.split())
        return f"{name} Expert"

    def synthesize_from_domains(self, domains: list[str]) -> None:
        """Create experts from detected domains."""
        # Create domains.md
        self.domains_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.domains_file, "w", encoding="utf-8") as f:
            f.write("# Project Domains\n\n")
            for domain in domains:
                f.write(f"- {domain}\n")
        
        # Create experts.yaml with correct format
        experts_config = {
            "experts": [
                {
                    "expert_id": f"expert-{domain}",
                    "expert_name": self._generate_expert_name(domain),
                    "primary_domain": domain,
                    "rag_enabled": False,
                    "fine_tuned": False,
                }
                for domain in domains
            ]
        }
        with open(self.experts_file, "w", encoding="utf-8") as f:
            yaml.dump(experts_config, f)
        
        # Create knowledge skeletons
        for domain in domains:
            domain_dir = self.knowledge_base / domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            
            for file_name in ["overview.md", "glossary.md", "decisions.md", "pitfalls.md", "constraints.md"]:
                file_path = domain_dir / file_name
                if not file_path.exists():
                    file_path.write_text(f"# {file_name.replace('.md', '').title()}\n\n", encoding="utf-8")
