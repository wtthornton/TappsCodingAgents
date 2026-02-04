"""
Code Snippet Handler - Detect and handle pasted code in user input.

Detects markdown code blocks, creates temporary files in scratchpad directory,
and integrates with workflow suggester for automatic *fix workflow invocation.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


# Language to file extension mapping
LANGUAGE_EXTENSIONS: dict[str, str] = {
    "python": ".py",
    "py": ".py",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "java": ".java",
    "go": ".go",
    "rust": ".rs",
    "rs": ".rs",
    "c": ".c",
    "cpp": ".cpp",
    "c++": ".cpp",
    "csharp": ".cs",
    "cs": ".cs",
    "ruby": ".rb",
    "rb": ".rb",
    "php": ".php",
    "swift": ".swift",
    "kotlin": ".kt",
    "scala": ".scala",
    "shell": ".sh",
    "bash": ".sh",
    "sh": ".sh",
    "sql": ".sql",
    "html": ".html",
    "css": ".css",
    "json": ".json",
    "yaml": ".yaml",
    "yml": ".yml",
    "xml": ".xml",
    "markdown": ".md",
    "md": ".md",
    "text": ".txt",
    "txt": ".txt",
}


# Markdown code fence pattern
MARKDOWN_CODE_FENCE_PATTERN = r"```(?P<lang>\w+)?\s*\n(?P<code>.*?)```"


@dataclass(frozen=True, slots=True)
class CodeSnippet:
    """
    Detected code snippet with metadata.

    Attributes:
        code: The extracted code content
        language: Detected language (or 'txt' if unknown)
        extension: File extension for the language
        confidence: Detection confidence (0.0-1.0)
    """

    code: str
    language: str
    extension: str
    confidence: float


@dataclass(frozen=True, slots=True)
class TempFile:
    """
    Temporary file information.

    Attributes:
        path: Full path to the temporary file
        filename: Just the filename
        language: Detected language
        created_at: Timestamp when file was created
    """

    path: Path
    filename: str
    language: str
    created_at: float


class CodeSnippetHandler:
    """
    Handler for detecting and processing pasted code snippets.

    Detects markdown code blocks in user input, creates temporary files
    in the scratchpad directory, and prepares for workflow integration.
    """

    def __init__(self, scratchpad_dir: Path | None = None):
        """
        Initialize code snippet handler.

        Args:
            scratchpad_dir: Path to scratchpad directory for temp files.
                If None, uses default Claude Code scratchpad location.
        """
        self._logger = logging.getLogger(__name__)

        # Use provided scratchpad or default location
        if scratchpad_dir is None:
            # Default Claude Code scratchpad location
            import tempfile

            base_temp = Path(tempfile.gettempdir())
            claude_dir = base_temp / "claude"

            # Try to find existing Claude directory with session ID
            if claude_dir.exists():
                # Look for subdirectories (session IDs)
                session_dirs = [d for d in claude_dir.iterdir() if d.is_dir()]
                if session_dirs:
                    # Use first session directory found
                    scratchpad_dir = session_dirs[0] / "scratchpad"
                else:
                    # Create default session directory
                    scratchpad_dir = claude_dir / "default" / "scratchpad"
            else:
                # Create default Claude directory structure
                scratchpad_dir = claude_dir / "default" / "scratchpad"

        self.scratchpad_dir = Path(scratchpad_dir)
        self._logger.debug(f"Scratchpad directory: {self.scratchpad_dir}")

        # Ensure scratchpad directory exists
        try:
            self.scratchpad_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._logger.warning(
                f"Could not create scratchpad directory {self.scratchpad_dir}: {e}"
            )

    def detect_code_snippet(self, user_input: str) -> CodeSnippet | None:
        """
        Detect code snippet in user input.

        Searches for markdown code fences (```lang...```) and extracts
        the code content and language.

        Args:
            user_input: User's natural language input

        Returns:
            CodeSnippet if code block detected, None otherwise

        Example:
            >>> handler = CodeSnippetHandler()
            >>> result = handler.detect_code_snippet('''
            ... Fix this code:
            ... ```python
            ... def add(a, b):
            ...     return a / b
            ... ```
            ... ''')
            >>> result.language
            'python'
            >>> result.code
            'def add(a, b):\\n    return a / b\\n'
        """
        if not user_input or not isinstance(user_input, str):
            return None

        try:
            # Search for markdown code fence
            match = re.search(
                MARKDOWN_CODE_FENCE_PATTERN,
                user_input,
                re.DOTALL | re.IGNORECASE
            )

            if not match:
                return None

            # Extract language and code
            language = match.group("lang")
            code = match.group("code")

            # Normalize language
            if language:
                language = language.lower().strip()
            else:
                language = "txt"  # Default if no language specified

            # Get file extension
            extension = LANGUAGE_EXTENSIONS.get(language, ".txt")

            # Validate code is not empty
            if not code or not code.strip():
                self._logger.debug("Code block detected but empty")
                return None

            # High confidence if language specified and code non-empty
            confidence = 0.95 if match.group("lang") else 0.80

            return CodeSnippet(
                code=code.strip(),
                language=language,
                extension=extension,
                confidence=confidence
            )

        except Exception as e:
            self._logger.error(f"Error detecting code snippet: {e}", exc_info=True)
            return None

    def generate_temp_filename(
        self,
        language: str,
        extension: str,
        code_content: str
    ) -> str:
        """
        Generate unique temporary filename.

        Uses timestamp and hash of code content to ensure uniqueness.

        Args:
            language: Detected language
            extension: File extension
            code_content: The code content (used for hash)

        Returns:
            Unique filename like "pasted_code_1234567890_abc123.py"

        Example:
            >>> handler = CodeSnippetHandler()
            >>> filename = handler.generate_temp_filename("python", ".py", "code")
            >>> filename.startswith("pasted_code_")
            True
            >>> filename.endswith(".py")
            True
        """
        # Generate timestamp
        timestamp = int(time.time())

        # Generate hash of code content
        code_hash = hashlib.md5(code_content.encode('utf-8')).hexdigest()[:8]

        # Construct filename
        filename = f"pasted_code_{timestamp}_{code_hash}{extension}"

        return filename

    def create_temp_file(self, snippet: CodeSnippet) -> TempFile | None:
        """
        Create temporary file with code snippet content.

        Writes the code snippet to a uniquely named file in the
        scratchpad directory.

        Args:
            snippet: CodeSnippet to write to file

        Returns:
            TempFile with file information, or None if creation failed

        Example:
            >>> handler = CodeSnippetHandler()
            >>> snippet = CodeSnippet(
            ...     code="print('hello')",
            ...     language="python",
            ...     extension=".py",
            ...     confidence=0.95
            ... )
            >>> temp_file = handler.create_temp_file(snippet)
            >>> temp_file.path.exists()
            True
        """
        try:
            # Generate unique filename
            filename = self.generate_temp_filename(
                snippet.language,
                snippet.extension,
                snippet.code
            )

            # Construct full path
            file_path = self.scratchpad_dir / filename

            # Write code to file
            file_path.write_text(snippet.code, encoding='utf-8')

            self._logger.info(f"Created temp file: {file_path}")

            return TempFile(
                path=file_path,
                filename=filename,
                language=snippet.language,
                created_at=time.time()
            )

        except Exception as e:
            self._logger.error(
                f"Failed to create temp file: {e}",
                exc_info=True
            )
            return None

    def detect_and_create_temp_file(
        self,
        user_input: str
    ) -> TempFile | None:
        """
        Detect code snippet and create temporary file in one step.

        Convenience method that combines detection and file creation.

        Args:
            user_input: User's natural language input

        Returns:
            TempFile if code detected and file created, None otherwise

        Example:
            >>> handler = CodeSnippetHandler()
            >>> temp_file = handler.detect_and_create_temp_file('''
            ... ```python
            ... def hello():
            ...     print("world")
            ... ```
            ... ''')
            >>> temp_file is not None
            True
        """
        # Detect code snippet
        snippet = self.detect_code_snippet(user_input)
        if snippet is None:
            return None

        # Create temp file
        temp_file = self.create_temp_file(snippet)
        return temp_file


# Convenience function for workflow integration
def detect_pasted_code(user_input: str) -> TempFile | None:
    """
    Detect pasted code and create temporary file.

    Convenience function for use in workflow suggester and other modules.

    Args:
        user_input: User's natural language input

    Returns:
        TempFile if code detected and file created, None otherwise

    Example:
        >>> temp_file = detect_pasted_code('''
        ... Fix this code:
        ... ```python
        ... def bad_code():
        ...     return 1 / 0
        ... ```
        ... ''')
        >>> temp_file is not None
        True
        >>> temp_file.language
        'python'
    """
    handler = CodeSnippetHandler()
    return handler.detect_and_create_temp_file(user_input)
