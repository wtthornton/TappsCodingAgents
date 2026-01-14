"""
Designer Agent - API contracts, data models, UI/UX specifications.
"""

import json
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction
from ...experts.agent_integration import ExpertSupportMixin


class DesignerAgent(BaseAgent, ExpertSupportMixin):
    """
    Designer Agent - API contracts, data models, UI/UX specifications.

    Permissions: Read, Write, Grep, Glob (no Edit, no Bash)

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify

    Responsibilities:
    - Design API contracts
    - Define data models
    - Create UI/UX specifications
    - Design wireframes (text-based)
    - Define design systems
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="designer", agent_name="Designer Agent", config=config
        )
        if config is None:
            config = load_config()
        self.config = config

        # Expert registry initialization (required due to multiple inheritance MRO issue)
        # BaseAgent.__init__() doesn't call super().__init__(), so ExpertSupportMixin.__init__()
        # is never called via MRO. We must manually initialize to avoid AttributeError.
        # The registry will be properly initialized in activate() via _initialize_expert_support()
        self.expert_registry: Any | None = None

        # Initialize Context7 helper
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the designer agent with expert support."""
        # Validate that expert_registry attribute exists (safety check)
        if not hasattr(self, 'expert_registry'):
            raise AttributeError(
                f"{self.__class__.__name__}.expert_registry not initialized. "
                "This should not happen if __init__() properly initializes the attribute."
            )
        await super().activate(project_root, offline_mode=offline_mode)
        await self._initialize_expert_support(project_root, offline_mode=offline_mode)

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for designer agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*design-api",
                "description": "Design API contracts and endpoints",
            },
            {
                "command": "*design-data-model",
                "description": "Design data models and schemas",
            },
            {"command": "*design-ui", "description": "Design UI/UX specifications"},
            {
                "command": "*create-wireframe",
                "description": "Create wireframe (text-based)",
            },
            {
                "command": "*define-design-system",
                "description": "Define design system (colors, typography, components)",
            },
            {
                "command": "*evaluate-design",
                "description": "Evaluate design quality and completeness",
            },
            {
                "command": "*validate-api-consistency",
                "description": "Validate API design consistency with project patterns",
            },
            {
                "command": "*validate-api-nfr",
                "description": "Validate API design against non-functional requirements",
            },
        ]

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute designer agent command.

        Commands:
        - *design-api: Design API contracts
        - *design-data-model: Design data models
        - *design-ui: Design UI/UX specifications
        - *create-wireframe: Create wireframe
        - *define-design-system: Define design system
        - *help: Show help
        """
        command = command.lstrip("*")

        if command == "help":
            return {"type": "help", "content": self.format_help()}

        elif command == "design-api":
            requirements = kwargs.get("requirements", "")
            api_type = kwargs.get("api_type", "REST")
            output_file = kwargs.get("output_file", None)
            generate_doc = kwargs.get("generate_doc", False) or kwargs.get("generate-doc", False)
            generate_code = kwargs.get("generate_code", False) or kwargs.get("generate-code", False)
            code_language = kwargs.get("code_language", "typescript") or kwargs.get("code-language", "typescript")
            output_format = kwargs.get("output_format", "markdown") or kwargs.get("output-format", "markdown")

            result = await self._design_api(requirements, api_type, output_file)
            
            # Generate document if requested
            if generate_doc:
                from ...core.document_generator import DocumentGenerator
                doc_generator = DocumentGenerator(project_root=self._project_root)
                
                # Determine output file if not provided
                if not output_file:
                    docs_dir = self._project_root / "docs" / "api"
                    docs_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = "api_design"
                    output_file = docs_dir / f"{safe_name}.{output_format if output_format != 'html' else 'html'}"
                
                # Generate document
                doc_path = doc_generator.generate_api_design_doc(
                    api_data=result,
                    output_file=output_file,
                    format=output_format,
                )
                
                result["document"] = {
                    "path": str(doc_path),
                    "format": output_format,
                }
            
            # Generate code if requested
            if generate_code:
                from ...core.code_generator import CodeGenerator
                code_generator = CodeGenerator(project_root=self._project_root)
                
                # Determine code output file
                if code_language == "typescript":
                    code_dir = self._project_root / "src" / "api" / "clients"
                    code_dir.mkdir(parents=True, exist_ok=True)
                    api_name = result.get("name", "ApiClient") or "ApiClient"
                    code_file = code_dir / f"{api_name}.ts"
                else:
                    code_dir = self._project_root / "src" / "api"
                    code_dir.mkdir(parents=True, exist_ok=True)
                    api_name = result.get("name", "api_client") or "api_client"
                    code_file = code_dir / f"{api_name}.py"
                
                # Generate API client code
                try:
                    code_path = code_generator.generate_api_client(
                        api_data=result,
                        output_file=code_file,
                        language=code_language,
                    )
                    
                    result["code"] = {
                        "path": str(code_path),
                        "language": code_language,
                    }
                except Exception as e:
                    result["code_error"] = str(e)
            
            return result

        elif command == "design-data-model":
            requirements = kwargs.get("requirements", "")
            data_source = kwargs.get("data_source", "")
            output_file = kwargs.get("output_file", None)
            generate_code = kwargs.get("generate_code", False) or kwargs.get("generate-code", False)
            code_language = kwargs.get("code_language", "typescript") or kwargs.get("code-language", "typescript")

            result = await self._design_data_model(requirements, data_source, output_file)
            
            # Generate code if requested
            if generate_code:
                from ...core.code_generator import CodeGenerator
                code_generator = CodeGenerator(project_root=self._project_root)
                
                # Determine code output file based on language
                if code_language == "typescript":
                    code_dir = self._project_root / "src" / "models"
                    code_dir.mkdir(parents=True, exist_ok=True)
                    model_name = result.get("name", "Model") or "Model"
                    code_file = code_dir / f"{model_name}.ts"
                    
                    # Generate TypeScript interface
                    try:
                        code_path = code_generator.generate_typescript_interface(
                            interface_data=result,
                            output_file=code_file,
                        )
                        result["code"] = {
                            "path": str(code_path),
                            "language": code_language,
                            "type": "interface",
                        }
                    except Exception as e:
                        result["code_error"] = str(e)
                elif code_language == "python":
                    code_dir = self._project_root / "src" / "models"
                    code_dir.mkdir(parents=True, exist_ok=True)
                    model_name = result.get("name", "model") or "model"
                    code_file = code_dir / f"{model_name}.py"
                    
                    # Generate Python class
                    try:
                        code_path = code_generator.generate_python_class(
                            class_data=result,
                            output_file=code_file,
                        )
                        result["code"] = {
                            "path": str(code_path),
                            "language": code_language,
                            "type": "class",
                        }
                    except Exception as e:
                        result["code_error"] = str(e)
            
            return result

        elif command == "design-ui":
            feature_description = kwargs.get("feature_description", "")
            user_stories = kwargs.get("user_stories", [])
            output_file = kwargs.get("output_file", None)

            return await self._design_ui(feature_description, user_stories, output_file)

        elif command == "create-wireframe":
            screen_description = kwargs.get("screen_description", "")
            wireframe_type = kwargs.get("wireframe_type", "page")
            output_file = kwargs.get("output_file", None)

            return await self._create_wireframe(
                screen_description, wireframe_type, output_file
            )

        elif command == "define-design-system":
            project_description = kwargs.get("project_description", "")
            brand_guidelines = kwargs.get("brand_guidelines", "")
            output_file = kwargs.get("output_file", None)

            return await self._define_design_system(
                project_description, brand_guidelines, output_file
            )

        elif command == "evaluate-design":
            design = kwargs.get("design", {})
            if isinstance(design, str):
                design_path = Path(design)
                if design_path.exists():
                    import json
                    design = json.loads(design_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Design file not found: {design}"}

            return await self._evaluate_design(design)

        elif command == "validate-api-consistency":
            api_design = kwargs.get("api_design", {})
            project_patterns = kwargs.get("project_patterns", {})

            if isinstance(api_design, str):
                api_path = Path(api_design)
                if api_path.exists():
                    import json
                    api_design = json.loads(api_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"API design file not found: {api_design}"}

            return await self._validate_api_consistency(api_design, project_patterns)

        elif command == "validate-api-nfr":
            api_design = kwargs.get("api_design", {})
            nfr_requirements = kwargs.get("nfr_requirements", {})

            if isinstance(api_design, str):
                api_path = Path(api_design)
                if api_path.exists():
                    import json
                    api_design = json.loads(api_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"API design file not found: {api_design}"}

            if isinstance(nfr_requirements, str):
                nfr_path = Path(nfr_requirements)
                if nfr_path.exists():
                    import json
                    nfr_requirements = json.loads(nfr_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"NFR requirements file not found: {nfr_requirements}"}

            return await self._validate_api_nfr(api_design, nfr_requirements)

        else:
            return {"error": f"Unknown command: {command}"}

    async def _design_api(
        self,
        requirements: str,
        api_type: str = "REST",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """Design API contracts and endpoints."""
        if not requirements:
            return {"error": "requirements is required"}

        # Consult Data Privacy expert for API design
        privacy_guidance = ""
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            privacy_consultation = await self.expert_registry.consult(
                query=f"Provide data privacy and security best practices for designing a {api_type} API with the following requirements: {requirements[:500]}",
                domain="data-privacy-compliance",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                privacy_consultation.confidence
                >= privacy_consultation.confidence_threshold
            ):
                privacy_guidance = privacy_consultation.weighted_answer

        privacy_guidance_section = (
            f"Data Privacy Expert Guidance:\n{privacy_guidance}\n"
            if privacy_guidance
            else ""
        )

        prompt = f"""Design an API contract for the following requirements.

