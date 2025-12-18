# Learning System Explainability

## Overview

The agent learning system now provides comprehensive explainability, allowing you to understand why decisions were made, which patterns were selected, and how learning is impacting performance.

## Features

### Decision Reasoning Logger

All learning decisions are logged with full context:

- **Decision History**: Complete history of all learning decisions
- **Reasoning Chains**: Full reasoning for each decision
- **Source Tracking**: Tracks whether decisions came from learned experience or best practices
- **Confidence Scores**: Confidence levels for each decision

### Pattern Selection Explanation

Understand why patterns were selected:

- **Relevance Scores**: How relevant each pattern is to the context
- **Quality Metrics**: Quality, security, and usage statistics
- **Justification**: Human-readable explanations for selections
- **Comparison**: Compare multiple patterns side-by-side

### Learning Impact Reports

Track learning effectiveness:

- **Before/After Metrics**: Compare metrics before and after learning
- **Improvement Tracking**: Track improvements over time
- **Effectiveness Scores**: Calculate learning effectiveness
- **Export Reports**: Export reports in Markdown or JSON

### Learning Dashboard

Aggregated metrics and visualizations:

- **Capability Metrics**: Performance metrics per capability
- **Pattern Statistics**: Pattern library statistics
- **Security Metrics**: Security learning metrics
- **Failure Analysis**: Common failure modes and trends

## Usage

### Decision Logging

Decisions are automatically logged:

```python
from tapps_agents.core.agent_learning import AgentLearner

learner = AgentLearner(...)

# Learning automatically logs decisions
result = await learner.learn_from_task(...)

# Get decision history
history = learner.decision_logger.get_decision_history(
    decision_type="pattern_extraction_threshold",
    limit=10,
)

for decision in history:
    print(f"Decision: {decision.decision_type}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Confidence: {decision.confidence}")
    print(f"Sources: {decision.sources}")
```

### Explaining Decisions

Get human-readable explanations:

```python
# Get explanation for a specific decision
explanation = learner.decision_logger.explain_decision(decision_id)

print(explanation["explanation"])
# "Decision 'pattern_extraction_threshold' was made with 85.0% confidence.
#  Reasoning: High confidence from learned experience.
#  Sources: learned_experience."
```

### Pattern Selection Explanation

Understand why patterns were selected:

```python
# Get patterns
patterns = learner.get_learned_patterns(context="test")

# Explain selection
explanation = learner.pattern_explainer.explain_pattern_selection(
    selected_patterns=patterns,
    context="test",
)

print(f"Selected {explanation['selected_count']} patterns")
for pattern_info in explanation["patterns"]:
    print(f"Pattern: {pattern_info['pattern_id']}")
    print(f"Relevance: {pattern_info['relevance_score']}")
    print(f"Justification: {pattern_info['justification']}")
```

### Learning Impact Reports

Track learning effectiveness:

```python
# Impact reports are automatically generated during learning
result = await learner.learn_from_task(...)

if "learning_impact" in result:
    impact = result["learning_impact"]
    print(f"Overall Improvement: {impact['overall_improvement']}")
    print(f"Effectiveness: {impact['effectiveness']}")
    
    for metric, data in impact["improvements"].items():
        print(f"{metric}: {data['before']} -> {data['after']} "
              f"({data['improvement_percent']:.1f}% improvement)")
```

### Exporting Reports

Export reports in various formats:

```python
from tapps_agents.core.learning_explainability import LearningImpactReporter

reporter = LearningImpactReporter()

# Generate report
report = reporter.generate_impact_report(
    capability_id="test",
    before_metrics={"quality_score": 0.7},
    after_metrics={"quality_score": 0.85},
)

# Export as Markdown
markdown = reporter.export_report(report, format="markdown")
print(markdown)

# Export as JSON
json_str = reporter.export_report(report, format="json")
print(json_str)
```

### Learning Dashboard

Get comprehensive dashboard data:

```python
# Get complete dashboard data
dashboard = learner.dashboard.get_dashboard_data(
    capability_id="test",
    include_trends=True,
    include_failures=True,
    failure_mode_analyzer=learner.failure_mode_analyzer,
)

print(f"Capability Metrics: {dashboard['capability_metrics']}")
print(f"Pattern Statistics: {dashboard['pattern_statistics']}")
print(f"Security Metrics: {dashboard['security_metrics']}")
print(f"Decision Statistics: {dashboard['decision_statistics']}")
```

### Explaining Learning Process

Get comprehensive learning explanation:

```python
# Explain entire learning process
explanation = await learner.explain_learning(
    capability_id="test",
    task_id="task_1",
)

print("Decision Statistics:", explanation["decision_statistics"])
print("Pattern Selection:", explanation["pattern_selection"])
if "decision" in explanation:
    print("Decision Details:", explanation["decision"])
```

## Decision Statistics

Get statistics about decisions:

```python
stats = learner.decision_logger.get_decision_statistics()

print(f"Total Decisions: {stats['total_decisions']}")
print(f"By Type: {stats['by_type']}")
print(f"By Source: {stats['by_source']}")
print(f"Average Confidence: {stats['average_confidence']:.2%}")
```

## Pattern Comparison

Compare multiple patterns:

```python
patterns = learner.get_learned_patterns(context="test", limit=5)

comparison = learner.pattern_explainer.compare_patterns(patterns)

print(comparison["comparison"])
for pattern_info in comparison["patterns"]:
    print(f"{pattern_info['pattern_id']}: "
          f"quality={pattern_info['quality_score']:.2f}, "
          f"security={pattern_info['security_score']:.2f}")
```

## Learning Effectiveness

Track learning effectiveness over time:

```python
effectiveness = learner.impact_reporter.get_learning_effectiveness(
    capability_id="test",
)

print(f"Total Sessions: {effectiveness['total_sessions']}")
print(f"Average Improvement: {effectiveness['average_improvement']:.2f}")
print(f"Effectiveness Score: {effectiveness['effectiveness_score']:.2f}")
print(f"Trend: {effectiveness['improvement_trend']}")
```

## Best Practices

1. **Review Decision Logs**: Regularly review decision history to understand learning behavior
2. **Monitor Impact**: Track learning impact to measure effectiveness
3. **Explain Selections**: Use pattern selection explanations to understand recommendations
4. **Export Reports**: Export reports for documentation and analysis
5. **Dashboard Monitoring**: Use dashboard data for system health monitoring

## Configuration

### Log Limits

- **Max Decision Logs**: 1000 (configurable)
- **Log Retention**: Keeps most recent logs
- **History Queries**: Filter by type, time, or source

### Report Formats

- **Markdown**: Human-readable format for documentation
- **JSON**: Machine-readable format for analysis

## Integration

Explainability integrates throughout the learning system:

- **Automatic Logging**: All decisions are automatically logged
- **Pattern Explanations**: Generated during pattern selection
- **Impact Tracking**: Automatically tracked during learning
- **Dashboard Updates**: Real-time dashboard data

## See Also

- [Agent Learning Guide](AGENT_LEARNING_GUIDE.md)
- [Meta-Learning Guide](LEARNING_META_LEARNING.md)
- [Security Integration](LEARNING_SECURITY.md)

