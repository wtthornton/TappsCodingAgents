"""
Knowledge Base Management Commands

Commands for validating, monitoring, and managing knowledge bases.
"""

from pathlib import Path

from ...experts.builtin_registry import BuiltinExpertRegistry
from ...experts.knowledge_freshness import get_freshness_tracker
from ...experts.knowledge_validator import KnowledgeBaseValidator
from ...experts.rag_metrics import get_rag_metrics_tracker


class KnowledgeCommand:
    """Knowledge base management commands."""

    def validate(self, knowledge_dir: Path | None = None) -> dict:
        """
        Validate knowledge base files.

        Args:
            knowledge_dir: Optional knowledge directory (default: built-in knowledge)

        Returns:
            Validation results
        """
        if knowledge_dir is None:
            knowledge_dir = BuiltinExpertRegistry.get_builtin_knowledge_path()

        validator = KnowledgeBaseValidator(knowledge_dir)
        results = validator.validate_all()
        summary = validator.get_summary(results)

        return {
            "summary": summary,
            "results": [
                {
                    "file": str(r.file_path.relative_to(knowledge_dir)),
                    "valid": r.is_valid,
                    "issues": [
                        {
                            "severity": i.severity,
                            "line": i.line_number,
                            "message": i.message,
                            "rule": i.rule,
                        }
                        for i in r.issues
                    ],
                }
                for r in results
            ],
        }

    def metrics(self) -> dict:
        """
        Get RAG performance metrics.

        Returns:
            Performance metrics
        """
        tracker = get_rag_metrics_tracker()
        return {
            "metrics": tracker.get_metrics(),
            "recent_queries": tracker.get_recent_queries(20),
        }

    def freshness(self, knowledge_dir: Path | None = None, scan: bool = False) -> dict:
        """
        Get knowledge base freshness information.

        Args:
            knowledge_dir: Optional knowledge directory (default: built-in knowledge)
            scan: Whether to scan and update metadata

        Returns:
            Freshness summary
        """
        if knowledge_dir is None:
            knowledge_dir = BuiltinExpertRegistry.get_builtin_knowledge_path()

        tracker = get_freshness_tracker()

        if scan:
            scan_results = tracker.scan_and_update(knowledge_dir)
        else:
            scan_results = None

        summary = tracker.get_summary(knowledge_dir)
        stale_files = tracker.get_stale_files(knowledge_dir, max_age_days=365)
        deprecated_files = tracker.get_deprecated_files(knowledge_dir)

        return {
            "summary": summary,
            "scan_results": scan_results,
            "stale_files": [
                {
                    "file": str(f.relative_to(knowledge_dir)),
                    "last_updated": m.last_updated,
                }
                for f, m in stale_files[:10]  # Limit to 10
            ],
            "deprecated_files": [
                {
                    "file": str(f.relative_to(knowledge_dir)),
                    "deprecation_date": m.deprecation_date,
                    "replacement": m.replacement_file,
                }
                for f, m in deprecated_files
            ],
        }
