"""
Fuzzy Matching for Context7 KB cache lookups.

Provides fuzzy matching capabilities to handle variations in library/topic queries,
improving cache hit rates when exact matches aren't available.
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    try:
        from fuzzywuzzy import fuzz, process
        RAPIDFUZZ_AVAILABLE = False
    except ImportError:
        # Fallback to simple string similarity
        RAPIDFUZZ_AVAILABLE = False
        fuzz = None
        process = None


@dataclass
class FuzzyMatch:
    """Result of a fuzzy match operation."""
    library: str
    topic: str
    score: float
    original_query: str
    match_type: str  # "library", "topic", "both"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "library": self.library,
            "topic": self.topic,
            "score": self.score,
            "original_query": self.original_query,
            "match_type": self.match_type
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
                    if a[i-1] == b[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
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
        if self.use_rapidfuzz:
            # Use rapidfuzz (faster, better algorithms)
            return fuzz.ratio(s1.lower(), s2.lower()) / 100.0
        elif fuzz is not None:
            # Use fuzzywuzzy
            return fuzz.ratio(s1.lower(), s2.lower()) / 100.0
        else:
            # Fallback to simple similarity
            return self._simple_similarity(s1, s2)
    
    def find_matching_library(
        self,
        query: str,
        available_libraries: List[str],
        max_results: int = 5
    ) -> List[FuzzyMatch]:
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
                matches.append(FuzzyMatch(
                    library=library,
                    topic="",  # No topic match in library-only search
                    score=score,
                    original_query=query,
                    match_type="library"
                ))
        
        # Sort by score (descending) and return top N
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:max_results]
    
    def find_matching_topic(
        self,
        query: str,
        library: str,
        available_topics: List[str],
        max_results: int = 5
    ) -> List[FuzzyMatch]:
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
                matches.append(FuzzyMatch(
                    library=library,
                    topic=topic,
                    score=score,
                    original_query=query,
                    match_type="topic"
                ))
        
        # Sort by score (descending) and return top N
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:max_results]
    
    def find_matching_entry(
        self,
        library_query: str,
        topic_query: str,
        available_entries: List[Tuple[str, str]],  # List of (library, topic) tuples
        max_results: int = 5
    ) -> List[FuzzyMatch]:
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
                
                matches.append(FuzzyMatch(
                    library=library,
                    topic=topic,
                    score=combined_score,
                    original_query=f"{library_query}/{topic_query}",
                    match_type=match_type
                ))
        
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
        self,
        query: str,
        candidates: List[str]
    ) -> Optional[Tuple[str, float]]:
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
        
        if best_score >= self.threshold:
            return (best_match, best_score)
        
        return None

