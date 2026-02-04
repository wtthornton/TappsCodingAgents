"""
Specification compliance evaluator.

Validates that code matches requirements/stories and acceptance criteria.
"""

import logging
from pathlib import Path
from typing import Any

from ..evaluation_base import BaseEvaluator
from ..evaluation_models import Issue, IssueCategory, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class SpecComplianceEvaluator(BaseEvaluator):
    """
    Evaluator for specification compliance checking.
    
    Validates requirements/stories traceability and acceptance criteria coverage.
    """

    def __init__(self, workflow_state: dict[str, Any] | None = None):
        """
        Initialize spec compliance evaluator.
        
        Args:
            workflow_state: Optional workflow state for requirements/stories access
        """
        self.workflow_state = workflow_state or {}

    def get_name(self) -> str:
        """Get evaluator name."""
        return "spec_compliance"

    def is_applicable(self, target: Path | str) -> bool:
        """Always applicable (can check against any target)."""
        return True

    def evaluate(
        self, target: Path | str, context: dict[str, Any] | None = None
    ) -> IssueManifest:
        """
        Evaluate specification compliance.
        
        Args:
            target: File path or identifier to evaluate
            context: Optional context (requirements, stories, expected behavior)
            
        Returns:
            IssueManifest with compliance issues found
        """
        issues = IssueManifest()
        
        # Get requirements and stories from context or workflow state
        requirements = (context or {}).get("requirements", [])
        stories = (context or {}).get("stories", [])
        
        # If workflow state available, extract from there
        if self.workflow_state:
            requirements = self.workflow_state.get("requirements", requirements)
            stories = self.workflow_state.get("stories", stories)
        
        # Validate traceability
        if requirements:
            issues = self._check_requirements_traceability(
                target, requirements, context
            )
        
        if stories:
            story_issues = self._check_stories_coverage(target, stories, context)
            issues = issues.merge(story_issues)
        
        return issues

    def _check_requirements_traceability(
        self,
        target: Path | str,
        requirements: list[dict[str, Any]],
        context: dict[str, Any] | None,
    ) -> IssueManifest:
        """Check if code traces back to requirements."""
        issues = IssueManifest()
        target_path = Path(target) if isinstance(target, str) else target
        
        # Read code to check for requirement references
        if target_path.exists() and target_path.is_file():
            try:
                code = target_path.read_text(encoding="utf-8")
                
                # Check if requirements are mentioned in code/comments
                for req in requirements:
                    req_id = req.get("id", "")
                    req_description = req.get("description", "")
                    
                    # Look for requirement ID in code
                    if req_id and req_id not in code:
                        # Check if requirement is in comments
                        in_comments = any(
                            req_id in line or req_description[:50] in line
                            for line in code.splitlines()
                            if line.strip().startswith("#")
                        )
                        
                        if not in_comments:
                            issue = Issue(
                                id=f"spec_missing_traceability_{req_id}",
                                severity=IssueSeverity.MEDIUM,
                                category=IssueCategory.CORRECTNESS,
                                evidence=f"Requirement {req_id} not referenced in code: {req_description[:100]}",
                                repro=f"Check if requirement {req_id} is implemented in {target_path}",
                                suggested_fix=f"Add requirement reference or implement requirement {req_id}",
                                owner_step="implementation",
                                file_path=str(target_path),
                                traceability={"requirement_id": req_id},
                            )
                            issues.add_issue(issue)
            
            except Exception as e:
                logger.warning(f"Error checking requirements traceability: {e}")
        
        return issues

    def _check_stories_coverage(
        self,
        target: Path | str,
        stories: list[dict[str, Any]],
        context: dict[str, Any] | None,
    ) -> IssueManifest:
        """Check if acceptance criteria are met."""
        issues = IssueManifest()
        target_path = Path(target) if isinstance(target, str) else target
        
        # Check acceptance criteria coverage
        for story in stories:
            story_id = story.get("id", "")
            acceptance_criteria = story.get("acceptance_criteria", [])
            
            if not acceptance_criteria:
                continue
            
            # Simple check: verify acceptance criteria keywords in code
            if target_path.exists() and target_path.is_file():
                try:
                    code = target_path.read_text(encoding="utf-8").lower()
                    
                    for criterion in acceptance_criteria:
                        criterion_text = criterion.get("description", "").lower()
                        # Check if key terms from criterion appear in code
                        key_terms = [
                            word
                            for word in criterion_text.split()
                            if len(word) > 4
                        ]
                        
                        if key_terms:
                            found_terms = [
                                term for term in key_terms if term in code
                            ]
                            coverage = len(found_terms) / len(key_terms) if key_terms else 0
                            
                            if coverage < 0.5:  # Less than 50% coverage
                                issue = Issue(
                                    id=f"spec_low_coverage_{story_id}_{criterion.get('id', '')}",
                                    severity=IssueSeverity.MEDIUM,
                                    category=IssueCategory.CORRECTNESS,
                                    evidence=f"Low coverage for acceptance criteria: {criterion.get('description', '')[:100]}",
                                    repro=f"Verify acceptance criteria for story {story_id}",
                                    suggested_fix="Implement acceptance criteria or add test coverage",
                                    owner_step="testing",
                                    file_path=str(target_path),
                                    traceability={"story_id": story_id, "criterion_id": criterion.get("id")},
                                )
                                issues.add_issue(issue)
                
                except Exception as e:
                    logger.warning(f"Error checking stories coverage: {e}")
        
        return issues

