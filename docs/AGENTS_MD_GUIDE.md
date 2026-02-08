# AGENTS.md Guide

This guide explains how TappsCodingAgents uses the [AGENTS.md open format](https://agents.md/) to help AI coding agents work on your project.

## What is AGENTS.md?

**AGENTS.md** is a simple, open format for guiding AI coding agents. Think of it as a **README for agents**: a dedicated, predictable file at your project root where you provide context and instructions that help any coding agent (Cursor, GitHub Copilot, Aider, Gemini CLI, and others) work effectively on your project.

- **Purpose:** Extra context agents need—build steps, test commands, code style, and boundaries—without cluttering your human-facing README.
- **Format:** Standard Markdown; no required schema. Use whatever sections help your project.
- **Placement:** Repository root (and optionally in subpackages for monorepos; the closest file wins).

See [agents.md](https://agents.md/) and [GitHub's best practices](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) for more.

## How TappsCodingAgents Uses AGENTS.md

**AGENTS.md is the central entry point for AI coding agents.** When you run **`tapps-agents init`**, the framework **always** creates or overwrites **AGENTS.md** at your project root from a built-in template. The template includes:

- **Setup commands** – Install, test, and lint commands (filled from tech stack detection when possible).
- **Testing instructions** – Where tests live and that they should pass before merge.
- **Project structure** – Short description of key directories.
- **Code style** – Use the project's linter/formatter.
- **Git / PR workflow** – Run tests before commit; clear messages.
- **Boundaries** – Always / Ask first / Never (e.g. never commit secrets).
- **TappsCodingAgents (optional)** – How to use Simple Mode and workflows if you use the framework.

## Init Behavior

- **Every init:** `tapps-agents init` **always** creates or overwrites **AGENTS.md** at the project root from the framework template. AGENTS.md is framework-managed.
- **init --reset:** `tapps-agents init --reset` deletes and recreates AGENTS.md from the template (same as other framework files).

There are no flags to skip or force AGENTS.md; it is always installed and reset with the rest of the framework artifacts.

## Customizing AGENTS.md

After init, you can edit **AGENTS.md** for the current session or commit. The next run of `tapps-agents init` or `tapps-agents init --reset` will overwrite it with the template again. To keep custom content long-term, either:

- Maintain your customizations in a separate doc and re-apply after init, or
- Use the template as a starting point and avoid running init --reset if you have heavy customizations (or restore from backup after reset).

For most users, the template plus small edits (e.g. project name, commands) is sufficient; the file is in version control so you can revert init changes if needed.

## CLAUDE.md (optional)

Init can create **CLAUDE.md** at the project root for [Claude Code](https://claude.ai/code). Claude Code auto-loads CLAUDE.md; the template points to **AGENTS.md** for primary context. Use `tapps-agents init --no-claude-md` to skip creating CLAUDE.md. If created, CLAUDE.md is framework-managed and is recreated on `init --reset`.

## Relationship to Cursor Rules and Skills

- **AGENTS.md** – Tool-agnostic, open format. Any agent (Cursor, Copilot, Aider, etc.) can read it. Central hub for setup, commands, and boundaries.
- **Cursor Rules (`.cursor/rules/`)** – Cursor-specific rules and workflow guidance installed by `tapps-agents init`. User projects get a generic project-context rule that points to AGENTS.md; the framework repo keeps the full framework project-context.
- **Cursor Skills (`.claude/skills/`)** – TappsCodingAgents skill definitions for Cursor.

AGENTS.md complements (does not replace) Cursor Rules and Skills. Use AGENTS.md as the central agent entry point; use Rules and Skills for Cursor and TappsCodingAgents-specific behavior.

## References

- [AGENTS.md – agents.md](https://agents.md/)
- [GitHub Blog – How to write a great agents.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [agentsmd/agents.md (GitHub)](https://github.com/agentsmd/agents.md)
- Command reference: `tapps-agents init --help` and `.cursor/rules/command-reference.mdc` (init section)
