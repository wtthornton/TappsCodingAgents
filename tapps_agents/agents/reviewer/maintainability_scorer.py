"""
Context-Aware Maintainability Scorer - Language-aware maintainability analysis

Phase 3.1: Context-Aware Scoring Algorithm

Uses Strategy pattern to provide language-specific maintainability scoring
with pattern recognition, complexity analysis, and code structure evaluation.
"""

from __future__ import annotations

import ast
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ...core.language_detector import Language

# Constants for maintainability scoring
MI_EXCELLENT_THRESHOLD = 80.0  # Maintainability Index threshold for excellent code
MI_POOR_THRESHOLD = 20.0  # Maintainability Index threshold for poor code
MI_SCALE_FACTOR = 10.0  # Scale factor to convert MI (0-100) to score (0-10)
MAX_NESTING_DEPTH_THRESHOLD = 3  # Nesting depth threshold before penalties
MAX_AVG_FUNCTION_LENGTH = 50  # Average function length threshold (lines)
MAX_LINE_LENGTH = 100  # Maximum line length before penalties (characters)
BASE_SCORE = 5.0  # Base score for neutral maintainability


class MaintainabilityStrategy(ABC):
    """Base strategy for language-specific maintainability scoring."""

    @abstractmethod
    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate maintainability score (0-10 scale, higher is better).

        Args:
            code: Source code content
            file_path: Optional path to the file
            context: Optional context (e.g., project structure, dependencies)

        Returns:
            Maintainability score (0-10)
        """
        raise NotImplementedError


class PythonMaintainabilityStrategy(MaintainabilityStrategy):
    """Python-specific maintainability scoring strategy."""

    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """Calculate maintainability for Python code."""
        try:
            # Try to use radon if available (more accurate)
            try:
                from radon.complexity import mi_visit

                lines = code.splitlines()
                mi_score = mi_visit(code, lines)
                # Maintainability Index: 0-100 scale, convert to 0-10
                # MI > 80 = good (10), MI < 20 = bad (0)
                base_score = min(mi_score / MI_SCALE_FACTOR, 10.0)
            except ImportError:
                # Fallback to heuristic-based scoring
                base_score = self._heuristic_score(code)

            # Apply context-aware adjustments
            adjustments = self._analyze_patterns(code, file_path)
            final_score = base_score + adjustments

            return max(0.0, min(10.0, final_score))

        except SyntaxError:
            return 0.0
        except Exception:
            return BASE_SCORE  # Neutral on error

    def get_issues(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get specific maintainability issues (Phase 2 - P0).
        
        Returns list of issues with details like missing docstrings, long functions, etc.
        """
        from .issue_tracking import MaintainabilityIssue

        issues: list[MaintainabilityIssue] = []
        code_lines = code.splitlines()

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return [MaintainabilityIssue(
                issue_type="syntax_error",
                message="File contains syntax errors",
                severity="high"
            ).__dict__]

        # Check for missing docstrings in functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has docstring
                if not ast.get_docstring(node):
                    issues.append(MaintainabilityIssue(
                        issue_type="missing_docstring",
                        message=f"Function '{node.name}' is missing a docstring",
                        line_number=node.lineno,
                        function_name=node.name,
                        severity="medium",
                        suggestion="Add a docstring explaining the function's purpose, parameters, and return value"
                    ))

                # Check function length
                if hasattr(node, "end_lineno") and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                else:
                    # Estimate function length
                    func_length = len(code_lines[node.lineno - 1:node.lineno + 50]) if node.lineno <= len(code_lines) else 0

                if func_length > MAX_AVG_FUNCTION_LENGTH:
                    severity = "high" if func_length > 100 else "medium"
                    issues.append(MaintainabilityIssue(
                        issue_type="long_function",
                        message=f"Function '{node.name}' is {func_length} lines long (threshold: {MAX_AVG_FUNCTION_LENGTH})",
                        line_number=node.lineno,
                        function_name=node.name,
                        metric_value=float(func_length),
                        threshold=float(MAX_AVG_FUNCTION_LENGTH),
                        severity=severity,
                        suggestion=f"Extract helper methods or break into smaller functions (target: <{MAX_AVG_FUNCTION_LENGTH} lines)"
                    ))

                # Check nesting depth
                max_nesting = self._get_max_nesting_depth(node)
                if max_nesting > MAX_NESTING_DEPTH_THRESHOLD:
                    severity = "high" if max_nesting > 6 else "medium"
                    issues.append(MaintainabilityIssue(
                        issue_type="deep_nesting",
                        message=f"Function '{node.name}' has {max_nesting} levels of nesting (threshold: {MAX_NESTING_DEPTH_THRESHOLD})",
                        line_number=node.lineno,
                        function_name=node.name,
                        metric_value=float(max_nesting),
                        threshold=float(MAX_NESTING_DEPTH_THRESHOLD),
                        severity=severity,
                        suggestion="Extract nested logic into separate functions to reduce complexity"
                    ))

            elif isinstance(node, ast.ClassDef):
                # Check if class has docstring
                if not ast.get_docstring(node):
                    issues.append(MaintainabilityIssue(
                        issue_type="missing_docstring",
                        message=f"Class '{node.name}' is missing a docstring",
                        line_number=node.lineno,
                        class_name=node.name,
                        severity="medium",
                        suggestion="Add a docstring explaining the class's purpose and usage"
                    ))

        # Check for long lines
        for i, line in enumerate(code_lines, 1):
            if len(line) > MAX_LINE_LENGTH:
                issues.append(MaintainabilityIssue(
                    issue_type="long_line",
                    message=f"Line {i} is {len(line)} characters long (threshold: {MAX_LINE_LENGTH})",
                    line_number=i,
                    metric_value=float(len(line)),
                    threshold=float(MAX_LINE_LENGTH),
                    severity="low",
                    suggestion=f"Break long line into multiple lines or extract to variable"
                ))

        # Check for missing type hints in function signatures
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if return type annotation is missing
                if node.returns is None:
                    issues.append(MaintainabilityIssue(
                        issue_type="missing_type_hint",
                        message=f"Function '{node.name}' is missing return type annotation",
                        line_number=node.lineno,
                        function_name=node.name,
                        severity="low",
                        suggestion="Add return type annotation (e.g., -> str, -> int, -> None)"
                    ))

                # Check if all parameters have type hints
                params_without_hints = [arg.arg for arg in node.args.args if arg.annotation is None]
                if params_without_hints:
                    issues.append(MaintainabilityIssue(
                        issue_type="missing_type_hints",
                        message=f"Function '{node.name}' parameters missing type hints: {', '.join(params_without_hints)}",
                        line_number=node.lineno,
                        function_name=node.name,
                        severity="low",
                        suggestion="Add type annotations to all function parameters"
                    ))

        # Convert to dict format
        return [
            {
                "issue_type": issue.issue_type,
                "message": issue.message,
                "line_number": issue.line_number,
                "severity": issue.severity,
                "suggestion": issue.suggestion,
                "function_name": issue.function_name,
                "class_name": issue.class_name,
                "metric_value": issue.metric_value,
                "threshold": issue.threshold,
            }
            for issue in issues
        ]

    def _get_max_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in an AST node."""
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                child_depth = self._get_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._get_max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        return max_depth

    def _heuristic_score(self, code: str) -> float:
        """Heuristic-based scoring when radon is not available."""
        lines = code.split("\n")
        total_lines = len(lines)

        if total_lines == 0:
            return BASE_SCORE

        score = BASE_SCORE  # Base score

        # Positive factors
        has_docstrings = bool(re.search(r'""".*?"""', code, re.DOTALL))
        has_type_hints = bool(re.search(r"def\s+\w+\s*\([^)]*:\s*(str|int|float|bool|list|dict)", code))
        has_async = bool(re.search(r"async\s+def|await\s+", code))
        has_error_handling = bool(re.search(r"try\s*:|except\s+", code))
        has_dataclasses = bool(re.search(r"@dataclass|from dataclasses import", code))
        has_pydantic = bool(re.search(r"from pydantic import|BaseModel", code))

        # Negative factors
        long_lines = sum(1 for line in lines if len(line) > MAX_LINE_LENGTH)
        nesting_depth = self._calculate_nesting_depth(code)
        function_count = len(re.findall(r"def\s+\w+\s*\(", code))
        avg_function_length = total_lines / max(function_count, 1)

        # Apply adjustments
        if has_docstrings:
            score += 1.0
        if has_type_hints:
            score += 1.5
        if has_async:
            score += 0.5
        if has_error_handling:
            score += 0.5
        if has_dataclasses or has_pydantic:
            score += 0.5

        if long_lines > 0:
            score -= min(long_lines / total_lines * 1.5, 1.5)
        if nesting_depth > MAX_NESTING_DEPTH_THRESHOLD:
            score -= min((nesting_depth - MAX_NESTING_DEPTH_THRESHOLD) * 0.5, 2.0)
        if avg_function_length > MAX_AVG_FUNCTION_LENGTH:
            score -= min((avg_function_length - MAX_AVG_FUNCTION_LENGTH) / MAX_AVG_FUNCTION_LENGTH * 1.0, 1.5)

        return max(0.0, min(10.0, score))

    def _analyze_patterns(self, code: str, file_path: Path | None = None) -> float:
        """Analyze Python-specific patterns for maintainability adjustments."""
        adjustments = 0.0

        # Good patterns
        if re.search(r"@lru_cache|@functools\.lru_cache", code):
            adjustments += 0.3  # Caching improves maintainability
        if re.search(r"from typing import|from __future__ import annotations", code):
            adjustments += 0.2  # Type hints improve maintainability
        if re.search(r"class\s+\w+\(.*BaseModel|class\s+\w+\(.*Pydantic", code):
            adjustments += 0.3  # Pydantic models improve structure
        if re.search(r"async def|asyncio\.|TaskGroup", code):
            adjustments += 0.2  # Modern async patterns

        # Bad patterns (penalties)
        if re.search(r"eval\(|exec\(|__import__\(", code):
            adjustments -= 1.0  # Security/maintainability risk
        if re.search(r"global\s+\w+", code):
            adjustments -= 0.3  # Global state reduces maintainability

        return adjustments

    def _calculate_nesting_depth(self, code: str) -> int:
        """Calculate maximum nesting depth in code."""
        try:
            tree = ast.parse(code)
            max_depth = 0

            def visit_node(node: ast.AST, depth: int = 0) -> None:
                nonlocal max_depth
                max_depth = max(max_depth, depth)

                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                        visit_node(child, depth + 1)
                    else:
                        visit_node(child, depth)

            visit_node(tree)
            return max_depth
        except SyntaxError:
            return 0


class TypeScriptMaintainabilityStrategy(MaintainabilityStrategy):
    """TypeScript-specific maintainability scoring strategy."""

    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """Calculate maintainability for TypeScript code."""
        lines = code.split("\n")
        total_lines = len(lines)

        if total_lines == 0:
            return BASE_SCORE

        # Base score - TypeScript has better type safety
        is_typescript = file_path and file_path.suffix in [".ts", ".tsx"]
        TYPESCRIPT_BASE_BOOST = 1.0  # TypeScript gets 1.0 point boost for type safety
        score = BASE_SCORE + TYPESCRIPT_BASE_BOOST if is_typescript else BASE_SCORE

        # Pattern analysis
        patterns = self._analyze_patterns(code, is_typescript)
        score += patterns["positive"]
        score -= patterns["negative"]

        # Structure analysis
        structure = self._analyze_structure(code, total_lines)
        score += structure["positive"]
        score -= structure["negative"]

        return max(0.0, min(10.0, score))

    def _analyze_patterns(self, code: str, is_typescript: bool) -> dict[str, float]:
        """Analyze TypeScript/JavaScript patterns."""
        positive = 0.0
        negative = 0.0

        # Type safety patterns
        has_types = sum(
            1
            for line in code.split("\n")
            if ": " in line
            and (
                "string" in line
                or "number" in line
                or "boolean" in line
                or "object" in line
                or "Array<" in line
                or "Promise<" in line
                or "Record<" in line
            )
        )
        has_interfaces = len(re.findall(r"interface\s+\w+", code))
        has_type_aliases = len(re.findall(r"type\s+\w+\s*=", code))
        has_generics = len(re.findall(r"<\w+>", code))
        has_const_assertions = bool(re.search(r"as const", code))

        # Documentation
        has_jsdoc = bool(re.search(r"/\*\*[\s\S]*?\*/", code))
        has_comments = sum(
            1 for line in code.split("\n") if line.strip().startswith("//") or "/*" in line
        )

        # Error handling
        has_error_handling = bool(re.search(r"try\s*\{|catch\s*\(|throw\s+new\s+Error", code))

        # Code organization
        has_exports = len(re.findall(r"export\s+(const|function|class|interface|type)", code))
        has_imports = len(re.findall(r"import\s+.*from\s+['\"]", code))

        # Apply positive factors
        if is_typescript:
            if has_types > 0:
                positive += min(has_types / len(code.split("\n")) * 2.5, 2.5)
            if has_interfaces > 0:
                positive += min(has_interfaces * 0.3, 1.0)
            if has_type_aliases > 0:
                positive += min(has_type_aliases * 0.2, 0.5)
            if has_generics > 0:
                positive += min(has_generics * 0.1, 0.5)
            if has_const_assertions:
                positive += 0.2

        if has_jsdoc:
            positive += 1.5
        if has_comments > 0:
            positive += min(has_comments / len(code.split("\n")) * 2, 2.0)
        if has_error_handling:
            positive += 0.5
        if has_exports > 0:
            positive += min(has_exports * 0.1, 0.5)
        if has_imports > 0:
            positive += min(has_imports * 0.05, 0.3)

        # Negative factors
        long_lines = sum(1 for line in code.split("\n") if len(line) > 120)
        nesting_depth = self._calculate_nesting_depth(code)
        function_count = len(re.findall(r"(function|const\s+\w+\s*=\s*\(|=>\s*\{)", code))
        avg_function_length = len(code.split("\n")) / max(function_count, 1)

        if long_lines > 0:
            negative += min(long_lines / len(code.split("\n")) * 1.5, 1.5)
        if nesting_depth > 3:
            negative += min((nesting_depth - 3) * 0.5, 2.0)
        if avg_function_length > 50:
            negative += min((avg_function_length - 50) / 50 * 1.0, 1.5)

        # Bad patterns
        if re.search(r"any\s+", code):
            negative += 0.5  # Use of 'any' reduces type safety
        if re.search(r"eval\(|Function\(", code):
            negative += 1.0  # Security/maintainability risk

        return {"positive": positive, "negative": negative}

    def _analyze_structure(self, code: str, total_lines: int) -> dict[str, float]:
        """Analyze code structure and organization."""
        positive = 0.0
        negative = 0.0

        # Check for proper module structure
        has_default_export = bool(re.search(r"export\s+default", code))
        has_named_exports = len(re.findall(r"export\s+(const|function|class)", code)) > 0

        if has_default_export or has_named_exports:
            positive += 0.3

        # Check for circular dependencies (heuristic)
        imports = re.findall(r"import\s+.*from\s+['\"]([^'\"]+)['\"]", code)
        if len(set(imports)) < len(imports):
            negative += 0.5  # Potential circular dependencies

        return {"positive": positive, "negative": negative}

    def _calculate_nesting_depth(self, code: str) -> int:
        """Calculate maximum nesting depth (heuristic-based)."""
        max_depth = 0
        current_depth = 0

        for line in code.split("\n"):
            # Count opening braces
            current_depth += line.count("{") - line.count("}")
            max_depth = max(max_depth, current_depth)

        return max_depth


class ReactMaintainabilityStrategy(MaintainabilityStrategy):
    """React-specific maintainability scoring strategy."""

    def __init__(self, typescript_strategy: TypeScriptMaintainabilityStrategy | None = None):
        """Initialize with optional TypeScript strategy for composition."""
        self.typescript_strategy = typescript_strategy or TypeScriptMaintainabilityStrategy()

    def calculate(
        self, code: str, file_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> float:
        """Calculate maintainability for React code."""
        # Start with TypeScript base score
        base_score = self.typescript_strategy.calculate(code, file_path, context)

        # Add React-specific maintainability boost
        react_boost = self._calculate_react_maintainability_boost(code)
        final_score = base_score + react_boost

        return max(0.0, min(10.0, final_score))

    def _calculate_react_maintainability_boost(self, code: str) -> float:
        """Calculate maintainability boost from React patterns (0-2.0)."""
        boost = 0.0

        # Type safety for props
        if re.search(r"interface\s+\w+Props|type\s+\w+Props", code):
            boost += 0.5

        # Proper component structure
        if re.search(
            r"(export\s+)?(const|function)\s+\w+\s*[:=]\s*(\([^)]*\)\s*=>|React\.FC)", code
        ):
            boost += 0.5

        # Error handling
        if re.search(r"try\s*\{|ErrorBoundary|componentDidCatch", code):
            boost += 0.5

        # Documentation (JSDoc)
        if re.search(r"/\*\*.*\*/", code, re.DOTALL):
            boost += 0.5

        # Custom hooks pattern (good separation of concerns)
        if re.search(r"function\s+use\w+\s*\(|const\s+use\w+\s*=", code):
            boost += 0.3

        # Proper state management
        if re.search(r"useState\(|useReducer\(", code):
            boost += 0.2

        return min(boost, 2.0)


class MaintainabilityScorer:
    """
    Context-aware maintainability scorer using Strategy pattern.

    Automatically selects the appropriate strategy based on detected language.
    """

    def __init__(self):
        """Initialize with language-specific strategies."""
        self.strategies: dict[Language, MaintainabilityStrategy] = {
            Language.PYTHON: PythonMaintainabilityStrategy(),
            Language.TYPESCRIPT: TypeScriptMaintainabilityStrategy(),
            Language.JAVASCRIPT: TypeScriptMaintainabilityStrategy(),  # Use TS strategy for JS
            Language.REACT: ReactMaintainabilityStrategy(),
        }

    def calculate(
        self,
        code: str,
        language: Language,
        file_path: Path | None = None,
        context: dict[str, Any] | None = None,
    ) -> float:
        """
        Calculate maintainability score for code in the given language.

        Args:
            code: Source code content
            language: Detected language
            file_path: Optional path to the file
            context: Optional context (e.g., project structure, dependencies)

        Returns:
            Maintainability score (0-10)
        """
        strategy = self.strategies.get(language)
        if strategy:
            return strategy.calculate(code, file_path, context)

        # Fallback to Python strategy for unknown languages
        return PythonMaintainabilityStrategy().calculate(code, file_path, context)

    def get_issues(
        self,
        code: str,
        language: Language,
        file_path: Path | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get specific maintainability issues (Phase 2 - P0).
        
        Returns list of issues with details like missing docstrings, long functions, etc.
        
        Args:
            code: Source code content
            language: Detected language
            file_path: Optional path to the file
            context: Optional context
            
        Returns:
            List of maintainability issues with details
        """
        strategy = self.strategies.get(language)
        if strategy and hasattr(strategy, "get_issues"):
            return strategy.get_issues(code, file_path, context)

        # Fallback to Python strategy for unknown languages
        if hasattr(PythonMaintainabilityStrategy(), "get_issues"):
            return PythonMaintainabilityStrategy().get_issues(code, file_path, context)

        # Return empty list if strategy doesn't support get_issues
        return []

