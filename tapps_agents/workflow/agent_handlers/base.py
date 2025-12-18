"""
Base Agent Execution Handler

Abstract base class for agent-specific execution handlers.

Epic 20: Complexity Reduction - Story 20.1
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..models import WorkflowStep


class AgentExecutionHandler(ABC):
    """
    Abstract base class for agent-specific execution handlers.
    
    Each handler encapsulates the logic for executing a specific agent type,
    reducing complexity in the main WorkflowExecutor._execute_step method.
    """
    
    def __init__(
        self,
        project_root: Path,
        state: Any,
        workflow: Any,
        run_agent_fn: Any,
        executor: Any = None,
    ):
        """
        Initialize the handler.
        
        Args:
            project_root: Root directory for the project
            state: WorkflowState instance
            workflow: Workflow instance
            run_agent_fn: Function to run agent commands
            executor: Optional executor instance for utility methods
        """
        self.project_root = project_root
        self.state = state
        self.workflow = workflow
        self.run_agent = run_agent_fn
        self.executor = executor
    
    @abstractmethod
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute the agent step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Optional target file path
            
        Returns:
            List of created artifacts (dict with 'name' and 'path' keys)
            
        Raises:
            ValueError: If step requirements are not met
        """
        pass
    
    @abstractmethod
    def supports(self, agent_name: str, action: str) -> bool:
        """
        Check if this handler supports the given agent and action.
        
        Args:
            agent_name: Agent name (lowercase)
            action: Normalized action name
            
        Returns:
            True if this handler can execute the step
        """
        pass

