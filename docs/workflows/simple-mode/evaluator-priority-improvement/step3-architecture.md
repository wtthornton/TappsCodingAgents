# Step 3: Architecture Design - Evaluator Agent Priority System Improvement

**Date:** January 16, 2025  
**Workflow:** Simple Mode *build  
**Agent:** Architect  
**Stage:** System Architecture Design

---

## System Architecture Overview

The enhanced priority evaluation system introduces a modular architecture that separates concerns into distinct components: factor extraction, score calculation, priority classification, and historical tracking. This design ensures consistency, maintainability, and extensibility.

---

## Component Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ReportGenerator                          │
│  (Existing - Enhanced with PriorityEvaluator)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ uses
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  PriorityEvaluator                          │
│  (New - Core Priority Evaluation Engine)                    │
├─────────────────────────────────────────────────────────────┤
│  + evaluate(recommendation, data_sources) -> PriorityResult │
└─────┬───────────────────────────────────────────────────────┘
      │
      │ uses
      ├──────────────────┬──────────────────┬─────────────────┐
      ▼                  ▼                  ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│FactorExtractor│  │ScoreCalculator│  │PriorityClassif│  │HistoryTracker│
│              │  │              │  │ier          │  │              │
├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤
│+ extract()   │  │+ calculate() │  │+ classify()  │  │+ track()     │
│              │  │              │  │              │  │+ get_trends() │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
      │                  │                  │                  │
      │                  │                  │                  │
      └──────────────────┴──────────────────┴──────────────────┘
                         │
                         │ reads from
                         ▼
         ┌──────────────────────────────────────┐
         │      Data Sources                     │
         ├──────────────────────────────────────┤
         │  - quality_data (QualityAnalyzer)     │
         │  - workflow_data (WorkflowAnalyzer)  │
         │  - usage_data (UsageAnalyzer)        │
         │  - recommendation (description, etc.) │
         └──────────────────────────────────────┘
```

---

## Component Details

### 1. PriorityEvaluator (Core Engine)

**Location:** `tapps_agents/agents/evaluator/priority_evaluator.py`

**Responsibilities:**
- Orchestrate priority evaluation process
- Coordinate factor extraction, scoring, and classification
- Integrate with historical tracking
- Provide unified API for ReportGenerator

**Interface:**
```python
class PriorityEvaluator:
    def evaluate(
        self,
        recommendation: dict[str, Any],
        quality_data: dict[str, Any] | None = None,
        workflow_data: dict[str, Any] | None = None,
        usage_data: dict[str, Any] | None = None,
        config: PriorityConfig | None = None
    ) -> PriorityResult:
        """
        Evaluate recommendation priority.
        
        Returns PriorityResult with:
        - priority: str (critical/high/medium/low)
        - score: float (0-10)
        - factors: dict[str, float]
        - rationale: str
        """
```

**Dependencies:**
- FactorExtractor
- ScoreCalculator
- PriorityClassifier
- HistoryTracker (optional)

---

### 2. FactorExtractor

**Location:** `tapps_agents/agents/evaluator/priority_evaluator.py` (as nested class)

**Responsibilities:**
- Extract objective metrics from recommendation content
- Parse description text for keywords and patterns
- Extract metrics from data sources (quality, workflow, usage)
- Return structured factor scores

**Factors Extracted:**

1. **Impact Severity** (0-10)
   - Keyword detection: "security", "vulnerability", "data loss", "failure", etc.
   - Quality score analysis: Low scores indicate high severity
   - Workflow deviation analysis: Broken workflows = high severity

2. **Effort Complexity** (0-10, inverted)
   - Description analysis: "quick fix", "simple", "complex", "refactor"
   - Code metrics: Lines of code, file count, test coverage
   - Historical data: Similar fixes in past

3. **Risk Level** (0-10)
   - Security keywords: "vulnerability", "breach", "injection"
   - Production impact: "outage", "downtime", "data corruption"
   - User impact keywords: "frustration", "broken", "error"

4. **User Impact** (0-10)
   - Usage data analysis: Command frequency, user count
   - Workflow data: Steps affected, completion rate
   - Quality data: Test failures, error rates

5. **Business Value** (0-10)
   - Strategic keywords: "revenue", "customer", "competitive"
   - Framework keywords: "adoption", "productivity", "efficiency"
   - Quality keywords: "maintainability", "technical debt"

6. **Code Quality Impact** (0-10)
   - Quality score improvements: Potential score increase
   - Test coverage: Coverage improvement potential
   - Technical debt: Debt reduction potential

**Interface:**
```python
class FactorExtractor:
    def extract(
        self,
        recommendation: dict[str, Any],
        quality_data: dict[str, Any] | None = None,
        workflow_data: dict[str, Any] | None = None,
        usage_data: dict[str, Any] | None = None
    ) -> dict[str, float]:
        """
        Extract objective factors from recommendation.
        
        Returns dict with factor scores:
        {
            "impact_severity": float (0-10),
            "effort_complexity": float (0-10),
            "risk_level": float (0-10),
            "user_impact": float (0-10),
            "business_value": float (0-10),
            "code_quality_impact": float (0-10)
        }
        """
