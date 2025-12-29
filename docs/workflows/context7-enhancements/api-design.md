# Context7 Automatic Integration - API Design

**Date:** 2025-01-16  
**Status:** Complete  
**Purpose:** API specifications for Context7 automatic integration enhancements

## Overview

This document specifies the API contracts for the Context7 automatic integration enhancements. All APIs follow async/await patterns and return structured dictionaries.

## Core APIs

### 1. BaseAgent._auto_fetch_context7_docs()

**Purpose:** Universal hook for automatic Context7 documentation fetching across all agents.

**Signature:**
```python
async def _auto_fetch_context7_docs(
    self,
    code: str | None = None,
    prompt: str | None = None,
    error_message: str | None = None,
    language: str = "python"
) -> dict[str, dict[str, Any]]
```

**Parameters:**
- `code` (str | None): Optional code content to analyze for library imports
- `prompt` (str | None): Optional prompt text to analyze for library mentions
- `error_message` (str | None): Optional error message or stack trace to analyze
- `language` (str): Programming language for code analysis (default: "python")

**Returns:**
- `dict[str, dict[str, Any]]`: Dictionary mapping library names to their documentation
  - Format: `{library_name: {content: str, source: str, ...}, ...}`
  - Returns empty dict `{}` if:
    - Context7 is disabled
    - No libraries detected
    - Context7 helper unavailable

**Behavior:**
1. Checks if Context7 helper is available and enabled
2. Detects libraries from all provided sources (code, prompt, error_message)
3. Deduplicates detected libraries
4. Fetches documentation for all detected libraries via Context7 API
5. Returns documentation dictionary or empty dict

**Example:**
```python
# In any agent method
context7_docs = await self._auto_fetch_context7_docs(
    code="from fastapi import FastAPI",
    error_message="FastAPI HTTPException occurred"
)

if context7_docs:
    fastapi_docs = context7_docs.get("fastapi", {})
    content = fastapi_docs.get("content", "")
```

**Error Handling:**
- Returns empty dict if Context7 unavailable (graceful degradation)
- No exceptions raised for missing Context7

---

### 2. LibraryDetector.detect_from_error()

**Purpose:** Detect libraries from error messages and stack traces (Enhancement 5).

**Signature:**
```python
def detect_from_error(self, error_message: str) -> list[str]
```

**Parameters:**
- `error_message` (str): Error message or stack trace to analyze

**Returns:**
- `list[str]`: Sorted list of detected library names (lowercase)

**Detection Patterns:**
- Pattern matching for common error formats:
  - `(\w+)\.(HTTPException|ValidationError|NotFound|APIRouter|FastAPI)` → FastAPI, Pydantic
  - `(\w+)\.(raises|fixture|mark)` → pytest
  - `(\w+)\.(exc\.|orm\.)` → SQLAlchemy
  - `from\s+(\w+)\s+import` → Import statements in tracebacks
  - `(\w+)\.(core\.exceptions|db\.)` → Django
  - `(\w+)\.(models\.|admin\.)` → Django models/admin

- Known library error keywords:
  - FastAPI: `["HTTPException", "APIRouter", "FastAPI", "fastapi"]`
  - pytest: `["pytest.raises", "pytest.fixture", "pytest.mark", "pytest"]`
  - SQLAlchemy: `["sqlalchemy.exc", "sqlalchemy.orm", "sqlalchemy"]`
  - Django: `["django.core.exceptions", "django.db", "django"]`
  - Flask: `["flask", "Flask", "flask.Flask"]`
  - Pydantic: `["pydantic", "ValidationError", "BaseModel"]`
  - requests: `["requests", "requests.exceptions"]`
  - httpx: `["httpx", "httpx.exceptions"]`
  - aiohttp: `["aiohttp", "aiohttp.exceptions"]`

**Example:**
```python
detector = LibraryDetector()
error = "FastAPI HTTPException: Route not found"
libraries = detector.detect_from_error(error)
# Returns: ["fastapi"]
```

**Notes:**
- Case-insensitive detection
- Filters out standard library modules
- Returns sorted, deduplicated list

---

### 3. LibraryDetector.detect_all()

**Purpose:** Detect libraries from all available sources (updated to include error messages).

**Signature:**
```python
def detect_all(
    self,
    code: str | None = None,
    prompt: str | None = None,
    error_message: str | None = None,
    language: str = "python"
) -> list[str]
```

**Parameters:**
- `code` (str | None): Optional code content
- `prompt` (str | None): Optional prompt text
- `error_message` (str | None): Optional error message or stack trace (NEW)
- `language` (str): Programming language (default: "python")

**Returns:**
- `list[str]`: Combined, deduplicated, sorted list of detected library names

**Behavior:**
1. Detects from project files (`detect_from_project_files()`)
2. Detects from code (`detect_from_code()`)
3. Detects from prompt (`detect_from_prompt()`)
4. Detects from error messages (`detect_from_error()`) - NEW
5. Combines and deduplicates all results
6. Returns sorted list

**Example:**
```python
detector = LibraryDetector()
libraries = detector.detect_all(
    code="import fastapi",
    prompt="Use pytest for testing",
    error_message="sqlalchemy.exc.IntegrityError"
)
# Returns: ["fastapi", "pytest", "sqlalchemy"]
```

---

### 4. Context7AgentHelper.detect_topics()

**Purpose:** Automatically detect relevant Context7 topics from code context (Enhancement 7).

**Signature:**
```python
def detect_topics(self, code: str, library: str) -> list[str]
```

**Parameters:**
- `code` (str): Code content to analyze
- `library` (str): Library name to detect topics for

