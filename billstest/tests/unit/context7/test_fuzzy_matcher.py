"""
Unit tests for Context7 fuzzy matcher.
"""

import pytest

from tapps_agents.context7.fuzzy_matcher import FuzzyMatch, FuzzyMatcher


class TestFuzzyMatcher:
    @pytest.fixture
    def matcher(self):
        return FuzzyMatcher(threshold=0.7)

    @pytest.fixture
    def matcher_low_threshold(self):
        return FuzzyMatcher(threshold=0.5)

    def test_initialization(self):
        matcher = FuzzyMatcher(threshold=0.8)
        assert matcher.threshold == 0.8

    def test_simple_similarity_exact_match(self, matcher):
        score = matcher._simple_similarity("react", "react")
        assert score == 1.0

    def test_simple_similarity_no_match(self, matcher):
        score = matcher._simple_similarity("react", "angular")
        assert 0.0 <= score < 0.7

    def test_simple_similarity_partial_match(self, matcher):
        score = matcher._simple_similarity("react", "react-dom")
        assert score > 0.5

    def test_calculate_similarity(self, matcher):
        score = matcher._calculate_similarity("react", "react")
        assert score == 1.0

    def test_find_matching_library_exact_match(self, matcher):
        libraries = ["react", "vue", "angular"]
        matches = matcher.find_matching_library("react", libraries)
        assert len(matches) > 0
        assert matches[0].library == "react"
        assert matches[0].score >= 1.0

    def test_find_matching_library_fuzzy_match(self, matcher_low_threshold):
        libraries = ["react", "react-dom", "vue"]
        matches = matcher_low_threshold.find_matching_library("react-dom", libraries)
        assert len(matches) > 0
        assert any(m.library == "react-dom" for m in matches)

    def test_find_matching_library_no_match(self, matcher):
        libraries = ["react", "vue", "angular"]
        matches = matcher.find_matching_library("python", libraries)
        assert len(matches) == 0

    def test_find_matching_library_max_results(self, matcher_low_threshold):
        libraries = ["react", "react-dom", "react-router", "vue", "vuex"]
        matches = matcher_low_threshold.find_matching_library(
            "react", libraries, max_results=2
        )
        assert len(matches) <= 2

    def test_find_matching_topic_exact_match(self, matcher):
        topics = ["hooks", "routing", "state"]
        matches = matcher.find_matching_topic("hooks", "react", topics)
        assert len(matches) > 0
        assert matches[0].topic == "hooks"
        assert matches[0].score >= 1.0

    def test_find_matching_topic_fuzzy_match(self, matcher_low_threshold):
        topics = ["hooks", "hook-system", "routing"]
        matches = matcher_low_threshold.find_matching_topic("hook", "react", topics)
        assert len(matches) > 0
        assert any(m.topic in ["hooks", "hook-system"] for m in matches)

    def test_find_matching_entry_exact_match(self, matcher):
        entries = [("react", "hooks"), ("vue", "components"), ("angular", "routing")]
        matches = matcher.find_matching_entry("react", "hooks", entries)
        assert len(matches) > 0
        assert matches[0].library == "react"
        assert matches[0].topic == "hooks"
        assert matches[0].match_type == "both"

    def test_find_matching_entry_partial_match(self, matcher_low_threshold):
        entries = [
            ("react", "hooks"),
            ("react-dom", "rendering"),
            ("vue", "components"),
        ]
        matches = matcher_low_threshold.find_matching_entry("react", "hook", entries)
        assert len(matches) > 0
        assert matches[0].library in ["react", "react-dom"]

    def test_find_matching_entry_library_only_match(self, matcher_low_threshold):
        entries = [("react", "hooks"), ("react", "routing"), ("vue", "components")]
        matches = matcher_low_threshold.find_matching_entry(
            "react", "unknown-topic", entries
        )
        # Should still match on library even if topic doesn't match
        assert len(matches) > 0

    def test_is_match_exact(self, matcher):
        assert matcher.is_match("react", "react") is True

    def test_is_match_fuzzy(self, matcher_low_threshold):
        assert matcher_low_threshold.is_match("react", "react-dom") is True

    def test_is_match_no_match(self, matcher):
        assert matcher.is_match("react", "angular") is False

    def test_get_best_match_exact(self, matcher):
        candidates = ["react", "vue", "angular"]
        result = matcher.get_best_match("react", candidates)
        assert result is not None
        assert result[0] == "react"
        assert result[1] >= 1.0

    def test_get_best_match_no_match(self, matcher):
        candidates = ["react", "vue", "angular"]
        result = matcher.get_best_match("python", candidates)
        assert result is None

    def test_get_best_match_fuzzy(self, matcher_low_threshold):
        candidates = ["react", "react-dom", "vue"]
        result = matcher_low_threshold.get_best_match("react-dom", candidates)
        assert result is not None
        assert result[0] == "react-dom"

    def test_fuzzy_match_to_dict(self, matcher):
        match = FuzzyMatch(
            library="react",
            topic="hooks",
            score=0.95,
            original_query="react/hooks",
            match_type="both",
        )
        match_dict = match.to_dict()
        assert match_dict["library"] == "react"
        assert match_dict["topic"] == "hooks"
        assert match_dict["score"] == 0.95
        assert match_dict["match_type"] == "both"

    def test_find_matching_library_empty_input(self, matcher):
        matches = matcher.find_matching_library("", ["react", "vue"])
        assert len(matches) == 0

        matches = matcher.find_matching_library("react", [])
        assert len(matches) == 0

    def test_find_matching_topic_empty_input(self, matcher):
        matches = matcher.find_matching_topic("", "react", ["hooks"])
        assert len(matches) == 0

        matches = matcher.find_matching_topic("hooks", "react", [])
        assert len(matches) == 0

    def test_find_matching_entry_empty_input(self, matcher):
        matches = matcher.find_matching_entry("", "hooks", [("react", "hooks")])
        assert len(matches) == 0

        matches = matcher.find_matching_entry("react", "hooks", [])
        assert len(matches) == 0

    def test_case_insensitive_matching(self, matcher):
        libraries = ["React", "Vue", "Angular"]
        matches = matcher.find_matching_library("react", libraries)
        assert len(matches) > 0

    def test_combined_score_weighting(self, matcher_low_threshold):
        """Test that combined scores properly weight library and topic."""
        entries = [("react", "hooks"), ("react", "routing"), ("vue", "hooks")]
        matches = matcher_low_threshold.find_matching_entry("react", "hooks", entries)

        # Should prioritize exact library+topic matches
        assert len(matches) > 0
        assert matches[0].library == "react"
        assert matches[0].topic == "hooks"
