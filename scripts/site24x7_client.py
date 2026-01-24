"""
Site24x7 API client using Zoho OAuth2 refresh_token flow.

This module provides a minimal client for interacting with the Site24x7 API
using Zoho OAuth2 authentication. The client automatically handles token
refresh and provides convenience methods for common API operations.

Auth header format for Site24x7:
    Authorization: Zoho-oauthtoken <access_token>
"""

import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class Site24x7Client:
    """
    Minimal Site24x7 API client using Zoho OAuth2 refresh_token flow.

    This client handles OAuth2 token refresh automatically and provides
    a simple interface for making authenticated API requests to Site24x7.

    Args:
        client_id: Zoho OAuth2 client ID
        client_secret: Zoho OAuth2 client secret
        refresh_token: Zoho OAuth2 refresh token
        api_base_url: Site24x7 API base URL (default: https://www.site24x7.com/api)
        token_url: Zoho OAuth2 token endpoint (default: https://accounts.zoho.com/oauth/v2/token)
        timeout_s: Request timeout in seconds (default: 30)

    Example:
        ```python
        client = Site24x7Client(
            client_id=os.environ["SITE24X7_CLIENT_ID"],
            client_secret=os.environ["SITE24X7_CLIENT_SECRET"],
            refresh_token=os.environ["SITE24X7_REFRESH_TOKEN"],
        )
        status = client.current_status()
        ```

    Note:
        For EU data centers, use:
        - api_base_url="https://www.site24x7.eu/api"
        - token_url="https://accounts.zoho.eu/oauth/v2/token"
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        api_base_url: str = "https://www.site24x7.com/api",
        token_url: str = "https://accounts.zoho.com/oauth/v2/token",
        timeout_s: int = 30,
    ):
        if not client_id:
            raise ValueError("client_id cannot be empty")
        if not client_secret:
            raise ValueError("client_secret cannot be empty")
        if not refresh_token:
            raise ValueError("refresh_token cannot be empty")
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")

        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.api_base_url = api_base_url.rstrip("/")
        self.token_url = token_url
        self.timeout_s = timeout_s

        self._access_token: str | None = None
        self._access_token_expiry_epoch: float = 0.0  # unix epoch seconds

        logger.debug(
            f"Site24x7Client initialized with api_base_url={self.api_base_url}, "
            f"token_url={self.token_url}, timeout_s={self.timeout_s}"
        )

    def _refresh_access_token(self) -> str:
        """
        Exchange refresh_token -> access_token.

        Zoho returns JSON containing access_token and expires_in (seconds) in most cases.
        The token is refreshed 60 seconds before expiry to avoid race conditions.

        Returns:
            The new access token string.

        Raises:
            RuntimeError: If the token response is missing access_token.
            requests.RequestException: If the token refresh request fails.
        """
        logger.debug("Refreshing access token")
        try:
            resp = requests.post(
                self.token_url,
                data={
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
                timeout=self.timeout_s,
            )
            resp.raise_for_status()
            payload = resp.json()

            if "access_token" not in payload:
                error_msg = "Token response missing access_token"
                logger.error(f"{error_msg}: {payload}")
                raise RuntimeError(error_msg)

            access_token = payload["access_token"]

            # Some Zoho responses include expires_in / expires_in_sec; handle both.
            expires_in = payload.get("expires_in_sec", payload.get("expires_in", 3600))
            # Refresh a bit early so we don't race expiry.
            self._access_token_expiry_epoch = time.time() + int(expires_in) - 60
            self._access_token = access_token

            logger.debug(
                f"Access token refreshed successfully, expires in {expires_in} seconds"
            )
            return access_token
        except requests.RequestException as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise

    def _get_access_token(self) -> str:
        """
        Get current access token, refreshing if necessary.

        Returns:
            Valid access token string.
        """
        if self._access_token and time.time() < self._access_token_expiry_epoch:
            return self._access_token
        return self._refresh_access_token()

    def _headers(self) -> dict[str, str]:
        """
        Get HTTP headers for authenticated requests.

        Returns:
            Dictionary with Authorization and Accept headers.
        """
        token = self._get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Accept": "application/json",
        }

    def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Make a GET request to the Site24x7 API.

        Args:
            path: API endpoint path (leading slash optional)
            params: Optional query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: If the request fails
        """
        if not path:
            raise ValueError("path cannot be empty")

        url = f"{self.api_base_url}/{path.lstrip('/')}"
        logger.debug(f"Making GET request to {url} with params={params}")

        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self.timeout_s,
            )
            resp.raise_for_status()
            # Site24x7 returns JSON for most endpoints
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"GET request to {url} failed: {e}")
            raise

    def post(
        self, path: str, data: dict[str, Any] | None = None, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Make a POST request to the Site24x7 API.

        Args:
            path: API endpoint path (leading slash optional)
            data: Optional form data
            json: Optional JSON payload

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: If the request fails
        """
        if not path:
            raise ValueError("path cannot be empty")

        url = f"{self.api_base_url}/{path.lstrip('/')}"
        logger.debug(f"Making POST request to {url}")

        try:
            resp = requests.post(
                url,
                headers=self._headers(),
                data=data,
                json=json,
                timeout=self.timeout_s,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"POST request to {url} failed: {e}")
            raise

    # --- Example convenience calls ---
    def current_status(self, group_required: bool = False) -> dict[str, Any]:
        """
        Get current status of all monitors.

        Known endpoint used in the wild:
            https://www.site24x7.com/api/current_status?group_required=false

        Args:
            group_required: If True, include group information in response

        Returns:
            Dictionary containing current status information
        """
        return self.get(
            "/current_status", params={"group_required": str(group_required).lower()}
        )


def main() -> None:
    """
    Example usage of Site24x7Client.

    Prefer env vars so you don't hardcode secrets in code.
    """
    # Prefer env vars so you don't hardcode secrets in code.
    client = Site24x7Client(
        client_id=os.environ["SITE24X7_CLIENT_ID"],
        client_secret=os.environ["SITE24X7_CLIENT_SECRET"],
        refresh_token=os.environ["SITE24X7_REFRESH_TOKEN"],
        # Change these if your Site24x7 account is in another DC, e.g. EU:
        # api_base_url="https://www.site24x7.eu/api",
        # token_url="https://accounts.zoho.eu/oauth/v2/token",
    )

    status = client.current_status(group_required=False)
    print("Top-level keys:", list(status.keys()))
    print("Sample payload snippet:", str(status)[:500])


if __name__ == "__main__":
    # Configure logging for example usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
