---
title: API Reference
version: 3.3.0
status: active
last_updated: 2026-01-20
tags: [api, reference, python, cli, agents, workflow]
---

# API Reference

## Overview

TappsCodingAgents provides:

- a **Python API** (agent classes + workflow engine)
- a **CLI** (`tapps-agents` entrypoint)

## Python API

### Agent Lifecycle

All workflow agents follow the same basic pattern:

```python
import asyncio
from tapps_agents.agents.reviewer.agent import ReviewerAgent

async def main() -> None:
    agent = ReviewerAgent()
    await agent.activate()
    try:
        result = await agent.run("review", file="path/to/file.py")
        print(result)
    finally:
        await agent.close()

asyncio.run(main())
```

### Configuration

Configuration is loaded from `.tapps-agents/config.yaml` (searched upward from the current directory). If not found, defaults are used.

```python
from tapps_agents.core.config import load_config

config = load_config()  # defaults if no file is found
# MAL configuration removed - all LLM operations handled by Cursor Skills
print(config.agents.reviewer.quality_threshold)
```

See `docs/CONFIGURATION.md` for the full schema.

### Note on LLM Operations

All LLM operations are handled by Cursor Skills, which use the developer's configured model in Cursor.
- Agents prepare instruction objects that are executed via Cursor Skills
- No local LLM or API keys required
- Cursor handles all model selection and execution

See `docs/HOW_IT_WORKS.md`.

### Project Profiling

```python
from pathlib import Path
from tapps_agents.core.project_profile import ProjectProfileDetector, save_project_profile

profile = ProjectProfileDetector(project_root=Path.cwd()).detect_profile()
path = save_project_profile(profile)
print(path)  # .tapps-agents/project-profile.yaml
```

### Workflow Engine

```python
from pathlib import Path
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.parser import WorkflowParser

workflow = WorkflowParser.parse_file(Path("workflows/presets/rapid-dev.yaml"))
executor = WorkflowExecutor(project_root=Path.cwd(), auto_detect=False)
state = executor.start(workflow=workflow)
print(state.workflow_id, state.status)
```

### Batch Review Workflow

Review multiple services in parallel with timeout protection:

```python
from pathlib import Path
from tapps_agents.agents.reviewer.batch_review import BatchReviewWorkflow
from tapps_agents.agents.reviewer.service_discovery import ServiceDiscovery, Priority

# Discover services
discovery = ServiceDiscovery(project_root=Path.cwd())
services = discovery.discover_services_with_priority(prioritize=True)

# Review services in parallel (with 5-minute timeout per service)
workflow = BatchReviewWorkflow(
    project_root=Path.cwd(),
    max_parallel=4,  # Max concurrent reviews
    review_timeout=300.0  # 5 minutes per service
)

result = await workflow.review_services(
    services=services,
    parallel=True,
    include_scoring=True,
    include_llm_feedback=True
)

print(f"Reviewed {result.services_reviewed} services")
print(f"Passed: {result.passed}, Failed: {result.failed}")
print(f"Average score: {result.average_score:.2f}")
```

### Phased Review Strategy

Review services in priority-based phases with progress persistence:

```python
from pathlib import Path
from tapps_agents.agents.reviewer.phased_review import PhasedReviewStrategy
from tapps_agents.agents.reviewer.service_discovery import Priority

strategy = PhasedReviewStrategy(
    project_root=Path.cwd(),
    max_parallel=4
)

# Execute phased review (critical → high → medium → low)
result = await strategy.execute_phased_review(
    review_id="my-review-2025-01-15",
    phases=[Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW],
    resume=True,  # Resume from saved progress if interrupted
    parallel=True,
    include_scoring=True,
    include_llm_feedback=True
)

print(f"Completed {result.completed_phases} of {result.total_phases} phases")
print(f"Services reviewed: {result.services_reviewed}")
print(f"Passed: {result.passed}, Failed: {result.failed}")

# Resume interrupted review
resumed_result = await strategy.execute_phased_review(
    review_id="my-review-2025-01-15",
    resume=True  # Automatically resumes from saved progress
)
```

**Note**: Progress is automatically saved to `.tapps-agents/review-progress.json` for resumability.

## CLI

### Entry Points

Both of these are supported:

