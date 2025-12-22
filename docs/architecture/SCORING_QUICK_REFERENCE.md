# Scoring Architecture - Quick Reference

## Current Architecture

### Components

1. **BaseScorer** (`scoring.py`)
   - Protocol/interface all scorers must implement
   - Defines `score_file(file_path, code) -> dict[str, Any]`

2. **ScorerRegistry** (`scorer_registry.py`)
   - Central registry for language-specific scorers
   - Supports registration and fallback chains
   - Handles scorer instantiation with config

3. **ScorerFactory** (`scoring.py`)
   - Public API for getting scorers
   - Uses ScorerRegistry internally
   - Maintains backward compatibility

4. **Metric Strategies** (`metric_strategies.py`)
   - Reusable metric calculation logic
   - Language-agnostic patterns

### Built-in Scorers

Currently supported languages:
- ✅ **Python** - `CodeScorer` (via hardcoded instantiation)
- ✅ **TypeScript** - `TypeScriptScorer` (via hardcoded instantiation)
- ✅ **JavaScript** - `TypeScriptScorer` (via hardcoded instantiation)
- ✅ **React** - `ReactScorer` (via hardcoded instantiation)

### Usage

```python
from tapps_agents.agents.reviewer.scoring import ScorerFactory
from tapps_agents.core.language_detector import Language

# Get scorer for a language
scorer = ScorerFactory.get_scorer(Language.PYTHON, config)
scores = scorer.score_file(file_path, code)
```

### Adding New Language

```python
from tapps_agents.agents.reviewer.scoring import BaseScorer
from tapps_agents.agents.reviewer.scorer_registry import register_scorer
from tapps_agents.core.language_detector import Language

@register_scorer(Language.GO)
class GoScorer(BaseScorer):
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        # Implement scoring logic
        return {
            "complexity_score": ...,
            "security_score": ...,
            "maintainability_score": ...,
            "overall_score": ...,
            "metrics": {...}
        }
```

### Using Metric Strategies

```python
from tapps_agents.agents.reviewer.metric_strategies import (
    ComplexityStrategy,
    SecurityStrategy,
    TestCoverageStrategy,
)

class MyScorer(BaseScorer):
    def __init__(self):
        self.complexity = ComplexityStrategy()
        self.security = SecurityStrategy()
        self.test_coverage = TestCoverageStrategy()
    
    def score_file(self, file_path: Path, code: str) -> dict[str, Any]:
        return {
            "complexity_score": self.complexity.calculate(file_path, code),
            "security_score": self.security.calculate(file_path, code),
            "test_coverage_score": self.test_coverage.calculate(file_path, code),
            # ... other metrics
        }
```

### Fallback Chains

```python
from tapps_agents.agents.reviewer.scorer_registry import ScorerRegistry

# React automatically falls back to TypeScript, then JavaScript
ScorerRegistry.register_fallback_chain(
    Language.VUE,
    [Language.TYPESCRIPT, Language.JAVASCRIPT]
)
```

## Architecture Benefits

✅ **Extensible** - Add languages without core code changes  
✅ **Reusable** - Common metrics via strategies  
✅ **Composable** - Build complex scorers from simple parts  
✅ **Backward Compatible** - Existing code continues to work  
✅ **Testable** - Each component can be tested independently  

## Files

- `tapps_agents/agents/reviewer/scoring.py` - BaseScorer, CodeScorer, ScorerFactory
- `tapps_agents/agents/reviewer/scorer_registry.py` - Registration system
- `tapps_agents/agents/reviewer/metric_strategies.py` - Reusable metrics
- `tapps_agents/agents/reviewer/typescript_scorer.py` - TypeScript/JS scorer
- `tapps_agents/agents/reviewer/react_scorer.py` - React scorer

## Next Steps

1. Create `GenericScorer` using metric strategies for unknown languages
2. Register built-in scorers explicitly (avoid hardcoded instantiation)
3. Add more metric strategies (performance, maintainability)
4. Make weights configurable per language in config.yaml

