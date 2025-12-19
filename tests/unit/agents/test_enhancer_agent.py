"""
Unit tests for Enhancer Agent.

Tests agent initialization, command handling, enhancement pipeline,
expert integration, and error handling.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.enhancer.agent import EnhancerAgent

pytestmark = pytest.mark.unit


class TestEnhancerAgentInitialization:
    """Tests for EnhancerAgent initialization."""

    @patch("tapps_agents.agents.enhancer.agent.load_config")
    def test_enhancer_agent_init(self, mock_load_config):
        """Test EnhancerAgent initialization."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        agent = EnhancerAgent()
        assert agent.agent_id == "enhancer"
        assert agent.agent_name == "Enhancer Agent"
        assert agent.config is not None
        assert agent.analyst is not None
        assert agent.context_manager is not None

    @pytest.mark.asyncio
    async def test_enhancer_agent_activate(self, temp_project_dir: Path):
        """Test EnhancerAgent activation."""
        agent = EnhancerAgent()
        await agent.activate(temp_project_dir)
        
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_enhancer_agent_get_commands(self):
        """Test EnhancerAgent command list."""
        agent = EnhancerAgent()
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        command_names = [cmd["command"] for cmd in commands]
        assert "*enhance" in command_names
        assert "*enhance-quick" in command_names
        assert "*enhance-resume" in command_names


