# Context Window Optimization — Implementation Plan (Options 1–3)

**Status:** Draft (design / implementation plan)  
**Created:** 2026-02-03  
**Scope:** Options 1 (tiered context + token budgets), 2 (token-aware artifact injection + summarization), 3 (Context7 on-demand + caps) from the prioritized context-window optimization list.

**Goals:**
- Bound context size at every LLM call so TappsCodingAgents stays within model context limits and maintains quality.
- Improve workflow success (e.g. implementer gets the right prior-step context without overflow or truncation).
- Restore Context7 cache health (target >80% hit rate, <100 ms cache response) and enforce per-agent doc caps.

**References:**
- Health: Context7 cache FAIL (65/100), 79.1% hit, 465 ms; 53 failed workflows (usage dashboard).
- Existing code: `tapps_agents/core/tiered_context.py`, `tapps_agents/core/context_intelligence/token_budget_manager.py`, `ContextIntelligenceConfig` in `config.py`; build orchestrator `_enrich_implementer_context` (character caps); Context7 `agent_integration.py`, `lookup.py`.
- Docs: `docs/context7/CONTEXT7_PATTERNS.md` (agent token limits), `requirements/PROJECT_REQUIREMENTS.md` (tiered context tiers).

---

## Overview

| Option | Summary | Primary owners (conceptual) |
|--------|---------|-----------------------------|
| **1** | Enforce tiered context and token budgets at every call site | Core / workflow |
| **2** | Token-aware workflow artifact injection and summarization | Simple mode / build |
| **3** | Context7 strict on-demand usage and per-agent caps | Context7 / config |

**Phasing:** Implement in order 1 → 2 → 3. Option 2 can reuse token estimation and budget concepts from Option 1; Option 3 is largely independent but benefits from a consistent “context budget” mindset.

---

## Option 1: Enforce Tiered Context and Token Budgets at Every Call Site

### 1.1 Current state

- **TieredContextBuilder** (`tapps_agents/core/tiered_context.py`): Builds context by tier (TIER1 1K, TIER2 5K, TIER3 20K tokens) from file structure, signatures, bodies, etc. Used only where explicitly imported; **not** used in build orchestrator or cursor executor.
- **TokenBudgetManager** (`tapps_agents/core/context_intelligence/token_budget_manager.py`): Tracks used vs budget (default 4000); `can_add`, `add`, `reset`. **Not** used on the main workflow execution paths.
- **ContextIntelligenceConfig** (`tapps_agents/core/config.py`): `token_budget_management_enabled`, `default_token_budget` (4000, range 1000–16000), `progressive_loading_enabled`. No wiring to TieredContextBuilder or TokenBudgetManager in orchestrators or executor.
- **BuildOrchestrator / CursorWorkflowExecutor:** Build prompts and step params without a single “context assembly” path; no tier selection per step and no token budget applied before sending to the model.

### 1.2 Target state

- **Single context-construction path:** All payloads that include file/code context for an LLM go through one service (or a small set of entry points) that applies tier + token budget.
- **Tier per step type:** Each workflow step type (e.g. enhance, plan, architect, design, implement, review, test) has an assigned default tier (e.g. planner TIER1, implementer TIER2, reviewer TIER1). Config or step metadata can override.
- **Token budget enforced:** Before adding any context block, the path checks `TokenBudgetManager.can_add(estimated_tokens)`; if over budget, it either truncates, drops lowest-priority content, or returns a clear “over budget” so the caller can shorten the prompt. Step-type-specific budgets (e.g. implementer 6000, reviewer 4000) are supported via config.
- **Observability:** Log or metric when budget is hit or tier is downgraded so we can tune defaults.

### 1.3 Design decisions

- **Where to centralize:** Introduce a **ContextAssemblyService** (or **UnifiedContextBuilder**) in `tapps_agents/core/` that:
  - Takes (step_type, target_file, optional extra_spec) and returns a single context dict + token estimate.
  - Uses TieredContextBuilder for file-based context and TokenBudgetManager for the total.
  - Reads tier and budget from config (and optional step metadata).
