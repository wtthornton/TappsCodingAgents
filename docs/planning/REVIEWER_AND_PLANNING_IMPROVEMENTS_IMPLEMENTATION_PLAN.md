# Reviewer and Planning Improvements: Executable Implementation Plan

**Status:** Draft  
**Created:** 2026-02-07  
**Updated:** 2026-02-07 (synced from PRD via tapps-agents planner + reviewer)  
**Source:** [REVIEWER_AGENT_IMPROVEMENT_PRD.md](REVIEWER_AGENT_IMPROVEMENT_PRD.md) and design discussion  
**Review:** Run `tapps-agents reviewer review docs/planning/REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md` to validate.

---

## Purpose

This document is the **executable checklist** for implementing:
1. **Reviewer improvements:** Expert selection metrics, dashboard visibility, HistoryLogger wiring
2. **Planning doc review:** Markdown/planning doc scorer, Epic evaluator, implementation plan checks

Each task is actionable, with clear file paths and acceptance criteria.

## Scope

- **In scope:** Phases 1–6 as defined below
- **Out of scope:** Changing core scoring thresholds; adding new expert domains; dedicated planning-review agent

## Audience

- Implementers (developers executing the plan)
- Reviewers (tapps-agents reviewer and human review)
- Future maintainers

## How to use this plan

1. Execute **phases in order** (Phase 1 → 6). Do not skip phases.
2. Within each phase, complete tasks in the order listed. Check off each `- [ ]` when done.
3. Run **Phase N done** verification before moving to the next phase.
4. When a phase is complete, add at the end: `**Completed:** YYYY-MM-DD` (optional).

## Key files reference

| Purpose | Path |
|---------|------|
| Expert registry | `tapps_agents/experts/expert_registry.py` |
| Confidence metrics | `tapps_agents/experts/confidence_metrics.py` |
| Performance tracker | `tapps_agents/experts/performance_tracker.py` |
| History logger | `tapps_agents/experts/history_logger.py` |
| Dashboard collector | `tapps_agents/dashboard/data_collector.py` |
| Dashboard renderer | `tapps_agents/dashboard/html_renderer.py` |
| Reviewer agent | `tapps_agents/agents/reviewer/agent.py` |
| Scorer registry | `tapps_agents/agents/reviewer/scorer_registry.py` |
| Base scorer | `tapps_agents/agents/reviewer/scoring.py` |
| Planner agent | `tapps_agents/agents/planner/agent.py` |
| Story evaluator | `tapps_agents/core/story_evaluator.py` |
| Config | `tapps_agents/core/config.py` |

---

## Decisions (from PRD)

| Topic | Decision |
|-------|----------|
| **Backward compatibility** | Legacy `confidence_metrics.json` records without `expert_ids` or `selection_reason`: use `expert_ids=[]` and `selection_reason="unknown"` on load. No migration required. |
| **Dashboard fallback alert** | Threshold = 30% (combined fallback_builtin + fallback_all of total consultations). |
| **Recent consultations** | Dashboard shows last 20 records (by timestamp). |

---

## Table of contents

