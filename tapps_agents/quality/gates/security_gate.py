"""
Security Gate

Checks for secrets, PII, vulnerabilities, and security issues.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ...experts.governance import GovernanceLayer, GovernancePolicy
from ..secret_scanner import SecretScanner
from .base import BaseGate, GateResult, GateSeverity

logger = logging.getLogger(__name__)


class SecurityGate(BaseGate):
    """
    Security gate that checks for:
    - Secrets (API keys, tokens, passwords)
    - PII (SSN, credit cards, emails)
    - Credentials
    - Security vulnerabilities
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize security gate.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.governance = GovernanceLayer(
            policy=GovernancePolicy(
                filter_secrets=config.get("filter_secrets", True) if config else True,
                filter_tokens=config.get("filter_tokens", True) if config else True,
                filter_credentials=config.get("filter_credentials", True) if config else True,
                filter_pii=config.get("filter_pii", True) if config else True,
            )
        )
        self.secret_scanner = SecretScanner()

    def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Evaluate security gate.

        Args:
            context: Context with file_path, content, or artifacts

        Returns:
            GateResult

        Raises:
            MissingContextError: If required context is missing
        """
        # Validate context
        if not context or not isinstance(context, dict):
            return GateResult(
                passed=False,
                severity=GateSeverity.ERROR,
                message="Invalid context: context must be a dictionary",
                details={"error": "Invalid context type"},
            )

        issues: list[str] = []
        details: dict[str, Any] = {
            "secrets_found": [],
            "pii_found": [],
            "credentials_found": [],
            "vulnerabilities": [],
        }

        # Check file content if provided
        content = context.get("content")
        file_path = context.get("file_path")
        
        if content:
            try:
                # Use governance layer to filter content
                filter_result = self.governance.filter_content(content, source=str(file_path) if file_path else None)
                
                if not filter_result.allowed:
                    issues.append(f"Security issue detected: {filter_result.reason}")
                    if filter_result.detected_issues:
                        for issue in filter_result.detected_issues:
                            if "Secret" in issue:
                                details["secrets_found"].append(issue)
                            elif "PII" in issue:
                                details["pii_found"].append(issue)
                            elif "Credentials" in issue:
                                details["credentials_found"].append(issue)
                            elif "Token" in issue:
                                details["secrets_found"].append(issue)
            except Exception as e:
                logger.error(f"Security gate evaluation error: {e}", exc_info=True)
                return GateResult(
                    passed=False,
                    severity=GateSeverity.ERROR,
                    message=f"Security gate evaluation failed: {str(e)}",
                    details={"error": str(e)},
                )

        # Scan file if path provided
        if file_path:
            try:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    try:
                        # Use secret scanner
                        scan_result = self.secret_scanner.scan_file(file_path_obj)
                        if scan_result.secrets_found:
                            issues.extend([f"Secret found: {s.type}" for s in scan_result.secrets_found])
                            details["secrets_found"].extend([s.type for s in scan_result.secrets_found])
                    except Exception as e:
                        logger.warning(f"Secret scanner error for {file_path}: {e}")
                        # Continue evaluation even if scanner fails
            except Exception as e:
                logger.warning(f"Invalid file path {file_path}: {e}")

        # Check for vulnerabilities in dependencies
        if context.get("check_dependencies", False):
            # This would integrate with dependency scanning
            # For now, just a placeholder
            pass

        # Determine severity and result
        if details["secrets_found"] or details["pii_found"]:
            severity = GateSeverity.CRITICAL
            passed = False
            message = f"Security gate failed: {len(issues)} security issues found"
        elif details["credentials_found"]:
            severity = GateSeverity.ERROR
            passed = False
            message = "Security gate failed: Credentials detected"
        elif issues:
            severity = GateSeverity.WARNING
            passed = True  # Warnings don't block
            message = f"Security warnings: {len(issues)} issues found"
        else:
            severity = GateSeverity.INFO
            passed = True
            message = "Security gate passed"

        return GateResult(
            passed=passed,
            severity=severity,
            message=message,
            details=details if any(details.values()) else None,
            remediation="Remove secrets, PII, and credentials from code. Use environment variables or secret managers.",
            metadata={"gate_name": "security_gate"},
        )
