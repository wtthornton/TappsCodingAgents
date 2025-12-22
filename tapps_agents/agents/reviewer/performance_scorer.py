"""
Context-Aware Performance Scorer - Language-aware performance analysis

Phase 3.2: Performance Scoring Enhancement

Uses Strategy pattern to provide language-specific performance scoring
with pattern recognition for performance optimizations.
"""

from __future__ import annotations

import ast
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ...core.language_detector import Language


class PerformanceStrategy(ABC):
    """Base strategy for language-specific performance scoring."""

    @abstractmethod
    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate performance score (0-10 scale, higher is better).

        Args:
            code: Source code content
            file_path: Optional path to the file
            context: Optional context (other scores, config, etc.)

        Returns:
            Performance score (0.0-10.0)
        """
        pass


class PythonPerformanceStrategy(PerformanceStrategy):
    """Python-specific performance scoring strategy."""

    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate Python performance score.

        Checks for:
        - Caching (functools.lru_cache, functools.cache)
        - Async/await patterns
        - Lazy evaluation (generators)
        - Inefficient patterns (nested loops, large comprehensions)
        """
        score = 10.0
        issues = []
        optimizations = []

        try:
            tree = ast.parse(code)

            # Check for caching patterns
            has_cache = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if (
                            isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "functools"
                            and node.func.attr in ["lru_cache", "cache"]
                        ):
                            has_cache = True
                            optimizations.append("caching")
                    elif isinstance(node.func, ast.Name):
                        if node.func.id in ["lru_cache", "cache"]:
                            has_cache = True
                            optimizations.append("caching")

            # Check for async/await patterns
            has_async = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.args:
                    if any("async" in str(kwarg) for kwarg in node.args.kwonlyargs):
                        pass  # async keyword
                if isinstance(node, ast.FunctionDef) and hasattr(node, "async_"):
                    if node.async_:
                        has_async = True
                        optimizations.append("async_patterns")
                elif isinstance(node, ast.AsyncFunctionDef):
                    has_async = True
                    optimizations.append("async_patterns")

            # Check for generators (lazy evaluation)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if any(isinstance(n, ast.Yield) or isinstance(n, ast.YieldFrom) for n in ast.walk(node)):
                        optimizations.append("generators")

            # Check for inefficient patterns
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check function size
                    if hasattr(node, "end_lineno") and node.end_lineno is not None:
                        func_lines = node.end_lineno - node.lineno
                    else:
                        func_lines = len(code.split("\n")[node.lineno - 1 : node.lineno + 49])

                    if func_lines > 100:
                        issues.append("very_large_function")
                    elif func_lines > 50:
                        issues.append("large_function")

                    # Check nesting depth
                    max_depth = self._get_max_nesting_depth(node)
                    if max_depth > 6:
                        issues.append("very_deep_nesting")
                    elif max_depth > 4:
                        issues.append("deep_nesting")

                # Check for nested loops
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if isinstance(child, ast.For) and child != node:
                            issues.append("nested_loops")
                            break

                # Check for expensive comprehensions
                if isinstance(node, ast.ListComp):
                    func_calls = sum(1 for n in ast.walk(node) if isinstance(n, ast.Call))
                    if func_calls > 5:
                        issues.append("expensive_comprehension")

        except SyntaxError:
            return 0.0
        except Exception:
            return 5.0  # Neutral score on parse errors

        # Apply penalties
        penalty_map = {
            "large_function": 0.5,
            "very_large_function": 1.5,
            "deep_nesting": 1.0,
            "very_deep_nesting": 2.0,
            "nested_loops": 1.5,
            "expensive_comprehension": 0.5,
        }

        seen_issues = set()
        for issue in issues:
            if issue not in seen_issues:
                score -= penalty_map.get(issue, 0.5)
                seen_issues.add(issue)

        # Apply bonuses for optimizations
        bonus_map = {
            "caching": 1.5,
            "async_patterns": 1.0,
            "generators": 0.5,
        }

        seen_optimizations = set()
        for opt in optimizations:
            if opt not in seen_optimizations:
                score += bonus_map.get(opt, 0.5)
                seen_optimizations.add(opt)

        return max(0.0, min(10.0, score))

    def _get_max_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a function."""
        max_depth = 0

        def visit(node: ast.AST, depth: int) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                    visit(child, depth + 1)
                else:
                    visit(child, depth)

        visit(node, 0)
        return max_depth


class TypeScriptPerformanceStrategy(PerformanceStrategy):
    """TypeScript-specific performance scoring strategy."""

    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate TypeScript performance score.

        Checks for:
        - Type optimizations (const assertions, type narrowing)
        - Compilation optimizations (readonly, as const)
        - Efficient type definitions
        """
        score = 7.0  # Start with neutral score
        optimizations = []

        # Check for const assertions (as const)
        if re.search(r"\bas\s+const\b", code):
            optimizations.append("const_assertions")
            score += 1.0

        # Check for readonly modifiers
        readonly_count = len(re.findall(r"\breadonly\b", code))
        if readonly_count > 0:
            optimizations.append("readonly_types")
            score += min(readonly_count * 0.1, 0.5)

        # Check for type narrowing patterns
        if re.search(r"if\s*\([^)]*\)\s*\{[^}]*typeof\s+[^}]+\}", code):
            optimizations.append("type_narrowing")
            score += 0.5

        # Check for efficient type definitions (type vs interface)
        # Prefer type for unions/intersections, interface for objects
        type_defs = len(re.findall(r"\btype\s+\w+\s*=", code))
        interface_defs = len(re.findall(r"\binterface\s+\w+", code))

        # Check for const enums (compile-time optimization)
        if re.search(r"\bconst\s+enum\b", code):
            optimizations.append("const_enums")
            score += 0.5

        # Check for efficient array/object patterns
        if re.search(r"Object\.freeze|Object\.seal", code):
            optimizations.append("immutable_objects")
            score += 0.5

        # Penalize any patterns (weaker performance)
        if re.search(r"any\s*[:\[]", code):
            score -= 0.5

        # Check for inefficient patterns
        # Nested object destructuring can be expensive
        deep_destructuring = re.search(r"\{[^}]*\{[^}]*\{[^}]*\}[^}]*\}[^}]*\}", code)
        if deep_destructuring:
            score -= 0.5

        return max(0.0, min(10.0, score))


