# Reviewer Agent Improvement PRD

**Status:** Implemented (EPIC-53)  
**Created:** 2026-02-07  
**Author:** TappsCodingAgents Team  
**Implementation plan:** [REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md](REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md)  
**Review:** Run `tapps-agents reviewer review docs/planning/REVIEWER_AGENT_IMPROVEMENT_PRD.md` for validation.

---

## Purpose

This PRD defines improvements to the TappsCodingAgents **Reviewer Agent** to increase transparency, debuggability, and effectiveness. The reviewer is a core quality gate in workflows; improvements here benefit the entire framework and adaptive learning system.

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| Expert selection metrics and observability | Changing core scoring logic or thresholds |
| Dashboard visibility for expert choices | Adding new expert definitions or domains to the registry |
| Expert selection reasoning and diagnostics | Reviewer CLI/API changes |
| Correlation of selection with outcomes for adaptive learning | Changes to other agents (implementer, tester, etc.) |
| Reviewer consulting additional *existing* domains for planning docs | |

---

## Current State

### Reviewer Agent Overview

- **Role:** Code review with 7-category scoring (complexity, security, maintainability, test_coverage, performance, structure, devex), LLM feedback, and quality gates.
- **Expert usage:** When `include_llm_feedback` is true, the reviewer consults experts for review guidance before generating feedback.
- **Domains consulted:** Hardcoded in agent code:
  - Always: `security`, `performance-optimization`, `code-quality-analysis`
  - Conditionally: `api-design-integration` (if API client pattern detected), and external API subdomain (if "external" or "third-party" in code preview).

### Expert Selection Flow

1. Reviewer calls `expert_registry.consult(query, domain, include_all=True, prioritize_builtin=True, agent_id="reviewer")` per domain.
2. `ExpertRegistry.consult()` selects experts by:
   - **Weight matrix** (if configured, `prioritize_builtin=False`): uses `ExpertWeightMatrix` for primary expert and optional full set.
   - **Domain match** (`prioritize_builtin=True`, default for reviewer): `_get_experts_for_domain()` finds experts by `primary_domain`, prioritizes built-in for technical domains.
   - **Fallback:** If no domain match, uses all built-in experts (technical) or customer+built-in (business).

### What Is Tracked Today

| Source | Data | Persisted |
|--------|------|-----------|
| `ConfidenceMetricsTracker` | agent_id, domain, confidence, threshold, agreement_level, num_experts, primary_expert, query_preview | `.tapps-agents/confidence_metrics.json` |
| `ExpertPerformanceTracker` | expert_id, domain, confidence, query, timestamp | `.tapps-agents/learning/expert_performance.jsonl` |
| Dashboard | Expert performance (consultations, avg_confidence, first_pass_rate, domains, ROI) | Rendered from above |

### What Is *Not* Tracked

- **Full list of expert IDs** consulted per call.
- **Selection reason** (weight_matrix vs domain_match vs fallback).
- **Agent → domain mapping** (e.g., "reviewer consulted security, performance, code-quality").
- **HistoryLogger** has a `reasoning` field for "why consulted or not consulted" but is **never called** anywhere in the codebase.

### Expert Sharing (Architecture)

**Experts are shared across agents.** All agents that use `ExpertSupportMixin` (Reviewer, Implementer, Tester, Architect, Designer, Ops, Enhancer) share the same `ExpertRegistry`. The reviewer leverages this shared registry—it does not have its own experts. Each agent chooses which domains to consult based on its role; the reviewer currently consults security, performance-optimization, code-quality-analysis, and api-design-integration for code. For planning docs (PRDs, epics, implementation plans), the reviewer should consult different existing domains: `documentation-knowledge-management`, `development-workflow`, `software-architecture`.

---

## Goals

1. **Transparency:** Operators and developers can see which experts were chosen for each consultation and why.
2. **Debuggability:** When confidence is low or outcomes are poor, selection path and reasoning help identify root cause.
3. **Adaptive learning:** Correlate selection path with outcomes to improve weight matrix, domain config, and expert effectiveness.
4. **Dashboard value:** Surface expert selection metrics so users can assess reviewer behavior and expert system health.

---

## Success Criteria

- [x] Every expert consultation records: expert IDs consulted, selection reason (weight_matrix | domain_match | fallback).
- [x] Dashboard experts tab shows: selection reason distribution, recent consultations with domain → experts → reason.
- [x] Low-confidence or fallback-heavy consultations can be traced and investigated.
- [x] Adaptive learning can use selection path data to adjust weights and identify expert weaknesses.

---

## Proposed Improvements

### 1. Expert Selection Metrics

**Requirement:** Record selection metadata at consultation time.

| Field | Type | Description |
|-------|------|-------------|
| `expert_ids` | `list[str]` | Full list of expert IDs consulted |
| `selection_reason` | `str` | One of: `weight_matrix`, `domain_match_builtin`, `domain_match_customer`, `fallback_builtin`, `fallback_all` |

**Implementation:** Extend `ExpertRegistry.consult()` to compute and pass `selection_reason` when calling `ConfidenceMetricsTracker.record()` and `ExpertPerformanceTracker.track_consultation()`. Add logic in the registry to set the reason based on which branch populated `expert_ids_to_consult`.

