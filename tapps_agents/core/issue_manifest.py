"""
Issue Manifest system for structured issue tracking.

Provides issue aggregation, deduplication, and traceability capabilities.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

from .evaluation_models import Issue, IssueCategory, IssueManifest, IssueSeverity

logger = logging.getLogger(__name__)


class IssueManifestManager:
    """
    Manager for IssueManifest with advanced capabilities.
    
    Provides aggregation, deduplication, prioritization, and traceability.
    """

    def __init__(self):
        """Initialize issue manifest manager."""
        self.manifest = IssueManifest()

    def add_issue(self, issue: Issue) -> None:
        """Add an issue to the manifest."""
        self.manifest.add_issue(issue)

    def add_issues(self, issues: list[Issue]) -> None:
        """Add multiple issues to the manifest."""
        self.manifest.add_issues(issues)

    def deduplicate(self) -> IssueManifest:
        """
        Remove duplicate issues based on multiple criteria.
        
        Uses ID, file+line, and content hash for deduplication.
        """
        seen: dict[str, Issue] = {}
        
        for issue in self.manifest.issues:
            # Primary: Use ID
            if issue.id in seen:
                continue
            
            # Secondary: Use file+line+category combination
            file_line_key = f"{issue.file_path}:{issue.line_number}:{issue.category.value}"
            if file_line_key in seen:
                # Merge evidence if similar
                existing = seen[file_line_key]
                if existing.severity == issue.severity:
                    # Merge evidence
                    existing.evidence += f"\n\nAdditional: {issue.evidence}"
                    continue
            
            # Tertiary: Use content hash (evidence + suggested_fix)
            content_hash = self._hash_issue_content(issue)
            if content_hash in seen:
                continue
            
            seen[issue.id] = issue
        
        return IssueManifest(issues=list(seen.values()))

    def _hash_issue_content(self, issue: Issue) -> str:
        """Generate hash for issue content (for deduplication)."""
        content = f"{issue.evidence}:{issue.suggested_fix}:{issue.category.value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def prioritize(self) -> IssueManifest:
        """Sort issues by priority (severity, then category)."""
        severity_order = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.HIGH: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 3,
        }
        
        sorted_issues = sorted(
            self.manifest.issues,
            key=lambda i: (
                severity_order.get(i.severity, 999),
                i.category.value,
            ),
        )
        
        return IssueManifest(issues=sorted_issues)

    def filter_by_severity(self, min_severity: IssueSeverity) -> IssueManifest:
        """Filter issues by minimum severity."""
        severity_levels = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.HIGH: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 3,
        }
        min_level = severity_levels.get(min_severity, 999)
        
        filtered = [
            issue
            for issue in self.manifest.issues
            if severity_levels.get(issue.severity, 999) <= min_level
        ]
        
        return IssueManifest(issues=filtered)

    def link_traceability(
        self, requirements: dict[str, Any], stories: dict[str, Any]
    ) -> None:
        """
        Link issues to requirements and user stories for traceability.
        
        Args:
            requirements: Requirements dictionary with IDs
            stories: User stories dictionary with IDs
        """
        for issue in self.manifest.issues:
            # Extract potential requirement/story IDs from traceability or evidence
            traceability = issue.traceability
            
            # Link to requirements if mentioned in evidence or traceability
            req_ids = self._extract_ids(issue.evidence + str(traceability), "REQ")
            if req_ids:
                traceability.setdefault("requirements", []).extend(req_ids)
            
            # Link to stories if mentioned
            story_ids = self._extract_ids(issue.evidence + str(traceability), "STORY")
            if story_ids:
                traceability.setdefault("stories", []).extend(story_ids)
            
            issue.traceability = traceability

    def _extract_ids(self, text: str, prefix: str) -> list[str]:
        """Extract requirement or story IDs from text."""
        # Simple pattern matching for IDs like REQ-123 or STORY-456
        import re
        
        pattern = rf"{prefix}[-_]?(\d+)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [f"{prefix}-{match}" for match in matches]

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics of issues."""
        counts = self.manifest.count_by_severity()
        category_counts: dict[IssueCategory, int] = {}
        
        for issue in self.manifest.issues:
            category_counts[issue.category] = (
                category_counts.get(issue.category, 0) + 1
            )
        
        return {
            "total": len(self.manifest.issues),
            "by_severity": {k.value: v for k, v in counts.items()},
            "by_category": {k.value: v for k, v in category_counts.items()},
            "critical_count": counts.get(IssueSeverity.CRITICAL, 0),
            "high_count": counts.get(IssueSeverity.HIGH, 0),
            "resolved_count": sum(1 for i in self.manifest.issues if i.resolved),
        }

    def export_markdown(self, file_path: Path) -> None:
        """Export issues to Markdown format."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Issue Manifest\n\n")
            
            summary = self.get_summary()
            f.write("## Summary\n\n")
            f.write(f"- **Total Issues**: {summary['total']}\n")
            f.write(f"- **Critical**: {summary['critical_count']}\n")
            f.write(f"- **High**: {summary['high_count']}\n")
            f.write(f"- **Resolved**: {summary['resolved_count']}\n\n")
            
            # Group by severity
            for severity in IssueSeverity:
                issues = self.manifest.get_by_severity(severity)
                if not issues:
                    continue
                
                f.write(f"## {severity.value.upper()} Issues\n\n")
                for issue in issues:
                    f.write(f"### {issue.id}\n\n")
                    f.write(f"**Category**: {issue.category.value}\n\n")
                    f.write(f"**Evidence**:\n{issue.evidence}\n\n")
                    f.write(f"**Reproduction**:\n{issue.repro}\n\n")
                    f.write(f"**Suggested Fix**:\n{issue.suggested_fix}\n\n")
                    if issue.file_path:
                        f.write(f"**Location**: {issue.file_path}")
                        if issue.line_number:
                            f.write(f":{issue.line_number}")
                        f.write("\n\n")
                    if issue.traceability:
                        f.write(f"**Traceability**: {issue.traceability}\n\n")
                    f.write("---\n\n")

    def export_html(self, file_path: Path) -> None:
        """Export issues to HTML format."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Issue Manifest</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .critical { background-color: #fee; border-left: 4px solid #c00; }
        .high { background-color: #ffe; border-left: 4px solid #fa0; }
        .medium { background-color: #ffe; border-left: 4px solid #ff0; }
        .low { background-color: #efe; border-left: 4px solid #0a0; }
        .issue { margin: 10px 0; padding: 10px; }
        .resolved { opacity: 0.6; }
    </style>
</head>
<body>
    <h1>Issue Manifest</h1>
"""
        
        summary = self.get_summary()
        html += "<h2>Summary</h2><ul>"
        html += f"<li><strong>Total Issues</strong>: {summary['total']}</li>"
        html += f"<li><strong>Critical</strong>: {summary['critical_count']}</li>"
        html += f"<li><strong>High</strong>: {summary['high_count']}</li>"
        html += f"<li><strong>Resolved</strong>: {summary['resolved_count']}</li></ul>"
        
        for severity in IssueSeverity:
            issues = self.manifest.get_by_severity(severity)
            if not issues:
                continue
            
            html += f"<h2>{severity.value.upper()} Issues</h2>"
            for issue in issues:
                resolved_class = "resolved" if issue.resolved else ""
                html += f'<div class="issue {severity.value} {resolved_class}">'
                html += f"<h3>{issue.id}</h3>"
                html += f"<p><strong>Category</strong>: {issue.category.value}</p>"
                html += f"<p><strong>Evidence</strong>:<br>{issue.evidence.replace(chr(10), '<br>')}</p>"
                html += f"<p><strong>Suggested Fix</strong>:<br>{issue.suggested_fix.replace(chr(10), '<br>')}</p>"
                if issue.file_path:
                    location = issue.file_path
                    if issue.line_number:
                        location += f":{issue.line_number}"
                    html += f"<p><strong>Location</strong>: {location}</p>"
                html += "</div>"
        
        html += "</body></html>"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

