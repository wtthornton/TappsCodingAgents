# Story: Dual-Write to Analytics When Recording Executions

**Status:** Implemented  
**Priority:** Medium  
**Source:** HEALTH_METRICS_REVIEW_2026-01-30 (Recommendation 3.2)

---

## Goal

When workflow/step execution is recorded via `ExecutionMetricsCollector.record_execution()`, also write to the analytics pipeline (`AnalyticsCollector.record_agent_execution()` / `record_workflow_execution()`) so health overview "usage" and outcomes have real data without relying only on execution-metrics fallback.

---

## Background

- **Execution metrics:** `.tapps-agents/metrics/executions_*.jsonl` — written by `ExecutionMetricsCollector` from workflow/step handlers.
- **Analytics:** `.tapps-agents/analytics/history/` — written by `AnalyticsCollector`; read by health overview "usage" and outcomes (via `CursorAnalyticsAccessor` → `AnalyticsDashboard`).
- Today, workflow/simple-mode execution does **not** call `AnalyticsCollector`, so usage and outcomes often show "no data" until we fall back to execution metrics. Dual-write keeps both in sync and improves long-term analytics.

---

## Acceptance Criteria

1. Wherever `ExecutionMetricsCollector.record_execution()` is called (workflow executor / step runner), also call the appropriate analytics recording (e.g. `AnalyticsCollector.record_agent_execution()` for step-level, and aggregate to `record_workflow_execution()` when a workflow completes).
2. Use the same project root / config so paths align (`.tapps-agents/analytics/` under project root).
3. Dual-write is best-effort: if analytics recording fails, execution metrics recording still succeeds (no blocking).
4. Document the dual-write in CONFIGURATION.md or health/analytics docs.

---

## Implementation Notes

- **Locations to add dual-write:** Search for `record_execution(` and ensure the same call site (or a shared helper) also invokes analytics recording with the same workflow_id, agent/skill, success, duration, etc.
- **Mapping:** Map execution metric fields (skill, command, workflow_id, success, duration_ms) to analytics schema (agent_id, workflow_id, success, duration, etc.).
- **Config:** Optional flag to disable analytics write (e.g. `analytics.record_from_execution: true`) for projects that want metrics only.

---

## References

- Execution metrics: `tapps_agents/workflow/execution_metrics.py` (`ExecutionMetricsCollector`)
- Analytics: `tapps_agents/core/analytics_dashboard.py` (`AnalyticsCollector`, `AnalyticsDashboard`)
- Health overview usage fallback: `tapps_agents/cli/commands/health.py` (execution-metrics fallback when analytics empty)
- HEALTH_METRICS_REVIEW_2026-01-30.md (Recommendation 3.2)
