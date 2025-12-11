# Pattern Extraction Best Practices

## Overview

Pattern extraction is the process of identifying and storing successful code patterns from high-quality task outputs. This guide covers best practices for effective pattern extraction.

## Pattern Types

### Function Patterns

**Best Practice:** Extract function patterns with clear signatures and implementations.

```python
# Good: Clear function pattern
def calculate_total(items: List[Item]) -> float:
    """Calculate total price of items."""
    return sum(item.price for item in items)

# Pattern includes:
# - Type hints
# - Docstring
# - Clear logic
# - Return type
```

**Extraction Criteria:**
- Function has type hints
- Function has docstring
- Function is under 50 lines
- Function has quality_score >= 0.7

### Class Patterns

**Best Practice:** Extract class patterns with clear structure and responsibilities.

```python
# Good: Well-structured class pattern
class UserService:
    """Service for user operations."""
    
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID."""
        return self.repository.find_by_id(user_id)
```

**Extraction Criteria:**
- Class has clear single responsibility
- Methods are well-organized
- Type hints present
- Docstrings present

### Import Patterns

**Best Practice:** Extract common import patterns for libraries.

```python
# Good: Standard import pattern
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
```

**Extraction Criteria:**
- Imports follow project conventions
- Standard library imports first
- Third-party imports second
- Local imports last

### Structural Patterns

**Best Practice:** Extract decorators, context managers, and other structural patterns.

```python
# Good: Decorator pattern
@dataclass
class Task:
    task_id: str
    status: str

# Good: Context manager pattern
with open(file_path) as f:
    content = f.read()
```

## Quality Thresholds

### Minimum Quality Score

**Best Practice:** Only extract patterns from code with quality_score >= 0.7.

```python
extractor = PatternExtractor(min_quality_threshold=0.7)

# Only high-quality patterns are extracted
patterns = extractor.extract_patterns(
    code=code,
    quality_score=0.8,  # Above threshold
    task_id=task_id
)
```

**Rationale:**
- Prevents learning bad patterns
- Focuses on successful approaches
- Maintains pattern library quality

### Multi-Metric Quality

**Best Practice:** Consider all quality metrics, not just overall score.

```python
# Check individual metrics
if (scores["complexity"] >= 7.0 and
    scores["security"] >= 7.0 and
    scores["maintainability"] >= 7.0):
    # Extract patterns
    patterns = extractor.extract_patterns(code, quality_score, task_id)
```

## Pattern Storage

### Pattern Limits

**Best Practice:** Limit pattern storage based on hardware profile.

```python
# NUC: Store top 100 patterns
# Workstation: Store top 1000 patterns

if hardware_profile == HardwareProfile.NUC:
    max_patterns = 100
else:
    max_patterns = 1000

# Keep only highest quality patterns
patterns.sort(key=lambda p: p.quality_score, reverse=True)
patterns = patterns[:max_patterns]
```

### Pattern Deduplication

**Best Practice:** Avoid storing duplicate patterns.

```python
# Check if pattern already exists
existing_pattern = find_similar_pattern(new_pattern)

if existing_pattern:
    # Update existing pattern
    existing_pattern.usage_count += 1
    existing_pattern.learned_from.append(task_id)
else:
    # Store new pattern
    store_pattern(new_pattern)
```

### Pattern Metadata

**Best Practice:** Store comprehensive pattern metadata.

```python
pattern = CodePattern(
    pattern_id="func_calculate_total_1234",
    pattern_type="function",
    code_snippet=code_snippet,
    context="Calculate total from list of items",
    quality_score=0.85,
    usage_count=1,
    success_rate=1.0,
    learned_from=[task_id],
    metadata={
        "language": "python",
        "framework": "none",
        "complexity": "low",
        "dependencies": []
    }
)
```

## Pattern Retrieval

### Context Matching

**Best Practice:** Retrieve patterns based on task context.

```python
# Match patterns to context
patterns = extractor.get_patterns_for_context(
    context="Calculate total price",
    pattern_type="function",
    limit=5
)

# Patterns are ranked by:
# 1. Quality score
# 2. Usage count
# 3. Context relevance
```

### Pattern Diversity

**Best Practice:** Retrieve diverse patterns, not just top pattern.

```python
# Get multiple patterns for variety
patterns = extractor.get_patterns_for_context(context, limit=5)

# This provides:
# - Multiple approaches
# - Fallback options
# - Creative solutions
```

## Pattern Evolution

### Usage Tracking

**Best Practice:** Track pattern usage and success rates.

```python
# Update pattern on each use
pattern.usage_count += 1

# Track success
if task_successful:
    pattern.success_rate = update_success_rate(pattern.success_rate, True)
else:
    pattern.success_rate = update_success_rate(pattern.success_rate, False)
```

### Pattern Refinement

**Best Practice:** Refine patterns based on usage feedback.

```python
# If pattern success rate drops below threshold
if pattern.success_rate < 0.6:
    # Mark for review
    mark_pattern_for_review(pattern)
    
    # Consider removing or updating
    if pattern.usage_count > 10:
        remove_pattern(pattern)
```

## Anti-Patterns

### ❌ Extracting from Low-Quality Code

**Problem:** Learning bad patterns pollutes library.

**Solution:** Use quality threshold (>= 0.7).

### ❌ Storing Too Many Patterns

**Problem:** Pattern library becomes unwieldy.

**Solution:** Limit storage based on hardware, keep only top patterns.

### ❌ Ignoring Context

**Problem:** Patterns retrieved don't match task context.

**Solution:** Use context-aware pattern retrieval.

### ❌ No Pattern Evolution

**Problem:** Patterns become outdated.

**Solution:** Track usage and success rates, refine or remove underperforming patterns.

## References

- [Agent Learning Guide](../../../docs/AGENT_LEARNING_GUIDE.md)
- [PatternExtractor](../../../tapps_agents/core/agent_learning.py)

