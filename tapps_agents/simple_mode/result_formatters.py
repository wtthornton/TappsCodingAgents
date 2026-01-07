"""
Step Result Formatters for Simple Mode Workflows.

Decorator-based formatter registry with Protocol typing for extensible
result formatting. Converts raw agent outputs to readable markdown.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol

from .step_results import (
    ArchitectStepResult,
    BaseStepResult,
    DesignerStepResult,
    EnhancerStepResult,
    ImplementerStepResult,
    PlannerStepResult,
    ReviewerStepResult,
    StepStatus,
    QAStepResult,
    VerificationStepResult,
)


# Protocol for formatter functions (Python 3.8+ structural subtyping)
class ResultFormatter(Protocol):
    """Protocol for result formatter functions."""

    def __call__(self, result: BaseStepResult) -> str:
        ...


class FormatterRegistry:
    """Registry for step result formatters using decorator pattern."""

    _formatters: dict[str, ResultFormatter] = {}

    @classmethod
    def register(
        cls, agent_name: str
    ) -> Callable[[ResultFormatter], ResultFormatter]:
        """Decorator to register a formatter for an agent type.

        Args:
            agent_name: Name of the agent this formatter handles

        Returns:
            Decorator function
        """

        def decorator(func: ResultFormatter) -> ResultFormatter:
            cls._formatters[agent_name] = func
            return func

        return decorator

    @classmethod
    def format(cls, result: BaseStepResult) -> str:
        """Format a step result using the registered formatter.

        Args:
            result: Step result to format

        Returns:
            Formatted markdown string
        """
        formatter = cls._formatters.get(result.agent_name, cls._default_formatter)
        try:
            return formatter(result)
        except Exception as e:
            # Fallback on formatter error
            return cls._error_formatter(result, str(e))

    @staticmethod
    def _default_formatter(result: BaseStepResult) -> str:
        """Default formatter for unregistered agent types."""
        status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"
        lines = [
            f"# Step {result.step_number}: {result.agent_name.title()}",
            "",
            f"**Status:** {status_icon} {result.status.value.upper()}",
        ]
        if result.error_message:
            lines.extend(["", f"**Error:** {result.error_message}"])
        if result.duration_seconds:
            lines.extend(["", f"**Duration:** {result.duration_seconds:.2f}s"])
        if result.raw_output:
            lines.extend([
                "",
                "## Raw Output",
                "",
                "```json",
                str(result.raw_output)[:2000],
                "```",
            ])
        return "\n".join(lines)

    @staticmethod
    def _error_formatter(result: BaseStepResult, error: str) -> str:
        """Formatter for when formatting fails."""
        return f"""# Step {result.step_number}: {result.agent_name.title()}

**Status:** ⚠️ FORMATTING ERROR

**Error:** Failed to format result: {error}

## Raw Result

