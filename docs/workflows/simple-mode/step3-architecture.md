# Step 3: Architecture Design - Codebase Context Injection

## System Architecture

### Component Overview

The codebase context injection system consists of four main components:

1. **File Discovery Module** - Finds related files using semantic search
2. **Pattern Extraction Module** - Extracts patterns from related files
3. **Cross-Reference Analyzer** - Detects dependencies and relationships
4. **Context Synthesizer** - Generates human-readable context summary

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Enhancer Agent                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         _stage_codebase_context()                     │  │
│  │                                                       │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐  │  │
│  │  │ File Discovery │  │ Pattern Extraction       │  │  │
│  │  │                │  │                          │  │  │
│  │  │ - Semantic     │  │ - Architectural patterns │  │  │
│  │  │   search       │  │ - Coding conventions     │  │  │
│  │  │ - Domain-based │  │ - Code structures         │  │  │
│  │  │ - Tech-based   │  │ - Style patterns          │  │  │
│  │  └────────────────┘  └──────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐  │  │
│  │  │ Cross-Reference │  │ Context Synthesizer      │  │  │
│  │  │ Analyzer        │  │                          │  │  │
│  │  │                 │  │ - Summary generation     │  │  │
│  │  │ - Import graph  │  │ - Format for prompts     │  │  │
│  │  │ - Usage tracking│  │ - Metadata inclusion     │  │  │
│  │  │ - Dependencies  │  │                          │  │  │
│  │  └────────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ codebase_search│  │ AST Parser     │  │ File System    │
│ Tool           │  │                │  │ Utilities      │
└────────────────┘  └────────────────┘  └────────────────┘
```

## Component Design

### 1. File Discovery Module

**Purpose:** Find related files based on prompt analysis

**Responsibilities:**
- Execute semantic search queries based on domains and technologies
- Filter and rank search results
- Limit results to top 10 most relevant files
- Filter out irrelevant files (tests, generated, build artifacts)

**Interface:**
```python
async def _find_related_files(
    self, 
    prompt: str, 
    analysis: dict[str, Any]
) -> list[str]:
    """
    Find related files using semantic search.
    
    Args:
        prompt: Original user prompt
        analysis: Analysis stage output (contains domains, technologies)
    
    Returns:
        List of file paths (max 10)
    """
```

**Implementation Strategy:**
- Use `codebase_search` tool if available (from Cursor tools)
- Fall back to keyword-based file search if semantic search unavailable
- Search by domains: `f"files related to {domain}"` for each domain
- Search by technologies: `f"files using {tech}"` for each technology
- Combine results and deduplicate
- Filter by file extensions and paths (exclude tests, generated files)
- Rank by relevance and return top 10

**Error Handling:**
- Catch search exceptions and log warnings
- Return empty list on failure (doesn't break pipeline)
- Provide fallback to simple file system search

### 2. Pattern Extraction Module

**Purpose:** Extract existing patterns from related files

**Responsibilities:**
- Analyze file structure and imports
- Identify architectural patterns
- Extract coding conventions
- Document patterns in structured format

**Interface:**
```python
async def _extract_patterns(
    self, 
    related_files: list[str]
) -> list[dict[str, Any]]:
    """
    Extract patterns from related files.
    
    Args:
        related_files: List of file paths to analyze
    
    Returns:
        List of pattern dictionaries with type, description, examples
    """
```

**Implementation Strategy:**
- Read file contents (limit to source files, skip large files)
- Parse imports to identify architectural patterns
- Analyze import structure to identify patterns (e.g., dependency injection)
- Extract function/class naming conventions
- Identify common code structures (routers, services, models, tests)
- Use AST parsing for deeper analysis if needed
- Document patterns with examples

**Pattern Types:**
- **Architectural Patterns**: Dependency injection, repository pattern, service layer
- **Code Structure**: Router patterns, service patterns, model patterns
- **Naming Conventions**: Function names, class names, variable names
- **Style Patterns**: Import organization, docstring format, type hints

**Error Handling:**
- Skip files that can't be read (permissions, encoding issues)
- Log warnings for parsing failures
- Return empty list if all files fail

### 3. Cross-Reference Analyzer

**Purpose:** Detect dependencies and relationships between files

**Responsibilities:**
- Parse import statements
- Build dependency graph
- Track file usage
- Map relationships between components

**Interface:**
```python
async def _find_cross_references(
    self, 
    related_files: list[str]
) -> list[dict[str, Any]]:
    """
    Find cross-references between files.
    
    Args:
        related_files: List of file paths to analyze
    
    Returns:
        List of cross-reference dictionaries with source, target, type
    """
