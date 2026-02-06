"""Tests for svg_charts module — pure Python SVG chart generators."""

from tapps_agents.dashboard.svg_charts import (
    bar_chart,
    horizontal_bar_chart,
    number_pill,
    radar_chart,
    ring_gauge,
    sparkline,
    status_badge,
)


class TestRingGauge:
    def test_basic_ring(self):
        svg = ring_gauge(75, max_val=100)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "75" in svg  # displayed value

    def test_zero_value(self):
        svg = ring_gauge(0, max_val=100)
        assert "0" in svg

    def test_with_label(self):
        svg = ring_gauge(85, label="Health")
        assert "Health" in svg

    def test_custom_colour(self):
        svg = ring_gauge(50, colour="#ff0000")
        assert "#ff0000" in svg

    def test_custom_size(self):
        svg = ring_gauge(50, size=200)
        assert 'width="200"' in svg

    def test_max_clamp(self):
        """Values > max should clamp to max."""
        svg = ring_gauge(150, max_val=100)
        assert "<svg" in svg

    def test_zero_max(self):
        """Zero max should not crash."""
        svg = ring_gauge(50, max_val=0)
        assert "<svg" in svg


class TestBarChart:
    def test_basic_bars(self):
        svg = bar_chart(["A", "B", "C"], [10, 20, 30])
        assert "<svg" in svg
        assert "<rect" in svg

    def test_empty(self):
        svg = bar_chart([], [])
        assert "<svg" in svg

    def test_single_bar(self):
        svg = bar_chart(["X"], [100])
        assert "<rect" in svg

    def test_zero_values(self):
        svg = bar_chart(["A", "B"], [0, 0])
        assert "<svg" in svg

    def test_no_values_display(self):
        svg = bar_chart(["A"], [5], show_values=False)
        assert "<svg" in svg


class TestHorizontalBarChart:
    def test_basic(self):
        svg = horizontal_bar_chart(["Alpha", "Beta"], [40, 60])
        assert "<svg" in svg
        assert "Alpha" in svg

    def test_empty(self):
        result = horizontal_bar_chart([], [])
        assert result == ""

    def test_custom_colours(self):
        svg = horizontal_bar_chart(["A", "B"], [1, 2], colours=["#f00", "#0f0"])
        assert "#f00" in svg


class TestSparkline:
    def test_basic(self):
        svg = sparkline([1, 3, 2, 5, 4])
        assert "<svg" in svg
        assert "<polyline" in svg

    def test_single_point(self):
        """Single point should return empty SVG."""
        svg = sparkline([5])
        assert "<svg" in svg
        assert "<polyline" not in svg

    def test_empty(self):
        svg = sparkline([])
        assert "<svg" in svg

    def test_no_fill(self):
        svg = sparkline([1, 2, 3], fill=False)
        assert "<polygon" not in svg

    def test_flat_line(self):
        svg = sparkline([5, 5, 5, 5])
        assert "<svg" in svg


class TestStatusBadge:
    def test_healthy(self):
        svg = status_badge("healthy")
        assert "#00b894" in svg  # green

    def test_degraded(self):
        svg = status_badge("degraded")
        assert "#fdcb6e" in svg  # yellow

    def test_unhealthy(self):
        svg = status_badge("unhealthy")
        assert "#ff6b6b" in svg  # red


class TestNumberPill:
    def test_basic(self):
        html = number_pill("42", "Workflows")
        assert "42" in html
        assert "Workflows" in html
        assert "pill" in html


class TestRadarChart:
    def test_basic(self):
        dims = {"complexity": 80, "security": 90, "maintainability": 70}
        svg = radar_chart(dims)
        assert "<svg" in svg
        assert "<polygon" in svg

    def test_empty(self):
        result = radar_chart({})
        assert result == ""

    def test_all_zero(self):
        dims = {"a": 0, "b": 0, "c": 0}
        svg = radar_chart(dims)
        assert "<svg" in svg