Requirements:
{requirements}

API Type: {api_type}

{privacy_guidance_section}

Provide a comprehensive API design including:
1. API Overview and Purpose
2. Base URL and Versioning Strategy
3. Endpoints (with HTTP methods)
4. Request/Response Schemas (JSON format)
5. Authentication & Authorization
6. Error Handling (error codes and messages)
7. Rate Limiting
8. Pagination (if applicable)
9. Query Parameters
10. Example Requests/Responses

Format as structured JSON with OpenAPI-style specification."""

        try:
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="designer",
                command="design-api",
                prompt=prompt,
                parameters={
                    "api_type": api_type,
                    "requirements": requirements,
                    "output_file": str(output_file) if output_file else None,
                },
            )

            return {
                "success": True,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
            }
        except Exception as e:
            return {"error": f"Failed to design API: {str(e)}"}

    async def _design_data_model(
        self,
        requirements: str,
        data_source: str = "",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """Design data models and schemas."""
        if not requirements:
            return {"error": "requirements is required"}

        # Consult Data Privacy expert for data model design
        privacy_guidance = ""
        database_guidance = ""
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            privacy_consultation = await self.expert_registry.consult(
                query=f"Provide data privacy and security best practices for designing data models with the following requirements: {requirements[:500]}",
                domain="data-privacy-compliance",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                privacy_consultation.confidence
                >= privacy_consultation.confidence_threshold
            ):
                privacy_guidance = privacy_consultation.weighted_answer
            
            # Consult Database expert for time-series/InfluxDB patterns (Phase 1.2: HomeIQ Support)
            requirements_lower = requirements.lower()
            if any(keyword in requirements_lower for keyword in ["influxdb", "time-series", "time series", "iot", "sensor", "metrics"]):
                database_consultation = await self.expert_registry.consult(
                    query=f"Provide database design patterns for time-series data modeling with the following requirements: {requirements[:500]}",
                    domain="database-data-management",
                    agent_id=self.agent_id,
                    prioritize_builtin=True,
                )
                if (
                    database_consultation.confidence
                    >= database_consultation.confidence_threshold
                ):
                    database_guidance = database_consultation.weighted_answer

        privacy_guidance_section = (
            f"Data Privacy Expert Guidance:\n{privacy_guidance}\n"
            if privacy_guidance
            else ""
        )
        database_guidance_section = (
            f"Database Expert Guidance (Time-Series/InfluxDB):\n{database_guidance}\n"
            if database_guidance
            else ""
        )

        prompt = f"""Design data models and schemas for the following requirements.

