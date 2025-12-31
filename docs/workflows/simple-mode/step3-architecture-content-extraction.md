# Step 3: Architecture Design - Improved Content Extraction

**Workflow:** Simple Mode *build  
**Feature:** Priority 2 - Improved Content Extraction from Context7  
**Date:** January 2025

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Enhanced Content Extraction System                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Context7ReviewEnhancer (Existing)                          │
│  └─> Uses: MarkdownParser, SectionDetector, ContentExtractor│
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ MarkdownParser   │  │ SectionDetector  │               │
│  │                  │  │                  │               │
│  │ - Parse headers │  │ - Detect sections│               │
│  │ - Parse lists   │  │ - Handle hierarchy│              │
│  │ - Parse tables  │  │ - Keyword matching│              │
│  │ - Parse code    │  │ - Boundary detection│            │
│  └────────┬─────────┘  └────────┬─────────┘               │
│           │                     │                          │
│           └──────────┬──────────┘                          │
│                      │                                     │
│           ┌──────────▼──────────┐                         │
│           │ ContentExtractor     │                         │
│           │                      │                         │
│           │ - Extract lists     │                         │
│           │ - Extract tables    │                         │
│           │ - Extract code      │                         │
│           │ - Quality filtering │                         │
│           └─────────────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. MarkdownParser

**Location:** `tapps_agents/agents/reviewer/markdown_parser.py` (new)

**Purpose:** Parse markdown structure into structured format

