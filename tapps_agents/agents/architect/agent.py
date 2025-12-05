"""
Architect Agent - System and security architecture design.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from ...core.mal import MAL
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config


class ArchitectAgent(BaseAgent):
    """
    Architect Agent - System and security architecture design.
    
    Permissions: Read, Write, Grep, Glob (no Edit, no Bash)
    
    Responsibilities:
    - Design system architecture
    - Create architecture diagrams (text-based)
    - Select technologies
    - Design security architecture
    - Define system boundaries
    """
    
    def __init__(self, mal: Optional[MAL] = None, config: Optional[ProjectConfig] = None):
        super().__init__(agent_id="architect", agent_name="Architect Agent", config=config)
        if config is None:
            config = load_config()
        self.config = config
        
        # Initialize MAL
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )
    
    def get_commands(self) -> List[Dict[str, str]]:
        """Return available commands for architect agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {"command": "*design-system", "description": "Design system architecture for a feature or project"},
            {"command": "*create-diagram", "description": "Create architecture diagram (text-based)"},
            {"command": "*select-technology", "description": "Select technology stack for a component"},
            {"command": "*design-security", "description": "Design security architecture"},
            {"command": "*define-boundaries", "description": "Define system boundaries and interfaces"},
        ]
    
    async def run(self, command: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute architect agent command.
        
        Commands:
        - *design-system: Design system architecture
        - *create-diagram: Create architecture diagram
        - *select-technology: Select technology stack
        - *design-security: Design security architecture
        - *define-boundaries: Define system boundaries
        - *help: Show help
        """
        command = command.lstrip("*")
        
        if command == "help":
            return {"type": "help", "content": self.format_help()}
        
        elif command == "design-system":
            requirements = kwargs.get("requirements", "")
            context = kwargs.get("context", "")
            output_file = kwargs.get("output_file", None)
            
            return await self._design_system(requirements, context, output_file)
        
        elif command == "create-diagram":
            architecture_description = kwargs.get("architecture_description", "")
            diagram_type = kwargs.get("diagram_type", "component")
            output_file = kwargs.get("output_file", None)
            
            return await self._create_diagram(architecture_description, diagram_type, output_file)
        
        elif command == "select-technology":
            component_description = kwargs.get("component_description", "")
            requirements = kwargs.get("requirements", "")
            constraints = kwargs.get("constraints", [])
            
            return await self._select_technology(component_description, requirements, constraints)
        
        elif command == "design-security":
            system_description = kwargs.get("system_description", "")
            threat_model = kwargs.get("threat_model", "")
            
            return await self._design_security(system_description, threat_model)
        
        elif command == "define-boundaries":
            system_description = kwargs.get("system_description", "")
            context = kwargs.get("context", "")
            
            return await self._define_boundaries(system_description, context)
        
        else:
            return {"error": f"Unknown command: {command}"}
    
    async def _design_system(
        self,
        requirements: str,
        context: str = "",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Design system architecture."""
        if not requirements:
            return {"error": "requirements is required"}
        
        prompt = f"""Design a system architecture based on the following requirements.

Requirements:
{requirements}

{f"Context: {context}" if context else ""}

Provide a comprehensive architecture design including:
1. System Overview
2. Architecture Pattern (microservices, monolith, serverless, etc.)
3. Component Diagram (text-based)
4. Technology Stack
5. Data Flow
6. Integration Points
7. Scalability Considerations
8. Security Considerations
9. Deployment Architecture

Format as structured JSON with detailed architecture specification."""

        try:
            response = await self.mal.generate(
                prompt=prompt,
                model=self.config.mal.model if self.config.mal else "qwen2.5-coder:7b",
                temperature=0.2
            )
            
            architecture = {
                "requirements": requirements,
                "architecture": response,
                "components": [],
                "technology_stack": [],
                "data_flow": ""
            }
            
            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(architecture, indent=2))
                architecture["output_file"] = str(output_path)
            
            return {
                "success": True,
                "architecture": architecture
            }
        except Exception as e:
            return {"error": f"Failed to design system: {str(e)}"}
    
    async def _create_diagram(
        self,
        architecture_description: str,
        diagram_type: str = "component",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create architecture diagram (text-based)."""
        if not architecture_description:
            return {"error": "architecture_description is required"}
        
        diagram_types = {
            "component": "component diagram showing system components and relationships",
            "sequence": "sequence diagram showing interactions over time",
            "deployment": "deployment diagram showing deployment architecture",
            "class": "class diagram showing object relationships",
            "data-flow": "data flow diagram showing data movement"
        }
        
        diagram_description = diagram_types.get(diagram_type, "architecture diagram")
        
        prompt = f"""Create a text-based {diagram_description} for the following architecture.

Architecture Description:
{architecture_description}

Provide a clear, ASCII/text-based diagram that can be rendered in markdown or plain text.
Use standard diagram notation (boxes, arrows, labels) for clarity.

Format:
1. Diagram (ASCII/text format)
2. Legend/Explanation
3. Key Relationships
"""

        try:
            response = await self.mal.generate(
                prompt=prompt,
                model=self.config.mal.model if self.config.mal else "qwen2.5-coder:7b",
                temperature=0.1
            )
            
            diagram = {
                "type": diagram_type,
                "architecture": architecture_description,
                "diagram": response
            }
            
            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(diagram["diagram"])
                diagram["output_file"] = str(output_path)
            
            return {
                "success": True,
                "diagram": diagram
            }
        except Exception as e:
            return {"error": f"Failed to create diagram: {str(e)}"}
    
    async def _select_technology(
        self,
        component_description: str,
        requirements: str = "",
        constraints: List[str] = None
    ) -> Dict[str, Any]:
        """Select technology stack for a component."""
        if constraints is None:
            constraints = []
        
        prompt = f"""Select an appropriate technology stack for the following component.

Component Description:
{component_description}

{f"Requirements: {requirements}" if requirements else ""}

{f"Constraints: {', '.join(constraints)}" if constraints else ""}

For each technology recommendation, provide:
1. Technology Name
2. Rationale
3. Pros and Cons
4. Fit for Requirements
5. Learning Curve
6. Community Support
7. Alternative Options

Format as structured JSON with technology recommendations."""

        try:
            response = await self.mal.generate(
                prompt=prompt,
                model=self.config.mal.model if self.config.mal else "qwen2.5-coder:7b",
                temperature=0.3
            )
            
            technology_selection = {
                "component": component_description,
                "requirements": requirements,
                "constraints": constraints,
                "recommendations": response
            }
            
            return {
                "success": True,
                "technology_selection": technology_selection
            }
        except Exception as e:
            return {"error": f"Failed to select technology: {str(e)}"}
    
    async def _design_security(
        self,
        system_description: str,
        threat_model: str = ""
    ) -> Dict[str, Any]:
        """Design security architecture."""
        if not system_description:
            return {"error": "system_description is required"}
        
        prompt = f"""Design a security architecture for the following system.

System Description:
{system_description}

{f"Threat Model: {threat_model}" if threat_model else ""}

Provide a comprehensive security design including:
1. Security Principles
2. Authentication & Authorization Strategy
3. Data Protection (encryption, at-rest, in-transit)
4. Network Security
5. API Security
6. Threat Mitigation Strategies
7. Security Monitoring & Logging
8. Compliance Considerations
9. Security Best Practices

Format as structured JSON with detailed security architecture."""

        try:
            response = await self.mal.generate(
                prompt=prompt,
                model=self.config.mal.model if self.config.mal else "qwen2.5-coder:7b",
                temperature=0.2
            )
            
            security_design = {
                "system": system_description,
                "threat_model": threat_model,
                "security_architecture": response
            }
            
            return {
                "success": True,
                "security_design": security_design
            }
        except Exception as e:
            return {"error": f"Failed to design security: {str(e)}"}
    
    async def _define_boundaries(
        self,
        system_description: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Define system boundaries and interfaces."""
        if not system_description:
            return {"error": "system_description is required"}
        
        prompt = f"""Define system boundaries and interfaces for the following system.

System Description:
{system_description}

{f"Context: {context}" if context else ""}

Provide:
1. System Boundaries (what's inside vs outside)
2. External Dependencies
3. API Interfaces (REST, GraphQL, gRPC, etc.)
4. Data Interfaces (data formats, schemas)
5. Integration Points
6. Interface Contracts
7. Service Contracts
8. Communication Protocols

Format as structured JSON with boundary and interface definitions."""

        try:
            response = await self.mal.generate(
                prompt=prompt,
                model=self.config.mal.model if self.config.mal else "qwen2.5-coder:7b",
                temperature=0.2
            )
            
            boundaries = {
                "system": system_description,
                "boundaries_and_interfaces": response
            }
            
            return {
                "success": True,
                "boundaries": boundaries
            }
        except Exception as e:
            return {"error": f"Failed to define boundaries: {str(e)}"}

