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

## Security Best Practices

### 21. Security-Aware Pattern Learning

**Best Practice:** Always scan code for security vulnerabilities before learning.

```python
# Security scanning is automatic, but verify results
result = await learner.learn_from_task(
    capability_id="test",
    task_id="task_1",
    code=code,
    quality_scores=scores,
    success=True,
)

# Check security results
if result["security_checked"]:
    if result["security_score"] < 7.0:
        logger.warning("Code was too insecure to learn from")
        # Review vulnerabilities
        for vuln in result["security_vulnerabilities"]:
            logger.warning(f"Vulnerability: {vuln['test_name']} at line {vuln['line']}")
```

**Benefits:**
- Prevents learning vulnerable patterns
- Maintains security standards
- Protects against security regressions

### 22. Security Threshold Configuration

**Best Practice:** Set appropriate security thresholds for your security requirements.

```python
# For high-security environments
extractor = PatternExtractor(
    security_threshold=8.0,  # Stricter threshold
)

# For general development
extractor = PatternExtractor(
    security_threshold=7.0,  # Standard threshold
)
```

## Negative Feedback Learning Best Practices

### 23. Learn from Failures

**Best Practice:** Always learn from failed tasks to avoid repeating mistakes.

```python
# Automatic anti-pattern extraction from failures
result = await learner.learn_from_task(
    capability_id="test",
    task_id="task_1",
    code=failed_code,
    success=False,  # Task failed
)

# Review failure analysis
if result["failure_analyzed"]:
    failure_mode = result["failure_analysis"]["failure_mode"]
    suggestions = result["failure_analysis"]["suggestions"]
    logger.info(f"Failure mode: {failure_mode}")
    for suggestion in suggestions:
        logger.info(f"Prevention: {suggestion}")
```

**Benefits:**
- Avoids repeating mistakes
- Identifies common failure patterns
- Provides prevention strategies

### 24. Track User Rejections

**Best Practice:** Explicitly record user rejections for learning.

```python
# When user rejects code
result = await learner.learn_from_rejection(
    capability_id="test",
    task_id="task_2",
    code=rejected_code,
    rejection_reason="Code contains security vulnerabilities",
    quality_score=0.4,
)

# Anti-patterns are automatically extracted and stored
```

**Benefits:**
- Learns from explicit feedback
- Tracks rejection patterns
- Improves based on user preferences

### 25. Review Anti-Patterns

**Best Practice:** Regularly review anti-patterns to understand what to avoid.

```python
# Get anti-patterns for context
anti_patterns = learner.negative_feedback_handler.get_anti_patterns_for_context(
    context="security",
    limit=10,
)

# Review what to avoid
for pattern in anti_patterns:
    logger.warning(f"Avoid: {pattern.code_snippet[:100]}")
    logger.warning(f"Reasons: {', '.join(pattern.failure_reasons)}")
    logger.warning(f"Rejected {pattern.rejection_count} times")
```

## Explainability Best Practices

### 26. Review Decision Logs

**Best Practice:** Regularly review decision logs to understand learning behavior.

```python
# Get decision history
history = learner.decision_logger.get_decision_history(
    decision_type="pattern_extraction_threshold",
    limit=20,
)

# Review decisions
for decision in history:
    print(f"Decision: {decision.decision_type}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Confidence: {decision.confidence:.2%}")
    print(f"Sources: {', '.join(decision.sources)}")
```

**Benefits:**
- Understand learning decisions
- Identify decision patterns
- Debug learning issues

### 27. Explain Pattern Selection

**Best Practice:** Use pattern selection explanations to understand recommendations.

```python
# Get patterns with explanations
patterns = learner.get_learned_patterns(context="test")
explanation = learner.pattern_explainer.explain_pattern_selection(
    selected_patterns=patterns,
    context="test",
)

# Review why patterns were selected
for pattern_info in explanation["patterns"]:
    print(f"Pattern: {pattern_info['pattern_id']}")
    print(f"Relevance: {pattern_info['relevance_score']:.2f}")
    print(f"Justification: {pattern_info['justification']}")
```

