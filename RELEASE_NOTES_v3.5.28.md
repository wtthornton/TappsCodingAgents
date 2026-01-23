# Release 3.5.28 - 2026-01-24

## Installation & Setup Experience Improvements

This release focuses on improving the installation and setup experience based on user feedback. Key improvements make it easier to get started with TappsCodingAgents, especially on Windows and when using the framework as a subdirectory.

### Added

- **Working directory detection for init** - When run from the TappsCodingAgents framework directory (e.g. as a subdirectory), init warns and offers to initialize in the detected project root (`is_framework_directory`, `detect_project_root`).
- **Pre-installation Python check** - `scripts/check_prerequisites.py` checks for Python 3.13+; on Windows suggests `py -3.13 -m pip install -e .` when found.
- **`tapps-agents docs`** - Prints documentation URL; `--open` opens in the default browser.
- **`.gitattributes` export-ignore** - Excludes docs, tests, examples, demo, scripts, requirements, tools, and root meta files from `git archive` (MANIFEST.in unchanged for sdist).

### Changed

- **Init success messaging** - Phased: "Core setup complete. Optional: Context7, Node.js, dev extras. Run 'tapps-agents doctor' for details." when only optional components are missing; MCP/npx no longer treated as hard errors.
- **Init "What's next"** - "Optional enhancements" block: CONTEXT7_API_KEY, `pip install -e \".[dev]\"`, Node.js; MCP/npx described as optional.
- **Context7 setup prompt** - Brief explanation of library-docs benefit and that it is optional.
- **MCP/Node messaging** - "MCP optional features not configured" / "MCP servers are optional; the framework works without them" ( [WARN] instead of [ERROR] when only optional MCP/Node missing).
- **Packaging** - Removed broad `"*"` from `[tool.setuptools.package-data]`; `tapps_agents` now `resources/**/*`, `experts/**/*`. `MANIFEST.in`: `global-exclude` for AGENTS.md, CHANGELOG.md, CLAUDE.md, CLAUDE.local.example.md, CONTRIBUTING.md, SECURITY.md.

### Documentation

- **README / QUICK_START** - Python 3.13+ and `py -3.13` (Windows) / `python3.13` (Linux/macOS); "run init from project root" with correct/wrong examples; `check_prerequisites.py`; "After installing, run `tapps-agents doctor`"; Windows and Linux/macOS install subsections.
- **Init --help** - Note: "Run init from your project root, not from the TappsCodingAgents framework directory."

---

**Full Changelog**: https://github.com/wtthornton/TappsCodingAgents/blob/main/CHANGELOG.md#3528---2026-01-24
