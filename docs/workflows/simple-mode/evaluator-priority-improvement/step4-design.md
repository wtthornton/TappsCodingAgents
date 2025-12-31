# Step 4: Component Design - Evaluator Agent Priority System Improvement

**Date:** January 16, 2025  
**Workflow:** Simple Mode *build  
**Agent:** Designer  
**Stage:** Component Design Specifications

---

## Component Design Specifications

This document provides detailed specifications for each component in the priority evaluation system.

---

## 1. PriorityEvaluator Class

### Class Specification

**File:** `tapps_agents/agents/evaluator/priority_evaluator.py`

**Class Definition:**
```python
class PriorityEvaluator:
    """
    Objective priority evaluation engine for recommendations.
    
    Evaluates recommendations using multiple objective factors to produce
    consistent, reproducible priority assignments.
    """
    
    def __init__(
        self,
        config: PriorityConfig | None = None,
        project_root: Path | None = None
    ):
        """
        Initialize priority evaluator.
        
        Args:
            config: Priority evaluation configuration
            project_root: Project root directory for history tracking
        """
    
    def evaluate(
        self,
        recommendation: dict[str, Any],
        quality_data: dict[str, Any] | None = None,
        workflow_data: dict[str, Any] | None = None,
        usage_data: dict[str, Any] | None = None
    ) -> PriorityResult:
        """
        Evaluate recommendation priority.
        
        Args:
            recommendation: Recommendation dictionary with description, type, etc.
            quality_data: Quality analysis data (from QualityAnalyzer)
            workflow_data: Workflow analysis data (from WorkflowAnalyzer)
            usage_data: Usage analysis data (from UsageAnalyzer)
        
        Returns:
            PriorityResult with priority, score, factors, and rationale
        """
```

**Data Structures:**

```python
@dataclass
class PriorityResult:
    """Result of priority evaluation."""
    priority: str  # "critical", "high", "medium", "low"
    score: float  # 0.0-10.0
    factors: dict[str, float]  # Factor scores
    rationale: str  # Explanation of priority assignment
    recommendation_id: str | None = None  # Optional recommendation ID

@dataclass
class PriorityConfig:
    """Configuration for priority evaluation."""
    weights: dict[str, float]  # Factor weights (must sum to 1.0)
    thresholds: dict[str, float]  # Priority thresholds
    enable_history: bool = True  # Enable historical tracking
    project_root: Path | None = None  # Project root for history storage
```

---

## 2. FactorExtractor Class

### Class Specification

**File:** `tapps_agents/agents/evaluator/priority_evaluator.py` (nested class)

**Class Definition:**
```python
class FactorExtractor:
    """
    Extracts objective factors from recommendations and data sources.
    
    Analyzes recommendation descriptions, quality data, workflow data,
    and usage data to extract objective metrics for priority evaluation.
    """
    
    # Keyword patterns for factor extraction
    IMPACT_SEVERITY_KEYWORDS = {
        "security": 10,
        "vulnerability": 10,
        "breach": 10,
        "data loss": 9,
        "corruption": 9,
        "failure": 8,
        "broken": 7,
        "error": 6,
        "issue": 5,
        "improvement": 3,
        "enhancement": 2,
        "cosmetic": 1,
    }
    
    EFFORT_KEYWORDS = {
        "quick fix": 1,
        "simple": 2,
        "easy": 2,
        "minor": 3,
        "moderate": 4,
        "complex": 6,
        "refactor": 7,
        "major": 8,
        "rewrite": 9,
        "architectural": 10,
    }
    
    RISK_KEYWORDS = {
        "outage": 10,
        "downtime": 9,
        "security breach": 9,
        "data corruption": 8,
        "vulnerability": 9,
        "injection": 9,
        "xss": 8,
        "csrf": 8,
        "frustration": 6,
        "confusion": 4,
        "minor": 2,
    }
    
    def extract(
        self,
        recommendation: dict[str, Any],
        quality_data: dict[str, Any] | None = None,
        workflow_data: dict[str, Any] | None = None,
        usage_data: dict[str, Any] | None = None
    ) -> dict[str, float]:
        """
        Extract objective factors from recommendation.
        
        Returns dict with factor scores (0-10):
        {
            "impact_severity": float,
            "effort_complexity": float,
            "risk_level": float,
            "user_impact": float,
            "business_value": float,
            "code_quality_impact": float
        }
        """
```

