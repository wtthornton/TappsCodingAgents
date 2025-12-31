# Step 3: Architecture Design - Priority 2 & 3 Missing Parts

**Workflow:** Simple Mode *build  
**Feature:** Complete Priority 2 & 3 - Missing Formatter Support and Pattern Enhancements  
**Date:** January 2025

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Formatter Enhancements (Priority 2)            │
├─────────────────────────────────────────────────────────────┤
│  format_markdown()                                          │
│  format_html()                                              │
│  format_text()                                              │
│  └─> NEW: format_library_recommendations()                  │
│  └─> NEW: format_pattern_guidance()                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         Content Extraction Enhancements (Priority 2)        │
├─────────────────────────────────────────────────────────────┤
│  Context7ReviewEnhancer                                     │
│  └─> IMPROVED: _extract_best_practices()                    │
│  └─> IMPROVED: _extract_common_mistakes()                   │
│  └─> IMPROVED: _extract_examples()                           │
│  └─> NEW: Enhanced markdown parser                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         Pattern Detection Enhancements (Priority 3)         │
├─────────────────────────────────────────────────────────────┤
│  PatternDetector                                            │
│  ├─> EXISTING: Keyword-based detection                      │
│  ├─> NEW: AST-based detection                               │
│  ├─> NEW: API pattern detection                             │
│  ├─> NEW: Database pattern detection                        │
│  ├─> NEW: Testing pattern detection                        │
│  ├─> NEW: Security pattern detection                        │
│  └─> NEW: Performance pattern detection                    │
│                                                              │
│  PatternRegistry (NEW)                                      │
│  ├─> Pattern registration                                   │
│  ├─> Pattern metadata                                       │
│  └─> Configuration-driven patterns                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. Formatter Enhancements

**Location:** `tapps_agents/cli/formatters.py`

**New Functions:**
- `_format_library_recommendations_markdown(recommendations: dict) -> str`
- `_format_pattern_guidance_markdown(guidance: dict) -> str`
- `_format_library_recommendations_html(recommendations: dict) -> str`
- `_format_pattern_guidance_html(guidance: dict) -> str`
- `_format_library_recommendations_text(recommendations: dict) -> str`
- `_format_pattern_guidance_text(guidance: dict) -> str`

**Integration:**
- Update `format_markdown()` to call new formatting functions
- Update `format_html()` to call new formatting functions
- Update text formatter (if exists) or create one

### 2. Content Extraction Enhancements

**Location:** `tapps_agents/agents/reviewer/context7_enhancer.py`

**Enhanced Methods:**
- `_extract_best_practices()` - Better markdown parsing
- `_extract_common_mistakes()` - Better section detection
- `_extract_examples()` - Better code block extraction
- `_parse_markdown_sections()` - NEW: Structured markdown parsing

**New Dependencies:**
- Consider using `markdown` library for better parsing (optional)
- Enhanced regex patterns for section detection

### 3. Additional Pattern Detectors

**Location:** `tapps_agents/agents/reviewer/pattern_detector.py`

**New Methods:**
- `detect_api_pattern()` - REST, GraphQL, gRPC
- `detect_database_pattern()` - ORM, migrations, queries
- `detect_testing_pattern()` - Unit tests, integration tests, mocking
- `detect_security_pattern()` - Authentication, authorization, encryption
- `detect_performance_pattern()` - Caching, async, batching

**New Pattern Indicators:**
- API_INDICATORS, DATABASE_INDICATORS, TESTING_INDICATORS, etc.

### 4. AST-Based Pattern Detection

**Location:** `tapps_agents/agents/reviewer/ast_pattern_detector.py` (new)

**Purpose:** AST-based pattern detection for Python code

**Methods:**
- `detect_patterns_ast(code: str) -> list[PatternMatch]`
- `_detect_rag_ast(tree: ast.AST) -> Optional[PatternMatch]`
- `_detect_api_ast(tree: ast.AST) -> Optional[PatternMatch]`
- Similar methods for other patterns

**Integration:**
- PatternDetector uses AST detector if available
- Falls back to keyword-based if AST fails

### 5. Pattern Registry System

**Location:** `tapps_agents/agents/reviewer/pattern_registry.py` (new)

**Purpose:** Extensible pattern registration system

**Classes:**
- `PatternRegistry` - Main registry class
- `PatternDefinition` - Pattern metadata dataclass

**Methods:**
- `register_pattern(definition: PatternDefinition)`
- `get_patterns() -> list[PatternDefinition]`
- `detect_all_patterns(code: str) -> list[PatternMatch]`

---

## Data Flow

### Formatter Enhancement Flow

