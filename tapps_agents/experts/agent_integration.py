"""
Agent Integration with Expert System

Provides helper methods and patterns for agents to integrate with the expert system.
Agents can use these utilities to consult experts during their workflows.
"""

import logging
from pathlib import Path

from .expert_registry import TECHNICAL_DOMAINS, ConsultationResult, ExpertRegistry


logger = logging.getLogger(__name__)


class ExpertSupportMixin:
    """
    Mixin class that provides expert consultation capabilities to agents.

    Agents can inherit from this mixin to gain access to expert consultation
    without modifying their core functionality.

    Usage:
        class MyAgent(BaseAgent, ExpertSupportMixin):
            async def activate(self, project_root: Optional[Path] = None):
                await super().activate(project_root)
                await self._initialize_expert_support(project_root)

            async def my_method(self):
                result = await self._consult_expert(
                    query="How should I handle this?",
                    domain="security",
                    prioritize_builtin=True
                )
    """

    def __init__(self, *args, **kwargs):
        """Initialize expert support mixin."""
        super().__init__(*args, **kwargs)
        self.expert_registry: ExpertRegistry | None = None

    async def _initialize_expert_support(
        self,
        project_root: Path | None = None,
        domains_file: Path | None = None,
        experts_config_file: Path | None = None,
    ) -> None:
        """
        Initialize expert registry for this agent.

        Args:
            project_root: Project root directory
            domains_file: Optional path to domains.md file
            experts_config_file: Optional path to experts.yaml file
        """
        if not project_root:
            return

        # Try to load from domains.md first
        if not domains_file:
            domains_file = project_root / ".tapps-agents" / "domains.md"

        if domains_file and domains_file.exists():
            try:
                self.expert_registry = ExpertRegistry.from_domains_file(domains_file)
                return
            except Exception:
                logger.debug("Failed to load expert registry from domains.md", exc_info=True)

        # Try to load from experts.yaml
        if not experts_config_file:
            experts_config_file = project_root / ".tapps-agents" / "experts.yaml"

        if experts_config_file and experts_config_file.exists():
            try:
                # Try to load domain config if available
                domain_config = None
                if domains_file and domains_file.exists():
                    from .domain_config import DomainConfigParser

                    domain_config = DomainConfigParser.parse(domains_file)

                self.expert_registry = ExpertRegistry.from_config_file(
                    experts_config_file, domain_config=domain_config
                )
                return
            except Exception:
                logger.debug("Failed to load expert registry from experts.yaml", exc_info=True)

        # Fallback: create registry with built-in experts only
        try:
            self.expert_registry = ExpertRegistry(domain_config=None, load_builtin=True)
        except Exception:
            self.expert_registry = None

    async def _consult_expert(
        self,
        query: str,
        domain: str,
        prioritize_builtin: bool | None = None,
        include_all: bool = True,
    ) -> ConsultationResult | None:
        """
        Consult experts on a domain question.

        Args:
            query: The question to ask experts
            domain: Domain context (e.g., "security", "performance-optimization")
            prioritize_builtin: If True, prioritize built-in experts for technical domains.
                               If False, prioritize customer experts for business domains.
                               If None, auto-determine based on domain type.
            include_all: Whether to consult all experts or just primary

        Returns:
            ConsultationResult if successful, None otherwise
        """
        if not self.expert_registry:
            return None

        # Auto-determine prioritize_builtin if not specified
        if prioritize_builtin is None:
            prioritize_builtin = domain in TECHNICAL_DOMAINS

        try:
            return await self.expert_registry.consult(
                query=query,
                domain=domain,
                include_all=include_all,
                prioritize_builtin=prioritize_builtin,
            )
        except Exception:
            return None

    async def _consult_builtin_expert(
        self, query: str, domain: str, include_all: bool = True
    ) -> ConsultationResult | None:
        """
        Convenience method to consult built-in experts for technical domains.

        Args:
            query: The question to ask
            domain: Technical domain (e.g., "security", "accessibility")
            include_all: Whether to consult all experts or just primary

        Returns:
            ConsultationResult if successful, None otherwise
        """
        return await self._consult_expert(
            query=query, domain=domain, prioritize_builtin=True, include_all=include_all
        )

    async def _consult_customer_expert(
        self, query: str, domain: str, include_all: bool = True
    ) -> ConsultationResult | None:
        """
        Convenience method to consult customer experts for business domains.

        Args:
            query: The question to ask
            domain: Business domain (e.g., "e-commerce", "healthcare")
            include_all: Whether to consult all experts or just primary

        Returns:
            ConsultationResult if successful, None otherwise
        """
        return await self._consult_expert(
            query=query,
            domain=domain,
            prioritize_builtin=False,
            include_all=include_all,
        )

    def _has_expert_support(self) -> bool:
        """Check if expert registry is available."""
        return self.expert_registry is not None

    def _list_available_experts(self) -> list:
        """List all available expert IDs."""
        if not self.expert_registry:
            return []
        return self.expert_registry.list_experts()

    def _get_expert(self, expert_id: str):
        """Get a specific expert by ID."""
        if not self.expert_registry:
            return None
        return self.expert_registry.get_expert(expert_id)


def create_agent_with_expert_support(agent_class, project_root: Path | None = None):
    """
    Factory function to create an agent with expert support initialized.

    This is a convenience function for creating agents that need expert support.

    Args:
        agent_class: Agent class to instantiate
        project_root: Project root directory

    Returns:
        Agent instance with expert support initialized
    """
    agent = agent_class()

    # If agent has expert support mixin, initialize it
    if hasattr(agent, "_initialize_expert_support"):
        import asyncio

        if asyncio.iscoroutinefunction(agent._initialize_expert_support):
            asyncio.run(agent._initialize_expert_support(project_root))
        else:
            agent._initialize_expert_support(project_root)

    return agent
