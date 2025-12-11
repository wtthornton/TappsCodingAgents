# Expert Confidence System Guide

**Version:** 2.1.0  
**Last Updated:** December 2025

## Overview

The Expert Confidence System provides sophisticated confidence calculation for expert consultations, ensuring that agents only act on high-confidence expert advice. This system was introduced in v2.1.0 to improve the reliability and accuracy of expert-guided decisions.

## Confidence Calculation

### Algorithm

The confidence score is calculated using a weighted algorithm that considers multiple factors:

```python
confidence = (
    max_confidence * 0.4 +      # Maximum expert confidence (40%)
    agreement_level * 0.3 +      # Expert agreement (30%)
    rag_quality * 0.2 +          # Knowledge base match quality (20%)
    domain_relevance * 0.1       # Domain relevance score (10%)
)
```

### Factors Explained

1. **Max Confidence (40%)**
   - Highest confidence score from all expert responses
   - Based on expert's confidence in their domain
   - Derived from weight matrix (51% primary, 49% split)

2. **Agreement Level (30%)**
   - Measures how well experts agree on the answer
   - Calculated from semantic similarity of responses
   - Higher agreement = higher confidence

3. **RAG Quality (20%)**
   - Quality of knowledge base retrieval
   - Based on number of relevant sources found
   - 2 sources per response = perfect quality (1.0)

4. **Domain Relevance (10%)**
   - How relevant the domain is to the query
   - Technical domains: 1.0
   - Business domains: 0.9

## Agent Integration

The following agents have integrated expert consultation with confidence checking:

| Agent | Experts | Threshold | Rationale |
|-------|---------|-----------|----------|
| **Reviewer** | Security, Performance, Testing, Accessibility, Code Quality | 0.8 | High - Critical code reviews require high confidence |
| **Architect** | Security, Performance, UX, Software Architecture | 0.75 | High - Architecture decisions have long-term impact |
| **Implementer** | Security, Performance | 0.7 | Medium-High - Code generation needs reliable guidance |
| **Tester** | Testing | 0.7 | Medium-High - Test quality affects reliability |
| **Designer** | Accessibility, UX, Data Privacy | 0.65 | Medium - Design decisions are important but less critical |
| **Ops** | Security, Data Privacy | 0.75 | High - Operations decisions affect security and compliance |

## Agent-Specific Thresholds

Each agent type has a configurable confidence threshold based on the criticality of decisions:

| Agent | Default Threshold | Rationale |
|-------|------------------|-----------|
| **Reviewer** | 0.8 | High threshold for code reviews (critical quality decisions) |
| **Architect** | 0.75 | High for architecture decisions (system-wide impact) |
| **Implementer** | 0.7 | Medium-high for code generation (important but can iterate) |
| **Designer** | 0.65 | Medium for design decisions (important but flexible) |
| **Tester** | 0.7 | Medium-high for test generation (important for quality) |
| **Ops** | 0.75 | High for operations (production impact) |
| **Enhancer** | 0.6 | Medium for enhancements (improvements, not critical) |
| **Analyst** | 0.65 | Medium for analysis (informational) |
| **Planner** | 0.6 | Medium for planning (can be adjusted) |
| **Debugger** | 0.7 | Medium-high for debugging (important for fixing) |
| **Documenter** | 0.5 | Lower for documentation (less critical) |
| **Orchestrator** | 0.6 | Medium for orchestration (coordination) |

### Configuration

Configure thresholds in `.tapps-agents/config.yaml`:

```yaml
agents:
  reviewer:
    min_confidence_threshold: 0.8
  architect:
    min_confidence_threshold: 0.75
  implementer:
    min_confidence_threshold: 0.7
```

## Usage

### Basic Consultation

```python
from tapps_agents.experts.expert_registry import ExpertRegistry

registry = ExpertRegistry(load_builtin=True)

# Consult with agent-specific threshold
result = await registry.consult(
    query="How to secure this API?",
    domain="security",
    prioritize_builtin=True,
    agent_id="reviewer"  # Uses reviewer's threshold (0.8)
)

# Check confidence
print(f"Confidence: {result.confidence:.2%}")
print(f"Threshold: {result.confidence_threshold:.2%}")
print(f"Meets threshold: {result.confidence >= result.confidence_threshold}")
print(f"Agreement: {result.agreement_level:.2%}")
```

### Using Confidence in Agents

```python
class MyAgent(BaseAgent):
    def __init__(self, expert_registry: Optional[ExpertRegistry] = None):
        super().__init__(agent_id="my-agent", agent_name="My Agent")
        self.expert_registry = expert_registry
    
    async def my_method(self):
        if self.expert_registry:
            result = await self.expert_registry.consult(
                query="Expert question",
                domain="security",
                agent_id="my-agent"
            )
            
            # Only use expert guidance if confidence meets threshold
            if result.confidence >= result.confidence_threshold:
                # Use expert guidance
                expert_guidance = result.weighted_answer
            else:
                # Log low confidence
                print(f"Low confidence: {result.confidence:.2%} < {result.confidence_threshold:.2%}")
```

