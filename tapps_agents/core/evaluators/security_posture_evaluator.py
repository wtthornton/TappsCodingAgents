"""
Security posture evaluator.

Extends beyond vulnerability scanning to security pattern compliance and best practices.
"""

import logging
import re
from pathlib import Path
from typing import Any

from ..evaluation_base import BaseEvaluator
from ..evaluation_models import Issue, IssueCategory, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class SecurityPostureEvaluator(BaseEvaluator):
    """
    Evaluator for comprehensive security posture assessment.
    
    Checks security patterns, best practices, and potential vulnerabilities.
    """

    def __init__(self):
        """Initialize security posture evaluator."""
        # Common insecure patterns
        self.insecure_patterns = [
            (r'eval\s*\(', "Use of eval() can execute arbitrary code"),
            (r'exec\s*\(', "Use of exec() can execute arbitrary code"),
            (r'__import__\s*\(', "Dynamic imports can be security risks"),
            (r'pickle\.loads\s*\(', "Unpickling untrusted data can execute code"),
            (r'subprocess\.call\s*\(', "Command injection risk"),
            (r'os\.system\s*\(', "Command injection risk"),
            (r'password\s*=\s*["\'].*["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'].*["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'].*["\']', "Hardcoded secret"),
        ]

    def get_name(self) -> str:
        """Get evaluator name."""
        return "security_posture"

    def is_applicable(self, target: Path | str) -> bool:
        """Applicable to code files."""
        target_path = Path(target) if isinstance(target, str) else target
        return target_path.suffix in [".py", ".js", ".ts", ".tsx", ".jsx"]

    def evaluate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> IssueManifest:
        """
        Evaluate security posture.
        
        Args:
            target: File path to evaluate
            context: Optional context
            
        Returns:
            IssueManifest with security issues found
        """
        target_path = Path(target) if isinstance(target, str) else target
        issues = IssueManifest()
        
        if not target_path.exists() or not target_path.is_file():
            return issues
        
        try:
            code = target_path.read_text(encoding="utf-8")
            
            # Check insecure patterns
            for pattern, description in self.insecure_patterns:
                matches = list(re.finditer(pattern, code, re.IGNORECASE))
                for match in matches:
                    line_num = code[:match.start()].count("\n") + 1
                    
                    # Determine severity based on pattern
                    severity = IssueSeverity.CRITICAL if "eval" in pattern or "exec" in pattern or "pickle" in pattern else IssueSeverity.HIGH
                    
                    issue = Issue(
                        id=f"security_pattern_{pattern[:10]}_{line_num}",
                        severity=severity,
                        category=IssueCategory.SECURITY,
                        evidence=f"Security risk detected: {description}",
                        repro=f"Inspect line {line_num} in {target_path}",
                        suggested_fix=f"Remove or secure: {match.group(0)} - {description}",
                        owner_step="implementation",
                        file_path=str(target_path),
                        line_number=line_num,
                    )
                    issues.add_issue(issue)
            
            # Check for missing input validation
            validation_issues = self._check_input_validation(code, target_path)
            issues = issues.merge(validation_issues)
            
        except Exception as e:
            logger.warning(f"Error in security posture evaluation: {e}")
        
        return issues

    def _check_input_validation(
        self, code: str, file_path: Path
    ) -> IssueManifest:
        """Check for missing input validation."""
        issues = IssueManifest()
        
        # Simple heuristic: look for functions that accept user input but don't validate
        # This is a simplified check - full analysis would require AST parsing
        if "def " in code and "input(" in code:
            # Check if input() calls have validation nearby
            input_pattern = r'input\s*\('
            validation_patterns = [
                r'if\s+.*:\s*raise',
                r'assert\s+',
                r'validate',
                r'\.isnumeric\(\)',
                r'\.isdigit\(\)',
            ]
            
            input_matches = list(re.finditer(input_pattern, code))
            for match in input_matches:
                # Check next 20 lines for validation
                start_pos = match.start()
                next_lines = code[start_pos:start_pos + 1000]
                
                has_validation = any(
                    re.search(pattern, next_lines, re.IGNORECASE)
                    for pattern in validation_patterns
                )
                
                if not has_validation:
                    line_num = code[:start_pos].count("\n") + 1
                    issue = Issue(
                        id=f"security_missing_validation_{line_num}",
                        severity=IssueSeverity.MEDIUM,
                        category=IssueCategory.SECURITY,
                        evidence=f"Potential missing input validation at line {line_num}",
                        repro=f"Check input validation in {file_path} around line {line_num}",
                        suggested_fix="Add input validation and sanitization",
                        owner_step="implementation",
                        file_path=str(file_path),
                        line_number=line_num,
                    )
                    issues.add_issue(issue)
        
        return issues

