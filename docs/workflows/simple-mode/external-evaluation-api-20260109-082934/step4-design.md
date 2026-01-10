# API Design: External Evaluation API

## Metadata
- **Created**: 2026-01-09T08:29:34
- **Workflow**: Build
- **Feature**: External Evaluation Feedback API

## API Specifications

### Python API

#### EvaluatorAgent.submit_feedback()

**Purpose**: Submit feedback about TappsCodingAgents performance from external projects

**Signature**:
```python
async def submit_feedback(
    self,
    performance_ratings: dict[str, float],
    suggestions: list[str],
    context: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
```

**Parameters**:
- `performance_ratings` (dict[str, float], required): Dictionary of metric names to ratings (typically 1.0-10.0 scale)
  - Example: `{"overall": 8.5, "usability": 7.0, "documentation": 9.0}`
  - Keys are metric names (strings)
  - Values are numeric ratings (floats)
- `suggestions` (list[str], required): List of text suggestions for improvement
  - Example: `["Improve error messages", "Add more examples"]`
  - Must contain at least one suggestion
- `context` (dict[str, Any], optional): Optional context information
  - Common keys: `workflow_id`, `agent_id`, `task_type`, `timestamp`
  - Example: `{"workflow_id": "workflow-123", "agent_id": "reviewer"}`
- `metrics` (dict[str, Any], optional): Optional performance metrics
  - Common keys: `execution_time_seconds`, `quality_score`, `code_lines_processed`
  - Example: `{"execution_time_seconds": 45.2, "quality_score": 85.0}`
- `project_id` (str, optional): Optional project identifier for tracking

**Returns**:
```python
{
    "success": True,
    "feedback_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Feedback submitted successfully",
    "timestamp": "2026-01-09T08:29:34Z"
}
```

**Errors**:
- `ValueError`: Invalid input data (e.g., ratings out of range, empty suggestions)
- `IOError`: File system error (permissions, disk space)
- `RuntimeError`: Storage initialization failed

**Example Usage**:
```python
from tapps_agents.agents.evaluator.agent import EvaluatorAgent

async def main():
    evaluator = EvaluatorAgent()
    await evaluator.activate()
    
    result = await evaluator.submit_feedback(
        performance_ratings={
            "overall": 8.5,
            "usability": 7.0,
            "documentation": 9.0
        },
        suggestions=[
            "Improve error messages",
            "Add more examples in documentation"
        ],
        context={
            "workflow_id": "my-workflow-123",
            "agent_id": "reviewer"
        },
        metrics={
            "execution_time_seconds": 45.2
        },
        project_id="my-project-v1.0"
    )
    
    print(f"Feedback ID: {result['feedback_id']}")
    await evaluator.close()

import asyncio
asyncio.run(main())
```

---

#### EvaluatorAgent.get_feedback()

**Purpose**: Retrieve a specific feedback entry by ID

**Signature**:
```python
async def get_feedback(self, feedback_id: str) -> dict[str, Any]:
```

**Parameters**:
- `feedback_id` (str, required): UUID of the feedback entry

**Returns**:
```python
{
    "success": True,
    "feedback": {
        "feedback_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-01-09T08:29:34Z",
        "performance_ratings": {"overall": 8.5, "usability": 7.0},
        "suggestions": ["Improve error messages"],
        "context": {"workflow_id": "workflow-123"},
        "metrics": {"execution_time_seconds": 45.2},
        "project_id": "my-project-v1.0"
    }
}
```

**Errors**:
- `FileNotFoundError`: Feedback ID not found
- `ValueError`: Invalid feedback ID format

---

#### EvaluatorAgent.list_feedback()

**Purpose**: List feedback entries with optional filtering

**Signature**:
```python
async def list_feedback(
    self,
    workflow_id: str | None = None,
    agent_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
```

**Parameters**:
- `workflow_id` (str, optional): Filter by workflow ID
- `agent_id` (str, optional): Filter by agent ID
- `start_date` (str, optional): ISO format date string (e.g., "2026-01-01")
- `end_date` (str, optional): ISO format date string (e.g., "2026-01-31")
- `limit` (int, optional): Maximum number of entries to return

**Returns**:
```python
{
    "success": True,
    "count": 10,
    "feedback": [
        {
            "feedback_id": "...",
            "timestamp": "...",
            "performance_ratings": {...},
            "suggestions": [...],
            ...
        },
        ...
    ]
}
```

---

### CLI API

#### Command: `tapps-agents evaluator submit-feedback`

**Purpose**: Submit feedback via command line

