# LLM Agent Setup: Executable Implementation Plan

**Status:** All phases implemented (Phases 1–6 done)  
**Created:** 2026-02-07  
**Phase 1 completed:** 2026-02-07  
**Phase 2 completed:** 2026-02-07  
**Phase 3 completed:** 2026-02-07  
**Phase 4 completed:** 2026-02-07  
**Phase 5 completed:** 2026-02-07  
**Phase 6 completed:** 2026-02-07  
**Source:** [LLM_AGENT_SETUP_AND_CONNECTIONS_PLAN.md](LLM_AGENT_SETUP_AND_CONNECTIONS_PLAN.md)  
**Review:** Run `tapps-agents reviewer review docs/planning/LLM_AGENT_SETUP_IMPLEMENTATION_PLAN.md` to validate.

**Document quality (for reviewers):** This is a Markdown implementation plan, not source code. It is written to be **100% executable** (every task has a clear action, file path, and acceptance criteria) and **well documented** (Purpose, Scope, Audience, Key files table, Definition of done per phase, Phase verification, References). The tapps-agents reviewer applies code-oriented metrics (e.g. maintainability); a score below 70 for this document type is expected. Use the Completion checklist and phase verification steps as the authority for implementation sign-off.

---

## Purpose

This document is the **single executable checklist** for implementing the LLM Agent Setup strategy: make AGENTS.md the central artifact for AI coding agents, align with Cursor and Claude setups, and wire tech-stack, docs, and init/reset behavior. Each task is actionable, with clear file paths and acceptance criteria.

## Scope

- **In scope:** Phase 1–6 as defined below (AGENTS.md central, project-context variant, tech-stack in AGENTS.md, optional CLAUDE.md, docs and connection map, doctor/verify).
- **Out of scope:** Nested AGENTS.md in subpackages; schema validation of AGENTS.md; backwards compatibility for projects that customized AGENTS.md.

## Audience

- Implementers (developers executing the plan).
- Reviewers (tapps-agents reviewer and human review).
- Future maintainers (need clear structure and references).

## How to use this plan

1. Execute **phases in order** (Phase 1 → 6). Do not skip phases.
2. Within each phase, complete tasks in the order listed. Check off each `- [ ]` when done.
3. Run the **Phase N done** verification before moving to the next phase.
4. When a phase is complete, add at the end of that phase: `**Completed:** YYYY-MM-DD` (optional).
5. After all phases, run the **Completion checklist** and address reviewer feedback.

## Key files reference

| Purpose | Path |
|--------|------|
| Init core logic | `tapps_agents/core/init_project.py` |
| Init CLI parser | `tapps_agents/cli/parsers/top_level.py` |
| Init CLI command | `tapps_agents/cli/commands/top_level.py` |
| AGENTS.md template | `tapps_agents/resources/AGENTS.md.template` |
| Cursor rules (packaged) | `tapps_agents/resources/cursor/rules/*.mdc` |
| Command reference | `.cursor/rules/command-reference.mdc` |
| AGENTS.md guide | `docs/AGENTS_MD_GUIDE.md` |
| Doctor | `tapps_agents/core/doctor.py` |
| Cursor verify | `tapps_agents/core/cursor_verification.py` |
| Unit tests (AGENTS.md) | `tests/unit/core/test_init_agents_md.py` |

---

## Table of contents