Requirements:
{requirements}

{f"Data Source: {data_source}" if data_source else ""}

{privacy_guidance_section}
{database_guidance_section}

Provide comprehensive data model design including:
1. Entity Relationship Overview
2. Data Models/Entities (with attributes)
3. Data Types and Constraints
4. Relationships (one-to-one, one-to-many, many-to-many)
5. Indexes and Keys
6. Data Validation Rules
7. Data Migration Considerations
8. Schema Definition (JSON Schema or similar)

Format as structured JSON with detailed data model specification."""

        try:
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="designer",
                command="design-data-model",
                prompt=prompt,
                parameters={
                    "requirements": requirements,
                    "data_source": data_source,
                    "output_file": str(output_file) if output_file else None,
                },
            )

            return {
                "success": True,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
            }
        except Exception as e:
            return {"error": f"Failed to design data model: {str(e)}"}

    async def _design_ui(
        self,
        feature_description: str,
        user_stories: list[str] | None = None,
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """Design UI/UX specifications."""
        if not feature_description:
            return {"error": "feature_description is required"}

        if user_stories is None:
            user_stories = []

        # Consult UX and Accessibility experts
        ux_guidance = ""
        accessibility_guidance = ""
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            ux_consultation = await self.expert_registry.consult(
                query=f"Provide UX best practices for designing UI for: {feature_description[:500]}",
                domain="user-experience",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if ux_consultation.confidence >= ux_consultation.confidence_threshold:
                ux_guidance = ux_consultation.weighted_answer

            accessibility_consultation = await self.expert_registry.consult(
                query=f"Provide accessibility best practices for designing UI for: {feature_description[:500]}",
                domain="accessibility",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                accessibility_consultation.confidence
                >= accessibility_consultation.confidence_threshold
            ):
                accessibility_guidance = accessibility_consultation.weighted_answer

        ux_guidance_section = (
            f"UX Expert Guidance:\n{ux_guidance}\n" if ux_guidance else ""
        )
        accessibility_guidance_section = (
            f"Accessibility Expert Guidance:\n{accessibility_guidance}\n"
            if accessibility_guidance
            else ""
        )

        prompt = f"""Design UI/UX specifications for the following feature.

