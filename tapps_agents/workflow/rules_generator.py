"""
Cursor Rules Generator - Generate workflow documentation from YAML definitions.
"""

import logging
from pathlib import Path
from typing import Any

from .models import Workflow
from .parser import WorkflowParser

logger = logging.getLogger(__name__)


class CursorRulesGenerator:
    """Generate Cursor Rules documentation from workflow YAML files."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize the rules generator.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root

    def find_workflow_files(self) -> list[tuple[Path, str | None]]:
        """
        Find all workflow YAML files in preset directories.

        Returns:
            List of tuples (file_path, resource_name) where resource_name is None for regular files
        """
        workflow_files: list[tuple[Path, str | None]] = []

        # Check project workflows/presets first
        project_presets = self.project_root / "workflows" / "presets"
        if project_presets.exists():
            for yaml_file in project_presets.glob("*.yaml"):
                workflow_files.append((yaml_file, None))

        # Check framework resources if project presets not found
        if not workflow_files:
            try:
                from importlib import resources as importlib_resources

                resource_path = importlib_resources.files("tapps_agents.resources.workflows.presets")
                if resource_path.is_dir():
                    for entry in resource_path.iterdir():
                        if entry.name.endswith(".yaml") and not entry.is_dir():
                            # Store as resource name for later reading
                            workflow_files.append((Path(entry.name), entry.name))
            except (ImportError, Exception) as e:
                logger.debug(f"Could not load workflow files from resources: {e}")

        return sorted(workflow_files, key=lambda x: x[0].name)

    def extract_quality_gates(self, workflow: Workflow) -> dict[str, Any]:
        """
        Extract quality gate thresholds from workflow steps.

        Args:
            workflow: Parsed Workflow object

        Returns:
            Dictionary with quality gate information
        """
        gates: dict[str, Any] = {}

        for step in workflow.steps:
            if step.scoring and isinstance(step.scoring, dict):
                thresholds = step.scoring.get("thresholds", {})
                if thresholds:
                    if "overall_min" in thresholds:
                        gates["overall"] = thresholds["overall_min"]
                    if "security_min" in thresholds:
                        gates["security"] = thresholds["security_min"]
                    if "maintainability_min" in thresholds:
                        gates["maintainability"] = thresholds["maintainability_min"]

        return gates

    def get_workflow_aliases(self, workflow_id: str) -> list[str]:
        """
        Get command aliases for a workflow ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of aliases
        """
        alias_map: dict[str, list[str]] = {
            "full-sdlc": ["full", "enterprise"],
            "rapid-dev": ["rapid", "feature"],
            "fix": ["fix", "maintenance", "hotfix", "urgent", "refactor", "quick-fix"],
            "quality": ["quality", "improve"],
            "brownfield-analysis": ["brownfield"],
        }
        return alias_map.get(workflow_id, [])

    def generate(self, output_path: Path | None = None) -> str:
        """
        Generate Cursor Rules markdown from workflow YAML files.

        Args:
            output_path: Output file path (unused, kept for API compatibility)

        Returns:
            Generated markdown content

        Raises:
            ValueError: If no workflows are found or all workflows fail to parse
        """
        # Find workflow files
        workflow_files = self.find_workflow_files()
        if not workflow_files:
            logger.warning("No workflow YAML files found")
            raise ValueError(
                "No workflow YAML files found. "
                "Ensure workflows exist in workflows/presets/ or framework resources."
            )

        # Parse workflows
        workflows: list[Workflow] = []
        parse_errors: list[str] = []
        
        for workflow_file, resource_name in workflow_files:
            try:
                if resource_name:
                    # Handle resource paths (from importlib.resources)
                    try:
                        from importlib import resources as importlib_resources

                        resource = importlib_resources.files("tapps_agents.resources.workflows.presets")
                        content_file = resource / resource_name
                        if content_file.exists():
                            content = content_file.read_text(encoding="utf-8")
                            import yaml

                            yaml_content = yaml.safe_load(content)
                            workflow = WorkflowParser.parse(yaml_content, file_path=workflow_file)
                            workflows.append(workflow)
                        else:
                            parse_errors.append(f"Resource file not found: {resource_name}")
                    except Exception as e:
                        error_msg = f"Could not parse resource workflow {workflow_file}: {e}"
                        logger.debug(error_msg)
                        parse_errors.append(error_msg)
                else:
                    # Regular file path
                    workflow = WorkflowParser.parse_file(workflow_file)
                    workflows.append(workflow)
            except Exception as e:
                error_msg = f"Could not parse workflow {workflow_file}: {e}"
                logger.warning(error_msg)
                parse_errors.append(error_msg)

        if not workflows:
            error_message = "No valid workflows found"
            if parse_errors:
                error_message += f". Parse errors: {'; '.join(parse_errors[:3])}"
            logger.error(error_message)
            raise ValueError(error_message)

        # Sort workflows by a consistent order (5 presets)
        workflow_order = ["full-sdlc", "rapid-dev", "fix", "quality", "brownfield-analysis"]
        workflows.sort(key=lambda w: (
            workflow_order.index(w.id) if w.id in workflow_order else 999,
            w.id
        ))

        # Generate markdown
        lines: list[str] = []
        lines.append("# Workflow Presets - Quick Commands")
        lines.append("")
        lines.append("## Overview")
        lines.append("")
        lines.append(
            "TappsCodingAgents provides preset workflows that can be executed with simple one-word commands. "
            "These workflows automatically orchestrate multiple agents to complete common SDLC tasks."
        )
        lines.append("")
        lines.append("## Available Workflow Presets")
        lines.append("")

        # Generate sections for each workflow
        for i, workflow in enumerate(workflows, 1):
            lines.append(f"### {i}. {workflow.name}")
            aliases = self.get_workflow_aliases(workflow.id)
            if aliases:
                alias_text = f" (`{'` / `'.join(aliases)}`)"
                lines[-1] += alias_text
            lines.append("")
            lines.append(f"**Command:** `python -m tapps_agents.cli workflow {aliases[0] if aliases else workflow.id}`")
            lines.append("")
            if workflow.description:
                lines.append(f"**Best for:** {workflow.description}")
                lines.append("")
            lines.append("**Agent Sequence:**")
            for j, step in enumerate(workflow.steps, 1):
                agent_name = step.agent.title()
                action_desc = step.action.replace("_", " ").title()
                lines.append(f"{j}. {agent_name} - {action_desc}")
            lines.append("")
            gates = self.extract_quality_gates(workflow)
            if gates:
                lines.append("**Quality Gates:**")
                if "overall" in gates:
                    lines.append(f"- Overall score: ≥{gates['overall']}")
                if "security" in gates:
                    lines.append(f"- Security: ≥{gates['security']}")
                if "maintainability" in gates:
                    lines.append(f"- Maintainability: ≥{gates['maintainability']}")
                lines.append("")

        # Add usage section
        lines.append("## Usage in Cursor AI")
        lines.append("")
        lines.append("When working in Cursor AI, you can:")
        lines.append("")
        lines.append("1. **Run workflows directly:**")
        lines.append("   - Type: \"Run rapid development workflow\"")
        lines.append("   - Or: \"Execute full SDLC pipeline\"")
        lines.append("   - Or: \"Start quality improvement\"")
        lines.append("")
        lines.append("2. **Use voice commands:**")
        lines.append("   - \"run rapid dev\"")
        lines.append("   - \"execute enterprise workflow\"")
        lines.append("   - \"start quick fix\"")
        lines.append("")
        lines.append("3. **Reference in conversations:**")
        lines.append("   - \"Use the rapid workflow for this feature\"")
        lines.append("   - \"This needs the full enterprise workflow\"")
        lines.append("   - \"Run the quality improvement cycle\"")
        lines.append("")

        # Add when to use section
        lines.append("## When to Use Each Workflow")
        lines.append("")
        for workflow in workflows:
            aliases = self.get_workflow_aliases(workflow.id)
            primary_alias = aliases[0] if aliases else workflow.id
            if workflow.description:
                # Extract use case from description
                use_case = workflow.description.split(".")[0] if "." in workflow.description else workflow.description
                lines.append(f"- **{use_case}** → `workflow {primary_alias}`")
        lines.append("")

        # Add integration section
        lines.append("## Integration")
        lines.append("")
        lines.append("These workflows integrate with:")
        lines.append("- ✅ Expert consultation (domain experts)")
        lines.append("- ✅ Quality gates (scoring thresholds)")
        lines.append("- ✅ Context tiers (token optimization)")
        lines.append("- ✅ Multi-agent orchestration")
        lines.append("- ✅ Git worktree isolation")
        lines.append("")

        # Add list command
        lines.append("## List All Presets")
        lines.append("")
        lines.append("```bash")
        lines.append("python -m tapps_agents.cli workflow list")
        lines.append("```")
        lines.append("")

        # Add customization section
        lines.append("## Customization")
        lines.append("")
        lines.append("Workflow presets are defined in `workflows/presets/`:")
        for workflow in workflows:
            lines.append(f"- `{workflow.id}.yaml`")
        lines.append("")
        lines.append("You can modify these files or create your own presets.")
        lines.append("")

        content = "\n".join(lines)
        return content

    def write(self, output_path: Path | None = None, backup: bool = True) -> Path:
        """
        Generate and write Cursor Rules markdown to file.

        Args:
            output_path: Output file path (defaults to .cursor/rules/workflow-presets.mdc)
            backup: Whether to backup existing file

        Returns:
            Path to written file
        """
        if output_path is None:
            output_path = self.project_root / ".cursor" / "rules" / "workflow-presets.mdc"

        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file
        if backup and output_path.exists():
            backup_path = output_path.with_suffix(".mdc.backup")
            try:
                import shutil

                shutil.copy2(output_path, backup_path)
                logger.debug(f"Backed up existing rules to {backup_path}")
            except Exception as e:
                logger.warning(f"Could not backup existing rules: {e}")

        # Generate content
        try:
            content = self.generate()
        except ValueError as e:
            msg = str(e)
            if "No workflow YAML files found" in msg:
                logger.warning(
                    "Could not generate workflow-presets.mdc (no YAML found). %s", msg
                )
            else:
                logger.error(f"Failed to generate rules: {e}")
            raise

        if not content or not content.strip():
            raise ValueError("Generated content is empty")

        # Write file
        try:
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"Generated Cursor Rules at {output_path}")
        except OSError as e:
            logger.error(f"Failed to write rules file: {e}")
            raise

        return output_path

