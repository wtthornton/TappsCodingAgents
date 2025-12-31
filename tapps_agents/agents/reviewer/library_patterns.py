"""
Library Pattern Checkers - Extensible plugin architecture for library-specific code review patterns.

This module provides a plugin-style architecture for library-specific pattern checking,
making it easy to add new library patterns without modifying core agent code.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from ...context7.agent_integration import Context7AgentHelper

logger = logging.getLogger(__name__)


class LibraryPatternChecker(ABC):
    """Base class for library-specific pattern checking."""
    
    @property
    @abstractmethod
    def library_name(self) -> str:
        """Library name this checker handles."""
        pass
    
    @abstractmethod
    def matches(self, code: str, libraries_detected: list[str]) -> bool:
        """
        Check if this pattern applies to the code.
        
        Args:
            code: The code to check
            libraries_detected: List of detected library names
        
        Returns:
            True if this pattern applies
        """
        pass
    
    @abstractmethod
    async def generate_suggestions(
        self,
        code: str,
        context7_helper: Context7AgentHelper
    ) -> list[dict[str, Any]]:
        """
        Generate Context7 suggestions for this library.
        
        Args:
            code: The code to analyze
            context7_helper: Context7 helper for fetching documentation
        
        Returns:
            List of suggestion dictionaries
        """
        pass


class FastAPIPatternChecker(LibraryPatternChecker):
    """FastAPI-specific pattern checker."""
    
    @property
    def library_name(self) -> str:
        return "fastapi"
    
    def matches(self, code: str, libraries_detected: list[str]) -> bool:
        """Check if code uses FastAPI routing patterns."""
        code_lower = code.lower()
        lib_lower = self.library_name.lower()
        return (
            lib_lower in [lib.lower() for lib in libraries_detected] and
            ("route" in code_lower or "router" in code_lower)
        )
    
    async def generate_suggestions(
        self,
        code: str,
        context7_helper: Context7AgentHelper
    ) -> list[dict[str, Any]]:
        """Generate FastAPI routing suggestions."""
        suggestions = []
        
        try:
            # Detect topics for FastAPI
            topics = context7_helper.detect_topics(code, self.library_name)
            if "routing" not in topics:
                return suggestions
            
            # Proactively fetch routing documentation
            routing_docs = await context7_helper.get_documentation(
                library=self.library_name,
                topic="routing",
                use_fuzzy_match=True
            )
            
            if not routing_docs:
                return suggestions
            
            # Check for potential route ordering issues
            # Look for parameterized routes before specific routes
            route_pattern = r"@(?:router|app)\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]"
            routes = re.findall(route_pattern, code, re.IGNORECASE)
            
            # Check if there are parameterized routes (containing {})
            param_routes = [r for r in routes if "{" in r]
            specific_routes = [r for r in routes if "{" not in r]
            
            # If we have both types, suggest checking order
            if param_routes and specific_routes:
                suggestions.append({
                    "type": "context7_best_practice",
                    "library": self.library_name,
                    "issue": "Route ordering: Parameterized routes (e.g., /{id}) should come after specific routes (e.g., /stats)",
                    "guidance": routing_docs.get("content", "")[:500] if routing_docs.get("content") else "",
                    "source": routing_docs.get("source", "Context7 KB"),
                    "severity": "info",
                })
        except Exception as e:
            logger.debug(f"FastAPI pattern checker failed: {e}")
        
        return suggestions


class ReactPatternChecker(LibraryPatternChecker):
    """React-specific pattern checker."""
    
    @property
    def library_name(self) -> str:
        return "react"
    
    def matches(self, code: str, libraries_detected: list[str]) -> bool:
        """Check if code uses React hooks."""
        code_lower = code.lower()
        lib_lower = self.library_name.lower()
        return (
            lib_lower in [lib.lower() for lib in libraries_detected] and
            ("usestate" in code_lower or "useeffect" in code_lower)
        )
    
    async def generate_suggestions(
        self,
        code: str,
        context7_helper: Context7AgentHelper
    ) -> list[dict[str, Any]]:
        """Generate React hooks suggestions."""
        suggestions = []
        
        try:
            topics = context7_helper.detect_topics(code, self.library_name)
            if "hooks" not in topics:
                return suggestions
            
            hooks_docs = await context7_helper.get_documentation(
                library=self.library_name,
                topic="hooks",
                use_fuzzy_match=True
            )
            
            if hooks_docs:
                suggestions.append({
                    "type": "context7_best_practice",
                    "library": self.library_name,
                    "issue": "React hooks best practices available",
                    "guidance": hooks_docs.get("content", "")[:500] if hooks_docs.get("content") else "",
                    "source": hooks_docs.get("source", "Context7 KB"),
                    "severity": "info",
                })
        except Exception as e:
            logger.debug(f"React pattern checker failed: {e}")
        
        return suggestions


class PytestPatternChecker(LibraryPatternChecker):
    """pytest-specific pattern checker."""
    
    @property
    def library_name(self) -> str:
        return "pytest"
    
    def matches(self, code: str, libraries_detected: list[str]) -> bool:
        """Check if code uses pytest fixtures."""
        code_lower = code.lower()
        lib_lower = self.library_name.lower()
        return (
            lib_lower in [lib.lower() for lib in libraries_detected] and
            ("fixture" in code_lower or "@pytest" in code_lower)
        )
    
    async def generate_suggestions(
        self,
        code: str,
        context7_helper: Context7AgentHelper
    ) -> list[dict[str, Any]]:
        """Generate pytest fixture suggestions."""
        suggestions = []
        
        try:
            topics = context7_helper.detect_topics(code, self.library_name)
            if "fixtures" not in topics:
                return suggestions
            
            fixtures_docs = await context7_helper.get_documentation(
                library=self.library_name,
                topic="fixtures",
                use_fuzzy_match=True
            )
            
            if fixtures_docs:
                suggestions.append({
                    "type": "context7_best_practice",
                    "library": self.library_name,
                    "issue": "pytest fixture best practices available",
                    "guidance": fixtures_docs.get("content", "")[:500] if fixtures_docs.get("content") else "",
                    "source": fixtures_docs.get("source", "Context7 KB"),
                    "severity": "info",
                })
        except Exception as e:
            logger.debug(f"pytest pattern checker failed: {e}")
        
        return suggestions


class LibraryPatternRegistry:
    """Registry for library pattern checkers."""
    
    def __init__(self):
        self._checkers: dict[str, LibraryPatternChecker] = {}
        # Register default checkers
        self.register(FastAPIPatternChecker())
        self.register(ReactPatternChecker())
        self.register(PytestPatternChecker())
    
    def register(self, checker: LibraryPatternChecker):
        """Register a pattern checker."""
        self._checkers[checker.library_name.lower()] = checker
        logger.debug(f"Registered library pattern checker: {checker.library_name}")
    
    async def generate_suggestions(
        self,
        code: str,
        libraries_detected: list[str],
        context7_helper: Context7AgentHelper
    ) -> list[dict[str, Any]]:
        """
        Generate suggestions from all matching checkers.
        
        Args:
            code: The code to analyze
            libraries_detected: List of detected library names
            context7_helper: Context7 helper for fetching documentation
        
        Returns:
            List of all suggestions from matching checkers
        """
        all_suggestions = []
        
        for lib in libraries_detected:
            checker = self._checkers.get(lib.lower())
            if checker and checker.matches(code, libraries_detected):
                try:
                    suggestions = await checker.generate_suggestions(code, context7_helper)
                    all_suggestions.extend(suggestions)
                except Exception as e:
                    logger.debug(f"Pattern checker {checker.library_name} failed: {e}")
        
        return all_suggestions