### Factor Extraction Logic

#### Impact Severity (0-10)

**Sources:**
1. Description keywords (weight: 0.6)
2. Quality scores (weight: 0.3)
3. Workflow deviations (weight: 0.1)

**Algorithm:**
```python
def extract_impact_severity(
    description: str,
    quality_data: dict | None,
    workflow_data: dict | None
) -> float:
    score = 5.0  # Default: medium
    
    # Keyword matching (0.6 weight)
    keyword_score = match_keywords(description, IMPACT_SEVERITY_KEYWORDS)
    score = score * 0.4 + keyword_score * 0.6
    
    # Quality score analysis (0.3 weight)
    if quality_data:
        overall_score = quality_data.get("scores", {}).get("overall", 70.0)
        if overall_score < 50:
            score = max(score, 8.0)  # Low quality = high severity
        elif overall_score < 60:
            score = max(score, 6.0)
    
    # Workflow deviations (0.1 weight)
    if workflow_data:
        deviations = workflow_data.get("deviations", [])
        if deviations:
            high_impact_deviations = [d for d in deviations if d.get("impact") == "high"]
            if high_impact_deviations:
                score = max(score, 7.0)
    
    return clamp(score, 0.0, 10.0)
```

#### Effort Complexity (0-10, inverted)

**Sources:**
1. Description keywords (weight: 0.7)
2. Code metrics (weight: 0.3)

**Algorithm:**
```python
def extract_effort_complexity(
    description: str,
    quality_data: dict | None
) -> float:
    score = 5.0  # Default: medium
    
    # Keyword matching (0.7 weight)
    keyword_score = match_keywords(description, EFFORT_KEYWORDS)
    score = score * 0.3 + keyword_score * 0.7
    
    # Code metrics (0.3 weight)
    # Note: Actual code metrics would require codebase analysis
    # For now, use description hints
    
    return clamp(score, 0.0, 10.0)
```

#### Risk Level (0-10)

**Sources:**
1. Description keywords (weight: 0.8)
2. Security indicators (weight: 0.2)

**Algorithm:**
```python
def extract_risk_level(
    description: str,
    quality_data: dict | None
) -> float:
    score = 5.0  # Default: medium
    
    # Keyword matching (0.8 weight)
    keyword_score = match_keywords(description, RISK_KEYWORDS)
    score = score * 0.2 + keyword_score * 0.8
    
    # Security indicators (0.2 weight)
    security_keywords = ["security", "vulnerability", "breach", "injection", "xss", "csrf"]
    if any(kw in description.lower() for kw in security_keywords):
        score = max(score, 8.0)
    
    return clamp(score, 0.0, 10.0)
```

#### User Impact (0-10)

**Sources:**
1. Usage data (weight: 0.6)
2. Workflow data (weight: 0.4)

**Algorithm:**
```python
def extract_user_impact(
    usage_data: dict | None,
    workflow_data: dict | None
) -> float:
    score = 5.0  # Default: medium
    
    if usage_data:
        stats = usage_data.get("statistics", {})
        total_commands = stats.get("total_commands", 0)
        
        # High usage = high user impact
        if total_commands > 1000:
            score = 8.0
        elif total_commands > 500:
            score = 6.0
        elif total_commands > 100:
            score = 4.0
    
    if workflow_data:
        step_analysis = workflow_data.get("step_analysis", {})
        completion_rate = step_analysis.get("completion_rate", 1.0)
        
        # Low completion rate = high user impact (workflow broken)
        if completion_rate < 0.5:
            score = max(score, 8.0)
        elif completion_rate < 0.8:
            score = max(score, 6.0)
    
    return clamp(score, 0.0, 10.0)
```

