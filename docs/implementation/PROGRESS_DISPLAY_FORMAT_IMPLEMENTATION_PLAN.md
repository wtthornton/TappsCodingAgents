# Progress Display Format — Implementation Plan

**Status:** Draft (implementation plan)  
**Created:** 2026-02-05  
**Source:** [HomeIQ Progress Display Format Guide](C:\cursor\HomeIQ\docs\guides\progress-display-format.md)  
**Scope:** Implement, upgrade, or change TappsCodingAgents to use the same terminal-style progress display format for workflow and multi-phase status reporting.

---

## Goals

- **Adopt the phase-grid progress display format** so workflow and phase status are shown in a consistent, scannable, terminal-style layout (icons, Unicode progress bars, status labels, sub-items with tree characters).
- **Unify progress presentation** across workflow completion summaries, `workflow state list/show`, and any multi-step or multi-phase reporting (epic execution, health, etc.).
- **Keep Windows/CI compatibility** by supporting both UTF-8 (Unicode block `█`) and ASCII-safe modes, consistent with existing `unicode_safe` and `--progress plain` behavior.

---

## Reference: Phase-Grid Format Summary

| Component        | Specification |
|-----------------|----------------|
| **Status icons** | ✅ Complete, 📋 Ready, ⏳ Pending, 🔄 In progress, ❌ Failed, ⚠️ Warning |
| **Progress bar** | `[██████████]` 10 blocks; `█` (U+2588) filled, space empty |
| **Status labels** | COMPLETE, READY, PENDING, IN PROGRESS, FAILED |
| **Layout**       | Phase name (left, ~20 chars), icon (2), bar (12 chars), percentage (e.g. `100%`), label |
| **Sub-items**    | `  └─` (U+2514, U+2500) for tree structure |

Example:

```
📊 Progress Summary

Phase 0: Pre-Deployment  ✅ [██████████] 100% COMPLETE
  └─ Stories: 5/5 ✅
Phase 1: Batch Rebuild   ✅ [██████████] 100% COMPLETE
  └─ Services: 38/40 ✅
Phase 2: Std Libraries   📋 [          ] 0% READY
  └─ Stories: 0/7

TOTAL: 33.3% complete (2/6 phases)
```

---

## Current State in TappsCodingAgents