## Confidence Metrics Tracking

### Automatic Tracking

All expert consultations are automatically tracked to `.tapps-agents/confidence_metrics.json`:

```python
from tapps_agents.experts.confidence_metrics import get_tracker

tracker = get_tracker()

# Get statistics for an agent
stats = tracker.get_statistics(agent_id="reviewer", domain="security")
# Returns:
# {
#   "count": 150,
#   "avg_confidence": 0.82,
#   "min_confidence": 0.45,
#   "max_confidence": 0.98,
#   "avg_agreement": 0.75,
#   "threshold_meet_rate": 0.87,
#   "low_confidence_count": 12
# }
```

### Querying Metrics

```python
# Get all metrics for an agent
metrics = tracker.get_metrics(agent_id="reviewer")

# Get metrics for a domain
metrics = tracker.get_metrics(domain="security")

# Get metrics with confidence filter
metrics = tracker.get_metrics(
    agent_id="reviewer",
    min_confidence=0.7,
    max_confidence=1.0
)
```

### Metrics Fields

Each metric record contains:
- `timestamp`: When the consultation occurred
- `agent_id`: Agent that made the consultation
- `domain`: Domain of the consultation
- `confidence`: Calculated confidence score
- `threshold`: Agent-specific threshold
- `meets_threshold`: Whether confidence met threshold
- `agreement_level`: Agreement level between experts
- `num_experts`: Number of experts consulted
- `primary_expert`: Primary expert ID
- `query_preview`: First 100 chars of query

## Best Practices

### 1. Use Appropriate Thresholds

- **High (0.75-0.8)**: Critical decisions that affect production
- **Medium-High (0.7)**: Important decisions that can be iterated
- **Medium (0.6-0.65)**: Standard decisions with flexibility
- **Lower (0.5)**: Less critical decisions

### 2. Monitor Confidence Metrics

Regularly review confidence metrics to:
- Identify low-confidence consultations
- Tune thresholds based on actual usage
- Improve knowledge bases for better RAG quality
- Track expert effectiveness

### 3. Handle Low Confidence

When confidence is below threshold:
- Log the consultation for review
- Consider consulting additional experts
- Use fallback logic or default behavior
- Alert users to low confidence

### 4. Improve Confidence

To improve confidence scores:
- **Enhance Knowledge Bases**: Add more relevant content
- **Improve RAG Quality**: Better retrieval = higher confidence
- **Consult Multiple Experts**: Higher agreement = higher confidence
- **Refine Queries**: More specific queries = better matches

## Troubleshooting

### Low Confidence Scores

**Symptoms:**
- Confidence consistently below threshold
- Low RAG quality scores
- Low agreement levels

**Solutions:**
1. Check knowledge base content relevance
2. Improve query specificity
3. Consult more experts for better agreement
4. Review domain relevance

### Threshold Too High

**Symptoms:**
- Many consultations fail threshold check
- Expert guidance rarely used

**Solutions:**
1. Lower threshold in config
2. Improve knowledge bases
3. Review threshold rationale

### Threshold Too Low

**Symptoms:**
- Low-quality expert guidance accepted
- Poor results from expert consultations

**Solutions:**
1. Raise threshold in config
2. Improve expert knowledge bases
3. Review consultation queries

## API Reference

### ConfidenceCalculator

```python
from tapps_agents.experts.confidence_calculator import ConfidenceCalculator

# Calculate confidence
confidence, threshold = ConfidenceCalculator.calculate(
    responses=expert_responses,
    domain="security",
    agent_id="reviewer",
    agreement_level=0.85,
    rag_quality=0.9
)

# Get threshold
threshold = ConfidenceCalculator.get_threshold("reviewer")

# Check if meets threshold
meets = ConfidenceCalculator.meets_threshold(confidence, "reviewer")
```

### ConsultationResult

```python
@dataclass
class ConsultationResult:
    domain: str
    query: str
    responses: List[Dict[str, Any]]
    weighted_answer: str
    agreement_level: float
    confidence: float                    # Calculated confidence
    confidence_threshold: float          # Agent-specific threshold
    primary_expert: str
    all_experts_agreed: bool
```

## Related Documentation

- [Built-in Experts Guide](./BUILTIN_EXPERTS_GUIDE.md)
- [Expert Configuration Guide](./EXPERT_CONFIG_GUIDE.md)
- [API Reference](./API.md)
- [Configuration Guide](./CONFIGURATION.md)

