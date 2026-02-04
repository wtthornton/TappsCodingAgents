"""
Tests for Context7 enhancements in agent_base.py

Tests the _auto_fetch_context7_docs method and Context7 integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.config import ProjectConfig


class MockAgent(BaseAgent):
    """Mock agent for testing BaseAgent functionality."""
    
    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(agent_id="test_agent", agent_name="Test Agent", config=config)
    
    async def run(self, command: str, **kwargs):
        """Required abstract method implementation."""
        return {"success": True}


class TestAutoFetchContext7Docs:
    """Test _auto_fetch_context7_docs method."""
    
    @pytest.mark.asyncio
    async def test_auto_fetch_context7_docs_disabled(self):
        """Test that method returns empty dict when Context7 is disabled."""
        agent = MockAgent()
        agent.context7 = None
        
        result = await agent._auto_fetch_context7_docs(code="import fastapi")
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_auto_fetch_context7_docs_from_code(self):
        """Test library detection from code."""
        agent = MockAgent()
        
        # Mock Context7 helper
        mock_helper = MagicMock()
        mock_helper.enabled = True
        mock_helper.detect_libraries = MagicMock(return_value=["fastapi", "pydantic"])
        mock_helper.get_documentation_for_libraries = AsyncMock(return_value={
            "fastapi": {"content": "FastAPI docs", "source": "Context7"},
            "pydantic": {"content": "Pydantic docs", "source": "Context7"}
        })
        agent.context7 = mock_helper
        
        result = await agent._auto_fetch_context7_docs(code="from fastapi import FastAPI\nfrom pydantic import BaseModel")
        
        assert "fastapi" in result
        assert "pydantic" in result
        mock_helper.detect_libraries.assert_called_once()
        mock_helper.get_documentation_for_libraries.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auto_fetch_context7_docs_from_prompt(self):
        """Test library detection from prompt text."""
        agent = MockAgent()
        
        mock_helper = MagicMock()
        mock_helper.enabled = True
        mock_helper.detect_libraries = MagicMock(return_value=["pytest"])
        mock_helper.get_documentation_for_libraries = AsyncMock(return_value={
            "pytest": {"content": "Pytest docs", "source": "Context7"}
        })
        agent.context7 = mock_helper
        
        result = await agent._auto_fetch_context7_docs(prompt="Use pytest to write tests")
        
        assert "pytest" in result
        mock_helper.detect_libraries.assert_called_once_with(
            code=None, prompt="Use pytest to write tests", error_message=None, language="python"
        )
    
    @pytest.mark.asyncio
    async def test_auto_fetch_context7_docs_from_error(self):
        """Test library detection from error messages."""
        agent = MockAgent()
        
        mock_helper = MagicMock()
        mock_helper.enabled = True
        mock_helper.detect_libraries = MagicMock(return_value=["fastapi"])
        mock_helper.get_documentation_for_libraries = AsyncMock(return_value={
            "fastapi": {"content": "FastAPI error handling", "source": "Context7"}
        })
        agent.context7 = mock_helper
        
        error_msg = "FastAPI HTTPException: Route not found"
        result = await agent._auto_fetch_context7_docs(error_message=error_msg)
        
        assert "fastapi" in result
        mock_helper.detect_libraries.assert_called_once_with(
            code=None, prompt=None, error_message=error_msg, language="python"
        )
    
    @pytest.mark.asyncio
    async def test_auto_fetch_context7_docs_all_sources(self):
        """Test library detection from all sources combined."""
        agent = MockAgent()
        
        mock_helper = MagicMock()
        mock_helper.enabled = True
        mock_helper.detect_libraries = MagicMock(return_value=["fastapi", "pytest", "pydantic"])
        mock_helper.get_documentation_for_libraries = AsyncMock(return_value={
            "fastapi": {"content": "FastAPI docs", "source": "Context7"},
            "pytest": {"content": "Pytest docs", "source": "Context7"},
            "pydantic": {"content": "Pydantic docs", "source": "Context7"}
        })
        agent.context7 = mock_helper
        
        result = await agent._auto_fetch_context7_docs(
            code="from fastapi import FastAPI",
            prompt="Use pytest for testing",
            error_message="pydantic.ValidationError"
        )
        
        assert len(result) == 3
        mock_helper.detect_libraries.assert_called_once_with(
            code="from fastapi import FastAPI",
            prompt="Use pytest for testing",
            error_message="pydantic.ValidationError",
            language="python"
        )
    
    @pytest.mark.asyncio
    async def test_auto_fetch_context7_docs_no_libraries_detected(self):
        """Test that method returns empty dict when no libraries detected."""
        agent = MockAgent()
        
        mock_helper = MagicMock()
        mock_helper.enabled = True
        mock_helper.detect_libraries = MagicMock(return_value=[])
        agent.context7 = mock_helper
        
        result = await agent._auto_fetch_context7_docs(code="print('hello')")
        
        assert result == {}
        mock_helper.get_documentation_for_libraries.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auto_fetch_context7_docs_deduplicates_libraries(self):
        """Test that duplicate libraries are deduplicated."""
        agent = MockAgent()
        
        mock_helper = MagicMock()
        mock_helper.enabled = True
        # Simulate duplicate detection
        mock_helper.detect_libraries = MagicMock(return_value=["fastapi", "fastapi", "pydantic"])
        mock_helper.get_documentation_for_libraries = AsyncMock(return_value={
            "fastapi": {"content": "FastAPI docs", "source": "Context7"},
            "pydantic": {"content": "Pydantic docs", "source": "Context7"}
        })
        agent.context7 = mock_helper
        
        await agent._auto_fetch_context7_docs(code="import fastapi")
        
        # Should only fetch once per library
        call_args = mock_helper.get_documentation_for_libraries.call_args
        libraries_arg = call_args[1]["libraries"]
        assert len(libraries_arg) == 2  # Deduplicated
        assert "fastapi" in libraries_arg
        assert "pydantic" in libraries_arg

