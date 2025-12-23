"""
Credential Validation for Context7 Integration.

Validates Context7 API credentials and provides actionable error messages.
"""

import logging
import os
from dataclasses import dataclass

from ..mcp.gateway import MCPGateway

logger = logging.getLogger(__name__)


@dataclass
class CredentialValidationResult:
    """Result of credential validation."""

    valid: bool
    error: str | None = None
    actionable_message: str | None = None
    credential_source: str | None = None  # "env", "config", "mcp"


class CredentialValidator:
    """Validates Context7 credentials."""

    def __init__(self, mcp_gateway: MCPGateway | None = None):
        """
        Initialize credential validator.

        Args:
            mcp_gateway: Optional MCPGateway instance for testing credentials
        """
        self.mcp_gateway = mcp_gateway

    def validate_credentials(self) -> CredentialValidationResult:
        """
        Validate Context7 credentials.

        R2/R3: Improved availability detection with clear error messages.

        Checks:
        1. Runtime mode (Cursor vs headless)
        2. MCP server availability (Cursor mode preferred)
        3. Environment variables (or encrypted storage) for fallback
        4. Provides actionable error messages

        Returns:
            CredentialValidationResult
        """
        from ..core.runtime_mode import is_cursor_mode
        
        # R2: Check runtime mode first
        in_cursor_mode = is_cursor_mode()
        
        # Check MCP gateway availability (preferred in Cursor mode)
        if self.mcp_gateway:
            from .backup_client import check_mcp_tools_available
            mcp_available, mcp_source = check_mcp_tools_available(self.mcp_gateway)
            
            if mcp_available:
                if mcp_source == "cursor_mcp":
                    # R2: In Cursor mode, MCP tools are available - no API key needed
                    return CredentialValidationResult(
                        valid=True,
                        credential_source="mcp",
                        actionable_message="Context7 MCP tools available via Cursor's MCP server (no API key needed)",
                    )
                elif mcp_source == "local_gateway":
                    return CredentialValidationResult(
                        valid=True,
                        credential_source="mcp",
                        actionable_message="Context7 MCP tools available via local gateway",
                    )
        
        # Check environment variables or encrypted storage (for HTTP fallback)
        try:
            from .backup_client import _ensure_context7_api_key
            context7_key = _ensure_context7_api_key()
        except Exception:
            context7_key = os.getenv("CONTEXT7_API_KEY")
        
        if context7_key:
            # Determine source (env or encrypted storage)
            source = "env" if os.getenv("CONTEXT7_API_KEY") else "encrypted_storage"
            return CredentialValidationResult(
                valid=True,
                credential_source=source,
                actionable_message=f"Context7 API key found ({'environment variable' if source == 'env' else 'encrypted storage'}) - will use HTTP fallback",
            )

        # R3: No credentials found - provide actionable error message
        if in_cursor_mode:
            # In Cursor mode, suggest MCP server configuration
            return CredentialValidationResult(
                valid=False,
                error="No Context7 credentials found",
                actionable_message=(
                    "Context7 is not configured. In Cursor mode, you can:\n"
                    "1. Configure Context7 MCP server in `.cursor/mcp.json` (recommended)\n"
                    "2. Set CONTEXT7_API_KEY environment variable for HTTP fallback\n\n"
                    "To configure MCP server:\n"
                    "  Run: tapps-agents init (creates .cursor/mcp.json)\n"
                    "  Or manually add Context7 server to your MCP settings"
                ),
            )
        else:
            # In headless mode, suggest API key
            return CredentialValidationResult(
                valid=False,
                error="No Context7 credentials found",
                actionable_message=(
                    "Context7 credentials are not configured. To set up:\n"
                    "1. Set CONTEXT7_API_KEY environment variable\n"
                    "2. Or configure Context7 MCP server in your MCP settings\n\n"
                    "For local development:\n"
                    "  export CONTEXT7_API_KEY='your-api-key'\n\n"
                    "For CI/CD:\n"
                    "  Add CONTEXT7_API_KEY to your CI/CD secrets"
                ),
            )

    async def test_credentials(self) -> CredentialValidationResult:
        """
        Test credentials by making a test API call.

        Returns:
            CredentialValidationResult with test results
        """
        if not self.mcp_gateway:
            return CredentialValidationResult(
                valid=False,
                error="MCP Gateway not available",
                actionable_message="MCP Gateway is required to test credentials",
            )

        try:
            # Try to resolve a well-known library (this is a lightweight test)
            # Use backup client with automatic fallback (MCP Gateway -> HTTP)
            from .backup_client import call_context7_resolve_with_fallback
            
            result = await call_context7_resolve_with_fallback("react", self.mcp_gateway)

            if result.get("success"):
                return CredentialValidationResult(
                    valid=True,
                    credential_source="mcp",
                    actionable_message="Context7 credentials are valid and working",
                )
            else:
                error_msg = result.get("error", "Unknown error")
                return CredentialValidationResult(
                    valid=False,
                    error=error_msg,
                    actionable_message=(
                        f"Context7 API call failed: {error_msg}\n"
                        "Please check:\n"
                        "1. Your API key is correct\n"
                        "2. Your API key has not expired\n"
                        "3. Context7 service is available"
                    ),
                )
        except Exception as e:
            return CredentialValidationResult(
                valid=False,
                error=str(e),
                actionable_message=(
                    f"Failed to test Context7 credentials: {str(e)}\n"
                    "Please check:\n"
                    "1. MCP Gateway is properly configured\n"
                    "2. Context7 MCP server is running\n"
                    "3. Network connectivity is available"
                ),
            )

    def get_setup_instructions(self) -> str:
        """
        Get setup instructions for Context7 credentials.

        Returns:
            Setup instructions as a string
        """
        return """
Context7 Credential Setup Instructions
======================================

Option 1: Environment Variable (Recommended for local development)
------------------------------------------------------------------
export CONTEXT7_API_KEY='your-api-key-here'

Option 2: MCP Server Configuration (Recommended for production)
------------------------------------------------------------------
Configure Context7 MCP server in your MCP settings file.

For Cursor/VS Code:
1. Open MCP settings (usually in .cursor/mcp.json or similar)
2. Add Context7 server configuration:
   {
     "mcpServers": {
       "Context7": {
         "command": "npx",
         "args": ["-y", "@context7/mcp-server"],
         "env": {
           "CONTEXT7_API_KEY": "your-api-key-here"
         }
       }
     }
   }

Option 3: CI/CD Setup
---------------------
Add CONTEXT7_API_KEY to your CI/CD platform secrets:
- GitHub Actions: Repository Settings > Secrets
- GitLab CI: CI/CD Variables
- CircleCI: Project Settings > Environment Variables

Verification:
-------------
Run: python -c "from tapps_agents.context7 import CredentialValidator; import asyncio; asyncio.run(CredentialValidator().test_credentials())"
"""


