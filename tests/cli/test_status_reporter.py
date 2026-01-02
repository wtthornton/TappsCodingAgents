"""
Tests for StatusReporter.
"""

import sys
import time
from io import StringIO

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.cli.utils.status_reporter import StatusReporter


class TestStatusReporter:
    """Tests for StatusReporter class."""
    
    def test_init_with_total_steps(self):
        """Test StatusReporter initialization with total steps."""
        reporter = StatusReporter(total_steps=7)
        assert reporter.total_steps == 7
        assert reporter.current_step == 0
        assert len(reporter.step_times) == 0
        assert len(reporter.step_status) == 0
    
    def test_init_without_total_steps(self):
        """Test StatusReporter initialization without total steps."""
        reporter = StatusReporter()
        assert reporter.total_steps == 0
        assert reporter.current_step == 0
    
    def test_start_step(self, capsys):
        """Test starting a step."""
        reporter = StatusReporter(total_steps=7)
        reporter.start_step(1, "Test step")
        
        assert reporter.current_step == 1
        assert len(reporter.step_times) == 1
        assert reporter.step_times[0][0] == 1
        assert reporter.step_times[0][1] == "Test step"
        
        # Check output
        captured = capsys.readouterr()
        assert "[1/7]" in captured.err or "Step 1" in captured.err
        assert "Test step" in captured.err
    
    def test_start_step_without_total(self, capsys):
        """Test starting a step without total steps."""
        reporter = StatusReporter()
        reporter.start_step(1, "Test step")
        
        captured = capsys.readouterr()
        assert "[Step 1]" in captured.err
    
    def test_complete_step_success(self, capsys):
        """Test completing a step successfully."""
        reporter = StatusReporter(total_steps=7)
        reporter.start_step(1, "Test step")
        time.sleep(0.01)  # Small delay to ensure duration > 0
        reporter.complete_step(1, "Test step", "success")
        
        assert reporter.step_status[1] == "success"
        assert len(reporter.step_times) == 1
        
        # Check that duration was recorded
        duration = reporter.step_times[0][2]
        assert isinstance(duration, float)
        assert duration > 0
        
        # Check output
        captured = capsys.readouterr()
        assert "[OK]" in captured.err
    
    def test_complete_step_failed(self, capsys):
        """Test completing a step with failure."""
        reporter = StatusReporter(total_steps=7)
        reporter.start_step(1, "Test step")
        reporter.complete_step(1, "Test step", "failed")
        
        assert reporter.step_status[1] == "failed"
        
        captured = capsys.readouterr()
        assert "[FAIL]" in captured.err
    
    def test_complete_step_skipped(self, capsys):
        """Test completing a step as skipped."""
        reporter = StatusReporter(total_steps=7)
        reporter.start_step(1, "Test step")
        reporter.complete_step(1, "Test step", "skipped")
        
        assert reporter.step_status[1] == "skipped"
        
        captured = capsys.readouterr()
        assert "[SKIP]" in captured.err
    
    def test_print_summary(self, capsys):
        """Test printing execution summary."""
        reporter = StatusReporter(total_steps=3)
        
        # Execute some steps
        reporter.start_step(1, "Step 1")
        reporter.complete_step(1, "Step 1", "success")
        
        reporter.start_step(2, "Step 2")
        reporter.complete_step(2, "Step 2", "success")
        
        reporter.print_summary()
        
        captured = capsys.readouterr()
        assert "Execution Summary" in captured.err
        assert "Steps Executed: 2/3" in captured.err
        assert "Total Time:" in captured.err
        assert "Step Details:" in captured.err
    
    def test_print_summary_with_failures(self, capsys):
        """Test printing summary with failed steps."""
        reporter = StatusReporter(total_steps=3)
        
        reporter.start_step(1, "Step 1")
        reporter.complete_step(1, "Step 1", "success")
        
        reporter.start_step(2, "Step 2")
        reporter.complete_step(2, "Step 2", "failed")
        
        reporter.print_summary()
        
        captured = capsys.readouterr()
        assert "Steps Executed: 1/3" in captured.err
        assert "[FAIL]" in captured.err
    
    def test_multiple_steps_tracking(self):
        """Test tracking multiple steps."""
        reporter = StatusReporter(total_steps=5)
        
        for i in range(1, 6):
            reporter.start_step(i, f"Step {i}")
            reporter.complete_step(i, f"Step {i}", "success")
        
        assert len(reporter.step_times) == 5
        assert len(reporter.step_status) == 5
        assert reporter.step_status[5] == "success"
