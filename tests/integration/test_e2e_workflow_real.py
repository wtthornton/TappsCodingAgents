"""
End-to-end integration tests.

These tests verify complete workflows from start to finish.
They test:
- Agent initialization
- Instruction object creation
- File operations
- Result processing
"""

import pytest

from tapps_agents.agents.reviewer.agent import ReviewerAgent

pytestmark = pytest.mark.integration


@pytest.mark.e2e
@pytest.mark.asyncio
class TestE2EWorkflowReal:
    """End-to-end workflow tests."""

    @pytest.fixture
    def test_project(self, tmp_path):
        """Create a minimal test project structure."""
        project = tmp_path / "test_project"
        project.mkdir()
        
        # Minimal source file for faster processing
        src_file = project / "main.py"
        src_file.write_text("def hello(): return True\n")
        
        # Create config directory
        config_dir = project / ".tapps-agents"
        config_dir.mkdir()
        
        return project

    @pytest.fixture
    def test_project(self, tmp_path):
        """Create a minimal test project structure."""
        project = tmp_path / "test_project"
        project.mkdir()
        
        src_file = project / "main.py"
        src_file.write_text("def hello(): return True\n")
        
        config_dir = project / ".tapps-agents"
        config_dir.mkdir()
        
        return project

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_full_score_workflow(self, test_project):
        """Test complete score workflow."""
        reviewer = ReviewerAgent()
        
        source_file = test_project / "main.py"
        
        try:
            await reviewer.activate(test_project)
            assert reviewer.config is not None
            
            result = await reviewer.run("score", file=str(source_file))
            
            assert "file" in result
            assert "scoring" in result
            assert "overall_score" in result["scoring"]
            assert 0 <= result["scoring"]["overall_score"] <= 100
        finally:
            await reviewer.close()

