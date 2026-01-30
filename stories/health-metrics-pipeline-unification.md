---
epic_id: HM-001
epic_name: Health Metrics Pipeline Unification
created: 2026-01-30
status: planned
priority: high
estimated_effort: 31.5-41 hours (4-6 days)
---

# Epic: Health Metrics Pipeline Unification

## Overview

Unify health metrics data pipelines to accurately reflect framework usage, eliminate false "unhealthy" status, and improve user experience for heavy users and minimal setups.

**Problem Statement**: Health overview and usage are driven by two separate data pipelines (execution metrics and analytics) that are not aligned. This causes:
- Health overview showing "0 workflows" despite heavy usage
- Overall status "UNHEALTHY" despite 83.1/100 weighted score
- Outcomes showing "no data" despite review executions
- Discouraging messages for minimal but functional setups

**Solution**: Implement fallback to execution metrics when analytics is empty, improve overall status logic to use "degraded" for high scores with non-critical failures, and relax thresholds for minimal setups.

**Stakeholders**:
- **Primary**: Framework Users (accurate metrics), Heavy Users (reduced false alarms), New Users (clearer guidance)
- **Secondary**: Framework Maintainers (unified pipeline), CI/CD Systems (reliable status)

**References**:
- Requirements: `scratchpad/health-metrics-requirements.md`
- Review Document: `docs/feedback/HEALTH_METRICS_REVIEW_2026-01-30.md`
- Enhanced Prompt: `scratchpad/health-metrics-enhanced-prompt.md`

---

## User Stories

### Story 1: Usage Fallback to Execution Metrics (Priority 1 - High Impact)

**Story ID**: HM-001-S1
**Title**: Accurate Usage Statistics via Execution Metrics Fallback
**Priority**: High
**Story Points**: 8
**Estimated Effort**: 10.5-11.5 hours
**Status**: Planned

#### User Story

As a **framework user**,
I want to see **accurate usage statistics** in health overview that reflect actual workflow and agent executions,
So that I can **monitor framework activity** even when the analytics directory doesn't exist.

#### Context

Currently, health overview usage section only reads from `.tapps-agents/analytics/` which is never populated by workflow/simple-mode executions. This results in showing "0 workflows completed today" despite heavy framework usage. Execution metrics in `.tapps-agents/metrics/executions_*.jsonl` contain the actual execution data but are not used by health overview.

#### Acceptance Criteria

1. ✅ **Analytics Preference**: Health overview MUST first try to read from `.tapps-agents/analytics/`
2. ✅ **Fallback Activation**: If analytics directory is empty or has zero agents/workflows, aggregate from execution metrics
3. ✅ **Today's Usage**: Derive "completed today" and "failed today" from execution metrics (last 1 day, UTC timezone)
4. ✅ **Top Agents**: Derive "top 5 agents" from execution metrics `skill` field (last 30 days, sorted by frequency)
5. ✅ **Top Workflows**: Derive "top 5 workflows" from execution metrics `workflow_id` field (last 30 days, sorted by completion count)
6. ✅ **Reusable Helper**: Create `_get_usage_from_execution_metrics(project_root, days)` helper function
7. ✅ **Logging**: Log INFO message when fallback is activated with count of records processed
8. ✅ **Performance**: Aggregation completes in <500ms for files up to 1000 records/day
9. ✅ **Memory**: Uses streaming/line-by-line reading (not loading entire file into memory)
10. ✅ **Error Handling**: Malformed JSONL lines are skipped with warning log (not crash)
11. ✅ **Backward Compatibility**: Existing analytics pipeline continues to work when analytics data exists

#### Technical Details

**Files to Modify**:
- `tapps_agents/cli/commands/health.py` - Add `_get_usage_from_execution_metrics()` helper and integrate into `handle_health_overview_command()`
- `tapps_agents/workflow/execution_metrics.py` - May need `get_metrics()` enhancements for date filtering

**Dependencies**:
- None (standalone implementation)

**Complexity Drivers**:
- Date filtering with timezone handling (UTC)
- Grouping/aggregation logic (workflow_id, skill)
- Handling missing fields (old records without `skill`)
- Performance optimization (streaming I/O)

#### Tasks

1. **Create helper function** (`_get_usage_from_execution_metrics()` in health.py)
   - Signature: `(project_root: Path, days: int) -> Dict[str, Any]`
   - Return: `{"completed": int, "failed": int, "top_agents": List[str], "top_workflows": List[str]}`
   - Complexity: Medium (2-3 hours)

