"""RAG Knowledge Synchronization Commands.

Commands for synchronizing RAG knowledge files with codebase changes.
"""

import logging
from pathlib import Path
from typing import Optional

from tapps_agents.core.sync.rag_synchronizer import RagSynchronizer
from tapps_agents.core.generators.project_overview_generator import ProjectOverviewGenerator

logger = logging.getLogger(__name__)


class RagCommand:
    """RAG knowledge synchronization commands."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize RAG command.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()

    def sync(
        self,
        dry_run: bool = False,
        auto_apply: bool = False,
        report_only: bool = False,
    ) -> dict:
        """Synchronize RAG knowledge files with codebase changes.

        Args:
            dry_run: Simulate changes without applying
            auto_apply: Automatically apply changes without confirmation
            report_only: Only generate and display change report

        Returns:
            Synchronization results
        """
        try:
            # Initialize synchronizer
            synchronizer = RagSynchronizer(self.project_root)

            # Detect package renames
            logger.info("Detecting package renames...")
            renames = synchronizer.detect_package_renames()

            # Find stale imports
            logger.info("Finding stale imports...")
            stale_refs = synchronizer.find_stale_imports()

            # Generate change report
            logger.info("Generating change report...")
            report = synchronizer.generate_change_report(renames, stale_refs)

            # If report_only, return report without applying
            if report_only:
                return {
                    "status": "report_generated",
                    "report": {
                        "timestamp": report.timestamp,
                        "total_files": report.total_files,
                        "total_changes": report.total_changes,
                        "renames": [
                            {
                                "old_name": r.old_name,
                                "new_name": r.new_name,
                                "file_path": str(r.file_path),
                                "confidence": r.confidence,
                            }
                            for r in report.renames
                        ],
                        "stale_refs": [
                            {
                                "file_path": str(ref.file_path),
                                "line_number": ref.line_number,
                                "old_import": ref.old_import,
                                "suggested_import": ref.suggested_import,
                            }
                            for ref in report.stale_refs
                        ],
                        "diff_preview": report.diff_preview,
                    },
                }

            # If no changes detected
            if report.total_changes == 0:
                return {
                    "status": "no_changes",
                    "message": "No changes detected",
                    "report": {
                        "timestamp": report.timestamp,
                        "total_files": report.total_files,
                        "total_changes": report.total_changes,
                    },
                }

            # Apply changes
            if dry_run:
                logger.info("DRY RUN: Changes will not be applied")
                success = synchronizer.apply_changes(report, dry_run=True)
                status = "dry_run_success" if success else "dry_run_failed"
            elif auto_apply:
                logger.info("Auto-applying changes...")
                success = synchronizer.apply_changes(report, dry_run=False)
                status = "changes_applied" if success else "changes_failed"
            else:
                # Interactive mode - ask for confirmation
                logger.info("Changes require confirmation (use --auto-apply to skip)")
                return {
                    "status": "confirmation_required",
                    "report": {
                        "timestamp": report.timestamp,
                        "total_files": report.total_files,
                        "total_changes": report.total_changes,
                        "diff_preview": report.diff_preview,
                    },
                    "message": "Use --auto-apply to apply changes automatically",
                }

            return {
                "status": status,
                "report": {
                    "timestamp": report.timestamp,
                    "total_files": report.total_files,
                    "total_changes": report.total_changes,
                    "diff_preview": report.diff_preview,
                },
            }

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def generate_overview(
        self,
        output_file: Optional[Path] = None,
        force: bool = False,
    ) -> dict:
        """Generate project overview from metadata and architecture.

        Args:
            output_file: Output file path (defaults to PROJECT_OVERVIEW.md)
            force: Force regeneration even if file is recent

        Returns:
            Generation results
        """
        try:
            # Initialize generator
            generator = ProjectOverviewGenerator(
                project_root=self.project_root,
                output_file=output_file,
            )

            # Generate overview
            logger.info("Generating project overview...")
            overview = generator.generate_overview()

            # Update file
            updated = generator.update_overview(force=force)

            return {
                "status": "success",
                "updated": updated,
                "output_file": str(generator.output_file),
                "overview_length": len(overview),
            }

        except Exception as e:
            logger.error(f"Overview generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def detect_architecture(self) -> dict:
        """Detect architecture patterns from directory structure.

        Returns:
            Detected architecture patterns
        """
        try:
            # Initialize generator
            generator = ProjectOverviewGenerator(project_root=self.project_root)

            # Detect patterns
            logger.info("Detecting architecture patterns...")
            patterns = generator.detect_architecture_patterns()

            return {
                "status": "success",
                "patterns": [
                    {
                        "pattern": p.pattern.value,
                        "confidence": p.confidence,
                        "indicators": p.indicators,
                    }
                    for p in patterns
                ],
            }

        except Exception as e:
            logger.error(f"Architecture detection failed: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def extract_metadata(self) -> dict:
        """Extract project metadata from configuration files.

        Returns:
            Extracted project metadata
        """
        try:
            # Initialize generator
            generator = ProjectOverviewGenerator(project_root=self.project_root)

            # Extract metadata
            logger.info("Extracting project metadata...")
            metadata = generator.extract_project_metadata()

            return {
                "status": "success",
                "metadata": metadata.to_dict(),
            }

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
