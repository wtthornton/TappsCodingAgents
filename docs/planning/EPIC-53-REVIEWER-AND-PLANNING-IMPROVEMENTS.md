# EPIC-53: Reviewer and Planning Improvements

**Epic ID:** EPIC-53  
**Status:** Completed  
**Priority:** High  
**Source:** [REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md](REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md)  
**Created:** 2026-02-07

---

## Epic Overview

### Goal

Implement reviewer improvements (expert selection metrics, dashboard visibility, HistoryLogger) and planning-doc review capabilities (Markdown/planning scorer, Epic evaluator, implementation plan checks).

### Problem Statement

**Current State:**
- Expert consultations do not record which experts were selected or why (weight_matrix vs domain_match vs fallback).
- Dashboard does not surface expert selection metrics or fallback-rate alerts.
- Reviewer uses generic fallback scoring for `.md` files instead of structure/completeness/traceability.
- No structured evaluation for Epic documents or implementation plans.

**Desired State:**
- Every consultation records `expert_ids` and `selection_reason`; backward-compatible with existing data.
- Dashboard Experts tab shows selection reason distribution, recent consultations, and high-fallback alert.
- Markdown planning docs (PRDs, plans, epics) get structure/completeness/traceability scores.
- Planner can evaluate Epics and implementation plans for quality feedback.

### Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Expert selection visibility | None | Dashboard shows distribution + recent 20 |
| Fallback alert | None | Recommendation when fallback > 30% |
| Markdown review | Generic 50 fallback | Structure/completeness/traceability scores |
| Epic evaluation | None | Planner *evaluate-epic returns scores |
| Implementation plan evaluation | None | Planner *evaluate-plan returns scores |

### Scope

- **In scope:** Phases 1–6 of the implementation plan.
- **Out of scope:** Changing core scoring thresholds; new expert domains; dedicated planning-review agent.

---

## Epic Stories

### Story Summary

| ID | Story | Points | Phase | Dependencies | Status |
|----|-------|--------|-------|--------------|--------|
| RP-001 | Expert selection metrics | 5 | Phase 1 | — | Done |
| RP-002 | Dashboard enhancements for expert selection | 5 | Phase 2 | RP-001 | Done |
| RP-003 | Markdown/planning doc scorer | 8 | Phase 3 | — | Done |
| RP-004 | Epic evaluator | 8 | Phase 4 | — | Done |
| RP-005 | Implementation plan checks | 5 | Phase 5 | RP-004 | Done |
| RP-006 | HistoryLogger wiring (optional) | 3 | Phase 6 | RP-001 | Done |

**Total Story Points:** 34  
**Estimated Duration:** 5–6 weeks

---

## Phase 1: Expert selection metrics

**Goal:** Record which experts were consulted and why for every consultation.

### RP-001: Expert selection metrics (5 points)

**User Story:**
> As a framework maintainer, I want every expert consultation to record expert_ids and selection_reason (weight_matrix | domain_match | fallback), so that we can measure selection quality and reduce fallback usage.

**Acceptance Criteria:**
1. In `expert_registry.py` `consult()`, set `selection_reason` on every code path that sets `expert_ids_to_consult`: `weight_matrix`, `domain_match_builtin`, `domain_match_customer`, `fallback_builtin`, `fallback_all`.
2. Pass `expert_ids` and `selection_reason` into `ConfidenceMetricsTracker.record()` and `ExpertPerformanceTracker.track_consultation()`.
3. `ConfidenceMetric` dataclass has `expert_ids: list[str]` and `selection_reason: str` with defaults; `record()` accepts and persists them.
4. `_load_metrics()` / `_save_metrics()` handle legacy records without these keys as `[]` and `"unknown"`.
5. `ExpertPerformanceTracker.track_consultation()` accepts optional `expert_ids` and `selection_reason` and writes them to JSONL.
6. Existing `confidence_metrics.json` loads without error (backward compatible).

**Tasks:**
- [x] 1.1 Add `selection_reason` in ExpertRegistry.consult() for all branches; pass to tracker.record() and track_consultation().
- [x] 1.2 Extend ConfidenceMetricsTracker: ConfidenceMetric fields, record() signature, load/save legacy handling.
- [x] 1.3 Extend ExpertPerformanceTracker: track_consultation() optional params and JSONL output.
- [x] 1.4 Verification: pytest or manual check of confidence_metrics.json and expert_performance.jsonl for new fields.

