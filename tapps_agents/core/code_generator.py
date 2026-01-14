"""
Code Generator for TappsCodingAgents.

Provides code file generation from design specifications with templates
and multi-language support.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CodeTemplate:
    """Code template definition."""

    name: str
    language: str
    type: str  # "interface", "class", "service", "component", etc.
    template_content: str


class CodeGenerator:
    """
    Generates code files from design specifications.
    
    Supports:
    - Template-based code generation
    - Multiple languages (Python, TypeScript, etc.)
    - Multi-file code generation
    - Code quality integration
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize code generator.
        
        Args:
            project_root: Optional project root for template discovery
        """
        self.project_root = project_root or Path.cwd()
        self.templates_dir = self.project_root / ".tapps-agents" / "code_templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Register default templates
        self._register_default_templates()

    def _register_default_templates(self) -> None:
        """Register default code templates."""
        self.templates = {
            ("typescript", "interface"): self._get_typescript_interface_template(),
            ("python", "class"): self._get_python_class_template(),
            ("python", "service"): self._get_python_service_template(),
            ("typescript", "api_client"): self._get_typescript_api_client_template(),
        }

    def generate_typescript_interface(
        self,
        interface_data: dict[str, Any],
        output_file: str | Path,
    ) -> Path:
        """
        Generate TypeScript interface from data model.
        
        Args:
            interface_data: Interface data from designer agent
            output_file: Output file path
            
        Returns:
            Path to generated file
        """
        template = self.templates.get(("typescript", "interface"))
        if not template:
            raise ValueError("TypeScript interface template not found")

        content = self._render_template(template, interface_data)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def generate_python_class(
        self,
        class_data: dict[str, Any],
        output_file: str | Path,
    ) -> Path:
        """
        Generate Python class from specification.
        
        Args:
            class_data: Class data from designer/architect agent
            output_file: Output file path
            
        Returns:
            Path to generated file
        """
        template = self.templates.get(("python", "class"))
        if not template:
            raise ValueError("Python class template not found")

        content = self._render_template(template, class_data)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def generate_api_client(
        self,
        api_data: dict[str, Any],
        output_file: str | Path,
        language: str = "typescript",
    ) -> Path:
        """
        Generate API client code from API design.
        
        Args:
            api_data: API design data from designer agent
            output_file: Output file path
            language: Programming language (typescript, python)
            
        Returns:
            Path to generated file
        """
        template_key = (language, "api_client")
        template = self.templates.get(template_key)
        if not template:
            raise ValueError(f"API client template for {language} not found")

        content = self._render_template(template, api_data)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def generate_multi_file_structure(
        self,
        structure_data: dict[str, Any],
        base_dir: Path,
    ) -> list[Path]:
        """
        Generate multiple files from structure specification.
        
        Args:
            structure_data: Structure data with files to generate
            base_dir: Base directory for generated files
            
        Returns:
            List of generated file paths
        """
        generated_files = []

        for file_spec in structure_data.get("files", []):
            file_path = base_dir / file_spec["path"]
            file_type = file_spec.get("type", "class")
            language = file_spec.get("language", "python")
            content = file_spec.get("content")

            if content:
                # Use provided content
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                generated_files.append(file_path)
            else:
                # Generate from template
                template_key = (language, file_type)
                template = self.templates.get(template_key)
                if template:
                    content = self._render_template(template, file_spec.get("data", {}))
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding="utf-8")
                    generated_files.append(file_path)

        return generated_files

    def _render_template(self, template: str, data: dict[str, Any]) -> str:
        """Render template with data (simple string replacement for now)."""
        # Simple template rendering - in production, use Jinja2
        result = template
        for key, value in data.items():
            placeholder = f"{{{{ {key} }}}}"
            if isinstance(value, (list, dict)):
                # Handle complex types
                import json
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            result = result.replace(placeholder, value_str)
        return result

    def _get_typescript_interface_template(self) -> str:
        """Get TypeScript interface template."""
        return """/**
 * {{ description or 'Generated interface' }}
 */
export interface {{ name }} {
{% if properties %}
{% for prop in properties %}
  {{ prop.name }}{% if not prop.required %}?{% endif %}: {{ prop.type }};
{% endfor %}
{% else %}
  // No properties defined
{% endif %}
}
"""

    def _get_python_class_template(self) -> str:
        """Get Python class template."""
        return """\"\"\"
{{ description or 'Generated class' }}
\"\"\"

from typing import Any, Optional
{% if imports %}
{% for imp in imports %}
{{ imp }}
{% endfor %}
{% endif %}


class {{ name }}({{ base_class or 'object' }}):
    \"\"\"
    {{ description or 'Generated class' }}
    \"\"\"

    def __init__(self{% if parameters %}, {{ parameters }}{% endif %}):
        \"\"\"
        Initialize {{ name }}.
        \"\"\"
{% if properties %}
{% for prop in properties %}
        self.{{ prop.name }} = {{ prop.name }}
{% endfor %}
{% endif %}
"""

    def _get_python_service_template(self) -> str:
        """Get Python service template."""
        return """\"\"\"
{{ description or 'Generated service' }}
\"\"\"

from typing import Any, Optional
{% if imports %}
{% for imp in imports %}
{{ imp }}
{% endfor %}
{% endif %}


class {{ name }}Service:
    \"\"\"
    {{ description or 'Generated service' }}
    \"\"\"

    def __init__(self{% if dependencies %}, {{ dependencies }}{% endif %}):
        \"\"\"
        Initialize {{ name }}Service.
        \"\"\"
{% if dependencies %}
{% for dep in dependencies %}
        self.{{ dep }} = {{ dep }}
{% endfor %}
{% endif %}

{% if methods %}
{% for method in methods %}
    async def {{ method.name }}(self{% if method.parameters %}, {{ method.parameters }}{% endif %}):
        \"\"\"
        {{ method.description or 'Method description' }}
        \"\"\"
        # TODO: Implement {{ method.name }}
        pass

{% endfor %}
{% endif %}
"""

    def _get_typescript_api_client_template(self) -> str:
        """Get TypeScript API client template."""
        return """/**
 * {{ description or 'Generated API client' }}
 */

export class {{ name }}Client {
  private baseUrl: string;

  constructor(baseUrl: string = '{{ base_url or "http://localhost:8000" }}') {
    this.baseUrl = baseUrl;
  }

{% if endpoints %}
{% for endpoint in endpoints %}
  /**
   * {{ endpoint.description or 'Endpoint description' }}
   */
  async {{ endpoint.method_name or endpoint.path.replace('/', '_').replace('-', '_') }}(
{% if endpoint.parameters %}
    {{ endpoint.parameters }}
{% endif %}
  ): Promise<{{ endpoint.response_type or 'any' }}> {
    const response = await fetch(`${this.baseUrl}{{ endpoint.path }}`, {
      method: '{{ endpoint.method or "GET" }}',
{% if endpoint.method != "GET" %}
      headers: {
        'Content-Type': 'application/json',
      },
{% if endpoint.request_body %}
      body: JSON.stringify({{ endpoint.request_body }}),
{% endif %}
{% endif %}
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

{% endfor %}
{% endif %}
}
"""
