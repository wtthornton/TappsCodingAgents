"""Enhanced knowledge need detector for proactive detection."""

import logging
from typing import Any

from .expert_engine import KnowledgeNeed

logger = logging.getLogger(__name__)


class KnowledgeNeedDetector:
    """Detects knowledge needs from workflow, repo, and Cursor signals."""

    def detect_from_workflow(
        self, step_context: dict[str, Any], issues_manifest: Any | None = None
    ) -> list[KnowledgeNeed]:
        """Detect knowledge needs from workflow signals."""
        needs = []
        
        # Detect from current step
        agent = step_context.get("agent")
        step_context.get("action")
        
        if agent == "reviewer":
            needs.append(KnowledgeNeed(
                domain="code_quality",
                query="What are the best practices for code review in this context?",
                context=step_context,
                priority="high",
            ))
        
        # Detect from issues manifest
        if issues_manifest:
            try:
                # Try to get critical issues if it's an IssueManifest object
                if hasattr(issues_manifest, 'get_critical_issues'):
                    critical_issues = issues_manifest.get_critical_issues()
                elif hasattr(issues_manifest, 'issues'):
                    # Fallback: check issues directly
                    from ...core.evaluation_models import IssueSeverity
                    critical_issues = [
                        issue for issue in issues_manifest.issues
                        if issue.severity == IssueSeverity.CRITICAL
                    ]
                else:
                    critical_issues = []
                
                if critical_issues:
                    needs.append(KnowledgeNeed(
                        domain="security",
                        query="How to fix critical security issues?",
                        context={"issues_count": len(critical_issues)},
                        priority="critical",
                    ))
            except Exception as e:
                logger.warning(f"Error detecting issues from manifest: {e}")
        
        return needs

    def detect_from_repo(self, repo_signals: dict[str, Any]) -> list[KnowledgeNeed]:
        """Detect knowledge needs from repository signals."""
        needs = []
        
        # Detect from dependencies
        repo_signals.get("dependencies", [])
        frameworks = repo_signals.get("frameworks", [])
        
        for framework in frameworks:
            needs.append(KnowledgeNeed(
                domain=framework.lower(),
                query=f"Best practices for {framework}",
                context={"framework": framework},
                priority="normal",
            ))
        
        return needs

    def detect_from_cursor(self, cursor_signals: dict[str, Any]) -> list[KnowledgeNeed]:
        """Detect knowledge needs from Cursor interaction signals."""
        needs = []
        
        # Detect from commands
        command = cursor_signals.get("command")
        if command:
            needs.append(KnowledgeNeed(
                domain="general",
                query=f"How to best execute {command}?",
                context=cursor_signals,
                priority="normal",
            ))
        
        return needs

