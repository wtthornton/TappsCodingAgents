"""
Tool Registry - Manages available MCP tools.
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum


class ToolCategory(Enum):
    """Tool categories."""
    FILESYSTEM = "filesystem"
    GIT = "git"
    ANALYSIS = "analysis"
    CUSTOM = "custom"


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    category: ToolCategory
    handler: Callable
    parameters: Dict[str, Any]
    cache_strategy: Optional[str] = None
    requires_auth: bool = False


class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._by_category: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
    
    def register(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        handler: Callable,
        parameters: Optional[Dict[str, Any]] = None,
        cache_strategy: Optional[str] = None,
        requires_auth: bool = False
    ):
        """
        Register a tool.
        
        Args:
            name: Tool name
            description: Tool description
            category: Tool category
            handler: Callable that handles the tool execution
            parameters: Tool parameters schema
            cache_strategy: Cache strategy (tier1, tier2, tier3, none)
            requires_auth: Whether tool requires authentication
        """
        tool_def = ToolDefinition(
            name=name,
            description=description,
            category=category,
            handler=handler,
            parameters=parameters or {},
            cache_strategy=cache_strategy,
            requires_auth=requires_auth
        )
        
        self._tools[name] = tool_def
        self._by_category[category].append(name)
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:
        """
        List registered tools.
        
        Args:
            category: Optional category filter
        
        Returns:
            List of tool names
        """
        if category:
            return self._by_category.get(category, []).copy()
        return list(self._tools.keys())
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
        
        Returns:
            True if tool was removed, False if not found
        """
        if name not in self._tools:
            return False
        
        tool_def = self._tools[name]
        self._by_category[tool_def.category].remove(name)
        del self._tools[name]
        return True
    
    def get_all_definitions(self) -> Dict[str, ToolDefinition]:
        """Get all tool definitions."""
        return self._tools.copy()

