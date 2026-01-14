"""
Document Generator for TappsCodingAgents.

Provides complete document generation from agent outputs with templates
and multi-format support.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template


@dataclass
class DocumentTemplate:
    """Document template definition."""

    name: str
    type: str  # "user_story", "architecture", "api_design", etc.
    template_content: str
    default_format: str = "markdown"


class DocumentGenerator:
    """
    Generates complete documents from agent outputs.
    
    Supports:
    - Template-based document generation
    - Multiple output formats (markdown, HTML, etc.)
    - Auto-population from agent outputs
    - Custom template injection
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize document generator.
        
        Args:
            project_root: Optional project root for template discovery
        """
        self.project_root = project_root or Path.cwd()
        self.templates_dir = self.project_root / ".tapps-agents" / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
        )

        # Register default templates
        self._register_default_templates()

    def _register_default_templates(self) -> None:
        """Register default document templates."""
        self.templates = {
            "user_story": self._get_user_story_template(),
            "architecture": self._get_architecture_template(),
            "api_design": self._get_api_design_template(),
            "technical_design": self._get_technical_design_template(),
            "plan": self._get_plan_template(),
        }

    def generate_user_story_doc(
        self,
        story_data: dict[str, Any],
        output_file: str | Path | None = None,
        format: str = "markdown",
    ) -> str | Path:
        """
        Generate complete user story document.
        
        Args:
            story_data: User story data from planner agent
            output_file: Optional output file path
            format: Output format (markdown, html)
            
        Returns:
            Generated document string, or Path if output_file provided
        """
        template = self.templates["user_story"]
        content = self._render_template(template, story_data, format)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            return output_path

        return content

    def generate_architecture_doc(
        self,
        architecture_data: dict[str, Any],
        output_file: str | Path | None = None,
        format: str = "markdown",
    ) -> str | Path:
        """
        Generate complete architecture document.
        
        Args:
            architecture_data: Architecture data from architect agent
            output_file: Optional output file path
            format: Output format (markdown, html)
            
        Returns:
            Generated document string, or Path if output_file provided
        """
        template = self.templates["architecture"]
        content = self._render_template(template, architecture_data, format)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            return output_path

        return content

    def generate_api_design_doc(
        self,
        api_data: dict[str, Any],
        output_file: str | Path | None = None,
        format: str = "markdown",
    ) -> str | Path:
        """
        Generate complete API design document.
        
        Args:
            api_data: API design data from designer agent
            output_file: Optional output file path
            format: Output format (markdown, html)
            
        Returns:
            Generated document string, or Path if output_file provided
        """
        template = self.templates["api_design"]
        content = self._render_template(template, api_data, format)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            return output_path

        return content

    def generate_plan_doc(
        self,
        plan_data: dict[str, Any],
        output_file: str | Path | None = None,
        format: str = "markdown",
    ) -> str | Path:
        """
        Generate complete plan document.
        
        Args:
            plan_data: Plan data from planner agent
            output_file: Optional output file path
            format: Output format (markdown, html)
            
        Returns:
            Generated document string, or Path if output_file provided
        """
        template = self.templates["plan"]
        content = self._render_template(template, plan_data, format)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            return output_path

        return content

    def _render_template(
        self, template: str, data: dict[str, Any], format: str
    ) -> str:
        """Render template with data."""
        jinja_template = Template(template)
        rendered = jinja_template.render(
            **data,
            generated_at=datetime.now().isoformat(),
            format=format,
        )

        # Convert to HTML if requested
        if format == "html":
            return self._markdown_to_html(rendered)

        return rendered

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (basic implementation)."""
        # For now, return basic HTML wrapper
        # In production, use markdown library
        try:
            import markdown

            html_body = markdown.markdown(markdown)
        except ImportError:
            # Fallback: basic HTML
            html_body = f"<pre>{markdown}</pre>"

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Generated Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    def _get_user_story_template(self) -> str:
        """Get user story document template."""
        return """# User Story: {{ title or 'Untitled Story' }}

**Status:** {{ status or 'Draft' }}  
**Priority:** {{ priority or 'Medium' }}  
**Story Points:** {{ story_points or 'Not Estimated' }}  
**Epic:** {{ epic or 'None' }}

## Description

{{ description or 'No description provided.' }}

## Acceptance Criteria

{% if acceptance_criteria %}
{% for criterion in acceptance_criteria %}
- {{ criterion }}
{% endfor %}
{% else %}
- No acceptance criteria defined
{% endif %}

## Technical Notes

{% if technical_notes %}
{{ technical_notes }}
{% else %}
No technical notes provided.
{% endif %}

## Dependencies

{% if dependencies %}
{% for dep in dependencies %}
- {{ dep }}
{% endfor %}
{% else %}
No dependencies identified.
{% endif %}

## Tasks

{% if tasks %}
{% for task in tasks %}
### Task {{ loop.index }}: {{ task.title or 'Untitled Task' }}

**Estimate:** {{ task.estimate or 'Not estimated' }}  
**Status:** {{ task.status or 'Not Started' }}

{{ task.description or 'No description' }}

{% endfor %}
{% else %}
No tasks defined.
{% endif %}

---
*Generated on {{ generated_at }}*
"""

    def _get_architecture_template(self) -> str:
        """Get architecture document template."""
        return """# Architecture Design: {{ title or 'System Architecture' }}

**Version:** {{ version or '1.0' }}  
**Status:** {{ status or 'Draft' }}  
**Date:** {{ generated_at }}

## Overview

{{ overview or 'No overview provided.' }}

## System Components

{% if components %}
{% for component in components %}
### {{ component.name or 'Unnamed Component' }}

**Type:** {{ component.type or 'Unknown' }}  
**Description:** {{ component.description or 'No description' }}

**Responsibilities:**
{% if component.responsibilities %}
{% for resp in component.responsibilities %}
- {{ resp }}
{% endfor %}
{% else %}
- No responsibilities defined
{% endif %}

**Interfaces:**
{% if component.interfaces %}
{% for interface in component.interfaces %}
- {{ interface }}
{% endfor %}
{% else %}
- No interfaces defined
{% endif %}

{% endfor %}
{% else %}
No components defined.
{% endif %}

## Data Flow

{% if data_flow %}
{{ data_flow }}
{% else %}
No data flow diagram provided.
{% endif %}

## Technology Stack

{% if technology_stack %}
{% for tech in technology_stack %}
- **{{ tech.name }}:** {{ tech.version or 'Not specified' }} - {{ tech.purpose or 'No purpose specified' }}
{% endfor %}
{% else %}
No technology stack defined.
{% endif %}

## Security Considerations

{% if security_considerations %}
{{ security_considerations }}
{% else %}
No security considerations documented.
{% endif %}

## Performance Requirements

{% if performance_requirements %}
{{ performance_requirements }}
{% else %}
No performance requirements specified.
{% endif %}

## Deployment Architecture

{% if deployment %}
{{ deployment }}
{% else %}
No deployment architecture defined.
{% endif %}

---
*Generated on {{ generated_at }}*
"""

    def _get_api_design_template(self) -> str:
        """Get API design document template."""
        return """# API Design: {{ title or 'API Specification' }}

**Version:** {{ version or '1.0' }}  
**Base URL:** {{ base_url or 'Not specified' }}  
**Date:** {{ generated_at }}

## Overview

{{ overview or 'No overview provided.' }}

## Endpoints

{% if endpoints %}
{% for endpoint in endpoints %}
### {{ endpoint.method or 'GET' }} {{ endpoint.path or '/unknown' }}

**Description:** {{ endpoint.description or 'No description' }}

**Parameters:**
{% if endpoint.parameters %}
{% for param in endpoint.parameters %}
- **{{ param.name }}** ({{ param.type or 'string' }}): {{ param.description or 'No description' }}
  {% if param.required %}*Required*{% else %}*Optional*{% endif %}
{% endfor %}
{% else %}
No parameters
{% endif %}

**Request Body:**
{% if endpoint.request_body %}
```json
{{ endpoint.request_body }}
```
{% else %}
No request body
{% endif %}

**Response:**
{% if endpoint.response %}
```json
{{ endpoint.response }}
```
{% else %}
No response example
{% endif %}

**Status Codes:**
{% if endpoint.status_codes %}
{% for code in endpoint.status_codes %}
- **{{ code.code }}:** {{ code.description }}
{% endfor %}
{% else %}
- **200:** Success
{% endif %}

{% endfor %}
{% else %}
No endpoints defined.
{% endif %}

## Data Models

{% if data_models %}
{% for model in data_models %}
### {{ model.name or 'Unnamed Model' }}

**Type:** {{ model.type or 'object' }}

**Properties:**
{% if model.properties %}
{% for prop in model.properties %}
- **{{ prop.name }}** ({{ prop.type or 'string' }}): {{ prop.description or 'No description' }}
  {% if prop.required %}*Required*{% else %}*Optional*{% endif %}
{% endfor %}
{% else %}
No properties defined
{% endif %}

**Example:**
{% if model.example %}
```json
{{ model.example }}
```
{% else %}
No example provided
{% endif %}

{% endfor %}
{% else %}
No data models defined.
{% endif %}

## Authentication

{% if authentication %}
{{ authentication }}
{% else %}
No authentication method specified.
{% endif %}

## Error Handling

{% if error_handling %}
{{ error_handling }}
{% else %}
Standard HTTP status codes apply.
{% endif %}

---
*Generated on {{ generated_at }}*
"""

    def _get_technical_design_template(self) -> str:
        """Get technical design document template."""
        return """# Technical Design: {{ title or 'Technical Design Document' }}

**Version:** {{ version or '1.0' }}  
**Status:** {{ status or 'Draft' }}  
**Date:** {{ generated_at }}

## Overview

{{ overview or 'No overview provided.' }}

## Requirements

{% if requirements %}
{{ requirements }}
{% else %}
No requirements documented.
{% endif %}

## Design Decisions

{% if design_decisions %}
{% for decision in design_decisions %}
### {{ decision.title or 'Design Decision' }}

**Context:** {{ decision.context or 'No context provided' }}  
**Decision:** {{ decision.decision or 'No decision documented' }}  
**Rationale:** {{ decision.rationale or 'No rationale provided' }}

{% endfor %}
{% else %}
No design decisions documented.
{% endif %}

## Implementation Details

{% if implementation_details %}
{{ implementation_details }}
{% else %}
No implementation details provided.
{% endif %}

## Testing Strategy

{% if testing_strategy %}
{{ testing_strategy }}
{% else %}
No testing strategy defined.
{% endif %}

---
*Generated on {{ generated_at }}*
"""

    def _get_plan_template(self) -> str:
        """Get plan document template."""
        return """# Development Plan: {{ title or 'Feature Plan' }}

**Status:** {{ status or 'Draft' }}  
**Date:** {{ generated_at }}

## Overview

{{ overview or 'No overview provided.' }}

## User Stories

{% if user_stories %}
{% for story in user_stories %}
### Story {{ loop.index }}: {{ story.title or 'Untitled Story' }}

**Priority:** {{ story.priority or 'Medium' }}  
**Story Points:** {{ story.story_points or 'Not Estimated' }}

{{ story.description or 'No description' }}

**Acceptance Criteria:**
{% if story.acceptance_criteria %}
{% for criterion in story.acceptance_criteria %}
- {{ criterion }}
{% endfor %}
{% else %}
- No acceptance criteria defined
{% endif %}

{% endfor %}
{% else %}
No user stories defined.
{% endif %}

## Task Breakdown

{% if tasks %}
{% for task in tasks %}
### {{ task.title or 'Untitled Task' }}

**Estimate:** {{ task.estimate or 'Not estimated' }}  
**Dependencies:** {{ task.dependencies or 'None' }}

{{ task.description or 'No description' }}

{% endfor %}
{% else %}
No tasks defined.
{% endif %}

## Timeline

{% if timeline %}
{{ timeline }}
{% else %}
No timeline provided.
{% endif %}

## Dependencies

{% if dependencies %}
{% for dep in dependencies %}
- {{ dep }}
{% endfor %}
{% else %}
No dependencies identified.
{% endif %}

---
*Generated on {{ generated_at }}*
"""
