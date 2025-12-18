"""
Architect Agent - System and security architecture design.
"""

import json
import logging
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL
from ...experts.agent_integration import ExpertSupportMixin

logger = logging.getLogger(__name__)


class ArchitectAgent(BaseAgent, ExpertSupportMixin):
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

    def __init__(
        self,
        mal: MAL | None = None,
        config: ProjectConfig | None = None,
        expert_registry: Any | None = None,
    ):
        super().__init__(
            agent_id="architect", agent_name="Architect Agent", config=config
        )
        if config is None:
            config = load_config()
        self.config = config

        # Initialize MAL
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )

        # Initialize Context7 helper
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

        # Expert registry will be initialized in activate() via ExpertSupportMixin
        # Allow manual override if provided
        self.expert_registry = None
        if expert_registry:
            self.expert_registry = expert_registry

    async def activate(self, project_root: Path | None = None):
        """Activate the architect agent with expert support."""
        await super().activate(project_root)
        # Initialize expert support via mixin
        await self._initialize_expert_support(project_root)

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for architect agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*design-system",
                "description": "Design system architecture for a feature or project",
            },
            {
                "command": "*create-diagram",
                "description": "Create architecture diagram (text-based)",
            },
            {
                "command": "*select-technology",
                "description": "Select technology stack for a component",
            },
            {
                "command": "*design-security",
                "description": "Design security architecture",
            },
            {
                "command": "*define-boundaries",
                "description": "Define system boundaries and interfaces",
            },
        ]

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
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

            return await self._create_diagram(
                architecture_description, diagram_type, output_file
            )

        elif command == "select-technology":
            component_description = kwargs.get("component_description", "")
            requirements = kwargs.get("requirements", "")
            constraints = kwargs.get("constraints", [])

            return await self._select_technology(
                component_description, requirements, constraints
            )

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

    async def _consult_experts_for_design(
        self, requirements: str, context: str
    ) -> dict[str, Any]:
        """Consult experts for architecture guidance."""
        expert_guidance: dict[str, Any] = {}
        if not self.expert_registry:
            return expert_guidance

        # Consult Software Architecture expert
        try:
            arch_consultation = await self.expert_registry.consult(
                query=f"Design system architecture for: {requirements}. Context: {context}",
                domain="software-architecture",
                include_all=True,
                prioritize_builtin=True,
                agent_id="architect",
            )
            expert_guidance["architecture"] = arch_consultation.weighted_answer
            expert_guidance["architecture_confidence"] = arch_consultation.confidence
        except Exception:
            logger.debug("Architecture expert consultation failed", exc_info=True)

        # Consult Performance expert
        try:
            perf_consultation = await self.expert_registry.consult(
                query=f"Performance considerations for architecture: {requirements}",
                domain="performance-optimization",
                include_all=True,
                prioritize_builtin=True,
                agent_id="architect",
            )
            expert_guidance["performance"] = perf_consultation.weighted_answer
        except Exception:
            logger.debug("Performance expert consultation failed", exc_info=True)

        # Consult Security expert
        try:
            sec_consultation = await self.expert_registry.consult(
                query=f"Security architecture considerations: {requirements}",
                domain="security",
                include_all=True,
                prioritize_builtin=True,
                agent_id="architect",
            )
            expert_guidance["security"] = sec_consultation.weighted_answer
        except Exception:
            logger.debug("Security expert consultation failed", exc_info=True)

        return expert_guidance

    def _format_expert_guidance(self, expert_guidance: dict[str, Any]) -> str:
        """Format expert guidance into a prompt section."""
        if not expert_guidance:
            return ""

        expert_section = "\n\nExpert Guidance:\n"
        if "architecture" in expert_guidance:
            expert_section += (
                f"\nArchitecture Expert:\n{expert_guidance['architecture'][:500]}...\n"
            )
        if "performance" in expert_guidance:
            expert_section += (
                f"\nPerformance Expert:\n{expert_guidance['performance'][:300]}...\n"
            )
        if "security" in expert_guidance:
            expert_section += (
                f"\nSecurity Expert:\n{expert_guidance['security'][:300]}...\n"
            )
        return expert_section

    async def _get_context7_docs_for_design(
        self, requirements: str, context: str
    ) -> dict[str, str]:
        """Get Context7 documentation for mentioned technologies."""
        context7_docs: dict[str, str] = {}
        if not self.context7:
            return context7_docs

        full_text = f"{requirements} {context}"
        if not self.context7.should_use_context7(full_text):
            return context7_docs

        # Extract potential library names and get docs
        libraries = await self.context7.search_libraries(requirements, limit=5)
        for lib_info in libraries:
            lib_name = (
                lib_info.get("id", "").split("/")[-1]
                if isinstance(lib_info, dict)
                else str(lib_info)
            )
            if lib_name:
                doc = await self.context7.get_documentation(
                    lib_name, topic="architecture"
                )
                if doc:
                    context7_docs[lib_name] = doc.get("content", "")[:500]

        return context7_docs

    def _format_context7_docs(self, context7_docs: dict[str, str]) -> str:
        """Format Context7 documentation into a prompt section."""
        if not context7_docs:
            return ""

        context7_section = "\n\nRelevant Architecture Documentation:\n"
        for lib_name, doc_content in context7_docs.items():
            context7_section += f"\n{lib_name} Architecture:\n{doc_content[:300]}...\n"
        return context7_section

    def _build_design_prompt(
        self,
        requirements: str,
        context: str,
        expert_section: str,
        context7_section: str,
    ) -> str:
        """Build the architecture design prompt."""
        return f"""Design a system architecture based on the following requirements.
{expert_section}

Requirements:
{requirements}

{f"Context: {context}" if context else ""}
{context7_section}

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

    def _save_architecture_result(
        self, architecture: dict[str, Any], output_file: str | None
    ) -> None:
        """Save architecture result to file if specified."""
        if not output_file:
            return

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(architecture, indent=2))
        architecture["output_file"] = str(output_path)

    async def _design_system(
        self, requirements: str, context: str = "", output_file: str | None = None
    ) -> dict[str, Any]:
        """Design system architecture."""
        if not requirements:
            return {"error": "requirements is required"}

        # Consult experts for architecture guidance
        expert_guidance = await self._consult_experts_for_design(requirements, context)
        expert_section = self._format_expert_guidance(expert_guidance)

        # Get Context7 documentation
        context7_docs = await self._get_context7_docs_for_design(requirements, context)
        context7_section = self._format_context7_docs(context7_docs)

        # Build prompt
        prompt = self._build_design_prompt(
            requirements, context, expert_section, context7_section
        )

        try:
            response = await self.mal.generate(
                prompt=prompt,
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.2,
            )

            architecture = {
                "requirements": requirements,
                "architecture": response,
                "components": [],
                "technology_stack": [],
                "data_flow": "",
            }

            # Save to file if specified
            self._save_architecture_result(architecture, output_file)

            result = {"success": True, "architecture": architecture}
            if expert_guidance:
                result["expert_guidance"] = expert_guidance
            return result
        except Exception as e:
            return {"error": f"Failed to design system: {str(e)}"}

    async def _create_diagram(
        self,
        architecture_description: str,
        diagram_type: str = "component",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """Create architecture diagram (text-based)."""
        if not architecture_description:
            return {"error": "architecture_description is required"}

        diagram_types = {
            "component": "component diagram showing system components and relationships",
            "sequence": "sequence diagram showing interactions over time",
            "deployment": "deployment diagram showing deployment architecture",
            "class": "class diagram showing object relationships",
            "data-flow": "data flow diagram showing data movement",
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
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.1,
            )

            diagram = {
                "type": diagram_type,
                "architecture": architecture_description,
                "diagram": response,
            }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(diagram["diagram"])
                diagram["output_file"] = str(output_path)

            return {"success": True, "diagram": diagram}
        except Exception as e:
            return {"error": f"Failed to create diagram: {str(e)}"}

    async def _select_technology(
        self,
        component_description: str,
        requirements: str = "",
        constraints: list[str] | None = None,
    ) -> dict[str, Any]:
        """Select technology stack for a component."""
        if constraints is None:
            constraints = []

        # Consult Software Architecture expert for technology selection
        tech_guidance = ""
        if self.expert_registry:
            try:
                tech_consultation = await self.expert_registry.consult(
                    query=f"Select technology stack for: {component_description}. Requirements: {requirements}. Constraints: {', '.join(constraints) if constraints else 'None'}",
                    domain="software-architecture",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="architect",
                )
                tech_guidance = tech_consultation.weighted_answer
            except Exception:
                logger.debug("Technology selection consultation failed", exc_info=True)

        # Use Context7 to get documentation for mentioned technologies
        context7_docs = {}
        if self.context7:
            full_text = (
                f"{component_description} {requirements} {' '.join(constraints)}"
            )
            if self.context7.should_use_context7(full_text):
                # Search for library mentions and get docs
                libraries = await self.context7.search_libraries(
                    component_description, limit=3
                )
                for lib_info in libraries:
                    lib_name = (
                        lib_info.get("id", "").split("/")[-1]
                        if isinstance(lib_info, dict)
                        else str(lib_info)
                    )
                    if lib_name:
                        doc = await self.context7.get_documentation(
                            lib_name, topic="overview"
                        )
                        if doc:
                            context7_docs[lib_name] = doc.get("content", "")[
                                :500
                            ]  # First 500 chars

        context7_section = ""
        if context7_docs:
            context7_section = "\n\nRelevant Technology Documentation from Context7:\n"
            for lib_name, doc_content in context7_docs.items():
                context7_section += f"\n{lib_name}:\n{doc_content[:300]}...\n"

        tech_guidance_section = (
            f"Architecture Expert Guidance:\n{tech_guidance}" if tech_guidance else ""
        )

        prompt = f"""Select an appropriate technology stack for the following component.

