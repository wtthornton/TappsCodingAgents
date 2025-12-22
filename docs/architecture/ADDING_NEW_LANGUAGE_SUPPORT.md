# Adding New Language Support - Generic Architecture Guide

## Overview

With the new generic scoring architecture, adding support for a new programming language is straightforward and doesn't require modifying core code.

## Architecture Components

### 1. Scorer Registry
- Central registry for language-specific scorers
- Supports fallback chains (e.g., React → TypeScript)
- Auto-registration on import

### 2. Metric Strategies
- Reusable metric calculation logic
- Language-agnostic patterns (complexity, security, test coverage)
- Can be extended with language-specific implementations

### 3. Base Scorer Interface
- Consistent interface across all languages
- Standardized score format
- Configurable weights

## Adding Support for a New Language

### Step 1: Add Language to Enum

```python
# tapps_agents/core/language_detector.py
class Language(str, Enum):
    # ... existing languages ...
    RUST = "rust"
    GO = "go"
    # ... etc
```

### Step 2: Create Language-Specific Scorer

```python
# tapps_agents/agents/reviewer/rust_scorer.py
from .scoring import BaseScorer
from ...core.language_detector import Language

class RustScorer(BaseScorer):
    """Code quality scorer for Rust files."""
    
    def __init__(self, clippy_enabled: bool = True):
        self.clippy_enabled = clippy_enabled
        self.has_clippy = self._check_clippy_available()
    
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """Calculate scores for Rust file."""
        scores = {
            "complexity_score": self._calculate_complexity(code),
            "security_score": self._calculate_security(code),
            "maintainability_score": self._calculate_maintainability(code),
            "test_coverage_score": self._calculate_test_coverage(file_path),
            "performance_score": self._calculate_performance(code),
            "linting_score": self._calculate_linting_score(file_path),
            "overall_score": 0.0,
            "metrics": {},
        }
        
        # Calculate overall score with Rust-specific weights
        scores["overall_score"] = self._calculate_overall_score(scores)
        
        return scores
    
    # Implement language-specific calculation methods
    def _calculate_complexity(self, code: str) -> float:
        # Use Rust-specific complexity analysis
        ...
```

### Step 3: Register the Scorer

**Option A: Using Decorator (Recommended)**

```python
# tapps_agents/agents/reviewer/rust_scorer.py
from .scorer_registry import register_scorer
from ...core.language_detector import Language

@register_scorer(Language.RUST)
class RustScorer(BaseScorer):
    ...
```

**Option B: Manual Registration**

```python
# In your module's __init__.py or initialization code
from .scorer_registry import ScorerRegistry
from .rust_scorer import RustScorer
from ...core.language_detector import Language

ScorerRegistry.register(Language.RUST, RustScorer)
```

### Step 4: (Optional) Set Up Fallback Chain

If your language can fall back to another language's scorer:

```python
from .scorer_registry import ScorerRegistry

# Example: Vue files can use TypeScript scorer as fallback
ScorerRegistry.register_fallback_chain(
    Language.VUE,
    [Language.TYPESCRIPT, Language.JAVASCRIPT]
)
```

### Step 5: (Optional) Use Metric Strategies

Reuse common metrics instead of reimplementing:

```python
from .metric_strategies import (
    ComplexityStrategy,
    SecurityStrategy,
    TestCoverageStrategy,
)

class RustScorer(BaseScorer):
    def __init__(self):
        # Use generic metric strategies
        self.complexity_strategy = ComplexityStrategy()
        self.security_strategy = SecurityStrategy()
        self.test_coverage_strategy = TestCoverageStrategy()
    
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        scores = {
            "complexity_score": self.complexity_strategy.calculate(file_path, code),
            "security_score": self.security_strategy.calculate(file_path, code),
            "test_coverage_score": self.test_coverage_strategy.calculate(file_path, code),
            # ... Rust-specific metrics ...
        }
        ...
```

## Example: Adding Java Support

```python
# tapps_agents/agents/reviewer/java_scorer.py
from pathlib import Path
from typing import Any

from ...core.language_detector import Language
from .scoring import BaseScorer
from .scorer_registry import register_scorer

@register_scorer(Language.JAVA)
class JavaScorer(BaseScorer):
    """Code quality scorer for Java files."""
    
    def __init__(self, checkstyle_enabled: bool = True, spotbugs_enabled: bool = True):
        self.checkstyle_enabled = checkstyle_enabled
        self.spotbugs_enabled = spotbugs_enabled
    
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        """Calculate scores for Java file."""
        scores = {
            "complexity_score": self._calculate_complexity(code),
            "security_score": self._calculate_security(file_path, code),
            "maintainability_score": self._calculate_maintainability(code),
            "test_coverage_score": self._calculate_test_coverage(file_path),
            "performance_score": self._calculate_performance(code),
            "linting_score": self._calculate_linting_score(file_path),
            "overall_score": 0.0,
            "metrics": {},
        }
        
        # Java-specific weights
        scores["overall_score"] = (
            (10 - scores["complexity_score"]) * 0.20 +
            scores["security_score"] * 0.25 +
            scores["maintainability_score"] * 0.25 +
            scores["test_coverage_score"] * 0.15 +
            scores["performance_score"] * 0.10 +
            scores["linting_score"] * 0.05
        ) * 10
        
        return scores
    
    def _calculate_complexity(self, code: str) -> float:
        # Use Java-specific complexity analysis (cyclomatic complexity via tools)
        ...
    
    # Implement other methods...
```

## Benefits of Generic Architecture

1. **No Core Code Changes**: Add new languages without modifying `ScorerFactory` or `ReviewerAgent`
2. **Reusable Metrics**: Use common metric strategies across languages
3. **Consistent Interface**: All scorers follow the same interface
4. **Fallback Support**: Automatic fallback chains for related languages
5. **Easy Testing**: Test each scorer independently
6. **Plugin-like Extensibility**: Languages can be added via plugins or extensions

## Configuration

Language-specific configuration can be added to `config.yaml`:

```yaml
quality_tools:
  rust:
    clippy_enabled: true
    clippy_config: ".clippy.toml"
  java:
    checkstyle_enabled: true
    spotbugs_enabled: true
    checkstyle_config: "checkstyle.xml"
```

Then access in scorer:

```python
def __init__(self, config: ProjectConfig | None = None):
    quality_tools = config.quality_tools if config else None
    rust_config = getattr(quality_tools, 'rust', None) if quality_tools else None
    self.clippy_enabled = rust_config.clippy_enabled if rust_config else True
```

## Best Practices

1. **Inherit from BaseScorer**: Ensure consistent interface
2. **Use Metric Strategies**: Reuse common metrics when possible
3. **Handle Missing Tools Gracefully**: Return neutral scores when tools unavailable
4. **Document Language-Specific Features**: Comment on language-specific patterns
5. **Test Coverage**: Write tests for your scorer
6. **Follow Naming Conventions**: Use `{language}_scorer.py` naming

## Summary

The generic architecture makes it easy to add new language support:

1. Create a scorer class inheriting from `BaseScorer`
2. Register it with `@register_scorer(Language.XXX)`
3. Implement language-specific metric calculations
4. Optionally use metric strategies for common metrics
5. Optionally set up fallback chains

No core code modifications required!

