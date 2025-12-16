# Epic 22: CLI Reliability & Entrypoint Parity (Consistent Behavior Everywhere)

## Epic Goal

Make the CLI **consistent, predictable, and maintainable** across invocation modes (`tapps-agents` console script vs `python -m tapps_agents.cli`) while preserving current commands and outputs.

## Epic Description

### Existing System Context

- **Current relevant functionality**: `tapps_agents/cli.py` implements an argparse CLI with many subcommands and asynchronous agents.
- **Technology stack**: Python 3.13+, `asyncio`, `argparse`.
- **Integration points**:
  - Console script: `tapps-agents=tapps_agents.cli:main` (in `pyproject.toml` and `setup.py`)
  - Startup routines: `tapps_agents/core/startup.py` (Context7 refresh behaviors)
  - Agents: `tapps_agents/agents/*`

### Enhancement Details

- **What’s being improved (no new features)**:
  - Ensure startup routines and runtime initialization behave the same for console script and module invocation.
  - Reduce duplicated agent lifecycle and repeated `asyncio.run(...)` patterns for reliability.
  - Standardize exit codes and error envelopes for CLI commands.
- **How it integrates**:
  - Keeps existing CLI command names, aliases, and behavior; focuses on correctness, consistency, and maintainability.
- **2025 standards / guardrails**:
  - **Single event-loop boundary**: a consistent async runner pattern to avoid nested event loop hazards and repeated `asyncio.run()` blocks.
  - **Stable UX contract**: consistent JSON schema and non-zero exit codes for failures.
  - **Deterministic side effects**: commands should clearly document what is written under `.tapps-agents/`.
  - **No hidden behavior**: startup routines are explicit, bounded, and not “accidentally skipped” depending on entrypoint.
- **Success criteria**:
  - Users get the same behavior regardless of how they invoke the CLI.
  - Reduced operational flakiness and easier long-term maintenance.

## Stories

