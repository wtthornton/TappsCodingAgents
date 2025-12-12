"""
Visual Feedback Integration Examples

Demonstrates usage of the Visual Feedback system for iterative UI refinement.
"""

import asyncio
from datetime import UTC


# Example 1: Basic Visual Design
async def example_basic_visual_design():
    """Example: Basic visual design with feedback."""
    print("=" * 60)
    print("Example 1: Basic Visual Design")
    print("=" * 60)

    from tapps_agents.agents.designer.visual_designer import VisualDesignerAgent

    # Initialize agent
    agent = VisualDesignerAgent()
    await agent.activate()

    # Design UI with visual feedback
    result = await agent.run(
        "*visual-design",
        feature_description="User login page with email and password fields",
        user_stories=[
            "As a user, I want to log in with my email and password",
            "I want to see error messages if login fails",
            "I want to be redirected to my dashboard after successful login",
        ],
        max_iterations=3,
        quality_threshold=0.75,
        output_file="output/login_page.html",
    )

    print("\nDesign Results:")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Initial Quality: {result['initial_quality']:.2f}")
    print(f"  Final Quality: {result['final_quality']:.2f}")
    print(f"  Quality Improvement: {result['quality_improvement']:.2f}")
    print(f"  Improvement Trend: {result['improvement_trend']}")
    print("\nRecommendations:")
    for rec in result["recommendations"]:
        print(f"  - {rec}")

    print(f"\nOutput saved to: {result['output_file']}")


