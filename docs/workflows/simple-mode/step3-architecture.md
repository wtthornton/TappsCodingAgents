# Step 3: Architecture Design - Brownfield System Review Feature

## System Overview

The Brownfield System Review feature automates the analysis of existing codebases, creates expert configurations, and populates RAG knowledge bases. It integrates with existing TappsCodingAgents components to provide a seamless workflow.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Brownfield Review Orchestrator               │
│  (Coordinates all components, manages workflow state)           │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ├──────────────────────────────────────────────┐
               │                                              │
               ▼                                              ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│   BrownfieldAnalyzer     │              │  ExpertConfigGenerator    │
│                          │              │                          │
│  - Analyze codebase      │              │  - Generate YAML configs  │
│  - Detect technologies   │              │  - Create expert entries  │
│  - Identify patterns     │              │  - Set weights/matrices   │
│                          │              │  - Validate configs       │
└──────────┬───────────────┘              └──────────┬───────────────┘
           │                                          │
           │ Uses                                     │ Uses
           ▼                                          ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│   DomainStackDetector    │              │    ExpertRegistry         │
│  (Existing Component)    │              │  (Existing Component)    │
│                          │              │                          │
│  - Detect domains        │              │  - Load expert configs   │
│  - Map tech to domains   │              │  - Register experts      │
│  - Prioritize domains    │              │  - Manage expert lifecycle│
└──────────────────────────┘              └──────────────────────────┘
           │
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Knowledge Ingestion Pipeline                       │
│  (Existing Component - Enhanced for Expert-Specific KBs)       │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ Project Sources  │  │ Context7 Sources │                   │
│  │ - Requirements   │  │ - Library Docs    │                   │
│  │ - Architecture   │  │ - API References  │                   │
│  │ - ADRs          │  │ - Best Practices │                   │
│  │ - Runbooks      │  └──────────────────┘                   │
│  └──────────────────┘                                          │
│           │              │                                      │
│           └──────┬───────┘                                      │
│                  ▼                                              │
│         ┌──────────────────┐                                   │
│         │ Expert Knowledge  │                                   │
│         │ Base Population   │                                   │
│         └──────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
           │
           │ Creates/Populates
           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Expert Knowledge Bases                             │
│                                                                 │
│  .tapps-agents/kb/                                              │
│  ├── expert-python/          (VectorKnowledgeBase)              │
│  ├── expert-fastapi/         (VectorKnowledgeBase)              │
│  ├── expert-frontend/        (SimpleKnowledgeBase)              │
│  └── expert-{domain}/        (Auto-created per domain)           │
└─────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. BrownfieldAnalyzer

**Purpose:** Analyze brownfield codebase and detect domains/technologies

**Location:** `tapps_agents/core/brownfield_analyzer.py`

**Responsibilities:**
- Analyze project structure (files, directories, patterns)
- Detect programming languages and frameworks
- Identify dependencies from package files
- Integrate with DomainStackDetector
- Generate analysis report

**Key Methods:**
```python
class BrownfieldAnalyzer:
    def __init__(self, project_root: Path, domain_detector: DomainStackDetector):
        """Initialize analyzer with project root and domain detector."""
    
    async def analyze(self) -> BrownfieldAnalysisResult:
        """Perform complete brownfield analysis."""
    
    def detect_languages(self) -> list[str]:
        """Detect programming languages from file extensions."""
    
    def detect_frameworks(self) -> list[str]:
        """Detect frameworks from dependency files and code patterns."""
    
    def detect_dependencies(self) -> list[str]:
        """Extract dependencies from package files."""
    
    async def detect_domains(self) -> list[DomainMatch]:
        """Use DomainStackDetector to identify domains."""
```

**Dependencies:**
- `DomainStackDetector` (existing)
- `ProjectProfile` (existing)

---

### 2. ExpertConfigGenerator

**Purpose:** Generate expert YAML configurations based on detected domains

**Location:** `tapps_agents/core/expert_config_generator.py`

**Responsibilities:**
- Generate expert configurations for detected domains
- Create/update `.tapps-agents/experts.yaml`
- Set default expert weights and confidence matrices
- Validate generated configurations
- Preserve existing expert configurations

