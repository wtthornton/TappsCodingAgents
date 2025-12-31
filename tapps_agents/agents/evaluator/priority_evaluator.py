"""
Priority Evaluator - Objective priority evaluation engine for recommendations.

Provides consistent, independent, and reproducible priority classification
for fixes and enhancements based on multiple objective factors.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ...core.config import ProjectConfig, load_config


@dataclass
class PriorityResult:
    """Result of priority evaluation."""
    priority: str  # "critical", "high", "medium", "low"
    score: float  # 0.0-10.0
    factors: dict[str, float]  # Factor scores
    rationale: str  # Explanation of priority assignment
    recommendation_id: str | None = None  # Optional recommendation ID


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
        
        Args:
            recommendation: Recommendation dictionary
            quality_data: Quality analysis data
            workflow_data: Workflow analysis data
            usage_data: Usage analysis data
        
        Returns:
            Dictionary with factor scores (0-10)
        """
        description = (recommendation.get("description") or recommendation.get("recommendation") or "").lower()
        
        return {
            "impact_severity": self._extract_impact_severity(description, quality_data, workflow_data),
            "effort_complexity": self._extract_effort_complexity(description, quality_data),
            "risk_level": self._extract_risk_level(description, quality_data),
            "user_impact": self._extract_user_impact(usage_data, workflow_data),
            "business_value": self._extract_business_value(description),
            "code_quality_impact": self._extract_code_quality_impact(description, quality_data),
        }
    
    def _extract_impact_severity(
        self,
        description: str,
        quality_data: dict[str, Any] | None,
        workflow_data: dict[str, Any] | None
    ) -> float:
        """Extract impact severity factor (0-10)."""
        score = 5.0  # Default: medium
        
        # Keyword matching (0.6 weight)
        keyword_score = self._match_keywords(description, self.IMPACT_SEVERITY_KEYWORDS)
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
        
        return self._clamp(score, 0.0, 10.0)
    
    def _extract_effort_complexity(
        self,
        description: str,
        quality_data: dict[str, Any] | None
    ) -> float:
        """Extract effort complexity factor (0-10, inverted: lower = higher priority)."""
        score = 5.0  # Default: medium
        
        # Keyword matching (0.7 weight)
        keyword_score = self._match_keywords(description, self.EFFORT_KEYWORDS)
        score = score * 0.3 + keyword_score * 0.7
        
        return self._clamp(score, 0.0, 10.0)
    
    def _extract_risk_level(
        self,
        description: str,
        quality_data: dict[str, Any] | None
    ) -> float:
        """Extract risk level factor (0-10)."""
        score = 5.0  # Default: medium
        
        # Keyword matching (0.8 weight)
        keyword_score = self._match_keywords(description, self.RISK_KEYWORDS)
        score = score * 0.2 + keyword_score * 0.8
        
        # Security indicators (0.2 weight)
        security_keywords = ["security", "vulnerability", "breach", "injection", "xss", "csrf"]
        if any(kw in description for kw in security_keywords):
            score = max(score, 8.0)
        
        return self._clamp(score, 0.0, 10.0)
    
    def _extract_user_impact(
        self,
        usage_data: dict[str, Any] | None,
        workflow_data: dict[str, Any] | None
    ) -> float:
        """Extract user impact factor (0-10)."""
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
        
        return self._clamp(score, 0.0, 10.0)
    
    def _extract_business_value(self, description: str) -> float:
        """Extract business value factor (0-10)."""
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
        
        keyword_score = self._match_keywords(description, business_keywords)
        score = score * 0.3 + keyword_score * 0.7
        
        return self._clamp(score, 0.0, 10.0)
    
    def _extract_code_quality_impact(
        self,
        description: str,
        quality_data: dict[str, Any] | None
    ) -> float:
        """Extract code quality impact factor (0-10)."""
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
        
        keyword_score = self._match_keywords(description, quality_keywords)
        score = max(score, keyword_score * 0.2)
        
        return self._clamp(score, 0.0, 10.0)
    
    def _match_keywords(self, text: str, keywords: dict[str, float]) -> float:
        """Match keywords in text and return highest score found."""
        if not text:
            return 5.0
        
        max_score = 0.0
        for keyword, score in keywords.items():
            if keyword in text:
                max_score = max(max_score, score)
        
        return max_score if max_score > 0 else 5.0
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range."""
        return max(min_val, min(max_val, value))


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
        
        return self._clamp(score, 0.0, 10.0)
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range."""
        return max(min_val, min(max_val, value))


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


