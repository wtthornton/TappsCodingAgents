# GitHub Issue: Project Cleanup Agent

**Copy the sections below into a new GitHub issue** (e.g. [New Issue](https://github.com/wtthornton/TappsCodingAgents/issues/new) → choose "Feature Request" or paste into body).

---

**Title:** `[FEATURE] Project Cleanup Agent – guided project and docs cleanup`

**Labels:** `enhancement`

---

## Feature Description

An agent or simple-mode workflow that helps keep the project clean after heavy use of tapps-agents and iterative development: suggest moving misplaced root-level files, identify outdated or incorrect documentation, and flag documents that are complete and no longer needed (for archive or removal). The agent should leverage existing skills (e.g. analyst, documenter, reviewer) and configurable best practices, recommend actions with **user confirmation** for destructive or structural changes, and only **auto-clean** framework-owned artifacts.

## Problem Statement

- **Existing cleanup is narrow:** `tapps-agents cleanup` only prunes workflow-docs and sessions by age/count. It does not help with root clutter, outdated docs, or obsolete/complete documents.
- **Heavy use creates mess:** After "vibe coding" and repeated use of workflows, projects accumulate misplaced files in the root, docs that no longer match the code, and artifacts that are done and no longer needed.
- **No guided best practices:** There is no single, repeatable way to apply project-structure and doc-curation best practices; cleanup is ad hoc and inconsistent.

## Proposed Solution

- **Project Cleanup Agent** (or a simple-mode command, e.g. `*cleanup-project` / `*tidy`) that:
  1. **Recommends** (does not auto-apply) moves for misplaced root-level files based on configurable conventions.
  2. **Identifies** potentially outdated or incorrect docs (e.g. by comparing to code or age) and suggests updates or archival.
  3. **Flags** documents that appear complete/obsolete and proposes archive or removal, with user confirmation.
  4. **Auto-cleans** only framework-owned artifacts (extend existing `cleanup workflow-docs` / `cleanup sessions` behavior as appropriate).
- Leverage **existing agents/skills:** analyst (what's needed vs obsolete), documenter (doc freshness/sync), reviewer (structure/quality), orchestrator/simple-mode for the workflow.
- **Configurable** conventions (e.g. where root files belong, doc layout, retention rules) so the agent adapts to repo type (app vs lib vs monorepo).
- **Safe by default:** destructive or structural actions require explicit user approval; no blind auto-move/delete of user content.

## Use Cases

1. **Post–workflow clutter:** After many simple-mode/workflow runs, user runs project cleanup to get suggestions for moving stray files from root and archiving old workflow docs.
2. **Doc hygiene:** User wants a report of docs that may be outdated (e.g. API docs, README sections) or that are "done" (e.g. one-off planning/feedback docs) and optional archive/remove suggestions.
3. **Onboarding consistency:** New contributors run guided cleanup so their branch matches project layout and doc conventions.
4. **CI or pre-release:** Optional "cleanup check" that reports issues (e.g. misplaced files, stale docs) without making changes, for gate or audit.

## Alternatives Considered

- **Manual cleanup only:** Keeps status quo; does not scale and does not encode best practices.
- **Fully automated moves/deletes:** Too risky and project-specific; could break references or remove needed files. Rejected in favor of recommend-then-confirm.
- **External scripts per repo:** Possible but not reusable; a framework agent provides one place for conventions and patterns.

## Additional Context

- Aligns with existing cleanup: extend the current cleanup story (workflow-docs, sessions) with a broader "project cleanup" capability.
- Fits 14-agent + simple-mode model: either a dedicated agent or a simple-mode workflow that orchestrates analyst, documenter, reviewer.
- Best practices and "where things belong" should be configurable (e.g. in `.tapps-agents/` or project config) so different repo layouts are supported.

## Implementation Notes

- **Scope:** Start with recommendations and reporting; auto-apply only for framework-owned artifacts. Add move/archive/delete only with explicit user confirmation and clear preview/dry-run.
- **Skills to leverage:** @analyst (requirements/obsolete detection), @documenter (doc sync/freshness), @reviewer (structure/quality), @orchestrator or simple-mode for sequencing.
- **Output:** Report or checklist (e.g. markdown/JSON) listing suggested moves, stale/done docs, and proposed archive/removals; optional interactive confirm step for applying changes.
- **Configuration:** New or extended config section for cleanup conventions (e.g. `root_file_rules`, `doc_retention`, `archive_paths`) to keep behavior project-aware and safe.
