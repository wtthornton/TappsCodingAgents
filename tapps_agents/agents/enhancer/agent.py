"""
Enhancer Agent - Prompt enhancement utility that runs prompts through all TappsCodingAgents capabilities.
"""

import asyncio
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...agents.analyst.agent import AnalystAgent
from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.context_manager import ContextManager
from ...core.instructions import GenericInstruction
from ...core.runtime_mode import is_cursor_mode

if TYPE_CHECKING:
    from ...experts.expert_registry import ExpertRegistry

if TYPE_CHECKING:
    from ...agents.architect.agent import ArchitectAgent
    from ...agents.designer.agent import DesignerAgent
    from ...agents.ops.agent import OpsAgent
    from ...agents.planner.agent import PlannerAgent
    from ...agents.reviewer.agent import ReviewerAgent


logger = logging.getLogger(__name__)


class EnhancerAgent(BaseAgent):
    """
    Enhancer Agent - Transforms simple prompts into comprehensive, context-aware prompts.

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify

    Responsibilities:
    - Analyze prompt intent and scope
    - Enrich with requirements analysis
    - Add architecture guidance
    - Inject codebase context
    - Include quality standards
    - Consult industry experts
    - Synthesize enhanced prompt
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="enhancer", agent_name="Enhancer Agent", config=config
        )
        if config is None:
            config = load_config()
        self.config = config


        # Initialize sub-agents
        self.analyst = AnalystAgent(config=config)
        self.architect: ArchitectAgent | None = None  # Lazy load
        self.designer: DesignerAgent | None = None  # Lazy load
        self.planner: PlannerAgent | None = None  # Lazy load
        self.reviewer: ReviewerAgent | None = None  # Lazy load
        self.ops: OpsAgent | None = None  # Lazy load

        # Expert registry (lazy load)
        if TYPE_CHECKING:
            pass
        self.expert_registry: ExpertRegistry | None = None

        # Context manager
        self.context_manager = ContextManager()

        # Skill invoker for executing Cursor Skills when possible
        self.skill_invoker = None  # Lazy load

        # Enhancement state
        self.current_session: dict[str, Any] | None = None

    async def activate(self, project_root: Path | None = None):
        """Activate the enhancer agent."""
        await super().activate(project_root)
        await self.analyst.activate(project_root)

        # Initialize skill invoker if available
        try:
            from ...workflow.skill_invoker import SkillInvoker
            self.skill_invoker = SkillInvoker(project_root=project_root, use_api=False)
        except Exception:
            logger.debug("SkillInvoker not available; skills will be prepared but not executed")

        # Load expert registry if domains.md exists
        if project_root:
            domains_file = project_root / ".tapps-agents" / "domains.md"
            if domains_file.exists():
                try:
                    from ...experts.expert_registry import ExpertRegistry
                    self.expert_registry = ExpertRegistry.from_domains_file(
                        domains_file
                    )
                except Exception:
                    logger.debug("Expert registry optional; continuing without it")

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for enhancer agent."""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*enhance",
                "description": "Full enhancement pipeline (all stages)",
            },
            {
                "command": "*enhance-quick",
                "description": "Quick enhancement (stages 1-3 only)",
            },
            {
                "command": "*enhance-stage",
                "description": "Run specific enhancement stage",
            },
            {
                "command": "*enhance-resume",
                "description": "Resume interrupted enhancement session",
            },
        ]

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute enhancer agent command.

        Commands:
        - *enhance: Full enhancement pipeline
        - *enhance-quick: Quick enhancement (analysis, requirements, architecture)
        - *enhance-stage: Run specific stage
        - *enhance-resume: Resume session
        - *help: Show help
        """
        command = command.lstrip("*")

        if command == "help":
            return {"type": "help", "content": self.format_help()}

        elif command == "enhance":
            prompt = kwargs.get("prompt", "")
            output_format = kwargs.get("output_format", "markdown")
            output_file = kwargs.get("output_file", None)
            config_path = kwargs.get("config_path", None)

            return await self._enhance_full(
                prompt, output_format, output_file, config_path
            )

        elif command == "enhance-quick":
            prompt = kwargs.get("prompt", "")
            output_format = kwargs.get("output_format", "markdown")
            output_file = kwargs.get("output_file", None)

            return await self._enhance_quick(prompt, output_format, output_file)

        elif command == "enhance-stage":
            stage = kwargs.get("stage", "")
            prompt = kwargs.get("prompt", "")
            session_id = kwargs.get("session_id", None)

            return await self._enhance_stage(stage, prompt, session_id)

        elif command == "enhance-resume":
            session_id = kwargs.get("session_id", "")

            return await self._resume_session(session_id)

        else:
            return {"error": f"Unknown command: {command}"}

    async def _enhance_full(
        self,
        prompt: str,
        output_format: str = "markdown",
        output_file: str | None = None,
        config_path: str | None = None,
    ) -> dict[str, Any]:
        """Run full enhancement pipeline through all stages."""
        if not prompt:
            return {"error": "prompt is required"}

        # Load enhancement config
        enhancement_config = self._load_enhancement_config(config_path)

        # Create session
        session_id = self._create_session(prompt, enhancement_config)
        session = self.current_session
        if session is None:
            return {"error": "Failed to initialize enhancement session"}

        # Calculate total stages for progress tracking
        total_stages = sum(
            [
                enhancement_config.get("stages", {}).get("analysis", True),
                enhancement_config.get("stages", {}).get("requirements", True),
                enhancement_config.get("stages", {}).get("architecture", True),
                enhancement_config.get("stages", {}).get("codebase_context", True),
                enhancement_config.get("stages", {}).get("quality", True),
                enhancement_config.get("stages", {}).get("implementation", True),
                enhancement_config.get("stages", {}).get("synthesis", True),
            ]
        )
        current_stage = 0

        try:
            # Stage 1: Analysis
            if enhancement_config.get("stages", {}).get("analysis", True):
                current_stage += 1
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Analysis",
                    "Analyzing prompt intent and scope...",
                )
                await asyncio.sleep(0.01)  # Ensure output appears immediately
                session["stages"]["analysis"] = await self._stage_analysis(prompt)
                self._print_progress(
                    current_stage, total_stages, "Analysis", "[OK] Analysis complete"
                )

            # Stage 2: Requirements
            if enhancement_config.get("stages", {}).get("requirements", True):
                current_stage += 1
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Requirements",
                    "Gathering requirements from analyst and experts...",
                )
                await asyncio.sleep(0.01)
                session["stages"]["requirements"] = await self._stage_requirements(
                    prompt, session["stages"].get("analysis", {})
                )
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Requirements",
                    "[OK] Requirements gathered",
                )

            # Stage 3: Architecture
            if enhancement_config.get("stages", {}).get("architecture", True):
                current_stage += 1
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Architecture",
                    "Generating architecture guidance...",
                )
                await asyncio.sleep(0.01)
                session["stages"]["architecture"] = await self._stage_architecture(
                    prompt, session["stages"].get("requirements", {})
                )
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Architecture",
                    "[OK] Architecture guidance complete",
                )

            # Stage 4: Codebase Context
            if enhancement_config.get("stages", {}).get("codebase_context", True):
                current_stage += 1
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Codebase Context",
                    "Analyzing codebase and finding related files...",
                )
                await asyncio.sleep(0.01)
                session["stages"]["codebase_context"] = (
                    await self._stage_codebase_context(
                        prompt, session["stages"].get("analysis", {})
                    )
                )
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Codebase Context",
                    "[OK] Codebase context injected",
                )

            # Stage 5: Quality Standards
            if enhancement_config.get("stages", {}).get("quality", True):
                current_stage += 1
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Quality Standards",
                    "Defining quality standards and thresholds...",
                )
                await asyncio.sleep(0.01)
                session["stages"]["quality"] = await self._stage_quality(
                    prompt, session["stages"].get("requirements", {})
                )
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Quality Standards",
                    "[OK] Quality standards defined",
                )

            # Stage 6: Implementation Strategy
            if enhancement_config.get("stages", {}).get("implementation", True):
                current_stage += 1
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Implementation Strategy",
                    "Creating implementation plan and task breakdown...",
                )
                await asyncio.sleep(0.01)
                session["stages"]["implementation"] = await self._stage_implementation(
                    prompt,
                    session["stages"].get("requirements", {}),
                    session["stages"].get("architecture", {}),
                )
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Implementation Strategy",
                    "[OK] Implementation plan created",
                )

            # Stage 7: Synthesis
            if enhancement_config.get("stages", {}).get("synthesis", True):
                current_stage += 1
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Synthesis",
                    "Synthesizing enhanced prompt from all stages...",
                )
                await asyncio.sleep(0.01)
                session["stages"]["synthesis"] = await self._stage_synthesis(
                    prompt, session["stages"], output_format
                )
                self._print_progress(
                    current_stage,
                    total_stages,
                    "Synthesis",
                    "[OK] Enhanced prompt synthesized",
                )

            # Save session
            self._save_session(session_id, session)

            # Format output
            result = self._format_output(session, output_format)

            # Write to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if output_format == "json":
                    output_path.write_text(json.dumps(result, indent=2))
                    if isinstance(result, dict):
                        result["output_file"] = str(output_path)
                else:
                    output_path.write_text(result)
                    # For markdown, result is a string, so we can't add to it
                    # Return dict with both the markdown and file path
                    result = {
                        "enhanced_prompt": result,
                        "output_file": str(output_path),
                    }

            return {
                "success": True,
                "session_id": session_id,
                "enhanced_prompt": result,
                "stages_completed": list(session["stages"].keys()),
                "metadata": session["metadata"],
            }

        except Exception as e:
            return {"error": f"Enhancement failed: {str(e)}", "session_id": session_id}

    async def _enhance_quick(
        self,
        prompt: str,
        output_format: str = "markdown",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        """Quick enhancement (stages 1-3 only)."""
        if not prompt:
            return {"error": "prompt is required"}

        session_id = self._create_session(
            prompt,
            {"stages": {"analysis": True, "requirements": True, "architecture": True}},
        )
        session = self.current_session
        if session is None:
            return {"error": "Failed to initialize enhancement session"}

        total_stages = 4  # analysis, requirements, architecture, synthesis
        current_stage = 0

        try:
            # Stage 1: Analysis
            current_stage += 1
            self._print_progress(
                current_stage,
                total_stages,
                "Analysis",
                "Analyzing prompt intent and scope...",
            )
            session["stages"]["analysis"] = await self._stage_analysis(prompt)
            self._print_progress(
                current_stage, total_stages, "Analysis", "✅ Analysis complete"
            )

            # Stage 2: Requirements
            current_stage += 1
            self._print_progress(
                current_stage,
                total_stages,
                "Requirements",
                "Gathering requirements from analyst and experts...",
            )
            await asyncio.sleep(0.01)
            session["stages"]["requirements"] = await self._stage_requirements(
                prompt, session["stages"].get("analysis", {})
            )
            self._print_progress(
                current_stage,
                total_stages,
                "Requirements",
                "[OK] Requirements gathered",
            )

            # Stage 3: Architecture
            current_stage += 1
            self._print_progress(
                current_stage,
                total_stages,
                "Architecture",
                "Generating architecture guidance...",
            )
            await asyncio.sleep(0.01)
            session["stages"]["architecture"] = await self._stage_architecture(
                prompt, session["stages"].get("requirements", {})
            )
            self._print_progress(
                current_stage,
                total_stages,
                "Architecture",
                "[OK] Architecture guidance complete",
            )

            # Quick synthesis
            current_stage += 1
            self._print_progress(
                current_stage,
                total_stages,
                "Synthesis",
                "Synthesizing enhanced prompt...",
            )
            await asyncio.sleep(0.01)
            session["stages"]["synthesis"] = await self._stage_synthesis(
                prompt, session["stages"], output_format
            )
            self._print_progress(
                current_stage,
                total_stages,
                "Synthesis",
                "[OK] Enhanced prompt synthesized",
            )

            self._save_session(session_id, session)
            result = self._format_output(session, output_format)

            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if output_format == "json":
                    output_path.write_text(json.dumps(result, indent=2))
                    if isinstance(result, dict):
                        result["output_file"] = str(output_path)
                else:
                    output_path.write_text(result)
                    # For markdown, result is a string, so we can't add to it
                    # Return dict with both the markdown and file path
                    result = {
                        "enhanced_prompt": result,
                        "output_file": str(output_path),
                    }

            return {
                "success": True,
                "session_id": session_id,
                "enhanced_prompt": result,
                "stages_completed": [
                    "analysis",
                    "requirements",
                    "architecture",
                    "synthesis",
                ],
            }

        except Exception as e:
            return {
                "error": f"Quick enhancement failed: {str(e)}",
                "session_id": session_id,
            }

    async def _enhance_stage(
        self, stage: str, prompt: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """Run a specific enhancement stage."""
        if not prompt and not session_id:
            return {"error": "prompt or session_id required"}

        # Load or create session
        if session_id:
            session = self._load_session(session_id)
            if not session:
                return {"error": f"Session not found: {session_id}"}
            prompt = session["metadata"]["original_prompt"]
        else:
            session_id = self._create_session(prompt, {})
            session = self.current_session
            if session is None:
                return {"error": "Failed to initialize enhancement session"}

        # Run stage
        stage_handlers: dict[str, Any] = {
            "analysis": self._stage_analysis,
            "requirements": self._stage_requirements,
            "architecture": self._stage_architecture,
            "codebase_context": self._stage_codebase_context,
            "quality": self._stage_quality,
            "implementation": self._stage_implementation,
            "synthesis": self._stage_synthesis,
        }

        if stage not in stage_handlers:
            return {
                "error": f"Unknown stage: {stage}. Available: {list(stage_handlers.keys())}"
            }

        try:
            handler: Any = stage_handlers[stage]
            if stage == "requirements":
                result = await handler(prompt, session["stages"].get("analysis", {}))
            elif stage == "architecture":
                result = await handler(
                    prompt, session["stages"].get("requirements", {})
                )
            elif stage == "codebase_context":
                result = await handler(prompt, session["stages"].get("analysis", {}))
            elif stage == "quality":
                result = await handler(
                    prompt, session["stages"].get("requirements", {})
                )
            elif stage == "implementation":
                result = await handler(
                    prompt,
                    session["stages"].get("requirements", {}),
                    session["stages"].get("architecture", {}),
                )
            elif stage == "synthesis":
                result = await handler(prompt, session["stages"], "markdown")
            else:
                result = await handler(prompt)

            session["stages"][stage] = result
            self._save_session(session_id, session)

            return {
                "success": True,
                "stage": stage,
                "result": result,
                "session_id": session_id,
            }

        except Exception as e:
            return {
                "error": f"Stage {stage} failed: {str(e)}",
                "session_id": session_id,
            }

    async def _resume_session(self, session_id: str) -> dict[str, Any]:
        """Resume an interrupted enhancement session."""
        session = self._load_session(session_id)
        if not session:
            return {"error": f"Session not found: {session_id}"}

        self.current_session = session
        prompt = session["metadata"]["original_prompt"]

        # Continue from where we left off
        # This is a simplified version - in production, would track which stages completed
        return await self._enhance_full(
            prompt, output_format="markdown", config_path=None
        )

    # Stage implementations

    async def _stage_analysis(self, prompt: str) -> dict[str, Any]:
        """Stage 1: Analyze prompt intent, scope, and domains."""
        analysis_prompt = f"""Analyze the following prompt and extract:
1. Intent (feature, bug fix, refactor, documentation, etc.)
2. Detected domains (security, user-management, payments, etc.)
3. Estimated scope (small: 1-2 files, medium: 3-5 files, large: 6+ files)
4. Recommended workflow type (greenfield, brownfield, quick-fix)
5. Key technologies mentioned
6. Complexity level (low, medium, high)

Prompt: {prompt}

Provide structured JSON response with the following format:
{{
  "intent": "feature",
  "scope": "medium",
  "workflow_type": "greenfield",
  "domains": ["security", "user-management"],
  "technologies": ["Python", "FastAPI"],
  "complexity": "medium"
}}"""

        # Use analyst agent to perform analysis
        try:
            analysis_result = await self.analyst.run(
                "analyze-prompt",
                description=prompt,
            )
            
            # Extract analysis text from result
            analysis_text = ""
            if isinstance(analysis_result, dict):
                analysis_text = analysis_result.get("analysis", "") or analysis_result.get("result", "") or str(analysis_result)
            else:
                analysis_text = str(analysis_result)
            
            # Parse the response to extract structured data
            parsed = self._parse_analysis_response(analysis_text)
            
            return {
                "original_prompt": prompt,
                "intent": parsed.get("intent", "unknown"),
                "scope": parsed.get("scope", "unknown"),
                "workflow_type": parsed.get("workflow_type", "unknown"),
                "domains": parsed.get("domains", []),
                "technologies": parsed.get("technologies", []),
                "complexity": parsed.get("complexity", "medium"),
                "analysis": analysis_text,  # Keep raw response for reference
                "parsed_data": parsed,  # Store parsed data
            }
        except Exception as e:
            logger.warning(f"Analysis stage failed: {e}, using fallback values")
            # Return fallback values if analysis fails
            return {
                "original_prompt": prompt,
                "intent": "unknown",
                "scope": "unknown",
                "workflow_type": "unknown",
                "domains": [],
                "technologies": [],
                "complexity": "medium",
                "analysis": f"Analysis failed: {str(e)}",
                "parsed_data": {},
            }

    async def _stage_requirements(
        self, prompt: str, analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Stage 2: Enrich requirements with analyst and experts."""
        # Use analyst to gather requirements
        requirements_result = await self.analyst.run(
            "gather-requirements",
            description=prompt,
            context=analysis.get("analysis", ""),
        )

        requirements = (
            requirements_result.get("requirements", {})
            if "error" not in requirements_result
            else {}
        )
        
        # Try to execute the skill if we have a skill invoker and instruction
        if self.skill_invoker and "requirements" in requirements_result:
            req_data = requirements_result["requirements"]
            if "skill_command" in req_data:
                try:
                    # Try to execute the skill command
                    skill_result = await self._try_execute_skill(
                        req_data["skill_command"],
                        worktree_path=self.config.project_root or Path.cwd(),
                    )
                    # If we got a result, merge it into requirements
                    if skill_result and "result" in skill_result:
                        # Try to extract actual requirements from the result
                        parsed_req = self._parse_requirements_from_result(skill_result["result"])
                        if parsed_req:
                            requirements.update(parsed_req)
                except Exception as e:
                    logger.debug(f"Failed to execute skill: {e}", exc_info=True)

        # Consult experts if available
        expert_consultations = {}
        domains = analysis.get("domains", [])

        if self.expert_registry and domains:
            for domain in domains:
                try:
                    consultation = await self.expert_registry.consult(
                        query=f"What are the domain-specific requirements, business rules, and best practices for: {prompt}",
                        domain=domain,
                        include_all=True,
                    )
                    expert_consultations[domain] = {
                        "weighted_answer": consultation.weighted_answer,
                        "confidence": consultation.confidence,
                        "agreement_level": consultation.agreement_level,
                        "primary_expert": consultation.primary_expert,
                        "sources": [
                            r.get("sources", []) for r in consultation.responses
                        ],
                    }
                except Exception:
                    logger.debug(
                        "Expert consultation optional; continuing without it",
                        exc_info=True,
                    )

        return {
            "functional_requirements": requirements.get("functional_requirements", []),
            "non_functional_requirements": requirements.get(
                "non_functional_requirements", []
            ),
            "technical_constraints": requirements.get("technical_constraints", []),
            "assumptions": requirements.get("assumptions", []),
            "expert_consultations": expert_consultations,
            "requirements_analysis": requirements.get("analysis", ""),
        }

    async def _stage_architecture(
        self, prompt: str, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Stage 3: Architecture guidance."""
        if self.architect is None:
            from ...agents.architect.agent import ArchitectAgent

            self.architect = ArchitectAgent(config=self.config)
            await self.architect.activate()

        # Get architecture guidance
        arch_result = await self.architect.run(
            "design-system",
            requirements=prompt,
            context=json.dumps(requirements, indent=2),
        )

        return {
            "system_design": arch_result.get("architecture", {}),
            "design_patterns": [],
            "technology_recommendations": [],
            "architecture_guidance": arch_result.get("guidance", ""),
        }

    async def _stage_codebase_context(
        self, prompt: str, analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Stage 4: Inject codebase context."""
        # This would analyze the codebase and find related files
        # For now, return empty context
        return {
            "related_files": [],
            "existing_patterns": [],
            "cross_references": [],
            "codebase_context": "No codebase context available",
        }

    async def _stage_quality(
        self, prompt: str, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Stage 5: Quality standards."""
        if self.ops is None:
            from ...agents.ops.agent import OpsAgent

            self.ops = OpsAgent(config=self.config)
            await self.ops.activate()

        # Get security requirements
        security_result = await self.ops.run("security-scan", target=None)

        return {
            "security_requirements": security_result.get("requirements", []),
            "testing_requirements": [
                "Unit tests required",
                "Integration tests for APIs",
            ],
            "performance_requirements": [],
            "code_quality_thresholds": {
                "overall_score": 70.0,
                "complexity_max": 5.0,
                "security_min": 8.0,
            },
        }

    async def _stage_implementation(
        self, prompt: str, requirements: dict[str, Any], architecture: dict[str, Any]
    ) -> dict[str, Any]:
        """Stage 6: Implementation strategy."""
        if self.planner is None:
            from ...agents.planner.agent import PlannerAgent

            self.planner = PlannerAgent(config=self.config)
            await self.planner.activate()

        # Create implementation plan
        plan_result = await self.planner.run("plan", description=prompt)

        return {
            "task_breakdown": plan_result.get("tasks", []),
            "implementation_order": plan_result.get("order", []),
            "dependencies": [],
            "estimated_effort": plan_result.get("estimate", {}),
        }

    def _build_synthesis_prompt(
        self, prompt: str, stages: dict[str, Any]
    ) -> str:
        """Build synthesis prompt from stages."""
        return f"""Synthesize an enhanced prompt from the following analysis:

Original Prompt: {prompt}

Analysis: {json.dumps(stages.get('analysis', {}), indent=2)}
Requirements: {json.dumps(stages.get('requirements', {}), indent=2)}
Architecture: {json.dumps(stages.get('architecture', {}), indent=2)}
Quality: {json.dumps(stages.get('quality', {}), indent=2)}
Implementation: {json.dumps(stages.get('implementation', {}), indent=2)}

Create a comprehensive, context-aware enhanced prompt that includes all relevant information."""

    async def _stage_synthesis(
        self, prompt: str, stages: dict[str, Any], output_format: str
    ) -> dict[str, Any]:
        """Stage 7: Synthesize enhanced prompt."""
        if is_cursor_mode():
            # Cursor mode: Return structured data for Cursor Skill synthesis
            synthesis_prompt = self._build_synthesis_prompt(prompt, stages)
            instruction = GenericInstruction(
                agent_name="enhancer",
                command="synthesize-prompt",
                prompt=synthesis_prompt,
                parameters={
                    "original_prompt": prompt,
                    "stages": json.dumps(stages),
                    "output_format": output_format,
                },
            )

            return {
                "instruction": instruction.to_dict(),
                "skill_command": instruction.to_skill_command(),
                "synthesis_data": {
                    "original_prompt": prompt,
                    "stages": stages,
                    "format": output_format,
                },
                "format": output_format,
                "metadata": {
                    "original_prompt": prompt,
                    "stages_used": list(stages.keys()),
                    "synthesized_at": datetime.now().isoformat(),
                    "mode": "cursor-skills",
                },
            }
        else:
            # Headless mode: Use MAL for synthesis
            synthesis_prompt = self._build_synthesis_prompt(prompt, stages)
            
            try:
                from ...core.mal import MAL, MALDisabledInCursorModeError
                
                mal_config = self.config.mal if self.config else None
                if mal_config and mal_config.enabled:
                    mal = MAL(config=mal_config)
                    enhanced = await mal.generate(
                        prompt=synthesis_prompt,
                        model=mal_config.default_model if mal_config else None,
                        temperature=0.3,
                    )
                    return {
                        "enhanced_prompt": enhanced,
                        "format": output_format,
                        "metadata": {
                            "original_prompt": prompt,
                            "stages_used": list(stages.keys()),
                            "synthesized_at": datetime.now().isoformat(),
                            "mode": "headless-mal",
                        },
                    }
                else:
                    # MAL not configured, return structured data
                    logger.warning("MAL not configured for headless mode synthesis")
                    return {
                        "enhanced_prompt": None,
                        "synthesis_data": {
                            "original_prompt": prompt,
                            "stages": stages,
                            "format": output_format,
                        },
                        "format": output_format,
                        "metadata": {
                            "original_prompt": prompt,
                            "stages_used": list(stages.keys()),
                            "synthesized_at": datetime.now().isoformat(),
                            "mode": "structured",
                        },
                    }
            except MALDisabledInCursorModeError:
                # Should not happen in headless mode, but handle gracefully
                logger.warning("MAL disabled error in headless mode")
                return {
                    "enhanced_prompt": None,
                    "synthesis_data": {
                        "original_prompt": prompt,
                        "stages": stages,
                        "format": output_format,
                    },
                    "format": output_format,
                    "metadata": {
                        "original_prompt": prompt,
                        "stages_used": list(stages.keys()),
                        "synthesized_at": datetime.now().isoformat(),
                        "mode": "structured",
                    },
                }
            except Exception as e:
                logger.error(f"Synthesis failed: {e}", exc_info=True)
                return {
                    "error": f"Synthesis failed: {str(e)}",
                    "format": output_format,
                    "metadata": {
                        "original_prompt": prompt,
                        "stages_used": list(stages.keys()),
                        "synthesized_at": datetime.now().isoformat(),
                    },
                }

    # Helper methods

    def _load_enhancement_config(
        self, config_path: str | None = None
    ) -> dict[str, Any]:
        """Load enhancement configuration."""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path.cwd() / ".tapps-agents" / "enhancement-config.yaml"

        if config_file.exists():
            import yaml

            try:
                with open(config_file) as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                logger.debug("Failed to load stage defaults; using fallbacks")

        # Return defaults
        return {
            "stages": {
                "analysis": True,
                "requirements": True,
                "architecture": True,
                "codebase_context": True,
                "quality": True,
                "implementation": True,
                "synthesis": True,
            }
        }

    def _create_session(self, prompt: str, config: dict[str, Any]) -> str:
        """Create a new enhancement session."""
        session_id = hashlib.sha256(
            f"{prompt}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]

        self.current_session = {
            "session_id": session_id,
            "metadata": {
                "original_prompt": prompt,
                "created_at": datetime.now().isoformat(),
                "config": config,
            },
            "stages": {},
        }

        return session_id

    def _save_session(self, session_id: str, session: dict[str, Any]):
        """Save session to disk."""
        sessions_dir = Path.cwd() / ".tapps-agents" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        session_file = sessions_dir / f"{session_id}.json"
        session_file.write_text(json.dumps(session, indent=2))

    def _load_session(self, session_id: str) -> dict[str, Any] | None:
        """Load session from disk."""
        session_file = Path.cwd() / ".tapps-agents" / "sessions" / f"{session_id}.json"
        if session_file.exists():
            return json.loads(session_file.read_text())
        return None

    def _format_output(self, session: dict[str, Any], format: str) -> Any:
        """Format output based on format type."""
        synthesis = session["stages"].get("synthesis", {})

        if format == "json":
            return {
                "original_prompt": session["metadata"]["original_prompt"],
                "enhanced_prompt": synthesis.get("enhanced_prompt", ""),
                "stages": session["stages"],
                "metadata": session["metadata"],
            }
        else:  # markdown
            enhanced = synthesis.get("enhanced_prompt", "")
            if not enhanced:
                # Fallback: create markdown from stages
                enhanced = self._create_markdown_from_stages(session)
            return enhanced

    def _create_markdown_from_stages(self, session: dict[str, Any]) -> str:
        """Create markdown output from stages."""
        prompt = session["metadata"]["original_prompt"]
        stages = session["stages"]

        lines = [f"# Enhanced Prompt: {prompt}", ""]
        lines.append("## Metadata")
        lines.append(f"- **Created**: {session['metadata']['created_at']}")
        lines.append("")

        # Analysis section with all extracted fields
        if "analysis" in stages:
            lines.append("## Analysis")
            analysis = stages["analysis"]
            
            # Display parsed fields
            intent = analysis.get('intent', 'unknown')
            scope = analysis.get('scope', 'unknown')
            workflow_type = analysis.get('workflow_type', 'unknown')
            domains = analysis.get('domains', [])
            technologies = analysis.get('technologies', [])
            complexity = analysis.get('complexity', 'medium')
            
            lines.append(f"- **Intent**: {intent}")
            lines.append(f"- **Scope**: {scope}")
            lines.append(f"- **Workflow Type**: {workflow_type}")
            lines.append(f"- **Complexity**: {complexity}")
            
            if domains:
                lines.append(f"- **Detected Domains**: {', '.join(domains)}")
            
            if technologies:
                lines.append(f"- **Technologies**: {', '.join(technologies)}")
            
            lines.append("")

        # Requirements section with all content
        if "requirements" in stages:
            lines.append("## Requirements")
            reqs = stages["requirements"]
            
            # Functional Requirements
            if reqs.get("functional_requirements"):
                lines.append("### Functional Requirements")
                for req in reqs["functional_requirements"]:
                    lines.append(f"- {req}")
                lines.append("")
            
            # Non-functional Requirements
            if reqs.get("non_functional_requirements"):
                lines.append("### Non-Functional Requirements")
                for req in reqs["non_functional_requirements"]:
                    lines.append(f"- {req}")
                lines.append("")
            
            # Technical Constraints
            if reqs.get("technical_constraints"):
                lines.append("### Technical Constraints")
                for constraint in reqs["technical_constraints"]:
                    lines.append(f"- {constraint}")
                lines.append("")
            
            # Assumptions
            if reqs.get("assumptions"):
                lines.append("### Assumptions")
                for assumption in reqs["assumptions"]:
                    lines.append(f"- {assumption}")
                lines.append("")
            
            # Requirements Analysis
            if reqs.get("requirements_analysis"):
                lines.append("### Requirements Analysis")
                lines.append(reqs["requirements_analysis"])
                lines.append("")

            # Expert Consultations
            if reqs.get("expert_consultations"):
                lines.append("### Domain Context (from Industry Experts)")
                for domain, consultation in reqs["expert_consultations"].items():
                    lines.append(f"#### {domain.title()} Domain")
                    lines.append(
                        f"**Confidence**: {consultation.get('confidence', 0):.2%}"
                    )
                    lines.append(
                        f"**Agreement**: {consultation.get('agreement_level', 0):.2%}"
                    )
                    lines.append(
                        f"**Primary Expert**: {consultation.get('primary_expert', 'unknown')}"
                    )
                    lines.append("")
                    weighted_answer = consultation.get("weighted_answer", "")
                    if weighted_answer:
                        lines.append(weighted_answer)
                    lines.append("")

        # Architecture section with all content
        if "architecture" in stages:
            lines.append("## Architecture Guidance")
            arch = stages["architecture"]
            
            # Architecture Guidance
            if arch.get("architecture_guidance"):
                lines.append(arch["architecture_guidance"])
                lines.append("")
            
            # System Design
            if arch.get("system_design"):
                lines.append("### System Design")
                if isinstance(arch["system_design"], dict):
                    for key, value in arch["system_design"].items():
                        lines.append(f"**{key.title()}**: {value}")
                else:
                    lines.append(str(arch["system_design"]))
                lines.append("")
            
            # Design Patterns
            if arch.get("design_patterns"):
                lines.append("### Design Patterns")
                for pattern in arch["design_patterns"]:
                    lines.append(f"- {pattern}")
                lines.append("")
            
            # Technology Recommendations
            if arch.get("technology_recommendations"):
                lines.append("### Technology Recommendations")
                for tech in arch["technology_recommendations"]:
                    lines.append(f"- {tech}")
                lines.append("")

        # Codebase Context section
        if "codebase_context" in stages:
            lines.append("## Codebase Context")
            ctx = stages["codebase_context"]
            
            if ctx.get("codebase_context"):
                lines.append(ctx["codebase_context"])
                lines.append("")
            
            # Related Files
            if ctx.get("related_files"):
                lines.append("### Related Files")
                for file in ctx["related_files"]:
                    lines.append(f"- {file}")
                lines.append("")
            
            # Existing Patterns
            if ctx.get("existing_patterns"):
                lines.append("### Existing Patterns")
                for pattern in ctx["existing_patterns"]:
                    lines.append(f"- {pattern}")
                lines.append("")
            
            # Cross References
            if ctx.get("cross_references"):
                lines.append("### Cross References")
                for ref in ctx["cross_references"]:
                    lines.append(f"- {ref}")
                lines.append("")

        # Quality Standards section
        if "quality" in stages:
            lines.append("## Quality Standards")
            quality = stages["quality"]
            
            # Code Quality Thresholds
            if quality.get("code_quality_thresholds"):
                thresholds = quality["code_quality_thresholds"]
                lines.append("### Code Quality Thresholds")
                lines.append(f"- **Overall Score Threshold**: {thresholds.get('overall_score', 70)}")
                if thresholds.get('complexity_target'):
                    lines.append(f"- **Complexity Target**: {thresholds['complexity_target']}")
                if thresholds.get('security_target'):
                    lines.append(f"- **Security Target**: {thresholds['security_target']}")
                lines.append("")
            
            # Quality Standards Text
            if quality.get("quality_standards"):
                lines.append("### Quality Standards")
                lines.append(quality["quality_standards"])
                lines.append("")

        # Implementation Strategy section
        if "implementation" in stages:
            lines.append("## Implementation Strategy")
            impl = stages["implementation"]
            
            # Task Breakdown
            if impl.get("task_breakdown"):
                lines.append("### Task Breakdown")
                for task in impl["task_breakdown"]:
                    lines.append(f"- {task}")
                lines.append("")
            
            # Implementation Plan
            if impl.get("implementation_plan"):
                lines.append("### Implementation Plan")
                if isinstance(impl["implementation_plan"], str):
                    lines.append(impl["implementation_plan"])
                else:
                    lines.append(str(impl["implementation_plan"]))
                lines.append("")
            
            # Implementation Steps
            if impl.get("steps"):
                lines.append("### Implementation Steps")
                for i, step in enumerate(impl["steps"], 1):
                    lines.append(f"{i}. {step}")
                lines.append("")

        # Synthesis section (final enhanced prompt)
        if "synthesis" in stages:
            lines.append("## Enhanced Prompt")
            synthesis = stages["synthesis"]
            if isinstance(synthesis, dict):
                enhanced_prompt = synthesis.get("enhanced_prompt", synthesis.get("result", ""))
            else:
                enhanced_prompt = str(synthesis)
            
            if enhanced_prompt:
                lines.append("")
                lines.append(enhanced_prompt)
                lines.append("")

        return "\n".join(lines)

    def _parse_analysis_response(self, response_text: str) -> dict[str, Any]:
        """
        Parse analysis response to extract structured data.
        
        Handles both JSON and markdown-formatted responses.
        
        Args:
            response_text: Raw response text from analyst
            
        Returns:
            Dictionary with parsed fields (intent, scope, workflow_type, etc.)
        """
        parsed: dict[str, Any] = {}
        
        if not response_text:
            return parsed
        
        # Try to extract JSON from response
        # Look for JSON code blocks first
        import re
        
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                return parsed
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object directly
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return parsed
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to extract fields using regex patterns
        # Extract intent
        intent_match = re.search(r'"intent"\s*:\s*"([^"]+)"|intent[:\s]+([a-z-]+)', response_text, re.IGNORECASE)
        if intent_match:
            parsed["intent"] = intent_match.group(1) or intent_match.group(2) or "unknown"
        
        # Extract scope
        scope_match = re.search(r'"scope"\s*:\s*"([^"]+)"|scope[:\s]+(small|medium|large)', response_text, re.IGNORECASE)
        if scope_match:
            parsed["scope"] = scope_match.group(1) or scope_match.group(2) or "unknown"
        
        # Extract workflow_type
        workflow_match = re.search(r'"workflow_type"\s*:\s*"([^"]+)"|workflow[:\s]+(greenfield|brownfield|quick-fix)', response_text, re.IGNORECASE)
        if workflow_match:
            parsed["workflow_type"] = workflow_match.group(1) or workflow_match.group(2) or "unknown"
        
        # Extract domains (list)
        domains_match = re.search(r'"domains"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
        if domains_match:
            domains_str = domains_match.group(1)
            domains = [d.strip().strip('"\'') for d in domains_str.split(',') if d.strip()]
            parsed["domains"] = domains
        
        # Extract technologies (list)
        tech_match = re.search(r'"technologies"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
        if tech_match:
            tech_str = tech_match.group(1)
            technologies = [t.strip().strip('"\'') for t in tech_str.split(',') if t.strip()]
            parsed["technologies"] = technologies
        
        # Extract complexity
        complexity_match = re.search(r'"complexity"\s*:\s*"([^"]+)"|complexity[:\s]+(low|medium|high)', response_text, re.IGNORECASE)
        if complexity_match:
            parsed["complexity"] = complexity_match.group(1) or complexity_match.group(2) or "medium"
        
        return parsed

    def _print_progress(self, current: int, total: int, stage_name: str, message: str):
        """Print progress indicator with percentage - real-time unbuffered output."""
        percentage = int((current / total) * 100) if total > 0 else 0
        bar_length = 30
        filled = int(bar_length * current / total) if total > 0 else 0
        # Use ASCII-compatible characters for better cross-platform support
        bar = "=" * filled + "-" * (bar_length - filled)

        # Use ASCII checkmark for better compatibility
        checkmark = "[OK]" if message.startswith("✅") or "[OK]" in message else ""
        clean_message = message.replace("✅", "").replace("[OK]", "").strip()

        # Print progress line with immediate flush - ensure real-time output
        progress_line = f"[{current}/{total}] {percentage:3d}% |{bar}| {stage_name}: {checkmark} {clean_message}"
        # Write directly to stderr and force immediate flush for real-time display
        sys.stderr.write(progress_line + "\n")
        sys.stderr.flush()

    async def close(self):
        """Clean up resources."""
        # Close agents that have a close method (not all agents implement it)
        agents_to_close = [
            self.analyst,
            self.architect,
            self.designer,
            self.planner,
            self.reviewer,
            self.ops,
        ]

        for agent in agents_to_close:
            if agent and hasattr(agent, "close"):
                try:
                    await agent.close()
                except (AttributeError, TypeError):
                    pass  # Agent doesn't have close or it's not async
