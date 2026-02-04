"""
Utility functions for domain name handling.
"""

import re
from urllib.parse import urlparse

# Known domain-to-directory name mappings for built-in experts
# Maps expert domain names to their actual knowledge base directory names
# This handles cases where domain names don't match directory names
DOMAIN_TO_DIRECTORY_MAP = {
    "performance-optimization": "performance",
    "ai-agent-framework": "ai-frameworks",
    "testing-strategies": "testing",
}


def sanitize_domain_for_path(domain: str) -> str:
    """
    Sanitize a domain name or URL for use as a directory path.

    Handles URLs by extracting the hostname and path, then sanitizing
    invalid filename characters. This ensures cross-platform compatibility.
    
    Also handles known domain-to-directory name mappings for built-in experts.

    Args:
        domain: Domain name or URL (e.g., "home-automation" or "https://www.home-assistant.io/docs/")

    Returns:
        Sanitized string safe for use as a directory name

    Examples:
        >>> sanitize_domain_for_path("home-automation")
        'home-automation'
        >>> sanitize_domain_for_path("https://www.home-assistant.io/docs/")
        'home-assistant.io-docs'
        >>> sanitize_domain_for_path("https://example.com/api/v1")
        'example.com-api-v1'
        >>> sanitize_domain_for_path("performance-optimization")
        'performance'
    """
    if not domain:
        return "unknown"

    # Check for known domain-to-directory mappings first (built-in experts)
    if domain in DOMAIN_TO_DIRECTORY_MAP:
        return DOMAIN_TO_DIRECTORY_MAP[domain]

    # Try to parse as URL
    try:
        parsed = urlparse(domain)
        if parsed.netloc:  # Has a hostname, it's a URL
            # Extract hostname and path
            parts = [parsed.netloc.replace("www.", "")]
            if parsed.path and parsed.path != "/":
                # Add path segments, removing leading/trailing slashes
                path_parts = [p for p in parsed.path.strip("/").split("/") if p]
                parts.extend(path_parts)
            domain = "-".join(parts)
    except Exception:
        # Not a valid URL, use as-is
        pass

    # Replace invalid filename characters with hyphens
    # Windows invalid chars: < > : " / \ | ? *
    # Also replace spaces, ampersands, and other problematic chars
    sanitized = re.sub(r'[<>:"/\\|?*\s&]+', '-', domain)

    # Remove leading/trailing dots and hyphens (Windows doesn't allow these)
    sanitized = sanitized.strip('.-')

    # Replace multiple consecutive hyphens with single hyphen
    sanitized = re.sub(r'-+', '-', sanitized)

    # Ensure it's not empty and not too long (Windows path limit)
    if not sanitized:
        sanitized = "unknown"
    elif len(sanitized) > 200:  # Reasonable limit for directory names
        sanitized = sanitized[:200].rstrip('-')

    return sanitized.lower()

