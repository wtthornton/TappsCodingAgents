# Negative Feedback Learning

## Overview

The agent learning system now learns from failures, rejections, and low-quality code by extracting anti-patterns. This enables agents to avoid repeating mistakes and improve over time.

## Features

### Anti-Pattern Extraction

The system automatically extracts anti-patterns from:

- **Failed Tasks**: Tasks that completed with `success=False`
- **Low-Quality Code**: Code with quality scores below threshold (default: 0.7)
- **User Rejections**: Code explicitly rejected by users
- **User Corrections**: Original code that was corrected

### Failure Mode Analysis

Failures are automatically categorized:

- **Syntax Errors**: Parse errors, indentation issues
- **Security Issues**: Vulnerabilities, insecure patterns
- **Performance Issues**: Timeouts, slow execution
- **Logic Errors**: Incorrect calculations, bugs
- **Complexity Issues**: High cyclomatic complexity
- **Maintainability Issues**: Poor code structure

### Negative Feedback Tracking

The system tracks:

- **Rejections**: User rejections with reasons
- **Corrections**: User corrections with before/after code
- **Failure Reasons**: Detailed failure analysis
- **Rejection Counts**: How often patterns were rejected

## Usage

### Learning from Failures

The system automatically learns from failed tasks:

```python
from tapps_agents.core.agent_learning import AgentLearner

learner = AgentLearner(...)

# Learn from a failed task
result = await learner.learn_from_task(
    capability_id="test",
    task_id="task_1",
    code=failed_code,
    quality_scores={"overall_score": 30.0},
    success=False,  # Task failed
)

# Check results
print(f"Anti-patterns extracted: {result['anti_patterns_extracted']}")
print(f"Failure analyzed: {result['failure_analyzed']}")
print(f"Failure mode: {result['failure_analysis']['failure_mode']}")
```

### Learning from Rejections

Explicitly learn from user rejections:

```python
result = await learner.learn_from_rejection(
    capability_id="test",
    task_id="task_2",
    code=rejected_code,
    rejection_reason="Code contains security vulnerabilities",
    quality_score=0.4,
)

print(f"Anti-patterns extracted: {result['anti_patterns_extracted']}")
print(f"Rejection recorded: {result['rejection_recorded']}")
```

### Retrieving Anti-Patterns

Get anti-patterns to avoid:

```python
# Get anti-patterns for a context
anti_patterns = learner.negative_feedback_handler.get_anti_patterns_for_context(
    context="security",
    limit=5,
)

for pattern in anti_patterns:
    print(f"Avoid: {pattern.code_snippet}")
    print(f"Reasons: {pattern.failure_reasons}")
    print(f"Rejected {pattern.rejection_count} times")
```

### Failure Mode Analysis

Analyze failure patterns:

```python
# Get common failure modes
common_modes = learner.failure_mode_analyzer.get_common_failure_modes(limit=5)

for mode in common_modes:
    print(f"Mode: {mode['mode']}")
    print(f"Count: {mode['count']}")
    print(f"Reasons: {mode['reasons']}")
```

## Anti-Pattern Data Structure

Anti-patterns extend the `CodePattern` structure:

```python
@dataclass
class CodePattern:
    # ... standard fields ...
    is_anti_pattern: bool = False
    failure_reasons: list[str] = []
    rejection_count: int = 0
    security_score: float = 0.0
```

## Pattern Filtering

By default, anti-patterns are excluded from pattern retrieval:

```python
# Get patterns (excludes anti-patterns by default)
patterns = learner.get_learned_patterns(
    context="test",
    exclude_anti_patterns=True,  # Default
)

# Include anti-patterns for "what not to do" examples
all_patterns = learner.get_learned_patterns(
    context="test",
    exclude_anti_patterns=False,
)
```

## Failure Mode Categories

### Syntax Error

**Indicators**: SyntaxError, parse errors, indentation issues

**Prevention Suggestions**:
- Use syntax checking tools (Ruff, pylint)
- Review Python syntax rules
- Check indentation

### Security Issue

**Indicators**: Security vulnerabilities, insecure patterns, low security scores

**Prevention Suggestions**:
- Run security scanning (Bandit)
- Review security best practices
- Avoid insecure patterns (eval, exec, shell=True)

### Performance Issue

**Indicators**: Timeouts, slow execution, performance warnings

**Prevention Suggestions**:
- Profile code to identify bottlenecks
- Review algorithm complexity
- Consider caching or lazy evaluation

### Logic Error

**Indicators**: Incorrect results, bugs, wrong calculations

**Prevention Suggestions**:
- Add unit tests
- Use type checking (mypy)
- Review code logic and edge cases

### Complexity Issue

**Indicators**: High cyclomatic complexity, deep nesting

**Prevention Suggestions**:
- Refactor into smaller functions
- Reduce nesting depth
- Use design patterns

### Maintainability Issue

**Indicators**: Poor structure, low maintainability scores

**Prevention Suggestions**:
- Improve documentation
- Follow consistent coding style
- Reduce code duplication

## Best Practices

1. **Review Failure Modes**: Regularly check common failure modes
2. **Learn from Rejections**: Always record user rejections
3. **Track Corrections**: Learn from both original and corrected code
4. **Monitor Anti-Patterns**: Review anti-patterns to understand what to avoid
5. **Use Failure Suggestions**: Implement prevention suggestions from failure analysis

## Integration with Learning

Negative feedback learning integrates seamlessly:

- **Automatic Extraction**: Anti-patterns extracted automatically from failures
- **Pattern Storage**: Stored alongside regular patterns with `is_anti_pattern=True`
- **Context-Aware**: Anti-patterns retrieved based on context
- **Rejection Tracking**: Patterns track how often they were rejected

## Configuration

### Quality Thresholds

- **Max Quality Threshold**: 0.7 (code below this generates anti-patterns)
- **Failure Extraction**: Enabled by default
- **Rejection Tracking**: Enabled by default

### Customization

```python
from tapps_agents.core.agent_learning import AntiPatternExtractor

extractor = AntiPatternExtractor(
    max_quality_threshold=0.6,  # Lower threshold = more anti-patterns
)
```

## See Also

- [Agent Learning Guide](AGENT_LEARNING_GUIDE.md)
- [Security Integration](LEARNING_SECURITY.md)
- [Explainability Guide](LEARNING_EXPLAINABILITY.md)

