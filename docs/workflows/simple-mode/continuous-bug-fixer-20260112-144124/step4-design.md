# Step 4: Design Specifications - Continuous Bug Finder and Fixer

## API Specifications

### CLI Command Interface

**Command:** `tapps-agents continuous-bug-fix`

**Alias:** `tapps-agents bug-fix-continuous` (optional)

**Usage:**
```bash
tapps-agents continuous-bug-fix [OPTIONS]
```

**Options:**
- `--test-path <path>`: Test directory or file to run (default: `tests/`)
- `--max-iterations <n>`: Maximum loop iterations (default: `10`)
- `--commit-strategy <strategy>`: Commit strategy - `one-per-bug` or `batch` (default: `one-per-bug`)
- `--no-commit`: Skip commits (dry-run mode)
- `--format <format>`: Output format - `json` or `text` (default: `text`)
- `--help`: Show help text

**Examples:**
```bash
# Basic usage
tapps-agents continuous-bug-fix

# Custom test path and max iterations
tapps-agents continuous-bug-fix --test-path tests/unit/ --max-iterations 5

# Batch commit strategy
tapps-agents continuous-bug-fix --commit-strategy batch

# Dry run (no commits)
tapps-agents continuous-bug-fix --no-commit
```

---

## Component APIs

### 1. BugFinder API

**Module:** `tapps_agents.continuous_bug_fix.bug_finder`

**Classes:**

#### `BugInfo` (Dataclass)

```python
@dataclass
class BugInfo:
    """Information about a detected bug."""
    file_path: str          # Source file with bug (relative to project root)
    error_message: str      # Error description/message
    test_name: str          # Test function name that failed
    test_file: str          # Test file path (relative to project root)
    line_number: int | None # Line number in source file (if available)
    traceback: str | None   # Full traceback (optional, for debugging)
```

#### `BugFinder` (Class)

```python
class BugFinder:
    """Finds bugs by running tests and parsing failures."""
    
    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ) -> None:
        """
        Initialize BugFinder.
        
        Args:
            project_root: Project root directory (default: current directory)
            config: Project configuration (optional)
        """
    
    async def find_bugs(
        self,
        test_path: str | None = None,
    ) -> list[BugInfo]:
        """
        Run tests and return list of bugs found.
        
        Args:
            test_path: Test directory or file to run (default: tests/)
            
        Returns:
            List of BugInfo objects representing detected bugs
            
        Raises:
            ValueError: If test_path doesn't exist
            RuntimeError: If pytest execution fails critically
        """
    
    async def _run_pytest(
        self,
        test_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute pytest and capture output.
        
        Args:
            test_path: Test directory or file to run
            
        Returns:
            Dictionary with:
                - success: bool
                - return_code: int
                - stdout: str
                - stderr: str
        """
    
    def _parse_pytest_output(
        self,
        output: str,
        stderr: str,
    ) -> list[BugInfo]:
        """
        Parse pytest output to extract bug information.
        
        Args:
            output: pytest stdout
            stderr: pytest stderr
            
        Returns:
            List of BugInfo objects
        """
    
    def _extract_source_file(
        self,
        test_file: str,
        traceback: str,
    ) -> tuple[str | None, int | None]:
        """
        Extract source file path and line number from test failure.
        
        Args:
            test_file: Test file path
            traceback: Test failure traceback
            
        Returns:
            Tuple of (source_file_path, line_number) or (None, None)
        """
```

---

### 2. BugFixCoordinator API

**Module:** `tapps_agents.continuous_bug_fix.bug_fix_coordinator`

**Classes:**

#### `BugFixCoordinator` (Class)

```python
class BugFixCoordinator:
    """Coordinates bug fixing using FixOrchestrator."""
    
    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ) -> None:
        """
        Initialize BugFixCoordinator.
        
        Args:
            project_root: Project root directory
            config: Project configuration
        """
    
    async def fix_bug(
        self,
        bug: BugInfo,
    ) -> dict[str, Any]:
        """
        Fix a single bug using FixOrchestrator.
        
        Args:
            bug: BugInfo object with bug details
            
        Returns:
            Dictionary with:
                - success: bool
                - result: FixOrchestrator result dict
                - error: str | None (if failed)
        """
    
    async def verify_fix(
        self,
        bug: BugInfo,
        test_path: str | None = None,
    ) -> bool:
        """
        Re-run tests to verify bug is fixed.
        
        Args:
            bug: BugInfo object with bug details
            test_path: Test directory or file to run
            
        Returns:
            True if bug is fixed (test passes), False otherwise
        """
```