- `tapps-agents ...` (installed console script)
- `python -m tapps_agents.cli ...` (module invocation)

### Top-Level Commands

From `python -m tapps_agents.cli --help`, the CLI exposes:

- **Agent subcommands**: `reviewer`, `planner`, `implementer`, `tester`, `debugger`, `documenter`, `analyst`, `architect`, `designer`, `improver`, `ops`, `enhancer`, `orchestrator`, `evaluator`
- **Utility subcommands**: `workflow`, `init`, `doctor`, `score`, `setup-experts`, `analytics`, `create`, `hardware-profile` (or `hardware`), `continuous-bug-fix`

### Command Naming (with and without `*`)

The CLI accepts **both** forms for many agent commands:

- `reviewer review ...`
- `reviewer *review ...` (alias)

### Common Examples

```bash
# Reviewer - Single File
python -m tapps_agents.cli reviewer review path/to/file.py
python -m tapps_agents.cli reviewer score path/to/file.py
python -m tapps_agents.cli reviewer lint path/to/file.py
python -m tapps_agents.cli reviewer type-check path/to/file.py
python -m tapps_agents.cli reviewer report path/to/dir json markdown html

# Reviewer - Batch Operations (Multiple Files)
python -m tapps_agents.cli reviewer score file1.py file2.py file3.py
python -m tapps_agents.cli reviewer review file1.py file2.py --max-workers 4
python -m tapps_agents.cli reviewer lint file1.py file2.py --output results.json

# Reviewer - Glob Patterns
python -m tapps_agents.cli reviewer score --pattern "src/**/*.py"
python -m tapps_agents.cli reviewer review --pattern "tests/*.py" --max-workers 8
python -m tapps_agents.cli reviewer lint --pattern "**/*.ts" --output lint-report.html

# Reviewer - Output Formats
python -m tapps_agents.cli reviewer score file.py --output report.json
python -m tapps_agents.cli reviewer score file.py --output report.md --format markdown
python -m tapps_agents.cli reviewer score file.py --output report.html --format html

# Quick shortcut (same as reviewer score)
python -m tapps_agents.cli score path/to/file.py

# Enhancer - Prompt Enhancement
python -m tapps_agents.cli enhancer enhance "Create a user authentication feature"
python -m tapps_agents.cli enhancer enhance "Fix the bug in login.py" --output enhanced.md
python -m tapps_agents.cli enhancer enhance-quick "Quick enhancement" --output quick.md

# Workflow presets
python -m tapps_agents.cli workflow list
python -m tapps_agents.cli workflow rapid
python -m tapps_agents.cli workflow full

# Project initialization
python -m tapps_agents.cli init

# Environment diagnostics
python -m tapps_agents.cli doctor
python -m tapps_agents.cli doctor --format json

# Expert setup wizard
python -m tapps_agents.cli setup-experts init
python -m tapps_agents.cli setup-experts add
python -m tapps_agents.cli setup-experts list

# Analytics
python -m tapps_agents.cli analytics dashboard
python -m tapps_agents.cli analytics agents
python -m tapps_agents.cli analytics workflows
python -m tapps_agents.cli analytics trends --metric-type agent_duration --days 30
python -m tapps_agents.cli analytics system

# Create new project (primary use case)
python -m tapps_agents.cli create "Build a task management web app"
python -m tapps_agents.cli create "Create a REST API for user management" --workflow rapid

# Hardware profile management
python -m tapps_agents.cli hardware-profile
python -m tapps_agents.cli hardware-profile --set nuc
python -m tapps_agents.cli hardware-profile --set auto

# Evaluator - Framework effectiveness analysis
python -m tapps_agents.cli evaluator evaluate
python -m tapps_agents.cli evaluator evaluate --workflow-id workflow-123
python -m tapps_agents.cli evaluator evaluate --output my-evaluation.md
python -m tapps_agents.cli evaluator evaluate-workflow workflow-123 --format markdown
```

## Batch Operations

The reviewer agent now supports batch processing for multiple files:

### Multiple Files
```bash
# Score multiple files at once
python -m tapps_agents.cli reviewer score file1.py file2.py file3.py

# Review multiple files with custom concurrency
python -m tapps_agents.cli reviewer review file1.py file2.py --max-workers 4
```

