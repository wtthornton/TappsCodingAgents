"""
Workflow Analyzer - Analyzes workflow adherence and execution patterns.
"""

from typing import Any


class WorkflowAnalyzer:
    """
    Analyzes workflow adherence and execution patterns.
    
    Checks:
    - Steps executed vs steps required
    - Documentation artifacts created
    - Workflow deviations
    - Completion rates
    """

    def analyze_workflow(
        self,
        workflow_id: str,
        workflow_state: dict[str, Any],
        workflow_definition: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analyze workflow execution.
        
        Args:
            workflow_id: Workflow identifier
            workflow_state: Workflow execution state
            workflow_definition: Workflow YAML definition (if available)
        
        Returns:
            Dictionary with workflow analysis
        """
        # Check step completion
        step_analysis = self.check_step_completion(workflow_definition, workflow_state)
        
        # Verify artifacts
        artifact_analysis = self.verify_artifacts(workflow_definition, workflow_state)
        
        # Identify deviations
        deviations = self.identify_deviations(workflow_definition, workflow_state)
        
        return {
            "workflow_id": workflow_id,
            "step_analysis": step_analysis,
            "artifact_analysis": artifact_analysis,
            "deviations": deviations,
            "recommendations": self._generate_recommendations(step_analysis, deviations)
        }

    def check_step_completion(
        self,
        workflow_definition: dict[str, Any] | None,
        workflow_state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Check if all required steps were executed.
        
        Returns:
            Dictionary with step completion analysis
        """
        steps_executed = workflow_state.get("step_executions", [])
        executed_count = len(steps_executed)
        
        # Try to determine required steps
        required_count = executed_count  # Default: assume all executed steps were required
        if workflow_definition:
            steps = workflow_definition.get("steps", [])
            required_count = len(steps)
        
        completion_rate = (executed_count / required_count) if required_count > 0 else 1.0
        
        # Identify missing steps (if definition available)
        missing_steps = []
        if workflow_definition:
            defined_step_ids = {step.get("id") for step in workflow_definition.get("steps", [])}
            executed_step_ids = {step.get("step_id") for step in steps_executed}
            missing_step_ids = defined_step_ids - executed_step_ids
            missing_steps = list(missing_step_ids)
        
        return {
            "steps_required": required_count,
            "steps_executed": executed_count,
            "completion_rate": completion_rate,
            "missing_steps": missing_steps,
            "executed_steps": [step.get("step_id") for step in steps_executed],
        }

    def verify_artifacts(
        self,
        workflow_definition: dict[str, Any] | None,
        workflow_state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Verify documentation artifacts were created.
        
        Returns:
            Dictionary with artifact analysis
        """
        # Get expected artifacts from workflow definition
        expected_artifacts = []
        if workflow_definition:
            # Simple Mode workflows typically create docs in docs/workflows/simple-mode/
            workflow_type = workflow_definition.get("type", "")
            if "build" in workflow_type.lower():
                expected_artifacts = [
                    "step1-enhanced-prompt.md",
                    "step2-user-stories.md",
                    "step3-architecture.md",
                    "step4-design.md",
                    "step6-review.md",
                    "step7-testing.md",
                ]
        
        # Get created artifacts from workflow state
        created_artifacts = workflow_state.get("artifacts", [])
        created_names = [artifact.get("name", "") for artifact in created_artifacts]
        
        # Find missing artifacts
        missing_artifacts = [art for art in expected_artifacts if art not in created_names]
        
        creation_rate = (len(created_names) / len(expected_artifacts)) if expected_artifacts else 1.0
        
        return {
            "artifacts_expected": expected_artifacts,
            "artifacts_created": created_names,
            "artifacts_missing": missing_artifacts,
            "creation_rate": creation_rate,
        }

    def identify_deviations(
        self,
        workflow_definition: dict[str, Any] | None,
        workflow_state: dict[str, Any]
    ) -> list[dict]:
        """
        Identify workflow deviations.
        
        Returns:
            List of deviation dictionaries
        """
        deviations = []
        
        # Check step completion
        step_analysis = self.check_step_completion(workflow_definition, workflow_state)
        if step_analysis.get("completion_rate", 1.0) < 1.0:
            deviations.append({
                "type": "step_skipped",
                "description": f"Only {step_analysis['steps_executed']}/{step_analysis['steps_required']} steps executed",
                "impact": "high",
                "recommendation": "Ensure all workflow steps are executed for complete results",
            })
        
        # Check artifacts
        artifact_analysis = self.verify_artifacts(workflow_definition, workflow_state)
        if artifact_analysis.get("creation_rate", 1.0) < 1.0:
            deviations.append({
                "type": "artifact_missing",
                "description": f"Missing {len(artifact_analysis['artifacts_missing'])} documentation artifacts",
                "impact": "medium",
                "recommendation": "Create all required documentation artifacts",
            })
        
        return deviations

    def _generate_recommendations(
        self,
        step_analysis: dict[str, Any],
        deviations: list[dict]
    ) -> list[dict]:
        """Generate recommendations based on workflow analysis."""
        recommendations = []
        
        # Add deviation-based recommendations
        recommendations.extend(deviations)
        
        # Add completion-based recommendations
        completion_rate = step_analysis.get("completion_rate", 1.0)
        if completion_rate < 0.8:
            recommendations.append({
                "type": "workflow",
                "description": f"Workflow completion rate is {completion_rate:.1%} (below 80% threshold)",
                "impact": "high",
                "recommendation": "Investigate why workflow steps are being skipped",
            })
        
        return recommendations