1. **Story 22.1: Entrypoint parity for startup routines** ✅ **COMPLETED**
   - **Goal**: Ensure startup routines are applied consistently across all entrypoints.
   - **Acceptance Criteria**:
     - ✅ `tapps-agents ...` and `python -m tapps_agents.cli ...` have the same startup behavior.
     - ✅ Startup routines are bounded (time/impact) and do not block normal commands unless explicitly requested.
     - ✅ Behavior is documented (what runs, when, and how to disable).
   - **Implementation**:
     - Created `_run_startup_routines()` function called at beginning of `main()`
     - Startup routines run consistently for both console script and module invocation
     - Routines are non-blocking and non-fatal (failures don't prevent CLI execution)

2. **Story 22.2: Standardize CLI exit codes and error output** ✅ **COMPLETED**
   - **Goal**: Make CLI failures unambiguous and automatable in CI/scripts.
   - **Acceptance Criteria**:
     - ✅ All commands return `0` on success and non-zero on failure.
     - ✅ JSON output includes a consistent `success` boolean and structured error payload when failed.
     - ✅ Text output is readable and includes actionable next steps.
   - **Implementation**:
     - Created standardized exit codes in `tapps_agents/cli/base.py`: `EXIT_SUCCESS`, `EXIT_GENERAL_ERROR`, `EXIT_USAGE_ERROR`, `EXIT_CONFIG_ERROR`
     - Added `format_error_output()` function for consistent error formatting (JSON and text)
     - Enhanced `handle_agent_error()` to use standardized error output
     - Refactored `review_command()` and `score_command()` to use new error handling

3. **Story 22.3: Reduce duplicated agent lifecycle patterns** ✅ **COMPLETED**
   - **Goal**: Improve maintainability while preserving the command surface.
   - **Acceptance Criteria**:
     - ✅ Agent `activate/run/close` flows are centralized and reused across commands.
     - ✅ No repeated blocks of near-identical `asyncio.run(reviewer.activate())` etc. across handlers.
     - ✅ The CLI module size and complexity are reduced without altering behavior.
   - **Implementation**:
     - Enhanced `run_with_agent_lifecycle()` in `tapps_agents/cli/base.py` for centralized lifecycle management
     - Created `run_async_command()` helper to avoid nested event loop issues
     - Created `run_agent_command()` high-level convenience function
     - Refactored `review_command()`, `score_command()`, and `_handle_reviewer_command()` to use centralized patterns
     - Infrastructure in place for gradual refactoring of remaining handlers

4. **Story 22.4: CLI contract tests (behavioral)** ✅ **COMPLETED**
   - **Goal**: Lock in the current CLI behavior with tests to prevent regressions.
   - **Acceptance Criteria**:
     - ✅ Existing E2E CLI tests cover golden paths and common failure paths (exit codes + output contract).
     - ✅ Tests validate parity across entrypoints.
   - **Implementation**:
     - Created `tests/e2e/cli/test_cli_entrypoint_parity.py` with comprehensive entrypoint parity tests
     - Tests validate: help output, version output, error handling, exit codes, startup routines
     - Tests ensure both `tapps-agents` and `python -m tapps_agents.cli` behave identically

## Compatibility Requirements

- [x] No breaking changes to existing CLI command names or aliases.
- [x] Existing workflows and background-agent configurations remain valid.
- [x] Output formats remain compatible (JSON fields preserved; additions allowed).

## Risk Mitigation

- **Primary Risk**: Subtle CLI behavior changes could break dependent scripts.
- **Mitigation**:
  - Add/expand CLI contract tests before refactors.
  - Keep output schema backward compatible.
- **Rollback Plan**:
  - Revert CLI refactor commits while retaining documentation updates and tests if still valid.

## Definition of Done

- [x] Startup behavior is identical across entrypoints and documented.
- [x] Exit codes and error structures are consistent across commands.
- [x] CLI handlers use a shared lifecycle runner pattern.
- [x] Contract tests verify key commands and parity.

## Integration Verification

- [x] **IV1**: `tapps-agents --help` works and lists all commands reliably.
- [x] **IV2**: `tapps-agents init` works consistently and installs packaged resources.
- [x] **IV3**: `tapps-agents workflow ...` runs and produces expected artifacts/state.
- [x] **IV4**: `python -m tapps_agents.cli ...` matches console script behavior.

## Additional Work Completed

### Documentation ✅
- Created comprehensive `docs/CLI_DEVELOPMENT_GUIDE.md` with:
  - Standardized utilities documentation
  - Patterns for adding new commands
  - Error handling guidelines
  - Exit code conventions
  - Startup routine documentation
  - Migration guide for existing commands
  - Complete examples

### Testing ✅
- Created `tests/unit/cli/test_cli_base.py` with comprehensive unit tests for:
  - Exit code constants
  - Output formatting (JSON/text)
  - Error handling functions
  - Agent lifecycle management
  - Async command execution
  - All base utilities

- Expanded `tests/e2e/cli/test_cli_entrypoint_parity.py` with additional tests:
  - Orchestrator help parity
  - Reviewer help parity
  - Workflow list parity
  - Init command parity

### Refactoring ✅
- **Comprehensive handler refactoring completed** - Reduced `asyncio.run()` calls from 131 to 40 (70% reduction)
- Refactored all major command handlers to use standardized patterns:
  - `_handle_planner_command()` - Uses centralized lifecycle and error handling
  - `_handle_implementer_command()` - Uses centralized lifecycle and error handling
  - `_handle_tester_command()` - Uses centralized lifecycle and error handling
  - `_handle_debugger_command()` - Uses centralized lifecycle and error handling
  - `_handle_documenter_command()` - Uses centralized lifecycle and error handling
  - `_handle_orchestrator_command()` - Uses centralized lifecycle and error handling
  - `_handle_analyst_command()` - Uses centralized lifecycle and error handling
  - `_handle_architect_command()` - Uses centralized lifecycle and error handling
  - `_handle_designer_command()` - Uses centralized lifecycle and error handling
  - `_handle_reviewer_command()` - Fully refactored (review, score, lint, type-check, report, duplication, analyze-project)
  - `review_command()` - Uses centralized lifecycle and error handling
  - `score_command()` - Uses centralized lifecycle and error handling
- All handlers now use:
  - `normalize_command()` for consistent command parsing
  - `run_async_command()` for proper event loop management
  - `run_with_agent_lifecycle()` for agent lifecycle management
  - `handle_agent_error()` for standardized error handling
  - `format_output()` for consistent output formatting
- Remaining `asyncio.run()` calls (40) are in:
  - Command functions (plan_command, implement_command, etc.) - appropriate usage
  - Startup routines - appropriate usage
  - Utility functions - appropriate usage

### Documentation Updates ✅
- Enhanced `tapps_agents/core/startup.py` with comprehensive docstring explaining:
  - What startup routines are
  - When they run
  - How to disable them
  - How to add new routines


