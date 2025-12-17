"""
Unit tests for natural language parser (Story 9.1, 9.2).
"""

import pytest

from tapps_agents.workflow.nlp_parser import NaturalLanguageParser, WorkflowIntent, WorkflowIntentResult


@pytest.mark.unit
class TestNaturalLanguageParser:
    """Tests for NaturalLanguageParser."""

    def test_exact_match(self):
        """Test exact workflow name matching."""
        parser = NaturalLanguageParser()
        result = parser.parse("rapid-dev")

        assert result.workflow_name == "rapid-dev"
        assert result.confidence >= 0.9
        assert result.match_type == "exact"

    def test_alias_match(self):
        """Test alias matching."""
        parser = NaturalLanguageParser()
        result = parser.parse("rapid")

        assert result.workflow_name == "rapid-dev"
        assert result.confidence >= 0.8
        assert "rapid" in result.aliases_matched

    def test_synonym_match(self):
        """Test synonym matching."""
        parser = NaturalLanguageParser()
        result = parser.parse("rapid development")

        assert result.workflow_name == "rapid-dev"
        assert result.confidence >= 0.7

    def test_fuzzy_match(self):
        """Test fuzzy matching."""
        parser = NaturalLanguageParser()
        result = parser.parse("rapd-dev")  # Typo

        # Should still match with lower confidence
        assert result.workflow_name is not None
        assert result.match_type == "fuzzy"

    def test_no_match(self):
        """Test no match scenario."""
        parser = NaturalLanguageParser()
        result = parser.parse("nonexistent workflow")

        assert result.workflow_name is None
        assert result.confidence == 0.0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        parser = NaturalLanguageParser()
        result1 = parser.parse("RAPID")
        result2 = parser.parse("rapid")

        assert result1.workflow_name == result2.workflow_name

    def test_intent_detection(self):
        """Test intent detection."""
        parser = NaturalLanguageParser()
        result = parser.detect_intent("run rapid development")

        assert result.action_verb == "run"
        assert result.workflow_name == "rapid-dev"
        assert result.workflow_type == "rapid"
        assert result.confidence > 0.0

    def test_parameter_extraction(self):
        """Test parameter extraction."""
        parser = NaturalLanguageParser()
        result = parser.detect_intent("run fix on example.py")

        assert result.action_verb == "run"
        assert "target_file" in result.parameters
        assert result.parameters["target_file"] == "example.py"

    def test_ambiguity_detection(self):
        """Test ambiguity detection."""
        parser = NaturalLanguageParser()
        result = parser.detect_intent("run workflow")

        # Should detect ambiguity if multiple matches
        # (This depends on actual workflow names)
        assert isinstance(result.ambiguity_flag, bool)

