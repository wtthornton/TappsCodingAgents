"""
Unit tests for network detection utilities.
"""
import socket
from unittest.mock import MagicMock, patch

import httpx
import pytest

from tapps_agents.cli.network_detection import NetworkDetector


@patch("httpx.Client")
def test_check_openai_api_success(mock_client_class):
    """Test successful OpenAI API check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.head.return_value = mock_response
    mock_client_class.return_value = mock_client

    assert NetworkDetector.check_openai_api() is True


@patch("httpx.Client")
def test_check_openai_api_401_auth_required(mock_client_class):
    """Test OpenAI API check with 401 (auth required but reachable)."""
    mock_response = MagicMock()
    mock_response.status_code = 401  # Auth required - endpoint is reachable
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.head.return_value = mock_response
    mock_client_class.return_value = mock_client

    assert NetworkDetector.check_openai_api() is True


@patch("httpx.Client")
def test_check_openai_api_connection_error(mock_client_class):
    """Test OpenAI API check with connection error."""
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.head.side_effect = httpx.ConnectError("Connection failed")
    mock_client_class.return_value = mock_client

    assert NetworkDetector.check_openai_api() is False


@patch("httpx.Client")
def test_check_openai_api_timeout(mock_client_class):
    """Test OpenAI API check with timeout."""
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.head.side_effect = httpx.TimeoutException("Timeout")
    mock_client_class.return_value = mock_client

    assert NetworkDetector.check_openai_api() is False


@patch("httpx.Client")
def test_check_openai_api_socket_error(mock_client_class):
    """Test OpenAI API check with socket error."""
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.head.side_effect = socket.gaierror("Name resolution failed")
    mock_client_class.return_value = mock_client

    assert NetworkDetector.check_openai_api() is False


@patch("httpx.Client")
def test_check_context7_api_success(mock_client_class):
    """Test successful Context7 API check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.head.return_value = mock_response
    mock_client_class.return_value = mock_client

    assert NetworkDetector.check_context7_api() is True


@patch("httpx.Client")
def test_check_context7_api_connection_error(mock_client_class):
    """Test Context7 API check with connection error."""
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.head.side_effect = httpx.ConnectError("Connection failed")
    mock_client_class.return_value = mock_client

    assert NetworkDetector.check_context7_api() is False


@patch("tapps_agents.cli.network_detection.NetworkDetector.check_openai_api")
def test_is_network_available_true(mock_check):
    """Test network availability check returns True when API is reachable."""
    mock_check.return_value = True
    assert NetworkDetector.is_network_available() is True


@patch("tapps_agents.cli.network_detection.NetworkDetector.check_openai_api")
def test_is_network_available_false(mock_check):
    """Test network availability check returns False when API is unreachable."""
    mock_check.return_value = False
    assert NetworkDetector.is_network_available() is False


@patch("tapps_agents.cli.network_detection.NetworkDetector.check_openai_api")
def test_is_network_available_exception(mock_check):
    """Test network availability check handles exceptions gracefully."""
    mock_check.side_effect = Exception("Unexpected error")
    assert NetworkDetector.is_network_available() is False


def test_check_network_requirements():
    """Test detailed network requirements check."""
    with patch("tapps_agents.cli.network_detection.NetworkDetector.check_openai_api") as mock_openai, \
         patch("tapps_agents.cli.network_detection.NetworkDetector.check_context7_api") as mock_context7, \
         patch("tapps_agents.cli.network_detection.NetworkDetector.is_network_available") as mock_general:
        
        mock_openai.return_value = True
        mock_context7.return_value = False
        mock_general.return_value = True
        
        result = NetworkDetector.check_network_requirements()
        
        assert result["openai_api"] is True
        assert result["context7_api"] is False
        assert result["general_internet"] is True