Feature Description:
{feature_description}

{f"User Stories: {chr(10).join(f'- {story}' for story in user_stories)}" if user_stories else ""}

{ux_guidance_section}
{accessibility_guidance_section}

Provide comprehensive UI/UX design including:
1. User Journey/Flow
2. Screen Layouts
3. User Interactions
4. Navigation Structure
5. Accessibility Requirements
6. Responsive Design Considerations
7. UI Components Needed
8. User Feedback Mechanisms
9. Error States and Handling
10. Loading States

Format as structured JSON with detailed UI/UX specification."""

        try:
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="designer",
                command="design-ui",
                prompt=prompt,
                parameters={
                    "feature": feature_description,
                    "user_stories": user_stories,
                    "output_file": str(output_file) if output_file else None,
                },
            )

            return {
                "success": True,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
            }
        except Exception as e:
            return {"error": f"Failed to design UI: {str(e)}"}

    async def _create_wireframe(
        self,
        screen_description: str,
        wireframe_type: str = "page",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """Create wireframe (text-based)."""
        if not screen_description:
            return {"error": "screen_description is required"}

        prompt = f"""Create a text-based wireframe for the following screen.

Screen Description:
{screen_description}

Wireframe Type: {wireframe_type}

Provide a clear, ASCII/text-based wireframe that can be rendered in markdown or plain text.
Use boxes, lines, and labels to represent:
- Layout structure
- UI components
- Content areas
- Navigation elements
- Interactive elements

Include:
1. Wireframe (ASCII/text format)
2. Component Labels
3. Layout Explanation
4. User Flow Notes

