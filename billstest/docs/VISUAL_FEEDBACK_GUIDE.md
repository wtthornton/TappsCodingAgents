# Visual Feedback Integration Guide

**Version:** 1.0  
**Date:** 2025-12-11  
**Status:** Phase 2.1-2.3 Complete

## Overview

The Visual Feedback Integration system provides multi-level visual feedback for iterative UI refinement. It enables the Designer Agent to generate UIs, capture visual feedback, analyze layout and accessibility, and iteratively improve designs based on feedback.

## Architecture

### Components

1. **VisualFeedbackCollector** - Collects visual feedback from generated UIs
2. **VisualAnalyzer** - Analyzes visual elements, layout, and accessibility
3. **UIComparator** - Compares UI iterations to identify improvements
4. **VisualPatternLearner** - Learns visual patterns from feedback
5. **BrowserController** - Controls headless browser for UI rendering
6. **VisualDesignerAgent** - Enhanced designer with visual feedback capabilities
7. **IterativeRefinement** - Manages iterative UI improvement loop

### Hardware-Aware Design

The system adapts to different hardware profiles:

- **NUC Devices** (≤6 cores, ≤16GB RAM)
  - Lightweight visual analysis
  - Cloud rendering fallback
  - Minimal image processing

- **Development Machines** (6-12 cores, 16-32GB RAM)
  - Standard visual analysis
  - Local browser rendering
  - Balanced processing

- **Workstation Machines** (>12 cores, >32GB RAM)
  - Full visual analysis
  - Detailed comparison
  - Complete image processing

## Usage

### Basic Visual Design

```python
from tapps_agents.agents.designer.visual_designer import VisualDesignerAgent

# Initialize agent
agent = VisualDesignerAgent()

# Activate agent
await agent.activate()

# Design UI with visual feedback
result = await agent.run(
    "*visual-design",
    feature_description="User login page",
    user_stories=[
        "As a user, I want to log in",
        "I want to see my profile after login"
    ],
    max_iterations=5,
    quality_threshold=0.8
)

print(f"Final quality: {result['final_quality']:.2f}")
print(f"Iterations: {result['iterations']}")
print(f"Improvement: {result['quality_improvement']:.2f}")
```

### Iterative Refinement

```python
from tapps_agents.agents.designer.visual_designer import (
    IterativeRefinement, RefinementConfig
)

# Configure refinement
config = RefinementConfig(
    max_iterations=5,
    quality_threshold=0.8,
    min_improvement=0.05,
    screenshot_dir="./screenshots",
    enable_accessibility_check=True,
    enable_layout_analysis=True
)

# Create refinement instance
refinement = IterativeRefinement(config=config)

# Define refinement callback
async def refine_callback(html, feedback, suggestions, requirements):
    """Refine HTML based on feedback."""
    # Use LLM or template engine to refine HTML
    # based on suggestions and feedback
    refined_html = apply_suggestions(html, suggestions)
    return refined_html

# Run refinement
initial_html = "<html><body><button>Click</button></body></html>"
requirements = {"feature_description": "Test feature"}

result = await refinement.refine_ui(
    initial_html,
    requirements,
    refinement_callback=refine_callback
)

# Get summary
summary = refinement.get_refinement_summary()
print(f"Quality improved from {summary['initial_quality']:.2f} to {summary['final_quality']:.2f}")
```

### Browser Controller

```python
from tapps_agents.core.browser_controller import (
    BrowserController, BrowserType, ScreenshotOptions
)

# Initialize browser controller
controller = BrowserController(
    browser_type=BrowserType.CHROMIUM,
    headless=True
)

# Start browser
controller.start()

# Load HTML
html_content = "<html><body><h1>Hello</h1></body></html>"
controller.load_html(html_content)

# Capture screenshot
options = ScreenshotOptions(
    full_page=True,
    quality=90
)
controller.capture_screenshot("screenshot.png", options=options)

# Simulate interactions
controller.click("#button")
controller.type_text("#input", "Hello World")
controller.scroll(0, 100)

# Get interaction history
history = controller.get_interaction_history()
for event in history:
    print(f"{event.event_type}: {event.selector}")

# Stop browser
controller.stop()
```

