# Step 3: Architecture Design - JSON Agent-to-Agent Communication

**Generated**: 2025-01-16  
**Workflow**: Build - JSON Agent-to-Agent Communication Implementation  
**Agent**: @architect  
**Stage**: System Architecture Design

---

## Architecture Overview

### Design Pattern: Hybrid JSON/Markdown with Two-Way Conversion

The architecture implements a **dual-format system** where:
- **JSON is the primary format** for agent-to-agent communication (reliable, parseable, structured)
- **Markdown is generated** for human consumption (readable, git-friendly, documentation)

This hybrid approach provides:
- ✅ **Reliable parsing** for agents (JSON eliminates regex fragility)
- ✅ **Human readability** for documentation and git diffs
- ✅ **Backward compatibility** during migration
- ✅ **Lossless conversion** between formats

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Agent Execution Layer                      │
│  (Analyst, Planner, Architect, Designer, Implementer, etc.) │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Outputs JSON (primary format)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    JSON Schema Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Requirements │  │ User Stories │  │  Architecture│     │
│  │   Schema     │  │    Schema    │  │    Schema    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Design     │  │   Review     │  │    Test      │     │
│  │   Schema     │  │   Schema     │  │    Schema    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│              (Pydantic Models with Validation)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Validated JSON
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Converter Layer                            │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │ Markdown → JSON  │◄───────┤  JSON → Markdown │          │
│  │    Converter     │        │    Generator     │          │
│  └──────────────────┘        └──────────────────┘          │
│                  (Bidirectional Conversion)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐        ┌──────────────────┐
│ Agent Workflow│        │ Human Interface  │
│   Handlers    │        │   (Markdown)     │
│  (Consume JSON)│        │  (Documentation) │
└───────────────┘        └──────────────────┘
```

---

## Component Details

### 1. JSON Schema Layer

**Location**: `tapps_agents/schemas/`

**Purpose**: Define type-safe, validated JSON schemas for all agent outputs using Pydantic models.

**Components**:

#### 1.1 Base Schema Models
```python
# tapps_agents/schemas/base.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaseAgentOutput(BaseModel):
    """Base schema for all agent outputs."""
    status: str  # "complete", "in_progress", "failed"
    timestamp: datetime
    agent: str
    correlation_id: Optional[str] = None
    passes: Optional[bool] = None  # Status tracking (Ralph-style)
    completed: Optional[bool] = None
