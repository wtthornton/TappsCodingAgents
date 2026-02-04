"""
Network availability detection utilities.

Following 2025 best practices:
- Short timeout (2 seconds) to avoid blocking
- Fail-safe approach (assume offline if check fails)
- Lightweight HEAD requests for connectivity
"""
import logging
import socket

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment, unused-ignore]

logger = logging.getLogger(__name__)


class NetworkDetector:
    """Network availability detector with lightweight checks.
    
    Following 2025 best practices:
    - Short timeout (2 seconds) to avoid blocking
    - Fail-safe approach (assume offline if check fails)
    - Lightweight HEAD requests for connectivity
    """
    
    # Short timeout to avoid blocking (2025 best practice: 2 seconds)
    CHECK_TIMEOUT = 2.0
    
    @staticmethod
    def is_network_available() -> bool:
        """Quick check if network is available.
        
        Uses lightweight checks with short timeout to avoid blocking.
        Returns False if any check fails (fail-safe approach).
        
        Returns:
            True if network appears available, False otherwise
        """
        if httpx is None:
            logger.debug("httpx not available, assuming network unavailable")
            return False
            
        try:
            # Check OpenAI API endpoint (most critical for TappsCodingAgents)
            return NetworkDetector.check_openai_api()
        except Exception as e:
            logger.debug(f"Network check failed: {e}")
            return False
    
    @staticmethod
    def check_openai_api() -> bool:
        """Check OpenAI API availability.
        
        Returns:
            True if OpenAI API endpoint is reachable, False otherwise
        """
        if httpx is None:
            return False
            
        try:
            # Lightweight HEAD request to check connectivity
            # Note: 401/403 responses indicate reachable but auth needed - that's OK
            with httpx.Client(timeout=NetworkDetector.CHECK_TIMEOUT) as client:
                response = client.head("https://api.openai.com/v1/models")
                return response.status_code in (200, 401, 403)
        except (httpx.ConnectError, httpx.TimeoutException, socket.gaierror):
            return False
        except Exception as e:
            logger.debug(f"OpenAI API check failed: {e}")
            return False
    
    @staticmethod
    def check_context7_api() -> bool:
        """Check Context7 API availability.
        
        Returns:
            True if Context7 API endpoint is reachable, False otherwise
        """
        if httpx is None:
            return False
            
        try:
            with httpx.Client(timeout=NetworkDetector.CHECK_TIMEOUT) as client:
                response = client.head("https://api.context7.com/health", follow_redirects=True)
                return response.status_code < 500
        except (httpx.ConnectError, httpx.TimeoutException, socket.gaierror):
            return False
        except Exception:
            return False
    
    @staticmethod
    def check_network_requirements() -> dict[str, bool]:
        """Check availability of specific network dependencies.
        
        Returns a dictionary with availability status for each service.
        Useful for detailed diagnostics.
        
        Returns:
            Dictionary mapping service names to availability status
        """
        return {
            "openai_api": NetworkDetector.check_openai_api(),
            "context7_api": NetworkDetector.check_context7_api(),
            "general_internet": NetworkDetector.is_network_available(),
        }

