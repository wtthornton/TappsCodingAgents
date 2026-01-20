"""
Prompt enhancement middleware for automatic prompt enhancement in CLI commands.

This module provides middleware that automatically enhances user prompts
before they reach individual agents, ensuring high-quality code generation.
"""

import asyncio
from argparse import Namespace
from typing import Any

from ...agents.enhancer.agent import EnhancerAgent
from ...core.config import AutoEnhancementConfig, load_config


# Mapping of agent.command -> prompt argument name. Value None means do not enhance.
# Intentional exclusions: (debugger, debug) — error text must stay exact;
# (implementer, refactor) — instructions are usually narrow; improver improve — not added.
# architect and designer default to enabled: False in AutoEnhancementConfig.commands.
PROMPT_ARGUMENT_MAP: dict[tuple[str, str], str] = {
    ("implementer", "implement"): "specification",
    ("implementer", "generate-code"): "specification",
    ("planner", "plan"): "description",
    ("planner", "create-story"): "description",
    ("architect", "design-system"): "requirements",
    ("designer", "design-api"): "requirements",
    ("designer", "design-data-model"): "requirements",
    ("designer", "design-system"): "project_description",
    ("designer", "define-design-system"): "project_description",
    ("analyst", "gather-requirements"): "description",
    # Skip enhancement: error text and narrow refactor instructions
    ("debugger", "debug"): None,
    ("implementer", "refactor"): None,
}


def detect_prompt_argument(args: Namespace) -> tuple[str, str] | None:
    """
    Detect prompt argument in CLI command arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (argument_name, argument_value) if found, None otherwise
    """
    agent = getattr(args, "agent", None)
    command = getattr(args, "command", None)

    if not agent or not command:
        return None

    # Normalize command (remove * prefix if present)
    if command.startswith("*"):
        command = command[1:]

    # Look up prompt argument name
    prompt_arg_name = PROMPT_ARGUMENT_MAP.get((agent, command))
    if prompt_arg_name is None:
        return None

    # Get prompt value
    prompt_value = getattr(args, prompt_arg_name, None)
    if not prompt_value or not isinstance(prompt_value, str):
        return None

    return (prompt_arg_name, prompt_value)


def assess_prompt_quality(prompt: str, config: AutoEnhancementConfig) -> float:
    """
    Assess prompt quality and return a score (0-100).

    Higher scores indicate better quality prompts that may not need enhancement.

    Args:
        prompt: The prompt to assess
        config: Auto-enhancement configuration

    Returns:
        Quality score from 0-100
    """
    if not prompt or len(prompt.strip()) < config.min_prompt_length:
        return 0.0

    score = 50.0  # Base score

    # Length factor (longer prompts often more detailed)
    length_factor = min(len(prompt) / 200, 1.0) * 20  # Up to 20 points
    score += length_factor

    # Keyword indicators of quality
    quality_keywords = [
        "requirements",
        "specification",
        "architecture",
        "design",
        "implementation",
        "test",
        "error handling",
        "validation",
        "security",
        "performance",
    ]
    keyword_count = sum(1 for keyword in quality_keywords if keyword.lower() in prompt.lower())
    keyword_factor = min(keyword_count / 5, 1.0) * 15  # Up to 15 points
    score += keyword_factor

    # Structure indicators (sentences, paragraphs)
    sentence_count = prompt.count(".") + prompt.count("!") + prompt.count("?")
    if sentence_count > 3:
        score += 10  # Multiple sentences indicate detail

    # Technical terms (indicates domain knowledge)
    technical_terms = [
        "api",
        "endpoint",
        "database",
        "model",
        "service",
        "controller",
        "middleware",
        "authentication",
        "authorization",
    ]
    tech_count = sum(1 for term in technical_terms if term.lower() in prompt.lower())
    tech_factor = min(tech_count / 3, 1.0) * 5  # Up to 5 points
    score += tech_factor

    # "Already a spec" heuristics: structured prompts often need no enhancement
    pl = prompt.lower()
    spec_indicators = 0
    if any(c in prompt for c in ("- ", "* ", "• ")) or (
        len([s for s in prompt.split() if s and s[0].isdigit() and "." in s[:3]]) >= 2
    ):
        spec_indicators += 2  # bullets or numbered list
    if "acceptance criteria" in pl or "acceptance criterion" in pl:
        spec_indicators += 2
    if "user story" in pl or "as a " in pl and " i want " in pl:
        spec_indicators += 2
    if any(w in pl for w in (" shall ", " must ", " should ")):
        spec_indicators += 2
    spec_factor = min(spec_indicators / 4, 1.0) * 20  # Up to 20 points
    score += spec_factor

    return min(score, 100.0)


