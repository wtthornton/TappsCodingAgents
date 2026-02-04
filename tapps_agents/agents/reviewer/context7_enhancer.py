"""
Context7 Review Enhancer - Integrates Context7 lookups into review workflow.

Provides library-specific recommendations and pattern guidance from Context7.
"""

import asyncio
import logging
from dataclasses import dataclass

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
            
            for lib, result in zip(libraries, results, strict=False):
                if isinstance(result, Exception):
                    logger.warning(f"Context7 lookup failed for library {lib}: {result}")
                    continue
                
                if result:
                    recommendations[lib] = result
        except TimeoutError:
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
            except TimeoutError:
                logger.warning(f"Context7 lookup timeout for pattern: {pattern.pattern_name}")
            except Exception as e:
                logger.warning(f"Context7 lookup error for pattern {pattern.pattern_name}: {e}")
        
        return guidance
    
    async def _lookup_library_docs(
        self,
        library: str
    ) -> LibraryRecommendation | None:
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
                except TimeoutError:
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
            
        except TimeoutError:
            logger.warning(f"Context7 lookup timeout for library: {library}")
            return None
        except Exception as e:
            logger.warning(f"Context7 lookup failed for library {library}: {e}")
            return None
    
    async def _lookup_pattern_docs(
        self,
        pattern: PatternMatch
    ) -> PatternGuidance | None:
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
            
        except TimeoutError:
            logger.warning(f"Context7 lookup timeout for pattern: {pattern.pattern_name}")
            return None
        except Exception as e:
            logger.warning(f"Context7 lookup failed for pattern {pattern.pattern_name}: {e}")
            return None
    
    def _extract_best_practices(self, content: str) -> list[str]:
        """
        Extract best practices from Context7 content with enhanced parsing.
        
        Enhanced approach:
        1. Try to find section by header (## Best Practices, etc.)
        2. Extract from section with better parsing
        3. Fallback to keyword-based extraction if section not found
        """
        try:
            # Enhanced: Try to find section by header
            section = self._find_section_by_header(
                content, 
                ["best practice", "best practices", "recommendation", "recommendations", "tip", "tips"]
            )
            
            if section:
                # Extract from section
                practices = self._extract_from_section(section, content)
                return self._filter_and_limit(practices, max_items=5)
        except Exception as e:
            logger.debug(f"Enhanced extraction failed, using fallback: {e}")
        
        # Fallback to simple keyword-based extraction
        return self._extract_best_practices_simple(content)
    
    def _extract_best_practices_simple(self, content: str) -> list[str]:
        """Simple keyword-based extraction (fallback method)."""
        practices = []
        lines = content.split('\n')
        in_best_practices = False
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["best practice", "recommendation", "tip"]):
                in_best_practices = True
                continue
            
            if in_best_practices:
                stripped = line.strip()
                if stripped.startswith(('-', '*', '•', '1.', '2.', '3.')):
                    practice = stripped.lstrip('-*•1234567890. ').strip()
                    if practice and len(practice) > 10:
                        practices.append(practice)
                elif stripped and not stripped.startswith('#'):
                    if any(keyword in line_lower for keyword in ["should", "recommend", "best", "use"]):
                        practices.append(stripped)
            
            if line.startswith('#') and in_best_practices:
                in_best_practices = False
        
        return practices[:5]
    
    def _extract_common_mistakes(self, content: str) -> list[str]:
        """
        Extract common mistakes from Context7 content with enhanced parsing.
        
        Enhanced approach:
        1. Try to find section by header
        2. Extract from section with better parsing
        3. Fallback to keyword-based extraction
        """
        try:
            # Enhanced: Try to find section by header
            section = self._find_section_by_header(
                content,
                ["common mistake", "common mistakes", "pitfall", "pitfalls", "avoid", "anti-pattern", "anti-patterns"]
            )
            
            if section:
                # Extract from section
                mistakes = self._extract_from_section(section, content)
                return self._filter_and_limit(mistakes, max_items=5)
        except Exception as e:
            logger.debug(f"Enhanced extraction failed, using fallback: {e}")
        
        # Fallback to simple keyword-based extraction
        return self._extract_common_mistakes_simple(content)
    
    def _extract_common_mistakes_simple(self, content: str) -> list[str]:
        """Simple keyword-based extraction (fallback method)."""
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
        """
        Extract usage examples from Context7 content with enhanced parsing.
        
        Enhanced approach:
        1. Try to find "Examples" section by header
        2. Extract code blocks from section if found
        3. Fallback to extracting all code blocks
        """
        try:
            # Enhanced: Try to find "Examples" section
            section = self._find_section_by_header(
                content,
                ["example", "examples", "usage", "code example", "code examples"]
            )
            
            if section:
                # Extract code blocks from section
                examples = self._extract_code_blocks_from_section(section, content)
                return examples[:3]
        except Exception as e:
            logger.debug(f"Enhanced extraction failed, using fallback: {e}")
        
        # Fallback: Extract all code blocks
        return self._extract_all_code_blocks(content)[:3]
    
    def _extract_recommendations(self, content: str) -> list[str]:
        """Extract recommendations from Context7 content."""
        # Similar to best practices extraction
        return self._extract_best_practices(content)
    
    def _find_section_by_header(
        self, 
        content: str, 
        keywords: list[str]
    ) -> tuple[int, int] | None:
        """
        Find section by header keywords.
        
        Enhanced section detection that looks for markdown headers (##, ###, etc.)
        containing the specified keywords.
        
        Args:
            content: Markdown content
            keywords: List of keywords to search for in headers
            
        Returns:
            Tuple of (start_line, end_line) if found, None otherwise
        """
        lines = content.split('\n')
        in_section = False
        start_line = None
        current_level = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if line is a header (starts with #)
            if stripped.startswith('#'):
                # Extract header level and text
                header_level = len(stripped) - len(stripped.lstrip('#'))
                header_text = stripped.lstrip('#').strip().lower()
                
                # Check if header contains any keyword
                if any(keyword in header_text for keyword in keywords):
                    in_section = True
                    start_line = i
                    current_level = header_level
                elif in_section:
                    # Found next header at same or higher level, end of section
                    if header_level <= current_level:
                        return (start_line, i - 1)
        
        # If we're still in a section at the end, return to end of content
        if in_section:
            return (start_line, len(lines) - 1)
        
        return None
    
    def _extract_from_section(
        self, 
        section: tuple[int, int], 
        content: str
    ) -> list[str]:
        """
        Extract content from a section.
        
        Enhanced extraction that handles:
        - List items (bulleted and numbered)
        - Nested lists
        - Paragraph text
        
        Args:
            section: Tuple of (start_line, end_line)
            content: Full markdown content
            
        Returns:
            List of extracted items
        """
        lines = content.split('\n')
        start, end = section
        section_lines = lines[start:end + 1]
        
        items = []
        for line in section_lines:
            stripped = line.strip()
            
            # Skip empty lines and headers
            if not stripped or stripped.startswith('#'):
                continue
            
            # Extract list items (bulleted)
            if stripped.startswith(('-', '*', '•')):
                item = stripped.lstrip('-*• ').strip()
                if item and len(item) > 10:
                    items.append(item)
            # Extract numbered list items
            elif stripped and stripped[0].isdigit() and '.' in stripped[:5]:
                # Handle numbered lists: "1. Item", "2. Item", etc.
                parts = stripped.split('.', 1)
                if len(parts) == 2:
                    item = parts[1].strip()
                    if item and len(item) > 10:
                        items.append(item)
            # Extract substantial paragraph text
            elif stripped and not stripped.startswith('```') and len(stripped) > 20:
                # Only add if it looks like a recommendation/practice
                if any(keyword in stripped.lower() for keyword in 
                       ["should", "recommend", "best", "use", "avoid", "don't", "never"]):
                    items.append(stripped)
        
        return items
    
    def _extract_code_blocks_from_section(
        self, 
        section: tuple[int, int], 
        content: str
    ) -> list[str]:
        """
        Extract code blocks from a section.
        
        Args:
            section: Tuple of (start_line, end_line)
            content: Full markdown content
            
        Returns:
            List of code block contents
        """
        lines = content.split('\n')
        start, end = section
        section_content = '\n'.join(lines[start:end + 1])
        
        return self._extract_all_code_blocks(section_content)
    
    def _extract_all_code_blocks(self, content: str) -> list[str]:
        """
        Extract all code blocks from content.
        
        Enhanced to handle language tags and preserve formatting.
        
        Args:
            content: Markdown content
            
        Returns:
            List of code block contents
        """
        examples = []
        in_code_block = False
        code_block = []
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            if stripped.startswith('```'):
                if in_code_block:
                    # End of code block
                    if code_block:
                        examples.append('\n'.join(code_block))
                    code_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                    # Language tag is on the same line (```python), skip it
            elif in_code_block:
                code_block.append(line)
        
        # Handle unclosed code block
        if code_block:
            examples.append('\n'.join(code_block))
        
        return examples
    
    def _filter_and_limit(
        self, 
        items: list[str], 
        max_items: int = 5,
        min_length: int = 10
    ) -> list[str]:
        """
        Filter and limit extracted items.
        
        Removes duplicates (case-insensitive) and filters by length.
        
        Args:
            items: List of extracted items
            max_items: Maximum number of items to return
            min_length: Minimum length for an item
            
        Returns:
            Filtered and limited list
        """
        # Filter by length
        filtered = [item for item in items if len(item.strip()) >= min_length]
        
        # Remove duplicates (case-insensitive)
        seen = set()
        unique = []
        for item in filtered:
            item_lower = item.lower().strip()
            if item_lower not in seen:
                seen.add(item_lower)
                unique.append(item)
        
        # Limit
        return unique[:max_items]
