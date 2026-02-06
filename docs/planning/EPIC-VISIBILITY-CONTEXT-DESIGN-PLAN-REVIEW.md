# Epic Visibility and Context Design Plan — Review Summary

**Plan:** [EPIC-AND-WORKFLOW-ENHANCEMENT-DESIGN-PLAN.md](EPIC-AND-WORKFLOW-ENHANCEMENT-DESIGN-PLAN.md)  
**Reviewed:** 2026-02-05  
**Tools:** tapps-agents reviewer score, web research on best practices  
**Updated:** 2026-02-05 — Added Agent/Context Benefits audit; Phase 0 (Context and Variable Wiring); §7 Auto-Selection Matrix  
**Updated:** 2026-02-06 — §8 Claude Code CLI Integration Audit (subagents, agent teams, skills, SDK). Major gaps found. §8.7 `.claude/settings.json` gap identified and resolved (Phase 7.8 added to plan). §9 Expert System LLM Visibility gap: LLM cannot see/consult experts → Phase 8 added.  
**Updated:** 2026-02-06 — §10 Code Alignment Audit: Cross-referenced plan with code changes from other agents (Init Autofill Phases 1-3). Plan updated with Implementation Status section, tiered execution order, dependency graph, and acknowledgment of already-built infrastructure.

---

## 0. Agent and Context Benefits Audit (2026-02-05)

Review of agents, experts, and workflow steps found that **agents get full tapps-agents benefits** (ExpertSupportMixin, Context7, adaptive learning) when invoked. The issue is **input context**—what spec/state is passed into each step.

### Findings

| Path | Implementer Context Source | Epic/Story-Only Support |
|------|----------------------------|--------------------------|
| **Build orchestrator** (*build) | WorkflowDocumentationManager + ArtifactContextBuilder (spec, user_stories, architecture, api_design, token budget) | N/A |
| **Epic / WorkflowExecutor** | ImplementerHandler reads user_prompt, enhanced_prompt, architecture | Epic sets description/story_description; ImplementerHandler does NOT read them |

**Gaps addressed in plan update:**

1. Variable mismatch: Epic sets `description`/`story_description`; ImplementerHandler expects `user_prompt`/`enhanced_prompt`. For story-only, implementer gets no spec.
2. Story-only workflow: implement → review → test has no enhance/plan. Spec = story + acceptance criteria; must wire through state.
3. Full Epic workflow: Planner output (user_stories) not passed to Implementer; no Planner→Implementer output contract.

**Plan changes:** Added Phase 0 (Context and Variable Wiring) as pre-requisite; ImplementerHandler must accept description/story_description/acceptance_criteria as fallback; Epic orchestrator must set these for story-only.

---

## 1. TappsCodingAgents Reviewer Results

**File:** `docs/planning/EPIC-AND-WORKFLOW-ENHANCEMENT-DESIGN-PLAN.md`

| Metric | Score | Notes |
|--------|-------|------|
| Overall | 45.1/100 | Expected for design doc (not code) |
| Complexity | 10.0/10 | Low complexity, clear structure |
| Security | 10.0/10 | No sensitive patterns |
| Maintainability | 3.5/10 | Markdown; structure helps |
| Linting | 10.0/10 | Clean |
| Type Checking | 5.0/10 | N/A for markdown |

**Note:** The reviewer is tuned for code. The plan scored well on structure and clarity; lower maintainability/type scores are expected for design documentation.

**Plan updated (2026-02-05):** Suggestions from §3–5 folded into main plan. **Full update (2026-02-05):** Added executive summary, best practices, alternatives considered, Beads integration (§2.3), framework detection (§2.4), cleanup epic-state spec (§1.3), state concurrency strategy (run_id default). **Phase 6 and execution (2026-02-05):** Added Phase 6 (Documentation and Project Setup: init, init --reset, Cursor rules, AGENTS.md, CLAUDE.md, Skills, docs), Execution Best Practices, Validation and Review; tapps-agents reviewer run (score 45.1).

---

## 2. Best Practices (From Research)

### 2.1 Epic and Story Execution