**Key Methods:**
```python
class ExpertConfigGenerator:
    def __init__(self, project_root: Path, expert_registry: ExpertRegistry):
        """Initialize generator with project root and expert registry."""
    
    def generate_expert_configs(
        self, 
        domains: list[DomainMatch]
    ) -> list[ExpertConfig]:
        """Generate expert configurations for detected domains."""
    
    def write_expert_configs(
        self, 
        configs: list[ExpertConfig],
        merge: bool = True
    ) -> None:
        """Write expert configurations to experts.yaml."""
    
    def validate_config(self, config: ExpertConfig) -> bool:
        """Validate expert configuration."""
```

**Dependencies:**
- `ExpertRegistry` (existing)
- YAML file handling

---

### 3. BrownfieldReviewOrchestrator

**Purpose:** Orchestrate the complete brownfield review workflow

**Location:** `tapps_agents/core/brownfield_review.py`

**Responsibilities:**
- Coordinate all components
- Manage workflow state
- Handle errors and recovery
- Generate progress reports
- Support dry-run mode

**Key Methods:**
```python
class BrownfieldReviewOrchestrator:
    def __init__(
        self,
        project_root: Path,
        context7_helper: Context7AgentHelper | None = None,
        dry_run: bool = False
    ):
        """Initialize orchestrator."""
    
    async def review(
        self,
        auto: bool = False,
        include_context7: bool = True
    ) -> BrownfieldReviewResult:
        """Perform complete brownfield review."""
    
    async def _analyze_codebase(self) -> BrownfieldAnalysisResult:
        """Step 1: Analyze codebase."""
    
    async def _create_experts(self, domains: list[DomainMatch]) -> list[ExpertConfig]:
        """Step 2: Create expert configurations."""
    
    async def _populate_rag(
        self,
        experts: list[ExpertConfig],
        include_context7: bool = True
    ) -> dict[str, IngestionResult]:
        """Step 3: Populate RAG knowledge bases."""
    
    def _generate_report(self, result: BrownfieldReviewResult) -> str:
        """Generate human-readable report."""
```

**Dependencies:**
- `BrownfieldAnalyzer`
- `ExpertConfigGenerator`
- `KnowledgeIngestionPipeline` (existing)
- `Context7AgentHelper` (existing)

---

### 4. Enhanced KnowledgeIngestionPipeline

**Purpose:** Extend existing pipeline to support expert-specific knowledge bases

**Location:** `tapps_agents/experts/knowledge_ingestion.py` (enhance existing)

**Enhancements:**
- Support expert-specific knowledge base directories
- Map ingested content to appropriate experts
- Create knowledge bases per expert
- Populate from both project sources and Context7

**New Methods:**
```python
class KnowledgeIngestionPipeline:
    async def ingest_for_expert(
        self,
        expert_id: str,
        expert_domain: str,
        include_context7: bool = True
    ) -> IngestionResult:
        """Ingest knowledge for a specific expert."""
    
    def _create_expert_kb(
        self,
        expert_id: str,
        expert_domain: str
    ) -> VectorKnowledgeBase | SimpleKnowledgeBase:
        """Create knowledge base for expert."""
```

---

## Data Models

### BrownfieldAnalysisResult
```python
@dataclass
class BrownfieldAnalysisResult:
    project_root: Path
    languages: list[str]
    frameworks: list[str]
    dependencies: list[str]
    domains: list[DomainMatch]
    detected_at: datetime
    analysis_metadata: dict[str, Any]
```

### ExpertConfig
```python
@dataclass
class ExpertConfig:
    expert_id: str
    expert_name: str
    primary_domain: str
    rag_enabled: bool
    knowledge_base_dir: Path
    confidence_matrix: dict[str, float]
    metadata: dict[str, Any]
```

### BrownfieldReviewResult
```python
@dataclass
class BrownfieldReviewResult:
    analysis: BrownfieldAnalysisResult
    experts_created: list[ExpertConfig]
    rag_results: dict[str, IngestionResult]
    errors: list[str]
    warnings: list[str]
    execution_time: float
    dry_run: bool
```

---

## Integration Points

### 1. CLI Integration

**File:** `tapps_agents/cli/commands/top_level.py`

**New Command Handler:**
```python
def handle_brownfield_review(args: object) -> None:
    """Handle brownfield review command."""
    orchestrator = BrownfieldReviewOrchestrator(
        project_root=Path.cwd(),
        context7_helper=get_context7_helper(),
        dry_run=args.dry_run
    )
    result = asyncio.run(orchestrator.review(auto=args.auto))
    print(result.report)
```

