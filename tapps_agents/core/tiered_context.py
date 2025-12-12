"""
Tiered Context - Context tier definitions and builders.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .ast_parser import ASTParser, ModuleInfo


logger = logging.getLogger(__name__)


class ContextTier(Enum):
    """Context tier levels."""

    TIER1 = "tier1"  # Core context
    TIER2 = "tier2"  # Extended context
    TIER3 = "tier3"  # Full context


@dataclass
class TierConfig:
    """Configuration for a context tier."""

    name: str
    max_tokens: int
    cache_ttl: int  # seconds
    includes: list[str]
    inherits: str | None = None


class TieredContextBuilder:
    """Builds context according to tier definitions."""

    # Default tier configurations
    TIER_CONFIGS = {
        ContextTier.TIER1: TierConfig(
            name="Core Context",
            max_tokens=1000,
            cache_ttl=300,  # 5 minutes
            includes=[
                "file_structure",
                "type_definitions",
                "function_signatures",
                "imports_exports",
            ],
            inherits=None,
        ),
        ContextTier.TIER2: TierConfig(
            name="Extended Context",
            max_tokens=5000,
            cache_ttl=120,  # 2 minutes
            includes=["function_bodies", "local_dependencies", "test_files"],
            inherits="tier1",
        ),
        ContextTier.TIER3: TierConfig(
            name="Full Context",
            max_tokens=20000,
            cache_ttl=60,  # 1 minute
            includes=["git_history", "documentation", "cross_references"],
            inherits="tier2",
        ),
    }

    def __init__(self, ast_parser: ASTParser | None = None):
        self.ast_parser = ast_parser or ASTParser()

    def build_context(
        self, file_path: Path, tier: ContextTier, include_related: bool = False
    ) -> dict[str, Any]:
        """
        Build context for a file at the specified tier.

        Args:
            file_path: Path to the file
            tier: Context tier level
            include_related: Whether to include related files

        Returns:
            Dictionary with tiered context
        """
        config = self.TIER_CONFIGS[tier]
        context: dict[str, Any] = {
            "tier": tier.value,
            "file": str(file_path),
            "content": {},
        }

        # Parse file structure
        module_info = self.ast_parser.parse_file(file_path)

        # Build tier-specific context
        if "file_structure" in config.includes or config.inherits:
            context["content"]["structure"] = self._build_structure(module_info)

        if "function_signatures" in config.includes or config.inherits:
            context["content"]["functions"] = self._build_function_signatures(
                module_info
            )

        if "type_definitions" in config.includes or config.inherits:
            context["content"]["classes"] = self._build_class_signatures(module_info)

        if "imports_exports" in config.includes or config.inherits:
            context["content"]["imports"] = module_info.imports

        # Tier 2 additions
        if tier in (ContextTier.TIER2, ContextTier.TIER3):
            if "function_bodies" in config.includes:
                context["content"]["function_bodies"] = self._build_function_bodies(
                    file_path, module_info
                )

            if "local_dependencies" in config.includes and include_related:
                context["content"]["dependencies"] = self._find_local_dependencies(
                    file_path, module_info
                )

        # Tier 3 additions
        if tier == ContextTier.TIER3:
            # Full file content (within token limit)
            try:
                full_content = file_path.read_text(encoding="utf-8")
                context["content"]["full_file"] = self._truncate_to_tokens(
                    full_content, config.max_tokens
                )
            except Exception:
                logger.debug("Failed to read full file content for tier3 context", exc_info=True)

        # Calculate token estimate
        context["token_estimate"] = self._estimate_tokens(context)

        return context

    def _build_structure(self, module_info: ModuleInfo) -> dict[str, Any]:
        """Build file structure summary."""
        return {
            "functions": [f.name for f in module_info.functions],
            "classes": [c.name for c in module_info.classes],
            "imports_count": len(module_info.imports),
        }

    def _build_function_signatures(
        self, module_info: ModuleInfo
    ) -> list[dict[str, Any]]:
        """Build function signatures."""
        return [
            {
                "name": func.name,
                "line": func.line,
                "signature": func.signature,
                "args": func.args,
                "returns": func.returns,
                "docstring": (
                    func.docstring[:200] if func.docstring else None
                ),  # Truncate long docstrings
            }
            for func in module_info.functions
        ]

    def _build_class_signatures(self, module_info: ModuleInfo) -> list[dict[str, Any]]:
        """Build class signatures."""
        return [
            {
                "name": cls.name,
                "line": cls.line,
                "bases": cls.bases,
                "methods": cls.methods,
                "docstring": cls.docstring[:200] if cls.docstring else None,
            }
            for cls in module_info.classes
        ]

    def _build_function_bodies(
        self, file_path: Path, module_info: ModuleInfo
    ) -> dict[str, str]:
        """Build function bodies (Tier 2)."""
        try:
            code = file_path.read_text(encoding="utf-8")
            lines = code.split("\n")

            function_bodies = {}
            for func in module_info.functions:
                # Extract function body (simplified - assumes function ends at next def/class)
                start_line = func.line - 1
                end_line = self._find_function_end(lines, start_line)
                body = "\n".join(lines[start_line:end_line])
                function_bodies[func.name] = body[:1000]  # Limit body size

            return function_bodies
        except Exception:
            return {}

    def _find_function_end(self, lines: list[str], start_line: int) -> int:
        """Find the end of a function (simplified)."""
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())

        for i in range(start_line + 1, len(lines)):
            line = lines[i].rstrip()
            if not line:  # Empty line
                continue

            current_indent = len(lines[i]) - len(lines[i].lstrip())
            # Check if we've hit a def/class at same or lower indent level
            if current_indent <= indent_level:
                if line.lstrip().startswith(("def ", "class ")):
                    return i

            # Safety limit
            if i - start_line > 100:
                return i

        return len(lines)

    def _find_local_dependencies(
        self, file_path: Path, module_info: ModuleInfo
    ) -> list[str]:
        """Find local dependencies (files in same directory/module)."""
        dependencies = []
        base_dir = file_path.parent

        # Check imports for local files
        for imp in module_info.imports:
            # Try to resolve to local file
            potential_file = base_dir / f"{imp.split('.')[-1]}.py"
            if potential_file.exists():
                dependencies.append(str(potential_file))

        return dependencies

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to approximate token limit.
        Rough estimate: ~4 characters per token.
        """
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n... [truncated]"

    def _estimate_tokens(self, context: dict[str, Any]) -> int:
        """Estimate token count for context."""
        # Rough estimate: serialize to JSON string and count tokens
        import json

        json_str = json.dumps(context)
        # Rough estimate: ~4 characters per token
        return len(json_str) // 4