- **Step-to-tier mapping:** Define a default mapping (e.g. in config or a small table): analyst/planner/reviewer → TIER1; architect/designer/implementer → TIER2; optional “deep analysis” → TIER3. Allow overrides per workflow step in preset YAML (e.g. `context_tier: tier2`).
- **Scope of “every call site”:** At minimum: BuildOrchestrator (implementer and any step that receives file/code context), FixOrchestrator (debugger/implementer context), CursorWorkflowExecutor (when it builds context for a step). Full SDLC orchestrator similarly. Skills that build their own prompts (e.g. via SkillInvoker) should receive already-bounded context from the executor/orchestrator rather than building unbounded context themselves.
- **Backward compatibility:** If `token_budget_management_enabled` is False or config is missing, keep current behavior (no tiering, no budget). Feature flag or config section for “strict context mode.”

### 1.4 Implementation tasks

1. **Config**
   - Add (or extend) a section for context assembly, e.g. `context_assembly` or under `context_intelligence`:
     - `step_tier_defaults: { step_id: tier1|tier2|tier3 }`
     - `step_token_budgets: { step_id: int }` (optional overrides)
     - `strict_context_enabled: bool` (default True for new behavior when implemented)
   - Ensure `default_token_budget` and `token_budget_management_enabled` from ContextIntelligenceConfig are read by the new service.

2. **ContextAssemblyService (or UnifiedContextBuilder)**
   - New module under `tapps_agents/core/` (e.g. `context_assembly.py` or under `context_intelligence/`).
   - Dependencies: TieredContextBuilder, TokenBudgetManager, ASTParser, config.
   - `build_context_for_step(step_id: str, target_path: Path | None, options: dict) -> dict`:
     - Resolve tier from step_id (and overrides).
     - Create TokenBudgetManager with step budget (or default).
     - If target_path: call TieredContextBuilder.build_context(path, tier); estimate tokens; add to budget (if can_add); else truncate or omit.
     - Return structured context + `token_estimate` and `budget_exceeded: bool`.
   - Helper to estimate tokens for a string (chars/4 or optional tiktoken if available).

3. **Wire into BuildOrchestrator**
   - Where implementer (or other steps) get file/code context, call ContextAssemblyService instead of ad-hoc file reads.
   - Pass step_id (e.g. `implementer`) and target_file; use returned context in the payload passed to the skill/API.
   - If budget_exceeded, log and optionally trim other parts of the prompt (e.g. spec summary) to stay under cap.

4. **Wire into FixOrchestrator**
   - Same pattern for debugger and implementer steps: use ContextAssemblyService for any file-based context.

5. **Wire into CursorWorkflowExecutor**
   - In `_get_step_params` or wherever context for a step is built, use ContextAssemblyService when building “code context” for the step so that all Cursor workflow steps get tiered, budgeted context.

6. **Full SDLC / other orchestrators**
   - Audit and wire any other paths that build LLM payloads with file/code context through the same service.

7. **Tests**
   - Unit tests: ContextAssemblyService with mock TieredContextBuilder/TokenBudgetManager; tier resolution; budget exceeded behavior.
   - Integration: One build and one fix run that verify context size (e.g. token_estimate) is within configured budget.

### 1.5 Acceptance criteria

- Every code path that builds context for an LLM workflow step (build, fix, full, cursor executor) uses ContextAssemblyService (or equivalent) when `strict_context_enabled` is True.
- Configurable step → tier and step → token budget; default tier for implementer is TIER2, for reviewer TIER1.
- TokenBudgetManager prevents total context from exceeding the step budget; when exceeded, behavior is defined (truncate or drop) and logged.
- No regression: with `strict_context_enabled` False or config absent, behavior matches current (no tiering/budget).
- Docs: Update CONFIGURATION.md and any architecture docs to describe the single context path and config keys.

