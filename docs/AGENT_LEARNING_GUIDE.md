# Agent Learning System Guide

**Version:** 2.0.5  
**Date:** January 2026  
**Status:** ✅ Complete

---

## Overview

The Agent Learning System enables agents to autonomously improve their capabilities over time by learning from past tasks, extracting successful patterns, optimizing prompts, and analyzing feedback.

**Key Features:**
- **Capability Registry**: Tracks performance metrics for each agent capability
- **Pattern Learning**: Extracts and reuses successful code patterns
- **Prompt Optimization**: A/B tests and optimizes prompts based on outcomes
- **Feedback Analysis**: Analyzes code scores to identify improvement areas
- **Hardware-Aware**: Adjusts learning intensity based on hardware profile
- **Security Integration**: Security scanning prevents learning from vulnerable code
- **Negative Feedback Learning**: Learns from failures, rejections, and low-quality code
- **Explainability**: Full transparency into learning decisions and pattern selection
- **Meta-Learning**: Self-improving system that optimizes its own learning parameters

---

## Architecture

### Components

1. **CapabilityRegistry** - Tracks agent capabilities and metrics
2. **AgentLearner** - Core learning engine
3. **PatternExtractor** - Extracts patterns from successful code
4. **AntiPatternExtractor** - Extracts anti-patterns from failures
5. **SecurityScanner** - Security scanning for pattern validation
6. **NegativeFeedbackHandler** - Handles rejections and corrections
7. **FailureModeAnalyzer** - Analyzes and categorizes failures
8. **PromptOptimizer** - Optimizes prompts via A/B testing
9. **FeedbackAnalyzer** - Analyzes code scoring feedback
10. **DecisionReasoningLogger** - Logs all learning decisions
11. **PatternSelectionExplainer** - Explains pattern selection
12. **LearningImpactReporter** - Tracks learning effectiveness
13. **LearningEffectivenessTracker** - Tracks effectiveness over time
14. **LearningSelfAssessor** - Assesses learning quality
15. **AdaptiveLearningRate** - Adjusts learning intensity
16. **LearningStrategySelector** - Selects optimal strategies
17. **LearningDashboard** - Aggregates metrics for visualization
18. **LearningAwareMixin** - Easy integration with agents

### Learning Flow

```
Task Execution
    ↓
Update Capability Metrics
    ↓
Extract Patterns (if quality > threshold)
    ↓
Analyze Feedback
    ↓
Optimize Prompts (A/B testing)
    ↓
Store in Memory System
    ↓
Refine Capabilities (if needed)
```

---

## Hardware-Aware Learning

The system automatically adjusts learning intensity based on hardware:

| Hardware Profile | Learning Intensity | Pattern Storage | Prompt Optimization |
|-----------------|-------------------|----------------|-------------------|
| NUC | LOW | Essential only | Compressed prompts |
| Development | MEDIUM | Balanced | Standard prompts |
| Workstation | HIGH | Full patterns | Detailed prompts |
| Server | HIGH | Full patterns | Detailed prompts |

---

## Usage

### Basic Setup

```python
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.learning_integration import LearningAwareMixin
from tapps_agents.core.capability_registry import CapabilityRegistry

class MyAgent(BaseAgent, LearningAwareMixin):
    def __init__(self, *args, **kwargs):
        BaseAgent.__init__(self, *args, **kwargs)
        LearningAwareMixin.__init__(self, *args, **kwargs)
        
        # Register capabilities
        self.register_capability("code_generation", initial_quality=0.5)
        self.register_capability("code_review", initial_quality=0.5)
```

### Learning from Tasks

```python
async def execute_task(self, command: str, **kwargs):
    capability_id = f"{command}_{self.agent_id}"
    task_id = kwargs.get("task_id", f"task-{uuid.uuid4()}")
    
    start_time = time.time()
    
    try:
        # Execute task
        result = await self._execute_internal(command, **kwargs)
        
        # Get code scores if available
        quality_scores = kwargs.get("quality_scores")
        code = kwargs.get("code")
        
        # Learn from task
        learning_results = self.learn_from_task(
            capability_id=capability_id,
            task_id=task_id,
            code=code,
            quality_scores=quality_scores,
            success=True,
            duration=time.time() - start_time
        )
        
        logger.info(f"Learning results: {learning_results}")
        
        return result
    except Exception as e:
        # Learn from failure
        self.learn_from_task(
            capability_id=capability_id,
            task_id=task_id,
            success=False,
            duration=time.time() - start_time
        )
        raise
```

