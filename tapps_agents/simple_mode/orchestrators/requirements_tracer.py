"""Requirements traceability for linking requirements to deliverables."""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RequirementsTracer:
    """Trace requirements to deliverables."""

    VALID_DELIVERABLE_TYPES = {"code", "tests", "docs", "templates"}

    def __init__(self, requirements: dict[str, Any] | None = None):
        """Initialize tracer with requirements.

        Args:
            requirements: Requirements dict with requirement IDs as keys
        """
        self.requirements = requirements or {}
        self.trace: dict[str, dict[str, list[Path]]] = {}

    def add_trace(
        self, requirement_id: str, deliverable_type: str, path: Path
    ) -> None:
        """Link a requirement to a deliverable.

        Args:
            requirement_id: Requirement ID (e.g., "R1-VERIFY-001")
            deliverable_type: One of: code, tests, docs, templates
            path: Path to the deliverable file

        Raises:
            ValueError: If deliverable_type is invalid
        """
        if deliverable_type not in self.VALID_DELIVERABLE_TYPES:
            raise ValueError(
                f"Invalid deliverable_type: {deliverable_type}. "
                f"Must be one of: {self.VALID_DELIVERABLE_TYPES}"
            )

        # Initialize trace entry if doesn't exist
        if requirement_id not in self.trace:
            self.trace[requirement_id] = {
                "code": [],
                "tests": [],
                "docs": [],
                "templates": [],
            }

        # Add path if not already present (avoid duplicates)
        if path not in self.trace[requirement_id][deliverable_type]:
            self.trace[requirement_id][deliverable_type].append(path)
            logger.debug(
                f"Linked requirement {requirement_id} -> {deliverable_type}: {path}"
            )

    def verify_requirement(self, requirement_id: str) -> dict[str, Any]:
        """Verify a requirement is fully implemented.

        Args:
            requirement_id: Requirement ID to verify

        Returns:
            Dictionary with:
            - complete: bool - Whether requirement is complete
            - gaps: list[str] - List of missing deliverable types
            - deliverables: dict - All deliverables linked to requirement
        """
        if requirement_id not in self.trace:
            return {
                "complete": False,
                "missing": "all",
                "gaps": ["code", "tests", "docs"],
                "deliverables": {},
            }

        trace = self.trace[requirement_id]
        gaps = []

        # Check for required deliverables
        # Code is always required
        if not trace["code"]:
            gaps.append("code")

        # Tests are required for code deliverables
        if trace["code"] and not trace["tests"]:
            gaps.append("tests")

        # Docs are typically required
        if not trace["docs"]:
            gaps.append("docs")

        # Templates are optional (only if applicable)
        # Don't require templates unless code indicates templates are needed

        return {
            "complete": len(gaps) == 0,
            "gaps": gaps,
            "deliverables": {
                "code": [str(p) for p in trace["code"]],
                "tests": [str(p) for p in trace["tests"]],
                "docs": [str(p) for p in trace["docs"]],
                "templates": [str(p) for p in trace["templates"]],
            },
        }

    def verify_all_requirements(self) -> dict[str, Any]:
        """Verify all requirements are fully implemented.

        Returns:
            Dictionary with:
            - complete: bool - Whether all requirements are complete
            - requirements: dict - Status for each requirement
            - gaps: list[dict] - List of gaps with requirement_id and missing types
        """
        requirements_status = {}
        all_gaps = []

        # Check all traced requirements
        for requirement_id in self.trace:
            status = self.verify_requirement(requirement_id)
            requirements_status[requirement_id] = status

            if not status["complete"]:
                all_gaps.append({
                    "requirement_id": requirement_id,
                    "missing_types": status["gaps"],
                    "deliverables": status["deliverables"],
                })

        # Check for requirements in requirements dict that aren't traced
        for req_id in self.requirements:
            if req_id not in self.trace:
                all_gaps.append({
                    "requirement_id": req_id,
                    "missing_types": ["all"],
                    "deliverables": {},
                })
                requirements_status[req_id] = {
                    "complete": False,
                    "missing": "all",
                    "gaps": ["all"],
                    "deliverables": {},
                }

        return {
            "complete": len(all_gaps) == 0,
            "requirements": requirements_status,
            "gaps": all_gaps,
        }

    def get_traceability_report(self) -> dict[str, Any]:
        """Generate traceability matrix report.

        Returns:
            Dictionary with traceability matrix and statistics
        """
        matrix = {}
        stats = {
            "total_requirements": len(self.requirements) if self.requirements else len(self.trace),
            "traced_requirements": len(self.trace),
            "total_deliverables": 0,
            "by_type": {
                "code": 0,
                "tests": 0,
                "docs": 0,
                "templates": 0,
            },
        }

        for requirement_id, deliverables in self.trace.items():
            matrix[requirement_id] = {
                "code": len(deliverables["code"]),
                "tests": len(deliverables["tests"]),
                "docs": len(deliverables["docs"]),
                "templates": len(deliverables["templates"]),
            }

            stats["by_type"]["code"] += len(deliverables["code"])
            stats["by_type"]["tests"] += len(deliverables["tests"])
            stats["by_type"]["docs"] += len(deliverables["docs"])
            stats["by_type"]["templates"] += len(deliverables["templates"])

        stats["total_deliverables"] = sum(stats["by_type"].values())

        return {
            "matrix": matrix,
            "statistics": stats,
        }

    def extract_requirement_ids(
        self, user_stories: list[dict[str, Any]]
    ) -> list[str]:
        """Extract requirement IDs from user stories.

        Args:
            user_stories: List of user story dicts with "id" or "requirement_id" field

        Returns:
            List of requirement ID strings
        """
        requirement_ids = []

        for story in user_stories:
            # Try "id" field first
            req_id = story.get("id")
            if not req_id:
                # Try "requirement_id" field
                req_id = story.get("requirement_id")

            if req_id and isinstance(req_id, str):
                requirement_ids.append(req_id)
            else:
                # Try to extract from story text
                story_text = str(story)
                # Pattern: R{n}-{type}-{num}
                pattern = r"R\d+-[A-Z]+-\d+"
                matches = re.findall(pattern, story_text)
                requirement_ids.extend(matches)

        logger.debug(f"Extracted {len(requirement_ids)} requirement IDs from user stories")
        return list(set(requirement_ids))  # Deduplicate

    def to_dict(self) -> dict[str, Any]:
        """Convert tracer to dictionary for serialization.

        Returns:
            Dictionary representation of tracer
        """
        return {
            "requirements": self.requirements,
            "trace": {
                req_id: {
                    deliverable_type: [str(p) for p in paths]
                    for deliverable_type, paths in deliverables.items()
                }
                for req_id, deliverables in self.trace.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementsTracer":
        """Create tracer from dictionary (for checkpoint restoration).

        Args:
            data: Dictionary representation from to_dict()

        Returns:
            RequirementsTracer instance
        """
        tracer = cls(requirements=data.get("requirements", {}))
        trace_data = data.get("trace", {})

        for req_id, deliverables in trace_data.items():
            for deliverable_type, paths in deliverables.items():
                for path_str in paths:
                    tracer.add_trace(req_id, deliverable_type, Path(path_str))

        return tracer
