"""
Base Expert Agent Class

Industry Experts are business domain authorities (NOT technical specialists).
They provide domain knowledge through consultation, RAG, and weighted decisions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..core.agent_base import BaseAgent
from ..core.config import ProjectConfig
from ..core.mal import MAL
from .simple_rag import SimpleKnowledgeBase
from .vector_rag import VectorKnowledgeBase

if TYPE_CHECKING:
    from ..core.project_profile import ProjectProfile


class BaseExpert(BaseAgent):
    """
    Base class for Industry Expert agents.

    Characteristics:
    - Business domain authority (not technical)
    - Read-only permissions (advisory role)
    - Weighted decision-making (51% primary)
    - RAG + Fine-tuning support
    - Consultation interface

    Permissions: Read, Grep, Glob (no Write, Edit, Bash)
    """

    def __init__(
        self,
        expert_id: str,
        expert_name: str,
        primary_domain: str,
        confidence_matrix: dict[str, float] | None = None,
        mal: MAL | None = None,
        config: ProjectConfig | None = None,
        rag_enabled: bool = False,
        fine_tuned: bool = False,
    ):
        """
        Initialize an Industry Expert agent.

        Args:
            expert_id: Unique identifier (e.g., "expert-home-automation")
            expert_name: Human-readable name
            primary_domain: Domain where this expert has 51% authority
            confidence_matrix: Confidence weights per domain {domain: weight}
            mal: Model Abstraction Layer instance
            config: Project configuration
            rag_enabled: Whether RAG is enabled for this expert
            fine_tuned: Whether this expert uses fine-tuned models
        """
        super().__init__(agent_id=expert_id, agent_name=expert_name, config=config)

        self.expert_id = expert_id
        self.primary_domain = primary_domain
        self.confidence_matrix = confidence_matrix or {}
        self.mal = mal
        self.rag_enabled = rag_enabled
        self.fine_tuned = fine_tuned
        self.project_root: Path | None = None

        # Built-in expert flags (set by ExpertRegistry)
        self._is_builtin: bool = False
        self._builtin_knowledge_path: Path | None = None

        # RAG components (to be initialized if enabled)
        self.rag_interface: Any | None = None
        self.knowledge_base: SimpleKnowledgeBase | VectorKnowledgeBase | None = None

        # Fine-tuning components (to be initialized if enabled)
        self.adapter = None

    async def activate(self, project_root: Path | None = None):
        """Activate the expert agent following BMAD activation pattern."""
        await super().activate(project_root)
        self.project_root = project_root or Path.cwd()

        # Initialize RAG if enabled
        if self.rag_enabled:
            await self._initialize_rag()

        # Initialize fine-tuning adapter if enabled
        if self.fine_tuned:
            await self._initialize_adapter()

        self.greet()
        await self.run("help")

    async def _initialize_rag(self):
        """
        Initialize RAG interface and knowledge base.

        For built-in experts, checks built-in knowledge path first.
        For customer experts, checks project knowledge path.

        Uses VectorKnowledgeBase (FAISS) when available, falls back to SimpleKnowledgeBase.
        """
        knowledge_dirs: list[Path] = []

        if self._is_builtin and self._builtin_knowledge_path:
            # Built-in expert: check built-in knowledge first
            builtin_domain_dir = self._builtin_knowledge_path / self.primary_domain
            if builtin_domain_dir.exists():
                knowledge_dirs.append(builtin_domain_dir)
            # Also check general built-in knowledge
            if self._builtin_knowledge_path.exists():
                knowledge_dirs.append(self._builtin_knowledge_path)

        # Customer knowledge (project-specific)
        if self.project_root:
            customer_domain_dir = (
                self.project_root / ".tapps-agents" / "knowledge" / self.primary_domain
            )
            if customer_domain_dir.exists():
                knowledge_dirs.append(customer_domain_dir)
            # General customer knowledge
            customer_general = self.project_root / ".tapps-agents" / "knowledge"
            if customer_general.exists() and customer_general not in knowledge_dirs:
                knowledge_dirs.append(customer_general)

        # Initialize knowledge base with vector backend if available
        if knowledge_dirs:
            primary_dir = knowledge_dirs[0]

            # Try to use VectorKnowledgeBase (FAISS-based)
            try:
                from ..core.config import get_expert_config

                get_expert_config()
                self.knowledge_base = VectorKnowledgeBase(
                    knowledge_dir=primary_dir,
                    domain=self.primary_domain,
                    chunk_size=512,
                    overlap=50,
                    embedding_model="all-MiniLM-L6-v2",
                    similarity_threshold=0.7,
                )
                self.rag_interface = self.knowledge_base

                # Log backend selection
                backend_type = self.knowledge_base.get_backend_type()
                if backend_type == "vector":
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Expert {self.expert_id}: Using VectorKnowledgeBase (FAISS) for RAG"
                    )
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Expert {self.expert_id}: Using SimpleKnowledgeBase fallback for RAG"
                    )
            except Exception as e:
                # Fallback to SimpleKnowledgeBase
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(
                    f"Failed to initialize VectorKnowledgeBase for {self.expert_id}: {e}. "
                    "Falling back to SimpleKnowledgeBase."
                )
                self.knowledge_base = SimpleKnowledgeBase(
                    primary_dir, domain=self.primary_domain
                )
                self.rag_interface = self.knowledge_base
        else:
            # No knowledge base available
            self.knowledge_base = None
            self.rag_interface = None

    async def _initialize_adapter(self):
        """Initialize fine-tuning adapter (LoRA)."""
        # Placeholder for adapter initialization
        # Will be implemented when fine-tuning support is added
        pass

    def greet(self):
        """Greet user with expert role and domain."""
        pass  # Experts don't write to stdout directly

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute expert command.

        Common commands:
        - *consult {query}: Answer domain question
        - *validate {artifact}: Validate domain correctness
        - *provide-context {topic}: Provide domain context
        - *help: Show available commands
        """
        command = command.lstrip("*")
        handler_name = f"_handle_{command.replace('-', '_')}"

        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return await handler(**kwargs)
        else:
            return {
                "error": f"Unknown command: {command}. Use '*help' to see available commands."
            }

    async def _handle_consult(
        self, query: str, domain: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Consult the expert on a domain question.

        This is the primary consultation interface for workflow agents.

        Args:
            query: The question or request for domain knowledge
            domain: Optional domain context (defaults to primary_domain)

        Returns:
            Consultation response with answer, confidence, and sources
        """
        domain = domain or self.primary_domain
        confidence = self.confidence_matrix.get(domain, 0.0)

        # Build context from domain knowledge
        context = await self._build_domain_context(query, domain)

        # Get project profile if available (from kwargs)
        project_profile = kwargs.get("project_profile")

        # Query using LLM with domain context
        prompt = await self._build_consultation_prompt(
            query, context, domain, project_profile=project_profile
        )
        response = await self._query_llm(prompt)

        return {
            "answer": response,
            "confidence": confidence,
            "domain": domain,
            "sources": await self._get_sources(query, domain),
            "expert_id": self.expert_id,
            "expert_name": self.agent_name,
        }

    async def _handle_validate(
        self, artifact: str, artifact_type: str = "code", **kwargs: Any
    ) -> dict[str, Any]:
        """
        Validate an artifact (code, design, etc.) for domain correctness.

        Args:
            artifact: The artifact to validate (code string, design doc, etc.)
            artifact_type: Type of artifact (code, design, api, etc.)

        Returns:
            Validation result with feedback and correctness score
        """
        domain = kwargs.get("domain", self.primary_domain)
        confidence = self.confidence_matrix.get(domain, 0.0)

        # Build validation context
        context = await self._build_validation_context(artifact, artifact_type, domain)

        # Query for validation
        prompt = await self._build_validation_prompt(
            artifact, artifact_type, context, domain
        )
        validation = await self._query_llm(prompt)

        return {
            "valid": True,  # Will be parsed from LLM response
            "feedback": validation,
            "confidence": confidence,
            "domain": domain,
            "expert_id": self.expert_id,
        }

    async def _handle_provide_context(
        self, topic: str, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Provide domain context on a specific topic.

        Args:
            topic: The topic to provide context for

        Returns:
            Context information with relevant domain knowledge
        """
        domain = kwargs.get("domain", self.primary_domain)
        context = await self._build_domain_context(topic, domain)

        return {
            "context": context,
            "topic": topic,
            "domain": domain,
            "expert_id": self.expert_id,
        }

    async def _handle_help(self) -> dict[str, Any]:
        """Show available expert commands."""
        help_message = {
            "*consult {query} [domain]": "Answer a domain-specific question",
            "*validate {artifact} [artifact_type]": "Validate an artifact for domain correctness",
            "*provide-context {topic} [domain]": "Provide domain context on a topic",
            "*help": "Show this help message",
        }
        return {"content": help_message}

    # Default implementations using simple RAG

    async def _build_domain_context(self, query: str, domain: str) -> str:
        """
        Build domain-specific context for a query.

        Uses simple file-based RAG if enabled, otherwise returns empty context.
        """
        if self.rag_enabled and self.knowledge_base:
            from ..core.config import get_expert_config

            expert_config = get_expert_config()
            return self.knowledge_base.get_context(
                query, max_length=expert_config.rag_max_length
            )
        return f"Domain: {domain}. No additional context available."

    async def _get_sources(self, query: str, domain: str) -> list[str]:
        """
        Get knowledge sources for a query.

        Returns file paths from knowledge base if RAG is enabled.
        """
        if self.rag_enabled and self.knowledge_base:
            from ..core.config import get_expert_config

            expert_config = get_expert_config()
            return self.knowledge_base.get_sources(
                query, max_results=expert_config.rag_max_results
            )
        return []

    async def _build_consultation_prompt(
        self,
        query: str,
        context: str,
        domain: str,
        project_profile: ProjectProfile | None = None,
    ) -> str:
        """
        Build LLM prompt for consultation.

        Args:
            query: The question to ask
            context: Domain context from RAG
            domain: Domain name
            project_profile: Optional project profile for context-aware advice
        """
        prompt = f"""You are a {domain} domain expert.
        
Domain Context:
{context}
"""

        # Add project profile context if available and high confidence
        if project_profile:
            profile_context = self._format_profile_context(project_profile)
            if profile_context:
                prompt += f"\nProject Context:\n{profile_context}\n"

        prompt += f"""
Question: {query}

Provide a clear, accurate answer based on your domain expertise. Tailor your advice to the project's characteristics if relevant. Cite sources if applicable.
Answer:"""

        return prompt

    def _format_profile_context(self, profile: ProjectProfile) -> str:
        """
        Format project profile as context string for LLM.

        Only includes high-confidence profile values (from config).

        Args:
            profile: ProjectProfile instance

        Returns:
            Formatted context string or empty string if no high-confidence values
        """
        from ..core.config import get_expert_config

        expert_config = get_expert_config()
        profile_threshold = expert_config.profile_confidence_threshold

        context_parts = []

        # Deployment type
        if (
            profile.deployment_type
            and profile.deployment_type_confidence >= profile_threshold
        ):
            context_parts.append(
                f"- Deployment: {profile.deployment_type} "
                f"(confidence: {profile.deployment_type_confidence:.1%})"
            )

        # Security level
        if (
            profile.security_level
            and profile.security_level_confidence >= profile_threshold
        ):
            context_parts.append(
                f"- Security Level: {profile.security_level} "
                f"(confidence: {profile.security_level_confidence:.1%})"
            )

        # Compliance requirements
        high_confidence_compliance = [
            req
            for req in profile.compliance_requirements
            if req.confidence >= profile_threshold
        ]
        if high_confidence_compliance:
            compliance_names = ", ".join(req.name for req in high_confidence_compliance)
            context_parts.append(f"- Compliance Requirements: {compliance_names}")

        # Tenancy (if detected)
        if profile.tenancy and profile.tenancy_confidence >= profile_threshold:
            context_parts.append(
                f"- Tenancy: {profile.tenancy} "
                f"(confidence: {profile.tenancy_confidence:.1%})"
            )

        # User scale (if detected)
        if profile.user_scale and profile.user_scale_confidence >= profile_threshold:
            context_parts.append(
                f"- User Scale: {profile.user_scale} "
                f"(confidence: {profile.user_scale_confidence:.1%})"
            )

        return "\n".join(context_parts) if context_parts else ""

    async def _build_validation_prompt(
        self, artifact: str, artifact_type: str, context: str, domain: str
    ) -> str:
        """Build LLM prompt for validation."""
        return f"""You are a {domain} domain expert validating a {artifact_type}.

Domain Context:
{context}

{artifact_type.capitalize()} to validate:
{artifact}

Validate this artifact for domain correctness. Provide:
1. Is it correct? (yes/no)
2. Feedback and suggestions
3. Domain-specific issues found

Validation:"""

    async def _build_validation_context(
        self, artifact: str, artifact_type: str, domain: str
    ) -> str:
        """Build context for validation."""
        return await self._build_domain_context(f"{artifact_type} validation", domain)

    async def _query_llm(self, prompt: str) -> str:
        """Query LLM using MAL."""
        if self.mal is None:
            from ..core.config import load_config

            self.config = self.config or load_config()
            self.mal = MAL(config=self.config.mal)

        response = await self.mal.generate(prompt)
        return response
