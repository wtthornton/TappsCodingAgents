#!/usr/bin/env python3
"""
Context7 KB Cache Pre-population Script

Pre-populates the Context7 KB cache with common libraries and project dependencies.
This script helps achieve 95%+ cache hit rate by warming up the cache before use.

Usage:
    python scripts/prepopulate_context7_cache.py
    python scripts/prepopulate_context7_cache.py --requirements requirements.txt
    python scripts/prepopulate_context7_cache.py --libraries fastapi pytest sqlalchemy
"""

# ruff: noqa: E402

import argparse
import asyncio
import re
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Windows encoding compatibility
from tapps_agents.core.unicode_safe import setup_windows_encoding, safe_print
setup_windows_encoding()

from tapps_agents.context7.commands import Context7Commands
from tapps_agents.core.config import load_config

# Common libraries to pre-populate (always cached)
COMMON_LIBRARIES = [
    # Python Web Frameworks
    "fastapi",
    "django",
    "flask",
    "starlette",
    # Database
    "sqlalchemy",
    "pymongo",
    "psycopg2",
    "sqlite3",
    # Testing
    "pytest",
    "unittest",
    "pytest-asyncio",
    "pytest-mock",
    # Code Quality
    "ruff",
    "mypy",
    "bandit",
    "black",
    # HTTP/API
    "httpx",
    "requests",
    "aiohttp",
    # Data Processing
    "pandas",
    "numpy",
    "pydantic",
    # Async
    "asyncio",
    "aiofiles",
    # Type Checking
    "typing",
    "typing-extensions",
]

# Common topics to cache for each library
COMMON_TOPICS = {
    "fastapi": ["routing", "dependency-injection", "middleware", "errors"],
    "pytest": ["fixtures", "parametrize", "markers", "async"],
    "sqlalchemy": ["models", "queries", "sessions", "relationships"],
    "django": ["models", "views", "urls", "middleware"],
    "pydantic": ["models", "validation", "serialization"],
}


def parse_requirements_file(requirements_path: Path) -> set[str]:
    """
    Parse requirements.txt to extract library names.

    Args:
        requirements_path: Path to requirements.txt

    Returns:
        Set of library names (without version constraints)
    """
    libraries = set()

    if not requirements_path.exists():
        safe_print(f"[WARN] Requirements file not found: {requirements_path}")
        return libraries

    try:
        content = requirements_path.read_text(encoding="utf-8")

        for line in content.splitlines():
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Remove version constraints and extras
            # Examples:
            #   pydantic>=2.10.0 -> pydantic
            #   fastapi[dev] -> fastapi
            #   git+https://... -> skip
            if line.startswith("git+") or line.startswith("http"):
                continue

            # Extract library name (before any version specifiers)
            match = re.match(r"^([a-zA-Z0-9_-]+)", line)
            if match:
                lib_name = match.group(1).lower()
                # Normalize common variations
                lib_name = lib_name.replace("_", "-")
                libraries.add(lib_name)

    except Exception as e:
        safe_print(f"[WARN] Error parsing requirements file: {e}")

    return libraries


async def pre_populate_library(
    context7_commands: Context7Commands,
    library: str,
    topics: list[str] | None = None,
) -> bool:
    """
    Pre-populate cache for a library and optional topics.

    Args:
        context7_commands: Context7Commands instance
        library: Library name
        topics: Optional list of topics to cache

    Returns:
        True if successful, False otherwise
    """
    if not context7_commands.enabled:
        safe_print(f"[WARN] Context7 is not enabled, skipping {library}")
        return False

    success_count = 0

    # Cache overview first
    safe_print(f"  [CACHE] Caching {library} (overview)...", end=" ", flush=True)
    result = await context7_commands.cmd_docs(library)
    if result.get("success"):
        safe_print("[OK]", flush=True)
        success_count += 1
    else:
        safe_print(f"[FAIL] ({result.get('error', 'Unknown error')})", flush=True)

    # Cache specific topics
    if topics:
        for topic in topics:
            safe_print(f"  [CACHE] Caching {library} ({topic})...", end=" ", flush=True)
            result = await context7_commands.cmd_docs(library, topic=topic)
            if result.get("success"):
                safe_print("[OK]", flush=True)
                success_count += 1
            else:
                safe_print(f"[FAIL] ({result.get('error', 'Unknown error')})", flush=True)

    return success_count > 0


