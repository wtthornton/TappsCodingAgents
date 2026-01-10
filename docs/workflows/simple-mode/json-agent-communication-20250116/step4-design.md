# Step 4: Component Design - JSON Schemas and Converters

**Generated**: 2025-01-16  
**Workflow**: Build - JSON Agent-to-Agent Communication Implementation  
**Agent**: @designer  
**Stage**: Component Design Specifications

---

## JSON Schema Definitions

### Base Schema

All agent outputs extend from a base schema with common fields:

```python
# tapps_agents/schemas/base.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BaseAgentOutput(BaseModel):
    """Base schema for all agent outputs."""
    
    status: str = Field(
        description="Execution status",
        pattern="^(complete|in_progress|failed|cancelled)$"
    )
    timestamp: datetime = Field(
        description="Timestamp when output was generated"
    )
    agent: str = Field(
        description="Agent name that generated this output"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for tracking across workflow steps"
    )
    passes: Optional[bool] = Field(
        default=None,
        description="Status tracking (Ralph-style): true if requirements met, false otherwise"
    )
    completed: Optional[bool] = Field(
        default=None,
        description="Whether the task is completed (for autonomous execution)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "complete",
                "timestamp": "2025-01-16T12:00:00Z",
                "agent": "analyst",
                "correlation_id": "abc123",
                "passes": True,
                "completed": True
            }
        }
```

---

## Agent-Specific Schemas

### 1. Requirements Schema (Analyst Agent)

```python
# tapps_agents/schemas/requirements.py
from pydantic import BaseModel, Field
from typing import Optional, List

class Requirement(BaseModel):
    """Individual requirement."""
    id: str = Field(description="Unique requirement ID")
    description: str = Field(description="Requirement description")
    priority: Optional[str] = Field(default=None, description="Priority: high, medium, low")
    category: Optional[str] = Field(default=None, description="Category/tag")

class ExpertConsultation(BaseModel):
    """Expert consultation result."""
    domain: str = Field(description="Expert domain")
    weighted_answer: str = Field(description="Weighted consensus answer")
    confidence: float = Field(description="Confidence score (0-1)")
    agreement_level: float = Field(description="Agreement level (0-1)")
    primary_expert: str = Field(description="Primary expert name")

class RequirementsOutput(BaseAgentOutput):
    """Analyst agent requirements output."""
    
    functional_requirements: List[Requirement] = Field(
        default_factory=list,
        description="Functional requirements"
    )
    non_functional_requirements: List[Requirement] = Field(
        default_factory=list,
        description="Non-functional requirements (performance, security, etc.)"
    )
    technical_constraints: List[str] = Field(
        default_factory=list,
        description="Technical constraints"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions"
    )
    open_questions: List[str] = Field(
        default_factory=list,
        description="Open questions"
    )
    expert_consultations: Optional[List[ExpertConsultation]] = Field(
        default=None,
        description="Expert consultation results (if applicable)"
    )
    requirements_analysis: Optional[str] = Field(
        default=None,
        description="Requirements analysis summary"
    )
```

**JSON Example**:
```json
{
  "status": "complete",
  "timestamp": "2025-01-16T12:00:00Z",
  "agent": "analyst",
  "correlation_id": "req-123",
  "passes": true,
  "completed": true,
  "functional_requirements": [
    {
      "id": "FR-001",
      "description": "System shall authenticate users via JWT tokens",
      "priority": "high",
      "category": "security"
    }
  ],
  "non_functional_requirements": [
    {
      "id": "NFR-001",
      "description": "API response time shall be < 200ms",
      "priority": "medium",
      "category": "performance"
    }
  ],
  "technical_constraints": [
    "Must use Python 3.10+",
    "Must support Windows and Linux"
  ],
  "assumptions": [
    "Users have valid email addresses"
  ]
}
```

---

### 2. User Story Schema (Planner Agent)