#### Business Value (0-10)

**Sources:**
1. Description keywords (weight: 1.0)

**Algorithm:**
```python
def extract_business_value(description: str) -> float:
    score = 5.0  # Default: medium
    
    business_keywords = {
        "revenue": 10,
        "customer": 8,
        "competitive": 8,
        "adoption": 7,
        "productivity": 6,
        "efficiency": 5,
        "maintainability": 4,
        "technical debt": 3,
    }
    
    keyword_score = match_keywords(description, business_keywords)
    score = score * 0.3 + keyword_score * 0.7
    
    return clamp(score, 0.0, 10.0)
```

#### Code Quality Impact (0-10)

**Sources:**
1. Quality data (weight: 0.8)
2. Description keywords (weight: 0.2)

**Algorithm:**
```python
def extract_code_quality_impact(
    description: str,
    quality_data: dict | None
) -> float:
    score = 5.0  # Default: medium
    
    if quality_data:
        scores = quality_data.get("scores", {})
        overall = scores.get("overall", 70.0)
        
        # Low quality = high improvement potential
        if overall < 50:
            score = 8.0  # High impact potential
        elif overall < 60:
            score = 6.0
        elif overall < 70:
            score = 4.0
    
    quality_keywords = {
        "test coverage": 7,
        "maintainability": 6,
        "technical debt": 5,
        "code quality": 4,
        "refactor": 6,
    }
    
    keyword_score = match_keywords(description, quality_keywords)
    score = max(score, keyword_score * 0.2)
    
    return clamp(score, 0.0, 10.0)
```

---

## 3. ScoreCalculator Class

### Class Specification

**File:** `tapps_agents/agents/evaluator/priority_evaluator.py` (nested class)

**Class Definition:**
```python
class ScoreCalculator:
    """
    Calculates priority scores from factor scores using weighted formula.
    """
    
    DEFAULT_WEIGHTS = {
        "impact_severity": 0.25,
        "effort_complexity": 0.20,  # Inverted: easier = higher priority
        "risk_level": 0.20,
        "user_impact": 0.15,
        "business_value": 0.10,
        "code_quality_impact": 0.10
    }
    
    def calculate(
        self,
        factors: dict[str, float],
        weights: dict[str, float] | None = None
    ) -> float:
        """
        Calculate priority score from factors.
        
        Args:
            factors: Factor scores (0-10)
            weights: Factor weights (default: DEFAULT_WEIGHTS)
        
        Returns:
            Priority score (0-10)
        """
        if weights is None:
            weights = self.DEFAULT_WEIGHTS
        
        # Validate weights sum to 1.0
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        # Calculate weighted score
        # Note: effort_complexity is inverted (lower effort = higher priority)
        score = (
            factors.get("impact_severity", 5.0) * weights.get("impact_severity", 0.25) +
            (10.0 - factors.get("effort_complexity", 5.0)) * weights.get("effort_complexity", 0.20) +
            factors.get("risk_level", 5.0) * weights.get("risk_level", 0.20) +
            factors.get("user_impact", 5.0) * weights.get("user_impact", 0.15) +
            factors.get("business_value", 5.0) * weights.get("business_value", 0.10) +
            factors.get("code_quality_impact", 5.0) * weights.get("code_quality_impact", 0.10)
        )
        
        return clamp(score, 0.0, 10.0)
```

---

## 4. PriorityClassifier Class

### Class Specification

**File:** `tapps_agents/agents/evaluator/priority_evaluator.py` (nested class)

