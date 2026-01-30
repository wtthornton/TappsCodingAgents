# Health Metrics Pipeline Unification - System Architecture

**Date**: 2026-01-30
**Version**: 1.0
**Status**: Design
**Architect**: TappsCodingAgents Architect Agent
**Epic**: HM-001 - Health Metrics Pipeline Unification

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Design Patterns](#design-patterns)
4. [Component Architecture](#component-architecture)
5. [Data Flow](#data-flow)
6. [API Contracts](#api-contracts)
7. [Integration Points](#integration-points)
8. [Security Architecture](#security-architecture)
9. [Performance Architecture](#performance-architecture)
10. [Technology Stack](#technology-stack)
11. [Deployment Architecture](#deployment-architecture)
12. [Migration Strategy](#migration-strategy)

---

## 1. Executive Summary

### 1.1 Problem Statement

The TappsCodingAgents health metrics system suffers from **data pipeline misalignment** where execution metrics and analytics are written to separate locations without synchronization. This causes:

- Health overview showing "0 workflows" despite heavy usage (analytics empty, metrics populated)
- Overall status "UNHEALTHY" despite 83.1/100 score (any unhealthy check → overall unhealthy)
- Outcomes showing "no data" despite review executions (no review artifacts or analytics)
- Discouraging messages for minimal but functional setups

### 1.2 Solution Overview

Implement a **unified health metrics architecture** using the **Fallback Pattern** to prefer official analytics data while gracefully falling back to execution metrics when analytics is unavailable. Key improvements:

1. **Usage Fallback**: Aggregate usage from `.tapps-agents/metrics/executions_*.jsonl` when `.tapps-agents/analytics/` is empty
2. **Outcomes Fallback**: Derive outcomes from review execution metrics when review artifacts don't exist
3. **Smart Status Logic**: Use "degraded" status when score ≥75 and only non-critical checks fail
4. **Dual-Write (Optional)**: Synchronize execution metrics to analytics for long-term consistency
5. **Relaxed Thresholds**: Encourage new users with minimal setups

### 1.3 Architectural Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Backward Compatibility** | Existing analytics pipeline must work unchanged | Analytics data always preferred when available |
| **Graceful Degradation** | System continues with reduced functionality | Fall back to execution metrics when analytics empty |
| **Performance** | No degradation to health check speed | Streaming I/O, caching, <500ms aggregation |
| **Separation of Concerns** | Data sources clearly separated | Dedicated providers for analytics vs metrics |
| **Testability** | Easy to test with mocks | Dependency injection, interface-based design |

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Health Overview CLI Command                  │
│                  (handle_health_overview_command)               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               v
        ┌──────────────────────────────────────────┐
        │     Usage Data Resolution (NEW)          │
        │  1. Try Analytics (AnalyticsDashboard)   │
        │  2. If empty → Execution Metrics Fallback│
        └──────────┬─────────────────┬─────────────┘
                   │                 │
        (Primary)  v                 v  (Fallback - NEW)
    ┌──────────────────┐     ┌──────────────────────────┐
    │ Analytics        │     │ Execution Metrics        │
    │ Dashboard        │     │ Aggregator (Helper)      │
    │ (.analytics/)    │     │ (_get_usage_from_        │
    │                  │     │  execution_metrics)      │
    └──────────────────┘     └──────────────────────────┘
                                     │
                                     v
                          ┌──────────────────────┐
                          │ Execution Metrics    │
                          │ Collector            │
                          │ (.metrics/           │
                          │  executions_*.jsonl) │
                          └──────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              Outcome Health Check (OutcomeHealthCheck)          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               v
        ┌──────────────────────────────────────────┐
        │   Outcome Data Resolution (NEW)          │
        │  1. Try Review Artifacts + Analytics     │
        │  2. If empty → Execution Metrics Fallback│
        └──────────┬─────────────────┬─────────────┘
                   │                 │
        (Primary)  v                 v  (Fallback - NEW)
    ┌──────────────────┐     ┌──────────────────────────┐
    │ Review           │     │ Execution Metrics        │
    │ Artifacts +      │     │ Review Aggregator        │
    │ Analytics        │     │ (_compute_outcomes_from_ │
    │                  │     │  execution_metrics)      │
    └──────────────────┘     └──────────────────────────┘
                                     │
                                     v
                          ┌──────────────────────┐
                          │ Execution Metrics    │
                          │ Collector            │
                          │ (review executions)  │
                          └──────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│           Health Orchestrator (get_overall_health)              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               v
        ┌──────────────────────────────────────────┐
        │   Status Decision Logic (MODIFIED)       │
        │  - Calculate weighted score              │
        │  - Identify critical vs non-critical     │
        │  - If score ≥75 + only non-critical      │
        │    unhealthy → status = "degraded"       │
        └──────────────────────────────────────────┘
```

### 2.2 Current State vs Future State

#### Current State (Before)

```
Execution Path:
  Workflow → ExecutionMetricsCollector → .tapps-agents/metrics/executions_*.jsonl

Health Overview:
  CLI Command → AnalyticsDashboard → .tapps-agents/analytics/ (EMPTY!)
  Result: "0 workflows completed today"

Outcome Check:
  OutcomeHealthCheck → Review Artifacts + Analytics (EMPTY!)
  Result: "No outcome data available" (score: 50)

Overall Status:
  get_overall_health() → ANY unhealthy check → overall "unhealthy"
  Result: Score 83.1 but status "UNHEALTHY"
```

#### Future State (After)

```
Execution Path (with Optional Dual-Write):
  Workflow → ExecutionMetricsCollector → .tapps-agents/metrics/executions_*.jsonl
          └→ AnalyticsCollector → .tapps-agents/analytics/ (POPULATED!)

Health Overview (with Fallback):
  CLI Command → Try Analytics (preferred)
             └→ If empty → _get_usage_from_execution_metrics()
  Result: Accurate workflow counts even without analytics

Outcome Check (with Fallback):
  OutcomeHealthCheck → Try Review Artifacts + Analytics (preferred)
                    └→ If empty → _compute_outcomes_from_execution_metrics()
  Result: "Outcomes derived from execution metrics: N reviews, Y% passed" (score: 60-70)

Overall Status (Smart Logic):
  get_overall_health() → If score ≥75 AND only non-critical unhealthy → "degraded"
  Result: Score 83.1 with status "DEGRADED" (core functionality healthy)
```

---

## 3. Design Patterns

### 3.1 Fallback Pattern (Primary Pattern)

**Intent**: Provide primary functionality with graceful degradation to secondary data source when primary is unavailable.

**Structure**:
```python
class DataProvider:
    def get_data(self):
        # Try primary source
        data = self._try_primary_source()
        if data and self._is_sufficient(data):
            return data

        # Fall back to secondary source
        logger.info("Primary source empty, using fallback")
        return self._try_fallback_source()
```

**Participants**:
- **Primary Source**: Analytics Dashboard (`.tapps-agents/analytics/`)
- **Fallback Source**: Execution Metrics Aggregator (`.tapps-agents/metrics/`)
- **Client**: Health Overview Command, Outcome Health Check

**Applicability**:
- Usage data resolution (analytics → execution metrics)
- Outcome data resolution (review artifacts + analytics → execution metrics)

**Benefits**:
- Backward compatibility (analytics continues to work)
- Resilience (system works even when analytics is empty)
- Performance (primary source cached, fallback computed on demand)

**Implementation**:
```python
# Usage Fallback (in health.py)
def _get_usage_data(project_root: Path) -> Dict[str, Any]:
    """Get usage data with fallback to execution metrics."""
    # Try analytics (primary)
    analytics = CursorAnalyticsAccessor()
    dashboard_data = analytics.get_dashboard_data()
    agents = dashboard_data.get("agents", [])
    workflows = dashboard_data.get("workflows", [])

    # Check if analytics has data
    if agents or workflows:
        logger.debug("Using analytics data for usage")
        return _format_analytics_usage(agents, workflows)

    # Fall back to execution metrics
    logger.info("Analytics empty, using execution metrics fallback")
    return _get_usage_from_execution_metrics(project_root, days=30)
```

### 3.2 Adapter Pattern

**Intent**: Convert execution metrics format to analytics-compatible format.

**Structure**:
```python
class ExecutionMetricsAdapter:
    """Adapts execution metrics to analytics format."""

    def to_analytics_agent(self, metric: ExecutionMetric) -> Dict:
        return {
            "agent_name": metric.skill or metric.command,
            "status": metric.status,
            "duration_ms": metric.duration_ms,
            "timestamp": metric.started_at,
        }

    def to_analytics_workflow(self, metrics: List[ExecutionMetric]) -> Dict:
        return {
            "workflow_id": metrics[0].workflow_id,
            "status": self._aggregate_status(metrics),
            "duration_ms": self._total_duration(metrics),
        }
```

**Applicability**:
- Transforming execution metrics to analytics format for fallback
- Dual-write implementation (metrics → analytics)

### 3.3 Strategy Pattern

**Intent**: Define a family of data source strategies and make them interchangeable.

**Structure**:
```python
class DataSourceStrategy(ABC):
    @abstractmethod
    def get_usage(self) -> Dict[str, Any]:
        pass

class AnalyticsDataSource(DataSourceStrategy):
    def get_usage(self) -> Dict[str, Any]:
        return self._analytics.get_dashboard_data()

class ExecutionMetricsDataSource(DataSourceStrategy):
    def get_usage(self) -> Dict[str, Any]:
        return self._aggregate_from_metrics()

# Usage
data_source: DataSourceStrategy = (
    AnalyticsDataSource() if analytics_available
    else ExecutionMetricsDataSource()
)
usage = data_source.get_usage()
```

**Applicability**:
- Swapping between analytics and execution metrics data sources
- Future extensibility (add new data sources)

---

## 4. Component Architecture

### 4.1 Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                      CLI Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  handle_health_overview_command()                        │  │
│  │  - Entry point for health overview CLI                   │  │
│  │  - Coordinates usage data resolution                     │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼─────────────────────────────────────┘
                         │
┌────────────────────────v────────────────────────────────────────┐
│                   Data Providers (NEW)                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  _get_usage_from_execution_metrics(project_root, days) │    │
│  │  - Fallback aggregator for usage data                  │    │
│  │  - Reads JSONL files, filters by date, aggregates      │    │
│  │  - Returns: {completed, failed, top_agents, top_workflows}│ │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  _compute_outcomes_from_execution_metrics(days)         │   │
│  │  - Fallback aggregator for outcomes data               │   │
│  │  - Filters review executions, computes success/gate_pass│   │
│  │  - Returns: {review_count, success_rate, gate_pass_rate}│  │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────v────────────────────────────────────────┐
│                 Data Sources (Existing)                         │
│  ┌──────────────────────────────────┐  ┌────────────────────┐  │
│  │  AnalyticsDashboard              │  │ ExecutionMetrics   │  │
│  │  - get_dashboard_data()          │  │ Collector          │  │
│  │  - Read .analytics/              │  │ - get_metrics()    │  │
│  │  - Primary source                │  │ - Read .metrics/   │  │
│  └──────────────────────────────────┘  │ - Fallback source  │  │
│                                         └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Health Check Layer                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  OutcomeHealthCheck (MODIFIED)                         │     │
│  │  - run() with fallback logic                           │     │
│  │  - Try review artifacts + analytics first              │     │
│  │  - Fall back to _compute_outcomes_from_execution_metrics│    │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  KnowledgeBaseHealthCheck (MODIFIED)                   │     │
│  │  - Relaxed thresholds for minimal setups               │     │
│  │  - Encouraging messaging                                │    │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Context7CacheHealthCheck (MODIFIED)                   │     │
│  │  - Relaxed hit rate thresholds                          │    │
│  │  - Acceptable baseline messaging                        │    │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────v────────────────────────────────────────┐
│                 Health Orchestrator (MODIFIED)                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  get_overall_health()                                  │     │
│  │  - Calculate weighted score                            │     │
│  │  - Identify critical vs non-critical checks            │     │
│  │  - Smart status logic (degraded when score ≥75)        │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│             Optional: Dual-Write Layer (Story 4)                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Workflow Executor (MODIFIED)                          │     │
│  │  - Call record_execution() → Execution Metrics         │     │
│  │  - Call record_agent_execution() → Analytics           │     │
│  │  - Error handling (log warning if analytics fails)     │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Responsibilities

#### 4.2.1 Data Provider Layer (NEW)

**Component**: `_get_usage_from_execution_metrics(project_root, days)`

**Responsibilities**:
- Read execution metrics JSONL files from `.tapps-agents/metrics/`
- Filter metrics by date range (last N days, UTC timezone)
- Group executions by `workflow_id` and `skill`
- Aggregate counts (completed, failed, top agents, top workflows)
- Handle malformed JSONL lines gracefully (skip with warning)
- Log INFO message when fallback is activated

**Interfaces**:
```python
def _get_usage_from_execution_metrics(
    project_root: Path,
    days: int
) -> Dict[str, Any]:
    """
    Aggregate usage data from execution metrics.

    Args:
        project_root: Project root directory
        days: Number of days to look back (1 for today, 30 for top lists)

    Returns:
        {
            "completed": int,  # Completed workflows today
            "failed": int,     # Failed workflows today
            "top_agents": List[str],      # Top 5 agents by frequency
            "top_workflows": List[str],   # Top 5 workflows by completion count
        }
    """
```

**Dependencies**:
- `ExecutionMetricsCollector` (for get_metrics() if needed)
- Python stdlib: `pathlib`, `json`, `datetime`, `logging`

---

**Component**: `_compute_outcomes_from_execution_metrics(days)`

**Responsibilities**:
- Filter execution metrics for review-related executions
- Compute success rate from execution status
- Compute gate pass rate from `gate_pass` field
- Return outcome metrics for fallback scoring

**Interfaces**:
```python
def _compute_outcomes_from_execution_metrics(
    self,
    days: int = 30
) -> Dict[str, Any]:
    """
    Compute outcome metrics from execution metrics (fallback).

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        {
            "review_executions_count": int,
            "success_rate": float,  # Percentage (0-100)
            "gate_pass_rate": float | None,  # Percentage or None if no data
        }
    """
```

**Dependencies**:
- `ExecutionMetricsCollector`
- Python stdlib: `pathlib`, `datetime`, `logging`

#### 4.2.2 Health Check Layer (MODIFIED)

**Component**: `OutcomeHealthCheck`

**Modifications**:
- Add `_compute_outcomes_from_execution_metrics()` method
- Modify `run()` to check for empty analytics/artifacts and fall back
- Include fallback metadata in `HealthCheckResult.details`

**New Logic**:
```python
def run(self) -> HealthCheckResult:
    # Try existing logic (review artifacts + analytics)
    review_artifacts = self._get_review_artifacts()
    analytics_data = self.accessor.get_dashboard_data()

    # Check if we have data
    if not review_artifacts and not analytics_data.get("agents"):
        # Fall back to execution metrics
        logger.info("No review artifacts or analytics, using execution metrics fallback")
        fallback_data = self._compute_outcomes_from_execution_metrics(days=30)

        # Calculate score based on fallback data
        score = 60.0  # Base
        if fallback_data["success_rate"] >= 80.0:
            score += 10.0
        if fallback_data.get("gate_pass_rate") and fallback_data["gate_pass_rate"] >= 70.0:
            score += 5.0

        return HealthCheckResult(
            name=self.name,
            status="degraded" if score >= 70.0 else "unhealthy",
            score=score,
            message=f"Outcomes derived from execution metrics: {fallback_data['review_executions_count']} reviews",
            details={
                **fallback_data,
                "fallback_used": True,
                "fallback_source": "execution_metrics",
            }
        )

    # Continue with existing logic...
```

---

**Component**: `KnowledgeBaseHealthCheck`

**Modifications**:
- Reduce penalty for 2-4 files from -20 to -10
- Adjust status threshold: degraded if score >= 60 (was 70)
- Add encouraging message for minimal setups

**New Logic**:
```python
# Check if KB is minimal but acceptable
if 2 <= total_files <= 4 and total_domains >= 1:
    score -= 10.0  # Reduced penalty (was -20)
    issues.append("Minimal KB setup")
    remediation.append(
        "Minimal KB setup (2 files, 1 domain) is acceptable for basic usage. "
        "Score improves with more domains/content. Run: tapps-agents knowledge ingest"
    )
elif total_files < 2:
    score -= 20.0
    issues.append("Very few KB files")
```

---

**Component**: `Context7CacheHealthCheck`

**Modifications**:
- Adjust hit rate penalty: 70-90% → -10 (was -15), <70% → -30 (unchanged)
- Adjust response time penalty: 150-300ms → -5, >300ms → -10
- Add acceptable baseline messaging

**New Logic**:
```python
# Check hit rate (relaxed thresholds)
if 70.0 <= hit_rate < 90.0:
    score -= 10.0  # Reduced penalty (was -15)
    issues.append(f"Hit rate {hit_rate:.1f}% is acceptable for many setups")
    remediation.append(
        f"Hit rate {hit_rate:.1f}% is acceptable for many setups. "
        "Target ≥95% for optimal performance. "
        "Run: python scripts/prepopulate_context7_cache.py"
    )
elif hit_rate < 70.0:
    score -= 30.0  # Unchanged
    issues.append(f"Very low hit rate: {hit_rate:.1f}%")
```

#### 4.2.3 Health Orchestrator (MODIFIED)

**Component**: `HealthOrchestrator.get_overall_health()`

**Modifications**:
- Define critical vs non-critical checks
- Implement smart status logic (degraded when score ≥75 and only non-critical fail)
- Add explanatory message in details

**New Logic**:
```python
def get_overall_health(self, results: Dict[str, HealthCheckResult]) -> Dict[str, Any]:
    # Existing: Calculate weighted score
    critical_checks = {"environment", "execution"}
    total_weight = 0.0
    weighted_score = 0.0
    status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}

    for name, result in results.items():
        weight = 2.0 if name in critical_checks else 1.0
        total_weight += weight
        weighted_score += result.score * weight
        status_counts[result.status] += 1

    overall_score = weighted_score / total_weight if total_weight > 0 else 0.0

    # NEW: Smart status logic
    critical_unhealthy = any(
        results[name].status == "unhealthy"
        for name in critical_checks
        if name in results
    )

    non_critical_checks = set(results.keys()) - critical_checks
    only_non_critical_unhealthy = (
        status_counts["unhealthy"] > 0 and not critical_unhealthy
    )

    # Determine status
    if overall_score >= 75.0 and only_non_critical_unhealthy:
        overall_status = "degraded"
        status_reason = "Status degraded due to non-critical checks; core functionality is healthy"
    elif status_counts["unhealthy"] > 0:
        overall_status = "unhealthy"
        status_reason = None
    elif status_counts["degraded"] > 0:
        overall_status = "degraded"
        status_reason = None
    else:
        overall_status = "healthy"
        status_reason = None

    return {
        "status": overall_status,
        "score": overall_score,
        "message": f"Overall health: {overall_status} ({overall_score:.1f}/100)",
        "status_reason": status_reason,
        # ... rest of existing logic
    }
```

---

## 5. Data Flow

### 5.1 Usage Data Flow (Story 1)

```
┌─────────────────────────────────────────────────────────────┐
│ User: tapps-agents health overview                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     v
      ┌──────────────────────────────┐
      │ handle_health_overview_command│
      └────────────┬─────────────────┘
                   │
                   v
      ┌────────────────────────────────┐
      │ Try Analytics (Primary)        │
      │ CursorAnalyticsAccessor        │
      │ .get_dashboard_data()          │
      └──────┬─────────────────────────┘
             │
             v
        ┌─────────┐
        │ Empty?  │
        └─┬───┬───┘
          │   │
    (No)  │   │  (Yes)
          │   │
          v   v
    Use   │   ┌────────────────────────────────────┐
  Analytics   │ Fallback: _get_usage_from_         │
    Data      │ execution_metrics(project_root, 30)│
              └────────────┬───────────────────────┘
                           │
                           v
              ┌─────────────────────────────────────┐
              │ 1. List .metrics/executions_*.jsonl │
              │ 2. Filter by date (last 30 days)    │
              │ 3. Parse JSONL (streaming)          │
              │ 4. Group by workflow_id, skill      │
              │ 5. Aggregate counts                 │
              └────────────┬────────────────────────┘
                           │
                           v
              ┌─────────────────────────────────────┐
              │ Return:                             │
              │ {                                   │
              │   completed: 42,                    │
              │   failed: 3,                        │
              │   top_agents: ["reviewer",          │
              │                "implementer", ...], │
              │   top_workflows: ["build",          │
              │                  "review", ...]     │
              │ }                                   │
              └────────────┬────────────────────────┘
                           │
                           v
              ┌─────────────────────────────────────┐
              │ Format & Display in Health Overview │
              └─────────────────────────────────────┘
```

### 5.2 Outcomes Data Flow (Story 2)

```
┌─────────────────────────────────────────────────────────────┐
│ User: tapps-agents health check                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     v
      ┌──────────────────────────────┐
      │ OutcomeHealthCheck.run()     │
      └────────────┬─────────────────┘
                   │
                   v
      ┌────────────────────────────────┐
      │ Try Review Artifacts +         │
      │ Analytics (Primary)            │
      │ - .tapps-agents/reports/       │
      │ - AnalyticsDashboard           │
      └──────┬─────────────────────────┘
             │
             v
        ┌─────────┐
        │ Empty?  │
        └─┬───┬───┘
          │   │
    (No)  │   │  (Yes)
          │   │
          v   v
    Use   │   ┌────────────────────────────────────┐
  Existing│   │ Fallback: _compute_outcomes_from_  │
   Logic  │   │ execution_metrics(days=30)         │
          │   └────────────┬───────────────────────┘
          │                │
          │                v
          │   ┌─────────────────────────────────────┐
          │   │ 1. Get execution metrics            │
          │   │ 2. Filter: command=="review" OR     │
          │   │    skill contains "reviewer"        │
          │   │ 3. Filter: last 30 days             │
          │   │ 4. Compute success rate             │
          │   │ 5. Compute gate_pass rate           │
          │   └────────────┬────────────────────────┘
          │                │
          │                v
          │   ┌─────────────────────────────────────┐
          │   │ Return:                             │
          │   │ {                                   │
          │   │   review_executions_count: 25,      │
          │   │   success_rate: 88.0,               │
          │   │   gate_pass_rate: 76.0              │
          │   │ }                                   │
          │   └────────────┬────────────────────────┘
          │                │
          │                v
          │   ┌─────────────────────────────────────┐
          │   │ Calculate Score:                    │
          │   │ base=60 + (success≥80? 10 : 0)      │
          │   │        + (gate_pass≥70? 5 : 0)      │
          │   │ Score: 60-70 range                  │
          │   └────────────┬────────────────────────┘
          │                │
          └────────────────┘
                           │
                           v
              ┌─────────────────────────────────────┐
              │ Return HealthCheckResult            │
              │ - status: "degraded" or "unhealthy" │
              │ - score: 60-70                      │
              │ - details: fallback metadata        │
              └─────────────────────────────────────┘
```

### 5.3 Overall Status Data Flow (Story 3)

```
┌─────────────────────────────────────────────────────────────┐
│ HealthOrchestrator.get_overall_health(results)             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     v
      ┌──────────────────────────────┐
      │ Calculate Weighted Score     │
      │ - Critical checks: weight 2.0│
      │ - Non-critical: weight 1.0   │
      │ - weighted_score / total     │
      └────────────┬─────────────────┘
                   │
                   v
      ┌────────────────────────────────┐
      │ Identify Check Categories      │
      │ - critical = {environment,     │
      │               execution}       │
      │ - non_critical = {outcomes,    │
      │   knowledge_base, context7}    │
      └────────────┬───────────────────┘
                   │
                   v
      ┌────────────────────────────────┐
      │ Count Status by Category       │
      │ - critical_unhealthy count     │
      │ - non_critical_unhealthy count │
      └────────────┬───────────────────┘
                   │
                   v
      ┌──────────────────────────────────────────┐
      │ Decision Logic:                          │
      │                                          │
      │ IF score ≥75 AND                         │
      │    critical_unhealthy == 0 AND           │
      │    non_critical_unhealthy > 0            │
      │ THEN                                     │
      │   status = "degraded"                    │
      │   reason = "non-critical checks failed"  │
      │                                          │
      │ ELSE IF any check unhealthy              │
      │ THEN                                     │
      │   status = "unhealthy"                   │
      │                                          │
      │ ELSE IF any check degraded               │
      │ THEN                                     │
      │   status = "degraded"                    │
      │                                          │
      │ ELSE                                     │
      │   status = "healthy"                     │
      └──────────────────────┬───────────────────┘
                             │
                             v
              ┌──────────────────────────────────┐
              │ Return Overall Health Result     │
              │ - status                         │
              │ - score                          │
              │ - status_reason (if degraded)    │
              └──────────────────────────────────┘
```

### 5.4 Dual-Write Data Flow (Story 4 - Optional)

```
┌─────────────────────────────────────────────────────────────┐
│ Workflow Executor: Execute Step                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     v
      ┌──────────────────────────────┐
      │ ExecutionMetricsCollector    │
      │ .record_execution(...)       │
      │                              │
      │ Write to:                    │
      │ .tapps-agents/metrics/       │
      │  executions_2026-01-30.jsonl │
      └────────────┬─────────────────┘
                   │
                   v (NEW - Dual Write)
      ┌────────────────────────────────┐
      │ Try: AnalyticsCollector        │
      │ .record_agent_execution(...)   │
      │                                │
      │ Write to:                      │
      │ .tapps-agents/analytics/       │
      │  history/agents_*.json         │
      └──────┬─────────────────────────┘
             │
             v
        ┌─────────┐
        │ Success?│
        └─┬───┬───┘
          │   │
    (Yes) │   │  (No)
          │   │
          v   v
     Continue │
              v
      ┌────────────────────────────────┐
      │ Log Warning:                   │
      │ "Analytics write failed: {e}"  │
      │ (Execution continues)          │
      └────────────────────────────────┘
```

---

## 6. API Contracts

### 6.1 Data Provider Interfaces

#### 6.1.1 Usage Data Provider

```python
def _get_usage_from_execution_metrics(
    project_root: Path,
    days: int
) -> Dict[str, Any]:
    """
    Aggregate usage data from execution metrics (fallback source).

    Args:
        project_root: Project root directory containing .tapps-agents/
        days: Number of days to look back (1 for today, 30 for top lists)

    Returns:
        {
            "completed": int,           # Completed workflows in period
            "failed": int,              # Failed workflows in period
            "top_agents": List[str],    # Top 5 agents by frequency
            "top_workflows": List[str], # Top 5 workflows by completion count
            "source": "execution_metrics",
            "records_processed": int,   # Number of metrics read
        }

    Raises:
        IOError: If metrics directory is not readable (logged, returns empty data)

    Performance:
        - Must complete in <500ms for 1000 records
        - Uses streaming I/O (not loading all into memory)

    Side Effects:
        - Logs INFO message when fallback is activated
        - Logs WARNING for malformed JSONL lines (skips line, continues)
    """
```

#### 6.1.2 Outcomes Data Provider

```python
def _compute_outcomes_from_execution_metrics(
    self,
    days: int = 30
) -> Dict[str, Any]:
    """
    Compute outcome metrics from execution metrics (fallback source).

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        {
            "review_executions_count": int,    # Number of review executions
            "success_rate": float,             # Percentage (0-100)
            "gate_pass_rate": float | None,    # Percentage or None if no data
            "source": "execution_metrics",
            "records_processed": int,
        }

    Filtering Logic:
        Includes execution metrics where:
        - (command == "review" OR skill contains "reviewer") AND
        - started_at >= (now - days) in UTC

    Success Rate Calculation:
        success_rate = (count where status == "success") / total * 100

    Gate Pass Rate Calculation:
        gate_pass_rate = (count where gate_pass == True) /
                        (count where gate_pass is not None) * 100
        Returns None if no records have gate_pass field

    Side Effects:
        - Logs INFO message when fallback is activated
        - Logs DEBUG for filtering and aggregation details
    """
```

### 6.2 Health Check Result Schema

```python
@dataclass
class HealthCheckResult:
    """
    Health check result (existing schema - no breaking changes).

    New optional fields in `details` dict:
    - fallback_used: bool (indicates fallback was used)
    - fallback_source: str ("execution_metrics")
    - records_processed: int (number of metrics read)
    - status_reason: str (explanation for degraded status)
    """
    name: str
    status: Literal["healthy", "degraded", "unhealthy"]
    score: float  # 0-100
    message: str
    details: Dict[str, Any]
    remediation: List[str] | str | None = None
```

### 6.3 Execution Metric Schema

```python
@dataclass
class ExecutionMetric:
    """
    Single execution metric record (existing schema).

    Fields used by fallback logic:
    - workflow_id: str (for grouping workflows)
    - skill: str | None (for grouping agents, NEW field)
    - command: str (fallback if skill is None)
    - status: str ("success", "failed", "timeout", "cancelled")
    - started_at: str (ISO timestamp, for date filtering)
    - gate_pass: bool | None (for outcomes gate pass rate, NEW field)
    """
    execution_id: str
    workflow_id: str
    step_id: str
    command: str
    status: str
    duration_ms: float
    started_at: str
    retry_count: int = 0
    completed_at: str | None = None
    error_message: str | None = None
    skill: str | None = None           # NEW (recently added)
    gate_pass: bool | None = None      # NEW (recently added)
```

---

## 7. Integration Points

### 7.1 Internal Integration Points

| Component A | Component B | Integration Type | Data Flow |
|-------------|-------------|------------------|-----------|
| `handle_health_overview_command` | `AnalyticsDashboard` | Direct call | Analytics data (primary) |
| `handle_health_overview_command` | `_get_usage_from_execution_metrics` | Function call | Usage data (fallback) |
| `OutcomeHealthCheck` | `CursorAnalyticsAccessor` | Direct call | Analytics data (primary) |
| `OutcomeHealthCheck` | `_compute_outcomes_from_execution_metrics` | Method call | Outcome data (fallback) |
| `HealthOrchestrator` | `HealthCheckRegistry` | Registry pattern | All health check results |
| `Workflow Executor` | `ExecutionMetricsCollector` | Direct call | Execution metrics write |
| `Workflow Executor` | `AnalyticsCollector` (Optional) | Direct call | Analytics dual-write |

### 7.2 External Integration Points

| External System | Integration | Purpose |
|-----------------|-------------|---------|
| Filesystem (`.tapps-agents/metrics/`) | JSONL read | Read execution metrics |
| Filesystem (`.tapps-agents/analytics/`) | JSON read | Read analytics data |
| Filesystem (`.tapps-agents/reports/`) | JSON read | Read review artifacts |
| Logging System | Python `logging` | Log fallback activation, warnings |

### 7.3 Data Storage Locations

```
.tapps-agents/
├── metrics/
│   ├── executions_2026-01-20.jsonl    # Execution metrics (JSONL)
│   ├── executions_2026-01-29.jsonl
│   └── executions_2026-01-30.jsonl
│
├── analytics/                          # Analytics (JSON)
│   └── history/
│       ├── agents_2026-01.json
│       └── workflows_2026-01.json
│
├── reports/                            # Review artifacts (JSON)
│   └── 2026-01-30_review_abc123/
│       └── review_report.json
│
└── kb/                                 # Knowledge base
    └── context7-cache/
```

---

## 8. Security Architecture

### 8.1 Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| **Path Traversal** (reading metrics files) | High | Low | Use `Path.resolve()` to canonicalize paths; validate paths are within `.tapps-agents/` |
| **Malformed JSONL Injection** | Medium | Medium | JSON parse errors caught and logged; malicious data skipped |
| **Resource Exhaustion** (large JSONL files) | Medium | Low | Set max 10,000 lines per file; streaming I/O; timeout after 500ms |
| **Information Disclosure** (error messages) | Low | Low | Don't expose file paths in user-facing errors; log internally |

### 8.2 Security Controls

#### 8.2.1 Input Validation

```python
def _get_usage_from_execution_metrics(project_root: Path, days: int) -> Dict[str, Any]:
    # Validate project_root is absolute and exists
    project_root = project_root.resolve()  # Canonicalize path
    if not project_root.exists():
        logger.warning(f"Project root does not exist: {project_root}")
        return _empty_usage_data()

    # Validate metrics directory is within project root
    metrics_dir = project_root / ".tapps-agents" / "metrics"
    if not metrics_dir.is_relative_to(project_root):
        logger.error("Metrics directory is outside project root")
        return _empty_usage_data()

    # Validate days parameter
    if days < 1 or days > 365:
        logger.warning(f"Invalid days parameter: {days}, using 30")
        days = 30
```

#### 8.2.2 Error Handling

```python
# Don't expose file paths in user-facing errors
try:
    with open(metrics_file, "r") as f:
        data = json.loads(line)
except json.JSONDecodeError as e:
    # Log internal error with details
    logger.warning(f"Malformed JSON in {metrics_file}:{line_num}: {e}")
    # Skip line, continue processing
    continue
except Exception as e:
    # Generic user-facing error
    logger.error(f"Failed to read metrics: {type(e).__name__}")
    return _empty_usage_data()
```

#### 8.2.3 Resource Limits

```python
MAX_LINES_PER_FILE = 10_000
AGGREGATION_TIMEOUT_MS = 500

def _read_metrics_file(file_path: Path) -> List[ExecutionMetric]:
    """Read metrics file with resource limits."""
    metrics = []
    line_count = 0

    with open(file_path, "r") as f:
        for line in f:
            line_count += 1
            if line_count > MAX_LINES_PER_FILE:
                logger.warning(f"Max lines exceeded in {file_path}, stopping")
                break

            try:
                data = json.loads(line)
                metrics.append(ExecutionMetric.from_dict(data))
            except json.JSONDecodeError:
                continue  # Skip malformed lines

    return metrics
```

### 8.3 Data Privacy

- **No PII in execution metrics**: Execution metrics contain only workflow IDs, commands, and status (no user data)
- **Local file system only**: All data is stored locally in `.tapps-agents/` (no external transmission)
- **Read-only fallback**: Fallback logic only reads metrics, does not modify

---

## 9. Performance Architecture

### 9.1 Performance Requirements

| Component | Requirement | Measurement |
|-----------|-------------|-------------|
| `_get_usage_from_execution_metrics` | <500ms for 1000 records | Unit test with fixture file |
| `handle_health_overview_command` (total) | <2 seconds | Integration test |
| `_compute_outcomes_from_execution_metrics` | <300ms for 500 records | Unit test with fixture file |
| Memory usage (aggregation) | <50MB peak | Memory profiling |

### 9.2 Performance Optimizations

#### 9.2.1 Streaming I/O

```python
def _read_metrics_streaming(file_path: Path, days: int) -> Iterator[ExecutionMetric]:
    """Stream metrics from file (don't load all into memory)."""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)

    with open(file_path, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                metric = ExecutionMetric.from_dict(data)

                # Filter by date (early exit if outside range)
                metric_date = datetime.fromisoformat(metric.started_at.replace("Z", "+00:00"))
                if metric_date < cutoff_date:
                    continue

                yield metric
            except (json.JSONDecodeError, ValueError):
                continue  # Skip malformed lines
```

#### 9.2.2 Efficient Aggregation

```python
def _aggregate_workflows(metrics: Iterator[ExecutionMetric]) -> Dict[str, int]:
    """Aggregate workflows with single pass (O(n))."""
    workflow_counts = defaultdict(int)

    for metric in metrics:
        if metric.status == "success":
            workflow_counts[metric.workflow_id] += 1

    # Sort and return top 5 (O(n log n) for sort, but n is small after aggregation)
    return dict(sorted(workflow_counts.items(), key=lambda x: x[1], reverse=True)[:5])
```

#### 9.2.3 Date Filtering Optimization

```python
def _get_relevant_metric_files(metrics_dir: Path, days: int) -> List[Path]:
    """Only read metric files within date range."""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    relevant_files = []

    for file in metrics_dir.glob("executions_*.jsonl"):
        # Extract date from filename (executions_2026-01-30.jsonl)
        try:
            date_str = file.stem.split("_")[1]  # "2026-01-30"
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)

            if file_date >= cutoff_date:
                relevant_files.append(file)
        except (IndexError, ValueError):
            # Can't parse date, include file anyway
            relevant_files.append(file)

    return relevant_files
```

### 9.3 Caching Strategy (Future Enhancement)

```python
# Future: Cache aggregated usage data for 5 minutes
@lru_cache(maxsize=1)
def _get_cached_usage(project_root_str: str, days: int, cache_key: float) -> Dict[str, Any]:
    """Cache usage data with 5-minute TTL (cache_key is timestamp // 300)."""
    project_root = Path(project_root_str)
    return _get_usage_from_execution_metrics(project_root, days)

# Usage
cache_key = time.time() // 300  # 5-minute buckets
usage = _get_cached_usage(str(project_root), days, cache_key)
```

---

## 10. Technology Stack

### 10.1 Core Technologies

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| **Language** | Python | 3.8+ | Existing framework language |
| **File Format** | JSONL (metrics) | N/A | Existing format, append-only, streaming-friendly |
| **File I/O** | `pathlib.Path` | stdlib | Cross-platform, Pythonic API |
| **JSON Parsing** | `json` module | stdlib | Stdlib (no dependencies), fast for line-by-line |
| **Date Handling** | `datetime` | stdlib | UTC timezone support, ISO format parsing |
| **Logging** | `logging` module | stdlib | Structured logging, configurable levels |
| **Aggregation** | `collections.defaultdict` | stdlib | Efficient grouping/counting |

### 10.2 No New Dependencies

**Critical Constraint**: This architecture uses **stdlib only** (no new external dependencies).

**Rationale**:
- Avoid dependency conflicts
- Reduce installation complexity
- Leverage existing Python stdlib capabilities
- Maintain framework simplicity

---

## 11. Deployment Architecture

### 11.1 Deployment Model

**Type**: Single-process, local file system
**Distribution**: Python package (`tapps-agents` PyPI package)
**Installation**: `pip install tapps-agents`

### 11.2 File System Layout

```
<project_root>/
└── .tapps-agents/
    ├── config.yaml                    # Configuration
    ├── metrics/                       # Execution metrics (JSONL)
    │   ├── executions_2026-01-20.jsonl
    │   ├── executions_2026-01-29.jsonl
    │   └── executions_2026-01-30.jsonl
    ├── analytics/                     # Analytics (JSON)
    │   └── history/
    │       ├── agents_2026-01.json
    │       └── workflows_2026-01.json
    ├── reports/                       # Review artifacts
    │   └── 2026-01-30_review_abc123/
    │       └── review_report.json
    └── kb/                            # Knowledge base
        └── context7-cache/
```

### 11.3 Backward Compatibility

**Migration Path**: None required (backward compatible)

**Compatibility Matrix**:
| Component | Before | After | Compatible? |
|-----------|--------|-------|-------------|
| Execution metrics JSONL | Existing | Unchanged | ✅ Yes |
| Analytics JSON | Existing (if used) | Unchanged | ✅ Yes |
| HealthCheckResult schema | Existing fields | + optional details fields | ✅ Yes (additive) |
| Health overview CLI | Reads analytics only | Analytics OR metrics fallback | ✅ Yes (prefers analytics) |

---

## 12. Migration Strategy

### 12.1 Phased Rollout

**Phase 1 (Stories 1-3, 5)**: MVP - 4 days
- Implement fallback logic for usage and outcomes
- Implement smart degraded status logic
- Relax KB/Context7 thresholds
- **No breaking changes**, fully backward compatible

**Phase 2 (Story 4)**: Optional - 1 day (can be deferred)
- Implement dual-write to analytics
- Gradual data pipeline alignment
- **No breaking changes**, additive only

### 12.2 Rollback Plan

**If issues arise**:
1. **Feature flags**: Add config option to disable fallback logic
   ```yaml
   # .tapps-agents/config.yaml
   health:
     enable_execution_metrics_fallback: false  # Revert to analytics-only
   ```

2. **Revert commits**: Each story is a separate commit for easy rollback

3. **Monitoring**: Track health check execution time and error rates
   - Alert if health overview takes >5 seconds
   - Alert if fallback activation rate > 50% (indicates analytics not populated)

### 12.3 Data Migration

**No data migration required** (backward compatible).

Existing data continues to work:
- ✅ Old execution metrics (without `skill` or `gate_pass`) are handled gracefully
- ✅ Existing analytics data is preferred when available
- ✅ Old health check results are compatible with new schema (additive fields)

---

## Appendix A: Sequence Diagrams

### A.1 Usage Fallback Sequence

```
User          CLI           Analytics    ExecutionMetrics    Filesystem
 |             |                |              |                |
 |-- health ---+>               |              |                |
 |   overview  |                |              |                |
 |             |                |              |                |
 |             +-- get_data -->|              |                |
 |             |                |              |                |
 |             |<-- empty ------+              |                |
 |             |                |              |                |
 |             +-- fallback ------------------->               |
 |             |                               |                |
 |             |                               +-- read files -->
 |             |                               |                |
 |             |                               |<-- JSONL ------+
 |             |                               |                |
 |             |                               +-- aggregate -->|
 |             |                               |                |
 |             |<-- usage data ----------------+                |
 |             |                               |                |
 |<-- display -+                               |                |
 |   usage    |                               |                |
```

### A.2 Outcomes Fallback Sequence

```
HealthCheck  OutcomeCheck  ReviewArtifacts  Analytics  ExecutionMetrics
 |             |                |              |              |
 +-- run() -->|                |              |              |
 |             |                |              |              |
 |             +-- get_artifacts ->            |              |
 |             |                |              |              |
 |             |<-- empty ------+              |              |
 |             |                               |              |
 |             +-- get_analytics ------------->|              |
 |             |                               |              |
 |             |<-- empty ---------------------+              |
 |             |                                              |
 |             +-- fallback_compute ----------------------->  |
 |             |                                              |
 |             |                                              +-- filter -->
 |             |                                              |  (reviews)
 |             |                                              |
 |             |<-- outcome_data -----------------------------+
 |             |  {success_rate, gate_pass_rate}             |
 |             |                                              |
 |<-- result--+                                              |
 |   (score:  |                                              |
 |    60-70)  |                                              |
```

---

## Appendix B: Component Checklist

### B.1 Implementation Checklist

**Story 1: Usage Fallback**
- [ ] Create `_get_usage_from_execution_metrics()` helper function
- [ ] Implement date filtering (UTC timezone handling)
- [ ] Implement workflow/agent aggregation logic
- [ ] Add INFO logging for fallback activation
- [ ] Integrate into `handle_health_overview_command()`
- [ ] Handle malformed JSONL gracefully (skip with warning)
- [ ] Unit tests (empty dir, 1000 records, malformed JSON, date filtering)
- [ ] Integration tests (end-to-end with test project)
- [ ] Performance test (<500ms for 1000 records)

**Story 2: Outcomes Fallback**
- [ ] Add `_compute_outcomes_from_execution_metrics()` method to `OutcomeHealthCheck`
- [ ] Implement review execution filtering
- [ ] Implement success rate calculation
- [ ] Implement gate pass rate calculation
- [ ] Modify `run()` to check for empty and fall back
- [ ] Add fallback metadata to details
- [ ] Calculate score (60-70 range based on rates)
- [ ] Unit tests (filtering, rate calculations, scoring)
- [ ] Integration tests (end-to-end with review metrics)

**Story 3: Degraded Status Logic**
- [ ] Define critical vs non-critical check sets
- [ ] Modify `get_overall_health()` status logic
- [ ] Implement conditional status assignment (score ≥75 + only non-critical unhealthy → degraded)
- [ ] Add explanatory message in details["status_reason"]
- [ ] Unit tests (various check combinations)
- [ ] Integration tests (high score + non-critical failures)

**Story 4: Dual-Write (Optional)**
- [ ] Audit codebase for `record_execution()` call sites
- [ ] Add `record_agent_execution()` calls with field mapping
- [ ] Add `record_workflow_execution()` on workflow completion
- [ ] Implement error handling (try-except with warning log)
- [ ] Verify project root alignment
- [ ] Unit tests (dual-write logic, error handling)
- [ ] Integration tests (verify both pipelines populated)

**Story 5: Threshold Adjustments**
- [ ] Update `KnowledgeBaseHealthCheck` scoring for minimal setups
- [ ] Add encouraging KB messaging
- [ ] Update `Context7CacheHealthCheck` hit rate thresholds
- [ ] Add acceptable baseline Context7 messaging
- [ ] Adjust response time thresholds
- [ ] Unit tests (updated scoring for 2 files, 77% hit rate)

---

**Document Status**: Complete
**Next Steps**: Proceed to Designer Agent for API/data model design
**Created By**: TappsCodingAgents Architect Agent
**Created**: 2026-01-30
