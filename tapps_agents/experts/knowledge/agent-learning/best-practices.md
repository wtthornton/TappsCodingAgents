# Self-Improving Agents Best Practices

## Overview

Self-improving agents learn from past tasks to enhance their capabilities over time. This guide covers best practices for implementing and using agent learning systems effectively.

## Core Principles

### 1. Incremental Learning

**Best Practice:** Learn incrementally from each task, not in batches.

```python
# Good: Learn after each task
async def execute_task(self, command: str, **kwargs):
    result = await self._execute_internal(command, **kwargs)
    self.learn_from_task(capability_id, task_id, code=code, success=True)
    return result

# Bad: Learning in batches
# This delays learning and reduces responsiveness
```

**Benefits:**
- Immediate feedback loop
- Faster adaptation to new patterns
- Better real-time performance tracking

### 2. Quality Threshold Filtering

**Best Practice:** Only extract patterns from high-quality code (quality_score >= 0.7).

```python
# Set appropriate quality threshold
extractor = PatternExtractor(min_quality_threshold=0.7)

# Only extract from successful, high-quality tasks
if quality_score >= 0.7:
    patterns = extractor.extract_patterns(code, quality_score, task_id)
```

**Rationale:**
- Prevents learning bad patterns
- Focuses on successful approaches
- Reduces noise in pattern library

### 3. Hardware-Aware Learning Intensity

**Best Practice:** Adjust learning intensity based on hardware profile.

```python
# Automatic hardware detection
profiler = HardwareProfiler()
profile = profiler.detect_profile()

# Learning intensity adjusts automatically:
# - NUC: LOW (minimal learning, essential patterns only)
# - Development: MEDIUM (balanced learning)
# - Workstation: HIGH (aggressive learning)
```

**Benefits:**
- Optimal performance on all hardware
- Resource-efficient on low-power devices
- Full learning on high-performance systems

## Capability Management

### 4. Early Capability Registration

**Best Practice:** Register all capabilities at agent initialization.

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    # Register all capabilities upfront
    self.register_capability("code_generation", initial_quality=0.5)
    self.register_capability("code_review", initial_quality=0.5)
    self.register_capability("refactoring", initial_quality=0.5)
```

**Benefits:**
- Consistent metric tracking from start
- Better historical data
- Clearer capability boundaries

### 5. Granular Capability Definition

**Best Practice:** Define capabilities at appropriate granularity.

```python
# Good: Specific capabilities
self.register_capability("python_function_generation")
self.register_capability("python_class_generation")
self.register_capability("typescript_interface_generation")

# Bad: Too broad
self.register_capability("code_generation")  # Too generic
```

**Benefits:**
- More accurate metrics per capability
- Better pattern matching
- Targeted improvements

### 6. Regular Capability Health Checks

**Best Practice:** Monitor capability health and identify improvement candidates.

```python
# Check for capabilities needing improvement
candidates = self.get_improvement_candidates(limit=5)

for candidate in candidates:
    if candidate['quality_score'] < 0.6:
        logger.warning(f"Capability {candidate['capability_id']} needs attention")
        # Trigger refinement process
```

## Pattern Learning

### 7. Context-Aware Pattern Retrieval

**Best Practice:** Retrieve patterns based on task context.

```python
# Get relevant patterns for current task
patterns = self.get_learned_patterns(
    context="Generate REST API endpoint",
    pattern_type="function",
    limit=5
)

# Use patterns in prompt
pattern_examples = "\n".join([p.code_snippet for p in patterns])
prompt = f"{base_prompt}\n\nUse these successful patterns:\n{pattern_examples}"
```

**Benefits:**
- More relevant pattern suggestions
- Better code generation quality
- Faster task completion

### 8. Pattern Versioning and Evolution

**Best Practice:** Track pattern usage and evolve successful patterns.

```python
# Patterns automatically track:
# - Usage count
# - Success rate
# - Quality scores
# - Learned from task IDs

# Use patterns with highest success rates
patterns.sort(key=lambda p: (p.success_rate, p.quality_score), reverse=True)
```

### 9. Pattern Diversity

**Best Practice:** Maintain diverse pattern library, not just top patterns.

```python
# Don't just use top 1 pattern
# Use diverse set of successful patterns
patterns = self.get_learned_patterns(context, limit=5)

# This provides:
# - Multiple approaches
# - Fallback options
# - Creative solutions
```

## Prompt Optimization

### 10. A/B Testing Strategy

**Best Practice:** Systematically test prompt variants.

```python
# Create variants with specific modifications
variant1 = optimizer.create_variant(
    base_prompt="Write code",
    modifications=["add: Use type hints", "add: Add docstrings"]
)

variant2 = optimizer.create_variant(
    base_prompt="Write code",
    modifications=["add: Use async/await", "add: Add error handling"]
)

# Test both variants
for variant in [variant1, variant2]:
    result = test_prompt(variant.prompt_template)
    optimizer.record_test_result(variant.variant_id, result.success, result.quality)
```

**Best Practices:**
- Test at least 5 times per variant
- Use statistical significance
- Consider context-specific variants

### 11. Hardware-Aware Prompt Optimization

**Best Practice:** Optimize prompts for hardware profile.

```python
# Automatic optimization
optimized = self.optimize_prompt(base_prompt, context)

