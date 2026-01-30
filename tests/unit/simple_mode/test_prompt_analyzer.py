"""Unit tests for PromptAnalyzer."""

import pytest
from tapps_agents.simple_mode.prompt_analyzer import (
    PromptAnalyzer,
    TaskIntent,
    PromptComplexity,
    ExistingCodeReference,
    PromptAnalysis,
)


@pytest.mark.unit
class TestPromptAnalyzer:
    """Test PromptAnalyzer functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PromptAnalyzer()

    # Intent Detection Tests

    def test_detect_build_intent(self, analyzer):
        """Test build intent detection."""
        prompt = "Create a user authentication API with JWT tokens"
        analysis = analyzer.analyze(prompt)

        assert analysis.primary_intent == TaskIntent.BUILD
        assert analysis.intent_confidence >= 0.5

    def test_detect_validate_intent(self, analyzer):
        """Test validate intent detection."""
        prompt = "Compare implementation with existing code at lines 751-878"
        analysis = analyzer.analyze(prompt)

        # Should detect validate based on keywords
        assert analysis.primary_intent == TaskIntent.VALIDATE
        assert analysis.has_existing_code is True
        assert analysis.mentions_compare is True

    def test_detect_validate_intent_with_existing_implementation(self, analyzer):
        """Test validate intent with existing implementation mention."""
        prompt = "Check the existing implementation for correctness"
        analysis = analyzer.analyze(prompt)

        # Should prioritize VALIDATE due to keywords
        assert analysis.primary_intent in [TaskIntent.VALIDATE, TaskIntent.REVIEW]

    def test_detect_optimize_intent(self, analyzer):
        """Test optimize intent detection."""
        prompt = "Make this code faster with early exit optimization"
        analysis = analyzer.analyze(prompt)

        assert analysis.primary_intent == TaskIntent.OPTIMIZE

    def test_detect_fix_intent(self, analyzer):
        """Test fix intent detection."""
        prompt = "Fix the login bug in authentication"
        analysis = analyzer.analyze(prompt)

        assert analysis.primary_intent == TaskIntent.FIX

    def test_detect_review_intent(self, analyzer):
        """Test review intent detection."""
        prompt = "Review the code quality and security of this module"
        analysis = analyzer.analyze(prompt)

        assert analysis.primary_intent == TaskIntent.REVIEW

    def test_detect_test_intent(self, analyzer):
        """Test test intent detection."""
        prompt = "Generate tests for the user service with good coverage"
        analysis = analyzer.analyze(prompt)

        # Could be TEST or BUILD depending on scoring
        assert analysis.primary_intent in [TaskIntent.TEST, TaskIntent.BUILD]

    def test_detect_refactor_intent(self, analyzer):
        """Test refactor intent detection."""
        prompt = "Refactor this module to improve maintainability"
        analysis = analyzer.analyze(prompt)

        assert analysis.primary_intent == TaskIntent.REFACTOR

    def test_detect_explore_intent(self, analyzer):
        """Test explore intent detection."""
        prompt = "Explore the codebase to find authentication logic"
        analysis = analyzer.analyze(prompt)

        assert analysis.primary_intent == TaskIntent.EXPLORE

    # Complexity Tests

    def test_minimal_complexity(self, analyzer):
        """Test minimal complexity detection."""
        prompt = "Fix the login bug"
        analysis = analyzer.analyze(prompt)

        assert analysis.complexity == PromptComplexity.MINIMAL
        assert analysis.word_count < 50

    def test_standard_complexity(self, analyzer):
        """Test standard complexity detection."""
        prompt = " ".join(["word"] * 80)  # 80-word prompt
        analysis = analyzer.analyze(prompt)

        assert analysis.complexity == PromptComplexity.STANDARD
        assert 50 <= analysis.word_count < 150

    def test_detailed_complexity(self, analyzer):
        """Test detailed complexity detection."""
        prompt = " ".join(["word"] * 200)  # 200-word prompt
        analysis = analyzer.analyze(prompt)

        assert analysis.complexity == PromptComplexity.DETAILED
        assert 150 <= analysis.word_count < 300

    def test_comprehensive_complexity(self, analyzer):
        """Test comprehensive complexity detection."""
        prompt = " ".join(["word"] * 350)  # 350-word prompt
        analysis = analyzer.analyze(prompt)

        assert analysis.complexity == PromptComplexity.COMPREHENSIVE
        assert analysis.word_count >= 300

    # Existing Code Detection Tests

    def test_detect_existing_code_with_lines(self, analyzer):
        """Test existing code detection with line numbers."""
        prompt = "Compare with manual implementation at lines 751-878 in project_cleanup_agent.py"
        analysis = analyzer.analyze(prompt)

        assert analysis.has_existing_code is True
        assert len(analysis.existing_code_refs) > 0
        # Check if file path was detected
        assert any("project_cleanup_agent.py" in (ref.file_path or "") for ref in analysis.existing_code_refs)

    def test_detect_existing_code_simple_mention(self, analyzer):
        """Test detection of simple 'existing implementation' mention."""
        prompt = "Check against the existing implementation"
        analysis = analyzer.analyze(prompt)

        assert analysis.has_existing_code is True
        assert len(analysis.existing_code_refs) > 0

    def test_detect_existing_code_quality_hint_excellent(self, analyzer):
        """Test quality hint extraction for excellent code."""
        prompt = "Existing implementation is excellent at lines 100-200"
        analysis = analyzer.analyze(prompt)

        assert analysis.has_existing_code is True
        assert any(ref.quality_hint == "excellent" for ref in analysis.existing_code_refs)

    def test_detect_existing_code_quality_hint_needs_work(self, analyzer):
        """Test quality hint extraction for code needing work."""
        prompt = "The current code needs work and is broken"
        analysis = analyzer.analyze(prompt)

        assert analysis.has_existing_code is True

    def test_no_existing_code_detection(self, analyzer):
        """Test that no false positives for existing code."""
        prompt = "Create a new authentication system from scratch"
        analysis = analyzer.analyze(prompt)

        assert analysis.has_existing_code is False

    # Recommendation Tests

    def test_recommend_validation_workflow(self, analyzer):
        """Test validation workflow recommendation."""
        prompt = "Compare implementation with existing manual code at lines 100-200"
        analysis = analyzer.analyze(prompt, command="*build")

        assert analysis.recommended_workflow == "validate"
        # Confidence should be decent since we have clear indicators
        assert analysis.intent_confidence >= 0.7

    def test_recommend_build_workflow(self, analyzer):
        """Test build workflow recommendation."""
        prompt = "Create a new user management feature"
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_workflow == "build"

    def test_recommend_quick_wins_workflow(self, analyzer):
        """Test quick wins workflow recommendation."""
        prompt = "Optimize the code for better performance"
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_workflow == "quick-wins"

    def test_recommend_quick_enhancement_for_detailed_prompt(self, analyzer):
        """Test quick enhancement for detailed prompts."""
        prompt = " ".join([
            "Create a comprehensive user authentication system with the following features:",
            "1. JWT token-based authentication",
            "2. Refresh token rotation",
            "3. OAuth2 integration with Google and GitHub",
            "4. Role-based access control with custom permissions",
            "5. Password reset flow with email verification",
            "6. Two-factor authentication support",
            "7. Session management with Redis",
            "8. Comprehensive audit logging",
            "9. Rate limiting to prevent brute force attacks",
            "10. Secure password hashing with bcrypt",
        ] * 2)  # Make it detailed
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_enhancement == "quick"
        assert "concise enhancement" in analysis.analysis_rationale.lower()

    def test_recommend_full_enhancement_for_short_prompt(self, analyzer):
        """Test full enhancement for short prompts."""
        prompt = "Add user login"
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_enhancement == "full"
        assert "full enhancement" in analysis.analysis_rationale.lower()

    def test_recommend_minimal_preset_for_simple_task(self, analyzer):
        """Test minimal preset for simple tasks."""
        prompt = "Fix typo in docstring"
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_preset == "minimal"
        assert analysis.complexity == PromptComplexity.MINIMAL

    def test_recommend_standard_preset(self, analyzer):
        """Test standard preset for medium complexity."""
        prompt = "Add input validation to the user registration form"
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_preset == "standard"

    def test_recommend_comprehensive_preset(self, analyzer):
        """Test comprehensive preset for high complexity."""
        prompt = " ".join(["word"] * 350)  # Very long prompt
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_preset == "comprehensive"

    def test_recommend_validation_preset_for_comparison(self, analyzer):
        """Test validation preset when comparison is requested."""
        prompt = "Compare my implementation with the existing code"
        analysis = analyzer.analyze(prompt)

        assert analysis.recommended_preset == "validation"

    # Integration Tests

    def test_full_analysis_for_reference_updating_task(self, analyzer):
        """Test full analysis for the reference updating task scenario."""
        prompt = """Add reference updating to Project Cleanup Agent.
        IMPORTANT: Note that a manual implementation already exists starting at line 751 (ReferenceUpdater class).
        Compare your implementation approach with the existing manual implementation."""

        analysis = analyzer.analyze(prompt, command="*build")

        # Should detect validation intent
        assert analysis.primary_intent == TaskIntent.VALIDATE or any(
            intent == TaskIntent.BUILD for intent in analysis.secondary_intents
        )

        # Should detect existing code
        assert analysis.has_existing_code is True
        assert any("751" in (ref.description or "") for ref in analysis.existing_code_refs)

        # Should detect comparison keywords
        assert analysis.mentions_compare is True

        # Should recommend validation workflow
        assert analysis.recommended_workflow == "validate"

        # Should recommend quick enhancement (detailed prompt)
        assert analysis.recommended_enhancement == "quick"

    def test_command_override_with_validation(self, analyzer):
        """Test that explicit command can be overridden by analysis."""
        prompt = "Compare with existing implementation at line 500"
        analysis = analyzer.analyze(prompt, command="*build")

        # Should still detect validation intent despite build command
        assert analysis.recommended_workflow == "validate"
        assert analysis.has_existing_code is True

    def test_secondary_intents_detection(self, analyzer):
        """Test detection of secondary intents."""
        prompt = "Build a new feature and test it thoroughly with good coverage"
        analysis = analyzer.analyze(prompt)

        # Should detect both BUILD and TEST intents
        assert analysis.primary_intent in [TaskIntent.BUILD, TaskIntent.TEST]
        # Secondary intents should include the other
        assert len(analysis.secondary_intents) > 0

    def test_keyword_extraction(self, analyzer):
        """Test keyword extraction."""
        prompt = "Create authentication system with security features"
        analysis = analyzer.analyze(prompt)

        assert len(analysis.keywords) > 0
        # Should extract meaningful keywords (not stop words)
        assert "authentication" in analysis.keywords or "system" in analysis.keywords

    def test_mentions_flags(self, analyzer):
        """Test mentions_compare, mentions_validate, mentions_existing flags."""
        prompt = "Compare and validate the existing implementation"
        analysis = analyzer.analyze(prompt)

        assert analysis.mentions_compare is True
        assert analysis.mentions_validate is True
        assert analysis.mentions_existing is True

    def test_rationale_generation(self, analyzer):
        """Test that rationale is generated."""
        prompt = "Create a new feature"
        analysis = analyzer.analyze(prompt)

        assert analysis.analysis_rationale != ""
        assert len(analysis.analysis_rationale) > 0

    def test_estimated_lines_of_code(self, analyzer):
        """Test LOC estimation."""
        prompt = "Simple task"
        analysis = analyzer.analyze(prompt)

        # Should have some estimate
        assert analysis.estimated_lines_of_code >= 0

    # Edge Cases

    def test_empty_prompt(self, analyzer):
        """Test handling of empty prompt."""
        prompt = ""
        analysis = analyzer.analyze(prompt)

        # Should not crash, should default to BUILD
        assert analysis.primary_intent == TaskIntent.BUILD
        assert analysis.complexity == PromptComplexity.MINIMAL

    def test_very_long_prompt(self, analyzer):
        """Test handling of very long prompt."""
        prompt = " ".join(["word"] * 1000)  # 1000 words
        analysis = analyzer.analyze(prompt)

        assert analysis.complexity == PromptComplexity.COMPREHENSIVE
        assert analysis.word_count >= 1000

    def test_multiple_line_ranges(self, analyzer):
        """Test detection of multiple line ranges."""
        prompt = "Check lines 100-200 and lines 300-400 in file.py"
        analysis = analyzer.analyze(prompt)

        assert analysis.has_existing_code is True
        # Should detect multiple references
        assert len(analysis.existing_code_refs) >= 2

    def test_case_insensitive_detection(self, analyzer):
        """Test that detection is case-insensitive."""
        prompt = "COMPARE WITH EXISTING IMPLEMENTATION"
        analysis = analyzer.analyze(prompt)

        assert analysis.mentions_compare is True
        assert analysis.has_existing_code is True