- **Epics as containers:** Epics organize related stories; break work into smaller pieces to reduce risk and improve feedback loops ([Parallel HQ](https://www.parallelhq.com/blog/how-to-write-epic-in-agile)).
- **Topological ordering:** Execution order must respect dependencies; topological sort is the standard approach ([Harness](https://developer.harness.io/docs/release-orchestration/execution/parallel-vs-sequential-execution)).
- **Parallel when possible:** Independent stories/tasks should run in parallel; dependent work stays sequential ([TaskFlow](https://taskflow.github.io/taskflow/DependentAsyncTasking.html)).

### 2.2 Workflow State Persistence

- **JSON serialization:** State should be JSON-serializable for persistence and resume ([Pipedream](https://pipedream.com/docs/v1/workflows/steps/code/state), [UseWorkflow](https://useworkflow.dev/docs/foundations/serialization)).
- **Checkpoints at phase boundaries:** Capture state at end of each major phase (e.g. after each story) ([Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/checkpointing-and-resuming)).
- **Snapshot content:** Include step outputs, execution path, retry attempts, suspension/resumption metadata for exact resume ([Mastra](https://mastra.ai/en/reference/workflows/snapshots)).
- **Concurrency:** Be aware of race conditions when multiple workflow instances run; last writer wins or use locking ([Pipedream](https://pipedream.com/docs/v1/workflows/steps/code/state)).
- **Minimal state:** Store only essential data; prefer simple, immutable structures ([UseWorkflow](https://useworkflow.dev/docs/foundations/serialization)).

### 2.3 Session/Context Handoff

- **Handoffs as delegation:** In multi-agent systems, handoffs pass context to specialized agents ([LangChain](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs), [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/handoffs/)).
- **Context filtering:** Use input filters to control what history/context is passed; avoid passing entire conversation when not needed ([OpenAI Agents SDK](https://openai.github.io/openai-agents-python/handoffs/)).
- **Explicit handoff inputs:** Define what data the next agent needs (e.g. prior work summary, next story ID) ([OpenAI Agents SDK](https://openai.github.io/openai-agents-python/handoffs/)).

### 2.4 Wave-Based Parallel Execution

- **Wavefront pattern:** Tasks with no mutual dependencies form a wave and run in parallel; next wave starts when its dependencies complete ([TaskFlow](https://taskflow.github.io/taskflow/wavefront.html)).
- **Bounded concurrency:** Limit parallel execution (e.g. `max_parallel_stories: 3`) to avoid resource exhaustion.

---

## 3. Suggested Improvements to the Plan

### 3.1 Epic State Schema

**Current:** Single JSON file with stories array.

**Improvement:** Add version field and checksum for epic content to detect when the Epic .md has changed since state was saved.

```json
{
  "schema_version": 1,
  "epic_content_checksum": "sha256:...",
  "epic_id": "epic-51",
  ...
}
```

**Rationale:** On resume, if the Epic file changed, the plan should warn or require re-parse; stale state can cause wrong behavior.

### 3.2 State Concurrency

**Current:** Plan does not address concurrent Epic runs.

**Improvement:** Add guidance:

- Use `epic_id` + `run_id` (e.g. timestamp) in state path to avoid overwriting when multiple runs exist.
- Or: Use file locking (e.g. `fcntl` on Unix, `msvcrt` on Windows) when writing epic-state to prevent concurrent writers.

**Rationale:** Aligns with persistence best practices and avoids race conditions.

### 3.3 Checkpoint Content

**Current:** State stores `story_id`, `status`, `completed_at`, `artifacts`, `quality_scores`.

**Improvement:** Extend state to support resume:

- `workflow_id` or `workflow_state_path` for the last running story (if interrupted mid-story).
- `retry_count` per story for quality loopback tracking.

**Rationale:** Enables exact resume from a partially completed story, not just from last fully completed story.

### 3.4 Epic Memory — Summary Generation

**Current:** Plan says "append summary" but does not specify how the summary is produced.

**Improvement:** Define summary source:

- **Option A:** Template-based extraction from story result (files_changed, quality_scores).
- **Option B:** Optional LLM call to generate one-paragraph summary (adds cost).
- **Option C:** Use existing `ArtifactContextBuilder` summarization when enabled.

**Recommendation:** Start with Option A (no LLM); add Option B as opt-in.

### 3.5 Session Handoff Triggers

**Current:** "On Epic pause (Ctrl+C), SessionEnd hook, or explicit epic pause."

**Improvement:** Integrate with existing hooks:

- Add `EpicPaused` or `EpicStoryComplete` to [HOOKS_GUIDE.md](../HOOKS_GUIDE.md) event list.
- SessionEnd hook can call `EpicStateManager.write_handoff()` when an Epic run is in progress.
- Document that `--auto` / CI runs skip handoff (no interactive session).

**Rationale:** Reuses existing hook infrastructure instead of custom signal handling.

### 3.6 Parallel Execution — File Overlap Detection

**Current:** "Document that stories should touch different files; optional strict mode (future)."

**Improvement:** Add Phase 3.1 — lightweight overlap check:

- Before parallel wave: collect `files` (or inferred targets) from each story in the wave.
- If overlap detected: log warning and optionally fall back to sequential for that wave.
- Config: `epic.detect_file_overlap: true` (default); `epic.strict_parallel: false` (warn only, don't force sequential).

**Rationale:** Reduces risk of merge conflicts and overwrites without blocking parallel execution.

---

## 4. Alternatives Considered

### 4.1 Epic State: Single File vs. Per-Story Files

| Approach | Pros | Cons |
|----------|------|------|
| **Single JSON** (current plan) | Simple, atomic updates, easy to load | Large files for big Epics; merge conflicts if edited while running |
| **Per-story files** | Fine-grained; easier parallel writes | More files; need aggregation for status | 
| **SQLite** | ACID, queries, concurrent access | New dependency; overkill for single-project use |

**Recommendation:** Keep single JSON for Phase 1; consider per-story files only if concurrency becomes an issue.

### 4.2 Epic Memory: JSONL vs. Single JSON Array

| Approach | Pros | Cons |
|----------|------|------|
| **JSONL** (current plan) | Append-only; efficient for streaming; no re-parse of full history | Need to read last K lines |
| **Single JSON array** | One read; easy to slice last K | Rewrite whole file on append; risk of corruption on interrupt |

**Recommendation:** JSONL is preferable for append-only, crash-safe writes.

### 4.3 Approval: Flag vs. Prompt vs. Explicit Step

| Approach | Pros | Cons |
|----------|------|------|
| **--approved flag** | Unblocks CI/automation | No guard for accidental runs |
| **Prompt (y/n)** | Good for interactive use | Blocks automation; needs `--yes` or similar |
| **Explicit approve** | Clear audit trail; separates approval from execution | Extra step; possible drift if Epic changes after approve |

**Recommendation:** Support both: `--approved` / `--no-approval` for automation; default interactive prompt when not `--auto`. Add `epic approve` as optional for explicit audit.

### 4.4 Story-Only Workflow: Default or Opt-In

| Approach | Pros | Cons |
|----------|------|------|
| **Story-only default** | Aligns with "Epic = planning"; faster runs | May surprise users expecting full pipeline |
| **Full default, --story-only flag** | Backward compatible | Redundant planning per story |
| **Config-driven** | Flexible | More options to document |

**Recommendation:** Default to story-only for Epic execution (planning is in Epic). Add `--full` flag for users who want enhance/plan per story. Config: `epic.story_workflow_mode: "story-only"` (default).

---

## 5. Open Questions Resolved (Recommendations)

| Question | Recommendation |
|----------|----------------|
| Story-only default? | Yes, default to story-only for Epic. |
| Approval UX? | Both: `--approved` for automation; interactive prompt when not `--auto`. |
| Parallel default? | `max_parallel_stories: 3`. |
| Epic state cleanup? | Add `tapps-agents cleanup epic-state` (or extend `cleanup`) with `--retention-days 30`, `--remove-completed`. Run via cleanup workflow or manual. |

---

## 6. Summary

The plan is well-structured and matches agile and workflow best practices. Main refinements:

1. **State:** Add schema version and epic checksum; clarify concurrency and locking.
2. **Resume:** Extend state to support mid-story resume (workflow_id, retry_count).
3. **Epic memory:** Specify template-based summary first; optional LLM later.
4. **Hooks:** Integrate handoff with existing SessionEnd and Epic events.
5. **Parallel:** Add lightweight file-overlap detection with warn-only default.
6. **Defaults:** Story-only default; `--approved` + interactive prompt; `max_parallel_stories: 3`.

These changes should be folded into the main plan before implementation.

---

## 7. Auto-Selection Matrix: Workflow/Option Selection Based on Prompt

TappsCodingAgents has several mechanisms that auto-select workflows or options from prompts. Below: what exists, what each covers, and what is missing.

### 7.1 Matrix: Present vs. Missing

| Capability | Component | Trigger | What It Auto-Selects | Status |
|------------|-----------|---------|----------------------|--------|
| Intent from natural language | `IntentParser` | User types plain text (no `@simple-mode`) | IntentType → BUILD, FIX, REVIEW, TEST, REFACTOR, EPIC, etc. | ✅ Present |
| Proactive workflow suggestion | `WorkflowSuggester` | User about to do direct edits (no @simple-mode) | Suggests `@simple-mode *build`, `*fix`, `*review`, etc. | ✅ Present |
| Workflow mismatch validation | `validate_workflow_match` | User specifies `*full`/`*build`/`*fix` and runs | Warns if task doesn't match workflow; recommends switch | ✅ Present |
| Semantic intent (bug vs feature vs arch) | `detect_primary_intent` | Mismatch validation, checkpoints | bug_fix, enhancement, architectural | ✅ Present |
| Build preset (minimal/standard/comprehensive) | `suggest_build_preset` | Build workflow, automation | minimal \| standard \| comprehensive | ✅ Present |
| Preset from complexity/risk | `PresetRecommender` | `workflow recommend` (CLI) | minimal \| standard \| comprehensive \| full-sdlc | ✅ Present |
| Prompt analysis (intent, complexity, existing code) | `PromptAnalyzer` | Before orchestrator execute | recommended_workflow (build/validate), enhancement (full/quick), preset | ✅ Present |
| Checkpoint workflow switch | BuildOrchestrator checkpoints | After enhance, after plan, after test | Recommend *fix, *build, or continue; user confirms | ✅ Present |
| Framework vs user code detection | `PresetRecommender._is_framework_change` | Preset recommend | full-sdlc when `tapps_agents/` in path | ✅ Present |
| **Explicit `*build` / `*fix` / `*full` parsing** | `IntentParser` | User types `@simple-mode *build "..."` | N/A — falls through to keyword scoring | ❌ Missing |
| **Auto-select workflow when user gives only a prompt** | — | User: "Add user auth" (no workflow) | Auto-pick *build vs *fix vs *full without suggestion UI | ❌ Missing |
| **Unified intent taxonomy** | — | All analyzers | IntentParser vs detect_primary_intent vs PromptAnalyzer use different enums | ❌ Missing |
| **Epic/story workflow selection** | Epic orchestrator | Epic execution | Story-only vs full per-story not driven by prompt analysis | ❌ Missing |
| **Validate vs Build from "compare to existing"** | `PromptAnalyzer` | Has existing code refs | recommended_workflow=validate; not wired into IntentParser routing | ⚠️ Partial |

### 7.2 Gaps Summary

1. **Explicit command parsing**: `IntentParser` has explicit patterns for `*epic`, `*explore`, `*validate`, `*refactor`, `*plan`, `*pr`, `*brownfield`, `*enhance`, `*breakdown`, `*todo` but **not** for `*build`, `*fix`, `*full`, `*review`, `*test`. Those rely on keyword scoring, so `*build "Fix the bug"` can be mis-scored.
2. **Proactive vs reactive**: `WorkflowSuggester` suggests a workflow when the user *hasn’t* used @simple-mode; it does **not** auto-select and run. User must accept the suggestion.
3. **Intent taxonomy split**: `IntentParser` uses `IntentType`, `detect_primary_intent` uses bug_fix/enhancement/architectural, `PromptAnalyzer` uses `TaskIntent` (build/validate/fix/…). No single taxonomy.
4. **Validate workflow wiring**: `PromptAnalyzer` can recommend `validate` when "compare to existing" is present, but routing still uses `IntentParser`; validate is not consistently applied.

---

## 8. Claude Code CLI Integration Audit (2026-02-06)

Deep review of Claude Code's latest features ([subagents](https://code.claude.com/docs/en/sub-agents), [agent teams](https://code.claude.com/docs/en/agent-teams), [skills enhancements](https://code.claude.com/docs/en/skills), [Agent SDK / headless](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference)) against the current plan. **Multiple high-value gaps found** that would significantly improve Epic execution, parallel story running, context management, and CI/CD automation.

### 8.1 Current TappsCodingAgents vs Claude Code Feature Matrix

| Claude Code Feature | TappsCodingAgents Status | Plan Coverage | Priority |
|---------------------|--------------------------|---------------|----------|
| **Custom Subagents** (`.claude/agents/`) | **Not used** — only `.claude/skills/` (22 skills, 0 agents) | **Not in plan** | **HIGH** |
| **Agent Teams** (parallel sessions, shared tasks, messaging) | **Not used** — Phase 3 uses asyncio only | **Not in plan** | **HIGH** |
| **Persistent Memory** (`memory: user/project/local`) | **Not used** — Phase 4 reinvents with custom JSONL | **Partial** | **HIGH** |
| **Agent SDK / Headless** (`claude -p`, `--output-format json`, `--continue`) | **Not used** — docs say "No Skills, manual workflow" for CLI | **Not in plan** | **HIGH** |
| **`context: fork`** (skill isolation in subagent context) | **Not used** — skills run inline | **Not in plan** | **MEDIUM** |
| **Skill hooks** (lifecycle hooks per skill) | **Not used** — hooks only at project level | **Not in plan** | **MEDIUM** |
| **`--agents` CLI flag** (dynamic subagents via JSON) | **Not used** | **Not in plan** | **MEDIUM** |
| **Model selection per subagent** (haiku/sonnet/opus) | **Not used** — all agents same model | **Not in plan** | **MEDIUM** |
| **`!`command``** dynamic context injection | **Not used** | **Not in plan** | **LOW** |
| **`--max-budget-usd`** cost control | **Not used** | **Not in plan** | **LOW** |
| **`--json-schema`** validated structured output | **Not used** | **Not in plan** | **LOW** |
| **Plugins** (distributable skill + agent + hook bundles) | **Not used** | **Not in plan** | **FUTURE** |
| **`.claude/settings.json`** (project-level permissions, env, hooks, MCP) | **Not created by init** — only skills/commands | **Not in original plan** → **Added Phase 7.8** | **HIGH** |

### 8.2 HIGH Priority Gaps

#### Gap 1: Custom Subagents (`.claude/agents/`) — Not in Plan

**What Claude Code provides:** `.claude/agents/` directory with YAML frontmatter + markdown per agent. Each subagent gets: own context window, custom system prompt, tool restrictions, permission modes, persistent memory, model selection, lifecycle hooks, and skill preloading.

**TappsCodingAgents state:** Zero `.claude/agents/`. All 22 skills run in main context (no isolation). No cross-session learning. No model routing.

**Recommended subagents:**

| Subagent | Purpose | Model | Memory | Tools |
|----------|---------|-------|--------|-------|
| `epic-orchestrator` | Coordinate Epic story execution | inherit | project | All |
| `story-executor` | Execute individual stories (isolated context) | sonnet | project | All |
| `code-reviewer` | Review with persistent pattern memory | sonnet | project | Read, Grep, Glob, Bash |
| `researcher` | Fast codebase exploration (read-only) | haiku | none | Read, Grep, Glob |
| `debugger-agent` | Root cause analysis with debugging memory | sonnet | project | All |

**Plan impact:** Phase 6 (init): create `.claude/agents/` and install subagents; init --reset: preserve custom agents. Phase 4: leverage `memory: project` alongside JSONL. Phase 3: subagents provide natural story isolation.

#### Gap 2: Agent Teams for Epic Parallel Execution — Not in Plan

**What Claude Code provides:** Multiple sessions coordinated as a team. Team lead assigns tasks; teammates work independently with own context windows; shared task list with dependency tracking; inter-agent messaging; background execution (Ctrl+B); file-locked task claiming.

**Epic mapping:**

| Agent Team Concept | Epic Equivalent |
|--------------------|-----------------|
| Team lead | EpicOrchestrator session |
| Teammates | Story executor sessions |
| Shared task list | Epic stories (from .md) |
| Task dependencies | Story dependencies (topological order) |
| Task states | Story states (pending/running/done/failed) |
| Inter-agent messaging | Cross-story context (Epic memory) |

**Plan impact:** Phase 3 should offer Agent Teams as **primary** strategy for Claude Code CLI users. asyncio remains for Cursor / non-Claude-Code. Solves the **context window problem** — each story gets its own full context window. **Note:** Experimental flag required (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

**Recommended config:** `epic.parallel_strategy: "agent-teams" | "asyncio" | "sequential"` (default: sequential; auto-detect Claude Code availability).

#### Gap 3: Agent SDK / Headless Execution — Not in Plan

**What Claude Code provides:**
- `claude -p "query"` — non-interactive execution
- `--output-format json` — structured output with session ID
- `--json-schema` — validated structured output
- `--continue` / `--resume` — conversation continuation
- `--allowedTools` — auto-approve tools without prompting
- `--max-turns` / `--max-budget-usd` — limit execution and cost
- `--append-system-prompt` — add instructions to defaults
- `--agents` — dynamic subagent definitions via JSON
- Python and TypeScript SDK packages

**What this enables:**
- CI/CD Epic execution: `claude -p "Execute epic epic-51.md" --allowedTools "Bash,Read,Edit" --output-format json`
- Scripted story execution: each story as `claude -p` with `--continue`
- Cost-controlled runs: `--max-budget-usd 10.00`
- Structured results: `--json-schema` for story completion reports

**Plan impact:** New section for CI/CD integration; document `claude -p` usage for Epic runs; consider `tapps-agents epic run --claude-sdk` command.

#### Gap 4: Persistent Memory — Plan Partially Covers

Claude Code provides `memory: project` → `.claude/agent-memory/<name>/` with auto-curated `MEMORY.md` (first 200 lines injected into subagent context). Cross-session, automatic. The plan builds custom JSONL instead.

**Recommendation:** When Claude Code CLI is available, use native persistent memory for subagents. Keep JSONL as fallback for non-Claude-Code environments. Both serve different purposes: Epic memory = per-run context; persistent memory = cross-run learning.

### 8.3 MEDIUM Priority Gaps

| Gap | Feature | Value | Recommendation |
|-----|---------|-------|----------------|
| `context: fork` | Skills run in isolated subagent context | Story isolation, avoid main context pollution | Update selected skills; document pattern |
| Model routing | haiku (research), sonnet (impl), opus (architecture) | Cost optimization, speed for exploration | Add `model` to agent config and subagent defs |
| `--agents` JSON | Dynamic subagent definitions at session start | CI/CD portability, zero-install agents | `tapps-agents epic run --generate-agents-json` |
| Skill hooks | PreToolUse, PostToolUse, Stop per skill | Auto-Beads sync, quality enforcement | Add hooks to story-related skills |
| `tool-integrations.md` update | Docs say "No Skills, manual workflow" for CLI | **Inaccurate** — Claude CLI now has skills, subagents, teams | Must fix in Phase 6 |
| `.claude/settings.json` missing | No project-level settings for Claude Code users | Permissions, env vars, MCP approval not auto-configured | Create in init; add to doctor |

### 8.4 Recommended Plan Additions (Priority-Ordered)

| # | Enhancement | Where in Plan | Impact | Effort |
|---|-------------|---------------|--------|--------|
| 0 | **`.claude/settings.json` auto-configuration** | Phase 7.8 (new) | HIGH | Low |
| 1 | **`.claude/agents/` with framework subagents** | Phase 7.1 | HIGH | Medium |
| 2 | **Agent Teams as parallel strategy** | Phase 7.2 | HIGH | Medium |
| 3 | **Agent SDK / Headless integration** | Phase 7.3 | HIGH | Medium |
| 4 | **Persistent memory for subagents** | Phase 7.4 | HIGH | Low |
| 5 | **Model routing per agent** | Extend Phase 6 | MEDIUM | Low |
| 6 | **`context: fork` for skills** | Extend Phase 6 | MEDIUM | Low |
| 7 | **Skill hooks for Beads/quality** | Extend Phase 2.3 | MEDIUM | Low |
| 8 | **`--agents` JSON generation** | Extend Phase 3/8 | MEDIUM | Low |
| 9 | **Fix `tool-integrations.md`** | Phase 6 | MEDIUM | Low |

### 8.5 Architecture Vision: With Claude Code Integration

```
Current (Plan as-is):
  Epic.md → EpicOrchestrator → asyncio waves → story workflows → results
  (single process, shared context, JSONL memory)

Enhanced (with Claude Code):
  Epic.md → EpicOrchestrator (team lead)
    ├─ Teammate: story-executor (story 1, own context, memory: project)
    ├─ Teammate: story-executor (story 2, own context, memory: project)
    ├─ Teammate: story-executor (story 3, own context, memory: project)
    └─ Shared task list: Epic stories with dependencies
  
  Each teammate:
    Model: sonnet (impl) or haiku (research)
    Memory: project (persistent learning)
    Skills: implementer, reviewer, tester preloaded
    Hooks: Beads sync, quality gates
    Context: isolated (own context window)
  
  CI/CD:
    claude -p "Execute epic epic-51.md" \
      --agents '{"story-executor": {...}}' \
      --allowedTools "Bash,Read,Edit" \
      --output-format json --max-budget-usd 20.00
```

### 8.6 `tool-integrations.md` Documentation Gap

Current `docs/tool-integrations.md` states: "Claude Code CLI Limitations: No Cursor Skills, manual workflow steps, less integrated experience."

**This is outdated.** Claude Code CLI now supports: Skills (`.claude/skills/` + `.claude/commands/`), Subagents (`.claude/agents/`), Agent Teams (parallel execution), Persistent Memory, `context: fork`, Agent SDK (headless execution). **Claude Code CLI is now MORE capable than Cursor for multi-agent workflows.** Must fix in Phase 6.

### 8.7 Claude Code Settings Gap (`.claude/settings.json`)

**Critical finding**: `tapps-agents init` creates `.claude/skills/` and `.claude/commands/` but does **not** create `.claude/settings.json`. This means:

- **No project-level permissions** — Claude Code users must manually approve every tool use
- **No environment variables** — `TAPPS_AGENTS_MODE`, `CONTEXT7_KB_CACHE` not set automatically
- **No MCP auto-approval** — Context7 MCP server requires manual approval each session
- **No .gitignore entries** — `settings.local.json`, `agent-memory/` not excluded from git
- **No doctor checks** — `tapps-agents doctor` doesn't validate Claude Code settings

**Resolution**: Added **Phase 7.8** to the main plan covering:
1. `.claude/settings.json` created by `init` with permissions, env, MCP approval
2. `.claude/settings.local.json.example` template (API keys, agent teams flag)
3. Detection of Claude Code CLI availability (`which claude`)
4. `init --reset` preserves `settings.json` (user data) but resets template
5. `doctor` validates Claude Code settings health
6. `.gitignore` updated for local Claude Code files

### 8.8 Summary

The plan is solid for internal framework improvements (Phases 0–6). It **misses the most impactful Claude Code features** that would:

1. **Solve the context window problem** — Agent Teams give each story its own context
2. **Enable true parallel execution** — Teammates work independently
3. **Add persistent learning** — Subagent memory survives across sessions
4. **Unlock CI/CD automation** — Agent SDK enables headless Epic execution
5. **Optimize cost/speed** — Model routing (haiku for research, sonnet for impl)
6. **Zero-config Claude Code setup** — Settings auto-configured by `init` (Phase 7.8)

**Recommendation:** Add **Phase 7: Claude Code Integration** (settings, subagents, agent teams, persistent memory, SDK). This should be **optional and additive** — Phases 0–6 work without Claude Code. Phase 7 enhances when Claude Code CLI is available. **Phase 7.8 (settings) should be implemented first** as it provides immediate value to all Claude Code users.

---

## 9. Expert System LLM Visibility Gap (2026-02-06)

### Problem

The expert system (16 built-in + project-specific experts, RAG knowledge bases, Context7 cache) is **entirely invisible to the LLM**. When other projects use `tapps-agents init`, nothing tells the LLM what experts exist, what domains they cover, or how to consult them.

**Current flow**: Expert consultation happens automatically inside Python code (`ExpertSupportMixin._consult_expert()`). The LLM never explicitly requests it, doesn't know it happened, and can't trigger it for a specific domain.

**Impact**: Projects using tapps-agents don't get full value from expert knowledge because the LLM can't proactively leverage it.

### What the LLM CAN see today

| Access Method | What it provides | Limitation |
|---|---|---|
| `AGENTS.md` | One line: "Expert system with built-in technical domains" | No details, no list, no commands |
| `@enhancer` SKILL.md | Mentions auto-consulting experts during enhancement | Only enhancer, not other agents |
| `@reviewer *docs <library>` | Library docs from Context7 cache | Only library docs, not expert domain knowledge |
| `tapps-agents setup-experts list` | CLI: list configured experts | CLI only — LLM cannot invoke this |

### What the LLM CANNOT do today

- List available experts
- Consult a specific expert ("What does security expert say about JWT?")
- Browse expert knowledge bases
- Know which experts are relevant for current task
- Access Context7 cache inventory

### Resolution: Phase 8 Added to Plan

1. **Auto-generated `experts-available.mdc` rule** — `init` generates a Cursor Rule listing all experts, domains, triggers, and cached libraries. LLM always sees this.
2. **New `@expert` Cursor Skill** — `*list`, `*consult`, `*info`, `*search`, `*cached` commands
3. **New `tapps-agents expert` CLI group** — `list|consult|info|search|cached` subcommands
4. **All agent skills updated** — Each SKILL.md documents expert integration availability
5. **`init`/`init --reset` regenerates** the expert discovery rule when experts change

---

## 10. Code Alignment Audit (2026-02-06)

Cross-referenced the design plan against code changes made by other agents running in parallel.

### Findings

**Init Autofill system built (parallel initiative):** Other agents implemented a complete Init Autofill system (their Phases 1-3) that overlaps with and provides infrastructure for our plan Phases 6 and 8.

| Built Module | Our Plan Phase | Alignment |
|-------------|---------------|-----------|
| ConfigValidator | Phase 6 (init validation) | Aligned — reduces Phase 6 work |
| TechStackDetector | Phase 6.1 (init) | Aligned — integrated into init_project.py |
| Context7CacheManager | Phase 8.5 (expert cached) | Aligned — Phase 8 can leverage |
| ExpertGenerator | Phase 8 (expert infrastructure) | Aligned — Phase 8 builds on top |
| ExpertKnowledgeLinker | Phase 8 (expert infrastructure) | Aligned — not yet integrated into init |
| setup-experts CLI | Phase 8.3 (partial) | Partial overlap — manages expert CRUD; Phase 8 adds consultation |
| ExpertConfig | Phase 8 (expert infrastructure) | Aligned — confidence thresholds ready |
| RAG sync + CLI | New (not in plan) | Additive — knowledge sync when code changes |
| ProjectOverviewGenerator | New (not in plan) | Additive — project overview with architecture detection |
| Progress Display | New (not in plan) | Additive — phase-grid workflow progress |

### Config Gaps Confirmed

- No `epic.*` config section yet — expected (Phases 1-3 not started)
- No `claude_code.*` config section yet — expected (Phase 7 not started)
- `ExpertConfig` class exists with confidence thresholds — ready for Phase 8

### Execution Order Issues Found and Fixed

1. **Phase 6 was flat** — now tiered (Tier 4) with clear "already done" vs. "remaining" split
2. **Phase 8 infrastructure exists** — execution order now shows Phase 8 as Tier 5 (builds on existing modules)
3. **Dependency graph added** — explicit arrows showing which phases block which
4. **Tiered execution** — 7 tiers from "Must-Have" (Tier 1) to "Optional" (Tier 7)

### Plan Updates Made

1. Added **Implementation Status** section documenting what's built vs. not built
2. Updated **Phase 6** to reference init_autofill as "already done"
3. Updated **Phase 8** to acknowledge existing ExpertGenerator/Linker/CacheManager infrastructure
4. Updated **Phase 8.3** to clarify relationship between `setup-experts` (CRUD) and `expert` (consultation)
5. Updated **File Changes Summary** with "Already Built" and "Remaining" tables
6. Replaced flat Implementation Order with **tiered execution order** + dependency graph
7. Updated **Execution Best Practices** to reference existing modules and 130+ test suite
