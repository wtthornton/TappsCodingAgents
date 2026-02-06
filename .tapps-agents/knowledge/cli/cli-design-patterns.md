# CLI Design Patterns for TappsCodingAgents

## Overview

TappsCodingAgents CLI uses **argparse** (not Click) with Rich for terminal output. The CLI is structured as:
- `create_root_parser()` → root parser with global flags
- `register_all_parsers()` → 16 parser modules register subcommands
- `route_command()` → dispatches to 28 command handlers

## Entry Point

```
cli/__init__.py → main() → create_root_parser() → register_all_parsers() → parse_args() → route_command()
```

## Argparse Subcommand Groups

### Adding a New Subcommand

1. **Add parser** in `parsers/top_level.py` (or domain-specific parser):

```python
def register_epic_parser(subparsers):
    parser = subparsers.add_parser("epic", help="Epic management commands")
    epic_sub = parser.add_subparsers(dest="epic_command")

    run_parser = epic_sub.add_parser("run", help="Execute an epic document")
    run_parser.add_argument("epic_file")
    run_parser.add_argument("--auto", action="store_true", help="Fully automated")
    run_parser.add_argument("--approved", action="store_true", help="Skip approval")

    status_parser = epic_sub.add_parser("status", help="Show epic status")
    status_parser.add_argument("epic_id", nargs="?")
    status_parser.add_argument("--format", choices=["text", "json"], default="text")
```

2. **Add handler** in `commands/`:

```python
def handle_epic_run(args):
    """Handler for 'tapps-agents epic run <file>'."""
    ...
```

3. **Add route** in `main.py::route_command()`:

```python
if args.command == "epic":
    return handle_epic(args)
```

### Common CLI Options

- `--format {text,json}` — output format
- `--auto` — non-interactive mode
- `--verbose` / `--quiet` — output verbosity
- `--dry-run` — preview without executing

## Rich Output Patterns

### Status Tables

```python
from rich.table import Table
from rich.console import Console

def render_epic_status(state: EpicState):
    console = Console()
    table = Table(title=f"Epic: {state.epic_id}")
    table.add_column("Story", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Score", justify="right")
    for story_id, story in state.stories.items():
        color = {"completed": "green", "running": "yellow", "failed": "red"}.get(story.status, "white")
        table.add_row(story_id, f"[{color}]{story.status}[/]", str(story.quality_score or "-"))
    console.print(table)
```

### Progress Bars

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
    task = progress.add_task("Executing stories...", total=len(stories))
    for story in stories:
        await execute_story(story)
        progress.update(task, advance=1)
```

## Session Lifecycle

`ensure_session_started()` called early in `route_command()`:
- Generates session ID (UUID)
- Fires `SessionStart` hook
- Registers atexit `SessionEnd` handler
- Optionally hydrates task specs to Beads

## Windows Encoding

`main.py` handles Windows UTF-8 encoding at startup for `sys.stdout` and `sys.stderr`.

## Global Flag Reordering

CLI reorders flags for UX: global flags like `--verbose`, `--quiet` are accepted before subcommands.

## Known Issues (2026-02)

### 1. No ExitCode Enum
Uses raw integers. Recommended fix:

```python
from enum import IntEnum

class ExitCode(IntEnum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    USAGE_ERROR = 2
    CONFIG_ERROR = 3
    QUALITY_GATE_FAILED = 4
    TIMEOUT = 5
```

### 2. Inconsistent Error Output
Some commands use `print()`, others `logging`, others `rich.console`.
**Fix:** Standardize on `rich.console.Console` for user-facing; `logging` for debug.

### 3. Missing Input Validation
CLI arguments not validated before passing to handlers.
**Fix:** Add validation layer between argparse and command dispatch.

## Best Practices

1. **Always support `--format json`** for automation/CI
2. **Use ExitCode enum** for consistent exit codes
3. **Streaming output**: Use Rich for interactive, plain text for piped output
4. **Progressive disclosure**: Summary by default, details with `--verbose`
5. **Windows compatibility**: Use ASCII-safe symbols as fallbacks for Unicode
6. **Validate all paths** from CLI args before passing to handlers
7. **Test command dispatch**: Ensure every parser has a corresponding handler

## Related

- `tapps_agents/cli/` — CLI implementation
- `tapps_agents/cli/commands/` — Subcommand modules
- `tapps_agents/cli/parsers/` — Parser modules
- Rich documentation (via Context7)
