# AGENTS.md Integration Plan

**Note:** Superseded by [docs/planning/AGENTS_MD_CENTRAL_PLAN.md](AGENTS_MD_CENTRAL_PLAN.md) for init behavior (AGENTS.md central, no special flags).

**Status:** Draft  
**Created:** 2026-02-07  
**References:** [agents.md](https://agents.md/), [GitHub Blog – How to write a great agents.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/), [GitHub agentsmd/agents.md](https://github.com/agentsmd/agents.md)

## 1. Executive Summary

**[AGENTS.md](https://agents.md/)** is an open, standard format for guiding AI coding agents—a “README for agents” at the project root. It is used by 60k+ open-source projects and supported by Cursor, GitHub Copilot, Aider, Gemini CLI, and others. This plan proposes adding **AGENTS.md** as an optional project artifact created or scaffolded by `tapps-agents init` and `init --reset`, so that user projects get a best-practice agent instruction file that works across tools and complements TappsCodingAgents (Cursor Rules, Skills, config).

**Recommendation:** Treat AGENTS.md as a **project artifact** (like `.cursorignore`), not as an expert or a TappsCodingAgents agent. The framework will ship a template and an init step that creates or optionally refreshes `AGENTS.md` at the project root.

---

## 2. Background: What Is AGENTS.md?

- **Purpose:** A single, predictable place for context and instructions that help any AI coding agent work on the project.
- **Format:** Standard Markdown; no required schema. Sections are free-form (e.g. setup, testing, code style, boundaries).
- **Placement:** Repository root (and optionally in subpackages for monorepos; “closest file wins”).
- **Ecosystem:** Compatible with Cursor, Copilot, Aider, Gemini CLI, Zed, Warp, Devin, and others.

**Why separate from README?**

- README targets humans (quick start, contribution guidelines).
- AGENTS.md targets agents: build/test commands, conventions, boundaries, and detailed context that would clutter a README.

---

## 3. Best Practices (from agents.md and GitHub)

From [agents.md](https://agents.md/) and [GitHub’s analysis of 2,500+ repos](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/):

1. **Put commands early** – Executable commands with flags (e.g. `pytest -v`, `pnpm test`).
2. **Six core areas** – Commands, testing, project structure, code style, git/PR workflow, boundaries.
3. **Clear boundaries** – What agents may do without permission vs. what requires approval; what they must never touch (secrets, vendor, production config).
4. **Specific tech stack** – Exact versions and key deps (e.g. “React 18, TypeScript, Vite”).
5. **Code examples over long prose** – One concrete example of “good” style beats long descriptions.
6. **Dos and don’ts** – Explicit, nitpicky rules where helpful.

---

## 4. Should AGENTS.md Be an Expert, an Agent, or Something Else?

| Option | Conclusion | Rationale |
|--------|------------|-----------|
| **Expert** | No | Experts are domain knowledge (security, API design, etc.) consulted via `@expert *consult`. AGENTS.md is a project-level instruction file, not a consultable domain. |
| **TappsCodingAgents agent** | No | Our “agents” are workflow roles (reviewer, implementer, tester, etc.). AGENTS.md is an open-format file that any coding agent reads; we don’t “be” it—we help projects create and maintain it. |
| **Project artifact** | **Yes** | Like `.cursorignore`: a file at project root that init can create from a framework template. Optional refresh on init (e.g. `--reset-agents-md`). Not part of “framework-managed” reset set (user content). |

**Conclusion:** AGENTS.md is a **project artifact** scaffolded by init from a template. It is **not** an expert and **not** a TappsCodingAgents agent.

---

## 5. Relationship to Existing AGENTS.md in This Repo

- **This repo** already has an `AGENTS.md` at the root: it defines agent identity and project rules for TappsCodingAgents (framework development). It effectively **is** an AGENTS.md in the open-format spirit (context for agents).
- **User projects** that run `tapps-agents init` may have no AGENTS.md. We will provide a **template** that:
  - Follows the open format (setup, testing, structure, code style, git workflow, boundaries).
  - Can be filled with placeholders and/or tech-stack-aware content from init (e.g. Python + pytest, Node + pnpm).
  - Includes an optional section on TappsCodingAgents (Simple Mode, workflows, quality gates) so the file is useful for both generic agents and TappsCodingAgents users.

No conflict: our own AGENTS.md stays as-is; we add a **packaged template** and init logic for **user projects**.

---

## 6. Implementation Plan

### 6.1 Template Asset

- **Location:** `tapps_agents/resources/AGENTS.md.template` (or `tapps_agents/resources/templates/AGENTS.md`).
- **Content (high level):**
  - Brief intro: “This file helps AI coding agents work on this project (see [agents.md](https://agents.md/)).”
  - **Setup commands** – Install, dev server, test (placeholders or detected: e.g. `pip install -e .`, `pytest`, `pnpm install`, `pnpm test`).
  - **Testing instructions** – Where tests live, how to run, “fix tests before merge.”
  - **Project structure** – Short description of key dirs (`src/`, `tests/`, `docs/`, etc.); can be generic or tech-stack-aware.
  - **Code style** – Language/framework (e.g. Python: Ruff, Black, type hints); one small “good” example if desired.
  - **Git / PR workflow** – Branch naming, “run tests before commit,” PR title format if desired.
  - **Boundaries** – “Always / Ask first / Never” (e.g. never commit secrets; ask before schema changes).
  - **Optional: TappsCodingAgents** – Short section: “This project uses TappsCodingAgents. Prefer `@simple-mode *build` for features, `*fix` for bugs, `*review` for reviews; see `.cursor/rules/` and `tapps-agents` CLI.”

- **Placeholders:** e.g. `{{PROJECT_NAME}}`, `{{INSTALL_CMD}}`, `{{TEST_CMD}}`, `{{LINT_CMD}}` filled at init from tech stack detection and/or config.

### 6.2 Init Behavior

- **New function:** `init_agents_md(project_root, overwrite=False, tech_stack=None)` in `tapps_agents/core/init_project.py`.
  - Resolve template from package resources (`_resource_at` or equivalent).
  - Render template (replace placeholders from `tech_stack` and defaults).
  - **Target path:** `project_root / "AGENTS.md"`.
  - **Create if missing:** Always create if `AGENTS.md` does not exist.
  - **Overwrite:** Only if `overwrite=True` (e.g. `--reset-agents-md`). Otherwise leave existing `AGENTS.md` untouched.
  - Return `(created_or_updated: bool, path: str)` for reporting.

- **Integration in `init_project()`:**
  - Call `init_agents_md(project_root, overwrite=False, tech_stack=tech_stack)` after tech stack and config are set (so we can pass detected stack).
  - Add a result key, e.g. `results["agents_md"] = success`, and append to `results["files_created"]` when created/updated.
  - **CLI flag:** Add optional `--agents-md` (default: True) to enable/disable this step; `--no-agents-md` to skip.

### 6.3 Init --reset Behavior

- **Do not** add root `AGENTS.md` to `framework_files` in `identify_framework_files()`. So `init --reset` does **not** delete or overwrite the user’s AGENTS.md.
- **Optional flag:** `--reset-agents-md` to force overwrite `AGENTS.md` from template during init (or during init --reset). When set, call `init_agents_md(project_root, overwrite=True, tech_stack=...)`.

### 6.4 Doctor / Cursor Verify (Optional)

- **Doctor:** Optional check: “AGENTS.md present at project root.” If missing, suggest: “Add an AGENTS.md for agent-friendly context. Run `tapps-agents init` with agents-md enabled or create one manually. See https://agents.md/.”
- **Cursor verify:** Can mention AGENTS.md as recommended for cross-tool agent compatibility; do not fail verification if missing.

### 6.5 Documentation

- **New (or section in existing):** e.g. `docs/AGENTS_MD_GUIDE.md` (or a section in `docs/CONFIGURATION.md`):
  - What AGENTS.md is and why it’s useful.
  - How init creates/updates it (template, placeholders, `--no-agents-md`, `--reset-agents-md`).
  - Link to [agents.md](https://agents.md/) and GitHub best practices.
  - How it complements Cursor Rules and TappsCodingAgents (Rules/Skills are framework-specific; AGENTS.md is tool-agnostic).
- **Command reference / README:** Mention that `tapps-agents init` optionally creates AGENTS.md at project root.

### 6.6 Backward Compatibility

- **Existing projects:** No change unless they run init again; then they get AGENTS.md only if it doesn’t exist (or with `--reset-agents-md`).
- **Repos that already have AGENTS.md:** Init leaves it unchanged unless `--reset-agents-md` is used.

---

## 7. Task Breakdown

| # | Task | Owner | Notes |
|---|------|--------|--------|
| 1 | Add `AGENTS.md.template` under `tapps_agents/resources/` (or `resources/templates/`) with placeholders and six core sections + optional TappsCodingAgents section | - | Follow agents.md and GitHub best practices |
| 2 | Implement `init_agents_md(project_root, overwrite=False, tech_stack=None)` with template resolution and placeholder substitution | - | Reuse tech_stack from init; sensible defaults for unknown stacks |
| 3 | Call `init_agents_md` from `init_project()` after config/tech stack; add `results["agents_md"]` and `--no-agents-md` CLI flag | - | CLI in `tapps_agents/cli/` (init command) |
| 4 | Add `--reset-agents-md` CLI flag; when set, call `init_agents_md(..., overwrite=True)` | - | Document in command-reference and CONFIGURATION |
| 5 | (Optional) Doctor: check for AGENTS.md at root and suggest adding if missing | - | Non-blocking suggestion |
| 6 | (Optional) Cursor verify: mention AGENTS.md in “recommended” list | - | Do not fail if missing |
| 7 | Add `docs/AGENTS_MD_GUIDE.md` (or CONFIGURATION section) and update command-reference/README | - | Link to agents.md and best practices |

---

## 8. Out of Scope (Later)

- **Nested AGENTS.md:** Monorepo subpackages can add their own AGENTS.md; init only creates at project root unless we add a separate feature (e.g. `init --agents-md-subpackages`).
- **Expert or agent that “writes” AGENTS.md:** Could be a future documenter/analyst feature (“suggest AGENTS.md content from my project”); not part of this plan.
- **Validation of AGENTS.md:** No schema or strict validation; optional lint (e.g. markdownlint) can be mentioned in docs.

---

## 9. References

- [AGENTS.md – agents.md](https://agents.md/)
- [GitHub Blog – How to write a great agents.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [agentsmd/agents.md (GitHub)](https://github.com/agentsmd/agents.md)
- [Aider – always load conventions (AGENTS.md)](https://aider.chat/docs/usage/conventions.html#always-load-conventions)
- [Gemini CLI – contextFileName: AGENTS.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/configuration.md#available-settings-in-settingsjson)

---

**Document version:** 1.0  
**Last updated:** 2026-02-07