| Area | Current behavior |
|------|-------------------|
| **Progress bars** | `visual_feedback.VisualFeedbackGenerator.format_progress_bar()` uses `safe_format_progress_bar()` → ASCII `[===---]` (width 30). No Unicode block `█` option. |
| **unicode_safe** | `safe_format_progress_bar(percentage, width)` uses `=` and `-`; `_unicode_to_ascii` maps `█` → `#` for fallback. |
| **Progress updates** | `progress_updates.ProgressUpdateGenerator.format_for_chat()` uses markdown headers (## / ###), step indicator, status badges; single-step progress bar. Not phase-based. |
| **Workflow summary** | `workflow_summary.WorkflowSummaryGenerator.format_summary_for_chat()` uses status emoji, **Status:**, **Execution Time:**, step breakdown list. No phase grid or TOTAL line. |
| **CLI progress** | Global `--progress {auto,rich,plain,off}`; `TAPPS_PROGRESS`, `TAPPS_NO_PROGRESS`. Rich vs plain controls UI; no structured phase display. |
| **workflow state** | `workflow state list` / `workflow state show` output format is separate; no adoption of this layout yet. |

---

## Target State

1. **New module: progress display formatter**  
   - Implements the phase-grid format: progress bar (Unicode or ASCII), status line, full report with optional sub-items and TOTAL line.
   - Single place for “phase list + percentages + status + optional sub_items” → formatted string (and optional ASCII-safe variant).

2. **Workflow steps as phases**  
   - Map workflow steps to “Phase N: StepName” with completion percentage and status (COMPLETE / IN PROGRESS / PENDING / FAILED).  
   - Sub-items can include: duration, artifact count, gate result summary, etc.

3. **Integration points**  
   - **Completion summary:** `WorkflowSummaryGenerator` (or a dedicated path) can emit the new format in addition to or instead of current markdown (configurable).  
   - **workflow state show:** When showing one workflow, optionally output the phase grid + TOTAL.  
   - **Progress updates (chat):** Optionally include a compact phase summary (e.g. after each step) using the same format.  
   - **Epic / multi-phase:** Epic execution and any “multi-phase” reporter use the same formatter for consistency.

4. **Configuration and compatibility**  
   - **Display mode:** e.g. `progress_display_format: phasegrid | legacy | plain` (phasegrid = default for all projects with TappsCodingAgents; legacy = summary only; plain = ASCII-only bars).  
   - **Windows / no-UTF-8:** When `--progress plain` or ASCII-safe mode, use `#` (or `=`) for bar and ASCII labels; layout and column widths stay the same.

---

## Design Decisions

1. **Where to implement**  
   - New module under `tapps_agents/core/` (e.g. `progress_display.py`) so workflow and CLI can both use it without circular imports.  
   - Dependencies: only stdlib + optional `unicode_safe` for ASCII fallback. No dependency on workflow models in core; the caller (workflow or CLI) builds the list of “phases” (name, percentage, status, icon, sub_items).

2. **Unicode vs ASCII**  
   - **UTF-8 / rich:** Use `█` and emoji icons in phase-grid format.  
   - **Plain / Windows-safe:** Use `safe_format_progress_bar`-style bar (e.g. `#` or `=`) and ASCII labels (e.g. `[OK]`, `[PENDING]`); same column widths and layout.  
   - Detection: existing `--progress plain` / `TAPPS_PROGRESS=plain` or `TAPPS_NO_PROGRESS`, plus optional `unicode_safe.is_windows_console()` or explicit config.

3. **Backward compatibility**  
   - Default: phase-grid is the default; use `progress_display_format: legacy` to restore previous summary-only behavior.  
   - New format can be added as an extra section (“Progress Summary” block) before the existing summary, or replace it when new format is enabled.

4. **Data contract**  
   - Formatter accepts a list of phase-like dicts: `name`, `percentage`, `status`, `icon`, optional `sub_items` (list of strings).  
   - Workflow layer is responsible for mapping `WorkflowState` + `Workflow` to this list (completed steps = 100%, current = in progress, future = pending; optional sub_items from step executions/artifacts).

---

## Implementation Tasks

### Phase 1: Core formatter (no workflow dependency)

1. **Add `tapps_agents/core/progress_display.py`**
   - `create_progress_bar(percentage: float, width: int = 10, use_unicode: bool = True) -> str`  
     - Returns `[█████     ]` (Unicode) or `[#####     ]` (ASCII).  
   - `create_status_line(phase_name: str, percentage: float, status: str, icon: str, *, use_unicode: bool = True, name_width: int = 20, bar_width: int = 10) -> str`  
     - Padded name, icon, bar, percentage, status label; ASCII-safe icon/bar when `use_unicode=False`.  
   - `generate_status_report(phases: list[dict], *, title: str = "Progress Summary", use_unicode: bool = True, show_total: bool = True) -> str`  
     - `phases`: list of `{ "name", "percentage", "status", "icon", optional "sub_items": list[str] }`.  
     - Output: title, blank line, one line per phase (with optional `  └─` sub_items), then TOTAL line when `show_total=True`.  
   - Use `unicode_safe` (e.g. `safe_format_progress_bar` or a small helper) for ASCII bar when `use_unicode=False`; keep bar width 10 in both modes for consistency with guide.

2. **Tests**  
   - `tests/tapps_agents/core/test_progress_display.py`: test `create_progress_bar` (0, 50, 100; Unicode and ASCII), `create_status_line` alignment, `generate_status_report` with/without sub_items and TOTAL.

### Phase 2: Workflow integration

3. **Phase list builder**  
   - In `tapps_agents/workflow/` (e.g. in `workflow_summary.py` or new `workflow_progress_display.py`), add a function or method that, given `Workflow` + `WorkflowState`, returns the list of phase dicts expected by `generate_status_report`:  
     - One phase per step; `name` = e.g. `"Phase {i}: {step_id}"` or step label; `percentage` = 100 for completed, 0 for not started, optional partial for “in progress”; `status` / `icon` from state (completed → COMPLETE/✅, failed → FAILED/❌, running → IN PROGRESS/🔄, else PENDING/⏳).  
     - Optional `sub_items`: e.g. duration, “Artifacts: N”, gate score snippet.

4. **WorkflowSummaryGenerator**  
   - When config `progress_display_format == "homeiq"` (or equivalent):  
     - Build phase list from workflow state.  
     - Call `generate_status_report(phase_list, use_unicode=...)`.  
     - Either prepend this block to existing `format_summary_for_chat` output or replace the body with this + minimal metadata (workflow_id, execution time).  
   - Determine `use_unicode` from existing progress/terminal settings (e.g. `--progress plain` → False).

5. **workflow state show**  
   - When displaying a single workflow state, optionally print the same phase grid + TOTAL (e.g. when `--format text` and a “progress” view is requested). CLI to accept a flag or config so this is additive and non-breaking.

### Phase 3: Config, docs, and optional integrations

6. **Configuration**  
   - Add to config schema and `.tapps-agents/config.yaml` (or env):  
     - `progress_display_format: phasegrid | legacy | plain` (and document in CONFIGURATION.md).  
   - Document that `plain` forces ASCII bars and ASCII-safe icons.

7. **Documentation**  
   - Add `docs/guides/progress-display-format.md` (or link to HomeIQ guide) describing the format and that TappsCodingAgents can use it for workflow/epic status.  
   - In CONFIGURATION.md (or command-reference), document `progress_display_format` and `--progress` interaction.  
   - Optional: copy or adapt the “Implementation Guide” Python snippets from HomeIQ into this project’s guide so implementers have a single reference.

8. **Optional: Epic and health**  
   - Epic execution: if there is a “phase” or “story” list with completion state, feed it into `generate_status_report` for epic progress output.  
   - Health dashboard: if a text-based health summary has multiple “sections” or “checks,” consider reusing the same layout (section name, icon, bar, percentage, label) for consistency.

---

## Acceptance Criteria

- [x] `progress_display.create_progress_bar` and `create_status_line` produce HomeIQ-spec alignment and bar width (10 blocks); ASCII mode uses same layout with ASCII bar character.
- [x] `generate_status_report` with a list of phases and optional sub_items produces the exact structure (title, phase lines, sub_items with `└─`, TOTAL line).
- [x] When `progress_display_format: phasegrid` (or env `TAPPS_PROGRESS_DISPLAY_FORMAT=phasegrid`) is set, workflow completion summary includes the new progress block without breaking existing callers.
- [ ] `workflow state show` can optionally display the same phase grid (deferred).
- [x] Windows / `--progress plain` path uses ASCII-safe bars and no emoji (or ASCII substitutes); no UnicodeEncodeError.
- [x] Documentation describes the format and config options (CONFIGURATION.md, guides/progress-display-format.md).

---

## References

- **Source guide:** `C:\cursor\HomeIQ\docs\guides\progress-display-format.md`
- **Existing progress:** `tapps_agents/workflow/progress_updates.py`, `progress_manager.py`, `visual_feedback.py`, `workflow_summary.py`
- **Unicode safety:** `tapps_agents/core/unicode_safe.py`
- **CLI progress:** `.cursor/rules/command-reference.mdc` (Global CLI Options: `--progress`, `TAPPS_PROGRESS`)

---

**Status:** Phase 1–2 implemented (core formatter + workflow integration); Phase 3 partial (env + docs; config key optional).  
**Version:** 1.0.0  
**Created:** 2026-02-05  
**Implemented:** 2026-02-05 — `tapps_agents/core/progress_display.py`, `workflow_summary.workflow_state_to_phases`, `WorkflowSummaryGenerator` phasegrid/plain, `ProgressUpdateManager` env wiring, tests, CONFIGURATION.md.
