"""
Background Context Agent - Executes context management as a Background Agent.

This module provides a Background Agent wrapper around Context7 integration
that produces versioned, machine-readable context artifacts.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ..context7.agent_integration import Context7AgentHelper
from ..context7.commands import Context7Commands
from ..core.config import load_config
from ..mcp.gateway import MCPGateway
from .context_artifact import (
    ContextArtifact,
    ContextQuery,
    LibraryCacheEntry,
    ProjectProfile,
)


class BackgroundContextAgent:
    """
    Background Context Agent that manages Context7 knowledge base and produces artifacts.

    Epic 2 / Story 2.2: Background Cloud Agents - Docs, Ops, Context
    """

    def __init__(
        self,
        worktree_path: Path,
        correlation_id: str | None = None,
        timeout_seconds: float = 1800.0,  # 30 minutes default (for cache population)
    ):
        """
        Initialize Background Context Agent.

        Args:
            worktree_path: Path to worktree where context operations should run
            correlation_id: Optional correlation ID for tracking
            timeout_seconds: Maximum execution time in seconds
        """
        self.worktree_path = Path(worktree_path)
        self.correlation_id = correlation_id
        self.timeout_seconds = timeout_seconds
        self.config = load_config()
        self.context7_commands: Context7Commands | None = None
        self.context7_helper: Context7AgentHelper | None = None
        self.mcp_gateway: MCPGateway | None = None
        self._cancelled = False

    async def run_operation(
        self,
        operation_type: str,
        **kwargs: Any,
    ) -> ContextArtifact:
        """
        Run a context operation and produce artifact.

        Args:
            operation_type: Type of operation to run
                          ("cache_population", "query", "profiling", "cache_optimization")
            **kwargs: Additional arguments for the operation

        Returns:
            ContextArtifact with operation results
        """
        artifact = ContextArtifact(
            worktree_path=str(self.worktree_path),
            correlation_id=self.correlation_id,
            operation_type=operation_type,
        )

        try:
            # Initialize Context7 components
            self.context7_commands = Context7Commands(
                project_root=self.worktree_path, config=self.config
            )

            if not self.context7_commands.enabled:
                artifact.mark_failed("Context7 is not enabled in configuration")
                self._write_artifact(artifact)
                return artifact

            # Initialize MCP Gateway if available
            try:
                self.mcp_gateway = MCPGateway()
                self.context7_commands.set_mcp_gateway(self.mcp_gateway)
            except Exception:
                # MCP Gateway not available, continue without it
                pass

            # Initialize helper
            self.context7_helper = Context7AgentHelper(
                config=self.config,
                mcp_gateway=self.mcp_gateway,
                project_root=self.worktree_path,
            )

            if not self.context7_helper.enabled:
                artifact.mark_failed("Context7 helper is not enabled")
                self._write_artifact(artifact)
                return artifact

            artifact.status = "running"

            # Run operation with timeout
            await asyncio.wait_for(
                self._execute_operation(artifact, operation_type, **kwargs),
                timeout=self.timeout_seconds,
            )

            artifact.mark_completed()

        except asyncio.TimeoutError:
            artifact.mark_timeout()
        except asyncio.CancelledError:
            artifact.mark_cancelled()
        except Exception as e:
            artifact.mark_failed(str(e))

        # Write artifact to worktree
        self._write_artifact(artifact)

        return artifact

    async def _execute_operation(
        self,
        artifact: ContextArtifact,
        operation_type: str,
        **kwargs: Any,
    ) -> None:
        """Execute the specified operation."""
        if self._cancelled:
            artifact.mark_cancelled()
            return

        if not self.context7_commands or not self.context7_commands.enabled:
            artifact.mark_failed("Context7 commands not initialized")
            return

        try:
            if operation_type == "cache_population":
                await self._populate_cache(artifact, **kwargs)
            elif operation_type == "query":
                await self._execute_query(artifact, **kwargs)
            elif operation_type == "profiling":
                await self._profile_project(artifact, **kwargs)
            elif operation_type == "cache_optimization":
                await self._optimize_cache(artifact, **kwargs)
            else:
                artifact.mark_failed(f"Unknown operation type: {operation_type}")

        except Exception as e:
            artifact.mark_failed(str(e))

    async def _populate_cache(
        self, artifact: ContextArtifact, **kwargs: Any
    ) -> None:
        """Populate cache for libraries."""
        if not self.context7_commands:
            return

        libraries = kwargs.get("libraries", [])
        if not libraries:
            # Default libraries to populate
            libraries = ["fastapi", "pytest", "pydantic", "sqlalchemy"]

        for library in libraries:
            if self._cancelled:
                artifact.mark_cancelled()
                return

            try:
                # Resolve library ID first
                library_id = None
                if self.mcp_gateway:
                    try:
                        resolve_result = await self.mcp_gateway.call_tool(
                            "mcp_Context7_resolve-library-id", libraryName=library
                        )
                        if resolve_result.get("success"):
                            matches = resolve_result.get("result", {}).get("matches", [])
                            if matches:
                                library_id = matches[0].get("id")
                    except Exception:
                        pass

                # Check if already cached
                is_cached = self.context7_helper.is_library_cached(library) if self.context7_helper else False

                if is_cached:
                    # Get cache info
                    cache_stats = self.context7_helper.get_cache_statistics() if self.context7_helper else {}
                    entry = LibraryCacheEntry(
                        library_name=library,
                        library_id=library_id,
                        status="cached",
                        cache_hit_count=cache_stats.get("cache_hits", 0),
                    )
                    artifact.add_library_cache_entry(entry)
                    continue

                # Try to populate cache
                try:
                    # Use cmd_docs to trigger cache population
                    result = await self.context7_commands.cmd_docs(library=library)

                    if result.get("error"):
                        entry = LibraryCacheEntry(
                            library_name=library,
                            library_id=library_id,
                            status="failed",
                            error_message=result.get("error"),
                        )
                    else:
                        # Successfully cached
                        entry = LibraryCacheEntry(
                            library_name=library,
                            library_id=library_id,
                            status="cached",
                            cache_hit_count=1,
                        )

                    artifact.add_library_cache_entry(entry)

                except Exception as e:
                    entry = LibraryCacheEntry(
                        library_name=library,
                        library_id=library_id,
                        status="failed",
                        error_message=str(e),
                    )
                    artifact.add_library_cache_entry(entry)

            except Exception as e:
                entry = LibraryCacheEntry(
                    library_name=library,
                    status="failed",
                    error_message=str(e),
                )
                artifact.add_library_cache_entry(entry)

    async def _execute_query(
        self, artifact: ContextArtifact, **kwargs: Any
    ) -> None:
        """Execute Context7 query."""
        if not self.context7_helper:
            return

        query = kwargs.get("query")
        library = kwargs.get("library")
        topic = kwargs.get("topic")

        if not query and not library:
            artifact.mark_failed("Query or library must be provided")
            return

        try:
            start_time = asyncio.get_event_loop().time()

            # Execute query
            if library:
                result = await self.context7_helper.get_documentation(
                    library=library, topic=topic
                )
            else:
                # Search for libraries matching query
                results = await self.context7_helper.search_libraries(query=query)
                result = {"matches": results} if results else None

            end_time = asyncio.get_event_loop().time()
            execution_time = (end_time - start_time) * 1000  # Convert to ms

            cache_hit = False
            if result and isinstance(result, dict):
                cache_hit = result.get("source") == "cache"

            query_result = ContextQuery(
                query=query or f"{library}/{topic or 'overview'}",
                library=library,
                results_count=len(result.get("matches", [])) if isinstance(result, dict) and "matches" in result else (1 if result else 0),
                cache_hit=cache_hit,
                execution_time_seconds=execution_time / 1000.0,
            )

            artifact.add_query(query_result)

        except Exception as e:
            query_result = ContextQuery(
                query=query or f"{library}/{topic or 'overview'}",
                library=library,
                cache_hit=False,
                error_message=str(e),
            )
            artifact.add_query(query_result)

    async def _profile_project(
        self, artifact: ContextArtifact, **kwargs: Any
    ) -> None:
        """Profile the project."""
        # Simple project profiling based on files and structure
        try:
            # Analyze project structure
            has_docker = (self.worktree_path / "Dockerfile").exists()
            has_k8s = (self.worktree_path / "k8s").exists() or any(
                (self.worktree_path / "kubernetes").glob("*.yaml")
            )
            has_terraform = (self.worktree_path / "terraform").exists()

            # Determine deployment type
            if has_k8s or has_terraform:
                deployment_type = "cloud_native"
            elif has_docker:
                deployment_type = "hybrid"
            else:
                deployment_type = "on_premise"

            # Check for compliance files
            compliance = []
            if (self.worktree_path / "SECURITY.md").exists():
                compliance.append("security")
            if (self.worktree_path / "LICENSE").exists():
                compliance.append("license")

            # Simple scale estimation based on file count
            py_files = list(self.worktree_path.rglob("*.py"))
            file_count = len(py_files)

            if file_count < 50:
                user_scale = "small"
            elif file_count < 200:
                user_scale = "medium"
            elif file_count < 1000:
                user_scale = "large"
            else:
                user_scale = "enterprise"

            # Determine relevant experts based on project structure
            relevant_experts = []
            if has_docker or has_k8s:
                relevant_experts.append("devops")
            if any("test" in str(f) for f in py_files):
                relevant_experts.append("testing")
            if (self.worktree_path / "docs").exists():
                relevant_experts.append("documentation")

            profile = ProjectProfile(
                deployment_type=deployment_type,
                tenancy="multi_tenant",  # Default assumption
                user_scale=user_scale,
                compliance=compliance,
                security_posture="medium",  # Default assumption
                relevant_experts=relevant_experts,
            )

            artifact.set_project_profile(profile)

        except Exception as e:
            artifact.mark_failed(f"Project profiling failed: {str(e)}")

    async def _optimize_cache(
        self, artifact: ContextArtifact, **kwargs: Any
    ) -> None:
        """Optimize cache (cleanup, etc.)."""
        if not self.context7_commands:
            return

        try:
            # Run cache cleanup
            cleanup_result = await self.context7_commands.cmd_cleanup()

            if cleanup_result.get("success"):
                artifact.cache_cleanup_performed = True
                # Extract from nested result
                result_data = cleanup_result.get("result", {})
                if isinstance(result_data, dict):
                    artifact.files_removed = result_data.get("files_removed", 0)
                    artifact.space_freed_bytes = result_data.get("space_freed_bytes", 0)

            # Get updated cache statistics
            if self.context7_helper:
                stats = self.context7_helper.get_cache_statistics()
                artifact.cache_hit_rate = stats.get("hit_rate", 0.0)
                artifact.total_cache_size_bytes = stats.get("total_size_bytes", 0)

        except Exception as e:
            artifact.mark_failed(f"Cache optimization failed: {str(e)}")

    def _write_artifact(self, artifact: ContextArtifact) -> None:
        """Write artifact to worktree."""
        reports_dir = self.worktree_path / "reports" / "context"
        reports_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = reports_dir / "context-report.json"
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, indent=2)

    def cancel(self) -> None:
        """Cancel running operation."""
        self._cancelled = True
