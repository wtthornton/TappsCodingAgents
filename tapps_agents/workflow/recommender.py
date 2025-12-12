"""
Workflow Recommender - Recommend appropriate workflows based on project characteristics.
"""

from dataclasses import dataclass
from pathlib import Path

from .detector import ProjectCharacteristics, ProjectDetector, WorkflowTrack
from .models import Workflow
from .parser import WorkflowParser


@dataclass
class WorkflowRecommendation:
    """Workflow recommendation result."""

    workflow_file: str | None
    workflow: Workflow | None
    track: WorkflowTrack
    confidence: float
    characteristics: ProjectCharacteristics
    alternative_workflows: list[str]
    message: str


class WorkflowRecommender:
    """Recommend workflows based on project detection."""

    def __init__(
        self, project_root: Path | None = None, workflows_dir: Path | None = None
    ):
        """
        Initialize workflow recommender.

        Args:
            project_root: Root directory of the project
            workflows_dir: Directory containing workflow YAML files
        """
        self.project_root = project_root or Path.cwd()
        self.workflows_dir = workflows_dir or (self.project_root / "workflows")
        self.detector = ProjectDetector(project_root)

    def recommend(
        self,
        user_query: str | None = None,
        file_count: int | None = None,
        scope_description: str | None = None,
        auto_load: bool = True,
    ) -> WorkflowRecommendation:
        """
        Recommend a workflow based on project characteristics.

        Args:
            user_query: User's query or request (for quick-fix detection)
            file_count: Estimated number of files to change
            scope_description: Description of the change scope
            auto_load: Whether to automatically load the recommended workflow

        Returns:
            WorkflowRecommendation with recommendation details
        """
        # Detect project characteristics
        if user_query or file_count or scope_description:
            characteristics = self.detector.detect_from_context(
                user_query=user_query,
                file_count=file_count,
                scope_description=scope_description,
            )
        else:
            characteristics = self.detector.detect()

        # Get recommended workflow file
        workflow_file = self.detector.get_recommended_workflow(characteristics)

        # Find available workflows
        available_workflows = self._find_available_workflows()

        # Load workflow if requested and found
        workflow = None
        if auto_load and workflow_file:
            workflow_path = self.workflows_dir / f"{workflow_file}.yaml"
            if workflow_path.exists():
                try:
                    workflow = WorkflowParser.parse_file(workflow_path)
                except Exception:
                    # If recommended workflow doesn't exist, try to find a similar one
                    workflow_file = self._find_best_match(
                        workflow_file, available_workflows
                    )
                    if workflow_file:
                        workflow_path = self.workflows_dir / f"{workflow_file}.yaml"
                        if workflow_path.exists():
                            workflow = WorkflowParser.parse_file(workflow_path)

        # Get alternative workflows
        alternative_workflows = [w for w in available_workflows if w != workflow_file]

        # Generate recommendation message
        message = self._generate_message(
            characteristics, workflow_file, workflow is not None
        )

        return WorkflowRecommendation(
            workflow_file=workflow_file,
            workflow=workflow,
            track=characteristics.workflow_track,
            confidence=characteristics.confidence,
            characteristics=characteristics,
            alternative_workflows=alternative_workflows,
            message=message,
        )

    def _find_available_workflows(self) -> list[str]:
        """Find all available workflow files."""
        if not self.workflows_dir.exists():
            return []

        workflows = []
        for workflow_file in self.workflows_dir.glob("*.yaml"):
            workflows.append(workflow_file.stem)
        return workflows

    def _find_best_match(self, preferred: str, available: list[str]) -> str | None:
        """Find best matching workflow from available workflows."""
        if not available:
            return None

        # Try exact match first
        if preferred in available:
            return preferred

        # Try partial match
        preferred_lower = preferred.lower()
        for workflow in available:
            if (
                preferred_lower in workflow.lower()
                or workflow.lower() in preferred_lower
            ):
                return workflow

        # Return first available as fallback
        return available[0] if available else None

    def _generate_message(
        self,
        characteristics: ProjectCharacteristics,
        workflow_file: str | None,
        workflow_loaded: bool,
    ) -> str:
        """Generate human-readable recommendation message."""
        track_emojis = {
            WorkflowTrack.QUICK_FLOW: "⚡",
            WorkflowTrack.BMAD_METHOD: "📋",
            WorkflowTrack.ENTERPRISE: "🏢",
        }

        track_names = {
            WorkflowTrack.QUICK_FLOW: "Quick Flow",
            WorkflowTrack.BMAD_METHOD: "BMad Method",
            WorkflowTrack.ENTERPRISE: "Enterprise",
        }

        emoji = track_emojis.get(characteristics.workflow_track, "📋")
        track_name = track_names.get(characteristics.workflow_track, "BMad Method")

        parts = [
            f"{emoji} **{track_name}** workflow recommended",
            f"Confidence: {characteristics.confidence:.0%}",
            f"Project Type: {characteristics.project_type.value}",
        ]

        if workflow_file:
            if workflow_loaded:
                parts.append(f"✅ Loaded: `{workflow_file}.yaml`")
            else:
                parts.append(f"⚠️ Recommended: `{workflow_file}.yaml` (not found)")

        if characteristics.recommendations:
            parts.append("\nRecommendations:")
            for rec in characteristics.recommendations:
                parts.append(f"  • {rec}")

        return "\n".join(parts)

    def list_available_workflows(self) -> list[dict[str, str]]:
        """
        List all available workflows with metadata.

        Returns:
            List of workflow information dictionaries
        """
        workflows = []
        for workflow_file in self.workflows_dir.glob("*.yaml"):
            try:
                workflow = WorkflowParser.parse_file(workflow_file)
                workflows.append(
                    {
                        "file": workflow_file.name,
                        "id": workflow.id,
                        "name": workflow.name,
                        "type": workflow.type.value,
                        "description": workflow.description,
                    }
                )
            except Exception:
                # Skip invalid workflows
                continue
        return workflows