### 1.6 Risks and mitigations

- **Risk:** TieredContextBuilder is file-centric; some steps use “prompt + artifacts” without a single target file.  
  **Mitigation:** ContextAssemblyService can accept “no target file” and only apply token budget to artifact text (see Option 2); tier applies only when target_path is present.

- **Risk:** Over-truncation hurts quality.  
  **Mitigation:** Start with generous defaults (e.g. implementer 6000); add observability and tune from real runs.

---

## Option 2: Token-Aware Workflow Artifact Injection and Summarization

### 2.1 Current state

- **BuildOrchestrator._enrich_implementer_context** reads step 1–4 documentation and injects into implementer args with **fixed character caps**: step1 (enhanced prompt) 2000 chars, step2/3/4 (user-stories, architecture, design) 3000 chars each. No token counting; no priority order when total would exceed a safe size; truncation is by character slice (can cut mid-sentence).
- **WorkflowDocumentationReader** (`tapps_agents/simple_mode/documentation_reader.py`): `read_step_documentation(step_number, step_name)` returns full file content; caller (build orchestrator) does truncation.
- Other orchestrators (e.g. full SDLC) may pass prior artifacts similarly; pattern should be reusable.

### 2.2 Target state

- **Token budget for “previous step context”:** One configurable budget (e.g. 4000 tokens) for all prior-step artifacts combined. Fill in **priority order**: specification (step1) first, then user_stories (step2), then architecture (step3), then api_design (step4). When adding the next artifact would exceed the budget, either truncate that artifact to fit remaining budget or replace it with a **summary**.
- **Summarization when over budget:** If an artifact is too long to fit in the remaining budget, use a short summary instead of raw truncation. Summary can be: (a) template-based (e.g. “User stories: N items; key themes: …”), or (b) from a small/fast model call (e.g. “Summarize in 3 bullet points”). Design should allow both (template first, model summarization optional).
- **Token estimation:** Use the same token estimation as Option 1 (chars/4 or tiktoken) so that “previous step context” and “file context” share one budget concept.
- **Reuse:** The same “artifact budget + priority + summarization” can apply to any step that receives multiple prior artifacts (e.g. full SDLC implementer).

### 2.3 Design decisions

- **Budget config:** Add e.g. `artifact_context_budget_tokens: 4000` (default) under simple_mode or context_assembly. Optionally per-workflow-type (build vs full).
- **Priority order:** Fixed order (spec → stories → architecture → design) unless we add metadata to steps; document and keep consistent so implementer always sees the most important spec first.
- **Summarization:** Phase 1: template-based summary (e.g. “Step 2: User stories (3). Step 3: Architecture (1 component). Step 4: API design (2 endpoints).”) when over budget. Phase 2 (optional): call a small model to summarize the overflowing artifact into N bullets within token limit.
- **Where to implement:** New helper (e.g. `ArtifactContextBuilder` or method on ContextAssemblyService) that takes (list of (step_name, content), budget_tokens, priority_order) and returns dict of (key → content or summary). BuildOrchestrator._enrich_implementer_context calls this instead of raw read + char slice.

### 2.4 Implementation tasks

1. **Token estimation helper**
   - Reuse or expose the same estimator used in Option 1 (e.g. in a small `token_utils` or on ContextAssemblyService) so artifact sizes are in tokens.

2. **ArtifactContextBuilder (or equivalent)**
   - New class or function in `tapps_agents/simple_mode/` or under `tapps_agents/core/`:
     - Input: ordered list of (key, content_string), total token budget.
     - For each (key, content) in order: estimate tokens; if current_used + estimate <= budget, add full content; else if remaining budget > threshold (e.g. 200 tokens), add truncated content up to remaining; else add template summary for that key (e.g. “Step N: … (summary)”).
   - Template summaries: short strings per step type (e.g. “Enhanced prompt (summary)”, “User stories: N items”, “Architecture: …”, “API design: …”) so the model still knows what was produced.

