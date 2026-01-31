# Context7 Health Thresholds and Project vs MCP Cache

**Date:** 2026-01-30  
**Purpose:** Single reference for Context7 health check thresholds and the difference between the project cache and Cursor/MCP cache.

---

## 1. Context7 Health Check Thresholds

**Source:** `tapps_agents/health/checks/context7_cache.py`

| Metric | Target | Degraded | Unhealthy | Notes |
|--------|--------|----------|-----------|--------|
| **Hit rate** | ≥95% | 70–95% (−15 score) | <70% (−30 score) | 77% → "Low hit rate", unhealthy when score <70 |
| **Response time** | <150 ms | 150–1000 ms (−10) | >1000 ms (−20) | Avg response time in ms |
| **Cache size** | >0 bytes | — | 0 bytes (−10) | total_size_bytes |
| **Overall status** | score ≥85 | 70≤ score <85 | score <70 | From weighted score |

**Remediation (from check):**
- "Pre-populate cache: python scripts/prepopulate_context7_cache.py"
- "Run cache refresh: tapps-agents context7 refresh" (when stale ratio high)

**Relaxing thresholds:** To treat 77% hit rate as "degraded" instead of "unhealthy", change the hit-rate bands in `context7_cache.py` (e.g. unhealthy <70%, degraded 70–95%, healthy ≥95%). Response time can similarly use 150–1000 ms = degraded, >1000 ms = unhealthy.

---

## 2. Project Cache vs MCP/Cursor Cache

| | **Project cache** | **Cursor/MCP cache** |
|---|-------------------|------------------------|
| **Location** | `.tapps-agents/kb/context7-cache` (under project root) | Managed by Context7 MCP server (e.g. npx @context7/mcp-server); may be in user or MCP app data |
| **Written by** | Init pre-population, `prepopulate_context7_cache.py`, CLI `reviewer docs` / `implementer docs`, build post-planning refresh | MCP server when Cursor requests docs via Context7 MCP |
| **Read by** | Health check, CLI agents (reviewer, implementer), build orchestrator Context7 helper | Cursor chat when user asks for library docs via MCP |
| **Health check** | Yes — `tapps-agents health check` uses project cache metrics | No — health does not see MCP server cache |

**Implication:** Heavy "Context7" usage in Cursor chat (MCP) does **not** fill the **project** cache. To improve project cache hit rate and health score, run `python scripts/prepopulate_context7_cache.py` or use CLI commands that trigger project-cache lookups (`tapps-agents reviewer docs <library>`, build workflow with post-planning refresh).

---

## 3. References

- Context7 cache check: `tapps_agents/health/checks/context7_cache.py`
- Why project cache doesn’t fill automatically: `docs/feedback/CONTEXT7_CACHE_WHY_NOT_AUTO_2026-01-30.md`
- Config for Simple Mode Context7 refresh: `simple_mode.context7_refresh_after_planning`, `simple_mode.context7_refresh_max_libraries` in `.tapps-agents/config.yaml` (see `tapps_agents/core/config.py` `SimpleModeConfig`).
