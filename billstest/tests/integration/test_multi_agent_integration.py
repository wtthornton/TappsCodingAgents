"""
Multi-agent integration tests.

Tests workflows that involve multiple agents working together.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.integration


class TestMultiAgentWorkflow:
    """Test cases for multi-agent workflows."""

    @pytest.fixture
    def test_project(self, tmp_path):
        """Create a minimal test project structure."""
        project = tmp_path / "test_project"
        project.mkdir()
        
        # Create source file
        src_file = project / "main.py"
        src_file.write_text("def hello(): return True\n")
        
        # Create config directory
        config_dir = project / ".tapps-agents"
        config_dir.mkdir()
        
        return project

    @pytest.mark.asyncio
    async def test_analyst_to_planner_workflow(self, test_project):
        """Test workflow from analyst to planner."""
        from tapps_agents.agents.analyst.agent import AnalystAgent
        from tapps_agents.agents.planner.agent import PlannerAgent
        from tapps_agents.core.config import ProjectConfig
        
        with patch("tapps_agents.agents.analyst.agent.MAL") as mock_mal_class:
            mock_mal = MagicMock()
            mock_mal.generate = AsyncMock(return_value="Mocked requirements")
            mock_mal_class.return_value = mock_mal
            
            # Analyst gathers requirements
            analyst = AnalystAgent()
            analyst.mal = mock_mal
            await analyst.activate(test_project)
            
            analyst_result = await analyst.run(
                "gather-requirements",
                description="Test feature"
            )
            
            assert analyst_result.get("success") is True
            
            # Planner creates plan from requirements
            planner = PlannerAgent(mal=mock_mal)
            await planner.activate(test_project)
            
            planner_result = await planner.run(
                "plan",
                description="Test feature",
                requirements=analyst_result.get("requirements", "")
            )
            
            assert planner_result.get("success") is True

    @pytest.mark.asyncio
    async def test_implementer_to_reviewer_workflow(self, test_project):
        """Test workflow from implementer to reviewer."""
        from tapps_agents.agents.implementer.agent import ImplementerAgent
        from tapps_agents.agents.reviewer.agent import ReviewerAgent
        
        with patch("tapps_agents.agents.implementer.agent.MAL") as mock_mal_class:
            mock_mal = MagicMock()
            mock_mal.generate = AsyncMock(return_value="def test(): pass")
            mock_mal_class.return_value = mock_mal
            
            # Implementer generates code
            implementer = ImplementerAgent()
            implementer.mal = mock_mal
            implementer.code_generator = MagicMock()
            implementer.code_generator.generate = AsyncMock(return_value="def test(): pass")
            await implementer.activate(test_project)
            
            code_file = test_project / "generated.py"
            implementer_result = await implementer.run(
                "generate-code",
                description="Create test function",
                output_file=str(code_file)
            )
            
            assert implementer_result.get("success") is True
            
            # Reviewer reviews the code
            reviewer = ReviewerAgent()
            reviewer.mal = mock_mal
            await reviewer.activate(test_project)
            
            if code_file.exists():
                review_result = await reviewer.run("score", file=str(code_file))
                assert "scoring" in review_result or "file" in review_result

    @pytest.mark.asyncio
    async def test_architect_to_designer_workflow(self, test_project):
        """Test workflow from architect to designer."""
        from tapps_agents.agents.architect.agent import ArchitectAgent
        from tapps_agents.agents.designer.agent import DesignerAgent
        
        with patch("tapps_agents.agents.architect.agent.MAL") as mock_mal_class:
            mock_mal = MagicMock()
            mock_mal.generate = AsyncMock(return_value="System architecture design")
            mock_mal_class.return_value = mock_mal
            
            # Architect designs system
            architect = ArchitectAgent()
            architect.mal = mock_mal
            architect.expert_registry = None
            architect.context7 = None
            await architect.activate(test_project)
            
            arch_result = await architect.run(
                "design-system",
                requirements="Test system"
            )
            
            assert arch_result.get("success") is True
            
            # Designer creates API design
            designer = DesignerAgent()
            designer.mal = mock_mal
            designer.expert_registry = None
            designer.context7 = None
            await designer.activate(test_project)
            
            design_result = await designer.run(
                "design-api",
                requirements="Test API"
            )
            
            assert design_result.get("success") is True

    @pytest.mark.asyncio
    async def test_planner_to_implementer_to_tester_workflow(self, test_project):
        """Test complete workflow: planner -> implementer -> tester."""
        from tapps_agents.agents.implementer.agent import ImplementerAgent
        from tapps_agents.agents.planner.agent import PlannerAgent
        from tapps_agents.agents.tester.agent import TesterAgent
        
        with patch("tapps_agents.agents.planner.agent.MAL") as mock_mal_class:
            mock_mal = MagicMock()
            mock_mal.generate = AsyncMock(return_value="Test plan")
            mock_mal_class.return_value = mock_mal
            
            # Planner creates plan
            planner = PlannerAgent(mal=mock_mal)
            await planner.activate(test_project)
            
            plan_result = await planner.run("plan", description="Test feature")
            assert plan_result.get("success") is True
            
            # Implementer implements
            implementer = ImplementerAgent()
            implementer.mal = mock_mal
            implementer.code_generator = MagicMock()
            implementer.code_generator.generate = AsyncMock(return_value="def test(): pass")
            implementer.reviewer = None
            implementer.expert_registry = None
            implementer.context7 = None
            await implementer.activate(test_project)
            
            impl_result = await implementer.run(
                "generate-code",
                description="Implement feature"
            )
            assert impl_result.get("success") is True
            
            # Tester generates tests
            tester = TesterAgent(mal=mock_mal)
            tester.test_generator = MagicMock()
            tester.test_generator.generate = AsyncMock(return_value="def test_feature(): pass")
            await tester.activate(test_project)
            
            test_result = await tester.run(
                "generate-tests",
                file="test.py"
            )
            assert test_result.get("success") is True