### Visual Analysis

```python
from tapps_agents.core.visual_feedback import (
    VisualFeedbackCollector, VisualAnalyzer, VisualElement, VisualElementType
)

# Initialize components
collector = VisualFeedbackCollector()
analyzer = VisualAnalyzer()

# Create visual elements
elements = [
    VisualElement(
        element_type=VisualElementType.BUTTON,
        position=(10.0, 20.0),
        size=(100.0, 40.0),
        text="Click Me"
    ),
    VisualElement(
        element_type=VisualElementType.INPUT,
        position=(10.0, 70.0),
        size=(200.0, 40.0)
    )
]

# Analyze layout
layout_metrics = analyzer.analyze_layout(elements)

print(f"Spacing consistency: {layout_metrics.spacing_consistency:.2f}")
print(f"Alignment score: {layout_metrics.alignment_score:.2f}")
print(f"Visual hierarchy: {layout_metrics.visual_hierarchy:.2f}")

# Analyze accessibility
accessibility_metrics = analyzer.analyze_accessibility(
    elements,
    html_content="<html><body><button aria-label='Submit'>Submit</button></body></html>"
)

print(f"Color contrast: {accessibility_metrics.color_contrast_score:.2f}")
print(f"Keyboard navigable: {accessibility_metrics.keyboard_navigable}")
print(f"ARIA labels: {accessibility_metrics.aria_labels_present}")

# Calculate quality score
quality_score = analyzer.calculate_quality_score(
    layout_metrics,
    accessibility_metrics
)

print(f"Overall quality: {quality_score:.2f}")
```

### Comparing Iterations

```python
from tapps_agents.core.visual_feedback import UIComparator

# Create comparator
comparator = UIComparator()

# Compare iterations
previous_feedback = collector.get_feedback_history()[0]
current_feedback = collector.get_feedback_history()[1]

comparison = comparator.compare_iterations(previous_feedback, current_feedback)

print("Improvements:")
for improvement in comparison["improvements"]:
    print(f"  - {improvement}")

print("Regressions:")
for regression in comparison["regressions"]:
    print(f"  - {regression}")

print(f"Quality delta: {comparison['quality_delta']:.2f}")

# Get improvement trend
feedback_history = collector.get_feedback_history()
trend = comparator.get_improvement_trend(feedback_history)

print(f"Trend: {trend['trend']}")
print(f"Average improvement: {trend['average_improvement']:.2f}")
```

## Quality Metrics

### Layout Metrics

- **Spacing Consistency** (0.0-1.0): Consistency of spacing between elements
- **Alignment Score** (0.0-1.0): How well elements are aligned
- **Visual Hierarchy** (0.0-1.0): Clear visual hierarchy based on size and position
- **Whitespace Balance** (0.0-1.0): Balance of whitespace in the layout
- **Grid Consistency** (0.0-1.0): Consistency with grid system

### Accessibility Metrics

- **Color Contrast Score** (0.0-1.0): Color contrast ratio compliance
- **Keyboard Navigable**: Whether UI is keyboard accessible
- **Screen Reader Compatible**: Whether UI works with screen readers
- **ARIA Labels Present**: Whether ARIA labels are used
- **Focus Indicators Present**: Whether focus indicators are visible

### Overall Quality Score

The overall quality score is calculated as:
```
Quality = (Layout Score × 0.6) + (Accessibility Score × 0.4)
```

Where:
- Layout Score = Average of all layout metrics
- Accessibility Score = Weighted average of accessibility metrics

## Iterative Refinement Process

1. **Generate Initial UI** - Create initial HTML based on requirements
2. **Render UI** - Load HTML in headless browser
3. **Capture Visual Feedback** - Take screenshot, extract elements
4. **Analyze Feedback** - Analyze layout and accessibility
5. **Compare with Previous** - Identify improvements and regressions
6. **Refine UI** - Apply suggestions to improve HTML
7. **Repeat** - Continue until quality threshold met or max iterations reached

