"""
Tests for Weight Distribution Algorithm
"""

import pytest

from tapps_agents.experts.weight_distributor import (
    ExpertWeightMatrix,
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

    def test_calculate_weights_single_expert(self):
        """Test weight calculation for single expert (100% weight)."""
        domains = ["domain-a"]
        expert_primary_map = {"expert-a": "domain-a"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        # Single expert should have 100% weight
        assert matrix.get_expert_weight("expert-a", "domain-a") == 1.0

        # Validate
        errors = matrix.validate()
        assert len(errors) == 0

    def test_get_primary_expert_domain(self):
        """Test getting primary domain for an expert."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        assert matrix.get_primary_expert_domain("expert-a") == "domain-a"
        assert matrix.get_primary_expert_domain("expert-b") == "domain-b"
        assert matrix.get_primary_expert_domain("nonexistent") is None

    def test_get_expert_weight_nonexistent(self):
        """Test getting weight for nonexistent expert/domain."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        # Should return 0.0 for nonexistent combinations
        assert matrix.get_expert_weight("nonexistent", "domain-a") == 0.0
        assert matrix.get_expert_weight("expert-a", "nonexistent") == 0.0

    def test_get_primary_expert_nonexistent_domain(self):
        """Test getting primary expert for nonexistent domain."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        assert matrix.get_primary_expert("nonexistent") is None

    def test_recalculate_on_domain_add_duplicate_domain(self):
        """Test recalculating with duplicate domain raises error."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        with pytest.raises(ValueError, match="already exists"):
            WeightDistributor.recalculate_on_domain_add(
                matrix, "domain-a", "expert-c"
            )

    def test_recalculate_on_domain_add_duplicate_expert(self):
        """Test recalculating with duplicate expert raises error."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        with pytest.raises(ValueError, match="already exists"):
            WeightDistributor.recalculate_on_domain_add(
                matrix, "domain-c", "expert-a"
            )

    def test_format_matrix(self):
        """Test formatting weight matrix as table."""
        domains = ["domain-a", "domain-b"]
        expert_primary_map = {"expert-a": "domain-a", "expert-b": "domain-b"}

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)
        formatted = WeightDistributor.format_matrix(matrix)

        assert "Expert/Domain" in formatted
        assert "expert-a" in formatted
        assert "expert-b" in formatted
        assert "domain-a" in formatted
        assert "domain-b" in formatted
        assert "TOTAL" in formatted
        assert "0.510" in formatted or "0.51" in formatted

    def test_validate_column_sums(self):
        """Test validation checks column sums."""
        # Create invalid matrix with wrong column sum
        weights = {
            "expert-a": {"domain-a": 0.51, "domain-b": 0.49},
            "expert-b": {"domain-a": 0.49, "domain-b": 0.40},  # Wrong sum
        }
        matrix = ExpertWeightMatrix(
            weights=weights, domains=["domain-a", "domain-b"], experts=["expert-a", "expert-b"]
        )

        errors = matrix.validate()
        assert len(errors) > 0
        assert any("column sum" in error.lower() for error in errors)

    def test_validate_no_primary_expert(self):
        """Test validation catches missing primary expert."""
        # Create invalid matrix without primary expert
        weights = {
            "expert-a": {"domain-a": 0.40, "domain-b": 0.60},
            "expert-b": {"domain-a": 0.60, "domain-b": 0.40},  # No primary (>= 0.51)
        }
        matrix = ExpertWeightMatrix(
            weights=weights, domains=["domain-a", "domain-b"], experts=["expert-a", "expert-b"]
        )

        errors = matrix.validate()
        assert len(errors) > 0
        assert any("no primary expert" in error.lower() for error in errors)

    def test_validate_multiple_primaries(self):
        """Test validation catches multiple primary experts."""
        # Create invalid matrix with multiple primaries
        weights = {
            "expert-a": {"domain-a": 0.51, "domain-b": 0.49},
            "expert-b": {"domain-a": 0.51, "domain-b": 0.49},  # Both primary for domain-a
        }
        matrix = ExpertWeightMatrix(
            weights=weights, domains=["domain-a", "domain-b"], experts=["expert-a", "expert-b"]
        )

        errors = matrix.validate()
        assert len(errors) > 0
        assert any("multiple primary experts" in error.lower() for error in errors)

    def test_calculate_weights_4_experts(self):
        """Test weight calculation for 4 experts/domains."""
        domains = ["domain-a", "domain-b", "domain-c", "domain-d"]
        expert_primary_map = {
            "expert-a": "domain-a",
            "expert-b": "domain-b",
            "expert-c": "domain-c",
            "expert-d": "domain-d",
        }

        matrix = WeightDistributor.calculate_weights(domains, expert_primary_map)

        # Check primary weights (51%)
        assert matrix.get_expert_weight("expert-a", "domain-a") == 0.51
        assert matrix.get_expert_weight("expert-b", "domain-b") == 0.51

        # Check other weights (49% / 3 = ~16.33%)
        other_weight = 0.49 / 3
        assert abs(matrix.get_expert_weight("expert-a", "domain-b") - other_weight) < 0.001

        # Validate column sums
        for domain in domains:
            total = sum(
                matrix.get_expert_weight(expert_id, domain)
                for expert_id in ["expert-a", "expert-b", "expert-c", "expert-d"]
            )
            assert abs(total - 1.0) < 0.001
