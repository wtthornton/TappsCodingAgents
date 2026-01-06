# Step 1: Enhanced Prompt - Codebase Context Injection Implementation

## Original Prompt

Implement codebase context injection for the enhancer agent's `_stage_codebase_context` method. Currently, this method returns placeholder data. According to the analysis document (ANALYSIS_PROMPT_ENHANCEMENT_COMPARISON.md), this is the HIGH PRIORITY recommendation that provides real value for brownfield development.

## Enhanced Prompt with Requirements Analysis

### Functional Requirements

1. **Codebase Search Integration**
   - Use semantic search to find related files based on prompt analysis
   - Search by detected domains (e.g., "authentication", "payments", "user-management")
   - Search by detected technologies (e.g., "FastAPI", "SQLAlchemy", "pytest")
   - Limit results to top 10 most relevant files
   - Support both file path and content-based search

2. **Pattern Extraction**
   - Extract existing patterns from related files
   - Identify common code patterns (e.g., API route patterns, service patterns, test patterns)
   - Extract architectural patterns (e.g., dependency injection, repository pattern)
   - Identify coding conventions and style patterns

3. **Cross-Reference Detection**
   - Find files that import or reference related files
   - Identify dependency relationships between files
   - Map module dependencies and imports
   - Track file usage across the codebase

4. **Context Summary Generation**
   - Generate human-readable summary of codebase context
   - Include related files list with brief descriptions
   - Document existing patterns for consistency
   - Highlight cross-references and dependencies
   - Format context for inclusion in enhanced prompts

### Non-Functional Requirements

1. **Performance**
   - Codebase search should complete within 5 seconds for typical projects
   - Pattern extraction should be efficient (avoid full codebase scans)
   - Cache search results when possible
   - Limit file reads to necessary files only

2. **Reliability**
   - Gracefully handle missing files or permission errors
   - Provide fallback when codebase search fails
   - Return empty context rather than failing the entire enhancement
   - Log warnings for search failures without breaking workflow

3. **Maintainability**
   - Use existing codebase_search tool if available
   - Follow existing enhancer agent patterns
   - Integrate with existing stage pipeline seamlessly
   - Support configuration for search parameters

### Technical Constraints

1. **Integration Points**
   - Must work with existing `_stage_codebase_context` method signature
   - Must use `analysis` dict from previous stage (contains domains, technologies)
   - Must return dict with keys: `related_files`, `existing_patterns`, `cross_references`, `codebase_context`, `file_count`
   - Must be async to match other stage methods

2. **Dependencies**
   - Use codebase_search tool (if available) or semantic search capabilities
   - Leverage existing file system utilities
   - Use project config for project root path
   - Follow existing logging patterns

3. **Error Handling**
   - Catch and log exceptions without breaking enhancement pipeline
   - Return valid dict structure even on errors
   - Provide meaningful error messages in logs

### Assumptions

1. Codebase search tool or semantic search capability exists or can be implemented
2. Project root is available via `self.config.project_root`
3. Related files can be identified through semantic search or pattern matching
4. Pattern extraction can be done through code analysis or heuristics
5. Cross-references can be found through import/usage analysis

## Architecture Guidance

### System Design

The codebase context injection should:

1. **Search Strategy**
   - Use semantic search for domain/technology-based file discovery
   - Fall back to keyword search if semantic search unavailable
   - Prioritize files in main source directories (src/, tapps_agents/, etc.)
   - Filter out test files, generated files, and build artifacts

2. **Pattern Extraction Strategy**
   - Analyze file structure and imports for architectural patterns
   - Extract function/class naming conventions
   - Identify common code structures (routers, services, models)
   - Document patterns in structured format

3. **Cross-Reference Strategy**
   - Parse import statements to build dependency graph
   - Track file usage through static analysis
   - Identify related modules and packages
   - Map relationships between components

### Design Patterns

- **Strategy Pattern**: Different search strategies (semantic, keyword, pattern-based)
- **Adapter Pattern**: Adapt codebase_search tool to enhancer agent interface
- **Template Method**: Standard pattern extraction workflow
- **Facade Pattern**: Simplify complex codebase analysis operations

### Technology Recommendations

- Use existing `codebase_search` tool if available (from Cursor tools)
- Leverage Python's `ast` module for code analysis
- Use `pathlib` for file system operations
- Consider `grep` or `ripgrep` for pattern matching if needed

## Quality Standards

### Code Quality
- Follow existing enhancer agent code style
- Maintain async/await patterns
- Use type hints for all methods
- Add comprehensive docstrings
- Include error handling and logging

### Testing Requirements
- Unit tests for each helper method
- Integration tests for full codebase context stage
- Test error handling and edge cases
- Test with various project structures
- Verify performance requirements

### Documentation
- Document search strategies
- Explain pattern extraction algorithms
- Provide examples of generated context
- Update enhancer agent documentation

## Implementation Strategy

### Phase 1: Basic Implementation
1. Implement `_find_related_files` method using codebase_search
2. Implement basic pattern extraction
3. Implement cross-reference detection
4. Generate context summary

### Phase 2: Enhancement
1. Add caching for search results
2. Improve pattern extraction accuracy
3. Add configuration options
4. Optimize performance

### Phase 3: Integration
1. Integrate with synthesis stage
2. Test with real prompts
3. Verify context quality
4. Update documentation

## Expected Output Format

The enhanced prompt should include:

```markdown
## Codebase Context

### Related Files
- `tapps_agents/core/codebase_search.py` - Codebase search utilities
- `tapps_agents/agents/enhancer/agent.py` - Enhancer agent implementation
- ...

### Existing Patterns
- API routes follow FastAPI router pattern
- Services use dependency injection
- Tests use pytest fixtures
- ...

### Cross-References
- `enhancer/agent.py` imports `codebase_search` from `core`
- `build_orchestrator.py` uses enhanced prompts from enhancer
- ...

### Context Summary
[Human-readable summary of codebase context relevant to the prompt]
```
