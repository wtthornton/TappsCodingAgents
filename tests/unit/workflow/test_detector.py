"""
Tests for Project Type Detector.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import os

from tapps_agents.workflow.detector import (
    ProjectDetector,
    ProjectType,
    WorkflowTrack,
    ProjectCharacteristics
)


class TestProjectDetector:
    """Test project type detection."""
    
    def test_detect_greenfield_empty_directory(self):
        """Test detection of greenfield project (empty directory)."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            detector = ProjectDetector(project_root=project_root)
            
            characteristics = detector.detect()
            
            assert characteristics.project_type == ProjectType.GREENFIELD
            assert characteristics.workflow_track == WorkflowTrack.BMAD_METHOD
            assert characteristics.confidence >= 0.5
            assert "no_src" in characteristics.indicators
            assert characteristics.indicators["no_src"] is True
    
    def test_detect_brownfield_with_src(self):
        """Test detection of brownfield project (has src/ directory)."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "src").mkdir()
            (project_root / "package.json").touch()
            (project_root / ".git").mkdir()
            (project_root / "tests").mkdir()  # Add tests directory
            (project_root / "README.md").touch()  # Add docs
            # Create more files to avoid minimal_files indicator
            for i in range(10):
                (project_root / f"file{i}.txt").touch()
            
            detector = ProjectDetector(project_root=project_root)
            characteristics = detector.detect()
            
            assert characteristics.project_type == ProjectType.BROWNFIELD
            assert characteristics.workflow_track == WorkflowTrack.BMAD_METHOD
            assert characteristics.confidence >= 0.6
            assert characteristics.indicators["has_src"] is True
            assert characteristics.indicators["has_package_files"] is True
    
    def test_detect_quick_fix_from_query(self):
        """Test detection of quick-fix from user query."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            detector = ProjectDetector(project_root=project_root)
            
            characteristics = detector.detect_from_context(
                user_query="Fix the bug in authentication.py",
                file_count=1
            )
            
            assert characteristics.project_type == ProjectType.QUICK_FIX
            assert characteristics.workflow_track == WorkflowTrack.QUICK_FLOW
            assert characteristics.confidence >= 0.6
            assert "quick_fix_keywords" in characteristics.indicators
    
    def test_detect_quick_fix_small_scope(self):
        """Test detection of quick-fix from small file count."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            detector = ProjectDetector(project_root=project_root)
            
            characteristics = detector.detect_from_context(
                file_count=3,
                scope_description="fix error handling"
            )
            
            assert characteristics.project_type == ProjectType.QUICK_FIX
            assert characteristics.workflow_track == WorkflowTrack.QUICK_FLOW
            assert characteristics.indicators.get("small_scope") is True
    
    def test_detect_enterprise_with_compliance(self):
        """Test detection of enterprise project with compliance files."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "src").mkdir()
            (project_root / "compliance").mkdir()
            (project_root / "HIPAA.md").touch()
            
            detector = ProjectDetector(project_root=project_root)
            characteristics = detector.detect()
            
            assert characteristics.workflow_track == WorkflowTrack.ENTERPRISE
            assert characteristics.indicators.get("has_compliance") is True
            assert any("Compliance" in rec for rec in characteristics.recommendations)
    
    def test_get_recommended_workflow_quick_fix(self):
        """Test getting recommended workflow for quick-fix."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            detector = ProjectDetector(project_root=project_root)
            
            characteristics = detector.detect_from_context(
                user_query="fix bug",
                file_count=2
            )
            
            workflow_file = detector.get_recommended_workflow(characteristics)
            assert workflow_file == "quick-fix"
    
    def test_get_recommended_workflow_greenfield(self):
        """Test getting recommended workflow for greenfield."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            detector = ProjectDetector(project_root=project_root)
            
            characteristics = detector.detect()
            
            workflow_file = detector.get_recommended_workflow(characteristics)
            assert workflow_file in ["greenfield-development", "feature-development"]
    
    def test_get_recommended_workflow_enterprise(self):
        """Test getting recommended workflow for enterprise."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "src").mkdir()
            (project_root / "compliance").mkdir()
            (project_root / "security.md").touch()
            
            detector = ProjectDetector(project_root=project_root)
            characteristics = detector.detect()
            
            workflow_file = detector.get_recommended_workflow(characteristics)
            assert workflow_file == "enterprise-development"
    
    def test_indicators_collected(self):
        """Test that indicators are properly collected."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()
            (project_root / "README.md").touch()
            
            detector = ProjectDetector(project_root=project_root)
            characteristics = detector.detect()
            
            assert "has_src" in characteristics.indicators
            assert "has_tests" in characteristics.indicators
            assert "has_docs" in characteristics.indicators
            assert characteristics.indicators["has_src"] is True
            assert characteristics.indicators["has_tests"] is True

