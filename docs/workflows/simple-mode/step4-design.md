# Step 4: Component Design - Business Metrics API and Data Models

## API Design

### BusinessMetricsCollector API

#### Class: BusinessMetricsCollector
```python
class BusinessMetricsCollector:
    """Collects and aggregates business metrics from technical metrics."""
    
    def __init__(
        self,
        expert_engine: ExpertEngine | None = None,
        confidence_tracker: ConfidenceMetricsTracker | None = None,
        storage_path: Path | None = None
    )
    
    async def collect_metrics() -> BusinessMetricsData
    """Collect current business metrics from all sources."""
    
    def aggregate_adoption_metrics() -> AdoptionMetrics
    """Aggregate adoption metrics (usage, frequency, popularity)."""
    
    def calculate_effectiveness_metrics() -> EffectivenessMetrics
    """Calculate effectiveness metrics (quality improvements, bug prevention)."""
    
    def calculate_roi_metrics() -> ROIMetrics
    """Calculate ROI metrics (time savings, costs, ROI)."""
    
    async def save_metrics(metrics: BusinessMetricsData) -> None
    """Save metrics to storage."""
    
    def load_historical_metrics(
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[BusinessMetricsData]
    """Load historical metrics for date range."""
```

### MetricsStorage API

#### Class: MetricsStorage
```python
class MetricsStorage:
    """File-based storage for business metrics."""
    
    def __init__(self, storage_path: Path)
    
    def save_metrics(metrics: BusinessMetricsData) -> None
    """Save metrics to JSON file."""
    
    def load_current_metrics() -> BusinessMetricsData | None
    """Load current metrics snapshot."""
    
    def load_historical_metrics(
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[BusinessMetricsData]
    """Load historical metrics for date range."""
    
    def query_metrics(
        expert_id: str | None = None,
        domain: str | None = None,
        agent_id: str | None = None
    ) -> list[BusinessMetricsData]
    """Query metrics by filters."""
```

### ReportGenerator API

#### Class: ReportGenerator
```python
class ReportGenerator:
    """Generate human-readable reports from metrics."""
    
    def __init__(self, storage: MetricsStorage)
    
    def generate_weekly_report(
        start_date: datetime,
        end_date: datetime
    ) -> WeeklyReport
    """Generate weekly summary report."""
    
    def generate_roi_report(
        start_date: datetime,
        end_date: datetime
    ) -> ROIReport
    """Generate ROI analysis report."""
    
    def generate_usage_report(
        start_date: datetime,
        end_date: datetime
    ) -> UsageReport
    """Generate expert usage distribution report."""
    
    def export_to_markdown(report: Report, output_path: Path) -> None
    """Export report to Markdown format."""
```

## Data Models

### BusinessMetricsData
```python
@dataclass
class BusinessMetricsData:
    """Complete business metrics snapshot."""
    timestamp: datetime
    adoption_metrics: AdoptionMetrics
    effectiveness_metrics: EffectivenessMetrics
    quality_metrics: QualityMetrics
    roi_metrics: ROIMetrics
    operational_metrics: OperationalMetrics
```

### AdoptionMetrics
```python
@dataclass
class AdoptionMetrics:
    """Adoption and usage metrics."""
    total_consultations: int
    consultations_per_workflow: float
    consultations_per_day: float
    expert_usage_by_id: dict[str, int]  # expert_id -> count
    domain_usage: dict[str, int]  # domain -> count
    agent_usage: dict[str, int]  # agent_id -> count
    workflow_usage_percentage: float  # % of workflows using experts
```

### EffectivenessMetrics
```python
@dataclass
class CodeQualityImprovement:
    """Single code quality improvement record."""
    consultation_id: str
    before_score: float
    after_score: float
    improvement_percentage: float
    expert_id: str
    domain: str

@dataclass
class EffectivenessMetrics:
    """Effectiveness and impact metrics."""
    code_quality_improvements: list[CodeQualityImprovement]
    avg_quality_improvement: float
    bug_prevention_rate: float  # bugs prevented / total consultations
    avg_time_savings_minutes: float
    total_bugs_prevented: int
```

### QualityMetrics
```python
@dataclass
class QualityMetrics:
    """Quality and performance metrics."""
    avg_confidence: float
    confidence_trend: list[float]  # Last 30 days
    avg_agreement_level: float
    rag_quality_score: float
    cache_hit_rate: float
    avg_latency_ms: float
```

### ROIMetrics
```python
@dataclass
class ROIMetrics:
    """ROI and business value metrics."""
    total_consultations: int
    estimated_time_saved_hours: float
    estimated_cost_per_consultation: float  # Infrastructure cost
    estimated_value_per_consultation: float  # Time saved value
    total_cost: float
    total_value: float
    roi_percentage: float  # (value - cost) / cost * 100
    roi_per_consultation: float
```

### OperationalMetrics
```python
@dataclass
class OperationalMetrics:
    """System health and operational metrics."""
    cache_hit_rate: float
    context7_hit_rate: float
    local_kb_hit_rate: float
    avg_latency_ms: float
    error_rate: float
    knowledge_base_size: int  # Number of knowledge chunks
```

## Report Models

### WeeklyReport
```python
@dataclass
class WeeklyReport:
    """Weekly summary report."""
    period_start: datetime
    period_end: datetime
    total_consultations: int
    top_experts: list[tuple[str, int]]  # (expert_id, count)
    top_domains: list[tuple[str, int]]  # (domain, count)
    avg_confidence: float
    confidence_trend: str  # "increasing", "decreasing", "stable"
    code_quality_improvements: int
    estimated_time_saved_hours: float
    roi_percentage: float
```

### ROIReport
```python
@dataclass
class ROIReport:
    """ROI analysis report."""
    period_start: datetime
    period_end: datetime
    total_consultations: int
    total_cost: float
    total_value: float
    roi_percentage: float
    roi_per_consultation: float
    breakdown_by_expert: dict[str, ROIMetrics]  # expert_id -> ROI
    breakdown_by_domain: dict[str, ROIMetrics]  # domain -> ROI
```

### UsageReport
```python
@dataclass
class UsageReport:
    """Expert usage distribution report."""
    period_start: datetime
    period_end: datetime
    expert_distribution: dict[str, int]  # expert_id -> count
    domain_distribution: dict[str, int]  # domain -> count
    agent_distribution: dict[str, int]  # agent_id -> count
    workflow_usage_percentage: float
    most_used_expert: str
    least_used_expert: str
```

## Integration Points

### With ExpertEngine
- Read `ExpertEngine.get_metrics()` for operational metrics
- Track consultation counts from `ExpertEngine.metrics.expert_consultations`

### With ConfidenceMetricsTracker
- Read confidence metrics from tracker
- Calculate trends from historical confidence data

### With Reviewer Agent
- Hook into code quality scoring
- Store before/after scores for correlation

### With WorkflowExecutor
- Track which workflows use experts
- Track workflow outcomes

## Configuration

### BusinessMetricsConfig
```python
@dataclass
class BusinessMetricsConfig:
    """Configuration for business metrics collection."""
    enabled: bool = True
    storage_path: Path = Path(".tapps-agents/metrics")
    auto_collect: bool = True  # Auto-collect on expert consultation
    report_generation: bool = True
    weekly_report_enabled: bool = True
    roi_calculation_enabled: bool = True
    time_savings_per_consultation_minutes: float = 15.0  # Estimated
    cost_per_consultation: float = 0.01  # Infrastructure cost
```