**Responsibilities:**
- Parse markdown headers (##, ###, ####)
- Parse nested lists (bulleted and numbered)
- Parse markdown tables
- Parse code blocks with language tags
- Handle edge cases (malformed markdown)

**Interfaces:**
```python
class MarkdownParser:
    def parse(self, content: str) -> MarkdownDocument
    def parse_headers(self, content: str) -> list[Header]
    def parse_lists(self, content: str) -> list[List]
    def parse_tables(self, content: str) -> list[Table]
    def parse_code_blocks(self, content: str) -> list[CodeBlock]
```

**Data Models:**
```python
@dataclass
class MarkdownDocument:
    headers: list[Header]
    lists: list[List]
    tables: list[Table]
    code_blocks: list[CodeBlock]
    raw_content: str

@dataclass
class Header:
    level: int  # 1-6
    text: str
    line_number: int

@dataclass
class List:
    items: list[ListItem]
    ordered: bool
    start_line: int
    end_line: int

@dataclass
class ListItem:
    text: str
    level: int  # Nesting level
    line_number: int
```

### 2. SectionDetector

**Location:** `tapps_agents/agents/reviewer/section_detector.py` (new)

**Purpose:** Detect sections in parsed markdown

**Responsibilities:**
- Detect section headers with variations
- Handle subsection hierarchies
- Detect sections by keywords
- Handle section boundaries
- Support custom section names

**Interfaces:**
```python
class SectionDetector:
    def detect_section(
        self, 
        document: MarkdownDocument, 
        section_name: str
    ) -> Optional[Section]
    
    def detect_all_sections(
        self, 
        document: MarkdownDocument
    ) -> dict[str, Section]
```

**Data Models:**
```python
@dataclass
class Section:
    name: str
    start_line: int
    end_line: int
    level: int  # Header level
    content: str
    subsections: list[Section]
```

### 3. ContentExtractor

**Location:** `tapps_agents/agents/reviewer/content_extractor.py` (new)

**Purpose:** Extract structured data from sections

**Responsibilities:**
- Extract list items with nesting
- Extract table data
- Extract code blocks
- Extract inline code
- Quality filtering
- Context-aware extraction

**Interfaces:**
```python
class ContentExtractor:
    def extract_best_practices(
        self, 
        section: Section
    ) -> list[str]
    
    def extract_common_mistakes(
        self, 
        section: Section
    ) -> list[str]
    
    def extract_examples(
        self, 
        section: Section
    ) -> list[str]
```

---

## Data Flow

### Content Extraction Flow

```
Context7 Response (markdown content)
│
├─> MarkdownParser.parse(content)
│   ├─> Parse headers → list[Header]
│   ├─> Parse lists → list[List]
│   ├─> Parse tables → list[Table]
│   └─> Parse code blocks → list[CodeBlock]
│
├─> MarkdownDocument (structured)
│
├─> SectionDetector.detect_section(document, "Best Practices")
│   ├─> Find header matching "Best Practices"
│   ├─> Find section boundaries
│   └─> Return Section object
│
├─> ContentExtractor.extract_best_practices(section)
│   ├─> Extract list items from section
│   ├─> Filter by quality
│   ├─> Extract code examples
│   └─> Return list[str]
│
└─> LibraryRecommendation
    ├─> best_practices: list[str]
    ├─> common_mistakes: list[str]
    └─> usage_examples: list[str]
```

### Error Handling Flow

```
MarkdownParser.parse()
│
├─> Try: Parse markdown
│   ├─> Success: Return MarkdownDocument
│   └─> Failure: Log warning, return minimal document
│
├─> SectionDetector.detect_section()
│   ├─> Try: Detect section
│   │   ├─> Success: Return Section
│   │   └─> Failure: Return None, fallback to keyword matching
│
└─> ContentExtractor.extract_*()
    ├─> Try: Extract content
    │   ├─> Success: Return extracted content
    │   └─> Failure: Return empty list, log warning
```

---

## Integration Points

### 1. Context7ReviewEnhancer Integration

**Modify:** `tapps_agents/agents/reviewer/context7_enhancer.py`

**Changes:**
- Initialize MarkdownParser, SectionDetector, ContentExtractor
- Update `_extract_best_practices()` to use new components
- Update `_extract_common_mistakes()` to use new components
- Update `_extract_examples()` to use new components
- Add fallback to simple extraction if parsing fails

**Code Structure:**
```python
class Context7ReviewEnhancer:
    def __init__(self, ...):
        # ... existing code ...
        self.markdown_parser = MarkdownParser()
        self.section_detector = SectionDetector()
        self.content_extractor = ContentExtractor()
        self.use_enhanced_extraction = True  # Config option
    
    def _extract_best_practices(self, content: str) -> list[str]:
        if self.use_enhanced_extraction:
            try:
                return self._extract_enhanced(content, "best_practices")
            except Exception as e:
                logger.warning(f"Enhanced extraction failed: {e}, using fallback")
                return self._extract_simple(content, "best_practices")
        else:
            return self._extract_simple(content, "best_practices")
```

---

## Performance Considerations

### Optimization Strategies

1. **Lazy Parsing:**
   - Only parse markdown if enhanced extraction enabled
   - Cache parsed documents per content hash
   - Reuse parsed documents for multiple extractions

2. **Early Exit:**
   - Stop parsing if section not found early
   - Skip parsing if content is too small
   - Use simple extraction for very short content

3. **Caching:**
   - Cache parsed MarkdownDocument per content hash
   - Cache detected sections
   - TTL: 1 hour default

4. **Performance Targets:**
   - Markdown parsing: < 20ms per response
   - Section detection: < 10ms per response
   - Content extraction: < 20ms per response
   - Total: < 50ms per response

---

## Security Considerations

1. **Input Validation:**
   - Validate markdown content size (max 1MB)
   - Sanitize HTML if present in markdown
   - Limit recursion depth for nested structures

2. **Error Handling:**
   - Don't expose internal errors to users
   - Log errors without sensitive data
   - Graceful degradation on failures

---

## Testing Strategy

### Unit Tests

1. **MarkdownParser Tests:**
   - Test header parsing (various levels)
   - Test nested list parsing
   - Test table parsing
   - Test code block parsing
   - Test edge cases (malformed markdown)

2. **SectionDetector Tests:**
   - Test section detection with variations
   - Test subsection hierarchies
   - Test keyword matching
   - Test boundary detection

3. **ContentExtractor Tests:**
   - Test list extraction
   - Test table extraction
   - Test code extraction
   - Test quality filtering

### Integration Tests

1. **End-to-End Tests:**
   - Test complete extraction flow
   - Test with real Context7 responses
   - Test fallback to simple extraction
   - Test performance targets

---

**Next Step:** Proceed to Step 4 (Component Design) with this architecture.
