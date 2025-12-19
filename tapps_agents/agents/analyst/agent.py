"""
Analyst Agent - Requirements gathering, technical research, effort/risk estimation.
"""

import json
from pathlib import Path
from typing import Any

from ...context7.agent_integration import Context7AgentHelper, get_context7_helper
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.instructions import GenericInstruction


class AnalystAgent(BaseAgent):
    """
    Analyst Agent - Requirements gathering and technical research.

    Permissions: Read, Grep, Glob (read-only)

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify

    Responsibilities:
    - Gather requirements from stakeholders
    - Perform technical research
    - Estimate effort and risk
    - Competitive analysis
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(agent_id="analyst", agent_name="Analyst Agent", config=config)
        if config is None:
            config = load_config()
        self.config = config

        # Initialize Context7 helper
        self.context7: Context7AgentHelper | None = None
        if config:
            self.context7 = get_context7_helper(self, config)

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for analyst agent"""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*gather-requirements",
                "description": "Gather requirements from description or stakeholder input",
            },
            {
                "command": "*analyze-stakeholders",
                "description": "Analyze stakeholders and their needs",
            },
            {
                "command": "*research-technology",
                "description": "Research technology options for a requirement",
            },
            {
                "command": "*estimate-effort",
                "description": "Estimate effort and complexity for a feature",
            },
            {
                "command": "*assess-risk",
                "description": "Assess risks for a feature or project",
            },
            {
                "command": "*competitive-analysis",
                "description": "Perform competitive analysis",
            },
        ]

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute analyst agent command.

        Commands:
        - *gather-requirements: Gather requirements
        - *analyze-stakeholders: Analyze stakeholders
        - *research-technology: Research technology options
        - *estimate-effort: Estimate effort and complexity
        - *assess-risk: Assess risks
        - *competitive-analysis: Competitive analysis
        - *help: Show help
        """
        command = command.lstrip("*")

        if command == "help":
            return {"type": "help", "content": self.format_help()}

        elif command == "gather-requirements":
            description = kwargs.get("description", "")
            context = kwargs.get("context", "")
            output_file = kwargs.get("output_file", None)

            return await self._gather_requirements(description, context, output_file)

        elif command == "analyze-stakeholders":
            description = kwargs.get("description", "")
            stakeholders = kwargs.get("stakeholders", [])

            return await self._analyze_stakeholders(description, stakeholders)

        elif command == "research-technology":
            requirement = kwargs.get("requirement", "")
            context = kwargs.get("context", "")
            criteria = kwargs.get("criteria", [])

            return await self._research_technology(requirement, context, criteria)

        elif command == "estimate-effort":
            feature_description = kwargs.get("feature_description", "")
            context = kwargs.get("context", "")

            return await self._estimate_effort(feature_description, context)

        elif command == "assess-risk":
            feature_description = kwargs.get("feature_description", "")
            context = kwargs.get("context", "")

            return await self._assess_risk(feature_description, context)

        elif command == "competitive-analysis":
            product_description = kwargs.get("product_description", "")
            competitors = kwargs.get("competitors", [])

            return await self._competitive_analysis(product_description, competitors)

        else:
            return {"error": f"Unknown command: {command}"}

    async def _gather_requirements(
        self, description: str, context: str = "", output_file: str | None = None
    ) -> dict[str, Any]:
        """Gather requirements from description."""
        if not description:
            return {"error": "description is required"}

        # Build prompt
        prompt = f"""Analyze the following requirement description and extract detailed requirements.

Description:
{description}

{f"Context: {context}" if context else ""}

Please provide:
1. Functional Requirements (what the system should do)
2. Non-Functional Requirements (performance, security, scalability, etc.)
3. Technical Constraints
4. Assumptions
5. Open Questions

