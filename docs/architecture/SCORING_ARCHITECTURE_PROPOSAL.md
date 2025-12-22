# Generic Scoring Architecture Proposal

## Current Issues

1. **Hardcoded ScorerFactory**: Uses if/elif chains that require code changes to add new languages
2. **Code Duplication**: Each scorer reimplements similar score calculation logic
3. **No Standard Extension Point**: Adding new languages requires modifying multiple files
4. **Hardcoded Weights**: Each scorer has its own weight configuration
5. **Scattered Tool Detection**: Each scorer implements tool availability checks differently

## Proposed Generic Architecture

### 1. Metric Strategy Pattern

Extract common metrics into reusable strategy classes:

```python
class MetricStrategy(Protocol):
    """Base interface for metric calculation strategies."""
    
    def calculate(self, file_path: Path, code: str, context: dict[str, Any]) -> float:
        """Calculate metric score (0-10 scale)."""
        ...
```

**Benefits:**
- Reusable across languages (complexity, security patterns apply to many languages)
- Easy to swap implementations
- Testable in isolation

### 2. Scorer Registry Pattern

Replace hardcoded factory with a registry:

```python
class ScorerRegistry:
    """Registry for language-specific scorers."""
    
    _scorers: dict[Language, type[BaseScorer]] = {}
    
    @classmethod
    def register(cls, language: Language, scorer_class: type[BaseScorer]):
        """Register a scorer for a language."""
        ...
    
    @classmethod
    def get_scorer(cls, language: Language, config: ProjectConfig) -> BaseScorer:
        """Get appropriate scorer (with fallback chain)."""
        ...
```

**Benefits:**
- New languages can register without modifying factory code
- Supports fallback chains (e.g., React → TypeScript → Generic)
- Plugin-like extensibility

### 3. Layered Scorer Composition

Make ReactScorer's composition pattern generic:

```python
class LayeredScorer(BaseScorer):
    """Scorer that wraps another scorer with additional metrics."""
    
    def __init__(self, base_scorer: BaseScorer, layer_metrics: list[MetricStrategy]):
        self.base_scorer = base_scorer
        self.layer_metrics = layer_metrics
```

**Benefits:**
- Generic way to add framework-specific metrics (React, Vue, Angular, etc.)
- Reusable pattern for technology stacks

### 4. Tool Detection Abstraction

Standardize tool detection:

```python
class ToolDetector:
    """Generic tool availability detector."""
    
    def __init__(self, tool_config: dict[str, Any]):
        self.config = tool_config
    
    def is_available(self, tool_name: str) -> bool:
        """Check if tool is available."""
        ...
```

**Benefits:**
- Consistent tool detection across all scorers
- Configurable tool requirements per language

### 5. Configurable Score Weights

Make weights language-aware and configurable:

```yaml
scoring:
  weights:
    python:
      complexity: 0.20
      security: 0.30
      ...
    typescript:
      complexity: 0.20
      security: 0.15
      ...
```

## Implementation Plan

### Phase 1: Extract Common Metrics (Strategy Pattern)

Create metric strategies for:
- Complexity (already language-agnostic patterns)
- Security (common patterns across languages)
- Test Coverage (framework-agnostic heuristics)

### Phase 2: Create Scorer Registry

Replace ScorerFactory with registry:
- Auto-registration via decorators
- Fallback chain support
- Language inheritance (React → TypeScript)

### Phase 3: Standardize Tool Detection

- Create ToolDetector class
- Migrate all tool checks to use it
- Make tool requirements configurable

### Phase 4: Configurable Weights

- Add language-specific weight configs
- Default weights with overrides
- Validation for weight sums

## Benefits

1. **Extensibility**: Add new languages without modifying core code
2. **Maintainability**: Reduce duplication, single source of truth
3. **Testability**: Test metrics and scorers independently
4. **Flexibility**: Configure weights, tools, and metrics per language
5. **Composability**: Build complex scorers from simple building blocks

