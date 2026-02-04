"""
Workflow Documentation Manager - Organizes documentation by workflow ID.

Manages workflow-specific documentation directories and file paths.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


class DocumentationError(Exception):
    """Exception raised for documentation operation errors."""

    pass


class WorkflowDocumentationManager:
    """Manages workflow-specific documentation organization."""

    def __init__(
        self,
        base_dir: Path,
        workflow_id: str,
        create_symlink: bool = False,
    ):
        """
        Initialize documentation manager.

        Args:
            base_dir: Base directory for documentation (e.g., docs/workflows/simple-mode/)
            workflow_id: Workflow identifier
            create_symlink: Create 'latest' symlink to this workflow
        """
        self.base_dir = Path(base_dir)
        self.workflow_id = workflow_id
        self.create_symlink = create_symlink
        self._doc_dir: Path | None = None

    @staticmethod
    def generate_workflow_id(base_name: str = "build") -> str:
        """
        Generate unique workflow ID.

        Args:
            base_name: Base name for workflow ID

        Returns:
            Workflow ID in format: {base_name}-{timestamp}
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{base_name}-{timestamp}"

    def get_documentation_dir(self) -> Path:
        """
        Get workflow-specific documentation directory.

        Returns:
            Path to workflow documentation directory
        """
        if self._doc_dir is None:
            self._doc_dir = self.base_dir / self.workflow_id
        return self._doc_dir

    def get_step_file_path(
        self, step_number: int, step_name: str | None = None
    ) -> Path:
        """
        Get file path for step documentation.

        Args:
            step_number: Step number (1-based)
            step_name: Optional step name (e.g., "enhanced-prompt")

        Returns:
            Path to step documentation file
        """
        doc_dir = self.get_documentation_dir()
        if step_name:
            filename = f"step{step_number}-{step_name}.md"
        else:
            filename = f"step{step_number}.md"
        return doc_dir / filename

    def create_directory(self) -> Path:
        """
        Create workflow documentation directory.

        Returns:
            Path to created directory

        Raises:
            DocumentationError: If directory creation fails
        """
        doc_dir = self.get_documentation_dir()
        try:
            doc_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created documentation directory: {doc_dir}")
            return doc_dir
        except OSError as e:
            raise DocumentationError(
                f"Failed to create documentation directory {doc_dir}: {e}"
            ) from e

    def save_step_documentation(
        self,
        step_number: int,
        content: str,
        step_name: str | None = None,
    ) -> Path:
        """
        Save step documentation to workflow directory.

        Args:
            step_number: Step number (1-based)
            content: Documentation content (markdown)
            step_name: Optional step name

        Returns:
            Path to saved file

        Raises:
            DocumentationError: If save fails
        """
        # Ensure directory exists
        self.create_directory()

        # Get file path
        file_path = self.get_step_file_path(step_number, step_name)

        try:
            # Write content with UTF-8 encoding
            file_path.write_text(content, encoding="utf-8")
            logger.debug(f"Saved step documentation: {file_path}")
            return file_path
        except OSError as e:
            raise DocumentationError(
                f"Failed to save documentation to {file_path}: {e}"
            ) from e

    def create_latest_symlink(self) -> Path | None:
        """
        Create 'latest' symlink to this workflow.

        Returns:
            Path to symlink, or None if creation failed
        """
        if not self.create_symlink:
            return None

        symlink_path = self.base_dir / "latest"
        doc_dir = self.get_documentation_dir()

        try:
            # Remove existing symlink if it exists
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()

            # Create symlink (platform-specific)
            import sys

            if sys.platform == "win32":
                # Windows: Use junction or directory symlink
                # For now, create a text file with path (Windows symlinks require admin)
                symlink_path.write_text(
                    f"Latest workflow: {self.workflow_id}\nPath: {doc_dir}",
                    encoding="utf-8",
                )
                logger.debug(f"Created latest pointer file: {symlink_path}")
            else:
                # Unix: Create symlink
                symlink_path.symlink_to(doc_dir)
                logger.debug(f"Created latest symlink: {symlink_path}")

            return symlink_path
        except OSError as e:
            logger.warning(f"Failed to create latest symlink: {e}")
            return None

    def save_step_state(
        self,
        step_number: int,
        state: dict[str, Any],
        content: str,
        step_name: str | None = None,
    ) -> Path:
        """
        Save workflow state with YAML frontmatter and markdown content.

        Args:
            step_number: Step number (1-based)
            state: State dictionary to serialize
            content: Markdown content
            step_name: Optional step name

        Returns:
            Path to saved file

        Raises:
            DocumentationError: If save fails
        """
        if yaml is None:
            logger.warning("PyYAML not available, saving without state frontmatter")
            return self.save_step_documentation(step_number, content, step_name)

        # Ensure directory exists
        self.create_directory()

        # Get file path
        file_path = self.get_step_file_path(step_number, step_name)

        try:
            # Serialize state to YAML
            yaml_frontmatter = yaml.dump(state, default_flow_style=False, allow_unicode=True)

            # Combine YAML frontmatter and markdown content
            # Format: ---\n{yaml}\n---\n\n{markdown}
            full_content = f"---\n{yaml_frontmatter}---\n\n{content}"

            # Write content with UTF-8 encoding
            file_path.write_text(full_content, encoding="utf-8")
            logger.debug(f"Saved step state and documentation: {file_path}")
            return file_path
        except OSError as e:
            raise DocumentationError(
                f"Failed to save state to {file_path}: {e}"
            ) from e
        except Exception as e:
            raise DocumentationError(
                f"Failed to serialize state for step {step_number}: {e}"
            ) from e

    def create_workflow_summary(self) -> Path:
        """
        Create workflow summary file with key information.

        Returns:
            Path to summary file

        Raises:
            DocumentationError: If summary creation fails
        """
        self.create_directory()
        summary_path = self.get_documentation_dir() / "workflow-summary.md"

        try:
            # Collect information
            steps_completed = self._get_completed_steps()
            key_decisions = self._extract_key_decisions()
            artifacts_created = self._list_artifacts()

            # Generate summary markdown
            summary_lines = [
                f"# Workflow Summary: {self.workflow_id}",
                "",
                f"**Workflow ID:** {self.workflow_id}",
                f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Steps Completed",
                "",
            ]

            if steps_completed:
                for step_num in steps_completed:
                    summary_lines.append(f"- Step {step_num}")
            else:
                summary_lines.append("- No steps completed yet")

            summary_lines.extend([
                "",
                "## Key Decisions",
                "",
            ])

            if key_decisions:
                for decision in key_decisions:
                    summary_lines.append(f"- {decision}")
            else:
                summary_lines.append("- No key decisions extracted")

            summary_lines.extend([
                "",
                "## Artifacts Created",
                "",
            ])

            if artifacts_created:
                for artifact in artifacts_created:
                    summary_lines.append(f"- {artifact}")
            else:
                summary_lines.append("- No artifacts listed")

            summary_lines.extend([
                "",
                "## Step Files",
                "",
            ])

            # List step files
            doc_dir = self.get_documentation_dir()
            step_files = sorted(doc_dir.glob("step*.md"))
            for step_file in step_files:
                summary_lines.append(f"- [{step_file.name}]({step_file.name})")

            summary_content = "\n".join(summary_lines)
            summary_path.write_text(summary_content, encoding="utf-8")
            logger.debug(f"Created workflow summary: {summary_path}")
            return summary_path

        except OSError as e:
            raise DocumentationError(
                f"Failed to create workflow summary: {e}"
            ) from e

    def _get_completed_steps(self) -> list[int]:
        """Get list of completed step numbers."""
        doc_dir = self.get_documentation_dir()
        if not doc_dir.exists():
            return []

        step_files = doc_dir.glob("step*.md")
        step_numbers = []

        for step_file in step_files:
            # Extract step number from filename: step{N}-{name}.md or step{N}.md
            match = re.match(r"step(\d+)", step_file.stem)
            if match:
                step_numbers.append(int(match.group(1)))

        return sorted(step_numbers)

    def _extract_key_decisions(self) -> list[str]:
        """Extract key decisions from step files."""
        # Simple extraction: look for "## Key Decisions" or "## Decision" sections
        decisions = []
        doc_dir = self.get_documentation_dir()

        if not doc_dir.exists():
            return decisions

        for step_file in sorted(doc_dir.glob("step*.md")):
            try:
                content = step_file.read_text(encoding="utf-8")
                # Look for decision sections
                if "## Key Decisions" in content or "## Decision" in content:
                    # Extract decision items (simple heuristic)
                    lines = content.split("\n")
                    in_decision_section = False
                    for line in lines:
                        if "## Key Decisions" in line or "## Decision" in line:
                            in_decision_section = True
                            continue
                        if in_decision_section:
                            if line.startswith("##"):
                                break
                            if line.strip().startswith("-") and len(line.strip()) > 5:
                                decisions.append(line.strip()[2:])  # Remove "- "
            except Exception as e:
                logger.debug(f"Failed to extract decisions from {step_file}: {e}")

        return decisions[:10]  # Limit to 10 decisions

    def _list_artifacts(self) -> list[str]:
        """List artifacts created during workflow."""
        # Simple implementation: list code files created
        artifacts = []
        doc_dir = self.get_documentation_dir()

        # Check for common artifact patterns in step files
        if doc_dir.exists():
            for step_file in sorted(doc_dir.glob("step*.md")):
                try:
                    content = step_file.read_text(encoding="utf-8")
                    # Look for file paths mentioned in step files
                    import re
                    file_pattern = r"`([^`]+\.(py|md|yaml|yml|json))`"
                    matches = re.findall(file_pattern, content)
                    for match in matches:
                        file_path = match[0]
                        if file_path not in artifacts:
                            artifacts.append(file_path)
                except Exception:
                    pass

        return artifacts[:20]  # Limit to 20 artifacts
