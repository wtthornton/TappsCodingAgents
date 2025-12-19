"""
Designer Agent - API contracts, data models, UI/UX specifications.
"""

import json
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL
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

    def __init__(self, mal: MAL | None = None, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="designer", agent_name="Designer Agent", config=config
        )
        if config is None:
            config = load_config()
        self.config = config

        # Initialize MAL
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )

        # Expert registry will be initialized in activate
        self.expert_registry = None

        # Initialize Context7 helper
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

    async def activate(self, project_root: Path | None = None):
        """Activate the designer agent with expert support."""
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)

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

            return await self._design_api(requirements, api_type, output_file)

        elif command == "design-data-model":
            requirements = kwargs.get("requirements", "")
            data_source = kwargs.get("data_source", "")
            output_file = kwargs.get("output_file", None)

            return await self._design_data_model(requirements, data_source, output_file)

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
        if self.expert_registry:
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
            response = await self.mal.generate(
                prompt=prompt,
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.2,
            )

            api_design = {
                "api_type": api_type,
                "requirements": requirements,
                "specification": response,
                "endpoints": [],
                "schemas": {},
            }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(api_design, indent=2))
                api_design["output_file"] = str(output_path)

            return {"success": True, "api_design": api_design}
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
        if self.expert_registry:
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

        privacy_guidance_section = (
            f"Data Privacy Expert Guidance:\n{privacy_guidance}\n"
            if privacy_guidance
            else ""
        )

        prompt = f"""Design data models and schemas for the following requirements.

Requirements:
{requirements}

{f"Data Source: {data_source}" if data_source else ""}

{privacy_guidance_section}

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
            response = await self.mal.generate(
                prompt=prompt,
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.2,
            )

            data_model = {
                "requirements": requirements,
                "data_source": data_source,
                "models": response,
                "entities": [],
                "relationships": [],
            }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(data_model, indent=2))
                data_model["output_file"] = str(output_path)

            return {"success": True, "data_model": data_model}
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
        if self.expert_registry:
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
            response = await self.mal.generate(
                prompt=prompt,
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.3,
            )

            ui_design = {
                "feature": feature_description,
                "user_stories": user_stories,
                "specification": response,
                "screens": [],
                "interactions": [],
            }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(ui_design, indent=2))
                ui_design["output_file"] = str(output_path)

            return {"success": True, "ui_design": ui_design}
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
            response = await self.mal.generate(
                prompt=prompt,
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.2,
            )

            wireframe = {
                "type": wireframe_type,
                "screen": screen_description,
                "wireframe": response,
            }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(wireframe["wireframe"])
                wireframe["output_file"] = str(output_path)

            return {"success": True, "wireframe": wireframe}
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
        if self.expert_registry:
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
            response = await self.mal.generate(
                prompt=prompt,
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.3,
            )

            design_system = {
                "project": project_description,
                "brand_guidelines": brand_guidelines,
                "system": response,
                "colors": {},
                "typography": {},
                "components": [],
            }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(design_system, indent=2))
                design_system["output_file"] = str(output_path)

            return {"success": True, "design_system": design_system}
        except Exception as e:
            return {"error": f"Failed to define design system: {str(e)}"}
