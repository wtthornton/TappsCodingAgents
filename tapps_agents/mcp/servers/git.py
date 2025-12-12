"""
Git MCP Server - Git operations.
"""

import subprocess
from pathlib import Path
from typing import Any

from ..tool_registry import ToolCategory, ToolRegistry


class GitMCPServer:
    """MCP server for Git operations."""

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        """Register Git tools."""
        self.registry.register(
            name="git_status",
            description="Get Git repository status",
            category=ToolCategory.GIT,
            handler=self.git_status,
            parameters={
                "repo_path": {
                    "type": "string",
                    "required": False,
                    "description": "Repository path",
                }
            },
            cache_strategy="none",
        )

        self.registry.register(
            name="git_diff",
            description="Get Git diff for files",
            category=ToolCategory.GIT,
            handler=self.git_diff,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": False,
                    "description": "File path",
                },
                "repo_path": {
                    "type": "string",
                    "required": False,
                    "description": "Repository path",
                },
            },
            cache_strategy="none",
        )

        self.registry.register(
            name="git_log",
            description="Get Git commit log",
            category=ToolCategory.GIT,
            handler=self.git_log,
            parameters={
                "repo_path": {
                    "type": "string",
                    "required": False,
                    "description": "Repository path",
                },
                "limit": {
                    "type": "integer",
                    "required": False,
                    "description": "Number of commits",
                },
            },
            cache_strategy="none",
        )

        self.registry.register(
            name="git_blame",
            description="Get Git blame for a file",
            category=ToolCategory.GIT,
            handler=self.git_blame,
            parameters={
                "file_path": {
                    "type": "string",
                    "required": True,
                    "description": "File path",
                },
                "repo_path": {
                    "type": "string",
                    "required": False,
                    "description": "Repository path",
                },
            },
            cache_strategy="none",
        )

    def _run_git_command(self, args: list, repo_path: Path | None = None) -> str:
        """Run a Git command."""
        cmd = ["git"] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path or Path.cwd(),
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr}") from e
        except FileNotFoundError as e:
            raise RuntimeError("Git not found. Is Git installed?") from e

    def git_status(self, repo_path: str | None = None) -> dict[str, Any]:
        """Get Git status."""
        path = Path(repo_path) if repo_path else Path.cwd()
        output = self._run_git_command(["status", "--porcelain"], repo_path=path)

        lines = output.split("\n") if output else []
        files = []
        for line in lines:
            if line.strip():
                status = line[:2]
                file_path = line[3:]
                files.append({"status": status, "file": file_path})

        return {"repo_path": str(path), "files": files, "modified_count": len(files)}

    def git_diff(
        self, file_path: str | None = None, repo_path: str | None = None
    ) -> dict[str, Any]:
        """Get Git diff."""
        path = Path(repo_path) if repo_path else Path.cwd()
        args = ["diff"]

        if file_path:
            args.append(file_path)

        output = self._run_git_command(args, repo_path=path)

        return {"repo_path": str(path), "file_path": file_path, "diff": output}

    def git_log(
        self, repo_path: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        """Get Git log."""
        path = Path(repo_path) if repo_path else Path.cwd()

        format_str = "%H|%an|%ae|%ad|%s"
        args = ["log", f"--pretty=format:{format_str}", f"-{limit}"]

        output = self._run_git_command(args, repo_path=path)

        commits = []
        for line in output.split("\n"):
            if line.strip():
                parts = line.split("|", 4)
                if len(parts) == 5:
                    commits.append(
                        {
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "date": parts[3],
                            "message": parts[4],
                        }
                    )

        return {"repo_path": str(path), "commits": commits, "count": len(commits)}

    def git_blame(
        self, file_path: str, repo_path: str | None = None
    ) -> dict[str, Any]:
        """Get Git blame."""
        path = Path(repo_path) if repo_path else Path.cwd()
        file_path_obj = Path(file_path)

        output = self._run_git_command(["blame", str(file_path_obj)], repo_path=path)

        lines = []
        for line in output.split("\n"):
            if line.strip():
                # Parse blame line format: hash (author date line) content
                parts = line.split(" ", 4)
                if len(parts) >= 5:
                    lines.append(
                        {
                            "hash": parts[0],
                            "author": parts[1].strip("()"),
                            "date": parts[2],
                            "line_number": parts[3],
                            "content": parts[4] if len(parts) > 4 else "",
                        }
                    )

        return {
            "repo_path": str(path),
            "file_path": str(file_path_obj),
            "lines": lines,
            "count": len(lines),
        }
