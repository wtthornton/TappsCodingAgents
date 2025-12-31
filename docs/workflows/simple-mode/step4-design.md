# Step 4: Component Design Specifications - Evaluator Agent

**Date:** January 16, 2025  
**Workflow:** Simple Mode *build  
**Agent:** Designer  
**Stage:** Component Design Specifications

---

## Component Design Specifications

### 1. EvaluatorAgent Class Specification

**File:** `tapps_agents/agents/evaluator/agent.py`

**Class Definition:**
```python
class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Evaluates TappsCodingAgents framework effectiveness.
    
    Provides analysis of:
    - Command usage patterns (CLI vs Cursor Skills vs Simple Mode)
    - Workflow adherence (did users follow intended workflows?)
    - Code quality metrics
    - Actionable recommendations for continuous improvement
    """
```

**Initialization:**
```python
def __init__(self, config: ProjectConfig | None = None):
    super().__init__(
        agent_id="evaluator",
        agent_name="Evaluator Agent",
        config=config
    )
    self.config = config or load_config()
    
    # Analyzers (lazy initialization)
    self.usage_analyzer: UsageAnalyzer | None = None
    self.workflow_analyzer: WorkflowAnalyzer | None = None
    self.quality_analyzer: QualityAnalyzer | None = None
    self.report_generator: ReportGenerator | None = None
```

**Commands:**
```python
def get_commands(self) -> list[dict[str, str]]:
    return [
        {"command": "*evaluate", "description": "Evaluate framework effectiveness"},
        {"command": "*evaluate-workflow", "description": "Evaluate specific workflow"},
        {"command": "*help", "description": "Show available commands"},
    ]
```

**Main Run Method:**
```python
async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
    """
    Execute evaluator commands.
    
    Commands:
    - evaluate: Run full evaluation
    - evaluate-workflow <workflow_id>: Evaluate specific workflow
    - help: Show help
    """
    command = command.lstrip("*")
    
    if command == "help":
        return {"type": "help", "content": self.format_help()}
    elif command == "evaluate":
        workflow_id = kwargs.get("workflow_id")
        return await self._evaluate(workflow_id=workflow_id)
    elif command == "evaluate-workflow":
        workflow_id = kwargs.get("workflow_id")
        if not workflow_id:
            return {"error": "workflow_id is required"}
        return await self._evaluate_workflow(workflow_id)
    else:
        return {"error": f"Unknown command: {command}"}
```

---

### 2. UsageAnalyzer Class Specification

**File:** `tapps_agents/agents/evaluator/usage_analyzer.py`

**Class Definition:**
```python
class UsageAnalyzer:
    """
    Analyzes command usage patterns and statistics.
    
    Tracks:
    - Total commands executed
    - CLI vs Cursor Skills vs Simple Mode usage
    - Individual agent usage frequency
    - Command success/failure rates
    - Usage gaps (intended vs actual)
    """
```

**Key Methods:**

```python
def analyze_usage(
    self,
    workflow_state: dict[str, Any] | None = None,
    cli_logs: list[dict] | None = None,
    runtime_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Analyze command usage patterns.
    
    Args:
        workflow_state: Workflow execution state (if available)
        cli_logs: CLI execution logs (if available)
        runtime_data: Runtime analysis data (if available)
    
    Returns:
        Dictionary with usage statistics and analysis
    """
    # Collect all commands from data sources
    commands = self._collect_commands(workflow_state, cli_logs, runtime_data)
    
    # Calculate statistics
    stats = self.calculate_statistics(commands)
    
    # Identify gaps
    gaps = self.identify_gaps(stats)
    
    return {
        "statistics": stats,
        "gaps": gaps,
        "recommendations": self._generate_recommendations(stats, gaps)
    }
```

**Statistics Calculation:**
```python
def calculate_statistics(self, commands: list[dict]) -> dict[str, Any]:
    """
    Calculate usage statistics from command list.
    
    Returns:
        {
            "total_commands": int,
            "cli_commands": int,
            "cursor_skills": int,
            "simple_mode": int,
            "agent_usage": dict[str, int],  # agent_name -> count
            "command_success_rate": float,
            "most_used_agents": list[str],
            "least_used_agents": list[str]
        }
    """
```

**Gap Identification:**
```python
def identify_gaps(
    self,
    actual_stats: dict[str, Any],
    intended_usage: dict[str, Any] | None = None
) -> list[dict]:
    """
    Identify gaps between intended and actual usage.
    
    Returns:
        List of gap dictionaries:
        [
            {
                "type": "usage_pattern",  # or "workflow", "agent"
                "description": str,
                "impact": "high" | "medium" | "low",
                "recommendation": str
            },
            ...
        ]
    """
```