class ReactPerformanceStrategy(PerformanceStrategy):
    """React-specific performance scoring strategy."""

    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate React performance score.

        Checks for:
        - Memoization (useMemo, useCallback, React.memo)
        - Lazy loading (React.lazy, dynamic imports)
        - Code splitting
        - Re-render optimization patterns
        """
        score = 7.0  # Start with neutral score
        optimizations = []

        # Memoization patterns (highest impact)
        memo_count = len(re.findall(r"React\.memo\(|memo\(", code))
        use_memo_count = len(re.findall(r"useMemo\(", code))
        use_callback_count = len(re.findall(r"useCallback\(", code))

        if memo_count > 0 or use_memo_count > 0 or use_callback_count > 0:
            optimizations.append("memoization")
            # Cap bonus at 2.0 for memoization
            memo_bonus = min((memo_count * 0.5 + use_memo_count * 0.3 + use_callback_count * 0.3), 2.0)
            score += memo_bonus

        # Lazy loading (React.lazy)
        lazy_count = len(re.findall(r"lazy\(|React\.lazy", code))
        if lazy_count > 0:
            optimizations.append("lazy_loading")
            score += min(lazy_count * 0.5, 1.0)

        # Code splitting (dynamic imports)
        dynamic_import_count = len(re.findall(r"import\(|dynamic\s+import", code))
        if dynamic_import_count > 0:
            optimizations.append("code_splitting")
            score += min(dynamic_import_count * 0.3, 0.5)

        # Check for proper key usage in lists (prevents unnecessary re-renders)
        jsx_list_pattern = re.search(r"\.map\s*\([^)]*=>\s*\([^)]*<[^>]+", code)
        has_key_in_map = bool(re.search(r"\.map\s*\([^)]*key\s*=", code))
        if jsx_list_pattern and not has_key_in_map:
            score -= 1.0  # Missing keys in lists

        # Check for expensive operations in render
        # useEffect is good, direct async in render is bad
        has_use_effect = bool(re.search(r"useEffect\(", code))
        has_async_in_render = bool(re.search(r"(const|let|var)\s+\w+\s*=\s*async\s*\(\)\s*=>", code))
        if has_async_in_render and not has_use_effect:
            score -= 0.5

        # Check for unnecessary re-renders (inline functions in JSX)
        inline_fn_count = len(re.findall(r"onClick\s*=\s*\{[^}]*\(\)\s*=>", code))
        if inline_fn_count > 5:
            score -= min(inline_fn_count * 0.1, 1.0)

        return max(0.0, min(10.0, score))


class PerformanceScorer:
    """
    Context-aware performance scorer using Strategy pattern.

    Phase 3.2: Performance Scoring Enhancement
    """

    _strategies: dict[Language, PerformanceStrategy] = {}

    def __init__(self):
        """Initialize performance scorer with language strategies."""
        if not PerformanceScorer._strategies:
            PerformanceScorer._strategies = {
                Language.PYTHON: PythonPerformanceStrategy(),
                Language.TYPESCRIPT: TypeScriptPerformanceStrategy(),
                Language.JAVASCRIPT: TypeScriptPerformanceStrategy(),  # Use TypeScript strategy for JS
                Language.REACT: ReactPerformanceStrategy(),
            }

    def calculate(
        self,
        code: str,
        language: Language,
        file_path: Path | None = None,
        context: dict[str, Any] | None = None,
    ) -> float:
        """
        Calculate performance score for code in the given language.

        Args:
            code: Source code content
            language: Detected language
            file_path: Optional path to the file
            context: Optional context (other scores, config, etc.)

        Returns:
            Performance score (0.0-10.0)
        """
        strategy = PerformanceScorer._strategies.get(language)

        if not strategy:
            # Fallback: use Python strategy (most comprehensive)
            strategy = PerformanceScorer._strategies.get(Language.PYTHON, PythonPerformanceStrategy())

        return strategy.calculate(code, file_path, context)

