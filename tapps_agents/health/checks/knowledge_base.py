"""
Knowledge Base Health Check.

Checks RAG/KB population and performance.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from ...experts.simple_rag import SimpleKnowledgeBase
from ...experts.vector_rag import VectorKnowledgeBase
from ..base import HealthCheck, HealthCheckResult


class KnowledgeBaseHealthCheck(HealthCheck):
    """Health check for knowledge base population and performance."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize knowledge base health check.

        Args:
            project_root: Project root directory
        """
        super().__init__(name="knowledge_base", dependencies=["environment"])
        self.project_root = project_root or Path.cwd()
        self.kb_dir = self.project_root / ".tapps-agents" / "knowledge"
        self.rag_index_dir = self.project_root / ".tapps-agents" / "rag_index"

    def run(self) -> HealthCheckResult:
        """
        Run knowledge base health check.

        Returns:
            HealthCheckResult with KB status
        """
        try:
            # Check KB directory existence
            kb_exists = self.kb_dir.exists()
            if not kb_exists:
                return HealthCheckResult(
                    name=self.name,
                    status="degraded",
                    score=30.0,
                    message="Knowledge base directory does not exist",
                    details={
                        "kb_dir": str(self.kb_dir),
                        "exists": False,
                    },
                    remediation=[
                        "Knowledge base will be created automatically when agents run",
                        "Or run knowledge ingestion: tapps-agents knowledge ingest",
                    ],
                )

            # Count KB files and domains
            kb_files = list(self.kb_dir.rglob("*.md"))
            domains = set()
            for file in kb_files:
                # Extract domain from path (e.g., .tapps-agents/knowledge/<domain>/file.md)
                try:
                    rel_path = file.relative_to(self.kb_dir)
                    if len(rel_path.parts) > 1:
                        domains.add(rel_path.parts[0])
                except Exception:
                    pass

            total_files = len(kb_files)
            total_domains = len(domains)

            # Check for recent entries (last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_files = [
                f
                for f in kb_files
                if datetime.fromtimestamp(f.stat().st_mtime) >= seven_days_ago
            ]
            recent_count = len(recent_files)

            # Check RAG backend type
            backend_type = "unknown"
            vector_index_exists = False
            try:
                # Try to initialize vector RAG to detect backend
                test_kb = VectorKnowledgeBase(knowledge_dir=self.kb_dir, domain=None)
                backend_type = test_kb.get_backend_type()
                if backend_type == "vector":
                    # Check if index exists
                    for domain_dir in self.rag_index_dir.iterdir():
                        if domain_dir.is_dir():
                            index_file = domain_dir / "index.faiss"
                            if index_file.exists():
                                vector_index_exists = True
                                break
            except Exception:
                # Fallback to simple
                try:
                    test_kb = SimpleKnowledgeBase(knowledge_dir=self.kb_dir, domain=None)
                    backend_type = "simple"
                except Exception:
                    backend_type = "unknown"

            # Calculate health score
            score = 100.0
            issues = []
            remediation = []

            # Check if KB is empty
            if total_files == 0:
                score = 20.0
                issues.append("Knowledge base is empty")
                remediation.append("Run knowledge ingestion to populate KB")
            elif total_files < 5:
                score -= 20.0
                issues.append(f"Very few KB files: {total_files}")
                remediation.append("Consider running knowledge ingestion")

            # Check for recent activity
            if recent_count == 0 and total_files > 0:
                score -= 15.0
                issues.append("No recent KB activity (last 7 days)")
                remediation.append("Knowledge base may need refreshing")

            # Check backend type
            if backend_type == "simple":
                score -= 10.0
                issues.append("Using simple keyword search (vector RAG not available)")
                remediation.append("Install FAISS for semantic search: pip install faiss-cpu")
            elif backend_type == "unknown":
                score -= 20.0
                issues.append("Could not determine RAG backend type")

            # Check vector index if using vector backend
            if backend_type == "vector" and not vector_index_exists:
                score -= 15.0
                issues.append("Vector index not found - may need rebuilding")
                remediation.append("Vector index will be built automatically on first query")

            # Determine status
            if score >= 85.0:
                status = "healthy"
            elif score >= 70.0:
                status = "degraded"
            else:
                status = "unhealthy"

            # Build message
            message_parts = [
                f"Files: {total_files}",
                f"Domains: {total_domains}",
                f"Backend: {backend_type}",
            ]
            if recent_count > 0:
                message_parts.append(f"Recent: {recent_count}")
            message = " | ".join(message_parts)

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=max(0.0, score),
                message=message,
                details={
                    "total_files": total_files,
                    "total_domains": total_domains,
                    "recent_files_7d": recent_count,
                    "backend_type": backend_type,
                    "vector_index_exists": vector_index_exists,
                    "kb_dir": str(self.kb_dir),
                    "rag_index_dir": str(self.rag_index_dir),
                    "domains": list(domains),
                    "issues": issues,
                },
                remediation=remediation if remediation else None,
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Knowledge base check failed: {e}",
                details={"error": str(e), "kb_dir": str(self.kb_dir)},
                remediation=["Check KB directory permissions and structure"],
            )

