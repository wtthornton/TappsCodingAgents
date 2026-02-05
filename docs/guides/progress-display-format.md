# Progress Display Format (Terminal-Style)

**Status:** Reference / implementation planned  
**Created:** 2026-02-05  
**Purpose:** Describe the terminal-style progress display format adopted for workflow and multi-phase status in TappsCodingAgents.

---

## What This Is

A **visual status format** for multi-phase or multi-step progress (workflows, epic execution, health, CI-style pipelines). It uses:

- **Status icons** (e.g. ✅ Complete, 📋 Ready, ⏳ Pending, 🔄 In progress, ❌ Failed)
- **Unicode progress bars** `[██████████]` (10 blocks) or ASCII-safe `[#####     ]`
- **Status labels** (COMPLETE, READY, PENDING, IN PROGRESS, FAILED)
- **Sub-items** with tree characters `  └─` for details under each phase
- **TOTAL line** for overall completion (e.g. `TOTAL: 33.3% complete (2/6 phases)`)

Output is plain text in a code block, so it works in terminals, markdown, chat, and CI logs.

---

## Example (Workflow Completion)

```
📊 Progress Summary

Phase 0: Enhance        ✅ [██████████] 100% COMPLETE
  └─ Duration: 2m 15s
Phase 1: Plan           ✅ [██████████] 100% COMPLETE
  └─ Stories: 3
Phase 2: Architect      🔄 [█████     ]  50% IN PROGRESS
Phase 3: Implement     ⏳ [          ]   0% PENDING
Phase 4: Review         ⏳ [          ]   0% PENDING
Phase 5: Test           ⏳ [          ]   0% PENDING

TOTAL: 33.3% complete (2/6 phases)
```

---

## Specification Summary

| Component     | Specification |
|---------------|----------------|
| **Icons**     | ✅ 📋 ⏳ 🔄 ❌ ⚠️ (or ASCII equivalents when `--progress plain`) |
| **Bar**       | 10 blocks: `█` filled, space empty; or `#` / `=` in ASCII mode |
| **Layout**    | Phase name (~20 chars), icon, bar (12 chars), percentage, label |
| **Sub-items** | `  └─` then text |

---

## In TappsCodingAgents

- **Default:** Phase-grid is the default for all projects with TappsCodingAgents installed. Workflow completion summaries show the phase grid, giving developers a clear visual that TappsCodingAgents is active.
- **Implementation plan:** [Progress Display Format — Implementation Plan](../implementation/PROGRESS_DISPLAY_FORMAT_IMPLEMENTATION_PLAN.md)
- **Planned use:** Workflow completion summary, `workflow state show`, optional epic/health progress
- **Config:** `progress_display_format: phasegrid` (default) | `legacy` | `plain`
- **Compatibility:** ASCII-safe mode when `--progress plain` or on Windows console to avoid encoding issues

---

## Origin

The format was inspired by a guide from the HomeIQ project (`C:\cursor\HomeIQ\docs\guides\progress-display-format.md`). TappsCodingAgents calls its implementation **phase-grid** — a descriptive name for the scannable grid of phases with status icons and progress bars.