### Glob Patterns
```bash
# Process all Python files in a directory
python -m tapps_agents.cli reviewer score --pattern "src/**/*.py"

# Process test files only
python -m tapps_agents.cli reviewer lint --pattern "tests/*.py"
```

### Output Formats
```bash
# Save results to JSON file
python -m tapps_agents.cli reviewer score file.py --output report.json

# Generate HTML report
python -m tapps_agents.cli reviewer score file.py --output report.html --format html

# Generate Markdown report
python -m tapps_agents.cli reviewer score file.py --output report.md --format markdown

# Save lint results to file
python -m tapps_agents.cli reviewer lint file.py --output lint-report.json

# Save type-check results to file
python -m tapps_agents.cli reviewer type-check file.py --output type-check.json

# Batch lint with output file
python -m tapps_agents.cli reviewer lint file1.py file2.py --output batch-lint.json

# Batch type-check with HTML output
python -m tapps_agents.cli reviewer type-check --pattern "src/**/*.py" --output type-check.html --format html
```

## Enhancer Improvements

**Workflow integration:** full-sdlc (optional enhance before requirements), rapid-dev, and Epic run enhance steps via **EnhancerHandler** (`tapps_agents/workflow/agent_handlers/enhancer_handler.py`). **CLI auto-enhancement:** `auto_enhancement` and `PROMPT_ARGUMENT_MAP` in [CONFIGURATION.md](CONFIGURATION.md#automatic-prompt-enhancement-auto_enhancement).

The enhancer agent now provides complete output with all stage data:

### Enhanced Output
The enhancer now displays:
- **Analysis**: Intent, scope, workflow type, complexity, domains, technologies (all fields properly populated with fallback mechanism for reliability)
- **Requirements**: Gathered requirements from analyst and experts
- **Architecture Guidance**: Architecture recommendations and patterns
- **Codebase Context**: Related files and detected patterns
- **Quality Standards**: Quality thresholds and standards
- **Implementation Strategy**: Step-by-step implementation plan

### Example Output
```markdown
# Enhanced Prompt: Create a user authentication feature

## Analysis
- **Intent**: feature
- **Scope**: medium
- **Workflow Type**: greenfield
- **Complexity**: medium
- **Detected Domains**: security, user-management

## Requirements
1. Requirement 1: User authentication
2. Requirement 2: Password hashing

## Architecture Guidance
Use FastAPI with JWT tokens
Patterns: REST API, JWT

## Codebase Context
Related Files: auth.py, models.py
Patterns: MVC

## Quality Standards
Standards: PEP 8, Type hints
Thresholds: complexity < 5.0

## Implementation Strategy
Step 1: Create auth module
Step 2: Add JWT handling
```

## Evaluator Agent

The Evaluator Agent analyzes TappsCodingAgents framework effectiveness and generates actionable improvement recommendations.

### Python API

```python
import asyncio
from tapps_agents.agents.evaluator.agent import EvaluatorAgent

async def main() -> None:
    agent = EvaluatorAgent()
    await agent.activate()
    try:
        # Evaluate framework effectiveness
        result = await agent.run("evaluate", workflow_id="workflow-123")
        print(result)
        
        # Evaluate specific workflow
        result = await agent.run("evaluate-workflow", workflow_id="workflow-123")
        print(result)
    finally:
        await agent.close()

asyncio.run(main())
```

### CLI Usage

```bash
# Evaluate framework effectiveness
python -m tapps_agents.cli evaluator evaluate

# Evaluate specific workflow
python -m tapps_agents.cli evaluator evaluate --workflow-id workflow-123

# Generate report with custom output
python -m tapps_agents.cli evaluator evaluate --output my-evaluation.md

# Evaluate workflow with markdown format
python -m tapps_agents.cli evaluator evaluate-workflow workflow-123 --format markdown
```

### Output Format

The evaluator generates structured markdown reports with:

- **Executive Summary (TL;DR)**: Quick overview of findings
- **Usage Statistics**: Command usage patterns (CLI vs Cursor Skills vs Simple Mode)
- **Workflow Adherence Analysis**: Did users follow intended workflows?
- **Quality Metrics**: Code quality assessment
- **Prioritized Recommendations**: 
  - Priority 1: Critical improvements
  - Priority 2: Important improvements
  - Priority 3: Nice-to-have improvements

### Workflow Integration

The evaluator can run automatically at the end of `*build` workflows when enabled in configuration:

```yaml
agents:
  evaluator:
    auto_run: true  # Enable automatic evaluation
    output_dir: ".tapps-agents/evaluations"
    thresholds:
      quality_score: 70.0
      workflow_completion: 0.8
```

### Report Location

Reports are saved to `.tapps-agents/evaluations/` by default, with filenames like:
- `evaluation-2025-01-15-143022.md`
- `workflow-workflow-123-evaluation.md`

## Analyst Agent

Analyst Agent - Requirements gathering and technical research.

### Commands

- `description` - See agent documentation


## Architect Agent

Architect Agent - System and security architecture design.

### Commands

- `sequence` - See agent documentation
- `component` - See agent documentation
- `deployment` - See agent documentation
- `requirements` - See agent documentation
- `class` - See agent documentation


## Debugger Agent

Debugger Agent - Error analysis and debugging.


## Designer Agent

Designer Agent - API contracts, data models, UI/UX specifications.

### Commands

- `requirements` - See agent documentation
- `page` - See agent documentation
- `flow` - See agent documentation
- `component` - See agent documentation


## Documenter Agent

Documenter Agent - Documentation generation.


## Enhancer Agent

Enhancer Agent - Transforms simple prompts into comprehensive, context-aware prompts.

**Recent Improvements**: Analysis stage now properly populates all fields (intent, scope, workflow type, complexity, domains, technologies) with a reliable fallback mechanism. No more "unknown" values.

### Commands

- `enhance` - See agent documentation
- `quality` - See agent documentation
- `requirements` - See agent documentation
- `synthesis` - See agent documentation
- `architecture` - See agent documentation
- `codebase_context` - See agent documentation
- `analysis` - See agent documentation
- `implementation` - See agent documentation


## Evaluator Agent

Evaluator Agent - Evaluates TappsCodingAgents framework effectiveness.


## Implementer Agent

Implementer Agent - Code generation and file writing.


## Improver Agent

Improver Agent - Code refactoring, performance optimization, and quality improvements.

### Commands

- `memory` - See agent documentation
- `Edit` - See agent documentation
- `Glob` - See agent documentation
- `both` - See agent documentation
- `Grep` - See agent documentation
- `Write` - See agent documentation
- `Bash` - See agent documentation
- `help` - See agent documentation
- `type` - See agent documentation
- `instruction` - See agent documentation
- `Read` - See agent documentation
- `performance` - See agent documentation
- `file_path` - See agent documentation


## Ops Agent

Ops Agent - Security scanning, compliance, deployment, and infrastructure management.

### Commands

- `kubernetes` - See agent documentation
- `Write` - See agent documentation
- `xss` - See agent documentation
- `all` - See agent documentation
- `target` - See agent documentation
- `GDPR` - See agent documentation
- `terraform` - See agent documentation
- `Edit` - See agent documentation
- `production` - See agent documentation
- `help` - See agent documentation
- `environment` - See agent documentation
- `Glob` - See agent documentation
- `staging` - See agent documentation
- `Grep` - See agent documentation
- `Bash` - See agent documentation
- `type` - See agent documentation
- `HIPAA` - See agent documentation
- `local` - See agent documentation
- `docker` - See agent documentation
- `secrets` - See agent documentation
- `SOC2` - See agent documentation
- `general` - See agent documentation
- `sql_injection` - See agent documentation
- `Read` - See agent documentation


## Orchestrator Agent

Orchestrator Agent - Coordinates YAML-defined workflows and makes gate decisions.

### Commands

- `on_fail` - See agent documentation
- `on_pass` - See agent documentation
- `help` - See agent documentation


## Planner Agent

Planner Agent - Story/epic planning and task breakdown.


## Reviewer Agent

Reviewer Agent - Code review with Code Scoring.

### Reviewer Agent Features (2026-01-16)

The reviewer agent has been enhanced with comprehensive feedback improvements:

#### Test Coverage Detection
- **Accurate Coverage:** Returns 0.0% when no test files exist (previously 5.0-6.0)
- **Neutral Score:** Returns 5.0 when test files exist but no coverage data available
- **Actual Coverage:** Uses real coverage data when available

#### Maintainability Issues
- **Specific Issues:** Provides detailed maintainability issues with:
  - Line numbers
  - Issue type (missing docstrings, long functions, deep nesting, missing type hints)
  - Severity (high, medium, low)
  - Actionable suggestions
- **Summary Statistics:** Includes total count, breakdown by severity and type

#### Structured Feedback
- **Always Provided:** Structured feedback always returned (even when LLM unavailable):
  - Summary with overall assessment
  - Strengths list (what's good)
  - Issues list with severity and recommendations
  - Actionable recommendations
  - Priority level (low/medium/high)
- **Backward Compatible:** Works in both Cursor and CLI modes

#### Performance Issues
- **Line Numbers:** Performance bottlenecks include specific line numbers
- **Operation Types:** Identifies nested loops, expensive operations, bottlenecks
- **Context:** Provides context about where issues occur
- **Suggestions:** Actionable suggestions for improvement

#### Type Checking Scores
- **Actual Errors:** Scores reflect actual mypy errors (not static 5.0)
- **Error Details:** Includes error codes, expected vs actual types
- **Accurate Scoring:** Files with type errors show score < 10.0

#### Context-Aware Quality Gates
- **File Context Detection:** Automatically detects if file is new, modified, or existing
- **Adaptive Thresholds:**
  - **New files:** Lenient thresholds (overall: 5.0, security: 6.0, coverage: 0%)
  - **Modified files:** Standard thresholds (overall: 8.0, security: 8.5, coverage: 70%)
  - **Existing files:** Strict thresholds (overall: 8.0, security: 8.5, coverage: 80%)
- **Context Information:** Includes file context in review output

### Example Usage

```python
from tapps_agents.agents.reviewer.agent import ReviewerAgent

agent = ReviewerAgent()
await agent.activate()

# Review a file (includes all improvements)
result = await agent.review_file(
    "src/file.py",
    include_scoring=True,
    include_llm_feedback=True
)

# Access test coverage (accurate for files with no tests)
coverage = result["scoring"]["test_coverage_score"]  # 0.0 when no tests exist

# Access maintainability issues
if "maintainability_issues" in result:
    for issue in result["maintainability_issues"]:
        print(f"Line {issue['line_number']}: {issue['message']}")
        print(f"  Severity: {issue['severity']}")
        print(f"  Suggestion: {issue['suggestion']}")

# Access performance issues
if "performance_issues" in result:
    for issue in result["performance_issues"]:
        print(f"Line {issue['line_number']}: {issue['message']}")

# Access structured feedback
if "feedback" in result and "structured_feedback" in result["feedback"]:
    structured = result["feedback"]["structured_feedback"]
    print(f"Summary: {structured['summary']}")
    print(f"Priority: {structured['priority']}")

# Access file context (for quality gates)
if "file_context" in result:
    context = result["file_context"]
    print(f"File status: {context['status']}")  # 'new', 'modified', or 'existing'
    print(f"Thresholds applied: {context['thresholds_applied']}")
```

### Review Output Structure

```python
{
    "file": "src/file.py",
    "scoring": {
        "overall_score": 75.0,
        "test_coverage_score": 0.0,  # Accurate: 0.0 when no tests exist
        "maintainability_score": 7.5,
        "performance_score": 8.0,
        "type_checking_score": 8.5,  # Reflects actual mypy errors
        # ... other scores
    },
    "maintainability_issues": [  # NEW: Specific issues
        {
            "issue_type": "missing_docstring",
            "message": "Function 'calculate_sum' missing docstring",
            "line_number": 5,
            "severity": "medium",
            "suggestion": "Add docstring describing function purpose and parameters",
            "function_name": "calculate_sum"
        },
        # ... more issues
    ],
    "performance_issues": [  # NEW: Performance bottlenecks
        {
            "issue_type": "nested_loops",
            "message": "Nested for loops detected in function 'process_data'",
            "line_number": 15,
            "severity": "high",
            "suggestion": "Consider using itertools.product() or list comprehensions",
            "operation_type": "loop",
            "context": "Nested in function 'process_data'"
        },
        # ... more issues
    ],
    "feedback": {
        "structured_feedback": {  # NEW: Always provided
            "summary": "Code quality is good with some areas for improvement",
            "strengths": ["Well-structured code", "Good security practices"],
            "issues": [
                {"category": "maintainability", "priority": "medium", ...},
                {"category": "performance", "priority": "high", ...}
            ],
            "recommendations": ["Add docstrings", "Optimize nested loops"],
            "priority": "medium"
        }
    },
    "file_context": {  # NEW: Context-aware quality gates
        "status": "new",  # 'new', 'modified', or 'existing'
        "age_days": 0.5,
        "confidence": 0.9,
        "thresholds_applied": "new_file"
    },
    "quality_gate": {
        "passed": True,
        "thresholds": {
            "overall_min": 5.0,  # Lower for new files
            "security_min": 6.0,
            "test_coverage_min": 0.0
        },
        # ... quality gate results
    }
}
```


## Tester Agent

Tester Agent - Test generation and execution.

## Data Models

### Workflow Artifacts

All workflow artifacts use Pydantic v2 BaseModel for type safety and validation:

**Artifact Types**:
- `PlanningArtifact` - User stories and planning data
- `DesignArtifact` - Architecture and component design
- `CodeArtifact` - Code generation artifacts
- `ReviewArtifact` - Code review results
- `TestingArtifact` - Test results and coverage
- `QualityArtifact` - Quality analysis results
- `OperationsArtifact` - Security, compliance, and deployment artifacts
- `EnhancementArtifact` - Prompt enhancement artifacts
- `DocumentationArtifact` - Documentation generation artifacts
- `ContextArtifact` - Context analysis artifacts

**Location**: `tapps_agents/workflow/*_artifact.py`

**Usage**:
```python
from tapps_agents.workflow.planning_artifact import PlanningArtifact
from tapps_agents.workflow.artifact_helper import load_artifact, write_artifact
from tapps_agents.workflow.common_enums import ArtifactStatus

# Load artifact (handles both old and new formats)
artifact = load_artifact("planning.json", PlanningArtifact)

# Create new artifact
artifact = PlanningArtifact(
    artifact_type="planning",
    status=ArtifactStatus.COMPLETED,
    user_stories=[...],
)

# Save artifact
write_artifact(artifact, "planning.json")
```

### Enums

Type-safe Python Enums for artifact fields:

- `Priority` - Priority levels (HIGH, MEDIUM, LOW)
- `ArtifactStatus` - Artifact execution status (PENDING, RUNNING, COMPLETED, etc.)
- `RiskLevel` - Risk levels (LOW, MEDIUM, HIGH)
- `OperationType` - Operation types (CREATE, UPDATE, DELETE, etc.)
- `StoryStatus` - Story status (NOT_STARTED, IN_PROGRESS, DONE, etc.)

**Location**: `tapps_agents/workflow/common_enums.py`

### Structured Metadata Models

Structured models for metadata, plans, inputs, and results:

- `ArtifactMetadata` (TypedDict) - Flexible metadata structure
- `PlanDetails` (BaseModel) - Structured plan information
- `TaskInputs` (BaseModel) - Task input parameters
- `TaskResults` (BaseModel) - Task output results
- `RetryPolicy` (BaseModel) - Retry configuration

**Location**: `tapps_agents/workflow/metadata_models.py`

### JSON Schemas

JSON Schema files for all artifact models are available in `schemas/1.0/`:

```python
import json
import jsonschema

# Load schema
with open("schemas/1.0/PlanningArtifact.json") as f:
    schema = json.load(f)

# Validate artifact data
jsonschema.validate(instance=artifact_data, schema=schema)
```

See `schemas/README.md` for complete schema documentation.

### Migration Guide

For detailed migration information, see:
- **[Pydantic Migration Guide](IMPLEMENTATION/PYDANTIC_MIGRATION_GUIDE.md)** - Complete migration guide
- **[Migration Status](IMPLEMENTATION/pydantic_migration_status.md)** - Migration status and completion details

## Related Documentation

- `docs/CONFIGURATION.md`
- `docs/QUICK_WORKFLOW_COMMANDS.md`
- `docs/EXPERT_SETUP_WIZARD.md`
- `docs/PROJECT_PROFILING_GUIDE.md`
- `docs/ARCHITECTURE.md`
