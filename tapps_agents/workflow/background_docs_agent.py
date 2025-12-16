"""
Background Documentation Agent - Executes documentation generation as a Background Agent.

This module provides a Background Agent wrapper around the Documenter Agent
that produces versioned, machine-readable documentation artifacts.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from ..agents.documenter.agent import DocumenterAgent
from ..core.config import load_config
from .docs_artifact import DocFileResult, DocumentationArtifact


class BackgroundDocsAgent:
    """
    Background Documentation Agent that generates documentation and produces artifacts.

    Epic 2 / Story 2.2: Background Cloud Agents - Docs, Ops, Context
    """

    def __init__(
        self,
        worktree_path: Path,
        correlation_id: str | None = None,
        timeout_seconds: float = 900.0,  # 15 minutes default
    ):
        """
        Initialize Background Documentation Agent.

        Args:
            worktree_path: Path to worktree where documentation should be generated
            correlation_id: Optional correlation ID for tracking
            timeout_seconds: Maximum execution time in seconds
        """
        self.worktree_path = Path(worktree_path)
        self.correlation_id = correlation_id
        self.timeout_seconds = timeout_seconds
        self.config = load_config()
        self.documenter_agent: DocumenterAgent | None = None
        self._cancelled = False

    async def generate_documentation(
        self,
        target_path: Path | None = None,
        doc_types: list[str] | None = None,
    ) -> DocumentationArtifact:
        """
        Generate documentation and produce artifact.

        Args:
            target_path: Optional specific file or directory to document
            doc_types: Optional list of documentation types to generate
                      (e.g., ["api_docs", "readme", "docstrings"])

        Returns:
            DocumentationArtifact with generation results
        """
        artifact = DocumentationArtifact(
            worktree_path=str(self.worktree_path),
            correlation_id=self.correlation_id,
        )

        try:
            # Initialize documenter agent
            self.documenter_agent = DocumenterAgent(config=self.config)
            await self.documenter_agent.activate(project_root=self.worktree_path)

            # Change to worktree directory for documentation
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(self.worktree_path)

                artifact.status = "running"

                # Run documentation generation with timeout
                await asyncio.wait_for(
                    self._generate_docs(artifact, target_path, doc_types),
                    timeout=self.timeout_seconds,
                )

                artifact.mark_completed()

            finally:
                os.chdir(original_cwd)
                if self.documenter_agent:
                    await self.documenter_agent.close()

        except TimeoutError:
            artifact.mark_timeout()
        except asyncio.CancelledError:
            artifact.mark_cancelled()
        except Exception as e:
            artifact.mark_failed(str(e))

        # Write artifact to worktree
        self._write_artifact(artifact)

        return artifact

    async def _generate_docs(
        self,
        artifact: DocumentationArtifact,
        target_path: Path | None = None,
        doc_types: list[str] | None = None,
    ) -> None:
        """Generate documentation based on target and types."""
        if self._cancelled:
            artifact.mark_cancelled()
            return

        if not self.documenter_agent:
            artifact.mark_failed("Documenter agent not initialized")
            return

        # Determine target for documentation
        if target_path:
            analysis_target = Path(target_path)
        else:
            analysis_target = self.worktree_path

        # Default doc types if not specified
        if doc_types is None:
            doc_types = ["api_docs", "readme"]

        # Generate documentation based on types
        for doc_type in doc_types:
            if self._cancelled:
                artifact.mark_cancelled()
                return

            try:
                if doc_type == "api_docs":
                    await self._generate_api_docs(artifact, analysis_target)
                elif doc_type == "readme":
                    await self._generate_readme(artifact)
                elif doc_type == "docstrings":
                    await self._generate_docstrings(artifact, analysis_target)
                else:
                    # Unknown doc type, skip
                    result = DocFileResult(
                        file_path=str(analysis_target),
                        doc_type=doc_type,
                        status="skipped",
                        error_message=f"Unknown documentation type: {doc_type}",
                    )
                    artifact.add_file_result(result)

            except Exception as e:
                result = DocFileResult(
                    file_path=str(analysis_target),
                    doc_type=doc_type,
                    status="error",
                    error_message=str(e),
                )
                artifact.add_file_result(result)

    async def _generate_api_docs(
        self, artifact: DocumentationArtifact, target: Path
    ) -> None:
        """Generate API documentation."""
        if not self.documenter_agent:
            return

        try:
            # Find Python files to document
            if target.is_file() and target.suffix == ".py":
                files_to_doc = [target]
            elif target.is_dir():
                files_to_doc = list(target.rglob("*.py"))[:20]  # Limit to 20 files
            else:
                files_to_doc = []

            if not files_to_doc:
                result = DocFileResult(
                    file_path=str(target),
                    doc_type="api_docs",
                    status="skipped",
                    error_message="No Python files found to document",
                )
                artifact.add_file_result(result)
                return

            # Generate docs for each file
            for file_path in files_to_doc:
                if self._cancelled:
                    artifact.mark_cancelled()
                    return

                try:
                    result_dict = await self.documenter_agent.generate_docs_command(
                        file=str(file_path), output_format="markdown"
                    )

                    if "error" in result_dict:
                        result = DocFileResult(
                            file_path=str(file_path),
                            doc_type="api_docs",
                            status="error",
                            error_message=result_dict["error"],
                        )
                    else:
                        # Determine output file
                        output_file = result_dict.get("output_file")
                        if not output_file:
                            # Auto-generate output path
                            docs_dir = self.worktree_path / "docs" / "api"
                            docs_dir.mkdir(parents=True, exist_ok=True)
                            output_file = str(docs_dir / f"{file_path.stem}_api.md")

                        result = DocFileResult(
                            file_path=str(file_path),
                            doc_type="api_docs",
                            status="success",
                            output_file=output_file,
                            lines_added=len(result_dict.get("documentation", "").split("\n")),
                        )

                    artifact.add_file_result(result)

                except Exception as e:
                    result = DocFileResult(
                        file_path=str(file_path),
                        doc_type="api_docs",
                        status="error",
                        error_message=str(e),
                    )
                    artifact.add_file_result(result)

        except Exception as e:
            result = DocFileResult(
                file_path=str(target),
                doc_type="api_docs",
                status="error",
                error_message=str(e),
            )
            artifact.add_file_result(result)

    async def _generate_readme(self, artifact: DocumentationArtifact) -> None:
        """Generate or update README."""
        if not self.documenter_agent:
            return

        try:
            result_dict = await self.documenter_agent.update_readme_command(
                project_root=str(self.worktree_path)
            )

            if "error" in result_dict:
                result = DocFileResult(
                    file_path=str(self.worktree_path),
                    doc_type="readme",
                    status="error",
                    error_message=result_dict["error"],
                )
            else:
                readme_file = result_dict.get("readme_file", str(self.worktree_path / "README.md"))
                result = DocFileResult(
                    file_path=str(self.worktree_path),
                    doc_type="readme",
                    status="success",
                    output_file=readme_file,
                    lines_added=len(result_dict.get("readme", "").split("\n")),
                )

            artifact.add_file_result(result)

        except Exception as e:
            result = DocFileResult(
                file_path=str(self.worktree_path),
                doc_type="readme",
                status="error",
                error_message=str(e),
            )
            artifact.add_file_result(result)

    async def _generate_docstrings(
        self, artifact: DocumentationArtifact, target: Path
    ) -> None:
        """Generate or update docstrings."""
        if not self.documenter_agent:
            return

        try:
            # Find Python files to update
            if target.is_file() and target.suffix == ".py":
                files_to_update = [target]
            elif target.is_dir():
                files_to_update = list(target.rglob("*.py"))[:10]  # Limit to 10 files
            else:
                files_to_update = []

            if not files_to_update:
                result = DocFileResult(
                    file_path=str(target),
                    doc_type="docstrings",
                    status="skipped",
                    error_message="No Python files found to update",
                )
                artifact.add_file_result(result)
                return

            # Update docstrings for each file
            for file_path in files_to_update:
                if self._cancelled:
                    artifact.mark_cancelled()
                    return

                try:
                    result_dict = await self.documenter_agent.update_docstrings_command(
                        file=str(file_path), write_file=True
                    )

                    if "error" in result_dict:
                        result = DocFileResult(
                            file_path=str(file_path),
                            doc_type="docstrings",
                            status="error",
                            error_message=result_dict["error"],
                        )
                    else:
                        # Count lines updated (approximate)
                        updated_code = result_dict.get("updated_code", "")
                        lines_updated = len(updated_code.split("\n"))

                        result = DocFileResult(
                            file_path=str(file_path),
                            doc_type="docstrings",
                            status="success",
                            output_file=str(file_path),  # Updated in place
                            lines_updated=lines_updated,
                        )

                    artifact.add_file_result(result)

                except Exception as e:
                    result = DocFileResult(
                        file_path=str(file_path),
                        doc_type="docstrings",
                        status="error",
                        error_message=str(e),
                    )
                    artifact.add_file_result(result)

        except Exception as e:
            result = DocFileResult(
                file_path=str(target),
                doc_type="docstrings",
                status="error",
                error_message=str(e),
            )
            artifact.add_file_result(result)

    def _write_artifact(self, artifact: DocumentationArtifact) -> None:
        """Write artifact to worktree."""
        reports_dir = self.worktree_path / "reports" / "documentation"
        reports_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = reports_dir / "docs-report.json"
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, indent=2)

    def cancel(self) -> None:
        """Cancel running documentation generation."""
        self._cancelled = True