2. **Implement date filtering** (last N days from execution metrics)
   - Read `.tapps-agents/metrics/executions_*.jsonl` files
   - Filter by `started_at` >= N days ago (UTC)
   - Handle timezone-aware and naive timestamps
   - Complexity: Simple (1 hour)

3. **Implement aggregation logic** (group by workflow_id, skill)
   - Group executions by workflow_id (for today's completed/failed)
   - Group executions by skill (for top agents)
   - Count completions and sort by frequency
   - Complexity: Medium (2 hours)

4. **Add logging** (INFO level for fallback activation)
   - Log when fallback is activated
   - Include count of records processed
   - Complexity: Simple (0.5 hours)

5. **Integrate into health overview** command
   - Modify `handle_health_overview_command()` to use fallback
   - Prefer analytics, fall back to execution metrics when empty
   - Complexity: Simple (1 hour)

6. **Unit tests** for helper function
   - Test with empty metrics directory
   - Test with 1000-record fixture file
   - Test date filtering accuracy
   - Test aggregation correctness
   - Test malformed JSONL handling
   - Complexity: Medium (2 hours)

7. **Integration tests** with mock execution metrics
   - Create test project with execution metrics only (no analytics)
   - Run health overview and verify usage shows correct data
   - Verify performance (<2 seconds total)
   - Complexity: Medium (2 hours)

#### Definition of Done

- [ ] All acceptance criteria met
- [ ] All tasks completed
- [ ] Unit test coverage ≥80%
- [ ] Integration tests pass
- [ ] Performance requirement met (<500ms aggregation)
- [ ] Code review score ≥75
- [ ] Documentation updated

---

### Story 2: Outcomes Fallback to Execution Metrics (Priority 2 - Medium Impact)

**Story ID**: HM-001-S2
**Title**: Outcomes Derived from Execution Metrics
**Priority**: High
**Story Points**: 5
**Estimated Effort**: 9.5 hours
**Status**: Planned

#### User Story

As a **framework user**,
I want the outcomes health check to **reflect review activity** from execution metrics when review artifacts don't exist,
So that I **see accurate outcome trends** instead of "No outcome data available" when I've actually run reviews.

#### Context

OutcomeHealthCheck currently requires review artifacts (`.tapps-agents/reports/**/review_*.json`) or analytics data. When neither exists, it returns score 50 with message "No outcome data available". However, execution metrics contain review step data with `command == "review"` and `gate_pass` field, which can be used as a proxy for outcome quality.

#### Acceptance Criteria

1. ✅ **Analytics/Artifacts Preference**: `OutcomeHealthCheck.run()` MUST first try analytics + review artifacts
2. ✅ **Fallback Activation**: If `review_artifacts_count == 0` AND `len(agents_data) == 0`, fall back to execution metrics
3. ✅ **Review Filtering**: Filter execution metrics for `command == "review"` OR `skill` contains "reviewer" (last 30 days)
4. ✅ **Success Rate**: Compute success rate as `(count where status == "success") / total_review_executions * 100`
5. ✅ **Gate Pass Rate**: Compute gate pass rate as `(count where gate_pass == True) / (count where gate_pass is not None) * 100`
6. ✅ **Moderate Score**: Return score 60-70 instead of 50 when using fallback (60 base + 10 if success_rate ≥80% + 5 if gate_pass_rate ≥70%)
7. ✅ **Descriptive Message**: Message indicates "Outcomes derived from execution metrics: N review steps, Y% passed gate"
8. ✅ **Fallback Metadata**: Include metadata in details: `{"fallback_used": true, "fallback_source": "execution_metrics", "review_executions_count": <int>, "success_rate": <float>, "gate_pass_rate": <float | None>}`
9. ✅ **Logging**: Log INFO message when fallback is activated
10. ✅ **Backward Compatibility**: Existing logic using review artifacts is preserved

#### Technical Details

**Files to Modify**:
- `tapps_agents/health/checks/outcomes.py` - Add `_compute_outcomes_from_execution_metrics()` method and modify `run()`

**Dependencies**:
- None (standalone implementation)

**Complexity Drivers**:
- Filtering logic for review executions
- Gate pass rate calculation (handling None values)
- Scoring logic based on success/gate_pass rates

#### Tasks

1. **Create computation method** (`_compute_outcomes_from_execution_metrics()` in OutcomeHealthCheck)
   - Signature: `(days: int) -> Dict[str, Any]`
   - Return: `{"review_executions_count": int, "success_rate": float, "gate_pass_rate": float | None}`
   - Complexity: Medium (2 hours)

2. **Implement filtering** for review executions
   - Filter `command == "review"` OR `skill` contains "reviewer"
   - Filter by `started_at` >= 30 days ago
   - Complexity: Simple (1 hour)

3. **Compute success rate** and gate pass rate
   - Success rate: `(count where status == "success") / total * 100`
   - Gate pass rate: `(count where gate_pass == True) / (count where gate_pass is not None) * 100`
   - Complexity: Simple (1 hour)

4. **Update `run()` method** to use fallback
   - Check if analytics and artifacts are empty
   - Call `_compute_outcomes_from_execution_metrics()` if needed
   - Calculate score (60 base + bonuses)
   - Complexity: Simple (1 hour)

5. **Add metadata** to indicate fallback
   - Include fallback_used, fallback_source, counts, rates in details
   - Complexity: Simple (0.5 hours)

6. **Unit tests** for outcomes computation
   - Test with mock review execution metrics
   - Test success rate calculation
   - Test gate pass rate calculation (with and without gate_pass data)
   - Test scoring logic
   - Complexity: Medium (2 hours)

7. **Integration tests** with review execution metrics
   - Create test project with review execution metrics (no artifacts)
   - Run health check and verify outcomes fallback works
   - Verify score is 60-70 range
   - Complexity: Medium (2 hours)

#### Definition of Done

- [ ] All acceptance criteria met
- [ ] All tasks completed
- [ ] Unit test coverage ≥80%
- [ ] Integration tests pass
- [ ] Code review score ≥75
- [ ] Documentation updated

---

### Story 3: Overall Status Degraded Logic (Priority 3 - Medium Impact)

**Story ID**: HM-001-S3
**Title**: Smart Degraded Status for High Scores
**Priority**: High
**Story Points**: 5
**Estimated Effort**: 7 hours
**Status**: Planned

#### User Story

As a **heavy framework user** with high weighted score (≥75),
I want to see **"degraded" overall status** instead of "unhealthy" when only non-critical checks fail,
So that I **accurately understand system health** and reduce false alarm fatigue.

#### Context

Current logic sets overall status to "unhealthy" if ANY check is unhealthy, ignoring weighted score. This means a system with 83.1/100 score shows "UNHEALTHY" just because outcomes or knowledge_base checks failed, even though core functionality (environment, execution) is healthy. This creates false alarm fatigue for users.

#### Acceptance Criteria

1. ✅ **Critical Check Identification**: Define critical checks as `{"environment", "execution"}` and non-critical as `{"outcomes", "knowledge_base", "context7_cache", "automation"}`
2. ✅ **Weighted Score Threshold**: Use weighted score ≥75 as threshold for degraded status consideration
3. ✅ **Conditional Status Assignment**: Set overall status to "degraded" (not "unhealthy") when:
   - Weighted score ≥75 AND
   - All critical checks have status "healthy" or "degraded" (NOT "unhealthy") AND
   - Only non-critical checks have status "unhealthy"
4. ✅ **Existing Behavior Preserved**:
   - Overall "unhealthy" when critical check fails (regardless of score)
   - Overall "healthy" when all checks are healthy
   - Overall "unhealthy" when score <75
5. ✅ **Explanatory Messaging**: Add message in details["status_reason"]: "Status degraded due to non-critical checks; core functionality is healthy"
6. ✅ **Documentation**: Check categorization is clearly documented in code comments and docstrings

#### Technical Details

**Files to Modify**:
- `tapps_agents/health/orchestrator.py` - Modify `get_overall_health()` method (lines 137-242)

**Dependencies**:
- None (standalone implementation)

**Complexity Drivers**:
- Conditional logic for status assignment
- Backward compatibility (existing behavior for edge cases)
- Clear documentation of critical vs non-critical

#### Tasks

1. **Modify `get_overall_health()` logic** in HealthOrchestrator
   - Add critical/non-critical check identification
   - Implement conditional status assignment
   - Complexity: Medium (2 hours)

2. **Add critical vs non-critical check sets**
   - Define `CRITICAL_CHECKS = {"environment", "execution"}`
   - Define `NON_CRITICAL_CHECKS = {"outcomes", "knowledge_base", "context7_cache", "automation"}`
   - Complexity: Simple (0.5 hours)

3. **Implement conditional status assignment**
   - Check if weighted score ≥75
   - Check if all critical checks are healthy/degraded
   - Set status to "degraded" if conditions met, else "unhealthy"
   - Complexity: Simple (1 hour)

4. **Add explanatory message** in details
   - Add "status_reason" field to details dict
   - Message: "Status degraded due to non-critical checks; core functionality is healthy"
   - Complexity: Simple (0.5 hours)

5. **Unit tests** for various check combinations
   - Test: score ≥75 + critical healthy + non-critical unhealthy → degraded
   - Test: score ≥75 + critical unhealthy → unhealthy
   - Test: score <75 + non-critical unhealthy → unhealthy
   - Test: all checks healthy → healthy
   - Complexity: Medium (2 hours)

6. **Integration test** with high score + non-critical failures
   - Create mock health checks: environment=healthy, execution=healthy, outcomes=unhealthy
   - Verify overall status is "degraded" with score 83
   - Complexity: Simple (1 hour)

#### Definition of Done

- [ ] All acceptance criteria met
- [ ] All tasks completed
- [ ] Unit test coverage ≥80%
- [ ] Integration tests pass
- [ ] Code review score ≥75
- [ ] Documentation updated

---

### Story 4: Dual-Write to Analytics (Priority 4 - Medium Impact - Optional)

**Story ID**: HM-001-S4
**Title**: Sync Execution Metrics to Analytics Pipeline
**Priority**: Medium
**Story Points**: 8
**Estimated Effort**: 8.5 hours
**Status**: Planned (Optional)

#### User Story

As a **framework maintainer**,
I want execution metrics to **also populate analytics** when workflows execute,
So that **both pipelines stay in sync** long-term and health metrics have consistent data without relying on fallback.

#### Context

Current execution path only writes to `.tapps-agents/metrics/` via `ExecutionMetricsCollector.record_execution()`. Analytics in `.tapps-agents/analytics/` is never populated, causing the data pipeline misalignment. This story makes execution metrics also write to analytics for long-term data consistency.

**Note**: This story is OPTIONAL and can be deferred if time-constrained. Stories 1-3 and 5 provide immediate value via fallback logic.

#### Acceptance Criteria

1. ✅ **Call Site Identification**: All `ExecutionMetricsCollector.record_execution()` call sites are identified and documented
2. ✅ **Agent Execution Write**: Add `AnalyticsCollector.record_agent_execution()` call after each `record_execution()`
3. ✅ **Workflow Execution Write**: When workflow completes, aggregate to `AnalyticsCollector.record_workflow_execution()`
4. ✅ **Field Mapping**: Correct mapping of execution metric fields to analytics fields (agent_name ← skill|command, status ← status, duration_ms ← duration_ms, timestamp ← started_at)
5. ✅ **Project Root Alignment**: Both collectors use same project root (no duplicate directories)
6. ✅ **Error Handling**: Analytics write failures MUST NOT fail execution (try-except with warning log)
7. ✅ **Logging**: Warning is logged with error details if analytics write fails
8. ✅ **Backward Compatibility**: No changes to AnalyticsCollector schema or existing behavior

#### Technical Details

**Files to Modify**:
- `tapps_agents/workflow/execution_metrics.py` - Find call sites and add analytics writes
- Workflow executor files (e.g., `tapps_agents/workflow/executor.py`) - Add dual-write logic

**Dependencies**:
- None (standalone implementation, but builds on existing execution metrics)

**Complexity Drivers**:
- Identifying all call sites (audit)
- Field mapping correctness
- Error handling to prevent execution failure

#### Tasks

1. **Audit codebase** for `record_execution()` call sites
   - Search for all invocations
   - Document locations (workflow executor, step handlers, agent invocation points)
   - Complexity: Simple (1 hour)

2. **Add `record_agent_execution()` calls**
   - At each `record_execution()` call site, add corresponding analytics write
   - Map fields correctly
   - Complexity: Simple (1 hour)

3. **Add `record_workflow_execution()` on completion**
   - Identify workflow completion trigger
   - Aggregate status (success if all steps success, failed if any failed)
   - Calculate total duration
   - Complexity: Medium (2 hours)

4. **Add error handling** (try-except with warning log)
   - Wrap analytics writes in try-except
   - Log warning with error details if fails
   - Ensure execution continues
   - Complexity: Simple (0.5 hours)

5. **Unit tests** for dual-write logic
   - Test analytics write is called with correct parameters
   - Test execution continues if analytics write fails
   - Test field mapping correctness
   - Complexity: Medium (2 hours)

6. **Integration test** verifying both pipelines
   - Run workflow
   - Verify both `.tapps-agents/metrics/` and `.tapps-agents/analytics/` are populated
   - Verify data consistency
   - Complexity: Medium (2 hours)

#### Definition of Done

- [ ] All acceptance criteria met
- [ ] All tasks completed
- [ ] Unit test coverage ≥80%
- [ ] Integration tests pass
- [ ] Code review score ≥75
- [ ] Documentation updated

---

### Story 5: KB and Context7 Threshold Adjustments (Priority 5 - Low Impact)

**Story ID**: HM-001-S5
**Title**: Encouraging Thresholds for Minimal Setups
**Priority**: Low
**Story Points**: 3
**Estimated Effort**: 4.5 hours
**Status**: Planned

#### User Story

As a **new framework user** with minimal KB setup,
I want to see **"degraded" status with encouraging messaging** instead of "unhealthy" with discouraging warnings,
So that I **understand minimal setup is acceptable** and know how to improve if needed.

#### Context

Current thresholds are too strict for minimal setups:
- Knowledge Base: 2 files + 1 domain → score 55 → "unhealthy" with message "Very few KB files: 2"
- Context7 Cache: 77% hit rate → score 65 → "unhealthy" with message "Low hit rate: 77.0% (target: ≥95%)"

These messages are discouraging for users with functional minimal setups. Relaxing thresholds and adding encouraging messaging improves onboarding experience.

#### Acceptance Criteria

1. ✅ **KB Minimal Setup Scoring**: 2 files + 1 domain → score 60-70 → "degraded" (not "unhealthy")
2. ✅ **KB Encouraging Message**: Add message: "Minimal KB setup (2 files, 1 domain) is acceptable for basic usage. Score improves with more domains/content. Run: tapps-agents knowledge ingest"
3. ✅ **Context7 Hit Rate Threshold**: 70-90% hit rate → score 70-80 → "degraded" (not "unhealthy")
4. ✅ **Context7 Acceptable Baseline Message**: Add message: "Hit rate {X}% is acceptable for many setups. Target ≥95% for optimal performance. Run: python scripts/prepopulate_context7_cache.py"
5. ✅ **Context7 Response Time Threshold**: 150-300ms → -5 penalty (degraded), >300ms → -10 (unhealthy)
6. ✅ **Tone**: All messages are encouraging and actionable (include next step)
7. ✅ **Backward Compatibility**: Scoring logic for empty KB (0-1 files) and very low hit rate (<70%) remains "unhealthy"

#### Technical Details

**Files to Modify**:
- `tapps_agents/health/checks/knowledge_base.py` - Update scoring and messaging (lines 106-148)
- `tapps_agents/health/checks/context7_cache.py` - Update thresholds and messaging (lines 122-163)

**Dependencies**:
- None (standalone implementation)

**Complexity Drivers**:
- Adjusting scoring thresholds correctly
- Clear messaging that's encouraging yet actionable

#### Tasks

1. **Update `KnowledgeBaseHealthCheck` scoring**
   - Reduce penalty for 2-4 files from -20 to -10
   - Adjust status threshold: degraded if score >= 60 (was 70)
   - Complexity: Simple (1 hour)

2. **Add KB encouraging messaging**
   - Add message when total_files == 2 and total_domains == 1
   - Message includes actionable next step (tapps-agents knowledge ingest)
   - Complexity: Simple (0.5 hours)

3. **Update `Context7CacheHealthCheck` thresholds**
   - Adjust hit rate penalty: 70-90% → -10 (was -15), <70% → -30 (unchanged)
   - Adjust response time penalty: 150-300ms → -5, >300ms → -10
   - Complexity: Simple (1 hour)

4. **Add Context7 acceptable baseline messaging**
   - Add message when hit rate is 70-90%
   - Message includes actionable next step (prepopulate script)
   - Complexity: Simple (0.5 hours)

5. **Unit tests** for updated scoring
   - Test KB: 2 files + 1 domain → degraded
   - Test KB: 0 files → unhealthy
   - Test Context7: 77% hit rate → degraded
   - Test Context7: 60% hit rate → unhealthy
   - Test Context7: 176ms response time → small penalty
   - Complexity: Simple (1.5 hours)

#### Definition of Done

- [ ] All acceptance criteria met
- [ ] All tasks completed
- [ ] Unit test coverage ≥80%
- [ ] Code review score ≥75
- [ ] Documentation updated

---

## Epic Summary

### Story Prioritization

| Story | Priority | Impact | Points | Effort | Dependencies |
|-------|----------|--------|--------|--------|--------------|
| HM-001-S1: Usage Fallback | P1 | High | 8 | 10.5-11.5h | None |
| HM-001-S2: Outcomes Fallback | P2 | Medium | 5 | 9.5h | None |
| HM-001-S3: Degraded Status | P3 | Medium | 5 | 7h | None |
| HM-001-S4: Dual-Write (Optional) | P4 | Medium | 8 | 8.5h | None |
| HM-001-S5: Threshold Adjustments | P5 | Low | 3 | 4.5h | None |
| **Total (All)** | | | **29** | **40-41h** | |
| **MVP (P1-P3, P5)** | | | **21** | **31.5-32.5h** | |

### Implementation Phases

**Phase 1 (MVP - Stories 1, 2, 3, 5)**: 31.5-32.5 hours (4 days)
- Delivers high and medium impact improvements
- Addresses core user pain points
- Can be released independently

**Phase 2 (Optional - Story 4)**: 8.5 hours (1 day)
- Dual-write for long-term data consistency
- Can be deferred if time-constrained

### Success Metrics

**User Experience**:
- ✅ Heavy users see accurate usage statistics (not 0 workflows)
- ✅ Users with high scores (83+) see "degraded" status (not "unhealthy")
- ✅ Users with minimal setups see encouraging messages

**Technical**:
- ✅ Test coverage ≥80% for modified files
- ✅ Code review score ≥75
- ✅ Security scan passes
- ✅ Performance: Health overview <2 seconds

**Backward Compatibility**:
- ✅ Existing analytics pipeline works unchanged
- ✅ No breaking changes to HealthCheckResult schema
- ✅ Old execution metrics (without skill/gate_pass) still work

### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance degradation (large files) | Medium | High | Streaming I/O, max 10K lines |
| Breaking analytics pipeline | Low | Critical | Prefer analytics, only fall back when empty |
| Timezone issues | Medium | Medium | Use UTC, handle aware/naive datetimes |
| Dual-write failures (P4) | Low | Critical | Try-except, log warning, don't fail execution |

### Dependencies

**Internal**:
- ExecutionMetricsCollector (must have execution metrics to fall back to)
- AnalyticsCollector (P4 only)
- HealthCheckRegistry (for check categorization)

**External**:
- None (stdlib only)

**Blocking**:
- None (all stories can proceed independently)

---

## Appendix

### Story Point Reference (Fibonacci)

- **1 point**: Trivial task, <1 hour (e.g., update config value)
- **2 points**: Simple task, 1-2 hours (e.g., add logging)
- **3 points**: Small task, 2-4 hours (e.g., simple helper function)
- **5 points**: Medium task, 4-8 hours (e.g., outcomes fallback, degraded status)
- **8 points**: Large task, 8-16 hours (e.g., usage fallback, dual-write)
- **13 points**: Very large task, 16-32 hours (e.g., entire epic)

### Complexity Reference

- **Simple**: Straightforward implementation, minimal edge cases, <2 hours
- **Medium**: Moderate complexity, some edge cases, requires careful testing, 2-4 hours
- **Complex**: High complexity, many edge cases, significant testing, >4 hours

### Related Documents

- **Requirements**: `scratchpad/health-metrics-requirements.md`
- **Enhanced Prompt**: `scratchpad/health-metrics-enhanced-prompt.md`
- **Review Document**: `docs/feedback/HEALTH_METRICS_REVIEW_2026-01-30.md`
- **Health Architecture**: `docs/OBSERVABILITY_GUIDE.md`

---

**Document Status**: Complete
**Next Steps**: Proceed to Architect Agent for system design
**Created By**: TappsCodingAgents Planner Agent
**Created**: 2026-01-30
