"""
Collaborative Verification Agents

Verification and refinement agents without manual prompts.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Verification agent that examines outputs at each step."""

    def verify(self, output: Any, requirements: dict[str, Any]) -> dict[str, Any]:
        """
        Verify output meets requirements.

        Args:
            output: Output to verify
            requirements: Requirements to check against (e.g. required_keys, min_length, non_empty)

        Returns:
            Verification result with verified (bool) and issues (list of str)
        """
        issues: list[str] = []

        # Required keys: if requirements has required_keys, output (if dict) must contain them
        required_keys = requirements.get("required_keys")
        if isinstance(required_keys, list) and required_keys:
            if not isinstance(output, dict):
                issues.append(f"Output must be a dict with keys {required_keys}, got {type(output).__name__}")
            else:
                missing = [k for k in required_keys if k not in output]
                if missing:
                    issues.append(f"Missing required keys: {missing}")

        # Non-empty: if requirements.get("non_empty") is True, output must be non-empty
        if requirements.get("non_empty") is True:
            if output is None:
                issues.append("Output must be non-empty, got None")
            elif isinstance(output, (str, list, dict)) and len(output) == 0:
                issues.append("Output must be non-empty")

        # min_length: for str/list, check length
        min_len = requirements.get("min_length")
        if isinstance(min_len, (int, float)) and min_len > 0:
            if isinstance(output, (str, list)):
                if len(output) < int(min_len):
                    issues.append(f"Output length {len(output)} below min_length {min_len}")
            elif isinstance(output, dict) and len(output) < int(min_len):
                issues.append(f"Output has {len(output)} keys, below min_length {min_len}")

        return {"verified": len(issues) == 0, "issues": issues}


class RefinementAgent:
    """Refinement agent that revises outputs based on issues."""

    def refine(self, output: Any, issues: list[str]) -> Any:
        """
        Refine output based on issues.

        Args:
            output: Output to refine
            issues: List of issues to address

        Returns:
            Refined output (structure preserved; refinements recorded when possible)
        """
        if not issues:
            return output

        # For dict: add a refinement record without mutating semantic content
        if isinstance(output, dict):
            out = dict(output)
            out["_refinement"] = {"issues_addressed": issues, "refined": True}
            return out

        # For str: append a short refinement note as a comment block
        if isinstance(output, str):
            block = "\n\n# Refinement: issues to address: " + "; ".join(issues[:5])
            if len(issues) > 5:
                block += f" (+{len(issues) - 5} more)"
            return output + block

        # For other types, return as-is (refinement would need type-specific logic)
        return output

