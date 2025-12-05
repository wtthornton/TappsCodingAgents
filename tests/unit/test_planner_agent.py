"""
Unit tests for PlannerAgent helper methods.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from tapps_agents.agents.planner import PlannerAgent
from tapps_agents.core.mal import MAL


@pytest.mark.unit
class TestPlannerAgentHelpers:
    """Test cases for PlannerAgent helper methods."""
    
    @pytest.fixture
    def planner_agent(self, mock_mal):
        """Create a PlannerAgent instance for testing."""
        return PlannerAgent(mal=mock_mal)
    
    def test_generate_story_id_basic(self, planner_agent):
        """Test story ID generation from description."""
        description = "User should be able to log in"
        story_id = planner_agent._generate_story_id(description)
        
        assert isinstance(story_id, str)
        assert story_id.startswith("story-")
        assert "log" in story_id.lower() or "in" in story_id.lower()
    
    def test_generate_story_id_with_epic(self, planner_agent):
        """Test story ID generation with epic prefix."""
        description = "Add shopping cart"
        epic = "checkout"
        story_id = planner_agent._generate_story_id(description, epic=epic)
        
        assert isinstance(story_id, str)
        assert story_id.startswith("checkout-")
        assert "cart" in story_id.lower() or "shopping" in story_id.lower()
    
    def test_generate_story_id_special_characters(self, planner_agent):
        """Test story ID generation handles special characters."""
        description = "User's profile & settings!!!"
        story_id = planner_agent._generate_story_id(description)
        
        assert isinstance(story_id, str)
        assert " " not in story_id
        assert "'" not in story_id
        assert "&" not in story_id
        assert "!" not in story_id
    
    def test_extract_title_short(self, planner_agent):
        """Test title extraction from short description."""
        description = "User login feature"
        title = planner_agent._extract_title(description)
        
        assert title == "User login feature"
        assert len(title) <= 60
    
    def test_extract_title_long(self, planner_agent):
        """Test title extraction from long description."""
        description = "This is a very long description that exceeds the maximum length limit of 60 characters and should be truncated"
        title = planner_agent._extract_title(description)
        
        assert len(title) <= 60
        assert title.endswith("...")
    
    def test_extract_title_multiline(self, planner_agent):
        """Test title extraction from multiline description."""
        description = "First line\nSecond line\nThird line"
        title = planner_agent._extract_title(description)
        
        assert title == "First line"
    
    def test_infer_domain_backend(self, planner_agent):
        """Test domain inference for backend."""
        description = "Create API endpoint for user authentication"
        domain = planner_agent._infer_domain(description)
        
        assert domain == "backend"
    
    def test_infer_domain_frontend(self, planner_agent):
        """Test domain inference for frontend."""
        description = "Create UI component for user login page"
        domain = planner_agent._infer_domain(description)
        
        assert domain == "frontend"
    
    def test_infer_domain_testing(self, planner_agent):
        """Test domain inference for testing."""
        description = "Add test specs for authentication feature"
        domain = planner_agent._infer_domain(description)
        
        assert domain == "testing"
    
    def test_infer_domain_documentation(self, planner_agent):
        """Test domain inference for documentation."""
        description = "Write user documentation"
        domain = planner_agent._infer_domain(description)
        
        assert domain == "documentation"
    
    def test_infer_domain_general(self, planner_agent):
        """Test domain inference defaults to general."""
        description = "Some random feature"
        domain = planner_agent._infer_domain(description)
        
        assert domain == "general"
    
    def test_indent_yaml_multiline(self, planner_agent):
        """Test YAML multiline indentation."""
        text = "Line 1\nLine 2\nLine 3"
        indented = planner_agent._indent_yaml_multiline(text, indent=2)
        
        assert indented.startswith("  Line 1")
        assert "  Line 2" in indented
        assert "  Line 3" in indented
    
    def test_read_story_metadata_valid(self, planner_agent, tmp_path: Path):
        """Test reading story metadata from valid file."""
        story_file = tmp_path / "story-test.md"
        content = """# Test Story

```yaml
story_id: test-story
title: Test Story
epic: test-epic
status: draft
```

Content here
"""
        story_file.write_text(content)
        
        metadata = planner_agent._read_story_metadata(story_file)
        
        assert metadata["story_id"] == "test-story"
        assert metadata["title"] == "Test Story"
        assert metadata["epic"] == "test-epic"
        assert metadata["status"] == "draft"
    
    def test_read_story_metadata_invalid_yaml(self, planner_agent, tmp_path: Path):
        """Test reading story metadata from file with invalid YAML."""
        story_file = tmp_path / "story-invalid.md"
        content = """# Test Story

```yaml
story_id: test-story
title: [invalid yaml
```

Content here
"""
        story_file.write_text(content)
        
        metadata = planner_agent._read_story_metadata(story_file)
        
        assert metadata == {}
    
    def test_read_story_metadata_no_yaml(self, planner_agent, tmp_path: Path):
        """Test reading story metadata from file without YAML."""
        story_file = tmp_path / "story-no-yaml.md"
        content = """# Test Story

Just regular markdown content.
"""
        story_file.write_text(content)
        
        metadata = planner_agent._read_story_metadata(story_file)
        
        assert metadata == {}

