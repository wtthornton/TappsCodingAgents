"""
Context7 Review Enhancer - Integrates Context7 lookups into review workflow.

Provides library-specific recommendations and pattern guidance from Context7.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from ...context7.agent_integration import Context7AgentHelper
from .pattern_detector import PatternMatch

logger = logging.getLogger(__name__)


@dataclass
class LibraryRecommendation:
    """Library-specific recommendations from Context7."""
    library_name: str
    best_practices: list[str]
    common_mistakes: list[str]
    usage_examples: list[str]
    source: str  # "context7" or "cache"
    cached: bool = False


@dataclass
class PatternGuidance:
    """Pattern-specific guidance from Context7."""
    pattern_name: str
    recommendations: list[str]
    best_practices: list[str]
    source: str  # "context7" or "cache"
    cached: bool = False


class Context7ReviewEnhancer:
    """
    Enhances review with Context7 library documentation and pattern guidance.
    
    Responsibilities:
    - Lookup library documentation from Context7
    - Extract best practices and common mistakes
    - Provide pattern-specific guidance
    - Cache responses to avoid duplicate lookups
    """
    
    def __init__(
        self,
        context7_helper: Context7AgentHelper,
        timeout: int = 30,
        cache_enabled: bool = True
    ):
        """
        Initialize Context7 review enhancer.
        
        Args:
            context7_helper: Context7AgentHelper instance
            timeout: Timeout for Context7 lookups (seconds)
            cache_enabled: Whether to cache Context7 responses
        """
        self.context7_helper = context7_helper
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self._cache: dict[str, LibraryRecommendation | PatternGuidance] = {}
    
    async def get_library_recommendations(
        self,
        libraries: list[str]
    ) -> dict[str, LibraryRecommendation]:
        """
        Get Context7 recommendations for detected libraries.
        
        Args:
            libraries: List of library names
            
        Returns:
            Dictionary mapping library names to LibraryRecommendation objects
        """
        if not libraries:
            return {}
        
        recommendations = {}
        
        # Batch lookups with timeout
        tasks = [
            self._lookup_library_docs(lib) for lib in libraries
        ]
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout * len(libraries)  # Total timeout for all lookups
            )
            
            for lib, result in zip(libraries, results):
                if isinstance(result, Exception):
                    logger.warning(f"Context7 lookup failed for library {lib}: {result}")
                    continue
                
                if result:
                    recommendations[lib] = result
        except asyncio.TimeoutError:
            logger.warning(f"Context7 lookup timeout for libraries: {libraries}")
        except Exception as e:
            logger.warning(f"Context7 lookup error: {e}")
        
        return recommendations
    
    async def get_pattern_guidance(
        self,
        patterns: list[PatternMatch]
    ) -> dict[str, PatternGuidance]:
        """
        Get Context7 guidance for detected patterns.
        
        Args:
            patterns: List of PatternMatch objects
            
        Returns:
            Dictionary mapping pattern names to PatternGuidance objects
        """
        if not patterns:
            return {}
        
        guidance = {}
        
        # Lookup guidance for each pattern
        for pattern in patterns:
            try:
                result = await asyncio.wait_for(
                    self._lookup_pattern_docs(pattern),
                    timeout=self.timeout
                )
                if result:
                    guidance[pattern.pattern_name] = result
            except asyncio.TimeoutError:
                logger.warning(f"Context7 lookup timeout for pattern: {pattern.pattern_name}")
            except Exception as e:
                logger.warning(f"Context7 lookup error for pattern {pattern.pattern_name}: {e}")
        
        return guidance
    
    async def _lookup_library_docs(
        self,
        library: str
    ) -> Optional[LibraryRecommendation]:
        """
        Lookup library documentation from Context7.
        
        Args:
            library: Library name
            
        Returns:
            LibraryRecommendation if successful, None otherwise
        """
        # Check cache first
        cache_key = f"library:{library}"
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, LibraryRecommendation):
                return cached
        
        try:
            # Use Context7AgentHelper to lookup docs
            # Try multiple topics to get comprehensive information
            topics = ["best-practices", "common-mistakes", "usage", "examples"]
            
            all_content = []
            for topic in topics:
                try:
                    docs = await asyncio.wait_for(
                        self.context7_helper.get_documentation(
                            library=library,
                            topic=topic,
                            use_fuzzy_match=True
                        ),
                        timeout=self.timeout
                    )
                    if docs and docs.get("content"):
                        all_content.append(docs["content"])
                except asyncio.TimeoutError:
                    logger.debug(f"Context7 lookup timeout for {library} topic {topic}")
                except Exception as e:
                    logger.debug(f"Context7 lookup error for {library} topic {topic}: {e}")
            
            if not all_content:
                # Try without topic (general documentation)
                try:
                    docs = await asyncio.wait_for(
                        self.context7_helper.get_documentation(
                            library=library,
                            topic=None,
                            use_fuzzy_match=True
                        ),
                        timeout=self.timeout
                    )
                    if docs and docs.get("content"):
                        all_content.append(docs["content"])
                except Exception as e:
                    logger.debug(f"Context7 lookup error for {library}: {e}")
            
            if not all_content:
                return None
            
            # Combine all content
            combined_content = "\n\n".join(all_content)
            
            # Extract structured data from Context7 response
            recommendation = LibraryRecommendation(
                library_name=library,
                best_practices=self._extract_best_practices(combined_content),
                common_mistakes=self._extract_common_mistakes(combined_content),
                usage_examples=self._extract_examples(combined_content),
                source="context7"
            )
            
            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = recommendation
            
            return recommendation
            
        except asyncio.TimeoutError:
            logger.warning(f"Context7 lookup timeout for library: {library}")
            return None
        except Exception as e:
            logger.warning(f"Context7 lookup failed for library {library}: {e}")
            return None
    
    async def _lookup_pattern_docs(
        self,
        pattern: PatternMatch
    ) -> Optional[PatternGuidance]:
        """
        Lookup pattern guidance from Context7.
        
        Args:
            pattern: PatternMatch object
            
        Returns:
            PatternGuidance if successful, None otherwise
        """
        # Check cache first
        cache_key = f"pattern:{pattern.pattern_name}"
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, PatternGuidance):
                return cached
        
        try:
            # Lookup pattern-specific documentation
            # Map pattern names to Context7 search terms
            search_terms = {
                "rag_system": "RAG retrieval augmented generation",
                "multi_agent": "multi-agent expert systems",
                "weighted_decision": "weighted decision making"
            }
            
            search_term = search_terms.get(pattern.pattern_name, pattern.pattern_name)
            
            docs = await asyncio.wait_for(
                self.context7_helper.get_documentation(
                    library=search_term,
                    topic="best-practices",
                    use_fuzzy_match=True
                ),
                timeout=self.timeout
            )
            
            if not docs or not docs.get("content"):
                return None
            
            content = docs["content"]
            
            # Extract guidance from Context7 response
            guidance = PatternGuidance(
                pattern_name=pattern.pattern_name,
                recommendations=self._extract_recommendations(content),
                best_practices=self._extract_best_practices(content),
                source="context7"
            )
            
            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = guidance
            
            return guidance
            
        except asyncio.TimeoutError:
            logger.warning(f"Context7 lookup timeout for pattern: {pattern.pattern_name}")
            return None
        except Exception as e:
            logger.warning(f"Context7 lookup failed for pattern {pattern.pattern_name}: {e}")
            return None
    
    def _extract_best_practices(self, content: str) -> list[str]:
        """Extract best practices from Context7 content."""
        practices = []
        
        # Look for common patterns in markdown/content
        # Best practices often appear in sections like:
        # - "Best Practices"
        # - "Recommendations"
        # - "Tips"
        # - Bullet points with "should", "recommend", "best"
        
        lines = content.split('\n')
        in_best_practices = False
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["best practice", "recommendation", "tip"]):
                in_best_practices = True
                continue
            
            if in_best_practices:
                # Extract bullet points or numbered items
                stripped = line.strip()
                if stripped.startswith(('-', '*', '•', '1.', '2.', '3.')):
                    practice = stripped.lstrip('-*•1234567890. ').strip()
                    if practice and len(practice) > 10:  # Filter out very short items
                        practices.append(practice)
                elif stripped and not stripped.startswith('#'):
                    # Non-header line in best practices section
                    if any(keyword in line_lower for keyword in ["should", "recommend", "best", "use"]):
                        practices.append(stripped)
            
            # Stop at next section
            if line.startswith('#') and in_best_practices:
                in_best_practices = False
        
        # Limit to top 5 practices
        return practices[:5]
    
    def _extract_common_mistakes(self, content: str) -> list[str]:
        """Extract common mistakes from Context7 content."""
        mistakes = []
        
        lines = content.split('\n')
        in_mistakes = False
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["common mistake", "pitfall", "avoid", "don't", "anti-pattern"]):
                in_mistakes = True
                continue
            
            if in_mistakes:
                stripped = line.strip()
                if stripped.startswith(('-', '*', '•', '1.', '2.', '3.')):
                    mistake = stripped.lstrip('-*•1234567890. ').strip()
                    if mistake and len(mistake) > 10:
                        mistakes.append(mistake)
                elif stripped and not stripped.startswith('#'):
                    if any(keyword in line_lower for keyword in ["avoid", "don't", "never", "mistake"]):
                        mistakes.append(stripped)
            
            if line.startswith('#') and in_mistakes:
                in_mistakes = False
        
        return mistakes[:5]
    
    def _extract_examples(self, content: str) -> list[str]:
        """Extract usage examples from Context7 content."""
        examples = []
        
        # Look for code blocks
        in_code_block = False
        code_block = []
        
        for line in content.split('\n'):
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if code_block:
                        examples.append('\n'.join(code_block))
                        code_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block:
                code_block.append(line)
        
        return examples[:3]  # Limit to 3 examples
    
    def _extract_recommendations(self, content: str) -> list[str]:
        """Extract recommendations from Context7 content."""
        # Similar to best practices extraction
        return self._extract_best_practices(content)
