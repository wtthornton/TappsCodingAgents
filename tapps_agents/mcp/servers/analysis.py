"""
Analysis MCP Server - Code analysis operations.
"""

from pathlib import Path
from typing import Any

from ..tool_registry import ToolCategory, ToolRegistry


class AnalysisMCPServer:
    """MCP server for code analysis operations."""

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        """Register analysis tools."""
        self.registry.register(
            name="analyze_complexity",
            description="Analyze code complexity",
            category=ToolCategory.ANALYSIS,
            handler=self.analyze_complexity,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "Path to code file",
                }
            },
            cache_strategy="tier2",
        )

        self.registry.register(
            name="find_patterns",
            description="Find code patterns",
            category=ToolCategory.ANALYSIS,
            handler=self.find_patterns,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "Path to code file",
                },
                "pattern": {
                    "type": "string",
                    "required": True,
                    "description": "Pattern to find",
                },
            },
            cache_strategy="tier2",
        )

        self.registry.register(
            name="score_code",
            description="Score code quality",
            category=ToolCategory.ANALYSIS,
            handler=self.score_code,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "Path to code file",
                }
            },
            cache_strategy="tier2",
        )

        self.registry.register(
            name="detect_issues",
            description="Detect code issues",
            category=ToolCategory.ANALYSIS,
            handler=self.detect_issues,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "Path to code file",
                }
            },
            cache_strategy="tier2",
        )

    def analyze_complexity(self, file_path: str) -> dict[str, Any]:
        """Analyze code complexity."""
        try:
            from tapps_agents.agents.reviewer.scoring import CodeScorer
            from tapps_agents.core.config import load_config

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Use CodeScorer for complexity analysis
            config = load_config()
            weights = config.scoring.weights
            scorer = CodeScorer(weights)

            complexity_result = scorer._calculate_complexity(path)

            return {
                "file_path": str(path),
                "complexity": complexity_result.get("score", 0),
                "details": complexity_result,
            }
        except ImportError:
            # Fallback if CodeScorer not available
            return {
                "file_path": file_path,
                "complexity": 0,
                "details": {"error": "Complexity analysis not available"},
            }

    def find_patterns(self, file_path: str, pattern: str) -> dict[str, Any]:
        """Find code patterns."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        matches = []
        for line_num, line in enumerate(lines, 1):
            if pattern in line:
                matches.append({"line": line_num, "content": line.strip()})

        return {
            "file_path": str(path),
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
        }

    def score_code(self, file_path: str) -> dict[str, Any]:
        """Score code quality."""
        try:
            from tapps_agents.agents.reviewer.scoring import CodeScorer
            from tapps_agents.core.config import load_config

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Use CodeScorer for scoring
            config = load_config()
            weights = config.scoring.weights
            scorer = CodeScorer(weights)

            score_result = scorer.score_file(path)

            return {
                "file_path": str(path),
                "overall_score": score_result.get("overall_score", 0),
                "scores": score_result,
            }
        except ImportError:
            # Fallback if CodeScorer not available
            return {
                "file_path": file_path,
                "overall_score": 0,
                "scores": {"error": "Code scoring not available"},
            }

    def detect_issues(self, file_path: str) -> dict[str, Any]:
        """Detect code issues."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        issues = []

        # Simple issue detection
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Check for common issues
        for line_num, line in enumerate(lines, 1):
            # Check for TODO/FIXME
            if "TODO" in line or "FIXME" in line:
                issues.append(
                    {
                        "type": "todo",
                        "line": line_num,
                        "message": "TODO/FIXME comment found",
                        "content": line.strip(),
                    }
                )

            # Check for long lines (over 120 characters)
            if len(line) > 120:
                issues.append(
                    {
                        "type": "long_line",
                        "line": line_num,
                        "message": f"Line too long ({len(line)} characters)",
                        "content": line.strip()[:100],
                    }
                )

        return {"file_path": str(path), "issues": issues, "count": len(issues)}
