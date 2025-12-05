"""
Base Expert Agent Class

Industry Experts are business domain authorities (NOT technical specialists).
They provide domain knowledge through consultation, RAG, and weighted decisions.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

from ..core.agent_base import BaseAgent
from ..core.config import ProjectConfig
from ..core.mal import MAL
from .simple_rag import SimpleKnowledgeBase


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
        confidence_matrix: Optional[Dict[str, float]] = None,
        mal: Optional[MAL] = None,
        config: Optional[ProjectConfig] = None,
        rag_enabled: bool = False,
        fine_tuned: bool = False
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
        self.project_root: Optional[Path] = None
        
        # RAG components (to be initialized if enabled)
        self.rag_interface = None
        self.knowledge_base = None
        
        # Fine-tuning components (to be initialized if enabled)
        self.adapter = None
    
    async def activate(self, project_root: Optional[Path] = None):
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
        """Initialize RAG interface and knowledge base."""
        # Initialize simple file-based knowledge base
        knowledge_dir = self.project_root / ".tapps-agents" / "knowledge" / self.primary_domain
        
        # Fallback to general knowledge if domain-specific doesn't exist
        if not knowledge_dir.exists():
            knowledge_dir = self.project_root / ".tapps-agents" / "knowledge"
        
        self.knowledge_base = SimpleKnowledgeBase(knowledge_dir, domain=self.primary_domain)
        self.rag_interface = self.knowledge_base
    
    async def _initialize_adapter(self):
        """Initialize fine-tuning adapter (LoRA)."""
        # Placeholder for adapter initialization
        # Will be implemented when fine-tuning support is added
        pass
    
    def greet(self):
        """Greet user with expert role and domain."""
        pass  # Experts don't write to stdout directly
    
    async def run(self, command: str, **kwargs: Any) -> Dict[str, Any]:
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
            return {"error": f"Unknown command: {command}. Use '*help' to see available commands."}
    
    async def _handle_consult(self, query: str, domain: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
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
        
        # Query using LLM with domain context
        prompt = self._build_consultation_prompt(query, context, domain)
        response = await self._query_llm(prompt)
        
        return {
            "answer": response,
            "confidence": confidence,
            "domain": domain,
            "sources": await self._get_sources(query, domain),
            "expert_id": self.expert_id,
            "expert_name": self.agent_name
        }
    
    async def _handle_validate(self, artifact: str, artifact_type: str = "code", **kwargs: Any) -> Dict[str, Any]:
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
        prompt = self._build_validation_prompt(artifact, artifact_type, context, domain)
        validation = await self._query_llm(prompt)
        
        return {
            "valid": True,  # Will be parsed from LLM response
            "feedback": validation,
            "confidence": confidence,
            "domain": domain,
            "expert_id": self.expert_id
        }
    
    async def _handle_provide_context(self, topic: str, **kwargs: Any) -> Dict[str, Any]:
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
            "expert_id": self.expert_id
        }
    
    async def _handle_help(self) -> Dict[str, Any]:
        """Show available expert commands."""
        help_message = {
            "*consult {query} [domain]": "Answer a domain-specific question",
            "*validate {artifact} [artifact_type]": "Validate an artifact for domain correctness",
            "*provide-context {topic} [domain]": "Provide domain context on a topic",
            "*help": "Show this help message"
        }
        return {"content": help_message}
    
    # Default implementations using simple RAG
    
    async def _build_domain_context(self, query: str, domain: str) -> str:
        """
        Build domain-specific context for a query.
        
        Uses simple file-based RAG if enabled, otherwise returns empty context.
        """
        if self.rag_enabled and self.knowledge_base:
            return self.knowledge_base.get_context(query, max_length=2000)
        return f"Domain: {domain}. No additional context available."
    
    async def _get_sources(self, query: str, domain: str) -> List[str]:
        """
        Get knowledge sources for a query.
        
        Returns file paths from knowledge base if RAG is enabled.
        """
        if self.rag_enabled and self.knowledge_base:
            return self.knowledge_base.get_sources(query, max_results=5)
        return []
    
    async def _build_consultation_prompt(self, query: str, context: str, domain: str) -> str:
        """Build LLM prompt for consultation."""
        return f"""You are a {domain} domain expert.
        
Domain Context:
{context}

Question: {query}

Provide a clear, accurate answer based on your domain expertise. Cite sources if applicable.
Answer:"""
    
    async def _build_validation_prompt(self, artifact: str, artifact_type: str, context: str, domain: str) -> str:
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
    
    async def _build_validation_context(self, artifact: str, artifact_type: str, domain: str) -> str:
        """Build context for validation."""
        return await self._build_domain_context(f"{artifact_type} validation", domain)
    
    async def _query_llm(self, prompt: str) -> str:
        """Query LLM using MAL."""
        if self.mal is None:
            from ..core.config import load_config
            config = self.config or load_config()
            self.mal = MAL(config=self.config.mal)
        
        response = await self.mal.generate(prompt)
        return response

