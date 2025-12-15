"""
Unit tests for Context7 staleness policies.
"""

from datetime import UTC, datetime, timedelta

import pytest

from tapps_agents.context7.staleness_policies import (
    StalenessPolicy,
    StalenessPolicyManager,
)


class TestStalenessPolicy:
    def test_policy_creation(self):
        policy = StalenessPolicy(max_age_days=30, library_type="stable")
        assert policy.max_age_days == 30
        assert policy.library_type == "stable"

    def test_is_stale_fresh_entry(self):
        policy = StalenessPolicy(max_age_days=30)
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=10)).isoformat() + "Z"

        assert policy.is_stale(last_updated, now) is False

    def test_is_stale_old_entry(self):
        policy = StalenessPolicy(max_age_days=30)
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=31)).isoformat() + "Z"

        assert policy.is_stale(last_updated, now) is True

    def test_is_stale_exactly_at_threshold(self):
        policy = StalenessPolicy(max_age_days=30)
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=30)).isoformat() + "Z"

        # Exactly at threshold should not be stale (age <= max_age)
        assert policy.is_stale(last_updated, now) is False

    def test_is_stale_invalid_date(self):
        policy = StalenessPolicy(max_age_days=30)
        # Invalid date should be considered stale for safety
        assert policy.is_stale("invalid-date", datetime.now(UTC)) is True

    def test_days_until_stale_fresh(self):
        policy = StalenessPolicy(max_age_days=30)
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=10)).isoformat() + "Z"

        days = policy.days_until_stale(last_updated, now)
        assert days == 20  # 30 - 10

    def test_days_until_stale_already_stale(self):
        policy = StalenessPolicy(max_age_days=30)
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=35)).isoformat() + "Z"

        days = policy.days_until_stale(last_updated, now)
        assert days < 0  # Negative means already stale

    def test_days_until_stale_invalid_date(self):
        policy = StalenessPolicy(max_age_days=30)
        days = policy.days_until_stale("invalid-date", datetime.now(UTC))
        assert days == -1  # Error case returns -1


class TestStalenessPolicyManager:
    @pytest.fixture
    def manager(self):
        return StalenessPolicyManager(default_max_age_days=30)

    def test_initialization(self):
        manager = StalenessPolicyManager(default_max_age_days=14)
        assert manager.default_max_age_days == 14
        assert "stable" in manager.policies
        assert "active" in manager.policies
        assert "critical" in manager.policies

    def test_default_policies(self, manager):
        assert manager.policies["stable"].max_age_days == 30
        assert manager.policies["active"].max_age_days == 14
        assert manager.policies["critical"].max_age_days == 7

    def test_get_policy_stable(self, manager):
        policy = manager.get_policy("react")
        assert policy.max_age_days == 30
        assert policy.library_type == "stable"

    def test_get_policy_critical_by_name(self, manager):
        policy = manager.get_policy("jwt-auth")
        assert policy.max_age_days == 7
        assert policy.library_type == "critical"

    def test_get_policy_active_by_name(self, manager):
        policy = manager.get_policy("pytest")
        assert policy.max_age_days == 14
        assert policy.library_type == "active"

    def test_get_policy_explicit_type(self, manager):
        policy = manager.get_policy("some-lib", library_type="critical")
        assert policy.max_age_days == 7

    def test_get_policy_invalid_type_defaults(self, manager):
        policy = manager.get_policy("some-lib", library_type="nonexistent")
        # Should default to stable
        assert policy.max_age_days == 30

    def test_set_policy_custom(self, manager):
        manager.set_policy("experimental", max_age_days=3)
        policy = manager.get_policy("some-lib", library_type="experimental")
        assert policy.max_age_days == 3
        assert policy.library_type == "experimental"

    def test_is_entry_stale_fresh(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=10)).isoformat() + "Z"

        assert (
            manager.is_entry_stale("react", last_updated, reference_date=now) is False
        )

    def test_is_entry_stale_old(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=31)).isoformat() + "Z"

        assert manager.is_entry_stale("react", last_updated, reference_date=now) is True

    def test_is_entry_stale_critical_library(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=8)).isoformat() + "Z"

        # Critical libraries stale after 7 days
        assert (
            manager.is_entry_stale("jwt-auth", last_updated, reference_date=now) is True
        )

    def test_get_refresh_recommendation_keep(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=10)).isoformat() + "Z"

        rec = manager.get_refresh_recommendation("react", last_updated)
        assert rec["is_stale"] is False
        assert rec["recommendation"] == "keep"
        assert rec["library_type"] == "stable"

    def test_get_refresh_recommendation_refresh(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=31)).isoformat() + "Z"

        rec = manager.get_refresh_recommendation(
            "react", last_updated, reference_date=now
        )
        assert rec["is_stale"] is True
        assert rec["recommendation"] == "refresh"

    def test_get_refresh_recommendation_consider_refresh(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=25)).isoformat() + "Z"

        rec = manager.get_refresh_recommendation(
            "react", last_updated, reference_date=now
        )
        assert rec["recommendation"] == "consider_refresh"

    def test_library_type_detection_security(self, manager):
        policy = manager.get_policy("security-lib")
        assert policy.library_type == "critical"
        assert policy.max_age_days == 7

    def test_library_type_detection_auth(self, manager):
        policy = manager.get_policy("oauth-client")
        assert policy.library_type == "critical"

    def test_library_type_detection_test(self, manager):
        policy = manager.get_policy("vitest")
        assert policy.library_type == "active"
        assert policy.max_age_days == 14

    def test_library_type_detection_default(self, manager):
        policy = manager.get_policy("some-random-library")
        assert policy.library_type == "stable"
        assert policy.max_age_days == 30

    def test_get_refresh_recommendation_fields(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=10)).isoformat() + "Z"

        rec = manager.get_refresh_recommendation(
            "react", last_updated, reference_date=now
        )

        assert "library" in rec
        assert "is_stale" in rec
        assert "days_until_stale" in rec
        assert "max_age_days" in rec
        assert "library_type" in rec
        assert "recommendation" in rec

    def test_is_entry_stale_with_explicit_type(self, manager):
        now = datetime.now(UTC)
        last_updated = (now - timedelta(days=8)).isoformat() + "Z"

        # Should use explicit type instead of inferring
        assert (
            manager.is_entry_stale(
                "some-lib", last_updated, library_type="critical", reference_date=now
            )
            is True
        )