def should_enhance_prompt(
    prompt: str, agent: str, command: str, config: AutoEnhancementConfig
) -> bool:
    """
    Determine if a prompt should be enhanced.

    Args:
        prompt: The prompt to check
        agent: Agent name
        command: Command name
        config: Auto-enhancement configuration

    Returns:
        True if prompt should be enhanced, False otherwise
    """
    if not config.enabled:
        return False

    # Check per-command settings
    command_config = config.commands.get(agent, {})
    if not command_config.get("enabled", True):
        return False

    # Assess quality
    quality_score = assess_prompt_quality(prompt, config)
    return quality_score < config.quality_threshold


async def enhance_prompt(
    prompt: str,
    agent: str,
    command: str,
    config: AutoEnhancementConfig,
    enhance_mode: str | None = None,
) -> str:
    """
    Enhance a prompt using the Enhancer Agent.

    Args:
        prompt: Original prompt
        agent: Target agent name
        command: Target command name
        config: Auto-enhancement configuration
        enhance_mode: Override enhancement mode (quick/full), or None to use config

    Returns:
        Enhanced prompt string
    """
    # Get synthesis mode from override, command config, or default
    if enhance_mode:
        synthesis_mode = enhance_mode
    else:
        command_config = config.commands.get(agent, {})
        synthesis_mode = command_config.get("synthesis_mode", "quick")

    enhancer = EnhancerAgent()
    try:
        await enhancer.activate()

        if synthesis_mode == "full":
            result = await enhancer.run(
                "enhance",
                prompt=prompt,
                output_format="markdown",
            )
        else:
            result = await enhancer.run(
                "enhance-quick",
                prompt=prompt,
                output_format="markdown",
            )

        # Extract enhanced prompt from result
        if result.get("success"):
            enhanced_prompt = result.get("enhanced_prompt")
            
            # Check if this is Cursor mode (structured data with instruction)
            if isinstance(enhanced_prompt, dict):
                synthesis_data = enhanced_prompt.get("synthesis_data")
                if synthesis_data and isinstance(synthesis_data, dict):
                    # Use instruction when present (Cursor/structured path)
                    instruction = synthesis_data.get("instruction") or synthesis_data.get("enhanced_prompt")
                    if isinstance(instruction, str) and instruction.strip():
                        return instruction.strip()
                    # No usable instruction: enhancement handled by Cursor; return original
                    return prompt
                # Otherwise, try to extract enhanced_prompt from dict
                if "enhanced_prompt" in enhanced_prompt:
                    enhanced = enhanced_prompt["enhanced_prompt"]
                    if isinstance(enhanced, str):
                        return enhanced
                    # If it's still a dict, fall back to original
                    return prompt
                # No enhanced_prompt in dict, return original
                return prompt
            
            # String result (markdown format)
            if isinstance(enhanced_prompt, str):
                return enhanced_prompt
            
            # Unexpected format, return original
            return prompt
        else:
            # Enhancement failed, return original
            return prompt
    except Exception:
        # On any error, return original prompt
        return prompt
    finally:
        from ..utils.agent_lifecycle import safe_close_agent_sync

        safe_close_agent_sync(enhancer)


def enhance_prompt_if_needed(
    args: Namespace, config: AutoEnhancementConfig | None = None
) -> Namespace:
    """
    Enhance prompt in CLI arguments if needed.

    This is the main entry point for the middleware.

    Args:
        args: Parsed command-line arguments
        config: Auto-enhancement configuration (loads from file if None)

    Returns:
        Modified args with enhanced prompt (if enhancement occurred)
    """
    if config is None:
        project_config = load_config()
        config = project_config.auto_enhancement

    # Check if enhancement is disabled via flag
    if getattr(args, "no_enhance", False):
        return args

    # Detect prompt argument
    prompt_info = detect_prompt_argument(args)
    if not prompt_info:
        return args

    arg_name, prompt_value = prompt_info

    # Check if we should enhance
    agent = getattr(args, "agent", None)
    command = getattr(args, "command", None)
    if not agent or not command:
        return args

    # Normalize command
    if command.startswith("*"):
        command = command[1:]

    # Check if forced enhancement
    force_enhance = getattr(args, "enhance", False)
    enhance_mode_override = getattr(args, "enhance_mode", None)

    if not force_enhance and not should_enhance_prompt(prompt_value, agent, command, config):
        return args

    # Enhance the prompt
    enhanced = asyncio.run(
        enhance_prompt(prompt_value, agent, command, config, enhance_mode_override)
    )

    # Update args with enhanced prompt
    setattr(args, arg_name, enhanced)

    return args