Component Description:
{component_description}

{f"Requirements: {requirements}" if requirements else ""}

{f"Constraints: {', '.join(constraints)}" if constraints else ""}

{tech_guidance_section}
{context7_section}

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
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.3,
            )

            technology_selection = {
                "component": component_description,
                "requirements": requirements,
                "constraints": constraints,
                "recommendations": response,
                "context7_docs_used": (
                    list(context7_docs.keys()) if context7_docs else []
                ),
            }

            return {"success": True, "technology_selection": technology_selection}
        except Exception as e:
            return {"error": f"Failed to select technology: {str(e)}"}

    async def _design_security(
        self, system_description: str, threat_model: str = ""
    ) -> dict[str, Any]:
        """Design security architecture."""
        if not system_description:
            return {"error": "system_description is required"}

        # Consult Security expert
        security_guidance = ""
        security_confidence = 0.0
        if self.expert_registry:
            try:
                security_consultation = await self.expert_registry.consult(
                    query=f"Design security architecture for: {system_description}. Threat model: {threat_model}",
                    domain="security",
                    include_all=True,
                    prioritize_builtin=True,
                    agent_id="architect",
                )
                security_guidance = security_consultation.weighted_answer
                security_confidence = security_consultation.confidence
            except Exception:
                logger.debug("Security architecture consultation failed", exc_info=True)

        security_guidance_section = (
            f"Security Expert Guidance:\n{security_guidance}"
            if security_guidance
            else ""
        )

        prompt = f"""Design a security architecture for the following system.

System Description:
{system_description}

{f"Threat Model: {threat_model}" if threat_model else ""}

{security_guidance_section}

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
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.2,
            )

            security_design = {
                "system": system_description,
                "threat_model": threat_model,
                "security_architecture": response,
            }

            result = {"success": True, "security_design": security_design}
            if security_guidance:
                result["expert_guidance"] = {
                    "security": security_guidance,
                    "confidence": security_confidence,
                }
            return result
        except Exception as e:
            return {"error": f"Failed to design security: {str(e)}"}

    async def _define_boundaries(
        self, system_description: str, context: str = ""
    ) -> dict[str, Any]:
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
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.2,
            )

            boundaries = {
                "system": system_description,
                "boundaries_and_interfaces": response,
            }

            return {"success": True, "boundaries": boundaries}
        except Exception as e:
            return {"error": f"Failed to define boundaries: {str(e)}"}
