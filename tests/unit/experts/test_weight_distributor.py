"""
Tests for Weight Distribution Algorithm
"""

import pytest

from tapps_agents.experts.weight_distributor import (
    WeightDistributor,
)

pytestmark = pytest.mark.unit


class TestWeightDistributor:
    """Test weight distribution calculations."""

    def test_calculate_weights_2_experts(self):
        """Test weight calculation for 2 experts/domains."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        # Check primary weights (51%)
        assert matrix.get_expert_weight("expert-a", "domain-a") == 0.51
        assert matrix.get_expert_weight("expert-b", "domain-b") == 0.51

        # Check other weights (49%)
        assert matrix.get_expert_weight("expert-a", "domain-b") == 0.49
        assert matrix.get_expert_weight("expert-b", "domain-a") == 0.49

        # Validate
        errors = matrix.validate()
        assert len(errors) == 0

    def test_calculate_weights_3_experts(self):
        """Test weight calculation for 3 experts/domains."""
        domains = ["domain-a", "domain-b", "domain-c"]
        expert_primary_map = {
            "expert-a": "domain-a",
            "expert-b": "domain-b",
            "expert-c": "domain-c",
        }

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        # Check primary weights (51%)
        assert matrix.get_expert_weight("expert-a", "domain-a") == 0.51
        assert matrix.get_expert_weight("expert-b", "domain-b") == 0.51
        assert matrix.get_expert_weight("expert-c", "domain-c") == 0.51

        # Check other weights (49% / 2 = 24.5%)
        assert abs(matrix.get_expert_weight("expert-a", "domain-b") - 0.245) < 0.001
        assert abs(matrix.get_expert_weight("expert-a", "domain-c") - 0.245) < 0.001

        # Validate column sums (should be 1.0)
        for domain in domains:
            total = sum(
                matrix.get_expert_weight(expert_id, domain)
                for expert_id in ["expert-a", "expert-b", "expert-c"]
            )
            assert abs(total - 1.0) < 0.001

    def test_get_primary_expert(self):
        """Test getting primary expert for a domain."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        assert matrix.get_primary_expert("domain-a") == "expert-a"
        assert matrix.get_primary_expert("domain-b") == "expert-b"

    def test_validate_requirements(self):
        """Test validation catches errors."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        errors = matrix.validate()
        assert len(errors) == 0  # Should be valid

    def test_invalid_expert_count(self):
        """Test error when expert count doesn't match domain count."""
        domains = ["domain-a", "domain-b", "domain-c"]
        expert_primary_map = {
            "expert-a": "domain-a",
            "expert-b": "domain-b",
            # Missing expert-c
        }

        with pytest.raises(ValueError, match="Domains without primary expert"):
            WeightDistributor.calculate_weights(domains, expert_primary_map)

    def test_multiple_primaries_same_domain(self):
        """Test error when multiple experts claim same domain."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {
            "expert-a": "domain-a",
            "expert-b": "domain-a",  # Both claim domain-a!
        }

        with pytest.raises(ValueError, match="multiple primary experts"):
            WeightDistributor.calculate_weights(domains, expert_primary_map)

    def test_recalculate_on_domain_add(self):
        """Test recalculating weights when adding a domain."""
        # Start with 2 domains
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        # Add third domain
        new_matrix = WeightDistributor.recalculate_on_domain_add(
            matrix, "domain-c", "expert-c"
        )

        # New expert should have 51% on new domain
        assert new_matrix.get_expert_weight("expert-c", "domain-c") == 0.51

        # All experts should have updated weights (49% / 2 = 24.5% on other domains)
        assert abs(new_matrix.get_expert_weight("expert-a", "domain-b") - 0.245) < 0.001

        # Validate
        errors = new_matrix.validate()
        assert len(errors) == 0