---

### 3. WorkflowAnalyzer Class Specification

**File:** `tapps_agents/agents/evaluator/workflow_analyzer.py`

**Class Definition:**
```python
class WorkflowAnalyzer:
    """
    Analyzes workflow adherence and execution patterns.
    
    Checks:
    - Steps executed vs steps required
    - Documentation artifacts created
    - Workflow deviations
    - Completion rates
    """
```

**Key Methods:**

```python
def analyze_workflow(
    self,
    workflow_id: str,
    workflow_state: dict[str, Any],
    workflow_definition: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Analyze workflow execution.
    
    Args:
        workflow_id: Workflow identifier
        workflow_state: Workflow execution state
        workflow_definition: Workflow YAML definition (if available)
    
    Returns:
        Dictionary with workflow analysis
    """
    # Check step completion
    step_analysis = self.check_step_completion(workflow_definition, workflow_state)
    
    # Verify artifacts
    artifact_analysis = self.verify_artifacts(workflow_definition, workflow_state)
    
    # Identify deviations
    deviations = self.identify_deviations(workflow_definition, workflow_state)
    
    return {
        "workflow_id": workflow_id,
        "step_analysis": step_analysis,
        "artifact_analysis": artifact_analysis,
        "deviations": deviations,
        "recommendations": self._generate_recommendations(step_analysis, deviations)
    }
```

**Step Completion Check:**
```python
def check_step_completion(
    self,
    workflow_definition: dict[str, Any] | None,
    workflow_state: dict[str, Any]
) -> dict[str, Any]:
    """
    Check if all required steps were executed.
    
    Returns:
        {
            "steps_required": int,
            "steps_executed": int,
            "completion_rate": float,
            "missing_steps": list[str],
            "executed_steps": list[str]
        }
    """
```

**Artifact Verification:**
```python
def verify_artifacts(
    self,
    workflow_definition: dict[str, Any] | None,
    workflow_state: dict[str, Any]
) -> dict[str, Any]:
    """
    Verify documentation artifacts were created.
    
    Returns:
        {
            "artifacts_expected": list[str],
            "artifacts_created": list[str],
            "artifacts_missing": list[str],
            "creation_rate": float
        }
    """
```

---

### 4. QualityAnalyzer Class Specification

**File:** `tapps_agents/agents/evaluator/quality_analyzer.py`

**Class Definition:**
```python
class QualityAnalyzer:
    """
    Analyzes code quality metrics and issues.
    
    Tracks:
    - Quality scores from reviewer agent
    - Quality issues (syntax errors, test failures)
    - Quality trends over time
    """
```

**Key Methods:**

```python
def analyze_quality(
    self,
    quality_data: dict[str, Any] | None = None,
    workflow_state: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Analyze code quality metrics.
    
    Args:
        quality_data: Quality scores from reviewer agent (if available)
        workflow_state: Workflow state (may contain quality data)
    
    Returns:
        Dictionary with quality analysis
    """
    # Collect quality scores
    scores = self._collect_scores(quality_data, workflow_state)
    
    # Identify issues
    issues = self.identify_issues(scores)
    
    # Track trends (if historical data available)
    trends = self.track_trends(scores) if self._has_historical_data() else {}
    
    return {
        "scores": scores,
        "issues": issues,
        "trends": trends,
        "recommendations": self._generate_recommendations(scores, issues)
    }
```

**Issue Identification:**
```python
def identify_issues(
    self,
    scores: dict[str, float],
    thresholds: dict[str, float] | None = None
) -> list[dict]:
    """
    Identify quality issues below thresholds.
    
    Returns:
        List of issue dictionaries:
        [
            {
                "metric": str,  # "complexity", "security", etc.
                "score": float,
                "threshold": float,
                "severity": "high" | "medium" | "low",
                "recommendation": str
            },
            ...
        ]
    """
```

---

### 5. ReportGenerator Class Specification

**File:** `tapps_agents/agents/evaluator/report_generator.py`

**Class Definition:**
```python
class ReportGenerator:
    """
    Generates structured markdown reports.
    
    Combines analyzer outputs into actionable report with:
    - Executive summary
    - Usage statistics
    - Workflow adherence
    - Quality metrics
    - Prioritized recommendations
    """
```

**Key Methods:**

