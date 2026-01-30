"""Validation Orchestrator - Compare implementations and identify optimizations."""

from pathlib import Path
from typing import Any

from tapps_agents.agents.architect.agent import ArchitectAgent
from tapps_agents.agents.enhancer.agent import EnhancerAgent
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.core.config import ProjectConfig

from ..intent_parser import Intent
from ..workflows.validation_workflow import ValidationResult, ValidationWorkflow
from .base import SimpleModeOrchestrator


class ValidateOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for validation workflow."""

    def __init__(self, project_root: Path, config: ProjectConfig):
        """
        Initialize validation orchestrator.

        Args:
            project_root: Project root directory
            config: Project configuration
        """
        super().__init__(project_root, config)
        self.workflow: ValidationWorkflow | None = None

    async def execute(
        self,
        intent: Intent,
        parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute validation workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with validation results
        """
        if parameters is None:
            parameters = {}

        prompt = parameters.get("prompt", intent.original_input)
        existing_code_ref = parameters.get("existing_code_ref")

        # Extract existing code reference from prompt analysis if available
        prompt_analysis = parameters.get("prompt_analysis")
        if not existing_code_ref and prompt_analysis:
            if hasattr(prompt_analysis, 'existing_code_refs') and prompt_analysis.existing_code_refs:
                ref = prompt_analysis.existing_code_refs[0]
                if ref.file_path:
                    existing_code_ref = ref.file_path
                    if ref.line_range:
                        existing_code_ref = f"{ref.file_path}:{ref.line_range}"

        try:
            # Initialize agents
            agents = await self._initialize_agents()

            # Create validation workflow
            self.workflow = ValidationWorkflow(agents=agents)

            # Execute validation
            result = await self.workflow.execute(
                prompt=prompt,
                existing_code_ref=existing_code_ref,
                project_root=self.project_root
            )

            # Format and save report
            report = self._format_validation_report(result)
            report_path = self._save_report(report, "validation-report.md")

            return {
                "success": True,
                "workflow": "validation",
                "existing_code_quality": result.existing_code_quality,
                "proposed_design_quality": result.proposed_design_quality,
                "decision": result.decision,
                "rationale": result.rationale,
                "optimization_count": len(result.optimization_recommendations),
                "high_value_optimizations": len([
                    r for r in result.optimization_recommendations
                    if r.get("priority") == "high"
                ]),
                "report_path": str(report_path),
                "report": report
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Validation workflow failed: {str(e)}",
                "workflow": "validation"
            }
        finally:
            # Cleanup
            await self._cleanup_agents(agents)

    async def _initialize_agents(self) -> dict[str, Any]:
        """Initialize required agents."""
        agents = {}

        try:
            # Enhancer
            enhancer = EnhancerAgent(config=self.config)
            await enhancer.activate(self.project_root)
            agents["enhancer"] = enhancer

            # Reviewer
            reviewer = ReviewerAgent(config=self.config)
            await reviewer.activate(self.project_root)
            agents["reviewer"] = reviewer

            # Architect
            architect = ArchitectAgent(config=self.config)
            await architect.activate(self.project_root)
            agents["architect"] = architect

        except Exception as e:
            print(f"⚠️  Warning: Some agents failed to initialize: {e}")
            # Continue with available agents

        return agents

    async def _cleanup_agents(self, agents: dict[str, Any]) -> None:
        """Cleanup agents."""
        for agent in agents.values():
            try:
                if hasattr(agent, 'close'):
                    await agent.close()
            except Exception:
                pass  # Ignore cleanup errors

    def _format_validation_report(self, result: ValidationResult) -> str:
        """Format validation report as markdown."""
        from datetime import datetime

        report = f"""# Validation Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Existing Code Quality:** {result.existing_code_quality:.1f}/10
**Proposed Design Quality:** {result.proposed_design_quality:.1f}/10
**Decision:** {result.decision.upper().replace('_', ' ')}

---

## Executive Summary

{result.rationale}

---

## High-Value Optimizations (Implement Immediately) ⭐⭐⭐

{self._format_recommendations(result.optimization_recommendations, priority="high")}

---

## Medium-Value Optimizations (Consider) ⭐⭐

{self._format_recommendations(result.optimization_recommendations, priority="medium")}

---

## Low-Value Enhancements (Skip - YAGNI) ⭐

{self._format_recommendations(result.optimization_recommendations, priority="low")}

---

## Implementation Plan

**Phase 1:** High-value optimizations ({self._total_effort(result.optimization_recommendations, "high")} min)
**Phase 2:** Medium-value optimizations (optional)

**Total Impact:** {self._total_impact(result.optimization_recommendations, "high")}% improvement

---

## Next Steps

"""

        if result.decision == "keep_existing":
            report += """
1. Review and implement high-value optimizations
2. Update tests if needed
3. Document changes
4. Monitor performance improvements
"""
        else:
            report += """
1. Proceed with new implementation
2. Migrate existing functionality
3. Update tests
4. Phase out old code
"""

        return report

    def _format_recommendations(
        self,
        recommendations: list,
        priority: str
    ) -> str:
        """Format recommendations by priority."""
        filtered = [r for r in recommendations if r.get("priority") == priority]

        if not filtered:
            return "_No recommendations at this priority level_\n"

        result = []
        for i, rec in enumerate(filtered, 1):
            result.append(f"""
### {i}. {rec.get('name', 'Optimization')}

**Impact:** {rec.get('impact', 0)}% improvement
**Effort:** {rec.get('effort', 0)} minutes
**Description:** {rec.get('description', 'No description')}
""")

        return "\n".join(result)

    def _total_effort(self, recommendations: list, priority: str) -> int:
        """Calculate total effort for recommendations."""
        filtered = [r for r in recommendations if r.get("priority") == priority]
        return sum(r.get("effort", 0) for r in filtered)

    def _total_impact(self, recommendations: list, priority: str) -> int:
        """Calculate total impact for recommendations."""
        filtered = [r for r in recommendations if r.get("priority") == priority]
        if not filtered:
            return 0
        return int(sum(r.get("impact", 0) for r in filtered) / len(filtered))

    def _save_report(self, report: str, filename: str) -> Path:
        """Save report to file."""
        report_path = self.project_root / "docs" / "feedback" / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print(f"\n📄 Validation report saved to: {report_path}\n")
        return report_path
