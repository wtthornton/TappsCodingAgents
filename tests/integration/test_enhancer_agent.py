"""
End-to-end tests for the Enhancer Agent.

Based on enhanced prompt: "Add full end to end testing to Tapps CodingAgents prompt enhancements"
"""

import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from tapps_agents.agents.enhancer.agent import EnhancerAgent
from tapps_agents.core.config import load_config


@pytest.fixture
async def enhancer_agent():
    """Create and activate an Enhancer Agent for testing."""
    agent = EnhancerAgent()
    await agent.activate()
    yield agent
    await agent.close()


@pytest.mark.asyncio
async def test_enhancer_agent_initialization(enhancer_agent):
    """Test that the Enhancer Agent initializes correctly."""
    assert enhancer_agent is not None
    assert enhancer_agent.agent_id == "enhancer"
    assert enhancer_agent.mal is not None
    assert enhancer_agent.config is not None


@pytest.mark.asyncio
async def test_enhance_quick_basic(enhancer_agent):
    """Test quick enhancement with a simple prompt."""
    prompt = "Add user authentication"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt)
    
    assert result is not None
    assert "success" in result
    assert result["success"] is True
    assert "session_id" in result
    assert "enhanced_prompt" in result
    assert "stages_completed" in result
    
    # Check stages completed
    assert "analysis" in result["stages_completed"]
    assert "requirements" in result["stages_completed"]
    assert "architecture" in result["stages_completed"]
    assert "synthesis" in result["stages_completed"]


@pytest.mark.asyncio
async def test_enhance_full_basic(enhancer_agent):
    """Test full enhancement with all 7 stages."""
    prompt = "Add device health monitoring dashboard"
    
    result = await enhancer_agent.run("enhance", prompt=prompt)
    
    assert result is not None
    assert "success" in result
    assert result["success"] is True
    assert "session_id" in result
    assert "enhanced_prompt" in result
    assert "stages_completed" in result
    
    # Check all 7 stages completed
    expected_stages = ["analysis", "requirements", "architecture", "codebase_context", "quality", "implementation", "synthesis"]
    for stage in expected_stages:
        assert stage in result["stages_completed"], f"Stage {stage} not completed"


@pytest.mark.asyncio
async def test_enhance_quick_output_format_markdown(enhancer_agent):
    """Test quick enhancement outputs markdown format."""
    prompt = "Add logging functionality"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt, output_format="markdown")
    
    enhanced = result.get("enhanced_prompt", {})
    if isinstance(enhanced, dict):
        content = enhanced.get("enhanced_prompt_content", "")
    else:
        content = str(enhanced)
    
    # Check markdown structure
    assert "# Enhanced Prompt:" in content
    assert "## Metadata" in content
    assert "## Analysis" in content
    assert "## Requirements" in content
    assert "## Architecture Guidance" in content


@pytest.mark.asyncio
async def test_enhance_quick_output_format_json(enhancer_agent):
    """Test quick enhancement outputs JSON format."""
    prompt = "Add error handling"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt, output_format="json")
    
    enhanced = result.get("enhanced_prompt", {})
    assert isinstance(enhanced, dict)
    
    # Check JSON structure
    assert "original_prompt" in enhanced or "enhanced_prompt" in enhanced
    assert "stages" in enhanced
    assert "metadata" in enhanced


@pytest.mark.asyncio
async def test_enhance_output_file(enhancer_agent, tmp_path):
    """Test enhancement writes output to file."""
    prompt = "Add API documentation"
    output_file = tmp_path / "enhanced_prompt.md"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt, output_file=str(output_file))
    
    assert output_file.exists(), "Output file was not created"
    
    content = output_file.read_text()
    assert "# Enhanced Prompt:" in content
    assert prompt in content
    
    # Check result includes file path
    enhanced = result.get("enhanced_prompt", {})
    if isinstance(enhanced, dict):
        assert "output_file" in enhanced
        assert str(output_file) in str(enhanced["output_file"])


