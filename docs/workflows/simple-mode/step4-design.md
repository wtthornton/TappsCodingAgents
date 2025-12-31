# Step 4: Component Design - Automatic Documentation Updates for Framework Changes

## API Specifications

### 1. Framework Change Detector API

#### Class: `FrameworkChangeDetector`

**Location:** `tapps_agents/simple_mode/framework_change_detector.py`

**Purpose:** Detect framework changes (new agents, modified agents, new CLI commands)

**Methods:**

```python
class FrameworkChangeDetector:
    def __init__(self, project_root: Path):
        """
        Initialize framework change detector.
        
        Args:
            project_root: Project root directory
        """
        
    def detect_changes(
        self,
        known_agents: set[str] | None = None
    ) -> FrameworkChanges:
        """
        Detect framework changes since last check.
        
        Args:
            known_agents: Set of known agent names (from config or previous scan)
                         If None, will scan and return all current agents
        
        Returns:
            FrameworkChanges object with detected changes
        """
        
    def scan_agent_directories(
        self,
        agents_dir: Path | None = None
    ) -> list[str]:
        """
        Scan for agent directories in tapps_agents/agents/.
        
        Args:
            agents_dir: Agents directory path (default: project_root/tapps_agents/agents)
        
        Returns:
            List of agent names (directory names)
        """
        
    def detect_cli_registration(
        self,
        agent_name: str,
        cli_file: Path | None = None
    ) -> bool:
        """
        Check if agent is registered in CLI.
        
        Args:
            agent_name: Agent name to check
            cli_file: CLI main file path (default: project_root/tapps_agents/cli/main.py)
        
        Returns:
            True if agent is registered in CLI
        """
        
    def detect_skill_creation(
        self,
        agent_name: str,
        skills_dir: Path | None = None
    ) -> bool:
        """
        Check if agent skill file exists.
        
        Args:
            agent_name: Agent name to check
            skills_dir: Skills directory path (default: project_root/tapps_agents/resources/claude/skills)
        
        Returns:
            True if agent skill file exists
        """
        
    def get_agent_info(
        self,
        agent_name: str
    ) -> AgentInfo | None:
        """
        Extract agent information from agent directory.
        
        Args:
            agent_name: Agent name
        
        Returns:
            AgentInfo object with agent metadata, or None if not found
        """
```

**Data Structures:**

```python
@dataclass
class FrameworkChanges:
    """Detected framework changes."""
    new_agents: list[str]
    modified_agents: list[str]
    new_cli_commands: list[str]
    timestamp: datetime
    agent_info: dict[str, AgentInfo]  # agent_name -> AgentInfo

@dataclass
class AgentInfo:
    """Agent metadata extracted from code."""
    name: str
    purpose: str | None = None
    commands: list[str] = field(default_factory=list)
    description: str | None = None
    examples: list[str] = field(default_factory=list)
    
    @classmethod
    def from_agent_directory(
        cls,
        agent_dir: Path
    ) -> AgentInfo:
        """Extract agent info from agent directory."""
        # Parse agent.py for docstring (purpose)
        # Parse SKILL.md for commands
        # Extract examples if available
```

---

### 2. Documentation Updater API

#### Class: `FrameworkDocUpdater`

**Location:** `tapps_agents/agents/documenter/framework_doc_updater.py`

**Purpose:** Update project documentation files with new agent information

**Methods:**

```python
class FrameworkDocUpdater:
    def __init__(
        self,
        project_root: Path,
        create_backups: bool = True
    ):
        """
        Initialize documentation updater.
        
        Args:
            project_root: Project root directory
            create_backups: Whether to create backups before updates
        """
        
    def update_all_docs(
        self,
        agent_name: str,
        agent_info: AgentInfo
    ) -> UpdateResult:
        """
        Update all project documentation for a new agent.
        
        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
        
        Returns:
            UpdateResult with update status for each file
        """
        
    def update_readme(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        readme_path: Path | None = None
    ) -> bool:
        """
        Update README.md with new agent.
        
        Updates:
        - Agent count: Increment from (N) to (N+1)
        - Agent list: Add agent to list in alphabetical order
        
        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            readme_path: README.md path (default: project_root/README.md)
        
        Returns:
            True if update successful
        """
        
    def update_api_docs(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        api_path: Path | None = None
    ) -> bool:
        """
        Update API.md with agent documentation.
        
        Updates:
        - Subcommands list: Add agent to subcommands
        - API section: Add agent API documentation section
        
        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            api_path: API.md path (default: project_root/docs/API.md)
        
        Returns:
            True if update successful
        """
        
    def update_architecture_docs(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        arch_path: Path | None = None
    ) -> bool:
        """
        Update ARCHITECTURE.md with agent details.
        
        Updates:
        - Agent list: Add agent to agent list
        - Agent details: Add agent purpose and relationships
        
        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            arch_path: ARCHITECTURE.md path (default: project_root/docs/ARCHITECTURE.md)
        
        Returns:
            True if update successful
        """
        
    def update_agent_capabilities(
        self,
        agent_name: str,
        agent_info: AgentInfo,
        capabilities_path: Path | None = None
    ) -> bool:
        """
        Update agent-capabilities.mdc with agent section.
        
        Updates:
        - Agent section: Add agent section with purpose and commands
        
        Args:
            agent_name: Name of the new agent
            agent_info: Agent information
            capabilities_path: agent-capabilities.mdc path (default: project_root/.cursor/rules/agent-capabilities.mdc)
        
        Returns:
            True if update successful
        """
        
    def create_backup(
        self,
        file_path: Path
    ) -> Path | None:
        """
        Create backup of file before update.
        
        Args:
            file_path: File to backup
        
        Returns:
            Backup file path, or None if backup failed
        """
```