3. **Summarization (optional Phase 2)**
   - If template summary is insufficient, add an optional call to a summarization function (e.g. small local model or a single LLM call with “summarize in &lt;N&gt; tokens”) for the overflowing artifact. Gate by config (e.g. `artifact_summarization_enabled`) and keep timeout/cost small.

4. **Integrate into BuildOrchestrator._enrich_implementer_context**
   - Replace current read + char-slice logic with: read all four step docs; build ordered list (spec, user_stories, architecture, api_design); call ArtifactContextBuilder with `artifact_context_budget_tokens`; assign result back to args (same keys). Remove hardcoded 2000/3000 character limits.

5. **Config**
   - Add `artifact_context_budget_tokens` (default 4000) and optionally `artifact_summarization_enabled` (default False for Phase 1).

6. **Other consumers**
   - If full SDLC or other orchestrators inject prior-step artifacts, refactor them to use the same ArtifactContextBuilder and budget.

7. **Tests**
   - Unit: ArtifactContextBuilder with mock content; verify priority order; verify budget respected; verify summary used when over budget.
   - Integration: Build workflow run where step docs are large; verify implementer args stay within budget and contain either full or summarized content.

### 2.5 Acceptance criteria

- Implementer (and any step using prior artifacts) receives prior-step context that never exceeds `artifact_context_budget_tokens`.
- Priority order is spec → stories → architecture → design; when over budget, later artifacts are truncated or summarized.
- No raw mid-sentence character truncation; either full content or an explicit summary.
- Configurable budget; backward compatible (if config missing, use a safe default e.g. 4000).
- Documentation updated (CONFIGURATION.md, simple-mode or workflow docs) for the new config and behavior.

### 2.6 Risks and mitigations

- **Risk:** Template summaries too terse and reduce quality.  
  **Mitigation:** Make template summaries at least one sentence per step and include counts (e.g. “3 user stories”); optional model summarization for Phase 2.

- **Risk:** Token estimation (chars/4) inaccurate for some languages or formats.  
  **Mitigation:** Use tiktoken when available for the model in use; fallback to chars/4 with a small safety margin (e.g. budget 0.9x when using chars/4).

---

## Option 3: Context7 Strict On-Demand Usage and Per-Agent Caps

### 3.1 Current state

- **Health:** Context7 cache reported as FAIL (65/100): hit rate 79.1% (below 80% target), response time 465 ms (target &lt;100 ms for cache hits). Remediation suggests pre-populate cache.
- **CONTEXT7_PATTERNS.md:** Documents agent-specific token limits (Architect 4000, Implementer 3000, Tester 2500) and “use specific topics”; these are guidance, not enforced in code.
- **Context7 flow:** Agent integration (`agent_integration.py`) and KB lookup (`lookup.py`); docs are fetched by library (+ optional topic). No enforced per-agent token cap when injecting docs into a prompt; no strict “topic required” at fetch time.
- **Cache:** KBCache, prewarm via init; 277 entries, 211 libraries (doctor). Cache hit rate and response time are monitored but fetch path does not enforce a cap before returning content to the agent.

### 3.2 Target state

- **Topic required (or allowlist):** Every call that fetches library docs (e.g. get_docs, lookup) must specify a topic (or use an allowlist of “full library” for rare cases). Reject or warn when topic is missing so that “whole library” fetches are rare and intentional.
- **Per-agent token cap:** When Context7 content is injected into an agent’s context (e.g. in build orchestrator’s Context7 auto-detect or in reviewer/implementer when they request docs), enforce a maximum number of tokens per agent per turn. Use CONTEXT7_PATTERNS limits (Architect 4K, Implementer 3K, Tester 2.5K) as defaults; make them configurable (e.g. `context7.per_agent_max_tokens` or per-agent in config).
- **Lazy loading:** Do not pre-inject large blocks of Context7 docs into the system prompt by default. Inject only when the agent (or the workflow step) actually requests docs (e.g. via tool/MCP call or when the step is “implementer” and Context7 integration is enabled). Pre-warm remains for cache population, not for stuffing the prompt.
- **Cache health:** Ensure init pre-populates cache for project dependencies; document and (if needed) run prewarm in health remediation so hit rate can reach >80% and response time &lt;100 ms for hits.

