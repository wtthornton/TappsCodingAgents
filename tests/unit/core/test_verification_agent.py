"""Unit tests for VerificationAgent and RefinementAgent."""

import pytest

from tapps_agents.core.verification_agent import RefinementAgent, VerificationAgent


@pytest.mark.unit
class TestVerificationAgent:
    """Tests for VerificationAgent."""

    def test_verify_pass_empty_requirements(self):
        """Verify returns verified when requirements are empty."""
        agent = VerificationAgent()
        result = agent.verify({"a": 1}, {})
        assert result["verified"] is True
        assert result["issues"] == []

    def test_verify_pass_required_keys_present(self):
        """Verify passes when required_keys are present in output dict."""
        agent = VerificationAgent()
        result = agent.verify({"a": 1, "b": 2}, {"required_keys": ["a", "b"]})
        assert result["verified"] is True
        assert result["issues"] == []

    def test_verify_fail_required_keys_missing(self):
        """Verify fails when required_keys are missing."""
        agent = VerificationAgent()
        result = agent.verify({"a": 1}, {"required_keys": ["a", "b", "c"]})
        assert result["verified"] is False
        assert "Missing required keys" in result["issues"][0]
        assert "b" in result["issues"][0] or "c" in result["issues"][0]

    def test_verify_fail_non_empty_requirement(self):
        """Verify fails when non_empty is True and output is empty."""
        agent = VerificationAgent()
        result = agent.verify("", {"non_empty": True})
        assert result["verified"] is False
        assert any("non-empty" in i.lower() for i in result["issues"])

    def test_verify_fail_min_length(self):
        """Verify fails when output is shorter than min_length."""
        agent = VerificationAgent()
        result = agent.verify("ab", {"min_length": 5})
        assert result["verified"] is False
        assert any("length" in i.lower() or "min_length" in i for i in result["issues"])


@pytest.mark.unit
class TestRefinementAgent:
    """Tests for RefinementAgent."""

    def test_refine_empty_issues_returns_unchanged(self):
        """Refine returns output unchanged when issues are empty."""
        agent = RefinementAgent()
        out = {"x": 1}
        assert agent.refine(out, []) == out

    def test_refine_dict_adds_refinement_record(self):
        """Refine adds _refinement to dict output when issues present."""
        agent = RefinementAgent()
        out = {"x": 1}
        refined = agent.refine(out, ["issue1"])
        assert refined["x"] == 1
        assert refined.get("_refinement", {}).get("issues_addressed") == ["issue1"]
        assert refined["_refinement"]["refined"] is True

    def test_refine_str_appends_comment(self):
        """Refine appends a refinement note to str output."""
        agent = RefinementAgent()
        out = "original"
        refined = agent.refine(out, ["a", "b"])
        assert refined.startswith("original")
        assert "Refinement" in refined
        assert "a" in refined
        assert "b" in refined
