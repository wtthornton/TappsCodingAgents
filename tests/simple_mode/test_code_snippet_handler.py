"""
Comprehensive tests for code_snippet_handler module.

Tests code snippet detection, temp file creation, language detection,
and workflow integration. Target: ≥80% coverage.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.simple_mode.code_snippet_handler import (
    LANGUAGE_EXTENSIONS,
    CodeSnippet,
    CodeSnippetHandler,
    TempFile,
    detect_pasted_code,
)

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_scratchpad(tmp_path):
    """Create temporary scratchpad directory."""
    scratchpad = tmp_path / "scratchpad"
    scratchpad.mkdir(parents=True, exist_ok=True)
    return scratchpad


@pytest.fixture
def handler(temp_scratchpad):
    """Create CodeSnippetHandler with temp scratchpad."""
    return CodeSnippetHandler(scratchpad_dir=temp_scratchpad)


# ============================================================================
# Test CodeSnippet Dataclass
# ============================================================================

class TestCodeSnippet:
    """Test CodeSnippet dataclass."""

    def test_code_snippet_creation(self):
        """Test creating CodeSnippet instance."""
        snippet = CodeSnippet(
            code="print('hello')",
            language="python",
            extension=".py",
            confidence=0.95
        )

        assert snippet.code == "print('hello')"
        assert snippet.language == "python"
        assert snippet.extension == ".py"
        assert snippet.confidence == 0.95

    def test_code_snippet_immutable(self):
        """Test that CodeSnippet is immutable (frozen)."""
        snippet = CodeSnippet(
            code="test",
            language="python",
            extension=".py",
            confidence=0.95
        )

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            snippet.code = "modified"  # type: ignore


# ============================================================================
# Test TempFile Dataclass
# ============================================================================

class TestTempFile:
    """Test TempFile dataclass."""

    def test_temp_file_creation(self):
        """Test creating TempFile instance."""
        temp_file = TempFile(
            path=Path("/tmp/test.py"),
            filename="test.py",
            language="python",
            created_at=1234567890.0
        )

        assert temp_file.path == Path("/tmp/test.py")
        assert temp_file.filename == "test.py"
        assert temp_file.language == "python"
        assert temp_file.created_at == 1234567890.0


# ============================================================================
# Test CodeSnippetHandler Initialization
# ============================================================================

class TestCodeSnippetHandlerInit:
    """Test CodeSnippetHandler initialization."""

    def test_init_with_custom_scratchpad(self, temp_scratchpad):
        """Test initialization with custom scratchpad directory."""
        handler = CodeSnippetHandler(scratchpad_dir=temp_scratchpad)

        assert handler.scratchpad_dir == temp_scratchpad
        assert handler.scratchpad_dir.exists()

    def test_init_creates_scratchpad_directory(self, tmp_path):
        """Test that scratchpad directory is created if it doesn't exist."""
        non_existent = tmp_path / "new_scratchpad"
        assert not non_existent.exists()

        handler = CodeSnippetHandler(scratchpad_dir=non_existent)

        assert handler.scratchpad_dir.exists()

    def test_init_with_default_scratchpad(self):
        """Test initialization with default scratchpad (None)."""
        handler = CodeSnippetHandler(scratchpad_dir=None)

        # Should create a default scratchpad directory
        assert handler.scratchpad_dir is not None
        assert isinstance(handler.scratchpad_dir, Path)


# ============================================================================
# Test detect_code_snippet Method
# ============================================================================

class TestDetectCodeSnippet:
    """Test code snippet detection."""

    def test_detect_python_code_snippet(self, handler):
        """Test detecting Python code snippet."""
        user_input = '''
Fix this code:
```python
def add(a, b):
    return a + b
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is not None
        assert snippet.language == "python"
        assert snippet.extension == ".py"
        assert "def add" in snippet.code
        assert snippet.confidence == 0.95  # High confidence with language

    def test_detect_javascript_code_snippet(self, handler):
        """Test detecting JavaScript code snippet."""
        user_input = '''
