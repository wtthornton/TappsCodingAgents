# Step 4: Component Design - Brownfield System Review Feature

## API Specifications

### 1. BrownfieldAnalyzer API

**Module:** `tapps_agents.core.brownfield_analyzer`

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..experts.domain_detector import DomainStackDetector, DomainMapping

@dataclass
class BrownfieldAnalysisResult:
    """Result of brownfield codebase analysis."""
    project_root: Path
    languages: list[str]
    frameworks: list[str]
    dependencies: list[str]
    domains: list[DomainMapping]
    detected_at: datetime
    analysis_metadata: dict[str, Any]

class BrownfieldAnalyzer:
    """
    Analyzes brownfield codebase to detect technologies and domains.
    
    Usage:
        detector = DomainStackDetector(project_root)
        analyzer = BrownfieldAnalyzer(project_root, detector)
        result = await analyzer.analyze()
    """
    
    def __init__(
        self,
        project_root: Path,
        domain_detector: DomainStackDetector
    ) -> None:
        """
        Initialize analyzer.
        
        Args:
            project_root: Root directory of project to analyze
            domain_detector: DomainStackDetector instance for domain detection
        """
    
    async def analyze(self) -> BrownfieldAnalysisResult:
        """
        Perform complete brownfield analysis.
        
        Returns:
            BrownfieldAnalysisResult with detected languages, frameworks, 
            dependencies, and domains
        """
    
    def detect_languages(self) -> list[str]:
        """
        Detect programming languages from file extensions and content.
        
        Returns:
            List of detected language names (e.g., ["python", "typescript"])
        """
    
    def detect_frameworks(self) -> list[str]:
        """
        Detect frameworks from dependency files and code patterns.
        
        Returns:
            List of detected framework names (e.g., ["fastapi", "react"])
        """
    
    def detect_dependencies(self) -> list[str]:
        """
        Extract dependencies from package files.
        
        Supports:
        - Python: requirements.txt, pyproject.toml, setup.py
        - Node.js: package.json
        - Go: go.mod
        - Java: pom.xml, build.gradle
        
        Returns:
            List of dependency names (e.g., ["fastapi", "pytest", "react"])
        """
    
    async def detect_domains(self) -> list[DomainMapping]:
        """
        Use DomainStackDetector to identify domains.
        
        Returns:
            List of DomainMapping objects with confidence scores
        """
```

---

### 2. ExpertConfigGenerator API

**Module:** `tapps_agents.core.expert_config_generator`

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..experts.domain_detector import DomainMapping
from ..experts.expert_registry import ExpertRegistry

@dataclass
class ExpertConfig:
    """Expert configuration to be written to YAML."""
    expert_id: str
    expert_name: str
    primary_domain: str
    rag_enabled: bool = True
    knowledge_base_dir: Path | None = None
    confidence_matrix: dict[str, float] | None = None
    metadata: dict[str, Any] | None = None

class ExpertConfigGenerator:
    """
    Generates expert YAML configurations based on detected domains.
    
    Usage:
        registry = ExpertRegistry.from_domains_file(domains_file)
        generator = ExpertConfigGenerator(project_root, registry)
        configs = generator.generate_expert_configs(domains)
        generator.write_expert_configs(configs, merge=True)
    """
    
    def __init__(
        self,
        project_root: Path,
        expert_registry: ExpertRegistry | None = None
    ) -> None:
        """
        Initialize generator.
        
        Args:
            project_root: Root directory of project
            expert_registry: Optional ExpertRegistry for validation
        """
    
    def generate_expert_configs(
        self,
        domains: list[DomainMapping]
    ) -> list[ExpertConfig]:
        """
        Generate expert configurations for detected domains.
        
        Args:
            domains: List of DomainMapping objects from domain detection
            
        Returns:
            List of ExpertConfig objects ready to be written
        """
    
    def write_expert_configs(
        self,
        configs: list[ExpertConfig],
        merge: bool = True
    ) -> None:
        """
        Write expert configurations to experts.yaml.
        
        Args:
            configs: List of ExpertConfig objects to write
            merge: If True, merge with existing configs; if False, overwrite
        """
    
    def validate_config(self, config: ExpertConfig) -> bool:
        """
        Validate expert configuration.
        
        Args:
            config: ExpertConfig to validate
            
        Returns:
            True if valid, False otherwise
        """
    
    def _load_existing_configs(self) -> dict[str, Any]:
        """Load existing expert configurations from YAML."""
    
    def _merge_configs(
        self,
        existing: dict[str, Any],
        new: list[ExpertConfig]
    ) -> dict[str, Any]:
        """Merge new configs with existing ones."""
```

