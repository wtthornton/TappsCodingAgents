# Installation Feedback – Implementation Plan

**Source:** `INSTALLATION_FEEDBACK.md` (from Site24x7/TappsCodingAgents install experience)  
**Version Tested in Feedback:** v3.5.27  
**Date:** 2026-01-24

---

## Overview

This plan turns the installation and setup feedback into concrete, verified changes. Each item was checked against the current TappsCodingAgents codebase and packaging. Only changes that are accurate and desirable are included; rejected items are listed with reasons.

---

## 1. Verified Items (Include in Implementation)

### High Priority

#### 1.1 Working Directory Detection for `init` (Critical)

**Feedback:** When TappsCodingAgents is used as a subdirectory (e.g. `Site24x7/TappsCodingAgents/`), running `init` from the framework directory writes `.claude/`, `.cursor/`, `.tapps-agents/` into the framework tree instead of the project root.

**Verification:** No logic in `tapps_agents` detects “running from framework directory” or suggests the parent as project root. `init` uses `Path.cwd()` as project root.

**Planned changes:**
- Add `is_framework_directory(path: Path) -> bool`: e.g. `path.name == "TappsCodingAgents"`, `(path / "tapps_agents").exists()`, `(path / "pyproject.toml").exists()` and `"tapps-agents"` in project name in `pyproject.toml`.
- Add `detect_project_root(start_path: Path) -> Path | None`: walk up from `start_path`, look for `.git`, `src/`, `app/`, etc., and exclude the framework directory.
- In `handle_init_command` (or equivalent): if `Path.cwd()` is a framework directory and a parent project root is found, **warn** and **offer** to run init in the detected project root (with an explicit choice to continue in cwd or cancel).
- **Do not** auto‑change cwd; only suggest and, if the user agrees, run init with `project_root=detected_root`.

**Docs:** Add a short “Run init from your project root” note in README Quick Start and in `tapps-agents init --help`, with “wrong” and “right” examples (e.g. run from `your-project/`, not from `your-project/TappsCodingAgents/`).

**Files:** `tapps_agents/core/init_project.py`, `tapps_agents/cli/commands/top_level.py`, `README.md`, `docs/guides/QUICK_START.md`.

---

#### 1.2 Pre-Installation Python Version Check

**Feedback:** `requires-python = ">=3.13"` is only surfaced when `pip install` fails. Users on 3.11 or without 3.13 in PATH hit an opaque error.

**Verification:** `pyproject.toml` has `requires-python = ">=3.13"`. No pre-check script or friendly error before `pip`.

**Planned changes:**
- Add `scripts/check_prerequisites.py` that:
  - Checks `sys.version_info >= (3, 13)`; if not, on Windows tries `py -3.13 --version` and, if found, prints the exact command to use (e.g. `py -3.13 -m pip install -e .`).
  - On failure: print that 3.13+ is required, link to python.org, and suggest `py -3.13` (Windows) or `python3.13` (Linux/macOS).
- **Do not** change `requires-python` or add custom `setup.py`/`install` logic; keep the script opt‑in and document it.

**Docs:** README Quick Start: “Ensure Python 3.13+ (`python --version`). On Windows with multiple versions: `py -3.13 -m pip install -e .`.” Add a line: “Optionally run `python scripts/check_prerequisites.py` before installing.”

**Files:** `scripts/check_prerequisites.py` (new), `README.md`, `docs/guides/QUICK_START.md`.

---

#### 1.3 README Installation Instructions

**Feedback:** README should spell out Python 3.13, `py -3.13` on Windows, and `python -m tapps_agents.cli` when the `tapps-agents` entry point is not on PATH.

**Verification:** README already mentions “if command not found use `python -m tapps_agents.cli`” and points to `docs/TROUBLESHOOTING_CLI_INSTALLATION.md`. It does **not** explicitly say “3.13+”, “`py -3.13`”, or “run init from project root, not from the framework directory”.

**Planned changes:**
- In Quick Start: require “Python 3.13+” and show `py -3.13 -m pip install -e .` (Windows) and `python3.13 -m pip install -e .` (Linux/macOS) as alternatives.
- Keep and emphasize: “If `tapps-agents` is not found, use `python -m tapps_agents.cli`.”
- Add: “Run `init` from your **project root**, not from the TappsCodingAgents framework directory.” Reuse the same “wrong vs right” examples as in 1.1.

