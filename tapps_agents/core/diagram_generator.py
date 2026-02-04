"""
Diagram Generator - Generate Mermaid and PlantUML diagrams from architecture/design.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DiagramGenerator:
    """Generates visual diagrams from architecture and design artifacts."""

    def generate_mermaid_component_diagram(self, architecture: dict[str, Any]) -> str:
        """
        Generate Mermaid component diagram from architecture.

        Args:
            architecture: Architecture dict with components

        Returns:
            Mermaid diagram code
        """
        components = architecture.get("components", [])
        if not components:
            return "graph TD\n    A[No components defined]\n"

        diagram = "graph TD\n"
        connections = []

        for i, component in enumerate(components):
            if isinstance(component, dict):
                name = component.get("name", f"Component{i+1}")
                component.get("type", "component")
            else:
                name = str(component)

            # Mermaid node ID (sanitized)
            node_id = self._sanitize_id(name)

            # Add component node
            diagram += f'    {node_id}["{name}"]\n'

            # Add connections
            if isinstance(component, dict):
                depends_on = component.get("depends_on", [])
                for dep in depends_on:
                    dep_id = self._sanitize_id(dep)
                    connections.append(f"    {dep_id} --> {node_id}\n")

        # Add connections
        diagram += "".join(connections)

        return diagram

    def generate_mermaid_sequence_diagram(self, interactions: list[dict[str, Any]]) -> str:
        """
        Generate Mermaid sequence diagram from interactions.

        Args:
            interactions: List of interaction dicts with actors and messages

        Returns:
            Mermaid sequence diagram code
        """
        if not interactions:
            return "sequenceDiagram\n    participant A\n    A->>A: No interactions defined\n"

        diagram = "sequenceDiagram\n"

        # Extract unique actors
        actors = set()
        for interaction in interactions:
            if isinstance(interaction, dict):
                actors.add(interaction.get("from", "Actor1"))
                actors.add(interaction.get("to", "Actor2"))

        # Add participants
        for actor in sorted(actors):
            actor_id = self._sanitize_id(actor)
            diagram += f'    participant {actor_id} as {actor}\n'

        # Add interactions
        for interaction in interactions:
            if isinstance(interaction, dict):
                from_actor = self._sanitize_id(interaction.get("from", "Actor1"))
                to_actor = self._sanitize_id(interaction.get("to", "Actor2"))
                message = interaction.get("message", "interaction")
                arrow_type = interaction.get("type", "->>")  # ->>, -->, -x, -)

                diagram += f"    {from_actor}{arrow_type}{to_actor}: {message}\n"

        return diagram

    def generate_mermaid_class_diagram(self, classes: list[dict[str, Any]]) -> str:
        """
        Generate Mermaid class diagram from class definitions.

        Args:
            classes: List of class dicts with name, attributes, methods

        Returns:
            Mermaid class diagram code
        """
        if not classes:
            return "classDiagram\n    class NoClasses\n"

        diagram = "classDiagram\n"

        for cls in classes:
            if isinstance(cls, dict):
                name = cls.get("name", "Class")
                attributes = cls.get("attributes", [])
                methods = cls.get("methods", [])
            else:
                name = str(cls)
                attributes = []
                methods = []

            diagram += f"    class {name} {{\n"

            # Add attributes
            for attr in attributes:
                if isinstance(attr, dict):
                    attr_str = attr.get("name", "attribute")
                    attr_type = attr.get("type", "")
                    visibility = attr.get("visibility", "+")
                    if attr_type:
                        attr_str += f": {attr_type}"
                    diagram += f"        {visibility}{attr_str}\n"
                else:
                    diagram += f"        +{attr}\n"

            # Add methods
            for method in methods:
                if isinstance(method, dict):
                    method_str = method.get("name", "method")
                    params = method.get("parameters", [])
                    return_type = method.get("return_type", "")
                    visibility = method.get("visibility", "+")
                    if params:
                        method_str += f"({', '.join(str(p) for p in params)})"
                    if return_type:
                        method_str += f": {return_type}"
                    diagram += f"        {visibility}{method_str}\n"
                else:
                    diagram += f"        +{method}\n"

            diagram += "    }\n"

        return diagram

    def generate_plantuml_component_diagram(self, architecture: dict[str, Any]) -> str:
        """
        Generate PlantUML component diagram from architecture.

        Args:
            architecture: Architecture dict with components

        Returns:
            PlantUML diagram code
        """
        components = architecture.get("components", [])
        if not components:
            return "@startuml\ncomponent [No components]\n@enduml\n"

        diagram = "@startuml\n"

        for i, component in enumerate(components):
            if isinstance(component, dict):
                name = component.get("name", f"Component{i+1}")
                component.get("type", "component")
            else:
                name = str(component)

            diagram += f'component "{name}"\n'

            # Add dependencies
            if isinstance(component, dict):
                depends_on = component.get("depends_on", [])
                for dep in depends_on:
                    diagram += f'"{dep}" --> "{name}"\n'

        diagram += "@enduml\n"

        return diagram

    def export_to_file(self, diagram_code: str, output_path: Path, format: str = "mermaid"):
        """
        Export diagram to file.

        Args:
            diagram_code: Diagram code (Mermaid or PlantUML)
            output_path: Output file path
            format: "mermaid" or "plantuml"
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "mermaid":
            # Mermaid files use .mmd extension
            if output_path.suffix != ".mmd":
                output_path = output_path.with_suffix(".mmd")
            output_path.write_text(diagram_code, encoding="utf-8")

        elif format == "plantuml":
            # PlantUML files use .puml extension
            if output_path.suffix != ".puml":
                output_path = output_path.with_suffix(".puml")
            output_path.write_text(diagram_code, encoding="utf-8")

        else:
            raise ValueError(f"Unsupported format: {format}. Use 'mermaid' or 'plantuml'")

        logger.info(f"Diagram exported to: {output_path}")

    def _sanitize_id(self, name: str) -> str:
        """Sanitize name for use as Mermaid node ID."""
        # Remove special characters, replace spaces with underscores
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "A" + sanitized
        return sanitized or "Node"