```

**Implementation Strategy:**
- Keyword matching with weighted scoring
- Pattern recognition for common issue types
- Metric extraction from data sources
- Default values for missing data

---

### 3. ScoreCalculator

**Location:** `tapps_agents/agents/evaluator/priority_evaluator.py` (as nested class)

**Responsibilities:**
- Apply weighted formula to factor scores
- Normalize scores to 0-10 range
- Handle missing data gracefully
- Provide configurable weights

**Scoring Formula:**
```python
priority_score = (
    factors["impact_severity"] * weights["impact_severity"] +
    (10 - factors["effort_complexity"]) * weights["effort_complexity"] +  # Inverted
    factors["risk_level"] * weights["risk_level"] +
    factors["user_impact"] * weights["user_impact"] +
    factors["business_value"] * weights["business_value"] +
    factors["code_quality_impact"] * weights["code_quality_impact"]
)
```

**Default Weights:**
```python
DEFAULT_WEIGHTS = {
    "impact_severity": 0.25,
    "effort_complexity": 0.20,  # Inverted: easier = higher priority
    "risk_level": 0.20,
    "user_impact": 0.15,
    "business_value": 0.10,
    "code_quality_impact": 0.10
}
```

**Interface:**
```python
class ScoreCalculator:
    def calculate(
        self,
        factors: dict[str, float],
        weights: dict[str, float] | None = None
    ) -> float:
        """
        Calculate priority score from factors.
        
        Returns float (0-10)
        """
```

**Normalization:**
- Ensure all factor scores are in 0-10 range
- Handle missing factors with default values (5.0 = medium)
- Clamp final score to 0-10 range

---

### 4. PriorityClassifier

**Location:** `tapps_agents/agents/evaluator/priority_evaluator.py` (as nested class)

**Responsibilities:**
- Map priority scores to priority levels
- Provide rationale for classification
- Support configurable thresholds

**Classification Rules:**
```python
if score >= 8.5:
    priority = "critical"
    rationale = "High impact, low effort, or high risk issue requiring immediate attention"
elif score >= 7.0:
    priority = "high"
    rationale = "Significant impact or moderate risk issue that should be addressed soon"
elif score >= 5.0:
    priority = "medium"
    rationale = "Moderate impact issue that can be addressed when resources allow"
else:
    priority = "low"
    rationale = "Low impact improvement or nice-to-have feature"
```

**Interface:**
```python
class PriorityClassifier:
    def classify(
        self,
        score: float,
        thresholds: dict[str, float] | None = None
    ) -> tuple[str, str]:
        """
        Classify priority score into priority level.
        
        Returns tuple: (priority_level, rationale)
        """