### Using Learned Patterns

```python
def generate_code(self, context: str):
    # Get learned patterns for context
    patterns = self.get_learned_patterns(
        context=context,
        pattern_type="function",
        limit=5
    )
    
    # Use patterns in prompt
    pattern_examples = "\n".join([
        f"Example: {p.code_snippet[:100]}"
        for p in patterns
    ])
    
    prompt = f"""
    {context}
    
    Use these successful patterns:
    {pattern_examples}
    """
    
    return self._generate(prompt)
```

### Prompt Optimization

```python
def get_optimized_prompt(self, base_prompt: str, context: str):
    # Get optimized prompt (hardware-aware, A/B tested)
    optimized = self.optimize_prompt(base_prompt, context)
    
    return optimized
```

### Capability Metrics

```python
def check_capability_health(self, capability_id: str):
    metrics = self.get_capability_metrics(capability_id)
    
    if metrics:
        print(f"Quality Score: {metrics['quality_score']:.2f}")
        print(f"Success Rate: {metrics['success_rate']:.2f}")
        print(f"Usage Count: {metrics['usage_count']}")
        
        # Check if refinement needed
        if self.should_refine_capability(capability_id):
            print("⚠️  Capability needs refinement")
```

### Improvement Candidates

```python
def find_improvement_opportunities(self):
    candidates = self.get_improvement_candidates(limit=5)
    
    for candidate in candidates:
        print(f"Capability: {candidate['capability_id']}")
        print(f"  Quality: {candidate['quality_score']:.2f}")
        print(f"  Usage: {candidate['usage_count']}")
        print(f"  Success Rate: {candidate['success_rate']:.2f}")
```

---

## Integration with Code Scoring

The learning system integrates with the code scoring system to provide feedback:

```python
from tapps_agents.agents.reviewer.scoring import CodeScorer

# After code generation
scorer = CodeScorer()
scores = scorer.score_file(file_path, code)

# Learn from scores
learning_results = self.learn_from_task(
    capability_id="code_generation",
    task_id=task_id,
    code=code,
    quality_scores={
        "overall_score": scores["overall_score"],
        "metrics": scores["metrics"]
    },
    success=True
)

# Get improvement suggestions
if "improvement_suggestions" in learning_results:
    for suggestion in learning_results["improvement_suggestions"]:
        logger.info(f"💡 {suggestion}")
```

---

## Pattern Types

The system extracts several pattern types:

1. **Function Patterns**: Function definitions and structures
2. **Class Patterns**: Class definitions and architectures
3. **Import Patterns**: Import statement patterns
4. **Structural Patterns**: Decorators, context managers, etc.

### Pattern Quality Threshold

Patterns are only extracted from code with quality scores >= 0.7 (configurable).

---

## Prompt Optimization Strategies

### A/B Testing

The system automatically A/B tests prompt variants:

```python
# Create variants
optimizer = PromptOptimizer(hardware_profile)

variant1 = optimizer.create_variant(
    base_prompt="Write code",
    modifications=["add: Use type hints", "add: Add docstrings"]
)

variant2 = optimizer.create_variant(
    base_prompt="Write code",
    modifications=["add: Use async/await", "add: Add error handling"]
)

# Test variants
for variant in [variant1, variant2]:
    result = test_prompt(variant.prompt_template)
    optimizer.record_test_result(
        variant_id=variant.variant_id,
        success=result.success,
        quality_score=result.quality
    )

# Get best variant
best = optimizer.get_best_variant(min_tests=5)
```

### Hardware-Aware Optimization

Prompts are automatically optimized for hardware:

- **NUC**: Shorter prompts, essential instructions only
- **Workstation**: Full detailed prompts with examples

---

## Capability Refinement

Capabilities are automatically refined when:

1. Quality score < 0.7
2. Usage count >= 10
3. Improvement potential identified

### Refinement Types

1. **Prompt Optimization**: Improve prompts based on A/B test results
2. **Pattern Learning**: Apply successful patterns to similar tasks
3. **Feedback Loop**: Use code scoring feedback to improve

---

