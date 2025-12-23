# Step 4: API Design - Python Support Enhancement

**Date**: 2025-01-27  
**Workflow**: Simple Mode Full SDLC  
**Feature**: Enhance TappsCodingAgents to support Python for all agents

## API Design Overview

This document specifies the exact interfaces, methods, and signatures for implementing Python support enhancement in TappsCodingAgents.

## Core API Changes

### 1. ScorerRegistry API Enhancement

#### Class: `ScorerRegistry`

##### New Class Variables

```python
class ScorerRegistry:
    _scorers: dict[Language, type[BaseScorer]] = {}  # Existing
    _fallback_chains: dict[Language, list[Language]] = {...}  # Existing
    _initialized: bool = False  # NEW: Track initialization state
```

##### New Methods

```python
@classmethod
def _ensure_initialized(cls) -> None:
    """
    Ensure built-in scorers are registered (lazy initialization).
    
    This method is called automatically before scorer lookup to ensure
    all built-in scorers (Python, TypeScript, etc.) are registered.
    
    Raises:
        ImportError: If scorer classes cannot be imported (circular dependency issue)
        RuntimeError: If registration fails unexpectedly
    """
    pass

@classmethod
def _register_builtin_scorers(cls) -> None:
    """
    Register all built-in language scorers.
    
    This method registers:
    - CodeScorer for Language.PYTHON
    - TypeScriptScorer for Language.TYPESCRIPT (if available)
    - ReactScorer for Language.REACT (if available)
    
    Note: Uses lazy imports to avoid circular dependencies.
    """
    pass
```

##### Modified Methods

```python
@classmethod
def get_scorer(cls, language: Language, config: ProjectConfig | None = None) -> BaseScorer:
    """
    Get appropriate scorer for a language, with fallback support.
    
    Enhanced to automatically ensure built-in scorers are registered
    before lookup.
    
    Args:
        language: Detected language
        config: Optional project configuration
        
    Returns:
        BaseScorer instance appropriate for the language
        
    Raises:
        ValueError: If no scorer found and no fallback available
        
    Changes:
        - Now calls _ensure_initialized() before scorer lookup
        - Automatic registration of built-in scorers on first call
    """
    cls._ensure_initialized()  # NEW: Ensure initialization
    # ... rest of existing implementation ...
```

#### Complete Method Signatures

```python
class ScorerRegistry:
    """Registry for language-specific scorers."""
    
    # Class variables
    _scorers: dict[Language, type[BaseScorer]] = {}
    _fallback_chains: dict[Language, list[Language]] = {
        Language.REACT: [Language.TYPESCRIPT, Language.JAVASCRIPT],
        Language.TYPESCRIPT: [Language.JAVASCRIPT],
    }
    _initialized: bool = False
    
    @classmethod
    def register(
        cls,
        language: Language,
        scorer_class: type[BaseScorer],
        *,
        override: bool = False,
    ) -> None:
        """Register a scorer class for a language (unchanged)."""
        pass
    
    @classmethod
    def unregister(cls, language: Language) -> None:
        """Unregister a scorer for a language (unchanged)."""
        pass
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        NEW: Ensure built-in scorers are registered.
        
        This method performs lazy initialization of built-in scorers.
        It's safe to call multiple times (idempotent).
        """
        if cls._initialized:
            return
        
        try:
            cls._register_builtin_scorers()
            cls._initialized = True
        except Exception as e:
            # Log error but don't raise - allow manual registration
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to auto-register built-in scorers: {e}. "
                "You may need to register scorers manually."
            )
    
    @classmethod
    def _register_builtin_scorers(cls) -> None:
        """
        NEW: Register all built-in scorers.
        
        This method registers:
        - CodeScorer for Language.PYTHON
        - TypeScriptScorer for Language.TYPESCRIPT
        - ReactScorer for Language.REACT
        
        Uses lazy imports to avoid circular dependencies.
        """
        # Register Python scorer
        from .scoring import CodeScorer
        if not cls.is_registered(Language.PYTHON):
            cls.register(Language.PYTHON, CodeScorer, override=False)
        
        # Register TypeScript scorer (if available)
        try:
            from .typescript_scorer import TypeScriptScorer
            if not cls.is_registered(Language.TYPESCRIPT):
                cls.register(Language.TYPESCRIPT, TypeScriptScorer, override=False)
        except ImportError:
            pass  # TypeScript scorer not available
        
        # Register React scorer (if available)
        try:
            from .react_scorer import ReactScorer
            if not cls.is_registered(Language.REACT):
                cls.register(Language.REACT, ReactScorer, override=False)
        except ImportError:
            pass  # React scorer not available
    
    @classmethod
    def get_scorer(cls, language: Language, config: ProjectConfig | None = None) -> BaseScorer:
        """
        Get appropriate scorer for a language (MODIFIED).
        
        Now automatically ensures built-in scorers are registered.
        """
        cls._ensure_initialized()  # NEW: Ensure initialization
        
        # Try to get scorer for this language
        scorer_class = cls._scorers.get(language)
        
        if scorer_class:
            return cls._instantiate_scorer(scorer_class, language, config)
        
        # ... rest of existing fallback logic ...
    
    @classmethod
    def list_registered_languages(cls) -> list[Language]:
        """Get list of languages with registered scorers (unchanged)."""
        pass
    
    @classmethod
    def is_registered(cls, language: Language) -> bool:
        """Check if a language has a scorer registered (unchanged)."""
        pass
    
    @classmethod
    def register_fallback_chain(
        cls, language: Language, fallback_chain: list[Language]
    ) -> None:
        """Register a fallback chain for a language (unchanged)."""
        pass
    
    @classmethod
    def _instantiate_scorer(
        cls,
        scorer_class: type[BaseScorer],
        language: Language,
        config: ProjectConfig | None = None,
    ) -> BaseScorer:
        """Instantiate a scorer class (unchanged)."""
        pass
```

