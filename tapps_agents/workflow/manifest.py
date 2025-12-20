"""
Task Manifest Generator

Generates human-readable task checklists from workflow YAML and execution state.
Epic 7: Task Manifest Generation System
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .execution_plan import generate_execution_plan
from .models import Artifact, StepExecution, Workflow, WorkflowState, WorkflowStep


class TaskManifestGenerator:
    """Generates markdown task manifests from workflow state and execution plan."""

    def __init__(self, workflow: Workflow, state: WorkflowState):
        """
        Initialize manifest generator.

        Args:
            workflow: Workflow definition
            state: Current workflow state
        """
        self.workflow = workflow
        self.state = state
        self.execution_plan = generate_execution_plan(workflow)

    def generate(self) -> str:
        """
        Generate markdown task manifest.

        Returns:
            Markdown string with task checklist
        """
        # Edge case: empty workflow
        if not self.workflow.steps:
            return f"# Workflow: {self.workflow.name}\n\n**Status**: No steps defined.\n"
        
        lines: list[str] = []

        # Workflow metadata section
        lines.extend(self._generate_metadata_section())

        # Completed steps section
        lines.extend(self._generate_completed_steps_section())

        # Skipped steps section
        lines.extend(self._generate_skipped_steps_section())

        # Current step section
        lines.extend(self._generate_current_step_section())

        # Upcoming steps section
        lines.extend(self._generate_upcoming_steps_section())

        # Artifacts section
        lines.extend(self._generate_artifacts_section())

        return "\n".join(lines)

    def _generate_metadata_section(self) -> list[str]:
        """Generate workflow metadata section."""
        lines = [
            f"# Workflow: {self.workflow.name}",
            "",
            f"**ID**: `{self.workflow.id}`",
            f"**Version**: {self.workflow.version}",
            f"**Type**: {self.workflow.type.value}",
            "",
        ]

        # Status and progress
        completed_count = len(self.state.completed_steps)
        skipped_count = len(self.state.skipped_steps)
        total_steps = len(self.workflow.steps)
        progress_pct = int((completed_count / total_steps) * 100) if total_steps > 0 else 0

        # Calculate current step number
        if self.state.status == "completed":
            current_step_num = total_steps
        elif self.state.current_step:
            # Find index of current step
            current_idx = next(
                (i for i, s in enumerate(self.workflow.steps) if s.id == self.state.current_step),
                completed_count
            )
            current_step_num = current_idx + 1
        else:
            current_step_num = completed_count + 1

        status_emoji = self._get_status_emoji(self.state.status)
        lines.extend([
            f"## Status: {status_emoji} {self.state.status.title()} (Step {current_step_num} of {total_steps})",
            "",
            f"**Progress**: {completed_count}/{total_steps} steps completed ({progress_pct}%)",
        ])
        
        if skipped_count > 0:
            lines.append(f"**Skipped**: {skipped_count} steps")
        
        lines.append(f"**Started**: {self.state.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if self.state.status == "completed":
            # Find completion time from last step execution
            last_execution = self._get_last_step_execution()
            if last_execution and last_execution.completed_at:
                lines.append(f"**Completed**: {last_execution.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if self.state.error:
            lines.append(f"**Error**: {self.state.error}")

        lines.append("")
        return lines

    def _generate_completed_steps_section(self) -> list[str]:
        """Generate completed steps section."""
        if not self.state.completed_steps:
            return []

        lines = ["### Completed Steps", ""]

        for step_id in self.state.completed_steps:
            step = self._get_step_by_id(step_id)
            if not step:
                continue

            execution = self._get_step_execution(step_id)
            completion_time = ""
            if execution and execution.completed_at:
                completion_time = f" - Completed {execution.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"

            duration = ""
            if execution and execution.duration_seconds:
                duration = f" ({execution.duration_seconds:.1f}s)"

            lines.append(
                f"- [x] **{step.id}** ({step.agent}) - {step.action}{completion_time}{duration}"
            )

        lines.append("")
        return lines

    def _generate_skipped_steps_section(self) -> list[str]:
        """Generate skipped steps section."""
        if not self.state.skipped_steps:
            return []

        lines = ["### Skipped Steps", ""]

        for step_id in self.state.skipped_steps:
            step = self._get_step_by_id(step_id)
            if not step:
                continue

            lines.append(
                f"- [⏭️] **{step.id}** ({step.agent}) - {step.action} - **SKIPPED**"
            )

        lines.append("")
        return lines

    def _generate_current_step_section(self) -> list[str]:
        """Generate current step section."""
        if not self.state.current_step:
            return []

        step = self._get_step_by_id(self.state.current_step)
        if not step:
            return []

        lines = [
            "### Current Step",
            "",
            f"- [ ] **{step.id}** ({step.agent}) - {step.action} - **IN PROGRESS**",
            "",
        ]

        # Step details
        if step.requires:
            requires_status = self._format_artifact_status(step.requires)
            lines.append(f"  - **Requires**: {requires_status}")

        if step.creates:
            creates_status = self._format_expected_artifacts(step.creates)
            lines.append(f"  - **Creates**: {creates_status}")

        if step.consults:
            lines.append(f"  - **Consults**: {', '.join(step.consults)}")

        if step.gate:
            lines.append(f"  - **Gate**: Quality gate configured")

        # Worktree info (if available in metadata)
        if step.metadata and step.metadata.get("worktree"):
            lines.append(f"  - **Worktree**: `{step.metadata['worktree']}`")

        # Command (if available in metadata)
        if step.metadata and step.metadata.get("command"):
            lines.append(f"  - **Command**: `{step.metadata['command']}`")

        lines.append("")
        return lines

    def _generate_upcoming_steps_section(self) -> list[str]:
        """Generate upcoming steps section."""
        # Find steps that are not completed, not skipped, and not current
        upcoming_steps = []
        for step in self.workflow.steps:
            if (
                step.id not in self.state.completed_steps
                and step.id not in self.state.skipped_steps
                and step.id != self.state.current_step
            ):
                upcoming_steps.append(step)

        if not upcoming_steps:
            return []

        lines = ["### Upcoming Steps", ""]

        for step in upcoming_steps:
            # Check if step is blocked (missing required artifacts)
            is_blocked = self._is_step_blocked(step)
            status_indicator = "⏸️ Blocked" if is_blocked else "⏳ Waiting"

            blocking_info = ""
            if is_blocked:
                missing = self._get_missing_artifacts(step)
                if missing:
                    blocking_info = f" - Waiting for {', '.join(missing)}"

            lines.append(
                f"- [ ] **{step.id}** ({step.agent}) - {step.action} - {status_indicator}{blocking_info}"
            )

        lines.append("")
        return lines

    def _generate_artifacts_section(self) -> list[str]:
        """Generate artifacts section."""
        lines = ["### Artifacts", ""]

        # Collect all expected artifacts from workflow steps
        expected_artifacts: set[str] = set()
        for step in self.workflow.steps:
            expected_artifacts.update(step.creates)

        # Show created artifacts
        created_artifacts = [
            art_name
            for art_name, artifact in self.state.artifacts.items()
            if artifact.status == "complete"
        ]
        if created_artifacts:
            for art_name in sorted(created_artifacts):
                artifact = self.state.artifacts[art_name]
                created_by = f" (created by {artifact.created_by})" if artifact.created_by else ""
                lines.append(f"- ✅ `{art_name}`{created_by}")

        # Show expected but not yet created artifacts (not blocking any steps)
        pending_artifacts = expected_artifacts - set(self.state.artifacts.keys())
        blocking_artifacts = self._get_all_missing_artifacts()
        non_blocking_pending = pending_artifacts - blocking_artifacts
        
        if non_blocking_pending:
            for art_name in sorted(non_blocking_pending):
                # Find which step creates this artifact
                creating_step = self._find_step_creating_artifact(art_name)
                step_info = f" (expected from {creating_step.id})" if creating_step else ""
                lines.append(f"- ⏳ `{art_name}`{step_info}")

        # Show missing artifacts (blocking steps)
        if blocking_artifacts:
            for art_name in sorted(blocking_artifacts):
                lines.append(f"- ❌ `{art_name}` (missing, blocking steps)")

        lines.append("")
        return lines

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for workflow status."""
        status_map = {
            "running": "⏳",
            "completed": "✅",
            "failed": "❌",
            "paused": "⏸️",
        }
        return status_map.get(status.lower(), "⏳")

    def _get_step_by_id(self, step_id: str) -> WorkflowStep | None:
        """Get workflow step by ID."""
        return next((s for s in self.workflow.steps if s.id == step_id), None)

    def _get_step_execution(self, step_id: str) -> StepExecution | None:
        """Get step execution record."""
        return next(
            (se for se in self.state.step_executions if se.step_id == step_id),
            None,
        )

    def _get_last_step_execution(self) -> StepExecution | None:
        """Get the last step execution."""
        if not self.state.step_executions:
            return None
        # Get execution with latest completion time, or latest start time if not completed
        return max(
            self.state.step_executions,
            key=lambda se: (
                se.completed_at if se.completed_at else datetime.min,
                se.started_at if se.started_at else datetime.min,
            ),
        )

    def _format_artifact_status(self, artifact_names: list[str]) -> str:
        """Format artifact status with emojis."""
        parts = []
        for art_name in artifact_names:
            if art_name in self.state.artifacts:
                artifact = self.state.artifacts[art_name]
                if artifact.status == "complete":
                    parts.append(f"`{art_name}` ✅")
                else:
                    parts.append(f"`{art_name}` ⏳")
            else:
                parts.append(f"`{art_name}` ❌")
        return ", ".join(parts)

    def _format_expected_artifacts(self, artifact_names: list[str]) -> str:
        """Format expected artifacts."""
        parts = [f"`{name}` ⏳" for name in artifact_names]
        return ", ".join(parts)

    def _is_step_blocked(self, step: WorkflowStep) -> bool:
        """Check if step is blocked by missing artifacts."""
        for required_artifact in step.requires:
            if required_artifact not in self.state.artifacts:
                return True
            artifact = self.state.artifacts[required_artifact]
            if artifact.status != "complete":
                return True
        return False

    def _get_missing_artifacts(self, step: WorkflowStep) -> list[str]:
        """Get list of missing artifacts for a step."""
        missing = []
        for required_artifact in step.requires:
            if required_artifact not in self.state.artifacts:
                missing.append(required_artifact)
            else:
                artifact = self.state.artifacts[required_artifact]
                if artifact.status != "complete":
                    missing.append(required_artifact)
        return missing

    def _get_all_missing_artifacts(self) -> set[str]:
        """Get all missing artifacts that are blocking steps."""
        missing = set()
        for step in self.workflow.steps:
            if step.id not in self.state.completed_steps:
                missing.update(self._get_missing_artifacts(step))
        return missing

    def _find_step_creating_artifact(self, artifact_name: str) -> WorkflowStep | None:
        """Find step that creates an artifact."""
        return next(
            (s for s in self.workflow.steps if artifact_name in s.creates),
            None,
        )


