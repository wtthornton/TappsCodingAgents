"""
Code Scoring System - Calculates objective quality metrics
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import ast
import subprocess
import json as json_lib
import shutil

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

# Check if ruff is available in PATH
HAS_RUFF = shutil.which("ruff") is not None

# Check if mypy is available in PATH
HAS_MYPY = shutil.which("mypy") is not None

# Check if jscpd is available (via npm/npx)
def _check_jscpd_available() -> bool:
    """Check if jscpd is available via jscpd command or npx jscpd"""
    # Check for jscpd command directly
    if shutil.which("jscpd"):
        return True
    # Check for npx (Node.js package runner)
    if shutil.which("npx"):
        try:
            result = subprocess.run(
                ["npx", "--yes", "jscpd", "--version"],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    return False

HAS_JSCPD = _check_jscpd_available()

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

    def __init__(
        self,
        weights: Optional[ScoringWeightsConfig] = None,
        ruff_enabled: bool = True,
        mypy_enabled: bool = True,
        jscpd_enabled: bool = True,
        duplication_threshold: float = 3.0,
        min_duplication_lines: int = 5
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
            "test_coverage_score": 0.0,
            "performance_score": 0.0,
            "linting_score": 0.0,  # Phase 6.1: Ruff linting score
            "type_checking_score": 0.0,  # Phase 6.2: mypy type checking score
            "duplication_score": 0.0,  # Phase 6.4: jscpd duplication score
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
        scores["test_coverage_score"] = self._calculate_test_coverage(file_path)
        scores["metrics"]["test_coverage"] = scores["test_coverage_score"]
        
        # Performance Score (0-10, higher is better)
        scores["performance_score"] = self._calculate_performance(code)
        scores["metrics"]["performance"] = scores["performance_score"]
        
        # Linting Score (0-10, higher is better) - Phase 6.1
        scores["linting_score"] = self._calculate_linting_score(file_path)
        scores["metrics"]["linting"] = scores["linting_score"]
        
        # Type Checking Score (0-10, higher is better) - Phase 6.2
        scores["type_checking_score"] = self._calculate_type_checking_score(file_path)
        scores["metrics"]["type_checking"] = scores["type_checking_score"]
        
        # Duplication Score (0-10, higher is better) - Phase 6.4
        scores["duplication_score"] = self._calculate_duplication_score(file_path)
        scores["metrics"]["duplication"] = scores["duplication_score"]
        
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
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=file_path.parent if file_path.parent.exists() else None
            )
            
            # Parse JSON output
            if result.returncode == 0 and not result.stdout.strip():
                # No issues found
                return 10.0
            
            try:
                # Ruff JSON format: list of diagnostic objects
                diagnostics = json_lib.loads(result.stdout) if result.stdout.strip() else []
                
                if not diagnostics:
                    return 10.0
                
                # Count issues by severity
                # Ruff severity levels: E (Error), W (Warning), F (Fatal), I (Info)
                error_count = sum(1 for d in diagnostics if d.get("code", {}).get("name", "").startswith("E"))
                warning_count = sum(1 for d in diagnostics if d.get("code", {}).get("name", "").startswith("W"))
                fatal_count = sum(1 for d in diagnostics if d.get("code", {}).get("name", "").startswith("F"))
                
                # Calculate score: Start at 10, deduct points
                # Errors (E): -2 points each
                # Fatal (F): -3 points each
                # Warnings (W): -0.5 points each
                score = 10.0
                score -= (error_count * 2.0)
                score -= (fatal_count * 3.0)
                score -= (warning_count * 0.5)
                
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
    
    def get_ruff_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Get detailed Ruff linting issues for a file.
        
        Phase 6: Modern Quality Analysis - Ruff Integration
        
        Returns:
            List of diagnostic dictionaries with code, message, location, etc.
        """
        if not self.has_ruff or file_path.suffix != ".py":
            return []
        
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=file_path.parent if file_path.parent.exists() else None
            )
            
            if result.returncode == 0 and not result.stdout.strip():
                return []
            
            try:
                diagnostics = json_lib.loads(result.stdout) if result.stdout.strip() else []
                return diagnostics
            except json_lib.JSONDecodeError:
                return []
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return []
    
    def _calculate_type_checking_score(self, file_path: Path) -> float:
        """
        Calculate type checking score using mypy (0-10 scale, higher is better).
        
        Phase 6.2: Modern Quality Analysis - mypy Integration
        
        Returns:
            Type checking score (0-10), where 10 = no issues, 0 = many issues
        """
        if not self.has_mypy:
            return 5.0  # Neutral score if mypy not available
        
        # Only check Python files
        if file_path.suffix != ".py":
            return 10.0  # Perfect score for non-Python files (can't type check)
        
        try:
            # Run mypy with JSON output and error codes
            result = subprocess.run(
                ["mypy", "--show-error-codes", "--no-error-summary", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout (mypy can be slower than Ruff)
                cwd=file_path.parent if file_path.parent.exists() else None
            )
            
            # Parse mypy output
            if result.returncode == 0:
                # No type errors found
                return 10.0
            
            # mypy returns non-zero exit code when errors found
            # Count errors from stdout (mypy outputs errors to stdout)
            if not result.stdout.strip():
                # No output = no errors (unlikely but possible)
                return 10.0
            
            # Parse mypy error output
            # Format: filename:line: error: message [error-code]
            error_lines = [line for line in result.stdout.strip().split('\n') 
                          if 'error:' in line.lower()]
            error_count = len(error_lines)
            
            # Calculate score: Start at 10, deduct 0.5 points per error
            # Formula: 10 - (errors * 0.5)
            score = 10.0 - (error_count * 0.5)
            return max(0.0, min(10.0, score))
            
        except subprocess.TimeoutExpired:
            return 5.0  # Neutral on timeout
        except FileNotFoundError:
            # mypy not found in PATH
            return 5.0
        except Exception:
            # Any other error
            return 5.0
    
    def get_mypy_errors(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Get detailed mypy type checking errors for a file.
        
        Phase 6.2: Modern Quality Analysis - mypy Integration
        
        Returns:
            List of error dictionaries with line, message, error_code, etc.
        """
        if not self.has_mypy or file_path.suffix != ".py":
            return []
        
        try:
            result = subprocess.run(
                ["mypy", "--show-error-codes", "--no-error-summary", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=file_path.parent if file_path.parent.exists() else None
            )
            
            if result.returncode == 0:
                # No errors
                return []
            
            if not result.stdout.strip():
                return []
            
            # Parse mypy error output
            # Format: filename:line: error: message [error-code]
            errors = []
            for line in result.stdout.strip().split('\n'):
                if 'error:' not in line.lower():
                    continue
                
                # Parse line: "file.py:12: error: Missing return type [func-returns]"
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    filename = parts[0]
                    try:
                        line_num = int(parts[1])
                    except ValueError:
                        continue
                    
                    error_msg = parts[3].strip()
                    
                    # Extract error code (if present)
                    error_code = None
                    if '[' in error_msg and ']' in error_msg:
                        start = error_msg.rfind('[')
                        end = error_msg.rfind(']')
                        if start < end:
                            error_code = error_msg[start+1:end]
                            error_msg = error_msg[:start].strip()
                    
                    errors.append({
                        "filename": filename,
                        "line": line_num,
                        "message": error_msg,
                        "error_code": error_code,
                        "severity": "error"
                    })
            
            return errors
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return []
    
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
            if shutil.which("jscpd"):
                cmd = ["jscpd"]
            elif shutil.which("npx"):
                cmd = ["npx", "--yes", "jscpd"]
            else:
                return 5.0  # jscpd not available
            
            # Add jscpd arguments
            cmd.extend([
                target,
                "--format", "json",
                "--min-lines", str(self.min_duplication_lines),
                "--reporters", "json",
                "--output", "."  # Output to current directory
            ])
            
            # Run jscpd
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout (jscpd can be slow on large codebases)
                cwd=target_dir if Path(target_dir).exists() else None
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
                        with open(output_file, 'r', encoding='utf-8') as f:
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
                lines = result.stdout.split('\n') + result.stderr.split('\n')
                for line in lines:
                    if '%' in line and 'duplicate' in line.lower():
                        # Try to extract percentage
                        try:
                            pct_str = line.split('%')[0].split()[-1]
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
    
    def get_duplication_report(self, file_path: Path) -> Dict[str, Any]:
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
                "files": []
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
            if shutil.which("jscpd"):
                cmd = ["jscpd"]
            elif shutil.which("npx"):
                cmd = ["npx", "--yes", "jscpd"]
            else:
                return {"available": False, "percentage": 0.0, "duplicates": [], "files": []}
            
            cmd.extend([
                target,
                "--format", "json",
                "--min-lines", str(self.min_duplication_lines),
                "--reporters", "json"
            ])
            
            # Run jscpd
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=target_dir if Path(target_dir).exists() else None
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
                        with open(output_file, 'r', encoding='utf-8') as f:
                            report_data = json_lib.load(f)
                    else:
                        return {
                            "available": True,
                            "percentage": 0.0,
                            "duplicates": [],
                            "files": []
                        }
            except json_lib.JSONDecodeError:
                return {
                    "available": True,
                    "error": "Failed to parse jscpd output",
                    "percentage": 0.0,
                    "duplicates": [],
                    "files": []
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
                "files": report_data.get("statistics", {}).get("files", []) if "statistics" in report_data else [],
                "total_lines": report_data.get("statistics", {}).get("total", {}).get("lines", 0) if "statistics" in report_data else 0,
                "duplicated_lines": report_data.get("statistics", {}).get("duplicated", {}).get("lines", 0) if "statistics" in report_data else 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "available": True,
                "error": "jscpd timeout",
                "percentage": 0.0,
                "duplicates": [],
                "files": []
            }
        except FileNotFoundError:
            return {"available": False, "percentage": 0.0, "duplicates": [], "files": []}
        except Exception as e:
            return {
                "available": True,
                "error": str(e),
                "percentage": 0.0,
                "duplicates": [],
                "files": []
            }