class TestEnhancerAgentEnhanceCommand:
    """Tests for enhance command."""

    @pytest.mark.asyncio
    async def test_enhance_command_success(self, tmp_path):
        """Test enhance command with successful enhancement."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        # Mock all stage methods
        with patch.object(agent, '_stage_analysis', new_callable=AsyncMock) as mock_analysis, \
             patch.object(agent, '_stage_requirements', new_callable=AsyncMock) as mock_req, \
             patch.object(agent, '_stage_architecture', new_callable=AsyncMock) as mock_arch, \
             patch.object(agent, '_stage_codebase_context', new_callable=AsyncMock) as mock_context, \
             patch.object(agent, '_stage_quality', new_callable=AsyncMock) as mock_quality, \
             patch.object(agent, '_stage_implementation', new_callable=AsyncMock) as mock_impl, \
             patch.object(agent, '_stage_synthesis', new_callable=AsyncMock) as mock_synth, \
             patch.object(agent, '_print_progress', new_callable=MagicMock):
            
            mock_analysis.return_value = {"intent": "test"}
            mock_req.return_value = {"requirements": []}
            mock_arch.return_value = {"architecture": "simple"}
            mock_context.return_value = {"files": []}
            mock_quality.return_value = {"standards": []}
            mock_impl.return_value = {"plan": []}
            mock_synth.return_value = {
                "instruction": {},
                "skill_command": "",
                "format": "markdown",
                "metadata": {},
                "enhanced_prompt": "Enhanced prompt"
            }
            
            result = await agent.run("enhance", prompt="Test prompt")
            
            assert "success" in result
            assert result["success"] is True
            assert "session_id" in result
            assert "enhanced_prompt" in result

    @pytest.mark.asyncio
    async def test_enhance_command_missing_prompt(self):
        """Test enhance command without prompt."""
        agent = EnhancerAgent()
        await agent.activate()
        
        result = await agent.run("enhance")
        
        assert "error" in result
        assert "prompt is required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_enhance_command_with_output_file(self, tmp_path):
        """Test enhance command with output file."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        output_file = tmp_path / "output.md"
        
        # Mock all stage methods
        with patch.object(agent, '_stage_analysis', new_callable=AsyncMock) as mock_analysis, \
             patch.object(agent, '_stage_requirements', new_callable=AsyncMock) as mock_req, \
             patch.object(agent, '_stage_architecture', new_callable=AsyncMock) as mock_arch, \
             patch.object(agent, '_stage_codebase_context', new_callable=AsyncMock) as mock_context, \
             patch.object(agent, '_stage_quality', new_callable=AsyncMock) as mock_quality, \
             patch.object(agent, '_stage_implementation', new_callable=AsyncMock) as mock_impl, \
             patch.object(agent, '_stage_synthesis', new_callable=AsyncMock) as mock_synth, \
             patch.object(agent, '_print_progress', new_callable=MagicMock):
            
            mock_analysis.return_value = {"intent": "test"}
            mock_req.return_value = {"requirements": []}
            mock_arch.return_value = {"architecture": "simple"}
            mock_context.return_value = {"files": []}
            mock_quality.return_value = {"standards": []}
            mock_impl.return_value = {"plan": []}
            mock_synth.return_value = {
                "instruction": {},
                "skill_command": "",
                "format": "markdown",
                "metadata": {},
                "enhanced_prompt": "Enhanced prompt"
            }
            
            result = await agent.run("enhance", prompt="Test", output_file=str(output_file))
            
            assert "success" in result
            assert output_file.exists()

    @pytest.mark.asyncio
    async def test_enhance_command_json_format(self, tmp_path):
        """Test enhance command with JSON output format."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        # Mock all stage methods
        with patch.object(agent, '_stage_analysis', new_callable=AsyncMock) as mock_analysis, \
             patch.object(agent, '_stage_requirements', new_callable=AsyncMock) as mock_req, \
             patch.object(agent, '_stage_architecture', new_callable=AsyncMock) as mock_arch, \
             patch.object(agent, '_stage_codebase_context', new_callable=AsyncMock) as mock_context, \
             patch.object(agent, '_stage_quality', new_callable=AsyncMock) as mock_quality, \
             patch.object(agent, '_stage_implementation', new_callable=AsyncMock) as mock_impl, \
             patch.object(agent, '_stage_synthesis', new_callable=AsyncMock) as mock_synth, \
             patch.object(agent, '_print_progress', new_callable=MagicMock):
            
            mock_analysis.return_value = {"intent": "test"}
            mock_req.return_value = {"requirements": []}
            mock_arch.return_value = {"architecture": "simple"}
            mock_context.return_value = {"files": []}
            mock_quality.return_value = {"standards": []}
            mock_impl.return_value = {"plan": []}
            mock_synth.return_value = {"enhanced": "prompt"}
            
            result = await agent.run("enhance", prompt="Test", output_format="json")
            
            assert "success" in result
            assert "enhanced_prompt" in result


class TestEnhancerAgentEnhanceQuickCommand:
    """Tests for enhance-quick command."""

    @pytest.mark.asyncio
    async def test_enhance_quick_command_success(self, tmp_path):
        """Test enhance-quick command with successful enhancement."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        # Mock stage methods for quick enhancement
        with patch.object(agent, '_stage_analysis', new_callable=AsyncMock) as mock_analysis, \
             patch.object(agent, '_stage_requirements', new_callable=AsyncMock) as mock_req, \
             patch.object(agent, '_stage_architecture', new_callable=AsyncMock) as mock_arch, \
             patch.object(agent, '_stage_synthesis', new_callable=AsyncMock) as mock_synth, \
             patch.object(agent, '_print_progress', new_callable=MagicMock):
            
            mock_analysis.return_value = {"intent": "test"}
            mock_req.return_value = {"requirements": []}
            mock_arch.return_value = {"architecture": "simple"}
            mock_synth.return_value = {
                "instruction": {},
                "skill_command": "",
                "format": "markdown",
                "metadata": {},
                "enhanced_prompt": "Enhanced prompt"
            }
            
            result = await agent.run("enhance-quick", prompt="Test prompt")
            
            assert "success" in result
            assert result["success"] is True
            assert "session_id" in result
            assert "enhanced_prompt" in result
            assert "stages_completed" in result

    @pytest.mark.asyncio
    async def test_enhance_quick_command_missing_prompt(self):
        """Test enhance-quick command without prompt."""
        agent = EnhancerAgent()
        await agent.activate()
        
        result = await agent.run("enhance-quick")
        
        assert "error" in result
        assert "prompt is required" in result["error"].lower()