**Files:** `tapps_agents/experts/expert_registry.py`, `confidence_metrics.py`, `performance_tracker.py`

**Dependencies:** None

---

## Phase 2: Dashboard enhancements for expert selection

**Goal:** Surface expert selection metrics in the Performance Insight Dashboard.

### RP-002: Dashboard enhancements for expert selection (5 points)

**User Story:**
> As a user, I want the dashboard Experts tab to show selection reason distribution and recent consultations, and to alert when fallback rate is high, so that I can tune domain config and weight matrix.

**Acceptance Criteria:**
1. `DashboardDataCollector.collect_experts()` reads confidence metrics; aggregates `selection_reason` counts; builds last 20 consultations with timestamp, agent_id, domain, expert_ids, selection_reason.
2. Collector returns `selection_reason_distribution` and `recent_consultations`; `collect_all()` includes them under `experts`.
3. `_render_experts_tab()` has "Selection Reason Distribution" (bar/table) and "Recent Consultations" table (Timestamp, Agent, Domain, Experts, Selection Reason).
4. Generator adds recommendation when (fallback_builtin + fallback_all) > 30% of total: "High fallback rate in expert selection. Check domain config and weight matrix."
5. Manual verification: `tapps-agents dashboard --no-open` shows Experts tab with distribution and table.

**Tasks:**
- [x] 2.1 Extend DashboardDataCollector.collect_experts() with aggregation and recent 20.
- [x] 2.2 Extend html_renderer _render_experts_tab() with distribution and table.
- [x] 2.3 Add fallback-rate recommendation in generator.
- [x] 2.4 Verification: run dashboard and inspect Experts tab.

**Files:** `tapps_agents/dashboard/data_collector.py`, `html_renderer.py`, `generator.py`

**Dependencies:** RP-001 (metrics must be recorded first)

---

## Phase 3: Markdown/planning doc scorer

**Goal:** Structured scoring for PRDs, implementation plans, epics (markdown planning docs).

### RP-003: Markdown/planning doc scorer (8 points)

**User Story:**
> As a reviewer user, I want .md planning docs to receive structure, completeness, and traceability scores instead of a generic fallback, so that plan quality is measurable.

**Acceptance Criteria:**
1. New file `tapps_agents/agents/reviewer/markdown_planning_scorer.py` with `MarkdownPlanningScorer(BaseScorer)`.
2. `score_file(file_path, code)` returns dict with: `overall_score`, `structure_score`, `completeness_score`, `traceability_score`, `format_score`, `metrics`.
3. Scores normalized 0–10 or 0–100; structure (Purpose, Scope, Goals, phases), completeness (few TBD/placeholder), traceability (links), format (headings, lists, tables).
4. Regex/simple parsing for `## Purpose`, `## Scope`, `## Goals`, `## Phase`, `- [ ]`, `TBD`, `TODO`, `[text](path)`.
5. Scorer registered for `Language.MARKDOWN` in scorer_registry.py; reviewer uses it for .md files (no bypass).
6. Verification: `tapps-agents reviewer review docs/planning/REVIEWER_AGENT_IMPROVEMENT_PRD.md` returns structure/completeness and overall ≠ 50.0 fallback.

**Tasks:**
- [x] 3.1 Create MarkdownPlanningScorer and implement score_file() with four score categories.
- [x] 3.2 Register in scorer_registry for Language.MARKDOWN; ensure reviewer uses it for .md.
- [x] 3.3 Verification: review a planning .md and assert scores.

**Files:** `tapps_agents/agents/reviewer/markdown_planning_scorer.py`, `scorer_registry.py`, `agent.py`

**Dependencies:** None

---

## Phase 4: Epic evaluator

**Goal:** Planner can evaluate Epic documents (structure, story breakdown, dependencies).

### RP-004: Epic evaluator (8 points)

**User Story:**
> As a planner user, I want to run *evaluate-epic on an epic document and get structure, story breakdown, and dependency scores, so that I can improve epic quality before execution.

**Acceptance Criteria:**
1. New file `tapps_agents/core/epic_evaluator.py` with `EpicEvaluator`.
2. `evaluate(epic_content: str | Path)` returns structure similar to StoryQualityScore: overview_score, story_breakdown_score, dependency_score, overall, issues, recommendations.
3. Criteria: has overview, has story list or phase breakdown, has dependencies or ordering, stories have acceptance criteria.
4. Planner command `*evaluate-epic` accepts file path or content; calls EpicEvaluator.evaluate(); returns markdown/JSON.
5. Command documented in planner skill and CLI.
6. Verification: `tapps-agents planner evaluate-epic docs/planning/REVIEWER_AGENT_IMPROVEMENT_PRD.md` (or epic) returns structured scores.