# For NUC: Shorter, essential instructions only
# For Workstation: Full detailed prompts
```

**Benefits:**
- Faster execution on low-power devices
- Better quality on high-performance systems
- Optimal resource utilization

## Feedback Integration

### 12. Code Scoring Integration

**Best Practice:** Use code scoring system for learning feedback.

```python
from tapps_agents.agents.reviewer.scoring import CodeScorer

# After code generation
scorer = CodeScorer()
scores = scorer.score_file(file_path, code)

# Learn from scores
self.learn_from_task(
    capability_id=capability_id,
    task_id=task_id,
    code=code,
    quality_scores={
        "overall_score": scores["overall_score"],
        "metrics": scores["metrics"]
    },
    success=True
)
```

**Benefits:**
- Objective quality metrics
- Identifies weak areas
- Provides improvement suggestions

### 13. Multi-Metric Feedback

**Best Practice:** Consider all quality metrics, not just overall score.

```python
# Analyze individual metrics
analysis = feedback_analyzer.analyze_code_scores(scores, threshold=0.7)

# Focus on weak areas
for area in analysis["weak_areas"]:
    potential = analysis["improvement_potential"][area]
    if potential > 0.1:
        # Target improvement for this area
        improve_metric(area, potential)
```

## Performance Optimization

### 14. Lazy Pattern Loading

**Best Practice:** Load patterns only when needed.

```python
# Don't load all patterns at initialization
# Load on-demand based on context
patterns = self.get_learned_patterns(context, limit=5)  # Only load 5 relevant patterns
```

**Benefits:**
- Faster initialization
- Lower memory usage
- Better scalability

### 15. Pattern Storage Limits

**Best Practice:** Limit pattern storage based on hardware.

```python
# For NUC: Store only top 100 patterns
# For Workstation: Store up to 1000 patterns

if hardware_profile == HardwareProfile.NUC:
    max_patterns = 100
else:
    max_patterns = 1000
```

### 16. Metric Compression

**Best Practice:** Compress refinement history for NUC devices.

```python
# Automatic compression for NUC
if hardware_profile == HardwareProfile.NUC:
    # Store only essential refinement records
    # Compress old history
    compress_refinement_history(metric, keep_last=10)
```

## Integration Best Practices

### 17. Learning Hooks

**Best Practice:** Add learning hooks at key execution points.

```python
async def execute_task(self, command: str, **kwargs):
    capability_id = f"{command}_{self.agent_id}"
    task_id = kwargs.get("task_id", f"task-{uuid.uuid4()}")
    start_time = time.time()
    
    try:
        result = await self._execute_internal(command, **kwargs)
        
        # Learning hook: After successful execution
        self.learn_from_task(
            capability_id=capability_id,
            task_id=task_id,
            code=kwargs.get("code"),
            quality_scores=kwargs.get("quality_scores"),
            success=True,
            duration=time.time() - start_time
        )
        
        return result
    except Exception as e:
        # Learning hook: After failure
        self.learn_from_task(
            capability_id=capability_id,
            task_id=task_id,
            success=False,
            duration=time.time() - start_time
        )
        raise
```

### 18. Memory System Integration

**Best Practice:** Integrate with TaskMemory system for knowledge retention.

```python
# Learning system automatically stores in memory
# Patterns are linked to tasks
# Knowledge graph tracks relationships

# Retrieve similar tasks
similar_tasks = self.memory_system.get_similar_tasks(task_id)

# Use patterns from similar tasks
for similar_task in similar_tasks:
    patterns.extend(similar_task.patterns_used)
```

## Monitoring and Analytics

### 19. Capability Metrics Dashboard

**Best Practice:** Regularly review capability metrics.

```python
# Get capability health
metrics = self.get_capability_metrics(capability_id)

# Monitor:
# - Quality score trends
# - Success rate
# - Usage count
# - Refinement history
```

### 20. Learning Effectiveness Tracking

**Best Practice:** Track learning effectiveness over time.

```python
# Compare metrics before/after learning
before_quality = metric.quality_score
# ... learning period ...
after_quality = metric.quality_score

improvement = (after_quality - before_quality) / before_quality * 100
logger.info(f"Quality improved by {improvement:.1f}%")
```

## Common Pitfalls to Avoid

### ❌ Learning from All Tasks

**Problem:** Learning from low-quality tasks pollutes pattern library.

**Solution:** Use quality threshold filtering (>= 0.7).

### ❌ Too Many Capabilities

**Problem:** Over-granular capabilities fragment metrics.

**Solution:** Balance granularity - specific but not excessive.

### ❌ Ignoring Hardware Profile

**Problem:** Same learning intensity on all hardware wastes resources.

**Solution:** Use hardware-aware learning intensity.

### ❌ No Feedback Loop

**Problem:** Learning without quality feedback is blind.

**Solution:** Integrate code scoring system for objective feedback.

### ❌ Pattern Overfitting

**Problem:** Using same patterns repeatedly reduces creativity.

**Solution:** Maintain diverse pattern library, use multiple patterns.

## References

- [Agent Learning Guide](../../../docs/AGENT_LEARNING_GUIDE.md)
- [Task Memory Guide](../../../docs/TASK_MEMORY_GUIDE.md)
- [Capability Registry](../../../tapps_agents/core/capability_registry.py)
- [Agent Learning System](../../../tapps_agents/core/agent_learning.py)