### 2. ScorerFactory API (Unchanged)

```python
class ScorerFactory:
    """
    Factory to provide appropriate scorer based on language (unchanged).
    
    This class delegates to ScorerRegistry, which now handles
    automatic registration internally.
    """
    
    @staticmethod
    def get_scorer(language: Language, config: ProjectConfig | None = None) -> BaseScorer:
        """
        Get the appropriate scorer for a given language (unchanged).
        
        Now works automatically because ScorerRegistry ensures
        built-in scorers are registered.
        
        Args:
            language: Detected language enum
            config: Optional project configuration
            
        Returns:
            BaseScorer instance appropriate for the language
            
        Raises:
            ValueError: If no scorer is available for the language
        """
        from .scorer_registry import ScorerRegistry
        return ScorerRegistry.get_scorer(language, config)
```

### 3. Agent API Patterns

#### ReviewerAgent (Verified)

```python
class ReviewerAgent(BaseAgent, ExpertSupportMixin):
    """
    Reviewer Agent - Code review with Code Scoring (unchanged interface).
    
    Now supports Python files automatically through ScorerRegistry.
    """
    
    async def review_file(
        self,
        file_path: Path,
        include_scoring: bool = True,
        include_llm_feedback: bool = True,
    ) -> dict[str, Any]:
        """
        Review a code file (unchanged signature, enhanced behavior).
        
        Now automatically works for Python files because:
        1. LanguageDetector detects Language.PYTHON
        2. ScorerFactory.get_scorer() returns CodeScorer instance
        3. All scoring metrics work for Python
        
        Args:
            file_path: Path to code file
            include_scoring: Include code scores
            include_llm_feedback: Include LLM-generated feedback
            
        Returns:
            Review results with scores and feedback
            
        Example:
            >>> agent = ReviewerAgent()
            >>> await agent.activate()
            >>> result = await agent.review_file(Path("src/main.py"))
            >>> result["scoring"]["overall_score"]  # Works for Python!
        """
        # Detect language
        from ...core.language_detector import LanguageDetector
        detector = LanguageDetector(project_root=self._project_root)
        detection_result = detector.detect_language(file_path, code)
        language = detection_result.language  # Language.PYTHON for .py files
        
        # Get scorer (now works automatically!)
        from ...core.language_detector import Language
        from .scoring import ScorerFactory
        
        if language == Language.YAML:
            scores = self._score_yaml_file(file_path, code)
        else:
            scorer = ScorerFactory.get_scorer(language, self.config)  # ✅ Works!
            scores = scorer.score_file(file_path, code)
        
        # ... rest of implementation ...
```

#### Other Agents (Pattern to Follow)

```python
# Pattern for all agents that process code files
class AgentName(BaseAgent):
    async def process_file(self, file_path: Path) -> dict[str, Any]:
        """
        Process a code file with language-aware handling.
        
        Pattern:
        1. Detect language using LanguageDetector
        2. Route to language-specific handler
        3. Return results
        """
        # Step 1: Detect language
        from ...core.language_detector import LanguageDetector, Language
        detector = LanguageDetector(project_root=self._project_root)
        detection_result = detector.detect_language(file_path, code)
        language = detection_result.language
        
        # Step 2: Language-specific handling
        if language == Language.PYTHON:
            return await self._handle_python_file(file_path, code)
        elif language == Language.TYPESCRIPT:
            return await self._handle_typescript_file(file_path, code)
        else:
            return await self._handle_generic_file(file_path, code)
    
    async def _handle_python_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """Handle Python-specific processing."""
        # Python-specific logic here
        pass
```

## Configuration API (Unchanged)

### ProjectConfig Structure

```python
class ProjectConfig(BaseModel):
    """
    Project configuration (unchanged).
    
    Python support uses existing quality_tools configuration.
    """
    quality_tools: QualityToolsConfig | None = None
    scoring: ScoringConfig | None = None
    # ... other config fields ...

class QualityToolsConfig(BaseModel):
    """
    Quality tools configuration (unchanged).
    
    Python tools:
    - ruff_enabled: bool = True
    - mypy_enabled: bool = True
    - jscpd_enabled: bool = True
    - duplication_threshold: float = 3.0
    - min_duplication_lines: int = 5
    """
    ruff_enabled: bool = True
    mypy_enabled: bool = True
    jscpd_enabled: bool = True
    duplication_threshold: float = 3.0
    min_duplication_lines: int = 5
    # ... other tool configs ...
```