---

### 3. CommitManager API

**Module:** `tapps_agents.continuous_bug_fix.commit_manager`

**Classes:**

#### `CommitManager` (Class)

```python
class CommitManager:
    """Manages git commits for bug fixes."""
    
    def __init__(
        self,
        project_root: Path | None = None,
        strategy: str = "one-per-bug",
    ) -> None:
        """
        Initialize CommitManager.
        
        Args:
            project_root: Project root directory
            strategy: Commit strategy - "one-per-bug" or "batch"
        """
    
    async def commit_fix(
        self,
        bug: BugInfo,
        commit_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Commit a single fix.
        
        Args:
            bug: BugInfo object with bug details
            commit_message: Custom commit message (auto-generated if None)
            
        Returns:
            Dictionary with:
                - success: bool
                - commit_hash: str | None
                - branch: str | None
                - message: str
                - error: str | None (if failed)
        """
    
    async def commit_batch(
        self,
        bugs: list[BugInfo],
        commit_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Commit multiple fixes in one commit.
        
        Args:
            bugs: List of BugInfo objects
            commit_message: Custom commit message (auto-generated if None)
            
        Returns:
            Dictionary with commit information
        """
    
    def _generate_commit_message(
        self,
        bug: BugInfo,
    ) -> str:
        """
        Generate commit message for a bug fix.
        
        Args:
            bug: BugInfo object
            
        Returns:
            Commit message string
        """
```

---

### 4. ContinuousBugFixer API

**Module:** `tapps_agents.cli.commands.continuous_bug_fix`

**Classes:**

#### `ContinuousBugFixer` (Class)

```python
class ContinuousBugFixer:
    """Main orchestrator for continuous bug finding and fixing."""
    
    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ) -> None:
        """
        Initialize ContinuousBugFixer.
        
        Args:
            project_root: Project root directory
            config: Project configuration
        """
    
    async def execute(
        self,
        test_path: str | None = None,
        max_iterations: int = 10,
        commit_strategy: str = "one-per-bug",
        auto_commit: bool = True,
    ) -> dict[str, Any]:
        """
        Execute continuous bug finding and fixing.
        
        Args:
            test_path: Test directory or file to run
            max_iterations: Maximum loop iterations
            commit_strategy: Commit strategy - "one-per-bug" or "batch"
            auto_commit: Whether to commit fixes automatically
            
        Returns:
            Dictionary with execution results:
                - success: bool
                - iterations: int
                - bugs_found: int
                - bugs_fixed: int
                - bugs_failed: int
                - bugs_skipped: int
                - results: list[dict] (detailed results per iteration)
                - summary: dict (summary statistics)
        """
    
    async def _run_iteration(
        self,
        iteration: int,
        test_path: str | None = None,
        commit_strategy: str = "one-per-bug",
        auto_commit: bool = True,
    ) -> dict[str, Any]:
        """
        Execute one iteration of bug finding and fixing.
        
        Args:
            iteration: Current iteration number
            test_path: Test directory or file to run
            commit_strategy: Commit strategy
            auto_commit: Whether to commit fixes
            
        Returns:
            Dictionary with iteration results
        """
    
    def _generate_summary(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate summary report from execution results.
        
        Args:
            results: List of iteration result dictionaries
            
        Returns:
            Summary dictionary with statistics
        """
```

---

## Configuration Schema

**Location:** `.tapps-agents/config.yaml`

**Section:**
```yaml
continuous_bug_fix:
  max_iterations: 10
  commit_strategy: "one-per-bug"  # or "batch"
  auto_commit: true
  test_path: "tests/"
  skip_patterns: []  # Optional: patterns for bugs to skip
```

**Python Config Class:**
```python
@dataclass
class ContinuousBugFixConfig:
    """Configuration for continuous bug fix feature."""
    max_iterations: int = 10
    commit_strategy: str = "one-per-bug"
    auto_commit: bool = True
    test_path: str = "tests/"
    skip_patterns: list[str] = field(default_factory=list)
```

---

## CLI Parser Integration

**Location:** `tapps_agents/cli/parsers/top_level.py`

