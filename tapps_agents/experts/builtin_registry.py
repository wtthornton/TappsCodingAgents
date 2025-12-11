"""
Built-in Expert Registry

Manages framework-controlled, immutable experts that ship with the TappsCodingAgents package.
These experts provide technical domain knowledge (security, performance, testing, etc.)
and cannot be modified by customers. They complement customer-defined business domain experts.

2025 Architecture Pattern:
- Built-in experts: Framework-controlled, immutable, technical domains
- Customer experts: User-controlled, configurable, business domains
- Dual-layer consultation: Weighted aggregation with priority system
"""

from pathlib import Path
from typing import List, Dict, Set, Optional
import importlib.resources

from .expert_config import ExpertConfigModel


class BuiltinExpertRegistry:
    """
    Registry for built-in framework experts.
    
    Built-in experts are:
    - Immutable (cannot be modified by customers)
    - Framework-controlled (updated via framework releases)
    - Technical domain focused (security, performance, testing, etc.)
    - Auto-loaded by ExpertRegistry
    """
    
    # Technical domains where built-in experts have primary authority
    TECHNICAL_DOMAINS: Set[str] = {
        "security",
        "performance-optimization",
        "testing-strategies",
        "code-quality-analysis",
        "software-architecture",
        "development-workflow",
        "data-privacy-compliance",
        "accessibility",
        "user-experience",
        "documentation-knowledge-management",
        "ai-agent-framework",
    }
    
    # Built-in expert configurations
    # These will be expanded in phases
    BUILTIN_EXPERTS: List[ExpertConfigModel] = [
        # Phase 1: Security Expert
        ExpertConfigModel(
            expert_id="expert-security",
            expert_name="Security Expert",
            primary_domain="security",
            rag_enabled=True,
            fine_tuned=False,
        ),
        
        # Phase 2: Performance Expert
        ExpertConfigModel(
            expert_id="expert-performance",
            expert_name="Performance Expert",
            primary_domain="performance-optimization",
            rag_enabled=True,
            fine_tuned=False,
        ),
        
        # Phase 2: Testing Expert
        ExpertConfigModel(
            expert_id="expert-testing",
            expert_name="Testing Expert",
            primary_domain="testing-strategies",
            rag_enabled=True,
            fine_tuned=False,
        ),
        
        # Phase 3: Data Privacy Expert
        ExpertConfigModel(
            expert_id="expert-data-privacy",
            expert_name="Data Privacy & Compliance Expert",
            primary_domain="data-privacy-compliance",
            rag_enabled=True,
            fine_tuned=False,
        ),
        
        # Phase 4: Accessibility Expert
        ExpertConfigModel(
            expert_id="expert-accessibility",
            expert_name="Accessibility Expert",
            primary_domain="accessibility",
            rag_enabled=True,
            fine_tuned=False,
        ),
        
        # Phase 4: User Experience Expert
        ExpertConfigModel(
            expert_id="expert-user-experience",
            expert_name="User Experience Expert",
            primary_domain="user-experience",
            rag_enabled=True,
            fine_tuned=False,
        ),
        
        # Existing framework experts (already in use)
        ExpertConfigModel(
            expert_id="expert-ai-frameworks",
            expert_name="AI Agent Framework Expert",
            primary_domain="ai-agent-framework",
            rag_enabled=True,
            fine_tuned=False,
        ),
        ExpertConfigModel(
            expert_id="expert-code-quality",
            expert_name="Code Quality & Analysis Expert",
            primary_domain="code-quality-analysis",
            rag_enabled=True,
            fine_tuned=False,
        ),
        ExpertConfigModel(
            expert_id="expert-software-architecture",
            expert_name="Software Architecture Expert",
            primary_domain="software-architecture",
            rag_enabled=True,
            fine_tuned=False,
        ),
        ExpertConfigModel(
            expert_id="expert-devops",
            expert_name="Development Workflow Expert",
            primary_domain="development-workflow",
            rag_enabled=True,
            fine_tuned=False,
        ),
        ExpertConfigModel(
            expert_id="expert-documentation",
            expert_name="Documentation & Knowledge Management Expert",
            primary_domain="documentation-knowledge-management",
            rag_enabled=True,
            fine_tuned=False,
        ),
    ]
    
    @classmethod
    def get_builtin_experts(cls) -> List[ExpertConfigModel]:
        """
        Get all built-in expert configurations.
        
        Returns:
            List of ExpertConfigModel instances for built-in experts
        """
        return cls.BUILTIN_EXPERTS.copy()
    
    @classmethod
    def get_builtin_expert_ids(cls) -> List[str]:
        """
        Get list of all built-in expert IDs.
        
        Returns:
            List of expert IDs
        """
        return [expert.expert_id for expert in cls.BUILTIN_EXPERTS]
    
    @classmethod
    def is_builtin_expert(cls, expert_id: str) -> bool:
        """
        Check if an expert ID is a built-in expert.
        
        Args:
            expert_id: Expert ID to check
            
        Returns:
            True if built-in expert, False otherwise
        """
        return expert_id in cls.get_builtin_expert_ids()
    
    @classmethod
    def get_builtin_knowledge_path(cls) -> Path:
        """
        Get path to built-in knowledge bases directory.
        
        Returns:
            Path to knowledge/ directory in package
        """
        try:
            # Try to use importlib.resources (Python 3.9+)
            package = importlib.resources.files("tapps_agents.experts")
            knowledge_path = package / "knowledge"
            if knowledge_path.exists():
                return knowledge_path
        except (ImportError, AttributeError, TypeError):
            pass
        
        # Fallback: Use __file__ to find package path
        try:
            import tapps_agents.experts
            package_path = Path(tapps_agents.experts.__file__).parent
            knowledge_path = package_path / "knowledge"
            return knowledge_path
        except Exception:
            # Final fallback: relative path
            return Path(__file__).parent / "knowledge"
    
    @classmethod
    def is_technical_domain(cls, domain: str) -> bool:
        """
        Check if a domain is a technical domain (built-in expert authority).
        
        Args:
            domain: Domain name to check
            
        Returns:
            True if technical domain, False if business domain
        """
        return domain in cls.TECHNICAL_DOMAINS
    
    @classmethod
    def get_expert_for_domain(cls, domain: str) -> Optional[ExpertConfigModel]:
        """
        Get built-in expert configuration for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            ExpertConfigModel if found, None otherwise
        """
        for expert in cls.BUILTIN_EXPERTS:
            if expert.primary_domain == domain:
                return expert
        return None

