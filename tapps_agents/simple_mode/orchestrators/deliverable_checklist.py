"""Deliverable checklist for tracking workflow deliverables."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DeliverableChecklist:
    """Track all deliverables for a workflow execution."""

    VALID_CATEGORIES = {
        "core_code",
        "related_files",
        "documentation",
        "tests",
        "templates",
        "examples",
    }
    VALID_STATUSES = {"pending", "complete", "failed", "skipped"}

    def __init__(self, requirements: dict[str, Any] | None = None):
        """Initialize checklist with requirements context.

        Args:
            requirements: Optional requirements dict for context
        """
        self.requirements = requirements or {}
        self.checklist = {
            "core_code": [],
            "related_files": [],
            "documentation": [],
            "tests": [],
            "templates": [],
            "examples": [],
        }

    def add_deliverable(
        self,
        category: str,
        item: str,
        path: Path,
        status: str = "pending",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a deliverable to the checklist.

        Args:
            category: One of: core_code, related_files, documentation, tests, templates, examples
            item: Human-readable description of the deliverable
            path: File path to the deliverable
            status: Status of deliverable (pending, complete, failed, skipped)
            metadata: Optional metadata (e.g., requirement_id, step_number)

        Raises:
            ValueError: If category or status is invalid
        """
        if category not in self.VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category: {category}. Must be one of: {self.VALID_CATEGORIES}"
            )
        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {status}. Must be one of: {self.VALID_STATUSES}"
            )

        # Check if file exists (if it's a file path, not a directory)
        if path.exists() and path.is_file():
            # File exists, validate it
            pass
        elif not path.exists():
            # File doesn't exist yet - log warning but continue
            logger.debug(f"Deliverable path doesn't exist yet: {path}")

        deliverable = {
            "item": item,
            "path": path,
            "status": status,
            "metadata": metadata or {},
        }

        self.checklist[category].append(deliverable)
        logger.debug(
            f"Added deliverable: {category}/{item} ({status}) at {path}"
        )

    def discover_related_files(
        self, core_files: list[Path], project_root: Path
    ) -> list[Path]:
        """Discover all related files that might need updates.

        Args:
            core_files: List of core files that were implemented
            project_root: Project root directory for searching

        Returns:
            List of discovered related file paths
        """
        discovered = []
        seen = set()

        for core_file in core_files:
            # Find templates
            templates = self._find_templates(core_file, project_root)
            for template in templates:
                if template not in seen:
                    discovered.append(template)
                    seen.add(template)

            # Find documentation
            docs = self._find_documentation(core_file, project_root)
            for doc in docs:
                if doc not in seen:
                    discovered.append(doc)
                    seen.add(doc)

            # Find examples
            examples = self._find_examples(core_file, project_root)
            for example in examples:
                if example not in seen:
                    discovered.append(example)
                    seen.add(example)

        logger.info(f"Discovered {len(discovered)} related files for {len(core_files)} core files")
        return discovered

    def _find_templates(self, core_file: Path, project_root: Path) -> list[Path]:
        """Find template files related to core file.

        Args:
            core_file: Core file that was implemented
            project_root: Project root directory

        Returns:
            List of template file paths
        """
        templates = []
        core_path_str = str(core_file)

        # Pattern 1: Skill-related files -> skill templates
        if "tapps_agents/core/skills" in core_path_str or "tapps_agents/agents" in core_path_str:
            # Find skill templates in resources
            skills_dir = project_root / "tapps_agents" / "resources" / "claude" / "skills"
            if skills_dir.exists():
                for skill_dir in skills_dir.iterdir():
                    if skill_dir.is_dir():
                        skill_template = skill_dir / "SKILL.md"
                        if skill_template.exists():
                            templates.append(skill_template)

        # Pattern 2: Workflow-related files -> workflow templates
        if "workflow" in core_path_str.lower() or "orchestrator" in core_path_str.lower():
            templates_dir = project_root / "templates"
            if templates_dir.exists():
                # Search for workflow template files
                for template_file in templates_dir.rglob("*.yaml"):
                    templates.append(template_file)
                for template_file in templates_dir.rglob("*.yml"):
                    templates.append(template_file)

        return templates

    def _find_documentation(self, core_file: Path, project_root: Path) -> list[Path]:
        """Find documentation files that reference the feature.

        Args:
            core_file: Core file that was implemented
            project_root: Project root directory

        Returns:
            List of documentation file paths
        """
        docs = []
        core_file_name = core_file.name
        core_file_stem = core_file.stem

        # Search docs directory
        docs_dir = project_root / "docs"
        if docs_dir.exists():
            # Search for files mentioning the core file
            for doc_file in docs_dir.rglob("*.md"):
                try:
                    content = doc_file.read_text(encoding="utf-8")
                    # Check if doc references the core file
                    if core_file_name in content or core_file_stem in content:
                        docs.append(doc_file)
                except Exception as e:
                    logger.debug(f"Error reading doc file {doc_file}: {e}")

        # Check README files
        for readme_path in [
            project_root / "README.md",
            project_root / "docs" / "README.md",
        ]:
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding="utf-8")
                    if core_file_name in content or core_file_stem in content:
                        docs.append(readme_path)
                except Exception as e:
                    logger.debug(f"Error reading README {readme_path}: {e}")

        return docs

    def _find_examples(self, core_file: Path, project_root: Path) -> list[Path]:
        """Find example files demonstrating the feature.

        Args:
            core_file: Core file that was implemented
            project_root: Project root directory

        Returns:
            List of example file paths
        """
        examples = []
        core_file_stem = core_file.stem

        # Search examples directory
        examples_dir = project_root / "examples"
        if examples_dir.exists():
            for example_file in examples_dir.rglob("*"):
                if example_file.is_file():
                    # Match by filename pattern
                    if core_file_stem in example_file.name:
                        examples.append(example_file)

        # Search demo directory
        demo_dir = project_root / "demo"
        if demo_dir.exists():
            for demo_file in demo_dir.rglob("*"):
                if demo_file.is_file():
                    if core_file_stem in demo_file.name:
                        examples.append(demo_file)

        return examples

    def verify_completeness(self) -> dict[str, Any]:
        """Verify all checklist items are complete.

        Returns:
            Dictionary with:
            - complete: bool - Whether all items are complete
            - gaps: list[dict] - List of incomplete items with details
            - summary: dict - Summary by category
        """
        gaps = []
        summary = {}

        for category, items in self.checklist.items():
            total = len(items)
            complete_count = sum(1 for item in items if item["status"] == "complete")
            pending_count = sum(1 for item in items if item["status"] == "pending")
            failed_count = sum(1 for item in items if item["status"] == "failed")

            summary[category] = {
                "total": total,
                "complete": complete_count,
                "pending": pending_count,
                "failed": failed_count,
            }

            # Collect incomplete items
            for item in items:
                if item["status"] != "complete":
                    gaps.append({
                        "category": category,
                        "item": item["item"],
                        "path": item["path"],
                        "status": item["status"],
                        "metadata": item.get("metadata", {}),
                    })

        return {
            "complete": len(gaps) == 0,
            "gaps": gaps,
            "summary": summary,
        }

    def mark_complete(
        self, category: str, item: str | None = None, path: Path | None = None
    ) -> None:
        """Mark a deliverable as complete.

        Args:
            category: Category of deliverable
            item: Item description (optional, matches any if None)
            path: File path (optional, matches any if None)
        """
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")

        for deliverable in self.checklist[category]:
            match = True
            if item and deliverable["item"] != item:
                match = False
            if path and deliverable["path"] != path:
                match = False

            if match:
                deliverable["status"] = "complete"
                logger.debug(f"Marked {category}/{deliverable['item']} as complete")

    def to_dict(self) -> dict[str, Any]:
        """Convert checklist to dictionary for serialization.

        Returns:
            Dictionary representation of checklist
        """
        return {
            "requirements": self.requirements,
            "checklist": {
                category: [
                    {
                        "item": item["item"],
                        "path": str(item["path"]),
                        "status": item["status"],
                        "metadata": item.get("metadata", {}),
                    }
                    for item in items
                ]
                for category, items in self.checklist.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeliverableChecklist":
        """Create checklist from dictionary (for checkpoint restoration).

        Args:
            data: Dictionary representation from to_dict()

        Returns:
            DeliverableChecklist instance
        """
        checklist = cls(requirements=data.get("requirements"))
        checklist_data = data.get("checklist", {})

        for category, items in checklist_data.items():
            for item_data in items:
                checklist.add_deliverable(
                    category=category,
                    item=item_data["item"],
                    path=Path(item_data["path"]),
                    status=item_data["status"],
                    metadata=item_data.get("metadata", {}),
                )

        return checklist