```python
# tapps_agents/schemas/story.py
from pydantic import BaseModel, Field
from typing import Optional, List

class AcceptanceCriterion(BaseModel):
    """Acceptance criterion for a user story."""
    description: str = Field(description="Acceptance criterion description")
    verified: bool = Field(default=False, description="Whether criterion is verified")

class UserStory(BaseModel):
    """User story schema."""
    story_id: str = Field(description="Story ID (e.g., 'STORY-001')")
    title: str = Field(description="Story title")
    description: str = Field(description="Story description")
    epic: Optional[str] = Field(default=None, description="Epic name/ID")
    domain: Optional[str] = Field(default=None, description="Domain/category")
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    complexity: int = Field(default=3, ge=1, le=5, description="Complexity (1-5 scale)")
    status: str = Field(
        default="draft",
        pattern="^(draft|ready|in_progress|completed|blocked)$"
    )
    acceptance_criteria: List[AcceptanceCriterion] = Field(
        default_factory=list,
        description="Acceptance criteria"
    )
    tasks: List[str] = Field(default_factory=list, description="Task breakdown")
    estimated_effort_hours: Optional[float] = Field(default=None, description="Estimated effort")
    risk_level: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")
    dependencies: List[str] = Field(default_factory=list, description="Story dependencies")
    story_points: Optional[int] = Field(default=None, description="Story points")
    passes: Optional[bool] = Field(default=None, description="Status tracking (Ralph-style)")

class PlanningOutput(BaseAgentOutput):
    """Planner agent output."""
    
    stories: List[UserStory] = Field(
        default_factory=list,
        description="User stories"
    )
    plan_summary: Optional[str] = Field(
        default=None,
        description="Planning summary"
    )
    estimated_total_effort: Optional[float] = Field(
        default=None,
        description="Total estimated effort in hours"
    )
    suggested_priority_order: Optional[List[str]] = Field(
        default=None,
        description="Suggested story execution order"
    )
```

**JSON Example**:
```json
{
  "status": "complete",
  "timestamp": "2025-01-16T12:00:00Z",
  "agent": "planner",
  "correlation_id": "plan-123",
  "passes": true,
  "completed": true,
  "stories": [
    {
      "story_id": "STORY-001",
      "title": "Implement JSON schema definitions",
      "description": "Create JSON schemas for all agent outputs",
      "priority": "high",
      "complexity": 3,
      "status": "draft",
      "acceptance_criteria": [
        {
          "description": "Pydantic models defined for all agent output types",
          "verified": false
        }
      ],
      "story_points": 8,
      "passes": null
    }
  ],
  "estimated_total_effort": 120.0
}
```

---

### 3. Architecture Schema (Architect Agent)

```python
# tapps_agents/schemas/architecture.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Component(BaseModel):
    """System component."""
    name: str = Field(description="Component name")
    description: str = Field(description="Component description")
    responsibilities: List[str] = Field(default_factory=list)
    interfaces: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

class DataFlow(BaseModel):
    """Data flow between components."""
    source: str = Field(description="Source component")
    target: str = Field(description="Target component")
    data: str = Field(description="Data being transferred")
    protocol: Optional[str] = Field(default=None, description="Protocol (HTTP, gRPC, etc.)")

class ArchitectureOutput(BaseAgentOutput):
    """Architect agent output."""
    
    architecture_overview: str = Field(description="Architecture overview")
    design_pattern: Optional[str] = Field(default=None, description="Primary design pattern")
    components: List[Component] = Field(default_factory=list, description="System components")
    data_flows: List[DataFlow] = Field(default_factory=list, description="Data flows")
    technology_stack: List[str] = Field(default_factory=list, description="Technology stack")
    performance_considerations: Optional[str] = Field(
        default=None,
        description="Performance considerations"
    )
    security_considerations: Optional[str] = Field(
        default=None,
        description="Security considerations"
    )
    scalability_considerations: Optional[str] = Field(
        default=None,
        description="Scalability considerations"
    )
```

**JSON Example**:
```json
{
  "status": "complete",
  "timestamp": "2025-01-16T12:00:00Z",
  "agent": "architect",
  "correlation_id": "arch-123",
  "passes": true,
  "completed": true,
  "architecture_overview": "Hybrid JSON/Markdown architecture with bidirectional conversion",
  "design_pattern": "Hybrid JSON/Markdown with Two-Way Conversion",
  "components": [
    {
      "name": "JSON Schema Layer",
      "description": "Pydantic models for all agent outputs",
      "responsibilities": ["Schema validation", "Type safety"],
      "dependencies": []
    }
  ],
  "technology_stack": ["Pydantic", "Python json", "markdown-it-py"]
}
```

---

### 4. Design Schema (Designer Agent)

