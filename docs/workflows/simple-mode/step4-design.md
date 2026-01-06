# Step 4: Component Design Specifications - Codebase Context Injection

## API Design

### Method Signature

```python
async def _stage_codebase_context(
    self, 
    prompt: str, 
    analysis: dict[str, Any]
) -> dict[str, Any]:
    """
    Stage 4: Inject codebase context.
    
    Analyzes the codebase to find related files, extract patterns,
    and detect cross-references relevant to the prompt.
    
    Args:
        prompt: Original user prompt
        analysis: Analysis stage output containing:
            - domains: List of detected domains (e.g., ["authentication", "payments"])
            - technologies: List of detected technologies (e.g., ["FastAPI", "SQLAlchemy"])
            - intent: Prompt intent (e.g., "feature", "bug-fix")
            - scope: Prompt scope (e.g., "file", "module", "project")
    
    Returns:
        Dictionary with keys:
            - related_files: List[str] - Paths to related files (max 10)
            - existing_patterns: List[dict] - Extracted patterns
            - cross_references: List[dict] - File dependencies
            - codebase_context: str - Human-readable context summary
            - file_count: int - Number of related files found
    
    Raises:
        None - All errors are handled gracefully, returns empty context on failure
    """
```

### Helper Method Signatures

#### 1. File Discovery

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
        analysis: Analysis stage output
    
    Returns:
        List of file paths (max 10), sorted by relevance
    """
```

#### 2. Pattern Extraction

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
        List of pattern dictionaries with structure:
        {
            "type": str,  # "architectural", "structure", "naming", "style"
            "name": str,   # Pattern name
            "description": str,  # Pattern description
            "examples": list[str],  # Example file paths or code snippets
            "confidence": float  # Confidence score 0.0-1.0
        }
    """
```

#### 3. Cross-Reference Detection

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
        List of cross-reference dictionaries with structure:
        {
            "source": str,  # Source file path
            "target": str,  # Target file path
            "type": str,    # "import", "usage", "dependency"
            "details": str  # Additional details (e.g., imported symbols)
        }
    """
```

#### 4. Context Summary Generation

```python
def _generate_context_summary(
    self,
    related_files: list[str],
    existing_patterns: list[dict[str, Any]],
    cross_references: list[dict[str, Any]]
) -> str:
    """
    Generate human-readable context summary.
    
    Args:
        related_files: List of related file paths
        existing_patterns: List of extracted patterns
        cross_references: List of cross-references
    
    Returns:
        Markdown-formatted context summary
    """
```

## Data Models

### Pattern Dictionary

```python
{
    "type": "architectural" | "structure" | "naming" | "style",
    "name": str,  # e.g., "Dependency Injection Pattern"
    "description": str,  # Detailed description
    "examples": list[str],  # File paths or code snippets
    "confidence": float  # 0.0-1.0
}
```

### Cross-Reference Dictionary

```python
{
    "source": str,  # e.g., "tapps_agents/agents/enhancer/agent.py"
    "target": str,  # e.g., "tapps_agents/core/codebase_search.py"
    "type": "import" | "usage" | "dependency",
    "details": str  # e.g., "imports codebase_search function"
}
```

### Return Dictionary

```python
{
    "related_files": list[str],  # Max 10 file paths
    "existing_patterns": list[dict],  # Pattern dictionaries
    "cross_references": list[dict],  # Cross-reference dictionaries
    "codebase_context": str,  # Markdown-formatted summary
    "file_count": int  # Number of related files
}
```

## Component Specifications

### 1. File Discovery Component

**Input:**
- `prompt`: Original user prompt
- `analysis`: Dict with `domains` and `technologies` lists

**Processing:**
1. Build search queries from domains and technologies
2. Execute semantic search using `codebase_search` tool
3. Combine and deduplicate results
4. Filter out irrelevant files (tests, generated, build artifacts)
5. Rank by relevance
6. Limit to top 10 files

**Output:**
- List of file paths (max 10)

**Error Handling:**
- Catch search exceptions
- Log warnings
- Return empty list on failure

**Configuration:**
- Max files: 10 (configurable)
- Exclude patterns: `**/test_*.py`, `**/__pycache__/**`, `**/build/**`

### 2. Pattern Extraction Component

**Input:**
- `related_files`: List of file paths

**Processing:**
1. Read file contents (skip large files > 100KB)
2. Parse imports to identify architectural patterns
3. Analyze code structure (classes, functions, modules)
4. Extract naming conventions
5. Identify style patterns (imports, docstrings, type hints)
6. Document patterns with examples

**Output:**
- List of pattern dictionaries

**Error Handling:**
- Skip files that can't be read
- Handle parsing errors gracefully
- Log warnings for failures

**Pattern Types:**
- **Architectural**: Dependency injection, repository pattern, service layer
- **Structure**: Router patterns, service patterns, model patterns
- **Naming**: Function/class naming conventions
- **Style**: Import organization, docstring format, type hints

### 3. Cross-Reference Analyzer Component

**Input:**
- `related_files`: List of file paths

**Processing:**
1. Parse Python files using AST
2. Extract import statements
3. Build import graph
4. Track usage through function calls
5. Map module relationships

**Output:**
- List of cross-reference dictionaries

