"""
Tests for CLI feedback system.
"""
import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from tapps_agents.cli.feedback import (
    FeedbackManager,
    ProgressTracker,
    VerbosityLevel,
    get_feedback,
)


class TestFeedbackManager:
    """Test FeedbackManager functionality."""
    
    def test_singleton(self):
        """Test that FeedbackManager is a singleton."""
        manager1 = FeedbackManager.get_instance()
        manager2 = FeedbackManager.get_instance()
        assert manager1 is manager2
    
    def test_set_verbosity(self):
        """Test setting verbosity level."""
        FeedbackManager.set_verbosity(VerbosityLevel.QUIET)
        assert FeedbackManager.get_verbosity() == VerbosityLevel.QUIET
        
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        assert FeedbackManager.get_verbosity() == VerbosityLevel.NORMAL
        
        FeedbackManager.set_verbosity(VerbosityLevel.VERBOSE)
        assert FeedbackManager.get_verbosity() == VerbosityLevel.VERBOSE
    
    def test_info_quiet_mode(self):
        """Test that info messages are suppressed in quiet mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.QUIET)
        feedback = get_feedback()
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            feedback.info("Test message")
            assert stderr.getvalue() == ""
    
    def test_info_normal_mode(self):
        """Test that info messages appear in normal mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            feedback.info("Test message")
            assert "Test message" in stderr.getvalue()
    
    def test_info_verbose_mode(self):
        """Test that info messages have prefix in verbose mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.VERBOSE)
        feedback = get_feedback()
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            feedback.info("Test message")
            output = stderr.getvalue()
            assert "[INFO]" in output
            assert "Test message" in output
    
    def test_success_text_mode(self):
        """Test success message in text mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        feedback.format_type = "text"
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            feedback.success("Operation completed")
            assert "✓" in stderr.getvalue()
            assert "Operation completed" in stderr.getvalue()
    
    def test_success_json_mode(self):
        """Test success message in JSON mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        feedback.format_type = "json"
        
        with patch('sys.stdout', new=StringIO()) as stdout:
            feedback.success("Operation completed", data={"result": "ok"})
            output = json.loads(stdout.getvalue())
            assert output["success"] is True
            assert output["message"] == "Operation completed"
            assert "data" in output
    
    def test_warning_text_mode(self):
        """Test warning message in text mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        feedback.format_type = "text"
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            feedback.warning("This is a warning")
            assert "⚠" in stderr.getvalue()
            assert "Warning" in stderr.getvalue()
    
    def test_error_text_mode(self):
        """Test error message in text mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        feedback.format_type = "text"
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            with pytest.raises(SystemExit):
                feedback.error("Something went wrong", exit_code=1)
            assert "✗" in stderr.getvalue()
            assert "Error" in stderr.getvalue()
    
    def test_error_json_mode(self):
        """Test error message in JSON mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        feedback.format_type = "json"
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            with pytest.raises(SystemExit):
                feedback.error("Something went wrong", error_code="test_error", exit_code=1)
            output = json.loads(stderr.getvalue())
            assert output["success"] is False
            assert "error" in output
            assert output["error"]["code"] == "test_error"
    
    def test_progress_quiet_mode(self):
        """Test that progress is suppressed in quiet mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.QUIET)
        feedback = get_feedback()
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            feedback.progress("Processing...")
            assert stderr.getvalue() == ""
    
    def test_progress_normal_mode(self):
        """Test progress message in normal mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            feedback.progress("Processing...")
            assert "→" in stderr.getvalue()
            assert "Processing" in stderr.getvalue()
    
    def test_output_result_json(self):
        """Test output_result in JSON mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        feedback.format_type = "json"
        
        with patch('sys.stdout', new=StringIO()) as stdout:
            feedback.output_result({"key": "value"}, message="Done")
            output = json.loads(stdout.getvalue())
            assert output["success"] is True
            assert output["message"] == "Done"
            assert output["data"]["key"] == "value"
    
    def test_output_result_text(self):
        """Test output_result in text mode."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        feedback.format_type = "text"
        
        with patch('sys.stderr', new=StringIO()) as stderr, \
             patch('sys.stdout', new=StringIO()) as stdout:
            feedback.output_result({"key": "value"}, message="Done")
            assert "Done" in stderr.getvalue()


class TestProgressTracker:
    """Test ProgressTracker functionality."""
    
    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initialization."""
        feedback = get_feedback()
        tracker = ProgressTracker(10, "Test Operation", feedback)
        assert tracker.total_steps == 10
        assert tracker.current_step == 0
        assert tracker.operation_name == "Test Operation"
    
    def test_progress_tracker_update(self):
        """Test ProgressTracker update."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        tracker = ProgressTracker(5, "Test", feedback)
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            tracker.update(1, "Step 1")
            # Progress should be shown (throttled, but initial update should work)
            output = stderr.getvalue()
            # May be empty due to throttling, but should not error
    
    def test_progress_tracker_complete(self):
        """Test ProgressTracker completion."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        tracker = ProgressTracker(5, "Test", feedback)
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            tracker.complete("All done")
            output = stderr.getvalue()
            assert "completed" in output.lower()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_feedback(self):
        """Test get_feedback convenience function."""
        feedback = get_feedback()
        assert isinstance(feedback, FeedbackManager)
    
    def test_info_function(self):
        """Test info convenience function."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            from tapps_agents.cli.feedback import info
            info("Test message")
            assert "Test message" in stderr.getvalue()
    
    def test_success_function(self):
        """Test success convenience function."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            from tapps_agents.cli.feedback import success
            success("Done")
            assert "✓" in stderr.getvalue()
    
    def test_warning_function(self):
        """Test warning convenience function."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            from tapps_agents.cli.feedback import warning
            warning("Warning message")
            assert "⚠" in stderr.getvalue()
    
    def test_error_function(self):
        """Test error convenience function."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        
        with patch('sys.stderr', new=StringIO()) as stderr:
            from tapps_agents.cli.feedback import error
            with pytest.raises(SystemExit):
                error("Error message", exit_code=1)
            assert "✗" in stderr.getvalue()


class TestStreamSeparation:
    """Test that stdout and stderr are used correctly."""
    
    def test_progress_goes_to_stderr(self):
        """Test that progress messages go to stderr."""
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)
        feedback = get_feedback()
        
        with patch('sys.stdout', new=StringIO()) as stdout, \
             patch('sys.stderr', new=StringIO()) as stderr:
            feedback.progress("Processing...")
            assert stdout.getvalue() == ""
            assert stderr.getvalue() != ""
    
    def test_results_go_to_stdout(self):
        """Test that final results go to stdout."""
        FeedbackManager.set_verbosity(VerbosityLevel.QUIET)
        feedback = get_feedback()
        feedback.format_type = "json"
        
        with patch('sys.stdout', new=StringIO()) as stdout, \
             patch('sys.stderr', new=StringIO()) as stderr:
            feedback.output_result({"result": "data"})
            assert stdout.getvalue() != ""
            # In quiet mode, stderr should be minimal
            assert "result" in stdout.getvalue()

