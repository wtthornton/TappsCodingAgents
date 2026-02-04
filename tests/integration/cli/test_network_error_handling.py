"""
Integration tests for network error handling and graceful degradation.
"""
import uuid
from unittest.mock import patch

import pytest

from tapps_agents.core.network_errors import (
    NetworkError,
    NetworkOptionalError,
    NetworkRequiredError,
)


def test_network_error_has_uuid_request_id():
    """Test that NetworkError generates UUID request IDs."""
    error = NetworkError(operation_name="test operation")
    
    # Verify request_id is a valid UUID string
    request_id = error.request_id
    assert isinstance(request_id, str)
    # Should be able to parse as UUID
    parsed_uuid = uuid.UUID(request_id)
    assert str(parsed_uuid) == request_id


def test_network_error_custom_request_id():
    """Test that NetworkError accepts custom request ID."""
    custom_id = "82eda161-d98e-4c7d-a312-736002798f7b"
    error = NetworkError(operation_name="test", request_id=custom_id)
    
    assert error.request_id == custom_id


def test_network_error_to_dict_format():
    """Test that NetworkError.to_dict() matches Cursor CLI JSON format."""
    error = NetworkError(
        operation_name="test operation",
        request_id="82eda161-d98e-4c7d-a312-736002798f7b",
        session_id="session-123",
        details={"key": "value"},
    )
    
    error_dict = error.to_dict()
    
    assert error_dict["type"] == "error"
    assert error_dict["subtype"] == "connection_error"
    assert error_dict["is_error"] is True
    assert error_dict["operation"] == "test operation"
    assert error_dict["request_id"] == "82eda161-d98e-4c7d-a312-736002798f7b"
    assert error_dict["session_id"] == "session-123"
    assert error_dict["details"] == {"key": "value"}
    assert "message" in error_dict


def test_network_required_error_message():
    """Test that NetworkRequiredError includes network requirement context."""
    error = NetworkRequiredError(
        operation_name="test operation",
        request_id="82eda161-d98e-4c7d-a312-736002798f7b",
    )
    
    message = str(error)
    assert "test operation" in message
    assert "82eda161-d98e-4c7d-a312-736002798f7b" in message
    assert "requires network access" in message.lower()


def test_network_optional_error_message():
    """Test that NetworkOptionalError indicates offline fallback."""
    error = NetworkOptionalError(
        operation_name="test operation",
        request_id="82eda161-d98e-4c7d-a312-736002798f7b",
    )
    
    message = str(error)
    assert "test operation" in message
    assert "offline mode" in message.lower() or "reduced functionality" in message.lower()


def test_network_error_includes_original_error():
    """Test that NetworkError preserves original exception."""
    original = ConnectionError("Original connection failed")
    error = NetworkError(
        operation_name="test",
        original_error=original,
    )
    
    assert error.original_error == original
    assert str(original) in str(error)


def test_network_error_request_id_format():
    """Test that request IDs match expected format (UUID v4)."""
    error = NetworkError(operation_name="test")
    
    # UUID v4 format: 8-4-4-4-12 hex digits
    request_id = error.request_id
    parts = request_id.split("-")
    
    assert len(parts) == 5
    assert len(parts[0]) == 8
    assert len(parts[1]) == 4
    assert len(parts[2]) == 4
    assert len(parts[3]) == 4
    assert len(parts[4]) == 12


def test_error_handling_with_missing_network():
    """Test error handling when network is required but unavailable."""
    from tapps_agents.cli.command_classifier import (
        CommandClassifier,
        CommandNetworkRequirement,
    )
    from tapps_agents.cli.network_detection import NetworkDetector
    from tapps_agents.core.network_errors import NetworkRequiredError
    
    # Mock network unavailable
    with patch.object(NetworkDetector, "is_network_available", return_value=False):
        requirement = CommandClassifier.get_network_requirement("implementer", "implement")
        assert requirement == CommandNetworkRequirement.REQUIRED
        
        # Should raise NetworkRequiredError with proper context
        with pytest.raises(NetworkRequiredError) as exc_info:
            raise NetworkRequiredError(
                operation_name="implementer implement",
                message="Network is required for this command"
            )
        
        error = exc_info.value
        assert error.operation_name == "implementer implement"
        assert error.request_id is not None
        assert isinstance(error.request_id, str)

