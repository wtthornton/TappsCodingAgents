"""
Orchestrator Agent - Coordinates workflows and makes gate decisions.
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.workflow import Workflow, WorkflowExecutor, WorkflowParser


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Coordinates YAML-defined workflows and makes gate decisions.

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify

    Responsibilities:
    - Load and execute workflows
    - Make gate decisions based on scoring/conditions
    - Route to Greenfield/Brownfield workflows
    - Track workflow state
    - Coordinate agent execution
    """

    def __init__(self, config: Any | None = None):
        super().__init__(
            agent_id="orchestrator", agent_name="Orchestrator", config=config
        )
        self.workflow_executor: WorkflowExecutor | None = None
        self.current_workflow: Workflow | None = None

    async def activate(self, project_root: Path | None = None):
        """Activate the orchestrator agent."""
        await super().activate(project_root)

        # Initialize workflow executor
        if project_root:
            self.workflow_executor = WorkflowExecutor(project_root=project_root)
        else:
            self.workflow_executor = WorkflowExecutor()

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute orchestrator commands.

        Commands:
        - *workflow-list: List available workflows
        - *workflow-start {id}: Start a workflow
        - *workflow-status: Show current workflow status
        - *workflow-next: Show next step
        - *workflow-skip {step}: Skip an optional step
        - *workflow-resume: Resume interrupted workflow
        - *gate {condition}: Make a gate decision
        """
        if command == "*workflow-list":
            return await self._list_workflows()
        elif command == "*workflow-start":
            workflow_id = kwargs.get("workflow_id")
            if not workflow_id:
                return {"error": "workflow_id required"}
            return await self._start_workflow(workflow_id)
        elif command == "*workflow-status":
            return await self._get_workflow_status()
        elif command == "*workflow-next":
            return await self._get_next_step()
        elif command == "*workflow-skip":
            step_id = kwargs.get("step_id")
            if not step_id:
                return {"error": "step_id required"}
            return await self._skip_step(step_id)
        elif command == "*workflow-resume":
            return await self._resume_workflow()
        elif command == "*gate":
            condition = kwargs.get("condition")
            scoring_data = kwargs.get("scoring_data", {})
            return await self._make_gate_decision(condition, scoring_data)
        elif command == "*help":
            return await self._help()
        else:
            return {"error": f"Unknown command: {command}"}

    async def _list_workflows(self) -> dict[str, Any]:
        """List available workflows."""
        workflows_dir = Path("workflows")
        if not workflows_dir.exists():
            return {"workflows": [], "message": "No workflows directory found"}

        workflow_files = list(workflows_dir.glob("*.yaml")) + list(
            workflows_dir.glob("*.yml")
        )

        workflows = []
        for workflow_file in workflow_files:
            try:
                workflow = WorkflowParser.parse_file(workflow_file)
                workflows.append(
                    {
                        "id": workflow.id,
                        "name": workflow.name,
                        "description": workflow.description,
                        "version": workflow.version,
                        "type": workflow.type.value,
                        "file": str(workflow_file),
                    }
                )
            except Exception as e:
                workflows.append(
                    {
                        "id": workflow_file.stem,
                        "name": workflow_file.name,
                        "error": str(e),
                    }
                )

        return {"workflows": workflows}

    async def _start_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Start a workflow."""
        if not self.workflow_executor:
            return {"error": "Workflow executor not initialized"}

        # Find workflow file
        workflows_dir = Path("workflows")
        workflow_file = None

        for ext in [".yaml", ".yml"]:
            candidate = workflows_dir / f"{workflow_id}{ext}"
            if candidate.exists():
                workflow_file = candidate
                break

        if not workflow_file:
            return {"error": f"Workflow '{workflow_id}' not found"}

        try:
            # Load and start workflow
            workflow = self.workflow_executor.load_workflow(workflow_file)
            self.current_workflow = workflow
            state = self.workflow_executor.start()

            return {
                "success": True,
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "status": state.status,
                "current_step": state.current_step,
                "message": f"Workflow '{workflow.name}' started",
            }
        except Exception as e:
            return {"error": f"Failed to start workflow: {str(e)}"}

    async def _get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status."""
        if not self.workflow_executor:
            return {"error": "No workflow active"}

        status = self.workflow_executor.get_status()
        return status

    async def _get_next_step(self) -> dict[str, Any]:
        """Get next workflow step."""
        if not self.workflow_executor:
            return {"error": "No workflow active"}

        next_step = self.workflow_executor.get_next_step()
        if not next_step:
            return {"message": "No next step (workflow may be complete)"}

        return {
            "next_step": {
                "id": next_step.id,
                "agent": next_step.agent,
                "action": next_step.action,
                "context_tier": next_step.context_tier,
                "requires": next_step.requires,
                "creates": next_step.creates,
            }
        }

    async def _skip_step(self, step_id: str) -> dict[str, Any]:
        """Skip an optional step."""
        if not self.workflow_executor:
            return {"error": "No workflow active"}

        try:
            self.workflow_executor.skip_step(step_id)
            return {
                "success": True,
                "message": f"Step '{step_id}' skipped",
                "current_step": (
                    self.workflow_executor.state.current_step
                    if self.workflow_executor.state
                    else None
                ),
            }
        except Exception as e:
            return {"error": f"Failed to skip step: {str(e)}"}

    async def _resume_workflow(self) -> dict[str, Any]:
        """Resume an interrupted workflow."""
        if not self.workflow_executor:
            return {"error": "Workflow executor not initialized"}

        try:
            state = self.workflow_executor.load_last_state()
            self.current_workflow = self.workflow_executor.workflow

            return {
                "success": True,
                "workflow_id": state.workflow_id,
                "status": state.status,
                "current_step": state.current_step,
                "completed_steps": state.completed_steps,
                "skipped_steps": state.skipped_steps,
                "artifacts": {
                    k: {"path": v.path, "status": v.status}
                    for k, v in (state.artifacts or {}).items()
                },
                "message": "Workflow resumed from persisted state",
            }
        except FileNotFoundError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to resume workflow: {str(e)}"}

    async def _make_gate_decision(
        self, condition: str | None, scoring_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Make a gate decision based on condition and scoring data.

        Args:
            condition: Gate condition string (e.g., "scoring.passed == true")
            scoring_data: Scoring results from reviewer agent

        Returns:
            Gate decision with pass/fail status
        """
        if not condition:
            # Default gate: check if scoring passed
            passed = scoring_data.get("passed", False)
            overall_score = scoring_data.get("overall_score", 0)

            return {
                "passed": passed,
                "overall_score": overall_score,
                "message": "Gate passed" if passed else "Gate failed",
            }

        # Evaluate condition (simplified - in production, use a proper expression evaluator)
        try:
            # Simple condition evaluation
            if "scoring.passed" in condition:
                passed = scoring_data.get("passed", False)
                if "==" in condition and "true" in condition:
                    gate_passed = passed
                elif "==" in condition and "false" in condition:
                    gate_passed = not passed
                else:
                    gate_passed = passed

                return {
                    "passed": gate_passed,
                    "condition": condition,
                    "scoring": scoring_data,
                    "message": "Gate passed" if gate_passed else "Gate failed",
                }

            # Check score thresholds
            if "overall_score" in condition or "overall_min" in condition:
                overall_score = scoring_data.get("overall_score", 0)
                # Extract threshold from condition (simplified)
                threshold = 70  # Default
                if ">=" in condition:
                    try:
                        threshold = int(condition.split(">=")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass

                gate_passed = overall_score >= threshold
                return {
                    "passed": gate_passed,
                    "overall_score": overall_score,
                    "threshold": threshold,
                    "message": f"Gate {'passed' if gate_passed else 'failed'}: {overall_score} >= {threshold}",
                }

            return {
                "passed": False,
                "error": f"Unsupported condition: {condition}",
                "message": "Gate evaluation failed",
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Gate evaluation error",
            }

    async def _help(self) -> dict[str, Any]:
        """Show help for orchestrator commands."""
        return {
            "commands": {
                "*workflow-list": "List available workflows",
                "*workflow-start {workflow_id}": "Start a workflow",
                "*workflow-status": "Show current workflow status",
                "*workflow-next": "Show next step in workflow",
                "*workflow-skip {step_id}": "Skip an optional step",
                "*workflow-resume": "Resume interrupted workflow",
                "*gate {condition}": "Make a gate decision based on condition and scoring",
                "*help": "Show this help message",
            },
            "description": "Orchestrator Agent coordinates workflows and makes gate decisions",
        }