```

#### 1.2 Agent-Specific Schemas
- **`requirements_schema.py`**: Requirements output (functional, non-functional, constraints, assumptions)
- **`story_schema.py`**: User stories (id, title, description, acceptance criteria, dependencies, status)
- **`architecture_schema.py`**: Architecture designs (components, data flow, patterns, performance)
- **`design_schema.py`**: Component designs (API specs, data models, specifications)
- **`review_schema.py`**: Code reviews (scores, issues, recommendations)
- **`test_schema.py`**: Test results (test plans, test cases, validation criteria)
- **`enhancement_schema.py`**: Enhanced prompts (all 7 stages)

**Key Features**:
- Pydantic models for type safety and validation
- JSON Schema generation for documentation
- Status tracking fields (passes, completed, status)
- Optional fields for backward compatibility

---

### 2. Converter Layer

**Location**: `tapps_agents/converters/`

**Purpose**: Bidirectional conversion between Markdown and JSON formats.

#### 2.1 Markdown to JSON Converter
**File**: `tapps_agents/converters/markdown_to_json.py`

**Components**:
- **MarkdownParser**: Parses markdown artifacts into structured data
- **SchemaMapper**: Maps parsed data to JSON schemas
- **Validator**: Validates JSON output against schemas

**Implementation Strategy**:
1. Parse markdown using markdown parser (markdown-it-py or similar)
2. Extract structured data (headers, lists, tables, code blocks)
3. Map to JSON schema structure
4. Validate against Pydantic models
5. Return validated JSON

**Edge Cases Handled**:
- Malformed markdown (missing sections, invalid structure)
- Nested structures (lists within lists, tables)
- Code blocks (preserve formatting)
- Missing optional fields (default values)

#### 2.2 JSON to Markdown Generator
**File**: `tapps_agents/converters/json_to_markdown.py`

**Components**:
- **MarkdownRenderer**: Generates markdown from JSON schemas
- **Formatter**: Formats tables, lists, code blocks
- **TemplateEngine**: Uses templates for consistent formatting

**Implementation Strategy**:
1. Load JSON schema data
2. Generate markdown sections (headers, lists, tables)
3. Format code blocks with syntax highlighting
4. Apply templates for consistency
5. Return formatted markdown

**Features**:
- Human-readable formatting
- Git-friendly output (proper line breaks, spacing)
- Preserves structure (hierarchy, relationships)
- Round-trip compatible (JSON → Markdown → JSON preserves data)

---

### 3. Agent Output Layer

**Location**: `tapps_agents/agents/*/agent.py`

**Purpose**: Update all agents to output JSON as primary format.

#### 3.1 Agent Output Pattern

**Before (Markdown)**:
```python
# Agent outputs markdown string
result = await self._gather_requirements(description)
return result  # Markdown string
```

**After (JSON)**:
```python
# Agent outputs JSON schema
result = await self._gather_requirements(description)
schema = RequirementsOutput(
    status="complete",
    timestamp=datetime.now(),
    agent="analyst",
    functional_requirements=result["functional"],
    non_functional_requirements=result["non_functional"],
    # ... other fields
)
return schema.model_dump_json()  # JSON string
```

#### 3.2 Backward Compatibility

Agents maintain backward compatibility:
- **JSON output** (primary): For agent-to-agent communication
- **Markdown output** (optional): For human consumption (generated from JSON)

**CLI Support**:
```bash
# JSON output (default for agents)
tapps-agents analyst gather-requirements "..." --format json

# Markdown output (for humans)
tapps-agents analyst gather-requirements "..." --format markdown
```

---

### 4. Workflow Handler Updates

**Location**: `tapps_agents/workflow/`

**Purpose**: Update workflow handlers to consume JSON artifacts.

#### 4.1 Artifact System Integration

**Current State**:
- Artifact system already uses JSON (see `artifact_helper.py`)
- Agents output markdown (needs updating)
- Workflow handlers expect markdown (needs updating)

**Target State**:
- Agents output JSON (primary)
- Workflow handlers consume JSON directly
- Markdown generated for documentation

#### 4.2 Workflow Handler Pattern

**Before**:
```python
# Handler parses markdown
result = await agent.run(...)
# Parse markdown to extract data
data = parse_markdown(result)
```

**After**:
```python
# Handler consumes JSON directly
result = await agent.run(...)
# Parse JSON to schema
schema = RequirementsOutput.model_validate_json(result)
# Use schema directly (type-safe)
requirements = schema.functional_requirements
```

---

### 5. Epic Parser Enhancement

**Location**: `tapps_agents/epic/parser.py`

**Purpose**: Replace 415 lines of regex with JSON parsing.

#### 5.1 Current Implementation (Regex-based)

**Problems**:
- 415 lines of fragile regex patterns
- Error-prone parsing
- Difficult to maintain
- No status tracking

#### 5.2 New Implementation (JSON-based)

**Approach**:
1. **Epic JSON Schema**: Define EpicDocument schema (EpicDocument, Story, AcceptanceCriterion)
2. **JSON Parser**: Use native Python `json` library (reliable, fast)
3. **Status Tracking**: Add passes/completed fields to schema
4. **Backward Compatibility**: Support markdown epics via converter

**Code Reduction**:
- **Before**: 415 lines of regex
- **After**: ~50-100 lines of JSON parsing + schema validation
- **Reduction**: ~75% code reduction

**Performance**:
- JSON parsing is faster than regex (native Python implementation)
- Schema validation provides type safety

---

## Data Flow

### Agent-to-Agent Communication Flow

```
Agent A (Analyst)
    │
    │ Outputs JSON (RequirementsOutput schema)
    ▼
Workflow Handler
    │
    │ Validates JSON against schema
    │ Extracts structured data (type-safe)
    ▼
Agent B (Planner)
    │
    │ Consumes JSON directly
    │ Outputs JSON (StoryOutput schema)
    ▼
Workflow Handler
    │
    │ Continues workflow...
```

### Human Interface Flow

```
Agent Output (JSON)
    │
    │ JSON → Markdown Generator
    ▼
Markdown Documentation
    │
    │ Saved to docs/workflows/...
    │ Human-readable, git-friendly
```

---

## Integration Points

### Files to Modify

1. **Schema Definitions**:
   - `tapps_agents/schemas/` (new directory)
   - Create base schemas and agent-specific schemas

2. **Converters**:
   - `tapps_agents/converters/` (new directory)
   - `markdown_to_json.py`
   - `json_to_markdown.py`

3. **Agent Updates**:
   - `tapps_agents/agents/analyst/agent.py`
   - `tapps_agents/agents/planner/agent.py`
   - `tapps_agents/agents/architect/agent.py`
   - `tapps_agents/agents/designer/agent.py`
   - `tapps_agents/agents/reviewer/agent.py`
   - `tapps_agents/agents/tester/agent.py`
   - `tapps_agents/agents/enhancer/agent.py`

4. **Workflow Handlers**:
   - `tapps_agents/workflow/agent_handlers/` (update all handlers)
   - `tapps_agents/workflow/artifact_helper.py` (already JSON, verify compatibility)

5. **Epic Parser**:
   - `tapps_agents/epic/parser.py` (refactor to JSON)
   - `tapps_agents/epic/models.py` (update models for JSON)

6. **Simple Mode Orchestrators**:
   - `tapps_agents/simple_mode/orchestrators/` (update to consume JSON)

---

## Technology Stack

### Core Libraries

- **Pydantic** (v2.x): JSON schema validation and type safety
  - Models for all agent outputs
  - JSON Schema generation
  - Validation and error handling

- **Python `json`**: Native JSON parsing (replacing regex)
  - Fast, reliable parsing
  - Built-in error handling
  - No external dependencies

- **Markdown Libraries** (optional):
  - **markdown-it-py**: Markdown parsing for converter
  - **markdown**: Markdown generation for documentation
  - Only needed for converter layer

### Dependencies

```python
# Required
pydantic>=2.0.0  # Schema validation

# Optional (for converters)
markdown-it-py>=3.0.0  # Markdown parsing
markdown>=3.4.0  # Markdown generation
```

---

## Performance Considerations

### JSON Parsing vs Regex

**Expected Performance**:
- JSON parsing: ~10-50ms per artifact (native Python)
- Regex parsing: ~50-200ms per artifact (complex patterns)
- **Improvement**: 2-4x faster with JSON

**Benchmarking**:
- Benchmark EpicParser before/after (415 lines regex vs JSON)
- Measure artifact conversion time
- Monitor workflow execution time

### Memory Considerations

- JSON schemas are lightweight (Pydantic models)
- Converter layer processes artifacts in-memory (acceptable for workflow artifacts)
- No streaming needed (artifacts are small to medium size)

---

## Security Considerations

### JSON Schema Validation

- Pydantic models prevent injection attacks
- Schema validation ensures data integrity
- Type safety prevents type confusion vulnerabilities

### File I/O

- UTF-8 encoding for all file operations (Windows compatibility)
- Path validation to prevent directory traversal
- Safe exception handling (Unicode encoding errors)

---

## Migration Strategy

### Phase 1: Schema Definition (Week 1)
- Create all JSON schemas
- Add schema validation
- Unit tests for schemas

### Phase 2: Converter Implementation (Week 2)
- Implement Markdown → JSON converter
- Implement JSON → Markdown generator
- Comprehensive tests

### Phase 3: Agent Updates (Week 3-4)
- Update agents to output JSON
- Maintain backward compatibility (markdown generation)
- Update workflow handlers

### Phase 4: Epic Parser Refactor (Week 4)
- Replace regex with JSON parsing
- Add status tracking
- Performance benchmarks

### Phase 5: Testing & Migration (Week 5)
- Comprehensive testing
- Migration tools for existing artifacts
- Documentation updates

---

## Testing Strategy

### Unit Tests
- Schema validation (all schemas)
- Converter accuracy (round-trip conversion)
- Agent JSON output (all agents)
- Epic parser (JSON parsing)

### Integration Tests
- End-to-end workflow with JSON
- Agent-to-agent communication
- Workflow handler integration
- Epic orchestrator with JSON

### Performance Tests
- JSON parsing benchmarks
- Converter performance
- Workflow execution time comparison

### Migration Tests
- Convert existing markdown artifacts
- Verify data preservation
- Test backward compatibility

---

## Success Criteria

### Functional Requirements
- ✅ All agents output JSON as primary format
- ✅ All workflow handlers consume JSON
- ✅ Epic parser uses JSON (no regex)
- ✅ Bidirectional conversion (Markdown ↔ JSON)
- ✅ Status tracking enabled (passes/completed fields)

### Non-Functional Requirements
- ✅ JSON parsing faster than regex (2-4x improvement)
- ✅ 100% data preservation (lossless conversion)
- ✅ Code reduction (75% reduction in EpicParser)
- ✅ Test coverage ≥ 80%
- ✅ Code quality score ≥ 75

---

## Next Steps

Proceed to Step 4 (Component Design) to create detailed JSON schemas and converter specifications.
