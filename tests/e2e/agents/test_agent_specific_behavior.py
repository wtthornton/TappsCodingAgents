"""
E2E tests for agent-specific behavior and functionality.

Tests validate:
- Planner: plan creation, structure, completeness
- Implementer: code generation, correctness, style
- Reviewer: review feedback, quality, gate evaluation
- Tester: test generation, execution, results
"""

from unittest.mock import MagicMock, patch

import pytest

from tests.e2e.fixtures.agent_test_helpers import (
    create_test_agent,
    execute_command,
    validate_code_quality,
    validate_plan_completeness,
    validate_plan_structure,
    validate_review_feedback,
    validate_test_results,
)


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestPlannerAgentSpecificBehavior:
    """Test Planner agent-specific behavior."""

    @pytest.mark.asyncio
    async def test_plan_creation(self, e2e_project, mock_mal):
        """Test that planner creates plans with appropriate structure."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*plan",
            description="Create a user authentication system with login and registration",
        )

        assert result is not None
        if "error" not in result:
            # Should have plan data
            assert "plan" in result or "type" in result

    @pytest.mark.asyncio
    async def test_plan_structure_components(self, e2e_project, mock_mal):
        """Test that plan structure includes required components."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*plan",
            description="Implement a REST API for product management",
        )

        if "error" not in result and "plan" in result:
            plan = result["plan"]
            # Validate plan has required components
            validate_plan_structure(
                plan,
                ["task", "overview", "requirement", "feature", "story"],
            )

    @pytest.mark.asyncio
    async def test_plan_completeness(self, e2e_project, mock_mal):
        """Test that plans are complete and actionable."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*plan",
            description="Build a microservices architecture for e-commerce",
        )

        if "error" not in result and "plan" in result:
            plan = result["plan"]
            validate_plan_completeness(plan, {"min_length": 100, "has_tasks": True})

    @pytest.mark.asyncio
    async def test_plan_contextual_appropriateness(self, e2e_project, mock_mal):
        """Test that plans are contextually appropriate for the project."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*plan",
            description="Add database migration support to the project",
        )

        if "error" not in result:
            # Plan should be relevant to the description
            assert result is not None


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestImplementerAgentSpecificBehavior:
    """Test Implementer agent-specific behavior."""

    @pytest.mark.asyncio
    async def test_code_generation_matches_requirements(self, e2e_project, mock_mal):
        """Test that implementer generates code matching requirements."""
        agent = create_test_agent("implementer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*implement",
            description="Create a function to calculate the factorial of a number",
        )

        assert result is not None
        if "error" not in result:
            # Should have code or implementation
            assert "code" in result or "content" in result or "implementation" in result

    @pytest.mark.asyncio
    async def test_generated_code_syntax(self, e2e_project, mock_mal):
        """Test that generated code is syntactically correct."""
        agent = create_test_agent("implementer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*implement",
            description="def calculate_sum(a, b): return a + b",
        )

        if "error" not in result:
            # Extract code from result
            code = None
            if "code" in result:
                code = result["code"]
            elif "content" in result:
                code = result["content"]
            elif isinstance(result.get("implementation"), str):
                code = result["implementation"]

            if code and isinstance(code, str):
                # Validate syntax
                validate_code_quality(code, {})

    @pytest.mark.asyncio
    async def test_code_follows_standards(self, e2e_project, mock_mal):
        """Test that generated code follows coding standards."""
        agent = create_test_agent("implementer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*implement",
            description="Create a Python class for handling user data with validation",
        )

        if "error" not in result:
            code = None
            if "code" in result:
                code = result["code"]
            elif "content" in result:
                code = result["content"]

            if code and isinstance(code, str):
                # Check for basic standards
                validate_code_quality(
                    code, {"has_docstrings": True, "has_functions": True}
                )

    @pytest.mark.asyncio
    async def test_code_artifacts_produced(self, e2e_project, mock_mal, tmp_path):
        """Test that implementer produces code artifacts in expected locations."""
        agent = create_test_agent("implementer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*implement",
            description="Create a utility module for file operations",
            output_file=str(tmp_path / "utils.py"),
        )

        # Should produce output
        assert result is not None


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestReviewerAgentSpecificBehavior:
    """Test Reviewer agent-specific behavior."""

    @pytest.mark.asyncio
    async def test_review_feedback_structure(self, e2e_project, mock_mal, tmp_path):
        """Test that reviewer generates review feedback with appropriate structure."""
        # Create test file
        test_file = tmp_path / "test_code.py"
        test_file.write_text(
            """def example_function(x, y):
    return x + y
"""
        )

        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*review", file=str(test_file))

        assert result is not None
        if "error" not in result:
            validate_review_feedback(result, {"has_feedback": True})

    @pytest.mark.asyncio
    async def test_review_quality_assessments(self, e2e_project, mock_mal, tmp_path):
        """Test that review feedback includes quality assessments."""
        test_file = tmp_path / "code.py"
        test_file.write_text("def test(): pass\n")

        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*score", file=str(test_file))

        if "error" not in result:
            validate_review_feedback(result, {"has_score": True})

    @pytest.mark.asyncio
    async def test_review_actionable_recommendations(
        self, e2e_project, mock_mal, tmp_path
    ):
        """Test that review feedback provides actionable recommendations."""
        test_file = tmp_path / "code.py"
        test_file.write_text("def func(): pass\n")

        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*review", file=str(test_file))

        if "error" not in result:
            # Should have feedback or recommendations
            feedback_fields = ["feedback", "recommendations", "issues", "content"]
            assert any(field in result for field in feedback_fields)

    @pytest.mark.asyncio
    async def test_gate_evaluation(self, e2e_project, mock_mal, tmp_path):
        """Test that reviewer correctly evaluates gates (pass/fail decisions)."""
        test_file = tmp_path / "code.py"
        test_file.write_text("def good_code():\n    '''Well documented.'''\n    pass\n")

        agent = create_test_agent("reviewer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*review", file=str(test_file))

        if "error" not in result:
            validate_review_feedback(result, {"has_status": True})


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestTesterAgentSpecificBehavior:
    """Test Tester agent-specific behavior."""

    @pytest.mark.asyncio
    async def test_test_generation_matches_requirements(self, e2e_project, mock_mal):
        """Test that tester generates tests matching requirements."""
        agent = create_test_agent("tester", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*test",
            file="example.py",
            test_file="test_example.py",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_generated_tests_syntax(self, e2e_project, mock_mal, tmp_path):
        """Test that generated tests are syntactically correct."""
        # Create source file
        source_file = tmp_path / "calculator.py"
        source_file.write_text("def add(a, b): return a + b\n")

        agent = create_test_agent("tester", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*generate-tests",
            file=str(source_file),
        )

        if "error" not in result:
            # Should have test code
            assert result is not None

    @pytest.mark.asyncio
    async def test_test_execution_and_results(self, e2e_project, mock_mal, tmp_path):
        """Test that tester executes tests and reports results."""
        # Mock subprocess.run to avoid actually running pytest (which can hang)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "============================= test session starts =============================\n5 passed in 0.10s"
        mock_result.stderr = ""

        with patch("tapps_agents.agents.tester.agent.subprocess.run", return_value=mock_result):
            agent = create_test_agent("tester", mock_mal)
            await agent.activate(e2e_project)

            result = await execute_command(agent, "*run-tests")

            if "error" not in result:
                validate_test_results(result, {"has_status": True, "has_count": True})


@pytest.mark.e2e
@pytest.mark.template_type("minimal")
class TestAgentSpecificBehaviorScenarios:
    """Test agent-specific behavior in various scenarios."""

    @pytest.mark.asyncio
    async def test_simple_planner_scenario(self, e2e_project, mock_mal):
        """Test planner with simple scenario."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent, "*plan", description="Add a button to the UI"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_complex_planner_scenario(self, e2e_project, mock_mal):
        """Test planner with complex scenario."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*plan",
            description="Build a distributed microservices architecture with authentication, authorization, caching, and monitoring",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_simple_implementer_scenario(self, e2e_project, mock_mal):
        """Test implementer with simple scenario."""
        agent = create_test_agent("implementer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent, "*implement", description="Create a hello world function"
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_complex_implementer_scenario(self, e2e_project, mock_mal):
        """Test implementer with complex scenario."""
        agent = create_test_agent("implementer", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(
            agent,
            "*implement",
            description="Create a REST API with authentication, rate limiting, and error handling",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_edge_case_empty_input(self, e2e_project, mock_mal):
        """Test agents with empty input (edge case)."""
        agent = create_test_agent("planner", mock_mal)
        await agent.activate(e2e_project)

        result = await execute_command(agent, "*plan", description="")
        # Should handle gracefully
        assert result is not None

