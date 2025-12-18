"""
Unit tests for workflow artifacts.
"""


import pytest

from tapps_agents.workflow.code_artifact import CodeArtifact, CodeChange
from tapps_agents.workflow.context_artifact import (
    ContextArtifact,
    ContextQuery,
    LibraryCacheEntry,
    ProjectProfile,
)

pytestmark = pytest.mark.unit


class TestCodeArtifact:
    """Test cases for CodeArtifact."""

    def test_code_artifact_creation(self):
        """Test creating a code artifact."""
        artifact = CodeArtifact(
            operation_type="implement",
            worktree_path="/path/to/worktree"
        )
        
        assert artifact.schema_version == "1.0"
        assert artifact.status == "pending"
        assert artifact.operation_type == "implement"
        assert artifact.worktree_path == "/path/to/worktree"
        assert len(artifact.changes) == 0

    def test_code_artifact_add_change(self):
        """Test adding a code change."""
        artifact = CodeArtifact()
        change = CodeChange(
            file_path="test.py",
            change_type="feature",
            lines_added=10,
            lines_removed=2
        )
        
        artifact.add_change(change)
        
        assert len(artifact.changes) == 1
        assert artifact.total_files_modified == 1
        assert artifact.total_lines_added == 10
        assert artifact.total_lines_removed == 2

    def test_code_artifact_to_dict(self):
        """Test converting artifact to dictionary."""
        artifact = CodeArtifact(
            operation_type="implement",
            status="completed"
        )
        change = CodeChange(
            file_path="test.py",
            change_type="feature"
        )
        artifact.add_change(change)
        
        data = artifact.to_dict()
        
        assert data["schema_version"] == "1.0"
        assert data["status"] == "completed"
        assert len(data["changes"]) == 1
        assert data["changes"][0]["file_path"] == "test.py"

    def test_code_artifact_from_dict(self):
        """Test creating artifact from dictionary."""
        data = {
            "schema_version": "1.0",
            "status": "completed",
            "operation_type": "implement",
            "changes": [
                {
                    "file_path": "test.py",
                    "change_type": "feature",
                    "lines_added": 10,
                    "lines_removed": 2
                }
            ],
            "refactorings": []
        }
        
        artifact = CodeArtifact.from_dict(data)
        
        assert artifact.schema_version == "1.0"
        assert artifact.status == "completed"
        assert len(artifact.changes) == 1
        assert artifact.changes[0].file_path == "test.py"

    def test_code_change_creation(self):
        """Test creating a code change."""
        change = CodeChange(
            file_path="test.py",
            change_type="refactor",
            lines_added=5,
            lines_removed=3,
            functions_added=["new_func"],
            status="completed"
        )
        
        assert change.file_path == "test.py"
        assert change.change_type == "refactor"
        assert change.lines_added == 5
        assert change.lines_removed == 3
        assert "new_func" in change.functions_added
        assert change.status == "completed"


class TestContextArtifact:
    """Test cases for ContextArtifact."""

    def test_context_artifact_creation(self):
        """Test creating a context artifact."""
        artifact = ContextArtifact(
            operation_type="cache_population",
            worktree_path="/path/to/worktree"
        )
        
        assert artifact.schema_version == "1.0"
        assert artifact.status == "pending"
        assert artifact.operation_type == "cache_population"
        assert len(artifact.libraries_cached) == 0

    def test_context_artifact_add_library(self):
        """Test adding a library cache entry."""
        artifact = ContextArtifact()
        library = LibraryCacheEntry(
            library_name="pytest",
            library_id="/pytest/pytest",
            status="cached",
            cache_size_bytes=1024
        )
        
        artifact.add_library(library)
        
        assert len(artifact.libraries_cached) == 1
        assert artifact.cache_population_success == 1
        assert artifact.total_cache_size_bytes == 1024

    def test_context_artifact_add_query(self):
        """Test adding a context query."""
        artifact = ContextArtifact()
        query = ContextQuery(
            query="pytest fixtures",
            library="pytest",
            results_count=5,
            cache_hit=True
        )
        
        artifact.add_query(query)
        
        assert len(artifact.queries_executed) == 1
        assert artifact.total_queries == 1
        assert artifact.cache_hits == 1

    def test_context_artifact_to_dict(self):
        """Test converting artifact to dictionary."""
        artifact = ContextArtifact(
            operation_type="query",
            status="completed"
        )
        query = ContextQuery(query="test", results_count=1)
        artifact.add_query(query)
        
        data = artifact.to_dict()
        
        assert data["schema_version"] == "1.0"
        assert data["status"] == "completed"
        assert len(data["queries_executed"]) == 1

    def test_context_artifact_from_dict(self):
        """Test creating artifact from dictionary."""
        data = {
            "schema_version": "1.0",
            "status": "completed",
            "operation_type": "query",
            "libraries_cached": [],
            "queries_executed": [
                {
                    "query": "test",
                    "results_count": 1,
                    "cache_hit": False
                }
            ]
        }
        
        artifact = ContextArtifact.from_dict(data)
        
        assert artifact.schema_version == "1.0"
        assert artifact.status == "completed"
        assert len(artifact.queries_executed) == 1

    def test_project_profile_creation(self):
        """Test creating a project profile."""
        profile = ProjectProfile(
            deployment_type="cloud_native",
            tenancy="multi_tenant",
            user_scale="enterprise",
            compliance=["HIPAA", "SOC2"],
            security_posture="high"
        )
        
        assert profile.deployment_type == "cloud_native"
        assert profile.tenancy == "multi_tenant"
        assert profile.user_scale == "enterprise"
        assert "HIPAA" in profile.compliance
        assert profile.security_posture == "high"