### 3.3 Design decisions

- **Where to enforce topic:** In the public entry points that return doc content to callers (e.g. `get_library_docs`, or the method on Context7AgentHelper that performs lookup). If topic is None and allowlist for “full library” is not set for that library, return empty or short message and log warning.
- **Where to enforce per-agent cap:** At the point where Context7 content is merged into the payload for an agent (e.g. in BuildOrchestrator’s context7_docs injection, or in the skill invoker when it attaches “library docs” to the prompt). That layer should: (1) know the current agent/step id, (2) look up max_tokens for that agent, (3) estimate tokens of the doc content, (4) truncate or select only the first N tokens before attaching. Alternatively, the Context7 helper can accept `max_tokens` and return already-capped content.
- **Config:** Add `context7.require_topic: bool` (default True), `context7.per_agent_max_tokens: { agent_id: int }` (defaults from CONTEXT7_PATTERNS), and optionally `context7.allow_full_library_libraries: [ ... ]` for exceptions.
- **Pre-warm:** Keep existing prewarm in init; add or reference `scripts/prepopulate_context7_cache.py` in health check remediation text so users can run it to improve hit rate.

### 3.4 Implementation tasks

1. **Require topic at fetch**
   - In lookup path (e.g. KBLookup or the method that calls it), if topic is None and library is not in allow_full_library list, do not call API; return empty result and log warning. Add config `require_topic` (default True) and `allow_full_library_libraries` (default [] or small list).
   - Update all call sites that fetch Context7 docs to pass a topic (or use a default topic like “overview” when that’s intended).

2. **Per-agent max_tokens**
   - Add config `context7.per_agent_max_tokens` (e.g. architect: 4000, implementer: 3000, tester: 2500, reviewer: 3000, default: 2500).
   - In the code path that injects Context7 content into an agent prompt (e.g. BuildOrchestrator’s context7_docs, or agent_integration method that returns docs for a step), accept agent_id/step_id; look up max_tokens; estimate tokens of content; truncate to max_tokens (same token estimation as Option 1/2) before returning or attaching.
   - If Context7AgentHelper returns content, add optional parameter `max_tokens` and truncate inside the helper so all callers get capped content when they pass the param.

3. **Lazy loading**
   - Review BuildOrchestrator (and any other) “auto-detect libraries and fetch Context7 documentation” logic. Ensure we do not fetch and attach docs for all detected libraries up front. Prefer: fetch only when the step is one that uses docs (e.g. implementer), and optionally fetch only when the skill actually requests docs (tool/MCP). If current design already fetches per-step, document that as “on-demand for that step”; otherwise refactor to fetch in the step’s execution path with cap applied.

4. **Pre-warm and health**
   - Ensure `tapps-agents init` (and optional `prepopulate_context7_cache.py`) runs prewarm for project deps. Update health check remediation message to: “Pre-populate cache: run `python scripts/prepopulate_context7_cache.py` (or `tapps-agents init` with cache).”
   - Optionally add a health sub-check that verifies hit rate &gt;80% after a short warm-up run, or document target in CONTEXT7_PATTERNS.

5. **Documentation**
   - Update CONTEXT7_PATTERNS.md: require topic, per-agent caps, lazy loading. Update CONFIGURATION.md with new context7 keys.

6. **Tests**
   - Unit: Fetch with topic missing and require_topic True returns empty/warning; fetch with topic returns content; content truncated to per_agent_max_tokens when passed.
   - Integration: One agent flow that uses Context7; verify response size is within cap and cache hit rate is recorded.