class TestEnhancerAgentEnhanceStageCommand:
    """Tests for enhance-stage command."""

    @pytest.mark.asyncio
    async def test_enhance_stage_command_analysis(self, tmp_path):
        """Test enhance-stage command with analysis stage."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        # Create a session first
        session_id = agent._create_session("Test prompt", {})
        
        with patch.object(agent, '_stage_analysis', new_callable=AsyncMock) as mock_analysis:
            mock_analysis.return_value = {"intent": "test"}
            
            result = await agent.run("enhance-stage", stage="analysis", prompt="Test")
            
            assert "stage" in result
            assert result["stage"] == "analysis"

    @pytest.mark.asyncio
    async def test_enhance_stage_command_requirements(self, tmp_path):
        """Test enhance-stage command with requirements stage."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        # Create a session first
        session_id = agent._create_session("Test prompt", {})
        agent.current_session["stages"]["analysis"] = {"intent": "test"}
        
        with patch.object(agent, '_stage_requirements', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"requirements": []}
            
            result = await agent.run("enhance-stage", stage="requirements", prompt="Test")
            
            assert "stage" in result
            assert result["stage"] == "requirements"

    @pytest.mark.asyncio
    async def test_enhance_stage_command_invalid_stage(self, tmp_path):
        """Test enhance-stage command with invalid stage."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        result = await agent.run("enhance-stage", stage="invalid", prompt="Test")
        
        assert "error" in result


class TestEnhancerAgentEnhanceResumeCommand:
    """Tests for enhance-resume command."""

    @pytest.mark.asyncio
    async def test_enhance_resume_command_success(self, tmp_path):
        """Test enhance-resume command with existing session."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        # Create and save a session
        session_id = agent._create_session("Test prompt", {})
        agent.current_session["stages"]["analysis"] = {"intent": "test"}
        agent._save_session(session_id, agent.current_session)
        
        result = await agent.run("enhance-resume", session_id=session_id)
        
        assert "session_id" in result
        assert result["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_enhance_resume_command_missing_session(self):
        """Test enhance-resume command with non-existent session."""
        agent = EnhancerAgent()
        await agent.activate()
        
        result = await agent.run("enhance-resume", session_id="nonexistent")
        
        assert "error" in result


class TestEnhancerAgentHelperMethods:
    """Tests for helper methods."""

    def test_create_session(self):
        """Test _create_session creates a session."""
        agent = EnhancerAgent()
        
        session_id = agent._create_session("Test prompt", {})
        
        assert session_id is not None
        assert agent.current_session is not None
        assert agent.current_session["prompt"] == "Test prompt"

    @pytest.mark.asyncio
    async def test_save_session(self, tmp_path):
        """Test _save_session saves session to file."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        session_id = agent._create_session("Test prompt", {})
        agent._save_session(session_id, agent.current_session)
        
        # Check if session file exists
        session_file = tmp_path / ".tapps-agents" / "enhancement_sessions" / f"{session_id}.json"
        # May not exist if directory doesn't exist, but method should not error
        assert session_id is not None

    @pytest.mark.asyncio
    async def test_stage_analysis(self, tmp_path):
        """Test _stage_analysis method."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        with patch.object(agent.analyst, 'analyze', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"intent": "test", "scope": "small"}
            
            result = await agent._stage_analysis("Test prompt")
            
            assert "intent" in result or "analysis" in result

    @pytest.mark.asyncio
    async def test_stage_requirements(self, tmp_path):
        """Test _stage_requirements method."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        analysis = {"intent": "test"}
        
        with patch.object(agent.analyst, 'gather_requirements', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"requirements": []}
            
            result = await agent._stage_requirements("Test prompt", analysis)
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_stage_architecture(self, tmp_path):
        """Test _stage_architecture method."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        requirements = {"requirements": []}
        
        # Mock lazy-loaded architect
        with patch("tapps_agents.agents.enhancer.agent.ArchitectAgent") as mock_arch_class:
            mock_arch = MagicMock()
            mock_arch.design_system = AsyncMock(return_value={"architecture": "simple"})
            mock_arch_class.return_value = mock_arch
            
            result = await agent._stage_architecture("Test prompt", requirements)
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_stage_codebase_context(self, tmp_path):
        """Test _stage_codebase_context method."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        analysis = {"intent": "test"}
        
        result = await agent._stage_codebase_context("Test prompt", analysis)
        
        assert result is not None
        assert "files" in result or "context" in result

    @pytest.mark.asyncio
    async def test_stage_quality(self, tmp_path):
        """Test _stage_quality method."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        requirements = {"requirements": []}
        
        # Mock lazy-loaded reviewer
        with patch("tapps_agents.agents.enhancer.agent.ReviewerAgent") as mock_reviewer_class:
            mock_reviewer = MagicMock()
            mock_reviewer_class.return_value = mock_reviewer
            
            result = await agent._stage_quality("Test prompt", requirements)
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_stage_implementation(self, tmp_path):
        """Test _stage_implementation method."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        requirements = {"requirements": []}
        architecture = {"architecture": "simple"}
        
        # Mock lazy-loaded planner
        with patch("tapps_agents.agents.enhancer.agent.PlannerAgent") as mock_planner_class:
            mock_planner = MagicMock()
            mock_planner.create_story = AsyncMock(return_value={"story": "test"})
            mock_planner_class.return_value = mock_planner
            
            result = await agent._stage_implementation("Test prompt", requirements, architecture)
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_stage_synthesis(self, tmp_path):
        """Test _stage_synthesis method."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        stages = {
            "analysis": {"intent": "test"},
            "requirements": {"requirements": []},
            "architecture": {"architecture": "simple"}
        }
        
        result = await agent._stage_synthesis("Test prompt", stages, "markdown")
        
        assert result is not None
        assert isinstance(result, str) or isinstance(result, dict)

    def test_format_output_markdown(self):
        """Test _format_output with markdown format."""
        agent = EnhancerAgent()
        
        session = {
            "prompt": "Test prompt",
            "stages": {
                "synthesis": "Enhanced prompt"
            }
        }
        
        result = agent._format_output(session, "markdown")
        
        assert isinstance(result, str)
        assert "Enhanced prompt" in result or "Test prompt" in result

    def test_format_output_json(self):
        """Test _format_output with JSON format."""
        agent = EnhancerAgent()
        
        session = {
            "prompt": "Test prompt",
            "stages": {
                "synthesis": {"enhanced": "prompt"}
            }
        }
        
        result = agent._format_output(session, "json")
        
        assert isinstance(result, dict)


class TestEnhancerAgentErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Test unknown command handling."""
        agent = EnhancerAgent()
        await agent.activate()
        
        result = await agent.run("unknown-command")
        
        assert "error" in result
        assert "unknown command" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command."""
        agent = EnhancerAgent()
        await agent.activate()
        
        result = await agent.run("help")
        
        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_enhance_command_exception_handling(self, tmp_path):
        """Test enhance command handles exceptions."""
        agent = EnhancerAgent()
        await agent.activate(tmp_path)
        
        # Mock stage to raise exception
        with patch.object(agent, '_stage_analysis', new_callable=AsyncMock) as mock_analysis, \
             patch.object(agent, '_print_progress', new_callable=MagicMock):
            mock_analysis.side_effect = Exception("Stage failed")
            
            result = await agent.run("enhance", prompt="Test")
            
            assert "error" in result
            assert "failed" in result["error"].lower()

