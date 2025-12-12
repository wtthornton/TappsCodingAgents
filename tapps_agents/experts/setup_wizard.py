"""
Interactive Expert Setup Wizard

Helps developers initialize, add, remove, and configure experts with RAG support.
"""

import sys
from pathlib import Path
from typing import Any

import yaml

from .domain_config import DomainConfigParser
from .expert_config import load_expert_configs


class ExpertSetupWizard:
    """Interactive wizard for setting up experts."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / ".tapps-agents"
        self.experts_file = self.config_dir / "experts.yaml"
        self.domains_file = self.config_dir / "domains.md"
        self.knowledge_base_dir = self.config_dir / "knowledge"

    def _prompt(
        self,
        question: str,
        default: str | None = None,
        choices: list[str] | None = None,
    ) -> str:
        """Prompt user for input."""
        prompt_text = question
        if default:
            prompt_text += f" [{default}]"
        if choices:
            prompt_text += f" ({'/'.join(choices)})"
        prompt_text += ": "

        while True:
            try:
                response = input(prompt_text).strip()
                if not response and default:
                    return default
                if not response:
                    print("Please provide a value.")
                    continue
                if choices and response not in choices:
                    print(f"Please choose one of: {', '.join(choices)}")
                    continue
                return response
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.")
                sys.exit(0)

    def _prompt_yes_no(self, question: str, default: bool = True) -> bool:
        """Prompt for yes/no answer."""
        default_str = "Y/n" if default else "y/N"
        response = self._prompt(
            f"{question} ({default_str})",
            default="y" if default else "n",
            choices=["y", "n", "yes", "no"],
        )
        return response.lower() in ["y", "yes"]

    def _ensure_config_dir(self):
        """Ensure .tapps-agents directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

    def _load_existing_experts(self) -> list[dict[str, Any]]:
        """Load existing experts from config file."""
        if not self.experts_file.exists():
            return []
        try:
            configs = load_expert_configs(self.experts_file)
            return [config.model_dump() for config in configs]
        except Exception as e:
            print(f"Warning: Could not load existing experts: {e}")
            return []

    def _save_experts(self, experts: list[dict[str, Any]]):
        """Save experts to YAML file."""
        self._ensure_config_dir()

        # Write YAML with comments
        with open(self.experts_file, "w", encoding="utf-8") as f:
            f.write("# TappsCodingAgents Industry Experts Configuration\n")
            f.write("# .tapps-agents/experts.yaml\n\n")
            yaml.dump(
                {"experts": experts},
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        print(f"\nExperts saved to: {self.experts_file}")

    def _get_domains(self) -> list[str]:
        """Get list of domains from domains.md."""
        if not self.domains_file.exists():
            return []
        try:
            domain_config = DomainConfigParser.parse(self.domains_file)
            return [domain.name for domain in domain_config.domains]
        except (OSError, yaml.YAMLError, KeyError) as e:
            # File read errors, YAML parsing errors, or missing keys
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to load expert configs: {e}")
            return []

    def _setup_rag_knowledge_base(self, domain: str, expert_name: str):
        """Help set up RAG knowledge base for an expert."""
        domain_kb_dir = self.knowledge_base_dir / domain

        print(f"\nSetting up knowledge base for {expert_name}...")

        if not self._prompt_yes_no(
            f"Enable RAG (knowledge base) for {expert_name}?", default=True
        ):
            return False

        domain_kb_dir.mkdir(parents=True, exist_ok=True)

        # Check if knowledge files already exist
        existing_files = list(domain_kb_dir.glob("*.md"))
        if existing_files:
            print(f"\nFound {len(existing_files)} existing knowledge file(s):")
            for f in existing_files:
                print(f"  - {f.name}")
            if not self._prompt_yes_no("Add more knowledge files?", default=False):
                return True

        # Offer to create a template knowledge file
        if self._prompt_yes_no("Create a template knowledge file?", default=True):
            template_file = domain_kb_dir / f"{domain}-knowledge.md"
            template_content = f"""# {expert_name} Knowledge Base

## Domain: {domain}

Add your domain-specific knowledge here. This file will be used for RAG (Retrieval-Augmented Generation).

### Key Concepts

### Best Practices

### Common Patterns

### References

"""
            template_file.write_text(template_content, encoding="utf-8")
            print(f"Created template: {template_file}")
            print("\nTip: Edit this file to add your domain knowledge.")

        return True

    def add_expert(self):
        """Interactive wizard to add a new expert."""
        print("\n" + "=" * 60)
        print("Add New Expert")
        print("=" * 60)

        # Get expert details
        expert_name = self._prompt("Expert name (e.g., 'Home Automation Expert')")

        # Generate expert_id from name
        expert_id_suggestion = f"expert-{expert_name.lower().replace(' ', '-').replace('&', '').replace(',', '')}"
        expert_id = self._prompt("Expert ID", default=expert_id_suggestion)

        # Get domain
        domains = self._get_domains()
        if domains:
            print("\nAvailable domains:")
            for i, domain in enumerate(domains, 1):
                print(f"  {i}. {domain}")

            use_existing = self._prompt_yes_no("\nUse existing domain?", default=True)
            if use_existing:
                domain_choice = self._prompt(
                    "Domain number or name",
                    choices=domains + [str(i) for i in range(1, len(domains) + 1)],
                )
                if domain_choice.isdigit():
                    primary_domain = domains[int(domain_choice) - 1]
                else:
                    primary_domain = domain_choice
            else:
                primary_domain = self._prompt("Primary domain name")
        else:
            print("\n⚠️  No domains found in domains.md")
            if self._prompt_yes_no("Create domain entry later?", default=True):
                primary_domain = self._prompt(
                    "Primary domain name (will need to match domains.md)"
                )
            else:
                print("Please create .tapps-agents/domains.md first.")
                return

        # RAG setup
        rag_enabled = self._setup_rag_knowledge_base(primary_domain, expert_name)

        # Create expert config
        expert_config = {
            "expert_id": expert_id,
            "expert_name": expert_name,
            "primary_domain": primary_domain,
            "rag_enabled": rag_enabled,
            "fine_tuned": False,
        }

        # Load existing experts
        experts = self._load_existing_experts()

        # Check for duplicates
        if any(e.get("expert_id") == expert_id for e in experts):
            if not self._prompt_yes_no(
                f"Expert '{expert_id}' already exists. Replace?", default=False
            ):
                print("Cancelled.")
                return
            experts = [e for e in experts if e.get("expert_id") != expert_id]

        # Add new expert
        experts.append(expert_config)

        # Save
        self._save_experts(experts)

        print(f"\nExpert '{expert_name}' added successfully!")
        print(f"   Expert ID: {expert_id}")
        print(f"   Domain: {primary_domain}")
        print(f"   RAG Enabled: {rag_enabled}")

    def remove_expert(self):
        """Interactive wizard to remove an expert."""
        print("\n" + "=" * 60)
        print("Remove Expert")
        print("=" * 60)

        experts = self._load_existing_experts()

        if not experts:
            print("No experts found.")
            return

        print("\nCurrent experts:")
        for i, expert in enumerate(experts, 1):
            print(f"  {i}. {expert.get('expert_name')} ({expert.get('expert_id')})")

        choice = self._prompt("\nExpert number to remove")

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(experts):
                expert = experts[idx]
                if self._prompt_yes_no(
                    f"Remove '{expert.get('expert_name')}'?", default=False
                ):
                    experts.pop(idx)
                    self._save_experts(experts)
                    print(f"Expert '{expert.get('expert_name')}' removed.")
                else:
                    print("Cancelled.")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid selection.")

    def list_experts(self):
        """List all configured experts."""
        print("\n" + "=" * 60)
        print("Current Experts")
        print("=" * 60)

        experts = self._load_existing_experts()

        if not experts:
            print("No experts configured.")
            print("\nRun 'setup-experts add' to add your first expert.")
            return

        for i, expert in enumerate(experts, 1):
            print(f"\n{i}. {expert.get('expert_name')}")
            print(f"   ID: {expert.get('expert_id')}")
            print(f"   Domain: {expert.get('primary_domain')}")
            print(f"   RAG: {'Yes' if expert.get('rag_enabled') else 'No'}")

            # Check knowledge base
            domain = expert.get("primary_domain")
            if expert.get("rag_enabled") and domain:
                kb_dir = self.knowledge_base_dir / domain
                kb_files = list(kb_dir.glob("*.md")) if kb_dir.exists() else []
                print(f"   Knowledge Files: {len(kb_files)}")

    def init_project(self):
        """Initialize a new project with expert setup."""
        print("\n" + "=" * 60)
        print("Initialize TappsCodingAgents Project")
        print("=" * 60)

        print("\nThis wizard will help you set up experts for your project.")

        if not self._prompt_yes_no("Continue?", default=True):
            return

        self._ensure_config_dir()

        # Initialize Cursor Rules and workflow presets
        from ..core.init_project import init_project as init_project_setup

        if self._prompt_yes_no(
            "\nInitialize Cursor Rules and workflow presets?", default=True
        ):
            print("\nSetting up Cursor Rules and workflow presets...")
            init_results = init_project_setup(
                project_root=self.project_root,
                include_cursor_rules=True,
                include_workflow_presets=True,
            )

            if init_results["cursor_rules"]:
                print("  Created Cursor Rules: .cursor/rules/workflow-presets.mdc")
            if init_results["workflow_presets"]:
                print(
                    f"  Created {len(init_results['files_created'])} workflow preset(s)"
                )

        # Check for domains.md
        if not self.domains_file.exists():
            print("\nWarning: No domains.md found.")
            if self._prompt_yes_no("Create domains.md template?", default=True):
                self._create_domains_template()

        # Add first expert
        if self._prompt_yes_no("\nAdd your first expert?", default=True):
            self.add_expert()

        # Offer to add more
        while self._prompt_yes_no("\nAdd another expert?", default=False):
            self.add_expert()

        print("\n" + "=" * 60)
        print("Project initialization complete!")
        print("=" * 60)
        self.list_experts()

        print("\nQuick Commands Available:")
        print("  python -m tapps_agents.cli workflow list")
        print("  python -m tapps_agents.cli workflow rapid")
        print("  python -m tapps_agents.cli workflow full")

    def _create_domains_template(self):
        """Create a template domains.md file."""
        template = """# Project Domains

This file defines the business domains for your project and their primary experts.

## Project: Your Project Name

Brief description of your project.

### Domain 1: [Domain Name]

- **Primary Expert**: expert-[domain-name]
- **Description**: [Domain description]
- **Key Areas**: [Key areas covered by this domain]

"""
        self.domains_file.write_text(template, encoding="utf-8")
        print(f"Created template: {self.domains_file}")
        print("Tip: Edit this file to define your project's domains.")

    def run_wizard(self):
        """Run the main wizard menu."""
        print("\n" + "=" * 60)
        print("Expert Setup Wizard")
        print("=" * 60)
        print("\nWhat would you like to do?")
        print("  1. Initialize project (first-time setup)")
        print("  2. Add expert")
        print("  3. Remove expert")
        print("  4. List experts")
        print("  5. Exit")

        choice = self._prompt("\nChoice", choices=["1", "2", "3", "4", "5"])

        if choice == "1":
            self.init_project()
        elif choice == "2":
            self.add_expert()
        elif choice == "3":
            self.remove_expert()
        elif choice == "4":
            self.list_experts()
        else:
            print("Goodbye!")