**Files:** `README.md`, `docs/guides/QUICK_START.md`.

---

#### 1.4 Phased Init Output and Clearer Success / Optional States

**Feedback:** Init ends with “[X] Init complete (with errors)” and mixes required vs optional (Context7, Node/npx, dev tools). Users cannot tell if the setup is usable.

**Verification:** `INIT_IMPROVEMENTS_IMPLEMENTATION.md` improved MCP/Context7 and npx; there is no phased “Core / Optional / Dev” breakdown and no clear “Core setup complete” vs “optional enhancements” messaging.

**Planned changes:**
- Group init output into phases, e.g.:
  - **Phase 1 – Core:** Project config, Cursor Rules, Cursor Skills, workflow presets, MCP config file.
  - **Phase 2 – Optional:** Context7 API key, Node/npx (for MCP servers).
  - **Phase 3 – Dev tools:** pip-audit, pipdeptree, ruff, mypy, etc.
- Final line when core succeeds: e.g. “Core setup complete. Optional: Context7, Node.js, dev extras. Run `tapps-agents doctor` for details.”
- Replace “[X] Init complete (with errors)” with a neutral line when only optional/dev items are missing, e.g. “Init complete. Some optional components are not configured; run `tapps-agents doctor` for next steps.”

**Files:** `tapps_agents/core/init_project.py`, `tapps_agents/cli/commands/top_level.py` (or wherever init result is printed).

---

#### 1.5 Post-Init “What’s Next” and Optional Enhancements

**Feedback:** After init, users need a short “what to do next” and how to enable optional features.

**Planned changes:**
- After init, print a short “What’s next” block: e.g. “Open Cursor and try `@simple-mode *build \"...\"` or `@reviewer *help`”; “Optional: set `CONTEXT7_API_KEY`, `pip install -e \".[dev]\"`, Node.js for MCP”; “Run `tapps-agents doctor` anytime.”
- Reuse or reference `docs/guides/QUICK_START.md`, `docs/SIMPLE_MODE_GUIDE.md`, `docs/TROUBLESHOOTING.md` (or equivalent).

**Files:** `tapps_agents/cli/commands/top_level.py` (or init result printing).

---

### Medium Priority

#### 2.1 Context7 API Key Prompt (Clarity Only)

**Feedback:** The Context7 prompt should briefly explain what it is and why it helps (library docs, better suggestions, caching).

**Verification:** `offer_context7_setup` in `mcp_setup.py` and init flow exist; the on‑screen text can be more informative.

**Planned changes:**
- In the Context7 prompt: add 2–3 lines on “library documentation for agents, better suggestions, optional.” Keep options: env var (recommended), write to MCP config, skip. No behavior change to MCP or init logic.

**Files:** `tapps_agents/core/mcp_setup.py` (or wherever the Context7 prompt text lives).

---

#### 2.2 MCP / Node.js: Informational, Not Errors

**Feedback:** When Node/npx is missing, MCP-related messages look like hard errors even though the framework works without MCP.

**Verification:** Init and doctor already distinguish some MCP/Node checks; wording can still read as “error” when it’s optional.

**Planned changes:**
- When Node/npx is not found: use `[INFO]` or `[WARN]` and state that “MCP servers (Context7, Playwright, etc.) are optional; the framework works without them. Install Node.js from https://nodejs.org/ to enable MCP.”
- Avoid `[ERROR]` for “Node.js not installed” when the rest of init has succeeded.

**Files:** `tapps_agents/core/init_project.py`, `tapps_agents/core/mcp_setup.py`, `tapps_agents/core/doctor.py` (or wherever MCP/Node checks are reported).

---

#### 2.3 Documentation Examples: `tapps-agents` and `python -m tapps_agents.cli`

**Feedback:** Docs should show both `tapps-agents` and `python -m tapps_agents.cli` so users without the entry point on PATH can copy‑paste.

**Verification:** README and some docs already use `python -m tapps_agents.cli` in places; usage is not consistent everywhere.

