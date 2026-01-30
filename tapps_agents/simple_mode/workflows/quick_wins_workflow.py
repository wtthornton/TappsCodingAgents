"""Quick wins workflow for high-ROI optimizations."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QuickWin:
    """A quick win optimization opportunity."""
    name: str
    impact: int  # % improvement
    effort: int  # minutes
    description: str
    category: str  # "performance", "security", "maintainability"
    code_example: str | None = None


@dataclass
class QuickWinsResult:
    """Result of quick wins analysis."""
    file_path: str
    quick_wins: list[QuickWin] = field(default_factory=list)
    total_impact: int = 0
    total_effort: int = 0
    focus_area: str = "all"


class QuickWinsWorkflow:
    """
    Quick wins workflow for high-ROI optimizations.

    Steps:
    1. Quick analysis (2 min)
    2. Identify high-value optimizations (3 min)
    3. Generate optimization report (1 min)

    Total: ~6 minutes
    """

    def __init__(self, reviewer: Any = None):
        """
        Initialize quick wins workflow.

        Args:
            reviewer: Optional reviewer agent for code analysis
        """
        self.reviewer = reviewer

    async def execute(
        self,
        file_path: str,
        focus: str | None = None,
        project_root: Path | None = None
    ) -> QuickWinsResult:
        """
        Execute quick wins workflow.

        Args:
            file_path: Path to file to analyze
            focus: Optional focus area ("performance", "security", "maintainability", or None for all)
            project_root: Optional project root path

        Returns:
            QuickWinsResult with optimization opportunities
        """
        print("\n" + "="*60)
        print("⚡ QUICK WINS WORKFLOW")
        print("="*60)
        print(f"\nFinding high-ROI optimizations in: {file_path}")
        if focus:
            print(f"Focus area: {focus}")
        print()

        # Step 1: Quick analysis
        print("📊 Step 1/3: Quick Analysis (2 min)")
        analysis = await self._quick_analysis(file_path, project_root)

        # Step 2: Identify quick wins
        print("\n⚡ Step 2/3: Identifying Quick Wins (3 min)")
        quick_wins = self._identify_quick_wins(analysis, focus)

        # Step 3: Generate report
        print("\n📄 Step 3/3: Generating Report (1 min)")
        result = QuickWinsResult(
            file_path=file_path,
            quick_wins=quick_wins,
            total_impact=sum(w.impact for w in quick_wins),
            total_effort=sum(w.effort for w in quick_wins),
            focus_area=focus or "all"
        )

        print(f"\n✅ Found {len(quick_wins)} quick wins!")
        print(f"   Total impact: {result.total_impact}% improvement")
        print(f"   Total effort: {result.total_effort} minutes\n")

        return result

    async def _quick_analysis(
        self,
        file_path: str,
        project_root: Path | None
    ) -> dict[str, Any]:
        """Quick analysis of code quality."""
        if not self.reviewer:
            # Basic heuristic analysis without reviewer
            return {
                "quality_score": 7.0,
                "complexity": 7.0,
                "security": 7.0,
                "maintainability": 7.0,
                "performance_hints": ["Consider caching", "Add early exits"],
                "security_hints": ["Validate inputs", "Add error handling"],
                "maintainability_hints": ["Extract methods", "Add docstrings"]
            }

        try:
            # Use reviewer for quick analysis
            result = await self.reviewer.run(
                "score",  # Quick scoring instead of full review
                file_path=file_path
            )

            return {
                "quality_score": result.get("overall_score", 70) / 10.0,
                "complexity": result.get("complexity_score", 7.0),
                "security": result.get("security_score", 7.0),
                "maintainability": result.get("maintainability_score", 7.0),
                "issues": result.get("issues", [])
            }
        except Exception as e:
            print(f"⚠️  Quick analysis failed: {e}. Using heuristics.")
            return {
                "quality_score": 7.0,
                "complexity": 7.0,
                "security": 7.0,
                "maintainability": 7.0
            }

    def _identify_quick_wins(
        self,
        analysis: dict[str, Any],
        focus: str | None
    ) -> list[QuickWin]:
        """Identify high-ROI optimizations (effort < 15 min, impact > 50%)."""
        quick_wins: list[QuickWin] = []

        # Performance quick wins
        if not focus or focus == "performance":
            quick_wins.extend(self._find_performance_wins(analysis))

        # Security quick wins
        if not focus or focus == "security":
            quick_wins.extend(self._find_security_wins(analysis))

        # Maintainability quick wins
        if not focus or focus == "maintainability":
            quick_wins.extend(self._find_maintainability_wins(analysis))

        # Filter by ROI (effort <= 15 min, impact >= 50%)
        high_roi_wins = [
            w for w in quick_wins
            if w.effort <= 15 and w.impact >= 50
        ]

        # Sort by impact (highest first)
        high_roi_wins.sort(key=lambda x: x.impact, reverse=True)

        # Return top 5
        return high_roi_wins[:5]

    def _find_performance_wins(self, analysis: dict[str, Any]) -> list[QuickWin]:
        """Find performance quick wins."""
        wins: list[QuickWin] = []

        # Early exit optimization
        if analysis.get("complexity", 0) > 8.0:
            wins.append(QuickWin(
                name="Add early exit checks",
                impact=90,
                effort=5,
                description="Add early exit checks before expensive operations",
                category="performance",
                code_example="""
