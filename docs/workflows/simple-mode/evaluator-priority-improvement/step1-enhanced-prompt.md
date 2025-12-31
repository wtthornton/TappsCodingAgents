# Step 1: Enhanced Prompt - Evaluator Agent Priority System Improvement

**Date:** January 16, 2025  
**Workflow:** Simple Mode *build  
**Agent:** Enhancer  
**Stage:** Full Enhancement (7 stages)

---

## Original Prompt

Review the Evaluator Agent and make sure it has an excellent way to evaluate consistently and independently what is a critical, high, medium, and low fix or enhancement. The goal is over time we will not have many critical and highs as we continue to improve.

---

## Enhanced Prompt (7-Stage Pipeline)

### Stage 1: Analysis

**Intent:** Improve the Evaluator Agent's priority evaluation system to provide consistent, independent, and objective priority classification for fixes and enhancements.

**Domains Identified:**
- Code Quality & Metrics
- Priority Classification Systems
- Continuous Improvement
- Framework Evaluation
- Risk Assessment
- Impact Analysis

**Scope:**
- Enhance priority evaluation logic in `ReportGenerator.prioritize_recommendations()`
- Create objective scoring system for priority classification
- Implement independent evaluation (not relying on pre-set "impact" fields)
- Define clear, measurable criteria for Critical, High, Medium, Low priorities
- Add historical tracking to measure improvement over time
- Ensure consistency across different evaluation runs

**Workflow Type:** Framework Enhancement (agent improvement)

### Stage 2: Requirements

#### Functional Requirements

1. **Objective Priority Scoring System**
   - Calculate priority scores based on multiple objective factors
   - Factors: Impact severity, Effort complexity, Risk level, User impact, Business value
   - Each factor scored independently (0-10 scale)
   - Weighted combination produces final priority score
   - Score ranges map to priority levels:
     - Critical: 8.5-10.0
     - High: 7.0-8.4
     - Medium: 5.0-6.9
     - Low: 0.0-4.9

2. **Independent Evaluation**
   - Analyze recommendation content to extract objective metrics
   - Do not rely on pre-set "impact" or "type" fields
   - Parse description text for keywords and patterns
   - Analyze code quality scores, workflow data, usage patterns
   - Extract metrics from available data sources

3. **Consistent Evaluation Criteria**
   - Documented criteria for each priority level
   - Same recommendation evaluated same way across runs
   - Deterministic scoring (no randomness)
   - Clear thresholds and boundaries

4. **Historical Tracking & Improvement Measurement**
   - Track priority distribution over time
   - Measure reduction in Critical/High items
   - Store evaluation history in `.tapps-agents/evaluations/history/`
   - Generate trend reports showing improvement
   - Alert when Critical/High items increase unexpectedly

5. **Multi-Factor Analysis**
   - Impact Severity: How much does this affect users/system?
   - Effort Complexity: How hard is it to fix/implement?
   - Risk Level: What's the risk if not addressed?
   - User Impact: How many users affected?
   - Business Value: Strategic importance
   - Code Quality Impact: Effect on overall codebase quality
   - Dependencies: Blocks other work?

#### Non-Functional Requirements

1. **Performance**
   - Priority evaluation completes in < 1 second per recommendation
   - Batch processing for multiple recommendations
   - Caching of historical data

2. **Maintainability**
   - Clear, documented scoring algorithm
   - Configurable weights and thresholds
   - Unit tests for priority classification
   - Easy to adjust criteria as framework matures

3. **Accuracy**
   - Consistent results across runs
   - Reproducible priority assignments
   - Clear rationale for each priority level

4. **Extensibility**
   - Easy to add new evaluation factors
   - Pluggable scoring strategies
   - Support for custom priority levels (if needed)

### Stage 3: Architecture

#### System Design

**Priority Evaluation Engine**
```
PriorityEvaluator
├── FactorExtractor: Extract objective metrics from recommendations
├── ScoreCalculator: Calculate weighted priority scores
├── PriorityClassifier: Map scores to priority levels
├── HistoryTracker: Track priority trends over time
└── ReportGenerator: Generate prioritized reports
```