```javascript
function hello() {
    console.log("world");
}
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is not None
        assert snippet.language == "javascript"
        assert snippet.extension == ".js"
        assert "function hello" in snippet.code

    def test_detect_typescript_code_snippet(self, handler):
        """Test detecting TypeScript code snippet."""
        user_input = '''
```typescript
const add = (a: number, b: number): number => a + b;
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is not None
        assert snippet.language == "typescript"
        assert snippet.extension == ".ts"

    def test_detect_code_without_language(self, handler):
        """Test detecting code snippet without language specification."""
        user_input = '''
```
some code here
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is not None
        assert snippet.language == "txt"  # Default to txt
        assert snippet.extension == ".txt"
        assert snippet.confidence == 0.80  # Lower confidence without language

    def test_detect_no_code_snippet(self, handler):
        """Test when no code snippet is present."""
        user_input = "Just plain text without any code blocks"

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is None

    def test_detect_empty_code_block(self, handler):
        """Test detecting empty code block."""
        user_input = '''
```python
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is None  # Empty code blocks should return None

    def test_detect_code_case_insensitive(self, handler):
        """Test language detection is case-insensitive."""
        user_input = '''
```PYTHON
print("hello")
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is not None
        assert snippet.language == "python"  # Normalized to lowercase

    def test_detect_invalid_input_types(self, handler):
        """Test handling invalid input types."""
        assert handler.detect_code_snippet(None) is None
        assert handler.detect_code_snippet("") is None
        assert handler.detect_code_snippet(123) is None  # type: ignore

    def test_detect_multiple_code_blocks(self, handler):
        """Test detection with multiple code blocks (should detect first)."""
        user_input = '''
First block:
```python
def first():
    pass
```

Second block:
```javascript
function second() {}
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is not None
        assert snippet.language == "python"  # Should detect first block
        assert "def first" in snippet.code


# ============================================================================
# Test generate_temp_filename Method
# ============================================================================

class TestGenerateTempFilename:
    """Test temporary filename generation."""

    def test_generate_filename_with_python(self, handler):
        """Test generating filename for Python code."""
        filename = handler.generate_temp_filename("python", ".py", "print('test')")

        assert filename.startswith("pasted_code_")
        assert filename.endswith(".py")
        assert len(filename.split("_")) >= 3  # pasted_code_{timestamp}_{hash}

    def test_generate_filename_unique(self, handler):
        """Test that filenames are unique."""
        filename1 = handler.generate_temp_filename("python", ".py", "code1")
        filename2 = handler.generate_temp_filename("python", ".py", "code2")

        assert filename1 != filename2  # Different hashes

    def test_generate_filename_consistent_hash(self, handler):
        """Test that same code produces same hash."""
        code = "print('hello')"
        filename1 = handler.generate_temp_filename("python", ".py", code)
        filename2 = handler.generate_temp_filename("python", ".py", code)

        # Hash part should be the same
        hash1 = filename1.split("_")[-1].replace(".py", "")
        hash2 = filename2.split("_")[-1].replace(".py", "")
        assert hash1 == hash2


# ============================================================================
# Test create_temp_file Method
# ============================================================================

class TestCreateTempFile:
    """Test temporary file creation."""

    def test_create_temp_file_success(self, handler, temp_scratchpad):
        """Test successful temp file creation."""
        snippet = CodeSnippet(
            code="print('hello')",
            language="python",
            extension=".py",
            confidence=0.95
        )

        temp_file = handler.create_temp_file(snippet)

        assert temp_file is not None
        assert temp_file.path.exists()
        assert temp_file.path.parent == temp_scratchpad
        assert temp_file.filename.endswith(".py")
        assert temp_file.language == "python"
        assert temp_file.created_at > 0

    def test_create_temp_file_content(self, handler):
        """Test that temp file contains correct content."""
        snippet = CodeSnippet(
            code="def test():\n    pass",
            language="python",
            extension=".py",
            confidence=0.95
        )

        temp_file = handler.create_temp_file(snippet)

        assert temp_file is not None
        content = temp_file.path.read_text(encoding='utf-8')
        assert content == "def test():\n    pass"

    def test_create_temp_file_with_unicode(self, handler):
        """Test creating temp file with unicode content."""
        snippet = CodeSnippet(
            code="# 你好世界\nprint('hello')",
            language="python",
            extension=".py",
            confidence=0.95
        )

        temp_file = handler.create_temp_file(snippet)

        assert temp_file is not None
        content = temp_file.path.read_text(encoding='utf-8')
        assert "你好世界" in content

    @patch('pathlib.Path.write_text')
    def test_create_temp_file_write_error(self, mock_write, handler):
        """Test handling write error when creating temp file."""
        mock_write.side_effect = OSError("Permission denied")

        snippet = CodeSnippet(
            code="test",
            language="python",
            extension=".py",
            confidence=0.95
        )

        temp_file = handler.create_temp_file(snippet)

        assert temp_file is None  # Should return None on error


# ============================================================================
# Test detect_and_create_temp_file Method
# ============================================================================

class TestDetectAndCreateTempFile:
    """Test combined detection and file creation."""

    def test_detect_and_create_success(self, handler, temp_scratchpad):
        """Test successful detection and file creation."""
        user_input = '''