```python
def generate_report(
    self,
    usage_data: dict[str, Any],
    workflow_data: dict[str, Any] | None = None,
    quality_data: dict[str, Any] | None = None
) -> str:
    """
    Generate markdown report from analyzer outputs.
    
    Args:
        usage_data: Output from UsageAnalyzer
        workflow_data: Output from WorkflowAnalyzer (optional)
        quality_data: Output from QualityAnalyzer (optional)
    
    Returns:
        Markdown report as string
    """
    # Build report sections
    sections = []
    
    # Executive Summary
    sections.append(self._generate_executive_summary(
        usage_data, workflow_data, quality_data
    ))
    
    # Usage Statistics
    sections.append(self._generate_usage_section(usage_data))
    
    # Workflow Adherence (if available)
    if workflow_data:
        sections.append(self._generate_workflow_section(workflow_data))
    
    # Quality Metrics (if available)
    if quality_data:
        sections.append(self._generate_quality_section(quality_data))
    
    # Recommendations
    recommendations = self._collect_recommendations(
        usage_data, workflow_data, quality_data
    )
    prioritized = self.prioritize_recommendations(recommendations)
    sections.append(self._generate_recommendations_section(prioritized))
    
    return "\n\n".join(sections)
```

**Recommendation Prioritization:**
```python
def prioritize_recommendations(
    self,
    recommendations: list[dict]
) -> dict[str, list[dict]]:
    """
    Prioritize recommendations into Priority 1, 2, 3.
    
    Priority 1 (Critical): High impact, easy to fix
    Priority 2 (Important): High impact, moderate effort
    Priority 3 (Nice to Have): Lower impact or high effort
    
    Returns:
        {
            "priority_1": list[dict],
            "priority_2": list[dict],
            "priority_3": list[dict]
        }
    """
```

**Report Sections:**

1. **Executive Summary:**
   - Quick TL;DR
   - Top 3 recommendations
   - Overall assessment

2. **Usage Statistics:**
   - Command breakdown
   - CLI vs Skills vs Simple Mode
   - Agent usage frequency
   - Success rates

3. **Workflow Adherence:**
   - Steps executed vs required
   - Documentation artifacts
   - Deviations identified

4. **Quality Metrics:**
   - Overall scores
   - Quality issues
   - Trends (if available)

5. **Recommendations:**
   - Priority 1 (Critical)
   - Priority 2 (Important)
   - Priority 3 (Nice to Have)

---

## Data Models

### Command Data Model
```python
{
    "command": str,  # e.g., "review", "implement"
    "agent": str,    # e.g., "reviewer", "implementer"
    "invocation_method": str,  # "cli", "cursor_skill", "simple_mode"
    "timestamp": datetime,
    "success": bool,
    "duration": float,  # seconds
    "workflow_id": str | None
}
```

### Workflow State Model
```python
{
    "workflow_id": str,
    "workflow_type": str,  # "build", "full", etc.
    "steps": list[dict],  # Step execution data
    "artifacts": list[str],  # Created artifact paths
    "quality_scores": dict[str, float] | None,
    "completed": bool,
    "duration": float
}
```

### Report Model
```python
{
    "timestamp": datetime,
    "evaluation_type": str,  # "full", "workflow"
    "workflow_id": str | None,
    "usage_statistics": dict,
    "workflow_analysis": dict | None,
    "quality_analysis": dict | None,
    "recommendations": {
        "priority_1": list[dict],
        "priority_2": list[dict],
        "priority_3": list[dict]
    }
}
```

---

## API Specifications

### CLI API

**Command:** `tapps-agents evaluator evaluate [options]`

**Options:**
- `--workflow-id <id>`: Evaluate specific workflow
- `--format json|text|markdown`: Output format (default: markdown)
- `--output <file>`: Output file path (default: `.tapps-agents/evaluations/evaluation-{timestamp}.md`)

**Example:**
```bash
tapps-agents evaluator evaluate --workflow-id workflow-123 --format markdown
```

### Cursor Skills API

**Command:** `@evaluator *evaluate [--workflow-id <id>]`

**Example:**
```
@evaluator *evaluate
@evaluator *evaluate-workflow workflow-123
```

---

## Configuration

**File:** `.tapps-agents/config.yaml`

**Section:**
```yaml
evaluator:
  auto_run: false  # Run automatically at end of workflows
  output_dir: ".tapps-agents/evaluations"
  thresholds:
    quality_score: 70.0
    workflow_completion: 0.8
  enabled: true
```

---

## Error Handling

**Error Types:**
- `EvaluationError`: Base exception for evaluation failures
- `DataCollectionError`: Failed to collect evaluation data
- `AnalysisError`: Failed during analysis
- `ReportGenerationError`: Failed to generate report

**Error Handling Strategy:**
- Graceful degradation (continue with available data)
- Clear error messages
- Logging for debugging
- Return partial results if possible

---

## Next Steps

Proceed to Step 5: Code Implementation
