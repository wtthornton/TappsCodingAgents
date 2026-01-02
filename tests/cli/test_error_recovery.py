"""
Tests for ErrorRecoveryHandler.
"""

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.cli.utils.error_recovery import ErrorRecoveryHandler


class TestErrorRecoveryHandler:
    """Tests for ErrorRecoveryHandler class."""
    
    def test_init_non_interactive(self):
        """Test initialization in non-interactive mode."""
        handler = ErrorRecoveryHandler(interactive=False)
        assert handler.interactive is False
        assert len(handler.recovery_actions) == 0
    
    def test_init_interactive(self):
        """Test initialization in interactive mode."""
        handler = ErrorRecoveryHandler(interactive=True)
        assert handler.interactive is True
    
    def test_determine_recovery_strategy_timeout(self):
        """Test recovery strategy for timeout errors."""
        handler = ErrorRecoveryHandler()
        error = TimeoutError("Connection timeout")
        strategy = handler._determine_recovery_strategy(error, "test step")
        assert strategy == "retry"
    
    def test_determine_recovery_strategy_network(self):
        """Test recovery strategy for network errors."""
        handler = ErrorRecoveryHandler()
        error = ConnectionError("Network error")
        strategy = handler._determine_recovery_strategy(error, "test step")
        assert strategy == "retry"
    
    def test_determine_recovery_strategy_validation_non_critical(self):
        """Test recovery strategy for validation errors in non-critical steps."""
        handler = ErrorRecoveryHandler()
        error = ValueError("Validation error")
        strategy = handler._determine_recovery_strategy(error, "review step")
        assert strategy == "skip"
    
    def test_determine_recovery_strategy_validation_critical(self):
        """Test recovery strategy for validation errors in critical steps."""
        handler = ErrorRecoveryHandler()
        error = ValueError("Validation error")
        strategy = handler._determine_recovery_strategy(error, "implement step")
        assert strategy == "fail"
    
    def test_determine_recovery_strategy_file_not_found_non_critical(self):
        """Test recovery strategy for file not found in non-critical steps."""
        handler = ErrorRecoveryHandler()
        error = FileNotFoundError("File not found")
        strategy = handler._determine_recovery_strategy(error, "document step")
        assert strategy == "continue"
    
    def test_determine_recovery_strategy_file_not_found_critical(self):
        """Test recovery strategy for file not found in critical steps."""
        handler = ErrorRecoveryHandler()
        error = FileNotFoundError("File not found")
        strategy = handler._determine_recovery_strategy(error, "implement step")
        assert strategy == "fail"
    
    def test_determine_recovery_strategy_unknown_error(self):
        """Test recovery strategy for unknown errors."""
        handler = ErrorRecoveryHandler()
        error = RuntimeError("Unknown error")
        strategy = handler._determine_recovery_strategy(error, "test step")
        assert strategy == "fail"
    
    def test_handle_step_error_retry_success(self):
        """Test handling step error with successful retry."""
        handler = ErrorRecoveryHandler()
        retry_called = []
        
        def retry_callback():
            retry_called.append(True)
        
        error = TimeoutError("Timeout")
        action = handler.handle_step_error(
            step_num=1,
            step_name="test step",
            error=error,
            retry_callback=retry_callback,
        )
        
        assert action == "retry"
        assert len(retry_called) == 1
        assert len(handler.recovery_actions) == 1
        assert handler.recovery_actions[0]["recovery_action"] == "retry"
        assert handler.recovery_actions[0]["recovery_success"] is True
    
    def test_handle_step_error_retry_failure(self):
        """Test handling step error with failed retry."""
        handler = ErrorRecoveryHandler()
        
        def retry_callback():
            raise RuntimeError("Retry failed")
        
        error = TimeoutError("Timeout")
        action = handler.handle_step_error(
            step_num=1,
            step_name="test step",
            error=error,
            retry_callback=retry_callback,
        )
        
        assert action == "fail"
        assert len(handler.recovery_actions) == 1
        assert handler.recovery_actions[0]["recovery_action"] == "retry"
        assert handler.recovery_actions[0]["recovery_success"] is False
    
    def test_handle_step_error_skip(self):
        """Test handling step error with skip action."""
        handler = ErrorRecoveryHandler()
        skip_called = []
        
        def skip_callback():
            skip_called.append(True)
        
        error = ValueError("Validation error")
        action = handler.handle_step_error(
            step_num=1,
            step_name="review step",
            error=error,
            skip_callback=skip_callback,
        )
        
        assert action == "skip"
        assert len(skip_called) == 1
        assert handler.recovery_actions[0]["recovery_action"] == "skip"
    
    def test_handle_step_error_continue(self):
        """Test handling step error with continue action."""
        handler = ErrorRecoveryHandler()
        continue_called = []
        
        def continue_callback():
            continue_called.append(True)
        
        error = FileNotFoundError("File not found")
        action = handler.handle_step_error(
            step_num=1,
            step_name="document step",
            error=error,
            continue_callback=continue_callback,
        )
        
        assert action == "continue"
        assert len(continue_called) == 1
        assert handler.recovery_actions[0]["recovery_action"] == "continue"
    
    def test_handle_step_error_fail(self):
        """Test handling step error with fail action."""
        handler = ErrorRecoveryHandler()
        error = RuntimeError("Unknown error")
        action = handler.handle_step_error(
            step_num=1,
            step_name="test step",
            error=error,
        )
        
        assert action == "fail"
        assert handler.recovery_actions[0]["recovery_action"] == "fail"
    
    def test_get_recovery_summary(self):
        """Test getting recovery summary."""
        handler = ErrorRecoveryHandler()
        
        # Add some recovery actions
        handler.handle_step_error(1, "step1", TimeoutError("timeout"), retry_callback=lambda: None)
        handler.handle_step_error(2, "review step", ValueError("validation error"), skip_callback=lambda: None)
        handler.handle_step_error(3, "step3", RuntimeError("error"))
        
        summary = handler.get_recovery_summary()
        
        assert summary["total_recoveries"] == 3
        assert summary["retries"] == 1
        assert summary["skips"] == 1
        assert summary["failures"] == 1
        assert summary["continues"] == 0
        assert len(summary["actions"]) == 3