**Returns:**
- `list[str]`: List of detected topic names

**Topic Mappings:**
- **FastAPI:**
  - `routing`: Detects `@router.get`, `@router.post`, `APIRouter`, `route`
  - `path-parameters`: Detects `/{`, `{id}`, `path parameter`
  - `query-parameters`: Detects `Query(`, `query parameter`
  - `dependencies`: Detects `Depends(`, `dependency injection`

- **React:**
  - `hooks`: Detects `useState`, `useEffect`, `useCallback`
  - `state-management`: Detects `useState`, `useReducer`, `Context`
  - `routing`: Detects `Router`, `Route`, `Link`, `useNavigate`

- **pytest:**
  - `fixtures`: Detects `@pytest.fixture`, `fixture`
  - `parametrization`: Detects `@pytest.mark.parametrize`
  - `mocking`: Detects `mock`, `patch`, `MagicMock`

**Example:**
```python
helper = Context7AgentHelper(...)
code = """
from fastapi import APIRouter, Depends
@router.get("/users/{id}")
def get_user(id: int):
    pass
"""
topics = helper.detect_topics(code, "fastapi")
# Returns: ["routing", "path-parameters", "dependencies"]
```

---

### 5. Context7AgentHelper.detect_libraries()

**Purpose:** Detect libraries from all sources (updated to include error messages).

**Signature:**
```python
def detect_libraries(
    self,
    code: str | None = None,
    prompt: str | None = None,
    error_message: str | None = None,
    language: str = "python"
) -> list[str]
```

**Parameters:**
- `code` (str | None): Optional code content
- `prompt` (str | None): Optional prompt text
- `error_message` (str | None): Optional error message (NEW)
- `language` (str): Programming language (default: "python")

**Returns:**
- `list[str]`: List of detected library names

**Behavior:**
- Delegates to `LibraryDetector.detect_all()` with all parameters
- Returns empty list if Context7 disabled

---

## Configuration Models

### 6. ReviewerAgentContext7Config

**Purpose:** Per-agent Context7 configuration for Reviewer Agent.

**Model:**
```python
class ReviewerAgentContext7Config(BaseModel):
    """Context7 configuration for Reviewer Agent"""
    
    auto_detect: bool = Field(
        default=True,
        description="Enable automatic library detection for Reviewer Agent"
    )
    proactive_suggestions: bool = Field(
        default=True,
        description="Enable proactive Context7 suggestions for Reviewer Agent"
    )
    topics: list[str] = Field(
        default_factory=lambda: ["best-practices", "routing", "api-design"],
        description="Default topics to fetch for Reviewer Agent"
    )
```

**Usage:**
```python
config.agents.reviewer.context7.auto_detect = True
config.agents.reviewer.context7.proactive_suggestions = True
```

---

### 7. DebuggerAgentContext7Config

**Purpose:** Per-agent Context7 configuration for Debugger Agent.

**Model:**
```python
class DebuggerAgentContext7Config(BaseModel):
    """Context7 configuration for Debugger Agent"""
    
    auto_detect: bool = Field(
        default=True,
        description="Enable automatic library detection for Debugger Agent"
    )
    detect_from_errors: bool = Field(
        default=True,
        description="Detect libraries from error messages for Debugger Agent"
    )
```

**Usage:**
```python
config.agents.debugger.context7.auto_detect = True
config.agents.debugger.context7.detect_from_errors = True
```

---

### 8. ImplementerAgentContext7Config

**Purpose:** Per-agent Context7 configuration for Implementer Agent.

**Model:**
```python
class ImplementerAgentContext7Config(BaseModel):
    """Context7 configuration for Implementer Agent"""
    
    auto_detect: bool = Field(
        default=True,
        description="Enable automatic library detection for Implementer Agent"
    )
    detect_from_prompt: bool = Field(
        default=True,
        description="Detect libraries from prompt/specification text for Implementer Agent"
    )
```

**Usage:**
```python
config.agents.implementer.context7.auto_detect = True
config.agents.implementer.context7.detect_from_prompt = True
```

---

## Integration Points

### 9. Simple Mode Orchestrator Integration

**Location:** `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Integration:**
```python
# In BuildOrchestrator.execute()
context7_helper = get_context7_helper(self, self.config, self.project_root)
if context7_helper and context7_helper.enabled:
    detected_libraries = context7_helper.detect_libraries(prompt=original_description)
    if detected_libraries:
        context7_docs_for_enhancer = await context7_helper.get_documentation_for_libraries(
            libraries=detected_libraries,
            topic=None,
            use_fuzzy_match=True
        )
        # Inject into enhancer prompt
```

**Purpose:** Pre-fetch Context7 documentation for Simple Mode workflows based on initial prompt.

---

## Error Handling

All APIs follow graceful degradation patterns:

1. **Context7 Unavailable:** Returns empty dict/list, no exceptions
2. **No Libraries Detected:** Returns empty dict/list
3. **Context7 Disabled:** Returns empty dict/list
4. **API Errors:** Logged but don't break agent operations

## Testing

See test files:
- `tests/tapps_agents/core/test_agent_base_context7.py`
- `tests/tapps_agents/context7/test_library_detector_error_detection.py`

## Related Documentation

- [Enhancement Design](TAPPS_AGENTS_CONTEXT7_AUTO_ENHANCEMENT.md)
- [Implementation Summary](TAPPS_AGENTS_CONTEXT7_AUTO_ENHANCEMENT_IMPLEMENTATION.md)
- [Validation Results](TAPPS_AGENTS_CONTEXT7_AUTO_ENHANCEMENT_VALIDATION.md)

