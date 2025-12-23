"""
Architectural pattern adherence evaluator.

Validates layer violations, dependency rules, and pattern compliance.
"""

import logging
from pathlib import Path
from typing import Any

from ..evaluation_base import BaseEvaluator
from ..evaluation_models import Issue, IssueCategory, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class ArchitecturalEvaluator(BaseEvaluator):
    """
    Evaluator for architectural pattern adherence.
    
    Checks layer violations, dependency rules, and pattern catalog matching.
    """

    def __init__(self, pattern_catalog: dict[str, Any] | None = None):
        """
        Initialize architectural evaluator.
        
        Args:
            pattern_catalog: Optional pattern catalog for validation
        """
        self.pattern_catalog = pattern_catalog or {}

    def get_name(self) -> str:
        """Get evaluator name."""
        return "architectural"

    def is_applicable(self, target: Path | str) -> bool:
        """Always applicable."""
        return True

    def evaluate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> IssueManifest:
        """
        Evaluate architectural compliance.
        
        Args:
            target: File path to evaluate
            context: Optional context (layers, dependencies, patterns)
            
        Returns:
            IssueManifest with architectural issues found
        """
        target_path = Path(target) if isinstance(target, str) else target
        issues = IssueManifest()
        
        if not target_path.exists() or not target_path.is_file():
            return issues
        
        # Get architectural rules from context
        layers = (context or {}).get("layers", {})
        dependencies = (context or {}).get("dependencies", {})
        patterns = (context or {}).get("patterns", self.pattern_catalog)
        
        # Check layer violations
        if layers:
            layer_issues = self._check_layer_violations(target_path, layers)
            issues = issues.merge(layer_issues)
        
        # Check dependency rules
        if dependencies:
            dep_issues = self._check_dependency_rules(target_path, dependencies)
            issues = issues.merge(dep_issues)
        
        # Check pattern adherence
        if patterns:
            pattern_issues = self._check_pattern_adherence(target_path, patterns)
            issues = issues.merge(pattern_issues)
        
        return issues

    def _check_layer_violations(
        self, file_path: Path, layers: dict[str, Any]
    ) -> IssueManifest:
        """Check for layer violations (e.g., model importing from view)."""
        issues = IssueManifest()
        
        # Simple layer detection based on directory structure
        # e.g., models/ should not import from views/
        layer_rules = layers.get("rules", {})
        file_str = str(file_path)
        
        for layer_name, layer_config in layer_rules.items():
            layer_path = layer_config.get("path", "")
            forbidden_imports = layer_config.get("forbidden_imports", [])
            
            if layer_path in file_str:
                # This file is in a layer - check imports
                try:
                    code = file_path.read_text(encoding="utf-8")
                    
                    for forbidden in forbidden_imports:
                        if forbidden in code:
                            issue = Issue(
                                id=f"arch_layer_violation_{layer_name}_{forbidden}",
                                severity=IssueSeverity.HIGH,
                                category=IssueCategory.ARCHITECTURE,
                                evidence=f"Layer violation: {layer_name} imports from forbidden layer {forbidden}",
                                repro=f"Check imports in {file_path}",
                                suggested_fix=f"Refactor to respect layer boundaries: remove import of {forbidden}",
                                owner_step="implementation",
                                file_path=str(file_path),
                            )
                            issues.add_issue(issue)
                
                except Exception as e:
                    logger.warning(f"Error checking layer violations: {e}")
        
        return issues

    def _check_dependency_rules(
        self, file_path: Path, dependency_rules: dict[str, Any]
    ) -> IssueManifest:
        """Check dependency rules (e.g., no circular dependencies)."""
        issues = IssueManifest()
        
        # Check for dependency rule violations
        # This is a simplified check - full analysis would require dependency graph
        rules = dependency_rules.get("rules", [])
        
        try:
            code = file_path.read_text(encoding="utf-8")
            
            for rule in rules:
                rule_type = rule.get("type", "")
                forbidden = rule.get("forbidden", [])
                
                if rule_type == "no_imports_from":
                    for forbidden_module in forbidden:
                        if f"from {forbidden_module}" in code or f"import {forbidden_module}" in code:
                            issue = Issue(
                                id=f"arch_dep_violation_{forbidden_module}",
                                severity=IssueSeverity.MEDIUM,
                                category=IssueCategory.ARCHITECTURE,
                                evidence=f"Dependency rule violation: imports from {forbidden_module}",
                                repro=f"Check imports in {file_path}",
                                suggested_fix=f"Remove dependency on {forbidden_module} or update dependency rules",
                                owner_step="implementation",
                                file_path=str(file_path),
                            )
                            issues.add_issue(issue)
        
        except Exception as e:
            logger.warning(f"Error checking dependency rules: {e}")
        
        return issues

    def _check_pattern_adherence(
        self, file_path: Path, patterns: dict[str, Any]
    ) -> IssueManifest:
        """Check if code follows established patterns."""
        issues = IssueManifest()
        
        # Pattern adherence checking
        # This would ideally match against a pattern catalog
        # Simplified implementation checks for common anti-patterns
        
        try:
            code = file_path.read_text(encoding="utf-8")
            
            # Check for common anti-patterns
            anti_patterns = {
                "god_object": {
                    "indicator": lambda c: c.count("class ") > 10,  # Too many classes
                    "severity": IssueSeverity.MEDIUM,
                    "fix": "Split into smaller, focused classes",
                },
                "long_method": {
                    "indicator": lambda c: max(
                        len(line) for line in c.splitlines() if line.strip()
                    ) > 200,  # Very long lines
                    "severity": IssueSeverity.LOW,
                    "fix": "Break long methods into smaller functions",
                },
            }
            
            for pattern_name, pattern_info in anti_patterns.items():
                if pattern_info["indicator"](code):
                    issue = Issue(
                        id=f"arch_anti_pattern_{pattern_name}",
                        severity=pattern_info["severity"],
                        category=IssueCategory.ARCHITECTURE,
                        evidence=f"Potential anti-pattern detected: {pattern_name}",
                        repro=f"Review {file_path} for {pattern_name}",
                        suggested_fix=pattern_info["fix"],
                        owner_step="implementation",
                        file_path=str(file_path),
                    )
                    issues.add_issue(issue)
        
        except Exception as e:
            logger.warning(f"Error checking pattern adherence: {e}")
        
        return issues