---

### 3. BrownfieldReviewOrchestrator API

**Module:** `tapps_agents.core.brownfield_review`

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..context7.agent_integration import Context7AgentHelper
from ..experts.knowledge_ingestion import IngestionResult
from .brownfield_analyzer import BrownfieldAnalysisResult
from .expert_config_generator import ExpertConfig

@dataclass
class BrownfieldReviewResult:
    """Result of complete brownfield review."""
    analysis: BrownfieldAnalysisResult
    experts_created: list[ExpertConfig]
    rag_results: dict[str, IngestionResult]  # expert_id -> ingestion result
    errors: list[str]
    warnings: list[str]
    execution_time: float
    dry_run: bool
    report: str  # Human-readable summary report

class BrownfieldReviewOrchestrator:
    """
    Orchestrates complete brownfield review workflow.
    
    Usage:
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=Path.cwd(),
            context7_helper=context7_helper,
            dry_run=False
        )
        result = await orchestrator.review(auto=True, include_context7=True)
        print(result.report)
    """
    
    def __init__(
        self,
        project_root: Path,
        context7_helper: Context7AgentHelper | None = None,
        dry_run: bool = False
    ) -> None:
        """
        Initialize orchestrator.
        
        Args:
            project_root: Root directory of project to review
            context7_helper: Optional Context7 helper for library docs
            dry_run: If True, preview changes without applying
        """
    
    async def review(
        self,
        auto: bool = False,
        include_context7: bool = True
    ) -> BrownfieldReviewResult:
        """
        Perform complete brownfield review.
        
        Args:
            auto: If True, skip all prompts and use defaults
            include_context7: If True, fetch library docs from Context7
            
        Returns:
            BrownfieldReviewResult with complete analysis and results
        """
    
    async def _analyze_codebase(self) -> BrownfieldAnalysisResult:
        """Step 1: Analyze codebase structure and detect domains."""
    
    async def _create_experts(
        self,
        domains: list[DomainMapping]
    ) -> list[ExpertConfig]:
        """Step 2: Create expert configurations."""
    
    async def _populate_rag(
        self,
        experts: list[ExpertConfig],
        include_context7: bool = True
    ) -> dict[str, IngestionResult]:
        """Step 3: Populate RAG knowledge bases for each expert."""
    
    def _generate_report(self, result: BrownfieldReviewResult) -> str:
        """Generate human-readable summary report."""
```

---

### 4. Enhanced KnowledgeIngestionPipeline API

**Module:** `tapps_agents.experts.knowledge_ingestion` (enhance existing)

**New Methods:**

```python
class KnowledgeIngestionPipeline:
    # ... existing methods ...
    
    async def ingest_for_expert(
        self,
        expert_id: str,
        expert_domain: str,
        include_context7: bool = True
    ) -> IngestionResult:
        """
        Ingest knowledge for a specific expert.
        
        Args:
            expert_id: ID of expert (e.g., "expert-python")
            expert_domain: Primary domain of expert (e.g., "python")
            include_context7: If True, fetch Context7 library docs
            
        Returns:
            IngestionResult with statistics
        """
    
    def _create_expert_kb(
        self,
        expert_id: str,
        expert_domain: str
    ) -> VectorKnowledgeBase | SimpleKnowledgeBase:
        """
        Create knowledge base for expert.
        
        Args:
            expert_id: ID of expert
            expert_domain: Primary domain of expert
            
        Returns:
            Initialized knowledge base instance
        """