**Data Flow:**
1. Recommendation → FactorExtractor → Objective Metrics
2. Objective Metrics → ScoreCalculator → Priority Score (0-10)
3. Priority Score → PriorityClassifier → Priority Level (Critical/High/Medium/Low)
4. Priority Level + History → ReportGenerator → Prioritized Report

**Key Components:**

1. **FactorExtractor**
   - Parses recommendation description for keywords
   - Extracts metrics from quality_data, workflow_data, usage_data
   - Identifies patterns (security issues, workflow deviations, etc.)
   - Returns structured factor scores

2. **ScoreCalculator**
   - Applies weighted formula to factor scores
   - Configurable weights per factor
   - Normalizes scores to 0-10 range
   - Handles missing data gracefully

3. **PriorityClassifier**
   - Maps score ranges to priority levels
   - Configurable thresholds
   - Provides rationale for classification

4. **HistoryTracker**
   - Stores evaluation results in JSON format
   - Tracks priority distribution over time
   - Calculates improvement metrics
   - Generates trend visualizations

#### Integration Points

- **QualityAnalyzer**: Provides quality scores for recommendations
- **WorkflowAnalyzer**: Provides workflow adherence data
- **UsageAnalyzer**: Provides usage pattern data
- **ReportGenerator**: Uses priority evaluation for report generation

### Stage 4: Design

#### Priority Evaluation Algorithm

**Factor Extraction:**

1. **Impact Severity** (0-10)
   - Security vulnerability: 10
   - Data loss risk: 9
   - System failure: 8
   - Workflow broken: 7
   - Quality degradation: 6
   - Performance issue: 5
   - Documentation gap: 4
   - Minor improvement: 3
   - Nice-to-have: 2
   - Cosmetic: 1

2. **Effort Complexity** (0-10, inverted: lower = higher priority)
   - Quick fix (< 1 hour): 1 → Priority boost
   - Simple (1-4 hours): 2
   - Moderate (1-2 days): 4
   - Complex (3-5 days): 6
   - Very complex (> 5 days): 8

3. **Risk Level** (0-10)
   - Production outage risk: 10
   - Security breach risk: 9
   - Data corruption risk: 8
   - User frustration: 6
   - Technical debt: 4
   - Low risk: 2

4. **User Impact** (0-10)
   - All users affected: 10
   - Most users (>50%): 8
   - Many users (25-50%): 6
   - Some users (10-25%): 4
   - Few users (<10%): 2
   - No direct user impact: 1

5. **Business Value** (0-10)
   - Revenue critical: 10
   - Strategic initiative: 8
   - User satisfaction: 6
   - Developer productivity: 5
   - Code quality: 4
   - Maintenance: 3

6. **Code Quality Impact** (0-10)
   - Prevents future bugs: 8
   - Improves maintainability: 6
   - Reduces technical debt: 5
   - Improves test coverage: 4
   - Code style: 2

**Scoring Formula:**
```
Priority Score = (
    Impact Severity * 0.25 +
    (10 - Effort Complexity) * 0.20 +  // Inverted: easier = higher priority
    Risk Level * 0.20 +
    User Impact * 0.15 +
    Business Value * 0.10 +
    Code Quality Impact * 0.10
)
```

**Priority Classification:**
- **Critical** (8.5-10.0): Must fix immediately, blocks other work, high risk
- **High** (7.0-8.4): Should fix soon, significant impact, moderate risk
- **Medium** (5.0-6.9): Fix when possible, moderate impact, low risk
- **Low** (0.0-4.9): Nice to have, minimal impact, very low risk

#### Historical Tracking

**Storage Format:**
```json
{
  "evaluation_date": "2025-01-16T10:00:00Z",
  "total_recommendations": 15,
  "priority_distribution": {
    "critical": 2,
    "high": 3,
    "medium": 7,
    "low": 3
  },
  "recommendations": [
    {
      "id": "rec-001",
      "priority": "critical",
      "score": 9.2,
      "factors": {
        "impact_severity": 10,
        "effort_complexity": 2,
        "risk_level": 9,
        "user_impact": 8,
        "business_value": 8,
        "code_quality_impact": 7
      }
    }
  ]
}
```

