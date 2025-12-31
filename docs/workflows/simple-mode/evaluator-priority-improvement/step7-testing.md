# Step 7: Testing Plan and Validation - Evaluator Agent Priority System Improvement

**Date:** January 16, 2025  
**Workflow:** Simple Mode *build  
**Agent:** Tester  
**Stage:** Testing Plan and Validation

---

## Testing Strategy

### Test Coverage Target

**Target:** > 90% code coverage for priority evaluation logic

**Focus Areas:**
- Factor extraction logic
- Score calculation
- Priority classification
- Historical tracking
- Error handling

---

## Unit Tests

### 1. FactorExtractor Tests

**File:** `tests/agents/evaluator/test_priority_evaluator.py`

#### Test Cases

1. **test_extract_impact_severity_keywords**
   - Test keyword matching for impact severity
   - Verify scores for different keywords
   - Test default value when no keywords found

2. **test_extract_impact_severity_quality_data**
   - Test quality score analysis
   - Verify high severity for low quality scores
   - Test with missing quality data

3. **test_extract_impact_severity_workflow_deviations**
   - Test workflow deviation analysis
   - Verify high severity for high-impact deviations
   - Test with missing workflow data

4. **test_extract_effort_complexity**
   - Test effort keyword matching
   - Verify inverted scoring (lower effort = higher priority)
   - Test default value

5. **test_extract_risk_level**
   - Test risk keyword matching
   - Test security indicator detection
   - Verify high risk for security keywords

6. **test_extract_user_impact_usage_data**
   - Test user impact from usage statistics
   - Verify scaling based on command count
   - Test with missing usage data

7. **test_extract_user_impact_workflow_data**
   - Test user impact from workflow completion rates
   - Verify high impact for low completion rates
   - Test with missing workflow data

8. **test_extract_business_value**
   - Test business keyword matching
   - Verify scores for strategic terms
   - Test default value

9. **test_extract_code_quality_impact**
   - Test code quality impact from quality scores
   - Test keyword matching for quality terms
   - Verify high impact for low quality scores

10. **test_extract_all_factors**
    - Test complete factor extraction
    - Verify all factors are in 0-10 range
    - Test with various recommendation types

### 2. ScoreCalculator Tests

**File:** `tests/agents/evaluator/test_priority_evaluator.py`

#### Test Cases

1. **test_calculate_with_default_weights**
   - Test score calculation with default weights
   - Verify score is in 0-10 range
   - Test with various factor combinations

2. **test_calculate_with_custom_weights**
   - Test score calculation with custom weights
   - Verify weights sum validation
   - Test with invalid weights (should raise error)

3. **test_calculate_effort_inversion**
   - Test that lower effort complexity increases priority score
   - Verify inverted calculation: (10 - effort_complexity)

4. **test_calculate_missing_factors**
   - Test with missing factors (should use defaults)
   - Verify graceful handling of missing data

5. **test_calculate_edge_cases**
   - Test with all factors at minimum (0.0)
   - Test with all factors at maximum (10.0)
   - Test with mixed extreme values

### 3. PriorityClassifier Tests

**File:** `tests/agents/evaluator/test_priority_evaluator.py`

#### Test Cases

1. **test_classify_critical**
   - Test classification for critical priority (score >= 8.5)
   - Verify correct rationale

2. **test_classify_high**
   - Test classification for high priority (7.0 <= score < 8.5)
   - Verify correct rationale

3. **test_classify_medium**
   - Test classification for medium priority (5.0 <= score < 7.0)
   - Verify correct rationale

4. **test_classify_low**
   - Test classification for low priority (score < 5.0)
   - Verify correct rationale

5. **test_classify_threshold_boundaries**
   - Test classification at exact threshold values
   - Verify correct priority assignment at boundaries

6. **test_classify_custom_thresholds**
   - Test classification with custom thresholds
   - Verify threshold validation

### 4. PriorityEvaluator Tests

**File:** `tests/agents/evaluator/test_priority_evaluator.py`

#### Test Cases

1. **test_evaluate_complete_flow**
   - Test complete evaluation flow
   - Verify PriorityResult structure
   - Test with all data sources

2. **test_evaluate_missing_data**
   - Test evaluation with missing quality_data
   - Test evaluation with missing workflow_data
   - Test evaluation with missing usage_data
   - Verify graceful degradation

3. **test_evaluate_consistency**
   - Test that same recommendation produces same result
   - Verify deterministic evaluation

4. **test_evaluate_various_recommendations**
   - Test with security-related recommendations
   - Test with workflow-related recommendations
   - Test with quality-related recommendations
   - Test with low-priority recommendations

### 5. HistoryTracker Tests

**File:** `tests/agents/evaluator/test_priority_evaluator.py`

#### Test Cases

1. **test_track_evaluation**
   - Test storing evaluation results
   - Verify file creation
   - Verify JSON structure

2. **test_track_priority_distribution**
   - Test priority distribution calculation
   - Verify correct counts for each priority level

3. **test_track_average_score**
   - Test average score calculation
   - Verify correct computation

4. **test_get_trends**
   - Test trend analysis
   - Verify trend data structure
   - Test with no historical data

5. **test_get_trends_improvement_metrics**
   - Test improvement metrics calculation
   - Verify critical/high change percentages
   - Test trend direction detection

6. **test_get_trends_date_filtering**
   - Test filtering by days parameter
   - Verify only recent evaluations included

---

## Integration Tests

### 1. ReportGenerator Integration Tests

