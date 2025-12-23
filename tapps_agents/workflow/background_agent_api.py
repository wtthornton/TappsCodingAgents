"""
Background Agent API - Programmatic interface for Cursor Background Agents.

This module provides a programmatic interface to Cursor's Background Agent API,
allowing workflows to trigger and monitor Background Agents.

Based on Cursor 2.0 API documentation (2025).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]

from ..core.offline_mode import OfflineMode

logger = logging.getLogger(__name__)


class BackgroundAgentAPI:
    """
    Programmatic interface to Cursor's Background Agent API.
    
    This class provides methods to interact with Cursor's Background Agents
    programmatically, enabling automated workflow execution.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        """
        Initialize Background Agent API client.

        Args:
            api_key: Cursor API key (if None, tries to get from environment)
            base_url: Base URL for Cursor API (defaults to official API)
        """
        self.api_key = api_key or os.getenv("CURSOR_API_KEY")
        # Based on Cursor documentation: GET /v0/agents
        self.base_url = base_url or "https://api.cursor.com/v0"
        
        if not self.api_key:
            # Try to get from Cursor config
            cursor_config = self._get_cursor_config()
            if cursor_config:
                self.api_key = cursor_config.get("api_key")

    def _get_cursor_config(self) -> dict[str, Any] | None:
        """Get Cursor configuration from local config files."""
        # Try common Cursor config locations
        config_paths = [
            Path.home() / ".cursor" / "config.json",
            Path.home() / ".config" / "cursor" / "config.json",
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, encoding="utf-8") as f:
                        return json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
        
        return None

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def list_agents(self) -> list[dict[str, Any]]:
        """
        List all available Background Agents.

        Based on Cursor API documentation: GET /v0/agents
        
        Note: This endpoint may not exist publicly. If it fails,
        the method returns an empty list for graceful degradation.

        Returns:
            List of agent configurations (empty list if API unavailable)

        Raises:
            requests.RequestException: Only if API key is invalid (401)
        """
        # Check offline mode FIRST
        if OfflineMode.is_offline():
            import logging
            logger = logging.getLogger(__name__)
            logger.debug("Offline mode: skipping list_agents API call")
            return []
        # Based on Cursor docs: GET /v0/agents
        url = f"{self.base_url}/agents"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            # Handle different status codes
            if response.status_code == 404:
                # Endpoint doesn't exist - graceful degradation
                return []
            elif response.status_code == 401:
                # Invalid API key - raise exception
                raise requests.RequestException(
                    f"Unauthorized (401): Invalid API key for {url}"
                )
            
            response.raise_for_status()
            return response.json().get("agents", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Endpoint not found - graceful degradation
                return []
            raise
        except requests.RequestException as e:
            # Network errors, timeouts, etc. - log and degrade gracefully
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Background Agent API unavailable: {e}")
            OfflineMode.record_connection_failure()  # Track failure for offline mode
            return []

    def trigger_agent(
        self,
        agent_id: str,
        command: str,
        worktree_path: str | Path | None = None,
        environment: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Trigger a Background Agent to execute a command.

        Note: This endpoint needs verification. If unavailable,
        returns a placeholder response for graceful degradation.

        Args:
            agent_id: ID of the Background Agent to trigger
            command: Command to execute (Skill command string)
            worktree_path: Optional worktree path
            environment: Optional environment variables

        Returns:
            Execution result with job_id and status.
            If API unavailable, returns placeholder with status "pending"
            and message indicating fallback mode.

        Raises:
            requests.RequestException: Only if API key is invalid (401)
        """
        # Check offline mode FIRST - skip network call entirely if offline
        if OfflineMode.is_offline():
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Offline mode: skipping API call for agent {agent_id}")
            return {
                "status": "pending",
                "job_id": f"local-{agent_id}",
                "message": "Offline mode enabled, using file-based fallback",
                "fallback_mode": True,
            }
        
        # API endpoint structure (to be verified with actual Cursor API docs)
        # Possible endpoints based on research:
        # - POST /v0/background-agents/{id}/trigger
        # - POST /v0/agents/{id}/trigger
        # For now, try the most likely endpoint
        url = f"{self.base_url}/background-agents/{agent_id}/trigger"
        
        payload = {
            "command": command,
        }
        
        if worktree_path:
            payload["worktree_path"] = str(worktree_path)
        
        if environment:
            payload["environment"] = environment
        
        def network_operation():
            return requests.post(
                url, headers=self._get_headers(), json=payload, timeout=30
            )
        
        def local_fallback():
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Using local fallback for agent {agent_id}")
            return None  # Will be handled below
        
        try:
            response = OfflineMode.with_offline_fallback(
                network_operation=network_operation,
                local_fallback=local_fallback,
                operation_name=f"trigger_agent({agent_id})",
            )
            
            # If offline fallback was used, response is None
            if response is None:
                return {
                    "status": "pending",
                    "job_id": f"local-{agent_id}",
                    "message": "Offline mode: using file-based fallback",
                    "fallback_mode": True,
                }
            
            # Handle different status codes
            if response.status_code == 404:
                # Endpoint doesn't exist - graceful degradation
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Background Agent API endpoint not found: {url}")
                return {
                    "status": "pending",
                    "job_id": f"local-{agent_id}",
                    "message": "API endpoint not found, using file-based fallback",
                    "fallback_mode": True,
                }
            elif response.status_code == 401:
                # Invalid API key - raise exception
                raise requests.RequestException(
                    f"Unauthorized (401): Invalid API key for {url}"
                )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Endpoint not found - graceful degradation
                return {
                    "status": "pending",
                    "job_id": f"local-{agent_id}",
                    "message": "API endpoint not found, using file-based fallback",
                    "fallback_mode": True,
                }
            raise
        except requests.RequestException as e:
            # Network errors, timeouts, etc. - graceful degradation
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Background Agent API request failed: {e}")
            OfflineMode.record_connection_failure()  # Track failure for offline mode
            return {
                "status": "pending",
                "job_id": f"local-{agent_id}",
                "message": "API not available, using file-based fallback",
                "error": str(e),
                "fallback_mode": True,
            }

    def get_agent_status(self, job_id: str) -> dict[str, Any]:
        """
        Get the status of a Background Agent execution.

        Note: This endpoint needs verification. If unavailable,
        returns a placeholder response.

        Args:
            job_id: Job ID from trigger_agent response

        Returns:
            Status information. If API unavailable, returns placeholder
            with status "unknown".

        Raises:
            requests.RequestException: Only if API key is invalid (401)
        """
        # Check offline mode FIRST
        if OfflineMode.is_offline():
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Offline mode: skipping get_agent_status API call for {job_id}")
            return {
                "status": "unknown",
                "job_id": job_id,
                "message": "Offline mode enabled",
                "fallback_mode": True,
            }
        
        # Possible endpoints based on research:
        # - GET /v0/background-agents/jobs/{job_id}
        # - GET /v0/background-agents/{job_id}/status
        url = f"{self.base_url}/background-agents/jobs/{job_id}"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            # Handle different status codes
            if response.status_code == 404:
                # Endpoint doesn't exist - graceful degradation
                return {
                    "status": "unknown",
                    "job_id": job_id,
                    "message": "API endpoint not found",
                    "fallback_mode": True,
                }
            elif response.status_code == 401:
                # Invalid API key - raise exception
                raise requests.RequestException(
                    f"Unauthorized (401): Invalid API key for {url}"
                )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Endpoint not found - graceful degradation
                return {
                    "status": "unknown",
                    "job_id": job_id,
                    "message": "API endpoint not found",
                    "fallback_mode": True,
                }
            raise
        except requests.RequestException as e:
            # Network errors, timeouts, etc. - graceful degradation
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Background Agent API status check failed: {e}")
            OfflineMode.record_connection_failure()  # Track failure for offline mode
            return {
                "status": "unknown",
                "job_id": job_id,
                "message": "API not available",
                "error": str(e),
                "fallback_mode": True,
            }

    def get_agent_results(self, job_id: str) -> dict[str, Any]:
        """
        Get the results of a completed Background Agent execution.

        Args:
            job_id: Job ID from trigger_agent response

        Returns:
            Execution results

        Raises:
            requests.RequestException: If API request fails
        """
        # Note: This is a placeholder implementation
        url = f"{self.base_url}/background-agents/jobs/{job_id}/results"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # Graceful degradation
            return {
                "status": "error",
                "job_id": job_id,
                "message": "API not available",
                "error": str(e),
            }

    def wait_for_completion(
        self, job_id: str, timeout: int = 3600, poll_interval: int = 5
    ) -> dict[str, Any]:
        """
        Wait for a Background Agent execution to complete.

        Args:
            job_id: Job ID from trigger_agent response
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            Final execution results

        Raises:
            TimeoutError: If execution exceeds timeout
        """
        import time

        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_agent_status(job_id)
            
            if status.get("status") in ["completed", "failed", "error"]:
                if status.get("status") == "completed":
                    return self.get_agent_results(job_id)
                else:
                    return status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Background Agent execution exceeded timeout of {timeout}s")