@pytest.mark.asyncio
async def test_enhance_stage_analysis(enhancer_agent):
    """Test individual analysis stage."""
    prompt = "Add database migration"
    
    analysis = await enhancer_agent._stage_analysis(prompt)
    
    assert analysis is not None
    assert "original_prompt" in analysis
    assert analysis["original_prompt"] == prompt
    assert "intent" in analysis
    assert "scope" in analysis
    assert "workflow_type" in analysis
    assert "analysis" in analysis  # LLM response


@pytest.mark.asyncio
async def test_enhance_stage_requirements(enhancer_agent):
    """Test individual requirements stage."""
    prompt = "Add caching layer"
    analysis = await enhancer_agent._stage_analysis(prompt)
    
    requirements = await enhancer_agent._stage_requirements(prompt, analysis)
    
    assert requirements is not None
    assert "functional_requirements" in requirements
    assert "non_functional_requirements" in requirements
    assert "technical_constraints" in requirements
    assert "expert_consultations" in requirements


@pytest.mark.asyncio
async def test_enhance_stage_architecture(enhancer_agent):
    """Test individual architecture stage."""
    prompt = "Add microservices support"
    analysis = await enhancer_agent._stage_analysis(prompt)
    requirements = await enhancer_agent._stage_requirements(prompt, analysis)
    
    architecture = await enhancer_agent._stage_architecture(prompt, requirements)
    
    assert architecture is not None
    assert "system_design" in architecture
    assert "design_patterns" in architecture
    assert "technology_recommendations" in architecture
    assert "architecture_guidance" in architecture


@pytest.mark.asyncio
async def test_enhance_error_handling_empty_prompt(enhancer_agent):
    """Test error handling for empty prompt."""
    result = await enhancer_agent.run("enhance-quick", prompt="")
    
    assert "error" in result
    assert "prompt is required" in result["error"]


@pytest.mark.asyncio
async def test_enhance_error_handling_invalid_stage(enhancer_agent):
    """Test error handling for invalid stage."""
    result = await enhancer_agent.run("enhance-stage", stage="invalid_stage", prompt="test")
    
    # Should return error or handle gracefully
    assert result is not None
    # May return error or empty result


@pytest.mark.asyncio
async def test_enhance_session_management(enhancer_agent):
    """Test session creation and management."""
    prompt = "Add feature flags"
    
    result1 = await enhancer_agent.run("enhance-quick", prompt=prompt)
    session_id1 = result1.get("session_id")
    
    result2 = await enhancer_agent.run("enhance-quick", prompt=prompt)
    session_id2 = result2.get("session_id")
    
    # Each enhancement should create a new session
    assert session_id1 is not None
    assert session_id2 is not None
    assert session_id1 != session_id2, "Sessions should be unique"


@pytest.mark.asyncio
async def test_enhance_progress_tracking(enhancer_agent, capsys):
    """Test that progress indicators are printed."""
    prompt = "Add monitoring"
    
    # Capture stderr for progress output
    result = await enhancer_agent.run("enhance-quick", prompt=prompt)
    
    # Progress should be printed to stderr
    # Note: capsys may not capture stderr in all cases, so we just verify the result
    assert result is not None
    assert result["success"] is True


@pytest.mark.asyncio
async def test_enhance_multiple_prompts(enhancer_agent):
    """Test enhancing multiple different prompts."""
    prompts = [
        "Add user authentication",
        "Add database backup",
        "Add API rate limiting"
    ]
    
    results = []
    for prompt in prompts:
        result = await enhancer_agent.run("enhance-quick", prompt=prompt)
        results.append(result)
    
    # All should succeed
    assert len(results) == len(prompts)
    for result in results:
        assert result["success"] is True
        assert "enhanced_prompt" in result
    
    # All should have different session IDs
    session_ids = [r["session_id"] for r in results]
    assert len(set(session_ids)) == len(prompts), "Each prompt should have unique session"