Format as structured JSON with sections."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="analyst",
            command="analyze-requirements",
            prompt=prompt,
            parameters={"description": description},
        )

        requirements = {
            "description": description,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(requirements, indent=2))
                requirements["output_file"] = str(output_path)

            return {"success": True, "requirements": requirements}
        except Exception as e:
            return {"error": f"Failed to gather requirements: {str(e)}"}

    async def _analyze_stakeholders(
        self, description: str, stakeholders: list[str] | None = None
    ) -> dict[str, Any]:
        """Analyze stakeholders and their needs."""
        if stakeholders is None:
            stakeholders = []

        prompt = f"""Analyze stakeholders for the following project/feature.

Description:
{description}

{f"Stakeholders: {', '.join(stakeholders)}" if stakeholders else "Identify key stakeholders."}

For each stakeholder, provide:
1. Role/Title
2. Interests/Concerns
3. Influence Level (High/Medium/Low)
4. Requirements/Priorities
5. Communication Preferences

Format as structured JSON."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="analyst",
            command="analyze-stakeholders",
            prompt=prompt,
            parameters={
                "description": description,
                "stakeholders": stakeholders,
            },
        )

        return {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }
        except Exception as e:
            return {"error": f"Failed to analyze stakeholders: {str(e)}"}

    async def _research_technology(
        self, requirement: str, context: str = "", criteria: list[str] | None = None
    ) -> dict[str, Any]:
        """Research technology options."""
        if criteria is None:
            criteria = [
                "performance",
                "scalability",
                "ease_of_use",
                "community_support",
            ]

        prompt = f"""Research technology options for the following requirement.

Requirement:
{requirement}

{f"Context: {context}" if context else ""}

Evaluation Criteria:
{', '.join(criteria)}

For each technology option, provide:
1. Name and Description
2. Pros and Cons
3. Evaluation against criteria
4. Use Case Fit
5. Learning Curve
6. Community/Ecosystem

Format as structured JSON with technology recommendations."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="analyst",
            command="research-technology",
            prompt=prompt,
            parameters={
                "requirement": requirement,
                "criteria": criteria,
            },
        )

        return {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }
        except Exception as e:
            return {"error": f"Failed to research technology: {str(e)}"}

    async def _estimate_effort(
        self, feature_description: str, context: str = ""
    ) -> dict[str, Any]:
        """Estimate effort and complexity."""
        prompt = f"""Estimate development effort and complexity for the following feature.

Feature Description:
{feature_description}

{f"Context: {context}" if context else ""}

Provide estimates for:
1. Complexity Level (1-5, where 5 is most complex)
2. Estimated Hours/Story Points
3. Breakdown by component/task
4. Dependencies
5. Skills Required
6. Uncertainty/Risk Factors

Format as structured JSON."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="analyst",
            command="estimate-effort",
            prompt=prompt,
            parameters={"feature": feature_description},
        )

        return {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }
        except Exception as e:
            return {"error": f"Failed to estimate effort: {str(e)}"}

    async def _assess_risk(
        self, feature_description: str, context: str = ""
    ) -> dict[str, Any]:
        """Assess risks for a feature."""
        prompt = f"""Assess risks for the following feature/project.

Feature Description:
{feature_description}

{f"Context: {context}" if context else ""}

Identify and assess:
1. Technical Risks (with probability and impact)
2. Schedule Risks
3. Resource Risks
4. Security Risks
5. Compliance Risks
6. Mitigation Strategies

Format as structured JSON with risk assessment."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="analyst",
            command="assess-risk",
            prompt=prompt,
            parameters={"feature": feature_description},
        )

        return {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }
        except Exception as e:
            return {"error": f"Failed to assess risk: {str(e)}"}

    async def _competitive_analysis(
        self, product_description: str, competitors: list[str] | None = None
    ) -> dict[str, Any]:
        """Perform competitive analysis."""
        if competitors is None:
            competitors = []

        prompt = f"""Perform competitive analysis for the following product.

Product Description:
{product_description}

{f"Competitors: {', '.join(competitors)}" if competitors else "Identify key competitors."}

For each competitor, analyze:
1. Product Features
2. Strengths and Weaknesses
3. Pricing Model
4. Market Position
5. Technology Stack
6. User Experience

Provide:
- Competitive Landscape Overview
- Differentiation Opportunities
- Market Gaps
- Recommendations

Format as structured JSON."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="analyst",
            command="competitive-analysis",
            prompt=prompt,
            parameters={
                "product": product_description,
                "competitors": competitors,
            },
        )

        return {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
        }
        except Exception as e:
            return {"error": f"Failed to perform competitive analysis: {str(e)}"}
