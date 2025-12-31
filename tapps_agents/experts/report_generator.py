"""
Report Generator for Business Metrics

Generates human-readable reports from business metrics data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .business_metrics import (
    BusinessMetricsData,
    MetricsStorage,
    ROIMetrics,
)

logger = logging.getLogger(__name__)


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


class ReportGenerator:
    """Generate human-readable reports from metrics."""

    def __init__(self, storage: MetricsStorage):
        """
        Initialize report generator.

        Args:
            storage: MetricsStorage instance
        """
        self.storage = storage
        self.reports_path = storage.storage_path / "reports"
        self.reports_path.mkdir(parents=True, exist_ok=True)

    def generate_weekly_report(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> WeeklyReport:
        """Generate weekly summary report."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        # Load metrics for period
        metrics_list = self.storage.load_historical_metrics(start_date, end_date)

        if not metrics_list:
            # Use current metrics if no history
            current = self.storage.load_current_metrics()
            if current:
                metrics_list = [current]

        if not metrics_list:
            # Return empty report
            return WeeklyReport(
                period_start=start_date,
                period_end=end_date,
                total_consultations=0,
                top_experts=[],
                top_domains=[],
                avg_confidence=0.0,
                confidence_trend="stable",
                code_quality_improvements=0,
                estimated_time_saved_hours=0.0,
                roi_percentage=0.0,
            )

        # Aggregate data
        total_consultations = sum(
            m.adoption_metrics.total_consultations for m in metrics_list
        )

        # Aggregate expert usage
        expert_usage: dict[str, int] = {}
        domain_usage: dict[str, int] = {}
        confidences: list[float] = []

        for metrics in metrics_list:
            # Expert usage
            for expert_id, count in metrics.adoption_metrics.expert_usage_by_id.items():
                expert_usage[expert_id] = expert_usage.get(expert_id, 0) + count

            # Domain usage
            for domain, count in metrics.adoption_metrics.domain_usage.items():
                domain_usage[domain] = domain_usage.get(domain, 0) + count

            # Confidences
            if metrics.quality_metrics.avg_confidence > 0:
                confidences.append(metrics.quality_metrics.avg_confidence)

        # Top experts and domains
        top_experts = sorted(
            expert_usage.items(), key=lambda x: x[1], reverse=True
        )[:10]
        top_domains = sorted(
            domain_usage.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Average confidence
        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        # Confidence trend
        if len(metrics_list) >= 2:
            first_confidence = metrics_list[0].quality_metrics.avg_confidence
            last_confidence = metrics_list[-1].quality_metrics.avg_confidence
            if last_confidence > first_confidence * 1.05:
                confidence_trend = "increasing"
            elif last_confidence < first_confidence * 0.95:
                confidence_trend = "decreasing"
            else:
                confidence_trend = "stable"
        else:
            confidence_trend = "stable"

        # Code quality improvements
        total_improvements = sum(
            len(m.effectiveness_metrics.code_quality_improvements)
            for m in metrics_list
        )

        # Time saved and ROI (from latest metrics)
        latest = metrics_list[-1]
        estimated_time_saved_hours = latest.roi_metrics.estimated_time_saved_hours
        roi_percentage = latest.roi_metrics.roi_percentage

        report = WeeklyReport(
            period_start=start_date,
            period_end=end_date,
            total_consultations=total_consultations,
            top_experts=top_experts,
            top_domains=top_domains,
            avg_confidence=avg_confidence,
            confidence_trend=confidence_trend,
            code_quality_improvements=total_improvements,
            estimated_time_saved_hours=estimated_time_saved_hours,
            roi_percentage=roi_percentage,
        )

        return report

    def generate_roi_report(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> ROIReport:
        """Generate ROI analysis report."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Load metrics for period
        metrics_list = self.storage.load_historical_metrics(start_date, end_date)

        if not metrics_list:
            current = self.storage.load_current_metrics()
            if current:
                metrics_list = [current]

        if not metrics_list:
            return ROIReport(
                period_start=start_date,
                period_end=end_date,
                total_consultations=0,
                total_cost=0.0,
                total_value=0.0,
                roi_percentage=0.0,
                roi_per_consultation=0.0,
                breakdown_by_expert={},
                breakdown_by_domain={},
            )

        # Aggregate ROI from latest metrics
        latest = metrics_list[-1]
        roi_metrics = latest.roi_metrics

        # Simple breakdown (would need more detailed tracking for accurate breakdown)
        breakdown_by_expert: dict[str, ROIMetrics] = {}
        breakdown_by_domain: dict[str, ROIMetrics] = {}

        # For now, use aggregated data (Phase 3 enhancement would add detailed breakdown)
        for expert_id in latest.adoption_metrics.expert_usage_by_id.keys():
            # Estimate ROI per expert (simplified)
            usage_count = latest.adoption_metrics.expert_usage_by_id[expert_id]
            expert_roi = ROIMetrics(
                total_consultations=usage_count,
                estimated_time_saved_hours=usage_count
                * roi_metrics.estimated_value_per_consultation,
                estimated_cost_per_consultation=roi_metrics.estimated_cost_per_consultation,
                estimated_value_per_consultation=roi_metrics.estimated_value_per_consultation,
                total_cost=usage_count * roi_metrics.estimated_cost_per_consultation,
                total_value=usage_count * roi_metrics.estimated_value_per_consultation,
                roi_percentage=roi_metrics.roi_percentage,
                roi_per_consultation=roi_metrics.roi_per_consultation,
            )
            breakdown_by_expert[expert_id] = expert_roi

        report = ROIReport(
            period_start=start_date,
            period_end=end_date,
            total_consultations=roi_metrics.total_consultations,
            total_cost=roi_metrics.total_cost,
            total_value=roi_metrics.total_value,
            roi_percentage=roi_metrics.roi_percentage,
            roi_per_consultation=roi_metrics.roi_per_consultation,
            breakdown_by_expert=breakdown_by_expert,
            breakdown_by_domain=breakdown_by_domain,
        )

        return report

    def export_to_markdown(self, report: WeeklyReport | ROIReport, output_path: Path) -> None:
        """Export report to Markdown format."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                if isinstance(report, WeeklyReport):
                    self._write_weekly_report_markdown(f, report)
                elif isinstance(report, ROIReport):
                    self._write_roi_report_markdown(f, report)

            logger.info(f"Exported report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export report: {e}", exc_info=True)

    def _write_weekly_report_markdown(self, f: Any, report: WeeklyReport) -> None:
        """Write weekly report in Markdown format."""
        f.write(f"# Weekly Business Metrics Report\n\n")
        f.write(f"**Period:** {report.period_start.date()} to {report.period_end.date()}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Consultations:** {report.total_consultations}\n")
        f.write(f"- **Average Confidence:** {report.avg_confidence:.2%}\n")
        f.write(f"- **Confidence Trend:** {report.confidence_trend}\n")
        f.write(f"- **Code Quality Improvements:** {report.code_quality_improvements}\n")
        f.write(f"- **Estimated Time Saved:** {report.estimated_time_saved_hours:.1f} hours\n")
        f.write(f"- **ROI:** {report.roi_percentage:.1f}%\n\n")

        f.write(f"## Top Experts\n\n")
        for expert_id, count in report.top_experts[:5]:
            f.write(f"- **{expert_id}**: {count} consultations\n")

        f.write(f"\n## Top Domains\n\n")
        for domain, count in report.top_domains[:5]:
            f.write(f"- **{domain}**: {count} consultations\n")

    def _write_roi_report_markdown(self, f: Any, report: ROIReport) -> None:
        """Write ROI report in Markdown format."""
        f.write(f"# ROI Analysis Report\n\n")
        f.write(f"**Period:** {report.period_start.date()} to {report.period_end.date()}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Consultations:** {report.total_consultations}\n")
        f.write(f"- **Total Cost:** ${report.total_cost:.2f}\n")
        f.write(f"- **Total Value:** ${report.total_value:.2f}\n")
        f.write(f"- **ROI:** {report.roi_percentage:.1f}%\n")
        f.write(f"- **ROI per Consultation:** ${report.roi_per_consultation:.2f}\n\n")

        if report.breakdown_by_expert:
            f.write(f"## ROI by Expert\n\n")
            for expert_id, roi in list(report.breakdown_by_expert.items())[:10]:
                f.write(f"### {expert_id}\n\n")
                f.write(f"- Consultations: {roi.total_consultations}\n")
                f.write(f"- ROI: {roi.roi_percentage:.1f}%\n")
                f.write(f"- Value: ${roi.total_value:.2f}\n\n")