**Planned changes:**
- In `docs/`, `AGENTS.md`, and other user-facing guides: where CLI commands are shown, use either “`tapps-agents &lt;cmd&gt;` (or `python -m tapps_agents.cli &lt;cmd&gt;` if the command is not found)” or a short “On some setups, use `python -m tapps_agents.cli` instead of `tapps-agents`” note near the first CLI example.
- Prefer minimal duplication (one note + one form in examples) rather than repeating both forms in every command.

**Files:** `docs/README.md`, `docs/guides/QUICK_START.md`, `AGENTS.md`, `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`, and other docs that show CLI usage.

---

#### 2.4 Platform-Aware (Windows) Installation Notes

**Feedback:** Examples assume `python` or `python3`; on Windows, `py -3.13` is often needed.

**Verification:** README does not have a dedicated “Windows” subsection with `py -3.13` and PowerShell-friendly commands.

**Planned changes:**
- Add a short “Windows” (and optionally “Linux/macOS”) subsection in README or `docs/guides/QUICK_START.md`, e.g.:
  - Windows: `py -3.13 --version`, `py -3.13 -m pip install -e .`, `py -3.13 -m tapps_agents.cli init`.
  - Linux/macOS: `python3.13 --version`, `python3.13 -m pip install -e .`, `python3.13 -m tapps_agents.cli init`.

**Files:** `README.md`, `docs/guides/QUICK_START.md`.

---

#### 2.5 pyproject.toml `package-data` and MANIFEST

**Feedback:** `"*" = ["*.yaml", "*.yml", "*.md", "*.mdc", "*.j2"]` is too broad; also exclude docs/tests/examples from the distributed package.

**Verification:**
- `pyproject.toml`: `[tool.setuptools.packages.find]` has `include = ["tapps_agents*"]`, `exclude = ["tests*", "examples*"]`. `package-data` has `"*"` and `"tapps_agents" = ["resources/**/*"]`, `"tapps_agents.resources" = ["**/*"]`.
- `MANIFEST.in` already has `recursive-exclude` for `tests`, `docs`, `examples`, `scripts`, `workflows`, `requirements`, `templates`, etc. `recursive-include tapps_agents/resources *` is present. Workflow presets are under `tapps_agents/resources/workflows/presets` and are packaged.

**Planned changes:**
- **package-data:** Remove or narrow the `"*"` entry so it does not pull in root-level or unrelated `*.md`/`*.yaml`. Restrict to `tapps_agents` (and its subpackages) as needed for resources and experts. Keep `"tapps_agents" = ["resources/**/*"]` and `"tapps_agents.resources" = ["**/*"]`.
- **MANIFEST.in:** Add `global-exclude` for root-level files that must not appear in sdist: e.g. `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CLAUDE.local.example.md`, `CONTRIBUTING.md`, `SECURITY.md`. **Do not** add `recursive-exclude templates *` or `recursive-exclude workflows *` beyond what already exists; presets are correctly served from `tapps_agents/resources`; templates are a separate concern (see 2.6 and 3).

**Files:** `pyproject.toml`, `MANIFEST.in`.

---

#### 2.6 Templates and PyPI: Clarification Only (No MANIFEST Exclusions)

**Feedback:** “Exclude `templates`” and “templates are required at runtime.”

**Verification:**
- `MANIFEST.in` already has `recursive-exclude templates *`. `templates/` is at repo root, not under `tapps_agents`.
- Presets: `PresetLoader` and `init_workflow_presets` use `_resource_at("workflows", "presets")`; presets live in `tapps_agents/resources/workflows/presets` and are packaged. No change needed for presets.
- Templates: `template_selector`, `project_type_detector`, `role_loader` use `framework_root / "templates"` (e.g. `templates/tech_stacks`, `templates/project_types`, `templates/user_roles`, `templates/agent_roles`). For a PyPI install, `framework_root` is inside `site-packages`; `templates/` is not there, so those paths are `None`/missing and init falls back to `get_default_config()` without project-type or tech-stack template merging. Init still completes.