**Class Definition:**
```python
class PriorityClassifier:
    """
    Classifies priority scores into priority levels.
    """
    
    DEFAULT_THRESHOLDS = {
        "critical": 8.5,
        "high": 7.0,
        "medium": 5.0,
        "low": 0.0
    }
    
    PRIORITY_RATIONALE = {
        "critical": "High impact, low effort, or high risk issue requiring immediate attention",
        "high": "Significant impact or moderate risk issue that should be addressed soon",
        "medium": "Moderate impact issue that can be addressed when resources allow",
        "low": "Low impact improvement or nice-to-have feature"
    }
    
    def classify(
        self,
        score: float,
        thresholds: dict[str, float] | None = None
    ) -> tuple[str, str]:
        """
        Classify priority score into priority level.
        
        Args:
            score: Priority score (0-10)
            thresholds: Priority thresholds (default: DEFAULT_THRESHOLDS)
        
        Returns:
            Tuple of (priority_level, rationale)
        """
        if thresholds is None:
            thresholds = self.DEFAULT_THRESHOLDS
        
        # Classify based on thresholds
        if score >= thresholds.get("critical", 8.5):
            priority = "critical"
        elif score >= thresholds.get("high", 7.0):
            priority = "high"
        elif score >= thresholds.get("medium", 5.0):
            priority = "medium"
        else:
            priority = "low"
        
        rationale = self.PRIORITY_RATIONALE.get(priority, "Unknown priority")
        
        return priority, rationale
```

---

## 5. HistoryTracker Class

### Class Specification

**File:** `tapps_agents/agents/evaluator/history_tracker.py`

**Class Definition:**
```python
class HistoryTracker:
    """
    Tracks priority evaluation history for trend analysis.
    """
    
    def __init__(self, project_root: Path | None = None):
        """
        Initialize history tracker.
        
        Args:
            project_root: Project root directory for history storage
        """
        self.project_root = project_root or Path.cwd()
        self.history_dir = self.project_root / ".tapps-agents" / "evaluations" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def track(
        self,
        evaluation_id: str,
        recommendations: list[PriorityResult],
        metadata: dict[str, Any] | None = None
    ) -> Path:
        """
        Store evaluation results in history.
        
        Args:
            evaluation_id: Unique evaluation identifier
            recommendations: List of priority evaluation results
            metadata: Additional metadata (evaluation date, etc.)
        
        Returns:
            Path to stored history file
        """
        # Calculate priority distribution
        distribution = {
            "critical": sum(1 for r in recommendations if r.priority == "critical"),
            "high": sum(1 for r in recommendations if r.priority == "high"),
            "medium": sum(1 for r in recommendations if r.priority == "medium"),
            "low": sum(1 for r in recommendations if r.priority == "low"),
        }
        
        # Calculate average score
        avg_score = sum(r.score for r in recommendations) / len(recommendations) if recommendations else 0.0
        
        # Build history record
        history_record = {
            "evaluation_id": evaluation_id,
            "evaluation_date": (metadata or {}).get("evaluation_date", datetime.now().isoformat()),
            "total_recommendations": len(recommendations),
            "priority_distribution": distribution,
            "average_score": avg_score,
            "recommendations": [
                {
                    "id": r.recommendation_id or f"rec-{i}",
                    "description": metadata.get("recommendations", [{}])[i].get("description", ""),
                    "priority": r.priority,
                    "score": r.score,
                    "factors": r.factors,
                    "rationale": r.rationale
                }
                for i, r in enumerate(recommendations)
            ]
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"evaluation-{timestamp}.json"
        file_path = self.history_dir / filename
        
        file_path.write_text(
            json.dumps(history_record, indent=2),
            encoding="utf-8"
        )
        
        return file_path
    
    def get_trends(
        self,
        days: int = 30
    ) -> dict[str, Any]:
        """
        Get priority distribution trends over time.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with trend data
        """
        # Load historical files from last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        history_files = []
        
        for file_path in self.history_dir.glob("evaluation-*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                eval_date = datetime.fromisoformat(data.get("evaluation_date", ""))
                if eval_date >= cutoff_date:
                    history_files.append(data)
            except Exception:
                continue
        
        # Sort by date
        history_files.sort(key=lambda x: x.get("evaluation_date", ""))
        
        # Extract trends
        critical_trend = [h["priority_distribution"]["critical"] for h in history_files]
        high_trend = [h["priority_distribution"]["high"] for h in history_files]
        medium_trend = [h["priority_distribution"]["medium"] for h in history_files]
        low_trend = [h["priority_distribution"]["low"] for h in history_files]
        avg_score_trend = [h["average_score"] for h in history_files]
        
        # Calculate improvement metrics
        if len(history_files) >= 2:
            first = history_files[0]
            last = history_files[-1]
            
            critical_change = (
                (last["priority_distribution"]["critical"] - first["priority_distribution"]["critical"]) /
                max(first["priority_distribution"]["critical"], 1) * 100
            )
            high_change = (
                (last["priority_distribution"]["high"] - first["priority_distribution"]["high"]) /
                max(first["priority_distribution"]["high"], 1) * 100
            )
            avg_score_change = (
                (last["average_score"] - first["average_score"]) /
                max(first["average_score"], 1) * 100
            )
        else:
            critical_change = 0.0
            high_change = 0.0
            avg_score_change = 0.0
        
        return {
            "critical_trend": critical_trend,
            "high_trend": high_trend,
            "medium_trend": medium_trend,
            "low_trend": low_trend,
            "average_score_trend": avg_score_trend,
            "improvement_metrics": {
                "critical_change_percent": critical_change,
                "high_change_percent": high_change,
                "average_score_change_percent": avg_score_change,
                "trend_direction": "improving" if critical_change < 0 and high_change < 0 else "declining"
            }
        }
```