```python
# tapps_agents/schemas/design.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class APIEndpoint(BaseModel):
    """API endpoint specification."""
    method: str = Field(pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    path: str = Field(description="API path")
    description: str = Field(description="Endpoint description")
    request_schema: Optional[Dict[str, Any]] = Field(default=None, description="Request schema")
    response_schema: Optional[Dict[str, Any]] = Field(default=None, description="Response schema")
    status_codes: List[int] = Field(default_factory=list, description="HTTP status codes")

class DataModel(BaseModel):
    """Data model specification."""
    name: str = Field(description="Model name")
    fields: Dict[str, str] = Field(description="Field name to type mapping")
    relationships: Optional[Dict[str, str]] = Field(default=None, description="Relationships")
    constraints: Optional[List[str]] = Field(default=None, description="Constraints")

class DesignOutput(BaseAgentOutput):
    """Designer agent output."""
    
    design_type: str = Field(
        pattern="^(api|data_model|component|ui)$",
        description="Type of design"
    )
    api_specification: Optional[List[APIEndpoint]] = Field(
        default=None,
        description="API endpoints (if design_type is 'api')"
    )
    data_models: Optional[List[DataModel]] = Field(
        default=None,
        description="Data models (if design_type is 'data_model')"
    )
    component_specifications: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Component specifications (if design_type is 'component')"
    )
    design_summary: Optional[str] = Field(default=None, description="Design summary")
```

---

### 5. Review Schema (Reviewer Agent)

**Note**: This schema extends the existing `ReviewArtifact` model.

```python
# tapps_agents/schemas/review.py
from pydantic import BaseModel, Field
from typing import Optional, List

class ReviewComment(BaseModel):
    """Review comment/finding."""
    message: str = Field(description="Comment message")
    severity: str = Field(pattern="^(error|warning|info|suggestion)$")
    line_number: Optional[int] = Field(default=None, description="Line number (if applicable)")
    file_path: Optional[str] = Field(default=None, description="File path (if applicable)")
    category: Optional[str] = Field(default=None, description="Category (security, performance, etc.)")

class ReviewOutput(BaseAgentOutput):
    """Reviewer agent output."""
    
    overall_score: Optional[float] = Field(default=None, ge=0, le=100, description="Overall score")
    complexity_score: Optional[float] = Field(default=None, ge=0, le=10)
    security_score: Optional[float] = Field(default=None, ge=0, le=10)
    maintainability_score: Optional[float] = Field(default=None, ge=0, le=10)
    test_coverage_score: Optional[float] = Field(default=None, ge=0, le=100)
    performance_score: Optional[float] = Field(default=None, ge=0, le=10)
    
    decision: Optional[str] = Field(
        default=None,
        pattern="^(APPROVED|APPROVED_WITH_SUGGESTIONS|CHANGES_REQUESTED)$"
    )
    passed: Optional[bool] = Field(default=None, description="Whether review passed threshold")
    threshold: Optional[float] = Field(default=None, description="Quality threshold")
    
    comments: List[ReviewComment] = Field(default_factory=list)
    security_findings: List[ReviewComment] = Field(default_factory=list)
    refactoring_suggestions: List[ReviewComment] = Field(default_factory=list)
    
    review_summary: Optional[str] = Field(default=None, description="Review summary")
```

---

### 6. Test Schema (Tester Agent)

```python
# tapps_agents/schemas/test.py
from pydantic import BaseModel, Field
from typing import Optional, List

class TestCase(BaseModel):
    """Test case specification."""
    name: str = Field(description="Test case name")
    description: str = Field(description="Test description")
    test_type: str = Field(pattern="^(unit|integration|e2e)$")
    steps: List[str] = Field(default_factory=list, description="Test steps")
    expected_result: str = Field(description="Expected result")
    status: Optional[str] = Field(default=None, pattern="^(pass|fail|pending)$")

class TestOutput(BaseAgentOutput):
    """Tester agent output."""
    
    test_plan_summary: str = Field(description="Test plan summary")
    test_cases: List[TestCase] = Field(default_factory=list, description="Test cases")
    coverage_target: Optional[float] = Field(default=None, ge=0, le=100, description="Coverage target")
    coverage_actual: Optional[float] = Field(default=None, ge=0, le=100, description="Actual coverage")
    test_files_created: List[str] = Field(default_factory=list, description="Test files created")
    validation_criteria: Optional[List[str]] = Field(default=None, description="Validation criteria")
```

---

### 7. Epic Schema (Epic Parser)

**Note**: This schema extends the existing `EpicDocument` model.

