"""
Tests for compare semantics in IntentParser.

Tests the enhanced compare_to_codebase flag detection with various
compare-related phrases and patterns.
"""

import pytest

from tapps_agents.simple_mode.intent_parser import IntentParser, IntentType

pytestmark = pytest.mark.unit


@pytest.fixture
def parser():
    """Create IntentParser instance for testing."""
    return IntentParser()


class TestCompareSemantics:
    """Test compare_to_codebase flag detection."""

    # ========================================================================
    # Test Direct Compare Phrases
    # ========================================================================

    def test_compare_to(self, parser):
        """Test 'compare to' phrase."""
        intent = parser.parse("compare to our codebase patterns")
        assert intent.compare_to_codebase is True

    def test_compare_with(self, parser):
        """Test 'compare with' phrase."""
        intent = parser.parse("compare with project standards")
        assert intent.compare_to_codebase is True

    def test_compare_against(self, parser):
        """Test 'compare against' phrase."""
        intent = parser.parse("compare against our patterns")
        assert intent.compare_to_codebase is True

    def test_compare_this_to(self, parser):
        """Test 'compare this to' phrase."""
        intent = parser.parse("compare this to codebase")
        assert intent.compare_to_codebase is True

    def test_compare_this_with(self, parser):
        """Test 'compare this with' phrase."""
        intent = parser.parse("compare this with our patterns")
        assert intent.compare_to_codebase is True

    def test_compare_to_codebase(self, parser):
        """Test explicit 'compare to codebase' phrase."""
        intent = parser.parse("compare to codebase and fix")
        assert intent.compare_to_codebase is True

    def test_compare_to_our(self, parser):
        """Test 'compare to our' phrase."""
        intent = parser.parse("compare to our patterns")
        assert intent.compare_to_codebase is True

    def test_compare_to_project(self, parser):
        """Test 'compare to project' phrase."""
        intent = parser.parse("compare to project standards")
        assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Match/Align Phrases
    # ========================================================================

    def test_match_our(self, parser):
        """Test 'match our' phrase."""
        intent = parser.parse("match our coding standards")
        assert intent.compare_to_codebase is True

    def test_match_the(self, parser):
        """Test 'match the' phrase."""
        intent = parser.parse("match the project patterns")
        assert intent.compare_to_codebase is True

    def test_match_patterns(self, parser):
        """Test 'match patterns' phrase."""
        intent = parser.parse("make sure it match patterns")
        assert intent.compare_to_codebase is True

    def test_match_codebase(self, parser):
        """Test 'match codebase' phrase."""
        intent = parser.parse("match codebase style")
        assert intent.compare_to_codebase is True

    def test_align_with(self, parser):
        """Test 'align with' phrase."""
        intent = parser.parse("align with our architecture")
        assert intent.compare_to_codebase is True

    def test_align_to(self, parser):
        """Test 'align to' phrase."""
        intent = parser.parse("align to project standards")
        assert intent.compare_to_codebase is True

    def test_follow_patterns(self, parser):
        """Test 'follow patterns' phrase."""
        intent = parser.parse("follow patterns from our codebase")
        assert intent.compare_to_codebase is True

    def test_follow_our_patterns(self, parser):
        """Test 'follow our patterns' phrase."""
        intent = parser.parse("follow our patterns for error handling")
        assert intent.compare_to_codebase is True

    def test_follow_project_patterns(self, parser):
        """Test 'follow project patterns' phrase."""
        intent = parser.parse("follow project patterns and conventions")
        assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Make Match Phrases (Implicit Compare)
    # ========================================================================

    def test_make_match(self, parser):
        """Test 'make match' phrase."""
        intent = parser.parse("make match with our code style")
        assert intent.compare_to_codebase is True

    def test_make_this_match(self, parser):
        """Test 'make this match' phrase."""
        intent = parser.parse("make this match our patterns")
        assert intent.compare_to_codebase is True

    def test_make_it_match(self, parser):
        """Test 'make it match' phrase."""
        intent = parser.parse("make it match the codebase standards")
        assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Consistency Phrases
    # ========================================================================

    def test_consistent_with(self, parser):
        """Test 'consistent with' phrase."""
        intent = parser.parse("ensure code is consistent with our patterns")
        assert intent.compare_to_codebase is True

    def test_consistency_with(self, parser):
        """Test 'consistency with' phrase."""
        intent = parser.parse("check consistency with project standards")
        assert intent.compare_to_codebase is True

    def test_conform_to(self, parser):
        """Test 'conform to' phrase."""
        intent = parser.parse("conform to our coding guidelines")
        assert intent.compare_to_codebase is True

    def test_conform_with(self, parser):
        """Test 'conform with' phrase."""
        intent = parser.parse("conform with project architecture")
        assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Standard Phrases
    # ========================================================================

    def test_match_standards(self, parser):
        """Test 'match standards' phrase."""
        intent = parser.parse("match standards from the codebase")
        assert intent.compare_to_codebase is True

    def test_follow_standards(self, parser):
        """Test 'follow standards' phrase."""
        intent = parser.parse("follow standards set by the project")
        assert intent.compare_to_codebase is True

    def test_meet_standards(self, parser):
        """Test 'meet standards' phrase."""
        intent = parser.parse("meet standards defined in our codebase")
        assert intent.compare_to_codebase is True

    def test_adhere_to(self, parser):
        """Test 'adhere to' phrase."""
        intent = parser.parse("adhere to our coding conventions")
        assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Case Insensitivity
    # ========================================================================

    def test_case_insensitive_compare(self, parser):
        """Test compare detection is case-insensitive."""
        intents = [
            parser.parse("COMPARE TO our patterns"),
            parser.parse("Compare To our patterns"),
            parser.parse("compare to our patterns"),
        ]
        for intent in intents:
            assert intent.compare_to_codebase is True

    def test_case_insensitive_match(self, parser):
        """Test match detection is case-insensitive."""
        intents = [
            parser.parse("MATCH OUR patterns"),
            parser.parse("Match Our patterns"),
            parser.parse("match our patterns"),
        ]
        for intent in intents:
            assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Combined with Intent Types
    # ========================================================================

    def test_compare_with_review_intent(self, parser):
        """Test compare flag with review intent."""
        intent = parser.parse("review this code and compare to our patterns")
        assert intent.type == IntentType.REVIEW
        assert intent.compare_to_codebase is True

    def test_compare_with_fix_intent(self, parser):
        """Test compare flag with fix intent."""
        intent = parser.parse("compare to codebase and fix any differences")
        # Should detect both compare and fix
        assert intent.compare_to_codebase is True
        # Intent type depends on keyword weighting

    def test_compare_with_refactor_intent(self, parser):
        """Test compare flag with refactor intent."""
        intent = parser.parse("refactor this to match our patterns")
        assert intent.type == IntentType.REFACTOR
        assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Negative Cases (Should NOT Set Flag)
    # ========================================================================

    def test_no_compare_simple_review(self, parser):
        """Test simple review without compare."""
        intent = parser.parse("review this code for quality")
        assert intent.compare_to_codebase is False

    def test_no_compare_simple_fix(self, parser):
        """Test simple fix without compare."""
        intent = parser.parse("fix the bug in auth.py")
        assert intent.compare_to_codebase is False

    def test_no_compare_build(self, parser):
        """Test build without compare."""
        intent = parser.parse("build a new authentication system")
        assert intent.compare_to_codebase is False

    def test_no_compare_test(self, parser):
        """Test test generation without compare."""
        intent = parser.parse("generate tests for this module")
        assert intent.compare_to_codebase is False

    # ========================================================================
    # Test Edge Cases
    # ========================================================================

    def test_compare_with_whitespace(self, parser):
        """Test compare detection with leading/trailing whitespace."""
        intent = parser.parse("  compare to our patterns  ")
        assert intent.compare_to_codebase is True

    def test_compare_multiline(self, parser):
        """Test compare detection with multiline input."""
        intent = parser.parse("review this code\nand compare to our patterns")
        assert intent.compare_to_codebase is True

    def test_compare_with_punctuation(self, parser):
        """Test compare detection with punctuation."""
        intent = parser.parse("Compare to our patterns, and fix any issues!")
        assert intent.compare_to_codebase is True

    # ========================================================================
    # Test Real User Prompts
    # ========================================================================

    @pytest.mark.parametrize("prompt,should_set_flag", [
        ("compare this to our codebase patterns", True),
        ("match our coding standards", True),
        ("align with project architecture", True),
        ("make this match our patterns", True),
        ("ensure consistency with codebase", True),
        ("conform to our guidelines", True),
        ("follow standards defined in our codebase", True),
        ("adhere to coding conventions", True),
        ("review and compare to codebase", True),
        ("compare against our patterns and fix", True),
        ("review this file", False),
        ("fix the bug", False),
        ("build new feature", False),
        ("generate tests", False),
    ])
    def test_real_user_prompts(self, parser, prompt, should_set_flag):
        """Test real user prompts for compare flag."""
        intent = parser.parse(prompt)
        assert intent.compare_to_codebase == should_set_flag

    # ========================================================================
    # Test Integration with Workflow Suggester
    # ========================================================================

    def test_compare_flag_available_for_workflow_suggester(self, parser):
        """Test that compare flag is available in Intent for workflow suggester."""
        intent = parser.parse("compare to codebase and fix issues")

        # Intent should have compare_to_codebase attribute
        assert hasattr(intent, "compare_to_codebase")
        assert intent.compare_to_codebase is True

        # Intent should be usable by workflow suggester for confidence boosting
        # (workflow suggester reads intent.compare_to_codebase for hybrid detection)
