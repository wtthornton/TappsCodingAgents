"""
Playwright MCP Controller for browser automation via MCP tools.

Provides a unified interface for browser automation that works both:
- In Cursor IDE: Uses Playwright MCP tools directly
- In CLI mode: Falls back to Python Playwright package

This controller enables direct use of Playwright MCP capabilities including:
- Navigation and page management
- Element interaction (click, type, fill forms)
- Screenshots and snapshots
- Network monitoring
- Console message capture
- Accessibility tree access
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Import network recorder and trace manager
try:
    from ...agents.tester.network_recorder import NetworkRecorder
    from ...agents.tester.trace_manager import TraceManager
except ImportError:
    NetworkRecorder = None
    TraceManager = None

# Try to import Playwright for fallback
try:
    from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    Browser = Any
    Page = Any
    BrowserContext = Any


class MCPToolMode(Enum):
    """MCP tool invocation mode."""

    DIRECT = "direct"  # Direct MCP function calls (Cursor IDE)
    GATEWAY = "gateway"  # Via MCP Gateway (framework)
    FALLBACK = "fallback"  # Python Playwright package fallback


@dataclass
class ElementRef:
    """Element reference for MCP tool calls."""

    element: str  # Human-readable description
    ref: str  # Exact element reference from snapshot


@dataclass
class AccessibilitySnapshot:
    """Accessibility snapshot data."""

    content: str  # Snapshot markdown content
    filename: str | None = None  # Optional saved filename


@dataclass
class PerformanceMetrics:
    """Performance metrics from page load."""

    lcp: float | None = None  # Largest Contentful Paint (seconds)
    fid: float | None = None  # First Input Delay (milliseconds)
    cls: float | None = None  # Cumulative Layout Shift
    fcp: float | None = None  # First Contentful Paint (seconds)
    load_time: float | None = None  # Total load time (seconds)
    dom_content_loaded: float | None = None  # DOMContentLoaded time (seconds)
    network_requests: int = 0  # Number of network requests
    failed_requests: int = 0  # Number of failed requests


class PlaywrightMCPController:
    """
    Controller for Playwright MCP browser automation.

    Provides a unified interface that works in both Cursor IDE (MCP tools)
    and CLI mode (Python Playwright fallback).
    """

    def __init__(
        self,
        mcp_tool_handler: Callable | None = None,
        use_fallback: bool = True,
        enable_network_recording: bool = False,
        enable_tracing: bool = False,
    ):
        """
        Initialize Playwright MCP controller.

        Args:
            mcp_tool_handler: Function to call MCP tools (for Cursor IDE)
            use_fallback: Whether to fall back to Python Playwright if MCP unavailable
            enable_network_recording: Enable network request recording
            enable_tracing: Enable trace file generation
        """
        self.mcp_tool_handler = mcp_tool_handler
        self.use_fallback = use_fallback
        self.mode = self._detect_mode()
        self.current_tab_index = 0
        self.tabs: dict[int, Any] = {}  # Track multiple tabs

        # Fallback Playwright instances
        self.playwright: Any | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

        # Network recording and tracing
        self.network_recorder: NetworkRecorder | None = None
        self.trace_manager: TraceManager | None = None
        if enable_network_recording and NetworkRecorder:
            self.network_recorder = NetworkRecorder()
        if enable_tracing and TraceManager:
            self.trace_manager = TraceManager()

        if self.mode == MCPToolMode.FALLBACK and self.use_fallback:
            self._init_fallback()

    def _detect_mode(self) -> MCPToolMode:
        """Detect available MCP tool mode."""
        if self.mcp_tool_handler is not None:
            return MCPToolMode.DIRECT
        elif self.use_fallback and HAS_PLAYWRIGHT:
            return MCPToolMode.FALLBACK
        else:
            raise RuntimeError(
                "No Playwright available. Install Python Playwright package "
                "or configure Playwright MCP in Cursor."
            )

    def _init_fallback(self):
        """Initialize Python Playwright fallback."""
        if not HAS_PLAYWRIGHT:
            return

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            logger.info("Initialized Playwright fallback (Python package)")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright fallback: {e}")
            raise

    def _call_mcp_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call MCP tool via handler.

        Args:
            tool_name: Name of MCP tool (e.g., 'browser_navigate')
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        if self.mcp_tool_handler is None:
            raise RuntimeError("MCP tool handler not available")

        # Map tool names to MCP function names
        mcp_function_name = f"mcp_Playwright_{tool_name}"
        return self.mcp_tool_handler(mcp_function_name, **kwargs)

    def navigate(self, url: str) -> bool:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to

        Returns:
            True if successful, False otherwise
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                self._call_mcp_tool("browser_navigate", url=url)
                logger.info(f"Navigated to: {url} (MCP)")
                return True
            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                return False
        else:
            # Fallback to Python Playwright
            if not self.page:
                logger.error("Browser not initialized")
                return False
            try:
                self.page.goto(url, wait_until="load", timeout=30000)
                logger.info(f"Navigated to: {url} (fallback)")
                return True
            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                return False

    def snapshot(self, filename: str | None = None) -> AccessibilitySnapshot | None:
        """
        Get accessibility snapshot of current page.

        Args:
            filename: Optional filename to save snapshot

        Returns:
            AccessibilitySnapshot or None if failed
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                kwargs = {}
                if filename:
                    kwargs["filename"] = filename

                result = self._call_mcp_tool("browser_snapshot", **kwargs)
                content = result if isinstance(result, str) else result.get("content", "")

                return AccessibilitySnapshot(content=content, filename=filename)
            except Exception as e:
                logger.error(f"Snapshot failed: {e}")
                return None
        else:
            # Fallback: Use page content as snapshot
            if not self.page:
                logger.error("Browser not initialized")
                return None
            try:
                content = self.page.content()
                # Convert HTML to markdown-like snapshot
                snapshot_content = f"# Page Snapshot\n\n```html\n{content}\n```"
                return AccessibilitySnapshot(content=snapshot_content, filename=filename)
            except Exception as e:
                logger.error(f"Snapshot failed: {e}")
                return None

    def click(self, element: str, ref: str, button: str = "left") -> bool:
        """
        Click an element.

        Args:
            element: Human-readable element description
            ref: Exact element reference from snapshot
            button: Mouse button ("left", "right", "middle")

        Returns:
            True if successful, False otherwise
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                self._call_mcp_tool(
                    "browser_click", element=element, ref=ref, button=button
                )
                logger.debug(f"Clicked: {element}")
                return True
            except Exception as e:
                logger.error(f"Click failed: {e}")
                return False
        else:
            # Fallback: Use CSS selector from ref or element
            if not self.page:
                logger.error("Browser not initialized")
                return False
            try:
                # Try to extract selector from ref, fallback to element description
                selector = ref if ref.startswith("#") or ref.startswith(".") else element
                self.page.click(selector, button=button, timeout=5000)
                logger.debug(f"Clicked: {element} (fallback)")
                return True
            except Exception as e:
                logger.error(f"Click failed: {e}")
                return False

    def type_text(self, element: str, ref: str, text: str, submit: bool = False) -> bool:
        """
        Type text into an element.

        Args:
            element: Human-readable element description
            ref: Exact element reference from snapshot
            text: Text to type
            submit: Whether to submit after typing (press Enter)

        Returns:
            True if successful, False otherwise
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                self._call_mcp_tool(
                    "browser_type",
                    element=element,
                    ref=ref,
                    text=text,
                    submit=submit,
                )
                logger.debug(f"Typed into {element}: {text}")
                return True
            except Exception as e:
                logger.error(f"Type failed: {e}")
                return False
        else:
            # Fallback
            if not self.page:
                logger.error("Browser not initialized")
                return False
            try:
                selector = ref if ref.startswith("#") or ref.startswith(".") else element
                self.page.fill(selector, text)
                if submit:
                    self.page.press(selector, "Enter")
                logger.debug(f"Typed into {element}: {text} (fallback)")
                return True
            except Exception as e:
                logger.error(f"Type failed: {e}")
                return False

    def fill_form(self, fields: list[dict[str, Any]]) -> bool:
        """
        Fill multiple form fields at once.

        Args:
            fields: List of field dictionaries with 'name', 'type', 'ref', 'value'

        Returns:
            True if successful, False otherwise
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                # Convert fields to MCP format
                mcp_fields = []
                for field in fields:
                    mcp_fields.append(
                        {
                            "name": field.get("name", ""),
                            "type": field.get("type", "textbox"),
                            "ref": field.get("ref", ""),
                            "value": field.get("value", ""),
                        }
                    )
                self._call_mcp_tool("browser_fill_form", fields=mcp_fields)
                logger.debug(f"Filled form with {len(fields)} fields")
                return True
            except Exception as e:
                logger.error(f"Fill form failed: {e}")
                return False
        else:
            # Fallback: Fill fields one by one
            if not self.page:
                logger.error("Browser not initialized")
                return False
            try:
                for field in fields:
                    selector = field.get("ref") or field.get("name", "")
                    value = field.get("value", "")
                    field_type = field.get("type", "textbox")

                    if field_type == "checkbox":
                        if value:
                            self.page.check(selector)
                        else:
                            self.page.uncheck(selector)
                    elif field_type == "combobox":
                        self.page.select_option(selector, value)
                    else:
                        self.page.fill(selector, value)

                logger.debug(f"Filled form with {len(fields)} fields (fallback)")
                return True
            except Exception as e:
                logger.error(f"Fill form failed: {e}")
                return False

    def take_screenshot(
        self,
        filename: str | None = None,
        full_page: bool = False,
        element: str | None = None,
        ref: str | None = None,
    ) -> str | None:
        """
        Take a screenshot.

        Args:
            filename: Output filename
            full_page: Whether to capture full page
            element: Optional element description for element screenshot
            ref: Optional element reference for element screenshot

        Returns:
            Filename if successful, None otherwise
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                kwargs = {}
                if filename:
                    kwargs["filename"] = filename
                if full_page:
                    kwargs["fullPage"] = True
                if element and ref:
                    kwargs["element"] = element
                    kwargs["ref"] = ref

                result = self._call_mcp_tool("browser_take_screenshot", **kwargs)
                saved_filename = filename or result.get("filename", "screenshot.png")
                logger.info(f"Screenshot saved: {saved_filename}")
                return saved_filename
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                return None
        else:
            # Fallback
            if not self.page:
                logger.error("Browser not initialized")
                return None
            try:
                if not filename:
                    filename = "screenshot.png"

                screenshot_kwargs = {"path": filename, "full_page": full_page}
                if element and ref:
                    selector = ref if ref.startswith("#") or ref.startswith(".") else element
                    screenshot_kwargs["selector"] = selector

                self.page.screenshot(**screenshot_kwargs)
                logger.info(f"Screenshot saved: {filename} (fallback)")
                return filename
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                return None

    def get_console_messages(self, level: str = "info") -> list[dict[str, Any]]:
        """
        Get console messages from the page.

        Args:
            level: Message level ("error", "warning", "info", "debug")

        Returns:
            List of console messages
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                result = self._call_mcp_tool("browser_console_messages", level=level)
                return result if isinstance(result, list) else result.get("messages", [])
            except Exception as e:
                logger.error(f"Get console messages failed: {e}")
                return []
        else:
            # Fallback: Not easily available in Python Playwright
            logger.warning("Console messages not available in fallback mode")
            return []

    def get_network_requests(
        self, include_static: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get network requests from the page.

        Args:
            include_static: Whether to include static resources (images, fonts, etc.)

        Returns:
            List of network requests
        """
        requests = []
        if self.mode == MCPToolMode.DIRECT:
            try:
                result = self._call_mcp_tool(
                    "browser_network_requests", includeStatic=include_static
                )
                requests = result if isinstance(result, list) else result.get("requests", [])
            except Exception as e:
                logger.error(f"Get network requests failed: {e}")
                return []
        else:
            # Fallback: Not easily available in Python Playwright
            logger.warning("Network requests not available in fallback mode")
            return []

        # Record requests if recording is enabled
        if self.network_recorder and requests:
            for req in requests:
                self.network_recorder.record_request(
                    url=req.get("url", ""),
                    method=req.get("method", "GET"),
                    headers=req.get("headers", {}),
                    response_status=req.get("status"),
                    response_headers=req.get("responseHeaders", {}),
                    response_body=req.get("body"),
                    request_id=req.get("id"),
                )

        return requests

    def wait_for(
        self, text: str | None = None, text_gone: str | None = None, time: float | None = None
    ) -> bool:
        """
        Wait for text to appear/disappear or time to pass.

        Args:
            text: Text to wait for
            text_gone: Text to wait for to disappear
            time: Time to wait in seconds

        Returns:
            True if condition met, False otherwise
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                kwargs = {}
                if text:
                    kwargs["text"] = text
                if text_gone:
                    kwargs["textGone"] = text_gone
                if time:
                    kwargs["time"] = time

                self._call_mcp_tool("browser_wait_for", **kwargs)
                return True
            except Exception as e:
                logger.error(f"Wait failed: {e}")
                return False
        else:
            # Fallback
            if not self.page:
                logger.error("Browser not initialized")
                return False
            try:
                if text:
                    self.page.wait_for_selector(f"text={text}", timeout=5000)
                elif text_gone:
                    self.page.wait_for_selector(f"text={text_gone}", state="hidden", timeout=5000)
                elif time:
                    import time as time_module
                    time_module.sleep(time)

                return True
            except Exception as e:
                logger.error(f"Wait failed: {e}")
                return False

    def evaluate(self, function: str, element: str | None = None, ref: str | None = None) -> Any:
        """
        Evaluate JavaScript expression on page or element.

        Args:
            function: JavaScript function as string (e.g., "() => { return document.title; }")
            element: Optional element description
            ref: Optional element reference

        Returns:
            Evaluation result
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                kwargs = {"function": function}
                if element:
                    kwargs["element"] = element
                if ref:
                    kwargs["ref"] = ref

                result = self._call_mcp_tool("browser_evaluate", **kwargs)
                return result
            except Exception as e:
                logger.error(f"Evaluate failed: {e}")
                return None
        else:
            # Fallback
            if not self.page:
                logger.error("Browser not initialized")
                return None
            try:
                if element and ref:
                    selector = ref if ref.startswith("#") or ref.startswith(".") else element
                    return self.page.evaluate(function, self.page.query_selector(selector))
                else:
                    return self.page.evaluate(function)
            except Exception as e:
                logger.error(f"Evaluate failed: {e}")
                return None

    def start_network_recording(self, session_id: str | None = None, description: str | None = None) -> str:
        """
        Start network request recording.

        Args:
            session_id: Optional session ID
            description: Optional description

        Returns:
            Session ID
        """
        if self.network_recorder:
            return self.network_recorder.start_recording(session_id, description)
        else:
            logger.warning("Network recording not enabled")
            return ""

    def stop_network_recording(self):
        """Stop network recording and save."""
        if self.network_recorder:
            return self.network_recorder.stop_recording()
        return None

    def start_tracing(self, test_name: str | None = None) -> Path | None:
        """
        Start trace recording.

        Args:
            test_name: Optional test name

        Returns:
            Trace file path
        """
        if self.trace_manager and self.context:
            return self.trace_manager.start_tracing(self.context, test_name)
        elif self.trace_manager:
            # MCP mode - tracing will be handled by MCP
            return self.trace_manager.start_tracing(None, test_name)
        return None

    def stop_tracing(self) -> Path | None:
        """Stop tracing and save trace file."""
        if self.trace_manager:
            return self.trace_manager.stop_tracing(self.context)
        return None

    def create_tab(self) -> int:
        """
        Create a new browser tab.

        Returns:
            Tab index
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                result = self._call_mcp_tool("browser_tabs", action="new")
                tab_index = result.get("index", len(self.tabs))
                self.tabs[tab_index] = result
                logger.info(f"Created tab: {tab_index}")
                return tab_index
            except Exception as e:
                logger.error(f"Create tab failed: {e}")
                return -1
        else:
            # Fallback: Create new page in context
            if self.context:
                new_page = self.context.new_page()
                tab_index = len(self.tabs)
                self.tabs[tab_index] = new_page
                logger.info(f"Created tab: {tab_index} (fallback)")
                return tab_index
            return -1

    def switch_tab(self, tab_index: int) -> bool:
        """
        Switch to a different tab.

        Args:
            tab_index: Tab index to switch to

        Returns:
            True if successful
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                self._call_mcp_tool("browser_tabs", action="select", index=tab_index)
                self.current_tab_index = tab_index
                logger.info(f"Switched to tab: {tab_index}")
                return True
            except Exception as e:
                logger.error(f"Switch tab failed: {e}")
                return False
        else:
            # Fallback: Switch page reference
            if tab_index in self.tabs:
                self.page = self.tabs[tab_index]
                self.current_tab_index = tab_index
                logger.info(f"Switched to tab: {tab_index} (fallback)")
                return True
            return False

    def close_tab(self, tab_index: int | None = None) -> bool:
        """
        Close a browser tab.

        Args:
            tab_index: Tab index to close (None = current tab)

        Returns:
            True if successful
        """
        if tab_index is None:
            tab_index = self.current_tab_index

        if self.mode == MCPToolMode.DIRECT:
            try:
                self._call_mcp_tool("browser_tabs", action="close", index=tab_index)
                self.tabs.pop(tab_index, None)
                logger.info(f"Closed tab: {tab_index}")
                return True
            except Exception as e:
                logger.error(f"Close tab failed: {e}")
                return False
        else:
            # Fallback: Close page
            if tab_index in self.tabs:
                page = self.tabs.pop(tab_index)
                if hasattr(page, "close"):
                    page.close()
                logger.info(f"Closed tab: {tab_index} (fallback)")
                return True
            return False

    def list_tabs(self) -> list[dict[str, Any]]:
        """
        List all open tabs.

        Returns:
            List of tab information dictionaries
        """
        if self.mode == MCPToolMode.DIRECT:
            try:
                result = self._call_mcp_tool("browser_tabs", action="list")
                tabs = result if isinstance(result, list) else result.get("tabs", [])
                return tabs
            except Exception as e:
                logger.error(f"List tabs failed: {e}")
                return []
        else:
            # Fallback: Return tab indices
            return [{"index": idx, "url": "unknown"} for idx in self.tabs.keys()]

    def close(self):
        """Close browser and cleanup."""
        # Stop recording and tracing
        if self.network_recorder:
            self.stop_network_recording()
        if self.trace_manager:
            self.stop_tracing()

        # Close all tabs
        for tab_index in list(self.tabs.keys()):
            self.close_tab(tab_index)

        if self.mode == MCPToolMode.FALLBACK:
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
            logger.info("Browser closed (fallback)")
        else:
            # MCP mode: Browser is managed by MCP server
            logger.info("Browser cleanup (MCP managed)")
