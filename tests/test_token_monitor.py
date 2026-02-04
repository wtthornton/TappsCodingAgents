"""Tests for token monitoring system."""

from tapps_agents.core.token_monitor import TokenBudget, TokenMonitor, create_monitor


class TestTokenBudget:
    """Test TokenBudget class."""

    def test_default_initialization(self):
        """Test default token budget initialization."""
        budget = TokenBudget()
        assert budget.total == 200000
        assert budget.consumed == 0
        assert budget.remaining == 200000
        assert budget.usage_percentage == 0.0

    def test_custom_initialization(self):
        """Test custom token budget initialization."""
        budget = TokenBudget(total=100000, consumed=20000, remaining=80000)
        assert budget.total == 100000
        assert budget.consumed == 20000
        assert budget.remaining == 80000

    def test_usage_percentage_calculation(self):
        """Test usage percentage calculation."""
        budget = TokenBudget(total=100000, consumed=25000)
        assert budget.usage_percentage == 25.0

        budget.consumed = 50000
        assert budget.usage_percentage == 50.0

        budget.consumed = 90000
        assert budget.usage_percentage == 90.0

    def test_usage_percentage_zero_total(self):
        """Test usage percentage with zero total."""
        budget = TokenBudget(total=0, consumed=0)
        assert budget.usage_percentage == 0.0

    def test_threshold_green(self):
        """Test green threshold (<50%)."""
        budget = TokenBudget(total=100000, consumed=30000)
        assert budget.check_threshold() == "green"

    def test_threshold_yellow(self):
        """Test yellow threshold (50-74%)."""
        budget = TokenBudget(total=100000, consumed=50000)
        assert budget.check_threshold() == "yellow"

        budget.consumed = 74000
        assert budget.check_threshold() == "yellow"

    def test_threshold_orange(self):
        """Test orange threshold (75-89%)."""
        budget = TokenBudget(total=100000, consumed=75000)
        assert budget.check_threshold() == "orange"

        budget.consumed = 89000
        assert budget.check_threshold() == "orange"

    def test_threshold_red(self):
        """Test red threshold (≥90%)."""
        budget = TokenBudget(total=100000, consumed=90000)
        assert budget.check_threshold() == "red"

        budget.consumed = 99000
        assert budget.check_threshold() == "red"

    def test_to_dict(self):
        """Test dictionary serialization."""
        budget = TokenBudget(total=100000, consumed=50000, remaining=50000)
        data = budget.to_dict()

        assert data["total"] == 100000
        assert data["consumed"] == 50000
        assert data["remaining"] == 50000
        assert data["usage_percentage"] == 50.0
        assert data["threshold"] == "yellow"


