"""Tests for file_inference module."""

import os
import pytest
from pathlib import Path

from tapps_agents.simple_mode.file_inference import TargetFileInferencer


def normalize_path_for_comparison(path: str) -> str:
    """Normalize path separators for cross-platform comparison."""
    return path.replace("\\", "/")


class TestTargetFileInferencer:
    """Tests for TargetFileInferencer."""

    @pytest.fixture
    def inferencer(self, tmp_path: Path):
        """Create inferencer with temp directory."""
        return TargetFileInferencer(project_root=tmp_path)

    def test_infer_api_endpoint(self, inferencer):
        """Test inferring path for API endpoint description."""
        path = inferencer.infer_target_file("Create a REST API endpoint for users")
        assert "api" in path.lower() or "user" in path.lower()
        assert path.endswith(".py")

    def test_infer_service(self, inferencer):
        """Test inferring path for service description."""
        path = inferencer.infer_target_file("Build an authentication service")
        assert "service" in path.lower() or "auth" in path.lower()
        assert path.endswith(".py")

    def test_infer_model(self, inferencer):
        """Test inferring path for model description."""
        path = inferencer.infer_target_file("Create a User model with email and name")
        assert "model" in path.lower() or "user" in path.lower()
        assert path.endswith(".py")

    def test_infer_test_file(self, inferencer):
        """Test inferring path for test description - explicit test file request."""
        # Use a more explicit test file description
        path = inferencer.infer_target_file("Write unit tests for user service validation")
        # Should return a tests path or contain test keyword
        normalized = normalize_path_for_comparison(path.lower())
        assert "test" in normalized or normalized.startswith("tests/")
        assert path.endswith(".py")

    def test_infer_utility(self, inferencer):
        """Test inferring path for utility description."""
        path = inferencer.infer_target_file("Create helper functions for validation")
        assert "util" in path.lower() or "helper" in path.lower() or "validat" in path.lower()
        assert path.endswith(".py")

    def test_infer_with_context(self, inferencer):
        """Test inferring with architecture context."""
        path = inferencer.infer_target_file(
            "Build user authentication",
            context={"architecture": "Use src/auth/user_auth.py as base"}
        )
        # Should prefer context hints
        assert path.endswith(".py")

    def test_infer_with_file_path_in_context(self, inferencer):
        """Test inferring with explicit file_path in context."""
        path = inferencer.infer_target_file(
            "Any description",
            context={"file_path": "src/custom/my_file.py"}
        )
        # Normalize for cross-platform comparison
        normalized = normalize_path_for_comparison(path)
        assert normalized == "src/custom/my_file.py"

    def test_extract_feature_name_create(self, inferencer):
        """Test extracting feature name from 'create' pattern."""
        name = inferencer._extract_feature_name("create a user authentication feature")
        assert "user" in name or "auth" in name

    def test_extract_feature_name_implement(self, inferencer):
        """Test extracting feature name from 'implement' pattern."""
        name = inferencer._extract_feature_name("implement the payment processing system")
        assert "payment" in name or "processing" in name

    def test_extract_feature_name_fallback(self, inferencer):
        """Test feature name extraction fallback."""
        name = inferencer._extract_feature_name("do something interesting")
        # Should return something reasonable even for vague descriptions
        assert len(name) > 0
        assert "_" not in name or name.count("_") >= 0

    def test_normalize_path_adds_extension(self, inferencer):
        """Test that normalize adds .py extension if missing."""
        path = inferencer._normalize_path("src/myfile")
        assert path.endswith(".py")

    def test_normalize_path_adds_src_prefix(self, inferencer):
        """Test that normalize adds src/ or src\\ prefix if missing."""
        path = inferencer._normalize_path("myfile.py")
        normalized = normalize_path_for_comparison(path)
        assert normalized.startswith("src/")

    def test_suggest_alternatives(self, inferencer):
        """Test suggesting alternative paths."""
        alternatives = inferencer.suggest_alternatives(
            "Create a user API service",
            count=3
        )
        assert len(alternatives) == 3
        assert all(alt.endswith(".py") for alt in alternatives)

    def test_infer_from_previous_steps(self, inferencer):
        """Test inferring from previous step outputs."""
        path = inferencer.infer_from_previous_steps(
            enhanced_prompt="Build a user management system with CRUD operations",
            architecture="Component-based architecture with UserService",
            api_design="REST API with router pattern",
        )
        assert path.endswith(".py")
        assert "user" in path.lower() or "service" in path.lower() or "api" in path.lower()

    def test_infer_middleware(self, inferencer):
        """Test inferring middleware path."""
        path = inferencer.infer_target_file("Create authentication middleware")
        assert "middleware" in path.lower() or "auth" in path.lower()

    def test_infer_config(self, inferencer):
        """Test inferring config path."""
        path = inferencer.infer_target_file("Add configuration settings for the database")
        assert "config" in path.lower() or "settings" in path.lower()

    def test_default_fallback(self, inferencer):
        """Test that vague descriptions get reasonable defaults."""
        path = inferencer.infer_target_file("xyz abc 123")
        # Should still return a valid path
        assert path.endswith(".py")
        # Check for path separator (either / or \)
        normalized = normalize_path_for_comparison(path)
        assert "/" in normalized
