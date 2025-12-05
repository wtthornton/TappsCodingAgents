"""
Code Scoring System - Calculates objective quality metrics
"""

from typing import Dict, Any, Optional
from pathlib import Path
import ast

# Import analysis libraries
try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    HAS_RADON = True
except ImportError:
    HAS_RADON = False

try:
    import bandit
    from bandit.core import manager
    HAS_BANDIT = True
except ImportError:
    HAS_BANDIT = False

# Type hint for config
try:
    from ...core.config import ScoringWeightsConfig
except ImportError:
    ScoringWeightsConfig = None

# Import coverage tools
try:
    import coverage
    from coverage import Coverage
    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False


class CodeScorer:
    """Calculate code quality scores"""

    def __init__(self, weights: Optional[ScoringWeightsConfig] = None):
        self.has_radon = HAS_RADON
        self.has_bandit = HAS_BANDIT
        self.has_coverage = HAS_COVERAGE
        self.weights = weights  # Will use defaults if None
    
    def score_file(self, file_path: Path, code: str) -> Dict[str, Any]:
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
        scores = {
            "complexity_score": 0.0,
            "security_score": 0.0,
            "maintainability_score": 0.0,
            "test_coverage_score": 0.0,  # Placeholder - needs coverage tool
            "performance_score": 0.0,     # Placeholder - needs profiling
            "metrics": {}
        }
        
        # Complexity Score (0-10, lower is better)
        scores["complexity_score"] = self._calculate_complexity(code)
        scores["metrics"]["complexity"] = scores["complexity_score"]
        
        # Security Score (0-10, higher is better)
        scores["security_score"] = self._calculate_security(file_path, code)
        scores["metrics"]["security"] = scores["security_score"]
        
        # Maintainability Score (0-10, higher is better)
        scores["maintainability_score"] = self._calculate_maintainability(code)
        scores["metrics"]["maintainability"] = scores["maintainability_score"]
        
        # Test Coverage Score (0-10, higher is better)
        # Note: This requires running tests with coverage first
        scores["test_coverage_score"] = self._calculate_test_coverage(file_path)
        scores["metrics"]["test_coverage"] = scores["test_coverage_score"]
        
        # Performance Score (0-10, higher is better)
        scores["performance_score"] = self._calculate_performance(code)
        scores["metrics"]["performance"] = scores["performance_score"]
        
        # Overall Score (weighted average)
        # Use configured weights or defaults
        if self.weights:
            w = self.weights
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
            (10 - scores["complexity_score"]) * w.complexity +  # Invert complexity (lower is better)
            scores["security_score"] * w.security +
            scores["maintainability_score"] * w.maintainability +
            scores["test_coverage_score"] * w.test_coverage +
            scores["performance_score"] * w.performance
        )
        
        return scores
    
    def _calculate_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity (0-10 scale)"""
        if not self.has_radon:
            return 5.0  # Default neutral score
        
        try:
            tree = ast.parse(code)
            complexities = cc_visit(tree)
            
            if not complexities:
                return 1.0
            
            # Get max complexity
            max_complexity = max(cc.complexity for cc in complexities)
            
            # Scale to 0-10 (max complexity ~50 = 10)
            return min(max_complexity / 5.0, 10.0)
        except SyntaxError:
            return 10.0  # Syntax errors = max complexity
    
    def _calculate_security(self, file_path: Path, code: str) -> float:
        """Calculate security score (0-10 scale, higher is better)"""
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
            return max(0.0, 10.0 - (issues * 2))  # -2 points per issue
        
        try:
            # Use bandit for proper security analysis
            b_mgr = manager.BanditManager(
                config={},
                agg_type='file',
                debug=False
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
            return 5.0  # Default neutral on error
        except Exception as e:
            # Catch-all for unexpected errors (should be rare)
            return 5.0  # Default neutral on error
    
    def _calculate_maintainability(self, code: str) -> float:
        """Calculate maintainability index (0-10 scale, higher is better)"""
        if not self.has_radon:
            # Basic heuristic: code length and structure
            lines = code.split('\n')
            avg_line_length = sum(len(l) for l in lines) / len(lines) if lines else 0
            
            # Penalize very long lines
            long_lines = sum(1 for l in lines if len(l) > 100)
            score = 10.0 - (long_lines * 0.5)
            return max(0.0, score)
        
        try:
            # mi_visit expects (code_string, lines_list), not (tree, lines)
            # Parse to check for syntax errors first
            ast.parse(code)
            lines = code.splitlines()
            mi_score = mi_visit(code, lines)
            
            # Maintainability Index: 0-100 scale, convert to 0-10
            # MI > 80 = good (10), MI < 20 = bad (0)
            return min(mi_score / 10.0, 10.0)
        except SyntaxError:
            return 0.0
        except Exception:
            # Fallback on any other error
            return 5.0
    
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
            import xml.etree.ElementTree as ET
            
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
        
        Checks for:
        - Test file existence
        - Test directory structure
        - Test naming patterns
        """
        project_root = self._find_project_root(file_path)
        if project_root is None:
            return 5.0  # Neutral if can't determine
        
        # Look for test files
        test_dirs = ["tests", "test", "tests/unit", "tests/integration"]
        test_patterns = [
            f"test_{file_path.stem}.py",
            f"{file_path.stem}_test.py",
            f"test_{file_path.name}",
        ]
        
        score = 5.0  # Start neutral
        
        for test_dir in test_dirs:
            test_dir_path = project_root / test_dir
            if test_dir_path.exists():
                score += 1.0  # Bonus for having test directory
                for pattern in test_patterns:
                    test_file = test_dir_path / pattern
                    if test_file.exists():
                        score += 2.0  # Bonus for having test file
                        break
        
        return min(score, 10.0)
    
    def _find_project_root(self, file_path: Path) -> Optional[Path]:
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
                    if hasattr(node, 'end_lineno') and node.end_lineno is not None:
                        func_lines = node.end_lineno - node.lineno
                    else:
                        # Estimate: count lines in function body
                        func_lines = len(code.split('\n')[node.lineno - 1:node.lineno + 49]) if len(code.split('\n')) > node.lineno else 50
                    
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
                    func_calls = sum(1 for n in ast.walk(node) if isinstance(n, ast.Call))
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

