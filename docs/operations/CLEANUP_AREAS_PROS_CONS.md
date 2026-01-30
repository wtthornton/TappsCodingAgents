# Cleanup Areas: Pros and Cons

**Purpose:** Design rationale for what `tapps-agents cleanup` does and does **not** do—including why KBCleanup, RAG cleanup, and stale RAG deletion are not part of the main cleanup command, and pros/cons for other cleanup areas.

**Related:** Epic 7 / Story 7.5 (Operational Runbooks & Data Hygiene), `tapps_agents/core/cleanup_tool.py`, `.cursor/rules/command-reference.mdc` (cleanup section).

---

## 1. Why `cleanup` Should NOT Call KBCleanup (Context7 KB Cache)

**KBCleanup** (`tapps_agents/context7/cleanup.py`) manages the **Context7 library documentation cache**: age-based, size-based, and unused-entry removal.

### Pros of NOT integrating KBCleanup into `tapps-agents cleanup`

| Pro | Rationale |
|-----|-----------|
| **Different lifecycle** | Context7 cache is refilled on demand via MCP/API; cleanup is a cache-size/age policy, not "project hygiene." Users expect `cleanup` to remove *our* artifacts (workflows, sessions), not third-party/doc cache. |
| **Risk of breaking lookups** | Aggressive cleanup can evict entries still needed for `@reviewer *docs` / `@implementer *docs`. Next lookup may re-fetch (slower) or hit quota; users may not connect regression to `cleanup all`. |
| **Context7 may be disabled** | Many projects run without Context7. Running KBCleanup when cache is disabled or missing adds complexity and potential errors for no benefit. |
| **Policy is environment-specific** | Cache size/age limits depend on disk, API quota, and usage. Those belong in Context7/config, not in a generic "cleanup artifacts" command. |
| **Single responsibility** | `cleanup` stays "TappsCodingAgents artifact hygiene"; Context7 cache is a separate subsystem with its own tooling (e.g. health checks, cache refresh). |

### Cons of NOT integrating KBCleanup

| Con | Mitigation |
|-----|------------|
| **Cache can grow large** | Document Context7 cache location and that `KBCleanup` exists; optionally document "advanced: run Context7 cleanup" in operations/context7 docs. |
| **No one-click "clean everything"** | Accept that "everything" is workflow-docs + sessions (+ worktrees/analytics/cache if exposed); Context7 remains opt-in and separate. |

**Conclusion:** Keep KBCleanup **out** of `tapps-agents cleanup`. Use it only from Context7-specific code or (if ever) a dedicated `context7 cleanup` subcommand.

---

## 2. Why `cleanup` Should NOT "Clean RAG" (Experts Knowledge Base)

**RAG** here means the experts' knowledge base (e.g. `tapps_agents/experts/knowledge/`, project `.tapps-agents/` knowledge): markdown/content used for retrieval-augmented generation.

### Pros of NOT adding RAG "cleanup" to `tapps-agents cleanup`

| Pro | Rationale |
|-----|------------|
| **Content, not disposable artifacts** | Knowledge files are curated content. Deleting them by age or size risks removing intentional, rarely-updated reference material. |
| **No clear "safe" policy** | Unlike sessions (transient) or workflow-docs (runs), there is no universal rule for "this knowledge file is safe to delete." |
| **Ownership and versioning** | Many files live in repo or are user-maintained. A CLI cleanup deleting them would be surprising and dangerous. |
| **RAG index vs. source** | If "clean RAG" meant index/cache only, that's a different surface (e.g. vector index); the CLI today has no such concept. |
| **Explicit over implicit** | Any future "prune RAG index" or "remove orphan chunks" should be a separate, opt-in command with clear scope. |

### Cons of NOT cleaning RAG

| Con | Mitigation |
|-----|------------|
| **Stale or duplicate content can accumulate** | Use `tapps-agents knowledge freshness` (report-only) and `knowledge validate`; curation stays manual or in a dedicated, safe workflow. |
| **Disk usage from many knowledge files** | Document where knowledge lives and that cleanup does not touch it; large repos can use git LFS or archiving outside this CLI. |

**Conclusion:** Do **not** add a "clean RAG" step to `tapps-agents cleanup`. Keep knowledge as report-only (freshness/validate) and any future pruning as a separate, explicit command.