**Planned changes:**
- **Do not** add further MANIFEST exclusions for `templates` or `workflows`. Do not add `.gitattributes` `export-ignore` for `templates` or `workflows` so we can later include them in sdist if needed.
- **Optional, medium/low:** To get template merging on PyPI installs, package `templates/` (or a minimal subset) under `tapps_agents/resources/templates` and update `template_selector`, `project_type_detector`, `role_loader` to prefer `_resource_at("templates", ...)` when `framework_root / "templates"` is missing. This is a separate, backwards‑compatible enhancement; not required for this plan.

**Files:** None for “exclusions.” For the optional enhancement: `tapps_agents/resources`, `tapps_agents/core/template_selector.py`, `tapps_agents/core/project_type_detector.py`, `tapps_agents/core/role_template_loader.py`, `tapps_agents/core/role_loader.py`.

---

### Low Priority

#### 3.1 Dev Tools Explanation in Init

**Feedback:** Init warns about missing pip-audit, pipdeptree, etc., without saying they are optional and for dev/contributors.

**Planned changes:**
- In init (or in the Phase 3 / dev-tools section): add one line, e.g. “Dev tools (pip-audit, pipdeptree, ruff, mypy, pytest, etc.) are optional; install with `pip install -e \".[dev]\"` for framework development and contributing. Not required for using the framework.”

**Files:** `tapps_agents/core/init_project.py` or init output.

---

#### 3.2 Post-Install Verification and “Run doctor”

**Feedback:** Users want to quickly confirm the install works.

**Verification:** `tapps-agents doctor` exists and is documented. There is no dedicated “post-install” hook or script.

**Planned changes:**
- **Documentation only:** In README (and optionally in a short “Post-install” note): “After installing, run `tapps-agents doctor` (or `python -m tapps_agents.cli doctor`) to verify the setup.”
- **Optional:** Add a `tapps-agents verify` (or `post-install`) that runs a minimal subset of doctor checks and prints “Installation looks good” or “Run `tapps-agents doctor` for details.” Do not modify pip or use setuptools post-install hooks; keep it as an explicit, opt‑in command. If we add it, document in README.

**Files:** `README.md`, `docs/guides/QUICK_START.md`; optionally `tapps_agents/cli/commands/top_level.py` and parsers for `verify`/`post-install`.

---

#### 3.3 `tapps-agents docs` Command

**Feedback:** Provide a way to open or link to the main documentation.

**Planned changes:**
- Add `tapps-agents docs` that prints the docs URL (e.g. `https://github.com/wtthornton/TappsCodingAgents/tree/main/docs`) and, if `webbrowser` is available and a flag is set, opens it. Minimal implementation.

**Files:** `tapps_agents/cli/commands/top_level.py`, `tapps_agents/cli/parsers/top_level.py`.

---

#### 3.4 Actionable Python Version Error (Best-Effort)

**Feedback:** When `pip` fails with “requires a different Python,” the message is minimal.

**Verification:** The error comes from pip/setuptools; we cannot replace it. We can only document and provide `check_prerequisites.py`.

**Planned changes:**
- In `scripts/check_prerequisites.py`: if the current interpreter is &lt; 3.13, print an error block that mirrors the desired style: “Required: Python 3.13+; Detected: X.Y.Z”; “Solutions: (1) Install 3.13+ from python.org, (2) Windows: `py -3.13 -m pip install -e .`, (3) Linux/macOS: `python3.13 -m pip install -e .`.” Optionally, on Windows, run `py -3.13 --version` and, if it works, append “Found: use `py -3.13 -m pip install -e .`.”
- No change to pip or to `requires-python`.

**Files:** `scripts/check_prerequisites.py`.

---

#### 3.5 .gitattributes `export-ignore` (Optional)

**Feedback:** Use `export-ignore` so `git archive` omits dev-only content.

**Verification:** Not used for setuptools sdist in the current layout; `MANIFEST.in` controls sdist. `export-ignore` only affects `git archive`.

**Planned changes:**
- **Optional:** In `.gitattributes`, add `export-ignore` for: `docs/`, `tests/`, `examples/`, `demo/`, `scripts/`, `requirements/` (the directory), `tools/`, and root `AGENTS.md`, `CHANGELOG.md`, `CLAUDE.md`, `CLAUDE.local.example.md`, `CONTRIBUTING.md`, `SECURITY.md`, `pytest.ini`. **Do not** add `export-ignore` for `templates/` or `workflows/` so we retain the option to include them in source archives later.

