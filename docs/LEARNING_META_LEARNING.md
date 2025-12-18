# Meta-Learning System

## Overview

The meta-learning system enables the learning system to learn about its own learning effectiveness and optimize learning parameters autonomously. This creates a self-improving learning system that adapts to its environment.

## Features

### Learning Effectiveness Tracking

Tracks learning effectiveness over time:

- **Session Tracking**: Tracks each learning session with before/after metrics
- **Improvement Rates**: Calculates improvement rates over time
- **Strategy Effectiveness**: Identifies which learning strategies work best
- **ROI Calculation**: Calculates return on learning investment

### Self-Assessment

The system assesses its own learning quality:

- **Quality Assessment**: Evaluates overall learning quality
- **Pattern Evaluation**: Assesses pattern library quality
- **Gap Identification**: Identifies areas needing improvement
- **Improvement Suggestions**: Suggests how to improve learning

### Adaptive Learning Rate

Dynamically adjusts learning intensity:

- **Effectiveness-Based**: Adjusts based on recent effectiveness
- **Threshold Optimization**: Optimizes quality thresholds
- **Exploration Balance**: Balances exploration vs exploitation
- **Hardware Adaptation**: Adapts to hardware constraints

### Learning Strategy Selection

Selects optimal learning strategies:

- **Strategy Types**: Conservative, Balanced, Aggressive, Adaptive
- **A/B Testing**: Tests strategy effectiveness
- **Strategy Switching**: Switches to better strategies automatically
- **Parameter Optimization**: Optimizes strategy parameters

## Usage

### Effectiveness Tracking

Effectiveness is automatically tracked:

```python
from tapps_agents.core.agent_learning import AgentLearner

learner = AgentLearner(...)

# Learning automatically tracks effectiveness
result = await learner.learn_from_task(...)

# Check effectiveness tracking
if "learning_impact" in result:
    impact = result["learning_impact"]
    print(f"Effectiveness: {impact['effectiveness']:.2f}")
    print(f"Improvement: {impact['overall_improvement']:.2f}")
```

### Learning Optimization

Run meta-learning optimization:

```python
# Optimize learning system
optimization = await learner.optimize_learning(
    capability_id="test",
)

print(f"Quality Assessment: {optimization['quality_assessment']}")
print(f"Learning Gaps: {optimization['learning_gaps']}")
print(f"Optimal Strategy: {optimization['optimal_strategy']}")
print(f"Optimized Threshold: {optimization['optimized_threshold']}")

# Check if strategy was switched
if optimization.get("strategy_switched"):
    print(f"Switched to: {optimization['switch_result']['new_strategy']}")
```

### Effectiveness Metrics

Get effectiveness metrics:

```python
# Get improvement rate
rate = learner.effectiveness_tracker.calculate_improvement_rate(
    capability_id="test",
    days=30,
)

print(f"Sessions: {rate['sessions_count']}")
print(f"Average Improvement: {rate['average_improvement']:.2f}%")
print(f"Improvement Rate: {rate['improvement_rate']:.2f}%")

# Get effective strategies
strategies = learner.effectiveness_tracker.get_effective_strategies(
    capability_id="test",
)

for strategy, effectiveness in strategies.items():
    print(f"{strategy}: {effectiveness:.2f}")

# Get learning ROI
roi = learner.effectiveness_tracker.get_learning_roi(
    capability_id="test",
)

print(f"Total Sessions: {roi['total_sessions']}")
print(f"ROI Score: {roi['roi_score']:.2f}")
```

### Self-Assessment

Assess learning quality:

```python
# Assess learning quality
assessment = learner.self_assessor.assess_learning_quality(
    pattern_count=len(learner.pattern_extractor.patterns),
    anti_pattern_count=len(learner.anti_pattern_extractor.anti_patterns),
    average_quality=0.85,
    average_security=8.0,
)

print(f"Quality Score: {assessment['quality_score']:.2f}")
print(f"Pattern Count: {assessment['pattern_count']}")
print(f"Average Quality: {assessment['average_quality']:.2f}")

# Identify learning gaps
gaps = learner.self_assessor.identify_learning_gaps(
    capability_metrics={"success_rate": 0.75},
    pattern_statistics={
        "total_patterns": 5,
        "average_quality": 0.6,
        "average_security": 6.0,
    },
)

print("Learning Gaps:")
for gap in gaps:
    print(f"  - {gap}")

# Get improvement suggestions
suggestions = learner.self_assessor.suggest_improvements(assessment)
print("Suggestions:")
for suggestion in suggestions:
    print(f"  - {suggestion}")
```