---

## 3. Why `cleanup` Should NOT Delete "Stale RAG" Automatically

**Stale RAG** = content or indices that are old, deprecated, or no longer referenced. Deletion could mean: removing stale *metadata*, removing *files* marked deprecated, or pruning *vector/index* entries.

### Pros of NOT auto-deleting stale RAG in `cleanup`

| Pro | Rationale |
|-----|------------|
| **"Stale" is ambiguous** | Age alone is poor signal; some docs are intentionally long-lived. Deprecation is metadata, not a safe delete signal without user confirmation. |
| **Irreversibility** | Deleting source files or index entries is hard to undo. Fits a dedicated "prune with confirmation" flow, not a broad `cleanup all`. |
| **Freshness is today report-only** | `knowledge freshness` returns stale/deprecated lists; it does not delete. Adding delete to `cleanup` would bypass the current "report first" design. |
| **Cross-project consistency** | Framework knowledge (built-in) vs. project knowledge have different rules; one policy in `cleanup all` would not fit all. |

### Cons of NOT auto-deleting stale RAG

| Con | Mitigation |
|-----|------------|
| **Users may want to reclaim space from deprecated files** | Provide a separate command or script that deletes only deprecated files (or archives them) with confirmation and clear scope. |
| **Index bloat** | If/when the framework has an explicit "RAG index" (e.g. vector store), design a dedicated "rebuild index" or "prune index" command, not `cleanup`. |

**Conclusion:** Do **not** delete stale RAG inside `tapps-agents cleanup`. Keep stale/deprecated as report-only; any deletion or pruning should be a separate, explicit, and safe operation.

---

## 4. Pros and Cons for Other Cleanup Areas

### 4.1 Workflow docs (current: in CLI `cleanup`)

| Pros | Cons |
|------|------|
| Reduces clutter under `docs/workflows/simple-mode/`. | Old runs are hidden/archived; users must know archive location. |
| Configurable keep-latest + retention; optional archive. | Archive can grow if retention is long. |
| Clear "artifact of a run" semantics; safe to archive by age. | None significant. |

**Verdict:** Keep in `cleanup`; current design is appropriate.

---

### 4.2 Sessions (current: in CLI `cleanup`)

| Pros | Cons |
|------|------|
| `.tapps-agents/sessions/` is clearly transient (enhancer + agent sessions). | SessionManager and enhancer formats must stay in sync. |
| Zero-byte and old files are safe to remove by policy. | If a session is still "in use" (e.g. long-running agent), cleanup could remove its file; current policy uses age. |
| Frees disk and keeps directory manageable. | None critical if age/keep_latest are conservative. |

**Verdict:** Keep in `cleanup`; optional: document that very long-running sessions might be older than `max_age_days`.

---

### 4.3 Worktrees (current: in `CleanupTool`, not in CLI `cleanup`)

| Pros | Cons |
|------|------|
| Old workflow worktrees can consume a lot of disk. | Deleting a worktree is destructive; user may have unmerged work. |
| Clear "temporary" semantics for workflow-created worktrees. | Need to avoid deleting worktrees for in-progress workflows. |

**Verdict:** Reasonable to keep out of default `cleanup all`; if exposed, use a separate subcommand (e.g. `cleanup worktrees`) with retention and dry-run, and document risk.

---

### 4.4 Analytics (current: in `CleanupTool`, not in CLI `cleanup`)

| Pros | Cons |
|------|------|
| Old analytics history can be pruned by age to save space. | Historical metrics may be needed for trends; deleting loses data. |
| Simple policy (e.g. keep last N days). | Low disk impact compared to worktrees/workflow-docs. |

**Verdict:** Optional addition as `cleanup analytics` with long default retention (e.g. 90 days); not critical for "cleanup all."

---

### 4.5 Generic cache (current: in `CleanupTool`, not in CLI `cleanup`)

| Pros | Cons |
|------|------|
| `.tapps-agents/cache/` can grow; age-based prune is simple. | "Cache" is generic; may hold mixed content; risk of deleting something still needed. |
| Frees space with a simple policy. | Different from Context7 KB cache; naming can confuse. |

**Verdict:** If exposed, do so as a distinct subcommand (e.g. `cleanup cache`) with conservative defaults and documentation; do not conflate with Context7 cache.

---

