"""
Quality Metrics Aggregator - Aggregate and compare service-level metrics

Phase 6.4.2: Multi-Service Analysis
"""

from collections import defaultdict
from pathlib import Path
from typing import Any


class QualityAggregator:
    """
    Aggregate quality metrics across services and generate comparisons.

    Phase 6.4.2: Multi-Service Analysis
    """

    def __init__(self):
        """Initialize aggregator."""
        pass

    def aggregate_service_scores(
        self, service_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Aggregate quality scores across multiple services.

        Args:
            service_results: List of service analysis results, each containing:
                - service_name: Name of the service
                - scores: Dictionary of quality scores
                - files_analyzed: Number of files analyzed
                - total_lines: Total lines of code

        Returns:
            Aggregated metrics dictionary with:
            - service_count: Number of services analyzed
            - average_scores: Average scores across all services
            - total_files: Total files analyzed
            - total_lines: Total lines of code
            - services: List of individual service metrics
        """
        if not service_results:
            return {
                "service_count": 0,
                "average_scores": {},
                "total_files": 0,
                "total_lines": 0,
                "services": [],
            }

        # Initialize aggregators
        score_sums: defaultdict[str, float] = defaultdict(float)
        total_files = 0
        total_lines = 0
        service_count = len(service_results)

        # Aggregate scores and counts
        service_metrics = []
        for result in service_results:
            service_name = result.get("service_name", "Unknown")
            scores = result.get("scores", {})
            files_count = result.get("files_analyzed", 0)
            lines_count = result.get("total_lines", 0)

            # Sum scores
            for metric, value in scores.items():
                if isinstance(value, (int, float)):
                    score_sums[metric] += value

            total_files += files_count
            total_lines += lines_count

            # Store individual service metrics
            service_metrics.append(
                {
                    "service_name": service_name,
                    "scores": scores,
                    "files_analyzed": files_count,
                    "total_lines": lines_count,
                    "overall_score": scores.get("overall_score", 0.0),
                }
            )

        # Calculate averages
        average_scores = {}
        for metric, total in score_sums.items():
            average_scores[metric] = total / service_count

        return {
            "service_count": service_count,
            "average_scores": average_scores,
            "total_files": total_files,
            "total_lines": total_lines,
            "services": service_metrics,
        }

    def compare_services(self, service_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Compare quality metrics across services.

        Args:
            service_results: List of service analysis results

        Returns:
            Comparison dictionary with:
            - rankings: Service rankings by metric
            - best_services: Best service for each metric
            - worst_services: Worst service for each metric
            - metrics_comparison: Detailed comparison table
        """
        if not service_results:
            return {
                "rankings": {},
                "best_services": {},
                "worst_services": {},
                "metrics_comparison": [],
            }

        # Extract all metrics
        all_metrics = set()
        for result in service_results:
            scores = result.get("scores", {})
            all_metrics.update(scores.keys())

        # Build comparison data
        rankings = {}
        best_services = {}
        worst_services = {}
        metrics_comparison = []

        for metric in all_metrics:
            if metric == "metrics":  # Skip nested metrics dict
                continue

            # Get values for this metric across all services
            service_values = []
            for result in service_results:
                service_name = result.get("service_name", "Unknown")
                scores = result.get("scores", {})
                value = scores.get(metric, 0.0)
                service_values.append((service_name, value))

            # Sort by value (descending for scores, ascending for complexity)
            reverse = not metric.startswith(
                "complexity"
            )  # Complexity is lower-is-better
            service_values.sort(key=lambda x: x[1], reverse=reverse)

            # Store rankings
            rankings[metric] = [name for name, _ in service_values]

            # Store best and worst
            if service_values:
                best_services[metric] = service_values[0][0]  # First after sort
                worst_services[metric] = service_values[-1][0]  # Last after sort

            # Build comparison table row
            metrics_comparison.append(
                {
                    "metric": metric,
                    "best": best_services.get(metric, "N/A"),
                    "worst": worst_services.get(metric, "N/A"),
                    "range": {
                        "min": (
                            min(val for _, val in service_values)
                            if service_values
                            else 0.0
                        ),
                        "max": (
                            max(val for _, val in service_values)
                            if service_values
                            else 0.0
                        ),
                        "average": (
                            sum(val for _, val in service_values) / len(service_values)
                            if service_values
                            else 0.0
                        ),
                    },
                }
            )

        return {
            "rankings": rankings,
            "best_services": best_services,
            "worst_services": worst_services,
            "metrics_comparison": metrics_comparison,
        }

    def generate_service_report(
        self, service_results: list[dict[str, Any]], project_root: Path | None = None
    ) -> dict[str, Any]:
        """
        Generate comprehensive service analysis report.

        Args:
            service_results: List of service analysis results
            project_root: Optional project root path

        Returns:
            Complete report with aggregation and comparison
        """
        aggregated = self.aggregate_service_scores(service_results)
        comparison = self.compare_services(service_results)

        return {
            "project_root": str(project_root) if project_root else None,
            "aggregated": aggregated,
            "comparison": comparison,
            "services": aggregated.get("services", []),
        }