**File:** `tapps_agents/cli/parsers/top_level.py`

**New Parser:**
```python
brownfield_parser = subparsers.add_parser(
    "brownfield",
    help="Brownfield system analysis and expert creation"
)
brownfield_subparsers = brownfield_parser.add_subparsers(dest="brownfield_command")

review_parser = brownfield_subparsers.add_parser(
    "review",
    help="Review brownfield system and create experts"
)
review_parser.add_argument("--auto", action="store_true", help="Fully automated")
review_parser.add_argument("--dry-run", action="store_true", help="Preview changes")
review_parser.add_argument("--output-dir", type=Path, help="Output directory")
```

### 2. Simple Mode Integration

**File:** `tapps_agents/simple_mode/orchestrators/brownfield_orchestrator.py` (new)

**Orchestrator:**
```python
class BrownfieldOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for brownfield system review."""
    
    async def execute(self, intent: Intent, parameters: dict[str, Any]) -> AgentOutput:
        """Execute brownfield review workflow."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=self.project_root,
            context7_helper=self.context7_helper,
            dry_run=parameters.get("dry_run", False)
        )
        result = await orchestrator.review(auto=parameters.get("auto", False))
        return self._format_result(result)
```

**File:** `tapps_agents/simple_mode/command_parser.py` (enhance)

**Add Command:**
```python
BROWNFIELD_COMMANDS = [
    "brownfield-review",
    "review-brownfield",
    "analyze-project",
    "create-experts"
]
```

---

## Data Flow

### Complete Workflow

1. **User invokes command** (CLI or Simple Mode)
2. **BrownfieldReviewOrchestrator initializes**
   - Loads project root
   - Initializes DomainStackDetector
   - Initializes Context7AgentHelper (if available)
3. **Analysis Phase**
   - BrownfieldAnalyzer analyzes codebase
   - DomainStackDetector identifies domains
   - Generates BrownfieldAnalysisResult
4. **Expert Creation Phase**
   - ExpertConfigGenerator creates configs for each domain
   - Writes to `.tapps-agents/experts.yaml`
   - Validates configurations
5. **RAG Population Phase**
   - For each expert:
     - Creates knowledge base directory
     - Ingests project documentation
     - Fetches Context7 library docs (if enabled)
     - Builds vector indexes
   - Reports ingestion statistics
6. **Report Generation**
   - Generates summary report
   - Returns BrownfieldReviewResult

---

## Error Handling Strategy

1. **Domain Detection Failures**
   - Log error, continue with other domains
   - Include in final report

2. **Expert Creation Failures**
   - Log error, skip failed expert
   - Continue with other experts

3. **Context7 Unavailability**
   - Skip Context7 ingestion
   - Continue with project sources only
   - Log warning

4. **RAG Population Failures**
   - Log error per expert
   - Continue with other experts
   - Report failures in summary

5. **Resume Capability**
   - Store state in `.tapps-agents/brownfield-review-state.json`
   - Support resume from last successful step

---

## Performance Considerations

1. **Parallel Processing**
   - Process multiple experts in parallel
   - Parallel Context7 API calls (with rate limiting)

2. **Caching**
   - Cache domain detection results
   - Cache Context7 documentation
   - Cache analysis results

3. **Incremental Updates**
   - Only process changed files
   - Support incremental RAG updates

4. **Resource Management**
   - Limit concurrent operations
   - Monitor memory usage for large codebases

---

## Security Considerations

1. **Path Validation**
   - Validate all file paths
   - Prevent directory traversal

2. **Expert ID Sanitization**
   - Sanitize expert IDs and domain names
   - Prevent injection attacks

3. **Context7 API Key**
   - Secure API key handling
   - Never log API keys

---

## Testing Strategy

1. **Unit Tests**
   - BrownfieldAnalyzer methods
   - ExpertConfigGenerator methods
   - Configuration validation

2. **Integration Tests**
   - End-to-end workflow
   - Domain detection integration
   - Expert creation integration
   - RAG population integration

3. **CLI Tests**
   - Command parsing
   - Error handling
   - Output formatting

4. **Simple Mode Tests**
   - Command recognition
   - Workflow execution
   - Output formatting
