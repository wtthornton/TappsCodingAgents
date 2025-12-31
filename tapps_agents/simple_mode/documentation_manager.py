"""
Workflow Documentation Manager - Organizes documentation by workflow ID.

Manages workflow-specific documentation directories and file paths.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import logging

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
