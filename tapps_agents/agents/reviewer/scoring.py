"""
Code Scoring System - Calculates objective quality metrics
"""

import ast
import json as json_lib
import logging
import shutil
import subprocess  # nosec B404 - used with fixed args, no shell
import sys
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)

from ...core.config import ProjectConfig, ScoringWeightsConfig
from ...core.language_detector import Language
from ...core.subprocess_utils import wrap_windows_cmd_shim
from .score_constants import ComplexityConstants, SecurityConstants
from .validation import validate_code_input

# Import analysis libraries
try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit

    HAS_RADON = True
except ImportError:
    HAS_RADON = False

try:
    import bandit
    from bandit.core import config as bandit_config
    from bandit.core import manager

    HAS_BANDIT = True
except ImportError:
    HAS_BANDIT = False

# Check if ruff is available in PATH or via python -m ruff
def _check_ruff_available() -> bool:
    """Check if ruff is available via 'ruff' command or 'python -m ruff'"""
    # Check for ruff command directly
    if shutil.which("ruff"):
        return True
    # Check for python -m ruff
    try:
        result = subprocess.run(  # nosec B603 - fixed args
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


HAS_RUFF = _check_ruff_available()

# Check if mypy is available in PATH
HAS_MYPY = shutil.which("mypy") is not None


# Check if jscpd is available (via npm/npx)
def _check_jscpd_available() -> bool:
    """Check if jscpd is available via jscpd command or npx jscpd"""
    # Check for jscpd command directly
    if shutil.which("jscpd"):
        return True
    # Check for npx (Node.js package runner)
    npx_path = shutil.which("npx")
    if npx_path:
        try:
            cmd = wrap_windows_cmd_shim([npx_path, "--yes", "jscpd", "--version"])
            result = subprocess.run(  # nosec B603 - fixed args
                cmd,
                capture_output=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    return False


HAS_JSCPD = _check_jscpd_available()

# Import coverage tools
try:
    from coverage import Coverage

    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False


class BaseScorer:
    """
    Base class for all scorers.
    
    Defines the interface that all language-specific scorers must implement.
    """
    
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Score a file and return quality metrics.
        
        Args:
            file_path: Path to the file
            code: File content
            
        Returns:
            Dictionary with scores and metrics
        """
        raise NotImplementedError("Subclasses must implement score_file")


class CodeScorer(BaseScorer):
    """Calculate code quality scores for Python files"""

    def __init__(
        self,
        weights: ScoringWeightsConfig | None = None,
        ruff_enabled: bool = True,
        mypy_enabled: bool = True,
        jscpd_enabled: bool = True,
        duplication_threshold: float = 3.0,
        min_duplication_lines: int = 5,
    ):
        self.has_radon = HAS_RADON
        self.has_bandit = HAS_BANDIT
        self.has_coverage = HAS_COVERAGE
        self.has_ruff = HAS_RUFF and ruff_enabled
        self.has_mypy = HAS_MYPY and mypy_enabled
        self.has_jscpd = HAS_JSCPD and jscpd_enabled
        self.duplication_threshold = duplication_threshold
        self.min_duplication_lines = min_duplication_lines
        self.weights = weights  # Will use defaults if None

    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """
        Calculate scores for a code file.

        Returns:
            {
                "complexity_score": float (0-10),
                "security_score": float (0-10),
                "maintainability_score": float (0-10),
                "overall_score": float (0-100),
                "metrics": {...}
            }
        """
        metrics: dict[str, float] = {}
        scores: dict[str, Any] = {
            "complexity_score": 0.0,
            "security_score": 0.0,
            "maintainability_score": 0.0,
            "test_coverage_score": 0.0,
            "performance_score": 0.0,
            "linting_score": 0.0,  # Phase 6.1: Ruff linting score
            "type_checking_score": 0.0,  # Phase 6.2: mypy type checking score
            "duplication_score": 0.0,  # Phase 6.4: jscpd duplication score
            "metrics": metrics,
        }

        # Complexity Score (0-10, lower is better)
        scores["complexity_score"] = self._calculate_complexity(code)
        metrics["complexity"] = float(scores["complexity_score"])

        # Security Score (0-10, higher is better)
        scores["security_score"] = self._calculate_security(file_path, code)
        metrics["security"] = float(scores["security_score"])

        # Maintainability Score (0-10, higher is better)
        scores["maintainability_score"] = self._calculate_maintainability(code)
        metrics["maintainability"] = float(scores["maintainability_score"])

        # Test Coverage Score (0-10, higher is better)
        scores["test_coverage_score"] = self._calculate_test_coverage(file_path)
        metrics["test_coverage"] = float(scores["test_coverage_score"])

        # Performance Score (0-10, higher is better)
        # Phase 3.2: Use context-aware performance scorer
        from .performance_scorer import PerformanceScorer
        from ...core.language_detector import Language

        performance_scorer = PerformanceScorer()
        scores["performance_score"] = performance_scorer.calculate(
            code, Language.PYTHON, file_path, context=None
        )
        metrics["performance"] = float(scores["performance_score"])

        # Linting Score (0-10, higher is better) - Phase 6.1
        scores["linting_score"] = self._calculate_linting_score(file_path)
        metrics["linting"] = float(scores["linting_score"])
        
        # Get actual linting issues for transparency (P1 Improvement)
        linting_issues = self.get_ruff_issues(file_path)
        scores["linting_issues"] = self._format_ruff_issues(linting_issues)
        scores["linting_issue_count"] = len(linting_issues)

        # Type Checking Score (0-10, higher is better) - Phase 6.2
        scores["type_checking_score"] = self._calculate_type_checking_score(file_path)
        metrics["type_checking"] = float(scores["type_checking_score"])
        
        # Get actual type checking issues for transparency (P1 Improvement)
        type_issues = self.get_mypy_errors(file_path)
        scores["type_issues"] = type_issues  # Already formatted
        scores["type_issue_count"] = len(type_issues)

        # Duplication Score (0-10, higher is better) - Phase 6.4
        scores["duplication_score"] = self._calculate_duplication_score(file_path)
        metrics["duplication"] = float(scores["duplication_score"])

        class _Weights(Protocol):
            complexity: float
            security: float
            maintainability: float
            test_coverage: float
            performance: float

        # Overall Score (weighted average)
        # Use configured weights or defaults
        if self.weights is not None:
            w: _Weights = self.weights
        else:
            # Default weights
            class DefaultWeights:
                complexity = 0.20
                security = 0.30
                maintainability = 0.25
                test_coverage = 0.15
                performance = 0.10

            w = DefaultWeights()

        scores["overall_score"] = (
            (10 - scores["complexity_score"])
            * w.complexity  # Invert complexity (lower is better)
            + scores["security_score"] * w.security
            + scores["maintainability_score"] * w.maintainability
            + scores["test_coverage_score"] * w.test_coverage
            + scores["performance_score"] * w.performance
        ) * 10  # Scale from 0-10 weighted sum to 0-100

        # Phase 3.3: Validate all scores before returning
        from .score_validator import ScoreValidator
        from ...core.language_detector import Language

        validator = ScoreValidator()
        validation_results = validator.validate_all_scores(
            scores, language=Language.PYTHON, context=None
        )

        # Update scores with validated/clamped values and add explanations
        validated_scores = {}
        score_explanations = {}
        for category, result in validation_results.items():
            if result.valid and result.calibrated_score is not None:
                validated_scores[category] = result.calibrated_score
                if result.explanation:
                    score_explanations[category] = {
                        "explanation": result.explanation,
                        "suggestions": result.suggestions,
                    }
            else:
                validated_scores[category] = scores.get(category, 0.0)

        # Add explanations to result if any
        if score_explanations:
            validated_scores["_explanations"] = score_explanations

        return validated_scores if validated_scores else scores

    def _calculate_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity (0-10 scale)"""
        # Validate input
        validate_code_input(code, method_name="_calculate_complexity")
        
        if not self.has_radon:
            return 5.0  # Default neutral score

        try:
            tree = ast.parse(code)
            complexities = cc_visit(tree)

            if not complexities:
                return 1.0

            # Get max complexity
            max_complexity = max(cc.complexity for cc in complexities)

            # Scale to 0-10 using constants
            return min(
                max_complexity / ComplexityConstants.SCALING_FACTOR,
                ComplexityConstants.MAX_SCORE
            )
        except SyntaxError:
            return 10.0  # Syntax errors = max complexity

    def _calculate_security(self, file_path: Path | None, code: str) -> float:
        """Calculate security score (0-10 scale, higher is better)"""
        # Validate inputs
        validate_code_input(code, method_name="_calculate_security")
        if file_path is not None and not isinstance(file_path, Path):
            raise ValueError(f"_calculate_security: file_path must be Path or None, got {type(file_path).__name__}")
        
        if not self.has_bandit:
            # Basic heuristic check
            insecure_patterns = [
                "eval(",
                "exec(",
                "__import__",
                "pickle.loads",
                "subprocess.call",
                "os.system",
            ]
            issues = sum(1 for pattern in insecure_patterns if pattern in code)
            return max(
                0.0,
                SecurityConstants.MAX_SCORE - (issues * SecurityConstants.INSECURE_PATTERN_PENALTY)
            )

        try:
            # Use bandit for proper security analysis
            # BanditManager expects a BanditConfig, not a dict. Passing a dict can raise ValueError,
            # which would silently degrade scoring to a neutral 5.0.
            b_conf = bandit_config.BanditConfig()
            b_mgr = manager.BanditManager(
                config=b_conf,
                agg_type="file",
                debug=False,
                verbose=False,
                quiet=True,
                profile=None,
                ignore_nosec=False,
            )
            b_mgr.discover_files([str(file_path)], False)
            b_mgr.run_tests()

            # Count high/medium severity issues
            issues = b_mgr.get_issue_list()
            high_severity = sum(1 for i in issues if i.severity == bandit.HIGH)
            medium_severity = sum(1 for i in issues if i.severity == bandit.MEDIUM)

            # Score: 10 - (high*3 + medium*1)
            score = 10.0 - (high_severity * 3.0 + medium_severity * 1.0)
            return max(0.0, score)
        except (FileNotFoundError, PermissionError, ValueError) as e:
            # Specific exceptions for file/system errors
            logger.warning(f"Security scoring failed for {file_path}: {e}")
            return 5.0  # Default neutral on error
        except Exception as e:
            # Catch-all for unexpected errors (should be rare)
            logger.warning(f"Unexpected error during security scoring for {file_path}: {e}", exc_info=True)
            return 5.0  # Default neutral on error

    def _calculate_maintainability(self, code: str) -> float:
        """
        Calculate maintainability index (0-10 scale, higher is better).
        
        Phase 3.1: Enhanced with context-aware scoring using MaintainabilityScorer.
        Phase 2 (P0): Maintainability issues are captured separately via get_maintainability_issues().
        """
        from .maintainability_scorer import MaintainabilityScorer
        from ...core.language_detector import Language

        # Use context-aware maintainability scorer
        scorer = MaintainabilityScorer()
        return scorer.calculate(code, Language.PYTHON, file_path=None, context=None)

    def get_maintainability_issues(
        self, code: str, file_path: Path | None = None
    ) -> list[dict[str, Any]]:
        """
        Get specific maintainability issues (Phase 2 - P0).
        
        Returns list of issues with details like missing docstrings, long functions, etc.
        
        Args:
            code: Source code content
            file_path: Optional path to the file
            
        Returns:
            List of maintainability issues with details
        """
        from .maintainability_scorer import MaintainabilityScorer
        from ...core.language_detector import Language

        scorer = MaintainabilityScorer()
        return scorer.get_issues(code, Language.PYTHON, file_path=file_path, context=None)

    def _calculate_test_coverage(self, file_path: Path) -> float:
        """
        Calculate test coverage score (0-10 scale, higher is better).

        Attempts to read coverage data from:
        1. coverage.xml file in project root or .coverage file
        2. Falls back to heuristic if no coverage data available

        Args:
            file_path: Path to the file being scored

        Returns:
            Coverage score (0-10 scale)
        """
        if not self.has_coverage:
            # No coverage tool available, use heuristic
            return self._coverage_heuristic(file_path)

        try:
            # Try to find and parse coverage data
            project_root = self._find_project_root(file_path)
            if project_root is None:
                return 5.0  # Neutral if can't find project root

            # Look for coverage.xml first (pytest-cov output)
            coverage_xml = project_root / "coverage.xml"
            if coverage_xml.exists():
                return self._parse_coverage_xml(coverage_xml, file_path)

            # Look for .coverage database file
            coverage_db = project_root / ".coverage"
            if coverage_db.exists():
                return self._parse_coverage_db(coverage_db, file_path)

            # No coverage data found, use heuristic
            return self._coverage_heuristic(file_path)

        except Exception:
            # Fallback to heuristic on any error
            return self._coverage_heuristic(file_path)

    def _parse_coverage_xml(self, coverage_xml: Path, file_path: Path) -> float:
        """Parse coverage.xml and return coverage percentage for file_path"""
        try:
            # coverage.xml is locally generated, but use defusedxml to reduce XML attack risk.
            from defusedxml import ElementTree as ET

            tree = ET.parse(coverage_xml)
            root = tree.getroot()

            # Get relative path from project root
            project_root = coverage_xml.parent
            try:
                rel_path = file_path.relative_to(project_root)
                file_path_str = str(rel_path).replace("\\", "/")
            except ValueError:
                # File not in project root
                return 5.0

            # Find coverage for this file
            for package in root.findall(".//package"):
                for class_elem in package.findall(".//class"):
                    file_name = class_elem.get("filename", "")
                    if file_name == file_path_str or file_path.name in file_name:
                        # Get line-rate (coverage percentage)
                        line_rate = float(class_elem.get("line-rate", "0.0"))
                        # Convert 0-1 scale to 0-10 scale
                        return line_rate * 10.0

            # File not found in coverage report
            return 0.0
        except Exception:
            return 5.0  # Default on error

    def _parse_coverage_db(self, coverage_db: Path, file_path: Path) -> float:
        """Parse .coverage database and return coverage percentage"""
        try:
            cov = Coverage()
            cov.load()

            # Get coverage data
            data = cov.get_data()

            # Try to find file in coverage data
            try:
                rel_path = file_path.relative_to(coverage_db.parent)
                file_path_str = str(rel_path).replace("\\", "/")
            except ValueError:
                return 5.0

            # Get coverage for this file
            if file_path_str in data.measured_files():
                # Calculate coverage percentage
                lines = data.lines(file_path_str)
                if not lines:
                    return 0.0

                # Count covered vs total lines (simplified)
                # In practice, we'd need to check which lines are executable
                # For now, return neutral score
                return 5.0

            return 0.0  # File not covered
        except Exception:
            return 5.0

    def _coverage_heuristic(self, file_path: Path) -> float:
        """
        Heuristic-based coverage estimate.

        Phase 1 (P0): Fixed to return 0.0 when no test files exist.
        
        Checks for:
        - Test file existence (actual test files, not just directories)
        - Test directory structure
        - Test naming patterns

        Returns:
        - 0.0 if no test files exist (no tests written yet)
        - 5.0 if test files exist but no coverage data (tests exist but not run)
        - 10.0 if both test files and coverage data exist (not used here, handled by caller)
        """
        project_root = self._find_project_root(file_path)
        if project_root is None:
            return 0.0  # No project root = assume no tests (Phase 1 fix)

        # Look for test files with comprehensive patterns
        test_dirs = ["tests", "test", "tests/unit", "tests/integration", "tests/test", "test/test"]
        test_patterns = [
            f"test_{file_path.stem}.py",
            f"{file_path.stem}_test.py",
            f"test_{file_path.name}",
            # Also check for module-style test files
            f"test_{file_path.stem.replace('_', '')}.py",
            f"test_{file_path.stem.replace('-', '_')}.py",
        ]
        
        # Also check if the file itself is a test file
        if file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
            # File is a test file, assume it has coverage if it exists
            return 5.0  # Tests exist but no coverage data available

        # Check if any test files actually exist
        test_file_found = False
        for test_dir in test_dirs:
            test_dir_path = project_root / test_dir
            if test_dir_path.exists() and test_dir_path.is_dir():
                for pattern in test_patterns:
                    test_file = test_dir_path / pattern
                    if test_file.exists() and test_file.is_file():
                        test_file_found = True
                        break
                if test_file_found:
                    break

        # Phase 1 fix: Return 0.0 if no test files exist (no tests written yet)
        if not test_file_found:
            return 0.0

        # Test files exist but no coverage data available
        # Return neutral score (tests exist but not run yet)
        return 5.0

    def _find_project_root(self, file_path: Path) -> Path | None:
        """Find project root by looking for common markers"""
        current = file_path.resolve().parent

        # Look for project markers
        markers = [
            ".git",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
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

    def get_performance_issues(
        self, code: str, file_path: Path | None = None
    ) -> list[dict[str, Any]]:
        """
        Get specific performance issues with line numbers (Phase 4 - P1).
        
        Returns list of performance bottlenecks with details like nested loops, expensive operations, etc.
        
        Args:
            code: Source code content
            file_path: Optional path to the file
            
        Returns:
            List of performance issues with line numbers
        """
        from .issue_tracking import PerformanceIssue
        import ast

        issues: list[PerformanceIssue] = []
        code_lines = code.splitlines()

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return [PerformanceIssue(
                issue_type="syntax_error",
                message="File contains syntax errors - cannot analyze performance",
                severity="high"
            ).__dict__]

        # Analyze functions for performance issues
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for nested loops
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        # Check if this loop contains another loop
                        for nested_child in ast.walk(child):
                            if isinstance(nested_child, ast.For) and nested_child != child:
                                # Found nested loop
                                issues.append(PerformanceIssue(
                                    issue_type="nested_loops",
                                    message=f"Nested for loops detected in function '{node.name}' - potential O(n²) complexity",
                                    line_number=child.lineno,
                                    severity="high",
                                    operation_type="loop",
                                    context=f"Nested in function '{node.name}'",
                                    suggestion="Consider using itertools.product() or list comprehensions to flatten nested loops"
                                ))

                    # Check for expensive operations in loops
                    if isinstance(child, ast.For):
                        for loop_child in ast.walk(child):
                            if isinstance(loop_child, ast.Call):
                                # Check for expensive function calls in loops
                                if isinstance(loop_child.func, ast.Name):
                                    func_name = loop_child.func.id
                                    expensive_operations = ["time.fromisoformat", "datetime.fromisoformat", "re.compile", "json.loads"]
                                    if any(exp_op in func_name for exp_op in expensive_operations):
                                        issues.append(PerformanceIssue(
                                            issue_type="expensive_operation_in_loop",
                                            message=f"Expensive operation '{func_name}' called in loop at line {loop_child.lineno} - parse once before loop",
                                            line_number=loop_child.lineno,
                                            severity="medium",
                                            operation_type=func_name,
                                            context=f"In loop at line {child.lineno}",
                                            suggestion=f"Move '{func_name}' call outside the loop and cache the result"
                                        ))

            # Check for list comprehensions with function calls
            if isinstance(node, ast.ListComp):
                func_calls_in_comp = sum(1 for n in ast.walk(node) if isinstance(n, ast.Call))
                if func_calls_in_comp > 5:
                    issues.append(PerformanceIssue(
                        issue_type="expensive_comprehension",
                        message=f"List comprehension at line {node.lineno} contains {func_calls_in_comp} function calls - consider using generator or loop",
                        line_number=node.lineno,
                        severity="medium",
                        operation_type="comprehension",
                        suggestion="Consider using a generator expression or a loop for better performance"
                    ))

        # Convert to dict format
        return [
            {
                "issue_type": issue.issue_type,
                "message": issue.message,
                "line_number": issue.line_number,
                "severity": issue.severity,
                "suggestion": issue.suggestion,
                "operation_type": issue.operation_type,
                "context": issue.context,
            }
            for issue in issues
        ]

    def _calculate_performance(self, code: str) -> float:
        """
        Calculate performance score using static analysis (0-10 scale, higher is better).

        Checks for:
        - Function size (number of lines)
        - Nesting depth
        - Inefficient patterns (N+1 queries, nested loops, etc.)
        - Large list/dict comprehensions
        """
        try:
            tree = ast.parse(code)
            issues = []

            # Analyze functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check function size
                    # Use end_lineno if available (Python 3.8+), otherwise estimate
                    if hasattr(node, "end_lineno") and node.end_lineno is not None:
                        func_lines = node.end_lineno - node.lineno
                    else:
                        # Estimate: count lines in function body
                        func_lines = (
                            len(code.split("\n")[node.lineno - 1 : node.lineno + 49])
                            if len(code.split("\n")) > node.lineno
                            else 50
                        )

                    if func_lines > 50:
                        issues.append("large_function")  # > 50 lines
                    if func_lines > 100:
                        issues.append("very_large_function")  # > 100 lines

                    # Check nesting depth
                    max_depth = self._get_max_nesting_depth(node)
                    if max_depth > 4:
                        issues.append("deep_nesting")  # > 4 levels
                    if max_depth > 6:
                        issues.append("very_deep_nesting")  # > 6 levels

                # Check for nested loops (potential N^2 complexity)
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if isinstance(child, ast.For) and child != node:
                            issues.append("nested_loops")
                            break

                # Check for list comprehensions with function calls
                if isinstance(node, ast.ListComp):
                    # Count function calls in comprehension
                    func_calls = sum(
                        1 for n in ast.walk(node) if isinstance(n, ast.Call)
                    )
                    if func_calls > 5:
                        issues.append("expensive_comprehension")

            # Calculate score based on issues
            # Start with 10, deduct points for issues
            score = 10.0
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

            return max(0.0, min(10.0, score))

        except SyntaxError:
            return 0.0  # Syntax errors = worst performance score
        except Exception:
            return 5.0  # Default on error

    def _get_max_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in an AST node"""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            # Count nesting for control structures
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                child_depth = self._get_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._get_max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _calculate_linting_score(self, file_path: Path) -> float:
        """
        Calculate linting score using Ruff (0-10 scale, higher is better).

        Phase 6: Modern Quality Analysis - Ruff Integration

        Returns:
            Linting score (0-10), where 10 = no issues, 0 = many issues
        """
        if not self.has_ruff:
            return 5.0  # Neutral score if Ruff not available

        # Only check Python files
        if file_path.suffix != ".py":
            return 10.0  # Perfect score for non-Python files (can't lint)

        try:
            # Run ruff check with JSON output
            result = subprocess.run(  # nosec B603
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    "--output-format=json",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,  # 30 second timeout
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            # Parse JSON output
            if result.returncode == 0 and not result.stdout.strip():
                # No issues found
                return 10.0

            try:
                # Ruff JSON format: list of diagnostic objects
                diagnostics = (
                    json_lib.loads(result.stdout) if result.stdout.strip() else []
                )

                if not diagnostics:
                    return 10.0

                # Count issues by severity
                # Ruff severity levels: E (Error), W (Warning), F (Fatal), I (Info)
                error_count = sum(
                    1
                    for d in diagnostics
                    if d.get("code", {}).get("name", "").startswith("E")
                )
                warning_count = sum(
                    1
                    for d in diagnostics
                    if d.get("code", {}).get("name", "").startswith("W")
                )
                fatal_count = sum(
                    1
                    for d in diagnostics
                    if d.get("code", {}).get("name", "").startswith("F")
                )

                # Calculate score: Start at 10, deduct points
                # Errors (E): -2 points each
                # Fatal (F): -3 points each
                # Warnings (W): -0.5 points each
                score = 10.0
                score -= error_count * 2.0
                score -= fatal_count * 3.0
                score -= warning_count * 0.5

                return max(0.0, min(10.0, score))

            except json_lib.JSONDecodeError:
                # If JSON parsing fails, check stderr for errors
                if result.stderr:
                    return 5.0  # Neutral on parsing error
                return 10.0  # No output = no issues

        except subprocess.TimeoutExpired:
            return 5.0  # Neutral on timeout
        except FileNotFoundError:
            # Ruff not found in PATH
            return 5.0
        except Exception:
            # Any other error
            return 5.0

    def get_ruff_issues(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get detailed Ruff linting issues for a file.

        Phase 6: Modern Quality Analysis - Ruff Integration

        Returns:
            List of diagnostic dictionaries with code, message, location, etc.
        """
        if not self.has_ruff or file_path.suffix != ".py":
            return []

        try:
            result = subprocess.run(  # nosec B603
                [
                    sys.executable,
                    "-m",
                    "ruff",
                    "check",
                    "--output-format=json",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            if result.returncode == 0 and not result.stdout.strip():
                return []

            try:
                diagnostics = (
                    json_lib.loads(result.stdout) if result.stdout.strip() else []
                )
                return diagnostics
            except json_lib.JSONDecodeError:
                return []

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return []

    def _calculate_type_checking_score(self, file_path: Path) -> float:
        """
        Calculate type checking score using mypy (0-10 scale, higher is better).

        Phase 6.2: Modern Quality Analysis - mypy Integration
        Phase 5 (P1): Fixed to actually run mypy and return real scores (not static 5.0).

        Returns:
            Type checking score (0-10), where 10 = no issues, 0 = many issues
        """
        if not self.has_mypy:
            logger.debug("mypy not available - returning neutral score")
            return 5.0  # Neutral score if mypy not available

        # Only check Python files
        if file_path.suffix != ".py":
            return 10.0  # Perfect score for non-Python files (can't type check)

        try:
            # Phase 5 fix: Actually run mypy and parse errors
            # Run mypy with show-error-codes for better error parsing
            result = subprocess.run(  # nosec B603
                [
                    sys.executable,
                    "-m",
                    "mypy",
                    "--show-error-codes",
                    "--no-error-summary",
                    "--no-color-output",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,  # 60 second timeout (mypy can be slower than Ruff)
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            # Phase 5 fix: Parse mypy output correctly
            if result.returncode == 0:
                # No type errors found - return perfect score
                logger.debug(f"mypy found no errors for {file_path}")
                return 10.0

            # mypy returns non-zero exit code when errors found
            # mypy outputs errors to stdout (not stderr)
            output = result.stdout.strip()
            if not output:
                # No output but non-zero return code - assume success
                logger.debug(f"mypy returned non-zero but no output for {file_path}")
                return 10.0

            # Parse mypy error output
            # Format: filename:line: error: message [error-code]
            # Or: filename:line:column: error: message [error-code]
            error_lines = [
                line
                for line in output.split("\n")
                if "error:" in line.lower() and file_path.name in line
            ]
            error_count = len(error_lines)

            if error_count == 0:
                # No errors found despite non-zero return code (e.g., config issues)
                logger.debug(f"mypy returned non-zero but no parseable errors for {file_path}")
                return 10.0

            # Phase 5 fix: Calculate score based on actual error count
            # Formula: 10 - (errors * 0.5), but cap at 0.0
            score = 10.0 - (error_count * 0.5)
            logger.debug(f"mypy found {error_count} errors for {file_path}, score: {score:.1f}/10")
            return max(0.0, min(10.0, score))

        except subprocess.TimeoutExpired:
            logger.warning(f"mypy timed out for {file_path}")
            return 5.0  # Neutral on timeout
        except FileNotFoundError:
            # mypy not found in PATH
            logger.debug(f"mypy not found in PATH for {file_path}")
            self.has_mypy = False  # Update availability flag
            return 5.0
        except Exception as e:
            # Any other error
            logger.warning(f"mypy failed for {file_path}: {e}", exc_info=True)
            return 5.0

    def get_mypy_errors(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get detailed mypy type checking errors for a file.

        Phase 6.2: Modern Quality Analysis - mypy Integration

        Returns:
            List of error dictionaries with line, message, error_code, etc.
        """
        if not self.has_mypy or file_path.suffix != ".py":
            return []

        try:
            result = subprocess.run(  # nosec B603
                [
                    sys.executable,
                    "-m",
                    "mypy",
                    "--show-error-codes",
                    "--no-error-summary",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                cwd=file_path.parent if file_path.parent.exists() else None,
            )

            if result.returncode == 0:
                # No errors
                return []

            if not result.stdout.strip():
                return []

            # Parse mypy error output
            # Format: filename:line: error: message [error-code]
            errors = []
            for line in result.stdout.strip().split("\n"):
                if "error:" not in line.lower():
                    continue

                # Parse line: "file.py:12: error: Missing return type [func-returns]"
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    filename = parts[0]
                    try:
                        line_num = int(parts[1])
                    except ValueError:
                        continue

                    error_msg = parts[3].strip()

                    # Extract error code (if present)
                    error_code = None
                    if "[" in error_msg and "]" in error_msg:
                        start = error_msg.rfind("[")
                        end = error_msg.rfind("]")
                        if start < end:
                            error_code = error_msg[start + 1 : end]
                            error_msg = error_msg[:start].strip()

                    errors.append(
                        {
                            "filename": filename,
                            "line": line_num,
                            "message": error_msg,
                            "error_code": error_code,
                            "severity": "error",
                        }
                    )

            return errors

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return []

    def _format_ruff_issues(self, diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Format raw ruff diagnostics into a cleaner structure for output.
        
        P1 Improvement: Include actual lint errors in score output.
        
        Args:
            diagnostics: Raw ruff JSON diagnostics
            
        Returns:
            List of formatted issues with line, code, message, severity
        """
        formatted = []
        for diag in diagnostics:
            # Extract code info (ruff format: {"code": {"name": "F401", ...}})
            code_info = diag.get("code", {})
            if isinstance(code_info, dict):
                code = code_info.get("name", "")
            else:
                code = str(code_info)
            
            # Determine severity from code prefix
            severity = "warning"
            if code.startswith("E") or code.startswith("F"):
                severity = "error"
            elif code.startswith("W"):
                severity = "warning"
            elif code.startswith("I"):
                severity = "info"
            
            # Get location info
            location = diag.get("location", {})
            line = location.get("row", 0) if isinstance(location, dict) else 0
            column = location.get("column", 0) if isinstance(location, dict) else 0
            
            formatted.append({
                "code": code,
                "message": diag.get("message", ""),
                "line": line,
                "column": column,
                "severity": severity,
            })
        
        # Sort by line number
        formatted.sort(key=lambda x: (x.get("line", 0), x.get("column", 0)))
        
        return formatted

    def _calculate_duplication_score(self, file_path: Path) -> float:
        """
        Calculate duplication score using jscpd (0-10 scale, higher is better).

        Phase 6.4: Modern Quality Analysis - jscpd Integration

        Note: jscpd works on directories/files, so we analyze the parent directory
        or file directly. For single file, we analyze just that file.

        Returns:
            Duplication score (0-10), where 10 = no duplication, 0 = high duplication
            Score formula: 10 - (duplication_pct / 10)
        """
        if not self.has_jscpd:
            return 5.0  # Neutral score if jscpd not available

        # jscpd works best on directories or multiple files
        # For single file analysis, we'll analyze the file directly
        try:
            # Determine target (file or directory)
            target = str(file_path)
            if file_path.is_dir():
                target_dir = str(file_path)
            else:
                target_dir = str(file_path.parent)

            # Build jscpd command
            # Use npx if jscpd not directly available
            jscpd_path = shutil.which("jscpd")
            if jscpd_path:
                cmd = [jscpd_path]
            else:
                npx_path = shutil.which("npx")
                if not npx_path:
                    return 5.0  # jscpd not available
                cmd = [npx_path, "--yes", "jscpd"]

            # Add jscpd arguments
            cmd.extend(
                [
                    target,
                    "--format",
                    "json",
                    "--min-lines",
                    str(self.min_duplication_lines),
                    "--reporters",
                    "json",
                    "--output",
                    ".",  # Output to current directory
                ]
            )

            # Run jscpd
            result = subprocess.run(  # nosec B603 - fixed args
                wrap_windows_cmd_shim(cmd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,  # 2 minute timeout (jscpd can be slow on large codebases)
                cwd=target_dir if Path(target_dir).exists() else None,
            )

            # jscpd outputs JSON to stdout when using --reporters json
            # But it might also create a file, so check both
            json_output = result.stdout.strip()

            # Try to parse JSON from stdout
            try:
                if json_output:
                    report_data = json_lib.loads(json_output)
                else:
                    # Check for jscpd-report.json in output directory
                    output_file = Path(target_dir) / "jscpd-report.json"
                    if output_file.exists():
                        with open(output_file, encoding="utf-8") as f:
                            report_data = json_lib.load(f)
                    else:
                        # No duplication found (exit code 0 typically means no issues or success)
                        if result.returncode == 0:
                            return 10.0  # Perfect score (no duplication)
                        return 5.0  # Neutral on parse failure
            except json_lib.JSONDecodeError:
                # JSON parse error - might be text output
                # Try to extract duplication percentage from text output
                # Format: "Found X% duplicated lines out of Y total lines"
                lines = result.stdout.split("\n") + result.stderr.split("\n")
                for line in lines:
                    if "%" in line and "duplicate" in line.lower():
                        # Try to extract percentage
                        try:
                            pct_str = line.split("%")[0].split()[-1]
                            duplication_pct = float(pct_str)
                            score = 10.0 - (duplication_pct / 10.0)
                            return max(0.0, min(10.0, score))
                        except (ValueError, IndexError):
                            pass

                # If we can't parse, default behavior
                if result.returncode == 0:
                    return 10.0  # No duplication found
                return 5.0  # Neutral on parse failure

            # Extract duplication percentage from JSON report
            # jscpd JSON structure: { "percentage": X.X, ... }
            duplication_pct = report_data.get("percentage", 0.0)

            # Calculate score: 10 - (duplication_pct / 10)
            # This means:
            # - 0% duplication = 10.0 score
            # - 3% duplication (threshold) = 9.7 score
            # - 10% duplication = 9.0 score
            # - 30% duplication = 7.0 score
            # - 100% duplication = 0.0 score
            score = 10.0 - (duplication_pct / 10.0)
            return max(0.0, min(10.0, score))

        except subprocess.TimeoutExpired:
            return 5.0  # Neutral on timeout
        except FileNotFoundError:
            # jscpd not found
            return 5.0
        except Exception:
            # Any other error
            return 5.0

    def get_duplication_report(self, file_path: Path) -> dict[str, Any]:
        """
        Get detailed duplication report from jscpd.

        Phase 6.4: Modern Quality Analysis - jscpd Integration

        Returns:
            Dictionary with duplication report data including:
            - percentage: Duplication percentage
            - duplicates: List of duplicate code blocks
            - files: File-level duplication stats
        """
        if not self.has_jscpd:
            return {
                "available": False,
                "percentage": 0.0,
                "duplicates": [],
                "files": [],
            }

        try:
            # Determine target
            if file_path.is_dir():
                target_dir = str(file_path)
                target = str(file_path)
            else:
                target_dir = str(file_path.parent)
                target = str(file_path)

            # Build jscpd command
            jscpd_path = shutil.which("jscpd")
            if jscpd_path:
                cmd = [jscpd_path]
            else:
                npx_path = shutil.which("npx")
                if not npx_path:
                    return {
                        "available": False,
                        "percentage": 0.0,
                        "duplicates": [],
                        "files": [],
                    }
                cmd = [npx_path, "--yes", "jscpd"]

            cmd.extend(
                [
                    target,
                    "--format",
                    "json",
                    "--min-lines",
                    str(self.min_duplication_lines),
                    "--reporters",
                    "json",
                ]
            )

            # Run jscpd
            result = subprocess.run(  # nosec B603 - fixed args
                wrap_windows_cmd_shim(cmd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                cwd=target_dir if Path(target_dir).exists() else None,
            )

            # Parse JSON output
            json_output = result.stdout.strip()
            try:
                if json_output:
                    report_data = json_lib.loads(json_output)
                else:
                    # Check for output file
                    output_file = Path(target_dir) / "jscpd-report.json"
                    if output_file.exists():
                        with open(output_file, encoding="utf-8") as f:
                            report_data = json_lib.load(f)
                    else:
                        return {
                            "available": True,
                            "percentage": 0.0,
                            "duplicates": [],
                            "files": [],
                        }
            except json_lib.JSONDecodeError:
                return {
                    "available": True,
                    "error": "Failed to parse jscpd output",
                    "percentage": 0.0,
                    "duplicates": [],
                    "files": [],
                }

            # Extract relevant data from jscpd report
            # jscpd JSON format varies, but typically has:
            # - percentage: overall duplication percentage
            # - duplicates: array of duplicate pairs
            # - files: file-level statistics

            return {
                "available": True,
                "percentage": report_data.get("percentage", 0.0),
                "duplicates": report_data.get("duplicates", []),
                "files": (
                    report_data.get("statistics", {}).get("files", [])
                    if "statistics" in report_data
                    else []
                ),
                "total_lines": (
                    report_data.get("statistics", {}).get("total", {}).get("lines", 0)
                    if "statistics" in report_data
                    else 0
                ),
                "duplicated_lines": (
                    report_data.get("statistics", {})
                    .get("duplicated", {})
                    .get("lines", 0)
                    if "statistics" in report_data
                    else 0
                ),
            }

        except subprocess.TimeoutExpired:
            return {
                "available": True,
                "error": "jscpd timeout",
                "percentage": 0.0,
                "duplicates": [],
                "files": [],
            }
        except FileNotFoundError:
            return {
                "available": False,
                "percentage": 0.0,
                "duplicates": [],
                "files": [],
            }
        except Exception as e:
            return {
                "available": True,
                "error": str(e),
                "percentage": 0.0,
                "duplicates": [],
                "files": [],
            }


class ScorerFactory:
    """
    Factory to provide appropriate scorer based on language (Strategy Pattern).
    
    Phase 1.2: Language-Specific Scorers
    
    Now uses ScorerRegistry for extensible language support.
    """

    @staticmethod
    def get_scorer(language: Language, config: ProjectConfig | None = None) -> BaseScorer:
        """
        Get the appropriate scorer for a given language.
        
        Uses ScorerRegistry for extensible language support with fallback chains.
        
        Args:
            language: Detected language enum
            config: Optional project configuration
            
        Returns:
            BaseScorer instance appropriate for the language
            
        Raises:
            ValueError: If no scorer is available for the language (even with fallbacks)
        """
        from .scorer_registry import ScorerRegistry
        
        try:
            return ScorerRegistry.get_scorer(language, config)
        except ValueError:
            # If no scorer found, fall back to Python scorer as last resort
            # This maintains backward compatibility but may not work well for non-Python code
            # TODO: In the future, create a GenericScorer that uses metric strategies
            if language != Language.PYTHON:
                # Try Python scorer as absolute last resort
                try:
                    return ScorerRegistry.get_scorer(Language.PYTHON, config)
                except ValueError:
                    pass
            
            # If even Python scorer isn't available, raise the original error
            raise
