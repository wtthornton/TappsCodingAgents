"""
Agent Handler Registry

Registry for agent execution handlers using Strategy Pattern.

Epic 20: Complexity Reduction - Story 20.1
"""

from typing import Any

from .base import AgentExecutionHandler


class AgentHandlerRegistry:
    """
    Registry for agent execution handlers.
    
    Maintains a list of handlers and provides lookup functionality
    to find the appropriate handler for a given agent/action combination.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._handlers: list[AgentExecutionHandler] = []
    
    def register(self, handler: AgentExecutionHandler) -> None:
        """
        Register a handler.
        
        Args:
            handler: Handler instance to register
        """
        self._handlers.append(handler)
    
    def find_handler(
        self,
        agent_name: str,
        action: str,
    ) -> AgentExecutionHandler | None:
        """
        Find a handler that supports the given agent and action.
        
        Args:
            agent_name: Agent name (lowercase)
            action: Normalized action name
            
        Returns:
            Handler instance if found, None otherwise
        """
        for handler in self._handlers:
            if handler.supports(agent_name, action):
                return handler
        return None
    
    @classmethod
    def create_registry(
        cls,
        project_root: Any,
        state: Any,
        workflow: Any,
        run_agent_fn: Any,
        executor: Any = None,
    ) -> "AgentHandlerRegistry":
        """
        Create and populate a registry with all available handlers.
        
        Args:
            project_root: Root directory for the project
            state: WorkflowState instance
            workflow: Workflow instance
            run_agent_fn: Function to run agent commands
            executor: Optional executor instance for utility methods
            
        Returns:
            Populated registry instance
        """
        registry = cls()
        
        # Import and register all handlers
        from .analyst_handler import AnalystHandler
        from .architect_handler import ArchitectHandler
        from .debugger_handler import DebuggerHandler
        from .designer_handler import DesignerHandler
        from .documenter_handler import DocumenterHandler
        from .enhancer_handler import EnhancerHandler
        from .implementer_handler import ImplementerHandler
        from .ops_handler import OpsHandler
        from .orchestrator_handler import OrchestratorHandler
        from .planner_handler import PlannerHandler
        from .reviewer_handler import ReviewerHandler
        from .tester_handler import TesterHandler
        
        handlers = [
            DebuggerHandler,
            ImplementerHandler,
            ReviewerHandler,
            TesterHandler,
            AnalystHandler,
            PlannerHandler,
            ArchitectHandler,
            DesignerHandler,
            EnhancerHandler,
            OpsHandler,
            DocumenterHandler,
            OrchestratorHandler,
        ]
        
        for handler_class in handlers:
            handler = handler_class(
                project_root=project_root,
                state=state,
                workflow=workflow,
                run_agent_fn=run_agent_fn,
                executor=executor,
            )
            registry.register(handler)
        
        return registry

