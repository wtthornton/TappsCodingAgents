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
from ...core.instructions import GenericInstruction
from ...experts.agent_integration import ExpertSupportMixin

logger = logging.getLogger(__name__)


class ArchitectAgent(BaseAgent, ExpertSupportMixin):
    """
    Architect Agent - System and security architecture design.

    Permissions: Read, Write, Grep, Glob (no Edit, no Bash)

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify

    Responsibilities:
    - Design system architecture
    - Create architecture diagrams (text-based)
    - Select technologies
    - Design security architecture
    - Define system boundaries
    """

    def __init__(
        self,
        config: ProjectConfig | None = None,
        expert_registry: Any | None = None,
    ):
        super().__init__(
            agent_id="architect", agent_name="Architect Agent", config=config
        )
        if config is None:
            config = load_config()
        self.config = config

        # Initialize Context7 helper
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

        # Expert registry initialization (required due to multiple inheritance MRO issue)
        # BaseAgent.__init__() doesn't call super().__init__(), so ExpertSupportMixin.__init__()
        # is never called via MRO. We must manually initialize to avoid AttributeError.
        # The registry will be properly initialized in activate() via _initialize_expert_support()
        self.expert_registry: Any | None = None
        # Allow manual override if provided (for testing or special cases)
        if expert_registry:
            self.expert_registry = expert_registry

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the architect agent with expert support."""
        # Validate that expert_registry attribute exists (safety check)
        if not hasattr(self, 'expert_registry'):
            raise AttributeError(
                f"{self.__class__.__name__}.expert_registry not initialized. "
                "This should not happen if __init__() properly initializes the attribute."
            )
        await super().activate(project_root, offline_mode=offline_mode)
        # Initialize expert support via mixin
        await self._initialize_expert_support(project_root, offline_mode=offline_mode)

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
            {
                "command": "*evaluate-architecture",
                "description": "Evaluate architecture quality and completeness",
            },
            {
                "command": "*validate-requirements-alignment",
                "description": "Validate architecture covers all requirements",
            },
            {
                "command": "*review-architecture",
                "description": "Structured review of architecture with checklist",
            },
            {
                "command": "*validate-nfr",
                "description": "Validate architecture against non-functional requirements",
            },
            {
                "command": "*generate-diagram",
                "description": "Generate Mermaid or PlantUML diagram from architecture",
            },
            {
                "command": "*export-diagram",
                "description": "Export architecture diagram to file (Mermaid/PlantUML)",
            },
            {
                "command": "*suggest-patterns",
                "description": "Suggest design patterns based on requirements",
            },
            {
                "command": "*detect-patterns",
                "description": "Detect architecture patterns from project layout (§3.7)",
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
            output_file = kwargs.get("output_file")
            generate_doc = kwargs.get("generate_doc", False) or kwargs.get("generate-doc", False)
            generate_code = kwargs.get("generate_code", False) or kwargs.get("generate-code", False)
            code_language = kwargs.get("code_language", "python") or kwargs.get("code-language", "python")
            output_format = kwargs.get("output_format", "markdown") or kwargs.get("output-format", "markdown")

            result = await self._design_system(requirements, context, output_file)
            
            # Generate document if requested
            if generate_doc:
                from ...core.document_generator import DocumentGenerator
                doc_generator = DocumentGenerator(project_root=self._project_root)
                
                # Determine output file if not provided
                if not output_file:
                    docs_dir = self._project_root / "docs" / "architecture"
                    docs_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = "architecture_design"
                    output_file = docs_dir / f"{safe_name}.{output_format if output_format != 'html' else 'html'}"
                
                # Generate document
                doc_path = doc_generator.generate_architecture_doc(
                    architecture_data=result,
                    output_file=output_file,
                    format=output_format,
                )
                
                result["document"] = {
                    "path": str(doc_path),
                    "format": output_format,
                }
            
            # Generate code skeletons if requested
            if generate_code and "components" in str(result):
                from ...core.code_generator import CodeGenerator
                code_generator = CodeGenerator(project_root=self._project_root)
                
                # Try to extract components from result
                components = result.get("components", [])
                if not components and "instruction" in result:
                    # If we have instruction, we can't generate code yet
                    # But we can prepare for it
                    result["code_generation_ready"] = False
                    result["code_generation_note"] = "Code generation requires executed architecture design"
                elif components:
                    # Generate service skeletons for each component
                    generated_files = []
                    code_dir = self._project_root / "src" / "services"
                    code_dir.mkdir(parents=True, exist_ok=True)
                    
                    for component in components:
                        component_name = component.get("name", "Service") or "Service"
                        safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in component_name)
                        code_file = code_dir / f"{safe_name.lower()}.py"
                        
                        try:
                            code_path = code_generator.generate_python_class(
                                class_data={
                                    "name": component_name,
                                    "description": component.get("description", ""),
                                    "properties": component.get("properties", []),
                                },
                                output_file=code_file,
                            )
                            generated_files.append(str(code_path))
                        except Exception as e:
                            logger.warning(f"Failed to generate code for component {component_name}: {e}")
                    
                    if generated_files:
                        result["code"] = {
                            "files": generated_files,
                            "language": code_language,
                            "type": "service_skeletons",
                        }
            
            return result

        elif command == "create-diagram":
            architecture_description = kwargs.get("architecture_description", "")
            diagram_type = kwargs.get("diagram_type", "component")
            output_file = kwargs.get("output_file")

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

        elif command == "evaluate-architecture":
            architecture = kwargs.get("architecture", {})
            if isinstance(architecture, str):
                arch_path = Path(architecture)
                if arch_path.exists():
                    import json
                    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Architecture file not found: {architecture}"}

            return await self._evaluate_architecture(architecture)

        elif command == "validate-requirements-alignment":
            architecture = kwargs.get("architecture", {})
            requirements = kwargs.get("requirements", {})

            if isinstance(architecture, str):
                arch_path = Path(architecture)
                if arch_path.exists():
                    import json
                    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Architecture file not found: {architecture}"}

            if isinstance(requirements, str):
                req_path = Path(requirements)
                if req_path.exists():
                    import json
                    requirements = json.loads(req_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Requirements file not found: {requirements}"}

            return await self._validate_requirements_alignment(architecture, requirements)

        elif command == "review-architecture":
            architecture = kwargs.get("architecture", {})
            if isinstance(architecture, str):
                arch_path = Path(architecture)
                if arch_path.exists():
                    import json
                    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Architecture file not found: {architecture}"}

            return await self._review_architecture(architecture)

        elif command == "validate-nfr":
            architecture = kwargs.get("architecture", {})
            nfr_requirements = kwargs.get("nfr_requirements", {})

            if isinstance(architecture, str):
                arch_path = Path(architecture)
                if arch_path.exists():
                    import json
                    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Architecture file not found: {architecture}"}

            if isinstance(nfr_requirements, str):
                nfr_path = Path(nfr_requirements)
                if nfr_path.exists():
                    import json
                    nfr_requirements = json.loads(nfr_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"NFR requirements file not found: {nfr_requirements}"}

            return await self._validate_nfr(architecture, nfr_requirements)

        elif command == "generate-diagram":
            architecture = kwargs.get("architecture", {})
            diagram_type = kwargs.get("diagram_type", "component")  # component, sequence, class
            format_type = kwargs.get("format", "mermaid")  # mermaid, plantuml

            if isinstance(architecture, str):
                arch_path = Path(architecture)
                if arch_path.exists():
                    import json
                    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Architecture file not found: {architecture}"}

            return await self._generate_diagram(architecture, diagram_type, format_type)

        elif command == "export-diagram":
            architecture = kwargs.get("architecture", {})
            diagram_type = kwargs.get("diagram_type", "component")
            format_type = kwargs.get("format", "mermaid")
            output_file = kwargs.get("output_file")

            if isinstance(architecture, str):
                arch_path = Path(architecture)
                if arch_path.exists():
                    import json
                    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Architecture file not found: {architecture}"}

            if not output_file:
                return {"error": "output_file is required for export-diagram"}

            return await self._export_diagram(architecture, diagram_type, format_type, output_file)

        elif command == "suggest-patterns":
            requirements = kwargs.get("requirements", {})
            context = kwargs.get("context", {})

            if isinstance(requirements, str):
                req_path = Path(requirements)
                if req_path.exists():
                    import json
                    requirements = json.loads(req_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Requirements file not found: {requirements}"}

            return await self._suggest_patterns(requirements, context)

        elif command == "detect-patterns":
            from .pattern_detector import detect_architecture_patterns

            root = kwargs.get("path") or getattr(self, "_project_root", None) or Path.cwd()
            root = Path(root).resolve()
            patterns = detect_architecture_patterns(root)
            return {"patterns": patterns, "project_root": str(root)}

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

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="architect",
            command="design-system",
            prompt=prompt,
            parameters={
                "requirements": requirements,
                "output_file": str(output_file) if output_file else None,
            },
        )

        result = {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }
        if expert_guidance:
            result["expert_guidance"] = expert_guidance
        return result

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

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="architect",
            command="create-diagram",
            prompt=prompt,
            parameters={
                "diagram_type": diagram_type,
                "architecture": architecture_description,
                "output_file": str(output_file) if output_file else None,
            },
        )

        return {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }

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
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
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
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="architect",
                command="select-technology",
                prompt=prompt,
                parameters={
                    "component": component_description,
                    "requirements": requirements,
                    "constraints": constraints,
                },
            )

            return {
                "success": True,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
            }
        except Exception as e:
            return {"error": f"Failed to select technology: {e!s}"}

    async def _design_security(
        self, system_description: str, threat_model: str = ""
    ) -> dict[str, Any]:
        """Design security architecture."""
        if not system_description:
            return {"error": "system_description is required"}

        # Consult Security expert
        security_guidance = ""
        security_confidence = 0.0
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
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
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="architect",
                command="design-security",
                prompt=prompt,
                parameters={
                    "system": system_description,
                    "threat_model": threat_model,
                },
            )

            result = {
                "success": True,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
            }
            if security_guidance:
                result["expert_guidance"] = {
                    "security": security_guidance,
                    "confidence": security_confidence,
                }
            return result
        except Exception as e:
            return {"error": f"Failed to design security: {e!s}"}

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
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="architect",
                command="define-boundaries",
                prompt=prompt,
                parameters={
                    "system": system_description,
                    "context": context,
                },
            )

            return {
                "success": True,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
            }
        except Exception as e:
            return {"error": f"Failed to define boundaries: {e!s}"}

    async def _evaluate_architecture(self, architecture: dict[str, Any]) -> dict[str, Any]:
        """Evaluate architecture quality and completeness."""
        # Basic evaluation - can be enhanced with more sophisticated analysis
        score = {
            "overall": 75.0,  # Placeholder - would use actual evaluation logic
            "components_defined": len(architecture.get("components", [])) > 0,
            "patterns_identified": len(architecture.get("patterns", [])) > 0,
            "security_addressed": "security" in str(architecture).lower(),
            "scalability_addressed": "scal" in str(architecture).lower() or "scale" in str(architecture).lower(),
        }

        return {
            "success": True,
            "score": score,
            "architecture": architecture,
        }

    async def _validate_requirements_alignment(
        self, architecture: dict[str, Any], requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate architecture covers all requirements."""
        from ...core.design_validator import DesignValidator

        validator = DesignValidator()
        result = validator.validate_requirements_alignment(architecture, requirements)

        return {
            "success": True,
            "is_valid": result.is_valid,
            "requirements_coverage": result.requirements_coverage,
            "missing_requirements": result.missing_requirements,
            "pattern_violations": result.pattern_violations,
            "security_issues": result.security_issues,
            "scalability_concerns": result.scalability_concerns,
            "recommendations": result.recommendations,
        }

    async def _review_architecture(self, architecture: dict[str, Any]) -> dict[str, Any]:
        """Structured review of architecture with checklist."""
        from ...core.review_checklists import ArchitectureReviewChecklist

        checklist = ArchitectureReviewChecklist()
        result = checklist.review(architecture)

        return {
            "success": True,
            "overall_score": result.overall_score,
            "items_checked": result.items_checked,
            "items_total": result.items_total,
            "critical_issues": result.critical_issues,
            "high_issues": result.high_issues,
            "medium_issues": result.medium_issues,
            "low_issues": result.low_issues,
            "recommendations": result.recommendations,
            "checklist_items": [
                {
                    "category": item.category,
                    "item": item.item,
                    "checked": item.checked,
                    "severity": item.severity,
                    "notes": item.notes,
                }
                for item in result.checklist_items
            ],
        }

    async def _validate_nfr(
        self, architecture: dict[str, Any], nfr_requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate architecture against non-functional requirements."""
        from ...core.nfr_validator import NFRValidator

        validator = NFRValidator()
        result = validator.validate_architecture_nfr(architecture, nfr_requirements)

        return {
            "success": True,
            "is_valid": result.is_valid,
            "overall_score": result.overall_score,
            "security_score": result.security_score,
            "performance_score": result.performance_score,
            "reliability_score": result.reliability_score,
            "maintainability_score": result.maintainability_score,
            "security_issues": result.security_issues,
            "performance_issues": result.performance_issues,
            "reliability_issues": result.reliability_issues,
            "maintainability_issues": result.maintainability_issues,
            "recommendations": result.recommendations,
        }

    async def _generate_diagram(
        self, architecture: dict[str, Any], diagram_type: str, format_type: str
    ) -> dict[str, Any]:
        """Generate Mermaid or PlantUML diagram from architecture."""
        from ...core.diagram_generator import DiagramGenerator

        generator = DiagramGenerator()

        if format_type == "mermaid":
            if diagram_type == "component":
                diagram_code = generator.generate_mermaid_component_diagram(architecture)
            elif diagram_type == "sequence":
                interactions = architecture.get("interactions", [])
                diagram_code = generator.generate_mermaid_sequence_diagram(interactions)
            elif diagram_type == "class":
                classes = architecture.get("classes", [])
                diagram_code = generator.generate_mermaid_class_diagram(classes)
            else:
                return {"error": f"Unsupported diagram type: {diagram_type}. Use: component, sequence, class"}

        elif format_type == "plantuml":
            if diagram_type == "component":
                diagram_code = generator.generate_plantuml_component_diagram(architecture)
            else:
                return {"error": "PlantUML only supports component diagrams currently"}

        else:
            return {"error": f"Unsupported format: {format_type}. Use: mermaid, plantuml"}

        return {
            "success": True,
            "diagram_code": diagram_code,
            "format": format_type,
            "diagram_type": diagram_type,
        }

    async def _export_diagram(
        self, architecture: dict[str, Any], diagram_type: str, format_type: str, output_file: str
    ) -> dict[str, Any]:
        """Export architecture diagram to file."""
        from ...core.diagram_generator import DiagramGenerator

        generator = DiagramGenerator()

        # Generate diagram
        result = await self._generate_diagram(architecture, diagram_type, format_type)
        if "error" in result:
            return result

        diagram_code = result["diagram_code"]

        # Export to file
        output_path = Path(output_file)
        generator.export_to_file(diagram_code, output_path, format_type)

        return {
            "success": True,
            "output_file": str(output_path),
            "format": format_type,
            "diagram_type": diagram_type,
        }

    async def _suggest_patterns(self, requirements: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Suggest design patterns based on requirements."""
        from ...core.pattern_library import DesignPatternLibrary

        library = DesignPatternLibrary()
        suggestions = library.suggest_patterns(requirements, context)

        return {
            "success": True,
            "suggestions": suggestions,
            "total_patterns_available": len(library.patterns),
        }

    async def close(self) -> None:
        """Cleanup resources."""
        await super().close()
        # Context7 helper cleanup if needed
        # (Context7AgentHelper doesn't currently require explicit cleanup)
        # Design cache cleanup would go here if we add caching in the future