**Files:** `.gitattributes`.

---

## 2. Rejected or Modified Feedback (Do Not Implement As-Is)

### 2.1 Excluding `templates/` or `workflows/` Beyond Current MANIFEST

**Feedback:** “recursive-exclude templates *”, “recursive-exclude workflows *”, and similar in MANIFEST or `.gitattributes` to reduce package size.

**Reason to reject as stated:**
- `MANIFEST.in` already has `recursive-exclude templates *` and `recursive-exclude workflows *` for the **repo-root** `templates/` and `workflows/` directories.
- Workflow **presets** are correctly served from `tapps_agents/resources/workflows/presets` and are **included** via `recursive-include tapps_agents/resources *`. Excluding them would break PyPI behavior.
- The feedback both says “templates are required” and “exclude templates.” We do not add more exclusions for `templates` or `workflows`; we may later **include** templates (e.g. via `tapps_agents/resources/templates`) for PyPI parity. See §1, 2.6.

---

### 2.2 Adding `templates` or `workflows` to `[tool.setuptools.package-data]`

**Feedback:**  
`"templates" = ["**/*.yaml", ...]`, `"workflows" = ["**/*.yaml", ...]`.

**Reason to reject:**  
`templates` and `workflows` at repo root are **not** Python packages. `package-data` keys must be package names. We would need to either (a) ship templates under `tapps_agents.resources` and reference them there, or (b) include `templates/`/`workflows/` via `MANIFEST.in` and a different setuptools mechanism. Adopting the suggested `package-data` keys as-is would be invalid. We only narrow the `"*"` entry and keep `tapps_agents`/`tapps_agents.resources` (see §1, 2.5).

---

### 2.3 Package Size and “60–80% Smaller” for Editable Installs

**Feedback:** Much smaller installation by excluding docs, tests, examples, etc.

**Reason to modify:**
- For **editable** installs (`pip install -e .`), the “installation” is the project tree; we cannot remove `docs/`, `tests/`, etc. from the clone. Size claims for editable are misleading.
- For **sdist/wheel** (PyPI or `pip install .`), `MANIFEST.in` and `packages.find`/`package-data` already exclude most of that. We can tighten with `global-exclude` for root `.md` (see 2.5) and document that “for a smaller install, use a published wheel/sdist rather than an editable install from the repo.”
- We do **not** promise “60–80% smaller” in any official text; we only describe sdist/wheel as the appropriate way to get a minimal install.

---

### 2.4 Custom `install.py` or setuptools “Python &lt; 3.13” Abort

**Feedback:** An “install.py” or setup logic that detects Python &lt; 3.13 and exits with a custom message before dependency resolution.

**Reason to reject:**  
Adds build/setup complexity and can interfere with pip’s normal resolution. `scripts/check_prerequisites.py` plus README is sufficient and opt‑in. We keep `requires-python = ">=3.13"` and do not add another layer in the install path.

---

### 2.5 Post-Install Hook That Modifies PATH or Auto-Adds Scripts

**Feedback:** Post-install step that detects Scripts dir and “offers to add to PATH” or alters the environment.

**Reason to reject:**  
Modifying PATH or user environment from an install is invasive and platform‑ and shell‑specific. We only document that `tapps-agents` may not be on PATH and that `python -m tapps_agents.cli` is the fallback. Optional: in init or a “first-run” message, print the Scripts path and a one-line suggestion to add it to PATH manually. No automatic changes.

---

### 2.6 Doctor `--fix` or “Apply fixes? [y/N]”

**Feedback:** A `--fix` (or similar) that applies suggested fixes automatically after doctor.

**Reason to reject for this plan:**  
`doctor --suggest-fixes` already exists. Adding an interactive “Apply fixes?” or a `--fix` that touches the system is a larger feature (safety, idempotency, platforms). We only improve the clarity of `--suggest-fixes` output and, if needed, add more concrete command suggestions. No auto-apply in this implementation.

---

### 2.7 Separate `tapps-agents onboarding` Wizard

