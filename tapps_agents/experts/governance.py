"""
Governance & Safety Layer

Prevents sensitive data from entering the KB and ensures security.
Implements filters, prompt-injection handling, and retention policies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .knowledge_ingestion import KnowledgeEntry


@dataclass
class GovernancePolicy:
    """Governance policy configuration."""

    # Do-not-index filters
    filter_secrets: bool = True
    filter_tokens: bool = True
    filter_credentials: bool = True
    filter_pii: bool = True

    # Prompt-injection handling
    treat_as_untrusted: bool = True
    label_sources: bool = True

    # Retention & scope
    project_local_only: bool = True
    avoid_committing_runtime_state: bool = True

    # Human approval
    require_approval: bool = False
    approval_queue_path: Path | None = None


@dataclass
class FilterResult:
    """Result of content filtering."""

    allowed: bool
    reason: str | None = None
    filtered_content: str | None = None
    detected_issues: list[str] = field(default_factory=list)


class GovernanceLayer:
    """
    Governance and safety layer for knowledge ingestion.

    Prevents sensitive data, handles prompt injection, and enforces
    retention and scope policies.
    """

    # Secret patterns
    SECRET_PATTERNS = [
        r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"\n]{8,})",
        r"(?i)(token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{32,})",
        r"(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{32,})",
        r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----",
        r"ssh-rsa\s+[A-Za-z0-9+/=]{100,}",
    ]

    # PII patterns
    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b\d{3}\.\d{2}\.\d{4}\b",  # SSN variant
        r"\b\d{16}\b",  # Credit card
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email (context-dependent)
    ]

    # Credential patterns
    CREDENTIAL_PATTERNS = [
        r"(?i)(username|user|login)\s*[:=]\s*['\"]?([^\s'\"\n]+)",
        r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"\n]+)",
        r"(?i)(connection[_-]?string|conn[_-]?str)\s*[:=]\s*['\"]?([^\s'\"\n]+)",
    ]

    def __init__(self, policy: GovernancePolicy | None = None):
        """
        Initialize Governance Layer.

        Args:
            policy: Governance policy configuration
        """
        self.policy = policy or GovernancePolicy()

    def filter_content(self, content: str, source: str | None = None) -> FilterResult:
        """
        Filter content for sensitive data.

        Args:
            content: Content to filter
            source: Optional source identifier

        Returns:
            FilterResult indicating if content is allowed
        """
        detected_issues = []
        filtered_content = content

        # Check for secrets
        if self.policy.filter_secrets:
            for pattern in self.SECRET_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    detected_issues.append(f"Secret pattern detected: {pattern[:50]}")
                    # Redact secrets
                    filtered_content = re.sub(pattern, r"\1[REDACTED]", filtered_content)

        # Check for tokens
        if self.policy.filter_tokens:
            token_patterns = [
                r"(?i)(token|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{32,})",
            ]
            for pattern in token_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    detected_issues.append("Token detected")
                    filtered_content = re.sub(pattern, r"\1[REDACTED]", filtered_content)

        # Check for credentials
        if self.policy.filter_credentials:
            for pattern in self.CREDENTIAL_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    detected_issues.append("Credentials detected")
                    filtered_content = re.sub(pattern, r"\1[REDACTED]", filtered_content)

        # Check for PII (context-dependent, be careful with false positives)
        if self.policy.filter_pii:
            for pattern in self.PII_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    # Only flag if multiple matches (reduce false positives)
                    if len(matches) > 1:
                        detected_issues.append("Potential PII detected")
                        filtered_content = re.sub(pattern, "[REDACTED]", filtered_content)

        # Determine if content is allowed
        allowed = len(detected_issues) == 0 or not any(
            [
                self.policy.filter_secrets,
                self.policy.filter_tokens,
                self.policy.filter_credentials,
                self.policy.filter_pii,
            ]
        )

        reason = None
        if not allowed:
            reason = f"Content filtered due to: {', '.join(detected_issues)}"

        return FilterResult(
            allowed=allowed,
            reason=reason,
            filtered_content=filtered_content if filtered_content != content else None,
            detected_issues=detected_issues,
        )

    def validate_knowledge_entry(
        self, entry: KnowledgeEntry
    ) -> tuple[bool, str | None]:
        """
        Validate a knowledge entry against governance policies.

        Args:
            entry: Knowledge entry to validate

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        # Filter content
        filter_result = self.filter_content(entry.content, entry.source)

        if not filter_result.allowed:
            return False, filter_result.reason

        # Check retention & scope policies
        if self.policy.project_local_only:
            # Ensure entry is stored in project-local KB
            if not entry.source.startswith(str(Path.cwd())):
                return False, "Entry must be project-local"

        # Check for prompt injection
        if self.policy.treat_as_untrusted:
            # Label sources if enabled
            if self.policy.label_sources:
                entry.metadata["source_label"] = "untrusted"
                entry.metadata["source_verified"] = False

        return True, None

    def requires_approval(self, entry: KnowledgeEntry) -> bool:
        """
        Check if entry requires human approval.

        Args:
            entry: Knowledge entry to check

        Returns:
            True if approval is required
        """
        if not self.policy.require_approval:
            return False

        # Check if entry is new expert or significant KB addition
        if entry.source_type == "context7" and "expert" in entry.domain:
            return True

        # Check if entry has high-risk content
        filter_result = self.filter_content(entry.content, entry.source)
        if filter_result.detected_issues:
            return True

        return False

    def queue_for_approval(self, entry: KnowledgeEntry) -> Path:
        """
        Queue entry for human approval.

        Args:
            entry: Knowledge entry to queue

        Returns:
            Path to approval queue file
        """
        if not self.policy.approval_queue_path:
            raise ValueError("Approval queue path not configured")

        approval_dir = self.policy.approval_queue_path
        approval_dir.mkdir(parents=True, exist_ok=True)

        # Create approval request file
        import json
        from datetime import datetime

        approval_data = {
            "entry": {
                "title": entry.title,
                "domain": entry.domain,
                "source": entry.source,
                "source_type": entry.source_type,
                "metadata": entry.metadata,
            },
            "content_preview": entry.content[:500],  # First 500 chars
            "queued_at": datetime.now().isoformat(),
            "status": "pending",
        }

        # Generate unique filename
        safe_title = re.sub(r"[^\w\s-]", "", entry.title).strip().replace(" ", "_")
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        approval_file = approval_dir / filename

        approval_file.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")

        return approval_file

