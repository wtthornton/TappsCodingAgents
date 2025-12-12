"""
Filesystem MCP Server - File and directory operations.
"""

from pathlib import Path
from typing import Any

from ..tool_registry import ToolCategory, ToolRegistry


class FilesystemMCPServer:
    """MCP server for filesystem operations."""

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        """Register filesystem tools."""
        self.registry.register(
            name="read_file",
            description="Read contents of a file",
            category=ToolCategory.FILESYSTEM,
            handler=self.read_file,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "Path to file",
                }
            },
            cache_strategy="tier3",
        )

        self.registry.register(
            name="write_file",
            description="Write contents to a file",
            category=ToolCategory.FILESYSTEM,
            handler=self.write_file,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "Path to file",
                },
                "content": {
                    "type": "string",
                    "required": True,
                    "description": "File content",
                },
            },
            cache_strategy="invalidate",
        )

        self.registry.register(
            name="list_directory",
            description="List contents of a directory",
            category=ToolCategory.FILESYSTEM,
            handler=self.list_directory,
            parameters={
                "dir_path": {
                    "type": "string",
                    "required": True,
                    "description": "Directory path",
                },
                "recursive": {
                    "type": "boolean",
                    "required": False,
                    "description": "Recursive listing",
                },
            },
            cache_strategy="tier1",
        )

        self.registry.register(
            name="glob_search",
            description="Search for files matching a pattern",
            category=ToolCategory.FILESYSTEM,
            handler=self.glob_search,
            parameters={
                "pattern": {
                    "type": "string",
                    "required": True,
                    "description": "Glob pattern",
                },
                "root_dir": {
                    "type": "string",
                    "required": False,
                    "description": "Root directory",
                },
            },
            cache_strategy="tier1",
        )

        self.registry.register(
            name="grep_search",
            description="Search for text patterns in files",
            category=ToolCategory.FILESYSTEM,
            handler=self.grep_search,
            parameters={
                "pattern": {
                    "type": "string",
                    "required": True,
                    "description": "Search pattern",
                },
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "File to search",
                },
                "case_sensitive": {
                    "type": "boolean",
                    "required": False,
                    "description": "Case sensitive search",
                },
            },
            cache_strategy="tier2",
        )

    def read_file(self, file_path: str, encoding: str = "utf-8") -> dict[str, Any]:
        """Read file contents."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        content = path.read_text(encoding=encoding)
        return {"file_path": str(path), "content": content, "size": len(content)}

    def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> dict[str, Any]:
        """Write file contents."""
        path = Path(file_path)

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding=encoding)
        return {"file_path": str(path), "size": len(content), "written": True}

    def list_directory(self, dir_path: str, recursive: bool = False) -> dict[str, Any]:
        """List directory contents."""
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

        items = []
        if recursive:
            for item in path.rglob("*"):
                items.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )
        else:
            for item in path.iterdir():
                items.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )

        return {"directory": str(path), "items": items, "count": len(items)}

    def glob_search(
        self, pattern: str, root_dir: str | None = None
    ) -> dict[str, Any]:
        """Search for files matching a pattern."""
        if root_dir:
            search_path = Path(root_dir) / pattern
        else:
            search_path = Path(pattern)

        matches = list(search_path.parent.glob(search_path.name))

        return {
            "pattern": pattern,
            "matches": [str(m) for m in matches],
            "count": len(matches),
        }

    def grep_search(
        self, pattern: str, file_path: str, case_sensitive: bool = True
    ) -> dict[str, Any]:
        """Search for text patterns in a file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        matches = []
        flags = 0 if case_sensitive else 1  # re.IGNORECASE = 1
        import re

        for line_num, line in enumerate(lines, 1):
            if re.search(pattern, line, flags):
                matches.append({"line": line_num, "content": line.strip()})

        return {
            "file_path": str(path),
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
        }
