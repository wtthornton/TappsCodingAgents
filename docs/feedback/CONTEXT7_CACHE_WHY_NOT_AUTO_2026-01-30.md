# Why Context7 Cache Doesn’t Fill Automatically

**Date:** 2026-01-30  
**Summary:** The project’s Context7 cache (`.tapps-agents/kb/context7-cache`) is only filled in a few specific situations. It is **not** filled by normal Cursor usage or by every agent run.

---

## When the project cache **is** filled

1. **Init (one-time)**  
   `tapps-agents init` runs cache pre-population by default **after** core init, using the detected tech stack.  
   - Skipped if you pass `--no-cache`.  
   - Can fail silently if Context7 isn’t enabled, `CONTEXT7_API_KEY` is missing, or there’s a permission/load error (e.g. config load failure), so the cache may stay empty.

2. **Pre-populate script**  
   `python scripts/prepopulate_context7_cache.py` (optionally with `--requirements requirements.txt` or `--libraries …`) fills the cache for the libraries you specify or detect.  
   - This is the most reliable way to get a full cache.

3. **CLI docs lookups**  
   When a **CLI** command triggers a Context7 docs lookup that **misses** the project cache, the flow is: **API fetch → store in project cache**.  
   - So the project cache is filled when you run things like:  
     - `tapps-agents reviewer docs <library>`  
     - `tapps-agents implementer docs <library>`  
     and the requested library/topic isn’t already cached.  
   - Other CLI commands (e.g. `reviewer review`, `reviewer score`, `workflow`, `simple-mode *build`) do **not** necessarily call Context7; they only fill the cache if their implementation does a docs lookup and it misses.

4. **Brownfield review**  
   `tapps-agents brownfield review` (without `--no-context7`) can fetch library docs via Context7 and, when the framework’s Context7 helper is used, those lookups can populate the project cache on miss.

So “automatic” in the docs means: **automatic when one of these paths runs**, not “automatic on every Cursor or agent action.”

---

## When the project cache is **not** filled

1. **Cursor chat / MCP only**  
   If you use Cursor and ask for library docs via chat (or another tool) and the answer is served by the **Context7 MCP server** (e.g. `npx @context7/mcp-server`), that server talks to the Context7 API and may use its **own** cache. It does **not** write into the project’s `.tapps-agents/kb/context7-cache`.  
   So heavy “Context7” usage in Cursor chat does not by itself fill the **project** cache.

2. **Workflows that don’t do docs lookups**  
   Most workflow steps (e.g. planner, architect, designer, implementer, reviewer *review, tester) don’t call Context7 unless they’re explicitly written to fetch library docs. So normal `*build` / `*fix` / `*review` / `*test` runs often don’t trigger any Context7 lookup and don’t fill the project cache.

3. **Init with `--no-cache` or failed init cache**  
   If init was run with `--no-cache`, or the deferred cache step failed (no API key, Context7 disabled, permission error), the one-time init population never runs. The cache then only fills via the script or via CLI docs lookups (and brownfield, if used).

---

## How the code works (on-demand fill)

- **Lookup flow** (`tapps_agents/context7/lookup.py`): when you ask for docs for a library/topic, the code:
  1. Tries the **project** KB cache (e.g. `.tapps-agents/kb/context7-cache`).
  2. On **miss**, calls the Context7 API (via MCP gateway or HTTP fallback), then **stores** the result in the project cache with `self.kb_cache.store(...)`.
- So **any** code path that uses this lookup (CLI `reviewer docs`, `implementer docs`, brownfield Context7 helper, etc.) will fill the project cache on first request for that library/topic.  
- Cursor’s native Context7 MCP usage is a different path and does not use this `kb_cache.store()` for the project directory.

---

## Recommendations

1. **Fill the cache explicitly**  
   Run:  
   `python scripts/prepopulate_context7_cache.py`  
   (or with `--requirements requirements.txt`).  
   Do this after init and whenever you add dependencies or want better hit rates.

2. **Ensure init can populate cache**  
   When running `tapps-agents init`, ensure Context7 is enabled and `CONTEXT7_API_KEY` is set so the deferred cache step can succeed. Fix any config/permission issues if the cache stays empty after init.

3. **Use CLI docs commands to warm cache**  
   For libraries you care about, run:  
   `tapps-agents reviewer docs <library>`  
   (and optionally `tapps-agents implementer docs <library>`).  
   Each first request for a library/topic will fetch and cache it in the project.

4. **Optional: document the two “Context7” caches**  
   In user-facing docs, briefly explain that:
   - The **project** cache (used by health and CLI) is under `.tapps-agents/kb/context7-cache` and is filled by init (once), the prepopulate script, and CLI docs lookups.
   - Cursor’s Context7 MCP usage may use a different cache and does not update the project cache.

---

## References

- Context7 lookup and cache store: `tapps_agents/context7/lookup.py` (e.g. “Step 5: Store in cache if we got content”).
- Init cache request: `tapps_agents/core/init_project.py` (`pre_populate_cache`, `cache_requested`, `cache_libraries`).
- CLI running cache after init: `tapps_agents/cli/commands/top_level.py` (`cache_requested`, `pre_populate_context7_cache`).
- Pre-populate script: `scripts/prepopulate_context7_cache.py`.
- Health check remediation: “Pre-populate cache: python scripts/prepopulate_context7_cache.py” and “Or wait for automatic cache population during agent execution” (meaning: when an agent run actually performs a Context7 docs lookup via the framework).
