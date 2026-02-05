"""Init Autofill Integration Module.

This module integrates Phases 1-3 of the Init Autofill implementation:
- Phase 1: Configuration Validation & Tech Stack Detection
- Phase 2: Context7 Cache Management
- Phase 3.1: Expert Generator

Provides high-level functions for use by tapps-agents init and init --reset.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from tapps_agents.core.validators.config_validator import ConfigValidator
from tapps_agents.core.detectors.tech_stack_detector import TechStackDetector
from tapps_agents.core.context7.cache_manager import Context7CacheManager
from tapps_agents.core.generators.expert_generator import ExpertGenerator

logger = logging.getLogger(__name__)


def validate_project_configuration(
    project_root: Path,
    auto_fix: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """Validate project configuration using Phase 1 ConfigValidator.

    Args:
        project_root: Project root directory
        auto_fix: Whether to automatically fix issues (currently not supported by ConfigValidator)
        verbose: Whether to show detailed output

    Returns:
        Dictionary with validation results
    """
    try:
        validator = ConfigValidator(project_root=project_root)
        result = validator.validate_all()

        return {
            "success": result.valid,
            "errors": [str(e) for e in result.errors],
            "warnings": [str(w) for w in result.warnings],
            "auto_fixed": False,  # ConfigValidator doesn't support auto_fix yet
        }
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return {
            "success": False,
            "errors": [f"Validation error: {e}"],
            "warnings": [],
            "auto_fixed": False,
        }


def detect_tech_stack_enhanced(
    project_root: Path,
    generate_yaml: bool = True,
    max_files: int = 10000,
) -> Dict[str, Any]:
    """Detect tech stack using Phase 1 TechStackDetector.

    Args:
        project_root: Project root directory
        generate_yaml: Whether to generate tech-stack.yaml
        max_files: Maximum files to scan

    Returns:
        Dictionary with detection results
    """
    try:
        detector = TechStackDetector(project_root=project_root, max_files=max_files)

        # Detect all components
        languages = detector.detect_languages()
        libraries = detector.detect_libraries()
        frameworks = detector.detect_frameworks()  # No parameters, uses self.libraries
        domains = detector.detect_domains()

        # Generate tech-stack.yaml if requested
        yaml_path = None
        if generate_yaml:
            yaml_path = detector.generate_tech_stack_yaml()

        return {
            "success": True,
            "languages": languages,
            "libraries": libraries,
            "frameworks": frameworks,
            "domains": domains,
            "tech_stack_yaml": str(yaml_path) if yaml_path else None,
            "files_scanned": min(max_files, 10000),  # Approximate
        }
    except Exception as e:
        logger.error(f"Tech stack detection failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "languages": [],
            "libraries": [],
            "frameworks": [],
            "domains": [],
            "tech_stack_yaml": None,
        }


async def populate_context7_cache(
    project_root: Path,
    tech_stack_file: Optional[Path] = None,
    skip_cached: bool = True,
    max_concurrent: int = 5,
) -> Dict[str, Any]:
    """Populate Context7 cache using Phase 2 Context7CacheManager.

    Args:
        project_root: Project root directory
        tech_stack_file: Path to tech-stack.yaml (defaults to .tapps-agents/tech-stack.yaml)
        skip_cached: Whether to skip already-cached libraries
        max_concurrent: Maximum concurrent fetches

    Returns:
        Dictionary with cache population results
    """
    try:
        cache_manager = Context7CacheManager(project_root=project_root)

        if not cache_manager.enabled:
            return {
                "success": False,
                "error": "Context7 is not enabled",
                "total_libraries": 0,
                "already_cached": 0,
                "fetched": 0,
                "successful_fetches": 0,
                "failed_fetches": 0,
            }

        result = await cache_manager.scan_and_populate_from_tech_stack(
            tech_stack_file=tech_stack_file,
            skip_cached=skip_cached,
            max_concurrent=max_concurrent,
        )

        return result
    except Exception as e:
        logger.error(f"Context7 cache population failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_libraries": 0,
            "already_cached": 0,
            "fetched": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
        }


def generate_experts_from_knowledge(
    project_root: Path,
    auto_mode: bool = True,
    skip_existing: bool = True,
) -> Dict[str, Any]:
    """Generate experts from knowledge base using Phase 3.1 ExpertGenerator.

    Args:
        project_root: Project root directory
        auto_mode: Whether to skip confirmation prompts
        skip_existing: Whether to skip domains with existing experts

    Returns:
        Dictionary with expert generation results
    """
    try:
        generator = ExpertGenerator(project_root=project_root)
        result = generator.scan_and_generate(
            auto_mode=auto_mode,
            skip_existing=skip_existing,
        )

        return result
    except Exception as e:
        logger.error(f"Expert generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_files": 0,
            "generated": 0,
            "skipped": 0,
            "errors": 1,
            "generated_experts": [],
            "skipped_files": [],
            "error_details": [{"error": str(e)}],
        }


async def run_init_autofill(
    project_root: Path,
    auto_fix_config: bool = True,
    generate_tech_stack_yaml: bool = True,
    populate_cache: bool = True,
    generate_experts: bool = True,
    skip_cached_libraries: bool = True,
    skip_existing_experts: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run complete init autofill process (Phases 1-3).

    This is the main integration function that orchestrates all three phases:
    1. Validate configuration (Phase 1)
    2. Detect tech stack (Phase 1)
    3. Populate Context7 cache (Phase 2)
    4. Generate experts from knowledge (Phase 3)

    Args:
        project_root: Project root directory
        auto_fix_config: Whether to automatically fix configuration issues
        generate_tech_stack_yaml: Whether to generate tech-stack.yaml
        populate_cache: Whether to populate Context7 cache
        generate_experts: Whether to generate experts from knowledge base
        skip_cached_libraries: Whether to skip already-cached libraries
        skip_existing_experts: Whether to skip domains with existing experts
        verbose: Whether to show detailed output

    Returns:
        Dictionary with results from all phases
    """
    results = {
        "project_root": str(project_root),
        "validation": None,
        "tech_stack": None,
        "cache_population": None,
        "expert_generation": None,
        "overall_success": True,
    }

    # Phase 1: Configuration Validation
    if verbose:
        logger.info("[Phase 1] Validating configuration...")

    validation_result = validate_project_configuration(
        project_root=project_root,
        auto_fix=auto_fix_config,
        verbose=verbose,
    )
    results["validation"] = validation_result

    if not validation_result["success"] and not auto_fix_config:
        logger.warning("Configuration validation failed. Some features may not work correctly.")
        results["overall_success"] = False

    # Phase 1: Tech Stack Detection
    if verbose:
        logger.info("[Phase 1] Detecting tech stack...")

    tech_stack_result = detect_tech_stack_enhanced(
        project_root=project_root,
        generate_yaml=generate_tech_stack_yaml,
    )
    results["tech_stack"] = tech_stack_result

    if not tech_stack_result["success"]:
        logger.error("Tech stack detection failed.")
        results["overall_success"] = False
        # Continue with other phases

    # Phase 2: Context7 Cache Population
    if populate_cache:
        if verbose:
            logger.info("[Phase 2] Populating Context7 cache...")

        cache_result = await populate_context7_cache(
            project_root=project_root,
            skip_cached=skip_cached_libraries,
        )
        results["cache_population"] = cache_result

        if not cache_result["success"]:
            logger.warning("Context7 cache population failed or skipped (may not be enabled).")
            # Non-fatal: Context7 is optional

    # Phase 3.1: Expert Generation
    if generate_experts:
        if verbose:
            logger.info("[Phase 3.1] Generating experts from knowledge base...")

        expert_result = generate_experts_from_knowledge(
            project_root=project_root,
            auto_mode=True,
            skip_existing=skip_existing_experts,
        )
        results["expert_generation"] = expert_result

        if not expert_result["success"]:
            logger.warning("Expert generation failed.")
            # Non-fatal: Experts can be generated later

    if verbose:
        logger.info(f"[Init Autofill] Overall success: {results['overall_success']}")

    return results


def run_init_autofill_sync(
    project_root: Path,
    **kwargs
) -> Dict[str, Any]:
    """Synchronous wrapper for run_init_autofill.

    Use this from CLI or non-async code.
    """
    return asyncio.run(run_init_autofill(project_root, **kwargs))