```

**Configurable Thresholds:**
- Default: Critical (8.5), High (7.0), Medium (5.0), Low (0.0)
- Can be adjusted via config.yaml
- Thresholds can be asymmetric (e.g., stricter Critical threshold)

---

### 5. HistoryTracker

**Location:** `tapps_agents/agents/evaluator/history_tracker.py`

**Responsibilities:**
- Store evaluation results in JSON format
- Track priority distribution over time
- Calculate improvement metrics
- Generate trend reports

**Storage Format:**
```json
{
  "evaluation_id": "eval-20250116-100000",
  "evaluation_date": "2025-01-16T10:00:00Z",
  "total_recommendations": 15,
  "priority_distribution": {
    "critical": 2,
    "high": 3,
    "medium": 7,
    "low": 3
  },
  "average_score": 6.2,
  "recommendations": [
    {
      "id": "rec-001",
      "description": "Fix security vulnerability in auth",
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

**Storage Location:**
- `.tapps-agents/evaluations/history/evaluation-{timestamp}.json`
- One file per evaluation run
- Files named with timestamp for chronological ordering

**Interface:**
```python
class HistoryTracker:
    def track(
        self,
        evaluation_id: str,
        recommendations: list[PriorityResult],
        metadata: dict[str, Any] | None = None
    ) -> Path:
        """
        Store evaluation results in history.
        
        Returns Path to stored file
        """
    
    def get_trends(
        self,
        days: int = 30
    ) -> dict[str, Any]:
        """
        Get priority distribution trends over time.
        
        Returns dict with:
        - critical_trend: list[int] (counts over time)
        - high_trend: list[int]
        - medium_trend: list[int]
        - low_trend: list[int]
        - average_score_trend: list[float]
        - improvement_metrics: dict
        """
```

**Trend Analysis:**
- Load historical files from last N days
- Calculate priority distribution for each evaluation
- Calculate average priority score for each evaluation
- Generate improvement metrics:
  - Critical count change (%)
  - High count change (%)
  - Average score change (%)
  - Trend direction (improving/declining/stable)

---

## Data Flow

### Evaluation Flow

```
1. ReportGenerator receives recommendations
   │
   ▼
2. ReportGenerator calls PriorityEvaluator.evaluate() for each recommendation
   │
   ▼
3. PriorityEvaluator calls FactorExtractor.extract()
   │  - Parses recommendation description
   │  - Extracts metrics from data sources
   │  - Returns factor scores
   │
   ▼
4. PriorityEvaluator calls ScoreCalculator.calculate()
   │  - Applies weighted formula
   │  - Returns priority score (0-10)
   │
   ▼
5. PriorityEvaluator calls PriorityClassifier.classify()
   │  - Maps score to priority level
   │  - Returns priority and rationale
   │
   ▼
6. PriorityEvaluator calls HistoryTracker.track() (if enabled)
   │  - Stores evaluation result
   │
   ▼
7. PriorityEvaluator returns PriorityResult to ReportGenerator
   │
   ▼
8. ReportGenerator uses PriorityResult to generate prioritized report
```

---

## Integration Points

### With Existing Components

1. **ReportGenerator**
   - **Before:** Simple priority logic based on "impact" and "type" fields
   - **After:** Uses PriorityEvaluator for objective evaluation
   - **Changes:** Replace `prioritize_recommendations()` method
   - **Backward Compatibility:** Support both old and new systems (configurable)

2. **QualityAnalyzer**
   - **Usage:** Provides quality scores for factor extraction
   - **Integration:** Pass quality_data to PriorityEvaluator
   - **No Changes Required:** Existing interface sufficient

3. **WorkflowAnalyzer**
   - **Usage:** Provides workflow adherence data for factor extraction
   - **Integration:** Pass workflow_data to PriorityEvaluator
   - **No Changes Required:** Existing interface sufficient

4. **UsageAnalyzer**
   - **Usage:** Provides usage pattern data for factor extraction
   - **Integration:** Pass usage_data to PriorityEvaluator
   - **No Changes Required:** Existing interface sufficient

---

## Configuration

### Config Structure

```yaml
evaluator:
  priority_evaluation:
    enabled: true
    use_historical_tracking: true
    
    # Factor weights (must sum to 1.0)
    weights:
      impact_severity: 0.25
      effort_complexity: 0.20
      risk_level: 0.20
      user_impact: 0.15
      business_value: 0.10
      code_quality_impact: 0.10
    
    # Priority thresholds
    thresholds:
      critical: 8.5
      high: 7.0
      medium: 5.0
      low: 0.0
    
    # Historical tracking
    history:
      enabled: true
      retention_days: 90
      trend_analysis_days: 30
```

### Configuration Validation

- Weights must sum to 1.0 (within tolerance)
- Thresholds must be in descending order
- All thresholds must be in 0-10 range
- History retention must be positive integer

---

## Performance Considerations

### Optimization Strategies

1. **Caching**
   - Cache factor extraction results for identical recommendations
   - Cache historical trend calculations
   - Cache configuration values

2. **Batch Processing**
   - Process multiple recommendations in single batch
   - Load historical data once per batch
   - Minimize file I/O operations

3. **Lazy Loading**
   - Load historical data only when needed
   - Load configuration on first use
   - Defer trend analysis until requested

### Performance Targets

- **Factor Extraction:** < 100ms per recommendation
- **Score Calculation:** < 10ms per recommendation
- **Priority Classification:** < 1ms per recommendation
- **Historical Tracking:** < 50ms per evaluation (batch)
- **Total Evaluation:** < 1 second per recommendation

---

## Error Handling

### Error Scenarios

1. **Missing Data**
   - **Handling:** Use default values (5.0 = medium)
   - **Logging:** Log warning for missing data
   - **Impact:** Evaluation continues with reduced accuracy

2. **Invalid Configuration**
   - **Handling:** Use default configuration
   - **Logging:** Log error and fallback to defaults
   - **Impact:** Evaluation continues with default settings

3. **File I/O Errors**
   - **Handling:** Skip historical tracking, continue evaluation
   - **Logging:** Log error but don't fail evaluation
   - **Impact:** Evaluation succeeds but history not saved

4. **Invalid Recommendation Format**
   - **Handling:** Skip invalid recommendations, log warning
   - **Logging:** Log warning with recommendation ID
   - **Impact:** Other recommendations still evaluated

---

## Testing Strategy

### Unit Tests

- **FactorExtractor:** Test each factor extraction logic
- **ScoreCalculator:** Test weighted formula with various inputs
- **PriorityClassifier:** Test threshold boundaries
- **HistoryTracker:** Test storage and retrieval

### Integration Tests

- **End-to-End:** Full evaluation flow with real data
- **Consistency:** Same input produces same output
- **Performance:** Meets performance targets

### Test Data

- **Sample Recommendations:** Various types and formats
- **Historical Data:** Mock evaluation history
- **Edge Cases:** Missing data, invalid inputs, boundary conditions

---

## Migration Strategy

### Phased Rollout

1. **Phase 1:** Implement PriorityEvaluator alongside existing logic
2. **Phase 2:** Add feature flag to switch between old and new systems
3. **Phase 3:** Enable new system by default, keep old system as fallback
4. **Phase 4:** Remove old system after validation period

### Backward Compatibility

- Support both old and new priority systems
- Configurable via `evaluator.priority_evaluation.enabled`
- Default to new system, allow fallback to old system
- Migration guide for users

---

## Future Enhancements

### Potential Improvements

1. **Machine Learning:** Train model on historical priority assignments
2. **Custom Factors:** Allow users to define custom evaluation factors
3. **Priority Overrides:** Allow manual priority overrides with justification
4. **Priority Suggestions:** Suggest priority based on similar past recommendations
5. **Real-Time Updates:** Update priorities as codebase changes

---

## Summary

The architecture provides a modular, extensible, and maintainable solution for objective priority evaluation. Key design decisions:

- **Separation of Concerns:** Each component has single responsibility
- **Configurability:** Weights and thresholds are configurable
- **Extensibility:** Easy to add new factors or modify scoring
- **Performance:** Optimized for < 1 second per recommendation
- **Reliability:** Graceful error handling and fallbacks
- **Testability:** Clear interfaces enable comprehensive testing