### 4.6 Workflow state (current: `workflow state cleanup`, separate from `cleanup`)

| Pros | Cons |
|------|------|
| Old persisted workflow state can be removed by retention/max-per-workflow. | Removing state prevents resume; must be clearly documented. |
| Separate command keeps "resume" vs "artifact hygiene" concerns clear. | Two places to "clean" (cleanup vs workflow state) can confuse. |

**Verdict:** Keep as `workflow state cleanup`; do not merge into `tapps-agents cleanup` so that workflow-state semantics and resume implications stay explicit.

---

### 4.7 Branches (current: `workflow cleanup-branches`)

| Pros | Cons |
|------|------|
| Orphaned workflow branches can be removed to avoid clutter. | Deleting branches is irreversible and can affect CI/history. |
| Dry-run and confirmation support safe use. | Belongs to "workflow" namespace, not generic "cleanup." |

**Verdict:** Keep as `workflow cleanup-branches`; do not merge into `cleanup` so that branch semantics and safety stay clear.

---

## 5. Summary Table

| Area | In CLI `cleanup`? | Call KBCleanup / RAG / Stale RAG? | Recommendation |
|------|-------------------|------------------------------------|----------------|
| Workflow docs | Yes | No | Keep as-is. |
| Sessions | Yes | No | Keep as-is. |
| KBCleanup (Context7 KB) | No | No | Do not call from cleanup. |
| RAG (knowledge base) | No | No | Do not add "clean RAG" to cleanup. |
| Stale RAG deletion | No | No | Do not auto-delete in cleanup. |
| Worktrees | No (CleanupTool only) | No | Optional separate subcommand; keep out of default "all". |
| Analytics | No (CleanupTool only) | No | Optional subcommand; low priority. |
| Generic cache | No (CleanupTool only) | No | Optional subcommand; document vs Context7. |
| Workflow state | No (`workflow state cleanup`) | No | Keep separate. |
| Branches | No (`workflow cleanup-branches`) | No | Keep separate. |

---

## 6. Recommendations

**Leave as-is (no change required):**

- Keep `tapps-agents cleanup` as **workflow-docs** and **sessions** only (and **cleanup all** = both). Do not add KBCleanup, RAG cleanup, or stale RAG deletion to cleanup.
- Keep **workflow state** and **branches** as separate commands (`workflow state cleanup`, `workflow cleanup-branches`); do not merge into `cleanup`.
- No code or config changes are required for the current design to be correct and safe.

**Optional improvements (only if needed):**

| Priority | Action | Rationale |
|----------|--------|-----------|
| Low | Document in Context7 docs where the KB cache lives and that `KBCleanup` exists for advanced users. | Mitigates "cache can grow large" without touching cleanup. |
| Low | In cleanup or sessions docs, note that very long-running agent sessions may be older than `max_age_days` and could be pruned. | Avoids surprise for long runs. |
| Optional | Expose `cleanup worktrees` as a separate subcommand (retention + dry-run) if users ask for it. | CleanupTool already supports it; CLI exposure is additive. |
| Optional | Expose `cleanup analytics` and/or `cleanup cache` as separate subcommands with conservative defaults if disk pressure becomes an issue. | Low impact; add only on demand. |
| Future | If deprecated knowledge files become a pain, add a dedicated `knowledge prune` (or similar) that deletes/archives only deprecated files with confirmation. | Keeps cleanup unchanged; pruning stays explicit and safe. |

**Bottom line:** The current behavior is sound. Leave cleanup as-is unless you have a specific need (e.g. worktrees eating disk); then add optional subcommands or docs as in the table above.

---

## 7. References

- **Cleanup CLI:** `tapps_agents/cli/parsers/top_level.py` (cleanup subparsers), `tapps_agents/cli/commands/top_level.py` (`handle_cleanup_*`).
- **CleanupTool:** `tapps_agents/core/cleanup_tool.py` (workflow_docs, sessions, worktrees, analytics, cache).
- **Context7 KBCleanup:** `tapps_agents/context7/cleanup.py` (KBCleanup: age, size, unused).
- **Knowledge freshness (report-only):** `tapps_agents/experts/knowledge_freshness.py`, `tapps-agents knowledge freshness`.
- **Command reference:** `.cursor/rules/command-reference.mdc` (cleanup section).
