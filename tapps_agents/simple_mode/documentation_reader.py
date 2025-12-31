"""
Workflow Documentation Reader - Reads step documentation and state from .md files.

Provides utilities to read and parse workflow documentation files created by
WorkflowDocumentationManager.
"""

import logging
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


class DocumentationReaderError(Exception):
    """Exception raised for documentation reading errors."""

    pass


class WorkflowDocumentationReader:
    """Reads workflow documentation and state from .md files."""

    def __init__(
        self,
        base_dir: Path,
        workflow_id: str,
    ) -> None:
        """
        Initialize documentation reader.

        Args:
            base_dir: Base directory for documentation (e.g., docs/workflows/simple-mode/)
            workflow_id: Workflow identifier
        """
        if not workflow_id or ".." in workflow_id or "/" in workflow_id:
            raise ValueError(f"Invalid workflow_id: {workflow_id}")

        self.base_dir = Path(base_dir)
        self.workflow_id = workflow_id
        self._doc_dir: Path | None = None

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

    def read_step_documentation(
        self,
        step_number: int,
        step_name: str | None = None,
    ) -> str:
        """
        Read markdown content from step documentation file.

        Args:
            step_number: Step number (1-based)
            step_name: Optional step name

        Returns:
            Markdown content of the file (empty string if file doesn't exist)

        Raises:
            DocumentationReaderError: If file exists but cannot be read
        """
        file_path = self.get_step_file_path(step_number, step_name)

        if not file_path.exists():
            logger.debug(f"Step file not found: {file_path}")
            return ""

        try:
            content = file_path.read_text(encoding="utf-8")
            logger.debug(f"Read step documentation from: {file_path}")
            return content
        except UnicodeDecodeError as e:
            raise DocumentationReaderError(
                f"Failed to decode file {file_path}: {e}"
            ) from e
        except OSError as e:
            raise DocumentationReaderError(
                f"Failed to read file {file_path}: {e}"
            ) from e

    def read_step_state(
        self,
        step_number: int,
        step_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Read and parse YAML frontmatter state from step file.

        Args:
            step_number: Step number (1-based)
            step_name: Optional step name

        Returns:
            Parsed state dictionary, or empty dict if no frontmatter or file doesn't exist
        """
        if yaml is None:
            logger.warning("PyYAML not available, cannot parse state")
            return {}

        content = self.read_step_documentation(step_number, step_name)
        if not content:
            return {}

        # Parse YAML frontmatter
        # Format: ---\n{yaml}\n---\n\n{markdown}
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not frontmatter_match:
            logger.debug(f"No YAML frontmatter found in step {step_number}")
            return {}

        yaml_content = frontmatter_match.group(1)

        try:
            state = yaml.safe_load(yaml_content)
            if not isinstance(state, dict):
                logger.warning(f"YAML frontmatter is not a dictionary in step {step_number}")
                return {}
            logger.debug(f"Parsed state from step {step_number}")
            return state
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter in step {step_number}: {e}")
            return {}

    def validate_step_documentation(
        self,
        step_number: int,
        step_name: str,
        required_sections: list[str],
    ) -> dict[str, bool]:
        """
        Validate step documentation has required sections.

        Args:
            step_number: Step number (1-based)
            step_name: Step name
            required_sections: List of required section names

        Returns:
            Dictionary mapping section names to presence flags
        """
        content = self.read_step_documentation(step_number, step_name)
        if not content:
            return {section: False for section in required_sections}

        validation = {}
        for section in required_sections:
            # Check for section headers: ## {section} or ### {section}
            pattern = rf"^#{{2,3}}\s+{re.escape(section)}"
            validation[section] = bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))

        return validation
