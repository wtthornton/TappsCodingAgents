"""Expert synthesizer for auto-creating project experts."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExpertSynthesizer:
    """Automatically creates/updates project experts."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.domains_file = project_root / ".tapps-agents" / "domains.md"
        self.experts_file = project_root / ".tapps-agents" / "experts.yaml"
        self.knowledge_base = project_root / ".tapps-agents" / "knowledge"

    def synthesize_from_domains(self, domains: list[str]) -> None:
        """Create experts from detected domains."""
        # Create domains.md
        self.domains_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.domains_file, "w", encoding="utf-8") as f:
            f.write("# Project Domains\n\n")
            for domain in domains:
                f.write(f"- {domain}\n")
        
        # Create experts.yaml
        import yaml
        experts_config = {
            "experts": [
                {"id": f"expert-{domain}", "domain": domain, "type": "project"}
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
