"""
Brownfield Orchestrator - Coordinates brownfield system review workflow.

Coordinates: BrownfieldReviewOrchestrator → Report Generation

Provides Simple Mode integration for brownfield system analysis and expert creation.
"""

import logging
from typing import Any

from tapps_agents.context7.agent_integration import get_context7_helper
from tapps_agents.core.brownfield_review import BrownfieldReviewOrchestrator

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator

logger = logging.getLogger(__name__)


class BrownfieldOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for brownfield system review."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for brownfield review workflow."""
        return ["brownfield-review"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute brownfield review workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results including:
            - success: bool
            - analysis: BrownfieldAnalysisResult
            - experts_created: list[ExpertConfig]
            - rag_results: dict[str, IngestionResult]
            - report: str
            - errors: list[str]
            - warnings: list[str]
        """
        parameters = parameters or {}
        
        # Extract parameters
        auto = parameters.get("auto", True)  # Default to auto for Simple Mode
        dry_run = parameters.get("dry_run", False)
        include_context7 = not parameters.get("no_context7", False)
        parameters.get("output_dir")
        resume = parameters.get("resume", False)
        resume_from = parameters.get("resume_from") or parameters.get("resume_from_step")

        # Initialize Context7 helper if available
        context7_helper = None
        if include_context7:
            try:
                context7_helper = get_context7_helper(None, self.config, self.project_root)
            except Exception as e:
                logger.warning(f"Context7 helper not available: {e}")

        # Initialize orchestrator
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=self.project_root,
            context7_helper=context7_helper,
            dry_run=dry_run,
        )

        # Handle resume if requested
        if resume and resume_from:
            # Load state and resume from specific step
            # This would be implemented in the orchestrator
            logger.info(f"Resuming from step: {resume_from}")

        try:
            # Execute review
            result = await orchestrator.review(
                auto=auto,
                include_context7=include_context7,
                resume=resume,
                resume_from=resume_from,
            )

            # Format result for Simple Mode
            return {
                "success": len(result.errors) == 0,
                "analysis": {
                    "languages": result.analysis.languages,
                    "frameworks": result.analysis.frameworks,
                    "dependencies": result.analysis.dependencies,
                    "domains": [
                        {
                            "domain": d.domain,
                            "confidence": d.confidence,
                            "reasoning": d.reasoning,
                        }
                        for d in result.analysis.domains
                    ],
                },
                "experts_created": [
                    {
                        "expert_id": e.expert_id,
                        "expert_name": e.expert_name,
                        "primary_domain": e.primary_domain,
                        "rag_enabled": e.rag_enabled,
                        "knowledge_base_dir": str(e.knowledge_base_dir) if e.knowledge_base_dir else None,
                    }
                    for e in result.experts_created
                ],
                "rag_results": {
                    k: {
                        "entries_ingested": v.entries_ingested,
                        "entries_failed": v.entries_failed,
                        "source_type": v.source_type,
                    }
                    for k, v in result.rag_results.items()
                },
                "report": result.report,
                "errors": result.errors,
                "warnings": result.warnings,
                "execution_time": result.execution_time,
                "dry_run": result.dry_run,
            }
        except Exception as e:
            logger.error(f"Brownfield review failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "errors": [str(e)],
            }