1. [Phase 1: Expert selection metrics](#phase-1-expert-selection-metrics)
2. [Phase 2: Dashboard enhancements for expert selection](#phase-2-dashboard-enhancements-for-expert-selection)
3. [Phase 3: Markdown/planning doc scorer](#phase-3-markdownplanning-doc-scorer)
4. [Phase 4: Epic evaluator](#phase-4-epic-evaluator)
5. [Phase 5: Implementation plan checks](#phase-5-implementation-plan-checks)
6. [Phase 6: HistoryLogger wiring (optional)](#phase-6-historylogger-wiring-optional)
7. [Completion checklist](#completion-checklist)

---

## Phase 1: Expert selection metrics

**Goal:** Record which experts were consulted and why (weight_matrix | domain_match | fallback) for every consultation.

**Definition of done:** `ExpertRegistry.consult()` sets `selection_reason`; `ConfidenceMetricsTracker.record()` and `ExpertPerformanceTracker.track_consultation()` accept and persist `expert_ids` and `selection_reason`; existing data loads without error (backward compatible).

### 1.1 Add selection reason in ExpertRegistry

- [ ] **1.1.1** In `tapps_agents/experts/expert_registry.py`, inside `consult()`: after the block that populates `expert_ids_to_consult` (lines ~316–367), add a variable `selection_reason: str` set based on which branch ran:
  - If `self.weight_matrix and not prioritize_builtin`: `selection_reason = "weight_matrix"`
  - If `_get_experts_for_domain(..., prioritize_builtin=True)` and `is_technical_domain`: `selection_reason = "domain_match_builtin"`
  - If `_get_experts_for_domain(..., prioritize_builtin=False)` and not technical: `selection_reason = "domain_match_customer"`
  - If fallback to `list(self.builtin_experts.keys())`: `selection_reason = "fallback_builtin"`
  - If fallback to customer+builtin: `selection_reason = "fallback_all"`
  - **Acceptance:** Every code path that sets `expert_ids_to_consult` also sets `selection_reason`.

- [ ] **1.1.2** Pass `expert_ids_to_consult` and `selection_reason` into the `tracker.record()` call and into `ExpertPerformanceTracker.track_consultation()` (per-expert loop). For the per-expert loop, pass the same `selection_reason` for each expert.
  - **Acceptance:** Both tracking calls receive the new fields.

### 1.2 Extend ConfidenceMetricsTracker

- [ ] **1.2.1** In `tapps_agents/experts/confidence_metrics.py`, add to `ConfidenceMetric` dataclass: `expert_ids: list[str] = field(default_factory=list)`, `selection_reason: str = "unknown"`.
  - **Acceptance:** `ConfidenceMetric` has the new fields with defaults.

- [ ] **1.2.2** Update `record()` signature to accept `expert_ids: list[str] | None = None`, `selection_reason: str = "unknown"`. Set them on the `ConfidenceMetric` instance.
  - **Acceptance:** `record()` persists the new fields.

- [ ] **1.2.3** In `_load_metrics()` and `_save_metrics()`, handle `expert_ids` and `selection_reason`; for legacy records without these keys, use `[]` and `"unknown"`.
  - **Acceptance:** Existing `confidence_metrics.json` loads without error; new records include the fields.

### 1.3 Extend ExpertPerformanceTracker

- [ ] **1.3.1** In `tapps_agents/experts/performance_tracker.py`, add optional params to `track_consultation()`: `expert_ids: list[str] | None = None`, `selection_reason: str | None = None`. Include them in `consultation_data` dict if provided.
  - **Acceptance:** `track_consultation()` writes the new fields to JSONL when provided.

### Phase 1 verification

- [ ] Run: `pytest tests/unit/experts/ -v -k "confidence or performance"` (if such tests exist); otherwise run a manual consultation and inspect `confidence_metrics.json` and `expert_performance.jsonl` for new fields.

---

## Phase 2: Dashboard enhancements for expert selection

**Goal:** Surface expert selection metrics in the Performance Insight Dashboard.

**Definition of done:** Experts tab shows selection reason distribution and recent consultations with domain → expert_ids → selection_reason; recommendations alert when fallback rate is high.

### 2.1 Extend DashboardDataCollector

- [ ] **2.1.1** In `tapps_agents/dashboard/data_collector.py`, in `collect_experts()`: read `confidence_metrics.json` (or the ConfidenceMetricsTracker); aggregate `selection_reason` counts; build a list of last 20 consultations (per PRD Decisions) with `timestamp`, `agent_id`, `domain`, `expert_ids`, `selection_reason`.
  - **Acceptance:** `collect_experts()` returns `selection_reason_distribution: dict[str, int]` and `recent_consultations: list[dict]`.

- [ ] **2.1.2** Include the new data in the returned dict under keys `selection_reason_distribution` and `recent_consultations`.
  - **Acceptance:** `collect_all()` payload includes these under `experts`.

### 2.2 Extend Dashboard HTML renderer

- [ ] **2.2.1** In `tapps_agents/dashboard/html_renderer.py`, in `_render_experts_tab()`: add a section "Selection Reason Distribution" showing counts for `weight_matrix`, `domain_match_builtin`, `domain_match_customer`, `fallback_builtin`, `fallback_all` (bar chart or table).
  - **Acceptance:** Dashboard experts tab displays the distribution.

- [ ] **2.2.2** Add a "Recent Consultations" table with columns: Timestamp, Agent, Domain, Experts, Selection Reason. Use `recent_consultations` from data.
  - **Acceptance:** Table renders with up to 20 recent consultations.

### 2.3 Recommendations

- [ ] **2.3.1** In `tapps_agents/dashboard/generator.py`, add a recommendation when `fallback_builtin` + `fallback_all` count > 30% of total consultations: "High fallback rate in expert selection. Check domain config and weight matrix."
  - **Acceptance:** Recommendation appears when threshold exceeded.

### Phase 2 verification

- [ ] Run `tapps-agents dashboard --no-open`; open the generated HTML; verify Experts tab shows selection distribution and recent consultations.

---

## Phase 3: Markdown/planning doc scorer

**Goal:** Provide structured scoring for PRDs, implementation plans, epics, and stories (markdown planning docs) instead of generic fallback scores.

**Definition of done:** `MarkdownPlanningScorer` exists, is registered for `Language.MARKDOWN`, and produces structure/completeness/traceability scores; reviewer uses it for `.md` files.

### 3.1 Create MarkdownPlanningScorer

- [ ] **3.1.1** Create file `tapps_agents/agents/reviewer/markdown_planning_scorer.py`. Implement a class `MarkdownPlanningScorer(BaseScorer)` with:
  - `score_file(self, file_path: Path, code: str) -> dict[str, Any]`
  - Scoring categories (normalized 0–10 or 0–100): `structure_score` (has Purpose, Scope, Goals, phases), `completeness_score` (few TBD/placeholder), `traceability_score` (links between requirements/stories/phases), `format_score` (headings, lists, tables)
  - Return dict with keys: `overall_score`, `structure_score`, `completeness_score`, `traceability_score`, `format_score`, `metrics` (e.g. issues found)
  - **Acceptance:** Scorer runs on a sample PRD/plan markdown and returns non-zero scores.

- [ ] **3.1.2** Use regex/simple parsing for: `## Purpose`, `## Scope`, `## Goals`, `## Phase`, `- [ ]`, `TBD`, `TODO`, link patterns `[text](path)`.
  - **Acceptance:** Structure and completeness detection works on typical planning docs.

### 3.2 Register Markdown scorer

- [ ] **3.2.1** In `tapps_agents/agents/reviewer/scorer_registry.py`, in `_register_builtin_scorers()`: add registration for `Language.MARKDOWN` with `MarkdownPlanningScorer`.
  - **Acceptance:** `ScorerRegistry.get_scorer(Language.MARKDOWN, config)` returns a `MarkdownPlanningScorer` instance.

- [ ] **3.2.2** In `_instantiate_scorer()`, add a branch for `Language.MARKDOWN` that instantiates `MarkdownPlanningScorer()` (no special config needed initially).
  - **Acceptance:** Instantiation succeeds.

### 3.3 Wire reviewer for markdown

- [ ] **3.3.1** In `tapps_agents/agents/reviewer/agent.py`, the flow at ~1004–1023 already uses `ScorerFactory.get_scorer(language, self.config)`. Ensure `Language.MARKDOWN` is detected for `.md` files and that no special-case bypass exists for markdown.
  - **Acceptance:** Reviewing a `.md` file uses `MarkdownPlanningScorer` and returns structure/completeness/traceability scores.

### Phase 3 verification

- [ ] Run `tapps-agents reviewer review docs/planning/REVIEWER_AGENT_IMPROVEMENT_PRD.md`; assert scores include `structure_score`, `completeness_score`, and that `overall_score` is not the generic 50.0 fallback.

---

## Phase 4: Epic evaluator

**Goal:** Extend the Planner to evaluate Epic documents (structure, story breakdown, dependencies).

**Definition of done:** Planner has `*evaluate-epic` (or similar) command; EpicEvaluator evaluates epic structure and story breakdown; results are usable for quality feedback.

### 4.1 Create EpicEvaluator

- [ ] **4.1.1** Create file `tapps_agents/core/epic_evaluator.py`. Implement `EpicEvaluator` with:
  - `evaluate(epic_content: str | Path) -> EpicQualityScore` (or dict)
  - Criteria: has overview, has story list or phase breakdown, has dependencies or ordering, stories have acceptance criteria
  - Return structure similar to `StoryQualityScore`: `overview_score`, `story_breakdown_score`, `dependency_score`, `overall`, `issues`, `recommendations`
  - **Acceptance:** Evaluating a sample epic markdown returns structured scores.

### 4.2 Add Planner command

- [ ] **4.2.1** In `tapps_agents/agents/planner/agent.py`, add command `*evaluate-epic` that accepts a file path or epic content. Call `EpicEvaluator.evaluate()` and return results in markdown/JSON.
  - **Acceptance:** `@planner *evaluate-epic docs/prd/epic-51.md` returns epic quality scores.

### 4.3 Register in Planner skill/CLI

- [ ] **4.3.1** Add `*evaluate-epic` to the planner skill `.claude/skills/planner/SKILL.md` and to planner CLI if applicable.
  - **Acceptance:** Command is discoverable and documented.

### Phase 4 verification

- [ ] Run `tapps-agents planner evaluate-epic docs/planning/REVIEWER_AGENT_IMPROVEMENT_PRD.md` (or an epic doc); assert structured output with scores.

---

## Phase 5: Implementation plan checks

**Goal:** Extend Planner (or reuse StoryEvaluator) to check implementation plans for phases, tasks, and completion criteria.

**Definition of done:** Planner can evaluate implementation plans (phases defined, tasks with acceptance criteria, clear completion criteria).

### 5.1 Implementation plan evaluator

- [ ] **5.1.1** Create `tapps_agents/core/implementation_plan_evaluator.py` or extend `EpicEvaluator` with `evaluate_implementation_plan()`. Criteria: phases/sections present, tasks have checkboxes or acceptance criteria, completion checklist exists.
  - **Acceptance:** Evaluating a sample implementation plan returns scores.

### 5.2 Add Planner command

- [ ] **5.2.1** Add `*evaluate-implementation-plan` (or `*evaluate-plan`) to planner. Accept file path. Return structured evaluation.
  - **Acceptance:** Command works on `docs/planning/LLM_AGENT_SETUP_IMPLEMENTATION_PLAN.md` or similar.

### Phase 5 verification

- [ ] Run evaluation on an implementation plan; assert output includes phase/task/completion scores.

---

## Phase 6: HistoryLogger wiring (optional)

**Goal:** Use existing HistoryLogger for per-consultation "why" logging when enabled via config.

**Definition of done:** Config flag `expert_system.history_logging` exists; when true, `ExpertRegistry.consult()` calls `HistoryLogger.log_consultation()` with reasoning.

### 6.1 Config

- [ ] **6.1.1** In `tapps_agents/core/config.py` (or expert config), add `history_logging: bool = False` under expert system config.
  - **Acceptance:** Config loads without error; default is False.

### 6.2 Wire HistoryLogger

- [ ] **6.2.0** In `tapps_agents/experts/history_logger.py`, add `encoding="utf-8"` to `open()` in `_append_entry()` for Windows compatibility (existing code omits this).
  - **Acceptance:** File writes use UTF-8 encoding.

- [ ] **6.2.1** In `tapps_agents/experts/expert_registry.py`, after a successful consultation: if config has `history_logging=True`, call `HistoryLogger.log_consultation(expert_id=..., domain=..., consulted=True, confidence=..., reasoning=selection_reason)` for each expert (or once per consultation with primary expert).
  - **Acceptance:** When enabled, `.tapps-agents/expert-history.jsonl` receives entries with `reasoning` set.

### Phase 6 verification

- [ ] Set `expert_system.history_logging: true` in config; run a reviewer review; assert expert-history.jsonl has new entries with reasoning.

---

## Completion checklist

- [ ] All phases 1–6 executed and verified.
- [ ] Unit tests added/updated for new components (MarkdownPlanningScorer, EpicEvaluator, config).
- [ ] Documentation updated: command-reference.mdc, planner skill, REVIEWER_AGENT_IMPROVEMENT_PRD.md (mark items implemented).
- [ ] CHANGELOG.md updated with new features.
- [ ] Run full test suite: `pytest tests/ -v --ignore=tests/e2e/` (or equivalent).

---

## References

- [REVIEWER_AGENT_IMPROVEMENT_PRD.md](REVIEWER_AGENT_IMPROVEMENT_PRD.md)
- [EPIC-53-REVIEWER-AND-PLANNING-IMPROVEMENTS.md](EPIC-53-REVIEWER-AND-PLANNING-IMPROVEMENTS.md) — **Epic and user stories** (created from this plan)
- [LLM_AGENT_SETUP_IMPLEMENTATION_PLAN.md](LLM_AGENT_SETUP_IMPLEMENTATION_PLAN.md) (format reference)
- `tapps_agents/core/story_evaluator.py` (pattern for EpicEvaluator)
- `tapps_agents/agents/reviewer/scoring.py` (BaseScorer interface)