Format as structured content."""

        try:
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="designer",
                command="create-wireframe",
                prompt=prompt,
                parameters={
                    "type": wireframe_type,
                    "screen": screen_description,
                    "output_file": str(output_file) if output_file else None,
                },
            )

            return {
                "success": True,
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
            }
        except Exception as e:
            return {"error": f"Failed to create wireframe: {str(e)}"}

    async def _define_design_system(
        self,
        project_description: str,
        brand_guidelines: str = "",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """Define design system (colors, typography, components)."""
        if not project_description:
            return {"error": "project_description is required"}

        # Consult UX and Accessibility experts
        ux_guidance = ""
        accessibility_guidance = ""
        # Use defensive check to ensure attribute exists (safety for MRO issue)
        if hasattr(self, 'expert_registry') and self.expert_registry:
            ux_consultation = await self.expert_registry.consult(
                query=f"Provide UX best practices for defining a design system for: {project_description[:500]}",
                domain="user-experience",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if ux_consultation.confidence >= ux_consultation.confidence_threshold:
                ux_guidance = ux_consultation.weighted_answer

            accessibility_consultation = await self.expert_registry.consult(
                query=f"Provide accessibility best practices for defining a design system for: {project_description[:500]}",
                domain="accessibility",
                agent_id=self.agent_id,
                prioritize_builtin=True,
            )
            if (
                accessibility_consultation.confidence
                >= accessibility_consultation.confidence_threshold
            ):
                accessibility_guidance = accessibility_consultation.weighted_answer

        ux_guidance_section = (
            f"UX Expert Guidance:\n{ux_guidance}\n" if ux_guidance else ""
        )
        accessibility_guidance_section = (
            f"Accessibility Expert Guidance:\n{accessibility_guidance}\n"
            if accessibility_guidance
            else ""
        )

        prompt = f"""Define a design system for the following project.

Project Description:
{project_description}

{f"Brand Guidelines: {brand_guidelines}" if brand_guidelines else ""}

{ux_guidance_section}
{accessibility_guidance_section}

Provide comprehensive design system including:
1. Color Palette (primary, secondary, accent, neutral)
2. Typography (font families, sizes, weights, line heights)
3. Spacing System (margins, padding, grid)
4. Component Library (buttons, forms, cards, etc.)
5. Iconography
6. Imagery Guidelines
7. Animation/Transition Guidelines
8. Accessibility Standards
9. Design Tokens

Format as structured JSON with detailed design system specification."""

        try:
            # Prepare instruction for Cursor Skills
            instruction = GenericInstruction(
                agent_name="designer",
                command="create-design-system",
                prompt=prompt,
                parameters={
                    "project": project_description,
                    "brand_guidelines": brand_guidelines,
                    "output_file": str(output_file) if output_file else None,
                },
            )

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(design_system, indent=2))
                design_system["output_file"] = str(output_path)

            return {"success": True, "design_system": design_system}
        except Exception as e:
            return {"error": f"Failed to define design system: {str(e)}"}

    async def _evaluate_design(self, design: dict[str, Any]) -> dict[str, Any]:
        """Evaluate design quality and completeness."""
        # Basic evaluation - can be enhanced with more sophisticated analysis
        score = {
            "overall": 75.0,  # Placeholder
            "endpoints_defined": len(design.get("endpoints", [])) > 0,
            "schemas_defined": len(design.get("schemas", [])) > 0,
            "authentication_specified": "auth" in str(design).lower(),
            "documentation_present": "description" in str(design).lower() or "docs" in str(design).lower(),
        }

        return {
            "success": True,
            "score": score,
            "design": design,
        }

    async def _validate_api_consistency(
        self, api_design: dict[str, Any], project_patterns: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Validate API design consistency with project patterns."""
        from ...core.design_validator import DesignValidator

        validator = DesignValidator()
        result = validator.validate_api_consistency(api_design, project_patterns)

        return {
            "success": True,
            "is_consistent": result.is_consistent,
            "violations": result.violations,
            "pattern_deviations": result.pattern_deviations,
            "naming_inconsistencies": result.naming_inconsistencies,
            "recommendations": result.recommendations,
        }

    async def _validate_api_nfr(
        self, api_design: dict[str, Any], nfr_requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate API design against non-functional requirements."""
        from ...core.nfr_validator import NFRValidator

        validator = NFRValidator()
        result = validator.validate_api_nfr(api_design, nfr_requirements)

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
            "recommendations": result.recommendations,
        }