```
Review Result (with library_recommendations, pattern_guidance)
│
├─> format_markdown(result)
│   ├─> Existing formatting (scoring, issues, etc.)
│   ├─> _format_library_recommendations_markdown() → markdown section
│   └─> _format_pattern_guidance_markdown() → markdown section
│
├─> format_html(result)
│   ├─> Existing formatting (scoring, issues, etc.)
│   ├─> _format_library_recommendations_html() → HTML section
│   └─> _format_pattern_guidance_html() → HTML section
│
└─> format_text(result)
    ├─> Existing formatting (scoring, issues, etc.)
    ├─> _format_library_recommendations_text() → text section
    └─> _format_pattern_guidance_text() → text section
```

### Enhanced Content Extraction Flow

```
Context7 Response (markdown content)
│
├─> _parse_markdown_sections() → structured sections
│   ├─> Detect headers (##, ###)
│   ├─> Detect lists (bulleted, numbered)
│   ├─> Detect code blocks (```)
│   └─> Detect tables
│
├─> _extract_best_practices(content)
│   ├─> Find "Best Practices" section
│   ├─> Extract list items
│   └─> Extract code examples
│
├─> _extract_common_mistakes(content)
│   ├─> Find "Common Mistakes" section
│   ├─> Extract list items
│   └─> Extract warnings
│
└─> _extract_examples(content)
    ├─> Find code blocks
    ├─> Extract with language tags
    └─> Filter by relevance
```

### AST-Based Pattern Detection Flow

```
Python Code
│
├─> ast.parse(code) → AST tree
│
├─> AST Pattern Detector
│   ├─> Walk AST tree
│   ├─> Detect patterns in structure
│   │   ├─> RAG: Check for vectorstore classes, embedding functions
│   │   ├─> API: Check for route decorators, HTTP methods
│   │   ├─> Database: Check for ORM models, query methods
│   │   └─> etc.
│   └─> Return PatternMatch with higher confidence
│
└─> Fallback to keyword-based if AST fails
```

### Pattern Registry Flow

```
Pattern Registration
│
├─> PatternRegistry.register_pattern(definition)
│   ├─> Store pattern metadata
│   ├─> Store detection function
│   └─> Store confidence calculator
│
├─> PatternRegistry.detect_all_patterns(code)
│   ├─> For each registered pattern:
│   │   ├─> Call detection function
│   │   ├─> Calculate confidence
│   │   └─> Return PatternMatch if above threshold
│   └─> Return all detected patterns
│
└─> PatternDetector uses registry
    └─> Calls registry.detect_all_patterns()
```

---

## Integration Points

### 1. Formatter Integration

**Modify:** `tapps_agents/cli/formatters.py`

**Changes:**
- Add helper functions for new sections
- Update existing formatter functions to call helpers
- Maintain backward compatibility

### 2. Content Extraction Integration

**Modify:** `tapps_agents/agents/reviewer/context7_enhancer.py`

**Changes:**
- Enhance existing extraction methods
- Add new parsing helper methods
- Improve accuracy without breaking existing functionality

### 3. Pattern Detection Integration

**Modify:** `tapps_agents/agents/reviewer/pattern_detector.py`

**Changes:**
- Add new pattern detection methods
- Integrate AST-based detection
- Integrate pattern registry

**New Files:**
- `tapps_agents/agents/reviewer/ast_pattern_detector.py`
- `tapps_agents/agents/reviewer/pattern_registry.py`

---

## Performance Considerations

### Formatter Performance
- **Target:** No performance impact (formatters are fast)
- **Optimization:** Lazy formatting (only format if data exists)

### Content Extraction Performance
- **Target:** < 50ms per Context7 response
- **Optimization:** Cache parsed sections, incremental parsing

### AST Pattern Detection Performance
- **Target:** < 100ms per file
- **Optimization:** Early exit on pattern match, cache AST trees

### Pattern Registry Performance
- **Target:** < 10ms overhead per pattern
- **Optimization:** Lazy pattern loading, efficient matching

---

## Security Considerations

1. **AST Parsing:** Safe (read-only, no code execution)
2. **Markdown Parsing:** Sanitize HTML if present
3. **Pattern Registry:** Validate pattern definitions before registration

---

## Testing Strategy

### Unit Tests
1. Formatter tests for each output format
2. Content extraction tests with various markdown formats
3. Pattern detection tests for each new pattern type
4. AST detection tests
5. Pattern registry tests

### Integration Tests
1. End-to-end formatter tests
2. End-to-end pattern detection tests
3. Performance tests

---

**Next Step:** Proceed to Step 4 (Component Design) with this architecture.
