"""
Staleness Policies for Context7 KB cache.

Defines policies for determining when cached entries should be considered stale
and need refresh. Supports library-specific staleness rules.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class StalenessPolicy:
    """Policy for determining entry staleness."""

    max_age_days: int
    library_type: str = "stable"  # stable, active, critical

    def is_stale(
        self, last_updated: str, reference_date: datetime | None = None
    ) -> bool:
        """
        Check if an entry is stale based on last_updated timestamp.

        Args:
            last_updated: ISO format timestamp string (e.g., "2024-01-01T00:00:00Z")
            reference_date: Optional reference date (defaults to now)

        Returns:
            True if entry is stale
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        try:
            # Parse ISO format timestamp - handle both naive and timezone-aware
            updated_str = last_updated
            if updated_str.endswith("Z"):
                updated_str = updated_str[:-1] + "+00:00"

            updated_dt = datetime.fromisoformat(updated_str)
            # Make both dates naive for comparison
            if updated_dt.tzinfo is not None:
                updated_dt = updated_dt.replace(tzinfo=None)
            if reference_date.tzinfo is not None:
                reference_date = reference_date.replace(tzinfo=None)

            age = reference_date - updated_dt
            max_age = timedelta(days=self.max_age_days)

            return age > max_age
        except (ValueError, TypeError):
            # If we can't parse the date, consider it stale for safety
            return True

    def days_until_stale(
        self, last_updated: str, reference_date: datetime | None = None
    ) -> int:
        """
        Calculate days until entry becomes stale.

        Args:
            last_updated: ISO format timestamp string
            reference_date: Optional reference date (defaults to now)

        Returns:
            Days until stale (negative if already stale)
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        try:
            updated_str = last_updated
            if updated_str.endswith("Z"):
                updated_str = updated_str[:-1] + "+00:00"

            updated_dt = datetime.fromisoformat(updated_str)
            # Make both dates naive for comparison
            if updated_dt.tzinfo is not None:
                updated_dt = updated_dt.replace(tzinfo=None)
            if reference_date.tzinfo is not None:
                reference_date = reference_date.replace(tzinfo=None)

            age = reference_date - updated_dt
            max_age = timedelta(days=self.max_age_days)
            remaining = max_age - age

            return remaining.days
        except (ValueError, TypeError):
            return -1


class StalenessPolicyManager:
    """Manages staleness policies for different library types."""

    def __init__(self, default_max_age_days: int = 30):
        """
        Initialize policy manager.

        Args:
            default_max_age_days: Default max age in days for entries
        """
        self.default_max_age_days = default_max_age_days
        self.policies: dict[str, StalenessPolicy] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default staleness policies."""
        # Stable libraries (e.g., react, pytest) - 30 days
        self.policies["stable"] = StalenessPolicy(
            max_age_days=30, library_type="stable"
        )

        # Active libraries (e.g., vitest, playwright) - 14 days
        self.policies["active"] = StalenessPolicy(
            max_age_days=14, library_type="active"
        )

        # Critical libraries (e.g., security-libs, jwt) - 7 days
        self.policies["critical"] = StalenessPolicy(
            max_age_days=7, library_type="critical"
        )

    def get_policy(
        self, library: str, library_type: str | None = None
    ) -> StalenessPolicy:
        """
        Get staleness policy for a library.

        Args:
            library: Library name
            library_type: Optional library type (if None, tries to infer or uses default)

        Returns:
            StalenessPolicy instance
        """
        if library_type and library_type in self.policies:
            return self.policies[library_type]

        # Try to infer library type from name patterns
        library_lower = library.lower()

        if any(
            keyword in library_lower
            for keyword in ["security", "auth", "jwt", "oauth", "encrypt"]
        ):
            return self.policies["critical"]
        elif any(
            keyword in library_lower for keyword in ["test", "spec", "mock", "stub"]
        ):
            return self.policies["active"]
        else:
            return self.policies.get(
                "stable",
                StalenessPolicy(
                    max_age_days=self.default_max_age_days, library_type="stable"
                ),
            )

    def set_policy(self, library_type: str, max_age_days: int):
        """
        Set custom staleness policy for a library type.

        Args:
            library_type: Library type identifier
            max_age_days: Max age in days
        """
        self.policies[library_type] = StalenessPolicy(
            max_age_days=max_age_days, library_type=library_type
        )

    def is_entry_stale(
        self,
        library: str,
        last_updated: str,
        library_type: str | None = None,
        reference_date: datetime | None = None,
    ) -> bool:
        """
        Check if an entry is stale.

        Args:
            library: Library name
            last_updated: ISO format timestamp string
            library_type: Optional library type
            reference_date: Optional reference date

        Returns:
            True if entry is stale
        """
        policy = self.get_policy(library, library_type)
        return policy.is_stale(last_updated, reference_date)

    def get_refresh_recommendation(
        self,
        library: str,
        last_updated: str,
        library_type: str | None = None,
        reference_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get refresh recommendation for an entry.

        Args:
            library: Library name
            last_updated: ISO format timestamp string
            library_type: Optional library type

        Returns:
            Dictionary with refresh recommendation details
        """
        policy = self.get_policy(library, library_type)
        is_stale = policy.is_stale(last_updated, reference_date)
        days_until_stale = policy.days_until_stale(last_updated, reference_date)

        return {
            "library": library,
            "is_stale": is_stale,
            "days_until_stale": days_until_stale,
            "max_age_days": policy.max_age_days,
            "library_type": policy.library_type,
            "recommendation": (
                "refresh"
                if is_stale
                else "keep" if days_until_stale > 7 else "consider_refresh"
            ),
        }
