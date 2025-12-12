"""
Unit tests for Browser Controller (Phase 2.2).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from tapps_agents.core.browser_controller import (
    BrowserController, BrowserType, RenderingMode, ScreenshotOptions, InteractionEvent
)
from tapps_agents.core.hardware_profiler import HardwareProfile

pytestmark = pytest.mark.unit


class TestBrowserController:
    """Test BrowserController functionality."""
    
    def test_initialization_default(self):
        """Test controller initialization with default settings."""
        controller = BrowserController()
        assert controller.hardware_profile is not None
        assert controller.browser_type == BrowserType.CHROMIUM
        assert controller.headless is True
        assert len(controller.interaction_history) == 0
    
    def test_initialization_nuc_profile(self):
        """Test controller initialization with NUC profile (cloud rendering)."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        assert controller.hardware_profile == HardwareProfile.NUC
        assert controller.rendering_mode == RenderingMode.CLOUD
    
    def test_initialization_workstation_profile(self):
        """Test controller initialization with workstation profile (local rendering)."""
        controller = BrowserController(hardware_profile=HardwareProfile.WORKSTATION)
        assert controller.hardware_profile == HardwareProfile.WORKSTATION
        assert controller.rendering_mode == RenderingMode.LOCAL
    
    def test_initialization_custom_browser(self):
        """Test controller initialization with custom browser type."""
        controller = BrowserController(browser_type=BrowserType.FIREFOX)
        assert controller.browser_type == BrowserType.FIREFOX
    
    def test_start_cloud_rendering(self):
        """Test starting browser with cloud rendering (NUC)."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        result = controller.start()
        assert result is True  # Cloud rendering always succeeds
        assert controller.rendering_mode == RenderingMode.CLOUD
    
    @patch('tapps_agents.core.browser_controller.HAS_PLAYWRIGHT', False)
    def test_start_no_playwright(self):
        """Test starting browser without Playwright."""
        controller = BrowserController(hardware_profile=HardwareProfile.WORKSTATION)
        result = controller.start()
        assert result is False
    
    def test_stop_cloud_rendering(self):
        """Test stopping browser with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        controller.stop()  # Should not raise
    
    def test_navigate_cloud_rendering(self):
        """Test navigation with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.navigate("https://example.com")
        assert result is True
    
    def test_load_html_cloud_rendering(self):
        """Test loading HTML with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.load_html("<html><body>Test</body></html>")
        assert result is True
    
    def test_capture_screenshot_cloud_rendering(self):
        """Test screenshot capture with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = str(Path(tmpdir) / "screenshot.png")
            result = controller.capture_screenshot(screenshot_path)
            assert result is True
            assert Path(screenshot_path).exists()
    
    def test_capture_screenshot_with_options(self):
        """Test screenshot capture with options."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        
        options = ScreenshotOptions(
            full_page=True,
            quality=80,
            clip={"x": 0, "y": 0, "width": 100, "height": 100}
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = str(Path(tmpdir) / "screenshot.png")
            result = controller.capture_screenshot(screenshot_path, options=options)
            assert result is True
    
    def test_click_cloud_rendering(self):
        """Test click interaction with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.click("#button")
        assert result is True
        assert len(controller.interaction_history) == 1
        assert controller.interaction_history[0].event_type == "click"
        assert controller.interaction_history[0].selector == "#button"
    
    def test_type_text_cloud_rendering(self):
        """Test type text interaction with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.type_text("#input", "Hello World")
        assert result is True
        assert len(controller.interaction_history) == 1
        assert controller.interaction_history[0].event_type == "type"
        assert controller.interaction_history[0].text == "Hello World"
    
    def test_scroll_cloud_rendering(self):
        """Test scroll interaction with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.scroll(x=0, y=100)
        assert result is True
        assert len(controller.interaction_history) == 1
        assert controller.interaction_history[0].event_type == "scroll"
        assert controller.interaction_history[0].coordinates == (0, 100)
    
    def test_hover_cloud_rendering(self):
        """Test hover interaction with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.hover("#element")
        assert result is True
        assert len(controller.interaction_history) == 1
        assert controller.interaction_history[0].event_type == "hover"
    
    def test_press_key_cloud_rendering(self):
        """Test key press interaction with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.press_key("Enter")
        assert result is True
        assert len(controller.interaction_history) == 1
        assert controller.interaction_history[0].event_type == "keypress"
        assert controller.interaction_history[0].key == "Enter"
    
    def test_get_html_cloud_rendering(self):
        """Test getting HTML with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        html = controller.get_html()
        assert html is not None
        assert "Cloud rendering" in html
    
    def test_get_interaction_history(self):
        """Test getting interaction history."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        
        controller.click("#button1")
        controller.type_text("#input", "text")
        controller.scroll(0, 100)
        
        history = controller.get_interaction_history()
        assert len(history) == 3
        assert history[0].event_type == "click"
        assert history[1].event_type == "type"
        assert history[2].event_type == "scroll"
    
    def test_clear_interaction_history(self):
        """Test clearing interaction history."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        
        controller.click("#button")
        assert len(controller.interaction_history) == 1
        
        controller.clear_interaction_history()
        assert len(controller.interaction_history) == 0
    
    def test_wait_for_selector_cloud_rendering(self):
        """Test waiting for selector with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.wait_for_selector("#element")
        assert result is True
    
    def test_evaluate_script_cloud_rendering(self):
        """Test script evaluation with cloud rendering."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()
        result = controller.evaluate_script("return 42;")
        assert result is None  # Cloud rendering returns None


class TestScreenshotOptions:
    """Test ScreenshotOptions dataclass."""
    
    def test_default_options(self):
        """Test default screenshot options."""
        options = ScreenshotOptions()
        assert options.full_page is False
        assert options.clip is None
        assert options.quality == 90
        assert options.timeout == 30.0
    
    def test_custom_options(self):
        """Test custom screenshot options."""
        clip = {"x": 10, "y": 20, "width": 100, "height": 200}
        options = ScreenshotOptions(
            full_page=True,
            clip=clip,
            quality=80,
            timeout=60.0
        )
        assert options.full_page is True
        assert options.clip == clip
        assert options.quality == 80
        assert options.timeout == 60.0


class TestInteractionEvent:
    """Test InteractionEvent dataclass."""
    
    def test_click_event(self):
        """Test click interaction event."""
        event = InteractionEvent(
            event_type="click",
            selector="#button"
        )
        assert event.event_type == "click"
        assert event.selector == "#button"
        assert event.timestamp > 0
    
    def test_type_event(self):
        """Test type interaction event."""
        event = InteractionEvent(
            event_type="type",
            selector="#input",
            text="Hello"
        )
        assert event.event_type == "type"
        assert event.text == "Hello"
    
    def test_scroll_event(self):
        """Test scroll interaction event."""
        event = InteractionEvent(
            event_type="scroll",
            coordinates=(0, 100)
        )
        assert event.event_type == "scroll"
        assert event.coordinates == (0, 100)
    
    def test_keypress_event(self):
        """Test keypress interaction event."""
        event = InteractionEvent(
            event_type="keypress",
            key="Enter"
        )
        assert event.event_type == "keypress"
        assert event.key == "Enter"
    
    def test_event_metadata(self):
        """Test interaction event with metadata."""
        event = InteractionEvent(
            event_type="click",
            selector="#button",
            metadata={"test": True, "value": 42}
        )
        assert event.metadata["test"] is True
        assert event.metadata["value"] == 42

