"""
Unit tests for ModulePathSanitizer utility.

Tests module path sanitization functionality including hyphen replacement,
special character handling, and import statement sanitization.
"""

import pytest

from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

pytestmark = pytest.mark.unit


class TestModulePathSanitizer:
    """Test ModulePathSanitizer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = ModulePathSanitizer()

    # Module path sanitization tests
    def test_sanitize_module_path_basic_hyphen(self):
        """Test sanitize_module_path() with basic hyphen replacement."""
        path = "services.ai-automation-service-new"
        result = self.sanitizer.sanitize_module_path(path)
        assert result == "services.ai_automation_service_new"
        assert "-" not in result

    def test_sanitize_module_path_multiple_hyphens(self):
        """Test sanitize_module_path() with multiple hyphens."""
        path = "services.ai-automation-service-new.src.database"
        result = self.sanitizer.sanitize_module_path(path)
        assert result == "services.ai_automation_service_new.src.database"
        assert "-" not in result

    def test_sanitize_module_path_preserves_init(self):
        """Test sanitize_module_path() preserves __init__."""
        path = "services.ai-automation-service-new.src.database.__init__"
        result = self.sanitizer.sanitize_module_path(path)
        assert result == "services.ai_automation_service_new.src.database.__init__"
        assert "__init__" in result

    def test_sanitize_module_path_preserves_main(self):
        """Test sanitize_module_path() preserves __main__."""
        path = "services.ai-automation-service-new.__main__"
        result = self.sanitizer.sanitize_module_path(path)
        assert result == "services.ai_automation_service_new.__main__"
        assert "__main__" in result

    def test_sanitize_module_path_special_characters(self):
        """Test sanitize_module_path() with special characters."""
        path = "services.ai-automation@service#new"
        result = self.sanitizer.sanitize_module_path(path)
        # Special characters should be replaced with underscores
        assert "@" not in result
        assert "#" not in result
        assert result.count("_") > 0

    def test_sanitize_module_path_consecutive_underscores(self):
        """Test sanitize_module_path() removes consecutive underscores."""
        path = "services.ai__automation___service"
        result = self.sanitizer.sanitize_module_path(path)
        # Should not have consecutive underscores
        assert "__" not in result.replace("__init__", "").replace("__main__", "")

    def test_sanitize_module_path_leading_trailing_underscores(self):
        """Test sanitize_module_path() removes leading/trailing underscores."""
        path = "_services.ai-automation-service-new_"
        result = self.sanitizer.sanitize_module_path(path)
        # Should not start or end with underscore (except special cases)
        assert not result.startswith("_") or result.startswith("__")
        assert not result.endswith("_") or result.endswith("__")

    def test_sanitize_module_path_empty_string(self):
        """Test sanitize_module_path() with empty string."""
        result = self.sanitizer.sanitize_module_path("")
        assert result == ""

    def test_sanitize_module_path_single_part(self):
        """Test sanitize_module_path() with single part."""
        path = "test-module"
        result = self.sanitizer.sanitize_module_path(path)
        assert result == "test_module"

    def test_sanitize_module_path_complex(self):
        """Test sanitize_module_path() with complex path."""
        path = "services.ai-automation-service-new.src.database.models.user-model"
        result = self.sanitizer.sanitize_module_path(path)
        assert result == "services.ai_automation_service_new.src.database.models.user_model"
        assert "-" not in result

    # Import statement sanitization tests
    def test_sanitize_import_statement_from_import(self):
        """Test sanitize_import_statement() with 'from ... import' pattern."""
        import_stmt = "from services.ai-automation-service-new.src.database import *"
        result = self.sanitizer.sanitize_import_statement(import_stmt)
        assert result == "from services.ai_automation_service_new.src.database import *"
        assert "ai-automation-service-new" not in result
        assert "ai_automation_service_new" in result

    def test_sanitize_import_statement_import(self):
        """Test sanitize_import_statement() with 'import ...' pattern."""
        import_stmt = "import services.ai-automation-service-new.src.database"
        result = self.sanitizer.sanitize_import_statement(import_stmt)
        assert result == "import services.ai_automation_service_new.src.database"
        assert "ai-automation-service-new" not in result

    def test_sanitize_import_statement_no_match(self):
        """Test sanitize_import_statement() with no import pattern."""
        import_stmt = "not an import statement"
        result = self.sanitizer.sanitize_import_statement(import_stmt)
        assert result == import_stmt  # Should return as-is

    def test_sanitize_import_statement_empty(self):
        """Test sanitize_import_statement() with empty string."""
        result = self.sanitizer.sanitize_import_statement("")
        assert result == ""

    # Code sanitization tests
    def test_sanitize_imports_in_code_single_import(self):
        """Test sanitize_imports_in_code() with single import."""
        code = """