---

## 6. ReportGenerator Integration

### Changes to ReportGenerator

**File:** `tapps_agents/agents/evaluator/report_generator.py`

**Method Changes:**

```python
def prioritize_recommendations(
    self,
    recommendations: list[dict],
    quality_data: dict[str, Any] | None = None,
    workflow_data: dict[str, Any] | None = None,
    usage_data: dict[str, Any] | None = None
) -> dict[str, list[dict]]:
    """
    Prioritize recommendations using objective evaluation.
    
    Uses PriorityEvaluator for consistent, independent priority assignment.
    """
    evaluator = PriorityEvaluator(config=self.config)
    
    prioritized_results = []
    for rec in recommendations:
        result = evaluator.evaluate(
            recommendation=rec,
            quality_data=quality_data,
            workflow_data=workflow_data,
            usage_data=usage_data
        )
        prioritized_results.append({
            **rec,
            "priority": result.priority,
            "priority_score": result.score,
            "priority_factors": result.factors,
            "priority_rationale": result.rationale
        })
    
    # Group by priority
    priority_1 = [r for r in prioritized_results if r["priority"] == "critical"]
    priority_2 = [r for r in prioritized_results if r["priority"] == "high"]
    priority_3 = [r for r in prioritized_results if r["priority"] == "medium"]
    priority_4 = [r for r in prioritized_results if r["priority"] == "low"]
    
    return {
        "priority_1": priority_1,
        "priority_2": priority_2,
        "priority_3": priority_3,
        "priority_4": priority_4,
    }
```

---

## Configuration Schema

### Config Structure

**File:** `.tapps-agents/config.yaml`

```yaml
evaluator:
  priority_evaluation:
    enabled: true
    use_historical_tracking: true
    
    # Factor weights (must sum to 1.0)
    weights:
      impact_severity: 0.25
      effort_complexity: 0.20
      risk_level: 0.20
      user_impact: 0.15
      business_value: 0.10
      code_quality_impact: 0.10
    
    # Priority thresholds
    thresholds:
      critical: 8.5
      high: 7.0
      medium: 5.0
      low: 0.0
    
    # Historical tracking
    history:
      enabled: true
      retention_days: 90
      trend_analysis_days: 30
```

---

## Summary

This design provides:

1. **Modular Components:** Each component has clear responsibilities
2. **Objective Evaluation:** Factors extracted independently from data
3. **Configurable System:** Weights and thresholds are configurable
4. **Historical Tracking:** Trend analysis and improvement measurement
5. **Consistent Results:** Deterministic priority assignments
6. **Extensible Design:** Easy to add new factors or modify scoring