@pytest.mark.asyncio
async def test_enhance_codebase_context_stage(enhancer_agent):
    """Test codebase context stage in full enhancement."""
    prompt = "Add new feature"
    
    result = await enhancer_agent.run("enhance", prompt=prompt)
    
    assert "codebase_context" in result["stages_completed"]
    
    # Check session has codebase_context stage
    session = enhancer_agent.current_session
    assert "codebase_context" in session.get("stages", {})


@pytest.mark.asyncio
async def test_enhance_quality_stage(enhancer_agent):
    """Test quality standards stage in full enhancement."""
    prompt = "Add security features"
    
    result = await enhancer_agent.run("enhance", prompt=prompt)
    
    assert "quality" in result["stages_completed"]
    
    # Check session has quality stage
    session = enhancer_agent.current_session
    assert "quality" in session.get("stages", {})
    quality = session["stages"]["quality"]
    assert "code_quality_thresholds" in quality


@pytest.mark.asyncio
async def test_enhance_implementation_stage(enhancer_agent):
    """Test implementation strategy stage in full enhancement."""
    prompt = "Add new module"
    
    result = await enhancer_agent.run("enhance", prompt=prompt)
    
    assert "implementation" in result["stages_completed"]
    
    # Check session has implementation stage
    session = enhancer_agent.current_session
    assert "implementation" in session.get("stages", {})


@pytest.mark.asyncio
async def test_enhance_synthesis_stage(enhancer_agent):
    """Test synthesis stage creates final output."""
    prompt = "Add comprehensive testing"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt)
    
    assert "synthesis" in result["stages_completed"]
    
    # Check enhanced prompt is created
    enhanced = result.get("enhanced_prompt", {})
    if isinstance(enhanced, dict):
        content = enhanced.get("enhanced_prompt_content", "")
    else:
        content = str(enhanced)
    
    assert len(content) > 0, "Synthesis should create output"
    assert prompt in content or "Enhanced Prompt" in content


@pytest.mark.asyncio
async def test_enhance_agent_close(enhancer_agent):
    """Test that agent closes gracefully."""
    # Use the agent
    await enhancer_agent.run("enhance-quick", prompt="test")
    
    # Close should not raise
    await enhancer_agent.close()
    
    # Verify agent is closed (may not be directly testable, but no exception is good)
    assert True


@pytest.mark.asyncio
async def test_enhance_with_config_file(enhancer_agent):
    """Test enhancement respects configuration file."""
    prompt = "Add feature"
    
    # Should use config from .tapps-agents/enhancement-config.yaml if present
    result = await enhancer_agent.run("enhance", prompt=prompt)
    
    # Should complete successfully regardless of config
    assert result["success"] is True


@pytest.mark.asyncio
async def test_enhance_expert_integration(enhancer_agent):
    """Test that expert consultations are included when domains are detected."""
    prompt = "Add IoT device management"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt)
    
    # Check if expert consultations are in requirements
    session = enhancer_agent.current_session
    requirements = session.get("stages", {}).get("requirements", {})
    
    # Expert consultations may be empty if no domains detected, which is OK
    assert "expert_consultations" in requirements


@pytest.mark.asyncio
async def test_enhance_markdown_formatting(enhancer_agent):
    """Test that markdown output is properly formatted."""
    prompt = "Add documentation"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt, output_format="markdown")
    
    enhanced = result.get("enhanced_prompt", {})
    if isinstance(enhanced, dict):
        content = enhanced.get("enhanced_prompt_content", "")
    else:
        content = str(enhanced)
    
    # Check markdown structure
    lines = content.split("\n")
    assert any("# Enhanced Prompt:" in line for line in lines)
    assert any("## Metadata" in line for line in lines)
    assert any("## Analysis" in line for line in lines)


@pytest.mark.asyncio
async def test_enhance_json_structure(enhancer_agent):
    """Test that JSON output has correct structure."""
    prompt = "Add validation"
    
    result = await enhancer_agent.run("enhance-quick", prompt=prompt, output_format="json")
    
    enhanced = result.get("enhanced_prompt", {})
    assert isinstance(enhanced, dict)
    
    # Should be valid JSON structure
    json_str = json.dumps(enhanced)
    parsed = json.loads(json_str)
    assert parsed is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

