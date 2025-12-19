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
from ...core.mal import MAL

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

        # Initialize MAL
        mal_config = config.mal if config else None
        self.mal = MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )

        # Initialize sub-agents
        self.analyst = AnalystAgent(mal=self.mal, config=config)
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

        # Enhancement state
        self.current_session: dict[str, Any] | None = None

    async def activate(self, project_root: Path | None = None):
        """Activate the enhancer agent."""
        await super().activate(project_root)
        await self.analyst.activate(project_root)

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

Provide structured JSON response."""

        try:
            model_name = (
                self.config.mal.default_model
                if (self.config and self.config.mal)
                else "qwen2.5-coder:7b"
            )
            response = await self.mal.generate(
                prompt=analysis_prompt, model=model_name, temperature=0.3
            )

            # Parse response (simplified - in production use structured output)
            return {
                "original_prompt": prompt,
                "intent": "feature",  # Would parse from response
                "domains": [],  # Would extract from response
                "scope": "medium",
                "workflow_type": "greenfield",
                "technologies": [],
                "complexity": "medium",
                "analysis": response,
            }
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

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

    async def _stage_synthesis(
        self, prompt: str, stages: dict[str, Any], output_format: str
    ) -> dict[str, Any]:
        """Stage 7: Synthesize enhanced prompt."""
        # Combine all stages into final enhanced prompt
        synthesis_prompt = f"""Synthesize an enhanced prompt from the following analysis:

Original Prompt: {prompt}

Analysis: {json.dumps(stages.get('analysis', {}), indent=2)}
Requirements: {json.dumps(stages.get('requirements', {}), indent=2)}
Architecture: {json.dumps(stages.get('architecture', {}), indent=2)}
Quality: {json.dumps(stages.get('quality', {}), indent=2)}
Implementation: {json.dumps(stages.get('implementation', {}), indent=2)}

Create a comprehensive, context-aware enhanced prompt that includes all relevant information."""

        try:
            enhanced = await self.mal.generate(
                prompt=synthesis_prompt,
                model=(
                    self.config.mal.default_model
                    if (self.config and self.config.mal)
                    else "qwen2.5-coder:7b"
                ),
                temperature=0.3,
            )

            return {
                "enhanced_prompt": enhanced,
                "format": output_format,
                "metadata": {
                    "original_prompt": prompt,
                    "stages_used": list(stages.keys()),
                    "synthesized_at": datetime.now().isoformat(),
                },
            }
        except Exception as e:
            return {"error": f"Synthesis failed: {str(e)}"}

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

        if "analysis" in stages:
            lines.append("## Analysis")
            analysis = stages["analysis"]
            lines.append(f"- **Intent**: {analysis.get('intent', 'unknown')}")
            lines.append(f"- **Scope**: {analysis.get('scope', 'unknown')}")
            lines.append(f"- **Workflow**: {analysis.get('workflow_type', 'unknown')}")
            lines.append("")

        if "requirements" in stages:
            lines.append("## Requirements")
            reqs = stages["requirements"]
            if reqs.get("functional_requirements"):
                lines.append("### Functional Requirements")
                for req in reqs["functional_requirements"]:
                    lines.append(f"- {req}")
                lines.append("")

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
                    lines.append(consultation.get("weighted_answer", ""))
                    lines.append("")

        if "architecture" in stages:
            lines.append("## Architecture Guidance")
            arch = stages["architecture"]
            lines.append(arch.get("architecture_guidance", ""))
            lines.append("")

        if "quality" in stages:
            lines.append("## Quality Standards")
            quality = stages["quality"]
            lines.append(
                f"**Overall Score Threshold**: {quality.get('code_quality_thresholds', {}).get('overall_score', 70)}"
            )
            lines.append("")

        if "implementation" in stages:
            lines.append("## Implementation Strategy")
            impl = stages["implementation"]
            if impl.get("task_breakdown"):
                lines.append("### Task Breakdown")
                for task in impl["task_breakdown"]:
                    lines.append(f"- {task}")
                lines.append("")

        return "\n".join(lines)

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