### Adaptive Learning Rate

Monitor and adjust learning rate:

```python
# Get current learning rate
current_rate = learner.adaptive_rate.current_rate
print(f"Current Rate: {current_rate:.2f}")

# Adjust based on effectiveness
adjustment = learner.adaptive_rate.adjust_learning_intensity(0.85)

print(f"Previous Rate: {adjustment['previous_rate']:.2f}")
print(f"New Rate: {adjustment['new_rate']:.2f}")
print(f"Adjustment: {adjustment['adjustment']:+.2f}")

# Optimize thresholds
optimized = learner.adaptive_rate.optimize_thresholds(
    current_threshold=0.7,
    success_rate=0.95,
    quality_score=0.85,
)

print(f"Optimized Threshold: {optimized:.2f}")

# Balance exploration
balance = learner.adaptive_rate.balance_exploration(exploration_rate=0.1)
print(f"Exploration: {balance['exploration_rate']:.2f}")
print(f"Exploitation: {balance['exploitation_rate']:.2f}")
```

### Strategy Selection

Work with learning strategies:

```python
# Get current strategy
current = learner.current_strategy
print(f"Current Strategy: {current.value}")

# Select optimal strategy
optimal = learner.strategy_selector.select_strategy(
    capability_id="test",
    current_effectiveness=0.85,
    hardware_profile="workstation",
)

print(f"Optimal Strategy: {optimal.value}")

# Test strategy
test_result = learner.strategy_selector.test_strategy(
    strategy=LearningStrategy.AGGRESSIVE,
    effectiveness=0.9,
)

print(f"Strategy: {test_result['strategy']}")
print(f"Effectiveness: {test_result['effectiveness']:.2f}")
print(f"Average: {test_result['average_effectiveness']:.2f}")

# Optimize strategy parameters
parameters = {
    "quality_threshold": 0.7,
    "security_threshold": 7.0,
}

optimized = learner.strategy_selector.optimize_strategy(
    strategy=LearningStrategy.CONSERVATIVE,
    parameters=parameters,
)

print(f"Optimized Parameters: {optimized}")
```

## Learning Strategies

### Conservative

- **Thresholds**: High (quality ≥ 0.8, security ≥ 8.0)
- **Learning Speed**: Slow
- **Use Case**: High-security environments, critical systems
- **Hardware**: NUC, resource-constrained

### Balanced

- **Thresholds**: Medium (quality ≥ 0.7, security ≥ 7.0)
- **Learning Speed**: Moderate
- **Use Case**: General development, standard projects
- **Hardware**: Workstation, standard resources

### Aggressive

- **Thresholds**: Low (quality ≥ 0.6, security ≥ 6.0)
- **Learning Speed**: Fast
- **Use Case**: Rapid prototyping, experimental code
- **Hardware**: High-performance workstations

### Adaptive

- **Thresholds**: Dynamic (based on effectiveness)
- **Learning Speed**: Variable
- **Use Case**: Autonomous optimization
- **Hardware**: Any

## Best Practices

1. **Regular Optimization**: Run `optimize_learning()` periodically
2. **Monitor Effectiveness**: Track effectiveness metrics over time
3. **Review Strategies**: Review which strategies work best for your use case
4. **Adjust Thresholds**: Fine-tune thresholds based on effectiveness
5. **Balance Exploration**: Maintain exploration/exploitation balance

## Configuration

### Strategy Selection

The system automatically selects strategies based on:

- **Effectiveness**: Current learning effectiveness
- **Hardware**: Hardware profile (NUC vs Workstation)
- **Capability**: Specific capability requirements

### Adaptive Parameters

The system automatically adjusts:

- **Learning Rate**: Based on effectiveness
- **Quality Thresholds**: Based on success rates
- **Security Thresholds**: Based on security scores
- **Exploration Rate**: Based on effectiveness history

## Integration

Meta-learning integrates throughout the system:

- **Automatic Tracking**: Effectiveness tracked during every learning session
- **Automatic Adjustment**: Learning rate adjusted based on effectiveness
- **Automatic Optimization**: Thresholds optimized based on performance
- **Automatic Strategy Selection**: Strategies selected based on context

## See Also

- [Agent Learning Guide](AGENT_LEARNING_GUIDE.md)
- [Explainability Guide](LEARNING_EXPLAINABILITY.md)
- [Security Integration](LEARNING_SECURITY.md)