**Syntax**:
```bash
tapps-agents evaluator submit-feedback \
    --rating <metric>=<value> [--rating <metric>=<value> ...] \
    --suggestion <text> [--suggestion <text> ...] \
    [--workflow-id <id>] \
    [--agent-id <id>] \
    [--task-type <type>] \
    [--metric <key>=<value>] \
    [--project-id <id>] \
    [--file <path>]
```

**Arguments**:
- `--rating <metric>=<value>` (required, repeatable): Performance rating
  - Example: `--rating overall=8.5 --rating usability=7.0`
  - Value must be a number (typically 1.0-10.0)
- `--suggestion <text>` (required, repeatable): Suggestion text
  - Example: `--suggestion "Improve error messages" --suggestion "Add examples"`
- `--workflow-id <id>` (optional): Workflow identifier
- `--agent-id <id>` (optional): Agent identifier
- `--task-type <type>` (optional): Task type (e.g., "code-review", "test-generation")
- `--metric <key>=<value>` (optional, repeatable): Performance metric
  - Example: `--metric execution_time_seconds=45.2`
- `--project-id <id>` (optional): Project identifier
- `--file <path>` (optional): JSON file with feedback data (alternative to command-line args)

**File Format** (for `--file` option):
```json
{
    "performance_ratings": {
        "overall": 8.5,
        "usability": 7.0,
        "documentation": 9.0
    },
    "suggestions": [
        "Improve error messages",
        "Add more examples in documentation"
    ],
    "context": {
        "workflow_id": "workflow-123",
        "agent_id": "reviewer",
        "task_type": "code-review"
    },
    "metrics": {
        "execution_time_seconds": 45.2,
        "quality_score": 85.0
    },
    "project_id": "my-project-v1.0"
}
```

**Output**:
```
Feedback submitted successfully
Feedback ID: 550e8400-e29b-41d4-a716-446655440000
Saved to: .tapps-agents/feedback/feedback-550e8400-e29b-41d4-a716-446655440000.json
```

**Exit Codes**:
- `0`: Success
- `1`: Validation error (invalid input)
- `2`: File system error
- `3`: Other error

**Examples**:

```bash
# Basic feedback
tapps-agents evaluator submit-feedback \
    --rating overall=8.5 \
    --rating usability=7.0 \
    --suggestion "Improve error messages"

# With context
tapps-agents evaluator submit-feedback \
    --rating overall=9.0 \
    --suggestion "Great documentation" \
    --workflow-id workflow-123 \
    --agent-id reviewer \
    --project-id my-project-v1.0

# From JSON file
tapps-agents evaluator submit-feedback \
    --file feedback-data.json
```

---

#### Command: `tapps-agents evaluator get-feedback`

**Purpose**: Retrieve feedback by ID

**Syntax**:
```bash
tapps-agents evaluator get-feedback <feedback-id> [--format json|text]
```

**Arguments**:
- `feedback-id` (required): UUID of feedback entry
- `--format` (optional): Output format (default: `text`)

**Output** (text format):
```
Feedback ID: 550e8400-e29b-41d4-a716-446655440000
Timestamp: 2026-01-09T08:29:34Z

Performance Ratings:
  overall: 8.5
  usability: 7.0
  documentation: 9.0

Suggestions:
  - Improve error messages
  - Add more examples in documentation

Context:
  workflow_id: workflow-123
  agent_id: reviewer

Metrics:
  execution_time_seconds: 45.2

Project ID: my-project-v1.0
```

---

#### Command: `tapps-agents evaluator list-feedback`

**Purpose**: List feedback entries with optional filtering

**Syntax**:
```bash
tapps-agents evaluator list-feedback \
    [--workflow-id <id>] \
    [--agent-id <id>] \
    [--start-date <date>] \
    [--end-date <date>] \
    [--limit <n>] \
    [--format json|text]
```

**Arguments**:
- `--workflow-id <id>` (optional): Filter by workflow ID
- `--agent-id <id>` (optional): Filter by agent ID
- `--start-date <date>` (optional): Start date (YYYY-MM-DD)
- `--end-date <date>` (optional): End date (YYYY-MM-DD)
- `--limit <n>` (optional): Maximum entries to return
- `--format` (optional): Output format (default: `text`)

**Output** (text format):
```
Found 10 feedback entries

1. Feedback ID: 550e8400-e29b-41d4-a716-446655440000
   Timestamp: 2026-01-09T08:29:34Z
   Overall Rating: 8.5
   Suggestions: 2

2. Feedback ID: ...
   ...
```

---

## Data Models

### FeedbackData (Pydantic Model)

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