class TestTokenMonitor:
    """Test TokenMonitor class."""

    def test_initialization(self):
        """Test monitor initialization."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        assert monitor.budget == budget
        assert monitor.enable_warnings is True
        assert monitor.checkpoint_threshold == 90.0

    def test_update_tokens(self):
        """Test token update."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        result = monitor.update(10000)

        assert result.consumed == 10000
        assert result.remaining == 90000
        assert result.percentage == 10.0
        assert result.threshold == "green"

    def test_threshold_transition_no_warning(self):
        """Test no warning when threshold doesn't change."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        result1 = monitor.update(10000)  # 10% - green
        assert result1.threshold_changed is False  # Still green (started at green)
        assert result1.message is None  # Green has no message

        result2 = monitor.update(10000)  # 20% - still green
        assert result2.threshold_changed is False
        assert result2.message is None

    def test_threshold_transition_yellow_warning(self):
        """Test warning when crossing yellow threshold."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        # Cross into yellow
        result = monitor.update(50000)  # 50%

        assert result.threshold == "yellow"
        assert result.threshold_changed is True
        assert result.message is not None
        assert "⚠️" in result.message
        assert "50%" in result.message

    def test_threshold_transition_orange_warning(self):
        """Test warning when crossing orange threshold."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        # Cross into orange
        monitor.update(50000)  # Yellow
        result = monitor.update(25000)  # 75% - orange

        assert result.threshold == "orange"
        assert result.threshold_changed is True
        assert result.message is not None
        assert "🟠" in result.message
        assert "75%" in result.message

    def test_threshold_transition_red_warning(self):
        """Test warning when crossing red threshold."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        # Cross into red
        result = monitor.update(90000)  # 90%

        assert result.threshold == "red"
        assert result.threshold_changed is True
        assert result.message is not None
        assert "🔴" in result.message
        assert "90%" in result.message
        assert "checkpoint" in result.message.lower()

    def test_should_checkpoint_flag(self):
        """Test checkpoint flag at 90% threshold."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget, checkpoint_threshold=90.0)

        result1 = monitor.update(85000)  # 85%
        assert result1.should_checkpoint is False

        result2 = monitor.update(5000)  # 90%
        assert result2.should_checkpoint is True

    def test_warnings_disabled(self):
        """Test with warnings disabled."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget, enable_warnings=False)

        result = monitor.update(90000)  # Should trigger red

        assert result.threshold == "red"
        assert result.message is None  # No message when disabled

    def test_get_stats(self):
        """Test statistics gathering."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        monitor.update(50000)  # Yellow warning
        monitor.update(25000)  # Orange warning

        stats = monitor.get_stats()

        assert stats["total_updates"] == 2
        assert stats["warnings_issued"] == 2
        assert stats["current_threshold"] == "orange"
        assert stats["budget"]["consumed"] == 75000

    def test_format_status_simple(self):
        """Test status formatting (simple)."""
        budget = TokenBudget(total=200000)
        monitor = TokenMonitor(budget)
        monitor.update(50000)  # 25%

        status = monitor.format_status(verbose=False)

        assert "✅" in status  # Green
        assert "50K" in status  # Consumed
        assert "200K" in status  # Total
        assert "25.0%" in status  # Percentage
        assert "150K remaining" in status

    def test_format_status_verbose(self):
        """Test status formatting (verbose)."""
        budget = TokenBudget(total=200000)
        monitor = TokenMonitor(budget)
        monitor.update(100000)  # 50% - yellow

        status = monitor.format_status(verbose=True)

        assert "⚠️" in status  # Yellow
        assert "Updates:" in status
        assert "Warnings:" in status
        assert "Threshold:" in status

    def test_reset_monitor(self):
        """Test monitor reset."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        monitor.update(90000)  # Red threshold

        monitor.reset()

        assert monitor.budget.consumed == 0
        assert monitor.budget.remaining == 100000
        assert monitor._last_threshold == "green"
        assert monitor._update_count == 0
        assert len(monitor._warning_history) == 0

    def test_reset_with_new_total(self):
        """Test reset with new total."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        monitor.update(50000)
        monitor.reset(new_total=200000)

        assert monitor.budget.total == 200000
        assert monitor.budget.consumed == 0
        assert monitor.budget.remaining == 200000

    def test_multiple_updates(self):
        """Test multiple sequential updates."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        results = [
            monitor.update(10000),  # 10%
            monitor.update(20000),  # 30%
            monitor.update(30000),  # 60% - yellow
            monitor.update(20000),  # 80% - orange
            monitor.update(15000),  # 95% - red
        ]

        assert results[0].threshold == "green"
        assert results[1].threshold == "green"
        assert results[2].threshold == "yellow"
        assert results[3].threshold == "orange"
        assert results[4].threshold == "red"

        # Check warnings only on transitions
        assert results[0].message is None  # Green (initial)
        assert results[1].message is None  # Still green
        assert results[2].message is not None  # Green → yellow
        assert results[3].message is not None  # Yellow → orange
        assert results[4].message is not None  # Orange → red

    def test_result_to_dict(self):
        """Test result serialization."""
        budget = TokenBudget(total=100000)
        monitor = TokenMonitor(budget)

        result = monitor.update(50000)
        data = result.to_dict()

        assert data["consumed"] == 50000
        assert data["remaining"] == 50000
        assert data["percentage"] == 50.0
        assert data["threshold"] == "yellow"
        assert "timestamp" in data


class TestCreateMonitor:
    """Test create_monitor factory function."""

    def test_default_creation(self):
        """Test default monitor creation."""
        monitor = create_monitor()

        assert monitor.budget.total == 200000
        assert monitor.enable_warnings is True
        assert monitor.checkpoint_threshold == 90.0

    def test_custom_creation(self):
        """Test custom monitor creation."""
        monitor = create_monitor(
            total=150000,
            enable_warnings=False,
            checkpoint_threshold=85.0
        )

        assert monitor.budget.total == 150000
        assert monitor.enable_warnings is False
        assert monitor.checkpoint_threshold == 85.0

    def test_created_monitor_works(self):
        """Test that created monitor functions correctly."""
        monitor = create_monitor(total=100000)

        result = monitor.update(60000)

        assert result.consumed == 60000
        assert result.threshold == "yellow"
