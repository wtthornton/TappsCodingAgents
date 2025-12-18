"""
Tests for Knowledge Ingestion Pipeline.
"""

from pathlib import Path

import pytest

from tapps_agents.experts.knowledge_ingestion import (
    IngestionResult,
    KnowledgeEntry,
    KnowledgeIngestionPipeline,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


def test_knowledge_ingestion_pipeline_initialization(temp_project):
    """Test Knowledge Ingestion Pipeline initialization."""
    pipeline = KnowledgeIngestionPipeline(project_root=temp_project)
    assert pipeline.project_root == temp_project
    assert pipeline.config_dir == temp_project / ".tapps-agents"
    assert pipeline.knowledge_base_dir == temp_project / ".tapps-agents" / "knowledge"


def test_ingest_project_sources(temp_project):
    """Test ingesting project sources."""
    # Create sample project files
    docs_dir = temp_project / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    (docs_dir / "architecture.md").write_text("# Architecture\n\nSystem architecture description.")
    (temp_project / "requirements.txt").write_text("django==4.2.0\npytest==7.0.0\n")

    pipeline = KnowledgeIngestionPipeline(project_root=temp_project)
    result = pipeline.ingest_project_sources()

    assert isinstance(result, IngestionResult)
    assert result.source_type == "project"
    assert result.entries_ingested > 0


def test_extract_title_from_markdown():
    """Test title extraction from markdown."""
    pipeline = KnowledgeIngestionPipeline(project_root=Path("/tmp"))

    content = "# My Document Title\n\nContent here."
    title = pipeline._extract_title(Path("test.md"), content)
    assert title == "My Document Title"

    # Test fallback to filename
    title = pipeline._extract_title(Path("my-document.md"), "")
    assert "my" in title.lower() and "document" in title.lower()


def test_create_knowledge_entry():
    """Test knowledge entry creation."""
    entry = KnowledgeEntry(
        title="Test Entry",
        content="Test content",
        domain="python",
        source="test.md",
        source_type="project",
    )

    assert entry.title == "Test Entry"
    assert entry.content == "Test content"
    assert entry.domain == "python"
    assert entry.source_type == "project"


def test_distill_context7_content():
    """Test Context7 content distillation."""
    pipeline = KnowledgeIngestionPipeline(project_root=Path("/tmp"))

    content = "Original Context7 content"
    distilled = pipeline._distill_context7_content("django", "patterns", content)

    assert "How We Use django" in distilled
    assert "patterns" in distilled
    assert "Project-Specific Notes" in distilled