```

---

## CLI Command Specification

### Command: `brownfield review`

**Full Command:**
```bash
tapps-agents brownfield review [--auto] [--dry-run] [--output-dir <dir>] [--no-context7]
```

**Options:**
- `--auto`: Fully automated execution (skip prompts)
- `--dry-run`: Preview changes without applying
- `--output-dir <dir>`: Specify output directory for reports (default: `.tapps-agents/brownfield-review/`)
- `--no-context7`: Skip Context7 library documentation fetching

**Examples:**
```bash
# Full automated review
tapps-agents brownfield review --auto

# Preview changes
tapps-agents brownfield review --dry-run

# Skip Context7
tapps-agents brownfield review --auto --no-context7

# Custom output directory
tapps-agents brownfield review --auto --output-dir reports/brownfield/
```

**Output:**
- Progress indicators during execution
- Summary report at completion
- Expert configurations written to `.tapps-agents/experts.yaml`
- Knowledge bases created in `.tapps-agents/kb/{expert-id}/`

---

## Simple Mode Command Specification

### Command: `*brownfield-review`

**Cursor Chat Usage:**
```cursor
@simple-mode *brownfield-review
@simple-mode Review brownfield system and create experts
@simple-mode Analyze project and populate RAG
```

**Natural Language Patterns:**
- "Review brownfield system"
- "Analyze project and create experts"
- "Create experts from codebase analysis"
- "Populate RAG for brownfield project"

**Parameters:**
- `auto`: Boolean, fully automated (default: true)
- `dry_run`: Boolean, preview mode (default: false)
- `include_context7`: Boolean, fetch library docs (default: true)

**Output:**
- Progress updates in chat
- Summary report in markdown format
- Links to created expert configurations
- Statistics on knowledge base population

---

## Data Models

### BrownfieldAnalysisResult
```python
@dataclass
class BrownfieldAnalysisResult:
    project_root: Path
    languages: list[str]  # ["python", "typescript"]
    frameworks: list[str]  # ["fastapi", "react"]
    dependencies: list[str]  # ["fastapi", "pytest", "react"]
    domains: list[DomainMapping]  # From DomainStackDetector
    detected_at: datetime
    analysis_metadata: dict[str, Any]  # Additional metadata
```

### ExpertConfig
```python
@dataclass
class ExpertConfig:
    expert_id: str  # "expert-python"
    expert_name: str  # "Python Expert"
    primary_domain: str  # "python"
    rag_enabled: bool  # True
    knowledge_base_dir: Path  # .tapps-agents/kb/expert-python/
    confidence_matrix: dict[str, float] | None  # Domain confidence scores
    metadata: dict[str, Any] | None  # Additional metadata
```

### BrownfieldReviewResult
```python
@dataclass
class BrownfieldReviewResult:
    analysis: BrownfieldAnalysisResult
    experts_created: list[ExpertConfig]
    rag_results: dict[str, IngestionResult]  # expert_id -> result
    errors: list[str]
    warnings: list[str]
    execution_time: float  # Seconds
    dry_run: bool
    report: str  # Human-readable markdown report
```

---

## Component Interactions

### Sequence Diagram

```
User → CLI/SimpleMode → BrownfieldReviewOrchestrator
                          │
                          ├─→ BrownfieldAnalyzer
                          │     │
                          │     └─→ DomainStackDetector
                          │
                          ├─→ ExpertConfigGenerator
                          │     │
                          │     └─→ ExpertRegistry
                          │
                          └─→ KnowledgeIngestionPipeline
                                │
                                ├─→ Project Sources
                                │
                                └─→ Context7AgentHelper
                                      │
                                      └─→ Context7 API