async def main():
    """Main pre-population function."""
    parser = argparse.ArgumentParser(
        description="Pre-populate Context7 KB cache with library documentation"
    )
    parser.add_argument(
        "--requirements",
        type=str,
        default="requirements.txt",
        help="Path to requirements.txt file (default: requirements.txt)",
    )
    parser.add_argument(
        "--libraries", nargs="+", help="Additional libraries to cache (space-separated)"
    )
    parser.add_argument(
        "--topics", action="store_true", help="Cache common topics for each library"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()

    # Determine project root
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        project_root = Path.cwd()

    safe_print("[START] Context7 KB Cache Pre-population")
    safe_print("=" * 60)

    # Load configuration
    try:
        config = load_config(project_root)
        if not config.context7 or not config.context7.enabled:
            safe_print("[FAIL] Context7 is not enabled in configuration")
            safe_print("   Enable it in .tapps-agents/config.yaml")
            return 1
    except Exception as e:
        safe_print(f"[WARN] Error loading config: {e}")
        safe_print("   Continuing with default settings...")
        config = None

    # Initialize Context7 commands
    context7_commands = Context7Commands(project_root=project_root, config=config)

    if not context7_commands.enabled:
        safe_print("[FAIL] Context7 is not enabled")
        return 1

    # Collect libraries to cache
    libraries_to_cache = set(COMMON_LIBRARIES)

    # Add libraries from requirements.txt
    requirements_path = project_root / args.requirements
    if requirements_path.exists():
        safe_print(f"\n[PARSE] Parsing {args.requirements}...")
        req_libraries = parse_requirements_file(requirements_path)
        libraries_to_cache.update(req_libraries)
        safe_print(f"   Found {len(req_libraries)} libraries in requirements.txt")

    # Add explicitly specified libraries
    if args.libraries:
        libraries_to_cache.update(args.libraries)
        safe_print(f"   Added {len(args.libraries)} explicitly specified libraries")

    safe_print(f"\n[INFO] Total libraries to cache: {len(libraries_to_cache)}")
    safe_print("=" * 60)

    # Pre-populate cache
    success_count = 0
    fail_count = 0

    for library in sorted(libraries_to_cache):
        safe_print(f"\n[PROCESS] Processing {library}...")

        topics = None
        if args.topics and library in COMMON_TOPICS:
            topics = COMMON_TOPICS[library]

        success = await pre_populate_library(context7_commands, library, topics=topics)

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    safe_print("\n" + "=" * 60)
    safe_print("[REPORT] Pre-population Summary")
    safe_print("=" * 60)
    safe_print(f"[OK] Successfully cached: {success_count} libraries")
    safe_print(f"[FAIL] Failed to cache: {fail_count} libraries")
    if success_count + fail_count > 0:
        safe_print(f"[STATS] Success rate: {success_count / (success_count + fail_count) * 100:.1f}%")

    # Get cache statistics
    safe_print("\n[REPORT] Cache Statistics:")
    stats = context7_commands.cmd_status()
    if isinstance(stats, dict) and stats.get("success"):
        metrics = stats.get("metrics", {})
        safe_print(f"   Total entries: {metrics.get('total_entries', 'N/A')}")
        safe_print(f"   Total libraries: {metrics.get('total_libraries', 'N/A')}")
        safe_print(f"   Cache size: {metrics.get('cache_size_mb', 'N/A')} MB")
    else:
        safe_print("   (Statistics unavailable)")

    safe_print("\n[OK] Pre-population complete!")
    safe_print("\n[TIP] Run this script periodically to keep cache up-to-date")
    safe_print("   or use Context7 auto-refresh feature.")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
