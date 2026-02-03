# Epic Simple-Mode Fixes and Recommendations

**Date:** 2026-02-03  
**Context:** Running `tapps-agents simple-mode epic stories/enh-002-critical-enhancements.md --auto` exposed two bugs and led to follow-up improvements.

---

## Fixes Applied

### 1. EpicOrchestrator constructor (CLI)

**Problem:** The CLI passed `quality_threshold`, `critical_service_threshold`, and `enforce_quality_gates` into `EpicOrchestrator()`, but the Simple Mode wrapper extends `SimpleModeOrchestrator`, which only accepts `project_root` and `config`. This caused:

```text
TypeError: SimpleModeOrchestrator.__init__() got an unexpected keyword argument 'quality_threshold'
```

**Fix:** Removed those keyword arguments from the `EpicOrchestrator()` call in `tapps_agents/cli/commands/simple_mode.py`. Those options are already provided via `intent.parameters` and used inside `EpicOrchestrator.execute()`.

### 2. Workflow parsing in epic orchestrator

**Problem:** The core epic orchestrator called `parser.parse_workflow(workflow_yaml)`, but `WorkflowParser` has no such method. It exposes:

- `parse(content: dict, file_path=...)` — expects a dict
- `parse_file(file_path: Path)` — reads and parses a file

**Fix:**

- In `tapps_agents/epic/orchestrator.py`: use `WorkflowParser.parse_yaml(workflow_yaml)` so the YAML string is parsed in one step.
- Added `WorkflowParser.parse_yaml(yaml_string: str, file_path=...)` in `tapps_agents/workflow/parser.py` so callers with a YAML string have a single, clear API and don’t need to remember `yaml.safe_load` + `parse()`.

### 3. Regression test

**Added:** `tests/unit/epic/test_orchestrator_story_workflow.py` — asserts that the epic story workflow YAML format parses correctly with `WorkflowParser.parse_yaml()`. This guards against reintroducing a `parse_workflow`-style call or changing the parser API without updating the epic.

---

## Recommendations

### Code and API

1. **Orchestrator base vs. epic-specific options**  
   Consider letting `SimpleModeOrchestrator` accept `**kwargs` and forward them, or document that subclasses (e.g. `EpicOrchestrator` in simple_mode) must not require constructor args beyond `project_root` and `config` when used from the CLI. That keeps the CLI and orchestrator in sync and avoids similar TypeErrors.

2. **WorkflowParser usage**  
   For in-memory YAML strings, use `WorkflowParser.parse_yaml(yaml_string)`. For files, use `WorkflowParser.parse_file(path)`. For an already-loaded dict, use `WorkflowParser.parse(dict)`. Avoid ad-hoc `yaml.safe_load` + `parse` at call sites; use `parse_yaml` so the contract is clear and one place can change if YAML loading behavior changes.

3. **Epic execution timeout**  
   Epic runs with many stories and full workflows can exceed 10 minutes. For CI or scripts, either run the epic in the background, increase the timeout, or add a `--max-stories` (or similar) option to run a subset for validation.

### Operations

4. **Running full epics**  
   Prefer running `tapps-agents simple-mode epic <epic.md> --auto` from a terminal (or a long-timeout runner) so it can run to completion. The report is written to `stories/epic-<N>-report.json` when the run finishes.

5. **Worktree cleanup**  
   Epic execution creates worktrees under `.tapps-agents/worktrees/`. If you see permission or “path not found” errors involving those paths, consider cleaning old worktrees (e.g. via existing cleanup scripts or a scheduled job).

### Testing

6. **Epic CLI path**  
   Add an integration or e2e test that invokes the epic CLI with a minimal epic file (e.g. one story) and asserts non-zero completion or report generation, so the full CLI → Simple Mode → EpicOrchestrator → WorkflowParser path is exercised.

7. **Config loading in tests**  
   Unit tests that need `EpicOrchestrator` with a custom root should either pass a mocked `config` or ensure a valid minimal config file exists under the test root; `load_config(tmp_path)` can fail or behave oddly when the path is a bare temp dir.

---

## Files Touched

- `tapps_agents/cli/commands/simple_mode.py` — epic handler: removed extra orchestrator kwargs.
- `tapps_agents/epic/orchestrator.py` — use `WorkflowParser.parse_yaml(workflow_yaml)`; removed local `yaml` import.
- `tapps_agents/workflow/parser.py` — added `parse_yaml(yaml_string, file_path=...)`.
- `tests/unit/epic/test_orchestrator_story_workflow.py` — new test for story workflow YAML parsing.

---

## Follow-up: Epic .md Execution Status (2026-02-03)

**Recommendation implemented:** Sync execution status from report JSON into the epic markdown.

1. **Execution status note** – Added to `stories/enh-002-critical-enhancements.md`: completion is in `stories/epic-2-report.json`; run `tapps-agents simple-mode epic-status <path>` to sync into the .md.
2. **`epic-status` command** – `tapps-agents simple-mode epic-status <epic.md>` reads the report (default: same dir, `epic-N-report.json`) and adds/updates `**Execution status:** done | failed` for each story in the markdown.
3. **Module** – `tapps_agents/epic/markdown_sync.py`: `update_epic_markdown_from_report(epic_path, report_path=None, project_root=None)`.

After running an epic, run `simple-mode epic-status` to keep the .md in sync with the report.

**Monitor a run in progress:** The report file is updated as stories complete. To watch it:
- PowerShell: `Get-Content stories\epic-2-report.json -Wait -Tail 20`
- Bash: `tail -f stories/epic-2-report.json`

## References

- Epic workflow: `@simple-mode *epic <epic-doc.md>`, CLI: `tapps-agents simple-mode epic <path> [--auto]`
- Epic status sync: `tapps-agents simple-mode epic-status <path>`; module: `tapps_agents/epic/markdown_sync.py`
- Workflow parser: `tapps_agents/workflow/parser.py` (ADR-004 YAML-first workflows)
- Simple Mode orchestrators: `tapps_agents/simple_mode/orchestrators/base.py` (base only takes `project_root`, `config`)