```python
# tapps_agents/schemas/epic.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class StoryStatus(str, Enum):
    """Story execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"

class EpicAcceptanceCriterion(BaseModel):
    """Acceptance criterion for an Epic story."""
    description: str = Field(description="Acceptance criterion description")
    verified: bool = Field(default=False, description="Whether criterion is verified")

class EpicStory(BaseModel):
    """Epic story schema (compatible with existing Story model)."""
    epic_number: int = Field(description="Epic number")
    story_number: int = Field(description="Story number")
    story_id: str = Field(description="Story ID (e.g., '8.1')")
    title: str = Field(description="Story title")
    description: str = Field(description="Story description")
    acceptance_criteria: List[EpicAcceptanceCriterion] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list, description="Story dependencies (e.g., ['8.1'])")
    story_points: Optional[int] = Field(default=None)
    status: StoryStatus = Field(default=StoryStatus.NOT_STARTED)
    passes: Optional[bool] = Field(default=None, description="Status tracking (Ralph-style)")
    file_path: Optional[str] = Field(default=None, description="Path to story file")

class EpicDocument(BaseModel):
    """Epic document schema (compatible with existing EpicDocument model)."""
    epic_number: int = Field(description="Epic number")
    title: str = Field(description="Epic title")
    goal: str = Field(description="Epic goal")
    description: str = Field(description="Epic description")
    stories: List[EpicStory] = Field(default_factory=list)
    priority: Optional[str] = Field(default=None)
    timeline: Optional[str] = Field(default=None)
    prerequisites: List[str] = Field(default_factory=list)
    execution_notes: Dict[str, Any] = Field(default_factory=dict)
    definition_of_done: List[str] = Field(default_factory=list)
    status: Optional[str] = Field(default=None)
    file_path: Optional[str] = Field(default=None)
    
    # Status tracking
    passes: Optional[bool] = Field(default=None, description="Whether epic passes (all stories pass)")
    completion_percentage: Optional[float] = Field(default=None, ge=0, le=100)
```

---

## Converter Specifications

### Markdown to JSON Converter

**File**: `tapps_agents/converters/markdown_to_json.py`

**Function Signature**:
```python
def markdown_to_json(
    markdown_content: str,
    schema_type: str,
    validate: bool = True
) -> dict[str, Any]:
    """
    Convert markdown artifact to JSON schema.
    
    Args:
        markdown_content: Markdown content to convert
        schema_type: Schema type ('requirements', 'story', 'architecture', etc.)
        validate: Whether to validate output against schema
        
    Returns:
        JSON dictionary (validated if validate=True)
        
    Raises:
        ValueError: If conversion fails
        ValidationError: If validation fails
    """
```

**Implementation Strategy**:
1. Parse markdown using markdown parser (extract headers, lists, tables, code blocks)
2. Map parsed structure to schema fields based on schema_type
3. Create Pydantic model instance
4. Validate (if validate=True)
5. Return model.model_dump()

**Supported Schema Types**:
- `requirements` → RequirementsOutput
- `story` / `planning` → PlanningOutput
- `architecture` → ArchitectureOutput
- `design` → DesignOutput
- `review` → ReviewOutput
- `test` → TestOutput
- `epic` → EpicDocument

---

### JSON to Markdown Generator

**File**: `tapps_agents/converters/json_to_markdown.py`

**Function Signature**:
```python
def json_to_markdown(
    json_data: dict[str, Any] | BaseModel,
    schema_type: str,
    template: str | None = None
) -> str:
    """
    Generate markdown from JSON schema.
    
    Args:
        json_data: JSON dictionary or Pydantic model
        schema_type: Schema type (for template selection)
        template: Optional custom template
        
    Returns:
        Formatted markdown string
    """
```

**Implementation Strategy**:
1. Load JSON data (or extract from Pydantic model)
2. Select template based on schema_type (or use custom template)
3. Generate markdown sections:
   - Headers (H1, H2, H3)
   - Lists (bulleted, numbered)
   - Tables (for structured data)
   - Code blocks (for examples)
4. Format consistently (spacing, line breaks)
5. Return formatted markdown

**Templates**:
- Templates stored in `tapps_agents/converters/templates/`
- Jinja2-style templating for flexibility
- Default templates for each schema type

---

## Implementation Notes

### Schema Compatibility

- **Backward Compatibility**: Schemas extend/complement existing dataclass models (ReviewArtifact, PlanningArtifact, EpicDocument)
- **Migration Path**: Existing dataclasses can be converted to Pydantic models gradually
- **Status Tracking**: All schemas include `passes` and `completed` fields for Ralph-style status tracking

### Validation

- **Pydantic Validation**: All schemas use Pydantic for type safety and validation
- **JSON Schema Export**: Generate JSON Schema for documentation: `schema.model_json_schema()`
- **Error Handling**: Validation errors include field paths and error messages

### Performance

- **Lazy Loading**: Schemas are imported only when needed
- **Caching**: Parsed markdown/JSON can be cached for repeated conversions
- **Streaming**: Not needed (artifacts are small to medium size)

---

## Next Steps

Proceed to Step 5 (Implementation) to create the actual code for schemas and converters.
