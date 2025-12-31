# Step 3: Architecture Design - Automatic Documentation Updates for Framework Changes

## System Architecture

### Overview

The automatic documentation update system integrates into the existing build workflow to detect framework changes and update project documentation automatically. The system consists of four main components:

1. **Framework Change Detector** - Detects when new agents are created
2. **Documentation Updater** - Updates project documentation files
3. **Documentation Validator** - Validates documentation completeness
4. **Build Orchestrator Integration** - Integrates into build workflow

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Build Orchestrator                        │
│  (tapps_agents/simple_mode/orchestrators/                   │
│   build_orchestrator.py)                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Step 5: Implementation
                       │ (creates agent code)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│           Framework Change Detector                          │
│  (tapps_agents/simple_mode/                                 │
│   framework_change_detector.py)                             │
│                                                              │
│  - scan_agent_directories()                                 │
│  - detect_cli_registration()                                │
│  - detect_skill_creation()                                 │
│  - compare_with_known_state()                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Detected Changes
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Documentation Updater                           │
│  (tapps_agents/agents/documenter/                           │
│   framework_doc_updater.py)                                 │
│                                                              │
│  - update_readme()                                          │
│  - update_api_docs()                                        │
│  - update_architecture_docs()                              │
│  - update_agent_capabilities()                              │
│  - create_backup()                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Updates Complete
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            Documentation Validator                          │
│  (tapps_agents/agents/documenter/                           │
│   doc_validator.py)                                         │
│                                                              │
│  - validate_readme()                                       │
│  - validate_api_docs()                                     │
│  - validate_architecture_docs()                            │
│  - validate_agent_capabilities()                            │
│  - check_consistency()                                      │
│  - generate_report()                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Validation Report
                       ↓
                   Workflow Complete
```

### Component Details

#### 1. Framework Change Detector

**Location:** `tapps_agents/simple_mode/framework_change_detector.py`

**Responsibilities:**
- Scan `tapps_agents/agents/` directory for new agent directories
- Parse `tapps_agents/cli/main.py` for new agent registrations
- Check `tapps_agents/resources/claude/skills/` for new skill files
- Compare current state with known state (from config or previous scan)
- Return structured change information

**Key Methods:**
```python
class FrameworkChangeDetector:
    def detect_changes(
        self, 
        project_root: Path
    ) -> FrameworkChanges:
        """Detect framework changes since last check."""
        
    def scan_agent_directories(
        self, 
        agents_dir: Path
    ) -> list[str]:
        """Scan for agent directories."""
        
    def detect_cli_registration(
        self, 
        cli_file: Path, 
        agent_name: str
    ) -> bool:
        """Check if agent is registered in CLI."""
        
    def detect_skill_creation(
        self, 
        skills_dir: Path, 
        agent_name: str
    ) -> bool:
        """Check if agent skill file exists."""
```

**Data Structures:**
```python
@dataclass
class FrameworkChanges:
    new_agents: list[str]
    modified_agents: list[str]
    new_cli_commands: list[str]
    timestamp: datetime
```

#### 2. Documentation Updater

**Location:** `tapps_agents/agents/documenter/framework_doc_updater.py`

**Responsibilities:**
- Update README.md with new agent information
- Update API.md with agent API documentation
- Update ARCHITECTURE.md with agent details
- Update agent-capabilities.mdc with agent section
- Create backups before updates
- Use templates for consistent formatting

**Key Methods:**
```python
class FrameworkDocUpdater:
    def update_all_docs(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        project_root: Path
    ) -> UpdateResult:
        """Update all project documentation."""
        
    def update_readme(
        self,
        readme_path: Path,
        agent_name: str,
        agent_info: AgentInfo
    ) -> bool:
        """Update README.md with new agent."""
        
    def update_api_docs(
        self,
        api_path: Path,
        agent_name: str,
        agent_info: AgentInfo
    ) -> bool:
        """Update API.md with agent documentation."""
        
    def update_architecture_docs(
        self,
        arch_path: Path,
        agent_name: str,
        agent_info: AgentInfo
    ) -> bool:
        """Update ARCHITECTURE.md with agent details."""
        
    def update_agent_capabilities(
        self,
        capabilities_path: Path,
        agent_name: str,
        agent_info: AgentInfo
    ) -> bool:
        """Update agent-capabilities.mdc with agent section."""
        
    def create_backup(
        self,
        file_path: Path
    ) -> Path:
        """Create backup of file before update."""
```

**Data Structures:**
```python
@dataclass
class AgentInfo:
    name: str
    purpose: str
    commands: list[str]
    description: str | None = None
    examples: list[str] | None = None

@dataclass
class UpdateResult:
    readme_updated: bool
    api_updated: bool
    architecture_updated: bool
    capabilities_updated: bool
    backups_created: list[Path]
    errors: list[str]