class FeedbackContext(BaseModel):
    """Optional context information for feedback."""
    workflow_id: str | None = None
    agent_id: str | None = None
    task_type: str | None = None
    timestamp: datetime | None = None

class FeedbackMetrics(BaseModel):
    """Optional performance metrics."""
    execution_time_seconds: float | None = None
    quality_score: float | None = None
    code_lines_processed: int | None = None
    # Allow additional metrics
    additional: dict[str, Any] | None = None

class FeedbackData(BaseModel):
    """Feedback data model for external evaluation."""
    
    feedback_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    performance_ratings: dict[str, float] = Field(..., min_length=1)
    suggestions: list[str] = Field(..., min_length=1)
    context: FeedbackContext | None = None
    metrics: FeedbackMetrics | None = None
    project_id: str | None = None
    
    @field_validator('performance_ratings')
    @classmethod
    def validate_ratings(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate rating values are in reasonable range."""
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Rating '{key}' must be numeric")
            if value < 0.0 or value > 10.0:
                raise ValueError(f"Rating '{key}' must be between 0.0 and 10.0")
        return v
    
    @field_validator('suggestions')
    @classmethod
    def validate_suggestions(cls, v: list[str]) -> list[str]:
        """Validate suggestions are non-empty strings."""
        if not v:
            raise ValueError("At least one suggestion is required")
        for suggestion in v:
            if not isinstance(suggestion, str) or not suggestion.strip():
                raise ValueError("Suggestions must be non-empty strings")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
```

## Error Handling

### Validation Errors

**Python API**:
- Raises `ValueError` with descriptive message
- Field-level error details available via Pydantic validation

**CLI**:
- Prints error message to stderr
- Returns exit code 1
- Example: `Error: Rating 'overall' must be between 0.0 and 10.0`

### Storage Errors

**Python API**:
- Raises `IOError` for file system errors
- Raises `RuntimeError` for initialization failures
- Errors include context (file path, operation type)

**CLI**:
- Prints error message to stderr
- Returns exit code 2
- Example: `Error: Failed to save feedback: Permission denied`

### Not Found Errors

**Python API**:
- Raises `FileNotFoundError` for missing feedback

**CLI**:
- Prints error message to stderr
- Returns exit code 1
- Example: `Error: Feedback not found: 550e8400-...`

## Usage Examples

### Python API Examples

**Basic Submission**:
```python
result = await evaluator.submit_feedback(
    performance_ratings={"overall": 8.5},
    suggestions=["Great framework!"]
)
```

**Advanced Submission**:
```python
result = await evaluator.submit_feedback(
    performance_ratings={
        "overall": 8.5,
        "usability": 7.0,
        "documentation": 9.0,
        "performance": 8.0
    },
    suggestions=[
        "Improve error messages",
        "Add more examples",
        "Consider async/await patterns"
    ],
    context={
        "workflow_id": "my-workflow",
        "agent_id": "reviewer",
        "task_type": "code-review"
    },
    metrics={
        "execution_time_seconds": 45.2,
        "quality_score": 85.0
    },
    project_id="my-project-v1.0"
)
```

**Retrieval**:
```python
feedback = await evaluator.get_feedback("550e8400-...")
print(feedback["feedback"]["performance_ratings"])
```

**Listing**:
```python
all_feedback = await evaluator.list_feedback(limit=10)
recent_feedback = await evaluator.list_feedback(
    start_date="2026-01-01",
    end_date="2026-01-31"
)
```

### CLI Examples

**Quick Feedback**:
```bash
tapps-agents evaluator submit-feedback \
    --rating overall=9.0 \
    --suggestion "Excellent work!"
```

**Detailed Feedback**:
```bash
tapps-agents evaluator submit-feedback \
    --rating overall=8.5 \
    --rating usability=7.0 \
    --rating documentation=9.0 \
    --suggestion "Improve error messages" \
    --suggestion "Add more examples" \
    --workflow-id workflow-123 \
    --agent-id reviewer \
    --project-id my-project-v1.0
```

**From File**:
```bash
# Create feedback.json
cat > feedback.json << EOF
{
    "performance_ratings": {"overall": 8.5},
    "suggestions": ["Great framework!"]
}
EOF

# Submit
tapps-agents evaluator submit-feedback --file feedback.json
```

**Query Feedback**:
```bash
# List all
tapps-agents evaluator list-feedback

# Filter by date
tapps-agents evaluator list-feedback \
    --start-date 2026-01-01 \
    --end-date 2026-01-31

# Get specific feedback
tapps-agents evaluator get-feedback 550e8400-...
```
