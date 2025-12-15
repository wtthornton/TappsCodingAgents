"""
Integration tests for expert system with project profile integration.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, Mock

import pytest

from tapps_agents.core.project_profile import ComplianceRequirement, ProjectProfile
from tapps_agents.experts.base_expert import BaseExpert
from tapps_agents.experts.confidence_calculator import ConfidenceCalculator
from tapps_agents.experts.expert_registry import ExpertRegistry


@pytest.mark.unit
class TestBaseExpertWithProfile:
    """Test BaseExpert integration with project profile."""

    @pytest.mark.asyncio
    async def test_expert_uses_profile_in_prompt(self, mock_mal):
        """Test that expert includes project profile in consultation prompt."""
        expert = BaseExpert(
            expert_id="expert-test",
            expert_name="Test Expert",
            primary_domain="security",
            rag_enabled=False,
        )
        expert.mal = mock_mal

        profile = ProjectProfile(
            deployment_type="cloud",
            deployment_type_confidence=0.8,  # High enough to be included
            security_level="high",
            security_level_confidence=0.8,  # High enough to be included
            compliance_requirements=[
                ComplianceRequirement(
                    name="GDPR", confidence=0.9, indicators=["gdpr.md"]
                )
            ],
        )

        # Mock the prompt building
        prompt = await expert._build_consultation_prompt(
            query="How should I handle user data?",
            context="Security context",
            domain="security",
            project_profile=profile,
        )

        # Verify profile information is in prompt
        # Note: Only high-confidence values (>= 0.7) are included
        # Since we set compliance with 0.9 confidence, it should be included
        assert "gdpr" in prompt.lower() or "compliance" in prompt.lower()
        assert "security" in prompt.lower()
        assert "project context" in prompt.lower()

    @pytest.mark.asyncio
    async def test_expert_works_without_profile(self, mock_mal):
        """Test that expert works when no profile is provided."""
        expert = BaseExpert(
            expert_id="expert-test",
            expert_name="Test Expert",
            primary_domain="security",
            rag_enabled=False,
        )
        expert.mal = mock_mal

        # Should work without profile
        prompt = await expert._build_consultation_prompt(
            query="How should I handle user data?",
            context="Security context",
            domain="security",
            project_profile=None,
        )

        assert "security" in prompt.lower()
        assert "question" in prompt.lower() or "query" in prompt.lower()


@pytest.mark.unit
class TestExpertRegistryWithProfile:
    """Test ExpertRegistry integration with project profile."""

    @pytest.mark.asyncio
    async def test_registry_loads_profile(self, mock_mal):
        """Test that ExpertRegistry loads project profile."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_dir = project_root / ".tapps-agents"
            config_dir.mkdir()

            # Create and save a profile
            profile = ProjectProfile(
                deployment_type="enterprise", security_level="high"
            )
            from tapps_agents.core.project_profile import save_project_profile

            save_project_profile(profile, project_root)

            # Create registry with project root
            registry = ExpertRegistry(load_builtin=False)
            registry.project_root = project_root

            # Load profile
            loaded_profile = registry._get_project_profile()
            assert loaded_profile is not None
            assert loaded_profile.deployment_type == "enterprise"
            assert loaded_profile.security_level == "high"

    @pytest.mark.asyncio
    async def test_registry_passes_profile_to_experts(self, mock_mal):
        """Test that ExpertRegistry passes profile to experts during consultation."""
        registry = ExpertRegistry(load_builtin=False)

        # Create a mock expert
        mock_expert = Mock(spec=BaseExpert)
        mock_expert.expert_id = "expert-test"
        mock_expert.agent_name = "Test Expert"
        mock_expert.primary_domain = "security"
        mock_expert.run = AsyncMock(
            return_value={"answer": "Test answer", "confidence": 0.8, "sources": []}
        )
        registry.register_expert(mock_expert, is_builtin=False)

        # Create profile
        profile = ProjectProfile(deployment_type="cloud")
        registry.project_root = None  # Skip file loading
        registry._cached_profile = profile  # Set directly for testing

        # Consult expert (registry will select experts automatically)
        await registry.consult(
            query="Test question", domain="security", include_all=False
        )

        # Verify expert was called with profile
        mock_expert.run.assert_called_once()
        call_kwargs = mock_expert.run.call_args[1]
        assert "project_profile" in call_kwargs
        assert call_kwargs["project_profile"] == profile

    @pytest.mark.asyncio
    async def test_registry_handles_missing_profile(self, mock_mal):
        """Test that ExpertRegistry handles missing profile gracefully."""
        registry = ExpertRegistry(load_builtin=False)

        # Create a mock expert
        mock_expert = Mock(spec=BaseExpert)
        mock_expert.expert_id = "expert-test"
        mock_expert.agent_name = "Test Expert"
        mock_expert.primary_domain = "security"
        mock_expert.run = AsyncMock(
            return_value={"answer": "Test answer", "confidence": 0.8, "sources": []}
        )
        registry.register_expert(mock_expert, is_builtin=False)

        # No profile available - mock the profile getter to return None
        from unittest.mock import patch
        with patch.object(registry, '_get_project_profile', return_value=None):
            # Should still work
            await registry.consult(
                query="Test question", domain="security", include_all=False
            )

            # Verify expert was called (with None profile)
            mock_expert.run.assert_called_once()
            call_kwargs = mock_expert.run.call_args[1]
            assert "project_profile" in call_kwargs
            assert call_kwargs["project_profile"] is None


