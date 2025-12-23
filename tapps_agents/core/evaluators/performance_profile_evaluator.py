"""
Performance profile evaluator.

Identifies performance issues, bottlenecks, and resource usage patterns.
"""

import logging
import re
from pathlib import Path
from typing import Any

from ..evaluation_base import BaseEvaluator
from ..evaluation_models import Issue, IssueCategory, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class PerformanceProfileEvaluator(BaseEvaluator):
    """
    Evaluator for performance profiling.
    
    Identifies performance anti-patterns and potential bottlenecks.
    """

    def __init__(self):
        """Initialize performance profile evaluator."""
        # Performance anti-patterns
        self.anti_patterns = [
            (r'for\s+\w+\s+in\s+\w+\.append\s*\(', "Inefficient list building - use list comprehension"),
            (r'\.sort\s*\(\s*\)\s*.*\.sort\s*\(', "Multiple sorts - inefficient"),
            (r'SELECT\s+\*\s+FROM', "SELECT * can be inefficient - specify columns"),
            (r'nested\s+for\s+.*\s+for\s+', "Nested loops can be O(n²) or worse"),
        ]

    def get_name(self) -> str:
        """Get evaluator name."""
        return "performance_profile"

    def is_applicable(self, target: Path | str) -> bool:
        """Applicable to code files."""
        target_path = Path(target) if isinstance(target, str) else target
        return target_path.suffix in [".py", ".js", ".ts", ".tsx", ".jsx", ".sql"]

    def evaluate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> IssueManifest:
        """
        Evaluate performance profile.
        
        Args:
            target: File path to evaluate
            context: Optional context
            
        Returns:
            IssueManifest with performance issues found
        """
        target_path = Path(target) if isinstance(target, str) else target
        issues = IssueManifest()
        
        if not target_path.exists() or not target_path.is_file():
            return issues
        
        try:
            code = target_path.read_text(encoding="utf-8")
            
            # Check for performance anti-patterns
            for pattern, description in self.anti_patterns:
                matches = list(re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE))
                for match in matches:
                    line_num = code[:match.start()].count("\n") + 1
                    
                    issue = Issue(
                        id=f"perf_anti_pattern_{line_num}",
                        severity=IssueSeverity.LOW,
                        category=IssueCategory.PERFORMANCE,
                        evidence=f"Performance anti-pattern: {description}",
                        repro=f"Inspect line {line_num} in {target_path}",
                        suggested_fix=description,
                        owner_step="implementation",
                        file_path=str(target_path),
                        line_number=line_num,
                    )
                    issues.add_issue(issue)
            
            # Check for nested loops (O(n²) complexity)
            nested_loop_issues = self._check_nested_loops(code, target_path)
            issues = issues.merge(nested_loop_issues)
            
            # Check for potential database N+1 queries
            db_issues = self._check_database_queries(code, target_path)
            issues = issues.merge(db_issues)
            
        except Exception as e:
            logger.warning(f"Error in performance profile evaluation: {e}")
        
        return issues

    def _check_nested_loops(
        self, code: str, file_path: Path
    ) -> IssueManifest:
        """Check for deeply nested loops."""
        issues = IssueManifest()
        
        # Count nested for/while loops
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            # Simple heuristic: count consecutive for/while statements
            if i < len(lines) - 1:
                current_line = line.strip()
                next_line = lines[i].strip() if i < len(lines) else ""
                
                if re.match(r'for\s+', current_line) or re.match(r'while\s+', current_line):
                    # Check if next line also has a loop (simplified)
                    if re.match(r'for\s+', next_line) or re.match(r'while\s+', next_line):
                        issue = Issue(
                            id=f"perf_nested_loop_{i}",
                            severity=IssueSeverity.MEDIUM,
                            category=IssueCategory.PERFORMANCE,
                            evidence=f"Nested loops detected at line {i} - potential O(n²) complexity",
                            repro=f"Review nested loops in {file_path} around line {i}",
                            suggested_fix="Consider optimizing nested loops or using vectorized operations",
                            owner_step="implementation",
                            file_path=str(file_path),
                            line_number=i,
                        )
                        issues.add_issue(issue)
        
        return issues

    def _check_database_queries(
        self, code: str, file_path: Path
    ) -> IssueManifest:
        """Check for potential N+1 query patterns."""
        issues = IssueManifest()
        
        # Check for loops containing queries (N+1 pattern)
        query_patterns = [r'\.get\s*\(', r'\.filter\s*\(', r'SELECT\s+.*\s+FROM']
        loop_pattern = r'for\s+\w+\s+in'
        
        if re.search(loop_pattern, code):
            # Check if queries appear inside loops
            # This is simplified - full analysis would require parsing control flow
            for query_pattern in query_patterns:
                if re.search(query_pattern, code, re.IGNORECASE):
                    # Potential N+1 pattern
                    issue = Issue(
                        id=f"perf_n_plus_one_query",
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.PERFORMANCE,
                        evidence="Potential N+1 query pattern: database queries inside loops",
                        repro=f"Review {file_path} for queries inside loops",
                        suggested_fix="Use bulk queries or eager loading to avoid N+1 queries",
                        owner_step="implementation",
                        file_path=str(file_path),
                    )
                    issues.add_issue(issue)
                    break  # Only report once
        
        return issues