```

#### 3. Documentation Validator

**Location:** `tapps_agents/agents/documenter/doc_validator.py`

**Responsibilities:**
- Validate README.md mentions new agent
- Validate API.md documents new agent
- Validate ARCHITECTURE.md includes new agent
- Validate agent-capabilities.mdc has agent section
- Check agent count consistency across all docs
- Generate validation report

**Key Methods:**
```python
class DocValidator:
    def validate_completeness(
        self,
        agent_name: str,
        project_root: Path
    ) -> ValidationResult:
        """Validate all documentation is complete."""
        
    def validate_readme(
        self,
        readme_path: Path,
        agent_name: str
    ) -> bool:
        """Check README.md mentions agent."""
        
    def validate_api_docs(
        self,
        api_path: Path,
        agent_name: str
    ) -> bool:
        """Check API.md documents agent."""
        
    def validate_architecture_docs(
        self,
        arch_path: Path,
        agent_name: str
    ) -> bool:
        """Check ARCHITECTURE.md includes agent."""
        
    def validate_agent_capabilities(
        self,
        capabilities_path: Path,
        agent_name: str
    ) -> bool:
        """Check agent-capabilities.mdc has agent section."""
        
    def check_consistency(
        self,
        project_root: Path
    ) -> ConsistencyResult:
        """Check agent count consistency across docs."""
        
    def generate_report(
        self,
        validation_result: ValidationResult
    ) -> str:
        """Generate validation report."""
```

**Data Structures:**
```python
@dataclass
class ValidationResult:
    readme_valid: bool
    api_valid: bool
    architecture_valid: bool
    capabilities_valid: bool
    consistency_valid: bool
    agent_count: dict[str, int]  # doc_name -> count
    errors: list[str]
    warnings: list[str]

@dataclass
class ConsistencyResult:
    is_consistent: bool
    counts: dict[str, int]
    discrepancies: list[str]
```

#### 4. Build Orchestrator Integration

**Location:** `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Changes:**
- Add `documenter` to agent sequence
- Add framework change detection after implementation step
- Call documentation updater if framework changes detected
- Run validation after updates
- Handle validation failures gracefully

**Modified Methods:**
```python
class BuildOrchestrator:
    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for build workflow."""
        return [
            "enhancer",
            "planner",
            "architect",
            "designer",
            "implementer",
            "reviewer",  # If enabled
            "tester",    # If enabled
            "documenter"  # NEW: Add documentation step
        ]
    
    async def _execute_documenter_step(
        self,
        workflow_id: str,
        project_root: Path
    ) -> dict[str, Any]:
        """Execute documenter step for framework changes."""
        # 1. Detect framework changes
        # 2. Update documentation if changes detected
        # 3. Validate documentation
        # 4. Return results
```

### Data Flow

```
1. Build Workflow Executes
   ↓
2. Step 5: Implementation creates agent code
   ↓
3. Framework Change Detector scans for changes
   ↓
4. If changes detected:
   ├─→ Documentation Updater updates all docs
   │   ├─→ Update README.md
   │   ├─→ Update API.md
   │   ├─→ Update ARCHITECTURE.md
   │   └─→ Update agent-capabilities.mdc
   ↓
5. Documentation Validator validates updates
   ├─→ Check all docs mention agent
   ├─→ Check agent count consistency
   └─→ Generate validation report
   ↓
6. If validation fails:
   ├─→ Log warnings/errors
   └─→ Optionally fail workflow
   ↓
7. Workflow Complete
```

### File Update Patterns

#### README.md Update Pattern
```markdown
### Workflow Agents (14)  ← Update count

- `@reviewer` - Code review
- `@implementer` - Code generation
...
- `@evaluator` - Workflow evaluation  ← Insert new agent
```

#### API.md Update Pattern
```markdown
## Agent subcommands:

- `reviewer` - Code review commands
- `implementer` - Code generation commands
...
- `evaluator` - Workflow evaluation commands  ← Insert new agent

## Evaluator Agent  ← Add new section

### Commands

- `evaluate` - Evaluate workflow execution
...
```

#### ARCHITECTURE.md Update Pattern
```markdown
## Agents

- **Reviewer Agent** - Code quality analysis
- **Implementer Agent** - Code generation
...
- **Evaluator Agent** - Workflow evaluation  ← Insert new agent
```

#### agent-capabilities.mdc Update Pattern
```markdown
### Reviewer Agent

**Purpose**: Code review...

### Evaluator Agent  ← Insert new section

**Purpose**: Workflow evaluation...

**Commands**:
- `*evaluate` - Evaluate workflow execution
...
```

### Error Handling

1. **File Not Found**: Log warning, skip update for that file
2. **Parse Error**: Log error, create backup, attempt recovery
3. **Write Error**: Log error, restore backup if available
4. **Validation Failure**: Log errors, optionally fail workflow

### Performance Considerations

1. **Change Detection**: Use directory listing cache, only scan when needed
2. **File Updates**: Use efficient file operations, minimize I/O
3. **Validation**: Use regex patterns for fast checks, avoid full file parsing
4. **Backups**: Create backups only when updates are needed

### Security Considerations

1. **Path Validation**: Validate all file paths to prevent directory traversal
2. **Backup Location**: Store backups in safe location (`.tapps-agents/backups/`)
3. **File Permissions**: Preserve file permissions when creating backups
4. **Input Validation**: Validate agent names and metadata before updates

### Testing Strategy

1. **Unit Tests**: Test each component independently
2. **Integration Tests**: Test full workflow with mock agent creation
3. **Edge Cases**: Test with missing files, malformed docs, etc.
4. **Windows Compatibility**: Test on Windows environment
