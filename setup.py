"""
Setup script for TappsCodingAgents.

NOTE: This file is a minimal stub. All package metadata and dependencies
are defined in pyproject.toml, which is the authoritative source.

See docs/DEPENDENCY_POLICY.md for the dependency management policy.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = (
    readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
)

# NOTE: Dependencies are NOT defined here. They are read from pyproject.toml
# by setuptools automatically. This prevents drift between setup.py and pyproject.toml.
# See docs/DEPENDENCY_POLICY.md for details.

setup(
    # Minimal metadata - most is in pyproject.toml
    # Only include what's needed for backward compatibility or not in pyproject.toml
    include_package_data=True,
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    # Entry points are also defined in pyproject.toml [project.scripts],
    # but we keep them here for backward compatibility
    entry_points={
        "console_scripts": [
            "tapps-agents=tapps_agents.cli:main",
        ],
    },
)
