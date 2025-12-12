"""
Fuzzy Matching for Context7 KB cache lookups.

Provides fuzzy matching capabilities to handle variations in library/topic queries,
improving cache hit rates when exact matches aren't available.
"""

from dataclasses import dataclass
from typing import Any

fuzz: Any | None = None
process: Any | None = None

try:
    from rapidfuzz import fuzz as _rf_fuzz
    from rapidfuzz import process as _rf_process

    fuzz = _rf_fuzz
    process = _rf_process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    try:
        from fuzzywuzzy import fuzz as _fw_fuzz
        from fuzzywuzzy import process as _fw_process

        fuzz = _fw_fuzz
        process = _fw_process
        RAPIDFUZZ_AVAILABLE = False
    except ImportError:
        # Fallback to simple string similarity
        RAPIDFUZZ_AVAILABLE = False


@dataclass
class FuzzyMatch:
    """Result of a fuzzy match operation."""

    library: str
    topic: str
    score: float
    original_query: str
    match_type: str  # "library", "topic", "both"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "library": self.library,
            "topic": self.topic,
            "score": self.score,
            "original_query": self.original_query,
            "match_type": self.match_type,
        }


class FuzzyMatcher:
    """Fuzzy matching for Context7 KB cache entries."""

    def __init__(self, threshold: float = 0.7):
        """
        Initialize fuzzy matcher.

        Args:
            threshold: Minimum similarity score (0.0-1.0) to consider a match
        """
        self.threshold = threshold
        self.use_rapidfuzz = RAPIDFUZZ_AVAILABLE

    def _simple_similarity(self, s1: str, s2: str) -> float:
        """
        Simple string similarity using longest common subsequence.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not s1 or not s2:
            return 0.0

        s1_lower = s1.lower()
        s2_lower = s2.lower()

        if s1_lower == s2_lower:
            return 1.0

        # Calculate longest common subsequence
        def lcs_length(a: str, b: str) -> int:
            m, n = len(a), len(b)
            dp = [[0] * (n + 1) for _ in range(m + 1)]

            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if a[i - 1] == b[j - 1]:
                        dp[i][j] = dp[i - 1][j - 1] + 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

            return dp[m][n]

        lcs = lcs_length(s1_lower, s2_lower)
        max_len = max(len(s1_lower), len(s2_lower))

        return lcs / max_len if max_len > 0 else 0.0

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        fuzz_impl = fuzz
        if self.use_rapidfuzz and fuzz_impl is not None:
            # Use rapidfuzz (faster, better algorithms)
            return fuzz_impl.ratio(s1.lower(), s2.lower()) / 100.0
        elif fuzz_impl is not None:
            # Use fuzzywuzzy
            return fuzz_impl.ratio(s1.lower(), s2.lower()) / 100.0
        else:
            # Fallback to simple similarity
            return self._simple_similarity(s1, s2)

    def find_matching_library(
        self, query: str, available_libraries: list[str], max_results: int = 5
    ) -> list[FuzzyMatch]:
        """
        Find libraries that match the query using fuzzy matching.

        Args:
            query: Library name to search for
            available_libraries: List of available library names
            max_results: Maximum number of results to return

        Returns:
            List of FuzzyMatch objects, sorted by score (highest first)
        """
        if not query or not available_libraries:
            return []

        matches = []

        for library in available_libraries:
            score = self._calculate_similarity(query, library)

            if score >= self.threshold:
                matches.append(
                    FuzzyMatch(
                        library=library,
                        topic="",  # No topic match in library-only search
                        score=score,
                        original_query=query,
                        match_type="library",
                    )
                )

        # Sort by score (descending) and return top N
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:max_results]

    def find_matching_topic(
        self,
        query: str,
        library: str,
        available_topics: list[str],
        max_results: int = 5,
    ) -> list[FuzzyMatch]:
        """
        Find topics that match the query using fuzzy matching.

        Args:
            query: Topic name to search for
            library: Library name (for context)
            available_topics: List of available topic names for the library
            max_results: Maximum number of results to return

        Returns:
            List of FuzzyMatch objects, sorted by score (highest first)
        """
        if not query or not available_topics:
            return []

        matches = []

        for topic in available_topics:
            score = self._calculate_similarity(query, topic)

            if score >= self.threshold:
                matches.append(
                    FuzzyMatch(
                        library=library,
                        topic=topic,
                        score=score,
                        original_query=query,
                        match_type="topic",
                    )
                )

        # Sort by score (descending) and return top N
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:max_results]

    def find_matching_entry(
        self,
        library_query: str,
        topic_query: str,
        available_entries: list[tuple[str, str]],  # List of (library, topic) tuples
        max_results: int = 5,
    ) -> list[FuzzyMatch]:
        """
        Find library/topic entries that match both queries using fuzzy matching.

        Args:
            library_query: Library name to search for
            topic_query: Topic name to search for
            available_entries: List of (library, topic) tuples
            max_results: Maximum number of results to return

        Returns:
            List of FuzzyMatch objects, sorted by combined score (highest first)
        """
        if not library_query or not topic_query or not available_entries:
            return []

        matches = []

        for library, topic in available_entries:
            lib_score = self._calculate_similarity(library_query, library)
            topic_score = self._calculate_similarity(topic_query, topic)

            # Combined score (weighted average: 60% library, 40% topic)
            combined_score = (lib_score * 0.6) + (topic_score * 0.4)

            if combined_score >= self.threshold:
                match_type = "both"
                if lib_score >= self.threshold and topic_score < self.threshold:
                    match_type = "library"
                elif topic_score >= self.threshold and lib_score < self.threshold:
                    match_type = "topic"

                matches.append(
                    FuzzyMatch(
                        library=library,
                        topic=topic,
                        score=combined_score,
                        original_query=f"{library_query}/{topic_query}",
                        match_type=match_type,
                    )
                )

        # Sort by score (descending) and return top N
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:max_results]

    def is_match(self, query: str, candidate: str) -> bool:
        """
        Check if a candidate string matches the query above the threshold.

        Args:
            query: Query string
            candidate: Candidate string to check

        Returns:
            True if similarity score >= threshold
        """
        score = self._calculate_similarity(query, candidate)
        return score >= self.threshold

    def get_best_match(
        self, query: str, candidates: list[str]
    ) -> tuple[str, float] | None:
        """
        Get the best matching candidate for a query.

        Args:
            query: Query string
            candidates: List of candidate strings

        Returns:
            Tuple of (best_match, score) or None if no match above threshold
        """
        if not query or not candidates:
            return None

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            score = self._calculate_similarity(query, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= self.threshold and best_match is not None:
            return (best_match, best_score)

        return None

    # ---------------------------------------------------------------------
    # Compatibility helpers (contract stability)
    #
    # Older callers (and some CLI flows) expect a single entry-point method
    # named `find_best_match` that can accept a cache index object. Keep this
    # as a thin wrapper around the more explicit `find_matching_*` methods.
    # ---------------------------------------------------------------------

    def find_best_match(
        self,
        query: str,
        topic: str | None,
        cache_index: Any,
        max_results: int = 5,
    ) -> list[FuzzyMatch]:
        """
        Find best matches for a query across a cache index.

        Args:
            query: Query string (library/topic search term)
            topic: Optional topic; when provided we prefer matching entries
            cache_index: Cache index object with `.libraries` mapping
            max_results: Maximum results to return

        Returns:
            List of FuzzyMatch results sorted by score desc.
        """
        libraries_map = getattr(cache_index, "libraries", {}) or {}
        library_names = list(libraries_map.keys())

        matches: list[FuzzyMatch] = []

        # If a topic is provided, treat this as a (library/topic) entry match.
        if topic:
            available_entries: list[tuple[str, str]] = []
            for lib_name, lib_data in libraries_map.items():
                topics = (lib_data or {}).get("topics", {}) or {}
                for topic_name in topics.keys():
                    available_entries.append((lib_name, topic_name))
            return self.find_matching_entry(
                library_query=query,
                topic_query=topic,
                available_entries=available_entries,
                max_results=max_results,
            )

        # Otherwise, search both library names and topic names.
        matches.extend(self.find_matching_library(query, library_names, max_results))

        for lib_name, lib_data in libraries_map.items():
            topics = (lib_data or {}).get("topics", {}) or {}
            topic_names = list(topics.keys())
            matches.extend(
                self.find_matching_topic(query, lib_name, topic_names, max_results)
            )

        # Deduplicate by (library, topic, match_type) keeping best score.
        best: dict[tuple[str, str, str], FuzzyMatch] = {}
        for m in matches:
            key = (m.library, m.topic, m.match_type)
            existing = best.get(key)
            if existing is None or m.score > existing.score:
                best[key] = m

        out = sorted(best.values(), key=lambda x: x.score, reverse=True)
        return out[:max_results]