```

### Data Flow

1. **Analysis Phase**
   - `BrownfieldAnalyzer.analyze()` → `BrownfieldAnalysisResult`
   - Uses `DomainStackDetector.detect_stack()` for domain detection

2. **Expert Creation Phase**
   - `ExpertConfigGenerator.generate_expert_configs(domains)` → `list[ExpertConfig]`
   - `ExpertConfigGenerator.write_expert_configs(configs)` → writes to YAML

3. **RAG Population Phase**
   - For each expert:
     - `KnowledgeIngestionPipeline.ingest_for_expert(expert_id, domain)` → `IngestionResult`
     - Creates knowledge base in `.tapps-agents/kb/{expert-id}/`
     - Populates from project sources and Context7

4. **Report Generation**
   - `BrownfieldReviewOrchestrator._generate_report(result)` → markdown report

---

## Error Handling

### Error Categories

1. **Analysis Errors**
   - Domain detection failures → Log, continue with other domains
   - File read errors → Log, skip file

2. **Expert Creation Errors**
   - Invalid domain → Log, skip expert
   - YAML write errors → Log, return error list

3. **RAG Population Errors**
   - Context7 unavailable → Log warning, continue with project sources
   - Knowledge base creation failures → Log, skip expert
   - Ingestion failures → Log, continue with other sources

### Error Response Format

```python
@dataclass
class BrownfieldReviewResult:
    # ... other fields ...
    errors: list[str]  # ["Failed to detect domain X", "Context7 unavailable"]
    warnings: list[str]  # ["Skipped expert Y due to invalid config"]
```

---

## Configuration Files

### experts.yaml Structure

```yaml
experts:
  - expert_id: expert-python
    expert_name: Python Expert
    primary_domain: python
    rag_enabled: true
    knowledge_base_dir: .tapps-agents/kb/expert-python/
    confidence_matrix:
      python: 0.9
      testing: 0.8
      api-design-integration: 0.7
    metadata:
      created_by: brownfield-review
      created_at: "2026-01-16T10:00:00Z"
      detected_domains: ["python", "testing"]
  
  - expert_id: expert-fastapi
    expert_name: FastAPI Expert
    primary_domain: fastapi
    rag_enabled: true
    knowledge_base_dir: .tapps-agents/kb/expert-fastapi/
    # ... similar structure
```

---

## Testing Specifications

### Unit Tests

1. **BrownfieldAnalyzer Tests**
   - `test_detect_languages()` - Language detection from files
   - `test_detect_frameworks()` - Framework detection from dependencies
   - `test_detect_dependencies()` - Dependency extraction
   - `test_analyze()` - Complete analysis workflow

2. **ExpertConfigGenerator Tests**
   - `test_generate_expert_configs()` - Config generation
   - `test_write_expert_configs()` - YAML writing
   - `test_validate_config()` - Configuration validation
   - `test_merge_configs()` - Config merging

3. **BrownfieldReviewOrchestrator Tests**
   - `test_review()` - Complete workflow
   - `test_dry_run()` - Dry-run mode
   - `test_error_handling()` - Error recovery

### Integration Tests

1. **End-to-End Workflow**
   - Test complete workflow with sample project
   - Verify expert creation
   - Verify RAG population

2. **CLI Integration**
   - Test command parsing
   - Test command execution
   - Test output formatting

3. **Simple Mode Integration**
   - Test command recognition
   - Test workflow execution
   - Test output formatting

---

## Implementation Notes

1. **Reuse Existing Components**
   - Leverage `DomainStackDetector` for domain detection
   - Use `KnowledgeIngestionPipeline` for RAG population
   - Integrate with `ExpertRegistry` for expert management
   - Use `Context7AgentHelper` for library docs

2. **Incremental Development**
   - Start with analysis phase
   - Add expert creation
   - Add RAG population
   - Add CLI/Simple Mode integration

3. **Error Recovery**
   - Continue processing on individual failures
   - Log all errors with context
   - Provide comprehensive error reports

4. **Performance**
   - Parallel processing where possible
   - Caching of analysis results
   - Incremental RAG updates