```

**Implementation Strategy:**
- Parse Python files using AST module
- Extract import statements (absolute, relative, from imports)
- Build import graph (which files import which)
- Track usage through function calls and class instantiations
- Identify module relationships
- Map package dependencies

**Cross-Reference Types:**
- **Imports**: Direct imports between files
- **Usage**: Files that use classes/functions from other files
- **Dependencies**: Module-level dependencies
- **Relationships**: Related modules in same package

**Error Handling:**
- Handle syntax errors in files gracefully
- Skip files that can't be parsed
- Log warnings for parsing failures
- Return empty list if all files fail

### 4. Context Synthesizer

**Purpose:** Generate human-readable context summary

**Responsibilities:**
- Combine related files, patterns, and cross-references
- Format context for inclusion in enhanced prompts
- Generate summary text
- Include metadata

**Interface:**
```python
def _generate_context_summary(
    self,
    related_files: list[str],
    existing_patterns: list[dict[str, Any]],
    cross_references: list[dict[str, Any]]
) -> str:
    """
    Generate context summary from analysis results.
    
    Args:
        related_files: List of related file paths
        existing_patterns: List of extracted patterns
        cross_references: List of cross-references
    
    Returns:
        Human-readable context summary (markdown format)
    """
```

**Implementation Strategy:**
- Format related files as bullet list with brief descriptions
- Document patterns with examples
- List cross-references showing relationships
- Generate summary paragraph explaining context relevance
- Format as markdown for inclusion in enhanced prompts

**Output Format:**
```markdown
## Codebase Context

### Related Files
- `path/to/file1.py` - Description of file purpose
- `path/to/file2.py` - Description of file purpose

### Existing Patterns
- **Architectural Pattern**: Dependency injection pattern used in services
- **Code Structure**: FastAPI routers follow `/api/v1/{resource}` pattern
- **Naming Convention**: Services use `{Resource}Service` naming

### Cross-References
- `enhancer/agent.py` imports `codebase_search` from `core`
- `build_orchestrator.py` uses enhanced prompts from enhancer

### Context Summary
[Human-readable summary explaining how codebase context relates to prompt]
```

## Data Flow

### Enhancement Pipeline Integration

```
1. Analysis Stage
   └─> Output: { domains: [...], technologies: [...] }
       │
       ▼
2. Codebase Context Stage
   ├─> Input: prompt, analysis
   ├─> File Discovery: Find related files
   ├─> Pattern Extraction: Extract patterns
   ├─> Cross-Reference: Find dependencies
   ├─> Context Synthesis: Generate summary
   └─> Output: { related_files, patterns, cross_references, codebase_context }
       │
       ▼
3. Synthesis Stage
   └─> Includes codebase context in enhanced prompt
```

## Technology Stack

### Core Technologies
- **Python 3.10+**: Async/await support
- **AST Module**: Python code parsing
- **pathlib**: File system operations
- **codebase_search**: Semantic search tool (if available)

### Dependencies
- Existing enhancer agent infrastructure
- Project config for project root
- Logging utilities
- Error handling patterns

## Performance Considerations

### Optimization Strategies
1. **Caching**: Cache search results for repeated queries
2. **Lazy Loading**: Only read files when needed
3. **Parallel Processing**: Process multiple files concurrently
4. **Early Termination**: Stop searching after finding enough results
5. **File Filtering**: Skip large files, generated files, test files

### Performance Targets
- Codebase search: < 5 seconds
- Pattern extraction: < 2 seconds
- Cross-reference analysis: < 2 seconds
- Total stage execution: < 10 seconds

## Scalability Considerations

### Large Codebases
- Limit file reads to top 10 most relevant files
- Use efficient search algorithms
- Cache results to avoid repeated searches
- Process files in batches if needed

### Small Codebases
- Handle gracefully when few files found
- Provide meaningful context even with limited information
- Don't fail if no related files found

## Security Considerations

### File Access
- Respect file permissions
- Don't read sensitive files (config, secrets)
- Handle permission errors gracefully
- Log access for auditing

### Code Execution
- AST parsing is safe (no code execution)
- No eval() or exec() calls
- Read-only file operations

## Error Handling Strategy

### Graceful Degradation
- Return empty context if search fails (don't break pipeline)
- Log warnings for debugging
- Provide fallback mechanisms
- Maintain valid return structure

### Error Types
1. **Search Failures**: Log warning, return empty list
2. **File Read Errors**: Skip file, continue with others
3. **Parsing Errors**: Skip file, log warning
4. **Permission Errors**: Skip file, log warning

## Integration Points

### Enhancer Agent Integration
- Called from `_enhance_full()` method
- Receives `analysis` dict from analysis stage
- Returns context dict for synthesis stage
- Maintains async/await pattern

### Synthesis Stage Integration
- Context included in synthesis prompt
- Formatted as markdown section
- Optional (enhancement works without context)

## Testing Strategy

### Unit Tests
- Test file discovery with mock search results
- Test pattern extraction with sample files
- Test cross-reference detection with sample imports
- Test context summary generation

### Integration Tests
- Test full codebase context stage
- Test with real codebase
- Test error handling scenarios
- Test performance with various codebase sizes

### Edge Cases
- Empty codebase
- No related files found
- All files fail to parse
- Search tool unavailable
- Permission errors
