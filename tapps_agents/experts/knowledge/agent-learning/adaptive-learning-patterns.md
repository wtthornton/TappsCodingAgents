# Adaptive Learning Patterns

## Overview

This guide covers adaptive learning patterns for AI agents, including outcome tracking, weight adjustment, expert auto-generation, and continuous improvement.

## Core Patterns

### Pattern 1: Outcome Tracking

**Track Code Quality Outcomes:**
```python
from tapps_agents.core import OutcomeTracker, CodeOutcome

tracker = OutcomeTracker()

# Track initial scores
outcome = tracker.track_initial_scores(
    workflow_id="workflow-123",
    file_path=Path("code.py"),
    scores={
        "complexity_score": 7.0,
        "security_score": 8.0,
        "maintainability_score": 7.5,
        # ... other scores
    },
    expert_consultations=["expert-security"],
    agent_id="implementer"
)

# Finalize after iterations
tracker.finalize_outcome(
    workflow_id="workflow-123",
    final_scores=final_scores,
    time_to_correctness=120.0
)
```

**What to Track:**
- Initial code scores (all 7 categories)
- Final code scores (after iterations)
- Number of iterations needed
- Expert consultations used
- Time to achieve quality threshold
- First-pass success (yes/no)

### Pattern 2: Adaptive Scoring

**Adjust Weights Based on Outcomes:**
```python
from tapps_agents.core import AdaptiveScoringEngine

engine = AdaptiveScoringEngine(outcome_tracker=tracker)

# Load outcomes
outcomes = tracker.load_outcomes(limit=100)

# Adjust weights
adjusted_weights = await engine.adjust_weights(
    outcomes=outcomes,
    current_weights=current_weights
)

# Weights now emphasize metrics that predict first-pass success
```

**Algorithm:**
1. Calculate correlation between each metric and first-pass success
2. Identify which metrics best predict success
3. Adjust weights to emphasize predictive metrics
4. Apply gradual adjustment (learning rate)
5. Normalize to sum to 1.0

### Pattern 3: Expert Auto-Generation

**Detect Domains and Generate Experts:**
```python
from tapps_agents.experts import (
    AdaptiveDomainDetector,
    ExpertSuggester,
    AutoExpertGenerator,
)

# Detect new domains
detector = AdaptiveDomainDetector()
suggestions = await detector.detect_domains(
    prompt="Create OAuth2 refresh token client",
    code_context=code
)

# Suggest expert
suggester = ExpertSuggester()
expert_suggestion = await suggester.suggest_from_domain_detection(
    suggestions[0]
)

# Generate expert
generator = AutoExpertGenerator()
result = await generator.generate_expert(
    expert_suggestion,
    auto_approve=False
)
```

**Auto-Generation Process:**
1. Detect domain from prompt/code patterns
2. Check if expert already exists
3. Generate expert configuration
4. Create knowledge base structure
5. Populate initial knowledge
6. Update weight matrix
7. Validate configuration

### Pattern 4: Expert Performance Tracking

**Monitor Expert Effectiveness:**
```python
from tapps_agents.experts import ExpertPerformanceTracker

tracker = ExpertPerformanceTracker()

# Track consultation
tracker.track_consultation(
    expert_id="expert-security",
    domain="security",
    confidence=0.85,
    query="How to implement secure auth?"
)

# Calculate performance
performance = tracker.calculate_performance(
    "expert-security",
    days=30
)

# Metrics:
# - consultations: Number of consultations
# - avg_confidence: Average confidence score
# - first_pass_success_rate: % of first-pass successes
# - code_quality_improvement: Delta in scores
```

### Pattern 5: Adaptive Voting

**Adjust Expert Weights Based on Performance:**
```python
from tapps_agents.experts import AdaptiveVotingEngine

engine = AdaptiveVotingEngine(performance_tracker=tracker)

# Get performance data
performance_data = tracker.get_all_performance(days=30)

# Adjust voting weights
adjusted_matrix = await engine.adjust_voting_weights(
    performance_data=performance_data,
    current_matrix=current_matrix
)

# High-performing experts get higher weights
# Low-performing experts get lower weights
# 51% primary rule maintained
```

### Pattern 6: Knowledge Enhancement

**Automatically Improve Expert Knowledge:**
```python
from tapps_agents.experts import KnowledgeEnhancer

enhancer = KnowledgeEnhancer()

# Identify gaps
gaps = [
    KnowledgeGap(
        expert_id="expert-security",
        domain="security",
        query="OAuth2 refresh token flow",
        confidence=0.5,  # Low confidence = gap
        gap_type="low_confidence"
    )
]

# Enhance knowledge
updates = await enhancer.enhance_knowledge(
    expert_id="expert-security",
    gaps=gaps,
    successful_patterns=patterns
)

# Apply updates
for update in updates:
    enhancer.apply_update(update)
```

---

## Integration Patterns

### Pattern 1: Reviewer Integration

**Adaptive Scoring in Code Review:**
```python
# Reviewer automatically uses adaptive weights
reviewer = ReviewerAgent()
result = await reviewer.review_file(file_path)

# Outcome automatically tracked
# Adaptive weights applied to scoring
# Performance tracked for experts consulted
```

### Pattern 2: Enhancer Integration

**Expert Suggestions in Prompt Enhancement:**
```python
# Enhancer detects domains and suggests experts
enhancer = EnhancerAgent()
enhanced = await enhancer.enhance(prompt)

# Expert suggestions included in enhanced prompt
# LLM hints generated for expert consultations
# Auto-generation triggered if domains detected
```

### Pattern 3: Workflow Integration

**Adaptive Learning in Workflows:**
```python
# Simple Mode workflow automatically:
# 1. Detects domains
# 2. Suggests experts
# 3. Tracks outcomes
# 4. Adjusts weights
# 5. Improves over time

@simple-mode *build "Create OAuth2 client"
# → Automatically uses adaptive learning
```

---

## Best Practices

1. **Outcome Tracking:**
   - Track all code quality outcomes
   - Include expert consultations
   - Measure time to correctness
   - Track first-pass success

2. **Weight Adjustment:**
   - Use sufficient data (10+ outcomes)
   - Apply gradual changes (learning rate)
   - Validate weight changes
   - Monitor improvements

3. **Expert Generation:**
   - Detect domains proactively
   - Validate before generation
   - Populate knowledge bases
   - Update weight matrix

4. **Performance Monitoring:**
   - Track all consultations
   - Calculate success rates
   - Identify weaknesses
   - Suggest improvements

5. **Knowledge Enhancement:**
   - Identify gaps from low confidence
   - Extract successful patterns
   - Update knowledge bases
   - Validate updates

---

## Success Metrics

**Target Improvements:**
- 20%+ improvement in first-pass success rate
- 15%+ improvement in expert consultation effectiveness
- 50%+ reduction in iterations needed
- 30%+ improvement in first-pass code quality

**Measurement:**
- Track outcomes over time
- Compare before/after adaptive learning
- Monitor weight convergence
- Measure expert performance

---

## References

- Adaptive Learning Implementation: `docs/ADAPTIVE_LEARNING_IMPLEMENTATION.md`
- Outcome Tracker: `tapps_agents/core/outcome_tracker.py`
- Adaptive Scoring: `tapps_agents/core/adaptive_scoring.py`
- Expert Performance: `tapps_agents/experts/performance_tracker.py`
