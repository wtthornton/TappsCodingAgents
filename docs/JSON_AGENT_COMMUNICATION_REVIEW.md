# JSON Agent Communication, PRD, and User Stories - Review & Recommendations

## Executive Summary

This document reviews TappsCodingAgents' current JSON formats for:
1. **Agent-to-agent communication** (messaging system)
2. **PRD/Planning artifacts** (PlanningArtifact, UserStory)
3. **Epic/Story models** (EpicDocument, Story)
4. **Artifact schemas** (all artifact types)

**Overall Assessment**: Good foundation with versioned schemas and serialization, but there are opportunities for improvement in consistency, validation, and standardization.

## Current Implementation Review

### 1. Agent-to-Agent Communication (Messaging)

**Location**: `tapps_agents/workflow/messaging.py`

**Current Approach**:
- ✅ **Pydantic BaseModel** for message schemas
- ✅ **Schema versioning** (SCHEMA_VERSION = "1.0")
- ✅ **Type-safe validation** with Pydantic
- ✅ **File-based inbox/outbox** pattern
- ✅ **Message types**: TaskAssignmentMessage, StatusUpdateMessage, TaskCompleteMessage
- ✅ **Strict validation** (`extra: "forbid"`)

**Message Structure**:
```python
class BaseMessage(BaseModel):
    schema_version: str = Field(default=SCHEMA_VERSION)
    message_type: str
    workflow_id: str
    task_id: str
    agent_id: str
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utcnow)
    idempotency_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

**Strengths**:
- ✅ Modern approach (Pydantic v2)
- ✅ Strong type safety
- ✅ Automatic validation
- ✅ JSON serialization built-in (`model_dump(mode="json")`)
- ✅ Versioned schemas
- ✅ Atomic file operations

**Weaknesses**:
- ⚠️ `metadata: dict[str, Any]` - unstructured, no schema
- ⚠️ `inputs: dict[str, Any]` in TaskAssignmentMessage - unstructured
- ⚠️ `results: dict[str, Any]` in TaskCompleteMessage - unstructured
- ⚠️ No published JSON Schema (for external tooling/documentation)

### 2. Planning Artifacts (User Stories)

**Location**: `tapps_agents/workflow/planning_artifact.py`

**Current Approach**:
- ✅ **Dataclasses** with `to_dict()` / `from_dict()` methods
- ✅ **Schema versioning** (`schema_version: str = "1.0"`)
- ✅ **Structured UserStory model**
- ✅ **PlanningArtifact container**

**UserStory Structure**:
```python
@dataclass
class UserStory:
    story_id: str
    title: str
    description: str
    epic: str | None = None
    domain: str | None = None
    priority: str = "medium"  # "high", "medium", "low"
    complexity: int = 3  # 1-5 scale
    status: str = "draft"  # "draft", "ready", "in_progress", "completed"
    acceptance_criteria: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    estimated_effort_hours: float | None = None
    risk_level: str | None = None  # "low", "medium", "high"
    dependencies: list[str] = field(default_factory=list)
```

**PlanningArtifact Structure**:
```python
@dataclass
class PlanningArtifact:
    schema_version: str = "1.0"
    timestamp: str
    status: str = "pending"
    worktree_path: str | None = None
    correlation_id: str | None = None
    operation_type: str | None = None
    plan: dict[str, Any] = field(default_factory=dict)  # ⚠️ Unstructured
    user_stories: list[UserStory] = field(default_factory=list)
    total_stories: int = 0
    total_estimated_hours: float | None = None
    high_priority_stories: int = 0
    error: str | None = None
    cancelled: bool = False
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)  # ⚠️ Unstructured
```

**Strengths**:
- ✅ Clear structure for UserStory
- ✅ Versioned schema
- ✅ Serialization methods
- ✅ Rich metadata (priority, complexity, dependencies)

**Weaknesses**:
- ⚠️ **Dataclasses instead of Pydantic** (inconsistent with messaging)
- ⚠️ **No runtime validation** (dataclasses don't validate)
- ⚠️ `plan: dict[str, Any]` - unstructured
- ⚠️ `metadata: dict[str, Any]` - unstructured
- ⚠️ String enums (priority, status, risk_level) - no validation
- ⚠️ Manual serialization (`asdict()` + custom logic)

### 3. Epic Models (Epic Execution)

**Location**: `tapps_agents/epic/models.py`

**Current Approach**:
- ✅ **Dataclasses** with properties
- ✅ **Enum for StoryStatus** (good!)
- ✅ **Structured Story model**
- ✅ **EpicDocument container**

**Story Structure**:
```python
@dataclass
class Story:
    epic_number: int
    story_number: int
    title: str
    description: str
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    story_points: int | None = None
    status: StoryStatus = StoryStatus.NOT_STARTED  # ✅ Enum
    file_path: Path | None = None