```python
def hello():
    print("world")
```
        '''

        temp_file = handler.detect_and_create_temp_file(user_input)

        assert temp_file is not None
        assert temp_file.path.exists()
        assert temp_file.language == "python"

        content = temp_file.path.read_text()
        assert "def hello" in content

    def test_detect_and_create_no_code(self, handler):
        """Test when no code is detected."""
        user_input = "Just plain text"

        temp_file = handler.detect_and_create_temp_file(user_input)

        assert temp_file is None


# ============================================================================
# Test Convenience Function
# ============================================================================

class TestDetectPastedCode:
    """Test detect_pasted_code convenience function."""

    def test_detect_pasted_code_success(self):
        """Test detecting pasted code."""
        user_input = '''
Fix this code:
```python
def bad_code():
    return 1 / 0
```
        '''

        temp_file = detect_pasted_code(user_input)

        assert temp_file is not None
        assert temp_file.language == "python"
        assert temp_file.path.exists()

    def test_detect_pasted_code_no_code(self):
        """Test when no code is pasted."""
        user_input = "Just a question"

        temp_file = detect_pasted_code(user_input)

        assert temp_file is None


# ============================================================================
# Test Language Extensions Mapping
# ============================================================================

class TestLanguageExtensions:
    """Test language extension mapping."""

    def test_common_language_extensions(self):
        """Test common language mappings."""
        assert LANGUAGE_EXTENSIONS["python"] == ".py"
        assert LANGUAGE_EXTENSIONS["javascript"] == ".js"
        assert LANGUAGE_EXTENSIONS["typescript"] == ".ts"
        assert LANGUAGE_EXTENSIONS["java"] == ".java"
        assert LANGUAGE_EXTENSIONS["go"] == ".go"
        assert LANGUAGE_EXTENSIONS["rust"] == ".rs"

    def test_alias_mappings(self):
        """Test language alias mappings."""
        assert LANGUAGE_EXTENSIONS["py"] == ".py"
        assert LANGUAGE_EXTENSIONS["js"] == ".js"
        assert LANGUAGE_EXTENSIONS["ts"] == ".ts"
        assert LANGUAGE_EXTENSIONS["rs"] == ".rs"

    def test_shell_script_mappings(self):
        """Test shell script language mappings."""
        assert LANGUAGE_EXTENSIONS["shell"] == ".sh"
        assert LANGUAGE_EXTENSIONS["bash"] == ".sh"
        assert LANGUAGE_EXTENSIONS["sh"] == ".sh"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for code snippet handler."""

    def test_end_to_end_python_snippet(self, handler):
        """Test end-to-end Python snippet handling."""
        user_input = '''
I need help fixing this code:
```python
def calculate_average(numbers):
    return sum(numbers) / len(numbers)  # Bug: no zero check
```
        '''

        # Detect snippet
        snippet = handler.detect_code_snippet(user_input)
        assert snippet is not None
        assert snippet.language == "python"

        # Create temp file
        temp_file = handler.create_temp_file(snippet)
        assert temp_file is not None
        assert temp_file.path.exists()

        # Verify content
        content = temp_file.path.read_text()
        assert "def calculate_average" in content
        assert "sum(numbers)" in content

    def test_end_to_end_javascript_snippet(self, handler):
        """Test end-to-end JavaScript snippet handling."""
        user_input = '''
```javascript
const fetchData = async () => {
    const response = await fetch('/api/data');
    return response.json();
};
```
        '''

        temp_file = handler.detect_and_create_temp_file(user_input)

        assert temp_file is not None
        assert temp_file.language == "javascript"
        assert temp_file.filename.endswith(".js")

    def test_end_to_end_unknown_language(self, handler):
        """Test handling snippet with unknown language."""
        user_input = '''
```unknownlang
some code here
```
        '''

        snippet = handler.detect_code_snippet(user_input)

        assert snippet is not None
        # Unknown language should default to txt
        # But extension lookup will use unknownlang, defaulting to .txt in get()
        assert snippet.extension == ".txt"