def validate_context7_credentials(
    mcp_gateway: MCPGateway | None = None,
    raise_on_error: bool = False,
) -> CredentialValidationResult:
    """
    Convenience function to validate Context7 credentials.

    Args:
        mcp_gateway: Optional MCPGateway instance
        raise_on_error: Whether to raise exception on validation failure

    Returns:
        CredentialValidationResult

    Raises:
        RuntimeError: If raise_on_error=True and validation fails
    """
    validator = CredentialValidator(mcp_gateway=mcp_gateway)
    result = validator.validate_credentials()

    if raise_on_error and not result.valid:
        error_msg = result.actionable_message or result.error or "Credential validation failed"
        raise RuntimeError(error_msg)

    return result


async def test_context7_credentials(
    mcp_gateway: MCPGateway | None = None,
    raise_on_error: bool = False,
) -> CredentialValidationResult:
    """
    Convenience function to test Context7 credentials with API call.

    Args:
        mcp_gateway: Optional MCPGateway instance
        raise_on_error: Whether to raise exception on test failure

    Returns:
        CredentialValidationResult

    Raises:
        RuntimeError: If raise_on_error=True and test fails
    """
    validator = CredentialValidator(mcp_gateway=mcp_gateway)
    result = await validator.test_credentials()

    if raise_on_error and not result.valid:
        error_msg = result.actionable_message or result.error or "Credential test failed"
        raise RuntimeError(error_msg)

    return result