**File:** `tests/agents/evaluator/test_report_generator_integration.py`

#### Test Cases

1. **test_prioritize_recommendations_integration**
   - Test full integration with PriorityEvaluator
   - Verify prioritized output structure
   - Test with real recommendation data

2. **test_prioritize_recommendations_history_tracking**
   - Test historical tracking integration
   - Verify history files created
   - Test with history tracking disabled

3. **test_generate_report_with_priorities**
   - Test report generation with new priority system
   - Verify priority scores in report
   - Verify rationales in report

4. **test_report_priority_distribution**
   - Test priority distribution in reports
   - Verify correct grouping by priority level

### 2. EvaluatorAgent Integration Tests

**File:** `tests/agents/evaluator/test_evaluator_agent_integration.py`

#### Test Cases

1. **test_evaluate_command_integration**
   - Test full evaluate command flow
   - Verify report generation
   - Test with real workflow data

2. **test_evaluate_workflow_command_integration**
   - Test evaluate-workflow command flow
   - Verify workflow-specific evaluation
   - Test with real workflow state

---

## Test Data

### Sample Recommendations

```python
SAMPLE_RECOMMENDATIONS = [
    {
        "id": "rec-001",
        "description": "Fix security vulnerability in authentication",
        "type": "security",
        "impact": "high"
    },
    {
        "id": "rec-002",
        "description": "Improve test coverage for user service",
        "type": "quality",
        "impact": "medium"
    },
    {
        "id": "rec-003",
        "description": "Quick fix for broken workflow step",
        "type": "workflow",
        "impact": "high"
    },
    {
        "id": "rec-004",
        "description": "Minor cosmetic improvement to UI",
        "type": "enhancement",
        "impact": "low"
    }
]
```

### Sample Quality Data

```python
SAMPLE_QUALITY_DATA = {
    "scores": {
        "overall": 65.0,
        "complexity": 6.5,
        "security": 7.0,
        "maintainability": 6.0,
        "test_coverage": 5.5,
        "performance": 7.5
    },
    "issues": [
        {
            "metric": "test_coverage",
            "score": 5.5,
            "threshold": 7.0,
            "severity": "medium"
        }
    ]
}
```

### Sample Workflow Data

```python
SAMPLE_WORKFLOW_DATA = {
    "workflow_id": "workflow-123",
    "step_analysis": {
        "steps_required": 7,
        "steps_executed": 5,
        "completion_rate": 0.71
    },
    "deviations": [
        {
            "type": "step_skipped",
            "description": "Step 6 (review) was skipped",
            "impact": "high"
        }
    ]
}
```

### Sample Usage Data

```python
SAMPLE_USAGE_DATA = {
    "statistics": {
        "total_commands": 1250,
        "cli_commands": 800,
        "cursor_skills": 300,
        "simple_mode": 150,
        "command_success_rate": 0.92
    }
}
```

---

## Test Execution Plan

### Phase 1: Unit Tests (Priority 1)

1. Implement FactorExtractor tests
2. Implement ScoreCalculator tests
3. Implement PriorityClassifier tests
4. Implement PriorityEvaluator tests
5. Implement HistoryTracker tests

**Target:** > 90% coverage for priority_evaluator.py

### Phase 2: Integration Tests (Priority 2)

1. Implement ReportGenerator integration tests
2. Implement EvaluatorAgent integration tests

**Target:** Full integration coverage

### Phase 3: End-to-End Tests (Priority 3)

1. Test complete evaluation workflow
2. Test with real project data
3. Test historical tracking over time

**Target:** Validate real-world usage

---

## Validation Criteria

### Functional Validation

- ✅ All factors extracted correctly
- ✅ Scores calculated accurately
- ✅ Priorities classified correctly
- ✅ History tracked properly
- ✅ Reports generated with priorities

### Non-Functional Validation

- ✅ Performance: < 1 second per recommendation
- ✅ Consistency: Same input = same output
- ✅ Error Handling: Graceful degradation
- ✅ Memory: No memory leaks
- ✅ Thread Safety: Safe for concurrent use (if applicable)

---

## Test Implementation Checklist

- [ ] Create test file structure
- [ ] Implement FactorExtractor unit tests
- [ ] Implement ScoreCalculator unit tests
- [ ] Implement PriorityClassifier unit tests
- [ ] Implement PriorityEvaluator unit tests
- [ ] Implement HistoryTracker unit tests
- [ ] Implement ReportGenerator integration tests
- [ ] Implement EvaluatorAgent integration tests
- [ ] Add test data fixtures
- [ ] Run test coverage analysis
- [ ] Fix any failing tests
- [ ] Achieve > 90% coverage target

---

## Expected Test Results

### Unit Tests

- **Total Tests:** ~30-40 unit tests
- **Expected Pass Rate:** 100%
- **Coverage Target:** > 90%

### Integration Tests

- **Total Tests:** ~5-10 integration tests
- **Expected Pass Rate:** 100%
- **Coverage Target:** Full integration paths

---

## Test Maintenance

### Ongoing Maintenance

- Update tests when factor extraction logic changes
- Update tests when scoring formula changes
- Update tests when thresholds change
- Add tests for new features

### Test Data Updates

- Refresh sample data periodically
- Add edge cases as discovered
- Include real-world examples

---

## Conclusion

Comprehensive test suite required to validate priority evaluation system. Focus on unit tests first, then integration tests, then end-to-end validation. Target > 90% code coverage with 100% pass rate.