# Example 2: Iterative Refinement
async def example_iterative_refinement():
    """Example: Manual iterative refinement process."""
    print("\n" + "=" * 60)
    print("Example 2: Iterative Refinement")
    print("=" * 60)

    from tapps_agents.agents.designer.visual_designer import (
        IterativeRefinement,
        RefinementConfig,
    )

    # Configure refinement
    config = RefinementConfig(
        max_iterations=5,
        quality_threshold=0.8,
        min_improvement=0.05,
        screenshot_dir="./screenshots",
        enable_accessibility_check=True,
        enable_layout_analysis=True,
    )

    # Create refinement instance
    refinement = IterativeRefinement(config=config)

    # Initial HTML
    initial_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Product Card</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .card { border: 1px solid #ccc; padding: 20px; margin: 10px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Product Name</h2>
            <p>Product description goes here.</p>
            <button>Add to Cart</button>
        </div>
    </body>
    </html>
    """

    # Define refinement callback
    async def refine_callback(html, feedback, suggestions, requirements):
        """Refine HTML based on feedback."""
        print(f"\n  Refining based on {len(suggestions)} suggestions:")
        for suggestion in suggestions:
            print(f"    - {suggestion}")

        # In a real implementation, would use LLM or template engine
        # For this example, we'll just return improved HTML
        improved_html = html.replace(
            "<button>Add to Cart</button>",
            '<button aria-label="Add product to cart">Add to Cart</button>',
        )

        # Add focus styles if suggested
        if "focus indicators" in str(suggestions).lower():
            improved_html = improved_html.replace(
                "button { padding: 10px 20px; background: #007bff; color: white; border: none; }",
                "button { padding: 10px 20px; background: #007bff; color: white; border: none; } button:focus { outline: 2px solid #0056b3; }",
            )

        return improved_html

    # Run refinement
    requirements = {
        "feature_description": "Product card component",
        "user_stories": ["As a user, I want to add products to cart"],
    }

    print("\nStarting refinement process...")
    await refinement.refine_ui(
        initial_html, requirements, refinement_callback=refine_callback
    )

    # Get summary
    summary = refinement.get_refinement_summary()

    print("\nRefinement Summary:")
    print(f"  Iterations: {summary['iterations']}")
    print(f"  Initial Quality: {summary['initial_quality']:.2f}")
    print(f"  Final Quality: {summary['final_quality']:.2f}")
    print(f"  Quality Improvement: {summary['quality_improvement']:.2f}")
    print(f"  Improvement Trend: {summary['improvement_trend']}")
    print(f"  Average Improvement: {summary['average_improvement']:.2f}")

    # Clean up
    refinement.stop_browser()


# Example 3: Browser Controller
async def example_browser_controller():
    """Example: Using browser controller for UI testing."""
    print("\n" + "=" * 60)
    print("Example 3: Browser Controller")
    print("=" * 60)

    from tapps_agents.core.browser_controller import (
        BrowserController,
        BrowserType,
        ScreenshotOptions,
    )

    # Initialize browser controller
    controller = BrowserController(browser_type=BrowserType.CHROMIUM, headless=True)

    # Start browser
    if not controller.start():
        print("Failed to start browser (Playwright may not be installed)")
        print("This is expected in environments without Playwright")
        return

    try:
        # Load HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                button { padding: 10px 20px; margin: 10px; }
                input { padding: 8px; margin: 10px; width: 200px; }
            </style>
        </head>
        <body>
            <h1>Test Page</h1>
            <button id="btn1">Button 1</button>
            <button id="btn2">Button 2</button>
            <input id="input1" type="text" placeholder="Enter text">
        </body>
        </html>
        """

        controller.load_html(html_content)
        print("\n✓ HTML loaded")

        # Capture screenshot
        screenshot_path = "screenshot_example.png"
        options = ScreenshotOptions(full_page=True, quality=90)
        if controller.capture_screenshot(screenshot_path, options):
            print(f"✓ Screenshot saved: {screenshot_path}")

        # Simulate interactions
        controller.click("#btn1")
        print("✓ Clicked button 1")

        controller.type_text("#input1", "Hello World")
        print("✓ Typed text into input")

        controller.scroll(0, 100)
        print("✓ Scrolled page")

        # Get interaction history
        history = controller.get_interaction_history()
        print(f"\nInteraction History ({len(history)} events):")
        for i, event in enumerate(history, 1):
            print(
                f"  {i}. {event.event_type}: {event.selector or event.key or 'scroll'}"
            )

        # Get HTML
        current_html = controller.get_html()
        if current_html:
            print(f"\n✓ Retrieved HTML ({len(current_html)} characters)")

    finally:
        # Stop browser
        controller.stop()
        print("\n✓ Browser stopped")


# Example 4: Visual Analysis
async def example_visual_analysis():
    """Example: Visual analysis of UI elements."""
    print("\n" + "=" * 60)
    print("Example 4: Visual Analysis")
    print("=" * 60)

    from tapps_agents.core.visual_feedback import (
        VisualAnalyzer,
        VisualElement,
        VisualElementType,
        VisualFeedbackCollector,
    )

    # Initialize components
    collector = VisualFeedbackCollector()
    analyzer = VisualAnalyzer()

    # Create visual elements
    elements = [
        VisualElement(
            element_type=VisualElementType.HEADER,
            position=(0.0, 0.0),
            size=(800.0, 60.0),
            text="Header",
        ),
        VisualElement(
            element_type=VisualElementType.BUTTON,
            position=(10.0, 80.0),
            size=(120.0, 40.0),
            text="Primary Button",
        ),
        VisualElement(
            element_type=VisualElementType.BUTTON,
            position=(140.0, 80.0),
            size=(120.0, 40.0),
            text="Secondary Button",
        ),
        VisualElement(
            element_type=VisualElementType.INPUT,
            position=(10.0, 140.0),
            size=(300.0, 40.0),
            text="Email",
        ),
        VisualElement(
            element_type=VisualElementType.TEXT,
            position=(10.0, 200.0),
            size=(500.0, 30.0),
            text="Description text",
        ),
    ]

    # Analyze layout
    layout_metrics = analyzer.analyze_layout(elements)

    print("\nLayout Metrics:")
    print(f"  Spacing Consistency: {layout_metrics.spacing_consistency:.2f}")
    print(f"  Alignment Score: {layout_metrics.alignment_score:.2f}")
    print(f"  Visual Hierarchy: {layout_metrics.visual_hierarchy:.2f}")
    print(f"  Whitespace Balance: {layout_metrics.whitespace_balance:.2f}")
    print(f"  Grid Consistency: {layout_metrics.grid_consistency:.2f}")

    if layout_metrics.issues:
        print(f"\n  Issues ({len(layout_metrics.issues)}):")
        for issue in layout_metrics.issues[:3]:  # Show first 3
            print(f"    - {issue}")

    # Analyze accessibility
    html_with_aria = """
    <html>
    <body>
        <header>Header</header>
        <button aria-label="Primary action">Primary Button</button>
        <button aria-label="Secondary action">Secondary Button</button>
        <input type="email" aria-label="Email address" placeholder="Email">
        <p>Description text</p>
    </body>
    </html>
    """

    accessibility_metrics = analyzer.analyze_accessibility(
        elements, html_content=html_with_aria
    )

    print("\nAccessibility Metrics:")
    print(f"  Color Contrast Score: {accessibility_metrics.color_contrast_score:.2f}")
    print(f"  Keyboard Navigable: {accessibility_metrics.keyboard_navigable}")
    print(
        f"  Screen Reader Compatible: {accessibility_metrics.screen_reader_compatible}"
    )
    print(f"  ARIA Labels Present: {accessibility_metrics.aria_labels_present}")
    print(
        f"  Focus Indicators Present: {accessibility_metrics.focus_indicators_present}"
    )

    if accessibility_metrics.issues:
        print(f"\n  Issues ({len(accessibility_metrics.issues)}):")
        for issue in accessibility_metrics.issues:
            print(f"    - {issue}")

    # Calculate quality score
    quality_score = analyzer.calculate_quality_score(
        layout_metrics, accessibility_metrics
    )

    print(f"\nOverall Quality Score: {quality_score:.2f}")

    # Collect feedback
    feedback = collector.collect_feedback(
        iteration=1, visual_elements=elements, metadata={"test": True}
    )
    feedback.layout_metrics = layout_metrics
    feedback.accessibility_metrics = accessibility_metrics
    feedback.quality_score = quality_score

    print(f"\n✓ Feedback collected (iteration {feedback.iteration})")


# Example 5: Comparing Iterations
async def example_comparing_iterations():
    """Example: Comparing UI iterations."""
    print("\n" + "=" * 60)
    print("Example 5: Comparing Iterations")
    print("=" * 60)

    from datetime import datetime

    from tapps_agents.core.visual_feedback import (
        AccessibilityMetrics,
        LayoutMetrics,
        UIComparator,
        VisualFeedback,
        VisualFeedbackCollector,
    )

    # Initialize components
    collector = VisualFeedbackCollector()
    comparator = UIComparator()

    # Create feedback for iteration 1
    feedback1 = VisualFeedback(
        timestamp=datetime.now(UTC),
        iteration=1,
        quality_score=0.6,
        layout_metrics=LayoutMetrics(
            spacing_consistency=0.5,
            alignment_score=0.5,
            visual_hierarchy=0.6,
            whitespace_balance=0.5,
            grid_consistency=0.5,
        ),
        accessibility_metrics=AccessibilityMetrics(
            color_contrast_score=0.6,
            keyboard_navigable=False,
            screen_reader_compatible=False,
            aria_labels_present=False,
            focus_indicators_present=False,
        ),
    )
    collector.collect_feedback(iteration=1, visual_elements=[], metadata={})
    collector.feedback_history[-1] = feedback1

    # Create feedback for iteration 2 (improved)
    feedback2 = VisualFeedback(
        timestamp=datetime.now(UTC),
        iteration=2,
        quality_score=0.8,
        layout_metrics=LayoutMetrics(
            spacing_consistency=0.8,
            alignment_score=0.8,
            visual_hierarchy=0.8,
            whitespace_balance=0.7,
            grid_consistency=0.8,
        ),
        accessibility_metrics=AccessibilityMetrics(
            color_contrast_score=0.9,
            keyboard_navigable=True,
            screen_reader_compatible=True,
            aria_labels_present=True,
            focus_indicators_present=True,
        ),
    )
    collector.collect_feedback(iteration=2, visual_elements=[], metadata={})
    collector.feedback_history[-1] = feedback2

    # Compare iterations
    comparison = comparator.compare_iterations(feedback1, feedback2)

    print("\nComparison Results:")
    print(f"  Quality Delta: {comparison['quality_delta']:+.2f}")
    print(f"  Iteration Delta: {comparison['iteration_delta']}")

    print(f"\n  Improvements ({len(comparison['improvements'])}):")
    for improvement in comparison["improvements"]:
        print(f"    ✓ {improvement}")

    if comparison["regressions"]:
        print(f"\n  Regressions ({len(comparison['regressions'])}):")
        for regression in comparison["regressions"]:
            print(f"    ✗ {regression}")

    # Get improvement trend
    feedback_history = collector.get_feedback_history()
    trend = comparator.get_improvement_trend(feedback_history)

    print("\nImprovement Trend:")
    print(f"  Trend: {trend['trend']}")
    print(f"  Average Improvement: {trend['average_improvement']:+.2f}")
    print(f"  Final Quality: {trend['final_quality']:.2f}")


# Main execution
async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Visual Feedback Integration Examples")
    print("=" * 60)

    try:
        # Run examples
        await example_visual_analysis()
        await example_comparing_iterations()
        await example_browser_controller()
        await example_iterative_refinement()
        # Note: example_basic_visual_design requires full agent setup
        # Uncomment if you have full environment configured
        # await example_basic_visual_design()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