**Feedback:** New `tapps-agents onboarding` that runs a guided flow (prereqs, init, Context7, dev tools, demo).

**Reason to treat as out of scope:**  
`simple-mode init` and `tapps-agents init` already cover most of this. A separate `onboarding` would largely duplicate init and simple-mode. We prioritize: phased init output, “What’s next,” and docs. A future, thin `onboarding` that mostly delegates to init + doctor + docs could be considered separately; it is not part of this plan.

---

### 2.8 `tapps-agents install-dev` and `tapps-agents test-installation`

**Feedback:** Dedicated commands to install `.[dev]` and to “test” the installation.

**Reason to treat as low priority / out of scope:**
- `install-dev`: Wrapping `pip install -e ".[dev]"` in a custom command has limited benefit; we can document the exact `pip` invocation and, in init, mention “`pip install -e \".[dev]\"` for dev tools.” We do not add `install-dev` in this plan.
- `test-installation`: `tapps-agents doctor` already verifies the environment. An alias or a very small `verify` (see 3.2) would be acceptable; a separate “test-installation” with extra semantics is not needed for now.

---

## 3. Implementation Order

1. **Phase 1 (High impact, low risk)**  
   - 1.1 Working directory detection and init warning/offer  
   - 1.2 `scripts/check_prerequisites.py`  
   - 1.3 README (and QUICK_START) installation and “run init from project root”  
   - 2.5 MANIFEST.in `global-exclude` and pyproject `package-data` narrowing  

2. **Phase 2 (Init UX)**  
   - 1.4 Phased init output and clearer success/optional states  
   - 1.5 Post-init “What’s next”  
   - 2.1 Context7 prompt text  
   - 2.2 MCP/Node as informational  
   - 3.1 Dev tools explanation in init  

3. **Phase 3 (Docs and polish)**  
   - 2.3 Consistent `tapps-agents` / `python -m tapps_agents.cli` in docs  
   - 2.4 Platform-aware (Windows) notes  
   - 3.2 Post-install “run doctor” and optional `verify`  
   - 3.3 `tapps-agents docs`  
   - 3.4 `check_prerequisites.py` error message (actionable Python line)  
   - 3.5 `.gitattributes` `export-ignore` (optional)  

4. **Later / optional**  
   - 2.6 Packaging `templates` under `tapps_agents.resources` for PyPI (medium/low).  
   - Revisit `onboarding`, `install-dev`, `test-installation` only if we see clear user demand.

---

## 4. Files to Touch (Summary)

| Area              | Files |
|-------------------|-------|
| Init / working dir| `tapps_agents/core/init_project.py`, `tapps_agents/cli/commands/top_level.py` |
| Prereqs           | `scripts/check_prerequisites.py` (new) |
| Packaging         | `pyproject.toml`, `MANIFEST.in`, `.gitattributes` (optional) |
| MCP / Context7    | `tapps_agents/core/mcp_setup.py`, `tapps_agents/core/init_project.py`, `tapps_agents/core/doctor.py` |
| Docs              | `README.md`, `docs/guides/QUICK_START.md`, `docs/README.md`, `AGENTS.md`, `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md` |
| CLI               | `tapps_agents/cli/commands/top_level.py`, `tapps_agents/cli/parsers/top_level.py` (for `docs` and optional `verify`) |

---

## 5. References

- `docs/INSTALLATION_FEEDBACK.md` (or `C:\cursor\Site24x7\TappsCodingAgents\docs\INSTALLATION_FEEDBACK.md`) – source feedback  
- `docs/INIT_IMPROVEMENTS_IMPLEMENTATION.md` – existing init/MCP work  
- `docs/INIT_PROCESS_IMPROVEMENTS.md` – init process recommendations  
- `tapps_agents/core/init_project.py` – `_resource_at`, `init_workflow_presets`, template merging  
- `tapps_agents/workflow/preset_loader.py` – preset resolution (framework root vs `tapps_agents.resources`)  
- `tapps_agents/core/template_selector.py`, `project_type_detector.py`, `role_loader.py` – `framework_root / "templates"` usage  

---

**Document version:** 1.0  
**Last updated:** 2026-01-24
