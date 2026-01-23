"""
Approval Gate

Human-in-loop approval mechanism for workflow steps.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .base import BaseGate, GateResult, GateSeverity
from .exceptions import MissingContextError

logger = logging.getLogger(__name__)


@dataclass
class ApprovalRequest:
    """An approval request."""

    request_id: str
    workflow_id: str
    step_id: str
    requested_at: datetime
    requested_by: str
    reason: str
    metadata: dict[str, Any] | None = None


@dataclass
class Approval:
    """An approval decision."""

    request_id: str
    approved: bool
    approved_at: datetime
    approved_by: str
    comments: str | None = None


class ApprovalGate(BaseGate):
    """
    Approval gate that requires human-in-loop approval.
    
    Supports:
    - Synchronous approval (blocks until approved)
    - Asynchronous approval (workflow can continue, approval checked later)
    - Approval storage and audit trail
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize approval gate.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.approval_dir = Path(config.get("approval_dir", ".tapps-agents/approvals")) if config else Path(".tapps-agents/approvals")
        self.approval_dir.mkdir(parents=True, exist_ok=True)
        self.auto_approve = config.get("auto_approve", False) if config else False
        self.async_mode = config.get("async_mode", False) if config else False

    def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Evaluate approval gate.

        Args:
            context: Context with workflow_id, step_id, etc.

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

        # Validate required fields
        workflow_id = context.get("workflow_id")
        step_id = context.get("step_id")
        
        if not workflow_id:
            return GateResult(
                passed=False,
                severity=GateSeverity.ERROR,
                message="Missing required context field: workflow_id",
                details={"missing_fields": ["workflow_id"]},
            )
        
        if not step_id:
            return GateResult(
                passed=False,
                severity=GateSeverity.ERROR,
                message="Missing required context field: step_id",
                details={"missing_fields": ["step_id"]},
            )
        
        # Check if approval already exists
        approval = self._get_approval(workflow_id, step_id)
        
        if approval:
            if approval.approved:
                return GateResult(
                    passed=True,
                    severity=GateSeverity.INFO,
                    message=f"Approval gate passed: Approved by {approval.approved_by}",
                    details={"approval": {
                        "approved_by": approval.approved_by,
                        "approved_at": approval.approved_at.isoformat(),
                        "comments": approval.comments,
                    }},
                    metadata={"gate_name": "approval_gate", "approval_id": approval.request_id},
                )
            else:
                return GateResult(
                    passed=False,
                    severity=GateSeverity.ERROR,
                    message=f"Approval gate failed: Rejected by {approval.approved_by}",
                    details={"approval": {
                        "approved_by": approval.approved_by,
                        "approved_at": approval.approved_at.isoformat(),
                        "comments": approval.comments,
                    }},
                    remediation="Request approval from authorized personnel or address rejection reasons.",
                    metadata={"gate_name": "approval_gate", "approval_id": approval.request_id},
                )

        # Auto-approve if configured
        if self.auto_approve:
            self._create_approval(workflow_id, step_id, approved=True, approved_by="auto", comments="Auto-approved")
            return GateResult(
                passed=True,
                severity=GateSeverity.INFO,
                message="Approval gate passed: Auto-approved",
                metadata={"gate_name": "approval_gate", "auto_approved": True},
            )

        # Create approval request
        request_id = self._create_approval_request(workflow_id, step_id, context)
        
        if self.async_mode:
            # Async mode: allow workflow to continue, approval checked later
            return GateResult(
                passed=True,  # Allow to proceed in async mode
                severity=GateSeverity.WARNING,
                message=f"Approval gate: Approval requested (async mode). Request ID: {request_id}",
                details={"request_id": request_id, "async_mode": True},
                metadata={"gate_name": "approval_gate", "request_id": request_id, "async": True},
            )
        else:
            # Sync mode: block until approved
            return GateResult(
                passed=False,
                severity=GateSeverity.ERROR,
                message=f"Approval gate: Pending approval. Request ID: {request_id}",
                details={"request_id": request_id, "async_mode": False},
                remediation=f"Approval required. Request ID: {request_id}. Use 'tapps-agents approval approve {request_id}' to approve.",
                metadata={"gate_name": "approval_gate", "request_id": request_id, "async": False},
            )

    def _create_approval_request(
        self, workflow_id: str, step_id: str, context: dict[str, Any]
    ) -> str:
        """Create an approval request."""
        import uuid
        
        request_id = str(uuid.uuid4())
        request = ApprovalRequest(
            request_id=request_id,
            workflow_id=workflow_id,
            step_id=step_id,
            requested_at=datetime.now(UTC),
            requested_by=context.get("requested_by", "system"),
            reason=context.get("reason", "Approval required for workflow step"),
            metadata=context,
        )
        
        # Save request
        request_file = self.approval_dir / f"{request_id}.json"
        request_data = {
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "step_id": request.step_id,
            "requested_at": request.requested_at.isoformat(),
            "requested_by": request.requested_by,
            "reason": request.reason,
            "metadata": request.metadata,
            "status": "pending",
        }
        request_file.write_text(json.dumps(request_data, indent=2), encoding="utf-8")
        
        return request_id

    def _get_approval(self, workflow_id: str, step_id: str) -> Approval | None:
        """Get existing approval for workflow/step."""
        # Search for approval files
        for approval_file in self.approval_dir.glob("*.json"):
            try:
                data = json.loads(approval_file.read_text(encoding="utf-8"))
                if data.get("workflow_id") == workflow_id and data.get("step_id") == step_id:
                    if data.get("status") == "approved":
                        return Approval(
                            request_id=data["request_id"],
                            approved=True,
                            approved_at=datetime.fromisoformat(data["approved_at"]),
                            approved_by=data["approved_by"],
                            comments=data.get("comments"),
                        )
                    elif data.get("status") == "rejected":
                        return Approval(
                            request_id=data["request_id"],
                            approved=False,
                            approved_at=datetime.fromisoformat(data["approved_at"]),
                            approved_by=data["approved_by"],
                            comments=data.get("comments"),
                        )
            except Exception:
                continue
        
        return None

    def _create_approval(
        self,
        workflow_id: str,
        step_id: str,
        approved: bool,
        approved_by: str,
        comments: str | None = None,
    ) -> None:
        """Create an approval record."""
        import uuid
        
        request_id = str(uuid.uuid4())
        approval_file = self.approval_dir / f"{request_id}.json"
        approval_data = {
            "request_id": request_id,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "approved": approved,
            "approved_at": datetime.now(UTC).isoformat(),
            "approved_by": approved_by,
            "comments": comments,
            "status": "approved" if approved else "rejected",
        }
        approval_file.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")
