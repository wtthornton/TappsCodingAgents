# Health Metrics Review – Improvements for Heavy Usage (Past 3 Days)

**Date:** 2026-01-30  
**Context:** TappsCodingAgents repo; heavy use of tapps-agents and simple-mode in the past 3 days.  
**Current overview (post-implementation):** Overall **DEGRADED (86.2/100)**; usage now shows top agents/workflows from execution metrics; outcomes show derived-from-execution-metrics when no review artifacts.

**Verified with tapps-agents:** This document was double-checked using:
- `tapps-agents health overview --format text`
- `tapps-agents health check --format json`
- `tapps-agents reviewer review` and `tapps-agents reviewer score` on changed files (see below).  
Verification run: 2026-01-30 (and again post-implementation).

---

## What is complete

| # | Recommendation | Status | Verified with tapps-agents |
|---|----------------|--------|----------------------------|
| **3.1** | Use execution metrics for "usage" when analytics empty | **Complete** | `health overview` shows "Top agents (30d): reviewer: 1 runs (100% ok)", "Top workflows (30d): w: 1 (100% ok)" |
| **3.2** | Dual-write to analytics when recording executions | **Not done** | — |
| **3.3** | Outcomes fallback to execution metrics (review steps, gate_pass) | **Complete** | `health check` outcomes: status "degraded", score 75, message "Outcomes derived from execution metrics: 1 review steps, 100% passed gate" |
| **3.4** | Overall status degraded when score ≥75 and only non-critical unhealthy | **Complete** | `health overview` shows **DEGRADED (86.2/100)** instead of UNHEALTHY |
| **3.5** | KB / Context7 thresholds and messaging | **Not done** | — |

**Implementation details (complete items):**
- **3.1:** `_usage_data_from_execution_metrics(project_root)` in `tapps_agents/cli/commands/health.py`; used in `handle_health_overview_command` when analytics has no runs.
- **3.3:** Fallback in `OutcomeHealthCheck.run()` in `tapps_agents/health/checks/outcomes.py`; uses `ExecutionMetricsCollector`, filters review steps, returns degraded with gate_pass rate.
- **3.4:** Logic in `get_overall_health()` in `tapps_agents/health/orchestrator.py`; critical checks = environment, execution; non-critical = outcomes, knowledge_base, context7_cache.

**Review with tapps-agents (2026-01-30):**
- **Reviewer review:** `tapps-agents reviewer review tapps_agents/cli/commands/health.py tapps_agents/health/checks/outcomes.py tapps_agents/health/orchestrator.py --format text` → **3/3 files successful**.
- **Reviewer score:** `tapps-agents reviewer score` on the same three files → **3/3 successful**.
- **Health overview:** `tapps-agents health overview --format text` → Overall DEGRADED (86.2/100); usage shows top agents/workflows from execution metrics; outcomes show "derived from execution metrics."

---

## 1. Executive Summary

Health overview and usage are driven by **two separate data pipelines** that are not aligned. Execution (workflow/step) data is written to `.tapps-agents/metrics/` and used by the execution health check; the **usage** section in health overview reads from `.tapps-agents/analytics/`, which is **not** populated by current workflow/simple-mode execution. So heavy use does not show up in “usage,” and outcomes look like “no data” even when workflows and reviews have run.

Recommended improvements: **unify usage** (derive from execution metrics when analytics is empty), **optionally dual-write** to analytics when recording executions, **outcomes fallback** to execution metrics (e.g. review step + gate_pass), and **tune overall status** so a high weighted score (e.g. 83) with only non-critical checks failing can be “degraded” instead of “unhealthy.”

---

## 2. Current State

### 2.1 Two Data Pipelines

| Pipeline | Location | Written by | Read by |
|----------|----------|------------|---------|
| **Execution metrics** | `.tapps-agents/metrics/executions_*.jsonl` | `ExecutionMetricsCollector.record_execution()` | Execution health check, (not health overview usage) |
| **Analytics** | `.tapps-agents/analytics/history/` | `AnalyticsCollector.record_agent_execution()` / `record_workflow_execution()` | Health overview “usage,” outcomes (via `CursorAnalyticsAccessor` → `AnalyticsDashboard`) |

Workflow/simple-mode execution records steps via **ExecutionMetricsCollector** (e.g. in workflow executor or step handlers). **AnalyticsCollector** is only populated if something explicitly calls `record_agent_execution` / `record_workflow_execution`. That is not currently done in the main execution path.

**Verified state:** On this repo, `.tapps-agents/metrics/` contains only `executions_2026-01-20.jsonl` (1 record). The `.tapps-agents/analytics/` directory does not exist—so usage is always empty. Thus:

- **Execution check:** Healthy (100%) using the single execution in metrics (1/1 success).
- **Usage in overview:** Always shows 0 completed/failed today and no top agents/workflows because analytics is never written.
- **Implication:** Either execution recording happens only in specific code paths (e.g. CLI workflow steps), or simple-mode/Cursor-driven runs do not call `record_execution`; either way, unifying usage with execution metrics would help once more executions are recorded.

### 2.2 Outcomes Check

Outcomes use:

1. `CursorAnalyticsAccessor.get_dashboard_data()` (agents/workflows from analytics), and  
2. Review artifacts: `.tapps-agents/reports/**/review_*.json`.

If neither has data, the check correctly reports “No outcome data available” and scores low (50). **Verified:** `tapps-agents health check --format json` shows `outcomes.details.review_artifacts_count: 0`, `reports_dir: .tapps-agents/reports`. That is accurate for “outcome trends” but discouraging when the user has actually run many workflows and reviews; execution metrics do contain step-level success and `gate_pass` for review steps.

### 2.3 Overall Status Logic

In `HealthOrchestrator.get_overall_health()`:

- **Overall status = unhealthy** if **any** check has `status == "unhealthy"`.
- Weighted score (83.1) is not used for status; only per-check status counts.

So a single “unhealthy” check (e.g. outcomes, knowledge_base, context7_cache) forces overall to “unhealthy” even when environment and execution are healthy and the numeric score is high.

---

## 3. Recommendations

### 3.1 Use Execution Metrics for “Usage” When Analytics Is Empty (High impact)

**Problem:** Health overview “usage” only reads from Analytics (`.tapps-agents/analytics/`). After heavy use, usage still shows 0 workflows and no agents.

**Change:** In the health overview handler (or a small helper), when building “usage”:

1. Try existing Analytics dashboard data (agents/workflows, system).
2. If there are no (or negligible) workflow/agent counts, **aggregate from execution metrics**:
   - Read `.tapps-agents/metrics/executions_*.jsonl` (e.g. last 1 day for “today”, last 30 days for “top”).
   - Derive “completed today” / “failed today” from step-level status (by workflow_id or date).
   - Derive “top agents” from `skill` (or command) and “top workflows” from `workflow_id`.

**Result:** Overview reflects real usage (simple-mode and workflows) even when analytics was never written.

**Where:** `handle_health_overview_command` in `tapps_agents/cli/commands/health.py`, or a shared “usage data provider” that prefers analytics and falls back to execution metrics.

### 3.2 Optional: Dual-Write to Analytics When Recording Executions (Medium impact)

**Problem:** Analytics is the “official” source for usage dashboard and trends but is never populated by current execution path.

**Change:** Wherever `ExecutionMetricsCollector.record_execution()` is called (workflow executor / step runner), also call `AnalyticsCollector.record_agent_execution()` (and, if applicable, aggregate to `record_workflow_execution()` when a workflow completes). Use the same project root / config so paths align (e.g. `.tapps-agents/analytics/` under project root).

**Result:** Long-term, analytics and execution metrics stay in sync; health usage and outcomes have real data without relying on fallback.

### 3.3 Outcomes: Fallback to Execution Metrics When No Review Artifacts / Analytics (Medium impact)

**Problem:** Outcomes show “No outcome data” and low score even when many review steps have run (and `gate_pass` is in execution metrics).

**Change:** In `OutcomeHealthCheck.run()`:

1. Keep current logic using review_*.json and analytics dashboard.
2. If no (or very few) review artifacts and no workflow/agent data in analytics, **fallback to execution metrics**:
   - Filter metrics for `command == "review"` (or skill reviewer) and last 7/30 days.
   - Compute “success rate” and “gate_pass rate” from execution metrics.
   - Return a result like “Outcomes derived from execution metrics: N review steps, Y% passed gate” with a moderate score (e.g. 60–70) instead of 50 and “No outcome data.”

**Result:** After heavy use, outcomes reflect real review activity instead of a flat “no data.”

### 3.4 Overall Status: Consider Weighted Score and “Degraded” (Low/medium impact)

**Problem:** Overall is “unhealthy” even when weighted score is 83.1 and only non-critical checks (outcomes, knowledge_base, context7_cache) are unhealthy.

**Change:** In `get_overall_health()`:

- If weighted overall score >= e.g. 75 **and** all **critical** checks (environment, execution) are healthy or degraded (not unhealthy), set overall status to **“degraded”** instead of “unhealthy” when the only unhealthy checks are non-critical (e.g. outcomes, knowledge_base, context7_cache).
- Optionally: if the only “unhealthy” is outcomes and it’s due to “no data” (and execution check shows recent activity), treat outcomes as “degraded” or “unknown” so overall can be degraded rather than unhealthy.

**Result:** Heavy users with good environment and execution see “degraded” + 83 instead of “unhealthy” + 83, which better matches experience.

### 3.5 Knowledge Base and Context7 Messaging (Low impact)

**Verified from `tapps-agents health check --format json`:**