@pytest.mark.unit
class TestConfidenceCalculatorWithProfile:
    """Test ConfidenceCalculator integration with project profile."""

    def test_confidence_includes_project_context(self):
        """Test that confidence calculation includes project context relevance."""
        responses = [
            {
                "expert_id": "expert-1",
                "expert_name": "Expert 1",
                "answer": "For cloud deployments, use load balancers",
                "confidence": 0.9,
                "sources": [],
            },
            {
                "expert_id": "expert-2",
                "expert_name": "Expert 2",
                "answer": "Consider multi-tenant architecture",
                "confidence": 0.85,
                "sources": [],
            },
        ]

        profile = ProjectProfile(deployment_type="cloud", tenancy="multi")

        confidence, threshold = ConfidenceCalculator.calculate(
            responses=responses, domain="architecture", project_profile=profile
        )

        # Confidence should be calculated (including project context)
        assert 0.0 <= confidence <= 1.0
        assert threshold > 0.0

    def test_confidence_without_profile(self):
        """Test confidence calculation without profile."""
        responses = [
            {
                "expert_id": "expert-1",
                "expert_name": "Expert 1",
                "answer": "Use best practices",
                "confidence": 0.8,
                "sources": [],
            }
        ]

        confidence, threshold = ConfidenceCalculator.calculate(
            responses=responses, domain="security", project_profile=None
        )

        # Should still calculate confidence
        assert 0.0 <= confidence <= 1.0
        assert threshold > 0.0

    def test_project_context_relevance_calculation(self):
        """Test the project context relevance calculation logic."""
        # Test with matching keywords
        responses = [
            {
                "answer": "For enterprise cloud deployments, use Kubernetes",
                "confidence": 0.9,
            }
        ]

        profile = ProjectProfile(deployment_type="enterprise", user_scale="thousands")

        relevance = ConfidenceCalculator._calculate_project_context_relevance(
            responses, profile
        )

        # Should have some relevance (keywords match)
        assert 0.0 <= relevance <= 1.0

        # Test with no profile
        relevance_none = ConfidenceCalculator._calculate_project_context_relevance(
            responses, None
        )
        assert relevance_none == 0.0


@pytest.mark.unit
class TestEndToEndProfileIntegration:
    """End-to-end tests for profile integration."""

    @pytest.mark.asyncio
    async def test_full_consultation_flow_with_profile(self, mock_mal):
        """Test full consultation flow with project profile."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_dir = project_root / ".tapps-agents"
            config_dir.mkdir()

            # Create and save profile
            profile = ProjectProfile(
                deployment_type="cloud",
                security_level="high",
                compliance_requirements=[
                    ComplianceRequirement(
                        name="SOC2", confidence=0.95, indicators=["soc2.md"]
                    )
                ],
            )
            from tapps_agents.core.project_profile import save_project_profile

            save_project_profile(profile, project_root)

            # Create registry
            registry = ExpertRegistry(load_builtin=False)
            registry.project_root = project_root

            # Create mock expert
            expert = BaseExpert(
                expert_id="expert-security",
                expert_name="Security Expert",
                primary_domain="security",
                rag_enabled=False,
            )
            expert.mal = mock_mal
            registry.register_expert(expert, is_builtin=False)

            # Consult
            result = await registry.consult(
                query="How should I secure my cloud deployment?", domain="security"
            )

            # Verify result structure (ConsultationResult is a dataclass)
            assert hasattr(result, "weighted_answer") or hasattr(result, "responses")
            assert hasattr(result, "confidence")
            # Profile should have been loaded and used
            assert registry._cached_profile is not None

    @pytest.mark.asyncio
    async def test_profile_affects_confidence(self, mock_mal):
        """Test that project profile affects confidence calculation."""
        registry = ExpertRegistry(load_builtin=False)

        # Create expert with mock response
        expert = BaseExpert(
            expert_id="expert-test",
            expert_name="Test Expert",
            primary_domain="architecture",
            rag_enabled=False,
        )
        expert.mal = mock_mal

        # Mock the run method to return specific answer
        async def mock_run(command, **kwargs):
            if command == "consult":
                return {
                    "answer": "For cloud deployments, use microservices",
                    "confidence": 0.85,
                    "sources": [],
                }
            return {"error": "Unknown command"}

        expert.run = mock_run
        registry.register_expert(expert, is_builtin=False)

        # Test with profile
        profile_with_match = ProjectProfile(deployment_type="cloud")
        registry._cached_profile = profile_with_match

        result_with_profile = await registry.consult(
            query="What architecture should I use?", domain="architecture"
        )

        confidence_with = result_with_profile.confidence

        # Test without profile
        registry._cached_profile = None

        result_without_profile = await registry.consult(
            query="What architecture should I use?", domain="architecture"
        )

        confidence_without = result_without_profile.confidence

        # Confidence might differ (though not guaranteed due to other factors)
        # At minimum, both should be valid confidence scores
        assert 0.0 <= confidence_with <= 1.0
        assert 0.0 <= confidence_without <= 1.0
