"""
Observability & Quality Improvement Loop

Collects metrics, identifies weak areas, and generates improvement proposals.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ConsultationMetrics:
    """Metrics for expert consultation."""

    expert_id: str
    domain: str
    confidence: float
    agreement_level: float | None = None
    rag_quality: float | None = None
    threshold_met: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Context7Metrics:
    """Metrics for Context7 KB."""

    hit_rate: float  # Cache hit rate (0.0-1.0)
    latency_ms: float  # Average latency in milliseconds
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RAGMetrics:
    """Metrics for RAG KB."""

    retrieval_hit_rate: float  # Retrieval hit rate (0.0-1.0)
    low_quality_queries: list[dict[str, Any]] = field(default_factory=list)
    total_queries: int = 0
    successful_retrievals: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WeakArea:
    """Identified weak area in knowledge base."""

    domain: str
    rag_quality: float
    low_quality_queries: list[str]
    priority: str  # high, medium, low
    suggested_improvements: list[str] = field(default_factory=list)


@dataclass
class KBImprovementProposal:
    """Proposal for KB improvement."""

    domain: str
    title: str
    description: str
    template: str
    priority: str
    estimated_impact: str


class ObservabilitySystem:
    """
    Observability and quality improvement system for Expert Engine.

    Collects metrics, identifies weak areas, and generates improvement proposals.
    """

    def __init__(self, project_root: Path):
        """
        Initialize Observability System.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.config_dir = project_root / ".tapps-agents"
        self.metrics_dir = self.config_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Metrics storage
        self.consultation_metrics: list[ConsultationMetrics] = []
        self.context7_metrics: list[Context7Metrics] = []
        self.rag_metrics: list[RAGMetrics] = []

    def record_consultation(
        self,
        expert_id: str,
        domain: str,
        confidence: float,
        agreement_level: float | None = None,
        rag_quality: float | None = None,
        threshold_met: bool = False,
    ):
        """Record expert consultation metrics."""
        metric = ConsultationMetrics(
            expert_id=expert_id,
            domain=domain,
            confidence=confidence,
            agreement_level=agreement_level,
            rag_quality=rag_quality,
            threshold_met=threshold_met,
        )
        self.consultation_metrics.append(metric)
        self._persist_metrics()

    def record_context7_metrics(
        self,
        hit_rate: float,
        latency_ms: float,
        total_requests: int,
        cache_hits: int,
        cache_misses: int,
    ):
        """Record Context7 KB metrics."""
        metric = Context7Metrics(
            hit_rate=hit_rate,
            latency_ms=latency_ms,
            total_requests=total_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
        )
        self.context7_metrics.append(metric)
        self._persist_metrics()

    def record_rag_metrics(
        self,
        retrieval_hit_rate: float,
        low_quality_queries: list[dict[str, Any]],
        total_queries: int,
        successful_retrievals: int,
    ):
        """Record RAG KB metrics."""
        metric = RAGMetrics(
            retrieval_hit_rate=retrieval_hit_rate,
            low_quality_queries=low_quality_queries,
            total_queries=total_queries,
            successful_retrievals=successful_retrievals,
        )
        self.rag_metrics.append(metric)
        self._persist_metrics()

    def identify_weak_areas(self, threshold: float = 0.5) -> list[WeakArea]:
        """
        Identify weak areas in knowledge base.

        Args:
            threshold: RAG quality threshold below which area is considered weak

        Returns:
            List of identified weak areas
        """
        weak_areas = []

        # Group consultation metrics by domain
        domain_metrics: dict[str, list[ConsultationMetrics]] = {}
        for metric in self.consultation_metrics:
            if metric.domain not in domain_metrics:
                domain_metrics[metric.domain] = []
            domain_metrics[metric.domain].append(metric)

        # Identify weak domains
        for domain, metrics in domain_metrics.items():
            # Calculate average RAG quality
            rag_qualities = [
                m.rag_quality for m in metrics if m.rag_quality is not None
            ]
            if not rag_qualities:
                continue

            avg_rag_quality = sum(rag_qualities) / len(rag_qualities)

            if avg_rag_quality < threshold:
                # Collect low-quality queries
                low_quality_queries = [
                    f"Query in {domain} (quality: {m.rag_quality})"
                    for m in metrics
                    if m.rag_quality is not None and m.rag_quality < threshold
                ]

                # Determine priority
                if avg_rag_quality < 0.3:
                    priority = "high"
                elif avg_rag_quality < 0.4:
                    priority = "medium"
                else:
                    priority = "low"

                weak_area = WeakArea(
                    domain=domain,
                    rag_quality=avg_rag_quality,
                    low_quality_queries=low_quality_queries[:10],  # Top 10
                    priority=priority,
                )
                weak_areas.append(weak_area)

        return weak_areas

    def generate_improvement_proposals(
        self, weak_areas: list[WeakArea]
    ) -> list[KBImprovementProposal]:
        """
        Generate KB improvement proposals for weak areas.

        Args:
            weak_areas: List of identified weak areas

        Returns:
            List of improvement proposals
        """
        proposals = []

        for area in weak_areas:
            # Generate proposal based on weak area
            proposal = KBImprovementProposal(
                domain=area.domain,
                title=f"Improve {area.domain} Knowledge Base",
                description=f"RAG quality is {area.rag_quality:.2f} (below threshold). "
                f"Found {len(area.low_quality_queries)} low-quality queries.",
                template=self._generate_template(area),
                priority=area.priority,
                estimated_impact="High" if area.priority == "high" else "Medium",
            )
            proposals.append(proposal)

        return proposals

    def _generate_template(self, area: WeakArea) -> str:
        """Generate KB addition template for weak area."""
        template = f"""# {area.domain.title()} Knowledge Base Improvement

## Overview
This template helps improve the {area.domain} knowledge base based on identified weak areas.

## Current Issues
- RAG Quality: {area.rag_quality:.2f}
- Low-quality queries detected: {len(area.low_quality_queries)}

## Suggested Additions

### 1. Overview Section
Add comprehensive overview covering:
- Key concepts
- Common use cases
- Best practices

### 2. Glossary
Add definitions for:
- Domain-specific terms
- Technical terminology
- Common abbreviations

### 3. Patterns & Examples
Add practical examples:
- Code examples
- Usage patterns
- Integration examples

### 4. Pitfalls & Solutions
Document common issues:
- Known pitfalls
- Troubleshooting guides
- Workarounds

## Next Steps
1. Review low-quality queries: {', '.join(area.low_quality_queries[:3])}
2. Add knowledge entries addressing these queries
3. Re-run quality assessment
"""
        return template

    def run_maintenance_job(self) -> dict[str, Any]:
        """
        Run scheduled KB maintenance job.

        Returns:
            Dictionary with maintenance results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "weak_areas_identified": 0,
            "proposals_generated": 0,
            "metrics_analyzed": len(self.consultation_metrics),
        }

        # Identify weak areas
        weak_areas = self.identify_weak_areas()
        results["weak_areas_identified"] = len(weak_areas)

        # Generate proposals
        proposals = self.generate_improvement_proposals(weak_areas)
        results["proposals_generated"] = len(proposals)

        # Save proposals
        proposals_file = self.metrics_dir / "improvement_proposals.json"
        proposals_data = [
            {
                "domain": p.domain,
                "title": p.title,
                "description": p.description,
                "template": p.template,
                "priority": p.priority,
                "estimated_impact": p.estimated_impact,
            }
            for p in proposals
        ]
        proposals_file.write_text(
            json.dumps(proposals_data, indent=2), encoding="utf-8"
        )

        # Save weak areas report
        weak_areas_file = self.metrics_dir / "weak_areas.json"
        weak_areas_data = [
            {
                "domain": w.domain,
                "rag_quality": w.rag_quality,
                "priority": w.priority,
                "low_quality_queries_count": len(w.low_quality_queries),
            }
            for w in weak_areas
        ]
        weak_areas_file.write_text(
            json.dumps(weak_areas_data, indent=2), encoding="utf-8"
        )

        return results

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of all metrics."""
        # Calculate averages
        avg_confidence = (
            sum(m.confidence for m in self.consultation_metrics)
            / len(self.consultation_metrics)
            if self.consultation_metrics
            else 0.0
        )

        avg_rag_quality = (
            sum(
                m.rag_quality
                for m in self.consultation_metrics
                if m.rag_quality is not None
            )
            / len([m for m in self.consultation_metrics if m.rag_quality is not None])
            if any(m.rag_quality is not None for m in self.consultation_metrics)
            else 0.0
        )

        avg_context7_hit_rate = (
            sum(m.hit_rate for m in self.context7_metrics) / len(self.context7_metrics)
            if self.context7_metrics
            else 0.0
        )

        avg_rag_hit_rate = (
            sum(m.retrieval_hit_rate for m in self.rag_metrics) / len(self.rag_metrics)
            if self.rag_metrics
            else 0.0
        )

        return {
            "consultation_metrics": {
                "total_consultations": len(self.consultation_metrics),
                "average_confidence": avg_confidence,
                "average_rag_quality": avg_rag_quality,
            },
            "context7_metrics": {
                "total_records": len(self.context7_metrics),
                "average_hit_rate": avg_context7_hit_rate,
            },
            "rag_metrics": {
                "total_records": len(self.rag_metrics),
                "average_hit_rate": avg_rag_hit_rate,
            },
        }

    def _persist_metrics(self):
        """Persist metrics to disk."""
        # Save consultation metrics
        consultation_file = self.metrics_dir / "consultation_metrics.json"
        consultation_data = [
            {
                "expert_id": m.expert_id,
                "domain": m.domain,
                "confidence": m.confidence,
                "agreement_level": m.agreement_level,
                "rag_quality": m.rag_quality,
                "threshold_met": m.threshold_met,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in self.consultation_metrics[-100:]  # Keep last 100
        ]
        consultation_file.write_text(
            json.dumps(consultation_data, indent=2), encoding="utf-8"
        )

        # Save Context7 metrics
        context7_file = self.metrics_dir / "context7_metrics.json"
        context7_data = [
            {
                "hit_rate": m.hit_rate,
                "latency_ms": m.latency_ms,
                "total_requests": m.total_requests,
                "cache_hits": m.cache_hits,
                "cache_misses": m.cache_misses,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in self.context7_metrics[-100:]  # Keep last 100
        ]
        context7_file.write_text(
            json.dumps(context7_data, indent=2), encoding="utf-8"
        )

        # Save RAG metrics
        rag_file = self.metrics_dir / "rag_metrics.json"
        rag_data = [
            {
                "retrieval_hit_rate": m.retrieval_hit_rate,
                "low_quality_queries": m.low_quality_queries,
                "total_queries": m.total_queries,
                "successful_retrievals": m.successful_retrievals,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in self.rag_metrics[-100:]  # Keep last 100
        ]
        rag_file.write_text(json.dumps(rag_data, indent=2), encoding="utf-8")

