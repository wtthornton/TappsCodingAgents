"""
Target File Inference for Simple Mode Workflows.

Infers appropriate target file paths from description text
when the implementer step needs a file_path but none is provided.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class TargetFileInferencer:
    """Infers target file paths from natural language descriptions."""

    # Common file patterns by description keywords
    # IMPORTANT: Order matters - more specific patterns first, test patterns early
    FILE_PATTERNS: dict[str, str] = {
        # Test patterns - HIGH PRIORITY (check before other keywords like service/model)
        r"\bunit\s+test|\btest\s+for|\btests?\s+for|\bwrite\s+tests?\b|\badd\s+tests?\b": "tests/test_{name}.py",
        r"\btest\b": "tests/test_{name}.py",
        # API/Web patterns
        r"\bapi\b|\bendpoint|\broute|\brouter\b": "src/api/{name}.py",
        r"\brest\b.*\bapi\b|\brestful\b": "src/api/{name}.py",
        r"\bfastapi\b|\bflask\b|\bdjango\b": "src/api/{name}.py",
        r"\bcontroller\b": "src/controllers/{name}.py",
        r"\bmiddleware\b": "src/middleware/{name}.py",
        # Data/Model patterns
        r"\bmodel\b|\bentity\b|\bschema\b": "src/models/{name}.py",
        r"\bdatabase\b|\bdb\b|\brepository\b": "src/database/{name}.py",
        r"\bmigration\b": "src/migrations/{name}.py",
        # Service patterns
        r"\bservice\b": "src/services/{name}.py",
        r"\bhandler\b": "src/handlers/{name}.py",
        r"\bworker\b|\bjob\b|\btask\b": "src/workers/{name}.py",
        # Utility patterns
        r"\butil\b|\butility\b|\bhelper\b": "src/utils/{name}.py",
        r"\bconfig\b|\bconfiguration\b|\bsettings\b": "src/config/{name}.py",
        r"\bvalidat\b": "src/validators/{name}.py",
        # Authentication patterns
        r"\bauth\b|\bauthentication\b|\blogin\b": "src/auth/{name}.py",
        r"\bpermission\b|\bauthorization\b|\baccess\b": "src/auth/{name}.py",
        # CLI patterns
        r"\bcli\b|\bcommand.?line\b": "src/cli/{name}.py",
        # Frontend patterns
        r"\bcomponent\b.*\breact\b|\breact\b.*\bcomponent\b": "src/components/{name}.tsx",
        r"\bpage\b|\bview\b": "src/pages/{name}.tsx",
        # Default - catch-all
        r".*": "src/{name}.py",
    }

    # Keywords to extract feature names
    NAME_PATTERNS: list[tuple[str, int]] = [
        # "Create a <name> feature"
        (r"create\s+(?:a\s+)?([a-z_]+(?:\s+[a-z_]+)?)\s+(?:feature|module|service)", 1),
        # "Build <name> functionality"
        (r"build\s+(?:a\s+)?([a-z_]+(?:\s+[a-z_]+)?)\s+(?:functionality|feature)", 1),
        # "Implement <name>"
        (r"implement\s+(?:a\s+)?(?:the\s+)?([a-z_]+(?:\s+[a-z_]+)?)", 1),
        # "Add <name> endpoint/handler/service"
        (r"add\s+(?:a\s+)?(?:the\s+)?([a-z_]+(?:\s+[a-z_]+)?)\s+(?:endpoint|handler|service|api)", 1),
        # "<name> authentication/authorization"
        (r"([a-z_]+)\s+(?:authentication|authorization|auth)", 1),
        # "user <something>"
        (r"user\s+([a-z_]+)", 1),
    ]

    def __init__(self, project_root: Path | None = None):
        """Initialize the inferencer.

        Args:
            project_root: Project root directory for path resolution
        """
        self.project_root = project_root or Path.cwd()

    def infer_target_file(
        self,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Infer target file path from description.

        Args:
            description: Natural language description of the feature
            context: Optional context with hints (e.g., architecture, design docs)

        Returns:
            Inferred file path string
        """
        description_lower = description.lower()

        # Extract feature name from description
        feature_name = self._extract_feature_name(description_lower)

        # Determine file type/location from description
        file_template = self._determine_file_template(description_lower)

        # Generate path
        file_path = file_template.format(name=feature_name)

        # Check context for more specific paths
        if context:
            specific_path = self._check_context_for_path(context, feature_name)
            if specific_path:
                file_path = specific_path

        # Ensure path is valid
        return self._normalize_path(file_path)

    def _extract_feature_name(self, description: str) -> str:
        """Extract feature name from description.

        Args:
            description: Lowercase description text

        Returns:
            Extracted feature name (snake_case)
        """
        # Try each pattern
        for pattern, group in self.NAME_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                name = match.group(group)
                # Convert to snake_case
                name = re.sub(r"\s+", "_", name.strip())
                name = re.sub(r"[^a-z0-9_]", "", name)
                if name:
                    return name

        # Fallback: extract significant words
        words = re.findall(r"\b[a-z]{3,}\b", description)
        # Filter common words
        stop_words = {
            "the", "and", "for", "with", "that", "this", "from", "create",
            "build", "implement", "add", "new", "feature", "function", "class",
            "module", "service", "using", "use", "make", "should", "will",
        }
        significant = [w for w in words if w not in stop_words][:2]
        
        if significant:
            return "_".join(significant)
        
        return "new_feature"

    def _determine_file_template(self, description: str) -> str:
        """Determine file template based on description content.

        Args:
            description: Lowercase description text

        Returns:
            File path template string
        """
        for pattern, template in self.FILE_PATTERNS.items():
            if re.search(pattern, description, re.IGNORECASE):
                return template
        
        return "src/{name}.py"

    def _check_context_for_path(
        self,
        context: dict[str, Any],
        feature_name: str,
    ) -> str | None:
        """Check context for specific path hints.

        Args:
            context: Context dictionary with architecture/design info
            feature_name: Extracted feature name

        Returns:
            Specific path if found in context, None otherwise
        """
        # Check for explicit file path in context
        if "file_path" in context:
            return context["file_path"]

        # Check architecture section for component paths
        if "architecture" in context:
            arch = context["architecture"]
            if isinstance(arch, str):
                # Look for path patterns in architecture text
                path_match = re.search(
                    rf"(?:file|path|location):\s*([^\s]+{feature_name}[^\s]*\.py)",
                    arch,
                    re.IGNORECASE,
                )
                if path_match:
                    return path_match.group(1)

        # Check API design for endpoint paths
        if "api_design" in context:
            api = context["api_design"]
            if isinstance(api, str) and "router" in api.lower():
                return f"src/api/{feature_name}_router.py"

        return None

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path.

        Args:
            file_path: Raw file path

        Returns:
            Normalized file path
        """
        # Clean up path
        path = file_path.strip()
        
        # Ensure Python file extension
        if not path.endswith((".py", ".tsx", ".ts", ".js", ".jsx")):
            path = path + ".py" if not path.endswith("/") else path + "main.py"

        # Ensure leading directory (default to src/)
        if not path.startswith(("src/", "tests/", "lib/", "app/")):
            path = "src/" + path

        # Convert to Path for normalization and back to string
        normalized = str(Path(path))
        
        return normalized

    def infer_from_previous_steps(
        self,
        enhanced_prompt: str,
        architecture: str | None = None,
        api_design: str | None = None,
    ) -> str:
        """Infer target file from previous workflow step outputs.

        Args:
            enhanced_prompt: Output from enhancer step
            architecture: Output from architect step
            api_design: Output from designer step

        Returns:
            Inferred file path
        """
        context: dict[str, Any] = {}
        
        if architecture:
            context["architecture"] = architecture
        if api_design:
            context["api_design"] = api_design

        return self.infer_target_file(enhanced_prompt, context)

    def suggest_alternatives(
        self,
        description: str,
        count: int = 3,
    ) -> list[str]:
        """Suggest alternative file paths.

        Args:
            description: Description text
            count: Number of alternatives to suggest

        Returns:
            List of alternative file paths
        """
        description_lower = description.lower()
        feature_name = self._extract_feature_name(description_lower)
        
        alternatives = []
        for pattern, template in self.FILE_PATTERNS.items():
            if re.search(pattern, description_lower, re.IGNORECASE):
                path = template.format(name=feature_name)
                if path not in alternatives:
                    alternatives.append(self._normalize_path(path))
                    if len(alternatives) >= count:
                        break
        
        # If we don't have enough alternatives, add some common ones
        if len(alternatives) < count:
            common_templates = [
                "src/{name}.py",
                "src/services/{name}_service.py",
                "src/api/{name}_api.py",
                "src/utils/{name}_utils.py",
            ]
            for template in common_templates:
                path = self._normalize_path(template.format(name=feature_name))
                if path not in alternatives:
                    alternatives.append(path)
                    if len(alternatives) >= count:
                        break
        
        return alternatives[:count]
