"""
Metric Calculation Strategies - Reusable metric calculation logic across languages

This module provides reusable metric calculation strategies that can be shared
across different language-specific scorers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol


class MetricStrategy(Protocol):
    """
    Protocol for metric calculation strategies.
    
    Allows different implementations for different languages while maintaining
    a consistent interface.
    """

    def calculate(
        self, file_path: Path, code: str, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate metric score.
        
        Args:
            file_path: Path to the file being analyzed
            code: File content
            context: Optional context (scores from other metrics, config, etc.)
            
        Returns:
            Metric score (0-10 scale, where higher is generally better,
            except for complexity where lower is better)
        """
        ...


class BaseMetricStrategy(ABC):
    """Base class for metric strategies with common functionality."""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize metric strategy.
        
        Args:
            config: Optional configuration for the metric
        """
        self.config = config or {}

    @abstractmethod
    def calculate(
        self, file_path: Path, code: str, context: dict[str, Any] | None = None
    ) -> float:
        """Calculate metric score. Must be implemented by subclasses."""
        ...

    def validate_score(self, score: float, min_val: float = 0.0, max_val: float = 10.0) -> float:
        """
        Validate and clamp score to valid range.
        
        Args:
            score: Raw score value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Clamped score value
        """
        return max(min_val, min(max_val, score))


class ComplexityStrategy(BaseMetricStrategy):
    """
    Generic complexity calculation strategy.
    
    Uses heuristic analysis that works across multiple languages.
    Can be extended with language-specific AST parsing where available.
    """

    def calculate(
        self, file_path: Path, code: str, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate complexity score using heuristic analysis.
        
        Complexity score: 0-10 scale where LOWER is better
        """
        if not code.strip():
            return 1.0  # Empty file = minimal complexity

        lines = code.split("\n")
        complexity = 1  # Base complexity

        # Language-agnostic complexity indicators
        decision_keywords = [
            "if", "else", "for", "while", "do", "switch", "case", "catch", "try",
            "&&", "||", "?", ":", "?.",
        ]

        # Count decision points
        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            for keyword in decision_keywords:
                # Look for keyword as word boundary
                if f" {keyword} " in f" {stripped} " or f" {keyword}(" in f" {stripped} ":
                    complexity += 1

        # Normalize to 0-10 scale (divide by 5, cap at 10)
        complexity_score = min(complexity / 5.0, 10.0)

        return self.validate_score(complexity_score)


class TestCoverageStrategy(BaseMetricStrategy):
    """
    Generic test coverage detection strategy.
    
    Uses heuristics to detect test files and test coverage.
    Language-specific implementations can extend this.
    """

    def calculate(
        self, file_path: Path, code: str, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate test coverage score using heuristics.
        
        Returns: 0-10 scale where HIGHER is better
        """
        # Start with neutral score
        score = 5.0

        # Look for test files in common locations
        file_name = file_path.name.lower()
        file_stem = file_path.stem.lower()
        file_path.parent.name.lower()

        # Check if this IS a test file
        if any(
            pattern in file_name
            for pattern in ["test", "spec", "specs", "tests"]
        ):
            score += 2.0  # Bonus for having test files

        # Check for test directories
        project_root = self._find_project_root(file_path)
        if project_root:
            test_dirs = ["tests", "test", "__tests__", "spec", "specs"]
            for test_dir in test_dirs:
                test_path = project_root / test_dir
                if test_path.exists() and test_path.is_dir():
                    score += 1.0
                    break

        # Check for corresponding test file
        test_patterns = [
            f"test_{file_stem}",
            f"{file_stem}_test",
            f"{file_stem}.test",
            f"{file_stem}.spec",
        ]

        parent = file_path.parent
        for pattern in test_patterns:
            # Try different extensions
            for ext in [".py", ".ts", ".js", ".tsx", ".jsx", ".java"]:
                test_file = parent / f"{pattern}{ext}"
                if test_file.exists():
                    score += 2.0
                    return self.validate_score(score)

        return self.validate_score(score)

    def _find_project_root(self, file_path: Path) -> Path | None:
        """Find project root by looking for common markers."""
        current = file_path.resolve().parent

        markers = [
            ".git",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "package.json",
            "tsconfig.json",
            ".tapps-agents",
        ]

        for _ in range(10):  # Max 10 levels up
            for marker in markers:
                if (current / marker).exists():
                    return current
            if current.parent == current:
                break
            current = current.parent

        return None


class SecurityStrategy(BaseMetricStrategy):
    """
    Generic security pattern detection strategy.
    
    Detects common security anti-patterns that apply across languages.
    Language-specific implementations can add more sophisticated analysis.
    """

    def calculate(
        self, file_path: Path, code: str, context: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate security score by detecting insecure patterns.
        
        Returns: 0-10 scale where HIGHER is better
        """
        # Start with neutral score
        score = 10.0

        # Language-agnostic insecure patterns
        insecure_patterns = [
            ("eval(", -2.0),  # Code injection
            ("exec(", -2.0),  # Code execution
            ("dangerouslySetInnerHTML", -2.0),  # React XSS
            ("innerHTML", -1.0),  # XSS risk
            ("document.write", -1.0),  # XSS risk
            ("new Function", -2.0),  # Code injection
            ("Buffer.from", -0.5),  # Potential unsafe buffer usage
            ("crypto.randomBytes", 0.5),  # Good: using secure randomness
            ("crypto.getRandomValues", 0.5),  # Good: using secure randomness
        ]

        code_lower = code.lower()
        for pattern, penalty in insecure_patterns:
            if pattern.lower() in code_lower:
                score += penalty

        # Check for SQL injection patterns (heuristic)
        if any(
            pattern in code
            for pattern in ["SELECT", "INSERT", "UPDATE", "DELETE"]
        ):
            # Check for string concatenation in SQL (bad)
            if "+" in code or "f'" in code or 'f"' in code:
                score -= 1.0

        return self.validate_score(score)


# Registry of available metric strategies
AVAILABLE_METRICS: dict[str, type[BaseMetricStrategy]] = {
    "complexity": ComplexityStrategy,
    "test_coverage": TestCoverageStrategy,
    "security": SecurityStrategy,
}


def get_metric_strategy(metric_name: str, config: dict[str, Any] | None = None) -> BaseMetricStrategy | None:
    """
    Get a metric strategy by name.
    
    Args:
        metric_name: Name of the metric strategy
        config: Optional configuration
        
    Returns:
        Metric strategy instance or None if not found
    """
    strategy_class = AVAILABLE_METRICS.get(metric_name)
    if strategy_class:
        return strategy_class(config=config)
    return None