**Improvement Metrics:**
- Critical count trend (should decrease over time)
- High count trend (should decrease over time)
- Average priority score trend (should increase over time)
- Priority distribution changes

### Stage 5: Quality Standards

#### Code Quality Requirements

- **Test Coverage**: > 90% for priority evaluation logic
- **Type Safety**: Full type hints, Pydantic models for data structures
- **Documentation**: Comprehensive docstrings, algorithm documentation
- **Error Handling**: Graceful degradation for missing data
- **Performance**: < 1 second per recommendation evaluation

#### Security Requirements

- No external API calls in evaluation logic
- Input validation for all data sources
- Safe JSON parsing with error handling

#### Testing Requirements

- Unit tests for each factor extractor
- Unit tests for score calculator
- Unit tests for priority classifier
- Integration tests with real recommendation data
- Test for consistency (same input = same output)
- Test for historical tracking

### Stage 6: Implementation Strategy

#### Implementation Steps

1. **Create PriorityEvaluator Class**
   - Location: `tapps_agents/agents/evaluator/priority_evaluator.py`
   - Methods: `extract_factors()`, `calculate_score()`, `classify_priority()`

2. **Implement FactorExtractor**
   - Parse recommendation descriptions
   - Extract metrics from data sources
   - Return structured factor scores

3. **Implement ScoreCalculator**
   - Apply weighted formula
   - Handle missing data
   - Normalize scores

4. **Implement PriorityClassifier**
   - Map scores to priority levels
   - Provide rationale

5. **Implement HistoryTracker**
   - Store evaluation history
   - Track trends
   - Generate improvement reports

6. **Update ReportGenerator**
   - Integrate PriorityEvaluator
   - Replace simple priority logic
   - Add historical context to reports

7. **Add Configuration**
   - Configurable weights
   - Configurable thresholds
   - Enable/disable historical tracking

8. **Write Tests**
   - Unit tests for all components
   - Integration tests
   - Consistency tests

9. **Update Documentation**
   - Algorithm documentation
   - Configuration guide
   - Usage examples

### Stage 7: Synthesis

#### Enhanced Implementation Prompt

**Objective:** Enhance the Evaluator Agent's priority evaluation system to provide consistent, independent, and objective priority classification for fixes and enhancements.

**Key Requirements:**
1. Replace simple priority logic with objective scoring system
2. Extract factors independently from recommendation content
3. Use weighted formula to calculate priority scores
4. Classify into Critical/High/Medium/Low based on score ranges
5. Track historical priority distribution to measure improvement
6. Ensure consistency and reproducibility

**Implementation Approach:**
- Create `PriorityEvaluator` class with factor extraction, scoring, and classification
- Implement `HistoryTracker` for trend analysis
- Update `ReportGenerator` to use new evaluation system
- Add comprehensive tests and documentation

**Success Criteria:**
- Consistent priority assignments across runs
- Objective evaluation independent of pre-set fields
- Clear criteria for each priority level
- Historical tracking shows improvement over time
- Critical/High items decrease as codebase improves

---

## Quality Standards

- **Code Quality**: > 90% test coverage, full type hints
- **Performance**: < 1 second per recommendation
- **Consistency**: Same input always produces same output
- **Documentation**: Comprehensive algorithm documentation

## Architecture Guidance

- Modular design: FactorExtractor, ScoreCalculator, PriorityClassifier, HistoryTracker
- Integration with existing QualityAnalyzer, WorkflowAnalyzer, UsageAnalyzer
- Configuration-driven weights and thresholds
- Historical data storage in `.tapps-agents/evaluations/history/`

## Implementation Notes

- Start with PriorityEvaluator class
- Implement factor extraction from recommendation descriptions
- Use weighted scoring formula with configurable weights
- Add historical tracking for trend analysis
- Update ReportGenerator to use new system
- Write comprehensive tests