```
{str(result.raw_output)[:1000]}
```
"""

    @classmethod
    def get_registered_formatters(cls) -> list[str]:
        """Get list of registered formatter agent names."""
        return list(cls._formatters.keys())


# Self-registering formatters using decorator


@FormatterRegistry.register("enhancer")
def format_enhancer_result(result: EnhancerStepResult) -> str:
    """Format enhancer step result as markdown."""
    status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"
    lines = [
        "# Step 1: Enhanced Prompt",
        "",
        f"**Status:** {status_icon} {result.status.value.upper()}",
        "",
    ]

    if result.status == StepStatus.FAILED:
        if result.error_message:
            lines.extend(["**Error:**", "", result.error_message])
        return "\n".join(lines)

    lines.extend([
        "## Requirements Analysis",
        "",
        result.enhanced_prompt or "_No enhanced prompt generated_",
        "",
    ])

    if result.requirements:
        lines.extend(["## Extracted Requirements", ""])
        for req in result.requirements:
            lines.append(f"- {req}")
        lines.append("")

    if result.architecture_guidance:
        lines.extend([
            "## Architecture Guidance",
            "",
            result.architecture_guidance,
            "",
        ])

    if result.quality_standards:
        lines.extend([
            "## Quality Standards",
            "",
            result.quality_standards,
        ])

    if result.context7_info:
        lines.extend([
            "",
            "## Context7 Integration",
            "",
            f"- Libraries detected: {result.context7_info.get('libraries_detected', [])}",
            f"- Docs available: {result.context7_info.get('docs_available', 0)}",
        ])

    return "\n".join(lines)


@FormatterRegistry.register("planner")
def format_planner_result(result: PlannerStepResult) -> str:
    """Format planner step result as markdown."""
    status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"
    lines = [
        "# Step 2: User Stories",
        "",
        f"**Status:** {status_icon} {result.status.value.upper()}",
        "",
    ]

    if result.status == StepStatus.FAILED:
        if result.error_message:
            lines.extend(["**Error:**", "", result.error_message])
        return "\n".join(lines)

    lines.append(f"**Story Points Total:** {result.story_points}")
    if result.estimated_complexity:
        lines.append(f"**Estimated Complexity:** {result.estimated_complexity}")
    lines.append("")

    for i, story in enumerate(result.stories, 1):
        title = story.get("title", f"Story {i}")
        desc = story.get("description", "")
        lines.extend([
            f"## {i}. {title}",
            "",
        ])
        if desc:
            lines.extend([desc, ""])
        if criteria := story.get("acceptance_criteria", []):
            lines.append("**Acceptance Criteria:**")
            for c in criteria:
                lines.append(f"- {c}")
            lines.append("")

    if result.acceptance_criteria and not result.stories:
        lines.extend(["## Acceptance Criteria", ""])
        for criterion in result.acceptance_criteria:
            lines.append(f"- {criterion}")

    return "\n".join(lines)


@FormatterRegistry.register("architect")
def format_architect_result(result: ArchitectStepResult) -> str:
    """Format architect step result as markdown."""
    status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"
    lines = [
        "# Step 3: System Architecture",
        "",
        f"**Status:** {status_icon} {result.status.value.upper()}",
        "",
    ]

    if result.status == StepStatus.FAILED:
        if result.error_message:
            lines.extend(["**Error:**", "", result.error_message])
        return "\n".join(lines)

    lines.append(f"**Pattern:** {result.architecture_pattern or 'Not specified'}")
    lines.append("")

    if result.technology_stack:
        lines.extend([
            "## Technology Stack",
            "",
            *[f"- {tech}" for tech in result.technology_stack],
            "",
        ])

    if result.components:
        lines.extend(["## Components", ""])
        for comp in result.components:
            name = comp.get("name", "Component")
            purpose = comp.get("purpose", "")
            lines.append(f"### {name}")
            if purpose:
                lines.append(f"\n{purpose}\n")

    if result.data_flow:
        lines.extend([
            "## Data Flow",
            "",
            result.data_flow,
            "",
        ])

    if result.security_considerations:
        lines.extend([
            "## Security Considerations",
            "",
            result.security_considerations,
            "",
        ])

    if result.diagram:
        lines.extend([
            "## Architecture Diagram",
            "",
            "```",
            result.diagram,
            "```",
        ])

    return "\n".join(lines)


@FormatterRegistry.register("designer")
def format_designer_result(result: DesignerStepResult) -> str:
    """Format designer step result as markdown."""
    status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"
    lines = [
        "# Step 4: API Design",
        "",
        f"**Status:** {status_icon} {result.status.value.upper()}",
        "",
    ]

    if result.status == StepStatus.FAILED:
        if result.error_message:
            lines.extend(["**Error:**", "", result.error_message])
        return "\n".join(lines)

    if result.api_endpoints:
        lines.extend(["## Endpoints", ""])
        for endpoint in result.api_endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "/")
            desc = endpoint.get("description", "")
            lines.append(f"### `{method} {path}`")
            if desc:
                lines.append(f"\n{desc}\n")

    if result.data_models:
        lines.extend(["## Data Models", ""])
        for model in result.data_models:
            name = model.get("name", "Model")
            lines.append(f"### {name}")
            if fields := model.get("fields", []):
                lines.append("\n| Field | Type | Description |")
                lines.append("|-------|------|-------------|")
                for field in fields:
                    lines.append(
                        f"| {field.get('name', '')} | {field.get('type', '')} "
                        f"| {field.get('description', '')} |"
                    )
            lines.append("")

    if result.ui_components:
        lines.extend(["## UI Components", ""])
        for comp in result.ui_components:
            name = comp.get("name", "Component")
            desc = comp.get("description", "")
            lines.append(f"- **{name}**: {desc}")
        lines.append("")

    return "\n".join(lines)


@FormatterRegistry.register("implementer")
def format_implementer_result(result: ImplementerStepResult) -> str:
    """Format implementer step result as markdown."""
    status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"
    lines = [
        "# Step 5: Implementation",
        "",
        f"**Status:** {status_icon} {result.status.value.upper()}",
        "",
    ]

    if result.status == StepStatus.FAILED:
        if result.error_message:
            lines.extend(["**Error:**", "", result.error_message])
        return "\n".join(lines)

    if result.files_created:
        lines.extend([
            "## Files Created",
            "",
            *[f"- `{f}`" for f in result.files_created],
            "",
        ])

    if result.files_modified:
        lines.extend([
            "## Files Modified",
            "",
            *[f"- `{f}`" for f in result.files_modified],
            "",
        ])

    if result.backup_path:
        lines.extend([
            "## Backup",
            "",
            f"Original files backed up to: `{result.backup_path}`",
            "",
        ])

    if result.code_preview:
        lines.extend([
            "## Code Preview",
            "",
            "```python",
            result.code_preview[:2000],
            "```",
        ])

    return "\n".join(lines)


@FormatterRegistry.register("reviewer")
def format_reviewer_result(result: ReviewerStepResult) -> str:
    """Format reviewer step result as markdown."""
    status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"

    # Score icon based on overall score
    if result.overall_score >= 70:
        score_icon = "✅"
    elif result.overall_score >= 50:
        score_icon = "⚠️"
    else:
        score_icon = "❌"

    lines = [
        "# Step 6: Code Review",
        "",
        f"**Status:** {status_icon} {result.status.value.upper()}",
        "",
    ]

    if result.status == StepStatus.FAILED:
        if result.error_message:
            lines.extend(["**Error:**", "", result.error_message])
        return "\n".join(lines)

    lines.extend([
        f"## Overall Score: {result.overall_score:.0f}/100 {score_icon}",
        "",
        "### Metric Breakdown",
        "",
        "| Metric | Score |",
        "|--------|-------|",
        f"| Complexity | {result.complexity_score:.1f}/10 |",
        f"| Security | {result.security_score:.1f}/10 |",
        f"| Maintainability | {result.maintainability_score:.1f}/10 |",
        f"| Test Coverage | {result.test_coverage_score:.1f}/10 |",
        f"| Performance | {result.performance_score:.1f}/10 |",
        "",
    ])

    if result.issues:
        lines.extend([
            "## Issues Found",
            "",
        ])
        for issue in result.issues[:10]:
            if isinstance(issue, dict):
                lines.append(f"- {issue.get('message', issue)}")
            else:
                lines.append(f"- {issue}")
        if len(result.issues) > 10:
            lines.append(f"- ... and {len(result.issues) - 10} more issues")
        lines.append("")

    if result.recommendations:
        lines.extend([
            "## Recommendations",
            "",
            *[f"- {rec}" for rec in result.recommendations],
        ])

    return "\n".join(lines)


@FormatterRegistry.register("tester")
def format_tester_result(result: QAStepResult) -> str:
    """Format tester step result as markdown."""
    status_icon = "✅" if result.status == StepStatus.SUCCESS else "❌"
    lines = [
        "# Step 7: Test Generation",
        "",
        f"**Status:** {status_icon} {result.status.value.upper()}",
        "",
    ]

    if result.status == StepStatus.FAILED:
        if result.error_message:
            lines.extend(["**Error:**", "", result.error_message])
        return "\n".join(lines)

    lines.append(f"**Tests Generated:** {result.test_count}")
    if result.coverage_percent is not None:
        lines.append(f"**Coverage:** {result.coverage_percent:.1f}%")
    lines.append("")

    if result.test_files_created:
        lines.extend([
            "## Test Files",
            "",
            *[f"- `{f}`" for f in result.test_files_created],
            "",
        ])

    if result.test_plan:
        lines.extend([
            "## Test Plan",
            "",
            result.test_plan,
        ])

    return "\n".join(lines)


@FormatterRegistry.register("verification")
def format_verification_result(result: VerificationStepResult) -> str:
    """Format verification step result as markdown."""
    status_icon = "✅" if result.complete else "❌"
    lines = [
        "# Step 8: Comprehensive Verification Report",
        "",
        "## Verification Results",
        "",
        f"- **Status:** {status_icon} {'Complete' if result.complete else 'Incomplete'}",
        f"- **Deliverables:** {result.deliverables_verified}/{result.deliverables_total}",
        "",
    ]

    if result.gaps:
        lines.extend([
            "## Gaps Found",
            "",
        ])
        for gap in result.gaps:
            if isinstance(gap, dict):
                category = gap.get("category", "Gap")
                item = gap.get("item", gap)
                lines.append(f"- **{category}**: {item}")
            else:
                lines.append(f"- {gap}")
        lines.append("")

    if result.loopback_step:
        lines.extend([
            "## Loopback Required",
            "",
            f"Loop back to **Step {result.loopback_step}** to address gaps.",
        ])
    else:
        lines.extend([
            "## Status",
            "",
            f"{status_icon} All deliverables verified. Workflow complete."
            if result.complete
            else "⚠️ Verification incomplete. Review gaps above.",
        ])

    return "\n".join(lines)


def format_step_result(result: BaseStepResult) -> str:
    """Format a step result using the formatter registry.

    This is the main entry point for formatting step results.

    Args:
        result: Step result to format

    Returns:
        Formatted markdown string
    """
    return FormatterRegistry.format(result)


def format_failed_step(
    step_number: int,
    agent_name: str,
    error_message: str,
) -> str:
    """Format a failed step as markdown.

    Args:
        step_number: Step number
        agent_name: Name of the agent
        error_message: Error message

    Returns:
        Formatted markdown string
    """
    return f"""# Step {step_number}: {agent_name.title()}

**Status:** ❌ FAILED

**Error:** {error_message}
"""


def format_skipped_step(
    step_number: int,
    agent_name: str,
    skip_reason: str,
) -> str:
    """Format a skipped step as markdown.

    Args:
        step_number: Step number
        agent_name: Name of the agent
        skip_reason: Reason for skipping

    Returns:
        Formatted markdown string
    """
    return f"""# Step {step_number}: {agent_name.title()}

**Status:** ⏭️ SKIPPED

**Reason:** {skip_reason}
"""
