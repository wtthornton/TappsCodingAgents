# Step 4: Component Design - Improved Content Extraction

**Workflow:** Simple Mode *build  
**Feature:** Priority 2 - Improved Content Extraction from Context7  
**Date:** January 2025

---

## Component API Specifications

### Enhanced Extraction Methods

**File:** `tapps_agents/agents/reviewer/context7_enhancer.py`

#### Enhanced _extract_best_practices()

```python
def _extract_best_practices(self, content: str) -> list[str]:
    """
    Extract best practices from Context7 content with enhanced parsing.
    
    Enhanced approach:
    1. Try enhanced markdown parsing (headers, sections)
    2. Fallback to simple keyword matching if parsing fails
    3. Better section detection with variations
    4. Handle nested lists and structured content
    
    Args:
        content: Markdown content from Context7
        
    Returns:
        List of best practices (max 5)
    """
    # Enhanced extraction logic
    practices = []
    
    # Step 1: Try to find section by header
    section = self._find_section_by_header(content, ["best practice", "best practices", "recommendation", "recommendations"])
    
    if section:
        # Extract from section
        practices = self._extract_from_section(section, content)
    else:
        # Fallback to keyword-based extraction
        practices = self._extract_by_keywords(content, ["should", "recommend", "best", "use"])
    
    # Filter and limit
    return self._filter_and_limit(practices, max_items=5)
```

#### Enhanced _extract_common_mistakes()

```python
def _extract_common_mistakes(self, content: str) -> list[str]:
    """
    Extract common mistakes from Context7 content with enhanced parsing.
    
    Enhanced approach:
    1. Try enhanced markdown parsing
    2. Better section detection
    3. Handle structured content
    
    Args:
        content: Markdown content from Context7
        
    Returns:
        List of common mistakes (max 5)
    """
    mistakes = []
    
    # Step 1: Try to find section by header
    section = self._find_section_by_header(
        content, 
        ["common mistake", "common mistakes", "pitfall", "pitfalls", "avoid", "anti-pattern"]
    )
    
    if section:
        mistakes = self._extract_from_section(section, content)
    else:
        # Fallback to keyword-based extraction
        mistakes = self._extract_by_keywords(content, ["avoid", "don't", "never", "mistake", "wrong"])
    
    return self._filter_and_limit(mistakes, max_items=5)
```

#### Enhanced _extract_examples()

```python
def _extract_examples(self, content: str) -> list[str]:
    """
    Extract usage examples from Context7 content with enhanced parsing.
    
    Enhanced approach:
    1. Parse code blocks with language tags
    2. Extract from "Examples" section if present
    3. Better code block detection
    
    Args:
        content: Markdown content from Context7
        
    Returns:
        List of code examples (max 3)
    """
    examples = []
    
    # Step 1: Try to find "Examples" section
    section = self._find_section_by_header(content, ["example", "examples", "usage", "code example"])
    
    if section:
        # Extract code blocks from section
        examples = self._extract_code_blocks_from_section(section, content)
    else:
        # Extract all code blocks
        examples = self._extract_all_code_blocks(content)
    
    return examples[:3]  # Limit to 3
```

### Helper Methods

#### _find_section_by_header()

```python
def _find_section_by_header(
    self, 
    content: str, 
    keywords: list[str]
) -> Optional[tuple[int, int]]:
    """
    Find section by header keywords.
    
    Args:
        content: Markdown content
        keywords: List of keywords to search for in headers
        
    Returns:
        Tuple of (start_line, end_line) if found, None otherwise
    """
    lines = content.split('\n')
    in_section = False
    start_line = None
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Check if line is a header (starts with #)
        if line_lower.startswith('#'):
            # Check if header contains any keyword
            if any(keyword in line_lower for keyword in keywords):
                in_section = True
                start_line = i
            elif in_section:
                # Found next header, end of section
                return (start_line, i - 1)
    
    if in_section:
        return (start_line, len(lines) - 1)
    
    return None
```

#### _extract_from_section()

