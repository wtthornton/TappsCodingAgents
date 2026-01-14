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
            {
                "command": "*analyze-prompt",
                "description": "Analyze prompt for intent, scope, domains, and workflow type",
            },
            {
                "command": "*evaluate-requirements",
                "description": "Evaluate requirements quality and completeness",
            },
            {
                "command": "*validate-requirements",
                "description": "Validate requirements for completeness and quality",
            },
            {
                "command": "*trace-requirements",
                "description": "Create traceability matrix linking requirements to stories/tests",
            },
            {
                "command": "*review-requirements",
                "description": "Structured review of requirements with checklist",
            },
            {
                "command": "*analyze-change-impact",
                "description": "Analyze impact of requirement changes on stories/designs/implementation",
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
        - *analyze-prompt: Analyze prompt for intent, scope, domains, and workflow type
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

        elif command == "analyze-prompt":
            description = kwargs.get("description", "")
            context = kwargs.get("context", "")

            return await self._analyze_prompt(description, context)

        elif command == "evaluate-requirements":
            requirements = kwargs.get("requirements", {})
            if isinstance(requirements, str):
                # Try to load from file
                req_path = Path(requirements)
                if req_path.exists():
                    import json
                    requirements = json.loads(req_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Requirements file not found: {requirements}"}

            return await self._evaluate_requirements(requirements)

        elif command == "validate-requirements":
            requirements = kwargs.get("requirements", {})
            if isinstance(requirements, str):
                # Try to load from file
                req_path = Path(requirements)
                if req_path.exists():
                    import json
                    requirements = json.loads(req_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Requirements file not found: {requirements}"}

            return await self._validate_requirements(requirements)

        elif command == "trace-requirements":
            requirements = kwargs.get("requirements", {})
            stories = kwargs.get("stories", [])
            output_file = kwargs.get("output_file", None)

            return await self._trace_requirements(requirements, stories, output_file)

        elif command == "review-requirements":
            requirements = kwargs.get("requirements", {})
            if isinstance(requirements, str):
                req_path = Path(requirements)
                if req_path.exists():
                    import json
                    requirements = json.loads(req_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Requirements file not found: {requirements}"}

            return await self._review_requirements(requirements)

        elif command == "analyze-change-impact":
            old_requirements = kwargs.get("old_requirements", {})
            new_requirements = kwargs.get("new_requirements", {})

            if isinstance(old_requirements, str):
                old_path = Path(old_requirements)
                if old_path.exists():
                    import json
                    old_requirements = json.loads(old_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"Old requirements file not found: {old_requirements}"}

            if isinstance(new_requirements, str):
                new_path = Path(new_requirements)
                if new_path.exists():
                    import json
                    new_requirements = json.loads(new_path.read_text(encoding="utf-8"))
                else:
                    return {"error": f"New requirements file not found: {new_requirements}"}

            traceability_file = kwargs.get("traceability_file", None)
            return await self._analyze_change_impact(old_requirements, new_requirements, traceability_file)

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

        try:
            # For CLI mode, use LLM to generate requirements
            # For Cursor mode, return instruction for skill execution
            from ...core.runtime_mode import is_cursor_mode
            
            if is_cursor_mode():
                # Cursor mode: return instruction
                requirements = {
                    "description": description,
                    "instruction": instruction.to_dict(),
                    "skill_command": instruction.to_skill_command(),
                }
            else:
                # CLI mode: generate requirements using LLM
                from ...core.mal import MAL
                mal = MAL()
                await self.activate()
                
                response = await mal.generate(
                    prompt=prompt,
                    system_prompt="You are a requirements analyst. Extract and structure requirements from descriptions.",
                )
                
                # Parse JSON response
                try:
                    import json as json_lib
                    requirements_data = json_lib.loads(response)
                except (json_lib.JSONDecodeError, ValueError):
                    # If not JSON, structure it manually
                    requirements_data = {
                        "functional_requirements": [],
                        "non_functional_requirements": [],
                        "technical_constraints": [],
                        "assumptions": [],
                        "open_questions": [],
                    }
                
                # Generate markdown document
                markdown_content = self._format_requirements_markdown(
                    description=description,
                    context=context,
                    requirements_data=requirements_data,
                )
                
                requirements = {
                    "description": description,
                    "context": context,
                    "functional_requirements": requirements_data.get("functional_requirements", []),
                    "non_functional_requirements": requirements_data.get("non_functional_requirements", []),
                    "technical_constraints": requirements_data.get("technical_constraints", []),
                    "assumptions": requirements_data.get("assumptions", []),
                    "open_questions": requirements_data.get("open_questions", []),
                    "markdown": markdown_content,
                }
            
            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save markdown if available, otherwise save JSON
                if "markdown" in requirements:
                    output_path.write_text(requirements["markdown"], encoding="utf-8")
                else:
                    output_path.write_text(json.dumps(requirements, indent=2), encoding="utf-8")
                
                requirements["output_file"] = str(output_path)

            return {"success": True, "requirements": requirements}
        except Exception as e:
            return {"error": f"Failed to gather requirements: {str(e)}"}
    
    def _format_requirements_markdown(
        self,
        description: str,
        context: str,
        requirements_data: dict[str, Any],
    ) -> str:
        """Format requirements as markdown document."""
        lines = [
            f"# Requirements: {description}",
            "",
            "## Overview",
            "",
            description,
            "",
        ]
        
        if context:
            lines.extend([
                "## Context",
                "",
                context,
                "",
            ])
        
        # Functional Requirements
        func_reqs = requirements_data.get("functional_requirements", [])
        if func_reqs:
            lines.extend([
                "## Functional Requirements",
                "",
            ])
            for i, req in enumerate(func_reqs, 1):
                if isinstance(req, dict):
                    req_text = req.get("requirement", req.get("description", str(req)))
                else:
                    req_text = str(req)
                lines.append(f"{i}. {req_text}")
            lines.append("")
        
        # Non-Functional Requirements
        nfr_reqs = requirements_data.get("non_functional_requirements", [])
        if nfr_reqs:
            lines.extend([
                "## Non-Functional Requirements",
                "",
            ])
            for i, req in enumerate(nfr_reqs, 1):
                if isinstance(req, dict):
                    req_text = req.get("requirement", req.get("description", str(req)))
                else:
                    req_text = str(req)
                lines.append(f"{i}. {req_text}")
            lines.append("")
        
        # Technical Constraints
        constraints = requirements_data.get("technical_constraints", [])
        if constraints:
            lines.extend([
                "## Technical Constraints",
                "",
            ])
            for i, constraint in enumerate(constraints, 1):
                if isinstance(constraint, dict):
                    constraint_text = constraint.get("constraint", constraint.get("description", str(constraint)))
                else:
                    constraint_text = str(constraint)
                lines.append(f"{i}. {constraint_text}")
            lines.append("")
        
        # Assumptions
        assumptions = requirements_data.get("assumptions", [])
        if assumptions:
            lines.extend([
                "## Assumptions",
                "",
            ])
            for i, assumption in enumerate(assumptions, 1):
                if isinstance(assumption, dict):
                    assumption_text = assumption.get("assumption", assumption.get("description", str(assumption)))
                else:
                    assumption_text = str(assumption)
                lines.append(f"{i}. {assumption_text}")
            lines.append("")
        
        # Open Questions
        questions = requirements_data.get("open_questions", [])
        if questions:
            lines.extend([
                "## Open Questions",
                "",
            ])
            for i, question in enumerate(questions, 1):
                if isinstance(question, dict):
                    question_text = question.get("question", question.get("description", str(question)))
                else:
                    question_text = str(question)
                lines.append(f"{i}. {question_text}")
            lines.append("")
        
        return "\n".join(lines)

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

    async def _analyze_prompt(
        self, description: str, context: str = ""
    ) -> dict[str, Any]:
        """Analyze prompt for intent, scope, domains, and workflow type."""
        prompt = f"""Analyze the following prompt and extract structured information.

Prompt:
{description}

{f"Context: {context}" if context else ""}

Please analyze and extract:
1. Intent (feature, bug-fix, refactor, documentation, testing, etc.)
2. Detected domains (security, user-management, payments, database, api, ui, integration, etc.)
3. Estimated scope (small: 1-2 files, medium: 3-5 files, large: 6+ files)
4. Recommended workflow type (greenfield: new code, brownfield: existing code modification, quick-fix: urgent bug fix)
5. Key technologies mentioned or implied (Python, JavaScript, FastAPI, React, etc.)
6. Complexity level (low, medium, high)

Provide structured JSON response with the following format:
{{
  "intent": "feature",
  "scope": "medium",
  "workflow_type": "greenfield",
  "domains": ["security", "user-management"],
  "technologies": ["Python", "FastAPI"],
  "complexity": "medium"
}}

Be specific and accurate. If uncertain about a field, use reasonable defaults based on the prompt content."""

        # Prepare instruction for Cursor Skills
        instruction = GenericInstruction(
            agent_name="analyst",
            command="analyze-prompt",
            prompt=prompt,
            parameters={"description": description, "context": context},
        )

        return {
            "success": True,
            "instruction": instruction.to_dict(),
            "skill_command": instruction.to_skill_command(),
            "analysis": prompt,  # Include the analysis prompt for reference
        }

    async def _evaluate_requirements(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Evaluate requirements quality and completeness."""
        from ...core.requirements_evaluator import RequirementsEvaluator

        evaluator = RequirementsEvaluator()
        score = evaluator.evaluate(requirements)

        return {
            "success": True,
            "score": {
                "overall": score.overall,
                "completeness": score.completeness,
                "clarity": score.clarity,
                "testability": score.testability,
                "traceability": score.traceability,
                "feasibility": score.feasibility,
            },
            "issues": score.issues,
            "strengths": score.strengths,
            "recommendations": score.recommendations,
        }

    async def _validate_requirements(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Validate requirements for completeness and quality."""
        from ...core.requirements_evaluator import RequirementsEvaluator

        evaluator = RequirementsEvaluator()
        result = evaluator.validate(requirements)

        return {
            "success": True,
            "is_valid": result.is_valid,
            "score": {
                "overall": result.score.overall,
                "completeness": result.score.completeness,
                "clarity": result.score.clarity,
                "testability": result.score.testability,
                "traceability": result.score.traceability,
                "feasibility": result.score.feasibility,
            },
            "missing_elements": result.missing_elements,
            "ambiguous_requirements": result.ambiguous_requirements,
            "untestable_requirements": result.untestable_requirements,
            "issues": result.score.issues,
            "recommendations": result.score.recommendations,
        }

    async def _trace_requirements(
        self, requirements: dict[str, Any], stories: list[dict[str, Any]], output_file: str | None = None
    ) -> dict[str, Any]:
        """Create traceability matrix linking requirements to stories/tests."""
        from ...core.traceability import TraceabilityManager

        manager = TraceabilityManager()
        matrix = manager.get_matrix()

        # Add requirements to matrix
        func_reqs = requirements.get("functional_requirements", [])
        for i, req in enumerate(func_reqs):
            req_id = f"req-{i+1}"
            if isinstance(req, dict):
                req_id = req.get("id", req_id)
            matrix.add_requirement(req_id, req if isinstance(req, dict) else {"description": str(req)})

        # Add stories and link to requirements
        for i, story in enumerate(stories):
            story_id = story.get("id", f"story-{i+1}")
            matrix.add_story(story_id, story)

            # Try to link story to requirements (simple keyword matching)
            story_text = str(story).lower()
            for req_id, req_data in matrix.requirements.items():
                req_text = str(req_data).lower()
                # Simple keyword overlap check
                req_words = set(req_text.split())
                story_words = set(story_text.split())
                overlap = len(req_words & story_words)
                if overlap > 3:  # Threshold for linking
                    confidence = min(1.0, overlap / 10.0)
                    matrix.link("requirement", req_id, "story", story_id, "implements", confidence)

        # Save matrix
        manager.save_matrix()

        # Generate report
        report = matrix.generate_report()

        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import yaml
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(report, f, default_flow_style=False)

        return {
            "success": True,
            "traceability_report": report,
            "matrix_file": str(manager.matrix_file),
            "output_file": str(output_path) if output_file else None,
        }

    async def _review_requirements(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Structured review of requirements with checklist."""
        from ...core.review_checklists import RequirementsReviewChecklist

        checklist = RequirementsReviewChecklist()
        result = checklist.review(requirements)

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

    async def _analyze_change_impact(
        self, old_requirements: dict[str, Any], new_requirements: dict[str, Any], traceability_file: str | None = None
    ) -> dict[str, Any]:
        """Analyze impact of requirement changes."""
        from ...core.change_impact_analyzer import ChangeImpactAnalyzer
        from ...core.traceability import TraceabilityManager

        analyzer = ChangeImpactAnalyzer()

        # Load traceability matrix if provided
        traceability_matrix = None
        if traceability_file:
            manager = TraceabilityManager()
            manager.matrix_file = Path(traceability_file)
            if manager.matrix_file.exists():
                traceability_matrix = manager.get_matrix()

        report = analyzer.analyze_change_impact(old_requirements, new_requirements, traceability_matrix)

        return {
            "success": True,
            "changes_count": len(report.changes),
            "total_affected_stories": report.total_affected_stories,
            "total_affected_designs": report.total_affected_designs,
            "total_affected_implementations": report.total_affected_implementations,
            "critical_changes": report.critical_changes,
            "recommendations": report.recommendations,
            "changes": [
                {
                    "requirement_id": change.requirement_id,
                    "change_type": change.change_type,
                    "severity": change.severity,
                    "affected_stories": change.affected_stories,
                    "affected_designs": change.affected_designs,
                    "affected_implementations": change.affected_implementations,
                    "impact_description": change.impact_description,
                }
                for change in report.changes
            ],
        }

    async def close(self) -> None:
        """Cleanup resources."""
        await super().close()
        # Context7 helper cleanup if needed
        # (Context7AgentHelper doesn't currently require explicit cleanup)