class PriorityEvaluator:
    """
    Objective priority evaluation engine for recommendations.
    
    Evaluates recommendations using multiple objective factors to produce
    consistent, reproducible priority assignments.
    """
    
    def __init__(
        self,
        config: ProjectConfig | None = None,
        project_root: Path | None = None
    ):
        """
        Initialize priority evaluator.
        
        Args:
            config: Project configuration
            project_root: Project root directory for history tracking
        """
        if config is None:
            config = load_config()
        self.config = config
        self.project_root = project_root or Path.cwd()
        
        # Initialize components
        self.factor_extractor = FactorExtractor()
        self.score_calculator = ScoreCalculator()
        self.priority_classifier = PriorityClassifier()
        
        # Get configuration (will be added to config later)
        self.weights = self._get_weights()
        self.thresholds = self._get_thresholds()
        self.enable_history = self._get_enable_history()
    
    def _get_weights(self) -> dict[str, float]:
        """Get factor weights from config or use defaults."""
        # TODO: Add to config.yaml structure
        # For now, use defaults
        return ScoreCalculator.DEFAULT_WEIGHTS
    
    def _get_thresholds(self) -> dict[str, float]:
        """Get priority thresholds from config or use defaults."""
        # TODO: Add to config.yaml structure
        # For now, use defaults
        return PriorityClassifier.DEFAULT_THRESHOLDS
    
    def _get_enable_history(self) -> bool:
        """Get enable history flag from config or use defaults."""
        # TODO: Add to config.yaml structure
        # For now, use defaults
        return True
    
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
        # Extract factors
        factors = self.factor_extractor.extract(
            recommendation=recommendation,
            quality_data=quality_data,
            workflow_data=workflow_data,
            usage_data=usage_data
        )
        
        # Calculate score
        score = self.score_calculator.calculate(factors=factors, weights=self.weights)
        
        # Classify priority
        priority, rationale = self.priority_classifier.classify(score=score, thresholds=self.thresholds)
        
        return PriorityResult(
            priority=priority,
            score=score,
            factors=factors,
            rationale=rationale,
            recommendation_id=recommendation.get("id")
        )


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
                    "description": (metadata or {}).get("recommendations", [{}])[i].get("description", "") if i < len((metadata or {}).get("recommendations", [])) else "",
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
                eval_date_str = data.get("evaluation_date", "")
                if eval_date_str:
                    eval_date = datetime.fromisoformat(eval_date_str.replace("Z", "+00:00"))
                    if eval_date >= cutoff_date:
                        history_files.append(data)
            except Exception:
                continue
        
        # Sort by date
        history_files.sort(key=lambda x: x.get("evaluation_date", ""))
        
        if not history_files:
            return {
                "critical_trend": [],
                "high_trend": [],
                "medium_trend": [],
                "low_trend": [],
                "average_score_trend": [],
                "improvement_metrics": {
                    "critical_change_percent": 0.0,
                    "high_change_percent": 0.0,
                    "average_score_change_percent": 0.0,
                    "trend_direction": "stable"
                }
            }
        
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
        
        trend_direction = "improving" if critical_change < 0 and high_change < 0 else ("declining" if critical_change > 0 or high_change > 0 else "stable")
        
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
                "trend_direction": trend_direction
            }
        }