def generate_manifest(
    workflow: Workflow, state: WorkflowState
) -> str:
    """
    Generate task manifest from workflow and state.

    Args:
        workflow: Workflow definition
        state: Current workflow state

    Returns:
        Markdown task manifest string
    """
    generator = TaskManifestGenerator(workflow, state)
    return generator.generate()


def save_manifest(
    manifest: str, state_dir: Path, workflow_id: str
) -> Path:
    """
    Save manifest to workflow state directory.

    Args:
        manifest: Manifest markdown content
        state_dir: Directory where workflow state is stored
        workflow_id: Workflow ID

    Returns:
        Path to saved manifest file
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = state_dir / f"{workflow_id}" / "task-manifest.md"

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest, encoding="utf-8")

    return manifest_path


def sync_manifest_to_project_root(
    manifest: str, project_root: Path, filename: str = "workflow-tasks.md"
) -> Path:
    """
    Sync manifest to project root for visibility.

    Args:
        manifest: Manifest markdown content
        project_root: Project root directory
        filename: Filename for manifest in project root

    Returns:
        Path to synced manifest file
    """
    manifest_path = project_root / filename
    manifest_path.write_text(manifest, encoding="utf-8")
    return manifest_path


class TaskManifestParser:
    """Parser for reading and querying task manifests."""

    def __init__(self, manifest_path: Path):
        """
        Initialize manifest parser.

        Args:
            manifest_path: Path to manifest markdown file
        """
        self.manifest_path = manifest_path
        self.content = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""

    def get_current_step(self) -> str | None:
        """
        Get current step ID from manifest.

        Returns:
            Current step ID or None if not found
        """
        import re
        # More robust regex that handles whitespace variations
        match = re.search(
            r"###\s+Current\s+Step\s+-?\s*\[?\s*\]?\s*\*\*([^\*]+)\*\*",
            self.content,
            re.MULTILINE | re.IGNORECASE,
        )
        return match.group(1).strip() if match else None

    def get_blocked_steps(self) -> list[str]:
        """
        Get list of blocked step IDs.

        Returns:
            List of blocked step IDs
        """
        import re
        blocked = []
        # More robust regex that handles whitespace and emoji variations
        matches = re.finditer(
            r"-?\s*\[?\s*\]?\s*\*\*([^\*]+)\*\*.*?⏸️\s*Blocked",
            self.content,
            re.MULTILINE,
        )
        for match in matches:
            step_id = match.group(1).strip()
            if step_id:
                blocked.append(step_id)
        return blocked

    def get_completed_steps(self) -> list[str]:
        """
        Get list of completed step IDs.

        Returns:
            List of completed step IDs
        """
        import re
        completed = []
        # More robust regex that handles whitespace variations
        matches = re.finditer(
            r"-?\s*\[x\]\s*\*\*([^\*]+)\*\*",
            self.content,
            re.MULTILINE | re.IGNORECASE,
        )
        for match in matches:
            step_id = match.group(1).strip()
            if step_id:
                completed.append(step_id)
        return completed

    def get_missing_artifacts(self) -> list[str]:
        """
        Get list of missing artifacts.

        Returns:
            List of missing artifact names
        """
        import re
        missing = []
        # More robust regex that handles whitespace variations
        matches = re.finditer(
            r"-?\s*❌\s*`([^`]+)`\s*\(missing",
            self.content,
            re.MULTILINE,
        )
        for match in matches:
            artifact_name = match.group(1).strip()
            if artifact_name:
                missing.append(artifact_name)
        return missing

    def get_workflow_status(self) -> dict[str, Any]:
        """
        Get workflow status information.

        Returns:
            Dictionary with status information
        """
        import re
        
        status_match = re.search(
            r"## Status: .*? (\w+) \(Step (\d+) of (\d+)\)",
            self.content,
        )
        
        progress_match = re.search(
            r"\*\*Progress\*\*: (\d+)/(\d+) steps completed \((\d+)%\)",
            self.content,
        )
        
        return {
            "status": status_match.group(1).lower() if status_match else "unknown",
            "current_step_number": int(status_match.group(2)) if status_match else 0,
            "total_steps": int(status_match.group(3)) if status_match else 0,
            "completed_count": int(progress_match.group(1)) if progress_match else 0,
            "total_count": int(progress_match.group(2)) if progress_match else 0,
            "progress_percent": int(progress_match.group(3)) if progress_match else 0,
        }

    def validate_against_state(self, state: WorkflowState) -> tuple[bool, list[str]]:
        """
        Validate manifest against workflow state.

        Args:
            state: Workflow state to validate against

        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Check completed steps match
        manifest_completed = set(self.get_completed_steps())
        state_completed = set(state.completed_steps)
        if manifest_completed != state_completed:
            errors.append(
                f"Completed steps mismatch: manifest={manifest_completed}, state={state_completed}"
            )
        
        # Check current step matches
        manifest_current = self.get_current_step()
        if manifest_current != state.current_step:
            errors.append(
                f"Current step mismatch: manifest={manifest_current}, state={state.current_step}"
            )
        
        return len(errors) == 0, errors

