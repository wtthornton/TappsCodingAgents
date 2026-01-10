# Enhanced Prompt: External Evaluation API for TappsCodingAgents

## Metadata
- **Created**: 2026-01-09T08:29:34
- **Workflow**: Build
- **Feature**: External Evaluation Feedback API

## Analysis

### Intent
Create a Python API function/class that external projects can call to provide feedback and evaluation about how well TappsCodingAgents performed on their tasks. This enables continuous improvement through real-world usage feedback.

### Scope
- **Feature Type**: API Extension
- **Component**: New functionality for EvaluatorAgent or new ExternalFeedbackAgent
- **Integration Points**: 
  - EvaluatorAgent (existing agent that evaluates framework effectiveness)
  - Storage system (persist feedback)
  - Analytics/metrics system (aggregate feedback)

### Complexity
- **Level**: Medium
- **Dependencies**: 
  - Existing EvaluatorAgent infrastructure
  - Storage manager for persistence
  - Optional: Analytics aggregation

### Technologies
- Python 3.9+
- Pydantic (for data validation)
- JSON (for data serialization)
- Pathlib (for file operations)

## Requirements

### Functional Requirements

1. **API Function/Class**
   - Provide a Python function or class method that external projects can call
   - Accept feedback data: ratings, suggestions, metrics, comments
   - Support both programmatic (Python API) and CLI access
   - Store feedback persistently for analysis

2. **Feedback Data Model**
   - Performance ratings (1-10 scale or similar)
   - Text suggestions for improvement
   - Optional metrics (execution time, quality scores, etc.)
   - Context information (workflow ID, agent used, task type)
   - Timestamp and project identifier

3. **Storage**
   - Persist feedback to `.tapps-agents/feedback/` directory
   - JSON format for easy analysis
   - Support aggregation and querying

4. **Analysis Integration**
   - Feed collected feedback into EvaluatorAgent
   - Enable trend analysis over time
   - Support reporting and metrics

### Non-Functional Requirements

1. **Usability**
   - Simple API - easy for external projects to integrate
   - Clear documentation and examples
   - Minimal dependencies

2. **Performance**
   - Fast feedback submission (non-blocking preferred)
   - Efficient storage format
   - Scalable to many feedback entries

3. **Privacy & Security**
   - No sensitive code or data in feedback (unless explicitly provided)
   - Optional anonymization
   - Configurable data retention

4. **Compatibility**
   - Works with existing EvaluatorAgent
   - Compatible with Python 3.9+
   - Cross-platform (Windows, Linux, macOS)

## Architecture Guidance

### Recommended Approach

1. **Extend EvaluatorAgent**
   - Add `submit_feedback()` method to EvaluatorAgent
   - Leverage existing infrastructure (storage, analytics)
   - Maintain consistency with existing evaluation system

2. **Feedback Storage Module**
   - Create `tapps_agents/core/feedback_storage.py`
   - Handle persistence, retrieval, aggregation
   - Integrate with existing storage manager

3. **Data Models**
   - Pydantic models for type safety
   - Validation of feedback data
   - Support for optional fields

4. **CLI Command**
   - Add `evaluator submit-feedback` command
   - Enable manual feedback submission
   - Support batch operations

### Design Patterns

- **Repository Pattern**: Separate storage logic from business logic
- **Builder Pattern**: For constructing feedback objects
- **Observer Pattern**: Optional - notify when feedback is received

## Codebase Context

### Existing Components

1. **EvaluatorAgent** (`tapps_agents/agents/evaluator/agent.py`)
   - Evaluates framework effectiveness internally
   - Has analyzers and report generators
   - Can be extended with feedback collection

2. **Storage Manager** (`tapps_agents/core/storage_manager.py`)
   - Handles persistence of evaluations
   - Supports JSON storage
   - Can be extended for feedback storage

3. **CLI Structure** (`tapps_agents/cli/commands/evaluator.py`)
   - Existing evaluator commands
   - Can add new `submit-feedback` command

### Integration Points

- **EvaluatorAgent.run()**: Add new command handler
- **Storage Manager**: Extend with feedback storage methods
- **CLI Parser**: Add feedback submission command

## Quality Standards

### Code Quality Thresholds
- **Overall Score Threshold**: 70.0
- **Maintainability**: 8.0+
- **Security**: 7.0+
- **Test Coverage**: 80%+

### Coding Standards
- Type hints for all functions
- Docstrings for all public methods
- Error handling with meaningful messages
- Logging for debugging and monitoring
- PEP 8 compliance

### Testing Requirements
- Unit tests for feedback submission
- Integration tests with storage
- CLI command tests
- Error handling tests

## Implementation Strategy

### Phase 1: Core API (MVP)
1. Create feedback data models (Pydantic)
2. Add `submit_feedback()` method to EvaluatorAgent
3. Implement basic storage (JSON files)
4. Add CLI command

### Phase 2: Enhanced Features
1. Add feedback aggregation methods
2. Integrate with existing evaluation reports
3. Add analytics/metrics
4. Support batch operations

### Phase 3: Advanced Features (Optional)
1. Feedback validation rules
2. Automated analysis of feedback trends
3. Integration with learning system
4. Webhook support (future)

## Enhanced Prompt

Create an external evaluation API for TappsCodingAgents that allows other projects to submit feedback about framework performance. The API should:

1. **Provide a simple Python function/class method** (`EvaluatorAgent.submit_feedback()`) that accepts:
   - Performance ratings (numeric scores)
   - Text suggestions for improvement
   - Optional context (workflow_id, agent_id, task_type)
   - Optional metrics (execution_time, quality_scores, etc.)

2. **Store feedback persistently** in `.tapps-agents/feedback/` directory as JSON files with:
   - Unique feedback IDs
   - Timestamps
   - Structured data format

3. **Integrate with existing EvaluatorAgent** infrastructure:
   - Extend `EvaluatorAgent` class with feedback submission
   - Leverage existing storage patterns
   - Support aggregation and analysis

4. **Provide CLI command** (`tapps-agents evaluator submit-feedback`) for manual submission

5. **Follow framework patterns**:
   - Type hints and Pydantic models
   - Error handling and logging
   - Comprehensive documentation
   - Unit and integration tests

The implementation should be production-ready, well-tested, and follow TappsCodingAgents coding standards.