**Data Structures:**

```python
@dataclass
class UpdateResult:
    """Result of documentation updates."""
    readme_updated: bool
    api_updated: bool
    architecture_updated: bool
    capabilities_updated: bool
    backups_created: list[Path]
    errors: list[str]
    warnings: list[str]
    
    @property
    def success(self) -> bool:
        """Check if all updates were successful."""
        return (
            self.readme_updated and
            self.api_updated and
            self.architecture_updated and
            self.capabilities_updated and
            not self.errors
        )
```

**Update Patterns:**

#### README.md Update Pattern
```python
# Pattern: Update agent count
# Before: "- **Workflow Agents** (14):"
# After:  "- **Workflow Agents** (15):"

# Pattern: Add agent to list
# Insert after last agent in alphabetical order
# Format: "- `@{agent_name}` - {purpose}"
```

#### API.md Update Pattern
```python
# Pattern: Add to subcommands list
# Section: "## Agent subcommands:"
# Format: "- `{agent_name}` - {purpose}"

# Pattern: Add API section
# Insert after last agent section
# Format:
# "## {AgentName} Agent
# 
# ### Commands
# - `{command}` - {description}
# ..."
```

#### ARCHITECTURE.md Update Pattern
```python
# Pattern: Add to agent list
# Section: "## Agents"
# Format: "- **{AgentName} Agent** - {purpose}"
```

#### agent-capabilities.mdc Update Pattern
```python
# Pattern: Add agent section
# Insert after last agent section
# Format:
# "### {AgentName} Agent
# 
# **Purpose**: {purpose}
# 
# **Commands**:
# - `*{command}` - {description}
# ..."
```

---

### 3. Documentation Validator API

#### Class: `DocValidator`

**Location:** `tapps_agents/agents/documenter/doc_validator.py`

**Purpose:** Validate documentation completeness and consistency

**Methods:**

```python
class DocValidator:
    def __init__(self, project_root: Path):
        """
        Initialize documentation validator.
        
        Args:
            project_root: Project root directory
        """
        
    def validate_completeness(
        self,
        agent_name: str
    ) -> ValidationResult:
        """
        Validate all documentation is complete for an agent.
        
        Args:
            agent_name: Agent name to validate
        
        Returns:
            ValidationResult with validation status
        """
        
    def validate_readme(
        self,
        agent_name: str,
        readme_path: Path | None = None
    ) -> bool:
        """
        Check README.md mentions agent.
        
        Args:
            agent_name: Agent name to check
            readme_path: README.md path (default: project_root/README.md)
        
        Returns:
            True if agent is mentioned in README.md
        """
        
    def validate_api_docs(
        self,
        agent_name: str,
        api_path: Path | None = None
    ) -> bool:
        """
        Check API.md documents agent.
        
        Args:
            agent_name: Agent name to check
            api_path: API.md path (default: project_root/docs/API.md)
        
        Returns:
            True if agent is documented in API.md
        """
        
    def validate_architecture_docs(
        self,
        agent_name: str,
        arch_path: Path | None = None
    ) -> bool:
        """
        Check ARCHITECTURE.md includes agent.
        
        Args:
            agent_name: Agent name to check
            arch_path: ARCHITECTURE.md path (default: project_root/docs/ARCHITECTURE.md)
        
        Returns:
            True if agent is included in ARCHITECTURE.md
        """
        
    def validate_agent_capabilities(
        self,
        agent_name: str,
        capabilities_path: Path | None = None
    ) -> bool:
        """
        Check agent-capabilities.mdc has agent section.
        
        Args:
            agent_name: Agent name to check
            capabilities_path: agent-capabilities.mdc path (default: project_root/.cursor/rules/agent-capabilities.mdc)
        
        Returns:
            True if agent section exists in agent-capabilities.mdc
        """
        
    def check_consistency(
        self
    ) -> ConsistencyResult:
        """
        Check agent count consistency across all documentation.
        
        Returns:
            ConsistencyResult with consistency status
        """
        
    def generate_report(
        self,
        validation_result: ValidationResult
    ) -> str:
        """
        Generate validation report.
        
        Args:
            validation_result: Validation result to report
        
        Returns:
            Formatted validation report string
        """
```

**Data Structures:**

