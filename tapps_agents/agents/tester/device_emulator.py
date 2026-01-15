"""
Device Emulator for Playwright - Mobile and tablet device emulation.

Provides device profiles and emulation for testing responsive designs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DeviceCategory(Enum):
    """Device category."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


@dataclass
class DeviceProfile:
    """Device profile for emulation."""

    name: str
    category: DeviceCategory
    viewport_width: int
    viewport_height: int
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False
    user_agent: str = ""
    description: str = ""


class DeviceEmulator:
    """
    Device emulation for Playwright tests.

    Provides pre-configured device profiles and emulation setup.
    """

    # Pre-configured device profiles
    DEVICE_PROFILES: dict[str, DeviceProfile] = {
        # Mobile devices
        "iPhone 14": DeviceProfile(
            name="iPhone 14",
            category=DeviceCategory.MOBILE,
            viewport_width=390,
            viewport_height=844,
            device_scale_factor=3.0,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
            ),
            description="iPhone 14 (390x844)",
        ),
        "iPhone SE": DeviceProfile(
            name="iPhone SE",
            category=DeviceCategory.MOBILE,
            viewport_width=375,
            viewport_height=667,
            device_scale_factor=2.0,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            ),
            description="iPhone SE (375x667)",
        ),
        "Samsung Galaxy S21": DeviceProfile(
            name="Samsung Galaxy S21",
            category=DeviceCategory.MOBILE,
            viewport_width=360,
            viewport_height=800,
            device_scale_factor=3.0,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (Linux; Android 11; SM-G991B) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
            ),
            description="Samsung Galaxy S21 (360x800)",
        ),
        # Tablet devices
        "iPad Pro": DeviceProfile(
            name="iPad Pro",
            category=DeviceCategory.TABLET,
            viewport_width=1024,
            viewport_height=1366,
            device_scale_factor=2.0,
            is_mobile=False,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            ),
            description="iPad Pro (1024x1366)",
        ),
        "iPad Air": DeviceProfile(
            name="iPad Air",
            category=DeviceCategory.TABLET,
            viewport_width=820,
            viewport_height=1180,
            device_scale_factor=2.0,
            is_mobile=False,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            ),
            description="iPad Air (820x1180)",
        ),
        # Desktop devices
        "Desktop 1920x1080": DeviceProfile(
            name="Desktop 1920x1080",
            category=DeviceCategory.DESKTOP,
            viewport_width=1920,
            viewport_height=1080,
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            description="Desktop 1920x1080",
        ),
        "Desktop 1366x768": DeviceProfile(
            name="Desktop 1366x768",
            category=DeviceCategory.DESKTOP,
            viewport_width=1366,
            viewport_height=768,
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            description="Desktop 1366x768",
        ),
    }

    def __init__(self):
        """Initialize device emulator."""
        self.current_device: DeviceProfile | None = None

    def get_device(self, device_name: str) -> DeviceProfile | None:
        """
        Get device profile by name.

        Args:
            device_name: Name of device profile

        Returns:
            DeviceProfile or None if not found
        """
        return self.DEVICE_PROFILES.get(device_name)

    def list_devices(
        self, category: DeviceCategory | None = None
    ) -> list[DeviceProfile]:
        """
        List available device profiles.

        Args:
            category: Optional category filter

        Returns:
            List of DeviceProfile objects
        """
        devices = list(self.DEVICE_PROFILES.values())
        if category:
            devices = [d for d in devices if d.category == category]
        return devices

    def create_playwright_context_options(
        self, device_name: str
    ) -> dict[str, Any]:
        """
        Create Playwright context options for device emulation.

        Args:
            device_name: Name of device profile

        Returns:
            Dictionary of context options
        """
        device = self.get_device(device_name)
        if not device:
            raise ValueError(f"Device not found: {device_name}")

        options = {
            "viewport": {
                "width": device.viewport_width,
                "height": device.viewport_height,
            },
            "device_scale_factor": device.device_scale_factor,
            "is_mobile": device.is_mobile,
            "has_touch": device.has_touch,
        }

        if device.user_agent:
            options["user_agent"] = device.user_agent

        return options

    def create_mcp_emulation_code(self, device_name: str) -> str:
        """
        Create JavaScript code for MCP device emulation.

        Args:
            device_name: Name of device profile

        Returns:
            JavaScript code for device emulation
        """
        device = self.get_device(device_name)
        if not device:
            raise ValueError(f"Device not found: {device_name}")

        code = f"""
// Emulate {device.name}
await page.setViewportSize({{ width: {device.viewport_width}, height: {device.viewport_height} }});
await page.emulate({{ 
    viewport: {{ width: {device.viewport_width}, height: {device.viewport_height} }},
    deviceScaleFactor: {device.device_scale_factor},
    isMobile: {device.is_mobile},
    hasTouch: {device.has_touch},
    userAgent: "{device.user_agent}"
}});
"""
        return code.strip()
