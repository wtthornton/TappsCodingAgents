"""Proactive orchestrator for expert consultation."""

import logging
from typing import Any

from .expert_engine import ExpertEngine, ExpertRoutingPlan

logger = logging.getLogger(__name__)


class ProactiveOrchestrator:
    """Proactively consults experts before agents need them."""

    def __init__(self, expert_engine: ExpertEngine):
        self.expert_engine = expert_engine

    def pre_fetch_for_step(self, step_context: dict[str, Any]) -> list[ExpertRoutingPlan]:
        """Pre-fetch knowledge for upcoming workflow step."""
        plans = []
        
        # Detect knowledge needs for this step
        from .knowledge_need_detector import KnowledgeNeedDetector
        detector = KnowledgeNeedDetector()
        needs = detector.detect_from_workflow(step_context)
        
        # Generate routing plans
        for need in needs:
            plan = self.expert_engine.generate_routing_plan(need)
            plans.append(plan)
        
        return plans

