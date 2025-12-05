"""
Workflow Executor - Execute YAML workflow definitions.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from .models import Workflow, WorkflowStep, WorkflowState, Artifact
from .parser import WorkflowParser
from .recommender import WorkflowRecommender, WorkflowRecommendation


class WorkflowExecutor:
    """Executor for workflow definitions."""
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        expert_registry: Optional[Any] = None,
        auto_detect: bool = True
    ):
        """
        Initialize workflow executor.
        
        Args:
            project_root: Root directory for the project
            expert_registry: Optional ExpertRegistry instance for expert consultation
            auto_detect: Whether to enable automatic workflow detection and recommendation
        """
        self.project_root = project_root or Path.cwd()
        self.state: Optional[WorkflowState] = None
        self.workflow: Optional[Workflow] = None
        self.expert_registry = expert_registry
        self.auto_detect = auto_detect
        self.recommender: Optional[WorkflowRecommender] = None
        
        if auto_detect:
            self.recommender = WorkflowRecommender(
                project_root=self.project_root,
                workflows_dir=self.project_root / "workflows"
            )
    
    def recommend_workflow(
        self,
        user_query: Optional[str] = None,
        file_count: Optional[int] = None,
        scope_description: Optional[str] = None
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
            raise ValueError("Auto-detection is disabled. Enable auto_detect in __init__ or use load_workflow()")
        
        return self.recommender.recommend(
            user_query=user_query,
            file_count=file_count,
            scope_description=scope_description,
            auto_load=True
        )
    
    def load_workflow(self, workflow_path: Path) -> Workflow:
        """
        Load a workflow from file.
        
        Args:
            workflow_path: Path to workflow YAML file
        
        Returns:
            Loaded Workflow object
        """
        self.workflow = WorkflowParser.parse_file(workflow_path)
        return self.workflow
    
    def start(self, workflow: Optional[Workflow] = None) -> WorkflowState:
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
            status="running"
        )
        
        return self.state
    
    def get_current_step(self) -> Optional[WorkflowStep]:
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
    
    def get_next_step(self) -> Optional[WorkflowStep]:
        """Get the next workflow step after the current one."""
        current_step = self.get_current_step()
        if not current_step or not current_step.next:
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
        step_id: Optional[str] = None,
        artifacts: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Mark a step as complete.
        
        Args:
            step_id: Step ID (defaults to current step)
            artifacts: List of artifact information dictionaries
        """
        if not self.state:
            raise ValueError("Workflow not started")
        
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
                    metadata=art_data.get("metadata", {})
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
    
    def skip_step(self, step_id: str):
        """Skip a step."""
        if not self.state:
            raise ValueError("Workflow not started")
        
        if step_id not in self.state.skipped_steps:
            self.state.skipped_steps.append(step_id)
        
        # Find the step and move to next
        for step in self.workflow.steps:
            if step.id == step_id and step.next:
                self.state.current_step = step.next
                break
    
    async def consult_experts(
        self,
        query: str,
        domain: Optional[str] = None,
        step: Optional[WorkflowStep] = None
    ) -> Dict[str, Any]:
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
            raise ValueError("Expert registry not available. Provide expert_registry in __init__.")
        
        step = step or self.get_current_step()
        if not step:
            raise ValueError("No current step available for expert consultation.")
        
        # Get experts to consult from step
        expert_ids = step.consults
        if not expert_ids:
            raise ValueError(f"Step '{step.id}' has no experts configured in 'consults' field.")
        
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
            include_all=True  # Consult all experts for weighted decision
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
            "responses": consultation_result.responses
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get workflow execution status."""
        if not self.state:
            return {"status": "not_started"}
        
        current_step = self.get_current_step()
        
        return {
            "workflow_id": self.state.workflow_id,
            "status": self.state.status,
            "current_step": self.state.current_step,
            "current_step_details": {
                "id": current_step.id if current_step else None,
                "agent": current_step.agent if current_step else None,
                "action": current_step.action if current_step else None,
                "consults": current_step.consults if current_step else []
            } if current_step else None,
            "completed_steps": self.state.completed_steps,
            "skipped_steps": self.state.skipped_steps,
            "artifacts_count": len(self.state.artifacts),
            "can_proceed": self.can_proceed(),
            "expert_registry_available": self.expert_registry is not None
        }

