# Architecture Design: External Evaluation API

## Metadata
- **Created**: 2026-01-09T08:29:34
- **Workflow**: Build
- **Feature**: External Evaluation Feedback API

## System Architecture

### Overview

The External Evaluation API extends the existing EvaluatorAgent to accept feedback from external projects. The architecture follows the existing TappsCodingAgents patterns and integrates seamlessly with current infrastructure.

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    External Projects                        │
│  (Python API or CLI calls)                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ submit_feedback()
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                 EvaluatorAgent                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  submit_feedback() method                            │  │
│  │  - Validates input                                    │  │
│  │  - Creates FeedbackData object                        │  │
│  │  - Delegates to FeedbackStorage                       │  │
│  └──────────────────┬───────────────────────────────────┘  │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ stores feedback
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              FeedbackStorage (new module)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  - save_feedback(feedback_data)                      │  │
│  │  - load_feedback(feedback_id)                        │  │
│  │  - list_feedback(filters)                            │  │
│  │  - aggregate_feedback(filters)                       │  │
│  └──────────────────┬───────────────────────────────────┘  │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ JSON files
                    ▼
┌─────────────────────────────────────────────────────────────┐
│         .tapps-agents/feedback/                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  feedback-{uuid}.json                                │  │
│  │  feedback-{uuid}.json                                │  │
│  │  ...                                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Feedback Submission**
   - External project calls `EvaluatorAgent.submit_feedback()` or CLI command
   - EvaluatorAgent validates input using Pydantic models
   - FeedbackStorage saves to JSON file with unique ID
   - Returns feedback ID and confirmation

2. **Feedback Retrieval**
   - EvaluatorAgent or analysis tools call FeedbackStorage methods
   - Storage reads JSON files from `.tapps-agents/feedback/`
   - Data parsed and returned as FeedbackData objects
   - Optional filtering and aggregation

3. **Integration with Evaluation Reports**
   - EvaluatorAgent can include feedback in evaluation reports
   - Feedback aggregated with other metrics
   - Trends analyzed over time

## Component Design

### 1. Feedback Data Models (`tapps_agents/core/feedback_models.py`)

**Purpose**: Type-safe data structures for feedback

**Classes**:
- `FeedbackData`: Main feedback data model
- `PerformanceRating`: Ratings with validation
- `FeedbackContext`: Optional context information
- `FeedbackMetrics`: Optional metrics data

**Key Attributes**:
```python
class FeedbackData(BaseModel):
    feedback_id: str  # UUID
    timestamp: datetime
    performance_ratings: dict[str, float]  # e.g., {"overall": 8.5, "usability": 7.0}
    suggestions: list[str]
    context: FeedbackContext | None
    metrics: FeedbackMetrics | None
    project_id: str | None  # Optional identifier
```

### 2. FeedbackStorage (`tapps_agents/core/feedback_storage.py`)

**Purpose**: Handle persistent storage and retrieval of feedback

**Methods**:
- `save_feedback(feedback_data: FeedbackData) -> str`: Save feedback, return ID
- `load_feedback(feedback_id: str) -> FeedbackData | None`: Load by ID
- `list_feedback(filters: dict | None = None) -> list[FeedbackData]`: List with optional filters
- `aggregate_feedback(filters: dict | None = None) -> dict`: Aggregate statistics

**Storage Format**:
- JSON files in `.tapps-agents/feedback/`
- Filename: `feedback-{uuid}.json`
- Human-readable format for easy inspection

### 3. EvaluatorAgent Extension (`tapps_agents/agents/evaluator/agent.py`)

**Purpose**: Add feedback submission capability to existing agent

**New Methods**:
- `submit_feedback(...) -> dict[str, Any]`: Submit feedback (Python API)
- `_handle_submit_feedback(...) -> dict[str, Any]`: Internal handler
- `get_feedback(feedback_id: str) -> dict[str, Any]`: Retrieve feedback
- `list_feedback(...) -> dict[str, Any]`: List feedback with filters

**Integration**:
- Extends existing `run()` method with new command
- Uses FeedbackStorage for persistence
- Follows existing error handling patterns

### 4. CLI Command (`tapps_agents/cli/commands/evaluator.py`)