# Before
def process(data):
    result = expensive_operation(data)
    if not data:
        return None
    return result

# After
def process(data):
    if not data:  # Early exit
        return None
    return expensive_operation(data)
"""
            ))

        # Caching optimization
        wins.append(QuickWin(
            name="Add result caching",
            impact=80,
            effort=10,
            description="Cache frequently accessed results to reduce computation",
            category="performance",
            code_example="""
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(x):
    # ... expensive operation ...
    return result
"""
        ))

        # List comprehension optimization
        if analysis.get("complexity", 0) > 7.0:
            wins.append(QuickWin(
                name="Use list comprehensions",
                impact=60,
                effort=8,
                description="Replace loops with list comprehensions for better performance",
                category="performance",
                code_example="""
# Before
result = []
for item in items:
    if condition(item):
        result.append(transform(item))

# After
result = [transform(item) for item in items if condition(item)]
"""
            ))

        return wins

    def _find_security_wins(self, analysis: dict[str, Any]) -> list[QuickWin]:
        """Find security quick wins."""
        wins: list[QuickWin] = []

        security_score = analysis.get("security", 7.0)

        # Input validation
        if security_score < 8.5:
            wins.append(QuickWin(
                name="Add input validation",
                impact=85,
                effort=10,
                description="Validate and sanitize all user inputs",
                category="security",
                code_example="""
def process_user_input(data):
    # Validate input
    if not isinstance(data, str):
        raise ValueError("Input must be string")
    if len(data) > 1000:
        raise ValueError("Input too long")

    # Sanitize
    sanitized = data.strip()

    return process(sanitized)
"""
            ))

        # Error handling
        wins.append(QuickWin(
            name="Add proper error handling",
            impact=70,
            effort=12,
            description="Add try-except blocks to prevent information leakage",
            category="security",
            code_example="""
try:
    result = risky_operation()
except SpecificException as e:
    logger.error("Operation failed", exc_info=True)
    return safe_default_value  # Don't expose error details
"""
        ))

        return wins

    def _find_maintainability_wins(self, analysis: dict[str, Any]) -> list[QuickWin]:
        """Find maintainability quick wins."""
        wins: list[QuickWin] = []

        maintainability_score = analysis.get("maintainability", 7.0)
        complexity = analysis.get("complexity", 7.0)

        # Docstring addition
        if maintainability_score < 8.0:
            wins.append(QuickWin(
                name="Add comprehensive docstrings",
                impact=65,
                effort=15,
                description="Add docstrings to all functions and classes",
                category="maintainability",
                code_example="""
def calculate_total(items: List[Item]) -> float:
    '''Calculate total price of items.

    Args:
        items: List of items to calculate total for

    Returns:
        Total price as float

    Raises:
        ValueError: If items list is empty
    '''
    if not items:
        raise ValueError("Items list cannot be empty")
    return sum(item.price for item in items)
"""
            ))

        # Extract method refactoring
        if complexity > 8.0:
            wins.append(QuickWin(
                name="Extract complex logic into methods",
                impact=75,
                effort=12,
                description="Break down complex functions into smaller, focused methods",
                category="maintainability",
                code_example="""
# Before: One large method
def process_order(order):
    # 50 lines of complex logic
    ...

# After: Extracted methods
def process_order(order):
    validate_order(order)
    calculate_totals(order)
    apply_discounts(order)
    finalize_order(order)
"""
            ))

        # Type hints
        wins.append(QuickWin(
            name="Add type hints",
            impact=55,
            effort=10,
            description="Add type hints for better IDE support and documentation",
            category="maintainability",
            code_example="""
from typing import List, Dict, Optional

def process_data(
    data: List[Dict[str, Any]],
    options: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    '''Process data with options.'''
    # Implementation
    pass
"""
        ))

        return wins
