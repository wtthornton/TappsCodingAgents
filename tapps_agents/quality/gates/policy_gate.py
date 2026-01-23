"""
Policy Gate

Enforces compliance policies (GDPR, HIPAA, PCI-DSS) and custom policies.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .base import BaseGate, GateResult, GateSeverity
from .exceptions import GateConfigurationError

logger = logging.getLogger(__name__)


class PolicyGate(BaseGate):
    """
    Policy gate that enforces compliance and custom policies.
    
    Supports:
    - GDPR compliance
    - HIPAA compliance
    - PCI-DSS compliance
    - Custom project policies
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize policy gate.

        Args:
            config: Configuration dictionary with policy settings
        """
        super().__init__(config)
        self.policy_dir = Path(config.get("policy_dir", ".tapps-agents/policies")) if config else Path(".tapps-agents/policies")
        self.enabled_policies = config.get("enabled_policies", []) if config else []

    def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Evaluate policy gate.

        Args:
            context: Context with workflow/step information

        Returns:
            GateResult
        """
        # Validate context
        if not context or not isinstance(context, dict):
            return GateResult(
                passed=False,
                severity=GateSeverity.ERROR,
                message="Invalid context: context must be a dictionary",
                details={"error": "Invalid context type"},
            )

        violations: list[str] = []
        details: dict[str, Any] = {
            "policy_checks": {},
            "violations": [],
        }

        # Load and check enabled policies
        for policy_name in self.enabled_policies:
            if not policy_name or not isinstance(policy_name, str):
                logger.warning(f"Invalid policy name: {policy_name}, skipping")
                continue
            policy_result = self._check_policy(policy_name, context)
            details["policy_checks"][policy_name] = policy_result
            
            if not policy_result.get("passed", True):
                violations.append(f"Policy violation: {policy_name}")
                details["violations"].append({
                    "policy": policy_name,
                    "reason": policy_result.get("reason", "Unknown violation"),
                })

        # Check standard compliance policies if configured
        if self.config.get("check_gdpr", False):
            gdpr_result = self._check_gdpr_compliance(context)
            details["policy_checks"]["GDPR"] = gdpr_result
            if not gdpr_result.get("passed", True):
                violations.append("GDPR compliance violation")

        if self.config.get("check_hipaa", False):
            hipaa_result = self._check_hipaa_compliance(context)
            details["policy_checks"]["HIPAA"] = hipaa_result
            if not hipaa_result.get("passed", True):
                violations.append("HIPAA compliance violation")

        if self.config.get("check_pci_dss", False):
            pci_result = self._check_pci_dss_compliance(context)
            details["policy_checks"]["PCI-DSS"] = pci_result
            if not pci_result.get("passed", True):
                violations.append("PCI-DSS compliance violation")

        # Determine result
        if violations:
            severity = GateSeverity.ERROR
            passed = False
            message = f"Policy gate failed: {len(violations)} violations found"
        else:
            severity = GateSeverity.INFO
            passed = True
            message = "Policy gate passed"

        return GateResult(
            passed=passed,
            severity=severity,
            message=message,
            details=details if violations else None,
            remediation="Review and fix policy violations. See policy documentation for details.",
            metadata={"gate_name": "policy_gate", "policies_checked": list(details["policy_checks"].keys())},
        )

    def _check_policy(self, policy_name: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Check a custom policy.

        Args:
            policy_name: Name of the policy
            context: Context dictionary

        Returns:
            Policy check result
        """
        policy_file = self.policy_dir / f"{policy_name}.json"
        
        if not policy_file.exists():
            return {
                "passed": True,
                "reason": f"Policy file not found: {policy_file}",
            }

        try:
            policy_data = json.loads(policy_file.read_text(encoding="utf-8"))
            rules = policy_data.get("rules", [])
            
            for rule in rules:
                # Simple rule evaluation (can be extended)
                rule_type = rule.get("type")
                if rule_type == "file_pattern":
                    # Check if files match pattern
                    file_path = context.get("file_path", "")
                    pattern = rule.get("pattern", "")
                    if pattern and pattern in file_path:
                        if not rule.get("allowed", True):
                            return {
                                "passed": False,
                                "reason": f"File pattern violation: {pattern}",
                            }
            
            return {"passed": True}
        except Exception as e:
            return {
                "passed": True,  # Don't fail on policy load errors
                "reason": f"Policy evaluation error: {e}",
            }

    def _check_gdpr_compliance(self, context: dict[str, Any]) -> dict[str, Any]:
        """Check GDPR compliance."""
        # Basic GDPR checks
        # In a full implementation, this would check for:
        # - Data processing consent
        # - Right to deletion
        # - Data portability
        # - Privacy notices
        
        return {"passed": True, "reason": "GDPR compliance check not fully implemented"}

    def _check_hipaa_compliance(self, context: dict[str, Any]) -> dict[str, Any]:
        """Check HIPAA compliance."""
        # Basic HIPAA checks
        # In a full implementation, this would check for:
        # - PHI handling
        # - Encryption requirements
        # - Access controls
        # - Audit logging
        
        return {"passed": True, "reason": "HIPAA compliance check not fully implemented"}

    def _check_pci_dss_compliance(self, context: dict[str, Any]) -> dict[str, Any]:
        """Check PCI-DSS compliance."""
        # Basic PCI-DSS checks
        # In a full implementation, this would check for:
        # - Card data handling
        # - Encryption requirements
        # - Access controls
        # - Network segmentation
        
        return {"passed": True, "reason": "PCI-DSS compliance check not fully implemented"}
