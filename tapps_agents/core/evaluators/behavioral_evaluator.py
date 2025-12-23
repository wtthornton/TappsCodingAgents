"""
Behavioral correctness evaluator.

Validates that code behaves as it claims (logic flow analysis, contract validation).
"""

import ast
import logging
from pathlib import Path
from typing import Any

from ..evaluation_base import BaseEvaluator
from ..evaluation_models import Issue, IssueCategory, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class BehavioralEvaluator(BaseEvaluator):
    """
    Evaluator for behavioral correctness validation.
    
    Uses AST-based logic flow analysis to detect potential behavioral issues.
    """

    def __init__(self):
        """Initialize behavioral evaluator."""
        pass

    def get_name(self) -> str:
        """Get evaluator name."""
        return "behavioral"

    def is_applicable(self, target: Path | str) -> bool:
        """Check if evaluator can evaluate target (Python files only currently)."""
        target_path = Path(target) if isinstance(target, str) else target
        return target_path.suffix == ".py"

    def evaluate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> IssueManifest:
        """
        Evaluate behavioral correctness.
        
        Args:
            target: File path to evaluate
            context: Optional context (code content, expected behavior, etc.)
            
        Returns:
            IssueManifest with behavioral issues found
        """
        target_path = Path(target) if isinstance(target, str) else target
        issues = IssueManifest()
        
        if not target_path.exists():
            return issues
        
        try:
            code = target_path.read_text(encoding="utf-8")
            tree = ast.parse(code)
            
            # Analyze function contracts and logic flow
            issues = self._analyze_logic_flow(tree, target_path, code)
            
        except SyntaxError as e:
            # Syntax errors are critical behavioral issues
            issue = Issue(
                id=f"behavioral_syntax_{target_path.name}",
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.CORRECTNESS,
                evidence=f"Syntax error in {target_path.name}: {e}",
                repro=f"Run: python -m py_compile {target_path}",
                suggested_fix="Fix syntax error: " + str(e),
                owner_step="implementation",
                file_path=str(target_path),
                line_number=getattr(e, "lineno", None),
            )
            issues.add_issue(issue)
        except Exception as e:
            logger.warning(f"Error in behavioral evaluation of {target_path}: {e}")
        
        return issues

    def _analyze_logic_flow(
        self, tree: ast.AST, file_path: Path, code: str
    ) -> IssueManifest:
        """Analyze logic flow for potential behavioral issues."""
        issues = IssueManifest()
        
        # Find functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_issues = self._analyze_function(node, file_path, code)
                issues.add_issues(func_issues.issues)
        
        return issues

    def _analyze_function(
        self, func_node: ast.FunctionDef, file_path: Path, code: str
    ) -> IssueManifest:
        """Analyze a single function for behavioral issues."""
        issues = IssueManifest()
        
        # Check for unreachable code
        unreachable = self._find_unreachable_code(func_node)
        for line_num in unreachable:
            issue = Issue(
                id=f"behavioral_unreachable_{func_node.name}_line_{line_num}",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.CORRECTNESS,
                evidence=f"Unreachable code in function {func_node.name} at line {line_num}",
                repro=f"Inspect function {func_node.name} at line {line_num}",
                suggested_fix="Remove unreachable code or fix control flow",
                owner_step="implementation",
                file_path=str(file_path),
                line_number=line_num,
            )
            issues.add_issue(issue)
        
        # Check for missing return statements
        if not self._has_return_statement(func_node):
            # Check docstring for return type hint
            docstring = ast.get_docstring(func_node)
            if docstring and ("return" in docstring.lower() or "->" in docstring):
                issue = Issue(
                    id=f"behavioral_missing_return_{func_node.name}",
                    severity=IssueSeverity.MEDIUM,
                    category=IssueCategory.CORRECTNESS,
                    evidence=f"Function {func_node.name} may be missing return statement (docstring indicates return type)",
                    repro=f"Check function {func_node.name} return behavior",
                    suggested_fix="Add return statement or update docstring",
                    owner_step="implementation",
                    file_path=str(file_path),
                    line_number=func_node.lineno,
                )
                issues.add_issue(issue)
        
        return issues

    def _find_unreachable_code(self, func_node: ast.FunctionDef) -> list[int]:
        """Find unreachable code (after return/raise statements)."""
        unreachable_lines: list[int] = []
        returns_found = False
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.Return, ast.Raise)):
                returns_found = True
                # Mark subsequent statements as potentially unreachable
                # (simplified - full analysis would require control flow graph)
                if hasattr(node, "lineno"):
                    unreachable_lines.append(node.lineno + 1)
        
        return unreachable_lines if returns_found else []

    def _has_return_statement(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has return statements."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                return True
        return False