from services.ai-automation-service-new.src.database import *
"""
        result = self.sanitizer.sanitize_imports_in_code(code)
        assert "ai_automation_service_new" in result
        assert "ai-automation-service-new" not in result

    def test_sanitize_imports_in_code_multiple_imports(self):
        """Test sanitize_imports_in_code() with multiple imports."""
        code = """
from services.ai-automation-service-new.src.database import *
import services.ai-automation-service-new.src.models
"""
        result = self.sanitizer.sanitize_imports_in_code(code)
        assert "ai_automation_service_new" in result
        assert "ai-automation-service-new" not in result
        # Both imports should be sanitized
        assert result.count("ai_automation_service_new") == 2

    def test_sanitize_imports_in_code_mixed_code(self):
        """Test sanitize_imports_in_code() with mixed code and imports."""
        code = """
from services.ai-automation-service-new.src.database import *

def hello():
    print("world")
"""
        result = self.sanitizer.sanitize_imports_in_code(code)
        assert "ai_automation_service_new" in result
        assert "def hello()" in result  # Non-import code preserved

    def test_sanitize_imports_in_code_no_imports(self):
        """Test sanitize_imports_in_code() with no imports."""
        code = """
def hello():
    print("world")
"""
        result = self.sanitizer.sanitize_imports_in_code(code)
        assert result == code  # Should be unchanged

    def test_sanitize_imports_in_code_empty(self):
        """Test sanitize_imports_in_code() with empty code."""
        result = self.sanitizer.sanitize_imports_in_code("")
        assert result == ""

    # Identifier validation tests
    def test_is_valid_python_identifier_valid(self):
        """Test is_valid_python_identifier() with valid identifier."""
        assert self.sanitizer.is_valid_python_identifier("hello_world") is True
        assert self.sanitizer.is_valid_python_identifier("_private") is True
        assert self.sanitizer.is_valid_python_identifier("TestClass") is True
        assert self.sanitizer.is_valid_python_identifier("__init__") is True

    def test_is_valid_python_identifier_invalid_hyphen(self):
        """Test is_valid_python_identifier() with hyphen (invalid)."""
        assert self.sanitizer.is_valid_python_identifier("hello-world") is False

    def test_is_valid_python_identifier_invalid_leading_number(self):
        """Test is_valid_python_identifier() with leading number (invalid)."""
        assert self.sanitizer.is_valid_python_identifier("123hello") is False

    def test_is_valid_python_identifier_invalid_special_chars(self):
        """Test is_valid_python_identifier() with special characters (invalid)."""
        assert self.sanitizer.is_valid_python_identifier("hello@world") is False
        assert self.sanitizer.is_valid_python_identifier("hello.world") is False

    def test_is_valid_python_identifier_empty(self):
        """Test is_valid_python_identifier() with empty string."""
        assert self.sanitizer.is_valid_python_identifier("") is False

    def test_is_valid_python_identifier_none(self):
        """Test is_valid_python_identifier() with None."""
        assert self.sanitizer.is_valid_python_identifier(None) is False
