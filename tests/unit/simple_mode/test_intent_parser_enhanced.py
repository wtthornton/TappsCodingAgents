"""
Unit tests for enhanced IntentParser with Simple Mode intent detection.

Tests Simple Mode keyword detection and enhanced parse() method.
"""

import pytest

from tapps_agents.simple_mode.intent_parser import IntentParser, IntentType

pytestmark = pytest.mark.unit


class TestSimpleModeIntentDetection:
    """Test Simple Mode intent detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()

    def test_detect_simple_mode_intent_at_simple_mode(self):
        """Test detect_simple_mode_intent() with '@simple-mode'."""
        assert self.parser.detect_simple_mode_intent("@simple-mode build feature") is True

    def test_detect_simple_mode_intent_simple_mode(self):
        """Test detect_simple_mode_intent() with 'simple mode'."""
        assert self.parser.detect_simple_mode_intent("simple mode build feature") is True

    def test_detect_simple_mode_intent_use_simple_mode(self):
        """Test detect_simple_mode_intent() with 'use simple mode'."""
        assert self.parser.detect_simple_mode_intent("use simple mode to create api") is True

    def test_detect_simple_mode_intent_simple_mode_hyphen(self):
        """Test detect_simple_mode_intent() with 'simple-mode'."""
        assert self.parser.detect_simple_mode_intent("simple-mode build feature") is True

    def test_detect_simple_mode_intent_at_simple_mode_underscore(self):
        """Test detect_simple_mode_intent() with '@simple_mode'."""
        assert self.parser.detect_simple_mode_intent("@simple_mode build feature") is True

    def test_detect_simple_mode_intent_simple_mode_underscore(self):
        """Test detect_simple_mode_intent() with 'simple_mode'."""
        assert self.parser.detect_simple_mode_intent("simple_mode build feature") is True

    def test_detect_simple_mode_intent_case_insensitive(self):
        """Test detect_simple_mode_intent() is case insensitive."""
        assert self.parser.detect_simple_mode_intent("@SIMPLE-MODE build feature") is True
        assert self.parser.detect_simple_mode_intent("SIMPLE MODE build feature") is True

    def test_detect_simple_mode_intent_false_positive(self):
        """Test detect_simple_mode_intent() with false positives."""
        assert self.parser.detect_simple_mode_intent("build feature") is False
        assert self.parser.detect_simple_mode_intent("simple task") is False
        assert self.parser.detect_simple_mode_intent("mode of operation") is False

    def test_detect_simple_mode_intent_empty_string(self):
        """Test detect_simple_mode_intent() with empty string."""
        assert self.parser.detect_simple_mode_intent("") is False

    def test_detect_simple_mode_intent_partial_match(self):
        """Test detect_simple_mode_intent() with partial matches."""
        # Should match if keyword appears anywhere
        assert self.parser.detect_simple_mode_intent("I want to use simple mode") is True
        assert self.parser.detect_simple_mode_intent("Please use @simple-mode") is True


class TestEnhancedParse:
    """Test enhanced parse() method with Simple Mode detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()

    def test_parse_sets_force_simple_mode(self):
        """Test parse() sets force_simple_mode=True when detected."""
        intent = self.parser.parse("@simple-mode build feature")
        assert intent.parameters.get("force_simple_mode") is True

    def test_parse_simple_mode_with_build_keywords(self):
        """Test parse() with Simple Mode intent + build keywords."""
        intent = self.parser.parse("@simple-mode build user authentication")
        assert intent.parameters.get("force_simple_mode") is True
        assert intent.type in [IntentType.BUILD, IntentType.UNKNOWN]  # May detect as build

    def test_parse_simple_mode_with_review_keywords(self):
        """Test parse() with Simple Mode intent + review keywords."""
        intent = self.parser.parse("@simple-mode review my code")
        assert intent.parameters.get("force_simple_mode") is True

    def test_parse_simple_mode_with_fix_keywords(self):
        """Test parse() with Simple Mode intent + fix keywords."""
        intent = self.parser.parse("@simple-mode fix the error")
        assert intent.parameters.get("force_simple_mode") is True

    def test_parse_preserves_other_parameters(self):
        """Test parse() preserves other intent parameters."""
        intent = self.parser.parse("@simple-mode build feature in src/app.py")
        assert intent.parameters.get("force_simple_mode") is True
        # Should also extract file path if present
        if "files" in intent.parameters:
            assert len(intent.parameters["files"]) > 0

    def test_parse_without_simple_mode(self):
        """Test parse() without Simple Mode intent."""
        intent = self.parser.parse("build feature")
        assert intent.parameters.get("force_simple_mode") is not True
        # Should not have force_simple_mode or it should be False/None

    def test_parse_simple_mode_variations(self):
        """Test parse() with various Simple Mode keyword variations."""
        variations = [
            "@simple-mode build",
            "simple mode build",
            "use simple mode to build",
            "@simple_mode build",
            "simple-mode build",
        ]
        for variation in variations:
            intent = self.parser.parse(variation)
            assert intent.parameters.get("force_simple_mode") is True, f"Failed for: {variation}"


class TestRequirementsIntentDetection:
    """Test requirements intent detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IntentParser()

    def test_parse_requirements_keyword(self):
        """Test parse() detects requirements intent."""
        intent = self.parser.parse("gather requirements for user authentication")
        assert intent.type == IntentType.REQUIREMENTS

    def test_parse_extract_requirements(self):
        """Test parse() detects extract requirements intent."""
        intent = self.parser.parse("extract requirements from stakeholder description")
        assert intent.type == IntentType.REQUIREMENTS

    def test_parse_document_requirements(self):
        """Test parse() detects document requirements intent."""
        intent = self.parser.parse("document requirements for new feature")
        assert intent.type == IntentType.REQUIREMENTS

    def test_parse_analyze_requirements(self):
        """Test parse() detects analyze requirements intent."""
        intent = self.parser.parse("analyze requirements for payment system")
        assert intent.type == IntentType.REQUIREMENTS

    def test_parse_requirements_document(self):
        """Test parse() detects requirements document intent."""
        intent = self.parser.parse("create requirements document")
        assert intent.type == IntentType.REQUIREMENTS

    def test_parse_requirements_gathering(self):
        """Test parse() detects requirements gathering intent."""
        intent = self.parser.parse("requirements gathering for epic")
        assert intent.type == IntentType.REQUIREMENTS

    def test_parse_requirements_analysis(self):
        """Test parse() detects requirements analysis intent."""
        intent = self.parser.parse("requirements analysis for project")
        assert intent.type == IntentType.REQUIREMENTS

    def test_requirements_intent_agent_sequence(self):
        """Test requirements intent returns correct agent sequence."""
        intent = self.parser.parse("gather requirements")
        sequence = intent.get_agent_sequence()
        assert "analyst" in sequence
        assert "planner" in sequence
        assert "documenter" in sequence

    def test_requirements_intent_not_build(self):
        """Test requirements intent is distinct from build intent."""
        requirements_intent = self.parser.parse("gather requirements")
        build_intent = self.parser.parse("build feature")
        
        assert requirements_intent.type == IntentType.REQUIREMENTS
        assert build_intent.type == IntentType.BUILD
        assert requirements_intent.type != build_intent.type

    def test_requirements_keywords_case_insensitive(self):
        """Test requirements keywords are case insensitive."""
        variations = [
            "GATHER REQUIREMENTS",
            "Gather Requirements",
            "gather requirements",
            "Requirements Gathering",
        ]
        for variation in variations:
            intent = self.parser.parse(variation)
            assert intent.type == IntentType.REQUIREMENTS, f"Failed for: {variation}"