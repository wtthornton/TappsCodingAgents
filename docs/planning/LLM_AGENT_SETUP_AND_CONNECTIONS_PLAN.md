# Plan: LLM Agent Setup, Connections, and Best Application for Coding Agents

**Status:** Plan  
**Created:** 2026-02-07  
**Purpose:** Align TappsCodingAgents with 2026 Cursor and 2025 Claude setups, make AGENTS.md the central artifact, and wire tech-stack, docs, and auto-create/update so the framework is the best single application to support LLM coding agents.

---

## 1. Research Summary: Cursor 2026 vs Claude 2025 vs AGENTS.md

### 1.1 Cursor (2026)

- **Rules:** `.cursor/rules/*.mdc` — Markdown + YAML frontmatter (`description`, `globs`, `alwaysApply`). Version-controlled, project-scoped. Applied by glob, always, or @-mention.
- **Skills:** Specialized capabilities (e.g. TappsCodingAgents’ 14 agents + simple-mode). Invoked via `@skill-name *command`.
- **Commands:** Slash/command palette. Often back skills or workflows.
- **Ignore:** `.cursorignore` — like .gitignore for indexing and context.
- **MCP:** `.cursor/mcp.json` — Model Context Protocol servers (e.g. Context7).
- **No single “root context file”** — rules are the primary context; multiple .mdc files by domain. Best practice: `.cursor/rules/` with core, architecture, testing, security, etc.

### 1.2 Claude Code (2025)

- **CLAUDE.md:** Project root (and `~/.claude/CLAUDE.md`, module-level). **Auto-loaded** as project memory. Hierarchy: project → user → module. Contains project overview, structure, commands, style, workflows.
- **Init:** `/init` can generate CLAUDE.md from project analysis.
- **Project settings:** `.claude/` (e.g. settings, commands). Commands in `.claude/commands/` as slash commands.
- **Single primary file:** One CLAUDE.md per scope is the “brain” for that scope.

### 1.3 AGENTS.md (Open Standard)

- **Purpose:** Tool-agnostic “README for agents” at repo root. One file, many tools (Cursor, Copilot, Aider, Gemini CLI, etc.). 60k+ projects.
- **Content:** Setup commands, testing, structure, code style, git/PR workflow, boundaries. No required schema.
- **Alignment:** Can serve as **single source of truth**; Cursor-specific context lives in `.cursor/rules/`; Claude-specific in CLAUDE.md. Best practice: **AGENTS.md = canonical agent context**; Cursor rules and CLAUDE.md can reference or duplicate key points.

### 1.4 How They Align