**Tasks:**
- [x] 4.1 Create EpicEvaluator and evaluate() with overview, story_breakdown, dependency, issues, recommendations.
- [x] 4.2 Add *evaluate-epic to planner agent and wire to EpicEvaluator.
- [x] 4.3 Register in planner skill and CLI.
- [x] 4.4 Verification: run evaluate-epic on an epic doc.

**Files:** `tapps_agents/core/epic_evaluator.py`, `tapps_agents/agents/planner/agent.py`, planner SKILL.md, CLI

**Dependencies:** None

---

## Phase 5: Implementation plan checks

**Goal:** Planner can evaluate implementation plans (phases, tasks, completion criteria).

### RP-005: Implementation plan checks (5 points)

**User Story:**
> As a planner user, I want to run *evaluate-implementation-plan (or *evaluate-plan) on an implementation plan and get phase/task/completion scores, so that plans are validated before execution.

**Acceptance Criteria:**
1. New `tapps_agents/core/implementation_plan_evaluator.py` or extend EpicEvaluator with `evaluate_implementation_plan()`. Criteria: phases/sections present, tasks have checkboxes or acceptance criteria, completion checklist exists.
2. Planner command `*evaluate-implementation-plan` (or `*evaluate-plan`) accepts file path; returns structured evaluation.
3. Verification: run on `docs/planning/LLM_AGENT_SETUP_IMPLEMENTATION_PLAN.md` or REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md; output includes phase/task/completion scores.

**Tasks:**
- [x] 5.1 Create implementation plan evaluator (new module or EpicEvaluator extension).
- [x] 5.2 Add planner command and wire to evaluator.
- [x] 5.3 Verification: run on a sample implementation plan.

**Files:** `tapps_agents/core/implementation_plan_evaluator.py` (or epic_evaluator.py), planner agent/skill/CLI

**Dependencies:** RP-004 (reuse pattern; can be developed in parallel with optional dependency)

---

## Phase 6: HistoryLogger wiring (optional)

**Goal:** Use HistoryLogger for per-consultation "why" logging when enabled via config.

### RP-006: HistoryLogger wiring (3 points, optional)

**User Story:**
> As an operator, I want optional expert history logging with reasoning (selection_reason) so that I can audit why experts were chosen when debugging.

**Acceptance Criteria:**
1. Config flag `expert_system.history_logging: bool = False` in config (or expert config).
2. In expert_registry.consult(), when history_logging=True, call HistoryLogger.log_consultation(..., reasoning=selection_reason) after successful consultation.
3. In history_logger.py, use `encoding="utf-8"` in open() in _append_entry() for Windows compatibility.
4. Verification: set history_logging true; run reviewer review; expert-history.jsonl has entries with reasoning.

**Tasks:**
- [x] 6.1 Add history_logging to config; default False.
- [x] 6.2 Add UTF-8 encoding in HistoryLogger _append_entry().
- [x] 6.3 Wire ExpertRegistry.consult() to HistoryLogger when enabled.
- [x] 6.4 Verification: enable and run consultation; check expert-history.jsonl.

**Files:** `tapps_agents/core/config.py`, `tapps_agents/experts/history_logger.py`, `expert_registry.py`

**Dependencies:** RP-001 (selection_reason available)

---

## Completion checklist

- [x] All stories RP-001–RP-006 implemented and verified.
- [x] Unit tests for MarkdownPlanningScorer, EpicEvaluator, config.
- [x] Documentation: command-reference.mdc, planner skill, PRD updated.
- [x] CHANGELOG.md updated.
- [x] Full test suite: `pytest tests/ -v --ignore=tests/e2e/`.

---

## References

- [REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md](REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md) — Executable task checklist
- [REVIEWER_AGENT_IMPROVEMENT_PRD.md](REVIEWER_AGENT_IMPROVEMENT_PRD.md) — PRD
- `tapps_agents/core/story_evaluator.py` — Pattern for EpicEvaluator
- `tapps_agents/agents/reviewer/scoring.py` — BaseScorer interface