### 28. Monitor Learning Impact

**Best Practice:** Track learning impact to measure effectiveness.

```python
# Impact is automatically tracked, but review reports
result = await learner.learn_from_task(...)

if "learning_impact" in result:
    impact = result["learning_impact"]
    print(f"Effectiveness: {impact['effectiveness']:.2f}")
    print(f"Overall Improvement: {impact['overall_improvement']:.2f}")
    
    # Review improvements by metric
    for metric, data in impact["improvements"].items():
        print(f"{metric}: {data['improvement_percent']:.1f}% improvement")
```

## Meta-Learning Best Practices

### 29. Regular Optimization

**Best Practice:** Run meta-learning optimization periodically.

```python
# Optimize learning system
optimization = await learner.optimize_learning(
    capability_id="test",
)

# Review optimization results
print(f"Quality Assessment: {optimization['quality_assessment']['quality_score']:.2f}")
print(f"Learning Gaps: {optimization['learning_gaps']}")
print(f"Optimal Strategy: {optimization['optimal_strategy']}")

# Implement suggestions
for suggestion in optimization["improvement_suggestions"]:
    logger.info(f"Improvement: {suggestion}")
```

**Benefits:**
- Autonomous optimization
- Identifies learning gaps
- Suggests improvements

### 30. Monitor Effectiveness

**Best Practice:** Track learning effectiveness over time.

```python
# Get effectiveness metrics
roi = learner.effectiveness_tracker.get_learning_roi(
    capability_id="test",
)

print(f"Total Sessions: {roi['total_sessions']}")
print(f"Average Effectiveness: {roi['average_effectiveness']:.2f}")
print(f"ROI Score: {roi['roi_score']:.2f}")

# Get effective strategies
strategies = learner.effectiveness_tracker.get_effective_strategies(
    capability_id="test",
)

# Use most effective strategies
best_strategy = max(strategies.items(), key=lambda x: x[1])
print(f"Best Strategy: {best_strategy[0]} ({best_strategy[1]:.2f})")
```

### 31. Self-Assessment

**Best Practice:** Regularly assess learning quality.

```python
# Assess learning quality
assessment = learner.self_assessor.assess_learning_quality(
    pattern_count=len(learner.pattern_extractor.patterns),
    anti_pattern_count=len(learner.anti_pattern_extractor.anti_patterns),
    average_quality=0.85,
    average_security=8.0,
)

# Identify gaps
gaps = learner.self_assessor.identify_learning_gaps(
    capability_metrics={"success_rate": 0.75},
    pattern_statistics={"total_patterns": 50, "average_quality": 0.8},
)

# Address gaps
for gap in gaps:
    logger.warning(f"Learning Gap: {gap}")
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

### ❌ Ignoring Security

**Problem:** Learning from vulnerable code introduces security risks.

**Solution:** Always use security scanning, set appropriate thresholds.

### ❌ Not Learning from Failures

**Problem:** Repeating the same mistakes without learning.

**Solution:** Always extract anti-patterns from failures and rejections.

### ❌ Lack of Explainability

**Problem:** Can't understand why learning decisions were made.

**Solution:** Review decision logs and pattern selection explanations.

### ❌ No Meta-Learning

**Problem:** Learning system doesn't improve itself.

**Solution:** Run optimization periodically, monitor effectiveness.

## References

- [Agent Learning Guide](../../../docs/AGENT_LEARNING_GUIDE.md)
- [Learning Security Guide](../../../docs/LEARNING_SECURITY.md)
- [Negative Feedback Learning Guide](../../../docs/LEARNING_NEGATIVE_FEEDBACK.md)
- [Explainability Guide](../../../docs/LEARNING_EXPLAINABILITY.md)
- [Meta-Learning Guide](../../../docs/LEARNING_META_LEARNING.md)
- [Task Memory Guide](../../../docs/TASK_MEMORY_GUIDE.md)
- [Capability Registry](../../../tapps_agents/core/capability_registry.py)
- [Agent Learning System](../../../tapps_agents/core/agent_learning.py)