**Purpose**: Enable feedback submission via CLI

**Command**: `tapps-agents evaluator submit-feedback`

**Arguments**:
- `--rating <metric>=<value>`: Performance ratings (can specify multiple)
- `--suggestion <text>`: Suggestions (can specify multiple)
- `--workflow-id <id>`: Optional workflow ID
- `--agent-id <id>`: Optional agent ID
- `--file <path>`: Optional JSON file with feedback data
- `--project-id <id>`: Optional project identifier

**Output**: Feedback ID and confirmation message

## Data Models

### FeedbackData Structure

```python
{
    "feedback_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-01-09T08:29:34Z",
    "performance_ratings": {
        "overall": 8.5,
        "usability": 7.0,
        "documentation": 9.0,
        "performance": 8.0
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

### Storage Schema

**File**: `.tapps-agents/feedback/feedback-{uuid}.json`

**Format**: JSON (pretty-printed for readability)

**Validation**: Pydantic models ensure data integrity

## Integration Points

### 1. EvaluatorAgent Integration

- Add `submit_feedback` to command handler in `run()` method
- Import FeedbackStorage and FeedbackData models
- Follow existing error handling patterns
- Maintain backward compatibility

### 2. Storage Integration

- Use existing storage patterns from `storage_manager.py`
- Store in `.tapps-agents/feedback/` (similar to `.tapps-agents/evaluations/`)
- Create directory if missing
- Handle file system errors gracefully

### 3. CLI Integration

- Add parser in `tapps_agents/cli/parsers/evaluator.py`
- Add command handler in `tapps_agents/cli/commands/evaluator.py`
- Follow existing CLI patterns
- Support both interactive and scripted usage

## Performance Considerations

### Storage Efficiency
- JSON files are human-readable and easy to analyze
- Files stored individually for easy inspection
- No database required (simplifies deployment)
- Optional: Can migrate to database if volume grows

### Scalability
- File-based storage suitable for moderate volumes
- Can aggregate thousands of feedback entries
- Future: Database backend if needed

### Performance Targets
- Feedback submission: < 100ms (file I/O)
- Feedback retrieval: < 500ms (for 1000 entries)
- Aggregation: < 2s (for 1000 entries)

## Security Considerations

### Data Privacy
- No automatic code or file content storage
- Only explicit feedback data stored
- Optional project_id (user controls)
- Feedback data is user-provided (trusted source)

### Access Control
- Files stored in `.tapps-agents/feedback/` (project directory)
- Standard file system permissions apply
- No network exposure (local storage only)

### Validation
- Pydantic models validate all input
- Type checking prevents malformed data
- Range validation for ratings (e.g., 1-10)

## Error Handling

### Validation Errors
- Clear error messages for invalid input
- Field-level validation feedback
- Type conversion errors handled gracefully

### Storage Errors
- File system errors (permissions, disk space)
- JSON serialization errors
- Directory creation failures
- All errors logged with context

### User Experience
- Errors return structured error objects
- CLI provides user-friendly error messages
- Python API raises appropriate exceptions

## Testing Strategy

### Unit Tests
- FeedbackData model validation
- FeedbackStorage save/load operations
- EvaluatorAgent.submit_feedback() method
- Error handling scenarios

### Integration Tests
- End-to-end feedback submission workflow
- CLI command execution
- File system operations
- Data persistence verification

### Test Data
- Sample feedback data for testing
- Mock file system operations
- Test fixtures and helpers

## Deployment Considerations

### Backward Compatibility
- New functionality doesn't break existing EvaluatorAgent features
- Optional dependencies (no new required packages)
- Graceful degradation if storage fails

### Migration
- No migration needed (new feature)
- Existing evaluations unaffected
- Feedback storage is separate

### Configuration
- No new configuration required
- Storage directory created automatically
- Optional: Configurable storage location (future)

## Future Enhancements

### Phase 2 (Optional)
- Feedback aggregation dashboards
- Trend analysis and visualization
- Integration with learning system
- Automated feedback analysis

### Phase 3 (Optional)
- Database backend option
- Webhook notifications
- Feedback API server (HTTP endpoint)
- Real-time feedback processing
