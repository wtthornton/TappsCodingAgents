"""Context7 bundle loader for offline / no-API environments.

When `tapps-agents[context7-bundle]` is installed (or `tapps-agents-context7-bundle`
package exists), copies pre-fetched cache data into the project cache if empty.
Reserved for future use; no-op when bundle package is not installed.
"""

from __future__ import annotations

import importlib.util
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Package name for optional Context7 cache bundle (future)
BUNDLE_PACKAGE = "tapps_agents_context7_bundle"


def try_copy_context7_bundle(
    project_root: Path,
    cache_root: Path | None = None,
) -> dict[str, Any]:
    """Try to copy Context7 bundle into project cache if empty.

    When the optional bundle package is installed and project cache is empty,
    copies pre-fetched library docs into the project cache. No-op otherwise.

    Args:
        project_root: Project root directory
        cache_root: Cache directory (default: project_root/.tapps-agents/kb/context7-cache)

    Returns:
        Dict with keys: success, copied, error, source
    """
    if cache_root is None:
        cache_root = project_root / ".tapps-agents" / "kb" / "context7-cache"

    result: dict[str, Any] = {
        "success": False,
        "copied": 0,
        "error": None,
        "source": None,
    }

    # Check if bundle package is installed
    spec = importlib.util.find_spec(BUNDLE_PACKAGE)
    if spec is None or spec.origin is None or "origin" not in dir(spec):
        return result

    try:
        # Get bundle data path (package provides get_bundle_path() or similar)
        loader = getattr(spec, "loader", None)
        if loader is None:
            result["error"] = f"{BUNDLE_PACKAGE} has no loader"
            return result
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        get_path = getattr(module, "get_bundle_path", None)
        if get_path is None:
            result["error"] = f"{BUNDLE_PACKAGE} has no get_bundle_path()"
            return result

        bundle_path = Path(get_path())
        if not bundle_path.is_dir():
            result["error"] = f"Bundle path is not a directory: {bundle_path}"
            return result

        # Only copy if project cache is empty or missing
        cache_path = Path(cache_root)
        if cache_path.exists():
            # Check if cache has content (libraries/ or index with entries)
            libs_dir = cache_path / "libraries"
            if libs_dir.exists() and any(libs_dir.iterdir()):
                return result  # Cache already populated, skip

        cache_path.mkdir(parents=True, exist_ok=True)

        # Copy bundle contents (libraries/, topics/, index.yaml, etc.)
        copied = 0
        for item in bundle_path.iterdir():
            dst = cache_path / item.name
            if item.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(item, dst)
                copied += 1
            elif item.is_file():
                shutil.copy2(item, dst)
                copied += 1

        result["success"] = True
        result["copied"] = copied
        result["source"] = str(bundle_path)
        logger.info(
            f"Context7 bundle copied from {bundle_path} to {cache_path} ({copied} items)"
        )
    except Exception as e:
        result["error"] = str(e)
        logger.debug(f"Context7 bundle copy skipped: {e}")

    return result