```python
@dataclass
class ValidationResult:
    """Documentation validation result."""
    readme_valid: bool
    api_valid: bool
    architecture_valid: bool
    capabilities_valid: bool
    consistency_valid: bool
    agent_count: dict[str, int]  # doc_name -> count
    errors: list[str]
    warnings: list[str]
    
    @property
    def is_complete(self) -> bool:
        """Check if all documentation is complete."""
        return (
            self.readme_valid and
            self.api_valid and
            self.architecture_valid and
            self.capabilities_valid and
            self.consistency_valid
        )

@dataclass
class ConsistencyResult:
    """Agent count consistency check result."""
    is_consistent: bool
    counts: dict[str, int]  # doc_name -> agent_count
    discrepancies: list[str]  # List of discrepancy descriptions
```

---

### 4. Build Orchestrator Integration

#### Modified Methods in `BuildOrchestrator`

**Location:** `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Changes:**

```python
class BuildOrchestrator(SimpleModeOrchestrator):
    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for build workflow."""
        return [
            "enhancer",
            "planner",
            "architect",
            "designer",
            "implementer",
            "reviewer",    # If enabled
            "tester",      # If enabled
            "documenter"   # NEW: Add documentation step
        ]
    
    async def _execute_documenter_step(
        self,
        workflow_id: str,
        project_root: Path,
        implementation_result: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute documenter step for framework changes.
        
        Args:
            workflow_id: Workflow ID
            project_root: Project root directory
            implementation_result: Result from implementation step
        
        Returns:
            Dictionary with documentation update results
        """
        from tapps_agents.simple_mode.framework_change_detector import (
            FrameworkChangeDetector
        )
        from tapps_agents.agents.documenter.framework_doc_updater import (
            FrameworkDocUpdater
        )
        from tapps_agents.agents.documenter.doc_validator import (
            DocValidator
        )
        
        # 1. Detect framework changes
        detector = FrameworkChangeDetector(project_root)
        changes = detector.detect_changes()
        
        if not changes.new_agents:
            # No framework changes detected, skip documentation updates
            return {
                "type": "documenter",
                "framework_changes_detected": False,
                "skipped": True
            }
        
        # 2. Update documentation for each new agent
        updater = FrameworkDocUpdater(project_root)
        update_results = {}
        
        for agent_name in changes.new_agents:
            agent_info = changes.agent_info.get(agent_name)
            if agent_info:
                result = updater.update_all_docs(agent_name, agent_info)
                update_results[agent_name] = result
        
        # 3. Validate documentation
        validator = DocValidator(project_root)
        validation_results = {}
        
        for agent_name in changes.new_agents:
            result = validator.validate_completeness(agent_name)
            validation_results[agent_name] = result
        
        # 4. Check consistency
        consistency = validator.check_consistency()
        
        # 5. Generate report
        report = validator.generate_report(
            ValidationResult(
                readme_valid=all(r.readme_valid for r in validation_results.values()),
                api_valid=all(r.api_valid for r in validation_results.values()),
                architecture_valid=all(r.architecture_valid for r in validation_results.values()),
                capabilities_valid=all(r.capabilities_valid for r in validation_results.values()),
                consistency_valid=consistency.is_consistent,
                agent_count=consistency.counts,
                errors=[],
                warnings=[]
            )
        )
        
        return {
            "type": "documenter",
            "framework_changes_detected": True,
            "new_agents": changes.new_agents,
            "update_results": update_results,
            "validation_results": validation_results,
            "consistency": consistency,
            "report": report
        }
```

---

## Error Handling

### Error Types

1. **FileNotFoundError**: Documentation file doesn't exist
   - **Action**: Log warning, skip update for that file
   - **Recovery**: Continue with other files

2. **ParseError**: Cannot parse documentation file
   - **Action**: Log error, create backup, attempt recovery
   - **Recovery**: Try alternative parsing method or manual update

3. **WriteError**: Cannot write to file
   - **Action**: Log error, restore backup if available
   - **Recovery**: Retry with different method

4. **ValidationError**: Documentation validation failed
   - **Action**: Log errors, optionally fail workflow
   - **Recovery**: Provide clear error message with checklist

### Error Reporting

```python
@dataclass
class DocUpdateError(Exception):
    """Documentation update error."""
    file_path: Path
    operation: str
    error_message: str
    backup_path: Path | None = None
```

---

## Configuration

### Config Schema Addition

```yaml
agents:
  documenter:
    framework_doc_updates:
      enabled: true
      create_backups: true
      fail_on_validation_error: false
      validate_after_update: true
```

---

## Testing Requirements

### Unit Tests

1. **FrameworkChangeDetector Tests**
   - Test agent directory scanning
   - Test CLI registration detection
   - Test skill file detection
   - Test change detection logic

2. **FrameworkDocUpdater Tests**
   - Test README.md updates
   - Test API.md updates
   - Test ARCHITECTURE.md updates
   - Test agent-capabilities.mdc updates
   - Test backup creation

3. **DocValidator Tests**
   - Test completeness validation
   - Test consistency checks
   - Test report generation

### Integration Tests

1. **Full Workflow Test**
   - Create mock agent
   - Run build workflow
   - Verify documentation updates
   - Verify validation passes

2. **Edge Case Tests**
   - Missing documentation files
   - Malformed documentation
   - Multiple agents added simultaneously
