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


class CodeScorer:
    """Calculate code quality scores"""

    def __init__(self, weights: Optional[ScoringWeightsConfig] = None):
        self.has_radon = HAS_RADON
        self.has_bandit = HAS_BANDIT
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