- **Knowledge base (55):** Details: `total_files: 2`, `total_domains: 1`, `recent_files_7d: 0`, `backend_type: "simple"`, `vector_index_exists: false`. Issues: “Very few KB files: 2”, “No recent KB activity (last 7 days)”, “Using simple keyword search (vector RAG not available)”. Remediation: “Consider running knowledge ingestion”, “Install FAISS for semantic search: pip install faiss-cpu”. Consider adding a short message that “2 files, 1 domain” is acceptable for minimal setup and that score improves with more domains/content or link to `tapps-agents knowledge ingest`.
- **Context7 (65):** Details: hit rate 77.0%, avg response 176 ms, entries 141. Issues: “Low hit rate: 77.0% (target: ≥95%)”, “Slow response time: 176.0ms (target: <150ms)”, “Cache size is zero”. Remediation: “Pre-populate cache: python scripts/prepopulate_context7_cache.py”. Consider documenting that 77% is acceptable for many setups, or relax thresholds so 77% is “degraded” rather than “unhealthy” if intended.

---

## 4. Implementation Priority

| Priority | Item | Effort | Impact | Done |
|----------|------|--------|--------|------|
| 1 | Use execution metrics for usage in health overview when analytics empty | Small | High – usage reflects real use | **Yes** |
| 2 | Outcomes fallback to execution metrics (review steps, gate_pass) | Small | Medium – outcomes reflect real activity | **Yes** |
| 3 | Overall status: degraded when score ≥75 and only non-critical unhealthy | Small | Medium – less alarming for heavy users | **Yes** |
| 4 | Dual-write to analytics when recording executions | Medium | Medium – long-term consistency | No |
| 5 | KB / Context7 thresholds and messaging | Small | Low – clearer expectations | No |

---

## 5. Health Metrics Included (Per Feedback Guideline)

**Pre-implementation (original):** Overall UNHEALTHY (83.1/100); usage empty; outcomes "No outcome data available".

**Post-implementation (verified with tapps-agents 2026-01-30):**

```
========================================================================
  TAPPS-AGENTS  |  HEALTH + USAGE  |  1000-FOOT VIEW
========================================================================

  [WARN]  Overall: DEGRADED  (86.2/100)

  SUBSYSTEMS (health)
  ----------------------------------------------------------------------
  [OK]   AUTOMATION: 100.0/100  |  Automation checks: 4 healthy
  [FAIL] CONTEXT7 CACHE: 65.0/100  |  Hit rate: 77.0% | Response time: 176ms | Entries: 141
  [WARN] ENVIRONMENT: 97.3/100  |  Environment check: 2 warning(s), 35 check(s) passed
  [OK]   EXECUTION: 100.0/100  |  Success rate: 100.0% (1/1 workflows) | Median duration: 10ms
  [FAIL] KNOWLEDGE BASE: 55.0/100  |  Files: 2 | Domains: 1 | Backend: simple
  [WARN] OUTCOMES: 75.0/100  |  Outcomes derived from execution metrics: 1 review steps, 100% passed gate

  USAGE (agents & workflows)
  ----------------------------------------------------------------------
  Today: completed 0 workflows, failed 0  |  active: 0
  Avg workflow duration: 0.0s  |  CPU: 33%  Mem: 70%  Disk: 54%
  Top agents (30d): reviewer: 1 runs (100% ok)
  Top workflows (30d): w: 1 (100% ok)
========================================================================
```

**Health check summary (from `tapps-agents health check --format json`):** checks_run: 6, healthy: 2 (automation, execution), degraded: 2 (environment, outcomes), unhealthy: 2 (context7_cache, knowledge_base). Outcomes: `status: "degraded"`, `score: 75`, `message: "Outcomes derived from execution metrics: 1 review steps, 100% passed gate"`, `review_steps_from_execution_metrics: 1`, `gate_pass_rate: 100`, `success_rate: 100`.

**Code review:** Changed files (`health.py`, `outcomes.py`, `orchestrator.py`) were reviewed with `tapps-agents reviewer review` and `tapps-agents reviewer score`; all 3/3 passed (2026-01-30).

---

## 6. References

- Execution metrics: `tapps_agents/workflow/execution_metrics.py` (`ExecutionMetricsCollector`)
- Analytics: `tapps_agents/core/analytics_dashboard.py` (`AnalyticsCollector`, `AnalyticsDashboard`)
- Health overview usage: `tapps_agents/cli/commands/health.py` (`handle_health_overview_command`)
- Outcomes check: `tapps_agents/health/checks/outcomes.py` (uses `CursorAnalyticsAccessor` + `.tapps-agents/reports/**/review_*.json`)
- Overall health: `tapps_agents/health/orchestrator.py` (`get_overall_health`)
- Verification commands: `tapps-agents health overview --format text`, `tapps-agents health check --format json`