### 3.5 Acceptance criteria

- With `context7.require_topic` True, any fetch without a topic (and not in allowlist) does not call the API and returns empty or minimal response with warning.
- When Context7 content is injected for an agent, it is truncated to that agent’s `per_agent_max_tokens` (configurable).
- Context7 docs are not bulk pre-injected into the system prompt; they are fetched when the step/agent needs them, with cap applied.
- Health check remediation clearly suggests pre-populating cache to reach >80% hit rate.
- Config and CONTEXT7_PATTERNS.md document the new behavior and keys.

### 3.6 Risks and mitigations

- **Risk:** Requiring topic breaks existing callers that pass no topic.  
  **Mitigation:** Audit callers; add default topic “overview” or “usage” where appropriate; allowlist for known “full library” use cases; feature flag require_topic (default True) so it can be relaxed if needed.

- **Risk:** Truncating docs mid-content hurts accuracy.  
  **Mitigation:** Prefer “first N tokens” of the most relevant topic; document that agents should request specific topics to get the right slice; per-agent caps are already in CONTEXT7_PATTERNS as best practice.

---

## Cross-cutting

### Config schema (additions)

- **Option 1:** `context_intelligence` (or new `context_assembly`): `step_tier_defaults`, `step_token_budgets`, `strict_context_enabled`.
- **Option 2:** `simple_mode.artifact_context_budget_tokens`, optional `artifact_summarization_enabled`.
- **Option 3:** `context7.require_topic`, `context7.per_agent_max_tokens`, `context7.allow_full_library_libraries`.

### Token estimation

- Use one shared implementation (e.g. `tapps_agents/core/token_utils.py` or method on ContextAssemblyService): estimate_tokens(text) → int. Implementation: try tiktoken if available for the configured model, else chars/4 with optional safety factor. Used by Option 1, 2, and 3.

### Testing strategy

- Unit tests per new class/function; integration tests that run one build and one fix with strict context enabled and assert context size and (where possible) workflow completion.
- Option 3: add or extend Context7 tests for topic required and per-agent cap.

### Documentation updates

- **CONFIGURATION.md:** New keys for context_assembly, artifact_context_budget_tokens, context7 require_topic and per_agent_max_tokens.
- **Architecture / context:** Short section describing “single context path” (Option 1), “artifact budget and summarization” (Option 2), “Context7 on-demand and caps” (Option 3). Link from CONTEXT7_PATTERNS and CHECKPOINT_SYSTEM_GUIDE if relevant.
- **CONTEXT7_PATTERNS.md:** Align with enforced behavior (topic required, caps, lazy loading).

### Rollout

- Feature flags or config defaults so that new behavior can be turned on per project or globally after testing.
- Option 1: `strict_context_enabled` default False initially; switch to True after validation.
- Option 2: default `artifact_context_budget_tokens` 4000; no change to existing behavior other than token-based truncation and optional summary.
- Option 3: `require_topic` default True; ensure all in-repo callers pass topic before release.

---

## Summary table

| Item | Option 1 | Option 2 | Option 3 |
|------|----------|----------|----------|
| New modules | ContextAssemblyService, config section | ArtifactContextBuilder, token_utils (or shared) | Config + truncation in Context7 injection path |
| Touched areas | BuildOrchestrator, FixOrchestrator, CursorWorkflowExecutor, config | BuildOrchestrator._enrich_implementer_context, config | Context7 lookup, agent_integration, build Context7 injection, config, health |
| Default config | strict_context_enabled: False → True after validation | artifact_context_budget_tokens: 4000 | require_topic: True, per_agent_max_tokens from PATTERNS |
| Key acceptance | Single path, tier + budget applied | Artifact budget, priority, no raw truncation | Topic required, per-agent cap, lazy load |

This plan is intended to be implemented in order (1 → 2 → 3) with shared token estimation and config conventions across all three options.