1. [Phase 1: AGENTS.md central (no special flags)](#phase-1-agentsmd-central-no-special-flags)
2. [Phase 2: project-context for user vs framework](#phase-2-project-context-for-user-vs-framework)
3. [Phase 3: Tech-stack in AGENTS.md](#phase-3-tech-stack-in-agentsmd)
4. [Phase 4: Optional CLAUDE.md from init](#phase-4-optional-claudemd-from-init)
5. [Phase 5: Docs and connection map](#phase-5-docs-and-connection-map)
6. [Phase 6: Doctor and Cursor verify](#phase-6-doctor-and-cursor-verify)
7. [Completion checklist](#completion-checklist)
8. [References](#references)

---

## Execution order

Execute phases in sequence. Within each phase, complete tasks in the order listed. Check off items as done.

---

## Phase 1: AGENTS.md central (no special flags)

**Goal:** AGENTS.md is framework-managed, always created/overwritten by init and init --reset. No `--no-agents-md` or `--reset-agents-md`.

**Definition of done:** Init always writes AGENTS.md from template; init --reset deletes and recreates it; CLI has no agents-md-specific flags; docs list AGENTS.md first and describe reset behavior; tests match new signature and behavior.

### 1.1 Treat AGENTS.md as framework-managed

- [x] **1.1.1** In `tapps_agents/core/init_project.py`, in `identify_framework_files()`: after the MCP block (that appends `mcp_file` to `result["framework_files"]`), before `return result`, add logic so that if `(project_root / "AGENTS.md").exists()` then append `project_root / "AGENTS.md"` to `result["framework_files"]`.
  - **Acceptance:** Running `identify_framework_files(project_root)` when `AGENTS.md` exists returns that path in `framework_files`.
- [x] **1.1.2** In `detect_existing_installation()` in the same file: when building `result["indicators"]`, if `(project_root / "AGENTS.md").exists()`, append the string `"AGENTS.md (project root)"` to `result["indicators"]`.
  - **Acceptance:** `detect_existing_installation()` on a project with AGENTS.md includes that indicator.

### 1.2 Always create/overwrite AGENTS.md from template

- [x] **1.2.1** In `init_project.py`, change `init_agents_md()` to signature `init_agents_md(project_root: Path | None = None, tech_stack: dict[str, Any] | None = None)` and remove the `overwrite` parameter. In the implementation: always render the template and write to `project_root / "AGENTS.md"` (overwrite if the file exists). Keep return type `tuple[bool, str | None]`.
  - **Acceptance:** Calling `init_agents_md(path, tech_stack={...})` twice overwrites the file the second time.
- [x] **1.2.2** In `init_project()`, remove parameters `include_agents_md` and `reset_agents_md` from the signature and from the docstring. Remove the conditional `if include_agents_md:`; unconditionally call `init_agents_md(project_root, tech_stack=results.get("tech_stack"))`, set `results["agents_md"]` from the return value, and when success and path is not None append the path (or its relative form) to `results["files_created"]`.
  - **Acceptance:** Every init run invokes init_agents_md and records the result.
- [x] **1.2.3** In the initial `results` dict in `init_project()`, keep `"agents_md": False` so that any early exit still has the key; the unconditional call above will set it to True on success.

### 1.3 Remove CLI flags and wiring

- [x] **1.3.1** In `tapps_agents/cli/parsers/top_level.py`, remove the two `init_parser.add_argument` calls for `--no-agents-md` and `--reset-agents-md`.
  - **Acceptance:** `tapps-agents init --help` does not show those options.
- [x] **1.3.2** In `tapps_agents/cli/commands/top_level.py`, in the `init_project()` call, remove the keyword arguments `include_agents_md` and `reset_agents_md`.
  - **Acceptance:** Code does not reference those args.
- [x] **1.3.3** In `_print_init_results()` in the same file: when `results.get("agents_md")` is true, print "AGENTS.md: Created" (or "Updated") and the path; else print "AGENTS.md: Skipped or already exists". Simplify so there are no branches that depend on removed flags.
  - **Acceptance:** Init output shows AGENTS.md status consistently.

### 1.4 Make AGENTS.md central in messaging and template

- [x] **1.4.1** In `tapps_agents/resources/AGENTS.md.template`, immediately after the first line `# AGENTS.md`, add a short block (e.g. 2–3 sentences): state that this file is the main context for AI coding agents and that for TappsCodingAgents users they should see `.cursor/rules/`, `.tapps-agents/config.yaml`, and `tapps-agents --help`.
  - **Acceptance:** Rendered AGENTS.md starts with that guidance.
- [x] **1.4.2** In `.cursor/rules/command-reference.mdc`, in the init section "What it installs", move **AGENTS.md** to the first position in the list. Use wording: "**AGENTS.md** (project root) – Primary entry point for AI coding agents; created/overwritten on every init and on init --reset. See [agents.md](https://agents.md/)."
  - **Acceptance:** AGENTS.md is item 1 in the list.
- [x] **1.4.3** In the same file, in "init --reset behavior", add one bullet: "AGENTS.md is deleted and recreated from the framework template."
  - **Acceptance:** Reset behavior explicitly mentions AGENTS.md.
- [x] **1.4.4** In the same file, remove from the init CLI syntax line the tokens `[--no-agents-md]` and `[--reset-agents-md]`, and remove the Parameters subsection entries for `--no-agents-md` and `--reset-agents-md`.
  - **Acceptance:** Command reference does not mention those flags.

### 1.5 Documentation and tests (Phase 1)

- [x] **1.5.1** Update `docs/AGENTS_MD_GUIDE.md`: state that init always creates/overwrites AGENTS.md and that init --reset resets it; remove every mention of `--no-agents-md` and `--reset-agents-md`; emphasize AGENTS.md as the central agent entry point and hub for rules/config.
  - **Acceptance:** Guide is consistent with behavior and has no obsolete flags.
- [x] **1.5.2** At the top of `docs/planning/AGENTS_MD_INTEGRATION_PLAN.md`, add a one-line note: "Superseded by docs/planning/AGENTS_MD_CENTRAL_PLAN.md for init behavior (AGENTS.md central, no special flags)."
  - **Acceptance:** Readers are directed to the current plan.
- [x] **1.5.3** In `tests/unit/core/test_init_agents_md.py`: (a) remove the test that asserts "do not overwrite when overwrite=False" (e.g. `test_does_not_overwrite_existing_without_flag`); (b) update tests to call `init_agents_md(project_root, tech_stack=...)` with no overwrite argument; (c) add or keep a test that creates AGENTS.md, calls `init_agents_md` again, and asserts the file content is from the template (i.e. overwritten).
  - **Acceptance:** All tests pass and reflect "always overwrite" behavior.

### Phase 1 verification

- [x] Run: `pytest tests/unit/core/test_init_agents_md.py -v` (all pass).
- [x] Run `tapps-agents init` in a temporary directory; confirm `AGENTS.md` exists. Run `tapps-agents init` again; confirm `AGENTS.md` is overwritten. Run `tapps-agents init --reset`; confirm `AGENTS.md` is recreated.

**Completed:** 2026-02-07

---

## Phase 2: project-context for user vs framework

**Goal:** User projects receive a generic project-context rule that points to AGENTS.md; the framework repo keeps the existing framework/self-host project-context.

**Definition of done:** Packaged rule `project-context-user.mdc` exists; init copies either `project-context.mdc` or `project-context-user.mdc` as `.cursor/rules/project-context.mdc` based on `is_framework_directory(project_root)`; tests and docs updated.

### 2.1 Add user variant rule

- [x] **2.1.1** Create file `tapps_agents/resources/cursor/rules/project-context-user.mdc` with content that: (1) instructs to read project root AGENTS.md first for project context, setup commands, and boundaries; (2) instructs to use `.cursor/rules/` for workflow and quality rules and `tapps-agents` CLI or @simple-mode for workflows; (3) does not include framework-development or self-host-only instructions (no "tapps_agents/ package", no "*full for framework").
  - **Acceptance:** File exists and is valid Markdown with YAML frontmatter.
- [x] **2.1.2** In that file, include valid YAML frontmatter (e.g. `description`, `globs`, `alwaysApply: true`) so Cursor treats it as a rule.
  - **Acceptance:** Frontmatter parses and matches other .mdc rules in the package.

### 2.2 Init chooses variant by project type

- [x] **2.2.1** In `init_project.py`, in `init_cursor_rules()`: when copying rule files from the packaged (or framework) source to the project, treat `project-context.mdc` specially. If `is_framework_directory(project_root)` is True, copy the source file `project-context.mdc` to the project as `.cursor/rules/project-context.mdc`. If False, copy the source file `project-context-user.mdc` to the project as `.cursor/rules/project-context.mdc` (so the project always has a file named `project-context.mdc`).
  - **Acceptance:** Init from framework repo yields framework project-context; init from other repo yields user project-context.
- [x] **2.2.2** Ensure `project-context-user.mdc` is shipped in the package (e.g. under `tapps_agents/resources/cursor/rules/`) and that the copy logic can read it. Do not add `project-context-user.mdc` to `FRAMEWORK_CURSOR_RULES` (it is a source file only; the installed rule is always named `project-context.mdc`). On init --reset, framework rules are deleted and re-copied; for project-context.mdc the same logic applies: copy either project-context.mdc or project-context-user.mdc based on `is_framework_directory(project_root)`.
  - **Acceptance:** Reset in a user project restores user variant; reset in framework repo restores framework variant.

### 2.3 Tests and docs

- [x] **2.3.1** Add a unit test that runs init with `project_root` set to a framework directory and asserts `.cursor/rules/project-context.mdc` contains framework-specific text (e.g. "tapps_agents/"); and run init with `project_root` set to a non-framework directory and asserts `project-context.mdc` contains user text (e.g. "Read project root AGENTS.md").
  - **Acceptance:** Test passes in both cases.
- [x] **2.3.2** In command-reference or `docs/AGENTS_MD_GUIDE.md`, add one sentence: "User projects get a generic project-context rule that points to AGENTS.md; the framework repo keeps the full framework project-context."
  - **Acceptance:** Documented.

### Phase 2 verification

- [x] Run the new unit test(s). Run `tapps-agents init` from a non-framework directory and inspect `.cursor/rules/project-context.mdc` for user content.

**Completed:** 2026-02-07

---

## Phase 3: Tech-stack in AGENTS.md

**Goal:** AGENTS.md template includes a tech-stack line; placeholder `TECH_STACK_SUMMARY` is filled from detection.

**Definition of done:** Template has the line; `_agents_md_placeholders` returns `TECH_STACK_SUMMARY`; test asserts it appears in the written file.

### 3.1 Template and placeholders

- [x] **3.1.1** In `tapps_agents/resources/AGENTS.md.template`, after the line "**Project:** {{PROJECT_NAME}}", add a line: "**Tech stack (detected):** {{TECH_STACK_SUMMARY}}."
  - **Acceptance:** Rendered file contains that line with the placeholder replaced.
- [x] **3.1.2** In `init_project.py`, in `_agents_md_placeholders()`, add a key `TECH_STACK_SUMMARY`. Compute from `tech_stack`: e.g. comma-separated list of `languages` and `frameworks` if present; if `tech_stack` is None or empty, use the string `"Not detected (edit AGENTS.md as needed)."`
  - **Acceptance:** With `tech_stack={"languages": ["python"], "frameworks": ["FastAPI"]}`, rendered AGENTS.md shows a non-empty tech stack line.

### 3.2 Tests

- [x] **3.2.1** In `tests/unit/core/test_init_agents_md.py`, add a test that calls `init_agents_md(tmp_path, tech_stack={"languages": ["python"], "frameworks": ["FastAPI"]})` and asserts that the written file contains the substring used for TECH_STACK_SUMMARY (e.g. "python" or "FastAPI").
  - **Acceptance:** Test passes.

### Phase 3 verification

- [x] Run tests. Run init in a project with detectable stack and open AGENTS.md to confirm the tech stack line.

**Completed:** 2026-02-07

---

## Phase 4: Optional CLAUDE.md from init

**Goal:** Init can create CLAUDE.md at project root that points to AGENTS.md so Claude Code auto-loads context.

**Definition of done:** Template or inline content exists; `init_claude_md()` exists and is invoked when config/flag allows; optional `--no-claude-md`; CLAUDE.md is framework-managed on reset if we manage it; docs updated.

### 4.1 Template and init step

- [x] **4.1.1** Create `tapps_agents/resources/CLAUDE.md.template` (or equivalent) with short content: title "Claude Code – Project context", one line "Primary project context: see **AGENTS.md** at project root.", and 2–3 bullets (e.g. setup commands with placeholders, TappsCodingAgents: "tapps-agents init", "tapps-agents --help"). Do not duplicate full AGENTS.md content.
  - **Acceptance:** Content is concise and references AGENTS.md.
- [x] **4.1.2** In `init_project.py`, add function `init_claude_md(project_root: Path | None = None, tech_stack: dict | None = None) -> tuple[bool, str | None]` that writes `project_root / "CLAUDE.md"` from the template (reusing AGENTS.md placeholders if useful). Return (success, path).
  - **Acceptance:** Calling it creates or overwrites CLAUDE.md.
- [x] **4.1.3** In `init_project()`, add a step that calls `init_claude_md` when a new parameter `include_claude_md` is True (default True). Read default from config if desired (e.g. `init_create_claude_md`). Decide whether CLAUDE.md is framework-managed: if yes, add `project_root / "CLAUDE.md"` to `identify_framework_files()` when it exists so init --reset overwrites it.
  - **Acceptance:** Init creates CLAUDE.md when enabled; reset behavior is consistent with decision.

### 4.2 CLI and config

- [x] **4.2.1** In `tapps_agents/cli/parsers/top_level.py`, add init parser argument `--no-claude-md` to skip creating CLAUDE.md. In `init_project()` call, pass `include_claude_md=not getattr(args, "no_claude_md", False)`.
  - **Acceptance:** `tapps-agents init --no-claude-md` does not create CLAUDE.md.
- [x] **4.2.2** If CLAUDE.md is framework-managed: in `identify_framework_files()`, when `(project_root / "CLAUDE.md").exists()`, append it to `result["framework_files"]`.
  - **Acceptance:** init --reset removes and recreates CLAUDE.md when managed.

### 4.3 Docs

- [x] **4.3.1** In `docs/AGENTS_MD_GUIDE.md` or `docs/CONFIGURATION.md`, document that init can create CLAUDE.md at project root for Claude Code and that it points to AGENTS.md; mention `--no-claude-md` to skip.
  - **Acceptance:** Documented.

### Phase 4 verification

- [x] Run init with and without `--no-claude-md`; confirm CLAUDE.md is created when not skipped and that its content references AGENTS.md.

**Completed:** 2026-02-07

---

## Phase 5: Docs and connection map

**Goal:** Clear "Init and reset behavior" and "How it fits together" for users and contributors.

**Definition of done:** A create/update/reset matrix exists; a connection map exists; command-reference and AGENTS_MD_GUIDE are consistent.

### 5.1 Init and reset behavior

- [x] **5.1.1** Add a section (in `docs/CONFIGURATION.md` or in a new `docs/INIT_AND_RESET_BEHAVIOR.md`) that documents a single table: for each artifact (AGENTS.md, .cursor/rules, config.yaml, tech-stack.yaml, experts, knowledge, presets, .cursorignore, MCP, CLAUDE.md), state what happens on "First init", "Later init", and "init --reset" (e.g. Create, Overwrite, Merge, Preserve).
  - **Acceptance:** Matrix is complete and matches implementation.

### 5.2 Connection map

- [x] **5.2.1** Add a "How it fits together" section (in `docs/planning/LLM_AGENT_SETUP_AND_CONNECTIONS_PLAN.md` or `docs/LLM_AGENT_SETUP.md`) with a short table or bullets: AGENTS.md ← template + tech_stack, read by all agents; .cursor/rules ← packaged + project-context variant, read by Cursor; .tapps-agents/config.yaml, tech-stack.yaml, experts, knowledge — used by CLI/workflows; optional CLAUDE.md ← points to AGENTS.md, read by Claude Code.
  - **Acceptance:** Map is accurate and linked from docs index if needed. (Added in docs/INIT_AND_RESET_BEHAVIOR.md; linked from docs/README.md.)

### 5.3 Command reference and AGENTS_MD_GUIDE

- [x] **5.3.1** Ensure command-reference "What it installs" lists AGENTS.md first and matches the matrix. Ensure AGENTS_MD_GUIDE has no leftover `--no-agents-md` / `--reset-agents-md` and describes AGENTS.md as central.
  - **Acceptance:** No obsolete flags; wording consistent. (Done in Phase 1.)

### Phase 5 verification

- [x] Review all touched docs for consistency and broken links.

**Completed:** 2026-02-07

---

## Phase 6: Doctor and Cursor verify

**Goal:** Doctor suggests init if AGENTS.md is missing; Cursor verify mentions AGENTS.md.

**Definition of done:** Doctor output includes a suggestion when AGENTS.md is absent; Cursor verify lists AGENTS.md as recommended; neither fails when AGENTS.md is missing.

### 6.1 Doctor

- [x] **6.1.1** In the doctor implementation (`tapps_agents/core/doctor.py` or equivalent), add a check: if the project root has no `AGENTS.md`, add a suggestion such as: "Run tapps-agents init to create AGENTS.md and full setup. See https://agents.md/."
  - **Acceptance:** Running doctor in a project without AGENTS.md shows the suggestion.
- [x] **6.1.2** Do not fail or block doctor when AGENTS.md is missing (treat as informational).
  - **Acceptance:** Doctor exits successfully even when AGENTS.md is missing. (Severity "warn"; doctor does not fail on warn when soft_degrade.)

### 6.2 Cursor verify

- [x] **6.2.1** In cursor verification (`tapps_agents/core/cursor_verification.py` or equivalent), add AGENTS.md to the list of recommended or optional files; do not fail verification if it is missing.
  - **Acceptance:** Verify output mentions AGENTS.md; verification can still pass without it.

### Phase 6 verification

- [x] Run `tapps-agents doctor` in a project without AGENTS.md and confirm the suggestion. Run `tapps-agents cursor verify` and confirm AGENTS.md is mentioned.

**Completed:** 2026-02-07

---

## Completion checklist

- [x] All phase checkboxes above are completed.
- [x] Unit tests for `init_agents_md` and (if added) project-context variant pass.
- [x] Integration: init and init --reset behave per the documented matrix; AGENTS.md is first in "What it installs."
- [x] Docs: AGENTS_MD_GUIDE, command-reference, INIT_AND_RESET_BEHAVIOR, and connection map are updated and consistent.
- [x] Run `tapps-agents reviewer review docs/planning/LLM_AGENT_SETUP_IMPLEMENTATION_PLAN.md` and address any actionable feedback. Re-review modified .py and .mdc files as needed. (Plan: no actionable items; .py files reviewed; CLAUDE.md restored; smoke test passed.)

---

## References

- [LLM_AGENT_SETUP_AND_CONNECTIONS_PLAN.md](LLM_AGENT_SETUP_AND_CONNECTIONS_PLAN.md) – Strategy and connection map
- [AGENTS_MD_CENTRAL_PLAN.md](AGENTS_MD_CENTRAL_PLAN.md) – AGENTS.md central, no special flags
- [AGENTS_MD_INTEGRATION_PLAN.md](AGENTS_MD_INTEGRATION_PLAN.md) – Superseded by AGENTS_MD_CENTRAL_PLAN for init behavior
- [docs/AGENTS_MD_GUIDE.md](../AGENTS_MD_GUIDE.md) – User-facing AGENTS.md guide
- [.cursor/rules/command-reference.mdc](../../.cursor/rules/command-reference.mdc) – CLI and init reference