| Concern            | Cursor 2026      | Claude 2025      | AGENTS.md     |
|--------------------|------------------|------------------|---------------|
| Primary context   | .cursor/rules/*.mdc | CLAUDE.md      | AGENTS.md (root) |
| Tool-specific     | Rules, Skills, Commands | CLAUDE.md, .claude/ | —             |
| Cross-tool        | —                | —                | AGENTS.md     |
| Commands          | .cursor/commands/ | .claude/commands/ | Section in AGENTS.md |
| Ignore            | .cursorignore    | permissions/settings | —             |

**Recommended alignment for TappsCodingAgents:**

- **AGENTS.md** = central, tool-agnostic entry point (created/overwritten by init).
- **Cursor:** `.cursor/rules/` and Skills extend with TappsCodingAgents workflows; one rule (e.g. `project-context.mdc` or a new rule) says “Read AGENTS.md first; then use these rules and skills.”
- **Claude:** Optional **CLAUDE.md** created by init that either (a) says “Primary project context: see AGENTS.md” and includes a short summary, or (b) is a symlink/copy of AGENTS.md so Claude Code auto-loads the same content. Keeps one source of truth (AGENTS.md).

---

## 2. Current TappsCodingAgents Setup (What Init Creates)

| Artifact | Purpose | Source | When Created/Updated |
|----------|---------|--------|----------------------|
| AGENTS.md | Agent context (open format) | AGENTS.md.template + tech_stack placeholders | Init (if missing or --reset-agents-md); not in framework_files |
| .cursor/rules/*.mdc | Cursor rules | Packaged resources | Init / init --reset (framework rules) |
| project-context.mdc | Project context rule | Packaged (framework/self-host content) | Init (same file for all projects) |
| .claude/skills/ | Cursor Skills | Packaged | Init / init --reset |
| .cursor/commands/ | Cursor slash commands | Packaged | Init / init --reset |
| .tapps-agents/config.yaml | Config | default + project-type + tech-stack templates | Init (merge); preserved on reset |
| .tapps-agents/tech-stack.yaml | Detected stack + expert priorities | detect_tech_stack_enhanced | Init; updated on each init (merge) |
| .tapps-agents/experts.yaml | Experts config | Scaffold stub + optional auto from knowledge | Init; auto_experts can add |
| .tapps-agents/knowledge/ | Knowledge base | README + optional general/ | Init (scaffold) |
| workflows/presets/*.yaml | Workflow presets | Packaged | Init / init --reset |
| .cursorignore | Ignore patterns | Packaged + append | Init (create/merge) |
| .cursor/mcp.json | MCP config | Packaged (e.g. Context7) | Init (merge); reset if --reset-mcp |
| CLAUDE.md | Claude Code context | Not created by init | — |

**Gaps:**

1. **AGENTS.md** is optional (flags) and not reset; not positioned as central.
2. **project-context.mdc** is framework/self-host specific; user projects get “TappsCodingAgents framework” context instead of “your project + AGENTS.md.”
3. **Claude** has no CLAUDE.md from init; Claude Code users don’t get a single auto-loaded context unless they add it.
4. **Tech-stack** drives config and AGENTS.md placeholders but is not clearly summarized in AGENTS.md or in a single “project overview” rule for Cursor.
5. **Auto-update** semantics are unclear: what is “create once,” “overwrite on init,” “merge on init,” “refresh on demand.”

---

## 3. Target: AGENTS.md as Central Hub

### 3.1 Single Source of Truth

- **AGENTS.md** is the **canonical** agent-facing document:
  - Created/overwritten on every init and on init --reset (framework-managed).
  - First or prominent in “What it installs” and in docs.
  - Template includes: “Read this first. For TappsCodingAgents: see `.cursor/rules/`, `.tapps-agents/config.yaml`, and `tapps-agents --help`.”
- **Cursor:** Rules and Skills **reference** AGENTS.md (e.g. project-context or a dedicated rule: “Before using TappsCodingAgents workflows, read project root AGENTS.md for setup and boundaries.”).
- **Claude:** Init can create **CLAUDE.md** that:
  - Option A: Contains “Primary context: AGENTS.md” and a one-paragraph project summary + link to AGENTS.md.
  - Option B: Is generated from the same template as AGENTS.md (or a short Claude-specific wrapper that includes AGENTS.md content). Keeps one logical source; both files can be generated from the same template so they stay in sync.

### 3.2 Tech-Stack and Other Docs Flow

- **Detection:** `detect_tech_stack_enhanced` → `tech_stack` dict + `.tapps-agents/tech-stack.yaml` (and optionally `tech-stack.yaml` in project root if desired; currently only under .tapps-agents).
- **Config:** `init_project_config(tech_stack=...)` applies project-type and tech-stack templates to `.tapps-agents/config.yaml`.
- **AGENTS.md:** `init_agents_md(project_root, tech_stack=...)` fills INSTALL_CMD, TEST_CMD, LINT_CMD, PROJECT_NAME from tech_stack (and project name).
- **Optional:** Add a “Tech stack” section to AGENTS.md template (e.g. “Detected: Python, pytest, FastAPI”) populated from tech_stack so agents see it in one place.
- **Experts/knowledge:** `.tapps-agents/experts.yaml` and `.tapps-agents/knowledge/` are for TappsCodingAgents experts; AGENTS.md can say “Domain experts and knowledge: see `.tapps-agents/` and `tapps-agents expert`.”

### 3.3 Create vs Update Matrix (Target)

| Artifact | First init | Later init | init --reset |
|----------|------------|------------|--------------|
| AGENTS.md | Create from template | Overwrite from template | Delete + recreate from template |
| .cursor/rules/*.mdc | Copy framework rules | Skip if present (or reset) | Delete framework rules + copy |
| project-context.mdc | Copy (see 4.2) | — | Reset |
| .claude/skills/ | Copy | Skip or overwrite per policy | Reset |
| .tapps-agents/config.yaml | Create + templates | Merge / no overwrite | Preserve (user data) |
| .tapps-agents/tech-stack.yaml | Create from detection | Merge (preserve overrides) | Preserve |
| .tapps-agents/experts.yaml | Scaffold | Preserve | Preserve |
| .tapps-agents/knowledge/ | Scaffold | Preserve | Preserve |
| workflows/presets/*.yaml | Copy | — | Reset |
| .cursorignore | Create or merge | Merge | Reset (framework patterns) |
| CLAUDE.md (optional) | Create from AGENTS.md or ref | Overwrite or skip | Optional: reset if we manage it |

---

## 4. Detailed Plan: Fixes and Layout

### 4.1 AGENTS.md Central (No Special Flags)

- Implement **AGENTS_MD_CENTRAL_PLAN.md** in full:
  - Add AGENTS.md to `identify_framework_files()` so init --reset deletes and recreates it.
  - Always call `init_agents_md(project_root, tech_stack=...)` (always overwrite from template).
  - Remove `--no-agents-md` and `--reset-agents-md`.
  - In init output and command-reference, list AGENTS.md first under “What it installs.”
  - In AGENTS.md.template, add “Read this first” and explicit pointers to `.cursor/rules/`, `.tapps-agents/`, and `tapps-agents`.

### 4.2 project-context.mdc for User vs Framework

- **Problem:** Packaged `project-context.mdc` is written for TappsCodingAgents (framework + self-host). User projects get the wrong context.
- **Options:**
  - **A (recommended):** Ship two variants: `project-context.mdc` (framework: current content) and `project-context-user.mdc` (generic: “Read AGENTS.md; use .cursor/rules and tapps-agents; customize AGENTS.md and experts.”). Init chooses by **is_framework_directory(project_root)**: if true, copy project-context.mdc; else copy project-context-user.mdc as project-context.mdc.
  - **B:** Single rule that says only: “Read project root AGENTS.md for project context. Use .cursor/rules for workflow and tapps-agents CLI.” No framework-specific content in the generic rule.
- **Result:** User projects get a short, generic project-context that points to AGENTS.md; framework repo keeps detailed framework/self-host context.

### 4.3 Claude Code: CLAUDE.md from Init

- **Goal:** Claude Code users get auto-loaded context without manual setup.
- **Implementation:**
  - Add optional init step: **create CLAUDE.md at project root** when init runs.
  - Content: Either (1) a short file that says “Project context: see AGENTS.md” and lists setup commands and TappsCodingAgents usage, or (2) generate CLAUDE.md from the same data as AGENTS.md (e.g. same template with a “Claude” variant or a wrapper that embeds AGENTS.md by reference). Prefer (1) to keep AGENTS.md the single source; CLAUDE.md is a thin wrapper.
  - Config: `init_create_claude_md: true` in config default; CLI flag `--no-claude-md` to skip if we want to avoid touching CLAUDE.md for teams that manage it themselves.
  - Reset: If we manage CLAUDE.md, add it to framework_files when present so init --reset overwrites it; else leave CLAUDE.md as user content and do not add to framework_files.

### 4.4 Tech-Stack in AGENTS.md and One Place

- In **AGENTS.md.template**, add a **Tech stack** section (e.g. after “Project: {{PROJECT_NAME}}”): “Detected: {{TECH_STACK_SUMMARY}}.” Placeholder filled from tech_stack (e.g. “Python, pytest, FastAPI” or “Node, pnpm, React”).
- Ensure **init_agents_md** receives tech_stack and that _agents_md_placeholders adds TECH_STACK_SUMMARY (and keep INSTALL_CMD, TEST_CMD, LINT_CMD from detection).
- Optional: doctor or a small CLI command “tapps-agents project-summary” that prints AGENTS.md path + tech-stack summary for human or tool use.

### 4.5 Auto-Create and Auto-Update Rules

- **Auto-create (first init):** AGENTS.md, .cursor/rules, .claude/skills, .cursor/commands, config.yaml, tech-stack.yaml, experts scaffold, knowledge scaffold, presets, .cursorignore, mcp.json, (optional) CLAUDE.md.
- **Auto-update (every init, no reset):** AGENTS.md (overwrite from template), tech-stack.yaml (merge detection, preserve overrides). Optional: refresh workflow-presets.mdc from YAML. Do **not** overwrite config.yaml, experts.yaml, or knowledge/.
- **Reset (init --reset):** Overwrite: AGENTS.md, .cursor/rules (framework), .claude/skills, .cursor/commands, presets, .cursorignore, (optional) CLAUDE.md. Preserve: config.yaml, experts.yaml, knowledge/, tech-stack.yaml (or document if we ever reset tech-stack.yaml).
- Document this in **docs/CONFIGURATION.md** or **docs/planning/** as “Init and reset behavior” so users and contributors know what is created vs updated vs preserved.

### 4.6 Connection Map (Document)

- Add a **connection map** (e.g. in docs or in a rule):
  - **AGENTS.md** ← template + tech_stack (placeholders). Read by: all agents (Cursor, Claude, Copilot, etc.).
  - **.cursor/rules/** ← packaged + (optional) project-context user variant. Read by: Cursor. One rule points to AGENTS.md.
  - **.claude/skills/** ← packaged. Used by: Cursor (Skills). Skills invoke workflows; they don’t replace AGENTS.md.
  - **.tapps-agents/config.yaml** ← default + project-type + tech-stack templates. Used by: CLI and workflows.
  - **.tapps-agents/tech-stack.yaml** ← detection + expert priorities. Used by: config, experts, AGENTS.md placeholders.
  - **.tapps-agents/experts.yaml + knowledge/** ← scaffold + optional auto. Used by: expert system, enhancer.
  - **CLAUDE.md** (optional) ← generated from AGENTS.md or ref. Read by: Claude Code.
- This can live in **docs/LLM_AGENT_SETUP.md** or **docs/planning/LLM_AGENT_SETUP_AND_CONNECTIONS_PLAN.md** (this file) as a “How it fits together” section.

### 4.7 Doctor and Verify

- **Doctor:** Check for AGENTS.md at project root; if missing, suggest “Run tapps-agents init to create AGENTS.md and full setup.”
- **Cursor verify:** List AGENTS.md as a recommended file; do not fail if missing (init may not have been run).

---

## 5. Implementation Order

1. **Phase 1 – AGENTS.md central (no special flags)**  
   Implement AGENTS_MD_CENTRAL_PLAN.md: framework-managed AGENTS.md, always overwrite, remove flags, template “Read this first” and links to .cursor/rules and .tapps-agents.

2. **Phase 2 – project-context for user vs framework**  
   Add project-context-user.mdc (generic); init chooses project-context.mdc vs project-context-user.mdc by is_framework_directory(project_root).

3. **Phase 3 – Tech-stack in AGENTS.md**  
   Add TECH_STACK_SUMMARY (and any other placeholders) to template and _agents_md_placeholders.

4. **Phase 4 – CLAUDE.md (optional)**  
   Add init step and optional flag to create CLAUDE.md pointing to AGENTS.md; decide whether it is framework-managed on reset.

5. **Phase 5 – Docs and connection map**  
   Update AGENTS_MD_GUIDE, CONFIGURATION, and command-reference; add “Init and reset behavior” and “How it fits together” (connection map) to this plan or docs/LLM_AGENT_SETUP.md.

6. **Phase 6 – Doctor/verify**  
   Doctor check for AGENTS.md; Cursor verify mention.

---

## 6. Success Criteria

- **One central file:** AGENTS.md is the single, tool-agnostic entry point; Cursor and Claude setups reference or derive from it.
- **No special flags for AGENTS.md:** Init always creates/overwrites it; init --reset resets it.
- **Cursor alignment:** Rules (and optional user project-context) point to AGENTS.md; Skills and commands remain the way to run TappsCodingAgents workflows.
- **Claude alignment:** Optional CLAUDE.md created by init so Claude Code auto-loads context; content points to or reflects AGENTS.md.
- **Tech-stack and docs:** Tech stack drives config, tech-stack.yaml, and AGENTS.md placeholders; AGENTS.md summarizes stack and commands in one place.
- **Clear create/update/reset matrix:** Documented so users and contributors know what init creates, what it updates, and what it preserves on reset.

---

## 7. References

- [Cursor Rules](https://docs.cursor.com/context/rules)
- [Claude Code Setup](https://code.claude.com/docs/en/setup)
- [AGENTS.md](https://agents.md/)
- [Softcery: Agentic Coding with Claude and Cursor](https://softcery.com/lab/softcerys-guide-agentic-coding-best-practices/)
- docs/planning/AGENTS_MD_CENTRAL_PLAN.md
- docs/planning/AGENTS_MD_INTEGRATION_PLAN.md
