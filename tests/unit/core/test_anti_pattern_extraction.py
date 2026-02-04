"""
Unit tests for anti-pattern extraction functionality.
"""


from tapps_agents.core.agent_learning import (
    AntiPatternExtractor,
    CodePattern,
    FailureModeAnalyzer,
    NegativeFeedbackHandler,
)


class TestAntiPatternExtractor:
    """Test AntiPatternExtractor functionality."""

    def test_init(self):
        """Test AntiPatternExtractor initialization."""
        extractor = AntiPatternExtractor()
        assert extractor is not None
        assert extractor.max_quality_threshold == 0.7
        assert hasattr(extractor, "security_scanner")

    def test_extract_anti_patterns_from_failure(self):
        """Test extracting anti-patterns from failed code."""
        extractor = AntiPatternExtractor()

        failed_code = """
def bad_function():
    eval('unsafe')
    return None
"""

        anti_patterns = extractor.extract_anti_patterns(
            code=failed_code,
            quality_score=0.3,  # Low quality
            task_id="test_task_1",
            failure_reasons=["Security issue", "Low quality"],
        )

        assert len(anti_patterns) > 0
        assert all(p.is_anti_pattern for p in anti_patterns)
        assert all(p.success_rate == 0.0 for p in anti_patterns)

    def test_extract_anti_patterns_high_quality(self):
        """Test that high-quality code doesn't generate anti-patterns."""
        extractor = AntiPatternExtractor()

        good_code = """
def good_function():
    return True
"""

        anti_patterns = extractor.extract_anti_patterns(
            code=good_code,
            quality_score=0.9,  # High quality
            task_id="test_task_2",
            failure_reasons=[],
        )

        # Should not extract anti-patterns from high-quality code
        assert len(anti_patterns) == 0

    def test_extract_from_failure(self):
        """Test extract_from_failure method."""
        extractor = AntiPatternExtractor()

        failed_code = "def broken():\n    pass"

        anti_patterns = extractor.extract_from_failure(
            code=failed_code,
            task_id="test_task_3",
            failure_reasons=["Task failed"],
            quality_score=0.0,
        )

        assert isinstance(anti_patterns, list)
        assert all(p.is_anti_pattern for p in anti_patterns)

    def test_extract_from_rejection(self):
        """Test extract_from_rejection method."""
        extractor = AntiPatternExtractor()

        rejected_code = "def rejected():\n    pass"

        anti_patterns = extractor.extract_from_rejection(
            code=rejected_code,
            task_id="test_task_4",
            rejection_reason="User didn't like this approach",
            quality_score=0.5,
        )

        assert isinstance(anti_patterns, list)
        assert all(p.is_anti_pattern for p in anti_patterns)
        assert any("User rejection" in reason for p in anti_patterns for reason in p.failure_reasons)

    def test_get_anti_patterns_for_context(self):
        """Test retrieving anti-patterns for context."""
        extractor = AntiPatternExtractor()

        # Add some anti-patterns
        anti_pattern = CodePattern(
            pattern_id="anti_test_1",
            pattern_type="function",
            code_snippet="def bad():\n    pass",
            context="Bad function",
            quality_score=0.3,
            usage_count=1,
            success_rate=0.0,
            learned_from=["task_1"],
            is_anti_pattern=True,
            failure_reasons=["Failed"],
            rejection_count=2,
        )
        extractor.anti_patterns["anti_test_1"] = anti_pattern

        patterns = extractor.get_anti_patterns_for_context(
            context="test", limit=5
        )

        assert len(patterns) > 0
        assert all(p.is_anti_pattern for p in patterns)


