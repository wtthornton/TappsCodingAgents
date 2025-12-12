"""
Workflow Executor - Execute YAML workflow definitions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Artifact, Workflow, WorkflowState, WorkflowStep
from .parser import WorkflowParser
from .recommender import WorkflowRecommendation, WorkflowRecommender
from .state_manager import AdvancedStateManager


class WorkflowExecutor:
    """Executor for workflow definitions."""

    def __init__(
        self,
        project_root: Path | None = None,
        expert_registry: Any | None = None,
        auto_detect: bool = True,
        advanced_state: bool = True,
    ):
        """
        Initialize workflow executor.

        Args:
            project_root: Root directory for the project
            expert_registry: Optional ExpertRegistry instance for expert consultation
            auto_detect: Whether to enable automatic workflow detection and recommendation
            advanced_state: Whether to use advanced state management (validation, migration, recovery)
        """
        self.project_root = project_root or Path.cwd()
        self.state: WorkflowState | None = None
        self.workflow: Workflow | None = None
        self._workflow_path: Path | None = None
        self.expert_registry = expert_registry
        self.auto_detect = auto_detect
        self.advanced_state = advanced_state
        self.recommender: WorkflowRecommender | None = None
        self.state_manager: AdvancedStateManager | None = None

        # Initialize advanced state manager if enabled
        if self.advanced_state:
            state_dir = self._state_dir()
            self.state_manager = AdvancedStateManager(state_dir, compression=False)
        else:
            self.state_manager = None

        if auto_detect:
            self.recommender = WorkflowRecommender(
                project_root=self.project_root,
                workflows_dir=self.project_root / "workflows",
            )

    def recommend_workflow(
        self,
        user_query: str | None = None,
        file_count: int | None = None,
        scope_description: str | None = None,
    ) -> WorkflowRecommendation:
        """
        Recommend a workflow based on project characteristics.

        Args:
            user_query: User's query or request
            file_count: Estimated number of files to change
            scope_description: Description of the change scope

        Returns:
            WorkflowRecommendation with recommendation details

        Raises:
            ValueError: If auto_detect is disabled
        """
        if not self.auto_detect or not self.recommender:
            raise ValueError(
                "Auto-detection is disabled. Enable auto_detect in __init__ or use load_workflow()"
            )

        return self.recommender.recommend(
            user_query=user_query,
            file_count=file_count,
            scope_description=scope_description,
            auto_load=True,
        )

    def load_workflow(self, workflow_path: Path) -> Workflow:
        """
        Load a workflow from file.

        Args:
            workflow_path: Path to workflow YAML file

        Returns:
            Loaded Workflow object
        """
        self._workflow_path = workflow_path
        self.workflow = WorkflowParser.parse_file(workflow_path)
        return self.workflow

    def start(self, workflow: Workflow | None = None) -> WorkflowState:
        """
        Start workflow execution.

        Args:
            workflow: Workflow to execute (if not already loaded)

        Returns:
            Initial workflow state
        """
        if workflow:
            self.workflow = workflow

        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow() first.")

        self.state = WorkflowState(
            workflow_id=self.workflow.id,
            started_at=datetime.now(),
            current_step=self.workflow.steps[0].id if self.workflow.steps else None,
            status="running",
        )

        # Persist workflow path for resumption
        if self._workflow_path:
            self.state.variables["_workflow_path"] = str(self._workflow_path)

        self.save_state()

        return self.state

    def get_current_step(self) -> WorkflowStep | None:
        """Get the current workflow step."""
        if not self.state or not self.workflow:
            return None

        current_step_id = self.state.current_step
        if not current_step_id:
            return None

        for step in self.workflow.steps:
            if step.id == current_step_id:
                return step

        return None

    def get_next_step(self) -> WorkflowStep | None:
        """Get the next workflow step after the current one."""
        current_step = self.get_current_step()
        if not current_step or not current_step.next:
            return None
        if not self.workflow:
            return None

        for step in self.workflow.steps:
            if step.id == current_step.next:
                return step

        return None

    def can_proceed(self) -> bool:
        """Check if workflow can proceed to next step."""
        if not self.state or not self.workflow:
            return False

        current_step = self.get_current_step()
        if not current_step:
            return False

        # Check if required artifacts exist
        for artifact_name in current_step.requires:
            if artifact_name not in self.state.artifacts:
                return False

            artifact = self.state.artifacts[artifact_name]
            if artifact.status != "complete":
                return False

        return True

    def mark_step_complete(
        self,
        step_id: str | None = None,
        artifacts: list[dict[str, Any]] | None = None,
    ):
        """
        Mark a step as complete.

        Args:
            step_id: Step ID (defaults to current step)
            artifacts: List of artifact information dictionaries
        """
        if not self.state:
            raise ValueError("Workflow not started")
        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow() first.")

        step_id = step_id or self.state.current_step
        if not step_id:
            raise ValueError("No step to complete")

        # Mark step as completed
        if step_id not in self.state.completed_steps:
            self.state.completed_steps.append(step_id)

        # Add artifacts
        if artifacts:
            for art_data in artifacts:
                artifact = Artifact(
                    name=art_data.get("name", ""),
                    path=art_data.get("path", ""),
                    status="complete",
                    created_by=step_id,
                    created_at=datetime.now(),
                    metadata=art_data.get("metadata", {}),
                )
                self.state.artifacts[artifact.name] = artifact

        # Move to next step
        current_step = None
        for step in self.workflow.steps:
            if step.id == step_id:
                current_step = step
                break

        if current_step and current_step.next:
            self.state.current_step = current_step.next
        else:
            # Workflow complete
            self.state.current_step = None
            self.state.status = "completed"

        self.save_state()

    def skip_step(self, step_id: str):
        """Skip a step."""
        if not self.state:
            raise ValueError("Workflow not started")
        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow() first.")

        if step_id not in self.state.skipped_steps:
            self.state.skipped_steps.append(step_id)

        # Find the step and move to next
        for step in self.workflow.steps:
            if step.id == step_id and step.next:
                self.state.current_step = step.next
                break

        self.save_state()

    def _state_dir(self) -> Path:
        """Directory for persisted workflow state."""
        return self.project_root / ".tapps-agents" / "workflow-state"

    def _state_path_for(self, workflow_id: str) -> Path:
        return self._state_dir() / f"workflow-{workflow_id}.json"

    def _last_state_path(self) -> Path:
        return self._state_dir() / "last.json"

    @staticmethod
    def _artifact_to_dict(artifact: Artifact) -> dict[str, Any]:
        return {
            "name": artifact.name,
            "path": artifact.path,
            "status": artifact.status,
            "created_by": artifact.created_by,
            "created_at": (
                artifact.created_at.isoformat() if artifact.created_at else None
            ),
            "metadata": artifact.metadata or {},
        }

    @staticmethod
    def _artifact_from_dict(data: dict[str, Any]) -> Artifact:
        created_at = data.get("created_at")
        return Artifact(
            name=data.get("name", ""),
            path=data.get("path", ""),
            status=data.get("status", "pending"),
            created_by=data.get("created_by"),
            created_at=datetime.fromisoformat(created_at) if created_at else None,
            metadata=data.get("metadata", {}) or {},
        )

    def _state_to_dict(self, state: WorkflowState) -> dict[str, Any]:
        artifacts = {
            k: self._artifact_to_dict(v) for k, v in (state.artifacts or {}).items()
        }
        return {
            "workflow_id": state.workflow_id,
            "started_at": state.started_at.isoformat(),
            "current_step": state.current_step,
            "completed_steps": list(state.completed_steps or []),
            "skipped_steps": list(state.skipped_steps or []),
            "artifacts": artifacts,
            "variables": state.variables or {},
            "status": state.status,
            "error": state.error,
        }

    def _state_from_dict(self, data: dict[str, Any]) -> WorkflowState:
        artifacts_data = data.get("artifacts", {}) or {}
        artifacts = {k: self._artifact_from_dict(v) for k, v in artifacts_data.items()}
        started_at = datetime.fromisoformat(data["started_at"])
        return WorkflowState(
            workflow_id=data["workflow_id"],
            started_at=started_at,
            current_step=data.get("current_step"),
            completed_steps=data.get("completed_steps", []) or [],
            skipped_steps=data.get("skipped_steps", []) or [],
            artifacts=artifacts,
            variables=data.get("variables", {}) or {},
            status=data.get("status", "running"),
            error=data.get("error"),
        )

    def save_state(self) -> Path | None:
        """
        Persist current workflow state (best-effort).

        Uses advanced state management if enabled, otherwise falls back to basic persistence.

        Returns:
            Path to the saved state file, or None if nothing was saved.
        """
        if not self.state:
            return None

        try:
            # Use advanced state manager if available
            if self.state_manager:
                return self.state_manager.save_state(self.state, self._workflow_path)

            # Fallback to basic persistence
            state_dir = self._state_dir()
            state_dir.mkdir(parents=True, exist_ok=True)
            state_path = self._state_path_for(self.state.workflow_id)

            data = self._state_to_dict(self.state)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Update last pointer for easy resume
            last_data = {
                "workflow_id": self.state.workflow_id,
                "state_file": str(state_path),
                "saved_at": datetime.now().isoformat(),
                "workflow_path": data.get("variables", {}).get("_workflow_path"),
            }
            with open(self._last_state_path(), "w", encoding="utf-8") as f:
                json.dump(last_data, f, indent=2)

            return state_path
        except Exception:
            return None

    def load_last_state(self, validate: bool = True) -> WorkflowState:
        """
        Load the most recently persisted workflow state and attach it to this executor.

        Uses advanced state management if enabled, with validation and migration support.

        Args:
            validate: Whether to validate state integrity (only used with advanced state)

        This also attempts to reload the workflow YAML referenced by state variables.
        """
        # Use advanced state manager if available
        if self.state_manager:
            try:
                state, metadata = self.state_manager.load_state(validate=validate)

                # Reload workflow if we have a path
                if metadata.workflow_path:
                    candidate = Path(metadata.workflow_path)
                    if not candidate.is_absolute():
                        candidate = self.project_root / candidate
                    if candidate.exists():
                        self.load_workflow(candidate)

                self.state = state
                return state
            except FileNotFoundError:
                # Fall through to basic loading if advanced manager fails
                pass

        # Fallback to basic loading
        last_path = self._last_state_path()
        if not last_path.exists():
            raise FileNotFoundError("No persisted workflow state found to resume")

        last_data = json.loads(last_path.read_text(encoding="utf-8"))
        state_file = last_data.get("state_file")
        if not state_file:
            raise ValueError("Invalid last state pointer (missing state_file)")

        state_path = Path(state_file)
        if not state_path.is_absolute():
            state_path = self.project_root / state_path
        if not state_path.exists():
            raise FileNotFoundError(
                f"Persisted workflow state file not found: {state_path}"
            )

        data = json.loads(state_path.read_text(encoding="utf-8"))
        state = self._state_from_dict(data)

        # Reload workflow if we have a path
        workflow_path = (state.variables or {}).get("_workflow_path")
        if workflow_path:
            candidate = Path(workflow_path)
            if not candidate.is_absolute():
                candidate = self.project_root / candidate
            if candidate.exists():
                self.load_workflow(candidate)

        self.state = state
        return state

    def step_requires_expert_consultation(
        self, step: WorkflowStep | None = None
    ) -> bool:
        """
        Check if a step requires expert consultation.

        Args:
            step: Optional workflow step (defaults to current step)

        Returns:
            True if step has experts configured in 'consults' field
        """
        step = step or self.get_current_step()
        if not step:
            return False

        return bool(step.consults and len(step.consults) > 0)

    async def consult_experts_for_step(
        self, query: str | None = None, step: WorkflowStep | None = None
    ) -> dict[str, Any] | None:
        """
        Automatically consult experts for a step if it has 'consults' configured.

        This is a convenience method that:
        1. Checks if the step has experts configured
        2. Generates a context-aware query if none provided
        3. Consults the experts automatically
        4. Returns the consultation result

        Args:
            query: Optional query (auto-generated from step context if not provided)
            step: Optional workflow step (defaults to current step)

        Returns:
            Consultation result dict if experts were consulted, None otherwise

        Raises:
            ValueError: If expert registry not available but step requires consultation
        """
        step = step or self.get_current_step()
        if not step:
            return None

        # Check if step requires expert consultation
        if not self.step_requires_expert_consultation(step):
            return None

        # Ensure expert registry is available
        if not self.expert_registry:
            raise ValueError(
                f"Step '{step.id}' requires expert consultation (consults: {step.consults}), "
                "but expert_registry not available. Provide expert_registry in WorkflowExecutor.__init__."
            )

        # Generate query if not provided
        if not query:
            # Build context-aware query from step information
            query_parts = [f"Agent: {step.agent}", f"Action: {step.action}"]
            if step.notes:
                query_parts.append(f"Context: {step.notes}")
            if step.metadata:
                context_info = step.metadata.get(
                    "context", step.metadata.get("description")
                )
                if context_info:
                    query_parts.append(f"Additional context: {context_info}")

            query = (
                "Please provide expert guidance for this workflow step: "
                + " | ".join(query_parts)
            )

        # Determine domain from expert IDs
        expert_ids = step.consults
        domain = "general"
        if expert_ids:
            # Extract domain from first expert ID (experts follow pattern: expert-{domain})
            first_expert = expert_ids[0]
            if first_expert.startswith("expert-"):
                domain = first_expert.replace("expert-", "")
            else:
                # Try to infer from expert ID format
                domain = (
                    first_expert.split("-")[-1] if "-" in first_expert else "general"
                )

        # Consult experts via registry
        consultation_result = await self.expert_registry.consult(
            query=query,
            domain=domain,
            include_all=True,  # Consult all experts for weighted decision
        )

        # Store consultation in workflow state for reference
        if self.state:
            if "expert_consultations" not in self.state.variables:
                self.state.variables["expert_consultations"] = {}
            self.state.variables["expert_consultations"][step.id] = {
                "query": query,
                "domain": domain,
                "experts_consulted": expert_ids,
                "weighted_answer": consultation_result.weighted_answer,
                "confidence": consultation_result.confidence,
                "consulted_at": datetime.now().isoformat(),
            }

        return {
            "query": query,
            "domain": domain,
            "experts_consulted": expert_ids,
            "weighted_answer": consultation_result.weighted_answer,
            "confidence": consultation_result.confidence,
            "agreement_level": consultation_result.agreement_level,
            "primary_expert": consultation_result.primary_expert,
            "all_experts_agreed": consultation_result.all_experts_agreed,
            "responses": consultation_result.responses,
        }

    async def consult_experts(
        self,
        query: str,
        domain: str | None = None,
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        """
        Consult experts for the current step.

        Args:
            query: The question or request for domain knowledge
            domain: Optional domain context (extracted from step if not provided)
            step: Optional workflow step (defaults to current step)

        Returns:
            Consultation result from expert registry

        Raises:
            ValueError: If expert registry not available or no experts to consult
        """
        if not self.expert_registry:
            raise ValueError(
                "Expert registry not available. Provide expert_registry in __init__."
            )

        step = step or self.get_current_step()
        if not step:
            raise ValueError("No current step available for expert consultation.")

        # Get experts to consult from step
        expert_ids = step.consults
        if not expert_ids:
            raise ValueError(
                f"Step '{step.id}' has no experts configured in 'consults' field."
            )

        # Determine domain from step or use provided domain
        if not domain:
            # Try to infer domain from expert ID or step metadata
            if expert_ids:
                # Assume first expert's domain (experts follow pattern: expert-{domain})
                first_expert = expert_ids[0]
                if first_expert.startswith("expert-"):
                    domain = first_expert.replace("expert-", "")
                else:
                    domain = "general"
            else:
                domain = "general"

        # Consult experts via registry
        # The registry handles weighted aggregation
        consultation_result = await self.expert_registry.consult(
            query=query,
            domain=domain,
            include_all=True,  # Consult all experts for weighted decision
        )

        return {
            "query": query,
            "domain": domain,
            "experts_consulted": expert_ids,
            "weighted_answer": consultation_result.weighted_answer,
            "confidence": consultation_result.confidence,
            "agreement_level": consultation_result.agreement_level,
            "primary_expert": consultation_result.primary_expert,
            "all_experts_agreed": consultation_result.all_experts_agreed,
            "responses": consultation_result.responses,
        }

    def get_status(self) -> dict[str, Any]:
        """Get workflow execution status."""
        if not self.state:
            return {"status": "not_started"}

        current_step = self.get_current_step()

        return {
            "workflow_id": self.state.workflow_id,
            "status": self.state.status,
            "current_step": self.state.current_step,
            "current_step_details": (
                {
                    "id": current_step.id if current_step else None,
                    "agent": current_step.agent if current_step else None,
                    "action": current_step.action if current_step else None,
                    "consults": current_step.consults if current_step else [],
                }
                if current_step
                else None
            ),
            "completed_steps": self.state.completed_steps,
            "skipped_steps": self.state.skipped_steps,
            "artifacts_count": len(self.state.artifacts),
            "can_proceed": self.can_proceed(),
            "expert_registry_available": self.expert_registry is not None,
        }
