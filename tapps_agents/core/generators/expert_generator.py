"""Expert Generator for TappsCodingAgents.

This module auto-generates experts from knowledge files using LLM analysis.
Scans .tapps-agents/kb/ directory, analyzes markdown files, and generates
expert configurations following expert-{domain}-{topic} naming convention.

Module: Phase 3.1 - Expert Generator
From: docs/INIT_AUTOFILL_DETAILED_REQUIREMENTS.md
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class KnowledgeFileAnalysis:
    """Analysis result from knowledge file."""
    filepath: Path
    domain: str
    topic: str
    description: str
    consultation_triggers: list[str] = field(default_factory=list)
    priority: float = 0.80
    concepts: list[str] = field(default_factory=list)


@dataclass
class ExpertConfig:
    """Expert configuration for experts.yaml."""
    expert_id: str
    expert_name: str
    primary_domain: str
    rag_enabled: bool = True
    fine_tuned: bool = False
    knowledge_files: list[str] = field(default_factory=list)
    consultation_triggers: list[str] = field(default_factory=list)
    priority: float = 0.80


class ExpertGenerator:
    """Generates experts from knowledge files using analysis.

    This generator:
    - Scans .tapps-agents/knowledge/ for markdown files
    - Analyzes content to extract domain, triggers, and concepts
    - Generates expert configurations following naming conventions
    - Adds experts to experts.yaml with optional confirmation

    Performance target: < 10 seconds per knowledge file
    """

    def __init__(
        self,
        project_root: Path | None = None,
        knowledge_base_dir: Path | None = None,
        experts_yaml_path: Path | None = None,
    ):
        """Initialize expert generator.

        Args:
            project_root: Root directory of project (defaults to current directory)
            knowledge_base_dir: Knowledge base directory (defaults to .tapps-agents/knowledge)
            experts_yaml_path: Path to experts.yaml (defaults to .tapps-agents/experts.yaml)
        """
        self.project_root = project_root or Path.cwd()
        self.knowledge_base_dir = knowledge_base_dir or (
            self.project_root / ".tapps-agents" / "knowledge"
        )
        self.experts_yaml_path = experts_yaml_path or (
            self.project_root / ".tapps-agents" / "experts.yaml"
        )

    def analyze_knowledge_file(self, filepath: Path) -> KnowledgeFileAnalysis:
        """Extract domain, triggers, and concepts from knowledge file.

        Args:
            filepath: Path to knowledge file

        Returns:
            KnowledgeFileAnalysis with extracted information
        """
        # Read file content
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Failed to read {filepath}: {e}")

        # Extract domain from directory structure
        # E.g., .tapps-agents/knowledge/testing/testing-guide.md -> domain: testing
        relative_path = filepath.relative_to(self.knowledge_base_dir)
        domain_parts = list(relative_path.parts[:-1])  # All parts except filename
        domain = domain_parts[0] if domain_parts else "general"

        # Extract topic from filename
        # E.g., testing-guide.md -> topic: testing-guide
        topic = filepath.stem

        # Extract description from first heading or first paragraph
        description = self._extract_description(content)

        # Extract consultation triggers from content keywords
        consultation_triggers = self._extract_triggers(content, domain, topic)

        # Extract key concepts
        concepts = self._extract_concepts(content)

        # Calculate priority based on file characteristics
        priority = self._calculate_priority(content, domain)

        return KnowledgeFileAnalysis(
            filepath=filepath,
            domain=domain,
            topic=topic,
            description=description,
            consultation_triggers=consultation_triggers,
            priority=priority,
            concepts=concepts,
        )

    def check_expert_exists(self, domain: str) -> dict | None:
        """Check if expert covering domain already exists.

        Args:
            domain: Domain to check

        Returns:
            Expert configuration if exists, None otherwise
        """
        if not self.experts_yaml_path.exists():
            return None

        try:
            with open(self.experts_yaml_path, encoding="utf-8") as f:
                experts_data = yaml.safe_load(f) or {}
        except Exception:
            return None

        experts = experts_data.get("experts", [])

        # Check for exact domain match
        for expert in experts:
            primary_domain = expert.get("primary_domain", "")
            if primary_domain == domain:
                return expert

            # Check if expert_id contains domain
            expert_id = expert.get("expert_id", "")
            if domain in expert_id:
                return expert

        return None

    def generate_expert_config(self, analysis: KnowledgeFileAnalysis) -> ExpertConfig:
        """Generate expert configuration from analysis.

        Args:
            analysis: Knowledge file analysis

        Returns:
            ExpertConfig ready for experts.yaml
        """
        # Generate expert_id following convention: expert-{domain}-{topic}
        expert_id = f"expert-{analysis.domain}-{analysis.topic}"

        # Generate expert_name from domain and topic
        domain_title = analysis.domain.replace("-", " ").replace("_", " ").title()
        topic_title = analysis.topic.replace("-", " ").replace("_", " ").title()
        expert_name = f"{domain_title} - {topic_title} Expert"

        # Get relative path for knowledge_files
        relative_path = str(analysis.filepath.relative_to(self.project_root))

        return ExpertConfig(
            expert_id=expert_id,
            expert_name=expert_name,
            primary_domain=analysis.domain,
            rag_enabled=True,
            fine_tuned=False,
            knowledge_files=[relative_path],
            consultation_triggers=analysis.consultation_triggers,
            priority=analysis.priority,
        )

    def add_expert_to_yaml(
        self,
        config: ExpertConfig,
        confirm: bool = True,
        auto_mode: bool = False,
    ) -> bool:
        """Add expert to experts.yaml with optional confirmation.

        Args:
            config: Expert configuration to add
            confirm: Whether to prompt for confirmation
            auto_mode: Automatic mode (skip confirmation)

        Returns:
            True if expert was added, False otherwise
        """
        # Load existing experts
        if self.experts_yaml_path.exists():
            try:
                with open(self.experts_yaml_path, encoding="utf-8") as f:
                    experts_data = yaml.safe_load(f) or {}
            except Exception as e:
                raise ValueError(f"Failed to load {self.experts_yaml_path}: {e}")
        else:
            experts_data = {"experts": []}

        # Check if expert already exists
        experts = experts_data.get("experts", [])
        for expert in experts:
            if expert.get("expert_id") == config.expert_id:
                return False  # Expert already exists

        # Confirmation prompt (unless auto_mode)
        if confirm and not auto_mode:
            print("\n[EXPERT GENERATOR] Propose adding expert:")
            print(f"  ID: {config.expert_id}")
            print(f"  Name: {config.expert_name}")
            print(f"  Domain: {config.primary_domain}")
            print(f"  Priority: {config.priority:.2f}")
            print(f"  Knowledge Files: {len(config.knowledge_files)}")
            print(f"  Triggers: {', '.join(config.consultation_triggers[:3])}")

            response = input("\nAdd this expert to experts.yaml? [y/N]: ").strip().lower()
            if response not in ["y", "yes"]:
                return False

        # Add expert to YAML
        expert_dict = {
            "expert_id": config.expert_id,
            "expert_name": config.expert_name,
            "primary_domain": config.primary_domain,
            "rag_enabled": config.rag_enabled,
            "fine_tuned": config.fine_tuned,
        }

        # Add optional fields if present
        if config.knowledge_files:
            expert_dict["knowledge_files"] = config.knowledge_files
        if config.consultation_triggers:
            expert_dict["consultation_triggers"] = config.consultation_triggers
        if hasattr(config, "priority") and config.priority != 0.80:
            expert_dict["priority"] = config.priority

        experts.append(expert_dict)
        experts_data["experts"] = experts

        # Write back to file
        try:
            with open(self.experts_yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    experts_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            return True
        except Exception as e:
            raise ValueError(f"Failed to write {self.experts_yaml_path}: {e}")

    def scan_and_generate(
        self,
        auto_mode: bool = False,
        skip_existing: bool = True,
    ) -> dict:
        """Scan knowledge base and generate experts.

        Args:
            auto_mode: Automatic mode (no confirmation prompts)
            skip_existing: Skip files with existing experts

        Returns:
            Dictionary with generation results
        """
        if not self.knowledge_base_dir.exists():
            return {
                "success": False,
                "error": f"Knowledge base directory not found: {self.knowledge_base_dir}",
            }

        # Find all markdown files
        markdown_files = list(self.knowledge_base_dir.glob("**/*.md"))

        # Filter out README files
        markdown_files = [f for f in markdown_files if f.name.lower() != "readme.md"]

        generated = []
        skipped = []
        errors = []

        for filepath in markdown_files:
            try:
                # Analyze file
                analysis = self.analyze_knowledge_file(filepath)

                # Check if expert exists
                if skip_existing:
                    existing = self.check_expert_exists(analysis.domain)
                    if existing:
                        skipped.append(
                            {
                                "file": str(filepath.relative_to(self.project_root)),
                                "reason": f"Expert exists: {existing.get('expert_id')}",
                            }
                        )
                        continue

                # Generate config
                config = self.generate_expert_config(analysis)

                # Add to YAML
                success = self.add_expert_to_yaml(
                    config, confirm=not auto_mode, auto_mode=auto_mode
                )

                if success:
                    generated.append(
                        {
                            "file": str(filepath.relative_to(self.project_root)),
                            "expert_id": config.expert_id,
                            "domain": config.primary_domain,
                        }
                    )
                else:
                    skipped.append(
                        {
                            "file": str(filepath.relative_to(self.project_root)),
                            "reason": "User declined or already exists",
                        }
                    )

            except Exception as e:
                errors.append(
                    {
                        "file": str(filepath.relative_to(self.project_root)),
                        "error": str(e),
                    }
                )

        return {
            "success": True,
            "total_files": len(markdown_files),
            "generated": len(generated),
            "skipped": len(skipped),
            "errors": len(errors),
            "generated_experts": generated,
            "skipped_files": skipped,
            "error_details": errors,
        }

    # Private helper methods

    def _extract_description(self, content: str) -> str:
        """Extract description from content (first heading or paragraph)."""
        lines = content.split("\n")

        # Try to find first heading
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                # Remove markdown heading syntax
                desc = re.sub(r"^#+\s*", "", line).strip()
                if desc:
                    return desc

        # Fallback: first non-empty paragraph
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("**"):
                # Limit to first 200 characters
                return line[:200]

        return "Knowledge base content"

    def _extract_triggers(self, content: str, domain: str, topic: str) -> list[str]:
        """Extract consultation triggers from content keywords."""
        triggers = set()

        # Add domain and topic as triggers
        triggers.add(domain)
        triggers.add(topic)

        # Extract keywords from headings
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                # Extract words from heading
                heading = re.sub(r"^#+\s*", "", line).lower()
                # Split on common separators
                words = re.findall(r"\b[a-z][a-z0-9-]+\b", heading)
                for word in words:
                    if len(word) > 3 and word not in ["the", "and", "for", "with"]:
                        triggers.add(word)

        # Limit to 10 most relevant triggers
        return list(triggers)[:10]

    def _extract_concepts(self, content: str) -> list[str]:
        """Extract key concepts from content."""
        concepts = set()

        # Extract from headings
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("##"):  # Level 2 headings
                concept = re.sub(r"^#+\s*", "", line).strip()
                if concept:
                    concepts.add(concept)

        return list(concepts)[:10]

    def _calculate_priority(self, content: str, domain: str) -> float:
        """Calculate priority based on file characteristics (0.70-0.90)."""
        priority = 0.80  # Default

        # Increase for longer, more detailed files
        word_count = len(content.split())
        if word_count > 1000:
            priority += 0.05
        elif word_count > 500:
            priority += 0.03

        # Increase for certain high-priority domains
        high_priority_domains = {"testing", "quality", "security", "architecture"}
        if domain in high_priority_domains:
            priority += 0.05

        # Cap at 0.90
        return min(priority, 0.90)


def main() -> None:
    """CLI entry point for expert generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate experts from knowledge files")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatic mode (no confirmation prompts)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Generate even if experts exist (don't skip)",
    )
    args = parser.parse_args()

    # Initialize generator
    generator = ExpertGenerator(project_root=args.project_root)

    print("[EXPERT GENERATOR] Scanning knowledge base...")
    result = generator.scan_and_generate(
        auto_mode=args.auto,
        skip_existing=not args.force,
    )

    if result["success"]:
        print("\n[OK] Expert generation complete!")
        print(f"  Total Files: {result['total_files']}")
        print(f"  Generated: {result['generated']}")
        print(f"  Skipped: {result['skipped']}")
        print(f"  Errors: {result['errors']}")

        if result["generated_experts"]:
            print("\n[GENERATED EXPERTS]:")
            for expert in result["generated_experts"]:
                print(f"  - {expert['expert_id']} ({expert['domain']})")
    else:
        print(f"\n[ERROR] {result['error']}")


if __name__ == "__main__":
    main()
