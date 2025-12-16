"""
Unit tests for concurrency and race conditions.

This module tests:
- Concurrent agent activation
- Concurrent cache access
- Concurrent workflow execution
- Concurrent scoring operations
- Thread safety and race condition handling
"""

import asyncio
from pathlib import Path

import pytest

from tapps_agents.agents.reviewer.scoring import CodeScorer
from tapps_agents.core.cache_router import CacheType
from tapps_agents.core.context_manager import ContextTier
from tapps_agents.workflow import WorkflowExecutor, WorkflowParser


@pytest.mark.unit
class TestConcurrentAgentActivation:
    """Test concurrent agent activation."""

    @pytest.mark.asyncio
    async def test_concurrent_agent_activate(self, base_agent, tmp_path: Path):
        """Test multiple agents activating concurrently."""
        from tapps_agents.core.agent_base import BaseAgent
        
        # Create multiple agent instances
        agents = [
            BaseAgent(agent_id=f"agent-{i}", agent_name=f"Agent {i}")
            for i in range(5)
        ]
        
        # Activate all agents concurrently
        tasks = [agent.activate(tmp_path) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All activations should succeed
        for result in results:
            assert not isinstance(result, Exception)
        
        # All agents should have configs
        for agent in agents:
            assert agent.config is not None

    @pytest.mark.asyncio
    async def test_concurrent_agent_get_context(self, base_agent, tmp_path: Path):
        """Test concurrent get_context calls."""
        agent = base_agent
        await agent.activate(tmp_path)
        
        # Create multiple test files
        test_files = [tmp_path / f"test_{i}.py" for i in range(10)]
        for f in test_files:
            f.write_text(f"def test_{f.stem}(): pass\n")
        
        # Get context for all files concurrently
        tasks = [agent.get_context(f) for f in test_files]
        contexts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for context in contexts:
            assert not isinstance(context, Exception)
            assert isinstance(context, dict)

    @pytest.mark.asyncio
    async def test_concurrent_agent_parse_command(self, base_agent):
        """Test concurrent command parsing."""
        agent = base_agent
        
        # Parse multiple commands concurrently
        commands = ["*help"] + [f"*review file{i}.py" for i in range(10)]
        tasks = [asyncio.to_thread(agent.parse_command, cmd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            command, args = result
            assert isinstance(command, str)
            assert isinstance(args, dict)


@pytest.mark.unit
class TestConcurrentCacheAccess:
    """Test concurrent cache access."""

    @pytest.mark.asyncio
    async def test_concurrent_cache_get(self, unified_cache_real, tmp_path: Path):
        """Test concurrent cache get operations."""
        # Pre-populate cache
        test_files = [tmp_path / f"test_{i}.py" for i in range(10)]
        for f in test_files:
            f.write_text(f"def test_{f.stem}(): pass\n")
            unified_cache_real.put(
                cache_type=CacheType.TIERED_CONTEXT,
                key=str(f),
                value={"content": f"content_{f.stem}", "tier": "TIER1"},
                tier=ContextTier.TIER1,
            )
        
        # Concurrent gets
        async def get_cache(key):
            return unified_cache_real.get(
                cache_type=CacheType.TIERED_CONTEXT,
                key=key,
                tier=ContextTier.TIER1,
            )
        
        tasks = [get_cache(str(f)) for f in test_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed (may return None if not cached)
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_concurrent_cache_put(self, unified_cache_real, tmp_path: Path):
        """Test concurrent cache put operations."""
        test_files = [tmp_path / f"test_{i}.py" for i in range(10)]
        for f in test_files:
            f.write_text(f"def test_{f.stem}(): pass\n")
        
        # Concurrent puts
        async def put_cache(key, value):
            return unified_cache_real.put(
                cache_type=CacheType.TIERED_CONTEXT,
                key=key,
                value=value,
                tier=ContextTier.TIER1,
            )
        
        tasks = [
            put_cache(str(f), {"content": f"content_{f.stem}", "tier": "TIER1"})
            for f in test_files
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_concurrent_cache_get_put(self, unified_cache_real, tmp_path: Path):
        """Test concurrent get and put operations (race condition test)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass\n")
        
        # Mix of gets and puts concurrently
        async def get_op():
            return unified_cache_real.get(
                cache_type=CacheType.TIERED_CONTEXT,
                key=str(test_file),
                tier=ContextTier.TIER1,
            )
        
        async def put_op(value):
            return unified_cache_real.put(
                cache_type=CacheType.TIERED_CONTEXT,
                key=str(test_file),
                value=value,
                tier=ContextTier.TIER1,
            )
        
        tasks = [
            get_op(),
            put_op({"content": "value1", "tier": "TIER1"}),
            get_op(),
            put_op({"content": "value2", "tier": "TIER1"}),
            get_op(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed without exceptions
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_concurrent_cache_invalidate(self, unified_cache_real, tmp_path: Path):
        """Test concurrent cache invalidation."""
        test_files = [tmp_path / f"test_{i}.py" for i in range(10)]
        for f in test_files:
            f.write_text(f"def test_{f.stem}(): pass\n")
            unified_cache_real.put(
                cache_type=CacheType.TIERED_CONTEXT,
                key=str(f),
                value={"content": f"content_{f.stem}", "tier": "TIER1"},
                tier=ContextTier.TIER1,
            )
        
        # Concurrent invalidates
        async def invalidate_cache(key):
            return unified_cache_real.invalidate(
                cache_type=CacheType.TIERED_CONTEXT,
                key=key,
                tier=ContextTier.TIER1,
            )
        
        tasks = [invalidate_cache(str(f)) for f in test_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)


@pytest.mark.unit
class TestConcurrentWorkflowExecution:
    """Test concurrent workflow execution."""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_start(self, tmp_path: Path, monkeypatch):
        """Test starting multiple workflows concurrently."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        
        workflow_dict = {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                    }
                ],
            }
        }
        
        # Create multiple executors
        executors = [WorkflowExecutor(project_root=tmp_path) for _ in range(5)]
        workflow = WorkflowParser.parse(workflow_dict)
        
        # Start all workflows concurrently
        tasks = [asyncio.to_thread(executor.start, workflow) for executor in executors]
        states = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for state in states:
            assert not isinstance(state, Exception)
            assert state.workflow_id == "test-workflow"
            assert state.status == "running"

    @pytest.mark.asyncio
    async def test_concurrent_workflow_step_execution(self, tmp_path: Path, monkeypatch):
        """Test concurrent step execution in different workflows."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        
        workflow_dict = {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                    }
                ],
            }
        }
        
        # Create executors and start workflows
        executors = [WorkflowExecutor(project_root=tmp_path) for _ in range(3)]
        workflow = WorkflowParser.parse(workflow_dict)
        
        for executor in executors:
            executor.start(workflow)
        
        # Get current step concurrently
        async def get_step(executor):
            return asyncio.to_thread(executor.get_current_step)
        
        tasks = [get_step(executor) for executor in executors]
        steps = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for step_func in steps:
            assert not isinstance(step_func, Exception)


@pytest.mark.unit
class TestConcurrentScoringOperations:
    """Test concurrent scoring operations."""

    @pytest.mark.asyncio
    async def test_concurrent_score_file(self, tmp_path: Path):
        """Test scoring multiple files concurrently."""
        scorer = CodeScorer()
        
        # Create multiple test files
        test_files = [tmp_path / f"test_{i}.py" for i in range(10)]
        for f in test_files:
            f.write_text(f"def test_{f.stem}(): pass\n")
        
        # Score all files concurrently
        async def score_file(file_path):
            return asyncio.to_thread(
                scorer.score_file,
                file_path,
                file_path.read_text()
            )
        
        tasks = [score_file(f) for f in test_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, dict)
            assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_concurrent_score_same_file(self, tmp_path: Path):
        """Test scoring the same file concurrently (race condition test)."""
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass\n")
        content = test_file.read_text()
        
        # Score same file concurrently
        async def score():
            return asyncio.to_thread(scorer.score_file, test_file, content)
        
        tasks = [score() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, dict)
        
        # All results should be similar (same file, same content)
        scores = [r["overall_score"] for r in results]
        # Scores should be identical or very close (within rounding)
        assert all(abs(score - scores[0]) < 0.1 for score in scores)

    @pytest.mark.asyncio
    async def test_concurrent_scorer_instances(self, tmp_path: Path):
        """Test multiple scorer instances working concurrently."""
        scorers = [CodeScorer() for _ in range(5)]
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass\n")
        content = test_file.read_text()
        
        # Score with different scorer instances concurrently
        async def score(scorer):
            return asyncio.to_thread(scorer.score_file, test_file, content)
        
        tasks = [score(scorer) for scorer in scorers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, dict)
            assert "overall_score" in result


@pytest.mark.unit
class TestThreadSafety:
    """Test thread safety of operations."""

    def test_scorer_thread_safety(self, tmp_path: Path):
        """Test that scorer is thread-safe."""
        import threading
        
        scorer = CodeScorer()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass\n")
        content = test_file.read_text()
        
        results = []
        errors = []
        
        def score():
            try:
                result = scorer.score_file(test_file, content)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=score) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 10
        for result in results:
            assert isinstance(result, dict)
            assert "overall_score" in result

    @pytest.mark.skip(reason="TODO: Fix cache lock timeouts - all tests in this class need mock for file locking")
    def test_cache_thread_safety(self, unified_cache_real, tmp_path: Path):
        """Test that cache operations are thread-safe."""
        import threading
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass\n")
        
        results = []
        errors = []
        
        def cache_operation():
            try:
                result = unified_cache_real.put(
                    cache_type=CacheType.TIERED_CONTEXT,
                    key=str(test_file),
                    value={"content": "test", "tier": "TIER1"},
                    tier=ContextTier.TIER1,
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=cache_operation) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 10

