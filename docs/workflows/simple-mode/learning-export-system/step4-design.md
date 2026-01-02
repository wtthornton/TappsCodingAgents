# Step 4: Component Design - Learning Export API and Data Models

## API Design

### LearningDataExporter API

#### Class: LearningDataExporter
```python
class LearningDataExporter:
    """Collects and exports learning data from all learning system components."""
    
    def __init__(
        self,
        project_root: Path | None = None,
        learning_dashboard: LearningDashboard | None = None,
        capability_registry: CapabilityRegistry | None = None,
        analytics_dashboard: AnalyticsDashboard | None = None,
    )
    """Initialize exporter with learning system components."""
    
    def collect_capability_metrics(
        self,
        capability_id: str | None = None
    ) -> dict[str, Any]
    """Collect capability metrics from CapabilityRegistry."""
    
    def collect_pattern_statistics(self) -> dict[str, Any]
    """Collect pattern statistics from PatternExtractor."""
    
    def collect_learning_effectiveness(self) -> dict[str, Any]
    """Collect learning effectiveness data from meta-learning components."""
    
    def collect_analytics_data(self) -> dict[str, Any]
    """Collect analytics data from AnalyticsDashboard."""
    
    def collect_all_data(self) -> dict[str, Any]
    """Collect all learning data from all components."""
    
    def export(
        self,
        output_path: Path | None = None,
        anonymize: bool = True,
        compress: bool = False,
        format: str = "json"
    ) -> Path
    """Export learning data to file."""
    
    def get_export_metadata(self) -> dict[str, Any]
    """Get export metadata (timestamp, version, etc.)."""
```

### AnonymizationPipeline API

#### Class: AnonymizationPipeline
```python
class AnonymizationPipeline:
    """Anonymizes learning data for privacy."""
    
    def __init__(
        self,
        hash_salt: str | None = None,
        preserve_aggregates: bool = True
    )
    """Initialize anonymization pipeline."""
    
    def anonymize_path(self, path: str) -> str
    """Anonymize file paths (replace with generic patterns)."""
    
    def hash_identifier(self, identifier: str) -> str
    """Hash identifier using SHA-256."""
    
    def remove_code_snippets(self, data: dict[str, Any]) -> dict[str, Any]
    """Remove code snippets from data."""
    
    def anonymize_context(self, context: dict[str, Any]) -> dict[str, Any]
    """Anonymize context data."""
    
    def anonymize_export_data(
        self,
        export_data: dict[str, Any]
    ) -> dict[str, Any]
    """Anonymize complete export data."""
    
    def validate_anonymization(
        self,
        original: dict[str, Any],
        anonymized: dict[str, Any]
    ) -> AnonymizationReport
    """Validate anonymization completeness."""
    
    def generate_report(self) -> AnonymizationReport
    """Generate anonymization report."""
```

### ExportSchema API

#### Class: ExportSchema
```python
class ExportSchema:
    """Defines and validates export data format."""
    
    SCHEMA_VERSION = "1.0"
    
    @staticmethod
    def get_schema(version: str = "1.0") -> dict[str, Any]
    """Get JSON schema for specified version."""
    
    @staticmethod
    def validate(
        data: dict[str, Any],
        version: str = "1.0"
    ) -> ValidationResult
    """Validate export data against schema."""
    
    @staticmethod
    def migrate(
        data: dict[str, Any],
        from_version: str,
        to_version: str
    ) -> dict[str, Any]
    """Migrate export data between schema versions."""
    
    @staticmethod
    def get_latest_version() -> str
    """Get latest schema version."""
```

### CLI Commands API

#### Module: tapps_agents.cli.commands.learning
```python
def handle_learning_command(args: object) -> None
"""Handle learning CLI commands."""

def handle_learning_export(args: object) -> None
"""Handle 'learning export' command."""

def handle_learning_dashboard(args: object) -> None
"""Handle 'learning dashboard' command."""

def handle_learning_submit(args: object) -> None
"""Handle 'learning submit' command (future)."""
```

## Data Models

### ExportData
```python
@dataclass
class ExportData:
    """Complete export data structure."""
    
    export_metadata: ExportMetadata
    capability_metrics: CapabilityMetricsData
    pattern_statistics: PatternStatisticsData
    learning_effectiveness: LearningEffectivenessData
    analytics_data: AnalyticsData
    usage_patterns: UsagePatternsData
```

### ExportMetadata
```python
@dataclass
class ExportMetadata:
    """Export metadata."""
    
    export_timestamp: datetime
    framework_version: str
    export_version: str
    schema_version: str
    project_hash: str  # Anonymized project identifier
    anonymization_applied: bool
    privacy_notice: str
```

### CapabilityMetricsData
```python
@dataclass
class CapabilityMetricsData:
    """Capability metrics export data."""
    
    total_capabilities: int
    capabilities: list[CapabilityMetricExport]
    average_success_rate: float
    average_quality_score: float
    total_usage_count: int

@dataclass
class CapabilityMetricExport:
    """Single capability metric export (anonymized)."""
    
    capability_id: str  # Anonymized
    agent_id: str
    usage_count: int
    success_rate: float
    quality_score: float
    average_duration: float
    refinement_count: int
    # Note: refinement_history excluded for privacy
```