```

**EpicDocument Structure**:
```python
@dataclass
class EpicDocument:
    epic_number: int
    title: str
    goal: str
    description: str
    stories: list[Story] = field(default_factory=list)
    priority: str | None = None  # ⚠️ String, not enum
    timeline: str | None = None
    prerequisites: list[str] = field(default_factory=list)
    execution_notes: dict[str, Any] = field(default_factory=dict)  # ⚠️ Unstructured
    definition_of_done: list[str] = field(default_factory=list)
    status: str | None = None  # ⚠️ String, not enum
    file_path: Path | None = None
```

**Strengths**:
- ✅ Enum for StoryStatus (type-safe)
- ✅ Structured AcceptanceCriterion model
- ✅ Rich story metadata (points, dependencies)

**Weaknesses**:
- ⚠️ **Duplication with UserStory** (two different story models)
- ⚠️ **Dataclasses instead of Pydantic** (inconsistent)
- ⚠️ No runtime validation
- ⚠️ `execution_notes: dict[str, Any]` - unstructured
- ⚠️ String fields for priority/status (not enums)
- ⚠️ No JSON serialization methods (only used internally)

### 4. Artifact Schemas (All Types)

**Location**: `tapps_agents/workflow/*_artifact.py`

**Artifact Types**:
- PlanningArtifact
- DesignArtifact
- CodeArtifact
- ReviewArtifact
- TestingArtifact
- QualityArtifact
- OperationsArtifact
- EnhancementArtifact
- DocumentationArtifact
- ContextArtifact

**Current Pattern** (consistent across all):
```python
@dataclass
class XxxArtifact:
    schema_version: str = "1.0"
    timestamp: str
    status: str = "pending"
    worktree_path: str | None = None
    correlation_id: str | None = None
    # ... type-specific fields ...
    metadata: dict[str, Any] = field(default_factory=dict)  # ⚠️ Unstructured
    
    def to_dict(self) -> dict[str, Any]:
        # Manual serialization with asdict()
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> XxxArtifact:
        # Manual deserialization
```

**Strengths**:
- ✅ Consistent pattern across all artifacts
- ✅ Schema versioning
- ✅ Serialization methods
- ✅ Common fields (schema_version, timestamp, status, correlation_id)

**Weaknesses**:
- ⚠️ **All use dataclasses** (inconsistent with messaging)
- ⚠️ **No runtime validation**
- ⚠️ Manual serialization/deserialization
- ⚠️ `metadata: dict[str, Any]` - unstructured everywhere
- ⚠️ String enums for status (not type-safe)
- ⚠️ No published JSON Schema definitions

## Key Issues Identified

### Issue 1: Inconsistent Data Models (Dataclasses vs Pydantic)

**Problem**:
- Messaging uses **Pydantic BaseModel** (modern, validated)
- Artifacts use **dataclasses** (legacy, no validation)

**Impact**:
- Inconsistent patterns across codebase
- Artifacts lack runtime validation
- Harder to evolve schemas
- No automatic JSON Schema generation

**Example**:
```python
# Messaging (Pydantic) ✅
class TaskAssignmentMessage(BaseMessage):
    priority: Literal["low", "medium", "high"] = "medium"  # Validated
    
# Artifact (Dataclass) ⚠️
@dataclass
class PlanningArtifact:
    status: str = "pending"  # No validation, any string accepted
```

### Issue 2: Unstructured Fields (dict[str, Any])

**Problem**:
- Many fields use `dict[str, Any]` (no structure)
- Examples: `metadata`, `plan`, `inputs`, `results`, `execution_notes`

**Impact**:
- No type safety
- No validation
- Hard to document
- Hard to evolve
- Prone to errors

**Affected Fields**:
- `PlanningArtifact.plan: dict[str, Any]`
- `PlanningArtifact.metadata: dict[str, Any]`
- `TaskAssignmentMessage.inputs: dict[str, Any]`
- `TaskCompleteMessage.results: dict[str, Any]`
- `EpicDocument.execution_notes: dict[str, Any]`
- All artifact `metadata: dict[str, Any]`

### Issue 3: String Enums (Not Type-Safe)

**Problem**:
- Many fields use strings instead of Enums
- Examples: `priority`, `status`, `risk_level`, `operation_type`

**Impact**:
- No type safety
- No IDE autocomplete
- Prone to typos
- No validation

**Examples**:
```python
# ⚠️ String (no validation)
priority: str = "medium"  # Could be "MEDIUM", "med", "high", "invalid"

# ✅ Enum (validated)
status: StoryStatus = StoryStatus.NOT_STARTED  # Only valid values
```

### Issue 4: Duplicate Story Models

**Problem**:
- Two different story models:
  - `UserStory` (PlanningArtifact)
  - `Story` (EpicDocument)

**Impact**:
- Confusion about which to use
- Potential data loss when converting
- Maintenance burden (two models to keep in sync)

**Comparison**:
| Field | UserStory | Story |
|-------|-----------|-------|
| ID | `story_id: str` | `epic_number + story_number: int` |
| Status | `status: str` | `status: StoryStatus` (enum) |
| Acceptance Criteria | `list[str]` | `list[AcceptanceCriterion]` (structured) |
| Dependencies | `list[str]` | `list[str]` |
| Points | `estimated_effort_hours: float` | `story_points: int` |

### Issue 5: No Published JSON Schemas

**Problem**:
- No JSON Schema (JSON Schema spec) files published
- Schemas only exist as Python dataclasses/Pydantic models

**Impact**:
- Hard for external tools to validate
- No schema documentation
- No API contract documentation
- Harder integration with other systems

### Issue 6: Manual Serialization

**Problem**:
- Artifacts use manual `to_dict()` / `from_dict()`
- Requires custom logic for nested objects

**Impact**:
- More code to maintain
- Prone to bugs
- No automatic JSON Schema generation
- Inconsistent serialization

**Example**:
```python
# Manual (current) ⚠️
def to_dict(self) -> dict[str, Any]:
    data = asdict(self)
    data["user_stories"] = [asdict(story) for story in self.user_stories]
    return data

# Automatic (Pydantic) ✅
def to_dict(self) -> dict[str, Any]:
    return self.model_dump(mode="json")  # Automatic, handles nesting
```

## Recommendations

### Recommendation 1: Migrate Artifacts to Pydantic (HIGH PRIORITY) ⭐⭐⭐

**Why**:
- Consistency with messaging system
- Runtime validation
- Automatic JSON Schema generation
- Better type safety
- Less boilerplate code

**Implementation**:
1. Convert artifact dataclasses to Pydantic BaseModel
2. Replace `to_dict()` / `from_dict()` with `model_dump()` / `model_validate()`
3. Use Pydantic validators for complex validation
4. Use Pydantic Field for defaults and constraints

**Example Migration**:
```python
# Before (Dataclass) ⚠️
@dataclass
class UserStory:
    story_id: str
    priority: str = "medium"
    status: str = "draft"

# After (Pydantic) ✅
class UserStory(BaseModel):
    story_id: str
    priority: Literal["high", "medium", "low"] = "medium"
    status: Literal["draft", "ready", "in_progress", "completed"] = "draft"
    
    model_config = {"extra": "forbid"}
```

**Benefits**:
- ✅ Runtime validation
- ✅ Type-safe enums
- ✅ Automatic JSON Schema generation
- ✅ Consistent with messaging
- ✅ Less code

**Migration Strategy**:
- Phase 1: Create Pydantic models alongside dataclasses (parallel)
- Phase 2: Update artifact readers/writers to use Pydantic
- Phase 3: Remove dataclass implementations
- Phase 4: Update all consumers

### Recommendation 2: Structure Unstructured Fields (HIGH PRIORITY) ⭐⭐⭐

**Why**:
- Type safety
- Validation
- Documentation
- Better IDE support

**Implementation**:
1. Define structured models for `metadata`, `plan`, `inputs`, `results`
2. Use TypedDict for flexible but typed structures
3. Use Pydantic models for complex structures

**Examples**:

**For `metadata` fields**:
```python
# Define TypedDict for metadata
class ArtifactMetadata(TypedDict, total=False):
    agent_version: str
    execution_context: str
    custom_tags: list[str]
    related_artifacts: list[str]

# Use in artifact
class PlanningArtifact(BaseModel):
    metadata: ArtifactMetadata = Field(default_factory=dict)
```

**For `plan` field**:
```python
class PlanDetails(BaseModel):
    summary: str
    estimated_duration_hours: float | None = None
    key_risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

class PlanningArtifact(BaseModel):
    plan: PlanDetails | None = None  # Structured instead of dict[str, Any]
```

**For `inputs` / `results` in messages**:
```python
class TaskInputs(BaseModel):
    files: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)

class TaskAssignmentMessage(BaseMessage):
    inputs: TaskInputs = Field(default_factory=TaskInputs)
```

**Benefits**:
- ✅ Type safety
- ✅ Validation
- ✅ Documentation
- ✅ IDE autocomplete
- ✅ Easier to evolve

### Recommendation 3: Unify Story Models (MEDIUM PRIORITY) ⭐⭐

**Why**:
- Eliminate confusion
- Single source of truth
- Easier maintenance
- Better interoperability

**Options**:

**Option A: Use PlanningArtifact.UserStory for Everything**
- Pros: Already used in workflows
- Cons: Less structured acceptance criteria

**Option B: Use Epic.Story for Everything**
- Pros: More structured (AcceptanceCriterion model)
- Cons: Tied to Epic concept (epic_number, story_number)

**Option C: Create Unified Story Model**
- Pros: Best of both, cleaner API
- Cons: Migration effort

**Recommended: Option C - Unified Story Model**

```python
class AcceptanceCriterion(BaseModel):
    description: str
    verified: bool = False
    verification_method: str | None = None

class Story(BaseModel):
    # Unified ID system
    story_id: str  # "8.1" or "auth-001" - flexible
    
    # Core fields
    title: str
    description: str
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    
    # Metadata
    epic: str | None = None  # Epic ID or name
    domain: str | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    complexity: int = Field(ge=1, le=5, default=3)
    status: StoryStatus = StoryStatus.NOT_STARTED  # Enum
    story_points: int | None = None
    estimated_effort_hours: float | None = None
    risk_level: Literal["low", "medium", "high"] | None = None
    
    # Dependencies
    dependencies: list[str] = Field(default_factory=list)
    
    # Tasks (optional breakdown)
    tasks: list[str] = Field(default_factory=list)
    
    # File reference (if exists)
    file_path: Path | None = None
```

**Migration Strategy**:
1. Create unified `Story` model
2. Add conversion methods: `UserStory.to_story()`, `Epic.Story.to_story()`
3. Update consumers to use unified model
4. Deprecate old models
5. Remove old models

### Recommendation 4: Replace String Enums with Type-Safe Enums (MEDIUM PRIORITY) ⭐⭐

**Why**:
- Type safety
- IDE autocomplete
- Validation
- Prevents typos

**Implementation**:
```python
# Define enums
class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ArtifactStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Use in models
class UserStory(BaseModel):
    priority: Priority = Priority.MEDIUM
    risk_level: RiskLevel | None = None

class PlanningArtifact(BaseModel):
    status: ArtifactStatus = ArtifactStatus.PENDING
```

**Benefits**:
- ✅ Type safety
- ✅ IDE autocomplete
- ✅ Validation (only valid values)
- ✅ Self-documenting

### Recommendation 5: Publish JSON Schema Definitions (LOW PRIORITY) ⭐

**Why**:
- External tooling support
- API documentation
- Contract validation
- Integration with other systems

**Implementation**:
1. Use Pydantic's `model_json_schema()` to generate JSON Schema
2. Export schemas to `schemas/` directory
3. Version schemas (schemas/v1.0/, schemas/v2.0/)
4. Generate documentation from schemas

**Example**:
```python
# Generate JSON Schema
schema = PlanningArtifact.model_json_schema()

# Export to file
schema_path = Path("schemas/v1.0/planning-artifact.schema.json")
schema_path.write_text(json.dumps(schema, indent=2))
```

**Benefits**:
- ✅ External validation tools
- ✅ API documentation
- ✅ Contract testing
- ✅ Integration support

### Recommendation 6: Standardize on Pydantic Throughout (HIGH PRIORITY) ⭐⭐⭐

**Why**:
- Consistency
- Better tooling
- Less code
- Better validation

**Action Items**:
1. ✅ Migrate artifacts to Pydantic (Rec 1)
2. ✅ Structure unstructured fields (Rec 2)
3. ✅ Use Enums instead of strings (Rec 4)
4. ✅ Unify story models (Rec 3)
5. ⭐ Publish JSON schemas (Rec 5)

## Migration Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create Pydantic versions of artifact models (parallel to dataclasses)
- [ ] Define structured models for metadata, plan, inputs, results
- [ ] Create unified Story model
- [ ] Define Enums for priority, status, risk_level

### Phase 2: Migration (Week 3-4)
- [ ] Update artifact_helper.py to use Pydantic models
- [ ] Update artifact readers/writers
- [ ] Update workflow executor to use Pydantic artifacts
- [ ] Add conversion utilities (dataclass → Pydantic)

### Phase 3: Validation (Week 5)
- [ ] Add comprehensive tests
- [ ] Validate backward compatibility
- [ ] Update documentation
- [ ] Test with real workflows

### Phase 4: Cleanup (Week 6)
- [ ] Remove dataclass implementations
- [ ] Remove manual serialization code
- [ ] Update all consumers
- [ ] Publish JSON schemas

### Phase 5: Enhancement (Week 7+)
- [ ] Add JSON Schema generation
- [ ] Create schema documentation
- [ ] Add schema validation tools
- [ ] Create migration guides

## Priority Summary

| Recommendation | Priority | Impact | Effort |
|---------------|----------|--------|--------|
| Migrate to Pydantic | ⭐⭐⭐ HIGH | Very High | Medium |
| Structure unstructured fields | ⭐⭐⭐ HIGH | High | Medium |
| Unify story models | ⭐⭐ MEDIUM | Medium | High |
| Replace string enums | ⭐⭐ MEDIUM | Medium | Low |
| Publish JSON schemas | ⭐ LOW | Low | Low |

## Conclusion

TappsCodingAgents has a solid foundation with versioned schemas and serialization, but there are clear opportunities for improvement:

1. **Inconsistency**: Dataclasses vs Pydantic (messaging uses Pydantic, artifacts use dataclasses)
2. **Type Safety**: Unstructured `dict[str, Any]` fields and string enums
3. **Duplication**: Two different story models
4. **Validation**: No runtime validation for artifacts
5. **Documentation**: No published JSON Schema definitions

**Recommended Next Steps**:
1. Start with **Recommendation 1** (Migrate to Pydantic) - highest impact
2. Follow with **Recommendation 2** (Structure unstructured fields) - high impact
3. Then **Recommendation 3** (Unify story models) - medium impact
4. Finally **Recommendation 4** (Replace string enums) - medium impact, low effort

These improvements will result in:
- ✅ More consistent codebase
- ✅ Better type safety
- ✅ Runtime validation
- ✅ Automatic JSON Schema generation
- ✅ Easier maintenance
- ✅ Better developer experience