**Function to add:**
```python
def add_continuous_bug_fix_parser(
    subparsers: argparse._SubParsersAction
) -> None:
    """Add continuous-bug-fix command parser."""
    parser = subparsers.add_parser(
        "continuous-bug-fix",
        aliases=["bug-fix-continuous"],
        help="Continuously find and fix bugs from test failures",
        description="""
        Run tests continuously, detect bugs, fix them using bug-fix-agent,
        and commit fixes automatically. Stops when no bugs are found or
        max iterations reached.
        """,
    )
    
    parser.add_argument(
        "--test-path",
        type=str,
        default=None,
        help="Test directory or file to run (default: tests/)",
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum loop iterations (default: 10)",
    )
    
    parser.add_argument(
        "--commit-strategy",
        choices=["one-per-bug", "batch"],
        default="one-per-bug",
        help="Commit strategy: one-per-bug (default) or batch",
    )
    
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Skip commits (dry-run mode)",
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
```

---

## Command Handler Integration

**Location:** `tapps_agents/cli/commands/continuous_bug_fix.py`

**Function:**
```python
def handle_continuous_bug_fix_command(args: object) -> None:
    """Handle continuous-bug-fix command."""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "text")
    feedback.format_type = output_format
    
    # Parse arguments
    test_path = getattr(args, "test_path", None)
    max_iterations = getattr(args, "max_iterations", 10)
    commit_strategy = getattr(args, "commit_strategy", "one-per-bug")
    auto_commit = not getattr(args, "no_commit", False)
    
    # Load config
    from ...core.config import load_config
    config = load_config()
    
    # Override config with CLI args
    if test_path is None:
        test_path = config.continuous_bug_fix.test_path
    if max_iterations == 10:  # Only use config if default
        max_iterations = config.continuous_bug_fix.max_iterations
    if commit_strategy == "one-per-bug":  # Only use config if default
        commit_strategy = config.continuous_bug_fix.commit_strategy
    if auto_commit:  # Only use config if not explicitly disabled
        auto_commit = config.continuous_bug_fix.auto_commit
    
    # Execute
    from ...continuous_bug_fix.continuous_bug_fixer import ContinuousBugFixer
    
    fixer = ContinuousBugFixer(config=config)
    
    try:
        result = asyncio.run(
            fixer.execute(
                test_path=test_path,
                max_iterations=max_iterations,
                commit_strategy=commit_strategy,
                auto_commit=auto_commit,
            )
        )
        
        # Format and output result
        if output_format == "json":
            feedback.output_result(result)
        else:
            _format_text_output(result, feedback)
            
    except KeyboardInterrupt:
        feedback.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        feedback.error(f"Error: {e}", exit_code=1)
```

---

## Return Value Formats

### Execution Result (JSON)

```json
{
  "success": true,
  "iterations": 3,
  "bugs_found": 5,
  "bugs_fixed": 4,
  "bugs_failed": 1,
  "bugs_skipped": 0,
  "results": [
    {
      "iteration": 1,
      "bugs_found": 3,
      "bugs_fixed": 2,
      "bugs_failed": 1,
      "bugs": [
        {
          "file_path": "src/main.py",
          "error_message": "TypeError: ...",
          "test_name": "test_function",
          "test_file": "tests/test_main.py",
          "fix_result": {
            "success": true,
            "commit_hash": "abc123",
            "commit_message": "Fix: TypeError in main.py"
          }
        }
      ]
    }
  ],
  "summary": {
    "total_bugs_found": 5,
    "total_bugs_fixed": 4,
    "total_bugs_failed": 1,
    "fix_rate": 0.8,
    "iterations_run": 3
  }
}
```

### Text Output Format

```
Continuous Bug Fixer
====================

Iteration 1: Found 3 bugs, Fixed 2, Failed 1
Iteration 2: Found 1 bug, Fixed 1, Failed 0
Iteration 3: Found 0 bugs

Summary:
  Total Bugs Found: 5
  Bugs Fixed: 4
  Bugs Failed: 1
  Fix Rate: 80.0%
  Iterations Run: 3
```

---

## Error Handling

### Error Types

1. **TestExecutionError**: pytest execution failed
2. **BugFixError**: FixOrchestrator failed to fix bug
3. **CommitError**: Git commit failed
4. **ConfigurationError**: Invalid configuration

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_type": "TestExecutionError",
  "iterations": 2,
  "bugs_found": 3,
  "bugs_fixed": 1,
  "bugs_failed": 2
}
```
