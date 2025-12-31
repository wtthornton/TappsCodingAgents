# Step 3: Architecture Design - Business Metrics Collection

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Business Metrics System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ ExpertEngine     │      │ ConfidenceMetrics│            │
│  │ Metrics          │      │ Tracker          │            │
│  │ (Existing)       │      │ (Existing)       │            │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                          │                      │
│           └──────────┬───────────────┘                      │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │ BusinessMetrics      │                          │
│           │ Collector            │                          │
│           │                      │                          │
│           │ - Aggregate metrics │                          │
│           │ - Calculate ROI      │                          │
│           │ - Generate reports   │                          │
│           └──────────┬───────────┘                          │
│                      │                                      │
│           ┌──────────▼──────────┐                          │
│           │ MetricsStorage       │                          │
│           │ (JSON file-based)    │                          │
│           │                      │                          │
│           │ - Store metrics      │                          │
│           │ - Query metrics      │                          │
│           │ - Generate reports   │                          │
│           └──────────────────────┘                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Metrics Collection**
   - `ExpertEngine` collects technical metrics → `ExpertEngineMetrics`
   - `ExpertRegistry` tracks confidence → `ConfidenceMetricsTracker`
   - `BusinessMetricsCollector` aggregates both sources

2. **Storage**
   - Business metrics stored in `.tapps-agents/metrics/business_metrics.json`
   - Weekly reports in `.tapps-agents/metrics/reports/`
   - Correlation data in `.tapps-agents/metrics/correlations.json`

3. **Reporting**
   - On-demand report generation
   - Weekly automated reports (optional)
   - JSON and Markdown formats

### Key Components

#### 1. BusinessMetricsCollector
**Purpose:** Main class for collecting and aggregating business metrics

**Responsibilities:**
- Aggregate data from `ExpertEngineMetrics` and `ConfidenceMetricsTracker`
- Calculate business metrics (usage, popularity, ROI)
- Generate reports
- Store metrics to file

**Location:** `tapps_agents/experts/business_metrics.py`

#### 2. BusinessMetricsData
**Purpose:** Data model for business metrics

**Fields:**
- `timestamp`: When metrics were collected
- `adoption_metrics`: Usage statistics
- `effectiveness_metrics`: Code quality improvements
- `quality_metrics`: Confidence and agreement levels
- `roi_metrics`: ROI calculations
- `operational_metrics`: System health

**Location:** `tapps_agents/experts/business_metrics.py`

#### 3. MetricsStorage
**Purpose:** File-based storage for metrics

**Responsibilities:**
- Save metrics to JSON files
- Load historical metrics
- Query metrics by date range, expert, domain
- Generate report files

**Location:** `tapps_agents/experts/metrics_storage.py`

#### 4. ReportGenerator
**Purpose:** Generate human-readable reports

**Responsibilities:**
- Generate weekly summary reports
- Generate ROI reports
- Generate usage distribution reports
- Export to Markdown format

**Location:** `tapps_agents/experts/report_generator.py`

### Integration Points

1. **ExpertEngine Integration**
   - Hook into `ExpertEngine.get_metrics()` to collect technical metrics
   - Extend `ExpertEngineMetrics` with business context

2. **ConfidenceMetricsTracker Integration**
   - Read from `ConfidenceMetricsTracker` to get confidence data
   - Aggregate confidence trends

3. **Code Quality Integration**
   - Hook into reviewer agent to get code quality scores
   - Store before/after scores for correlation

4. **Workflow Integration**
   - Track which workflows use experts
   - Track workflow outcomes (bugs, quality scores)

### Data Models

#### BusinessMetricsData
```python
@dataclass
class BusinessMetricsData:
    timestamp: datetime
    adoption_metrics: AdoptionMetrics
    effectiveness_metrics: EffectivenessMetrics
    quality_metrics: QualityMetrics
    roi_metrics: ROIMetrics
    operational_metrics: OperationalMetrics
```

#### AdoptionMetrics
```python
@dataclass
class AdoptionMetrics:
    total_consultations: int
    consultations_per_workflow: float
    expert_usage_by_id: dict[str, int]
    domain_usage: dict[str, int]
    agent_usage: dict[str, int]
```

#### EffectivenessMetrics
```python
@dataclass
class EffectivenessMetrics:
    code_quality_improvements: list[CodeQualityImprovement]
    bug_prevention_rate: float
    avg_time_savings_minutes: float
```

#### ROIMetrics
```python
@dataclass
class ROIMetrics:
    total_consultations: int
    estimated_time_saved_hours: float
    estimated_cost_per_consultation: float
    estimated_value_per_consultation: float
    total_roi: float
```

### Storage Strategy

**File Structure:**
```
.tapps-agents/
├── metrics/
│   ├── business_metrics.json          # Current metrics snapshot
│   ├── business_metrics_history.json  # Historical metrics
│   ├── correlations.json              # Code quality correlations
│   └── reports/
│       ├── weekly_2025-12-31.json
│       ├── weekly_2025-12-31.md
│       ├── roi_2025-12-31.json
│       └── roi_2025-12-31.md
```

**JSON Format:**
- Human-readable with indentation
- Timestamp-based keys for historical data
- Easy to query and analyze

### Performance Considerations

- **Lazy Loading:** Load metrics only when needed
- **Incremental Updates:** Append to history instead of rewriting
- **Caching:** Cache aggregated metrics in memory
- **File Size:** Rotate old metrics files if they get too large

### Security Considerations

- **File Permissions:** Metrics files should be readable only by owner
- **No Sensitive Data:** Don't store user queries or code content
- **Local Only:** All storage is local, no network access

### Error Handling

- **Graceful Degradation:** If metrics collection fails, continue without it
- **File Locking:** Handle concurrent access to metrics files
- **Validation:** Validate metrics data before storing