**Error Handling:**
- Handle syntax errors gracefully
- Skip files that can't be parsed
- Log warnings for parsing failures

**Cross-Reference Types:**
- **Import**: Direct imports between files
- **Usage**: Files using classes/functions from other files
- **Dependency**: Module-level dependencies

### 4. Context Synthesizer Component

**Input:**
- `related_files`: List of file paths
- `existing_patterns`: List of pattern dictionaries
- `cross_references`: List of cross-reference dictionaries

**Processing:**
1. Format related files as markdown list
2. Document patterns with examples
3. List cross-references showing relationships
4. Generate summary paragraph
5. Format as markdown

**Output:**
- Markdown-formatted context summary

**Format:**
```markdown
## Codebase Context

### Related Files
- `path/to/file1.py` - Brief description
- `path/to/file2.py` - Brief description

### Existing Patterns
- **Architectural Pattern**: Dependency injection pattern
  - Example: `services/user_service.py` uses constructor injection
- **Code Structure**: FastAPI routers follow `/api/v1/{resource}` pattern
  - Example: `api/v1/users.py` implements user routes

### Cross-References
- `enhancer/agent.py` → `core/codebase_search.py` (imports codebase_search)
- `build_orchestrator.py` → `enhancer/agent.py` (uses enhanced prompts)

### Context Summary
[Human-readable summary explaining codebase context relevance]
```

## Integration Specifications

### Enhancer Agent Integration

**Location:** `tapps_agents/agents/enhancer/agent.py`

**Method:** `_stage_codebase_context()`

**Integration Points:**
1. Called from `_enhance_full()` method after analysis stage
2. Receives `analysis` dict from analysis stage
3. Returns context dict for synthesis stage
4. Maintains async/await pattern

**Synthesis Stage Usage:**
- Context included in synthesis prompt
- Formatted as markdown section
- Optional (enhancement works without context)

### Configuration

**Config File:** `.tapps-agents/config.yaml`

```yaml
enhancer:
  codebase_context:
    enabled: true
    max_files: 10
    exclude_patterns:
      - "**/test_*.py"
      - "**/__pycache__/**"
      - "**/build/**"
      - "**/dist/**"
    max_file_size_kb: 100
    semantic_search: true
    pattern_extraction: true
    cross_reference: true
```

## Error Handling Specifications

### Error Types and Handling

1. **Search Failures**
   - **Error**: `codebase_search` tool unavailable or fails
   - **Handling**: Log warning, return empty list
   - **Impact**: Context will be empty, but enhancement continues

2. **File Read Errors**
   - **Error**: Permission denied, file not found, encoding issues
   - **Handling**: Skip file, log warning, continue with other files
   - **Impact**: Partial context (other files still processed)

3. **Parsing Errors**
   - **Error**: Syntax errors, invalid Python code
   - **Handling**: Skip file, log warning, continue with other files
   - **Impact**: Partial patterns/cross-references

4. **Empty Results**
   - **Error**: No related files found
   - **Handling**: Return empty context with message
   - **Impact**: Enhancement continues without codebase context

### Logging

**Log Levels:**
- **DEBUG**: Detailed search queries, file processing
- **INFO**: Context generation summary (file count, pattern count)
- **WARNING**: Search failures, file read errors, parsing errors
- **ERROR**: Unexpected exceptions (should not occur due to error handling)

**Log Messages:**
```python
logger.debug(f"Searching for files related to domains: {domains}")
logger.info(f"Found {len(related_files)} related files")
logger.warning(f"Failed to read file {file_path}: {error}")
logger.warning(f"Codebase search unavailable, returning empty context")
```

## Performance Specifications

### Performance Targets

- **Codebase Search**: < 5 seconds
- **Pattern Extraction**: < 2 seconds (for 10 files)
- **Cross-Reference Analysis**: < 2 seconds (for 10 files)
- **Context Summary Generation**: < 0.5 seconds
- **Total Stage Execution**: < 10 seconds

### Optimization Strategies

1. **Limit File Reads**: Only read files when needed
2. **Skip Large Files**: Skip files > 100KB
3. **Parallel Processing**: Process multiple files concurrently (if beneficial)
4. **Early Termination**: Stop after finding enough results
5. **Caching**: Cache search results (future enhancement)

## Testing Specifications

### Unit Test Cases

1. **File Discovery**
   - Test with mock search results
   - Test filtering and ranking
   - Test limit enforcement
   - Test error handling

2. **Pattern Extraction**
   - Test with sample files
   - Test pattern identification
   - Test example extraction
   - Test error handling

3. **Cross-Reference Detection**
   - Test with sample imports
   - Test dependency graph building
   - Test usage tracking
   - Test error handling

4. **Context Summary Generation**
   - Test markdown formatting
   - Test with empty inputs
   - Test with various data combinations

### Integration Test Cases

1. **Full Stage Execution**
   - Test with real codebase
   - Test error scenarios
   - Test performance

2. **Enhancement Pipeline Integration**
   - Test context inclusion in synthesis
   - Test backward compatibility
   - Test with missing context

### Edge Cases

1. Empty codebase
2. No related files found
3. All files fail to parse
4. Search tool unavailable
5. Permission errors on all files
6. Very large codebase (> 1000 files)