## Best Practices

### 1. Register Capabilities Early

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    # Register all capabilities at initialization
    self.register_capability("code_generation")
    self.register_capability("code_review")
    self.register_capability("refactoring")
```

### 2. Learn from Every Task

```python
# Always call learn_from_task after task completion
try:
    result = await execute_task()
    self.learn_from_task(capability_id, task_id, code=code, success=True)
except Exception as e:
    self.learn_from_task(capability_id, task_id, success=False)
```

### 3. Use Quality Scores

```python
# Integrate with code scoring system
scores = scorer.score_file(file_path, code)
self.learn_from_task(
    capability_id=capability_id,
    task_id=task_id,
    code=code,
    quality_scores=scores,
    success=True
)
```

### 4. Monitor Capabilities

```python
# Regularly check capability health
candidates = self.get_improvement_candidates()
for candidate in candidates:
    logger.warning(f"Capability {candidate['capability_id']} needs improvement")
```

### 5. Hardware Awareness

```python
# Learning intensity is automatic, but you can check it
intensity = self.capability_registry.get_learning_intensity()
logger.info(f"Learning intensity: {intensity.value}")
```

---

## Performance Considerations

### Storage

- **NUC**: Compressed storage, essential metrics only (<50MB)
- **Workstation**: Full storage, detailed history (<200MB)

### Learning Operations

- **Pattern Extraction**: <100ms for typical code
- **Prompt Optimization**: <50ms
- **Feedback Analysis**: <50ms
- **Metric Updates**: <10ms

### Best Practices

- Enable learning only when needed
- Limit pattern storage for NUC devices
- Use quality thresholds to filter patterns
- Regularly review improvement candidates

---

## Troubleshooting

### Learning Not Working

**Problem**: No patterns being extracted

**Solution**:
- Check quality threshold (default: 0.7)
- Verify code quality scores are provided
- Check learning intensity (may be LOW on NUC)

### High Memory Usage

**Problem**: Learning system using too much memory

**Solution**:
- Enable compression for NUC
- Reduce pattern storage limit
- Clean up old refinement history

### No Improvement

**Problem**: Capabilities not improving

**Solution**:
- Check if learning is enabled
- Verify quality scores are being provided
- Review improvement candidates
- Check capability usage count (needs >= 10)

---

## Security Integration

The learning system now includes comprehensive security scanning to prevent learning from vulnerable code. See [Learning Security Guide](LEARNING_SECURITY.md) for details.

**Key Features:**
- Automatic security scanning before pattern extraction
- Security threshold filtering (default: 7.0/10)
- Vulnerability detection and reporting
- Security scores stored with patterns

## Negative Feedback Learning

The system learns from failures, rejections, and low-quality code by extracting anti-patterns. See [Negative Feedback Learning Guide](LEARNING_NEGATIVE_FEEDBACK.md) for details.

**Key Features:**
- Automatic anti-pattern extraction from failures
- Failure mode analysis and categorization
- User rejection tracking
- Anti-pattern retrieval to avoid mistakes

## Explainability

Full transparency into learning decisions and pattern selection. See [Explainability Guide](LEARNING_EXPLAINABILITY.md) for details.

**Key Features:**
- Decision reasoning logs
- Pattern selection explanations
- Learning impact reports
- Dashboard metrics

## Meta-Learning

The system optimizes its own learning parameters autonomously. See [Meta-Learning Guide](LEARNING_META_LEARNING.md) for details.

**Key Features:**
- Effectiveness tracking over time
- Self-assessment and gap identification
- Adaptive learning rate adjustment
- Strategy selection and optimization

## See Also

- [Capability Registry](../tapps_agents/core/capability_registry.py)
- [Agent Learning](../tapps_agents/core/agent_learning.py)
- [Learning Integration](../tapps_agents/core/learning_integration.py)
- [Task Memory Guide](TASK_MEMORY_GUIDE.md)
- [Code Scoring System](../tapps_agents/agents/reviewer/scoring.py)
- [Learning Security Guide](LEARNING_SECURITY.md)
- [Negative Feedback Learning Guide](LEARNING_NEGATIVE_FEEDBACK.md)
- [Explainability Guide](LEARNING_EXPLAINABILITY.md)
- [Meta-Learning Guide](LEARNING_META_LEARNING.md)