class TestNegativeFeedbackHandler:
    """Test NegativeFeedbackHandler functionality."""

    def test_init(self):
        """Test NegativeFeedbackHandler initialization."""
        handler = NegativeFeedbackHandler()
        assert handler is not None
        assert hasattr(handler, "anti_pattern_extractor")
        assert len(handler.rejections) == 0
        assert len(handler.corrections) == 0

    def test_record_rejection(self):
        """Test recording a rejection."""
        handler = NegativeFeedbackHandler()

        rejected_code = "def rejected():\n    pass"

        anti_patterns = handler.record_rejection(
            code=rejected_code,
            task_id="task_1",
            reason="Not secure enough",
            quality_score=0.4,
        )

        assert len(handler.rejections) == 1
        assert handler.rejections[0]["task_id"] == "task_1"
        assert handler.rejections[0]["reason"] == "Not secure enough"
        assert isinstance(anti_patterns, list)

    def test_record_correction(self):
        """Test recording a correction."""
        handler = NegativeFeedbackHandler()

        original_code = "def bad():\n    eval('unsafe')"
        corrected_code = "def good():\n    return True"

        anti_patterns, patterns = handler.record_correction(
            original_code=original_code,
            corrected_code=corrected_code,
            task_id="task_2",
            correction_reason="Fixed security issue",
        )

        assert len(handler.corrections) == 1
        assert handler.corrections[0]["task_id"] == "task_2"
        assert isinstance(anti_patterns, list)

    def test_extract_anti_patterns_from_feedback(self):
        """Test extracting anti-patterns from feedback."""
        handler = NegativeFeedbackHandler()

        code = "def problematic():\n    pass"
        feedback = "This code has performance issues"

        anti_patterns = handler.extract_anti_patterns_from_feedback(
            code=code,
            task_id="task_3",
            feedback=feedback,
        )

        assert isinstance(anti_patterns, list)
        assert all(p.is_anti_pattern for p in anti_patterns)

    def test_get_anti_patterns_for_context(self):
        """Test getting anti-patterns for context."""
        handler = NegativeFeedbackHandler()

        # Add an anti-pattern through rejection
        handler.record_rejection(
            code="def bad():\n    pass",
            task_id="task_4",
            reason="Bad pattern",
            quality_score=0.3,
        )

        patterns = handler.get_anti_patterns_for_context(
            context="test", limit=5
        )

        assert isinstance(patterns, list)


class TestFailureModeAnalyzer:
    """Test FailureModeAnalyzer functionality."""

    def test_init(self):
        """Test FailureModeAnalyzer initialization."""
        analyzer = FailureModeAnalyzer()
        assert analyzer is not None
        assert len(analyzer.failure_modes) == 0

    def test_analyze_failure_syntax_error(self):
        """Test analyzing a syntax error failure."""
        analyzer = FailureModeAnalyzer()

        result = analyzer.analyze_failure(
            code="def broken(\n    pass",  # Syntax error
            task_id="task_1",
            failure_reasons=["SyntaxError: invalid syntax"],
            quality_scores=None,
        )

        assert result["failure_mode"] == "syntax_error"
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    def test_analyze_failure_security_issue(self):
        """Test analyzing a security issue failure."""
        analyzer = FailureModeAnalyzer()

        result = analyzer.analyze_failure(
            code="eval('unsafe')",
            task_id="task_2",
            failure_reasons=["Security vulnerability detected"],
            quality_scores={"security_score": 3.0},
        )

        assert result["failure_mode"] == "security_issue"
        assert "security" in " ".join(result["suggestions"]).lower()

    def test_analyze_failure_performance_issue(self):
        """Test analyzing a performance issue failure."""
        analyzer = FailureModeAnalyzer()

        result = analyzer.analyze_failure(
            code="for i in range(1000000):\n    for j in range(1000000):\n        pass",
            task_id="task_3",
            failure_reasons=["Timeout: code too slow"],
            quality_scores=None,
        )

        assert result["failure_mode"] == "performance_issue"
        assert "performance" in " ".join(result["suggestions"]).lower()

    def test_identify_failure_mode(self):
        """Test failure mode identification."""
        analyzer = FailureModeAnalyzer()

        # Test syntax error
        mode = analyzer.identify_failure_mode(
            failure_reasons=["SyntaxError occurred"],
            quality_scores=None,
        )
        assert mode == "syntax_error"

        # Test security issue
        mode = analyzer.identify_failure_mode(
            failure_reasons=["Security vulnerability"],
            quality_scores={"security_score": 2.0},
        )
        assert mode == "security_issue"

        # Test logic error
        mode = analyzer.identify_failure_mode(
            failure_reasons=["Logic error: incorrect calculation"],
            quality_scores=None,
        )
        assert mode == "logic_error"

    def test_get_common_failure_modes(self):
        """Test getting common failure modes."""
        analyzer = FailureModeAnalyzer()

        # Add some failures
        analyzer.analyze_failure(
            code="def bad():\n    pass",
            task_id="task_1",
            failure_reasons=["Syntax error"],
            quality_scores=None,
        )
        analyzer.analyze_failure(
            code="def bad2():\n    pass",
            task_id="task_2",
            failure_reasons=["Syntax error"],
            quality_scores=None,
        )

        common_modes = analyzer.get_common_failure_modes(limit=5)

        assert len(common_modes) > 0
        assert common_modes[0]["mode"] == "syntax_error"
        assert common_modes[0]["count"] >= 2

    def test_suggest_prevention(self):
        """Test prevention suggestions."""
        analyzer = FailureModeAnalyzer()

        suggestions = analyzer.suggest_prevention(
            failure_mode="syntax_error",
            failure_reasons=["Syntax error"],
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("syntax" in s.lower() for s in suggestions)

