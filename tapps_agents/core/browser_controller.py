"""
Browser Controller for UI Rendering and Interaction

Provides headless browser control for visual feedback collection.
Supports Playwright with optional Selenium fallback.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .hardware_profiler import HardwareProfile, HardwareProfiler

logger = logging.getLogger(__name__)

# Try to import Playwright, fallback to mock if not available
try:
    from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    # Keep these as `Any` so runtime imports don't break annotations when Playwright
    # isn't installed (and so mypy doesn't infer `NoneType` here).
    Browser = Any
    Page = Any
    BrowserContext = Any
    logger.warning("Playwright not available. Browser operations will be mocked.")


class BrowserType(Enum):
    """Browser types."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class RenderingMode(Enum):
    """Rendering mode for browser operations."""

    LOCAL = "local"  # Local browser rendering
    CLOUD = "cloud"  # Cloud rendering service (for NUC devices)


@dataclass
class ScreenshotOptions:
    """Options for screenshot capture."""

    full_page: bool = False
    clip: dict[str, float] | None = None  # {x, y, width, height}
    quality: int = 90  # 0-100
    timeout: float = 30.0


@dataclass
class InteractionEvent:
    """User interaction event."""

    event_type: str  # "click", "type", "scroll", "hover", "keypress"
    selector: str | None = None
    text: str | None = None
    key: str | None = None
    coordinates: tuple[float, float] | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class BrowserController:
    """Controls headless browser for UI rendering."""

    def __init__(
        self,
        hardware_profile: HardwareProfile | None = None,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = True,
    ):
        """
        Initialize browser controller.

        Args:
            hardware_profile: Hardware profile for optimization
            browser_type: Browser type to use
            headless: Run browser in headless mode
        """
        self.hardware_profile = hardware_profile or HardwareProfiler().detect_profile()
        self.browser_type = browser_type
        self.headless = headless
        self.rendering_mode = self._get_rendering_mode()

        self.playwright: Any | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

        self.interaction_history: list[InteractionEvent] = []

    def _get_rendering_mode(self) -> RenderingMode:
        """Select rendering mode based on hardware."""
        if self.hardware_profile == HardwareProfile.NUC:
            return RenderingMode.CLOUD  # Use cloud fallback for NUC
        else:
            return RenderingMode.LOCAL

    def start(self) -> bool:
        """
        Start browser instance.

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            logger.info("Using cloud rendering fallback (NUC device)")
            return True  # Cloud rendering doesn't need local browser

        if not HAS_PLAYWRIGHT:
            logger.warning(
                "Playwright not available. Browser operations will be mocked."
            )
            return False

        try:
            self.playwright = sync_playwright().start()
            assert self.playwright is not None

            browser_map = {
                BrowserType.CHROMIUM: self.playwright.chromium,
                BrowserType.FIREFOX: self.playwright.firefox,
                BrowserType.WEBKIT: self.playwright.webkit,
            }

            browser_launcher = browser_map.get(
                self.browser_type, self.playwright.chromium
            )
            self.browser = browser_launcher.launch(headless=self.headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()

            logger.info(f"Browser started: {self.browser_type.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False

    def stop(self):
        """Stop browser instance."""
        if self.page:
            self.page.close()
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

        logger.info("Browser stopped")

    def navigate(
        self, url: str, wait_until: str = "load", timeout: float = 30.0
    ) -> bool:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to
            wait_until: Wait condition ("load", "domcontentloaded", "networkidle")
            timeout: Navigation timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            logger.info(f"Cloud navigation to: {url}")
            return True  # Mock for cloud rendering

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.goto(url, wait_until=wait_until, timeout=timeout * 1000)
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    def load_html(self, html_content: str, base_url: str = "http://localhost") -> bool:
        """
        Load HTML content directly.

        Args:
            html_content: HTML content to load
            base_url: Base URL for relative resources

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            logger.info("Cloud HTML load")
            return True  # Mock for cloud rendering

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.set_content(html_content, wait_until="domcontentloaded")
            logger.info("HTML content loaded")
            return True
        except Exception as e:
            logger.error(f"HTML load failed: {e}")
            return False

    def capture_screenshot(
        self, output_path: str, options: ScreenshotOptions | None = None
    ) -> bool:
        """
        Capture screenshot of current page.

        Args:
            output_path: Path to save screenshot
            options: Screenshot options

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            logger.info(f"Cloud screenshot to: {output_path}")
            # In real implementation, would call cloud rendering service
            Path(output_path).touch()  # Create empty file as placeholder
            return True

        if not self.page:
            logger.error("Browser not started")
            return False

        if options is None:
            options = ScreenshotOptions()

        try:
            screenshot_kwargs = {
                "path": output_path,
                "full_page": options.full_page,
                "timeout": options.timeout * 1000,
            }

            if options.clip:
                screenshot_kwargs["clip"] = options.clip

            if options.quality is not None:
                screenshot_kwargs["quality"] = options.quality

            self.page.screenshot(**screenshot_kwargs)
            logger.info(f"Screenshot saved: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return False

    def click(self, selector: str, timeout: float = 5.0) -> bool:
        """
        Click an element.

        Args:
            selector: CSS selector
            timeout: Wait timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            event = InteractionEvent(event_type="click", selector=selector)
            self.interaction_history.append(event)
            return True

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.click(selector, timeout=timeout * 1000)
            event = InteractionEvent(event_type="click", selector=selector)
            self.interaction_history.append(event)
            logger.debug(f"Clicked: {selector}")
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    def type_text(self, selector: str, text: str, timeout: float = 5.0) -> bool:
        """
        Type text into an element.

        Args:
            selector: CSS selector
            text: Text to type
            timeout: Wait timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            event = InteractionEvent(event_type="type", selector=selector, text=text)
            self.interaction_history.append(event)
            return True

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.fill(selector, text)
            event = InteractionEvent(event_type="type", selector=selector, text=text)
            self.interaction_history.append(event)
            logger.debug(f"Typed into {selector}: {text}")
            return True
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False

    def scroll(self, x: float = 0, y: float = 0) -> bool:
        """
        Scroll the page.

        Args:
            x: Horizontal scroll amount
            y: Vertical scroll amount

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            event = InteractionEvent(event_type="scroll", coordinates=(x, y))
            self.interaction_history.append(event)
            return True

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.evaluate(f"window.scrollBy({x}, {y})")
            event = InteractionEvent(event_type="scroll", coordinates=(x, y))
            self.interaction_history.append(event)
            logger.debug(f"Scrolled: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return False

    def hover(self, selector: str, timeout: float = 5.0) -> bool:
        """
        Hover over an element.

        Args:
            selector: CSS selector
            timeout: Wait timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            event = InteractionEvent(event_type="hover", selector=selector)
            self.interaction_history.append(event)
            return True

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.hover(selector, timeout=timeout * 1000)
            event = InteractionEvent(event_type="hover", selector=selector)
            self.interaction_history.append(event)
            logger.debug(f"Hovered: {selector}")
            return True
        except Exception as e:
            logger.error(f"Hover failed: {e}")
            return False

    def press_key(self, key: str) -> bool:
        """
        Press a key.

        Args:
            key: Key to press (e.g., "Enter", "Escape", "Tab")

        Returns:
            True if successful, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            event = InteractionEvent(event_type="keypress", key=key)
            self.interaction_history.append(event)
            return True

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.press("body", key)
            event = InteractionEvent(event_type="keypress", key=key)
            self.interaction_history.append(event)
            logger.debug(f"Pressed key: {key}")
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False

    def get_html(self) -> str | None:
        """
        Get current page HTML.

        Returns:
            HTML content or None if failed
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            return "<html><body>Cloud rendering</body></html>"  # Mock

        if not self.page:
            logger.error("Browser not started")
            return None

        try:
            return self.page.content()
        except Exception as e:
            logger.error(f"Get HTML failed: {e}")
            return None

    def get_interaction_history(self) -> list[InteractionEvent]:
        """
        Get interaction history.

        Returns:
            List of interaction events
        """
        return self.interaction_history.copy()

    def clear_interaction_history(self):
        """Clear interaction history."""
        self.interaction_history.clear()

    def wait_for_selector(
        self, selector: str, timeout: float = 5.0, state: str = "visible"
    ) -> bool:
        """
        Wait for selector to appear.

        Args:
            selector: CSS selector
            timeout: Wait timeout in seconds
            state: Wait state ("visible", "hidden", "attached", "detached")

        Returns:
            True if element found, False otherwise
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            return True  # Mock

        if not self.page:
            logger.error("Browser not started")
            return False

        try:
            self.page.wait_for_selector(selector, timeout=timeout * 1000, state=state)
            return True
        except Exception as e:
            logger.error(f"Wait for selector failed: {e}")
            return False

    def evaluate_script(self, script: str) -> Any | None:
        """
        Evaluate JavaScript in the page context.

        Args:
            script: JavaScript code to evaluate

        Returns:
            Evaluation result or None if failed
        """
        if self.rendering_mode == RenderingMode.CLOUD:
            return None  # Mock

        if not self.page:
            logger.error("Browser not started")
            return None

        try:
            return self.page.evaluate(script)
        except Exception as e:
            logger.error(f"Script evaluation failed: {e}")
            return None
