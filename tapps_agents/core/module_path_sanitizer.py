"""
Module Path Sanitizer - Sanitizes module paths for Python imports.

Replaces invalid characters (hyphens, special chars) with valid Python identifiers
(underscores) to prevent syntax errors in import statements.
"""

import re
from pathlib import Path


class ModulePathSanitizer:
    """
    Sanitizes module paths for Python imports.

    Replaces invalid characters (hyphens, special chars) with valid
    Python identifiers (underscores).

    Examples:
        >>> sanitizer = ModulePathSanitizer()
        >>> sanitizer.sanitize_module_path("services.ai-automation-service-new.src.database")
        'services.ai_automation_service_new.src.database'

        >>> sanitizer.sanitize_import_statement("from services.ai-automation-service-new.src.database import *")
        'from services.ai_automation_service_new.src.database import *'
    """

    def __init__(self):
        """Initialize module path sanitizer."""
        pass

    def sanitize_module_path(self, path: str) -> str:
        """
        Sanitize module path for Python imports.

        Args:
            path: Module path (e.g., "services.ai-automation-service-new.src.database")

        Returns:
            Sanitized path (e.g., "services.ai_automation_service_new.src.database")

        Rules:
        - Replace hyphens (-) with underscores (_)
        - Remove invalid characters (keep only alphanumeric, dots, underscores)
        - Remove consecutive underscores
        - Remove leading/trailing underscores (except for __init__, __main__, etc.)

        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> sanitizer.sanitize_module_path("services.ai-automation-service-new")
            'services.ai_automation_service_new'

            >>> sanitizer.sanitize_module_path("services.ai-automation-service-new.src.database")
            'services.ai_automation_service_new.src.database'

            >>> sanitizer.sanitize_module_path("services.ai-automation-service-new.src.database.__init__")
            'services.ai_automation_service_new.src.database.__init__'
        """
        if not path:
            return path

        # Split by dots to preserve module structure
        parts = path.split(".")

        # Sanitize each part
        sanitized_parts = []
        for part in parts:
            # Skip empty parts
            if not part:
                continue

            # Preserve special Python identifiers (__init__, __main__, etc.)
            if part.startswith("__") and part.endswith("__"):
                sanitized_parts.append(part)
                continue

            # Replace hyphens with underscores
            sanitized = part.replace("-", "_")

            # Remove invalid characters (keep only alphanumeric, underscores)
            sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", sanitized)

            # Remove consecutive underscores
            sanitized = re.sub(r"_+", "_", sanitized)

            # Remove leading/trailing underscores (but preserve if it's a valid identifier)
            sanitized = sanitized.strip("_")

            # Skip empty parts after sanitization
            if sanitized:
                sanitized_parts.append(sanitized)

        # Rejoin with dots
        return ".".join(sanitized_parts)

    def sanitize_import_statement(self, import_stmt: str) -> str:
        """
        Sanitize an import statement.

        Args:
            import_stmt: Import statement (e.g., "from services.ai-automation-service-new.src.database import *")

        Returns:
            Sanitized import statement

        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> sanitizer.sanitize_import_statement("from services.ai-automation-service-new.src.database import *")
            'from services.ai_automation_service_new.src.database import *'

            >>> sanitizer.sanitize_import_statement("import services.ai-automation-service-new.src.database")
            'import services.ai_automation_service_new.src.database'
        """
        if not import_stmt:
            return import_stmt

        # Pattern: "from <module_path> import ..."
        from_pattern = r"(from\s+)([^\s]+)(\s+import)"
        match = re.search(from_pattern, import_stmt)
        if match:
            prefix = match.group(1)
            module_path = match.group(2)
            suffix = match.group(3)
            sanitized_path = self.sanitize_module_path(module_path)
            return import_stmt.replace(module_path, sanitized_path)

        # Pattern: "import <module_path>"
        import_pattern = r"(import\s+)([^\s]+)(?:\s|$)"
        match = re.search(import_pattern, import_stmt)
        if match:
            prefix = match.group(1)
            module_path = match.group(2)
            sanitized_path = self.sanitize_module_path(module_path)
            return import_stmt.replace(module_path, sanitized_path)

        # No match - return as-is
        return import_stmt

    def sanitize_imports_in_code(self, code: str) -> str:
        """
        Sanitize all import statements in code.

        Args:
            code: Code string containing import statements

        Returns:
            Code with sanitized import statements

        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> code = '''
            ... from services.ai-automation-service-new.src.database import *
            ... import services.ai-automation-service-new.src.models
            ... '''
            >>> sanitized = sanitizer.sanitize_imports_in_code(code)
            >>> "ai_automation_service_new" in sanitized
            True
        """
        if not code:
            return code

        lines = code.split("\n")
        sanitized_lines = []

        for line in lines:
            # Check if line contains import statement
            if "import" in line and ("from" in line or line.strip().startswith("import")):
                sanitized_line = self.sanitize_import_statement(line)
                sanitized_lines.append(sanitized_line)
            else:
                sanitized_lines.append(line)

        return "\n".join(sanitized_lines)

    def is_valid_python_identifier(self, identifier: str) -> bool:
        """
        Check if a string is a valid Python identifier.

        Args:
            identifier: String to check

        Returns:
            True if valid Python identifier, False otherwise

        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> sanitizer.is_valid_python_identifier("hello_world")
            True
            >>> sanitizer.is_valid_python_identifier("hello-world")
            False
            >>> sanitizer.is_valid_python_identifier("123hello")
            False
        """
        if not identifier:
            return False

        # Python identifier pattern: letter or underscore, followed by letters, digits, underscores
        pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
        return bool(re.match(pattern, identifier))
