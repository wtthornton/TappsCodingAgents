"""
Enhancer Agent - Prompt enhancement utility that runs prompts through all TappsCodingAgents capabilities.
"""

# @ai-prime-directive: This file implements the Enhancer Agent with a 7-stage prompt enhancement pipeline.
# The enhancer transforms simple user prompts into comprehensive, context-aware specifications by analyzing
# intent, gathering requirements, consulting experts, and synthesizing enhanced prompts. This is a critical
# component of the Simple Mode build workflow.

# @ai-constraints:
# - Must maintain 7-stage pipeline order: Analysis → Requirements → Architecture → Codebase Context → Quality → Strategy → Synthesis
# - Each stage must produce valid output even if sub-components fail (graceful degradation)
# - Expert consultation is optional but recommended for domain-specific prompts
# - Codebase context extraction must respect MAX_FILE_SIZE_KB and MAX_RELATED_FILES limits
# - Performance: Full enhancement should complete in <30s for typical prompts

# @note[2025-01-15]: Enhancer is part of the instruction-based architecture per ADR-001.
# The 7-stage pipeline ensures comprehensive prompt enhancement while maintaining performance.
# See docs/architecture/decisions/ADR-001-instruction-based-architecture.md

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


def _safe_exception_str(e: Exception) -> str:
    """
    Safely convert exception to string, handling Unicode encoding errors.
    
    Args:
        e: Exception to convert
        
    Returns:
        Safe string representation of exception
    """
    try:
        return str(e)
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            # Use repr as fallback
            return repr(e)
        except Exception:
            # Last resort: just the exception type and message without encoding
            try:
                return f"{type(e).__name__}: {e.args[0] if e.args else 'Unknown error'}"
            except Exception:
                return f"{type(e).__name__}"
                return f"{type(e).__name__}"


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

    # Codebase context constants
    MAX_FILE_SIZE_KB = 100
    MAX_RELATED_FILES = 10
    MAX_PATTERNS = 5
    MAX_CROSS_REFERENCES = 5
    MAX_PROMPT_KEYWORDS = 5
    
    DEFAULT_EXCLUDE_PATTERNS = [
        "**/test_*.py",
        "**/__pycache__/**",
        "**/build/**",
        "**/dist/**",
        "**/.venv/**",
        "**/venv/**",
        "**/node_modules/**",
        "**/.git/**",
    ]

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

        # Context7 helper for Option 3 quality uplift (C1-C3, D1-D2, E2)
        self.context7 = None  # Lazy load in activate()

        # Enhancement state
        self.current_session: dict[str, Any] | None = None

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the enhancer agent."""
        await super().activate(project_root, offline_mode=offline_mode)
        await self.analyst.activate(project_root, offline_mode=offline_mode)

        # Initialize skill invoker if available
        try:
            from ...workflow.skill_invoker import SkillInvoker
            self.skill_invoker = SkillInvoker(project_root=project_root, use_api=False)
        except Exception:
            logger.debug("SkillInvoker not available; skills will be prepared but not executed")

        # Initialize Context7 helper for Option 3 quality uplift
        try:
            from ...context7.agent_integration import get_context7_helper
            self.context7 = get_context7_helper(self, self.config, project_root)
        except Exception as e:
            logger.debug(f"Context7 helper not available: {e}")

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
                    output_path.write_text(self._safe_json_dumps(result, indent=2))
                    if isinstance(result, dict):
                        result["output_file"] = str(output_path)
                else:
                    output_path.write_text(result, encoding="utf-8")
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
            error_msg = _safe_exception_str(e)
            return {"error": f"Enhancement failed: {error_msg}", "session_id": session_id}

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
                    output_path.write_text(self._safe_json_dumps(result, indent=2))
                    if isinstance(result, dict):
                        result["output_file"] = str(output_path)
                else:
                    output_path.write_text(result, encoding="utf-8")
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
            error_msg = _safe_exception_str(e)
            return {
                "error": f"Quick enhancement failed: {error_msg}",
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
            error_msg = _safe_exception_str(e)
            return {
                "error": f"Stage {stage} failed: {error_msg}",
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
        """
        Stage 1: Analyze prompt intent, scope, and domains.
        
        Option 3 (C1) Enhancement: Enhanced library detection with Context7 pre-fetching.
        """
        # C1: Detect libraries from prompt and pre-fetch Context7 docs
        # IMPORTANT: Only fetch docs for libraries that are:
        # 1. Explicitly mentioned in prompt (not just detected from keywords), OR
        # 2. Found in project dependencies (package.json, requirements.txt), OR
        # 3. Well-known libraries that are likely relevant
        detected_libraries = []
        context7_docs = {}
        
        if self.context7:
            try:
                # Detect libraries from prompt
                all_detected = self.context7.detect_libraries(prompt=prompt)
                
                # Filter: Only include libraries that are likely to be needed
                # Priority: Project deps > Explicit mentions > Well-known libraries
                if all_detected:
                    # Check which are in project files (high confidence)
                    project_libs = set(self.context7.detect_libraries(
                        code=None, prompt=None, error_message=None
                    ))
                    
                    # Filter to only libraries that are:
                    # - In project dependencies (installed packages), OR
                    # - Explicitly mentioned in prompt with library keywords, OR
                    # - Well-known libraries (from our validated list)
                    filtered_libraries = []
                    prompt_lower = prompt.lower()
                    
                    for lib in all_detected:
                        # Always include if it's in project dependencies
                        if lib in project_libs:
                            filtered_libraries.append(lib)
                        # Include if explicitly mentioned with library keywords
                        elif any(keyword in prompt_lower for keyword in [
                            f"{lib} library", f"{lib} framework", f"{lib} package",
                            f"using {lib}", f"with {lib}", f"import {lib}",
                            f"{lib} docs", f"{lib} documentation"
                        ]):
                            filtered_libraries.append(lib)
                        # Include well-known libraries if detected
                        elif self.context7.is_well_known_library(lib):
                            filtered_libraries.append(lib)
                    
                    detected_libraries = filtered_libraries
                    
                    # Only pre-fetch if we have filtered libraries
                    if detected_libraries:
                        logger.debug(f"C1: Filtered {len(all_detected)} detected libraries to {len(detected_libraries)} relevant ones")
                        context7_docs = await self.context7.get_documentation_for_libraries(
                            libraries=detected_libraries,
                            topic=None,  # Get general docs first
                            use_fuzzy_match=True
                        )
                        logger.debug(f"C1: Fetched {sum(1 for v in context7_docs.values() if v)} docs for {len(detected_libraries)} libraries")
                    else:
                        logger.debug(f"C1: No relevant libraries to fetch (filtered {len(all_detected)} detected libraries)")
            except Exception as e:
                logger.debug(f"C1: Library detection failed: {e}")

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

        # Perform analysis using analyst agent (now has analyze-prompt command)
        try:
            # Use analyst agent to perform analysis
            analysis_result = await self.analyst.run(
                "analyze-prompt",
                description=prompt,
            )
            
            # Check for error in result
            if isinstance(analysis_result, dict) and "error" in analysis_result:
                logger.debug(f"Analyst returned error: {analysis_result['error']}, using fallback analysis")
                parsed = self._fallback_analysis(prompt)
                analysis_text = json.dumps(parsed, indent=2)
            elif isinstance(analysis_result, dict) and analysis_result.get("success"):
                # Analyst returned instruction/skill_command (Cursor mode)
                # The actual analysis will be performed by the Cursor Skill
                # For now, use fallback but note that skill will execute
                logger.debug("Analyst returned instruction for Cursor Skill execution, using fallback for immediate results")
                parsed = self._fallback_analysis(prompt)
                analysis_text = analysis_result.get("analysis", json.dumps(parsed, indent=2))
            else:
                # Extract analysis text from result
                analysis_text = ""
                if isinstance(analysis_result, dict):
                    # Check for various possible response formats
                    analysis_text = (
                        analysis_result.get("analysis", "") or 
                        analysis_result.get("result", "") or 
                        analysis_result.get("response", "") or
                        str(analysis_result)
                    )
                else:
                    analysis_text = str(analysis_result)
                
                # Check if we got a valid response (not an error dict string)
                if analysis_text and not (analysis_text.startswith("{'error'") or '"error"' in analysis_text):
                    # Parse the response to extract structured data
                    parsed = self._parse_analysis_response(analysis_text)
                    # If parsing failed or returned empty, use fallback
                    if not parsed or (parsed.get("intent") == "unknown" and parsed.get("scope") == "unknown"):
                        logger.debug("Analysis parsing returned empty/unknown values, using fallback")
                        parsed = self._fallback_analysis(prompt)
                else:
                    logger.debug("Analysis result contains error, using fallback")
                    parsed = self._fallback_analysis(prompt)
        except Exception as e:
            logger.debug(f"Analysis stage failed: {e}, using fallback analysis")
            parsed = self._fallback_analysis(prompt)
            analysis_text = json.dumps(parsed, indent=2)
        
        # Merge detected libraries into technologies
        if detected_libraries:
            technologies = parsed.get("technologies", [])
            technologies.extend([lib for lib in detected_libraries if lib not in technologies])
            parsed["technologies"] = technologies
        
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
            # C1 Enhancement: Library detection and Context7 docs
            "detected_libraries": detected_libraries,
            "context7_docs": {k: v is not None for k, v in context7_docs.items()},  # Store availability only
        }

    async def _stage_requirements(
        self, prompt: str, analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Stage 2: Enrich requirements with analyst and experts.
        
        Option 3 (C2) Enhancement: Requirements with Context7 best practices.
        """
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
        
        # C2: Enhance requirements with Context7 best practices
        library_best_practices = {}
        api_compatibility = {}
        detected_libraries = analysis.get("detected_libraries", [])
        
        if self.context7 and detected_libraries:
            try:
                # Fetch best practices for each detected library
                for lib in detected_libraries:
                    best_practices = await self.context7.get_documentation(
                        library=lib,
                        topic="best-practices",
                        use_fuzzy_match=True
                    )
                    
                    if best_practices:
                        library_best_practices[lib] = {
                            "content_preview": best_practices.get("content", "")[:500] if best_practices.get("content") else "",
                            "source": best_practices.get("source", "unknown"),
                        }
                        
                        # Check API compatibility (basic check)
                        api_compatibility[lib] = {
                            "docs_available": True,
                            "best_practices_available": True,
                        }
                    else:
                        api_compatibility[lib] = {
                            "docs_available": False,
                            "best_practices_available": False,
                        }
                
                logger.debug(f"C2: Enhanced requirements with best practices for {len(library_best_practices)} libraries")
            except Exception as e:
                logger.debug(f"C2: Best practices enhancement failed: {e}")
        
        # Try to execute the skill if we have a skill invoker and instruction
        if self.skill_invoker and "requirements" in requirements_result:
            req_data = requirements_result["requirements"]
            if "skill_command" in req_data:
                try:
                    # Try to execute the skill command
                    skill_result = await self._try_execute_skill(
                        req_data["skill_command"],
                        worktree_path=self._project_root if hasattr(self, '_project_root') and self._project_root else Path.cwd(),
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
            # C2 Enhancement: Context7 best practices
            "library_best_practices": library_best_practices,
            "api_compatibility": api_compatibility,
        }

    async def _stage_architecture(
        self, prompt: str, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Stage 3: Architecture guidance.
        
        Option 3 (C3) Enhancement: Architecture with Context7 patterns.
        """
        if self.architect is None:
            from ...agents.architect.agent import ArchitectAgent

            self.architect = ArchitectAgent(config=self.config)
            await self.architect.activate()

        # Get architecture guidance
        arch_result = await self.architect.run(
            "design-system",
            requirements=prompt,
            context=self._safe_json_dumps(requirements, indent=2),
        )

        # C3: Enhance architecture with Context7 patterns
        library_patterns = {}
        integration_examples = {}
        
        # Get libraries from requirements (set in C2) or detect from prompt
        # IMPORTANT: Only fetch architecture docs for libraries that are:
        # 1. In project dependencies, OR
        # 2. Explicitly mentioned in requirements, OR
        # 3. Well-known libraries
        detected_libraries = []
        if "api_compatibility" in requirements:
            detected_libraries = list(requirements.get("api_compatibility", {}).keys())
        elif self.context7:
            # Only detect libraries that are likely relevant (same filtering as C1)
            all_detected = self.context7.detect_libraries(prompt=prompt)
            project_libs = set(self.context7.detect_libraries(
                code=None, prompt=None, error_message=None
            ))
            
            # Filter to only relevant libraries
            filtered = []
            prompt_lower = prompt.lower()
            for lib in all_detected:
                if (lib in project_libs or 
                    self.context7.is_well_known_library(lib) or
                    any(keyword in prompt_lower for keyword in [
                        f"{lib} library", f"{lib} framework", f"using {lib}"
                    ])):
                    filtered.append(lib)
            detected_libraries = filtered
        
        if self.context7 and detected_libraries:
            try:
                # Fetch architecture patterns for each library
                for lib in detected_libraries:
                    arch_patterns = await self.context7.get_documentation(
                        library=lib,
                        topic="architecture",
                        use_fuzzy_match=True
                    )
                    
                    if arch_patterns:
                        library_patterns[lib] = {
                            "content_preview": arch_patterns.get("content", "")[:500] if arch_patterns.get("content") else "",
                            "source": arch_patterns.get("source", "unknown"),
                        }
                        
                        # Extract integration examples (basic extraction)
                        content = arch_patterns.get("content", "")
                        if content:
                            # Look for code examples in content
                            if "example" in content.lower() or "integration" in content.lower():
                                integration_examples[lib] = {
                                    "has_examples": True,
                                    "pattern_available": True,
                                }
                    else:
                        # Try alternative topics
                        for alt_topic in ["patterns", "integration", "design"]:
                            alt_patterns = await self.context7.get_documentation(
                                library=lib,
                                topic=alt_topic,
                                use_fuzzy_match=True
                            )
                            if alt_patterns:
                                library_patterns[lib] = {
                                    "content_preview": alt_patterns.get("content", "")[:500] if alt_patterns.get("content") else "",
                                    "source": alt_patterns.get("source", "unknown"),
                                    "topic": alt_topic,
                                }
                                break
                
                logger.debug(f"C3: Enhanced architecture with patterns for {len(library_patterns)} libraries")
            except Exception as e:
                logger.debug(f"C3: Architecture patterns enhancement failed: {e}")

        return {
            "system_design": arch_result.get("architecture", {}),
            "design_patterns": [],
            "technology_recommendations": [],
            "architecture_guidance": arch_result.get("guidance", ""),
            # C3 Enhancement: Context7 architecture patterns
            "library_patterns": library_patterns,
            "integration_examples": integration_examples,
        }

    async def _stage_codebase_context(
        self, prompt: str, analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Stage 4: Inject codebase context."""
        try:
            # Find related files using semantic/keyword search
            related_files = await self._find_related_files(prompt, analysis)
            
            # Extract patterns from related files
            existing_patterns = await self._extract_patterns(related_files)
            
            # Find cross-references between files
            cross_references = await self._find_cross_references(related_files)
            
            # Generate context summary
            codebase_context = self._generate_context_summary(
                related_files, existing_patterns, cross_references
            )
            
            return {
                "related_files": related_files,
                "existing_patterns": existing_patterns,
                "cross_references": cross_references,
                "codebase_context": codebase_context,
                "file_count": len(related_files),
            }
        except Exception as e:
            logger.warning(f"Codebase context injection failed: {e}", exc_info=True)
            # Return empty context on failure (don't break enhancement pipeline)
            return {
                "related_files": [],
                "existing_patterns": [],
                "cross_references": [],
                "codebase_context": "No codebase context available (search failed)",
                "file_count": 0,
            }
    
    async def _find_related_files(
        self, prompt: str, analysis: dict[str, Any]
    ) -> list[str]:
        """
        Find related files using semantic/keyword search.
        
        Args:
            prompt: Original user prompt
            analysis: Analysis stage output (contains domains, technologies)
        
        Returns:
            List of file paths (max 10), sorted by relevance
        """
        related_files: set[str] = set()
        project_root = self._project_root if hasattr(self, '_project_root') and self._project_root else Path.cwd()
        max_files = self.MAX_RELATED_FILES
        
        try:
            domains = analysis.get("domains", [])
            technologies = analysis.get("technologies", [])
            
            # Build search terms from domains and technologies
            search_terms: list[str] = []
            search_terms.extend(domains)
            search_terms.extend(technologies)
            
            # Also extract keywords from prompt
            prompt_keywords = [
                word.lower()
                for word in prompt.split()
                if len(word) > 3 and word.isalnum()
            ]
            search_terms.extend(prompt_keywords[:self.MAX_PROMPT_KEYWORDS])
            
            if not search_terms:
                logger.debug("No search terms available for codebase context")
                return []
            
            # Search for Python files in project
            # Exclude test files, generated files, build artifacts
            exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS
            
            # Find Python files in project
            python_files: list[Path] = []
            for pattern in ["**/*.py"]:
                try:
                    files = list(project_root.glob(pattern))
                    python_files.extend(files)
                except Exception as e:
                    logger.debug(f"Failed to glob pattern {pattern}: {e}")
            
            # Filter out excluded files
            filtered_files: list[Path] = []
            for file_path in python_files:
                file_str = str(file_path)
                if any(
                    file_path.match(pattern) or pattern.replace("**/", "") in file_str
                    for pattern in exclude_patterns
                ):
                    continue
                # Skip large files
                try:
                    if file_path.stat().st_size > self.MAX_FILE_SIZE_KB * 1024:
                        continue
                except Exception:
                    continue
                filtered_files.append(file_path)
            
            # Score files by relevance (simple keyword matching)
            scored_files: list[tuple[Path, float]] = []
            for file_path in filtered_files:
                score = 0.0
                try:
                    # Read file content for keyword matching
                    content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                    file_name = file_path.name.lower()
                    file_path_str = str(file_path).lower()
                    
                    # Score based on search terms
                    for term in search_terms:
                        term_lower = term.lower()
                        # Higher score for filename matches
                        if term_lower in file_name:
                            score += 3.0
                        # Medium score for path matches
                        elif term_lower in file_path_str:
                            score += 2.0
                        # Lower score for content matches
                        elif term_lower in content:
                            score += 1.0
                except Exception as e:
                    logger.debug(f"Failed to read file {file_path}: {e}")
                    continue
                
                if score > 0:
                    scored_files.append((file_path, score))
            
            # Sort by score (highest first) and limit
            scored_files.sort(key=lambda x: x[1], reverse=True)
            related_files = {str(path) for path, _ in scored_files[:max_files]}
            
            logger.info(f"Found {len(related_files)} related files for codebase context")
            return list(related_files)
            
        except Exception as e:
            logger.warning(f"File discovery failed: {e}", exc_info=True)
            return []
    
    async def _extract_patterns(
        self, related_files: list[str]
    ) -> list[dict[str, Any]]:
        """
        Extract patterns from related files.
        
        Args:
            related_files: List of file paths to analyze
        
        Returns:
            List of pattern dictionaries
        """
        patterns: list[dict[str, Any]] = []
        
        if not related_files:
            return patterns
        
        try:
            import ast
            
            # Track patterns across files
            import_patterns: dict[str, int] = {}
            class_patterns: dict[str, int] = {}
            function_patterns: dict[str, int] = {}
            
            for file_path_str in related_files[:self.MAX_RELATED_FILES]:
                try:
                    file_path = Path(file_path_str)
                    if not file_path.exists():
                        continue
                    
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    
                    # Parse AST
                    try:
                        tree = ast.parse(content, filename=str(file_path))
                    except SyntaxError:
                        continue
                    
                    # Extract import patterns
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                import_path = alias.name.split(".")[0]
                                import_patterns[import_path] = import_patterns.get(import_path, 0) + 1
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                import_path = node.module.split(".")[0]
                                import_patterns[import_path] = import_patterns.get(import_path, 0) + 1
                        
                        # Extract class patterns
                        if isinstance(node, ast.ClassDef):
                            class_name = node.name
                            # Detect naming patterns
                            if class_name.endswith("Service"):
                                class_patterns["Service"] = class_patterns.get("Service", 0) + 1
                            elif class_name.endswith("Agent"):
                                class_patterns["Agent"] = class_patterns.get("Agent", 0) + 1
                            elif class_name.endswith("Router"):
                                class_patterns["Router"] = class_patterns.get("Router", 0) + 1
                        
                        # Extract function patterns
                        if isinstance(node, ast.FunctionDef):
                            func_name = node.name
                            if func_name.startswith("test_"):
                                function_patterns["test_"] = function_patterns.get("test_", 0) + 1
                            elif func_name.startswith("async def"):
                                function_patterns["async"] = function_patterns.get("async", 0) + 1
                
                except Exception as e:
                    logger.debug(f"Failed to extract patterns from {file_path_str}: {e}")
                    continue
            
            # Convert to pattern dictionaries
            # Architectural patterns (common imports)
            common_imports = [
                imp for imp, count in import_patterns.items()
                if count >= 2 and imp not in ["typing", "pathlib", "logging"]
            ]
            if common_imports:
                patterns.append({
                    "type": "architectural",
                    "name": "Common Import Patterns",
                    "description": f"Commonly imported modules: {', '.join(common_imports[:5])}",
                    "examples": related_files[:3],
                    "confidence": min(1.0, len(common_imports) / 5.0),
                })
            
            # Code structure patterns
            if class_patterns:
                structure_types = [t for t, count in class_patterns.items() if count >= 2]
                if structure_types:
                    patterns.append({
                        "type": "structure",
                        "name": "Class Structure Patterns",
                        "description": f"Common class types: {', '.join(structure_types)}",
                        "examples": related_files[:3],
                        "confidence": min(1.0, len(structure_types) / 3.0),
                    })
            
            logger.debug(f"Extracted {len(patterns)} patterns from {len(related_files)} files")
            
        except Exception as e:
            logger.warning(f"Pattern extraction failed: {e}", exc_info=True)
        
        return patterns
    
    async def _find_cross_references(
        self, related_files: list[str]
    ) -> list[dict[str, Any]]:
        """
        Find cross-references between files.
        
        Args:
            related_files: List of file paths to analyze
        
        Returns:
            List of cross-reference dictionaries
        """
        cross_references: list[dict[str, Any]] = []
        
        if not related_files:
            return cross_references
        
        try:
            import ast
            
            # Build file to module mapping
            file_modules: dict[str, str] = {}
            for file_path_str in related_files:
                try:
                    file_path = Path(file_path_str)
                    # Convert file path to module path
                    # e.g., tapps_agents/agents/enhancer/agent.py -> tapps_agents.agents.enhancer.agent
                    parts = file_path.parts
                    if "tapps_agents" in parts:
                        idx = parts.index("tapps_agents")
                        module_parts = parts[idx:-1]  # Exclude filename
                        module_name = ".".join(module_parts)
                        file_modules[file_path_str] = module_name
                except Exception:
                    continue
            
            # Analyze imports in each file
            for file_path_str in related_files:
                try:
                    file_path = Path(file_path_str)
                    if not file_path.exists():
                        continue
                    
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    
                    try:
                        tree = ast.parse(content, filename=str(file_path))
                    except SyntaxError:
                        continue
                    
                    # Extract imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module:
                                # Check if imported module matches any related file
                                for target_file, target_module in file_modules.items():
                                    if target_file != file_path_str and node.module.startswith(target_module):
                                        cross_references.append({
                                            "source": str(file_path),
                                            "target": target_file,
                                            "type": "import",
                                            "details": f"imports from {node.module}",
                                        })
                
                except Exception as e:
                    logger.debug(f"Failed to analyze cross-references in {file_path_str}: {e}")
                    continue
            
            logger.debug(f"Found {len(cross_references)} cross-references")
            
        except Exception as e:
            logger.warning(f"Cross-reference detection failed: {e}", exc_info=True)
        
        return cross_references
    
    def _generate_context_summary(
        self,
        related_files: list[str],
        existing_patterns: list[dict[str, Any]],
        cross_references: list[dict[str, Any]],
    ) -> str:
        """
        Generate human-readable context summary.
        
        Args:
            related_files: List of related file paths
            existing_patterns: List of extracted patterns
            cross_references: List of cross-references
        
        Returns:
            Markdown-formatted context summary
        """
        lines: list[str] = []
        lines.append("## Codebase Context\n")
        
        # Related files section
        if related_files:
            lines.append("### Related Files")
            for file_path in related_files[:self.MAX_RELATED_FILES]:
                # Get relative path for cleaner display
                try:
                    project_root = self._project_root if hasattr(self, '_project_root') and self._project_root else Path.cwd()
                    rel_path = Path(file_path).relative_to(project_root)
                    lines.append(f"- `{rel_path}`")
                except Exception:
                    lines.append(f"- `{file_path}`")
            lines.append("")
        else:
            lines.append("### Related Files")
            lines.append("- No related files found")
            lines.append("")
        
        # Existing patterns section
        if existing_patterns:
            lines.append("### Existing Patterns")
            for pattern in existing_patterns[:self.MAX_PATTERNS]:
                pattern_type = pattern.get("type", "unknown")
                pattern_name = pattern.get("name", "Unknown Pattern")
                pattern_desc = pattern.get("description", "")
                lines.append(f"- **{pattern_name}** ({pattern_type}): {pattern_desc}")
            lines.append("")
        else:
            lines.append("### Existing Patterns")
            lines.append("- No patterns extracted")
            lines.append("")
        
        # Cross-references section
        if cross_references:
            lines.append("### Cross-References")
            for ref in cross_references[:self.MAX_CROSS_REFERENCES]:
                source = ref.get("source", "")
                target = ref.get("target", "")
                ref_type = ref.get("type", "unknown")
                details = ref.get("details", "")
                try:
                    project_root = self._project_root if hasattr(self, '_project_root') and self._project_root else Path.cwd()
                    source_rel = Path(source).relative_to(project_root)
                    target_rel = Path(target).relative_to(project_root)
                    lines.append(f"- `{source_rel}` → `{target_rel}` ({ref_type})")
                    if details:
                        lines.append(f"  - {details}")
                except Exception:
                    lines.append(f"- `{source}` → `{target}` ({ref_type})")
            lines.append("")
        else:
            lines.append("### Cross-References")
            lines.append("- No cross-references found")
            lines.append("")
        
        # Context summary
        lines.append("### Context Summary")
        if related_files:
            lines.append(
                f"Found {len(related_files)} related files in the codebase. "
                f"Extracted {len(existing_patterns)} patterns and "
                f"{len(cross_references)} cross-references. "
                "Use these as reference when implementing new features."
            )
        else:
            lines.append(
                "No codebase context available. This may be a new project or "
                "the search did not find relevant files."
            )
        
        return "\n".join(lines)

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

Analysis: {self._safe_json_dumps(stages.get('analysis', {}), indent=2)}
Requirements: {self._safe_json_dumps(stages.get('requirements', {}), indent=2)}
Architecture: {self._safe_json_dumps(stages.get('architecture', {}), indent=2)}
Quality: {self._safe_json_dumps(stages.get('quality', {}), indent=2)}
Implementation: {self._safe_json_dumps(stages.get('implementation', {}), indent=2)}

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
                    "stages": self._safe_json_dumps(stages),
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

    def _safe_json_dumps(self, obj: Any, indent: int = 2) -> str:
        """
        Safely serialize object to JSON, handling circular references.
        
        Args:
            obj: Object to serialize
            indent: JSON indentation level
            
        Returns:
            JSON string representation
        """
        def _make_serializable(o: Any, seen: set[int] | None = None) -> Any:
            """Recursively convert object to JSON-serializable format."""
            if seen is None:
                seen = set()
            
            # Handle primitives first (no circular reference risk)
            if isinstance(o, (str, int, float, bool, type(None))):
                return o
            
            # Handle datetime (immutable)
            if isinstance(o, datetime):
                return o.isoformat()
            
            # Handle Path objects (immutable)
            if isinstance(o, Path):
                return str(o)
            
            # For mutable objects, check for circular references
            obj_id = id(o)
            if obj_id in seen:
                return "<circular reference>"
            
            try:
                # Handle dict
                if isinstance(o, dict):
                    seen.add(obj_id)
                    result = {}
                    for k, v in o.items():
                        # Skip non-string keys (convert to string)
                        key = str(k) if not isinstance(k, (str, int, float, bool, type(None))) else k
                        result[key] = _make_serializable(v, seen)
                    seen.remove(obj_id)
                    return result
                
                # Handle list/tuple
                if isinstance(o, (list, tuple)):
                    seen.add(obj_id)
                    result = [_make_serializable(item, seen) for item in o]
                    seen.remove(obj_id)
                    return result
                
                # For other objects, try to convert to dict or string
                if hasattr(o, '__dict__'):
                    seen.add(obj_id)
                    try:
                        result = _make_serializable(o.__dict__, seen)
                        seen.remove(obj_id)
                        return result
                    except Exception:
                        seen.remove(obj_id)
                        return str(o)
                
                # Fallback: convert to string
                return str(o)
                
            except Exception as e:
                # If anything fails, return error string
                seen.discard(obj_id)
                return f"<serialization error: {str(e)}>"
        
        try:
            serializable_obj = _make_serializable(obj)
            return json.dumps(serializable_obj, indent=indent, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to serialize session: {e}")
            # Last resort: return minimal error representation
            return json.dumps({"error": f"Serialization failed: {str(e)}"}, indent=indent)

    def _save_session(self, session_id: str, session: dict[str, Any]):
        """Save session to disk."""
        sessions_dir = Path.cwd() / ".tapps-agents" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        session_file = sessions_dir / f"{session_id}.json"
        session_file.write_text(self._safe_json_dumps(session, indent=2), encoding="utf-8")

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
            # Create a clean copy to avoid circular references
            # Use _safe_json_dumps to serialize and then parse back to ensure no circular refs
            try:
                # Create a clean dict structure without circular references
                stages_copy = {}
                for stage_name, stage_data in session["stages"].items():
                    if isinstance(stage_data, dict):
                        # Deep copy dict to break any circular references
                        stages_copy[stage_name] = self._clean_dict(stage_data)
                    else:
                        stages_copy[stage_name] = stage_data
                
                metadata_copy = {}
                for key, value in session["metadata"].items():
                    if isinstance(value, dict):
                        metadata_copy[key] = self._clean_dict(value)
                    else:
                        metadata_copy[key] = value
                
                return {
                    "original_prompt": session["metadata"]["original_prompt"],
                    "enhanced_prompt": synthesis.get("enhanced_prompt", ""),
                    "stages": stages_copy,
                    "metadata": metadata_copy,
                }
            except Exception as e:
                logger.warning(f"Error cleaning output dict: {e}, using fallback")
                # Fallback: return minimal structure
                return {
                    "original_prompt": session["metadata"].get("original_prompt", ""),
                    "enhanced_prompt": synthesis.get("enhanced_prompt", ""),
                    "stages": {},
                    "metadata": {"created_at": session["metadata"].get("created_at", "")},
                }
        else:  # markdown
            enhanced = synthesis.get("enhanced_prompt", "")
            if not enhanced:
                # Fallback: create markdown from stages
                enhanced = self._create_markdown_from_stages(session)
            return enhanced

    def _clean_dict(self, obj: Any, seen: set[int] | None = None) -> Any:
        """
        Recursively clean a dict to remove circular references.
        
        Args:
            obj: Object to clean
            seen: Set of object IDs already seen (for cycle detection)
            
        Returns:
            Cleaned object without circular references
        """
        if seen is None:
            seen = set()
        
        # Handle primitives
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle Path
        if isinstance(obj, Path):
            return str(obj)
        
        # Check for circular reference
        obj_id = id(obj)
        if obj_id in seen:
            return "<circular reference>"
        
        # Handle dict
        if isinstance(obj, dict):
            seen.add(obj_id)
            result = {}
            for k, v in obj.items():
                key = str(k) if not isinstance(k, (str, int, float, bool, type(None))) else k
                result[key] = self._clean_dict(v, seen)
            seen.remove(obj_id)
            return result
        
        # Handle list/tuple
        if isinstance(obj, (list, tuple)):
            seen.add(obj_id)
            result = [self._clean_dict(item, seen) for item in obj]
            seen.remove(obj_id)
            return tuple(result) if isinstance(obj, tuple) else result
        
        # Handle objects with __dict__
        if hasattr(obj, '__dict__'):
            seen.add(obj_id)
            try:
                result = self._clean_dict(obj.__dict__, seen)
                seen.remove(obj_id)
                return result
            except Exception:
                seen.remove(obj_id)
                return str(obj)
        
        # Fallback: convert to string
        return str(obj)

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
            
            # Always show domains section, even if empty
            if domains:
                lines.append(f"- **Detected Domains**: {', '.join(domains)}")
            else:
                lines.append("- **Detected Domains**: None detected")
            
            # Always show technologies section, even if empty
            if technologies:
                lines.append(f"- **Technologies**: {', '.join(technologies)}")
            else:
                lines.append("- **Technologies**: None detected")
            
            # Add raw analysis text if available for debugging
            if analysis.get('analysis') and isinstance(analysis.get('analysis'), str):
                raw_analysis = analysis.get('analysis')
                # Only show if it's not just the JSON dump
                if len(raw_analysis) > 200 or '"intent"' not in raw_analysis:
                    lines.append("")
                    lines.append("### Analysis Details")
                    lines.append("```")
                    lines.append(raw_analysis[:500] + ("..." if len(raw_analysis) > 500 else ""))
                    lines.append("```")
            
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
            else:
                lines.append("### Functional Requirements")
                lines.append("- *No functional requirements extracted yet. This will be populated during requirements gathering stage.*")
                lines.append("")
            
            # Non-functional Requirements
            if reqs.get("non_functional_requirements"):
                lines.append("### Non-Functional Requirements")
                for req in reqs["non_functional_requirements"]:
                    lines.append(f"- {req}")
                lines.append("")
            else:
                lines.append("### Non-Functional Requirements")
                lines.append("- *No non-functional requirements extracted yet.*")
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
            else:
                lines.append("*Architecture guidance will be generated during the architecture stage.*")
                lines.append("")
            
            # System Design
            if arch.get("system_design"):
                lines.append("### System Design")
                if isinstance(arch["system_design"], dict):
                    if arch["system_design"]:  # Check if dict is not empty
                        for key, value in arch["system_design"].items():
                            lines.append(f"**{key.title()}**: {value}")
                    else:
                        lines.append("*System design details pending.*")
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

    def _fallback_analysis(self, prompt: str) -> dict[str, Any]:
        """
        Fallback keyword-based analysis when MAL/LLM unavailable or analyst fails.
        
        Performs basic analysis using keyword matching and heuristics.
        
        Args:
            prompt: User prompt to analyze
            
        Returns:
            Dictionary with intent, scope, workflow_type, domains, technologies, complexity
        """
        prompt_lower = prompt.lower()
        word_count = len(prompt.split())
        
        # Detect intent
        if any(word in prompt_lower for word in ["fix", "bug", "error", "issue", "problem", "broken"]):
            intent = "bug-fix"
        elif any(word in prompt_lower for word in ["refactor", "improve", "optimize", "update", "modernize"]):
            intent = "refactor"
        elif any(word in prompt_lower for word in ["document", "docs", "readme", "documentation"]):
            intent = "documentation"
        elif any(word in prompt_lower for word in ["test", "tests", "testing", "coverage"]):
            intent = "testing"
        elif any(word in prompt_lower for word in ["create", "add", "build", "implement", "develop", "new"]):
            intent = "feature"
        else:
            intent = "feature"  # Default
        
        # Estimate scope (rough heuristic based on prompt length and keywords)
        if word_count < 15:
            scope = "small"
        elif word_count < 50:
            scope = "medium"
        else:
            scope = "large"
        
        # Detect workflow type
        if any(word in prompt_lower for word in ["new", "create", "build", "add", "implement"]):
            workflow_type = "greenfield"
        elif any(word in prompt_lower for word in ["existing", "current", "modify", "change", "update", "enhance"]):
            workflow_type = "brownfield"
        elif intent == "bug-fix":
            workflow_type = "quick-fix"
        else:
            workflow_type = "greenfield"
        
        # Detect domains (keyword-based)
        domains = []
        domain_keywords = {
            "security": ["security", "auth", "authentication", "authorization", "encrypt", "ssl", "jwt", "token"],
            "user-management": ["user", "account", "profile", "login", "logout", "session", "register"],
            "database": ["database", "db", "sql", "query", "model", "schema", "migration"],
            "api": ["api", "endpoint", "route", "request", "response", "rest", "graphql"],
            "ui": ["ui", "interface", "page", "component", "frontend", "tab", "navigation", "blueprint"],
            "integration": ["integrate", "integration", "service", "microservice", "connect"],
        }
        for domain, keywords in domain_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                domains.append(domain)
        
        # Detect technologies (keyword-based)
        technologies = []
        tech_keywords = {
            "Python": ["python", "py", "fastapi", "flask", "django", "pytest"],
            "JavaScript": ["javascript", "js", "node", "react", "vue", "angular"],
            "TypeScript": ["typescript", "ts"],
            "FastAPI": ["fastapi"],
            "React": ["react"],
            "Playwright": ["playwright"],
            "Puppeteer": ["puppeteer"],
            "Home Assistant": ["home assistant", "homeassistant", "ha"],
        }
        for tech, keywords in tech_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                if tech not in technologies:
                    technologies.append(tech)
        
        # Estimate complexity
        complexity_keywords = ["complex", "advanced", "sophisticated", "integrate", "system", "multiple", "scoring", "pattern"]
        if any(keyword in prompt_lower for keyword in complexity_keywords) or word_count > 60:
            complexity = "high"
        elif word_count < 20:
            complexity = "low"
        else:
            complexity = "medium"
        
        return {
            "intent": intent,
            "scope": scope,
            "workflow_type": workflow_type,
            "domains": domains if domains else [],
            "technologies": technologies if technologies else [],
            "complexity": complexity,
        }
    
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
        
        # Try to find JSON in code blocks (improved regex to handle nested objects)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                # Validate that we got meaningful data
                if parsed and isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object directly (improved to handle nested structures)
        # Look for balanced braces
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(response_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx >= 0:
                    try:
                        json_str = response_text[start_idx:i+1]
                        parsed = json.loads(json_str)
                        if parsed and isinstance(parsed, dict) and len(parsed) > 0:
                            return parsed
                    except json.JSONDecodeError:
                        pass
                    start_idx = -1
        
        # Fallback: try to extract fields using regex patterns
        # Extract intent (handle multiple formats: "intent": "value", intent: value, Intent: value)
        intent_patterns = [
            r'"intent"\s*:\s*"([^"]+)"',
            r"'intent'\s*:\s*'([^']+)'",
            r'intent[:\s]+([a-z-]+)',
            r'Intent[:\s]+([a-z-]+)',
        ]
        for pattern in intent_patterns:
            intent_match = re.search(pattern, response_text, re.IGNORECASE)
            if intent_match:
                parsed["intent"] = intent_match.group(1).strip() if intent_match.group(1) else "unknown"
                break
        
        # Extract scope
        scope_patterns = [
            r'"scope"\s*:\s*"([^"]+)"',
            r"'scope'\s*:\s*'([^']+)'",
            r'scope[:\s]+(small|medium|large)',
            r'Scope[:\s]+(small|medium|large)',
        ]
        for pattern in scope_patterns:
            scope_match = re.search(pattern, response_text, re.IGNORECASE)
            if scope_match:
                parsed["scope"] = scope_match.group(1).strip() if scope_match.group(1) else "unknown"
                break
        
        # Extract workflow_type
        workflow_patterns = [
            r'"workflow_type"\s*:\s*"([^"]+)"',
            r"'workflow_type'\s*:\s*'([^']+)'",
            r'"workflowType"\s*:\s*"([^"]+)"',
            r'workflow[:\s]+(greenfield|brownfield|quick-fix|quickfix)',
            r'Workflow[:\s]+(greenfield|brownfield|quick-fix|quickfix)',
        ]
        for pattern in workflow_patterns:
            workflow_match = re.search(pattern, response_text, re.IGNORECASE)
            if workflow_match:
                parsed["workflow_type"] = workflow_match.group(1).strip() if workflow_match.group(1) else "unknown"
                break
        
        # Extract domains (list) - handle various formats
        domains_patterns = [
            r'"domains"\s*:\s*\[(.*?)\]',
            r"'domains'\s*:\s*\[(.*?)\]",
            r'"domain"\s*:\s*\[(.*?)\]',  # singular form
            r'domains?[:\s]+\[(.*?)\]',  # with or without quotes
        ]
        for pattern in domains_patterns:
            domains_match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if domains_match:
                domains_str = domains_match.group(1)
                # Handle both quoted and unquoted items
                domains = []
                for item in domains_str.split(','):
                    cleaned = item.strip().strip('"\'[]')
                    if cleaned:
                        domains.append(cleaned)
                if domains:
                    parsed["domains"] = domains
                break
        
        # Extract technologies (list) - handle various formats
        tech_patterns = [
            r'"technologies"\s*:\s*\[(.*?)\]',
            r"'technologies'\s*:\s*\[(.*?)\]",
            r'"technology"\s*:\s*\[(.*?)\]',  # singular form
            r'technolog(?:ies|y)[:\s]+\[(.*?)\]',  # flexible matching
        ]
        for pattern in tech_patterns:
            tech_match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if tech_match:
                tech_str = tech_match.group(1)
                technologies = []
                for item in tech_str.split(','):
                    cleaned = item.strip().strip('"\'[]')
                    if cleaned:
                        technologies.append(cleaned)
                if technologies:
                    parsed["technologies"] = technologies
                break
        
        # Extract complexity
        complexity_patterns = [
            r'"complexity"\s*:\s*"([^"]+)"',
            r"'complexity'\s*:\s*'([^']+)'",
            r'complexity[:\s]+(low|medium|high)',
            r'Complexity[:\s]+(low|medium|high)',
        ]
        for pattern in complexity_patterns:
            complexity_match = re.search(pattern, response_text, re.IGNORECASE)
            if complexity_match:
                parsed["complexity"] = complexity_match.group(1).strip().lower() if complexity_match.group(1) else "medium"
                break
        
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
