"""
Docker/Container support for TappsCodingAgents.
"""

from .analyzer import DockerfileAnalyzer
from .debugger import ContainerDebugger
from .error_patterns import ErrorPatternDatabase

__all__ = ["DockerfileAnalyzer", "ContainerDebugger", "ErrorPatternDatabase"]

