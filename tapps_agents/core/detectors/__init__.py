"""Detector modules for TappsCodingAgents.

This package contains modules for detecting various aspects of projects:
- Tech stack detection (languages, libraries, frameworks)
- Domain detection
- Project type detection
"""

from tapps_agents.core.detectors.tech_stack_detector import TechStackDetector

__all__ = ["TechStackDetector"]