### 2. Wire HistoryLogger (Optional)

**Requirement:** Use existing `HistoryLogger` for per-consultation "why" logging when enabled.

- Add config flag: `expert_system.history_logging: bool` (default: false for backward compatibility).
- When true, call `HistoryLogger.log_consultation()` with `reasoning=selection_reason` from the registry after each consultation.
- History file: `.tapps-agents/expert-history.jsonl`.
- **Note:** When wiring, specify `encoding="utf-8"` in `HistoryLogger._append_entry()` to ensure Windows compatibility (existing code omits this).

### 3. Extend ConfidenceMetricsTracker

**Requirement:** Add `expert_ids` and `selection_reason` to `ConfidenceMetric` and `record()`.

- Update `ConfidenceMetric` dataclass.
- Update `record()` call sites in `expert_registry.py`.
- Persist in `confidence_metrics.json` (schema change). For legacy records without these keys, use `expert_ids=[]` and `selection_reason="unknown"` (see [Decisions](#decisions)).

### 4. Dashboard Enhancements

**Requirement:** Surface expert selection data in the Performance Insight Dashboard.

| Section | Additions |
|---------|-----------|
| Experts tab | Selection reason distribution (pie or bar: weight_matrix, domain_match, fallback counts) |
| Experts tab | Recent consultations table: timestamp, agent, domain, expert_ids, selection_reason (last 20 records) |
| Recommendations | Alert when fallback rate &gt; 30% (fallback_builtin + fallback_all) or when selection_reason is fallback and confidence &lt; threshold |

**Data source:** Aggregate from `confidence_metrics.json` and/or `expert_performance.jsonl`; extend `DashboardDataCollector.collect_experts()` to include selection metrics.

### 5. Domain Selection Observability (Future)

**Requirement (placeholder):** Consider tracking *which domains* the reviewer chose to consult (e.g., security always, api-design only when API pattern detected). This would help validate `_detect_api_client_pattern()` and domain-selection logic.

- *To be designed in follow-up.*

---

## Decisions

| Topic | Decision |
|-------|----------|
| **Backward compatibility** | Legacy `confidence_metrics.json` records without `expert_ids` or `selection_reason`: use `expert_ids=[]` and `selection_reason="unknown"` on load. No migration required. |
| **Dashboard fallback alert** | Threshold = 30% (combined fallback_builtin + fallback_all of total consultations). |
| **Recent consultations** | Dashboard shows last 20 records (by timestamp). |

---

## Open Questions

1. **Retention:** How long to keep detailed consultation history in `confidence_metrics.json` and `expert_performance.jsonl`? (e.g., last 1000 records, 30 days). Dashboard "recent consultations" uses last 20 records regardless.
2. **Performance:** Does adding selection_reason and expert_ids to every consultation add noticeable overhead?
3. **Config:** Should HistoryLogger be opt-in via config (recommended), or always on with rotation?

---

## Future Additions (Placeholder)

*Add items here as the design evolves:*

- [ ] Domain selection metrics (which domains the reviewer chose per file)
- [ ] API pattern detection accuracy tracking
- [ ] Expert consultation cost/token metrics
- [ ] *(Other items TBD)*

## Planning Doc Review (Added 2026-02-07)

The implementation plan extends this PRD with:

- **Markdown/planning doc scorer:** `MarkdownPlanningScorer` for PRDs, implementation plans, epics, stories (Phase 3)
- **Epic evaluator:** Planner `*evaluate-epic` for epic structure and story breakdown (Phase 4)
- **Implementation plan checks:** Planner `*evaluate-implementation-plan` for phase/task/completion criteria (Phase 5)

**Expert usage for planning docs:** When the reviewer scores markdown planning docs, it should consult the same shared ExpertRegistry with domain-appropriate experts: `documentation-knowledge-management` (structure, clarity), `development-workflow` (phases, tasks), `software-architecture` (epic structure, dependencies). No new experts—reuse existing built-in experts.

See [REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md](REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md).

---

## Key Files Reference

| Purpose | Path |
|---------|------|
| Reviewer agent | `tapps_agents/agents/reviewer/agent.py` |
| Expert registry | `tapps_agents/experts/expert_registry.py` |
| Confidence metrics | `tapps_agents/experts/confidence_metrics.py` |
| Performance tracker | `tapps_agents/experts/performance_tracker.py` |
| History logger | `tapps_agents/experts/history_logger.py` |
| Dashboard collector | `tapps_agents/dashboard/data_collector.py` |
| Dashboard renderer | `tapps_agents/dashboard/html_renderer.py` |
| Weight matrix | `tapps_agents/experts/weight_distributor.py` |
| Built-in experts | `tapps_agents/experts/builtin_registry.py` |

---

## References

- Expert system design: `docs/architecture/decisions/ADR-003-expert-system-design.md`
- Confidence calculator: `tapps_agents/experts/confidence_calculator.py`
- Adaptive scorer: `tapps_agents/agents/reviewer/adaptive_scorer.py`
- Dashboard generator: `tapps_agents/dashboard/generator.py`
