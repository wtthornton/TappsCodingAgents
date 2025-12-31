"""
Pattern Detector - Detects domain-specific code patterns.

Supported patterns:
- RAG (Retrieval Augmented Generation) systems
- Multi-agent systems
- Weighted decision-making algorithms
"""

import re
from dataclasses import dataclass
from typing import Optional

logger = __import__("logging").getLogger(__name__)


@dataclass
class PatternMatch:
    """Represents a detected code pattern."""
    pattern_name: str  # "rag_system", "multi_agent", "weighted_decision"
    confidence: float  # 0.0 to 1.0
    indicators: list[str]  # Keywords that triggered detection
    line_numbers: list[int]  # Line numbers where indicators were found


# Pattern indicators
RAG_INDICATORS = [
    "vectorstore", "embedding", "retrieval", "rag",
    "langchain.vectorstores", "faiss", "chroma", "pinecone",
    "vector_store", "vector_db", "semantic_search"
]

MULTI_AGENT_INDICATORS = [
    "agent", "orchestrator", "multi-agent", "agent_system",
    "agent_network", "agent_coordination", "multi_agent"
]

WEIGHTED_DECISION_INDICATORS = [
    "weighted", "scoring", "decision", "weight", "score",
    "weighted_score", "weighted_decision", "weighted_average",
    "weighted_sum", "weighted_combination"
]


class PatternDetector:
    """
    Detects domain-specific code patterns.
    
    Supported patterns:
    - RAG (Retrieval Augmented Generation) systems
    - Multi-agent systems
    - Weighted decision-making algorithms
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        case_sensitive: bool = False
    ):
        """
        Initialize pattern detector.
        
        Args:
            confidence_threshold: Minimum confidence to report pattern (0.0-1.0)
            case_sensitive: Whether pattern matching is case-sensitive
        """
        self.confidence_threshold = confidence_threshold
        self.case_sensitive = case_sensitive
    
    def detect_patterns(self, code: str) -> list[PatternMatch]:
        """
        Detect all patterns in code.
        
        Args:
            code: Source code as string
            
        Returns:
            List of PatternMatch objects (filtered by confidence threshold)
        """
        patterns = []
        
        # Detect RAG pattern
        rag_match = self.detect_rag_pattern(code)
        if rag_match and rag_match.confidence >= self.confidence_threshold:
            patterns.append(rag_match)
        
        # Detect multi-agent pattern
        multi_agent_match = self.detect_multi_agent_pattern(code)
        if multi_agent_match and multi_agent_match.confidence >= self.confidence_threshold:
            patterns.append(multi_agent_match)
        
        # Detect weighted decision pattern
        weighted_match = self.detect_weighted_decision_pattern(code)
        if weighted_match and weighted_match.confidence >= self.confidence_threshold:
            patterns.append(weighted_match)
        
        return patterns
    
    def detect_rag_pattern(self, code: str) -> Optional[PatternMatch]:
        """
        Detect RAG (Retrieval Augmented Generation) system patterns.
        
        Indicators:
        - vectorstore, embedding, retrieval, rag
        - langchain.vectorstores, faiss, chroma
        
        Args:
            code: Source code as string
            
        Returns:
            PatternMatch if detected, None otherwise
        """
        found_indicators, line_numbers = self._find_indicators(code, RAG_INDICATORS)
        
        if not found_indicators:
            return None
        
        confidence = self._calculate_confidence(RAG_INDICATORS, found_indicators)
        
        return PatternMatch(
            pattern_name="rag_system",
            confidence=confidence,
            indicators=found_indicators,
            line_numbers=line_numbers
        )
    
    def detect_multi_agent_pattern(self, code: str) -> Optional[PatternMatch]:
        """
        Detect multi-agent system patterns.
        
        Indicators:
        - agent, orchestrator, multi-agent, agent_system
        
        Args:
            code: Source code as string
            
        Returns:
            PatternMatch if detected, None otherwise
        """
        found_indicators, line_numbers = self._find_indicators(code, MULTI_AGENT_INDICATORS)
        
        if not found_indicators:
            return None
        
        confidence = self._calculate_confidence(MULTI_AGENT_INDICATORS, found_indicators)
        
        return PatternMatch(
            pattern_name="multi_agent",
            confidence=confidence,
            indicators=found_indicators,
            line_numbers=line_numbers
        )
    
    def detect_weighted_decision_pattern(self, code: str) -> Optional[PatternMatch]:
        """
        Detect weighted decision-making patterns.
        
        Indicators:
        - weighted, scoring, decision, weight, score
        
        Args:
            code: Source code as string
            
        Returns:
            PatternMatch if detected, None otherwise
        """
        found_indicators, line_numbers = self._find_indicators(code, WEIGHTED_DECISION_INDICATORS)
        
        if not found_indicators:
            return None
        
        confidence = self._calculate_confidence(WEIGHTED_DECISION_INDICATORS, found_indicators)
        
        return PatternMatch(
            pattern_name="weighted_decision",
            confidence=confidence,
            indicators=found_indicators,
            line_numbers=line_numbers
        )
    
    def _find_indicators(self, code: str, indicators: list[str]) -> tuple[list[str], list[int]]:
        """
        Find indicators in code and return found indicators with line numbers.
        
        Args:
            code: Source code as string
            indicators: List of indicator keywords to search for
            
        Returns:
            Tuple of (found_indicators, line_numbers)
        """
        found_indicators = []
        line_numbers = []
        lines = code.split('\n')
        
        for indicator in indicators:
            # Create regex pattern with word boundaries to avoid false positives
            if self.case_sensitive:
                pattern = rf'\b{re.escape(indicator)}\b'
            else:
                pattern = rf'\b{re.escape(indicator)}\b'
                code_lower = code.lower()
                indicator_lower = indicator.lower()
            
            # Search for indicator
            for line_num, line in enumerate(lines, start=1):
                search_line = line if self.case_sensitive else line.lower()
                search_indicator = indicator if self.case_sensitive else indicator.lower()
                
                if search_indicator in search_line:
                    # Use regex to ensure word boundary match
                    if re.search(rf'\b{re.escape(search_indicator)}\b', search_line, re.IGNORECASE if not self.case_sensitive else 0):
                        if indicator not in found_indicators:
                            found_indicators.append(indicator)
                        if line_num not in line_numbers:
                            line_numbers.append(line_num)
        
        return found_indicators, sorted(line_numbers)
    
    def _calculate_confidence(self, indicators: list[str], found: list[str]) -> float:
        """
        Calculate confidence score based on found indicators.
        
        Args:
            indicators: All possible indicators for the pattern
            found: Indicators that were found in code
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not found:
            return 0.0
        
        # Base confidence = (found_indicators / total_indicators) * 0.8
        base_confidence = len(found) / len(indicators) * 0.8
        
        # Bonus for multiple matches = min(found_count / 3.0, 0.2)
        multiple_bonus = min(len(found) / 3.0, 0.2)
        
        # Final confidence capped at 1.0
        return min(base_confidence + multiple_bonus, 1.0)
