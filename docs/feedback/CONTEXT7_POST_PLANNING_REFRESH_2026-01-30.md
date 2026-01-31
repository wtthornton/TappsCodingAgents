# Context7 Refresh After Simple-Mode Planning

**Date:** 2026-01-30  
**Summary:** Run a check/refresh every time simple-mode finishes planning, so Context7 cache is warmed based on the plan. Implemented as an automatic hook plus an LLM suggestion.

---

## What Was Implemented

1. **Automatic hook (BuildOrchestrator)**  
   After Step 2 (planning) completes in the build workflow, the orchestrator:
   - Collects the planner output and the enhanced prompt.
   - Calls `_refresh_context7_after_planning(enhanced_prompt, planner_output)`.
   - That helper detects libraries from the combined text (enhanced prompt + plan), filters to project/well-known/mentioned libs, and calls `context7_helper.get_documentation_for_libraries(...)` to warm the project Context7 cache.
   - Failures are non-blocking (logged at debug).

2. **LLM suggestion (Simple Mode SKILL)**  
   The Simple Mode skill instructs the LLM that:
   - After Step 2 (Create user stories) completes, a Context7 cache refresh runs automatically.
   - The LLM may also suggest or run: `python scripts/prepopulate_context7_cache.py` or `@reviewer *docs <library>` for key libraries from the plan.
   - This improves implementer and reviewer quality.

---

## Pros and Cons

### Automatic check (hook runs every time planning finishes)

| Pros | Cons |
|------|------|
| No user action required; cache is warmed for implement/review steps. | Extra Context7 API/cache work after every planning step (latency, quota). |
| Libraries are derived from the actual plan + enhanced prompt. | If plan mentions many libraries, refresh can be slow or hit rate limits. |
| Same behavior for CLI and Cursor; consistent. | User cannot disable it per run without a config flag. |
| Higher cache hit rate for implementer/reviewer. | Duplicate work if user already ran prepopulate or init cache. |

### LLM-suggested (suggest to the user; LLM or user runs refresh)

| Pros | Cons |
|------|------|
| User controls when to run (and can skip). | User may ignore the suggestion; cache may stay cold. |
| No extra latency unless user runs the suggested command. | Inconsistent: only helps when the LLM suggests and user complies. |
| Can target “key libraries from the plan” so the LLM chooses what to warm. | Depends on LLM following the skill instruction. |
| Fits “suggest, don’t force” patterns. | Manual step adds friction. |

### Combined (automatic hook + LLM suggestion)

- **Current design:** Automatic hook runs after planning; SKILL also tells the LLM it may suggest or run prepopulate / `*docs` for key libraries.
- **Pros:** Cache is warmed by default; LLM can still suggest a fuller prepopulate or targeted `*docs` when useful.
- **Cons:** Possible redundancy (hook + user running prepopulate); hook cost on every build.

---

## Recommendations

- **Keep the automatic hook** so most users get a warmer cache without doing anything. Optionally add a config flag (e.g. `simple_mode.context7_refresh_after_planning: true/false`) to disable it if needed.
- **Keep the LLM suggestion** so the LLM can suggest `prepopulate_context7_cache.py` or `@reviewer *docs <library>` when the plan clearly depends on specific libraries.
- **Optional:** Cap the number of libraries in the post-planning refresh (e.g. top 5–10 by relevance) to limit latency and quota use.

---

## References

- Build orchestrator: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py` (`_refresh_context7_after_planning`, post-planning hook).
- Simple Mode SKILL: `.claude/skills/simple-mode/SKILL.md` (after Step 2, Context7 refresh after planning).
- Context7 cache: `docs/feedback/CONTEXT7_CACHE_WHY_NOT_AUTO_2026-01-30.md`.