```python
def _extract_from_section(
    self, 
    section: tuple[int, int], 
    content: str
) -> list[str]:
    """
    Extract content from a section.
    
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
        
        # Extract list items
        if stripped.startswith(('-', '*', '•')):
            item = stripped.lstrip('-*• ').strip()
            if item and len(item) > 10:
                items.append(item)
        elif stripped and stripped[0].isdigit() and '.' in stripped[:3]:
            # Numbered list
            item = stripped.split('.', 1)[1].strip() if '.' in stripped else stripped
            if item and len(item) > 10:
                items.append(item)
        elif stripped and not stripped.startswith('#') and len(stripped) > 20:
            # Paragraph text (if substantial)
            items.append(stripped)
    
    return items
```

#### _extract_code_blocks_from_section()

```python
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
```

#### _extract_all_code_blocks()

```python
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
    language = None
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        if stripped.startswith('```'):
            if in_code_block:
                # End of code block
                if code_block:
                    examples.append('\n'.join(code_block))
                code_block = []
                language = None
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
                # Extract language if present: ```python
                if len(stripped) > 3:
                    language = stripped[3:].strip()
        elif in_code_block:
            code_block.append(line)
    
    # Handle unclosed code block
    if code_block:
        examples.append('\n'.join(code_block))
    
    return examples
```

#### _extract_by_keywords() (Fallback)

```python
def _extract_by_keywords(
    self, 
    content: str, 
    keywords: list[str]
) -> list[str]:
    """
    Fallback extraction using keyword matching.
    
    This is the original simple extraction method, used as fallback.
    
    Args:
        content: Markdown content
        keywords: Keywords to search for
        
    Returns:
        List of extracted items
    """
    items = []
    lines = content.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            stripped = line.strip()
            if stripped.startswith(('-', '*', '•')):
                item = stripped.lstrip('-*• ').strip()
                if item and len(item) > 10:
                    items.append(item)
            elif stripped and len(stripped) > 20:
                items.append(stripped)
    
    return items
```

#### _filter_and_limit()

```python
def _filter_and_limit(
    self, 
    items: list[str], 
    max_items: int = 5,
    min_length: int = 10
) -> list[str]:
    """
    Filter and limit extracted items.
    
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
```

---

## Integration with Context7ReviewEnhancer

### Updated Class Structure

```python
class Context7ReviewEnhancer:
    def __init__(
        self,
        context7_helper: Context7AgentHelper,
        timeout: int = 30,
        cache_enabled: bool = True,
        use_enhanced_extraction: bool = True  # NEW: Config option
    ):
        # ... existing code ...
        self.use_enhanced_extraction = use_enhanced_extraction
    
    def _extract_best_practices(self, content: str) -> list[str]:
        """Enhanced extraction with fallback."""
        if self.use_enhanced_extraction:
            try:
                return self._extract_best_practices_enhanced(content)
            except Exception as e:
                logger.debug(f"Enhanced extraction failed, using fallback: {e}")
                return self._extract_best_practices_simple(content)
        else:
            return self._extract_best_practices_simple(content)
    
    def _extract_best_practices_enhanced(self, content: str) -> list[str]:
        """New enhanced extraction method."""
        # Implementation using helper methods
    
    def _extract_best_practices_simple(self, content: str) -> list[str]:
        """Original simple extraction (renamed for clarity)."""
        # Original implementation
```

---

## Error Handling

### Graceful Degradation

```python
try:
    # Try enhanced extraction
    result = self._extract_enhanced(content)
except Exception as e:
    logger.warning(f"Enhanced extraction failed: {e}")
    # Fallback to simple extraction
    result = self._extract_simple(content)
```

### Input Validation

```python
def _validate_content(self, content: str) -> bool:
    """Validate content before processing."""
    if not content or not isinstance(content, str):
        return False
    if len(content) > 1_000_000:  # 1MB limit
        logger.warning("Content too large, skipping enhanced extraction")
        return False
    return True
```

---

**Next Step:** Proceed to Step 5 (Implementation) with these API specifications.