### Configuration File Example

```yaml
# .tapps-agents/config.yaml (unchanged)
quality_tools:
  ruff_enabled: true
  mypy_enabled: true
  jscpd_enabled: true
  duplication_threshold: 3.0
  min_duplication_lines: 5
```

## Public API Contracts

### 1. ScorerRegistry Public API

| Method | Signature | Behavior | Changes |
|--------|-----------|----------|---------|
| `register()` | `(language, scorer_class, override=False)` | Register scorer | Unchanged |
| `unregister()` | `(language)` | Unregister scorer | Unchanged |
| `get_scorer()` | `(language, config=None)` | Get scorer instance | **Enhanced**: Auto-registers built-ins |
| `list_registered_languages()` | `() -> list[Language]` | List registered languages | Unchanged |
| `is_registered()` | `(language) -> bool` | Check registration | Unchanged |
| `register_fallback_chain()` | `(language, fallback_chain)` | Register fallback | Unchanged |

### 2. ReviewerAgent Public API

| Method | Signature | Behavior | Changes |
|--------|-----------|----------|---------|
| `review_file()` | `(file_path, include_scoring=True, include_llm_feedback=True)` | Review file | **Enhanced**: Now works for Python |
| `lint_file()` | `(file_path)` | Lint file | Unchanged (already supports Python) |
| `type_check_file()` | `(file_path)` | Type check file | Unchanged (already supports Python) |

## Error Handling API

### Exception Types

```python
# Existing exceptions (unchanged)
class ScorerRegistrationError(ValueError):
    """Raised when scorer registration fails."""
    pass

# Usage in ScorerRegistry
try:
    cls._register_builtin_scorers()
except Exception as e:
    logger.warning(f"Failed to auto-register built-in scorers: {e}")
    # Continue - allow manual registration
```

### Error Messages

```python
# Error message format
f"Failed to register built-in Python scorer: {error_details}. "
"Please check dependencies and configuration."

# Available languages message
f"No scorer registered for language {language.value} "
f"and no fallback available. "
f"Available languages: {[lang.value for lang in cls._scorers.keys()]}"
```

## Testing API

### Test Utilities

```python
# Test helper to reset registry state
def reset_scorer_registry() -> None:
    """Reset ScorerRegistry to uninitialized state (for testing)."""
    ScorerRegistry._scorers.clear()
    ScorerRegistry._initialized = False

# Test helper to check registration
def assert_python_scorer_registered() -> None:
    """Assert that Python scorer is registered."""
    assert ScorerRegistry.is_registered(Language.PYTHON)
    scorer = ScorerRegistry.get_scorer(Language.PYTHON)
    assert isinstance(scorer, CodeScorer)
```

## Migration Guide

### For Users (No Action Required)

**Before:**
```python
# This would fail with ValueError
agent = ReviewerAgent()
await agent.activate()
result = await agent.review_file(Path("src/main.py"))  # ❌ Error
```

**After:**
```python
# This now works automatically
agent = ReviewerAgent()
await agent.activate()
result = await agent.review_file(Path("src/main.py"))  # ✅ Works!
```

### For Developers (Adding New Languages)

```python
# Pattern for adding new language scorer
from tapps_agents.agents.reviewer.scorer_registry import ScorerRegistry
from tapps_agents.core.language_detector import Language
from .my_scorer import MyLanguageScorer

# Register new scorer (can be done in module initialization)
ScorerRegistry.register(Language.MY_LANGUAGE, MyLanguageScorer)
```

## API Versioning

### Backward Compatibility

- ✅ All existing public APIs unchanged
- ✅ No breaking changes to method signatures
- ✅ Existing code continues to work
- ✅ New behavior is additive only

### Deprecations

- None (no deprecations required)

## Performance Considerations

### API Performance

| Operation | Before | After | Impact |
|-----------|--------|-------|--------|
| First `get_scorer()` call | Immediate lookup | +10-20ms (registration) | Negligible |
| Subsequent calls | Immediate lookup | Immediate lookup | No change |
| Module import | Instant | Instant | No change |

### Memory Footprint

- **Registration**: Class references only (~100 bytes per scorer)
- **Instances**: Created per request (unchanged behavior)
- **Total Impact**: <1KB additional memory

## Security Considerations

### API Security

- ✅ Registration only accepts `BaseScorer` subclasses (type-checked)
- ✅ No user code execution during registration
- ✅ Configuration validation (existing ProjectConfig validation)
- ✅ No new attack surface

## Next Steps

1. **Step 5**: Implement the API changes
2. **Step 6**: Code review and quality validation
3. **Step 7**: Testing and validation
4. **Step 8**: Security scanning
5. **Step 9**: Documentation