### PatternStatisticsData
```python
@dataclass
class PatternStatisticsData:
    """Pattern statistics export data."""
    
    total_patterns: int
    total_anti_patterns: int
    patterns_by_type: dict[str, int]
    average_quality: float
    average_security: float
    secure_patterns: int
    insecure_patterns: int
    # Note: Raw code snippets excluded for privacy
```

### LearningEffectivenessData
```python
@dataclass
class LearningEffectivenessData:
    """Learning effectiveness export data."""
    
    average_roi_score: float
    average_effectiveness: float
    improvement_trends: dict[str, float]
    learning_strategy_effectiveness: dict[str, float]
    meta_learning_optimizations: list[str]
```

### AnalyticsData
```python
@dataclass
class AnalyticsData:
    """Analytics export data."""
    
    agent_metrics: list[AgentMetricExport]
    workflow_metrics: list[WorkflowMetricExport]
    system_metrics: SystemMetricsExport
    trends: TrendsData

@dataclass
class AgentMetricExport:
    """Agent performance metric export."""
    
    agent_id: str
    total_executions: int
    success_rate: float
    average_duration: float
    error_count: int
```

### AnonymizationReport
```python
@dataclass
class AnonymizationReport:
    """Report on anonymization process."""
    
    paths_anonymized: int
    identifiers_hashed: int
    code_snippets_removed: int
    context_data_removed: int
    data_points_aggregated: int
    anonymization_complete: bool
    warnings: list[str]
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    """Schema validation result."""
    
    valid: bool
    errors: list[str]
    warnings: list[str]
    schema_version: str
```

## CLI Command Specifications

### Command: `tapps-agents learning export`

**Usage:**
```bash
tapps-agents learning export [--output <path>] [--no-anonymize] [--compress] [--format json|yaml] [--yes]
```

**Options:**
- `--output <path>`: Output file path (default: `.tapps-agents/exports/learning-export-{timestamp}.json`)
- `--no-anonymize`: Disable anonymization (NOT RECOMMENDED, requires explicit confirmation)
- `--compress`: Compress export with gzip
- `--format json|yaml`: Export format (default: json)
- `--yes`: Skip confirmation prompt

**Behavior:**
1. Collect all learning data from components
2. Apply anonymization (unless disabled)
3. Validate against export schema
4. Add export metadata
5. Save to file
6. Display anonymization report

**Output:**
- Export file path
- Anonymization report
- Validation status

### Command: `tapps-agents learning dashboard`

**Usage:**
```bash
tapps-agents learning dashboard [--capability <id>] [--format text|json] [--include-trends] [--include-failures]
```

**Options:**
- `--capability <id>`: Filter by capability ID
- `--format text|json`: Output format (default: text)
- `--include-trends`: Include trend data
- `--include-failures`: Include failure analysis

**Behavior:**
1. Load learning dashboard data
2. Format according to output format
3. Display to console or save to file

**Output:**
- Capability metrics
- Pattern statistics
- Security metrics
- Learning trends (if requested)
- Failure analysis (if requested)

### Command: `tapps-agents learning submit` (Future)

**Usage:**
```bash
tapps-agents learning submit [--export-file <path>] [--include-metadata] [--output <path>]
```

**Options:**
- `--export-file <path>`: Path to export file (default: latest export)
- `--include-metadata`: Include optional project metadata
- `--output <path>`: Save submission package to file

**Behavior:**
1. Load export file
2. Prepare submission package
3. Add submission metadata
4. Save to file or submit via API (future)

## Error Handling

### Export Errors

**MissingLearningDataError:**
- Raised when required learning components are not available
- Provides guidance on enabling learning system

**AnonymizationError:**
- Raised when anonymization cannot complete
- Provides specific error details

**ValidationError:**
- Raised when export data fails schema validation
- Provides validation error details and suggestions

**StorageError:**
- Raised when export file cannot be saved
- Provides disk space and permission guidance

## Configuration

### Learning Export Configuration

**Location:** `.tapps-agents/config.yaml`

```yaml
learning:
  export:
    enabled: true
    default_anonymize: true
    default_compress: false
    export_dir: ".tapps-agents/exports"
    schema_version: "1.0"
    privacy_notice: "Exported data is anonymized and contains no sensitive information."
```

## Integration Examples

### Example: Export Learning Data

```python
from tapps_agents.core.learning_export import LearningDataExporter
from pathlib import Path

exporter = LearningDataExporter(project_root=Path.cwd())
export_path = exporter.export(
    output_path=Path(".tapps-agents/exports/my-export.json"),
    anonymize=True,
    compress=False
)
print(f"Exported to: {export_path}")
```

### Example: View Dashboard

```python
from tapps_agents.core.learning_dashboard import LearningDashboard
from tapps_agents.core.capability_registry import CapabilityRegistry

registry = CapabilityRegistry()
dashboard = LearningDashboard(capability_registry=registry)
data = dashboard.get_dashboard_data()
print(f"Total capabilities: {data['capability_metrics']['total_capabilities']}")
```

### Example: Validate Export

```python
from tapps_agents.core.export_schema import ExportSchema
import json

with open("export.json") as f:
    data = json.load(f)

result = ExportSchema.validate(data, version="1.0")
if result.valid:
    print("Export is valid")
else:
    print(f"Validation errors: {result.errors}")
```