## Configuration

### RefinementConfig

```python
config = RefinementConfig(
    max_iterations=5,              # Maximum refinement iterations
    quality_threshold=0.8,          # Stop when quality reaches this
    min_improvement=0.05,          # Minimum improvement to continue
    screenshot_dir="./screenshots", # Directory for screenshots
    enable_accessibility_check=True, # Enable accessibility analysis
    enable_layout_analysis=True     # Enable layout analysis
)
```

### Hardware Profiles

The system automatically detects hardware profile:
- `HardwareProfile.NUC` - Low resources
- `HardwareProfile.DEVELOPMENT` - Medium resources
- `HardwareProfile.WORKSTATION` - High resources

## Best Practices

1. **Start with Clear Requirements** - Provide detailed feature descriptions and user stories
2. **Set Appropriate Thresholds** - Quality threshold should match project requirements
3. **Monitor Iterations** - Review refinement summary to understand improvements
4. **Use Screenshots** - Enable screenshot capture to visually review iterations
5. **Check Accessibility Early** - Enable accessibility checks from the start
6. **Leverage Pattern Learning** - Use learned patterns to improve future designs

## Troubleshooting

### Browser Not Starting

If browser fails to start:
- Check if Playwright is installed: `pip install playwright`
- Install browser: `playwright install chromium`
- For NUC devices, cloud rendering fallback is used automatically

### Low Quality Scores

If quality scores are consistently low:
- Review layout metrics to identify specific issues
- Check accessibility metrics for missing features
- Adjust refinement callback to address specific issues
- Increase max_iterations to allow more refinement

### Performance Issues

If performance is slow:
- Use lightweight mode on NUC devices (automatic)
- Reduce max_iterations
- Disable full-page screenshots
- Use cloud rendering fallback

## API Reference

### VisualFeedbackCollector

- `collect_feedback(iteration, screenshot_path, visual_elements, user_interactions, metadata)` - Collect feedback
- `get_feedback_history(limit)` - Get feedback history
- `clear_history()` - Clear feedback history

### VisualAnalyzer

- `analyze_layout(visual_elements, design_spec)` - Analyze layout
- `analyze_accessibility(visual_elements, html_content)` - Analyze accessibility
- `calculate_quality_score(layout_metrics, accessibility_metrics, weights)` - Calculate quality

### UIComparator

- `compare_iterations(previous, current)` - Compare two iterations
- `get_improvement_trend(feedback_history)` - Analyze improvement trend

### BrowserController

- `start()` - Start browser
- `stop()` - Stop browser
- `navigate(url, wait_until, timeout)` - Navigate to URL
- `load_html(html_content, base_url)` - Load HTML content
- `capture_screenshot(output_path, options)` - Capture screenshot
- `click(selector, timeout)` - Click element
- `type_text(selector, text, timeout)` - Type text
- `scroll(x, y)` - Scroll page
- `hover(selector, timeout)` - Hover over element
- `press_key(key)` - Press key

### IterativeRefinement

- `refine_ui(initial_html, requirements, refinement_callback)` - Refine UI iteratively
- `get_refinement_summary()` - Get refinement summary
- `start_browser()` - Start browser controller
- `stop_browser()` - Stop browser controller

### VisualDesignerAgent

- `run("*visual-design", feature_description, user_stories, max_iterations, quality_threshold, output_file)` - Design UI with visual feedback

## Examples

See `examples/visual_feedback_example.py` for complete examples.

## Success Criteria

- ✅ UI generation improves by 20%+ after 3 iterations
- ✅ Visual analysis completes in <10 seconds on workstation
- ✅ NUC devices can use cloud rendering fallback
- ✅ Visual feedback system uses <100MB memory

## Future Enhancements

- Real DOM parsing for visual element extraction
- Advanced color contrast calculation
- Machine learning-based layout suggestions
- Integration with design systems
- Real-time visual feedback dashboard

